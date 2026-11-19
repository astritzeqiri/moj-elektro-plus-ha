"""The shared "Moj Elektro" sidebar page.

One panel serves every meter. It exists while at least one loaded entry
has the sidebar option enabled and is removed with the last such entry.
"""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SIDEBAR,
    DEFAULT_SIDEBAR,
    DOMAIN,
    PANEL_COMPONENT,
    PANEL_FILE,
    PANEL_ICON,
    PANEL_URL,
    STATIC_URL,
    VERSION,
)

FRONTEND_DIR = Path(__file__).parent / "frontend"
DATA_PANEL = f"{DOMAIN}_panel_registered"
DATA_STATIC = f"{DOMAIN}_static_registered"


async def async_register_static(hass: HomeAssistant) -> None:
    """Serve the bundled page once per Home Assistant process."""
    if hass.data.get(DATA_STATIC):
        return
    hass.data[DATA_STATIC] = True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), True)]
    )


def _wanted(hass: HomeAssistant, excluding: str | None) -> bool:
    return any(
        entry.entry_id != excluding
        and entry.state is ConfigEntryState.LOADED
        and entry.options.get(CONF_SIDEBAR, DEFAULT_SIDEBAR)
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


async def async_update_panel(
    hass: HomeAssistant, *, including: str | None = None, excluding: str | None = None
) -> None:
    """Register or remove the panel to match the loaded entries.

    ``including`` is an entry being set up (not yet LOADED) whose sidebar
    option is enabled; ``excluding`` is an entry being unloaded.
    """
    wanted = including is not None or _wanted(hass, excluding)
    registered = hass.data.get(DATA_PANEL, False)
    if wanted and not registered:
        await async_register_static(hass)
        built = await hass.async_add_executor_job(_bundle_mtime)
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=PANEL_COMPONENT,
            sidebar_title="Moj Elektro",
            sidebar_icon=PANEL_ICON,
            module_url=f"{STATIC_URL}/{PANEL_FILE}?v={VERSION}.{built}",
            require_admin=False,
            config={"domain": DOMAIN},
        )
        hass.data[DATA_PANEL] = True
    elif not wanted and registered:
        frontend.async_remove_panel(hass, PANEL_URL, warn_if_unknown=False)
        hass.data[DATA_PANEL] = False


def _bundle_mtime() -> int:
    try:
        return int((FRONTEND_DIR / PANEL_FILE).stat().st_mtime)
    except OSError:
        return 0
