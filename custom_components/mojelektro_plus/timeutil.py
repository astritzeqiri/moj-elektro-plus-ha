"""Electricity-day and calendar helpers.

Identity is always the UTC instant at which a 15-minute interval ends.
Aggregation always uses Europe/Ljubljana, whatever timezone Home Assistant
itself runs in. An interval that ends at local midnight belongs to the day
(and month) before it.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from .const import INTERVAL, INTERVAL_SECONDS, MAX_REQUEST_DAYS, TIMEZONE

# Integration modules are imported in an executor thread, so loading the
# zone file here never blocks the event loop.
LJUBLJANA = ZoneInfo(TIMEZONE)


def to_epoch(moment: datetime) -> int:
    """Return whole UTC seconds for an aware datetime."""
    if moment.tzinfo is None:
        raise ValueError("naive datetime")
    return int(moment.timestamp())


def from_epoch(epoch: int) -> datetime:
    """Return an aware UTC datetime."""
    return datetime.fromtimestamp(epoch, UTC)


def local_midnight(day: date) -> datetime:
    """Return the aware Ljubljana midnight at which ``day`` starts."""
    return datetime(day.year, day.month, day.day, tzinfo=LJUBLJANA)


def day_bounds_epoch(day: date) -> tuple[int, int]:
    """Return (start, end) UTC epochs of a Ljubljana day (end exclusive)."""
    return (
        to_epoch(local_midnight(day)),
        to_epoch(local_midnight(day + timedelta(days=1))),
    )


def expected_intervals(day: date) -> int:
    """Return how many 15-minute intervals a Ljubljana day has: 92, 96 or 100."""
    start, end = day_bounds_epoch(day)
    return (end - start) // INTERVAL_SECONDS


def interval_day(end_epoch: int) -> date:
    """Return the Ljubljana consumption day an interval (by its end) belongs to."""
    start = from_epoch(end_epoch) - INTERVAL
    return start.astimezone(LJUBLJANA).date()


def interval_end_epochs(day: date) -> range:
    """Return every interval-end epoch belonging to a Ljubljana day."""
    start, end = day_bounds_epoch(day)
    return range(start + INTERVAL_SECONDS, end + 1, INTERVAL_SECONDS)


def month_start(day: date) -> date:
    """Return the first day of the month containing ``day``."""
    return day.replace(day=1)


def add_months(day: date, months: int) -> date:
    """Return the first day of the month ``months`` after ``day``'s month."""
    index = day.year * 12 + (day.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def month_days(first: date) -> list[date]:
    """Return every day of the month starting at ``first``."""
    nxt = add_months(first, 1)
    return [first + timedelta(days=i) for i in range((nxt - first).days)]


def local_today(now: datetime | None = None) -> date:
    """Return today's date in Ljubljana."""
    return (now or datetime.now(UTC)).astimezone(LJUBLJANA).date()


def parse_timestamp(value: str) -> datetime:
    """Parse an API timestamp (ISO 8601 with offset) into aware UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        # The spec says timestamps carry an offset; treat a missing one as
        # local Slovenian time rather than as the HA instance's zone.
        parsed = parsed.replace(tzinfo=LJUBLJANA)
    return parsed.astimezone(UTC)


def batches(start: date, end: date) -> Iterator[tuple[date, date]]:
    """Split ``[start, end)`` into calendar-month batches, each <= 35 days.

    ``end`` is exclusive, matching the API's ``endTime`` behaviour.
    """
    cursor = start
    while cursor < end:
        nxt = min(add_months(cursor, 1), end)
        if (nxt - cursor).days > MAX_REQUEST_DAYS:  # pragma: no cover - months < 35
            nxt = cursor + timedelta(days=MAX_REQUEST_DAYS)
        yield cursor, nxt
        cursor = nxt


def earliest_allowed(today: date) -> date:
    """Return the earliest start date the API serves (two years back).

    One spare day keeps requests clear of the boundary.
    """
    try:
        boundary = today.replace(year=today.year - 2)
    except ValueError:  # 29 February
        boundary = today.replace(year=today.year - 2, day=28)
    return boundary + timedelta(days=1)


def history_start(today: date, months: int) -> date:
    """Return the first day to backfill: ``months`` complete calendar months."""
    return max(add_months(month_start(today), -months), earliest_allowed(today))
