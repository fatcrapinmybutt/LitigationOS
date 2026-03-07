#!/usr/bin/env python3
"""
binary_ipc.py — Zero-copy binary IPC transport for LitigationOS
================================================================

High-performance MessagePack-based IPC between Python backend and Electron frontend.
Supports three transport modes: pipe (stdin/stdout), TCP socket, and shared memory (mmap).

Electron integration (Node.js consumer):

    const msgpack = require('msgpack-lite');
    const net = require('net');

    const client = net.connect(9876, '127.0.0.1');
    let pending = Buffer.alloc(0);

    client.on('data', (chunk) => {
        pending = Buffer.concat([pending, chunk]);
        while (pending.length >= 29) {
            const payloadLen = pending.readUInt32BE(0);
            const frameLen = 29 + payloadLen;
            if (pending.length < frameLen) break;

            const msgId = pending.slice(4, 20).toString('hex');
            const timestamp = pending.readDoubleBE(20);
            const flags = pending.readUInt8(28);
            let payload = pending.slice(29, frameLen);
            pending = pending.slice(frameLen);

            if (flags & 1) {
                const zlib = require('zlib');
                payload = zlib.inflateSync(payload);
            }
            const msg = msgpack.decode(payload);
            console.log(`[${msg.channel}] id=${msgId}`, msg.data);
        }
    });

    // Send a request
    function sendRequest(channel, data) {
        const packed = msgpack.encode({ channel, data });
        const header = Buffer.alloc(29);
        header.writeUInt32BE(packed.length, 0);
        // msg_id bytes 4..20 (random)
        require('crypto').randomFillSync(header, 4, 16);
        header.writeDoubleBE(Date.now() / 1000, 20);
        header.writeUInt8(0, 28);  // no compression
        client.write(Buffer.concat([header, packed]));
    }

Usage:
    python binary_ipc.py serve                  # Start IPC server (socket mode)
    python binary_ipc.py serve --mode pipe      # Start pipe mode
    python binary_ipc.py benchmark              # Compare JSON vs MessagePack vs compressed
    python binary_ipc.py test                   # Run self-test with sample data
"""

from __future__ import annotations

import asyncio
import io
import json
import mmap
import os
import signal
import struct
import sys
import time
import uuid
import zlib
from dataclasses import dataclass, field
from multiprocessing import shared_memory
from typing import Any, Callable, Iterator

import msgpack

# ---------------------------------------------------------------------------
# UTF-8 stdout safety (LitigationOS requirement)
# ---------------------------------------------------------------------------
if sys.stdout and hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(
            sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False
        )
    except (OSError, ValueError):
        pass

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_MESSAGE_SIZE = 100 * 1024 * 1024  # 100 MB
COMPRESSION_THRESHOLD = 64 * 1024      # 64 KB — auto-compress above this
SMALL_MESSAGE_THRESHOLD = 4 * 1024     # 4 KB — use JSON below this for lower overhead
BATCH_FLUSH_INTERVAL = 0.016           # 16 ms (60 fps)
DEFAULT_READ_TIMEOUT = 30.0            # seconds
DEFAULT_PORT = 9876
DEFAULT_HOST = "127.0.0.1"             # localhost only — no external network

# Frame: [4B payload_length][16B msg_id][8B timestamp][1B flags][payload]
HEADER_SIZE = 29
HEADER_STRUCT = struct.Struct(">I16sdB")  # big-endian: uint32, 16-byte raw, double, uint8

# Flag bits
FLAG_COMPRESSED = 0x01
FLAG_HAS_METADATA = 0x02
FLAG_STREAMING = 0x04
FLAG_ERROR = 0x08
FLAG_JSON_PAYLOAD = 0x10  # payload is JSON, not msgpack (for small messages)
FLAG_BATCH = 0x20

# Shared-memory header: [4B write_offset][4B read_offset][4B msg_count]
SHM_HEADER_SIZE = 12
SHM_HEADER_STRUCT = struct.Struct(">III")

# SQLite PRAGMAs (for any DB access inside this module)
DB_PRAGMAS = """
PRAGMA busy_timeout = 180000;
PRAGMA journal_mode = WAL;
PRAGMA mmap_size = 12884901888;
PRAGMA cache_size = -131072;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
"""


