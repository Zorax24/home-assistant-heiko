"""Privacy-safe diagnostics for the Heiko W600 integration."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

# Keep this value in sync with manifest.json.
_INTEGRATION_VERSION = "0.6.0"
_MAX_FIELD_COUNT = 1000


def _age_seconds(value: Any, now: datetime) -> int | None:
    """Return an age for an aware datetime, never the timestamp itself."""
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return None
    return max(0, int((now - value).total_seconds()))


def _field_count(value: Any) -> int | None:
    """Count present mapping values without exposing keys or values."""
    if not isinstance(value, Mapping):
        return None
    present = sum(item is not None for item in value.values())
    return min(present, _MAX_FIELD_COUNT)


def _get_coordinator(hass: HomeAssistant, entry: ConfigEntry) -> Any:
    """Read the coordinator from this integration's runtime storage safely."""
    hass_data = getattr(hass, "data", None)
    if not isinstance(hass_data, Mapping):
        return None
    domain_data = hass_data.get(DOMAIN)
    if not isinstance(domain_data, Mapping):
        return None
    entry_id = getattr(entry, "entry_id", None)
    if not isinstance(entry_id, str):
        return None
    return domain_data.get(entry_id)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return only explicitly allowlisted metadata."""
    coordinator = _get_coordinator(hass, entry)
    now = datetime.now(timezone.utc)

    return {
        "software": {"integration_version": _INTEGRATION_VERSION},
        "runtime": {
            "connected": getattr(coordinator, "connected", False) is True,
            "upstream_enabled": getattr(coordinator, "upstream_enabled", False) is True,
            "upstream_connected": getattr(coordinator, "_upstream_writer", None) is not None,
            "realtime_fresh": (
                getattr(coordinator, "is_realtime_fresh", False) is True
            ),
            "settings_fresh": (
                getattr(coordinator, "is_settings_fresh", False) is True
            ),
            "realtime_age_seconds": _age_seconds(
                getattr(coordinator, "last_realtime", None), now
            ),
            "settings_age_seconds": _age_seconds(
                getattr(coordinator, "last_settings", None), now
            ),
            "realtime_field_count": _field_count(
                getattr(coordinator, "realtime", None)
            ),
            "settings_field_count": _field_count(
                getattr(coordinator, "settings", None)
            ),
        },
        "configuration_ranges": {
            "listen_port": {"minimum": 1, "maximum": 65535},
            "upstream_port": {"minimum": 1, "maximum": 65535},
            "stale_seconds": {"minimum": 30, "maximum": 3600},
        },
    }
