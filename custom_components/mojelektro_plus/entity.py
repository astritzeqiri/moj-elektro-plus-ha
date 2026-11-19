"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
from .coordinator import MojElektroCoordinator


class MojElektroEntity(CoordinatorEntity[MojElektroCoordinator]):
    """One device per meter; unique IDs derive from the meter ID."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MojElektroCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.meter_id}_{key}"
        self._attr_translation_key = key
        meter = coordinator.store.meta.get("meter") or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.meter_id)},
            name=coordinator.config_entry.title,
            manufacturer="Moj Elektro (Informatika d.o.o.)",
            model=meter.get("meter_type") or "Electricity meter",
            serial_number=coordinator.meter_id,
            sw_version=f"{NAME} {VERSION}",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://mojelektro.si",
        )

    @property
    def available(self) -> bool:
        # Stored readings stay valid when a refresh fails: the data is
        # delayed by nature. Staleness is shown by the data-age sensor.
        return self.coordinator.data is not None
