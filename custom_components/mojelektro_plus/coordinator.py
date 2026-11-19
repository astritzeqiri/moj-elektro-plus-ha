"""Data coordinator: regular refresh, background backfill and range refresh."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import statistics
from .api import (
    AccessDenied,
    InvalidAuth,
    InvalidRequest,
    MojElektroClient,
    MojElektroError,
    NotFound,
    RateLimited,
    ReadingsResult,
    extract_gsrn,
    resolve_reading_types,
)
from .const import (
    BACKFILL_COMPLETE,
    BACKFILL_ERROR,
    BACKFILL_IDLE,
    BACKFILL_RUNNING,
    CONF_HISTORY_MONTHS,
    CONF_METER_ID,
    CONF_REFRESH_HOURS,
    DEFAULT_HISTORY_MONTHS,
    DEFAULT_REFRESH_HOURS,
    DOMAIN,
    EXPORT_AVAILABLE,
    EXPORT_NOT_PROVIDED,
    EXPORT_UNKNOWN,
    FALLBACK_READING_TYPES,
    MIN_REFRESH_HOURS,
    RECENT_WINDOW_DAYS,
    REGISTER_CODES,
    REGISTER_EXPORT,
    REGISTER_IMPORT,
    REGISTERS,
    RETENTION_DAYS,
    SIGNAL_UPDATED,
)
from .data import PeriodTotal, latest_complete_day
from .storage import MeterStore
from .timeutil import (
    add_months,
    batches,
    earliest_allowed,
    from_epoch,
    history_start,
    interval_day,
    local_today,
    month_start,
)

_LOGGER = logging.getLogger(__name__)

CATALOGUE_MAX_AGE = timedelta(days=7)
BACKFILL_PAUSE = 2.0
BACKFILL_MAX_FAILURES = 3
RATE_LIMIT_PAUSE = 60.0

type MojElektroConfigEntry = ConfigEntry[MojElektroCoordinator]


@dataclass(slots=True)
class RegisterSnapshot:
    """Derived values for one register."""

    latest_end: int | None = None
    latest_value: float | None = None
    latest_qualities: tuple[str, ...] = ()
    latest_day: date | None = None
    latest_day_total: PeriodTotal | None = None
    current_month: PeriodTotal | None = None
    current_month_start: date | None = None
    previous_month: PeriodTotal | None = None
    previous_month_start: date | None = None


@dataclass(slots=True)
class Snapshot:
    """Everything entities show; computed from stored intervals."""

    registers: dict[str, RegisterSnapshot] = field(default_factory=dict)
    export_status: str = EXPORT_UNKNOWN
    last_success: datetime | None = None
    computed: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def has_data(self) -> bool:
        snap = self.registers.get(REGISTER_IMPORT)
        return snap is not None and snap.latest_end is not None


def build_snapshot(store: MeterStore, today: date) -> Snapshot:
    """Compute entity values from stored data (pure, no I/O)."""
    snapshot = Snapshot(export_status=store.meta.get("export_status", EXPORT_UNKNOWN))
    if store.meta.get("last_success"):
        snapshot.last_success = datetime.fromisoformat(store.meta["last_success"])
    this_month = month_start(today)
    prev_month = add_months(this_month, -1)
    for register in REGISTERS:
        data = store.registers[register]
        snap = RegisterSnapshot()
        snap.latest_end = data.latest_end()
        if snap.latest_end is not None:
            snap.latest_value, snap.latest_qualities = data.get(snap.latest_end)
            snap.latest_day = latest_complete_day(data, today)
            if snap.latest_day is not None:
                snap.latest_day_total = data.day(snap.latest_day)
            snap.current_month_start = this_month
            snap.current_month = data.period(
                this_month, add_months(this_month, 1) - timedelta(days=1)
            )
            snap.previous_month_start = prev_month
            snap.previous_month = data.period(prev_month, this_month - timedelta(days=1))
        snapshot.registers[register] = snap
    return snapshot


class MojElektroCoordinator(DataUpdateCoordinator[Snapshot]):
    """Fetches and stores readings for one meter."""

    config_entry: MojElektroConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MojElektroConfigEntry,
        client: MojElektroClient,
        store: MeterStore,
    ) -> None:
        hours = max(
            MIN_REFRESH_HOURS,
            float(entry.options.get(CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS)),
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_METER_ID]}",
            update_interval=timedelta(hours=hours),
            always_update=True,
        )
        self.client = client
        self.store = store
        self.meter_id: str = entry.data[CONF_METER_ID]
        self._job: asyncio.Task[Any] | None = None
        self._job_lock = asyncio.Lock()
        self.job_progress: dict[str, Any] | None = None
        self._unloading = False
        self.export_listeners: list[Callable[[], None]] = []

    # ----------------------------------------------------------------- helpers

    @property
    def history_months(self) -> int:
        return int(self.config_entry.options.get(CONF_HISTORY_MONTHS, DEFAULT_HISTORY_MONTHS))

    def today(self) -> date:
        return local_today()

    def reading_type(self, register: str) -> str:
        code = REGISTER_CODES[register]
        return self.store.meta["reading_types"].get(code) or FALLBACK_READING_TYPES[code]

    @callback
    def notify(self) -> None:
        """Recompute values and tell entities and panel subscribers."""
        self.async_set_updated_data(build_snapshot(self.store, self.today()))
        async_dispatcher_send(self.hass, SIGNAL_UPDATED, self.config_entry.entry_id)

    @callback
    def publish_progress(self) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATED, self.config_entry.entry_id)
        self.async_update_listeners()

    # --------------------------------------------------------------- catalogues

    async def _async_refresh_catalogues(self, force: bool = False) -> None:
        meta = self.store.meta
        fetched = meta.get("catalogues_fetched")
        stale = (
            force
            or not fetched
            or datetime.now(UTC) - datetime.fromisoformat(fetched) > CATALOGUE_MAX_AGE
        )
        if not stale:
            return
        try:
            types = await self.client.get_reading_types()
            resolved = resolve_reading_types(types)
            if resolved:
                meta["reading_types"] = resolved
            qualities = await self.client.get_reading_qualities()
            meta["qualities"] = {
                str(q["readingQualityType"]): str(q.get("description") or "")
                for q in qualities
                if q.get("readingQualityType")
            }
            point = await self.client.get_meter_point(self.meter_id)
            meta["meter"] = sanitize_meter_point(point)
            meta["catalogues_fetched"] = datetime.now(UTC).isoformat()
        except (InvalidAuth, AccessDenied, NotFound):
            raise
        except MojElektroError as err:
            # Catalogues are helpful, not essential; readings still work with
            # the documented reading types.
            _LOGGER.warning("Could not refresh Moj Elektro catalogues: %s", err)

    # ---------------------------------------------------------------- fetching

    async def _fetch(self, start: date, end: date) -> int | None:
        """Fetch ``[start, end)`` for all relevant registers and merge.

        Returns the earliest changed interval end, or None.
        """
        registers = [REGISTER_IMPORT]
        export_status = self.store.meta.get("export_status", EXPORT_UNKNOWN)
        if export_status != EXPORT_NOT_PROVIDED:
            registers.append(REGISTER_EXPORT)
        types = {self.reading_type(r): r for r in registers}
        try:
            result = await self.client.get_readings(self.meter_id, start, end, types)
        except InvalidRequest:
            if len(registers) == 1:
                raise
            # Some meters may reject the export register; retry import only.
            types = {self.reading_type(REGISTER_IMPORT): REGISTER_IMPORT}
            result = await self.client.get_readings(self.meter_id, start, end, types)
            self._set_export_status(EXPORT_NOT_PROVIDED)
        return self._merge(result, types)

    def _merge(self, result: ReadingsResult, types: dict[str, str]) -> int | None:
        earliest: int | None = None
        returned: set[str] = set()
        for reading_type, readings in result.blocks.items():
            register = types.get(reading_type)
            if register is None:
                continue
            returned.add(register)
            merged = self.store.registers[register].merge(readings)
            statistics.mark_dirty(self.store.meta["stats"][register], merged.earliest_change)
            if merged.earliest_change is not None and (
                earliest is None or merged.earliest_change < earliest
            ):
                earliest = merged.earliest_change
            if register == REGISTER_EXPORT and any(r.value is not None for r in readings):
                self._set_export_status(EXPORT_AVAILABLE)
        if result.malformed:
            _LOGGER.warning("Skipped %s malformed readings", result.malformed)
        if (
            REGISTER_EXPORT in types.values()
            and REGISTER_IMPORT in returned
            and REGISTER_EXPORT not in returned
            and self.store.meta.get("export_status") == EXPORT_UNKNOWN
        ):
            # A successful response with import data but no export block:
            # the export register is not provided, which is not "zero export".
            self._set_export_status(EXPORT_NOT_PROVIDED)
        return earliest

    def _set_export_status(self, status: str) -> None:
        old = self.store.meta.get("export_status")
        if old == status:
            return
        self.store.meta["export_status"] = status
        if status == EXPORT_AVAILABLE:
            # Let the sensor platform add export entities without a reload.
            for listener in list(self.export_listeners):
                listener()

    def _prune(self) -> None:
        cutoff = int((datetime.now(UTC) - timedelta(days=RETENTION_DAYS)).timestamp())
        for register in REGISTERS:
            dropped = self.store.registers[register].prune_before(cutoff)
            if dropped:
                stats = self.store.meta["stats"][register]
                stats["anchor_sum"] = round(
                    float(stats.get("anchor_sum") or 0.0) + sum(v for _, v in dropped), 6
                )
                stats["anchor_hour"] = max(h for h, _ in dropped)

    async def _import_statistics(self) -> None:
        for register in REGISTERS:
            stats = self.store.meta["stats"][register]
            if stats.get("dirty_from") is None:
                continue
            if (
                register == REGISTER_EXPORT
                and self.store.meta.get("export_status") != EXPORT_AVAILABLE
            ):
                continue
            await statistics.async_import(
                self.hass,
                self.meter_id,
                self.config_entry.title,
                register,
                self.store.registers[register],
                stats,
            )

    # ----------------------------------------------------------------- refresh

    async def _async_update_data(self) -> Snapshot:
        """Refresh the recent overlapping window; schedule backfill if needed."""
        meta = self.store.meta
        meta["last_attempt"] = datetime.now(UTC).isoformat()
        today = self.today()
        start = max(today - timedelta(days=RECENT_WINDOW_DAYS), earliest_allowed(today))
        try:
            await self._async_refresh_catalogues()
            await self._fetch(start, today + timedelta(days=1))
        except InvalidAuth as err:
            meta["last_error"] = "invalid_auth"
            raise ConfigEntryAuthFailed(str(err)) from err
        except (AccessDenied, NotFound) as err:
            meta["last_error"] = "meter_inaccessible"
            self.store.async_schedule_save()
            raise UpdateFailed(f"Meter not accessible: {err}") from err
        except RateLimited as err:
            meta["last_error"] = "rate_limited"
            self.store.async_schedule_save()
            raise UpdateFailed(str(err), retry_after=err.retry_after) from err
        except MojElektroError as err:
            meta["last_error"] = type(err).__name__
            self.store.async_schedule_save()
            raise UpdateFailed(str(err)) from err
        meta["last_success"] = datetime.now(UTC).isoformat()
        meta["last_error"] = None
        self._prune()
        if not self.backfill_running:
            await self._import_statistics()
        self.store.async_schedule_save()
        self.hass.loop.call_soon(self.async_start_backfill)
        async_dispatcher_send(self.hass, SIGNAL_UPDATED, self.config_entry.entry_id)
        return build_snapshot(self.store, today)

    # ---------------------------------------------------------------- backfill

    @property
    def backfill_running(self) -> bool:
        return self._job is not None and not self._job.done()

    def plan_backfill(self) -> list[tuple[date, date]]:
        """Return the month batches still to fetch, newest first."""
        today = self.today()
        target = history_start(today, self.history_months)
        recent = today - timedelta(days=RECENT_WINDOW_DAYS)
        done = set(self.store.meta["backfill"].get("done") or [])
        return [
            (start, end)
            for start, end in reversed(list(batches(target, recent)))
            if f"{start.isoformat()}/{end.isoformat()}" not in done
        ]

    @callback
    def async_start_backfill(self, restart: bool = False) -> bool:
        """Start the background backfill if anything is missing."""
        if self._unloading or self.backfill_running:
            return False
        backfill = self.store.meta["backfill"]
        if restart:
            backfill["done"] = []
            backfill["error"] = None
        elif backfill.get("state") == BACKFILL_ERROR and backfill.get("error") == "invalid_auth":
            return False
        pending = self.plan_backfill()
        backfill["pending"] = [f"{s.isoformat()}/{e.isoformat()}" for s, e in pending]
        if not pending:
            if backfill.get("state") != BACKFILL_COMPLETE:
                backfill["state"] = BACKFILL_COMPLETE
                self.store.async_schedule_save()
            return False
        self._job = self.config_entry.async_create_background_task(
            self.hass,
            self._async_run_job(pending, kind="backfill"),
            f"{DOMAIN} backfill {self.meter_id}",
        )
        return True

    @callback
    def async_refresh_range(self, start: date, end: date) -> bool:
        """Re-fetch a user-selected range ``[start, end]`` in the background."""
        if self._unloading or self.backfill_running:
            return False
        today = self.today()
        start = max(start, earliest_allowed(today))
        end_exclusive = min(end + timedelta(days=1), today + timedelta(days=1))
        if end_exclusive <= start:
            return False
        pending = list(batches(start, end_exclusive))
        self._job = self.config_entry.async_create_background_task(
            self.hass,
            self._async_run_job(pending, kind="range"),
            f"{DOMAIN} range refresh {self.meter_id}",
        )
        return True

    async def _async_run_job(self, pending: list[tuple[date, date]], kind: str) -> None:
        backfill = self.store.meta["backfill"]
        total = len(pending)
        self.job_progress = {"kind": kind, "done": 0, "total": total, "current": None}
        if kind == "backfill":
            backfill["state"] = BACKFILL_RUNNING
            backfill["error"] = None
        self.publish_progress()
        failures = 0
        index = 0
        try:
            while index < len(pending):
                start, end = pending[index]
                self.job_progress["current"] = start.isoformat()
                try:
                    await self._fetch(start, end)
                except InvalidAuth:
                    backfill["error"] = "invalid_auth"
                    if kind == "backfill":
                        backfill["state"] = BACKFILL_ERROR
                    self.config_entry.async_start_reauth(self.hass)
                    return
                except RateLimited as err:
                    failures += 1
                    if failures > BACKFILL_MAX_FAILURES:
                        raise
                    await asyncio.sleep(
                        RATE_LIMIT_PAUSE if err.retry_after is None else err.retry_after
                    )
                    continue
                except MojElektroError:
                    failures += 1
                    if failures > BACKFILL_MAX_FAILURES:
                        raise
                    await asyncio.sleep(BACKFILL_PAUSE * 10 * failures)
                    continue
                failures = 0
                key = f"{start.isoformat()}/{end.isoformat()}"
                if kind == "backfill":
                    done = backfill.setdefault("done", [])
                    if key not in done:
                        done.append(key)
                    backfill["pending"] = [p for p in backfill.get("pending", []) if p != key]
                backfill["updated"] = datetime.now(UTC).isoformat()
                index += 1
                self.job_progress["done"] = index
                self.store.async_schedule_save()
                self.notify()
                if index < len(pending):
                    await asyncio.sleep(BACKFILL_PAUSE)
            if kind == "backfill":
                backfill["state"] = BACKFILL_COMPLETE
            await self._import_statistics()
        except asyncio.CancelledError:
            # Unload or shutdown: progress is persisted, resume next time.
            if kind == "backfill":
                backfill["state"] = BACKFILL_IDLE
            raise
        except MojElektroError as err:
            _LOGGER.warning("Moj Elektro %s stopped: %s", kind, err)
            backfill["error"] = type(err).__name__
            if kind == "backfill":
                backfill["state"] = BACKFILL_ERROR
            # Keep already-fetched data in statistics.
            await self._import_statistics()
        finally:
            self.job_progress = None
            self.store.async_schedule_save()
            if not self._unloading:
                self.notify()

    async def async_shutdown(self) -> None:
        """Stop background work and flush storage (safe to call twice)."""
        if self._unloading:
            return
        self._unloading = True
        if self._job is not None and not self._job.done():
            self._job.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._job
        await self.store.async_save()
        await super().async_shutdown()

    # ------------------------------------------------------------------ status

    def status(self) -> dict[str, Any]:
        """Return non-secret status for the panel and diagnostics."""
        meta = self.store.meta
        backfill = meta["backfill"]
        latest = self.store.registers[REGISTER_IMPORT].latest_end()
        earliest = self.store.registers[REGISTER_IMPORT].earliest_end()
        total = len(backfill.get("done") or []) + len(backfill.get("pending") or [])
        progress = self.job_progress
        return {
            "entry_id": self.config_entry.entry_id,
            "title": self.config_entry.title,
            "meter_id": self.meter_id,
            "export_status": meta.get("export_status", EXPORT_UNKNOWN),
            "latest_reading": from_epoch(latest).isoformat() if latest else None,
            "latest_day": interval_day(latest).isoformat() if latest else None,
            "earliest_reading": from_epoch(earliest).isoformat() if earliest else None,
            "earliest_day": interval_day(earliest).isoformat() if earliest else None,
            "last_success": meta.get("last_success"),
            "last_attempt": meta.get("last_attempt"),
            "last_error": meta.get("last_error"),
            "backfill": {
                "state": backfill.get("state", BACKFILL_IDLE),
                "done": len(backfill.get("done") or []),
                "total": total,
                "error": backfill.get("error"),
            },
            "job": dict(progress) if progress else None,
            "qualities": dict(meta.get("qualities") or {}),
            "history_start": history_start(self.today(), self.history_months).isoformat(),
            "earliest_allowed": earliest_allowed(self.today()).isoformat(),
            "timezone": "Europe/Ljubljana",
        }


def sanitize_meter_point(point: dict[str, Any]) -> dict[str, Any]:
    """Keep only technical, non-personal meter facts (no names or addresses)."""
    gsrn, measurement_gsrn = extract_gsrn(point)
    contract = (
        point.get("pogodbeniPodatki") if isinstance(point.get("pogodbeniPodatki"), dict) else {}
    )
    technical = (
        point.get("tehnicniPodatki") if isinstance(point.get("tehnicniPodatki"), dict) else {}
    )
    return {
        "gsrn": gsrn,
        "measurement_gsrn": measurement_gsrn,
        "meter_type": technical.get("tipStevca"),
        "has_15_minute_data": contract.get("obstoj15MinutneMeritve"),
        "remote_reading": contract.get("daljinskoCitanje"),
        "connection_power_kw": contract.get("prikljucnaMoc"),
        "installed_generation_kw": contract.get("instaliranaMocProizvodnje"),
        "phases": contract.get("steviloFaz"),
    }
