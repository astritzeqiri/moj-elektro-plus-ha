"""API client: request format, limits and error handling."""

from datetime import date
import json

import aiohttp
import pytest

from custom_components.mojelektro_plus.api import (
    AccessDenied,
    ApiTimeout,
    InvalidAuth,
    InvalidRequest,
    MalformedResponse,
    MojElektroClient,
    NotFound,
    RateLimited,
    ServiceError,
    extract_gsrn,
    normalize_meter_id,
    parse_readings,
    parse_retry_after,
    resolve_reading_types,
)

from .fake_api import IMPORT_RT, METER, TOKEN, FakeMojElektro, fixture


@pytest.fixture
def client(hass, fake_api):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    return MojElektroClient(async_get_clientsession(hass), TOKEN, retries=2, backoff=0)


async def test_request_format_matches_verified_call(client, fake_api, aioclient_mock):
    result = await client.get_readings(METER, date(2026, 1, 1), date(2026, 2, 1), [IMPORT_RT])
    url = fake_api.reading_requests()[-1]
    assert url.query["usagePoint"] == METER
    assert url.query["startTime"] == "2026-01-01"
    assert url.query["endTime"] == "2026-02-01"
    assert url.query.getall("option") == [f"ReadingType={IMPORT_RT}"]
    headers = aioclient_mock.mock_calls[-1][3]
    assert headers["X-API-TOKEN"] == TOKEN
    readings = result.blocks[IMPORT_RT]
    # A complete January needs February 1 as the (exclusive) end:
    # 31 days x 96 intervals, the last one ending at midnight on 1 February.
    assert len(readings) == 31 * 96
    assert readings[-1].end == int(
        __import__("datetime").datetime.fromisoformat("2026-02-01T00:00:00+01:00").timestamp()
    )


async def test_rejects_ranges_over_35_days_without_calling(client, fake_api):
    with pytest.raises(ValueError):
        await client.get_readings(METER, date(2026, 1, 1), date(2026, 2, 6), [IMPORT_RT])
    with pytest.raises(ValueError):
        await client.get_readings(METER, date(2026, 1, 1), date(2026, 1, 1), [IMPORT_RT])
    with pytest.raises(ValueError):
        await client.get_readings(METER, date(2026, 1, 1), date(2026, 1, 2), [])
    assert fake_api.requests == []


@pytest.mark.parametrize(
    ("status", "body", "error"),
    [
        (401, "", InvalidAuth),
        (403, json.dumps({"koda": "E.4.003", "opis": "Ni dostopa"}), AccessDenied),
        (
            404,
            json.dumps({"zahteva": "x", "errors": [{"koda": "E.4.004", "opis": "Ni"}]}),
            NotFound,
        ),
        (400, "not json at all", InvalidRequest),
    ],
)
async def test_http_errors_structured_and_empty(client, fake_api, status, body, error):
    fake_api.push(status, body)
    with pytest.raises(error) as info:
        await client.get_meter_point(METER)
    assert TOKEN not in str(info.value)
    if status == 403:
        assert "E.4.003" in str(info.value)


async def test_rate_limit_respects_retry_after_then_succeeds(client, fake_api):
    fake_api.push(429, "", {"Retry-After": "0"})
    point = await client.get_meter_point(METER)
    assert point["identifikator"]["gsrn"] == "000000000000000001"
    assert len(fake_api.requests) == 2


async def test_rate_limit_gives_up_after_retries(client, fake_api):
    for _ in range(3):
        fake_api.push(429, "", {"Retry-After": "0"})
    with pytest.raises(RateLimited):
        await client.get_reading_types()


async def test_server_errors_are_retried(client, fake_api):
    fake_api.push(503, "")
    fake_api.push(500, json.dumps({"koda": "E.5.000", "opis": "Napaka"}))
    assert await client.get_reading_types()
    for _ in range(3):
        fake_api.push(502, "")
    with pytest.raises(ServiceError):
        await client.get_reading_types()


