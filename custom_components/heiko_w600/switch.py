"""Boolean CMD02 controls."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .parameter_entity import HeikoParameterEntity
from .parameters import WRITABLE, validate_value


class HeikoSwitch(HeikoParameterEntity, SwitchEntity):
    @property
    def is_on(self) -> bool | None:
        value = self._value()
        return None if value is None else value != 0

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_parameter(
            self.definition["settingIndex"], validate_value(self.definition, True)
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_parameter(
            self.definition["settingIndex"], validate_value(self.definition, False)
        )


class HeikoCloudForwardingSwitch(CoordinatorEntity, SwitchEntity):
    """A local bridge setting, available even without heat-pump telemetry."""

    _attr_has_entity_name = True
    _attr_translation_key = "upstream_enabled"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:cloud-sync"

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_upstream_enabled"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="HEIKO W600")

    @property
    def available(self):
        return True

    @property
    def is_on(self):
        return self.coordinator.upstream_enabled

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_upstream_enabled(True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_upstream_enabled(False)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeikoCloudForwardingSwitch(coordinator, entry.entry_id)])
    async_add_entities(
        HeikoSwitch(coordinator, entry.entry_id, item)
        for item in WRITABLE if item["type"] == "boolean"
    )