# ---------------------------------------------------------------------------
# IPCMessage dataclass
# ---------------------------------------------------------------------------
@dataclass
class IPCMessage:
    """Binary IPC message with framing.

    Frame format (29-byte header + variable payload):
        [4B length][16B msg_id][8B timestamp][1B flags][NB payload]

    Flags:
        bit 0: compressed (zlib)
        bit 1: has metadata dict prepended in payload
        bit 2: streaming message (part of a stream)
        bit 3: error response
        bit 4: JSON payload (not msgpack)
        bit 5: batch of multiple messages
    """

    HEADER_SIZE: int = field(default=29, init=False, repr=False)

    channel: str
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    flags: int = 0
    payload: bytes = b""

    def to_frame(self) -> bytes:
        """Serialize to wire frame."""
        msg_id_bytes = bytes.fromhex(self.msg_id.replace("-", ""))[:16].ljust(16, b"\x00")
        header = HEADER_STRUCT.pack(len(self.payload), msg_id_bytes, self.timestamp, self.flags)
        return header + self.payload

    @classmethod
    def from_frame(cls, frame: bytes) -> "IPCMessage":
        """Deserialize from wire frame."""
        if len(frame) < HEADER_SIZE:
            raise ValueError(f"Frame too short: {len(frame)} < {HEADER_SIZE}")
        payload_len, msg_id_bytes, timestamp, flags = HEADER_STRUCT.unpack(frame[:HEADER_SIZE])
        payload = frame[HEADER_SIZE : HEADER_SIZE + payload_len]
        if len(payload) != payload_len:
            raise ValueError(f"Payload truncated: got {len(payload)}, expected {payload_len}")
        return cls(
            channel="",  # channel is inside the payload envelope
            msg_id=msg_id_bytes.hex(),
            timestamp=timestamp,
            flags=flags,
            payload=payload,
        )


