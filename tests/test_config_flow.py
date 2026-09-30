"""Offline unit tests for HEIKO W600 config entry setup.

The test loads the integration in an isolated namespace with tiny Home Assistant
and voluptuous stubs. It exercises input validation and setup/unload orchestration
without installing Home Assistant or opening network connections.
"""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_PATH = PROJECT_ROOT / "custom_components" / "heiko_w600"
TEST_PACKAGE = "_heiko_w600_offline_test"


class _FakeRequired:
    def __init__(self, key: str, default: object = None) -> None:
        self.key = key
        self.default = default


class _FakeSchema:
    def __init__(self, schema: dict[object, object]) -> None:
        self.schema = schema


class _FakeConfigFlow:
    def __init_subclass__(cls, *, domain: str | None = None, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.domain = domain

    def __init__(self) -> None:
        self.current_entries: list[object] = []
        self.unique_id: str | None = None

    async def async_set_unique_id(self, unique_id: str) -> None:
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self) -> None:
        return None

    def _async_current_entries(self) -> list[object]:
        return self.current_entries

    def async_abort(self, *, reason: str) -> dict[str, object]:
        return {"type": "abort", "reason": reason}

    def async_show_form(
        self,
        *,
        step_id: str,
        data_schema: object,
        errors: dict[str, str],
    ) -> dict[str, object]:
        return {
            "type": "form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors,
        }

    def async_create_entry(
        self, *, title: str, data: dict[str, str | int]
    ) -> dict[str, object]:
        return {"type": "create_entry", "title": title, "data": data}


class _FakeCoordinator:
    instances: list["_FakeCoordinator"] = []

    def __init__(self, hass: object, entry: object) -> None:
        self.hass = hass
        self.entry = entry
        self.started = False
        self.stopped = False
        type(self).instances.append(self)

    async def async_start(self) -> None:
        self.started = True

    async def async_stop(self) -> None:
        self.stopped = True


def _load_isolated_integration() -> tuple[types.ModuleType, types.ModuleType]:
    """Load the package with test-only imports, without modifying global HA modules."""
    module_names = (
        "homeassistant",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.core",
        "voluptuous",
    )
    missing = object()
    saved = {name: sys.modules.get(name, missing) for name in module_names}

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []  # type: ignore[attr-defined]

    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object  # type: ignore[attr-defined]
    config_entries.OptionsFlowWithReload = _FakeConfigFlow
    config_entries.ConfigFlow = _FakeConfigFlow  # type: ignore[attr-defined]
    config_entries.ConfigFlowResult = dict[str, object]  # type: ignore[attr-defined]

    const = types.ModuleType("homeassistant.const")

    class Platform:
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"
        SELECT = "select"
        NUMBER = "number"
        BUTTON = "button"

    const.Platform = Platform  # type: ignore[attr-defined]

    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object  # type: ignore[attr-defined]

    voluptuous = types.ModuleType("voluptuous")
    voluptuous.Required = _FakeRequired  # type: ignore[attr-defined]
    voluptuous.Schema = _FakeSchema  # type: ignore[attr-defined]

    homeassistant.config_entries = config_entries  # type: ignore[attr-defined]
    homeassistant.const = const  # type: ignore[attr-defined]
    homeassistant.core = core  # type: ignore[attr-defined]

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.const"] = const
    sys.modules["homeassistant.core"] = core
    sys.modules["voluptuous"] = voluptuous

    coordinator_module = types.ModuleType(f"{TEST_PACKAGE}.coordinator")
    coordinator_module.HeikoCoordinator = _FakeCoordinator  # type: ignore[attr-defined]
    sys.modules[coordinator_module.__name__] = coordinator_module

    try:
        package_spec = importlib.util.spec_from_file_location(
            TEST_PACKAGE,
            INTEGRATION_PATH / "__init__.py",
            submodule_search_locations=[str(INTEGRATION_PATH)],
        )
        if package_spec is None or package_spec.loader is None:
            raise RuntimeError("Could not load the integration package for tests")
        package = importlib.util.module_from_spec(package_spec)
        sys.modules[TEST_PACKAGE] = package
        package_spec.loader.exec_module(package)

        flow_spec = importlib.util.spec_from_file_location(
            f"{TEST_PACKAGE}.config_flow",
            INTEGRATION_PATH / "config_flow.py",
        )
        if flow_spec is None or flow_spec.loader is None:
            raise RuntimeError("Could not load config_flow.py for tests")
        flow_module = importlib.util.module_from_spec(flow_spec)
        sys.modules[flow_spec.name] = flow_module
        flow_spec.loader.exec_module(flow_module)
        return package, flow_module
    finally:
        for name, previous in saved.items():
            if previous is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous  # type: ignore[assignment]


INTEGRATION, FLOW = _load_isolated_integration()


