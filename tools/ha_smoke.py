"""Isolated real-HA setup/translation test; no hardware or cloud endpoints."""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
import shutil
import tempfile
from types import MappingProxyType

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr, area_registry as ar
from homeassistant.helpers.translation import async_get_translations
from homeassistant import loader

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "heiko_w600"


async def main():
    with tempfile.TemporaryDirectory(prefix="heiko-isolated-") as folder:
        shutil.copytree(ROOT / "custom_components", Path(folder) / "custom_components", ignore=shutil.ignore_patterns("__pycache__"))
        hass = HomeAssistant(folder)
        hass.config.language = "en"
        hass.config_entries = ConfigEntries(hass, {})
        loader.async_setup(hass)
        await ar.async_load(hass)
        dr.async_setup(hass)
        await dr.async_load(hass)
        await er.async_load(hass)
        entry = ConfigEntry(data={"listen_host":"127.0.0.1", "listen_port":0,
                                  "upstream_host":"127.0.0.1", "upstream_port":1,
                                  "stale_seconds":180, "upstream_enabled":False},
                            options={}, domain=DOMAIN, title="HEIKO W600",
                            unique_id="heiko_w600_single_instance", version=1, minor_version=1,
                            source="user", discovery_keys=MappingProxyType({}), subentries_data=[])
        try:
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.config_entries.async_add(entry)
            await hass.async_block_till_done()
            coordinator = hass.data[DOMAIN][entry.entry_id]
            assert coordinator._server is not None
            assert coordinator.upstream_enabled is False
            assert coordinator._upstream_writer is None
            entities = [item for item in er.async_get(hass).entities.values() if item.config_entry_id == entry.entry_id]
            assert len(entities) == 176, len(entities)
            cloud_entity = next(item for item in entities if item.unique_id.endswith("_upstream_enabled"))
            assert cloud_entity.original_name == "Forward to MyHeatPump", cloud_entity.original_name
            assert hass.states.get(cloud_entity.entity_id).state == "off"
            from custom_components.heiko_w600.dashboard import build_dashboard
            for language in ("en", "de"):
                for category in ("entity", "config", "options", "services", "exceptions"):
                    translated = await async_get_translations(hass, language, category, {DOMAIN})
                    assert translated, (language, category)
                dashboard = build_dashboard(entry.entry_id, entities, language)
                assert len(dashboard["views"]) == 3
                rows=[row for card in dashboard["views"][1]["cards"] for row in card.get("entities", [])]
                assert len(rows) == 129, len(rows)
                response = await hass.services.async_call(DOMAIN, "export_dashboard", {"language":language}, blocking=True, return_response=True)
                assert "yaml" in response
                assert ("Heat pump" if language == "en" else "Wärmepumpe") in response["yaml"]
            from homeassistant.exceptions import HomeAssistantError
            try:
                await hass.services.async_call(DOMAIN, "export_dashboard", {"language":"unsupported"}, blocking=True, return_response=True)
                raise AssertionError("Invalid dashboard language accepted")
            except HomeAssistantError as error:
                assert error.translation_key == "invalid_language"
            await coordinator.async_set_upstream_enabled(True)
            await coordinator.async_set_upstream_enabled(False)
            assert entry.options["upstream_enabled"] is False
            options_form = await hass.config_entries.options.async_init(entry.entry_id)
            assert options_form["type"] == "form", options_form
            assert options_form["step_id"] == "init"
            # Exercise the real ConfigFlow schema without adding a second listener.
            from custom_components.heiko_w600.config_flow import validate_config
            assert validate_config({"listen_host":"127.0.0.1","listen_port":"8899",
                                    "upstream_host":"cloud.example","upstream_port":"18899",
                                    "stale_seconds":"180","upstream_enabled":False})["upstream_enabled"] is False
            # Test actual HA exception translation with an occupied loopback port.
            from custom_components.heiko_w600.coordinator import HeikoCoordinator
            from homeassistant.exceptions import ConfigEntryNotReady
            bound_port = coordinator._server.sockets[0].getsockname()[1]
            conflict = ConfigEntry(data={**entry.data,"listen_port":bound_port}, options={}, domain=DOMAIN,
                                   title="Conflict", unique_id="synthetic_conflict", version=1, minor_version=1,
                                   source="user", discovery_keys=MappingProxyType({}), subentries_data=[])
            conflicting = HeikoCoordinator(hass, conflict)
            try:
                await conflicting.async_start()
                raise AssertionError("Port conflict did not fail")
            except ConfigEntryNotReady as error:
                assert error.translation_key == "listener_unavailable"
            finally:
                await conflicting.async_stop()
            assert await hass.config_entries.async_unload(entry.entry_id)
            assert DOMAIN not in hass.data
            print(json.dumps({"ha_core":"2026.9.4","entities":len(entities),"languages":["en","de"],"port_conflict":"passed","hardware_contact":False}))
        finally:
            await hass.async_stop(force=True)


if __name__ == "__main__":
    asyncio.run(main())
