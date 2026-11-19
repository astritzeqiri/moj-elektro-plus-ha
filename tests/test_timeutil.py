"""Calendar, DST and boundary rules."""

from datetime import UTC, date, datetime

from custom_components.mojelektro_plus.timeutil import (
    batches,
    earliest_allowed,
    expected_intervals,
    history_start,
    interval_day,
    interval_end_epochs,
    parse_timestamp,
    to_epoch,
)


def test_dst_days_have_92_and_100_intervals():
    assert expected_intervals(date(2026, 3, 29)) == 92  # spring forward
    assert expected_intervals(date(2026, 10, 25)) == 100  # fall back
    assert expected_intervals(date(2026, 3, 28)) == 96
    assert len(interval_end_epochs(date(2026, 3, 29))) == 92
    assert len(interval_end_epochs(date(2026, 10, 25))) == 100


def test_interval_ending_at_midnight_belongs_to_previous_day():
    midnight = parse_timestamp("2026-02-01T00:00:00+01:00")
    assert interval_day(to_epoch(midnight)) == date(2026, 1, 31)
    first = parse_timestamp("2026-02-01T00:15:00+01:00")
    assert interval_day(to_epoch(first)) == date(2026, 2, 1)


def test_aggregation_ignores_home_assistant_timezone():
    # 23:00 UTC on 31 Jan is already 1 Feb in Ljubljana (UTC+1).
    end = to_epoch(datetime(2026, 1, 31, 23, 15, tzinfo=UTC))
    assert interval_day(end) == date(2026, 2, 1)


def test_timestamps_keep_their_offsets():
    summer = parse_timestamp("2026-07-01T00:15:00+02:00")
    assert summer == datetime(2026, 6, 30, 22, 15, tzinfo=UTC)
    assert parse_timestamp("2026-07-01T00:15:00Z").tzinfo == UTC


def test_batches_are_calendar_months_with_exclusive_end():
    parts = list(batches(date(2025, 12, 15), date(2026, 3, 1)))
    assert parts == [
        (date(2025, 12, 15), date(2026, 1, 1)),
        (date(2026, 1, 1), date(2026, 2, 1)),
        (date(2026, 2, 1), date(2026, 3, 1)),
    ]
    assert all((end - start).days <= 35 for start, end in parts)


def test_history_start_complete_months_and_two_year_clamp():
    today = date(2026, 4, 10)
    assert history_start(today, 12) == date(2025, 4, 1)
    assert history_start(today, 0) == date(2026, 4, 1)
    assert history_start(today, 24) == earliest_allowed(today) == date(2024, 4, 11)
    assert earliest_allowed(date(2028, 2, 29)) == date(2026, 3, 1)