def _input(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "listen_host": "0.0.0.0",
        "listen_port": "8899",
        "upstream_host": "www.myheatpump.com",
        "upstream_port": "18899",
        "stale_seconds": "180",
    }
    values.update(overrides)
    return values


class ConfigValidationTests(unittest.TestCase):
    def test_normalizes_hosts_and_ports_and_discards_extra_values(self) -> None:
        config = FLOW.validate_config(
            _input(
                upstream_host="Pump.Example.",
                listen_port="00089",
                stale_seconds="3600",
                password="must not be stored",
            )
        )

        self.assertEqual(config["upstream_host"], "pump.example")
        self.assertEqual(config["listen_port"], 89)
        self.assertEqual(config["stale_seconds"], 3600)
        self.assertEqual(set(config), {
            "upstream_enabled",
            "listen_host",
            "listen_port",
            "upstream_host",
            "upstream_port",
            "stale_seconds",
        })

    def test_accepts_ipv6_without_resolving_it(self) -> None:
        config = FLOW.validate_config(_input(upstream_host="2001:db8::5"))
        self.assertEqual(config["upstream_host"], "2001:db8::5")

    def test_rejects_url_and_ambiguous_numeric_hosts(self) -> None:
        for value in ("tcp://pump.example", "999.999.999.999", "user@pump.example"):
            with self.subTest(value=value):
                with self.assertRaises(FLOW.ConfigFlowValidationError) as raised:
                    FLOW.validate_config(_input(listen_host=value))
                self.assertEqual(raised.exception.error_code, "invalid_listen_host")

    def test_rejects_invalid_tcp_ports(self) -> None:
        for field, value, error in (
            ("listen_port", "0", "invalid_listen_port"),
            ("listen_port", "65536", "invalid_listen_port"),
            ("upstream_port", "-1", "invalid_upstream_port"),
            ("upstream_port", "18899.5", "invalid_upstream_port"),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(FLOW.ConfigFlowValidationError) as raised:
                    FLOW.validate_config(_input(**{field: value}))
                self.assertEqual(raised.exception.error_code, error)

    def test_stale_threshold_includes_only_contract_range(self) -> None:
        for value in ("29", "3601", "1.5"):
            with self.subTest(value=value):
                with self.assertRaises(FLOW.ConfigFlowValidationError) as raised:
                    FLOW.validate_config(_input(stale_seconds=value))
                self.assertEqual(raised.exception.error_code, "invalid_stale_seconds")

        self.assertEqual(FLOW.validate_config(_input(stale_seconds="30"))["stale_seconds"], 30)
        self.assertEqual(FLOW.validate_config(_input(stale_seconds="3600"))["stale_seconds"], 3600)

    def test_flow_returns_form_error_without_endpoint_access(self) -> None:
        flow = FLOW.HeikoW600ConfigFlow()
        result = _run(flow.async_step_user(_input(upstream_port="not-a-port")))

        self.assertEqual(result["type"], "form")
        self.assertEqual(result["errors"], {"base": "invalid_upstream_port"})
        self.assertEqual(flow.unique_id, "heiko_w600_single_instance")

    def test_flow_creates_one_sanitized_entry(self) -> None:
        flow = FLOW.HeikoW600ConfigFlow()
        result = _run(flow.async_step_user(_input(password="not retained")))

        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["title"], "HEIKO W600")
        self.assertNotIn("password", result["data"])


class SetupLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        _FakeCoordinator.instances.clear()

    async def test_setup_starts_coordinator_and_loads_read_only_platforms(self) -> None:
        manager = _FakeConfigEntries()
        hass = _FakeHass(manager)
        entry = _FakeEntry("entry-1")

        self.assertTrue(await INTEGRATION.async_setup_entry(hass, entry))

        coordinator = _FakeCoordinator.instances[-1]
        self.assertTrue(coordinator.started)
        self.assertIs(hass.data["heiko_w600"]["entry-1"], coordinator)
        self.assertEqual(manager.forwarded, (entry, ("sensor", "binary_sensor", "switch", "select", "number", "button")))

    async def test_failed_platform_setup_stops_and_removes_coordinator(self) -> None:
        manager = _FakeConfigEntries()
        manager.forward_error = RuntimeError("synthetic setup failure")
        hass = _FakeHass(manager)
        entry = _FakeEntry("entry-2")

        with self.assertRaisesRegex(RuntimeError, "synthetic setup failure"):
            await INTEGRATION.async_setup_entry(hass, entry)

        self.assertTrue(_FakeCoordinator.instances[-1].stopped)
        self.assertNotIn("heiko_w600", hass.data)

    async def test_unload_failure_keeps_listener_running(self) -> None:
        manager = _FakeConfigEntries()
        manager.unload_result = False
        hass = _FakeHass(manager)
        entry = _FakeEntry("entry-3")
        await INTEGRATION.async_setup_entry(hass, entry)
        coordinator = _FakeCoordinator.instances[-1]

        self.assertFalse(await INTEGRATION.async_unload_entry(hass, entry))
        self.assertFalse(coordinator.stopped)
        self.assertIs(hass.data["heiko_w600"]["entry-3"], coordinator)

    async def test_successful_unload_stops_listener_and_clears_data(self) -> None:
        manager = _FakeConfigEntries()
        hass = _FakeHass(manager)
        entry = _FakeEntry("entry-4")
        await INTEGRATION.async_setup_entry(hass, entry)
        coordinator = _FakeCoordinator.instances[-1]

        self.assertTrue(await INTEGRATION.async_unload_entry(hass, entry))
        self.assertTrue(coordinator.stopped)
        self.assertNotIn("heiko_w600", hass.data)


