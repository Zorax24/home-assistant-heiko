"""Offline tests for the Heiko W600 diagnostics whitelist."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

INTEGRATION_DIR = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "heiko_w600"
)
PACKAGE_NAME = "_synthetic_heiko_w600_diagnostics_test"


def _load_module(module_name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


if PACKAGE_NAME not in sys.modules:
    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(INTEGRATION_DIR)]
    sys.modules[PACKAGE_NAME] = package

const = _load_module(f"{PACKAGE_NAME}.const", INTEGRATION_DIR / "const.py")
diagnostics = _load_module(
    f"{PACKAGE_NAME}.diagnostics", INTEGRATION_DIR / "diagnostics.py"
)


class SyntheticCoordinator:
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self.connected = True
        self.is_realtime_fresh = True
        self.is_settings_fresh = False
        self.last_realtime = now - timedelta(seconds=12)
        self.last_settings = now - timedelta(seconds=91)
        self.realtime = {
            "par04": "SYNTHETIC_TELEMETRY_VALUE",
            "private_frame": "SYNTHETIC_RAW_FRAME",
        }
        self.settings = {"par30": "SYNTHETIC_SETTING_VALUE"}


class SyntheticEntry:
    entry_id = "SYNTHETIC_ENTRY_ID"

    def __init__(self) -> None:
        self.data = {
            "listen_host": "SYNTHETIC_HOSTNAME",
            "listen_port": 8888,
            "upstream_host": "SYNTHETIC_UPSTREAM",
            "upstream_port": 18888,
            "token": "SYNTHETIC_TOKEN",
            "serial": "SYNTHETIC_SERIAL",
            "mac": "SYNTHETIC_MAC",
            "ip": "198.51.100.77",
        }


def get_diagnostics(coordinator: object | None) -> dict[str, object]:
    entry = SyntheticEntry()
    domain_data = {} if coordinator is None else {entry.entry_id: coordinator}
    hass = types.SimpleNamespace(data={const.DOMAIN: domain_data})
    return asyncio.run(
        diagnostics.async_get_config_entry_diagnostics(hass, entry)
    )


class DiagnosticsTests(unittest.TestCase):
    def test_allowlist_excludes_config_and_telemetry_values(self) -> None:
        result = get_diagnostics(SyntheticCoordinator())

        self.assertEqual(
            set(result),
            {"software", "runtime", "configuration_ranges"},
        )
        self.assertEqual(set(result["software"]), {"integration_version"})
        self.assertEqual(
            set(result["runtime"]),
            {
                "connected",
                "upstream_enabled",
                "upstream_connected",
                "realtime_fresh",
                "settings_fresh",
                "realtime_age_seconds",
                "settings_age_seconds",
                "realtime_field_count",
                "settings_field_count",
            },
        )
        self.assertTrue(result["runtime"]["connected"])
        self.assertTrue(result["runtime"]["realtime_fresh"])
        self.assertFalse(result["runtime"]["settings_fresh"])
        self.assertEqual(result["runtime"]["realtime_field_count"], 2)
        self.assertEqual(result["runtime"]["settings_field_count"], 1)

        serialized = json.dumps(result, sort_keys=True)
        for value in (
            "SYNTHETIC_HOSTNAME",
            "SYNTHETIC_UPSTREAM",
            "SYNTHETIC_TOKEN",
            "SYNTHETIC_ENTRY_ID",
            "SYNTHETIC_SERIAL",
            "SYNTHETIC_MAC",
            "198.51.100.77",
            "8888",
            "18888",
            "SYNTHETIC_TELEMETRY_VALUE",
            "SYNTHETIC_RAW_FRAME",
            "SYNTHETIC_SETTING_VALUE",
        ):
            self.assertNotIn(value, serialized)

    def test_runtime_lookup_uses_hass_data_and_omits_naive_timestamps(self) -> None:
        coordinator = SyntheticCoordinator()
        result = get_diagnostics(coordinator)
        runtime = result["runtime"]
        self.assertGreaterEqual(runtime["realtime_age_seconds"], 0)
        self.assertLess(runtime["realtime_age_seconds"], 60)
        self.assertGreaterEqual(runtime["settings_age_seconds"], 80)
        self.assertLess(runtime["settings_age_seconds"], 120)

        coordinator.last_realtime = datetime.now()
        coordinator.last_settings = None
        result = get_diagnostics(coordinator)
        self.assertIsNone(result["runtime"]["realtime_age_seconds"])
        self.assertIsNone(result["runtime"]["settings_age_seconds"])

    def test_missing_coordinator_fails_closed(self) -> None:
        result = get_diagnostics(None)
        runtime = result["runtime"]
        self.assertFalse(runtime["connected"])
        self.assertFalse(runtime["realtime_fresh"])
        self.assertFalse(runtime["settings_fresh"])
        self.assertIsNone(runtime["realtime_age_seconds"])
        self.assertIsNone(runtime["settings_age_seconds"])
        self.assertIsNone(runtime["realtime_field_count"])
        self.assertIsNone(runtime["settings_field_count"])

    def test_counts_only_present_fields(self) -> None:
        coordinator = SyntheticCoordinator()
        coordinator.realtime = {"par04": None, "par05": None}
        coordinator.settings = {"par30": "SYNTHETIC_SETTING_VALUE"}
        result = get_diagnostics(coordinator)
        self.assertEqual(result["runtime"]["realtime_field_count"], 0)
        self.assertEqual(result["runtime"]["settings_field_count"], 1)

    def test_static_ranges_and_manifest_version(self) -> None:
        result = get_diagnostics(None)
        self.assertEqual(
            result["configuration_ranges"],
            {
                "listen_port": {"minimum": 1, "maximum": 65535},
                "upstream_port": {"minimum": 1, "maximum": 65535},
                "stale_seconds": {"minimum": 30, "maximum": 3600},
            },
        )
        manifest = json.loads(
            (INTEGRATION_DIR / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            result["software"]["integration_version"],
            manifest["version"],
        )


if __name__ == "__main__":
    unittest.main()
