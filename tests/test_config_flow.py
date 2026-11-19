"""Config, options, reauth and reconfigure flows."""

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.mojelektro_plus.const import (
    CONF_HISTORY_MONTHS,
    CONF_METER_ID,
    CONF_NAME,
    CONF_REFRESH_HOURS,
    CONF_SIDEBAR,
    CONF_TOKEN,
    DOMAIN,
)

from .conftest import make_entry
from .fake_api import METER, TOKEN

USER_INPUT = {
    CONF_TOKEN: TOKEN,
    CONF_METER_ID: METER,
    CONF_NAME: "Hiša",
    CONF_HISTORY_MONTHS: 12,
    CONF_REFRESH_HOURS: 6,
    CONF_SIDEBAR: True,
}


@pytest.fixture(autouse=True)
def no_setup():
    with patch("custom_components.mojelektro_plus.async_setup_entry", return_value=True) as m:
        yield m


async def _start(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow_creates_entry(hass, fake_api):
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_METER_ID: " 9-12345 "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hiša"
    assert result["data"] == {CONF_TOKEN: TOKEN, CONF_METER_ID: METER}
    assert result["options"] == {
        CONF_HISTORY_MONTHS: 12,
        CONF_REFRESH_HOURS: 6.0,
        CONF_SIDEBAR: True,
    }
    assert result["result"].unique_id == METER
    # Validation read the meter and one day of readings.
    paths = [u.path for u in fake_api.requests]
    assert any(p.endswith("/merilno-mesto/9-12345") for p in paths)
    assert any(p.endswith("/meter-readings") for p in paths)


async def test_default_title_and_refresh_minimum(hass, fake_api):
    from homeassistant.data_entry_flow import InvalidData

    result = await _start(hass)
    data = {**USER_INPUT, CONF_REFRESH_HOURS: 0.1}
    data.pop(CONF_NAME)
    with pytest.raises(InvalidData):
        await hass.config_entries.flow.async_configure(result["flow_id"], data)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**data, CONF_REFRESH_HOURS: 1}
    )
    assert result["title"] == f"Moj Elektro {METER}"
    assert result["options"][CONF_REFRESH_HOURS] == 1.0


@pytest.mark.parametrize(
    ("status", "headers", "error"),
    [
        (401, {}, "invalid_auth"),
        (403, {}, "meter_inaccessible"),
        (404, {}, "meter_inaccessible"),
        (400, {}, "invalid_request"),
        (429, {"Retry-After": "0"}, "rate_limited"),
        (500, {}, "service_error"),
    ],
)
async def test_user_flow_errors(hass, fake_api, status, headers, error):
    result = await _start(hass)
    fake_api.push(status, "", headers)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    # The form never echoes the token back.
    for field in result["data_schema"].schema:
        if str(field) == CONF_TOKEN:
            assert (field.description or {}).get("suggested_value") in (None, "")


async def test_timeout_and_malformed(hass, aioclient_mock, frozen):
    aioclient_mock.get(
        f"https://api.informatika.si/mojelektro/v1/merilno-mesto/{METER}", exc=TimeoutError()
    )
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "timeout"}


async def test_malformed_response(hass, fake_api):
    fake_api.push(200, "<html>maintenance</html>")
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "service_error"}


async def test_invalid_meter_id_never_calls_api(hass, fake_api):
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_METER_ID: "4/93571"}
    )
    assert result["errors"] == {CONF_METER_ID: "invalid_meter_id"}
    assert fake_api.requests == []


async def test_inaccessible_meter(hass, fake_api):
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_METER_ID: "1-1"}
    )
    assert result["errors"] == {"base": "meter_inaccessible"}


async def test_duplicate_meter_aborts(hass, fake_api):
    make_entry().add_to_hass(hass)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_METER_ID: "09-012345"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_second_meter_is_separate_entry(hass, fake_api):
    make_entry().add_to_hass(hass)
    fake_api.meters.add("4-93571")
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**USER_INPUT, CONF_METER_ID: "4-93571"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2


async def test_reauth(hass, fake_api):
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    fake_api.push(401)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_TOKEN: "bad"})
    assert result["errors"] == {"base": "invalid_auth"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_TOKEN: "new-token"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == "new-token"


async def test_reconfigure_token_and_meter_mismatch(hass, fake_api):
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_METER_ID: "4-93571", CONF_TOKEN: "x"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "meter_mismatch"

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_METER_ID: METER, CONF_TOKEN: "rotated"}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TOKEN] == "rotated"

    # Leaving the token empty keeps the current one.
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_METER_ID: METER}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_TOKEN] == "rotated"


async def test_options_flow(hass, fake_api):
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_HISTORY_MONTHS: 18, CONF_REFRESH_HOURS: 12, CONF_SIDEBAR: False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_HISTORY_MONTHS: 18,
        CONF_REFRESH_HOURS: 12.0,
        CONF_SIDEBAR: False,
    }