def _run(awaitable: object) -> object:
    import asyncio

    return asyncio.run(awaitable)  # type: ignore[arg-type]


class _FakeEntry:
    def __init__(self, entry_id: str) -> None:
        self.entry_id = entry_id


class _FakeConfigEntries:
    def __init__(self) -> None:
        self.forwarded: tuple[object, tuple[str, ...]] | None = None
        self.forward_error: Exception | None = None
        self.unload_result = True

    async def async_forward_entry_setups(
        self, entry: object, platforms: tuple[str, ...]
    ) -> None:
        self.forwarded = (entry, platforms)
        if self.forward_error is not None:
            raise self.forward_error

    async def async_unload_platforms(
        self, entry: object, platforms: tuple[str, ...]
    ) -> bool:
        return self.unload_result


class _FakeHass:
    def __init__(self, config_entries: _FakeConfigEntries) -> None:
        self.data: dict[str, dict[str, object]] = {}
        self.config_entries = config_entries


class ManifestTests(unittest.TestCase):
    def test_manifest_marks_config_flow_as_single_local_device_entry(self) -> None:
        manifest = json.loads(
            (INTEGRATION_PATH / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["domain"], "heiko_w600")
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(manifest["integration_type"], "device")
        self.assertEqual(manifest["iot_class"], "local_push")

    def test_translation_json_files_are_well_formed(self) -> None:
        strings = json.loads(
            (INTEGRATION_PATH / "translations" / "en.json").read_text(encoding="utf-8")
        )
        german = json.loads(
            (INTEGRATION_PATH / "translations" / "de.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(strings["config"]["step"]["user"]["data"].keys(),
                         german["config"]["step"]["user"]["data"].keys())
        self.assertIn("already_configured", german["config"]["abort"])


class PlatformTranslationCoverageTests(unittest.TestCase):
    def _descriptor_keys(self, filename: str, variable: str) -> set[str]:
        source = (INTEGRATION_PATH / filename).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filename)
        values: list[ast.expr] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == variable
                and node.value is not None
            ):
                values.append(node.value)
            elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == variable
                for target in node.targets
            ):
                values.append(node.value)
        self.assertEqual(len(values), 1, f"Expected one {variable} descriptor")
        descriptor_tuple = values[0]
        self.assertIsInstance(descriptor_tuple, ast.Tuple)

        keys: set[str] = set()
        for descriptor in descriptor_tuple.elts:
            self.assertIsInstance(descriptor, ast.Call)
            key_keyword = next(
                (keyword for keyword in descriptor.keywords if keyword.arg == "key"),
                None,
            )
            self.assertIsNotNone(key_keyword)
            self.assertIsInstance(key_keyword.value, ast.Constant)
            self.assertIsInstance(key_keyword.value.value, str)
            keys.add(key_keyword.value.value)
        return keys

    def test_every_platform_descriptor_has_base_and_german_names(self) -> None:
        strings = json.loads(
            (INTEGRATION_PATH / "translations" / "en.json").read_text(encoding="utf-8")
        )
        german = json.loads(
            (INTEGRATION_PATH / "translations" / "de.json").read_text(
                encoding="utf-8"
            )
        )
        platforms = (
            ("sensor", "sensor.py", "SENSORS"),
            ("binary_sensor", "binary_sensor.py", "BINARY_SENSORS"),
        )

        for platform, filename, variable in platforms:
            with self.subTest(platform=platform):
                descriptor_keys = self._descriptor_keys(filename, variable)
                for language, translation in (
                    ("base", strings),
                    ("de", german),
                ):
                    with self.subTest(language=language):
                        names = translation.get("entity", {}).get(platform, {})
                        self.assertTrue(descriptor_keys <= set(names))
                        for key in descriptor_keys:
                            self.assertIsInstance(names[key].get("name"), str)
                            self.assertTrue(names[key]["name"].strip())


if __name__ == "__main__":
    unittest.main()