# ---------------------------------------------------------------------------
# BinaryTransport — core transport layer
# ---------------------------------------------------------------------------
class BinaryTransport:
    """MessagePack binary transport supporting pipe, socket, and mmap modes.

    Args:
        mode: 'pipe' (stdin/stdout), 'socket' (TCP), or 'mmap' (shared memory).
    """

    def __init__(self, mode: str = "pipe"):
        if mode not in ("pipe", "socket", "mmap"):
            raise ValueError(f"Unknown transport mode: {mode!r}")
        self.mode = mode
        self.packer = msgpack.Packer(use_bin_type=True, datetime=True)
        self.unpacker = msgpack.Unpacker(raw=False, max_buffer_size=MAX_MESSAGE_SIZE)

        self._reader: Any = None
        self._writer: Any = None
        self._shm_bridge: SharedMemoryBridge | None = None
        self._batch_buffer: list[bytes] = []
        self._last_flush: float = time.time()

        if mode == "pipe":
            self._reader = sys.stdin.buffer
            self._writer = sys.stdout.buffer
        elif mode == "mmap":
            self._shm_bridge = SharedMemoryBridge()

    # -- Sending ---------------------------------------------------------------

    def send(self, channel: str, data: Any, compress: bool = False) -> int:
        """Send a message on the given channel.

        Returns the number of bytes written (frame size).

        Routing:
            - payloads < 4 KB  → JSON (lower overhead)
            - payloads >= 4 KB → MessagePack
            - payloads > 64 KB → MessagePack + zlib level 1 (if *compress* or auto)
        """
        envelope = {"channel": channel, "data": data}
        flags = 0

        # Decide serialization format
        raw = self.packer.pack(envelope)
        if len(raw) < SMALL_MESSAGE_THRESHOLD:
            raw = json.dumps(envelope, default=str, separators=(",", ":")).encode("utf-8")
            flags |= FLAG_JSON_PAYLOAD

        # Compression
        if compress or len(raw) > COMPRESSION_THRESHOLD:
            compressed = zlib.compress(raw, level=1)
            if len(compressed) < len(raw):
                raw = compressed
                flags |= FLAG_COMPRESSED

        if len(raw) > MAX_MESSAGE_SIZE:
            raise ValueError(f"Payload too large: {len(raw)} > {MAX_MESSAGE_SIZE}")

        msg = IPCMessage(channel=channel, flags=flags, payload=raw)
        frame = msg.to_frame()
        self._write_frame(frame)
        return len(frame)

    def send_streaming(
        self,
        channel: str,
        iterator: Iterator[Any],
        chunk_size: int = 1000,
        total: int | None = None,
    ) -> int:
        """Stream large result sets in chunks for progressive rendering.

        Sends a header with the total count (if known), followed by chunks,
        then a termination sentinel. Returns total bytes sent.
        """
        total_bytes = 0

        # Header frame
        total_bytes += self.send(
            f"{channel}:stream:start",
            {"total": total, "chunk_size": chunk_size},
        )

        chunk: list[Any] = []
        sent_rows = 0
        for item in iterator:
            chunk.append(item)
            if len(chunk) >= chunk_size:
                total_bytes += self.send(
                    f"{channel}:stream:chunk",
                    {"offset": sent_rows, "rows": chunk},
                )
                sent_rows += len(chunk)
                chunk = []

        if chunk:
            total_bytes += self.send(
                f"{channel}:stream:chunk",
                {"offset": sent_rows, "rows": chunk},
            )
            sent_rows += len(chunk)

        # Termination
        total_bytes += self.send(
            f"{channel}:stream:end",
            {"total_sent": sent_rows},
        )
        return total_bytes

    def flush_batch(self) -> int:
        """Flush accumulated batch buffer. Returns bytes written."""
        if not self._batch_buffer:
            return 0
        combined = b"".join(self._batch_buffer)
        flags = FLAG_BATCH
        if len(combined) > COMPRESSION_THRESHOLD:
            compressed = zlib.compress(combined, level=1)
            if len(compressed) < len(combined):
                combined = compressed
                flags |= FLAG_COMPRESSED
        msg = IPCMessage(channel="__batch__", flags=flags, payload=combined)
        frame = msg.to_frame()
        self._write_frame(frame)
        self._batch_buffer.clear()
        self._last_flush = time.time()
        return len(frame)

    def send_batched(self, channel: str, data: Any) -> None:
        """Queue a small message for batch flush (every 16 ms)."""
        envelope = {"channel": channel, "data": data}
        raw = json.dumps(envelope, default=str, separators=(",", ":")).encode("utf-8")
        self._batch_buffer.append(struct.pack(">I", len(raw)) + raw)
        if time.time() - self._last_flush >= BATCH_FLUSH_INTERVAL:
            self.flush_batch()

    # -- Receiving -------------------------------------------------------------

    def receive(self, timeout: float = DEFAULT_READ_TIMEOUT) -> tuple[str, Any]:
        """Read one message. Returns (channel, data).

        Raises TimeoutError if no data within *timeout* seconds.
        """
        if self.mode == "mmap" and self._shm_bridge:
            return self._receive_mmap(timeout)
        return self._receive_stream(timeout)

    def _receive_stream(self, timeout: float) -> tuple[str, Any]:
        reader = self._reader
        if reader is None:
            raise RuntimeError("No reader attached")

        start = time.time()
        header_buf = self._read_exact(reader, HEADER_SIZE, timeout)
        payload_len, msg_id_bytes, timestamp, flags = HEADER_STRUCT.unpack(header_buf)

        if payload_len > MAX_MESSAGE_SIZE:
            raise ValueError(f"Incoming message too large: {payload_len}")

        remaining = timeout - (time.time() - start)
        if remaining <= 0:
            raise TimeoutError("Timeout reading payload")
        payload = self._read_exact(reader, payload_len, remaining)

        return self._decode_payload(payload, flags)

    def _receive_mmap(self, timeout: float) -> tuple[str, Any]:
        assert self._shm_bridge is not None
        start = time.time()
        while True:
            raw = self._shm_bridge.read()
            if raw is not None:
                # raw is a full frame
                if len(raw) >= HEADER_SIZE:
                    payload_len, _, _, flags = HEADER_STRUCT.unpack(raw[:HEADER_SIZE])
                    payload = raw[HEADER_SIZE : HEADER_SIZE + payload_len]
                    return self._decode_payload(payload, flags)
            if time.time() - start > timeout:
                raise TimeoutError("No data in shared memory within timeout")
            time.sleep(0.001)

    # -- Internal helpers ------------------------------------------------------

    def _decode_payload(self, payload: bytes, flags: int) -> tuple[str, Any]:
        if flags & FLAG_COMPRESSED:
            payload = zlib.decompress(payload)
        if flags & FLAG_JSON_PAYLOAD:
            envelope = json.loads(payload)
        else:
            envelope = msgpack.unpackb(payload, raw=False)
        return envelope.get("channel", ""), envelope.get("data")

    def _write_frame(self, frame: bytes) -> None:
        if self.mode == "mmap" and self._shm_bridge:
            self._shm_bridge.write(frame)
        elif self._writer:
            self._writer.write(frame)
            self._writer.flush()

    @staticmethod
    def _read_exact(reader: io.RawIOBase, n: int, timeout: float) -> bytes:
        """Read exactly *n* bytes with timeout."""
        buf = bytearray()
        start = time.time()
        while len(buf) < n:
            remaining = timeout - (time.time() - start)
            if remaining <= 0:
                raise TimeoutError(f"Timeout after reading {len(buf)}/{n} bytes")
            chunk = reader.read(n - len(buf))
            if chunk:
                buf.extend(chunk)
            elif chunk == b"":
                raise EOFError("Connection closed while reading")
            else:
                time.sleep(0.001)
        return bytes(buf)

    def attach(self, reader: Any = None, writer: Any = None) -> None:
        """Attach stream reader/writer (for socket mode)."""
        if reader is not None:
            self._reader = reader
        if writer is not None:
            self._writer = writer

    def close(self) -> None:
        """Release resources."""
        self.flush_batch()
        if self._shm_bridge:
            self._shm_bridge.close()
            self._shm_bridge = None


