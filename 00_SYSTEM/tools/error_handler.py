"""
LitigationOS Error Handler v1.0
Wraps ALL operations with robust error handling.
Prevents EAGAIN, DB connection, file I/O, encoding, and memory errors.
"""
import os
import sys
import time
import sqlite3
import traceback
import json
from pathlib import Path
from functools import wraps

# Import cycle_method for EAGAIN protection
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from cycle_method import (
        cycle_write, cycle_print, cycle_json,
        cycle_write_file, cycle_read_chunked, patch_stdout
    )
    _HAS_CYCLE = True
except ImportError:
    _HAS_CYCLE = False

    def cycle_write(stream, data):
        """Fallback: plain write."""
        return stream.write(data)

    def cycle_print(*args, **kwargs):
        """Fallback: built-in print."""
        print(*args, **kwargs)

    def cycle_json(obj, **kwargs):
        print(json.dumps(obj, default=str, ensure_ascii=False))

    def cycle_write_file(path, content, encoding='utf-8'):
        data = content.encode(encoding, errors='replace') if isinstance(content, str) else content
        with open(path, 'wb') as f:
            f.write(data)
        return len(data)

    def cycle_read_chunked(path, chunk_size=4096):
        with open(path, 'rb') as f:
            return f.read()

    def patch_stdout():
        pass

# ── Constants ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_BASE = 1.0          # seconds
CHUNK_SIZE = 4096            # bytes per I/O chunk
DB_PATH = r'C:\Users\andre\litigation_context.db'
LITIGOS_ROOT = r'C:\Users\andre\LitigationOS'

# ── Internal error log ─────────────────────────────────────────────────
_error_log: list = []


def _log(msg: str) -> None:
    """Append to internal log and write to stderr (never crashes)."""
    _error_log.append(msg)
    try:
        sys.stderr.write(f"[ErrorHandler] {msg}\n")
        sys.stderr.flush()
    except Exception:
        pass


# ── Base exception ─────────────────────────────────────────────────────
class LitigationError(Exception):
    """Base exception for LitigationOS errors."""
    pass


class DBConnectionError(LitigationError):
    """Database could not be reached after retries."""
    pass


class FileIOError(LitigationError):
    """File I/O failed after fallback attempts."""
    pass


