"""Interval storage: deduplication, revisions, coverage and boundaries."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from custom_components.mojelektro_plus.api import Reading
from custom_components.mojelektro_plus.data import (
    RegisterData,
    day_series,
    latest_complete_day,
)
from custom_components.mojelektro_plus.timeutil import interval_end_epochs

LJ = ZoneInfo("Europe/Ljubljana")


def readings_for(day: date, value: float = 0.25) -> list[Reading]:
    return [Reading(end, value) for end in interval_end_epochs(day)]


def test_overlapping_merges_never_double_count():
    data = RegisterData()
    first = data.merge(readings_for(date(2026, 1, 1)) + readings_for(date(2026, 1, 2)))
    assert first.added == 192
    again = data.merge(readings_for(date(2026, 1, 2)) + readings_for(date(2026, 1, 3)))
    assert again.added == 96 and again.unchanged == 96 and again.revised == 0
    assert data.period(date(2026, 1, 1), date(2026, 1, 3)).total == 72.0


def test_corrections_revise_in_place_and_report_earliest_change():
    data = RegisterData()
    data.merge(readings_for(date(2026, 1, 1)))
    ends = list(interval_end_epochs(date(2026, 1, 1)))
    result = data.merge([Reading(ends[10], 1.0, ("TEST.ESTIMATED",)), Reading(ends[40], 0.25)])
    assert result.revised == 1 and result.unchanged == 1
    assert result.earliest_change == ends[10]
    assert data.day(date(2026, 1, 1)).total == 24.75
    assert data.day(date(2026, 1, 1)).flagged == 1
    # Flag cleared by a later download.
    data.merge([Reading(ends[10], 1.0)])
    assert data.get(ends[10]) == (1.0, ())


def test_missing_value_never_erases_and_is_not_zero():
    data = RegisterData()
    ends = list(interval_end_epochs(date(2026, 1, 1)))
    data.merge([Reading(ends[0], 0.0), Reading(ends[1], None, ("TEST.NOT_READ",))])
    assert data.get(ends[0]) == (0.0, ())
    assert data.get(ends[1]) == (None, ("TEST.NOT_READ",))
    data.merge([Reading(ends[0], None)])
    assert data.get(ends[0]) == (0.0, ())
    total = data.day(date(2026, 1, 1))
    assert total.present == 1 and total.expected == 96 and not total.complete
    assert total.coverage == round(100 / 96, 2)
    series = day_series(data, date(2026, 1, 1))
    assert len(series) == 96 and series[0]["value"] == 0.0 and series[2]["value"] is None


def test_dst_days_complete_with_92_and_100_intervals():
    data = RegisterData()
    for day in (date(2026, 3, 29), date(2026, 10, 25)):
        data.merge(readings_for(day, 0.1))
    spring = data.day(date(2026, 3, 29))
    autumn = data.day(date(2026, 10, 25))
    assert (spring.present, spring.expected, spring.complete) == (92, 92, True)
    assert (autumn.present, autumn.expected, autumn.complete) == (100, 100, True)
    assert spring.total == 9.2 and autumn.total == 10.0


def test_midnight_and_month_boundaries():
    data = RegisterData()
    data.merge(readings_for(date(2026, 1, 31), 1.0) + readings_for(date(2026, 2, 1), 2.0))
    assert data.period(date(2026, 1, 1), date(2026, 1, 31)).total == 96.0
    assert data.period(date(2026, 2, 1), date(2026, 2, 28)).total == 192.0
    midnight = int(datetime(2026, 2, 1, tzinfo=LJ).timestamp())
    assert data.get(midnight) == (1.0, ())


def test_latest_complete_day_skips_partial_latest_day():
    data = RegisterData()
    data.merge(readings_for(date(2026, 4, 7)) + readings_for(date(2026, 4, 8)))
    data.merge(readings_for(date(2026, 4, 9))[:50])
    assert latest_complete_day(data, date(2026, 4, 10)) == date(2026, 4, 8)
    assert latest_complete_day(RegisterData(), date(2026, 4, 10)) is None


def test_hourly_and_prune():
    data = RegisterData()
    data.merge(readings_for(date(2026, 1, 1), 0.25) + readings_for(date(2026, 1, 2), 0.5))
    hours = list(data.hourly())
    assert len(hours) == 48
    assert hours[0][1] == 1.0 and hours[-1][1] == 2.0
    # Hour boundaries are UTC hours of the interval *start*.
    first_hour = int(datetime(2026, 1, 1, tzinfo=LJ).timestamp())
    assert hours[0][0] == first_hour
    dropped = data.prune_before(int(datetime(2026, 1, 2, 12, tzinfo=LJ).timestamp()))
    assert sum(v for _, v in dropped) > 0
    assert data.earliest_end() >= first_hour + 3600


def test_json_roundtrip():
    data = RegisterData()
    data.merge(readings_for(date(2026, 3, 29), 0.123456789))
    ends = list(interval_end_epochs(date(2026, 3, 29)))
    data.merge([Reading(ends[3], 0.5, ("A", "B"))])
    clone = RegisterData.from_json(data.as_json())
    assert clone.day(date(2026, 3, 29)) == data.day(date(2026, 3, 29))
    assert clone.get(ends[3]) == (0.5, ("A", "B"))
    assert clone.get(ends[0])[0] == 0.123457
    assert clone.latest_end() == ends[-1]
