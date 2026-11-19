"""Authenticated WebSocket commands used by the sidebar page.

Every command runs on Home Assistant's authenticated WebSocket connection.
Reading data needs a signed-in user; refresh and backfill need an
administrator. Responses never contain the Moj Elektro token.
"""

from __future__ import annotations

from datetime import date
from typing import Any

try:
    import probatio as vol
except ImportError:  # pragma: no cover - older Home Assistant
    import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import views
from .const import DOMAIN, EXPORT_AVAILABLE, SIGNAL_UPDATED
from .coordinator import MojElektroCoordinator


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_meters, ws_data, ws_csv, ws_refresh, ws_backfill, ws_subscribe):
        websocket_api.async_register_command(hass, command)


def _coordinators(hass: HomeAssistant) -> list[MojElektroCoordinator]:
    return [
        entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
        and isinstance(getattr(entry, "runtime_data", None), MojElektroCoordinator)
    ]


def _coordinator(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> MojElektroCoordinator | None:
    for coordinator in _coordinators(hass):
        if coordinator.config_entry.entry_id == msg["entry_id"]:
            return coordinator
    connection.send_error(msg["id"], "not_found", "Meter not found or not loaded.")
    return None


def _range(
    connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> tuple[date, date] | None:
    try:
        return views.parse_range(msg["start"], msg["end"])
    except views.RangeError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return None


@websocket_api.websocket_command({"type": f"{DOMAIN}/meters"})
@callback
def ws_meters(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """List configured meters with non-secret status."""
    connection.send_result(
        msg["id"],
        {
            "meters": [
                c.status() for c in sorted(_coordinators(hass), key=lambda c: c.config_entry.title)
            ]
        },
    )


DATA_SCHEMA = {
    vol.Required("entry_id"): str,
    vol.Required("start"): str,
    vol.Required("end"): str,
    vol.Optional("resolution", default="auto"): vol.In(views.RESOLUTIONS),
}


@websocket_api.websocket_command({"type": f"{DOMAIN}/data", **DATA_SCHEMA})
@websocket_api.async_response
async def ws_data(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Aggregated chart data for a date range (inclusive, Ljubljana days)."""
    coordinator = _coordinator(hass, connection, msg)
    if coordinator is None:
        return
    rng = _range(connection, msg)
    if rng is None:
        return
    first, last = rng
    try:
        resolution = views.choose_resolution(first, last, msg["resolution"])
    except views.RangeError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    include_export = coordinator.store.meta.get("export_status") == EXPORT_AVAILABLE
    registers = coordinator.store.registers
    # Aggregation over up to two years takes some milliseconds; keep it off
    # the event loop. The data structures are only mutated on the loop, so
    # take a snapshot copy first.
    snapshot = {k: _copy(v) for k, v in registers.items()}

    def compute() -> dict[str, Any]:
        return {
            "summary": views.summarize(snapshot, include_export, first, last),
            "points": views.series(snapshot, include_export, first, last, resolution),
        }

    result = await hass.async_add_executor_job(compute)
    connection.send_result(
        msg["id"],
        {
            "entry_id": coordinator.config_entry.entry_id,
            "start": first.isoformat(),
            "end": last.isoformat(),
            "resolution": resolution,
            "timezone": "Europe/Ljubljana",
            "unit": "kWh",
            "export_status": coordinator.store.meta.get("export_status"),
            "status": coordinator.status(),
            **result,
        },
    )


def _copy(register):
    from .data import Chunk, RegisterData

    clone = RegisterData()
    clone.chunks = {
        day: Chunk(list(chunk.values), dict(chunk.qualities))
        for day, chunk in register.chunks.items()
    }
    return clone


@websocket_api.websocket_command({"type": f"{DOMAIN}/csv", **DATA_SCHEMA})
@websocket_api.async_response
async def ws_csv(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    coordinator = _coordinator(hass, connection, msg)
    if coordinator is None:
        return
    rng = _range(connection, msg)
    if rng is None:
        return
    first, last = rng
    resolution = msg["resolution"]
    if resolution == "auto":
        resolution = views.choose_resolution(first, last, "auto")
    include_export = coordinator.store.meta.get("export_status") == EXPORT_AVAILABLE
    snapshot = {k: _copy(v) for k, v in coordinator.store.registers.items()}
    try:
        text = await hass.async_add_executor_job(
            views.to_csv, snapshot, include_export, first, last, resolution
        )
    except views.RangeError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    filename = (
        f"mojelektro_{coordinator.meter_id}_{first.isoformat()}_{last.isoformat()}_{resolution}.csv"
    )
    connection.send_result(msg["id"], {"filename": filename, "csv": text})


@websocket_api.websocket_command(
    {
        "type": f"{DOMAIN}/refresh",
        vol.Required("entry_id"): str,
        vol.Optional("start"): str,
        vol.Optional("end"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_refresh(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Refresh the recent window, or re-fetch a selected range in background."""
    coordinator = _coordinator(hass, connection, msg)
    if coordinator is None:
        return
    if "start" in msg or "end" in msg:
        rng = _range(connection, {**msg, "start": msg.get("start"), "end": msg.get("end")})
        if rng is None:
            return
        started = coordinator.async_refresh_range(*rng)
        if not started:
            connection.send_error(
                msg["id"], "busy", "Another download is running, or the range is unavailable."
            )
            return
        connection.send_result(msg["id"], {"started": True})
        return
    await coordinator.async_request_refresh()
    connection.send_result(msg["id"], {"started": True})


@websocket_api.websocket_command(
    {
        "type": f"{DOMAIN}/backfill",
        vol.Required("entry_id"): str,
        vol.Optional("restart", default=False): bool,
    }
)
@websocket_api.require_admin
@callback
def ws_backfill(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    coordinator = _coordinator(hass, connection, msg)
    if coordinator is None:
        return
    started = coordinator.async_start_backfill(restart=msg["restart"])
    connection.send_result(msg["id"], {"started": started})


@websocket_api.websocket_command({"type": f"{DOMAIN}/subscribe"})
@callback
def ws_subscribe(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Push {entry_id} whenever a meter's data or progress changes."""

    @callback
    def forward(entry_id: str) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], {"entry_id": entry_id}))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_UPDATED, forward)
    connection.send_result(msg["id"])