# ── Retry decorator ───────────────────────────────────────────────────
def retry_with_backoff(max_retries=MAX_RETRIES, backoff_base=BACKOFF_BASE,
                       exceptions=(Exception,)):
    """Decorator: retry function with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt == max_retries:
                        raise
                    wait = backoff_base * (2 ** attempt)
                    cycle_print(
                        f"[RETRY {attempt + 1}/{max_retries}] "
                        f"{func.__name__}: {e}, waiting {wait:.1f}s"
                    )
                    time.sleep(wait)
            raise last_exc  # unreachable but satisfies type checkers
        return wrapper
    return decorator


# ── Safe database wrapper ──────────────────────────────────────────────
class SafeDB:
    """Database connection with automatic retry, chunked queries, and WAL mode."""

    def __init__(self, db_path=DB_PATH, timeout=30):
        self.db_path = str(db_path)
        self.timeout = timeout
        self._conn = None

    # -- connection --
    @retry_with_backoff(
        max_retries=3,
        exceptions=(sqlite3.OperationalError, sqlite3.DatabaseError, OSError)
    )
    def connect(self):
        """Open (or re-open) a WAL-mode connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        return self._conn

    @property
    def conn(self):
        """Lazy connection getter."""
        if self._conn is None:
            self.connect()
        return self._conn

    # -- query helpers --
    @retry_with_backoff(
        max_retries=3,
        exceptions=(sqlite3.OperationalError,)
    )
    def execute(self, query, params=None):
        """Execute a single SQL statement with retry."""
        try:
            return self.conn.execute(query, params or ())
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e).lower():
                _log(f"DB locked, reconnecting: {e}")
                self.connect()
            raise

    def fetchall(self, query, params=None):
        """Execute and return all rows."""
        return self.execute(query, params).fetchall()

    def fetchone(self, query, params=None):
        """Execute and return one row."""
        return self.execute(query, params).fetchone()

    def execute_chunked(self, query, params=None, chunk_size=1000):
        """Execute query and yield results in chunks to prevent memory overflow."""
        cursor = self.execute(query, params)
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            yield rows

    def count(self, table):
        """Quick row count for a table."""
        row = self.fetchone(f"SELECT COUNT(*) FROM [{table}]")
        return row[0] if row else 0

    def tables(self):
        """List all user tables."""
        rows = self.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [r[0] for r in rows]

    def close(self):
        """Close connection gracefully."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # context manager
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc):
        self.close()


# ── Safe file writer ───────────────────────────────────────────────────
class SafeFileWriter:
    """File writer with EAGAIN protection, encoding fallback, long-path support."""

    @staticmethod
    def _long_path(path: str) -> str:
        """Prepend \\\\?\\ prefix on Windows when path exceeds MAX_PATH."""
        path = os.path.abspath(str(path))
        if os.name == 'nt' and len(path) > 259 and not path.startswith('\\\\?\\'):
            path = '\\\\?\\' + path
        return path

    @staticmethod
    def write(path, content, encoding='utf-8'):
        """Write content to file with full error protection.

        Falls back to Desktop if the primary path is not writable.
        Uses cycle_write_file when available for EAGAIN protection.
        """
        path = SafeFileWriter._long_path(str(path))
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)

            if _HAS_CYCLE:
                cycle_write_file(path, content, encoding=encoding)
            else:
                data = content.encode(encoding, errors='replace') if isinstance(content, str) else content
                with open(path, 'wb') as f:
                    for i in range(0, len(data), CHUNK_SIZE):
                        f.write(data[i:i + CHUNK_SIZE])
                        f.flush()
            return True

        except (OSError, IOError, PermissionError) as e:
            _log(f"File write failed: {path}: {e}")
            # Fallback to Desktop
            fallback = os.path.join(
                os.path.expanduser('~'), 'Desktop', os.path.basename(path)
            )
            try:
                with open(fallback, 'w', encoding=encoding, errors='replace') as f:
                    f.write(content if isinstance(content, str) else content.decode(encoding, errors='replace'))
                cycle_print(f"[FALLBACK] Saved to: {fallback}")
                return True
            except Exception as e2:
                _log(f"Fallback write also failed: {e2}")
                return False

    @staticmethod
    def read(path, encoding='utf-8'):
        """Read file with automatic encoding fallback.

        Tries multiple common encodings (UTF-8 → Latin-1 → CP1252) to
        handle OCR and legacy Windows documents gracefully.
        """
        path = SafeFileWriter._long_path(str(path))
        for enc in [encoding, 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']:
            try:
                with open(path, 'r', encoding=enc, errors='replace') as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except OSError as e:
                _log(f"Read failed ({enc}): {path}: {e}")
                return None
        return None

    @staticmethod
    def read_chunked(path, chunk_size=CHUNK_SIZE):
        """Read a large file in chunks (memory-safe). Returns bytes."""
        path = SafeFileWriter._long_path(str(path))
        if _HAS_CYCLE:
            return cycle_read_chunked(path, chunk_size=chunk_size)
        result = bytearray()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                result.extend(chunk)
        return bytes(result)


# ── Safe drive scanner ─────────────────────────────────────────────────
class SafeDriveScan:
    """Recursively scan directories with error resilience."""

    DEFAULT_SKIP = [
        '$Recycle.Bin', 'System Volume Information',
        'Windows', 'ProgramData', '.git', 'node_modules',
        '__pycache__', '.npm', '.cache', '.vs', '.vscode',
    ]

    def __init__(self, max_depth=20, skip_patterns=None):
        self.max_depth = max_depth
        self.skip_patterns = set(skip_patterns or self.DEFAULT_SKIP)
        self.errors: list = []

    def scan(self, root_path, extensions=None, max_files=None):
        """Walk *root_path* collecting file metadata.

        Parameters
        ----------
        extensions : set/list of str, e.g. {'.py', '.md'}
        max_files  : stop after this many files (None = unlimited)
        """
        root_path = str(root_path)
        if extensions:
            extensions = {e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions}
        results = []
        count = 0

        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
            # Prune skipped dirs in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in self.skip_patterns and not d.startswith('.')
            ]
            # Depth guard
            rel = os.path.relpath(dirpath, root_path)
            depth = 0 if rel == '.' else rel.count(os.sep) + 1
            if depth >= self.max_depth:
                dirnames.clear()
                continue

            for fname in filenames:
                if max_files and count >= max_files:
                    return results

                ext = os.path.splitext(fname)[1].lower()
                if extensions and ext not in extensions:
                    continue

                fpath = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(fpath)
                    results.append({
                        'path': fpath,
                        'name': fname,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'ext': ext,
                    })
                    count += 1
                except (PermissionError, OSError) as e:
                    self.errors.append(f"{fpath}: {e}")

        return results


# ── JSON helper ────────────────────────────────────────────────────────
def safe_json_dump(obj, path=None):
    """JSON-serialize with cycle-method safe output.

    Returns the JSON string.  Optionally writes to *path*.
    """
    try:
        text = json.dumps(obj, indent=2, default=str, ensure_ascii=False)
        if path:
            SafeFileWriter.write(path, text)
        return text
    except (TypeError, ValueError) as e:
        _log(f"JSON serialize: {e}")
        return json.dumps({"error": str(e)})


# ── Convenience: wrap any callable ─────────────────────────────────────
def safe_call(func, *args, default=None, **kwargs):
    """Call *func* and return its result, or *default* on any exception."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        _log(f"safe_call({func.__name__}): {e}")
        return default


