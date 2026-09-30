"""Explicit, non-mutating W600 data requests."""
from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class HeikoRequestButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, entry_id, command, name):
        super().__init__(coordinator)
        self.command = command
        self._attr_translation_key = f"request_{command:02d}"
        self._attr_unique_id = f"{entry_id}_request_{command:02d}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="HEIKO W600")

    @property
    def available(self):
        return self.coordinator.connected

    async def async_press(self):
        await self.coordinator.async_request_data(self.command)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HeikoRequestButton(coordinator, entry.entry_id, 6, "Request measurements"),
        HeikoRequestButton(coordinator, entry.entry_id, 7, "Request settings"),
    ])
