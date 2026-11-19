"""Versioned persistent storage for one meter (one config entry)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    REGISTERS,
    STORAGE_MINOR_VERSION,
    STORAGE_SAVE_DELAY,
    STORAGE_VERSION,
)
from .data import RegisterData


class _MigratingStore(Store[dict[str, Any]]):
    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        # Version 1.1 is the first format; future migrations go here.
        if old_major_version > STORAGE_VERSION:
            raise NotImplementedError
        return old_data


def default_meta() -> dict[str, Any]:
    """Return the metadata of a new store."""
    return {
        "reading_types": {},
        "qualities": {},
        "meter": {},
        "export_status": "unknown",
        "last_success": None,
        "last_attempt": None,
        "last_error": None,
        "backfill": {
            "state": "idle",
            "target_start": None,
            "done": [],
            "pending": [],
            "error": None,
            "updated": None,
        },
        # Statistics bookkeeping per register.
        "stats": {
            register: {"anchor_hour": None, "anchor_sum": 0.0, "dirty_from": None}
            for register in REGISTERS
        },
    }


class MeterStore:
    """Interval data plus metadata, saved with Home Assistant's Store helper.

    The JSON is written by the Store helper off the event loop. The token is
    never stored here; it lives only in the config entry.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = _MigratingStore(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.{entry_id}",
            minor_version=STORAGE_MINOR_VERSION,
            private=True,
        )
        self.registers: dict[str, RegisterData] = {r: RegisterData() for r in REGISTERS}
        self.meta: dict[str, Any] = default_meta()

    async def async_load(self) -> None:
        raw = await self._store.async_load()
        if not raw:
            return
        self.load_dict(raw)

    def load_dict(self, raw: dict[str, Any]) -> None:
        meta = default_meta()
        stored = raw.get("meta") or {}
        for key, value in stored.items():
            if key in ("backfill", "stats") and isinstance(value, dict):
                for sub, subvalue in value.items():
                    if isinstance(meta[key].get(sub), dict) and isinstance(subvalue, dict):
                        meta[key][sub].update(subvalue)
                    else:
                        meta[key][sub] = subvalue
            else:
                meta[key] = value
        self.meta = meta
        for register in REGISTERS:
            self.registers[register] = RegisterData.from_json(
                (raw.get("registers") or {}).get(register) or {}
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "registers": {r: d.as_json() for r, d in self.registers.items()},
        }

    def async_schedule_save(self) -> None:
        self._store.async_delay_save(self.as_dict, STORAGE_SAVE_DELAY)

    async def async_save(self) -> None:
        await self._store.async_save(self.as_dict())

    async def async_remove(self) -> None:
        await self._store.async_remove()
