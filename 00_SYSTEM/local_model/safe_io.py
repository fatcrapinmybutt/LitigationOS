"""
safe_io.py — Corruption-prevention I/O utilities for LitigationOS.

All writes are atomic (tmp → verify → rename). All copies/moves are
checksum-verified. SQLite writes use WAL mode with busy timeouts and
post-write integrity checks. Integrated with Cycle Method for zero EAGAIN.

Usage:
    from safe_io import SafeIO

    SafeIO.write_file("path/to/file.txt", content)
    SafeIO.write_bytes("path/to/file.bin", data)
    SafeIO.copy_file("src.txt", "dst.txt")
    SafeIO.move_file("src.txt", "dst.txt")
    SafeIO.safe_db_write("path/to/db.sqlite", "INSERT INTO ...", params)
    SafeIO.cycle_stdout(large_text)    # Cycle Method stdout
    report = SafeIO.scan_health("C:/path/to/root")
"""
from __future__ import annotations

# ── Cycle Method integration ──────────────────────────────────────────
import sys as _sys
from pathlib import Path as _CyclePath
try:
    _sys.path.insert(0, str(_CyclePath(__file__).resolve().parent.parent))
    from cycle_method import cycle_write as _cycle_write, cycle_print as _cycle_print, cycle_json as _cycle_json
    CYCLE_METHOD_AVAILABLE = True
except ImportError:
    CYCLE_METHOD_AVAILABLE = False
    _cycle_write = None
    _cycle_print = print
    _cycle_json = None

import hashlib
import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

