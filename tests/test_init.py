"""Setup, entities, backfill, persistence, statistics and unload."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
import json
from unittest.mock import patch
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.mojelektro_plus.const import DOMAIN, PANEL_URL
from custom_components.mojelektro_plus.timeutil import interval_end_epochs

from .conftest import TODAY, make_entry
from .fake_api import TOKEN, FakeMojElektro

LJ = ZoneInfo("Europe/Ljubljana")


async def setup(hass, entry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


def state(hass, key: str):
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"9-12345_{key}")
    assert entity_id, key
    return hass.states.get(entity_id)


def panels(hass) -> dict:
    return hass.data.get("frontend_panels", {})


async def test_setup_entities_and_values(hass, fake_api: FakeMojElektro):
    entry = make_entry(history=1)
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    # Latest interval: ends at local midnight starting today (delayed data).
    latest = state(hass, "import_latest_interval")
    end = datetime(2026, 4, 10, tzinfo=LJ)
    assert latest.attributes["interval_end"] == end.astimezone(UTC).isoformat()
    assert latest.attributes["delayed_data"] is True
    assert latest.attributes.get("state_class") is None
    value = float(latest.state)
    power = float(state(hass, "import_latest_average_power").state)
    assert power == pytest.approx(value * 4)
    assert state(hass, "import_latest_average_power").attributes["unit_of_measurement"] == "kW"

    day = state(hass, "import_latest_day")
    assert day.attributes["date"] == "2026-04-09"
    assert day.attributes["complete"] is True
    assert day.attributes["intervals_expected"] == 96
    assert day.attributes.get("state_class") is None

    month = state(hass, "import_current_month")
    assert month.attributes["month"] == "2026-04"
    assert month.attributes["partial"] is True
    assert month.attributes["intervals_present"] == 9 * 96
    assert month.attributes["intervals_expected"] == 30 * 96

    previous = state(hass, "import_previous_month")
    # March 2026 has a 92-interval DST day; backfill delivered all of it.
    assert previous.attributes["intervals_expected"] == 31 * 96 - 4
    assert previous.attributes["complete"] is True

    assert state(hass, "latest_reading").state == end.astimezone(UTC).isoformat()
    assert state(hass, "backfill").state == "complete"
    # No export register from this meter: no export entities.
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("sensor", DOMAIN, "9-12345_export_latest_day") is None
    # No large arrays and no token anywhere in the state machine.
    for st in hass.states.async_all():
        assert TOKEN not in json.dumps(st.as_dict(), default=str)
        assert len(json.dumps(st.attributes, default=str)) < 2000


async def test_export_entities_when_register_provided(hass, fake_api):
    fake_api.export = True
    entry = make_entry(history=0)
    await setup(hass, entry)
    await hass.async_block_till_done(wait_background_tasks=True)
    exported = state(hass, "export_latest_day")
    assert exported is not None
    assert float(exported.state) >= 0


async def test_backfill_uses_month_batches_and_exclusive_ends(hass, fake_api):
    entry = make_entry(history=2)
    await setup(hass, entry)
    ranges = [(u.query["startTime"], u.query["endTime"]) for u in fake_api.reading_requests()]
    # Validation-free setup: recent window first, then months newest first.
    assert ranges[0] == ("2026-04-03", "2026-04-11")
    assert ("2026-03-01", "2026-04-01") in ranges
    assert ("2026-02-01", "2026-03-01") in ranges
    assert ("2026-04-01", "2026-04-03") in ranges
    for start, end in ranges:
        assert (date.fromisoformat(end) - date.fromisoformat(start)).days <= 35


async def test_restart_persistence_and_api_outage(hass, fake_api, hass_storage):
    entry = make_entry(history=1)
    await setup(hass, entry)
    before = state(hass, "import_previous_month").state
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    stored = hass_storage[f"{DOMAIN}.{entry.entry_id}"]
    assert TOKEN not in json.dumps(stored)
    assert stored["version"] == 1

    # API now down: stored data still loads immediately, nothing re-fetched.
    for _ in range(20):
        fake_api.push(503)
    count = len(fake_api.reading_requests())
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.state is ConfigEntryState.LOADED
    assert state(hass, "import_previous_month").state == before
    assert state(hass, "import_latest_day").state != "unavailable"
    # Backfill was already complete, so it did not run again.
    assert len(fake_api.reading_requests()) - count <= 4


async def test_interrupted_backfill_resumes_only_missing_months(hass, fake_api):
    entry = make_entry(history=3)
    real_fetch = None

    calls = {"n": 0}

    async def flaky(self, start, end):
        calls["n"] += 1
        if calls["n"] == 3:  # recent window, newest month, then interrupted
            raise asyncio.CancelledError  # simulated shutdown mid-backfill
        return await real_fetch(self, start, end)

    from custom_components.mojelektro_plus.coordinator import MojElektroCoordinator

    real_fetch = MojElektroCoordinator._fetch
    with patch.object(MojElektroCoordinator, "_fetch", flaky):
        await setup(hass, entry)
    done = entry.runtime_data.store.meta["backfill"]["done"]
    assert len(done) == 1

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    backfill = entry.runtime_data.store.meta["backfill"]
    assert backfill["state"] == "complete"
    requested = [u.query["startTime"] for u in fake_api.reading_requests()]
    # The month fetched before the crash was not fetched a second time.
    assert requested.count(done[0].split("/")[0]) == 1


async def test_missing_intervals_and_quality_flags(hass, fake_api):
    day_ends = list(interval_end_epochs(date(2026, 4, 9)))
    fake_api.missing = set(day_ends[:4])
    fake_api.qualities = {day_ends[10]: ["TEST.ESTIMATED"]}
    entry = make_entry(history=0)
    await setup(hass, entry)
    # 9 April is now partial, so the latest *complete* day is 8 April.
    assert state(hass, "import_latest_day").attributes["date"] == "2026-04-08"
    month = state(hass, "import_current_month").attributes
    assert month["intervals_present"] == 9 * 96 - 4
    assert month["intervals_flagged"] == 1
    coverage = state(hass, "current_month_coverage")
    assert float(coverage.state) == pytest.approx(100 * (9 * 96 - 4) / (30 * 96), abs=0.01)


async def test_late_readings_and_corrections_are_merged(hass, fake_api):
    entry = make_entry(history=0)
    fake_api.available_until = datetime(2026, 4, 9, 12, tzinfo=LJ)
    await setup(hass, entry)
    assert state(hass, "import_latest_day").attributes["date"] == "2026-04-08"
    target = list(interval_end_epochs(date(2026, 4, 8)))[5]
    fake_api.overrides[("import", target)] = 5.0
    fake_api.available_until = datetime(2026, 4, 10, tzinfo=LJ)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "import_latest_day").attributes["date"] == "2026-04-09"
    value, _ = entry.runtime_data.store.registers["import"].get(target)
    assert value == 5.0


async def test_auth_failure_starts_reauth(hass, fake_api):
    entry = make_entry(history=0)
    await setup(hass, entry)
    fake_api.push(401)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert any(f["context"]["source"] == "reauth" for f in flows)


async def test_rate_limit_keeps_entities_available(hass, fake_api):
    entry = make_entry(history=0)
    await setup(hass, entry)
    for _ in range(4):
        fake_api.push(429, "", {"Retry-After": "0"})
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert entry.runtime_data.last_update_success is False
    assert entry.runtime_data.store.meta["last_error"] == "rate_limited"
    assert state(hass, "import_latest_day").state != "unavailable"


async def test_first_setup_retries_when_api_is_down(hass, fake_api):
    for _ in range(10):
        fake_api.push(503)
    entry = make_entry(history=0)
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_shared_panel_lifecycle(hass, fake_api):
    fake_api.meters.add("4-93571")
    first = make_entry(history=0)
    second = make_entry(history=0, meter="4-93571")
    await setup(hass, first)
    await setup(hass, second)
    assert PANEL_URL in panels(hass)
    assert await hass.config_entries.async_unload(first.entry_id)
    assert PANEL_URL in panels(hass)
    assert await hass.config_entries.async_unload(second.entry_id)
    assert PANEL_URL not in panels(hass)
    # Sidebar disabled: no panel at all.
    third = make_entry(history=0, sidebar=False)
    await hass.config_entries.async_setup(first.entry_id)
    await hass.config_entries.async_remove(first.entry_id)
    await setup(hass, third)
    assert PANEL_URL not in panels(hass)


async def test_unload_cancels_running_backfill(hass, fake_api):
    entry = make_entry(history=12)
    entry.add_to_hass(hass)

    with patch("custom_components.mojelektro_plus.coordinator.BACKFILL_PAUSE", 3600):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = entry.runtime_data
        assert coordinator.backfill_running
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
    assert not coordinator.backfill_running
    assert coordinator.store.meta["backfill"]["state"] == "idle"
    assert len(coordinator.store.meta["backfill"]["done"]) >= 1


async def test_scheduled_refresh_interval(hass, fake_api, frozen):
    entry = make_entry(history=0)
    await setup(hass, entry)
    count = len(fake_api.reading_requests())
    frozen.tick(timedelta(hours=6, minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(fake_api.reading_requests()) > count


async def test_refresh_range_service(hass, fake_api):
    entry = make_entry(history=0)
    await setup(hass, entry)
    count = len(fake_api.reading_requests())
    await hass.services.async_call(
        DOMAIN,
        "refresh_range",
        {"config_entry_id": entry.entry_id, "start_date": "2026-01-15", "end_date": "2026-02-10"},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    new = [(u.query["startTime"], u.query["endTime"]) for u in fake_api.reading_requests()[count:]]
    assert new == [("2026-01-15", "2026-02-01"), ("2026-02-01", "2026-02-11")]


async def test_remove_entry_deletes_storage(hass, fake_api, hass_storage):
    entry = make_entry(history=0)
    await setup(hass, entry)
    await hass.config_entries.async_unload(entry.entry_id)
    assert f"{DOMAIN}.{entry.entry_id}" in hass_storage
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert f"{DOMAIN}.{entry.entry_id}" not in hass_storage


async def test_today_constant_matches_fixture():
    assert date(2026, 4, 10) == TODAY