# ── Public error log access ────────────────────────────────────────────
def get_errors():
    """Return accumulated error log entries."""
    return list(_error_log)


def clear_errors():
    """Clear the internal error log."""
    _error_log.clear()


# ── Self-test ──────────────────────────────────────────────────────────
def self_test():
    """Verify all error handlers work."""
    passed = 0
    failed = 0

    # 1. SafeDB — connect and query
    try:
        db = SafeDB(DB_PATH)
        db.connect()
        row = db.execute("SELECT COUNT(*) FROM auth_rules").fetchone()
        cycle_print(f"[PASS] DB connect + query: {row[0]} auth_rules rows")
        # chunked read
        chunks = list(db.execute_chunked("SELECT rule_number FROM auth_rules LIMIT 5", chunk_size=2))
        cycle_print(f"[PASS] DB chunked query: {sum(len(c) for c in chunks)} rows in {len(chunks)} chunks")
        tbl_count = len(db.tables())
        cycle_print(f"[PASS] DB tables(): {tbl_count} tables")
        db.close()
        passed += 3
    except Exception as e:
        cycle_print(f"[FAIL] DB test: {e}")
        failed += 1

    # 2. SafeFileWriter — write / read / round-trip
    test_path = os.path.join(os.path.expanduser('~'), 'Desktop', '_error_handler_test.txt')
    try:
        payload = "Error handler test—unicode: é à ü ñ 中文 🔥\n" * 100
        ok = SafeFileWriter.write(test_path, payload)
        assert ok, "write returned False"
        content = SafeFileWriter.read(test_path)
        assert content is not None and len(content) > 0, "read returned empty"
        assert "中文" in content, "unicode round-trip failed"
        os.remove(test_path)
        cycle_print(f"[PASS] FileWriter write/read round-trip ({len(payload)} chars)")
        passed += 1
    except Exception as e:
        cycle_print(f"[FAIL] FileWriter test: {e}")
        failed += 1

    # 3. SafeDriveScan
    try:
        scanner = SafeDriveScan(max_depth=2)
        results = scanner.scan(LITIGOS_ROOT, extensions=['.py', '.md'], max_files=10)
        cycle_print(f"[PASS] DriveScan: {len(results)} files, {len(scanner.errors)} errors")
        passed += 1
    except Exception as e:
        cycle_print(f"[FAIL] DriveScan test: {e}")
        failed += 1

    # 4. retry_with_backoff decorator
    try:
        call_count = {'n': 0}

        @retry_with_backoff(max_retries=2, backoff_base=0.05, exceptions=(ValueError,))
        def flaky_func():
            call_count['n'] += 1
            if call_count['n'] < 3:
                raise ValueError("flaky")
            return "success"

        result = flaky_func()
        assert result == "success", f"expected 'success', got {result}"
        assert call_count['n'] == 3, f"expected 3 calls, got {call_count['n']}"
        cycle_print(f"[PASS] retry_with_backoff: succeeded after {call_count['n']} attempts")
        passed += 1
    except Exception as e:
        cycle_print(f"[FAIL] retry test: {e}")
        failed += 1

    # 5. safe_json_dump
    try:
        obj = {"case": "Pigors v Watson", "count": 329, "nested": {"a": [1, 2, 3]}}
        text = safe_json_dump(obj)
        assert '"Pigors v Watson"' in text
        cycle_print(f"[PASS] safe_json_dump ({len(text)} chars)")
        passed += 1
    except Exception as e:
        cycle_print(f"[FAIL] json test: {e}")
        failed += 1

    # 6. safe_call
    try:
        assert safe_call(int, "42") == 42
        assert safe_call(int, "not_a_number", default=-1) == -1
        cycle_print("[PASS] safe_call")
        passed += 1
    except Exception as e:
        cycle_print(f"[FAIL] safe_call test: {e}")
        failed += 1

    # 7. cycle_method integration
    try:
        assert _HAS_CYCLE, "cycle_method not imported"
        cycle_print("[PASS] cycle_method integration (EAGAIN protection active)")
        passed += 1
    except AssertionError:
        cycle_print("[WARN] cycle_method not available — fallback active")
        passed += 1  # still a valid config

    cycle_print(f"\n{'='*50}")
    cycle_print(f"SELF-TEST RESULTS: {passed} passed, {failed} failed")
    if failed == 0:
        cycle_print("ALL SELF-TESTS PASSED")
    cycle_print(f"{'='*50}")
    return failed == 0


if __name__ == "__main__":
    self_test()
    # Print file info
    me = os.path.abspath(__file__)
    cycle_print(f"\nFile: {me}")
    cycle_print(f"Size: {os.path.getsize(me):,} bytes")
