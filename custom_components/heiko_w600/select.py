"""Enumerated CMD02 controls."""

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .parameter_entity import HeikoParameterEntity
from .parameters import WRITABLE, validate_value


class HeikoSelect(HeikoParameterEntity, SelectEntity):
    async def async_handle_select_option(self, option: str) -> None:
        """Normalize legacy labels before Home Assistant validates options."""
        aliases = {label: f"option_{key}" for key, label in self.definition["states"].items()}
        await super().async_handle_select_option(aliases.get(option, option))

    @property
    def options(self) -> list[str]:
        return [f"option_{key}" for key in self.definition["states"]]

    @property
    def current_option(self) -> str | None:
        value = self._value()
        if value is None or not value.is_integer():
            return None
        return f"option_{int(value)}" if str(int(value)) in self.definition["states"] else None

    async def async_select_option(self, option: str) -> None:
        choices = {f"option_{key}": int(key) for key in self.definition["states"]}
        # Preserve old service-call labels as accepted aliases. Stored protocol values are unchanged.
        choices.update({label: int(key) for key, label in self.definition["states"].items()})
        if option not in choices:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="unsupported_selection")
        await self.coordinator.async_write_parameter(
            self.definition["settingIndex"],
            validate_value(self.definition, choices[option]),
        )


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HeikoSelect(coordinator, entry.entry_id, item)
        for item in WRITABLE
        if item["type"] == "number" and item["pageControl"] == "select"
    )