# ---------------------------------------------------------------------------
# SharedMemoryBridge — zero-copy via mmap / shared_memory
# ---------------------------------------------------------------------------
class SharedMemoryBridge:
    """Ring-buffer IPC over OS shared memory.

    Header layout (first 12 bytes):
        [4B write_offset][4B read_offset][4B msg_count]

    Each message in the ring is prefixed with a 4-byte length.

    Electron can map the same region via Node.js N-API SharedArrayBuffer:

        // Node.js (N-API addon or node-shm)
        const shm = require('shm-typed-array');
        const buf = shm.get('litigationos_ipc', 'Buffer');
        const writeOff = buf.readUInt32BE(0);
        const readOff = buf.readUInt32BE(4);
        // ... read messages starting at SHM_HEADER_SIZE + readOff
    """

    def __init__(self, name: str = "litigationos_ipc", size: int = 100 * 1024 * 1024):
        self.name = name
        self.size = size
        self._data_size = size - SHM_HEADER_SIZE
        self._shm: shared_memory.SharedMemory | None = None
        self._mm: mmap.mmap | None = None
        self._owns = False
        self._init_memory()

    def _init_memory(self) -> None:
        try:
            self._shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.size)
            self._owns = True
            # Zero the header
            self._shm.buf[:SHM_HEADER_SIZE] = SHM_HEADER_STRUCT.pack(0, 0, 0)
        except FileExistsError:
            self._shm = shared_memory.SharedMemory(name=self.name, create=False, size=self.size)
            self._owns = False

    @property
    def _buf(self) -> memoryview:
        assert self._shm is not None
        return self._shm.buf

    def _read_header(self) -> tuple[int, int, int]:
        raw = bytes(self._buf[:SHM_HEADER_SIZE])
        return SHM_HEADER_STRUCT.unpack(raw)

    def _write_header(self, write_off: int, read_off: int, msg_count: int) -> None:
        self._buf[:SHM_HEADER_SIZE] = SHM_HEADER_STRUCT.pack(write_off, read_off, msg_count)

    def write(self, data: bytes) -> int:
        """Write data into the ring buffer. Returns the offset written to."""
        msg_len = len(data)
        frame = struct.pack(">I", msg_len) + data
        frame_len = len(frame)

        if frame_len > self._data_size:
            raise ValueError(f"Message too large for shared memory: {frame_len} > {self._data_size}")

        write_off, read_off, msg_count = self._read_header()
        start = SHM_HEADER_SIZE + write_off

        # Wrap around if needed
        if write_off + frame_len > self._data_size:
            # Write a zero-length sentinel to signal wrap, then write at start
            if self._data_size - write_off >= 4:
                self._buf[start : start + 4] = struct.pack(">I", 0)
            write_off = 0
            start = SHM_HEADER_SIZE

        self._buf[start : start + frame_len] = frame
        new_write_off = write_off + frame_len
        self._write_header(new_write_off, read_off, msg_count + 1)
        return write_off

    def read(self) -> bytes | None:
        """Read the next message from the ring buffer. Non-blocking; returns None if empty."""
        write_off, read_off, msg_count = self._read_header()
        if msg_count == 0 or read_off == write_off:
            return None

        start = SHM_HEADER_SIZE + read_off
        raw_len = struct.unpack(">I", bytes(self._buf[start : start + 4]))[0]

        # Zero-length sentinel means wrap-around
        if raw_len == 0:
            read_off = 0
            start = SHM_HEADER_SIZE
            raw_len = struct.unpack(">I", bytes(self._buf[start : start + 4]))[0]
            if raw_len == 0:
                return None

        data = bytes(self._buf[start + 4 : start + 4 + raw_len])
        new_read_off = read_off + 4 + raw_len

        # Handle wrap for next read
        if new_read_off >= self._data_size:
            new_read_off = 0

        self._write_header(write_off, new_read_off, msg_count - 1)
        return data

    def create_view(self, table_data: list[dict]) -> memoryview:
        """Pack table data into shared memory and return a memoryview.

        The data is msgpack-encoded and written at the current write offset.
        Electron can read it directly via N-API SharedArrayBuffer without copying.
        """
        packed = msgpack.packb(table_data, use_bin_type=True)
        offset = self.write(packed)
        start = SHM_HEADER_SIZE + offset + 4  # skip length prefix
        return self._buf[start : start + len(packed)]

    def close(self) -> None:
        """Release shared memory."""
        if self._shm is not None:
            self._shm.close()
            if self._owns:
                try:
                    self._shm.unlink()
                except FileNotFoundError:
                    pass
            self._shm = None


