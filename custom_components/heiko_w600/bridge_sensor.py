"""Bridge health remains observable even before W600 telemetry arrives."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

FIELDS = (
    ("connection_state", "Connection status", None),
    ("bytes_to_cloud", "Data to manufacturer cloud", "B"),
    ("bytes_to_unit", "Data to heat pump", "B"),
    ("frames_received", "CRC-validated frames", None),
    ("last_write_result", "Last write request", None),
    ("realtime_age", "Measurement age", "s"),
    ("settings_age", "Settings age", "s"),
)


class HeikoBridgeSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator, entry_id, key, name, unit):
        super().__init__(coordinator)
        self.key = key
        self._attr_translation_key = key
        self._attr_native_unit_of_measurement = unit
        if key in ("connection_state", "last_write_result"):
            from homeassistant.components.sensor import SensorDeviceClass
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = (["stopped", "waiting", "measurements_stale", "settings_stale", "fresh"]
                                  if key == "connection_state" else ["none", "confirmed", "unconfirmed", "aborted"])
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry_id)}, name="HEIKO W600")

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        if self.key == "connection_state":
            if self.coordinator._server is None:
                return "stopped"
            if not self.coordinator.connected:
                return "waiting"
            if not self.coordinator.is_realtime_fresh:
                return "measurements_stale"
            if not self.coordinator.is_settings_fresh:
                return "settings_stale"
            return "fresh"
        if self.key in ("realtime_age", "settings_age"):
            from datetime import datetime, timezone
            stamp = (self.coordinator.last_realtime if self.key == "realtime_age"
                     else self.coordinator.last_settings)
            return None if stamp is None else max(0, int((datetime.now(timezone.utc)-stamp).total_seconds()))
        return getattr(self.coordinator, self.key)

    @property
    def extra_state_attributes(self):
        if self.key == "last_write_result":
            return {"parameter_index": self.coordinator.last_write_index,
                    "requested_value": self.coordinator.last_write_value}
        if self.key == "connection_state":
            return {"tcp_port": self.coordinator.listen_port,
                    "weiterleitung_aktiv": self.coordinator.upstream_enabled,
                    "w600_verbunden": self.coordinator._client_writer is not None,
                    "hersteller_verbunden": self.coordinator._upstream_writer is not None,
                    "messwerte_aktuell": self.coordinator.is_realtime_fresh,
                    "einstellungen_aktuell": self.coordinator.is_settings_fresh}
        return None
