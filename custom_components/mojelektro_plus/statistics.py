"""Long-term (external) statistics for the Energy dashboard.

Rows are hourly and placed at the hour the energy was *measured*, never at
the time it was downloaded, so delayed readings do not create spikes.

Cumulative sums are derived deterministically from stored intervals:

    sum(hour H) = anchor_sum + Σ hourly totals of stored hours <= H

``anchor_sum`` accumulates hours pruned from local storage. Pruning only
happens beyond the two-year API limit, so pruned data can never be fetched
again and counted twice. Whenever intervals change (late readings, user
refreshes, corrections), every row from the earliest changed hour onwards is
re-written; the recorder upserts rows by start time, so imports are
idempotent and restarts cannot duplicate consumption.
"""

from __future__ import annotations

from collections.abc import Iterator
import logging
from typing import Any

from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant

from .const import DOMAIN, INTERVAL_SECONDS, REGISTER_EXPORT, REGISTER_IMPORT
from .data import RegisterData
from .timeutil import from_epoch

_LOGGER = logging.getLogger(__name__)

IMPORT_CHUNK = 2000


def statistic_id(meter_id: str, register: str) -> str:
    """Return the external statistic id for a meter register."""
    slug = meter_id.replace("-", "_").lower()
    kind = "consumption" if register == REGISTER_IMPORT else "return"
    return f"{DOMAIN}:{slug}_energy_{kind}"


def statistic_name(title: str, register: str) -> str:
    label = "imported energy" if register == REGISTER_IMPORT else "exported energy"
    return f"{title} {label}"


def compute_rows(
    data: RegisterData,
    anchor_sum: float,
    from_hour: int | None,
) -> Iterator[tuple[int, float, float]]:
    """Yield (hour start epoch, hour kWh, cumulative kWh) from ``from_hour``."""
    running = anchor_sum
    for hour, total, _present in data.hourly():
        running = round(running + total, 6)
        if from_hour is None or hour >= from_hour:
            yield hour, total, running


def hour_of_end(end: int) -> int:
    """Return the UTC hour start an interval (identified by its end) falls in."""
    return ((end - INTERVAL_SECONDS) // 3600) * 3600


def recorder_available(hass: HomeAssistant) -> bool:
    return "recorder" in hass.config.components


async def async_import(
    hass: HomeAssistant,
    meter_id: str,
    title: str,
    register: str,
    data: RegisterData,
    stats_meta: dict[str, Any],
) -> int:
    """Import rows from ``stats_meta['dirty_from']``. Returns rows written."""
    if not recorder_available(hass):
        return 0
    from homeassistant.components.recorder.models import (
        StatisticData,
        StatisticMeanType,
        StatisticMetaData,
    )
    from homeassistant.components.recorder.statistics import (
        async_add_external_statistics,
    )
    from homeassistant.util.unit_conversion import EnergyConverter

    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=True,
        name=statistic_name(title, register),
        source=DOMAIN,
        statistic_id=statistic_id(meter_id, register),
        unit_class=EnergyConverter.UNIT_CLASS,
        unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    )
    rows: list[StatisticData] = []
    written = 0
    for hour, total, running in compute_rows(
        data, float(stats_meta.get("anchor_sum") or 0.0), stats_meta.get("dirty_from")
    ):
        rows.append(StatisticData(start=from_epoch(hour), state=total, sum=running))
        if len(rows) >= IMPORT_CHUNK:
            async_add_external_statistics(hass, metadata, rows)
            written += len(rows)
            rows = []
    if rows:
        async_add_external_statistics(hass, metadata, rows)
        written += len(rows)
    stats_meta["dirty_from"] = None
    _LOGGER.debug("Imported %s statistic rows for %s", written, register)
    return written


async def async_clear(hass: HomeAssistant, meter_id: str) -> None:
    """Remove this meter's statistics (used when the entry is removed)."""
    if not recorder_available(hass):
        return
    from homeassistant.components.recorder import get_instance

    get_instance(hass).async_clear_statistics(
        [statistic_id(meter_id, r) for r in (REGISTER_IMPORT, REGISTER_EXPORT)]
    )


def mark_dirty(stats_meta: dict[str, Any], earliest_end: int | None) -> None:
    """Record that rows from the hour of ``earliest_end`` must be rewritten."""
    if earliest_end is None:
        return
    hour = hour_of_end(earliest_end)
    current = stats_meta.get("dirty_from")
    stats_meta["dirty_from"] = hour if current is None else min(current, hour)
