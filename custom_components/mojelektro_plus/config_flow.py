"""Config, options, reauthentication and reconfiguration flows."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
import logging
from typing import Any

try:  # Home Assistant 2026.9+ validates schemas with probatio.
    import probatio as vol
except ImportError:  # pragma: no cover - older Home Assistant
    import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    AccessDenied,
    ApiTimeout,
    CannotConnect,
    InvalidAuth,
    InvalidRequest,
    MalformedResponse,
    MojElektroClient,
    MojElektroError,
    NotFound,
    RateLimited,
    ServiceError,
    normalize_meter_id,
)
from .const import (
    CODE_IMPORT,
    CONF_HISTORY_MONTHS,
    CONF_METER_ID,
    CONF_NAME,
    CONF_REFRESH_HOURS,
    CONF_SIDEBAR,
    CONF_TOKEN,
    DEFAULT_HISTORY_MONTHS,
    DEFAULT_REFRESH_HOURS,
    DEFAULT_SIDEBAR,
    DOMAIN,
    FALLBACK_READING_TYPES,
    MAX_HISTORY_MONTHS,
    MAX_REFRESH_HOURS,
    MIN_HISTORY_MONTHS,
    MIN_REFRESH_HOURS,
)
from .timeutil import local_today

_LOGGER = logging.getLogger(__name__)

TOKEN_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
HISTORY_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=MIN_HISTORY_MONTHS,
        max=MAX_HISTORY_MONTHS,
        step=1,
        mode=NumberSelectorMode.BOX,
        unit_of_measurement="months",
    )
)
REFRESH_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=MIN_REFRESH_HOURS,
        max=MAX_REFRESH_HOURS,
        step=0.5,
        mode=NumberSelectorMode.BOX,
        unit_of_measurement="h",
    )
)


def _options_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_HISTORY_MONTHS,
                default=defaults.get(CONF_HISTORY_MONTHS, DEFAULT_HISTORY_MONTHS),
            ): HISTORY_SELECTOR,
            vol.Required(
                CONF_REFRESH_HOURS,
                default=defaults.get(CONF_REFRESH_HOURS, DEFAULT_REFRESH_HOURS),
            ): REFRESH_SELECTOR,
            vol.Required(
                CONF_SIDEBAR, default=defaults.get(CONF_SIDEBAR, DEFAULT_SIDEBAR)
            ): BooleanSelector(),
        }
    )


def _clean_options(user_input: Mapping[str, Any]) -> dict[str, Any]:
    return {
        CONF_HISTORY_MONTHS: int(
            min(MAX_HISTORY_MONTHS, max(MIN_HISTORY_MONTHS, user_input[CONF_HISTORY_MONTHS]))
        ),
        CONF_REFRESH_HOURS: float(
            min(MAX_REFRESH_HOURS, max(MIN_REFRESH_HOURS, user_input[CONF_REFRESH_HOURS]))
        ),
        CONF_SIDEBAR: bool(user_input[CONF_SIDEBAR]),
    }


async def validate_access(hass, token: str, meter_id: str) -> dict[str, Any]:
    """Check the token and meter: meter configuration plus one day of readings.

    Returns non-secret meter facts. Raises a MojElektroError subclass.
    """
    client = MojElektroClient(async_get_clientsession(hass), token, retries=0)
    point = await client.get_meter_point(meter_id)
    today = local_today()
    await client.get_readings(
        meter_id,
        today - timedelta(days=2),
        today - timedelta(days=1),
        [FALLBACK_READING_TYPES[CODE_IMPORT]],
    )
    return point


def _error_key(err: Exception) -> str:
    if isinstance(err, InvalidAuth):
        return "invalid_auth"
    if isinstance(err, (AccessDenied, NotFound)):
        return "meter_inaccessible"
    if isinstance(err, InvalidRequest):
        return "invalid_request"
    if isinstance(err, ApiTimeout):
        return "timeout"
    if isinstance(err, RateLimited):
        return "rate_limited"
    if isinstance(err, (ServiceError, MalformedResponse)):
        return "service_error"
    if isinstance(err, CannotConnect):
        return "cannot_connect"
    return "unknown"


class MojElektroConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up one meter per config entry."""

    VERSION = 1
    MINOR_VERSION = 1

    async def _async_validate(self, token: str, meter_id: str, errors: dict[str, str]) -> bool:
        try:
            await validate_access(self.hass, token, meter_id)
        except MojElektroError as err:
            errors["base"] = _error_key(err)
            _LOGGER.debug("Validation failed: %s", type(err).__name__)
            return False
        except Exception:
            _LOGGER.exception("Unexpected error validating Moj Elektro access")
            errors["base"] = "unknown"
            return False
        return True

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input[CONF_TOKEN]).strip()
            try:
                meter_id = normalize_meter_id(str(user_input[CONF_METER_ID]))
            except ValueError:
                errors[CONF_METER_ID] = "invalid_meter_id"
            else:
                await self.async_set_unique_id(meter_id)
                self._abort_if_unique_id_configured()
                if not token:
                    errors[CONF_TOKEN] = "invalid_auth"
                elif await self._async_validate(token, meter_id, errors):
                    name = str(user_input.get(CONF_NAME) or "").strip()
                    return self.async_create_entry(
                        title=name or f"Moj Elektro {meter_id}",
                        data={CONF_TOKEN: token, CONF_METER_ID: meter_id},
                        options=_clean_options(user_input),
                    )
        schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): TOKEN_SELECTOR,
                vol.Required(CONF_METER_ID): TextSelector(),
                vol.Optional(CONF_NAME): TextSelector(),
            }
        ).extend(_options_schema({}).schema)
        # Never echo the token back into the form.
        suggested = {k: v for k, v in (user_input or {}).items() if k != CONF_TOKEN}
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input[CONF_TOKEN]).strip()
            if await self._async_validate(token, entry.data[CONF_METER_ID], errors):
                return self.async_update_reload_and_abort(entry, data_updates={CONF_TOKEN: token})
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): TOKEN_SELECTOR}),
            description_placeholders={"meter_id": entry.data[CONF_METER_ID]},
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Replace the token. The meter itself cannot change (unique ID)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            token = str(user_input.get(CONF_TOKEN) or "").strip() or entry.data[CONF_TOKEN]
            try:
                meter_id = normalize_meter_id(str(user_input[CONF_METER_ID]))
            except ValueError:
                errors[CONF_METER_ID] = "invalid_meter_id"
            else:
                await self.async_set_unique_id(meter_id)
                self._abort_if_unique_id_mismatch(reason="meter_mismatch")
                if await self._async_validate(token, meter_id, errors):
                    return self.async_update_reload_and_abort(
                        entry, data_updates={CONF_TOKEN: token}
                    )
        schema = vol.Schema(
            {
                vol.Required(CONF_METER_ID, default=entry.data[CONF_METER_ID]): TextSelector(),
                vol.Optional(CONF_TOKEN): TOKEN_SELECTOR,
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> MojElektroOptionsFlow:
        return MojElektroOptionsFlow()


class MojElektroOptionsFlow(OptionsFlowWithReload):
    """History depth, refresh interval and sidebar."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean_options(user_input))
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(self.config_entry.options)
        )
