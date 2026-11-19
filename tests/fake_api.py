"""A fake Moj Elektro service for tests. No real API is ever called.

It reproduces the behaviour confirmed against the live API:

* a ReadingType option is required,
* requests may span at most 35 days and reach at most two years back,
* ``endTime`` is exclusive (whole local days, Europe/Ljubljana),
* timestamps mark interval *ends*, with the local UTC offset,
* readings may carry quality flags or be absent.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from http import HTTPStatus
import json
from pathlib import Path
import re
from typing import Any
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)
from yarl import URL

BASE = "https://api.informatika.si/mojelektro/v1"
FIXTURES = Path(__file__).parent / "fixtures"
LJ = ZoneInfo("Europe/Ljubljana")
IMPORT_RT = "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0"
EXPORT_RT = "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0"
TOKEN = "test-token-not-real-0123456789"
METER = "9-12345"


def fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


def default_value(end: datetime, register: str) -> float | None:
    """Deterministic synthetic consumption in kWh per 15 minutes."""
    slot = int(end.timestamp()) // 900
    if register == "import":
        return round(0.05 + (slot % 8) * 0.025, 3)
    return round((slot % 3) * 0.01, 3)


class FakeMojElektro:
    """Configurable fake. Attach with ``fake.attach(aioclient_mock)``."""

    def __init__(self, today: date) -> None:
        self.today = today
        self.token = TOKEN
        self.meters = {METER}
        self.export = False
        self.value: Callable[[datetime, str], float | None] = default_value
        self.missing: set[int] = set()  # interval-end epochs
        self.qualities: dict[int, list[str]] = {}
        self.overrides: dict[tuple[str, int], float] = {}
        # Last available interval end: readings are published with a delay.
        self.available_until = datetime(
            today.year, today.month, today.day, tzinfo=LJ
        )  # i.e. through yesterday
        self.queue: list[tuple[int, str, dict[str, str]]] = []  # forced responses
        self.requests: list[URL] = []

    def attach(self, mock: AiohttpClientMocker) -> None:
        mock.get(re.compile(re.escape(BASE) + r"/.*"), side_effect=self._handle)

    def push(self, status: int, body: str = "", headers: dict[str, str] | None = None) -> None:
        """Force the next response(s) regardless of the request."""
        self.queue.append((status, body, headers or {}))

    def reading_requests(self) -> list[URL]:
        return [u for u in self.requests if u.path.endswith("/meter-readings")]

    async def _handle(self, method: str, url: URL, data: Any) -> AiohttpClientMockResponse:
        self.requests.append(url)
        if self.queue:
            status, body, headers = self.queue.pop(0)
            return AiohttpClientMockResponse(method, url, status=status, text=body, headers=headers)
        path = url.path.removeprefix("/mojelektro/v1")
        if path == "/reading-type":
            return self._json(method, url, fixture("reading_types.json"))
        if path == "/reading-qualities":
            return self._json(method, url, fixture("reading_qualities.json"))
        if path.startswith("/merilno-mesto/"):
            if path.rsplit("/", 1)[1] not in self.meters:
                return self._error(method, url, HTTPStatus.FORBIDDEN, "E.4.003", "Ni dostopa")
            return self._json(method, url, fixture("meter_point.json"))
        if path == "/meter-readings":
            return self._readings(method, url)
        return self._error(method, url, HTTPStatus.NOT_FOUND, "E.4.004", "Ni najdeno")

    def _json(self, method: str, url: URL, payload: Any) -> AiohttpClientMockResponse:
        return AiohttpClientMockResponse(method, url, json=payload)

    def _error(
        self, method: str, url: URL, status: int, code: str, text: str
    ) -> AiohttpClientMockResponse:
        return AiohttpClientMockResponse(
            method, url, status=status, json={"koda": code, "opis": text}
        )

    def _readings(self, method: str, url: URL) -> AiohttpClientMockResponse:
        query = url.query
        options = query.getall("option", [])
        if not options:
            return self._error(method, url, HTTPStatus.BAD_REQUEST, "E.4.001", "Manjka option")
        if query.get("usagePoint") not in self.meters:
            return self._error(method, url, HTTPStatus.FORBIDDEN, "E.4.003", "Ni dostopa")
        start = date.fromisoformat(query["startTime"])
        end = date.fromisoformat(query["endTime"])
        if (end - start).days > 35:
            return self._error(method, url, HTTPStatus.BAD_REQUEST, "E.4.002", "Najvec 35 dni")
        if start < self.today.replace(year=self.today.year - 2):
            return self._error(method, url, HTTPStatus.BAD_REQUEST, "E.4.002", "Najvec 2 leti")
        blocks = []
        for option in options:
            reading_type = option.split("=", 1)[1]
            register = {IMPORT_RT: "import", EXPORT_RT: "export"}.get(reading_type)
            if register is None or (register == "export" and not self.export):
                continue
            blocks.append(
                {
                    "readingType": reading_type,
                    "intervalReadings": self._series(start, end, register),
                }
            )
        return self._json(
            method,
            url,
            {
                "usagePoint": "000000000000000001",
                "messageCreated": datetime.now(UTC).isoformat(),
                "intervalBlocks": blocks,
            },
        )

    def _series(self, start: date, end: date, register: str) -> list[dict[str, Any]]:
        first = datetime(start.year, start.month, start.day, tzinfo=LJ).astimezone(UTC)
        last = datetime(end.year, end.month, end.day, tzinfo=LJ).astimezone(UTC)
        last = min(last, self.available_until.astimezone(UTC))
        out = []
        moment = first + timedelta(minutes=15)
        while moment <= last:
            epoch = int(moment.timestamp())
            local = moment.astimezone(LJ)
            item: dict[str, Any] = {"timestamp": local.isoformat()}
            if epoch not in self.missing:
                value = self.overrides.get((register, epoch), self.value(moment, register))
                if value is not None:
                    item["value"] = f"{value}"
            if epoch in self.qualities:
                item["readingQualities"] = [
                    {"readingQualityType": q} for q in self.qualities[epoch]
                ]
            out.append(item)
            moment += timedelta(minutes=15)
        return out
