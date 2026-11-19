"""Energy dashboard statistics against Home Assistant's real recorder."""

from __future__ import annotations

from datetime import UTC, date, datetime
import itertools
from zoneinfo import ZoneInfo

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    list_statistic_ids,
    statistics_during_period,
)
import pytest
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.mojelektro_plus.api import Reading
from custom_components.mojelektro_plus.data import RegisterData
from custom_components.mojelektro_plus.statistics import compute_rows, statistic_id
from custom_components.mojelektro_plus.timeutil import interval_end_epochs

from .conftest import make_entry
from .fake_api import METER

LJ = ZoneInfo("Europe/Ljubljana")
STAT = statistic_id(METER, "import")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    """The recorder must be set up before Home Assistant itself."""
    yield


@pytest.fixture
async def rec(fake_api):
    return fake_api


async def _rows(hass, start: datetime, end: datetime | None = None):
    result = await get_instance(hass).async_add_executor_job(
        statistics_during_period, hass, start, end, {STAT}, "hour", None, {"sum", "state"}
    )
    return result.get(STAT, [])


async def _setup(hass, entry):
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)


def test_rows_are_cumulative_and_hourly():
    data = RegisterData()
    data.merge([Reading(e, 0.25) for e in interval_end_epochs(date(2026, 1, 1))])
    rows = list(compute_rows(data, 10.0, None))
    assert len(rows) == 24
    assert rows[0][1] == 1.0 and rows[0][2] == 11.0
    assert rows[-1][2] == 34.0
    # Rewriting from a later hour keeps the same sums (deterministic).
    later = list(compute_rows(data, 10.0, rows[5][0]))
    assert later == rows[5:]


async def test_statistics_at_measurement_time_without_spikes(hass, rec):
    entry = make_entry(history=1)
    await _setup(hass, entry)
    ids = await get_instance(hass).async_add_executor_job(list_statistic_ids, hass)
    meta = next(i for i in ids if i["statistic_id"] == STAT)
    assert meta["source"] == "mojelektro_plus"
    assert meta["statistics_unit_of_measurement"] == "kWh"
    assert meta["has_sum"] is True

    # Data published on the 10th covers the 9th: nothing after local midnight.
    rows = await _rows(hass, datetime(2026, 3, 1, tzinfo=LJ))
    starts = [datetime.fromtimestamp(r["start"], UTC) for r in rows]
    assert max(starts) == datetime(2026, 4, 9, 23, tzinfo=LJ).astimezone(UTC)
    assert min(starts) == datetime(2026, 3, 1, tzinfo=LJ).astimezone(UTC)
    # Sums are monotonic and each step equals that hour's state.
    for prev, cur in itertools.pairwise(rows):
        assert cur["sum"] == pytest.approx(prev["sum"] + cur["state"], abs=1e-6)
    # The DST day (29 March) has 23 hourly rows.
    day = [
        s
        for s in starts
        if datetime(2026, 3, 29, tzinfo=LJ) <= s < datetime(2026, 3, 30, tzinfo=LJ)
    ]
    assert len(day) == 23
    # The total equals the stored interval total: no duplicates.
    store = entry.runtime_data.store.registers["import"]
    total = store.period(date(2026, 3, 1), date(2026, 4, 9)).total
    assert rows[-1]["sum"] == pytest.approx(total, abs=1e-4)


async def test_reimport_after_refresh_and_restart_is_idempotent(hass, rec):
    entry = make_entry(history=0)
    await _setup(hass, entry)
    first = await _rows(hass, datetime(2026, 4, 1, tzinfo=LJ))
    await entry.runtime_data.async_refresh()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)
    second = await _rows(hass, datetime(2026, 4, 1, tzinfo=LJ))
    assert [(r["start"], r["sum"]) for r in first] == [(r["start"], r["sum"]) for r in second]


async def test_correction_rewrites_later_sums(hass, rec):
    entry = make_entry(history=0)
    await _setup(hass, entry)
    before = await _rows(hass, datetime(2026, 4, 1, tzinfo=LJ))
    target = next(iter(interval_end_epochs(date(2026, 4, 5))))
    old = entry.runtime_data.store.registers["import"].get(target)[0]
    rec.overrides[("import", target)] = old + 2.0
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)
    after = await _rows(hass, datetime(2026, 4, 1, tzinfo=LJ))
    assert len(after) == len(before)
    hour = datetime(2026, 4, 5, tzinfo=LJ).timestamp()
    for b, a in zip(before, after, strict=True):
        delta = a["sum"] - b["sum"]
        assert delta == pytest.approx(2.0 if b["start"] >= hour else 0.0, abs=1e-6)


async def test_late_readings_land_on_their_own_hours(hass, rec):
    rec.available_until = datetime(2026, 4, 8, tzinfo=LJ)
    entry = make_entry(history=0)
    await _setup(hass, entry)
    last_before = (await _rows(hass, datetime(2026, 4, 1, tzinfo=LJ)))[-1]
    rec.available_until = datetime(2026, 4, 10, tzinfo=LJ)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)
    rows = await _rows(hass, datetime(2026, 4, 8, tzinfo=LJ))
    starts = [datetime.fromtimestamp(r["start"], UTC) for r in rows]
    assert starts[0] == datetime(2026, 4, 8, tzinfo=LJ).astimezone(UTC)
    assert len(rows) == 48
    # The first new hour continues from the earlier last sum: no spike.
    assert rows[0]["sum"] == pytest.approx(last_before["sum"] + rows[0]["state"], abs=1e-6)
    # Nothing was written at download time (today, 10 April).
    assert max(starts) < datetime(2026, 4, 10, tzinfo=LJ).astimezone(UTC)


async def test_remove_entry_clears_statistics(hass, rec):
    entry = make_entry(history=0)
    await _setup(hass, entry)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    ids = await get_instance(hass).async_add_executor_job(list_statistic_ids, hass)
    assert all(i["statistic_id"] != STAT for i in ids)
