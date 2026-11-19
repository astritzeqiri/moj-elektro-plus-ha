"""Constants for Moj Elektro Plus."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "mojelektro_plus"
VERSION: Final = "0.1.0"
NAME: Final = "Moj Elektro Plus"

API_BASE_URL: Final = "https://api.informatika.si/mojelektro/v1"

CONF_TOKEN: Final = "api_token"
CONF_METER_ID: Final = "meter_id"
CONF_NAME: Final = "name"
CONF_HISTORY_MONTHS: Final = "history_months"
CONF_REFRESH_HOURS: Final = "refresh_hours"
CONF_SIDEBAR: Final = "sidebar"

DEFAULT_HISTORY_MONTHS: Final = 12
MIN_HISTORY_MONTHS: Final = 0
# The API only serves readings up to two years into the past.
MAX_HISTORY_MONTHS: Final = 24
DEFAULT_REFRESH_HOURS: Final = 6.0
MIN_REFRESH_HOURS: Final = 1.0
MAX_REFRESH_HOURS: Final = 24.0
DEFAULT_SIDEBAR: Final = True

# Moj Elektro measurement periods.
INTERVAL: Final = timedelta(minutes=15)
INTERVAL_SECONDS: Final = 900
INTERVALS_PER_HOUR: Final = 4
TIMEZONE: Final = "Europe/Ljubljana"

# API limits, confirmed against the live service.
MAX_REQUEST_DAYS: Final = 35
MAX_HISTORY_DAYS: Final = 730

# How many days before "today" every regular refresh re-reads, to pick up
# late readings and corrections.
RECENT_WINDOW_DAYS: Final = 7

# Persisted intervals older than this are pruned. Above the two-year API
# limit so a re-fetch can never reach data that was already pruned.
RETENTION_DAYS: Final = 800

# Register codes ("oznaka") from GET /reading-type.
CODE_IMPORT: Final = "A+"
CODE_EXPORT: Final = "A-"
# Fallbacks if the reading-type catalogue cannot be fetched. Both values are
# stated by the official OpenAPI specification; the import one was also
# verified by a successful request.
FALLBACK_READING_TYPES: Final = {
    CODE_IMPORT: "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0",
    CODE_EXPORT: "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0",
}

REGISTER_IMPORT: Final = "import"
REGISTER_EXPORT: Final = "export"
REGISTERS: Final = (REGISTER_IMPORT, REGISTER_EXPORT)
REGISTER_CODES: Final = {REGISTER_IMPORT: CODE_IMPORT, REGISTER_EXPORT: CODE_EXPORT}

# Export availability.
EXPORT_UNKNOWN: Final = "unknown"
EXPORT_AVAILABLE: Final = "available"
EXPORT_NOT_PROVIDED: Final = "not_provided"

# Backfill states.
BACKFILL_IDLE: Final = "idle"
BACKFILL_RUNNING: Final = "running"
BACKFILL_COMPLETE: Final = "complete"
BACKFILL_ERROR: Final = "error"
BACKFILL_PAUSED: Final = "paused"

PANEL_URL: Final = "moj-elektro"
PANEL_COMPONENT: Final = "mojelektro-plus-panel"
PANEL_ICON: Final = "mdi:transmission-tower"
STATIC_URL: Final = f"/{DOMAIN}_static"
PANEL_FILE: Final = "mojelektro-panel.js"

STORAGE_VERSION: Final = 1
STORAGE_MINOR_VERSION: Final = 1
STORAGE_SAVE_DELAY: Final = 15

SIGNAL_UPDATED: Final = f"{DOMAIN}_updated"
EVENT_PROGRESS: Final = f"{DOMAIN}_progress"

SERVICE_REFRESH_RANGE: Final = "refresh_range"
