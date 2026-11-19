"""Sensors.

All energy readings are delayed (usually by a day or more). None of these
sensors has a state class: Home Assistant would otherwise compile
statistics at the moment the value *arrives*, producing spikes on the wrong
day. Energy dashboard history comes from external statistics instead (see
``statistics.py``), which are placed at the measurement time.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    BACKFILL_COMPLETE,
    BACKFILL_ERROR,
    BACKFILL_IDLE,
    BACKFILL_RUNNING,
    EXPORT_AVAILABLE,
    INTERVAL_SECONDS,
    INTERVALS_PER_HOUR,
    REGISTER_EXPORT,
    REGISTER_IMPORT,
)
from .coordinator import MojElektroConfigEntry, MojElektroCoordinator, RegisterSnapshot
from .data import PeriodTotal
from .entity import MojElektroEntity
from .timeutil import from_epoch

PARALLEL_UPDATES = 0


def _iso(epoch: int | None) -> str | None:
    return from_epoch(epoch).isoformat() if epoch is not None else None


def _period_attrs(total: PeriodTotal | None, extra: dict[str, Any]) -> dict[str, Any]:
    if total is None:
        return extra
    return {
        **extra,
        "complete": total.complete,
        "coverage": total.coverage,
        "intervals_present": total.present,
        "intervals_expected": total.expected,
        "intervals_flagged": total.flagged,
        "data_through": _iso(total.last_end),
    }


def _interval_attrs(snap: RegisterSnapshot) -> dict[str, Any]:
    if snap.latest_end is None:
        return {}
    return {
        "interval_start": _iso(snap.latest_end - INTERVAL_SECONDS),
        "interval_end": _iso(snap.latest_end),
        "quality_flags": list(snap.latest_qualities),
        "delayed_data": True,
    }


@dataclass(frozen=True, kw_only=True)
class RegisterSensorDescription(SensorEntityDescription):
    """A sensor computed from one register snapshot."""

    value_fn: Callable[[RegisterSnapshot], Any]
    attrs_fn: Callable[[RegisterSnapshot], dict[str, Any]]


def _total(attr: str) -> Callable[[RegisterSnapshot], Any]:
    def value(snap: RegisterSnapshot) -> Any:
        total: PeriodTotal | None = getattr(snap, attr)
        return total.total if total is not None and total.present else None

    return value


def _descriptions(register: str) -> list[RegisterSensorDescription]:
    energy = {
        "device_class": SensorDeviceClass.ENERGY,
        "native_unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
    }
    return [
        RegisterSensorDescription(
            key=f"{register}_latest_interval",
            suggested_display_precision=3,
            value_fn=lambda s: s.latest_value,
            attrs_fn=_interval_attrs,
            **energy,
        ),
        RegisterSensorDescription(
            key=f"{register}_latest_average_power",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.KILO_WATT,
            suggested_display_precision=3,
            # Average over the 15-minute interval (kWh x 4), not instantaneous.
            value_fn=lambda s: (
                round(s.latest_value * INTERVALS_PER_HOUR, 6)
                if s.latest_value is not None
                else None
            ),
            attrs_fn=_interval_attrs,
        ),
        RegisterSensorDescription(
            key=f"{register}_latest_day",
            suggested_display_precision=2,
            value_fn=_total("latest_day_total"),
            attrs_fn=lambda s: _period_attrs(
                s.latest_day_total,
                {"date": s.latest_day.isoformat() if s.latest_day else None},
            ),
            **energy,
        ),
        RegisterSensorDescription(
            key=f"{register}_current_month",
            suggested_display_precision=2,
            value_fn=_total("current_month"),
            attrs_fn=lambda s: _period_attrs(
                s.current_month,
                {
                    "month": s.current_month_start.strftime("%Y-%m")
                    if s.current_month_start
                    else None,
                    "partial": not (s.current_month and s.current_month.complete),
                },
            ),
            **energy,
        ),
        RegisterSensorDescription(
            key=f"{register}_previous_month",
            suggested_display_precision=2,
            value_fn=_total("previous_month"),
            attrs_fn=lambda s: _period_attrs(
                s.previous_month,
                {
                    "month": s.previous_month_start.strftime("%Y-%m")
                    if s.previous_month_start
                    else None,
                    "partial": not (s.previous_month and s.previous_month.complete),
                },
            ),
            **energy,
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MojElektroConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        RegisterSensor(coordinator, REGISTER_IMPORT, d) for d in _descriptions(REGISTER_IMPORT)
    ]
    entities += [
        LatestReadingSensor(coordinator),
        LastRefreshSensor(coordinator),
        DataAgeSensor(coordinator),
        CoverageSensor(coordinator),
        BackfillSensor(coordinator),
    ]
    async_add_entities(entities)

    added = False

    @callback
    def add_export() -> None:
        # Only once the API has actually returned export data: absence of
        # the register is not reported as zero export.
        nonlocal added
        if added or coordinator.store.meta.get("export_status") != EXPORT_AVAILABLE:
            return
        added = True
        async_add_entities(
            [
                RegisterSensor(coordinator, REGISTER_EXPORT, d)
                for d in _descriptions(REGISTER_EXPORT)
            ]
        )

    coordinator.export_listeners.append(add_export)
    entry.async_on_unload(lambda: coordinator.export_listeners.remove(add_export))
    add_export()


class RegisterSensor(MojElektroEntity, SensorEntity):
    entity_description: RegisterSensorDescription

    def __init__(
        self,
        coordinator: MojElektroCoordinator,
        register: str,
        description: RegisterSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._register = register

    @property
    def _snap(self) -> RegisterSnapshot | None:
        data = self.coordinator.data
        return data.registers.get(self._register) if data else None

    @property
    def native_value(self) -> Any:
        snap = self._snap
        return self.entity_description.value_fn(snap) if snap else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snap = self._snap
        return self.entity_description.attrs_fn(snap) if snap else {}


class LatestReadingSensor(MojElektroEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: MojElektroCoordinator) -> None:
        super().__init__(coordinator, "latest_reading")

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        if not data or not data.has_data:
            return None
        return from_epoch(data.registers[REGISTER_IMPORT].latest_end)


class LastRefreshSensor(MojElektroEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MojElektroCoordinator) -> None:
        super().__init__(coordinator, "last_refresh")

    @property
    def native_value(self) -> datetime | None:
        data = self.coordinator.data
        return data.last_success if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        meta = self.coordinator.store.meta
        return {"last_attempt": meta.get("last_attempt"), "last_error": meta.get("last_error")}


class DataAgeSensor(MojElektroEntity, SensorEntity):
    """Hours between now and the end of the latest available interval."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_suggested_display_precision = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MojElektroCoordinator) -> None:
        super().__init__(coordinator, "data_age")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._tick, timedelta(minutes=15), cancel_on_shutdown=True
            )
        )

    @callback
    def _tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if not data or not data.has_data:
            return None
        latest = from_epoch(data.registers[REGISTER_IMPORT].latest_end)
        return round((datetime.now(UTC) - latest).total_seconds() / 3600, 2)


class CoverageSensor(MojElektroEntity, SensorEntity):
    """Current month coverage: present intervals / expected intervals so far."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MojElektroCoordinator) -> None:
        super().__init__(coordinator, "current_month_coverage")

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if not data:
            return None
        month = data.registers[REGISTER_IMPORT].current_month
        return month.coverage if month else None


class BackfillSensor(MojElektroEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [BACKFILL_IDLE, BACKFILL_RUNNING, BACKFILL_COMPLETE, BACKFILL_ERROR]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: MojElektroCoordinator) -> None:
        super().__init__(coordinator, "backfill")

    @property
    def native_value(self) -> str:
        if self.coordinator.backfill_running:
            return BACKFILL_RUNNING
        state = self.coordinator.store.meta["backfill"].get("state", BACKFILL_IDLE)
        return state if state in self._attr_options else BACKFILL_IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self.coordinator.status()["backfill"]
        total = status["total"]
        return {
            "months_done": status["done"],
            "months_total": total,
            "progress": round(100 * status["done"] / total, 1) if total else 100.0,
            "error": status["error"],
        }
