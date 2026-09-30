from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import struct
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


def _install_home_assistant_stubs() -> None:
    """Keep these loopback tests runnable without installing Home Assistant."""
    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []
    helpers = types.ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    components = types.ModuleType("homeassistant.components")
    components.__path__ = []
    exceptions = types.ModuleType("homeassistant.exceptions")
    config_entries = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    const = types.ModuleType("homeassistant.const")
    update_coordinator = types.ModuleType(
        "homeassistant.helpers.update_coordinator"
    )
    device_registry = types.ModuleType(
        "homeassistant.helpers.device_registry"
    )
    sensor_module = types.ModuleType("homeassistant.components.sensor")
    binary_module = types.ModuleType("homeassistant.components.binary_sensor")
    switch_module = types.ModuleType("homeassistant.components.switch")
    select_module = types.ModuleType("homeassistant.components.select")
    number_module = types.ModuleType("homeassistant.components.number")

    class ConfigEntryNotReady(Exception):
        def __init__(self, *args, **kwargs):
            self.translation_key = kwargs.get("translation_key")
            super().__init__(*args)

    class HomeAssistantError(Exception):
        def __init__(self, *args, **kwargs):
            self.translation_key = kwargs.get("translation_key")
            super().__init__(*args)

    class ConfigEntry:
        pass

    class HomeAssistant:
        pass

    class Platform(str, Enum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"
        SELECT = "select"
        NUMBER = "number"
        BUTTON = "button"

    class DataUpdateCoordinator:
        def __init__(self, hass, logger, *, name, config_entry=None, **kwargs):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.config_entry = config_entry
            self.data = None
            self.last_update_success = True

        def async_set_updated_data(self, data):
            self.data = data
            self.last_update_success = True

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

        @property
        def unique_id(self):
            return getattr(self, "_attr_unique_id", None)

        @property
        def has_entity_name(self):
            return getattr(self, "_attr_has_entity_name", False)

        @property
        def device_info(self):
            return getattr(self, "_attr_device_info", None)

    class SensorDeviceClass(str, Enum):
        ENUM = "enum"
        TEMPERATURE = "temperature"
        FREQUENCY = "frequency"
        PRESSURE = "pressure"
        CURRENT = "current"
        VOLTAGE = "voltage"

    class EntityCategory(str, Enum):
        DIAGNOSTIC = "diagnostic"
        CONFIG = "config"

    class SensorStateClass(str, Enum):
        MEASUREMENT = "measurement"

    class BinarySensorDeviceClass(str, Enum):
        RUNNING = "running"

    class DeviceInfo(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class SensorEntity:
        pass

    class BinarySensorEntity:
        pass

    class SwitchEntity:
        pass

    class SelectEntity:
        pass

    class NumberEntity:
        pass

    @dataclass(frozen=True)
    class SensorEntityDescription:
        key: str
        name: str | None = None
        translation_key: str | None = None
        device_class: object | None = None
        native_unit_of_measurement: str | None = None
        state_class: object | None = None
        entity_category: object | None = None

    @dataclass(frozen=True)
    class BinarySensorEntityDescription:
        key: str
        name: str | None = None
        translation_key: str | None = None
        device_class: object | None = None

    exceptions.ConfigEntryNotReady = ConfigEntryNotReady
    exceptions.HomeAssistantError = HomeAssistantError
    config_entries.ConfigEntry = ConfigEntry
    core.HomeAssistant = HomeAssistant
    const.Platform = Platform
    const.EntityCategory = EntityCategory
    device_registry.DeviceInfo = DeviceInfo
    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.CoordinatorEntity = CoordinatorEntity
    sensor_module.SensorDeviceClass = SensorDeviceClass
    sensor_module.SensorStateClass = SensorStateClass
    sensor_module.SensorEntity = SensorEntity
    sensor_module.SensorEntityDescription = SensorEntityDescription
    binary_module.BinarySensorDeviceClass = BinarySensorDeviceClass
    binary_module.BinarySensorEntity = BinarySensorEntity
    binary_module.BinarySensorEntityDescription = BinarySensorEntityDescription
    switch_module.SwitchEntity = SwitchEntity
    select_module.SelectEntity = SelectEntity
    number_module.NumberEntity = NumberEntity

    sys.modules.update(
        {
            "homeassistant": homeassistant,
            "homeassistant.helpers": helpers,
            "homeassistant.components": components,
            "homeassistant.exceptions": exceptions,
            "homeassistant.config_entries": config_entries,
            "homeassistant.core": core,
            "homeassistant.const": const,
            "homeassistant.helpers.update_coordinator": update_coordinator,
            "homeassistant.helpers.device_registry": device_registry,
            "homeassistant.components.sensor": sensor_module,
            "homeassistant.components.binary_sensor": binary_module,
            "homeassistant.components.switch": switch_module,
            "homeassistant.components.select": select_module,
            "homeassistant.components.number": number_module,
        }
    )


_install_home_assistant_stubs()
from homeassistant.const import EntityCategory

CUSTOM_COMPONENTS = Path(__file__).resolve().parents[1] / "custom_components"
sys.path.insert(0, str(CUSTOM_COMPONENTS))

from heiko_w600.binary_sensor import BINARY_SENSORS, HeikoBinarySensor
from heiko_w600.coordinator import HeikoCoordinator
from heiko_w600.protocol import FrameParser, crc16_heiko
from heiko_w600.parameters import WRITABLE, validate_value
from heiko_w600.switch import HeikoSwitch
from heiko_w600.select import HeikoSelect
from heiko_w600.number import HeikoNumber
from homeassistant.exceptions import HomeAssistantError
from heiko_w600.sensor import SENSORS, HeikoSensor


DEVICE_ID = b"DEVICE"
OTHER_DEVICE_ID = b"OTHER!"


def make_frame(
    direction: str,
    command: int,
    payload: bytes,
    device_id: bytes = DEVICE_ID,
) -> bytes:
    """Build one synthetic device frame for an offline loopback test."""
    if direction == "unit_to_cloud":
        header, seed = b"\xaa\x55", 0x40FD
    else:
        header, seed = b"\x55\xaa", 0xBF02
    declared_length = 1 + len(payload)
    body = (
        header
        + b"\x00"
        + device_id
        + b"\x00"
        + declared_length.to_bytes(2, "little")
        + bytes([command])
        + payload
    )
    checksum = crc16_heiko(body, seed)
    return body + checksum.to_bytes(2, "little") + b"\x3a"


def make_realtime_payload(
    *,
    all_sentinels: bool = False,
    flow_temperature: float = 34.5,
    compressor_frequency: float = 45.0,
) -> bytes:
    values = [-99.0 if all_sentinels else 0.0 for _ in range(43)]
    if not all_sentinels:
        values[3] = flow_temperature  # par04
        values[4] = 29.25  # par05
        values[5] = 18.25  # par06
        values[6] = -99.0  # par07 unavailable on this synthetic device
        values[7] = 32.25  # par08
        values[8] = 20.5  # par09
        values[9] = -99.0  # par10 unavailable on this synthetic device
        values[10] = 23.75  # par11
        values[14] = 1.0  # par15 flow switch
        values[19] = compressor_frequency  # par20
        values[20] = 350.0  # par21 expansion valve steps
        values[21] = 24.5  # par22 high-side pressure, bar
        values[22] = 10.3  # par23 low-side pressure, bar
        values[23] = 8.75  # par24
        values[24] = 60.0  # par25 compressor discharge temperature
        values[25] = 12.0  # par26 compressor suction temperature
        values[26] = 40.0  # par27 outdoor heat exchanger temperature
        values[27] = 600.0  # par28 outdoor fan 1 rpm
        values[28] = 0.0  # par29 optional fan 2 stopped / valid zero
        values[29] = 4.5  # par30
        values[30] = 230.0  # par31
        values[31] = 0.0  # par32 defrost
        values[32] = 1.0  # par33 pump P0
        values[33] = 1.0  # par34 pump P1
        values[34] = 0.0  # par35 pump P2
        values[35] = 36.0  # par36 effective target
    return b"\x00" * 10 + struct.pack("<43f", *values)


def make_settings_payload() -> bytes:
    values = [0.0] * 138
    values[0] = 1.0
    return b"\x00\x00" + struct.pack("<138f", *values)


async def wait_until(predicate, timeout: float = 2.0) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() >= deadline:
            raise AssertionError("condition did not become true before timeout")
        await asyncio.sleep(0.005)


class HeikoRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_cloud_switch_persists_without_a_device_and_survives_restart(self):
        from heiko_w600.switch import HeikoCloudForwardingSwitch
        switch = HeikoCloudForwardingSwitch(self.coordinator, self.entry.entry_id)
        self.assertTrue(switch.available)
        self.assertTrue(switch.is_on)
        self.entry.options = {"stale_seconds": 60}
        await switch.async_turn_off()
        self.assertFalse(switch.is_on)
        self.assertEqual(self.entry.options, {"stale_seconds": 60, "upstream_enabled": False})
        restored = HeikoCoordinator(self.hass, self.entry)
        self.assertFalse(restored.upstream_enabled)
        self.assertEqual(restored.stale_seconds, 60)
        self.assertEqual(self.upstream_connection_count, 0)

    async def test_local_mode_acknowledges_valid_frames_and_never_opens_cloud(self):
        await self.coordinator.async_set_upstream_enabled(False)
        reader, writer = await asyncio.open_connection("127.0.0.1", self.coordinator.listen_port)
        await wait_until(lambda: self.coordinator.connected)
        frame = make_frame("unit_to_cloud", 1, make_realtime_payload())
        bad_crc = bytearray(frame)
        bad_crc[-3] ^= 1
        writer.write(bad_crc)
        await writer.drain()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(reader.read(1), .05)
        # Fragmented input must get one ACK only after a complete validated frame.
        writer.write(frame[:15])
        await writer.drain()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(reader.read(1), .05)
        writer.write(frame[15:] + make_frame("unit_to_cloud", 2, make_settings_payload()))
        await writer.drain()
        parser = FrameParser()
        acknowledgements = []
        while len(acknowledgements) < 2:
            acknowledgements.extend(parser.feed(await asyncio.wait_for(reader.read(512), 1)))
        self.assertEqual([f.command for f in acknowledgements], [3, 4])
        self.assertTrue(all(f.direction == "cloud_to_unit" and f.device_id == DEVICE_ID and not f.payload
                            for f in acknowledgements))
        self.assertTrue(self.coordinator.is_realtime_fresh)
        self.assertTrue(self.coordinator.is_settings_fresh)
        self.assertEqual(self.upstream_connection_count, 0)
        self.assertEqual(self.coordinator.bytes_to_cloud, 0)
        writer.close()
        await writer.wait_closed()

    async def test_toggle_cloud_in_both_directions_preserves_the_w600_socket(self):
        reader, writer = await self._connect_w600()
        generation = self.coordinator._active_generation
        await self.coordinator.async_set_upstream_enabled(False)
        self.assertTrue(self.coordinator.connected)
        self.assertIsNone(self.coordinator._upstream_writer)
        frame = make_frame("unit_to_cloud", 1, make_realtime_payload())
        writer.write(frame)
        await writer.drain()
        ack = FrameParser().feed(await asyncio.wait_for(reader.read(512), 1))[0]
        self.assertEqual(ack.command, 3)
        self.assertEqual(self.forwarded_to_upstream, b"")
        fresh = self.coordinator.last_realtime
        await self.coordinator.async_set_upstream_enabled(True)
        await wait_until(lambda: self.upstream_connection_count == 2 and self.coordinator._upstream_writer is not None)
        self.assertEqual(self.coordinator._active_generation, generation)
        self.assertEqual(self.coordinator.last_realtime, fresh)
        writer.write(frame)
        await writer.drain()
        await wait_until(lambda: self.forwarded_to_upstream == frame)
        cloud_ack = make_frame("cloud_to_unit", 3, b"")
        await self._send_from_upstream(cloud_ack)
        self.assertEqual(await asyncio.wait_for(reader.readexactly(len(cloud_ack)), 1), cloud_ack)
        await self.coordinator.async_set_upstream_enabled(False)
        writer.write(frame)
        await writer.drain()
        self.assertEqual(FrameParser().feed(await asyncio.wait_for(reader.read(512), 1))[0].command, 3)
        self.assertEqual(self.forwarded_to_upstream, frame)
        writer.close()
        await writer.wait_closed()

    async def test_local_mode_parameter_write_still_requires_fresh_readback(self):
        await self.coordinator.async_set_upstream_enabled(False)
        reader, writer = await asyncio.open_connection("127.0.0.1", self.coordinator.listen_port)
        await wait_until(lambda: self.coordinator.connected)
        writer.write(make_frame("unit_to_cloud", 2, make_settings_payload()))
        await writer.drain()
        ack = FrameParser().feed(await asyncio.wait_for(reader.read(512), 1))[0]
        self.assertEqual(ack.command, 4)
        task = asyncio.create_task(self.coordinator.async_write_parameter(0, 0))
        parser = FrameParser()
        commands = []
        while len(commands) < 2:
            commands.extend(parser.feed(await asyncio.wait_for(reader.read(512), 2)))
        self.assertEqual([f.command for f in commands], [5, 7])
        self.assertFalse(task.done())
        payload = bytearray(make_settings_payload())
        struct.pack_into("<f", payload, 2, 0.)
        writer.write(make_frame("unit_to_cloud", 2, payload))
        await writer.drain()
        await asyncio.wait_for(task, 1)
        self.assertEqual(self.coordinator.settings["setting_000"], 0.)
        self.assertEqual(self.upstream_connection_count, 0)
        writer.close()
        await writer.wait_closed()

    def test_dashboard_short_names_and_cloud_switch_use_stable_registry_ids(self):
        from heiko_w600.dashboard import build_dashboard
        entities = [SimpleNamespace(unique_id="x_par04", entity_id="sensor.renamed_flow",
                     config_entry_id="x", disabled_by=None, original_name="HEIKO W600 Vorlauftemperatur"),
                    SimpleNamespace(unique_id="x_upstream_enabled", entity_id="switch.renamed_cloud",
                     config_entry_id="x", disabled_by=None, original_name="HEIKO W600 Weiterleitung an MyHeatPump")]
        dashboard = build_dashboard("x", entities)
        rows = [row for view in dashboard["views"] for card in view["cards"] for row in card.get("entities", [])]
        self.assertTrue(all("HEIKO W600" not in row["name"] for row in rows))
        self.assertIn({"entity": "sensor.renamed_flow", "name": "Vorlauftemperatur"}, rows)
        self.assertEqual(sum(row["entity"] == "switch.renamed_cloud" for row in rows), 3)

    def test_read_only_catalog_sensors_use_ha_supported_category(self):
        from heiko_w600.parameters import CATALOG
        from heiko_w600.sensor import HeikoSettingSensor
        definitions = [item for item in CATALOG if not item["writable"]]
        self.assertEqual(len(definitions), 3)
        for item in definitions:
            sensor = HeikoSettingSensor(self.coordinator, "x", item)
            self.assertNotEqual(sensor._attr_entity_category, EntityCategory.CONFIG)
            self.assertEqual(sensor._attr_entity_category, EntityCategory.DIAGNOSTIC)

    async def test_read_buttons_send_only_cmd06_cmd07_and_preserve_freshness(self):
        reader, writer = await self._connect_w600()
        await self.coordinator.async_request_data(6)
        await self.coordinator.async_request_data(7)
        parser = FrameParser()
        frames = []
        while len(frames) < 2:
            frames.extend(parser.feed(await asyncio.wait_for(reader.read(128), 2)))
        self.assertEqual([frame.command for frame in frames], [6, 7])
        self.assertTrue(all(frame.direction == "cloud_to_unit" for frame in frames))
        self.assertTrue(all(frame.device_id == bytes(6) for frame in frames))
        self.assertIsNone(self.coordinator.last_realtime)
        self.assertIsNone(self.coordinator.last_settings)
        with self.assertRaises(HomeAssistantError):
            await self.coordinator.async_request_data(5)
        writer.close()
        await writer.wait_closed()

    def test_options_override_saved_connection_without_changing_entry(self):
        entry = SimpleNamespace(data=self.entry.data, options={"stale_seconds": 240})
        coordinator = HeikoCoordinator(self.hass, entry)
        self.assertEqual(coordinator.stale_seconds, 240)
        self.assertEqual(self.entry.data["stale_seconds"], 30)

    def test_dashboard_includes_every_catalog_parameter_with_renamed_ids(self):
        from heiko_w600.dashboard import build_dashboard
        from heiko_w600.parameters import CATALOG
        entities = [SimpleNamespace(unique_id=f"x_setting_{p['settingIndex']:03d}",
                     entity_id=f"number.renamed_{p['settingIndex']}",
                     config_entry_id="x", disabled_by=None) for p in CATALOG]
        entities.append(SimpleNamespace(unique_id="x_setting_000", entity_id="switch.other",
                         config_entry_id="other", disabled_by=None))
        dashboard = build_dashboard("x", entities)
        parameter_cards = dashboard["views"][1]["cards"]
        displayed = [row["entity"] for card in parameter_cards for row in card.get("entities", [])]
        self.assertEqual(set(displayed), {e.entity_id for e in entities[:-1]})
        self.assertEqual(len(displayed), 128)
        self.assertNotIn("switch.other", displayed)

    def test_bridge_diagnostics_visible_without_device(self):
        from heiko_w600.bridge_sensor import HeikoBridgeSensor
        sensor = HeikoBridgeSensor(self.coordinator, "x", "connection_state", "State", None)
        self.assertTrue(sensor.available)
        self.assertEqual("waiting", sensor.native_value)
        self.assertFalse(sensor.extra_state_attributes["w600_verbunden"])

    async def asyncSetUp(self) -> None:
        self.forwarded_to_upstream = bytearray()
        self.upstream_writer: asyncio.StreamWriter | None = None
        self.upstream_writers: set[asyncio.StreamWriter] = set()
        self.upstream_connected = asyncio.Event()
        self.upstream_connection_count = 0

        self.upstream_server = await asyncio.start_server(
            self._handle_upstream, "127.0.0.1", 0
        )
        self.upstream_port = self.upstream_server.sockets[0].getsockname()[1]

        self.entry = SimpleNamespace(
            entry_id="offline-test-entry",
            options={},
            data={
                "listen_host": "127.0.0.1",
                "listen_port": 0,
                "upstream_host": "127.0.0.1",
                "upstream_port": self.upstream_port,
                "stale_seconds": 30,
            },
        )
        def update_entry(entry, *, options):
            entry.options = options
        self.hass = SimpleNamespace(data={}, config_entries=SimpleNamespace(async_update_entry=update_entry))
        self.coordinator = HeikoCoordinator(self.hass, self.entry)
        self.coordinator._watchdog_interval = 0.01
        await self.coordinator.async_start()

    async def asyncTearDown(self) -> None:
        await asyncio.wait_for(self.coordinator.async_stop(), timeout=3.0)
        self.upstream_server.close()
        await self.upstream_server.wait_closed()
        for writer in tuple(self.upstream_writers):
            writer.close()
        await asyncio.gather(
            *(writer.wait_closed() for writer in self.upstream_writers),
            return_exceptions=True,
        )

    async def _handle_upstream(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self.upstream_writer = writer
        self.upstream_connection_count += 1
        self.upstream_writers.add(writer)
        self.upstream_connected.set()
        try:
            while chunk := await reader.read(4096):
                self.forwarded_to_upstream.extend(chunk)
        finally:
            self.upstream_writers.discard(writer)
            writer.close()

    async def _connect_w600(self):
        expected_upstream_count = self.upstream_connection_count + 1
        reader, writer = await asyncio.open_connection(
            "127.0.0.1", self.coordinator.listen_port
        )
        await wait_until(
            lambda: self.upstream_connection_count >= expected_upstream_count
            and self.coordinator.connected
        )
        return reader, writer

    async def test_catalog_write_requires_new_cmd02_readback(self) -> None:
        reader, writer = await self._connect_w600()
        with self.assertRaises(HomeAssistantError):
            await self.coordinator.async_write_parameter(0, 0)
        writer.write(make_frame("unit_to_cloud", 0x02, make_settings_payload()))
        await writer.drain()
        await wait_until(lambda: self.coordinator.is_settings_fresh)

        task = asyncio.create_task(self.coordinator.async_write_parameter(0, 0))
        parser = FrameParser()
        commands = []
        while len(commands) < 2:
            commands.extend(parser.feed(await asyncio.wait_for(reader.read(512), 2)))
        self.assertEqual([item.command for item in commands], [0x05, 0x07])
        self.assertEqual(commands[0].payload, struct.pack("<Hf", 0, 0))
        self.assertEqual(commands[0].device_id, DEVICE_ID)
        self.assertEqual(commands[1].device_id, bytes(6))
        self.assertEqual(self.coordinator.settings["setting_000"], 1.0)

        updated = bytearray(make_settings_payload())
        struct.pack_into("<f", updated, 2, 0.0)
        writer.write(make_frame("unit_to_cloud", 0x02, updated))
        await writer.drain()
        await asyncio.wait_for(task, 2)
        self.assertEqual(self.coordinator.settings["setting_000"], 0.0)
        self.assertNotIn(bytes([0x55, 0xAA]), self.forwarded_to_upstream)
        writer.close()
        await writer.wait_closed()

    async def test_upstream_write_blocks_local_write_until_settings_reply(self) -> None:
        _reader, writer = await self._connect_w600()
        writer.write(make_frame("unit_to_cloud", 0x02, make_settings_payload()))
        await writer.drain()
        await wait_until(lambda: self.coordinator.is_settings_fresh)
        await self._send_from_upstream(make_frame("cloud_to_unit", 0x05, struct.pack("<Hf", 0, 1)))
        await wait_until(lambda: self.coordinator._cloud_write_at is not None)
        with self.assertRaises(HomeAssistantError):
            await self.coordinator.async_write_parameter(0, 0)
        writer.write(make_frame("unit_to_cloud", 0x02, make_settings_payload()))
        await writer.drain()
        await wait_until(lambda: self.coordinator._cloud_write_at is None)
        writer.close()
        await writer.wait_closed()

    async def test_catalog_validation(self) -> None:
        self.assertEqual(len(WRITABLE), 125)
        self.assertEqual(
            (sum(x["type"] == "boolean" for x in WRITABLE),
             sum(x["pageControl"] == "select" and x["type"] == "number" for x in WRITABLE),
             sum(x["pageControl"] == "number" for x in WRITABLE)),
            (41, 14, 70),
        )
        power = next(x for x in WRITABLE if x["settingIndex"] == 0)
        with self.assertRaises(HomeAssistantError):
            validate_value(power, 2)
        mode = next(x for x in WRITABLE if x["settingIndex"] == 3)
        with self.assertRaises(HomeAssistantError):
            validate_value(mode, 99)
        bounded = next(x for x in WRITABLE if x["settingIndex"] == 10)
        with self.assertRaises(HomeAssistantError):
            validate_value(bounded, 1000)
        entities = [
            (HeikoSwitch if item["type"] == "boolean" else
             HeikoSelect if item["pageControl"] == "select" else HeikoNumber)(
                 self.coordinator, self.entry.entry_id, item
             ) for item in WRITABLE
        ]
        self.assertEqual(len({entity.unique_id for entity in entities}), 125)
        self.assertTrue(all(entity.has_entity_name for entity in entities))
        self.assertTrue(all(not entity.available for entity in entities))

    async def _send_from_upstream(self, frame: bytes) -> None:
        await wait_until(lambda: self.upstream_writer is not None)
        assert self.upstream_writer is not None
        self.upstream_writer.write(frame)
        await self.upstream_writer.drain()

    def _sensor(self, key: str) -> HeikoSensor:
        description = next(item for item in SENSORS if item.key == key)
        return HeikoSensor(self.coordinator, self.entry.entry_id, description)

    def _binary_sensor(self, key: str) -> HeikoBinarySensor:
        description = next(item for item in BINARY_SENSORS if item.key == key)
        return HeikoBinarySensor(self.coordinator, self.entry.entry_id, description)

    def test_sensor_catalog_matches_entity_mapping(self) -> None:
        expected = {
            "par04": ("temperature", "°C"),
            "par05": ("temperature", "°C"),
            "par06": ("temperature", "°C"),
            "par07": ("temperature", "°C"),
            "par08": ("temperature", "°C"),
            "par09": ("temperature", "°C"),
            "par10": ("temperature", "°C"),
            "par11": ("temperature", "°C"),
            "par20": ("frequency", "Hz"),
            "par21": (None, None),
            "par22": ("pressure", "bar"),
            "par23": ("pressure", "bar"),
            "par24": ("temperature", "°C"),
            "par25": ("temperature", "°C"),
            "par26": ("temperature", "°C"),
            "par27": ("temperature", "°C"),
            "par28": (None, "rpm"),
            "par29": (None, "rpm"),
            "par30": ("current", "A"),
            "par31": ("voltage", "V"),
            "par36": ("temperature", "°C"),
        }
        actual = {
            description.key: (
                description.device_class.value
                if description.device_class is not None
                else None,
                description.native_unit_of_measurement,
            )
            for description in SENSORS
        }
        self.assertEqual({k: actual[k] for k in expected}, expected)
        self.assertEqual(actual["par12"], ("voltage", "V"))
        self.assertEqual(actual["par39"], (None, "K"))
        self.assertEqual(actual["par41"], (None, "min"))
        self.assertEqual(len(SENSORS), 32)
        for description in SENSORS:
            entity = HeikoSensor(
                self.coordinator, self.entry.entry_id, description
            )
            self.assertEqual(
                entity.unique_id,
                f"{self.entry.entry_id}_{description.key}",
            )
            self.assertEqual(description.translation_key, description.key)
            self.assertIsNone(description.name)
            self.assertTrue(entity.has_entity_name)
            self.assertFalse(hasattr(entity, "_attr_name"))
            self.assertEqual(
                entity.device_info,
                {
                    "identifiers": {("heiko_w600", self.entry.entry_id)},
                    "name": "HEIKO W600",
                },
            )
        self.assertEqual(
            next(item for item in SENSORS if item.key == "par21").entity_category,
            EntityCategory.DIAGNOSTIC,
        )
        self._assert_translation_catalog("sensor", SENSORS)

    def test_binary_sensor_translations_and_device_grouping(self) -> None:
        self.assertEqual(len(BINARY_SENSORS), 6)
        for description in BINARY_SENSORS:
            entity = self._binary_sensor(description.key)
            self.assertEqual(description.translation_key, description.key)
            self.assertIsNone(description.name)
            self.assertTrue(entity.has_entity_name)
            self.assertFalse(hasattr(entity, "_attr_name"))
            self.assertEqual(
                entity.unique_id,
                f"{self.entry.entry_id}_{description.key}",
            )
            self.assertEqual(
                entity.device_info,
                {
                    "identifiers": {("heiko_w600", self.entry.entry_id)},
                    "name": "HEIKO W600",
                },
            )
        self._assert_translation_catalog("binary_sensor", BINARY_SENSORS)

    def _assert_translation_catalog(self, platform: str, descriptions) -> None:
        integration_path = CUSTOM_COMPONENTS / "heiko_w600"
        expected = {description.key for description in descriptions}
        for path in (
            integration_path / "translations" / "en.json",
            integration_path / "translations" / "de.json",
        ):
            with self.subTest(translation_file=path.name):
                translations = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(expected <= set(translations["entity"][platform]))

    async def test_proxy_is_transparent_and_decodes_valid_cmd01(self) -> None:
        client_reader, client_writer = await self._connect_w600()

        # A cloud-originated acknowledgement is forwarded but cannot claim identity.
        ack = make_frame("cloud_to_unit", 0x03, b"", OTHER_DEVICE_ID)
        await self._send_from_upstream(ack)
        self.assertEqual(
            await asyncio.wait_for(client_reader.readexactly(len(ack)), timeout=1.0),
            ack,
        )
        self.assertIsNone(self.coordinator._bound_device_id)

        frame = make_frame(
            "unit_to_cloud", 0x01, make_realtime_payload(), DEVICE_ID
        )
        split = len(frame) // 2
        client_writer.write(frame[:split])
        await client_writer.drain()
        await asyncio.sleep(0.02)
        self.assertIsNone(self.coordinator.last_realtime)

        client_writer.write(frame[split:])
        await client_writer.drain()
        await wait_until(lambda: self.coordinator.last_realtime is not None)
        await wait_until(
            lambda: bytes(self.forwarded_to_upstream).find(frame) >= 0
        )

        self.assertEqual(self.coordinator._bound_device_id, DEVICE_ID)
        self.assertAlmostEqual(self._sensor("par04").native_value, 34.5, places=3)
        self.assertTrue(self._sensor("par04").available)
        self.assertEqual(
            self._sensor("par04").unique_id,
            "offline-test-entry_par04",
        )
        self.assertAlmostEqual(self._sensor("par05").native_value, 29.25, places=3)
        self.assertAlmostEqual(self._sensor("par06").native_value, 18.25, places=3)
        self.assertAlmostEqual(self._sensor("par08").native_value, 32.25, places=3)
        self.assertAlmostEqual(self._sensor("par09").native_value, 20.5, places=3)
        self.assertAlmostEqual(self._sensor("par11").native_value, 23.75, places=3)
        for optional_key in ("par07", "par10"):
            self.assertFalse(self._sensor(optional_key).available)
            self.assertIsNone(self._sensor(optional_key).native_value)
        self.assertAlmostEqual(self._sensor("par21").native_value, 350.0, places=3)
        self.assertAlmostEqual(self._sensor("par22").native_value, 24.5, places=3)
        self.assertAlmostEqual(self._sensor("par23").native_value, 10.3, places=3)
        self.assertAlmostEqual(self._sensor("par24").native_value, 8.75, places=3)
        self.assertAlmostEqual(self._sensor("par25").native_value, 60.0, places=3)
        self.assertAlmostEqual(self._sensor("par26").native_value, 12.0, places=3)
        self.assertAlmostEqual(self._sensor("par27").native_value, 40.0, places=3)
        self.assertAlmostEqual(self._sensor("par28").native_value, 600.0, places=3)
        self.assertEqual(self._sensor("par29").native_value, 0.0)
        self.assertAlmostEqual(self._sensor("par30").native_value, 4.5, places=3)
        self.assertAlmostEqual(self._sensor("par31").native_value, 230.0, places=3)
        self.assertAlmostEqual(self._sensor("par36").native_value, 36.0, places=3)
        self.assertTrue(self._binary_sensor("par15").is_on)
        self.assertTrue(self._binary_sensor("par33").is_on)
        self.assertFalse(self._binary_sensor("par32").is_on)
        self.assertTrue(self._binary_sensor("compressor_running").is_on)

        # CMD02 remains available to the coordinator but is not exposed as an entity.
        settings = make_frame(
            "unit_to_cloud", 0x02, make_settings_payload(), DEVICE_ID
        )
        client_writer.write(settings)
        await client_writer.drain()
        await wait_until(lambda: self.coordinator.last_settings is not None)
        self.assertEqual(self.coordinator.settings["setting_000"], 1.0)
        self.assertEqual(len(SENSORS), 32)

        # Upstream bytes travel back unchanged as well.
        cloud_bytes = make_frame("cloud_to_unit", 0x03, b"", DEVICE_ID)
        await self._send_from_upstream(cloud_bytes)
        self.assertEqual(
            await asyncio.wait_for(
                client_reader.readexactly(len(cloud_bytes)), timeout=1.0
            ),
            cloud_bytes,
        )
        client_writer.close()
        await client_writer.wait_closed()

    async def test_bad_crc_sentinels_malformed_and_other_identity_do_not_refresh(self):
        _reader, client_writer = await self._connect_w600()

        valid_payload = make_realtime_payload()
        bad_crc = bytearray(
            make_frame("unit_to_cloud", 0x01, valid_payload, DEVICE_ID)
        )
        bad_crc[-3] ^= 0x01
        client_writer.write(bad_crc)
        await client_writer.drain()
        await wait_until(lambda: len(self.forwarded_to_upstream) >= len(bad_crc))
        self.assertIsNone(self.coordinator.last_realtime)
        self.assertIsNone(self.coordinator._bound_device_id)

        all_sentinels = make_frame(
            "unit_to_cloud",
            0x01,
            make_realtime_payload(all_sentinels=True),
            DEVICE_ID,
        )
        client_writer.write(all_sentinels)
        await client_writer.drain()
        await asyncio.sleep(0.03)
        self.assertIsNone(self.coordinator.last_realtime)
        self.assertIsNone(self.coordinator._bound_device_id)

        malformed = make_frame("unit_to_cloud", 0x01, b"short", DEVICE_ID)
        client_writer.write(malformed)
        await client_writer.drain()
        await asyncio.sleep(0.03)
        self.assertIsNone(self.coordinator.last_realtime)
        self.assertIsNone(self.coordinator._bound_device_id)

        good = make_frame(
            "unit_to_cloud", 0x01, valid_payload, DEVICE_ID
        )
        client_writer.write(good)
        await client_writer.drain()
        await wait_until(lambda: self.coordinator.last_realtime is not None)
        accepted_at = self.coordinator.last_realtime
        accepted_value = self.coordinator.realtime["par04"]

        other_identity = make_frame(
            "unit_to_cloud",
            0x01,
            make_realtime_payload(flow_temperature=99.0),
            OTHER_DEVICE_ID,
        )
        client_writer.write(other_identity)
        await client_writer.drain()
        await asyncio.sleep(0.03)
        self.assertEqual(self.coordinator.last_realtime, accepted_at)
        self.assertEqual(self.coordinator.realtime["par04"], accepted_value)

        client_writer.close()
        await client_writer.wait_closed()

    async def test_staleness_disconnect_reconnect_and_unload(self) -> None:
        client_reader, client_writer = await self._connect_w600()
        first = make_frame(
            "unit_to_cloud", 0x01, make_realtime_payload(), DEVICE_ID
        )
        client_writer.write(first)
        await client_writer.drain()
        await wait_until(lambda: self.coordinator.last_realtime is not None)
        sensor = self._sensor("par04")
        self.assertTrue(sensor.available)

        last_valid = self.coordinator.last_realtime
        self.coordinator._last_realtime = datetime.now(
            timezone.utc
        ) - timedelta(seconds=self.coordinator.stale_seconds + 1)
        await wait_until(lambda: self.coordinator.data["realtime_fresh"] is False)
        self.assertFalse(sensor.available)
        self.assertNotEqual(self.coordinator.last_realtime, None)
        self.assertNotEqual(self.coordinator.last_realtime, last_valid)

        second = make_frame(
            "unit_to_cloud", 0x01, make_realtime_payload(flow_temperature=35.0), DEVICE_ID
        )
        client_writer.write(second)
        await client_writer.drain()
        await wait_until(
            lambda: self.coordinator.is_realtime_fresh
            and self.coordinator.realtime["par04"] == 35.0
        )
        self.assertTrue(sensor.available)

        client_writer.close()
        await client_writer.wait_closed()
        await wait_until(lambda: not self.coordinator.connected)
        self.assertFalse(sensor.available)

        reconnect_reader, reconnect_writer = await self._connect_w600()
        third = make_frame(
            "unit_to_cloud", 0x01, make_realtime_payload(flow_temperature=32.0), DEVICE_ID
        )
        reconnect_writer.write(third)
        await reconnect_writer.drain()
        await wait_until(
            lambda: self.coordinator.is_realtime_fresh
            and self.coordinator.realtime["par04"] == 32.0
        )
        self.assertTrue(sensor.available)

        await asyncio.wait_for(self.coordinator.async_stop(), timeout=3.0)
        self.assertIsNone(self.coordinator._server)
        self.assertFalse(self.coordinator.connected)
        self.assertFalse(sensor.available)
        with self.assertRaises(OSError):
            await asyncio.open_connection(
                "127.0.0.1", self.coordinator.listen_port
            )
        reconnect_writer.close()
        await reconnect_writer.wait_closed()



if __name__ == "__main__":
    unittest.main()