async def test_timeout_maps_to_api_timeout(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.get("https://api.informatika.si/mojelektro/v1/reading-type", exc=TimeoutError())
    client = MojElektroClient(async_get_clientsession(hass), TOKEN, retries=1, backoff=0)
    with pytest.raises(ApiTimeout):
        await client.get_reading_types()
    assert aioclient_mock.call_count == 2


async def test_connection_error_is_not_leaking_token(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    aioclient_mock.get(
        "https://api.informatika.si/mojelektro/v1/reading-type", exc=aiohttp.ClientError(TOKEN)
    )
    client = MojElektroClient(async_get_clientsession(hass), TOKEN, retries=0)
    with pytest.raises(Exception) as info:
        await client.get_reading_types()
    assert TOKEN not in str(info.value)
    assert TOKEN not in repr(client)


async def test_malformed_and_empty_success_bodies(client, fake_api):
    fake_api.push(200, "")
    with pytest.raises(MalformedResponse):
        await client.get_reading_types()
    fake_api.push(200, json.dumps({"not": "a list"}))
    with pytest.raises(MalformedResponse):
        await client.get_reading_types()
    fake_api.push(200, json.dumps({"intervalBlocks": "nope"}))
    with pytest.raises(MalformedResponse):
        await client.get_readings(METER, date(2026, 1, 1), date(2026, 1, 2), [IMPORT_RT])


def test_parse_readings_missing_zero_and_quality():
    result = parse_readings(
        {
            "intervalBlocks": [
                {
                    "readingType": IMPORT_RT,
                    "intervalReadings": [
                        {"timestamp": "2026-01-01T00:15:00+01:00", "value": "0"},
                        {"timestamp": "2026-01-01T00:30:00+01:00"},
                        {
                            "timestamp": "2026-01-01T00:45:00+01:00",
                            "value": "0.250",
                            "readingQualities": [{"readingQualityType": "TEST.ESTIMATED"}],
                        },
                        {"timestamp": "garbage", "value": "1"},
                        {"timestamp": "2026-01-01T01:00:00+01:00", "value": "NaN"},
                    ],
                }
            ]
        }
    )
    readings = result.blocks[IMPORT_RT]
    assert [r.value for r in readings] == [0.0, None, 0.25]
    assert readings[2].qualities == ("TEST.ESTIMATED",)
    assert result.malformed == 2
    assert parse_readings({}).blocks == {}


def test_meter_ids_reading_types_and_gsrn():
    assert normalize_meter_id(" 4-93571 ") == "4-93571"
    assert normalize_meter_id("04-093571") == "4-93571"
    for bad in ("", "493571", "4_93571", "abc-1", "123-4"):
        with pytest.raises(ValueError):
            normalize_meter_id(bad)
    resolved = resolve_reading_types(fixture("reading_types.json"))
    assert resolved == {
        "A+": "32.0.2.4.1.2.12.0.0.0.0.0.0.0.0.3.72.0",
        "A-": "32.0.2.4.19.2.12.0.0.0.0.0.0.0.0.3.72.0",
    }
    assert extract_gsrn(fixture("meter_point.json")) == (
        "000000000000000001",
        "000000000000000002",
    )


def test_retry_after_parsing():
    assert parse_retry_after("12") == 12
    assert parse_retry_after("99999") == 300
    assert parse_retry_after(None) is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0
    assert parse_retry_after("soon") is None


async def test_fake_enforces_limits(hass, fake_api: FakeMojElektro):
    # Sanity check that the fake mirrors the confirmed API behaviour.
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    raw = MojElektroClient(async_get_clientsession(hass), TOKEN, retries=0)
    with pytest.raises(InvalidRequest):
        await raw.get_readings(METER, date(2023, 1, 1), date(2023, 2, 1), [IMPORT_RT])
