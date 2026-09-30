from __future__ import annotations

import math
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import DOMAIN, HeikoCoordinator
from .parameters import CATALOG
from .parameter_entity import HeikoParameterEntity
from .bridge_sensor import FIELDS, HeikoBridgeSensor

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="par01", translation_key="par01"),
    SensorEntityDescription(key="par12", translation_key="par12", native_unit_of_measurement="V", device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par13", translation_key="par13", native_unit_of_measurement="V", device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par14", translation_key="par14", native_unit_of_measurement="V", device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par37", translation_key="par37"),
    SensorEntityDescription(key="par38", translation_key="par38", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par39", translation_key="par39", native_unit_of_measurement="K", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par40", translation_key="par40", native_unit_of_measurement="K", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par41", translation_key="par41", native_unit_of_measurement="min", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par42", translation_key="par42", native_unit_of_measurement="min", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="par43", translation_key="par43", native_unit_of_measurement="min", state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(
        key="par04",
        translation_key="par04",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par05",
        translation_key="par05",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par06",
        translation_key="par06",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par07",
        translation_key="par07",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par08",
        translation_key="par08",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par09",
        translation_key="par09",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par10",
        translation_key="par10",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par11",
        translation_key="par11",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par20",
        translation_key="par20",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement="Hz",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par21",
        translation_key="par21",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par22",
        translation_key="par22",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement="bar",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par23",
        translation_key="par23",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement="bar",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par24",
        translation_key="par24",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par25",
        translation_key="par25",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par26",
        translation_key="par26",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par27",
        translation_key="par27",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par28",
        translation_key="par28",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par29",
        translation_key="par29",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par30",
        translation_key="par30",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement="A",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par31",
        translation_key="par31",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement="V",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="par36",
        translation_key="par36",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


class HeikoSensor(CoordinatorEntity, SensorEntity):
    """Read-only CMD01 sensor backed by the current validated snapshot."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: HeikoCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
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
            and self._numeric_value() is not None
        )

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        return self._numeric_value()

    def _numeric_value(self) -> float | None:
        value = self.coordinator.realtime.get(self.entity_description.key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not math.isfinite(value):
            return None
        return float(value)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Create read-only sensors for mapped CMD01 fields."""
    coordinator: HeikoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeikoBridgeSensor(coordinator, entry.entry_id, *field) for field in FIELDS)
    async_add_entities(HeikoSettingSensor(coordinator, entry.entry_id, item)
                       for item in CATALOG if not item["writable"])
    async_add_entities(
        HeikoSensor(coordinator, entry.entry_id, description)
        for description in SENSORS
    )


class HeikoSettingSensor(HeikoParameterEntity, SensorEntity):
    """Read-only versions from the same validated settings catalog."""
    @property
    def native_value(self):
        return self._value()
