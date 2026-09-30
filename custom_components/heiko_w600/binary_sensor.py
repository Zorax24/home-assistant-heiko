from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import DOMAIN, HeikoCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="par15",
        translation_key="par15",
    ),
    BinarySensorEntityDescription(
        key="par32",
        translation_key="par32",
    ),
    BinarySensorEntityDescription(
        key="par33",
        translation_key="par33",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="par34",
        translation_key="par34",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="par35",
        translation_key="par35",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key="compressor_running",
        translation_key="compressor_running",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
)


class HeikoBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Read-only boolean derived from validated CMD01 telemetry."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: HeikoCoordinator,
        entry_id: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="HEIKO W600",
        )

    @property
    def available(self) -> bool:
        return (
            self.coordinator.is_realtime_fresh
            and self._binary_value() is not None
        )

    @property
    def is_on(self) -> bool | None:
        if not self.available:
            return None
        return self._binary_value()

    def _binary_value(self) -> bool | None:
        key = self.entity_description.key
        if key == "compressor_running":
            frequency = self.coordinator.realtime.get("par20")
            if (
                isinstance(frequency, bool)
                or not isinstance(frequency, (int, float))
                or frequency < 0
            ):
                return None
            return frequency > 0

        value = self.coordinator.realtime.get(key)
        if value == 0 or value == 0.0:
            return False
        if value == 1 or value == 1.0:
            return True
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Create confirmed read-only CMD01 binary sensors."""
    coordinator: HeikoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HeikoBinarySensor(coordinator, entry.entry_id, description)
        for description in BINARY_SENSORS
    )