# ---------------------------------------------------------------------------
# IPCServer — ties transport + handlers together
# ---------------------------------------------------------------------------
class IPCServer:
    """IPC server combining transport selection, handler dispatch, and query helpers.

    Args:
        transport: 'auto', 'pipe', 'socket', or 'mmap'.
    """

    def __init__(self, transport: str = "auto"):
        self.handlers: dict[str, Callable] = {}
        self._transport_mode = transport
        self.transport = self._select_transport(transport)
        self._running = False

    @staticmethod
    def _select_transport(mode: str) -> BinaryTransport:
        if mode == "auto":
            # Prefer mmap > socket > pipe
            try:
                return BinaryTransport(mode="mmap")
            except Exception:
                return BinaryTransport(mode="socket")
        return BinaryTransport(mode=mode)

    def register_handler(self, channel: str, handler: Callable) -> None:
        """Register *handler* for messages arriving on *channel*.

        Handler signature: ``handler(data: Any) -> Any``
        The return value (if not None) is sent back on ``channel + '.response'``.
        """
        self.handlers[channel] = handler

    # -- High-level send helpers -----------------------------------------------

    def send_query_result(self, channel: str, rows: list[dict]) -> int:
        """Serialize SQL query results with schema metadata.

        Auto-compresses if > 64 KB. Includes column names and inferred types
        so the Electron side can reconstruct TypedArrays.
        """
        schema = _infer_schema(rows)
        envelope = {"schema": schema, "row_count": len(rows), "rows": rows}
        return self.transport.send(channel, envelope, compress=len(rows) > 500)

    def send_filing_package(self, channel: str, package: dict) -> int:
        """Send a filing package with raw PDF bytes (not base64).

        PDFs are kept as raw ``bytes`` — msgpack sends them natively as bin type.
        This saves ~33% bandwidth vs base64 encoding.
        """
        return self.transport.send(channel, package, compress=True)

    # -- Server loops ----------------------------------------------------------

    async def serve(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        """Start the IPC server.

        - socket mode: asyncio TCP server on *host*:*port*.
        - pipe mode: synchronous stdin/stdout loop.
        - mmap mode: polling loop on shared memory.
        """
        self._running = True
        _install_signal_handlers(self._shutdown)

        if self._transport_mode in ("socket", "auto"):
            await self._serve_socket(host, port)
        elif self._transport_mode == "pipe":
            self._serve_pipe()
        elif self._transport_mode == "mmap":
            self._serve_mmap()

    async def _serve_socket(self, host: str, port: int) -> None:
        server = await asyncio.start_server(self._handle_client, host, port)
        addr = server.sockets[0].getsockname() if server.sockets else (host, port)
        print(f"[binary_ipc] TCP server listening on {addr[0]}:{addr[1]}")
        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        addr = writer.get_extra_info("peername")
        print(f"[binary_ipc] Client connected: {addr}")
        try:
            while self._running:
                header = await asyncio.wait_for(reader.readexactly(HEADER_SIZE), timeout=DEFAULT_READ_TIMEOUT)
                payload_len, msg_id_bytes, ts, flags = HEADER_STRUCT.unpack(header)
                if payload_len > MAX_MESSAGE_SIZE:
                    break
                payload = await asyncio.wait_for(reader.readexactly(payload_len), timeout=DEFAULT_READ_TIMEOUT)
                channel, data = self.transport._decode_payload(payload, flags)

                if channel in self.handlers:
                    result = self.handlers[channel](data)
                    if result is not None:
                        resp_envelope = {"channel": f"{channel}.response", "data": result}
                        resp_raw = msgpack.packb(resp_envelope, use_bin_type=True)
                        resp_flags = 0
                        if len(resp_raw) > COMPRESSION_THRESHOLD:
                            compressed = zlib.compress(resp_raw, level=1)
                            if len(compressed) < len(resp_raw):
                                resp_raw = compressed
                                resp_flags |= FLAG_COMPRESSED
                        resp_header = HEADER_STRUCT.pack(len(resp_raw), msg_id_bytes, time.time(), resp_flags)
                        writer.write(resp_header + resp_raw)
                        await writer.drain()
        except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionResetError):
            pass
        finally:
            writer.close()
            print(f"[binary_ipc] Client disconnected: {addr}")

    def _serve_pipe(self) -> None:
        print("[binary_ipc] Pipe mode — reading from stdin", file=sys.stderr)
        while self._running:
            try:
                channel, data = self.transport.receive(timeout=DEFAULT_READ_TIMEOUT)
                if channel in self.handlers:
                    result = self.handlers[channel](data)
                    if result is not None:
                        self.transport.send(f"{channel}.response", result)
            except TimeoutError:
                continue
            except EOFError:
                break

    def _serve_mmap(self) -> None:
        print("[binary_ipc] Shared-memory mode — polling")
        while self._running:
            try:
                channel, data = self.transport.receive(timeout=1.0)
                if channel in self.handlers:
                    result = self.handlers[channel](data)
                    if result is not None:
                        self.transport.send(f"{channel}.response", result)
            except TimeoutError:
                continue

    def _shutdown(self) -> None:
        print("\n[binary_ipc] Shutting down...")
        self._running = False
        self.transport.close()

    def close(self) -> None:
        self._shutdown()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_schema(rows: list[dict]) -> list[dict]:
    """Infer column names and JS-compatible types from a list of row dicts."""
    if not rows:
        return []
    sample = rows[0]
    type_map = {
        int: "number",
        float: "number",
        str: "string",
        bool: "boolean",
        bytes: "binary",
        type(None): "null",
    }
    return [
        {"name": k, "type": type_map.get(type(v), "object")}
        for k, v in sample.items()
    ]


