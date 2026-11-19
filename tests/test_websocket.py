"""Sidebar-page backend: authenticated access, aggregation, CSV, redaction."""

from __future__ import annotations

import csv
import io
import json

from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)

from custom_components.mojelektro_plus.const import DOMAIN

from .conftest import make_entry
from .fake_api import METER, TOKEN


@pytest.fixture
async def loaded(hass, fake_api):
    fake_api.export = True
    entry = make_entry(history=1)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return entry


async def _call(client, payload):
    await client.send_json_auto_id(payload)
    return await client.receive_json()


async def test_meters_list_has_no_secrets(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    msg = await _call(client, {"type": f"{DOMAIN}/meters"})
    assert msg["success"]
    meters = msg["result"]["meters"]
    assert meters[0]["meter_id"] == METER
    assert meters[0]["latest_day"] == "2026-04-09"
    assert meters[0]["export_status"] == "available"
    assert meters[0]["backfill"]["state"] == "complete"
    assert TOKEN not in json.dumps(msg)


async def test_auto_resolution_and_summary(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    base = {"type": f"{DOMAIN}/data", "entry_id": loaded.entry_id}
    day = await _call(client, {**base, "start": "2026-04-09", "end": "2026-04-09"})
    assert day["success"], day
    result = day["result"]
    assert result["resolution"] == "interval"
    assert len(result["points"]) == 96
    assert result["timezone"] == "Europe/Ljubljana"
    summary = result["summary"]
    assert summary["import"]["complete"] is True
    assert summary["export"]["total"] is not None
    peak = summary["peak"]
    assert peak["power_kw"] == pytest.approx(peak["energy_kwh"] * 4)

    month = await _call(client, {**base, "start": "2026-03-01", "end": "2026-03-31"})
    assert month["result"]["resolution"] == "day"
    points = month["result"]["points"]
    assert len(points) == 31
    dst = next(p for p in points if p["start"] == "2026-03-29")
    assert dst["expected"] == 92 and dst["complete"]

    year = await _call(client, {**base, "start": "2025-04-11", "end": "2026-04-09"})
    assert year["result"]["resolution"] == "month"
    assert len(year["result"]["points"]) == 13
    # Months before the backfilled history are missing, not zero.
    assert year["result"]["points"][0]["import"] is None
    assert year["result"]["summary"]["import"]["complete"] is False


async def test_partial_period_and_daily_average(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    msg = await _call(
        client,
        {
            "type": f"{DOMAIN}/data",
            "entry_id": loaded.entry_id,
            "start": "2026-04-01",
            "end": "2026-04-30",
        },
    )
    summary = msg["result"]["summary"]
    assert summary["complete_days"] == 9
    assert summary["import"]["complete"] is False
    assert summary["import"]["coverage"] == pytest.approx(30.0)
    assert summary["daily_average"] == pytest.approx(summary["import"]["total"] / 9, abs=1e-3)


@pytest.mark.parametrize(
    "payload",
    [
        {"start": "2026-04-09", "end": "2026-04-01"},
        {"start": "not-a-date", "end": "2026-04-01"},
        {"start": "2020-01-01", "end": "2026-04-01"},
        {"start": "2026-01-01", "end": "2026-03-01", "resolution": "interval"},
    ],
)
async def test_invalid_ranges(hass, loaded, hass_ws_client, payload):
    client = await hass_ws_client(hass)
    msg = await _call(client, {"type": f"{DOMAIN}/data", "entry_id": loaded.entry_id, **payload})
    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_format"


async def test_unknown_meter(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    msg = await _call(
        client,
        {"type": f"{DOMAIN}/data", "entry_id": "nope", "start": "2026-04-01", "end": "2026-04-02"},
    )
    assert msg["error"]["code"] == "not_found"


async def test_csv_export(hass, loaded, hass_ws_client):
    client = await hass_ws_client(hass)
    msg = await _call(
        client,
        {
            "type": f"{DOMAIN}/csv",
            "entry_id": loaded.entry_id,
            "start": "2026-03-29",
            "end": "2026-03-29",
            "resolution": "interval",
        },
    )
    assert msg["success"]
    rows = list(csv.DictReader(io.StringIO(msg["result"]["csv"])))
    assert len(rows) == 92  # DST day
    first = rows[0]
    assert first["interval_end_europe_ljubljana"] == "2026-03-29T00:15:00+01:00"
    assert first["interval_end_utc"] == "2026-03-28T23:15:00+00:00"
    assert first["import_status"] == "ok"
    assert "export_kwh" in first
    assert rows[-1]["interval_end_europe_ljubljana"] == "2026-03-30T00:00:00+02:00"
    assert msg["result"]["filename"].endswith(".csv")

    monthly = await _call(
        client,
        {
            "type": f"{DOMAIN}/csv",
            "entry_id": loaded.entry_id,
            "start": "2026-02-01",
            "end": "2026-04-30",
            "resolution": "month",
        },
    )
    rows = list(csv.DictReader(io.StringIO(monthly["result"]["csv"])))
    # History reaches back to 1 March: February is missing, not zero.
    assert [r["import_complete"] for r in rows] == ["no", "yes", "no"]
    assert rows[0]["import_kwh"] == "" and rows[0]["import_intervals_present"] == "0"
    assert float(rows[1]["import_kwh"]) > 0


async def test_csv_marks_missing(hass, fake_api, hass_ws_client):
    from datetime import date

    from custom_components.mojelektro_plus.timeutil import interval_end_epochs

    ends = list(interval_end_epochs(date(2026, 4, 9)))
    fake_api.missing = {ends[0]}
    fake_api.qualities = {ends[1]: ["TEST.ESTIMATED"]}
    entry = make_entry(history=0)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    client = await hass_ws_client(hass)
    msg = await _call(
        client,
        {
            "type": f"{DOMAIN}/csv",
            "entry_id": entry.entry_id,
            "start": "2026-04-09",
            "end": "2026-04-09",
            "resolution": "interval",
        },
    )
    rows = list(csv.DictReader(io.StringIO(msg["result"]["csv"])))
    assert rows[0]["import_status"] == "missing" and rows[0]["import_kwh"] == ""
    assert rows[1]["import_status"] == "flagged"
    assert rows[1]["import_quality_flags"] == "TEST.ESTIMATED"


async def test_refresh_and_backfill_require_admin(hass, loaded, hass_ws_client, hass_admin_user):
    hass_admin_user.groups = []
    client = await hass_ws_client(hass)
    for payload in (
        {"type": f"{DOMAIN}/refresh", "entry_id": loaded.entry_id},
        {"type": f"{DOMAIN}/backfill", "entry_id": loaded.entry_id},
    ):
        msg = await _call(client, payload)
        assert not msg["success"]
        assert msg["error"]["code"] == "unauthorized"
    # Reading data is allowed for any signed-in user.
    msg = await _call(client, {"type": f"{DOMAIN}/meters"})
    assert msg["success"]


async def test_admin_refresh_range_and_subscribe(hass, loaded, hass_ws_client, fake_api):
    client = await hass_ws_client(hass)
    await client.send_json({"id": 10, "type": f"{DOMAIN}/subscribe"})
    assert (await client.receive_json())["success"]
    count = len(fake_api.reading_requests())
    await client.send_json(
        {
            "id": 11,
            "type": f"{DOMAIN}/refresh",
            "entry_id": loaded.entry_id,
            "start": "2026-03-01",
            "end": "2026-03-05",
        }
    )
    result = event = None
    while result is None or event is None:
        msg = await client.receive_json()
        if msg["id"] == 11:
            result = msg
        elif msg["id"] == 10 and msg["type"] == "event":
            event = msg
    assert result["success"] and result["result"]["started"]
    assert event["event"]["entry_id"] == loaded.entry_id
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(fake_api.reading_requests()) > count


async def test_diagnostics_redact_token_and_ids(hass, loaded, hass_client):
    assert await async_setup_component(hass, "diagnostics", {})
    diag = await get_diagnostics_for_config_entry(hass, hass_client, loaded)
    text = json.dumps(diag)
    assert TOKEN not in text
    assert METER not in text
    assert "000000000000000001" not in text
    assert diag["entry"]["data"]["api_token"] == "**REDACTED**"


async def test_panel_module_is_served(hass, loaded, hass_client):
    client = await hass_client()
    resp = await client.get("/mojelektro_plus_static/mojelektro-panel.js")
    assert resp.status == 200
    body = await resp.text()
    assert "mojelektro-plus-panel" in body
    assert TOKEN not in body
