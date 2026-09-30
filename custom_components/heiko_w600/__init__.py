"""Home Assistant setup and teardown for HEIKO W600."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import HeikoCoordinator

PLATFORMS: tuple[Platform, ...] = (
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Expose an on-demand dashboard export; never change an existing dashboard."""
    from homeassistant.core import SupportsResponse
    from homeassistant.exceptions import HomeAssistantError
    from homeassistant.helpers import entity_registry as er
    import yaml
    from .dashboard import build_dashboard

    async def export_dashboard(call):
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="not_configured")
        language = call.data.get("language", getattr(hass.config, "language", "en"))
        if "language" in call.data and language not in ("en", "de"):
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="invalid_language")
        dashboard = build_dashboard(entries[0].entry_id,
                                    er.async_get(hass).entities.values(), language)
        return {"yaml": yaml.safe_dump(dashboard, allow_unicode=True, sort_keys=False)}

    hass.services.async_register(DOMAIN, "export_dashboard", export_dashboard,
                                 supports_response=SupportsResponse.ONLY)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start the listener, register the coordinator, and load entity platforms."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    coordinator = HeikoCoordinator(hass, entry)

    try:
        await coordinator.async_start()
        domain_data[entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        domain_data.pop(entry.entry_id, None)
        if not domain_data:
            hass.data.pop(DOMAIN, None)
        await coordinator.async_stop()
        raise

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload platforms before stopping the listener and discarding runtime data."""
    domain_data = hass.data.get(DOMAIN, {})
    coordinator = domain_data.get(entry.entry_id)

    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    if coordinator is not None:
        await coordinator.async_stop()

    domain_data.pop(entry.entry_id, None)
    if not domain_data:
        hass.data.pop(DOMAIN, None)

    return True
