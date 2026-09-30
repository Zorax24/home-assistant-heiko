from __future__ import annotations

import importlib.util

import math
from pathlib import Path
import struct
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = PROJECT_ROOT / "custom_components" / "heiko_w600" / "protocol.py"
SPEC = importlib.util.spec_from_file_location("heiko_w600_protocol_under_test", PROTOCOL_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Cannot load protocol module from {PROTOCOL_PATH}")
PROTOCOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOL
SPEC.loader.exec_module(PROTOCOL)

FrameParser = PROTOCOL.FrameParser
crc16_heiko = PROTOCOL.crc16_heiko
decode_realtime_payload = PROTOCOL.decode_realtime_payload
decode_settings_payload = PROTOCOL.decode_settings_payload

_UNIT_SEED = 0x40FD
_CLOUD_SEED = 0xBF02
_UNIT_HEADER = b"\xaa\x55"
_CLOUD_HEADER = b"\x55\xaa"


def synthetic_frame(
    *,
    direction: str = "unit_to_cloud",
    command: int = 1,
    payload: bytes = b"",
    target: int = 3,
    device_id: bytes = b"\x01\x02\x03\x04\x05\x06",
    identifier: int = 1,
    declared_length: int | None = None,
    terminator: int = 0x3A,
    corrupt_crc: bool = False,
) -> bytes:
    """Create a test-only synthetic frame; production code exposes no frame builder."""
    header = _UNIT_HEADER if direction == "unit_to_cloud" else _CLOUD_HEADER
    seed = _UNIT_SEED if direction == "unit_to_cloud" else _CLOUD_SEED
    length = 1 + len(payload) if declared_length is None else declared_length
    covered = (
        header
        + bytes((target,))
        + device_id
        + bytes((identifier,))
        + length.to_bytes(2, "little")
        + bytes((command,))
        + payload
    )
    crc = crc16_heiko(covered, seed)
    if corrupt_crc:
        crc ^= 1
    return covered + crc.to_bytes(2, "little") + bytes((terminator,))


class HeikoCrcTests(unittest.TestCase):
    def test_directional_reference_crc_vector(self) -> None:
        # Valid synthetic frame prefix matching the audited field offsets.
        covered = bytes.fromhex("55 AA 00 00 00 00 00 00 00 01 01 00 06")
        self.assertEqual(crc16_heiko(covered, _CLOUD_SEED), 0xDAD6)

    def test_crc_rejects_bad_initial_value(self) -> None:
        with self.assertRaises(ValueError):
            crc16_heiko(b"data", -1)


class FrameParserTests(unittest.TestCase):
    def test_decodes_cloud_to_unit_frame(self) -> None:
        raw = bytes.fromhex("55 AA 00 00 00 00 00 00 00 01 01 00 06 D6 DA 3A")
        frames = FrameParser().feed(raw)
        self.assertEqual(len(frames), 1)
        frame = frames[0]
        self.assertEqual(frame.direction, "cloud_to_unit")
        self.assertEqual(frame.target, 0)
        self.assertEqual(frame.device_id, b"\x00" * 6)
        self.assertEqual(frame.identifier, 1)
        self.assertEqual(frame.command, 6)
        self.assertEqual(frame.payload, b"")

    def test_retains_fragment_until_complete(self) -> None:
        raw = synthetic_frame(payload=b"fragmented")
        parser = FrameParser()
        self.assertEqual(parser.feed(raw[:7]), [])
        expected = FrameParser().feed(raw)
        self.assertEqual(parser.feed(raw[7:]), expected)

    def test_handles_split_header_after_noise(self) -> None:
        raw = synthetic_frame(command=6)
        parser = FrameParser()
        self.assertEqual(parser.feed(b"noise\xaa"), [])
        frames = parser.feed(b"\x55" + raw[2:])
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].command, 6)

    def test_extracts_coalesced_frames_in_order(self) -> None:
        first = synthetic_frame(command=1, payload=b"one")
        second = synthetic_frame(direction="cloud_to_unit", command=6, payload=b"two")
        frames = FrameParser().feed(first + second)
        self.assertEqual([frame.command for frame in frames], [1, 6])
        self.assertEqual([frame.direction for frame in frames], ["unit_to_cloud", "cloud_to_unit"])
        self.assertEqual([frame.payload for frame in frames], [b"one", b"two"])

    def test_rejects_bad_crc_and_recovers_following_frame(self) -> None:
        invalid = synthetic_frame(payload=b"bad", corrupt_crc=True)
        valid = synthetic_frame(command=6, payload=b"good")
        frames = FrameParser().feed(invalid + valid)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].payload, b"good")

    def test_rejects_bad_terminator_and_recovers(self) -> None:
        invalid = synthetic_frame(payload=b"bad", terminator=0)
        valid = synthetic_frame(command=6, payload=b"good")
        frames = FrameParser().feed(invalid + valid)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].payload, b"good")

    def test_rejects_zero_and_oversized_lengths(self) -> None:
        zero_length = synthetic_frame(command=1, declared_length=0)
        oversized_length = synthetic_frame(command=1, declared_length=2049)
        valid = synthetic_frame(command=6)
        frames = FrameParser().feed(zero_length + oversized_length + valid)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].command, 6)

    def test_unknown_header_is_discarded(self) -> None:
        frames = FrameParser().feed(b"\x12\x34" + synthetic_frame(command=6))
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].command, 6)


class PayloadDecoderTests(unittest.TestCase):
    def test_realtime_offsets_keys_and_invalid_float_values(self) -> None:
        values = [float(index) for index in range(43)]
        values[0] = 0.0
        values[5] = -99.0
        values[6] = math.nan
        values[7] = math.inf
        values[42] = 42.5
        payload = b"prefix1234" + struct.pack("<43f", *values)

        decoded = decode_realtime_payload(payload)
        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(len(decoded), 43)
        self.assertEqual(decoded["par01"], 0.0)
        self.assertIsNone(decoded["par06"])
        self.assertIsNone(decoded["par07"])
        self.assertIsNone(decoded["par08"])
        self.assertEqual(decoded["par43"], 42.5)

    def test_settings_offsets_and_sentinel(self) -> None:
        values = [0.0] * 138
        values[1] = 12.25
        values[137] = -99.0
        decoded = decode_settings_payload(b"\x00\x01" + struct.pack("<138f", *values))
        self.assertIsNotNone(decoded)
        assert decoded is not None
        self.assertEqual(len(decoded), 138)
        self.assertEqual(decoded["setting_000"], 0.0)
        self.assertEqual(decoded["setting_001"], 12.25)
        self.assertIsNone(decoded["setting_137"])

    def test_short_or_non_bytes_payload_is_unavailable(self) -> None:
        self.assertIsNone(decode_realtime_payload(b"short"))
        self.assertIsNone(decode_settings_payload(b"short"))
        self.assertIsNone(decode_realtime_payload(None))  # type: ignore[arg-type]
        self.assertIsNone(decode_settings_payload(None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
