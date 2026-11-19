"""Asynchronous client for the Moj Elektro API.

The token is only ever placed in the ``X-API-TOKEN`` request header. It is
never logged, never included in exceptions and never returned to callers.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import contextlib
from dataclasses import dataclass, field
from datetime import date, datetime
from email.utils import parsedate_to_datetime
import json
import logging
import random
import re
import time
from typing import Any

import aiohttp

from .const import API_BASE_URL, MAX_REQUEST_DAYS
from .timeutil import parse_timestamp, to_epoch

_LOGGER = logging.getLogger(__name__)

METER_ID_PATTERN = re.compile(r"^\d{1,2}-\d+$")
GSRN_PATTERN = re.compile(r"^\d{18}$")

REQUEST_TIMEOUT = 30
MAX_RETRY_AFTER = 300
MIN_SPACING = 0.5
DEFAULT_BACKOFF = 2.0


class MojElektroError(Exception):
    """Base error. Messages never contain the token."""


class InvalidAuth(MojElektroError):
    """401: the token is missing, expired or wrong."""


class AccessDenied(MojElektroError):
    """403: the token is valid but cannot access this meter."""


class NotFound(MojElektroError):
    """404: the meter or measurement point does not exist."""


class InvalidRequest(MojElektroError):
    """400: the API rejected the parameters."""


class RateLimited(MojElektroError):
    """429 after all retries."""

    def __init__(self, message: str, retry_after: float | None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServiceError(MojElektroError):
    """5xx or another unexpected status after all retries."""


class ApiTimeout(MojElektroError):
    """The request timed out after all retries."""


class CannotConnect(MojElektroError):
    """A network-level failure after all retries."""


class MalformedResponse(MojElektroError):
    """The response was not the documented JSON structure."""


def normalize_meter_id(value: str) -> str:
    """Return the canonical form of a meter identifier, or raise ValueError."""
    cleaned = re.sub(r"\s+", "", value or "")
    if not METER_ID_PATTERN.fullmatch(cleaned):
        raise ValueError("invalid meter id")
    region, number = cleaned.split("-")
    return f"{int(region)}-{int(number)}"


@dataclass(slots=True, frozen=True)
class Reading:
    """A single interval reading identified by its UTC end instant."""

    end: int
    value: float | None
    qualities: tuple[str, ...] = ()


@dataclass(slots=True)
class ReadingsResult:
    """Parsed ``GET /meter-readings`` response."""

    blocks: dict[str, list[Reading]] = field(default_factory=dict)
    malformed: int = 0
    message_created: datetime | None = None


def _error_detail(payload: Any) -> str:
    """Return a short description from a documented error body, if any."""
    if not isinstance(payload, dict):
        return ""
    errors = payload.get("errors")
    items = errors if isinstance(errors, list) else [payload]
    parts = []
    for item in items:
        if isinstance(item, dict):
            code = item.get("koda")
            text = item.get("opis")
            if code or text:
                parts.append(" ".join(str(p) for p in (code, text) if p))
    return "; ".join(parts)[:300]


def parse_retry_after(value: str | None) -> float | None:
    """Parse a Retry-After header (seconds or HTTP date)."""
    if not value:
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            moment = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if moment is None:
            return None
        seconds = moment.timestamp() - time.time()
    return max(0.0, min(seconds, MAX_RETRY_AFTER))


def parse_readings(payload: Any) -> ReadingsResult:
    """Parse a meter-readings body. Raises MalformedResponse on bad shapes."""
    if not isinstance(payload, dict):
        raise MalformedResponse("meter readings response is not an object")
    blocks = payload.get("intervalBlocks", [])
    if blocks is None:
        blocks = []
    if not isinstance(blocks, list):
        raise MalformedResponse("intervalBlocks is not a list")
    result = ReadingsResult()
    created = payload.get("messageCreated")
    if isinstance(created, str):
        with contextlib.suppress(ValueError):
            result.message_created = parse_timestamp(created)
    for block in blocks:
        if not isinstance(block, dict) or not isinstance(block.get("readingType"), str):
            raise MalformedResponse("interval block without readingType")
        readings = block.get("intervalReadings") or []
        if not isinstance(readings, list):
            raise MalformedResponse("intervalReadings is not a list")
        parsed = result.blocks.setdefault(block["readingType"], [])
        for item in readings:
            reading = _parse_reading(item)
            if reading is None:
                result.malformed += 1
            else:
                parsed.append(reading)
    return result


def _parse_reading(item: Any) -> Reading | None:
    if not isinstance(item, dict) or not isinstance(item.get("timestamp"), str):
        return None
    try:
        end = to_epoch(parse_timestamp(item["timestamp"]))
    except ValueError:
        return None
    raw = item.get("value")
    value: float | None
    if raw is None or raw == "":
        value = None  # Missing, which is not the same as zero.
    else:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if value != value or value in (float("inf"), float("-inf")):
            return None
    qualities: list[str] = []
    for quality in item.get("readingQualities") or []:
        if isinstance(quality, dict) and isinstance(quality.get("readingQualityType"), str):
            qualities.append(quality["readingQualityType"])
    return Reading(end, value, tuple(sorted(set(qualities))))


class MojElektroClient:
    """Thin, rate-limited client. One instance per config entry."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        token: str,
        *,
        base_url: str = API_BASE_URL,
        retries: int = 3,
        backoff: float | None = None,
        concurrency: int = 1,
    ) -> None:
        self._session = session
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._retries = retries
        self._backoff = DEFAULT_BACKOFF if backoff is None else backoff
        self._semaphore = asyncio.Semaphore(concurrency)
        self._last_request = 0.0
        self.request_count = 0

    def __repr__(self) -> str:  # Never show the token.
        return f"MojElektroClient(base_url={self._base_url!r})"

    async def _request(self, path: str, params: list[tuple[str, str]] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        attempt = 0
        while True:
            try:
                return await self._request_once(url, params)
            except RateLimited as err:
                if attempt >= self._retries:
                    raise
                delay = err.retry_after
                if delay is None:
                    delay = self._backoff * (2**attempt)
            except (ServiceError, ApiTimeout, CannotConnect):
                if attempt >= self._retries:
                    raise
                delay = self._backoff * (2**attempt) + random.uniform(0, self._backoff)
            attempt += 1
            _LOGGER.debug("Retrying %s in %.1fs (attempt %s)", path, delay, attempt)
            await asyncio.sleep(delay)

    async def _request_once(self, url: str, params: list[tuple[str, str]] | None) -> Any:
        async with self._semaphore:
            wait = self._last_request + MIN_SPACING - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()
            self.request_count += 1
            try:
                async with self._session.get(
                    url,
                    params=params,
                    headers={"X-API-TOKEN": self._token, "Accept": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as response:
                    status = response.status
                    text = await response.text()
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
            except TimeoutError as err:
                raise ApiTimeout("Moj Elektro did not respond in time") from err
            except aiohttp.ClientError as err:
                raise CannotConnect(f"Cannot reach Moj Elektro ({type(err).__name__})") from err

        payload: Any = None
        if text.strip():
            try:
                payload = json.loads(text)
            except ValueError:
                payload = None
        detail = _error_detail(payload)
        suffix = f": {detail}" if detail else ""
        if status == 200:
            if payload is None:
                raise MalformedResponse("empty or non-JSON response")
            return payload
        if status == 401:
            raise InvalidAuth(f"Token rejected{suffix}")
        if status == 403:
            raise AccessDenied(f"Access denied{suffix}")
        if status == 404:
            raise NotFound(f"Not found{suffix}")
        if status == 400:
            raise InvalidRequest(f"Invalid request{suffix}")
        if status == 429:
            raise RateLimited(f"Rate limited{suffix}", retry_after)
        raise ServiceError(f"HTTP {status}{suffix}")

    async def get_meter_point(self, meter_id: str) -> dict[str, Any]:
        """GET /merilno-mesto/{identifikator}."""
        payload = await self._request(f"/merilno-mesto/{normalize_meter_id(meter_id)}")
        if not isinstance(payload, dict):
            raise MalformedResponse("meter point response is not an object")
        return payload

    async def get_measurement_point(self, gsrn: str) -> dict[str, Any]:
        """GET /merilna-tocka/{gsrn}."""
        if not GSRN_PATTERN.fullmatch(gsrn):
            raise ValueError("invalid gsrn")
        payload = await self._request(f"/merilna-tocka/{gsrn}")
        if not isinstance(payload, dict):
            raise MalformedResponse("measurement point response is not an object")
        return payload

    async def get_reading_types(self) -> list[dict[str, Any]]:
        """GET /reading-type."""
        payload = await self._request("/reading-type")
        if not isinstance(payload, list):
            raise MalformedResponse("reading types response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    async def get_reading_qualities(self) -> list[dict[str, Any]]:
        """GET /reading-qualities."""
        payload = await self._request("/reading-qualities")
        if not isinstance(payload, list):
            raise MalformedResponse("reading qualities response is not a list")
        return [item for item in payload if isinstance(item, dict)]

    async def get_readings(
        self,
        usage_point: str,
        start: date,
        end: date,
        reading_types: Iterable[str],
    ) -> ReadingsResult:
        """GET /meter-readings for ``[start, end)``; ``end`` is exclusive.

        At most 35 days per request, as enforced by the API.
        """
        types = list(reading_types)
        if not types:
            raise ValueError("at least one reading type is required")
        if end <= start:
            raise ValueError("end must be after start")
        if (end - start).days > MAX_REQUEST_DAYS:
            raise ValueError("a request may span at most 35 days")
        params = [
            ("usagePoint", normalize_meter_id(usage_point)),
            ("startTime", start.isoformat()),
            ("endTime", end.isoformat()),
        ]
        params.extend(("option", f"ReadingType={rt}") for rt in types)
        return parse_readings(await self._request("/meter-readings", params))


def resolve_reading_types(catalogue: list[dict[str, Any]]) -> dict[str, str]:
    """Map 15-minute energy register codes (A+, A-) to reading types."""
    found: dict[str, str] = {}
    for item in catalogue:
        code = item.get("oznaka")
        value = item.get("readingType")
        if (
            isinstance(code, str)
            and isinstance(value, str)
            and code in ("A+", "A-")
            and str(item.get("vrsta", "KOLICINA")).upper() == "KOLICINA"
            and "15" in str(item.get("perioda", "15"))
        ):
            found.setdefault(code, value)
    return found


def extract_gsrn(meter_point: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (meter-point GSRN, OMTO measurement-point GSRN)."""
    ident = meter_point.get("identifikator")
    point_gsrn = ident.get("gsrn") if isinstance(ident, dict) else None
    measurement = None
    for item in meter_point.get("merilneTocke") or []:
        if (
            isinstance(item, dict)
            and isinstance(item.get("gsrn"), str)
            and (item.get("vrsta") == "OMTO" or measurement is None)
        ):
            measurement = item["gsrn"]
    return (point_gsrn if isinstance(point_gsrn, str) else None), measurement