def _install_signal_handlers(shutdown_fn: Callable) -> None:
    """Install graceful shutdown on SIGINT/SIGTERM."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, lambda *_: shutdown_fn())
        except (OSError, ValueError):
            pass


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark() -> None:
    """Compare JSON vs MessagePack vs MessagePack+zlib across payload sizes."""
    import statistics

    sizes = [
        ("1 KB", 1_024),
        ("10 KB", 10_240),
        ("100 KB", 102_400),
        ("1 MB", 1_048_576),
    ]

    def make_payload(target_bytes: int) -> list[dict]:
        row = {
            "id": 12345,
            "title": "Motion to Compel Discovery — Pigors v Watson",
            "status": "filed",
            "score": 0.9823,
            "tags": ["custody", "discovery", "compelling"],
            "filed_at": "2025-06-15T09:30:00Z",
            "body": "x" * 80,
        }
        row_bytes = len(json.dumps(row).encode())
        count = max(1, target_bytes // row_bytes)
        return [dict(row, id=i) for i in range(count)]

    def timeit(fn: Callable, data: Any, iterations: int = 200) -> tuple[float, int]:
        """Returns (median_ms, output_bytes)."""
        result = fn(data)
        out_size = len(result)
        times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            fn(data)
            times.append((time.perf_counter() - t0) * 1000)
        return statistics.median(times), out_size

    # Serializers
    def json_encode(d: Any) -> bytes:
        return json.dumps(d, default=str, separators=(",", ":")).encode("utf-8")

    def json_decode(b: bytes) -> Any:
        return json.loads(b)

    def mp_encode(d: Any) -> bytes:
        return msgpack.packb(d, use_bin_type=True)

    def mp_decode(b: bytes) -> Any:
        return msgpack.unpackb(b, raw=False)

    def mp_zlib_encode(d: Any) -> bytes:
        return zlib.compress(msgpack.packb(d, use_bin_type=True), level=1)

    def mp_zlib_decode(b: bytes) -> Any:
        return msgpack.unpackb(zlib.decompress(b), raw=False)

    header = (
        f"{'Payload':<10} | {'Method':<18} | {'Encode ms':>10} | {'Decode ms':>10} "
        f"| {'Size':>10} | {'vs JSON':>8}"
    )
    print("\n" + "=" * 80)
    print("  LitigationOS Binary IPC Benchmark — JSON vs MessagePack vs MsgPack+zlib")
    print("=" * 80)
    print(header)
    print("-" * 80)

    for label, target in sizes:
        data = make_payload(target)

        json_bytes = json_encode(data)
        json_size = len(json_bytes)

        results = []

        # JSON
        enc_ms, enc_sz = timeit(json_encode, data)
        dec_ms, _ = timeit(json_decode, json_bytes)
        results.append(("JSON", enc_ms, dec_ms, enc_sz, 1.0))

        # MessagePack
        mp_bytes = mp_encode(data)
        enc_ms, enc_sz = timeit(mp_encode, data)
        dec_ms, _ = timeit(mp_decode, mp_bytes)
        results.append(("MessagePack", enc_ms, dec_ms, enc_sz, enc_sz / json_size))

        # MessagePack + zlib
        mpz_bytes = mp_zlib_encode(data)
        enc_ms, enc_sz = timeit(mp_zlib_encode, data)
        dec_ms, _ = timeit(mp_zlib_decode, mpz_bytes)
        results.append(("MsgPack+zlib", enc_ms, dec_ms, enc_sz, enc_sz / json_size))

        for method, enc, dec, sz, ratio in results:
            print(
                f"{label:<10} | {method:<18} | {enc:>9.3f}ms | {dec:>9.3f}ms "
                f"| {sz:>9,}B | {ratio:>7.1%}"
            )
        print("-" * 80)

    print("\nConclusion: MessagePack is faster and smaller. MsgPack+zlib trades")
    print("minimal CPU for major size reduction — ideal for payloads > 64 KB.\n")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def self_test() -> None:
    """Run basic IPC self-tests."""
    print("[test] IPCMessage round-trip...")
    msg = IPCMessage(channel="test.ping", payload=b"hello world")
    frame = msg.to_frame()
    msg2 = IPCMessage.from_frame(frame)
    assert msg2.payload == b"hello world"
    assert msg2.flags == 0
    print("  ✓ IPCMessage frame round-trip")

    print("[test] BinaryTransport encode/decode...")
    buf = io.BytesIO()
    transport = BinaryTransport(mode="pipe")
    transport._writer = buf

    transport.send("query.result", {"rows": [{"id": 1, "name": "test"}]})
    frame_data = buf.getvalue()
    assert len(frame_data) > HEADER_SIZE
    payload_len = struct.unpack(">I", frame_data[:4])[0]
    flags = frame_data[28]
    payload = frame_data[HEADER_SIZE : HEADER_SIZE + payload_len]
    channel, data = transport._decode_payload(payload, flags)
    assert channel == "query.result"
    assert data["rows"][0]["id"] == 1
    print("  ✓ Small message encode/decode (JSON path)")

    # Large message (msgpack path)
    buf2 = io.BytesIO()
    transport._writer = buf2
    big_data = {"rows": [{"id": i, "val": "x" * 100} for i in range(100)]}
    transport.send("bulk.data", big_data)
    frame_data2 = buf2.getvalue()
    payload_len2 = struct.unpack(">I", frame_data2[:4])[0]
    flags2 = frame_data2[28]
    payload2 = frame_data2[HEADER_SIZE : HEADER_SIZE + payload_len2]
    channel2, data2 = transport._decode_payload(payload2, flags2)
    assert channel2 == "bulk.data"
    assert len(data2["rows"]) == 100
    print("  ✓ Large message encode/decode (msgpack path)")

    # Compression
    buf3 = io.BytesIO()
    transport._writer = buf3
    huge_data = {"text": "A" * 200_000}
    transport.send("compressed.payload", huge_data, compress=True)
    frame_data3 = buf3.getvalue()
    flags3 = frame_data3[28]
    assert flags3 & FLAG_COMPRESSED, "Expected compressed flag"
    payload_len3 = struct.unpack(">I", frame_data3[:4])[0]
    assert payload_len3 < 200_000, "Compressed should be smaller"
    payload3 = frame_data3[HEADER_SIZE : HEADER_SIZE + payload_len3]
    ch3, d3 = transport._decode_payload(payload3, flags3)
    assert len(d3["text"]) == 200_000
    print("  ✓ Compression round-trip")

    # SharedMemoryBridge
    print("[test] SharedMemoryBridge...")
    shm = SharedMemoryBridge(name="litigationos_ipc_test", size=1 * 1024 * 1024)
    try:
        shm.write(b"hello_shm")
        result = shm.read()
        assert result == b"hello_shm", f"Got {result!r}"
        print("  ✓ SharedMemory write/read")

        # Empty read
        assert shm.read() is None
        print("  ✓ SharedMemory empty read returns None")

        # Multiple messages
        shm.write(b"msg1")
        shm.write(b"msg2")
        assert shm.read() == b"msg1"
        assert shm.read() == b"msg2"
        assert shm.read() is None
        print("  ✓ SharedMemory FIFO ordering")
    finally:
        shm.close()

    # Schema inference
    print("[test] Schema inference...")
    schema = _infer_schema([{"id": 1, "name": "test", "score": 0.95, "data": b"\x00"}])
    types = {s["name"]: s["type"] for s in schema}
    assert types["id"] == "number"
    assert types["name"] == "string"
    assert types["score"] == "number"
    assert types["data"] == "binary"
    print("  ✓ Schema inference")

    # Streaming
    print("[test] Streaming...")
    buf4 = io.BytesIO()
    transport._writer = buf4

    def row_gen():
        for i in range(50):
            yield {"id": i, "val": f"row_{i}"}

    total_bytes = transport.send_streaming("stream.test", row_gen(), chunk_size=20, total=50)
    assert total_bytes > 0
    print(f"  ✓ Streaming sent {total_bytes} bytes for 50 rows")

    # IPCServer registration
    print("[test] IPCServer handler registration...")
    server = IPCServer(transport="pipe")
    called = {}
    server.register_handler("echo", lambda d: (called.update(seen=True), d)[-1])
    assert "echo" in server.handlers
    result = server.handlers["echo"]({"msg": "hi"})
    assert result == {"msg": "hi"} and called.get("seen")
    print("  ✓ Handler registration and dispatch")

    # send_query_result
    print("[test] send_query_result...")
    buf5 = io.BytesIO()
    server.transport._writer = buf5
    rows = [{"id": i, "name": f"doc_{i}", "score": i * 0.1} for i in range(10)]
    nbytes = server.send_query_result("query.test", rows)
    assert nbytes > 0
    print(f"  ✓ send_query_result — {nbytes} bytes")

    transport.close()
    server.close()
    print("\n[test] All tests passed ✓")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="binary_ipc",
        description="LitigationOS Binary IPC Transport",
    )
    sub = parser.add_subparsers(dest="command")

    serve_p = sub.add_parser("serve", help="Start IPC server")
    serve_p.add_argument("--mode", choices=["pipe", "socket", "mmap", "auto"], default="auto")
    serve_p.add_argument("--host", default=DEFAULT_HOST)
    serve_p.add_argument("--port", type=int, default=DEFAULT_PORT)

    sub.add_parser("benchmark", help="Run serialization benchmarks")
    sub.add_parser("test", help="Run self-tests")

    args = parser.parse_args()

    if args.command == "serve":
        server = IPCServer(transport=args.mode)
        # Register a default echo handler for testing
        server.register_handler("echo", lambda d: d)
        server.register_handler("ping", lambda _: {"pong": time.time()})
        try:
            asyncio.run(server.serve(host=args.host, port=args.port))
        except KeyboardInterrupt:
            server.close()
    elif args.command == "benchmark":
        benchmark()
    elif args.command == "test":
        self_test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
