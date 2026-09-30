"""Named CMD02 settings from the ioBroker HEIKO 0.12.1 catalog."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN

CATALOG: tuple[dict[str, Any], ...] = tuple(
    json.loads(Path(__file__).with_name("parameters.json").read_text(encoding="utf-8-sig"))
)
WRITABLE: tuple[dict[str, Any], ...] = tuple(
    item for item in CATALOG if item["writable"]
)


def validate_value(definition: dict[str, Any], value: object) -> float:
    """Match the reference adapter's strict boolean, enum and range checks."""
    if not definition["writable"]:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="read_only")
    if definition["type"] == "boolean":
        if type(value) is not bool:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="boolean_required")
        return float(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="numeric_required")
    number = float(value)
    if not math.isfinite(number) or (definition["integer"] and not number.is_integer()):
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="finite_integer_required")
    if definition["min"] is not None and number < definition["min"]:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="below_minimum")
    if definition["max"] is not None and number > definition["max"]:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="above_maximum")
    if definition["pageControl"] == "select" and str(int(number)) not in definition["states"]:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="unsupported_selection")
    return number
