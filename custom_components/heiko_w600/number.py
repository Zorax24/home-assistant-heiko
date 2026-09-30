"""Bounded numeric CMD02 controls."""

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .parameter_entity import HeikoParameterEntity
from .parameters import WRITABLE, validate_value


class HeikoNumber(HeikoParameterEntity, NumberEntity):
    _attr_mode = "box"

    @property
    def native_unit_of_measurement(self):
        return self.definition.get("unit")

    @property
    def native_min_value(self) -> float:
        return float(self.definition["min"])

    @property
    def native_max_value(self) -> float:
        return float(self.definition["max"])

    @property
    def native_step(self) -> float:
        return float(self.definition["step"] or (1 if self.definition["integer"] else 0.1))

    @property
    def native_value(self) -> float | None:
        return self._value()

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_parameter(
            self.definition["settingIndex"], validate_value(self.definition, value)
        )


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HeikoNumber(coordinator, entry.entry_id, item)
        for item in WRITABLE
        if item["type"] == "number" and item["pageControl"] == "number"
    )
