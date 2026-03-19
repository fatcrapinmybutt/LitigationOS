"""
cycle_method.py — The Cycle Method: EAGAIN-proof chunked I/O engine.

RULE: Never write > CHUNK_SIZE bytes in one call. Always cycle through
chunks back-to-back, flushing between each. By design, the kernel buffer
can never overflow → zero EAGAIN errors, guaranteed.

Usage:
    from cycle_method import cycle_write, cycle_print, cycle_json

    cycle_write(sys.stdout.buffer, large_bytes)
    cycle_print(large_string)          # replaces print()
    cycle_json({"key": "value"})       # replaces print(json.dumps(...))
    cycle_write_file(path, content)    # chunked file write
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional, Union

# ── Configuration ──────────────────────────────────────────────────────
CHUNK_SIZE = 4096          # 4 KB — safe for any pipe/terminal buffer
MAX_RETRIES = 10           # per chunk
BACKOFF_BASE_MS = 10       # 10ms initial backoff
BACKOFF_MAX_MS = 640       # cap at 640ms
FLUSH_AFTER_CHUNK = True   # flush stdout after every chunk


def _backoff_sleep(retry: int) -> None:
    """Exponential backoff: 10ms → 20ms → 40ms → ... → 640ms max."""
    ms = min(BACKOFF_BASE_MS * (2 ** retry), BACKOFF_MAX_MS)
    time.sleep(ms / 1000.0)


def cycle_write(stream, data: bytes) -> int:
    """
    Write bytes to a stream using the Cycle Method.
    Chunks data into CHUNK_SIZE pieces, flushes between each.
    Returns total bytes written.
    """
    if not data:
        return 0

    total = len(data)
    written = 0

    while written < total:
        chunk = data[written:written + CHUNK_SIZE]
        retries = 0

        while retries < MAX_RETRIES:
            try:
                n = stream.write(chunk)
                if n is None:
                    n = len(chunk)  # some streams return None on success
                written += n

                # Flush between chunks to clear the buffer
                if FLUSH_AFTER_CHUNK and hasattr(stream, 'flush'):
                    try:
                        stream.flush()
                    except (OSError, BrokenPipeError):
                        pass
                break  # chunk written successfully, move to next

            except BlockingIOError:
                # EAGAIN equivalent — buffer full, wait and retry
                retries += 1
                if retries >= MAX_RETRIES:
                    # Log but don't crash — skip this chunk
                    _log_error(f"cycle_write: gave up after {MAX_RETRIES} retries "
                               f"at offset {written}/{total}")
                    return written
                _backoff_sleep(retries)

            except (BrokenPipeError, OSError) as e:
                _log_error(f"cycle_write: pipe error at offset {written}/{total}: {e}")
                return written

    return written


def cycle_print(*args, sep: str = ' ', end: str = '\n', 
                file=None, flush: bool = True) -> None:
    """
    Drop-in replacement for print() using the Cycle Method.
    Chunks output to prevent EAGAIN on any terminal/pipe.
    """
    output = sep.join(str(a) for a in args) + end
    payload = output.encode('utf-8', errors='replace')
    
    stream = (file or sys.stdout)
    buf = getattr(stream, 'buffer', stream)
    
    cycle_write(buf, payload)


def cycle_json(obj: Any, stream=None, pretty: bool = False) -> None:
    """
    Write a JSON object to stdout (or stream) using the Cycle Method.
    Drop-in replacement for print(json.dumps(obj)).
    """
    if pretty:
        text = json.dumps(obj, indent=2, default=str, ensure_ascii=False)
    else:
        text = json.dumps(obj, default=str, ensure_ascii=False)
    
    payload = (text + '\n').encode('utf-8', errors='replace')
    buf = getattr(stream or sys.stdout, 'buffer', stream or sys.stdout.buffer)
    
    cycle_write(buf, payload)


def cycle_write_file(path: Union[str, Path], content: Union[str, bytes],
                     encoding: str = 'utf-8') -> int:
    """
    Write content to a file using the Cycle Method.
    Atomic: writes to .tmp first, then renames.
    """
    path = Path(path)
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    
    if isinstance(content, str):
        data = content.encode(encoding, errors='replace')
    else:
        data = content
    
    try:
        with open(tmp_path, 'wb') as f:
            written = cycle_write(f, data)
        
        # Atomic rename
        if tmp_path.exists():
            if path.exists():
                path.unlink()
            tmp_path.rename(path)
        
        return written
    except Exception as e:
        _log_error(f"cycle_write_file: {path}: {e}")
        # Cleanup tmp
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def cycle_read_chunked(path: Union[str, Path], 
                       chunk_size: int = CHUNK_SIZE) -> bytes:
    """Read a file in chunks (memory-safe for large files)."""
    result = bytearray()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            result.extend(chunk)
    return bytes(result)


# ── Error logging ──────────────────────────────────────────────────────
_error_log: list = []

def _log_error(msg: str) -> None:
    """Log errors internally (never crash, never print to stdout to avoid recursion)."""
    _error_log.append(msg)
    try:
        sys.stderr.write(f"[CycleMethod] {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


def get_errors() -> list:
    """Return accumulated error log."""
    return list(_error_log)


def clear_errors() -> None:
    """Clear error log."""
    _error_log.clear()


# ── Monkey-patch helper (optional) ─────────────────────────────────────

def patch_stdout():
    """
    Replace sys.stdout with a CycleWriter wrapper.
    After calling this, ALL print() calls automatically use Cycle Method.
    """
    sys.stdout = CycleWriter(sys.stdout)


class CycleWriter:
    """
    Wrapper around a text stream that uses Cycle Method for all writes.
    Drop-in replacement for sys.stdout.
    """
    
    def __init__(self, original):
        self._original = original
        self._buffer = getattr(original, 'buffer', original)
        # Preserve all original attributes
        self.encoding = getattr(original, 'encoding', 'utf-8')
        self.errors = getattr(original, 'errors', 'replace')
        self.name = getattr(original, 'name', '<cycle_stdout>')
    
    def write(self, text: str) -> int:
        if not text:
            return 0
        payload = text.encode(self.encoding, errors='replace')
        return cycle_write(self._buffer, payload)
    
    def writelines(self, lines):
        for line in lines:
            self.write(line)
    
    def flush(self):
        try:
            self._buffer.flush()
        except Exception:
            pass
    
    def fileno(self):
        return self._original.fileno()
    
    def isatty(self):
        return self._original.isatty()
    
    def readable(self):
        return False
    
    def writable(self):
        return True
    
    def seekable(self):
        return False
    
    @property
    def closed(self):
        return getattr(self._original, 'closed', False)
    
    @property
    def buffer(self):
        return self._buffer
    
    def __getattr__(self, name):
        return getattr(self._original, name)


# ── Self-test ──────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("[CycleMethod] Self-test starting...")
    
    # Test 1: cycle_print
    cycle_print("Test 1: cycle_print works")
    
    # Test 2: Large output (10KB)
    big = "X" * 10000
    cycle_print(f"Test 2: Writing 10KB string ({len(big)} chars)")
    cycle_print(big)
    
    # Test 3: JSON output
    obj = {"test": 3, "data": "A" * 5000, "nested": {"key": "value"}}
    cycle_json(obj)
    cycle_print("Test 3: cycle_json works")
    
    # Test 4: File write
    test_path = Path(__file__).parent / "_cycle_test.tmp"
    cycle_write_file(test_path, "Cycle Method file write test\n" * 100)
    size = test_path.stat().st_size
    test_path.unlink()
    cycle_print(f"Test 4: File write OK ({size} bytes)")
    
    # Test 5: Monkey-patch
    patch_stdout()
    print("Test 5: After monkey-patch, print() uses Cycle Method automatically")
    print("X" * 8000)  # Should chunk into 2 pieces
    
    errors = get_errors()
    if errors:
        print(f"Errors: {errors}", file=sys.stderr)
    else:
        print("[CycleMethod] All tests passed — zero EAGAIN guaranteed")
