from __future__ import annotations

import asyncio
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .protocol import Frame, FrameParser, build_command_frame, build_set_parameter_payload, decode_realtime_payload, decode_settings_payload
from .parameters import WRITABLE, validate_value

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)
DOMAIN = "heiko_w600"
DEFAULT_LISTEN_HOST = "0.0.0.0"
DEFAULT_LISTEN_PORT = 8899
DEFAULT_UPSTREAM_HOST = "www.myheatpump.com"
DEFAULT_UPSTREAM_PORT = 18899
DEFAULT_STALE_SECONDS = 180
MIN_STALE_SECONDS = 30
MAX_STALE_SECONDS = 3600
_CONNECT_TIMEOUT = 10.0
_READ_SIZE = 4096


class HeikoCoordinator(DataUpdateCoordinator):
    """W600 TCP proxy with validated telemetry and confirmed parameter writes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            always_update=False,
        )
        config = {**(getattr(entry, "data", {}) or {}),
                  **(getattr(entry, "options", {}) or {})}
        self._entry = entry
        self.upstream_enabled = config.get("upstream_enabled", True) is not False
        self.listen_host = str(config.get("listen_host", DEFAULT_LISTEN_HOST))
        self.listen_port = self._bounded_int(
            config.get("listen_port"), DEFAULT_LISTEN_PORT, 0, 65535
        )
        self.upstream_host = str(
            config.get("upstream_host", DEFAULT_UPSTREAM_HOST)
        )
        self.upstream_port = self._bounded_int(
            config.get("upstream_port"), DEFAULT_UPSTREAM_PORT, 1, 65535
        )
        self.stale_seconds = self._bounded_int(
            config.get("stale_seconds"),
            DEFAULT_STALE_SECONDS,
            MIN_STALE_SECONDS,
            MAX_STALE_SECONDS,
        )
        self._watchdog_interval = min(
            1.0, max(0.05, self.stale_seconds / 4)
        )

        self._realtime: dict[str, float | None] = {
            f"par{index:02d}": None for index in range(1, 44)
        }
        self._settings: dict[str, float | None] = {
            f"setting_{index:03d}": None for index in range(138)
        }
        self._last_realtime: datetime | None = None
        self._last_settings: datetime | None = None
        self.connected = False
        self.bytes_to_cloud = 0
        self.bytes_to_unit = 0
        self.frames_received = 0
        self.last_write_result = "none"
        self.last_write_index = None
        self.last_write_value = None
        self._bound_device_id: bytes | None = None
        self._frame_context: Frame | None = None
        self._write_lock = asyncio.Lock()
        self._settings_sequence = 0
        self._pending_write: tuple[int, float, int, int, asyncio.Future[None]] | None = None
        self._cloud_write_at: float | None = None

        self._server: asyncio.Server | None = None
        self._watchdog_task: asyncio.Task[None] | None = None
        self._session_tasks: set[asyncio.Task[Any]] = set()
        self._session_lock = asyncio.Lock()
        self._active_generation = 0
        self._active_task: asyncio.Task[Any] | None = None
        self._client_writer: asyncio.StreamWriter | None = None
        self._upstream_writer: asyncio.StreamWriter | None = None
        self._upstream_task: asyncio.Task | None = None
        self._stopping = False

        # Push coordinators need an initial value before their first frame.
        self.data = self._snapshot()

    @staticmethod
    def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            number = int(value) if value is not None else default
        except (TypeError, ValueError):
            number = default
        return min(maximum, max(minimum, number))

    @property
    def realtime(self) -> dict[str, float | None]:
        return self._realtime

    @property
    def settings(self) -> dict[str, float | None]:
        return self._settings

    @property
    def last_realtime(self) -> datetime | None:
        return self._last_realtime

    @property
    def last_settings(self) -> datetime | None:
        return self._last_settings

    @property
    def is_realtime_fresh(self) -> bool:
        return self.connected and self._is_fresh(self._last_realtime)

    @property
    def is_settings_fresh(self) -> bool:
        return self.connected and self._is_fresh(self._last_settings)

    def _is_fresh(self, timestamp: datetime | None) -> bool:
        if timestamp is None:
            return False
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return 0 <= age <= self.stale_seconds

    def _snapshot(self) -> dict[str, Any]:
        return {
            "realtime": dict(self._realtime),
            "settings": dict(self._settings),
            "connected": self.connected,
            "upstream_enabled": self.upstream_enabled,
            "upstream_connected": self._upstream_writer is not None,
            "realtime_fresh": self.is_realtime_fresh,
            "settings_fresh": self.is_settings_fresh,
            "last_realtime": self._last_realtime,
            "last_settings": self._last_settings,
            "realtime_age": self._age_seconds(self._last_realtime),
            "settings_age": self._age_seconds(self._last_settings),
            "listener_running": self._server is not None,
            "bytes_to_cloud": self.bytes_to_cloud,
            "bytes_to_unit": self.bytes_to_unit,
            "frames_received": self.frames_received,
            "last_write_result": self.last_write_result,
        }

    @staticmethod
    def _age_seconds(timestamp: datetime | None) -> int | None:
        return None if timestamp is None else max(
            0, int((datetime.now(timezone.utc) - timestamp).total_seconds())
        )

    def _publish(self) -> None:
        self.async_set_updated_data(self._snapshot())

    async def async_start(self) -> None:
        """Start the inbound W600 listener and stale-data watchdog."""
        if self._server is not None:
            return
        self._stopping = False
        try:
            self._server = await asyncio.start_server(
                self._handle_client,
                self.listen_host,
                self.listen_port,
                limit=65536,
            )
        except OSError:
            raise ConfigEntryNotReady(translation_domain=DOMAIN, translation_key="listener_unavailable") from None

        sockets = self._server.sockets or ()
        if sockets:
            self.listen_port = int(sockets[0].getsockname()[1])
        self._watchdog_task = asyncio.create_task(
            self._watch_staleness(), name="heiko_w600_stale_watchdog"
        )

    async def async_stop(self) -> None:
        """Stop accepting connections, close streams, and cancel owned tasks."""
        self._stopping = True
        self._fail_pending("session_ended")
        server, self._server = self._server, None
        if server is not None:
            server.close()

        writers = (self._client_writer, self._upstream_writer)
        for writer in writers:
            if writer is not None:
                writer.close()

        watchdog, self._watchdog_task = self._watchdog_task, None
        if watchdog is not None:
            watchdog.cancel()

        current = asyncio.current_task()
        tasks = tuple(task for task in self._session_tasks if task is not current)
        for task in tasks:
            task.cancel()
        await asyncio.gather(
            *(task for task in (watchdog, *tasks) if task is not None),
            return_exceptions=True,
        )
        if server is not None:
            await server.wait_closed()
        await asyncio.gather(
            *(self._wait_closed(writer) for writer in writers if writer is not None),
            return_exceptions=True,
        )

        self._client_writer = None
        self._upstream_writer = None
        self._upstream_task = None
        self.connected = False
        self._publish()

    @staticmethod
    async def _wait_closed(writer: asyncio.StreamWriter) -> None:
        try:
            await asyncio.wait_for(writer.wait_closed(), timeout=2.0)
        except (OSError, asyncio.TimeoutError):
            pass

    async def _handle_client(
        self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        task = asyncio.current_task()
        if task is not None:
            self._session_tasks.add(task)
        generation = 0

        try:
            if self._stopping:
                return
            async with self._session_lock:
                old_task = self._active_task
                old_client = self._client_writer
                old_upstream = self._upstream_writer
                old_upstream_task = self._upstream_task
                self._active_generation += 1
                self._fail_pending("session_ended")
                self._frame_context = None
                self._cloud_write_at = None
                self._last_settings = None
                self._last_realtime = None
                generation = self._active_generation
                self._active_task = task
                self._client_writer = client_writer
                self._upstream_writer = None
                self._upstream_task = None
                self.connected = True
                self._publish()

            if old_client is not None:
                old_client.close()
            if old_upstream is not None:
                old_upstream.close()
            if old_task is not None and old_task is not task:
                old_task.cancel()
            if old_upstream_task is not None:
                old_upstream_task.cancel()
                await asyncio.gather(old_upstream_task, return_exceptions=True)
            if self._stopping or generation != self._active_generation:
                return
            self._start_upstream_task(generation, client_writer)
            await self._read_unit(client_reader, client_writer, generation)
        except asyncio.CancelledError:
            raise
        except (OSError, ConnectionError, asyncio.TimeoutError):
            if not self._stopping:
                _LOGGER.debug("W600 proxy session ended")
        finally:
            client_writer.close()
            await self._wait_closed(client_writer)

            if generation == self._active_generation:
                cloud_task, self._upstream_task = self._upstream_task, None
                if cloud_task is not None:
                    cloud_task.cancel()
                    await asyncio.gather(cloud_task, return_exceptions=True)
                self._fail_pending("session_ended")
                self._client_writer = None
                self._upstream_writer = None
                self._active_task = None
                self.connected = False
                self._frame_context = None
                self._publish()
            if task is not None:
                self._session_tasks.discard(task)

    def _start_upstream_task(self, generation, client_writer):
        if not self.upstream_enabled or self._stopping:
            return
        task = asyncio.create_task(self._run_upstream(generation, client_writer))
        self._upstream_task = task
        self._session_tasks.add(task)
        task.add_done_callback(self._session_tasks.discard)

    async def async_set_upstream_enabled(self, enabled: bool) -> None:
        """Persist the cloud relay choice while preserving the local W600 socket."""
        if not isinstance(enabled, bool):
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="boolean_required")
        async with self._write_lock:
            if enabled == self.upstream_enabled:
                return
            options = {**self._entry.options, "upstream_enabled": enabled}
            self.hass.config_entries.async_update_entry(self._entry, options=options)
            self.upstream_enabled = enabled
            cloud_task, self._upstream_task = self._upstream_task, None
            if cloud_task is not None:
                cloud_task.cancel()
                await asyncio.gather(cloud_task, return_exceptions=True)
            self._cloud_write_at = None
            if enabled and self.connected and self._client_writer is not None:
                self._start_upstream_task(self._active_generation, self._client_writer)
            self._publish()

    async def _run_upstream(self, generation, client_writer):
        """Reconnect the optional manufacturer relay independently of W600."""
        while self.upstream_enabled and not self._stopping and generation == self._active_generation:
            writer = None
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.upstream_host, self.upstream_port),
                    timeout=_CONNECT_TIMEOUT,
                )
                if not self.upstream_enabled or self._stopping or generation != self._active_generation:
                    return
                self._upstream_writer = writer
                self._publish()
                parser = FrameParser()
                while self.upstream_enabled and generation == self._active_generation:
                    chunk = await reader.read(_READ_SIZE)
                    if not chunk:
                        break
                    if not self.upstream_enabled or writer is not self._upstream_writer:
                        break
                    for frame in parser.feed(chunk):
                        self.frames_received += 1
                        if frame.direction == "cloud_to_unit" and frame.command == 0x05:
                            self._cloud_write_at = time.monotonic()
                            self._fail_pending("concurrent_cloud_write")
                    client_writer.write(chunk)
                    await client_writer.drain()
                    self.bytes_to_unit += len(chunk)
                    self._publish()
            except asyncio.CancelledError:
                raise
            except (OSError, ConnectionError, asyncio.TimeoutError):
                _LOGGER.debug("Manufacturer relay unavailable; local W600 remains connected")
            finally:
                if writer is not None:
                    writer.close()
                    await self._wait_closed(writer)
                if self._upstream_writer is writer:
                    self._upstream_writer = None
                    self._publish()
            await asyncio.sleep(5)

    async def _read_unit(self, reader, client_writer, generation):
        parser = FrameParser()
        while not self._stopping and generation == self._active_generation:
            chunk = await reader.read(_READ_SIZE)
            if not chunk:
                return
            for frame in parser.feed(chunk):
                self.frames_received += 1
                if self._accept_frame(frame) and not self.upstream_enabled:
                    # Reference ioBroker local mode: CMD01 -> CMD03, CMD02 -> CMD04.
                    ack = build_command_frame(frame, 0x03 if frame.command == 0x01 else 0x04)
                    client_writer.write(ack)
                    await client_writer.drain()
                    self.bytes_to_unit += len(ack)
            upstream = self._upstream_writer
            if self.upstream_enabled and upstream is not None and not upstream.is_closing():
                try:
                    upstream.write(chunk)
                    await upstream.drain()
                    self.bytes_to_cloud += len(chunk)
                except (OSError, ConnectionError):
                    upstream.close()
            self._publish()

    def _accept_frame(self, frame: Frame) -> bool:
        if frame.direction != "unit_to_cloud" or frame.command not in (0x01, 0x02):
            return False

        if frame.command == 0x01:
            values = decode_realtime_payload(frame.payload)
            if values is None or not any(value is not None for value in values.values()):
                return False
        else:
            values = decode_settings_payload(frame.payload)
            if values is None or not any(value is not None for value in values.values()):
                return False

        if self._bound_device_id is None:
            self._bound_device_id = frame.device_id
        elif not hmac.compare_digest(self._bound_device_id, frame.device_id):
            return False

        now = datetime.now(timezone.utc)
        self._frame_context = frame
        if frame.command == 0x01:
            self._realtime = values
            self._last_realtime = now
        else:
            self._settings = values
            self._last_settings = now
            self._cloud_write_at = None
            self._settings_sequence += 1
            pending = self._pending_write
            if pending is not None:
                index, expected, generation, sequence, future = pending
                actual = values.get(f"setting_{index:03d}")
                if (
                    generation == self._active_generation
                    and self._settings_sequence > sequence
                    and actual is not None
                    and abs(actual - expected) <= 0.001
                    and not future.done()
                ):
                    future.set_result(None)
        self._publish()
        return True

    def _fail_pending(self, reason: str) -> None:
        pending = self._pending_write
        self._pending_write = None
        if pending is not None and not pending[4].done():
            pending[4].set_exception(HomeAssistantError(translation_domain=DOMAIN, translation_key=reason))

    async def async_write_parameter(self, index: int, value: float) -> None:
        """Write one catalog parameter and require a fresh CMD02 echo."""
        definition = next((item for item in WRITABLE if item["settingIndex"] == index), None)
        if definition is None:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="not_writable")
        normalized = validate_value(definition, bool(value) if definition["type"] == "boolean" and value in (0.0, 1.0) else value)
        payload = build_set_parameter_payload(index, normalized)
        async with self._write_lock:
            writer = self._client_writer
            context = self._frame_context
            if (
                self._stopping or not self.connected or writer is None
                or writer.is_closing() or context is None
                or not self.is_settings_fresh
                or context.device_id != self._bound_device_id
            ):
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="settings_unavailable")
            if self._cloud_write_at is not None and time.monotonic() - self._cloud_write_at < 12:
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="cloud_write_pending")
            generation = self._active_generation
            sequence = self._settings_sequence
            future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
            self.last_write_index = index
            self.last_write_value = float(value)
            self._pending_write = (index, float(value), generation, sequence, future)
            try:
                writer.write(build_command_frame(context, 0x05, payload))
                await writer.drain()
                await asyncio.sleep(0.75)
                if generation != self._active_generation or writer.is_closing():
                    raise HomeAssistantError(translation_domain=DOMAIN, translation_key="connection_changed")
                # The reference adapter requests a fresh settings frame with CMD07.
                request_context = Frame("unit_to_cloud", 0, bytes(6), 1, 0, b"")
                writer.write(build_command_frame(request_context, 0x07))
                await writer.drain()
                await asyncio.wait_for(future, timeout=12.0)
                self.last_write_result = "confirmed"
            except (OSError, ConnectionError, asyncio.TimeoutError) as err:
                self.last_write_result = "unconfirmed"
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="write_unconfirmed") from err
            except HomeAssistantError:
                self.last_write_result = "aborted"
                raise
            finally:
                self._publish()
                if self._pending_write is not None and self._pending_write[4] is future:
                    self._pending_write = None
                if future.done() and not future.cancelled():
                    try:
                        future.exception()
                    except asyncio.CancelledError:
                        pass

    async def async_request_data(self, command: int) -> None:
        """Request telemetry or settings using the reference CMD06/CMD07 frame."""
        if command not in (0x06, 0x07):
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="unsupported_request")
        async with self._write_lock:
            writer = self._client_writer
            if not self.connected or writer is None or writer.is_closing():
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="not_connected")
            context = Frame("unit_to_cloud", 0, bytes(6), 1, 0, b"")
            try:
                writer.write(build_command_frame(context, command))
                await writer.drain()
            except (OSError, ConnectionError) as err:
                raise HomeAssistantError(translation_domain=DOMAIN, translation_key="request_failed") from err

    async def _watch_staleness(self) -> None:
        try:
            while not self._stopping:
                await asyncio.sleep(self._watchdog_interval)
                next_snapshot = self._snapshot()
                if next_snapshot != self.data:
                    self.async_set_updated_data(next_snapshot)
        except asyncio.CancelledError:
            raise
