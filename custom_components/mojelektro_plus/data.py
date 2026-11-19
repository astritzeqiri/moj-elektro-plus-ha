"""In-memory interval data, independent of Home Assistant.

Intervals are keyed by the UTC instant at which they end, so overlapping
downloads and DST transitions can never double-count. Internally values are
held in UTC-day chunks of 96 slots (UTC has no DST), which keeps the
persisted form compact and bounded.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import date, timedelta
import math
from typing import Any

from .api import Reading
from .const import INTERVAL_SECONDS
from .timeutil import (
    day_bounds_epoch,
    expected_intervals,
    interval_day,
    interval_end_epochs,
)

SLOTS = 96
DAY_SECONDS = 86400


def _locate(end: int) -> tuple[int, int]:
    """Return (UTC day index, slot) for an interval ending at ``end``."""
    if end % INTERVAL_SECONDS:
        raise ValueError("interval end is not on a 15-minute boundary")
    start = end - INTERVAL_SECONDS
    return start // DAY_SECONDS, (start % DAY_SECONDS) // INTERVAL_SECONDS


def _end_of(day_index: int, slot: int) -> int:
    return day_index * DAY_SECONDS + (slot + 1) * INTERVAL_SECONDS


@dataclass(slots=True)
class Chunk:
    """96 interval values of one UTC day; ``None`` means missing."""

    values: list[float | None] = field(default_factory=lambda: [None] * SLOTS)
    qualities: dict[int, tuple[str, ...]] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"v": self.values}
        if self.qualities:
            out["q"] = {str(k): list(v) for k, v in self.qualities.items()}
        return out

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> Chunk:
        values = list(raw.get("v", []))[:SLOTS]
        values += [None] * (SLOTS - len(values))
        clean = [
            float(v) if isinstance(v, (int, float)) and math.isfinite(v) else None for v in values
        ]
        qualities = {
            int(k): tuple(str(x) for x in v)
            for k, v in (raw.get("q") or {}).items()
            if str(k).isdigit() and 0 <= int(k) < SLOTS and isinstance(v, list)
        }
        return cls(clean, qualities)


@dataclass(slots=True)
class MergeResult:
    """What a merge changed."""

    added: int = 0
    revised: int = 0
    unchanged: int = 0
    earliest_change: int | None = None

    @property
    def changed(self) -> int:
        return self.added + self.revised


@dataclass(slots=True)
class PeriodTotal:
    """Total of a period, with completeness information."""

    total: float
    present: int
    expected: int
    flagged: int
    first_end: int | None = None
    last_end: int | None = None

    @property
    def complete(self) -> bool:
        return self.expected > 0 and self.present == self.expected

    @property
    def coverage(self) -> float:
        return round(100.0 * self.present / self.expected, 2) if self.expected else 0.0


class RegisterData:
    """All stored intervals of one register."""

    def __init__(self) -> None:
        self.chunks: dict[int, Chunk] = {}

    def get(self, end: int) -> tuple[float | None, tuple[str, ...]]:
        day, slot = _locate(end)
        chunk = self.chunks.get(day)
        if chunk is None:
            return None, ()
        return chunk.values[slot], chunk.qualities.get(slot, ())

    def merge(self, readings: Iterable[Reading]) -> MergeResult:
        """Idempotently merge readings; later downloads revise earlier ones.

        A reading without a value never erases a stored value: it carries no
        information beyond "not available in this response".
        """
        result = MergeResult()
        for reading in readings:
            day, slot = _locate(reading.end)
            chunk = self.chunks.get(day)
            old_value = chunk.values[slot] if chunk else None
            old_q = chunk.qualities.get(slot, ()) if chunk else ()
            if reading.value is None:
                if old_value is not None or old_q == reading.qualities:
                    result.unchanged += 1
                    continue
                new_value = None
            else:
                new_value = round(reading.value, 6)
            if new_value == old_value and reading.qualities == old_q:
                result.unchanged += 1
                continue
            if chunk is None:
                chunk = self.chunks[day] = Chunk()
            chunk.values[slot] = new_value
            if reading.qualities:
                chunk.qualities[slot] = reading.qualities
            else:
                chunk.qualities.pop(slot, None)
            if old_value is None and new_value is not None:
                result.added += 1
            else:
                result.revised += 1
            if result.earliest_change is None or reading.end < result.earliest_change:
                result.earliest_change = reading.end
        return result

    def iter_range(
        self, start: int, end: int
    ) -> Iterator[tuple[int, float | None, tuple[str, ...]]]:
        """Yield (end, value, qualities) for every interval ending in (start, end]."""
        for moment in range(start + INTERVAL_SECONDS, end + 1, INTERVAL_SECONDS):
            value, qualities = self.get(moment)
            yield moment, value, qualities

    def iter_present(self) -> Iterator[tuple[int, float, tuple[str, ...]]]:
        """Yield every stored value in time order."""
        for day in sorted(self.chunks):
            chunk = self.chunks[day]
            for slot, value in enumerate(chunk.values):
                if value is not None:
                    yield _end_of(day, slot), value, chunk.qualities.get(slot, ())

    def latest_end(self) -> int | None:
        for day in sorted(self.chunks, reverse=True):
            values = self.chunks[day].values
            for slot in range(SLOTS - 1, -1, -1):
                if values[slot] is not None:
                    return _end_of(day, slot)
        return None

    def earliest_end(self) -> int | None:
        for day in sorted(self.chunks):
            values = self.chunks[day].values
            for slot in range(SLOTS):
                if values[slot] is not None:
                    return _end_of(day, slot)
        return None

    def has_values(self) -> bool:
        return any(v is not None for c in self.chunks.values() for v in c.values)

    def period(self, first: date, last: date) -> PeriodTotal:
        """Sum Ljubljana days ``first``..``last`` inclusive."""
        start, _ = day_bounds_epoch(first)
        _, end = day_bounds_epoch(last)
        values: list[float] = []
        flagged = 0
        first_end = last_end = None
        for moment, value, qualities in self.iter_range(start, end):
            if value is None:
                continue
            values.append(value)
            if qualities:
                flagged += 1
            if first_end is None:
                first_end = moment
            last_end = moment
        expected = sum(
            expected_intervals(first + timedelta(days=i)) for i in range((last - first).days + 1)
        )
        return PeriodTotal(
            total=round(math.fsum(values), 6),
            present=len(values),
            expected=expected,
            flagged=flagged,
            first_end=first_end,
            last_end=last_end,
        )

    def day(self, day: date) -> PeriodTotal:
        return self.period(day, day)

    def hourly(self, from_hour: int | None = None) -> Iterator[tuple[int, float, int]]:
        """Yield (UTC hour start, kWh, intervals present) for hours with data."""
        current: int | None = None
        values: list[float] = []
        for end, value, _ in self.iter_present():
            hour = ((end - INTERVAL_SECONDS) // 3600) * 3600
            if from_hour is not None and hour < from_hour:
                continue
            if hour != current:
                if current is not None:
                    yield current, round(math.fsum(values), 6), len(values)
                current, values = hour, []
            values.append(value)
        if current is not None:
            yield current, round(math.fsum(values), 6), len(values)

    def prune_before(self, end_epoch: int) -> list[tuple[int, float]]:
        """Drop UTC days that end before ``end_epoch``; return dropped hourly sums."""
        cutoff_day = end_epoch // DAY_SECONDS
        dropped: list[tuple[int, float]] = []
        for day in sorted(d for d in self.chunks if d < cutoff_day):
            chunk = self.chunks.pop(day)
            for hour in range(24):
                part = [v for v in chunk.values[hour * 4 : hour * 4 + 4] if v is not None]
                if part:
                    dropped.append((day * DAY_SECONDS + hour * 3600, math.fsum(part)))
        return dropped

    def as_json(self) -> dict[str, Any]:
        return {str(day): chunk.as_json() for day, chunk in sorted(self.chunks.items())}

    @classmethod
    def from_json(cls, raw: dict[str, Any]) -> RegisterData:
        data = cls()
        for key, chunk in (raw or {}).items():
            if str(key).lstrip("-").isdigit() and isinstance(chunk, dict):
                data.chunks[int(key)] = Chunk.from_json(chunk)
        return data


def day_series(register: RegisterData, day: date) -> list[dict[str, Any]]:
    """Return every expected interval of a Ljubljana day, missing ones included."""
    return [
        {"end": end, "value": value, "q": list(qualities)}
        for end in interval_end_epochs(day)
        for value, qualities in [register.get(end)]
    ]


def latest_complete_day(register: RegisterData, before: date) -> date | None:
    """Return the most recent Ljubljana day before ``before`` that is complete."""
    latest = register.latest_end()
    if latest is None:
        return None
    day = min(interval_day(latest), before - timedelta(days=1))
    earliest = register.earliest_end()
    floor = interval_day(earliest) if earliest else day
    while day >= floor:
        if register.day(day).complete:
            return day
        day -= timedelta(days=1)
    return None
