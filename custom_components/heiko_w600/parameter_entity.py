"""Shared HA identity and availability for HEIKO CMD02 controls."""

from __future__ import annotations

import math
import json
from pathlib import Path
from typing import Any

from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeikoCoordinator

_SECTIONS = json.loads(Path(__file__).with_name("dashboard_strings.json").read_text(encoding="utf-8"))["en"]["sections"]


class HeikoParameterEntity(CoordinatorEntity):
    """A catalog-backed value, always sourced from a validated CMD02 frame."""

    def __init__(self, coordinator: HeikoCoordinator, entry_id: str, definition: dict[str, Any]) -> None:
        super().__init__(coordinator)
        self.definition = definition
        self._attr_unique_id = f"{entry_id}_setting_{definition['settingIndex']:03d}"
        self._attr_translation_key = f"setting_{definition['settingIndex']:03d}"
        self._attr_has_entity_name = True
        self._attr_entity_category = (
            None if definition["sectionName"] == "Schnelleinstellungen"
            else EntityCategory.CONFIG if definition["writable"]
            else EntityCategory.DIAGNOSTIC
        )
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="HEIKO W600")

    @property
    def extra_state_attributes(self):
        return {"section": _SECTIONS[self.definition["sectionName"]],
                "parameter_index": self.definition["settingIndex"],
                "confirmation": "CMD02", "source": "ioBroker HEIKO catalog"}

    @property
    def available(self) -> bool:
        return self.coordinator.is_settings_fresh and self._value() is not None

    def _value(self) -> float | None:
        value = self.coordinator.settings.get(f"setting_{self.definition['settingIndex']:03d}")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            return None
        return float(value)
