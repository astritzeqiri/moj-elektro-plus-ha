"""Server-side aggregation for the sidebar page and CSV export.

Pure functions over stored data; nothing here talks to the API, and nothing
returned contains the API token.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
import io
import math
from typing import Any

from .const import INTERVAL_SECONDS, INTERVALS_PER_HOUR, REGISTER_EXPORT, REGISTER_IMPORT
from .data import PeriodTotal, RegisterData
from .timeutil import (
    LJUBLJANA,
    add_months,
    day_bounds_epoch,
    expected_intervals,
    from_epoch,
    month_start,
)

MAX_RANGE_DAYS = 800
MAX_INTERVAL_DAYS = 14
MAX_CSV_INTERVAL_DAYS = 400
AUTO_INTERVAL_DAYS = 3
AUTO_DAY_DAYS = 92

RESOLUTIONS = ("auto", "interval", "day", "month")


class RangeError(ValueError):
    """Invalid range or resolution."""


def parse_range(start: str, end: str) -> tuple[date, date]:
    try:
        first = date.fromisoformat(start)
        last = date.fromisoformat(end)
    except (TypeError, ValueError) as err:
        raise RangeError("Dates must be YYYY-MM-DD.") from err
    if last < first:
        raise RangeError("The end date is before the start date.")
    if (last - first).days + 1 > MAX_RANGE_DAYS:
        raise RangeError(f"Choose at most {MAX_RANGE_DAYS} days.")
    return first, last


def choose_resolution(first: date, last: date, requested: str) -> str:
    days = (last - first).days + 1
    if requested not in RESOLUTIONS:
        raise RangeError("Unknown resolution.")
    if requested == "auto":
        if days <= AUTO_INTERVAL_DAYS:
            return "interval"
        if days <= AUTO_DAY_DAYS:
            return "day"
        return "month"
    if requested == "interval" and days > MAX_INTERVAL_DAYS:
        raise RangeError(f"15-minute view is limited to {MAX_INTERVAL_DAYS} days.")
    return requested


def _total_json(total: PeriodTotal) -> dict[str, Any]:
    return {
        "total": total.total if total.present else None,
        "present": total.present,
        "expected": total.expected,
        "coverage": total.coverage,
        "complete": total.complete,
        "flagged": total.flagged,
    }


def _days(first: date, last: date) -> list[date]:
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def summarize(
    registers: dict[str, RegisterData],
    include_export: bool,
    first: date,
    last: date,
) -> dict[str, Any]:
    """Totals, daily average and peak 15-minute average demand."""
    imp = registers[REGISTER_IMPORT]
    start, _ = day_bounds_epoch(first)
    _, end = day_bounds_epoch(last)
    peak_value = None
    peak_end = None
    days_with_data: set[date] = set()
    for moment, value, _q in imp.iter_range(start, end):
        if value is None:
            continue
        if peak_value is None or value > peak_value:
            peak_value, peak_end = value, moment
    import_total = imp.period(first, last)
    complete_days = 0
    complete_sum = []
    for day in _days(first, last):
        total = imp.day(day)
        if total.present:
            days_with_data.add(day)
        if total.complete:
            complete_days += 1
            complete_sum.append(total.total)
    out: dict[str, Any] = {
        "import": _total_json(import_total),
        "export": None,
        "days": len(_days(first, last)),
        "days_with_data": len(days_with_data),
        "complete_days": complete_days,
        # Averaged over complete days only, so gaps do not drag it down.
        "daily_average": round(math.fsum(complete_sum) / complete_days, 3)
        if complete_days
        else None,
        "peak": {
            "power_kw": round(peak_value * INTERVALS_PER_HOUR, 3),
            "energy_kwh": peak_value,
            "interval_start": from_epoch(peak_end - INTERVAL_SECONDS).isoformat(),
            "interval_end": from_epoch(peak_end).isoformat(),
        }
        if peak_value is not None
        else None,
    }
    if include_export:
        out["export"] = _total_json(registers[REGISTER_EXPORT].period(first, last))
    return out


def series(
    registers: dict[str, RegisterData],
    include_export: bool,
    first: date,
    last: date,
    resolution: str,
) -> list[dict[str, Any]]:
    """Chart points at the chosen resolution."""
    imp = registers[REGISTER_IMPORT]
    exp = registers[REGISTER_EXPORT] if include_export else None
    points: list[dict[str, Any]] = []
    if resolution == "interval":
        start, _ = day_bounds_epoch(first)
        _, end = day_bounds_epoch(last)
        for moment, value, qualities in imp.iter_range(start, end):
            point: dict[str, Any] = {
                "start": from_epoch(moment - INTERVAL_SECONDS).isoformat(),
                "end": from_epoch(moment).isoformat(),
                "import": value,
                "import_q": list(qualities),
            }
            if exp is not None:
                ev, eq = exp.get(moment)
                point["export"] = ev
                point["export_q"] = list(eq)
            points.append(point)
        return points
    if resolution == "day":
        periods = [(d, d) for d in _days(first, last)]
    else:
        periods = []
        cursor = month_start(first)
        while cursor <= last:
            nxt = add_months(cursor, 1)
            periods.append((max(cursor, first), min(nxt - timedelta(days=1), last)))
            cursor = nxt
    for p_first, p_last in periods:
        total = imp.period(p_first, p_last)
        point = {
            "start": p_first.isoformat(),
            "end": p_last.isoformat(),
            "import": total.total if total.present else None,
            "present": total.present,
            "expected": total.expected,
            "coverage": total.coverage,
            "complete": total.complete,
            "flagged": total.flagged,
        }
        if exp is not None:
            et = exp.period(p_first, p_last)
            point["export"] = et.total if et.present else None
            point["export_coverage"] = et.coverage
        points.append(point)
    return points


def to_csv(
    registers: dict[str, RegisterData],
    include_export: bool,
    first: date,
    last: date,
    resolution: str,
) -> str:
    """CSV with explicit timezone, units, quality and missing-data status."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    if resolution == "interval":
        if (last - first).days + 1 > MAX_CSV_INTERVAL_DAYS:
            raise RangeError(f"15-minute CSV is limited to {MAX_CSV_INTERVAL_DAYS} days.")
        header = [
            "interval_start_utc",
            "interval_end_utc",
            "interval_start_europe_ljubljana",
            "interval_end_europe_ljubljana",
            "import_kwh",
            "import_average_kw",
            "import_status",
            "import_quality_flags",
        ]
        if include_export:
            header += ["export_kwh", "export_status", "export_quality_flags"]
        writer.writerow(header)
        start, _ = day_bounds_epoch(first)
        _, end = day_bounds_epoch(last)
        imp = registers[REGISTER_IMPORT]
        for moment, value, qualities in imp.iter_range(start, end):
            s_utc = from_epoch(moment - INTERVAL_SECONDS)
            e_utc = from_epoch(moment)
            row = [
                s_utc.isoformat(),
                e_utc.isoformat(),
                s_utc.astimezone(LJUBLJANA).isoformat(),
                e_utc.astimezone(LJUBLJANA).isoformat(),
                "" if value is None else f"{value:.6f}".rstrip("0").rstrip(".") or "0",
                ""
                if value is None
                else f"{value * INTERVALS_PER_HOUR:.6f}".rstrip("0").rstrip(".") or "0",
                _status(value, qualities),
                " ".join(qualities),
            ]
            if include_export:
                ev, eq = registers[REGISTER_EXPORT].get(moment)
                row += [
                    "" if ev is None else f"{ev:.6f}".rstrip("0").rstrip(".") or "0",
                    _status(ev, eq),
                    " ".join(eq),
                ]
            writer.writerow(row)
        return buf.getvalue()
    header = [
        "period_start_europe_ljubljana",
        "period_end_europe_ljubljana_inclusive",
        "import_kwh",
        "import_intervals_present",
        "import_intervals_expected",
        "import_coverage_percent",
        "import_complete",
        "import_flagged_intervals",
    ]
    if include_export:
        header += ["export_kwh", "export_coverage_percent"]
    writer.writerow(header)
    for point in series(registers, include_export, first, last, resolution):
        row = [
            point["start"],
            point["end"],
            "" if point["import"] is None else point["import"],
            point["present"],
            point["expected"],
            point["coverage"],
            "yes" if point["complete"] else "no",
            point["flagged"],
        ]
        if include_export:
            row += ["" if point["export"] is None else point["export"], point["export_coverage"]]
        writer.writerow(row)
    return buf.getvalue()


def _status(value: float | None, qualities: tuple[str, ...]) -> str:
    if value is None:
        return "missing"
    return "flagged" if qualities else "ok"


def expected_for(first: date, last: date) -> int:
    return sum(expected_intervals(d) for d in _days(first, last))