logger = logging.getLogger("litigationos.safe_io")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _md5(path: Union[str, Path]) -> str:
    """Return hex MD5 digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1 << 20)  # 1 MiB
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _tmp_path(path: Union[str, Path]) -> str:
    """Generate a .tmp sibling path for atomic writes."""
    p = Path(path)
    return str(p.with_suffix(p.suffix + ".tmp"))


# ---------------------------------------------------------------------------
# SafeIO
# ---------------------------------------------------------------------------

class SafeIO:
    """Atomic, verified I/O operations. Cycle Method integrated."""

    # ------------------------------------------------------------------
    # Cycle Method stream writes (zero EAGAIN)
    # ------------------------------------------------------------------
    @staticmethod
    def cycle_stdout(text: str) -> None:
        """Write text to stdout using Cycle Method (4KB chunks)."""
        if CYCLE_METHOD_AVAILABLE and _cycle_write:
            _cycle_write(_sys.stdout.buffer, text.encode('utf-8', errors='replace'))
        else:
            _sys.stdout.write(text)
            _sys.stdout.flush()

    @staticmethod
    def cycle_json(obj, stream=None) -> None:
        """Write JSON to stdout using Cycle Method."""
        if CYCLE_METHOD_AVAILABLE and _cycle_json:
            _cycle_json(obj, stream=stream)
        else:
            import json
            _sys.stdout.write(json.dumps(obj, default=str) + "\n")
            _sys.stdout.flush()

    # ------------------------------------------------------------------
    # Text writes
    # ------------------------------------------------------------------
    @staticmethod
    def write_file(
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8",
    ) -> None:
        """Atomic text write: write → verify → rename.

        Raises IOError if verification fails.
        """
        path = str(path)
        tmp = _tmp_path(path)
        try:
            with open(tmp, "w", encoding=encoding) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Verify round-trip
            with open(tmp, "r", encoding=encoding) as f:
                if f.read() != content:
                    raise IOError(f"Write verification failed for {path}")

            # Atomic replace
            os.replace(tmp, path)
            logger.debug("write_file OK: %s", path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    # ------------------------------------------------------------------
    # Binary writes
    # ------------------------------------------------------------------
    @staticmethod
    def write_bytes(
        path: Union[str, Path],
        data: bytes,
    ) -> None:
        """Atomic binary write with checksum verification."""
        path = str(path)
        tmp = _tmp_path(path)
        expected = hashlib.md5(data).hexdigest()
        try:
            with open(tmp, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            if _md5(tmp) != expected:
                raise IOError(f"Binary write checksum mismatch for {path}")

            os.replace(tmp, path)
            logger.debug("write_bytes OK: %s", path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------
    @staticmethod
    def copy_file(
        src: Union[str, Path],
        dst: Union[str, Path],
    ) -> None:
        """Copy with MD5 checksum verification.

        Raises IOError if checksums do not match after copy.
        """
        src, dst = str(src), str(dst)
        src_hash = _md5(src)
        shutil.copy2(src, dst)
        if _md5(dst) != src_hash:
            os.remove(dst)
            raise IOError(
                f"Copy verification failed: {src} → {dst} "
                f"(expected {src_hash}, got {_md5(dst)})"
            )
        logger.debug("copy_file OK: %s → %s", src, dst)

    # ------------------------------------------------------------------
    # Move
    # ------------------------------------------------------------------
    @staticmethod
    def move_file(
        src: Union[str, Path],
        dst: Union[str, Path],
    ) -> None:
        """Move with checksum verification: copy → verify → delete source."""
        src, dst = str(src), str(dst)
        src_hash = _md5(src)
        shutil.copy2(src, dst)
        if _md5(dst) != src_hash:
            os.remove(dst)
            raise IOError(
                f"Move verification failed: {src} → {dst}"
            )
        os.remove(src)
        logger.debug("move_file OK: %s → %s", src, dst)

    # ------------------------------------------------------------------
    # SQLite
    # ------------------------------------------------------------------
    @staticmethod
    def safe_db_write(
        db_path: Union[str, Path],
        sql: str,
        params: Optional[Sequence[Any]] = None,
        busy_timeout_ms: int = 10_000,
        check_integrity: bool = True,
    ) -> sqlite3.Cursor:
        """Execute SQL with WAL mode, busy timeout, and optional integrity check.

        Returns the cursor so callers can read lastrowid / rowcount.
        """
        db_path = str(db_path)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
            conn.execute("PRAGMA journal_mode = WAL")

            cur = conn.execute(sql, params or ())
            conn.commit()

            if check_integrity:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    raise IOError(
                        f"Database integrity check failed after write: "
                        f"{db_path} — {result}"
                    )

            logger.debug("safe_db_write OK: %s", db_path)
            return cur
        finally:
            conn.close()

    @staticmethod
    def safe_db_execute_many(
        db_path: Union[str, Path],
        sql: str,
        params_seq: Sequence[Sequence[Any]],
        busy_timeout_ms: int = 10_000,
        check_integrity: bool = True,
    ) -> None:
        """Batch execute with the same safety guarantees."""
        db_path = str(db_path)
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
            conn.execute("PRAGMA journal_mode = WAL")

            conn.executemany(sql, params_seq)
            conn.commit()

            if check_integrity:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                if result[0] != "ok":
                    raise IOError(
                        f"Database integrity check failed after batch write: "
                        f"{db_path} — {result}"
                    )
            logger.debug("safe_db_execute_many OK: %s (%d rows)", db_path, len(params_seq))
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Health scanner
    # ------------------------------------------------------------------
    @staticmethod
    def scan_health(
        root: Union[str, Path],
        skip_dirs: Optional[set] = None,
        max_zip_size: int = 100_000_000,
        max_db_size: int = 200_000_000,
        max_text_size: int = 50_000_000,
    ) -> Dict[str, Any]:
        """Run a full corruption scan on a directory tree.

        Returns a dict with keys: zip, db, text_null, text_empty, summary.
        """
        if skip_dirs is None:
            skip_dirs = {"node_modules", ".git", "__pycache__", ".next", "dist", "build"}

        root = Path(root)
        results: Dict[str, List[Dict[str, str]]] = {
            "zip_corrupt": [],
            "db_corrupt": [],
            "text_null_bytes": [],
            "text_empty": [],
        }
        counts = {"zip_ok": 0, "db_ok": 0, "text_ok": 0}

        text_exts = {".md", ".txt", ".py", ".js", ".json", ".csv", ".html"}

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fname in filenames:
                fp = os.path.join(dirpath, fname)
                ext = os.path.splitext(fname)[1].lower()

                # ZIP check
                if ext == ".zip":
                    try:
                        sz = os.path.getsize(fp)
                        if sz == 0:
                            results["zip_corrupt"].append({"path": fp, "issue": "empty", "severity": "HIGH"})
                            continue
                        if sz > max_zip_size:
                            continue
                        with zipfile.ZipFile(fp) as z:
                            bad = z.testzip()
                            if bad:
                                results["zip_corrupt"].append({"path": fp, "issue": f"bad member: {bad}", "severity": "HIGH"})
                            else:
                                counts["zip_ok"] += 1
                    except Exception as e:
                        results["zip_corrupt"].append({"path": fp, "issue": str(e), "severity": "CRITICAL"})

                # DB check
                elif ext in (".db", ".sqlite", ".sqlite3"):
                    try:
                        sz = os.path.getsize(fp)
                        if sz == 0:
                            results["db_corrupt"].append({"path": fp, "issue": "empty", "severity": "HIGH"})
                            continue
                        if sz > max_db_size:
                            continue
                        conn = sqlite3.connect(fp)
                        conn.execute("PRAGMA busy_timeout = 5000")
                        r = conn.execute("PRAGMA integrity_check").fetchone()
                        conn.close()
                        if r[0] != "ok":
                            results["db_corrupt"].append({"path": fp, "issue": str(r), "severity": "HIGH"})
                        else:
                            counts["db_ok"] += 1
                    except Exception as e:
                        results["db_corrupt"].append({"path": fp, "issue": str(e), "severity": "CRITICAL"})

                # Text check
                elif ext in text_exts:
                    try:
                        sz = os.path.getsize(fp)
                        if sz == 0:
                            results["text_empty"].append({"path": fp})
                            continue
                        if sz > max_text_size:
                            continue
                        with open(fp, "rb") as fh:
                            raw = fh.read()
                        if b"\x00" in raw:
                            results["text_null_bytes"].append({"path": fp})
                        else:
                            counts["text_ok"] += 1
                    except Exception:
                        pass

        results["summary"] = {
            "zip_ok": counts["zip_ok"],
            "zip_corrupt": len(results["zip_corrupt"]),
            "db_ok": counts["db_ok"],
            "db_corrupt": len(results["db_corrupt"]),
            "text_ok": counts["text_ok"],
            "text_null_bytes": len(results["text_null_bytes"]),
            "text_empty": len(results["text_empty"]),
        }
        return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="LitigationOS SafeIO health scanner")
    parser.add_argument("root", help="Root directory to scan")
    parser.add_argument("-o", "--output", help="Output JSON path")
    args = parser.parse_args()

    print(f"Scanning {args.root} ...", file=sys.stderr)
    report = SafeIO.scan_health(args.root)

    s = report["summary"]
    print(f"ZIP:  {s['zip_ok']} ok, {s['zip_corrupt']} corrupt", file=sys.stderr)
    print(f"DB:   {s['db_ok']} ok, {s['db_corrupt']} corrupt", file=sys.stderr)
    print(f"Text: {s['text_ok']} ok, {s['text_null_bytes']} null-bytes, {s['text_empty']} empty", file=sys.stderr)

    out = json.dumps(report, indent=2)
    if args.output:
        SafeIO.write_file(args.output, out)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(out)
