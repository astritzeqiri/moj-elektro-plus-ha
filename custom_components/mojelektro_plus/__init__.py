"""Moj Elektro Plus: delayed 15-minute meter data, history and a sidebar page."""

from __future__ import annotations

from datetime import date

try:
    import probatio as vol
except ImportError:  # pragma: no cover - older Home Assistant
    import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from . import statistics
from .api import MojElektroClient
from .const import (
    CONF_METER_ID,
    CONF_SIDEBAR,
    CONF_TOKEN,
    DEFAULT_SIDEBAR,
    DOMAIN,
    SERVICE_REFRESH_RANGE,
)
from .coordinator import MojElektroConfigEntry, MojElektroCoordinator, build_snapshot
from .panel import async_update_panel
from .storage import MeterStore
from .timeutil import local_today
from .websocket import async_register as async_register_websocket

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry_id"): str,
        vol.Required("start_date"): cv.date,
        vol.Required("end_date"): cv.date,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register process-wide APIs once."""
    async_register_websocket(hass)

    async def refresh_range(call: ServiceCall) -> None:
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if entry is None or entry.domain != DOMAIN or not hasattr(entry, "runtime_data"):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="entry_not_loaded"
            )
        start: date = call.data["start_date"]
        end: date = call.data["end_date"]
        if end < start:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_range")
        if not entry.runtime_data.async_refresh_range(start, end):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="busy")

    hass.services.async_register(DOMAIN, SERVICE_REFRESH_RANGE, refresh_range, SERVICE_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MojElektroConfigEntry) -> bool:
    store = MeterStore(hass, entry.entry_id)
    await store.async_load()
    client = MojElektroClient(async_get_clientsession(hass), entry.data[CONF_TOKEN])
    coordinator = MojElektroCoordinator(hass, entry, client, store)
    entry.runtime_data = coordinator

    if store.registers["import"].has_values():
        # Stored data is shown immediately; the network refresh runs in the
        # background so startup is never blocked by the API.
        coordinator.data = build_snapshot(store, local_today())
        entry.async_create_background_task(
            hass, coordinator.async_refresh(), f"{DOMAIN} first refresh"
        )
    else:
        await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if entry.options.get(CONF_SIDEBAR, DEFAULT_SIDEBAR):
        await async_update_panel(hass, including=entry.entry_id)
    else:
        await async_update_panel(hass, excluding=entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MojElektroConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
        await async_update_panel(hass, excluding=entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: MojElektroConfigEntry) -> None:
    """Delete the meter's local history and its imported statistics."""
    await MeterStore(hass, entry.entry_id).async_remove()
    await statistics.async_clear(hass, entry.data[CONF_METER_ID])
