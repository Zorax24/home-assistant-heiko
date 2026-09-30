from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Literal

FrameDirection = Literal["unit_to_cloud", "cloud_to_unit"]

_UNIT_HEADER = b"\xaa\x55"
_CLOUD_HEADER = b"\x55\xaa"
_UNIT_CRC_INIT = 0x40FD
_CLOUD_CRC_INIT = 0xBF02
_END_BYTE = 0x3A
_PREFIX_LENGTH = 12
_CRC_LENGTH = 2
_MAX_DECLARED_LENGTH = 2048
_REALTIME_PREFIX_LENGTH = 10
_REALTIME_VALUE_COUNT = 43
_SETTINGS_PREFIX_LENGTH = 2
_SETTINGS_VALUE_COUNT = 138


@dataclass(frozen=True, slots=True)
class Frame:
    direction: FrameDirection
    target: int
    device_id: bytes
    identifier: int
    command: int
    payload: bytes


def crc16_heiko(data: bytes, initial_value: int) -> int:
    """Return the W600 reflected CRC-16 for data and a direction-specific seed."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    if not isinstance(initial_value, int) or not 0 <= initial_value <= 0xFFFF:
        raise ValueError("initial_value must be an unsigned 16-bit integer")

    crc = initial_value
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def build_command_frame(context: Frame, command: int, payload: bytes = b"") -> bytes:
    """Build a cloud-to-unit command using a validated inbound frame context."""
    if context.direction != "unit_to_cloud" or len(context.device_id) != 6:
        raise ValueError("A validated unit frame is required")
    if not 0 <= command <= 255 or len(payload) > _MAX_DECLARED_LENGTH - 1:
        raise ValueError("Invalid command")
    head = (
        _CLOUD_HEADER
        + bytes((context.target,))
        + context.device_id
        + bytes((context.identifier,))
        + (1 + len(payload)).to_bytes(2, "little")
        + bytes((command,))
        + payload
    )
    return head + crc16_heiko(head, _CLOUD_CRC_INIT).to_bytes(2, "little") + bytes((_END_BYTE,))


def build_set_parameter_payload(index: int, value: float) -> bytes:
    """Encode an explicitly validated CMD02 index and finite float32 value."""
    if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < 138:
        raise ValueError("Invalid parameter index")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Invalid parameter value")
    return struct.pack("<Hf", index, value)


class FrameParser:
    """Incremental parser that emits only complete, structurally valid, CRC-valid frames."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data must be bytes-like")
        self._buffer.extend(data)

        frames: list[Frame] = []
        offset = 0
        while offset < len(self._buffer):
            start = self._find_header(offset)
            if start < 0:
                last = self._buffer[-1] if self._buffer else None
                offset = len(self._buffer) - 1 if last in (0xAA, 0x55) else len(self._buffer)
                break

            if start > offset:
                offset = start

            available = len(self._buffer) - start
            if available < _PREFIX_LENGTH:
                break

            declared_length = int.from_bytes(self._buffer[start + 10 : start + 12], "little")
            if not 1 <= declared_length <= _MAX_DECLARED_LENGTH:
                offset = start + 1
                continue

            total_length = _PREFIX_LENGTH + declared_length + _CRC_LENGTH + 1
            if available < total_length:
                break

            end = start + total_length
            if self._buffer[end - 1] != _END_BYTE:
                offset = start + 1
                continue

            crc_offset = start + _PREFIX_LENGTH + declared_length
            expected_crc = int.from_bytes(self._buffer[crc_offset : crc_offset + 2], "little")
            crc_initial = _CLOUD_CRC_INIT if self._buffer[start : start + 2] == _CLOUD_HEADER else _UNIT_CRC_INIT
            actual_crc = crc16_heiko(self._buffer[start:crc_offset], crc_initial)
            if actual_crc != expected_crc:
                offset = start + 1
                continue

            header = bytes(self._buffer[start : start + 2])
            direction: FrameDirection = "unit_to_cloud" if header == _UNIT_HEADER else "cloud_to_unit"
            frames.append(
                Frame(
                    direction=direction,
                    target=self._buffer[start + 2],
                    device_id=bytes(self._buffer[start + 3 : start + 9]),
                    identifier=self._buffer[start + 9],
                    command=self._buffer[start + 12],
                    payload=bytes(self._buffer[start + 13 : crc_offset]),
                )
            )
            offset = end

        if offset:
            del self._buffer[:offset]
        return frames

    def _find_header(self, offset: int) -> int:
        for index in range(offset, len(self._buffer) - 1):
            pair = self._buffer[index : index + 2]
            if pair == _UNIT_HEADER or pair == _CLOUD_HEADER:
                return index
        return -1


def _normalize_float(value: float) -> float | None:
    if not math.isfinite(value) or value == -99:
        return None
    return value


def _decode_float_values(
    payload: bytes,
    prefix_length: int,
    count: int,
    key_factory,
) -> dict[str, float | None] | None:
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        return None
    if len(payload) < prefix_length + count * 4:
        return None

    values: dict[str, float | None] = {}
    for index in range(count):
        raw_value = struct.unpack_from("<f", payload, prefix_length + index * 4)[0]
        values[key_factory(index)] = _normalize_float(raw_value)
    return values


def decode_realtime_payload(payload: bytes) -> dict[str, float | None] | None:
    """Decode the 10-byte CMD01 prefix and 43 Float32-LE values."""
    return _decode_float_values(
        payload,
        _REALTIME_PREFIX_LENGTH,
        _REALTIME_VALUE_COUNT,
        lambda index: f"par{index + 1:02d}",
    )


def decode_settings_payload(payload: bytes) -> dict[str, float | None] | None:
    """Decode the 2-byte CMD02 prefix and 138 Float32-LE values."""
    return _decode_float_values(
        payload,
        _SETTINGS_PREFIX_LENGTH,
        _SETTINGS_VALUE_COUNT,
        lambda index: f"setting_{index:03d}",
    )
