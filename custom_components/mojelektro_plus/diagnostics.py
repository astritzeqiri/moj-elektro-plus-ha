"""Diagnostics with secrets and personal identifiers redacted."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_METER_ID, CONF_TOKEN, REGISTERS
from .coordinator import MojElektroConfigEntry

TO_REDACT = {CONF_TOKEN, CONF_METER_ID, "meter_id", "gsrn", "measurement_gsrn", "title"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MojElektroConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    status = coordinator.status()
    status.pop("qualities", None)
    store = coordinator.store
    registers = {}
    for register in REGISTERS:
        data = store.registers[register]
        registers[register] = {
            "stored_days": len(data.chunks),
            "earliest_end": data.earliest_end(),
            "latest_end": data.latest_end(),
            "stats": store.meta["stats"][register],
        }
    return async_redact_data(
        {
            "entry": {
                "data": dict(entry.data),
                "options": dict(entry.options),
                "title": entry.title,
            },
            "status": status,
            "meter": store.meta.get("meter"),
            "reading_types": store.meta.get("reading_types"),
            "quality_codes": sorted((store.meta.get("qualities") or {}).keys()),
            "backfill": store.meta.get("backfill"),
            "registers": registers,
            "api_requests_this_session": coordinator.client.request_count,
        },
        TO_REDACT,
    )
