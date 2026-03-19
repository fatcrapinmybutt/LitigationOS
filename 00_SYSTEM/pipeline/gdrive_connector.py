from __future__ import annotations
import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""Google Drive connector with rclone fallback — OPTIONAL infrastructure.

Primary: rclone mirror (local copy of Drive, no network needed after sync)
Secondary: Google Drive API (requires credentials, network)
Fallback: Manual file picker / local scan of SYNC_DIR

The pipeline works WITHOUT this module by scanning local drives.
"""

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Failsafe imports (matches config.py pattern) ---
try:
    from failsafe import safe_call, timeout, never_crash, CircuitBreaker
except ImportError:
    # Minimal inline fallbacks so module loads even without failsafe.py
    def timeout(seconds: float, fallback: Any = None):          # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

    def never_crash(fallback: Any = None):                      # type: ignore[misc]
        def decorator(fn):
            def wrapper(*a, **kw):
                try:
                    return fn(*a, **kw)
                except Exception:
                    return fallback
            return wrapper
        return decorator

    def safe_call(fn, *a, timeout_s=30, fallback=None, component="", **kw):
        try:
            return fn(*a, **kw)
        except Exception:
            return fallback

    @dataclass
    class CircuitBreaker:
        name: str = ""
        threshold: int = 3
        cooldown: float = 60.0
        _failures: int = 0
        _state: str = "CLOSED"
        _last_failure: float = 0.0

        def allow(self) -> bool:
            if self._state == "OPEN":
                if time.time() - self._last_failure > self.cooldown:
                    self._state = "HALF-OPEN"
                    return True
                return False
            return True

        def record_success(self):
            self._failures = 0
            self._state = "CLOSED"

        def record_failure(self):
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self.threshold:
                self._state = "OPEN"

# --- PipelineLogger (matches config.py pattern) ---
try:
    from config import PipelineLogger, LITIGOS_ROOT
except ImportError:
    LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

    class PipelineLogger:  # type: ignore[no-redef]
        def __init__(self, phase: str, cycle_dir: Path | None = None):
            self._phase = phase
            self._log = logging.getLogger(f"gdrive.{phase}")
            if not self._log.handlers:
                h = logging.StreamHandler(sys.stderr)
                h.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s"))
                self._log.addHandler(h)
                self._log.setLevel(logging.INFO)

        def info(self, msg: str):  self._log.info(msg)
        def warn(self, msg: str):  self._log.warning(msg)
        def error(self, msg: str): self._log.error(msg)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = LITIGOS_ROOT / "litigation_context.db"

SAFE_SUBTREES: tuple[Path, ...] = (
    LITIGOS_ROOT,
    Path(r"C:\Users\andre\scans"),
)

# Rate-limit: 100 requests per 100 seconds
_RATE_WINDOW = 100.0
_RATE_MAX = 100
_rate_timestamps: list[float] = []

_logger = PipelineLogger("gdrive_connector")

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_CREATE_DRIVE_FILES = """\
CREATE TABLE IF NOT EXISTS drive_files (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL DEFAULT 'rclone',
    remote_path  TEXT NOT NULL,
    local_path   TEXT,
    file_name    TEXT NOT NULL,
    mime_type    TEXT,
    size_bytes   INTEGER,
    modified_time TEXT,
    sha256       TEXT,
    drive_id     TEXT,
    synced_at    TEXT NOT NULL,
    ingested     INTEGER DEFAULT 0,
    UNIQUE(remote_path, source)
);
"""

_CREATE_INGEST_LOGS = """\
CREATE TABLE IF NOT EXISTS ingest_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    action    TEXT NOT NULL,
    source    TEXT,
    file_id   TEXT,
    file_path TEXT,
    detail    TEXT,
    ok        INTEGER DEFAULT 1
);
"""


def _get_db(db_path: Path | None = None, readonly: bool = False) -> sqlite3.Connection:
    """Open DB with WAL mode.  Read-only when *readonly* is True."""
    p = db_path or DB_PATH
    if readonly:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        conn.execute("PRAGMA query_only = ON")
    else:
        conn = sqlite3.connect(str(p))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=120000")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(_CREATE_DRIVE_FILES)
    conn.executescript(_CREATE_INGEST_LOGS)


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

def _validate_path(path: str | Path) -> bool:
    """Reject path traversal attempts.  Only allow paths under SAFE_SUBTREES."""
    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError):
        return False
    for subtree in SAFE_SUBTREES:
        try:
            resolved.relative_to(subtree.resolve())
            return True
        except ValueError:
            continue
    return False


def _rate_limit() -> None:
    """Block until rate budget is available (100 req / 100 s)."""
    now = time.time()
    global _rate_timestamps
    _rate_timestamps = [t for t in _rate_timestamps if now - t < _RATE_WINDOW]
    if len(_rate_timestamps) >= _RATE_MAX:
        wait = _RATE_WINDOW - (now - _rate_timestamps[0]) + 0.1
        _logger.warn(f"Rate limit reached — sleeping {wait:.1f}s")
        time.sleep(wait)
    _rate_timestamps.append(time.time())


def _log_access(conn: sqlite3.Connection, action: str,
                file_id: str | None = None, path: str | None = None,
                detail: str | None = None, ok: bool = True) -> None:
    """Append an audit row to ingest_logs."""
    conn.execute(
        "INSERT INTO ingest_logs (ts, action, source, file_id, file_path, detail, ok) "
        "VALUES (?, ?, 'gdrive_connector', ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), action, file_id, path, detail, int(ok)),
    )
    conn.commit()


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest for *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# GDriveConnector
# ---------------------------------------------------------------------------

class GDriveConnector:
    """Google Drive integration with offline-first design.

    Primary:   rclone mirror (local copy of Drive, no network needed after sync)
    Secondary: Google Drive API (requires credentials, network)
    Fallback:  Manual file picker (Electron native dialog) / local scan
    """

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    SYNC_DIR  = LITIGOS_ROOT / "00_SYSTEM" / "gdrive_mirror"
    CRED_PATH = LITIGOS_ROOT / "00_SYSTEM" / "credentials" / "gdrive_credentials.json"
    TOKEN_PATH = LITIGOS_ROOT / "00_SYSTEM" / "credentials" / "gdrive_token.json"

    def __init__(
        self,
        mode: str = "rclone",
        sync_dir: Path | str | None = None,
        db_path: Path | str | None = None,
    ):
        if mode not in ("rclone", "api", "local"):
            raise ValueError(f"Invalid mode '{mode}' — choose rclone | api | local")
        self.mode = mode
        self.sync_dir = Path(sync_dir) if sync_dir else self.SYNC_DIR
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn: sqlite3.Connection | None = None
        self._api_service: Any = None
        self._breaker = CircuitBreaker(name="gdrive_api", threshold=3, cooldown=60.0)
        _logger.info(f"GDriveConnector init  mode={mode}  sync_dir={self.sync_dir}")

    # -- DB lifecycle ------------------------------------------------------

    def _db(self, readonly: bool = False) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _get_db(self.db_path, readonly=readonly)
            _ensure_tables(self._conn)
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ======================================================================
    # Rclone methods (PRIMARY)
    # ======================================================================

    @never_crash(fallback=False)
    def rclone_setup(self, remote_name: str = "gdrive") -> bool:
        """Check if rclone is configured with a Google Drive remote."""
        if not shutil.which("rclone"):
            _logger.warn("rclone binary not found on PATH")
            return False
        result = subprocess.run(
            ["rclone", "listremotes"],
            capture_output=True, text=True, timeout=15,
        )
        remotes = [r.strip().rstrip(":") for r in result.stdout.splitlines() if r.strip()]
        ok = remote_name in remotes
        if not ok:
            _logger.warn(f"rclone remote '{remote_name}' not configured. "
                         f"Available: {remotes}")
        return ok

    @never_crash(fallback={"files_synced": 0, "bytes_transferred": 0, "errors": ["crash"]})
    def rclone_sync(
        self,
        remote_path: str = "Litigation_Intake",
        local_dir: Path | str | None = None,
        dry_run: bool = False,
        remote_name: str = "gdrive",
    ) -> dict:
        """Sync a Google Drive folder to local directory via rclone.

        Returns ``{files_synced, bytes_transferred, errors}``.
        """
        dest = Path(local_dir) if local_dir else self.sync_dir
        if not _validate_path(dest):
            return {"files_synced": 0, "bytes_transferred": 0,
                    "errors": [f"Destination outside safe subtree: {dest}"]}

        dest.mkdir(parents=True, exist_ok=True)
        source = f"{remote_name}:{remote_path}"

        cmd = [
            "rclone", "sync", source, str(dest),
            "--progress",
            "--drive-acknowledge-abuse",
            "--stats-one-line",
            "--stats", "5s",
            "--log-level", "NOTICE",
        ]
        if dry_run:
            cmd.append("--dry-run")

        _logger.info(f"rclone sync  {source} → {dest}  dry_run={dry_run}")
        _log_access(self._db(), "rclone_sync", path=str(dest),
                     detail=f"source={source} dry_run={dry_run}")

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        metrics = self._parse_rclone_output(proc.stdout + "\n" + proc.stderr)
        if proc.returncode != 0:
            metrics["errors"].append(proc.stderr.strip()[-500:] if proc.stderr else "unknown")

        # Register synced files in DB
        if not dry_run and proc.returncode == 0:
            self._register_local_files(dest, source="rclone")

        return metrics

    @never_crash(fallback=[])
    def rclone_list(
        self,
        remote_path: str = "Litigation_Intake",
        remote_name: str = "gdrive",
    ) -> list[dict]:
        """List files in a Google Drive folder via rclone lsjson."""
        source = f"{remote_name}:{remote_path}"
        proc = subprocess.run(
            ["rclone", "lsjson", source, "--recursive", "--no-mimetype"],
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            _logger.error(f"rclone lsjson failed: {proc.stderr[:300]}")
            return []
        try:
            items = json.loads(proc.stdout)
        except json.JSONDecodeError:
            _logger.error("rclone lsjson returned invalid JSON")
            return []
        return [
            {
                "name": it.get("Name", ""),
                "size": it.get("Size", 0),
                "modified": it.get("ModTime", ""),
                "path": it.get("Path", ""),
                "is_dir": it.get("IsDir", False),
            }
            for it in items
            if not it.get("IsDir", False)
        ]

    @never_crash(fallback=[])
    def rclone_check_new(
        self,
        remote_path: str = "Litigation_Intake",
        remote_name: str = "gdrive",
    ) -> list[dict]:
        """Return files in rclone remote not yet in drive_files table."""
        remote_files = self.rclone_list(remote_path, remote_name)
        if not remote_files:
            return []

        db = self._db(readonly=True)
        rows = db.execute(
            "SELECT remote_path FROM drive_files WHERE source = 'rclone'"
        ).fetchall()
        known = {r["remote_path"] for r in rows}

        new = [f for f in remote_files if f["path"] not in known]
        _logger.info(f"rclone_check_new: {len(new)} new / {len(remote_files)} total")
        return new

    # ======================================================================
    # Google Drive API methods (SECONDARY)
    # ======================================================================

    @never_crash(fallback=False)
    def api_authenticate(self) -> bool:
        """Authenticate with Google Drive API using OAuth2.

        Reads credentials from CRED_PATH, saves token to TOKEN_PATH.
        Falls back silently when credentials are absent.
        """
        if not self.CRED_PATH.exists():
            _logger.info("No credentials file — API mode unavailable (expected in local-only mode)")
            return False

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request as AuthRequest
        except ImportError:
            _logger.warn("google-auth / google-auth-oauthlib not installed — API unavailable")
            return False

        creds: Credentials | None = None
        if self.TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(self.TOKEN_PATH), self.SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(AuthRequest())
        elif not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(self.CRED_PATH), self.SCOPES)
            creds = flow.run_local_server(port=0)

        # Persist token
        self.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

        try:
            from googleapiclient.discovery import build
            self._api_service = build("drive", "v3", credentials=creds)
        except ImportError:
            _logger.warn("google-api-python-client not installed — API unavailable")
            return False

        _log_access(self._db(), "api_authenticate", detail="success")
        _logger.info("Google Drive API authenticated")
        return True

    @never_crash(fallback=[])
    def api_list_folder(
        self,
        folder_id: str | None = None,
        mime_filter: str = "application/pdf",
    ) -> list[dict]:
        """List files in a Google Drive folder via API."""
        if not self._api_service:
            if not self.api_authenticate():
                return []

        if not self._breaker.allow():
            _logger.warn("Circuit breaker OPEN for Drive API")
            return []

        _rate_limit()
        query_parts = ["trashed = false"]
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if mime_filter:
            query_parts.append(f"mimeType = '{mime_filter}'")
        q = " and ".join(query_parts)

        results: list[dict] = []
        page_token: str | None = None
        try:
            while True:
                _rate_limit()
                resp = (
                    self._api_service.files()
                    .list(
                        q=q,
                        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                        pageSize=100,
                        pageToken=page_token,
                    )
                    .execute()
                )
                for f in resp.get("files", []):
                    results.append({
                        "id": f["id"],
                        "name": f["name"],
                        "mimeType": f.get("mimeType", ""),
                        "size": int(f.get("size", 0)),
                        "modifiedTime": f.get("modifiedTime", ""),
                    })
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
            self._breaker.record_success()
        except Exception as exc:
            self._breaker.record_failure()
            _logger.error(f"api_list_folder failed: {exc}")
        return results

    @never_crash(fallback="")
    def api_download(self, file_id: str, dest_path: str | Path) -> str:
        """Download a file from Google Drive via API.  Returns local path."""
        dest = Path(dest_path)
        if not _validate_path(dest):
            _logger.error(f"Download blocked — path outside safe subtree: {dest}")
            return ""

        if not self._api_service:
            if not self.api_authenticate():
                return ""

        if not self._breaker.allow():
            _logger.warn("Circuit breaker OPEN — skipping download")
            return ""

        _rate_limit()
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            from googleapiclient.http import MediaIoBaseDownload
            import io

            request = self._api_service.files().get_media(fileId=file_id)
            with open(dest, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            self._breaker.record_success()
            _log_access(self._db(), "api_download", file_id=file_id, path=str(dest))
            _logger.info(f"Downloaded {file_id} → {dest}")
            return str(dest)
        except Exception as exc:
            self._breaker.record_failure()
            _logger.error(f"api_download failed for {file_id}: {exc}")
            _log_access(self._db(), "api_download", file_id=file_id,
                         path=str(dest), detail=str(exc)[:500], ok=False)
            return ""

    @never_crash(fallback=[])
    def api_check_new(self, folder_id: str | None = None) -> list[dict]:
        """Return files in Drive folder not yet in drive_files table."""
        remote = self.api_list_folder(folder_id, mime_filter="")
        if not remote:
            return []

        db = self._db(readonly=True)
        rows = db.execute(
            "SELECT drive_id FROM drive_files WHERE source = 'api'"
        ).fetchall()
        known = {r["drive_id"] for r in rows}

        new = [f for f in remote if f["id"] not in known]
        _logger.info(f"api_check_new: {len(new)} new / {len(remote)} total")
        return new

    # ======================================================================
    # Unified interface
    # ======================================================================

    def scan(self) -> list[dict]:
        """Scan for new files using the configured mode."""
        if self.mode == "rclone":
            return self.rclone_check_new()
        if self.mode == "api":
            return self.api_check_new()
        # mode == 'local'
        return self._scan_local()

    def fetch(self, files: list[dict], dest_dir: Path | str | None = None) -> list[str]:
        """Fetch files to local storage.

        * rclone/local — files already local, return paths.
        * api — download each to *dest_dir*.
        """
        dest = Path(dest_dir) if dest_dir else self.sync_dir
        if not _validate_path(dest):
            _logger.error(f"fetch blocked — dest outside safe subtree: {dest}")
            return []

        paths: list[str] = []
        if self.mode in ("rclone", "local"):
            for f in files:
                local = self.sync_dir / f.get("path", f.get("name", ""))
                if local.exists():
                    paths.append(str(local))
        elif self.mode == "api":
            dest.mkdir(parents=True, exist_ok=True)
            for f in files:
                fid = f.get("id", "")
                name = f.get("name", fid)
                p = self.api_download(fid, dest / name)
                if p:
                    paths.append(p)
        return paths

    @never_crash(fallback={})
    def get_status(self) -> dict:
        """Return connector status summary."""
        rclone_ok = bool(shutil.which("rclone"))
        api_ok = self.CRED_PATH.exists()

        synced_count = 0
        last_sync = None
        try:
            db = self._db(readonly=True)
            row = db.execute(
                "SELECT COUNT(*) AS cnt, MAX(synced_at) AS latest FROM drive_files"
            ).fetchone()
            if row:
                synced_count = row["cnt"]
                last_sync = row["latest"]
        except Exception:
            pass

        return {
            "mode": self.mode,
            "rclone_available": rclone_ok,
            "api_available": api_ok,
            "sync_dir": str(self.sync_dir),
            "sync_dir_exists": self.sync_dir.exists(),
            "files_synced": synced_count,
            "last_sync": last_sync,
        }

    # ======================================================================
    # Internal helpers
    # ======================================================================

    def _scan_local(self) -> list[dict]:
        """Scan SYNC_DIR for files not yet in drive_files."""
        if not self.sync_dir.exists():
            _logger.info(f"Sync dir does not exist: {self.sync_dir}")
            return []

        db = self._db(readonly=True)
        rows = db.execute(
            "SELECT local_path FROM drive_files WHERE source = 'local'"
        ).fetchall()
        known = {r["local_path"] for r in rows}

        new: list[dict] = []
        for fp in self.sync_dir.rglob("*"):
            if fp.is_file() and str(fp) not in known:
                new.append({
                    "name": fp.name,
                    "path": str(fp.relative_to(self.sync_dir)),
                    "size": fp.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        fp.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                })
        _logger.info(f"_scan_local: {len(new)} new files in {self.sync_dir}")
        return new

    def _register_local_files(self, directory: Path, source: str = "rclone") -> int:
        """Walk *directory* and upsert files into drive_files."""
        db = self._db()
        count = 0
        now = datetime.now(timezone.utc).isoformat()
        for fp in directory.rglob("*"):
            if not fp.is_file():
                continue
            rel = str(fp.relative_to(directory))
            db.execute(
                "INSERT INTO drive_files "
                "(source, remote_path, local_path, file_name, size_bytes, modified_time, synced_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(remote_path, source) DO UPDATE SET "
                "local_path=excluded.local_path, size_bytes=excluded.size_bytes, "
                "modified_time=excluded.modified_time, synced_at=excluded.synced_at",
                (
                    source, rel, str(fp), fp.name, fp.stat().st_size,
                    datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc).isoformat(),
                    now,
                ),
            )
            count += 1
        db.commit()
        _log_access(db, "register_local_files", path=str(directory),
                     detail=f"source={source} count={count}")
        return count

    @staticmethod
    def _parse_rclone_output(text: str) -> dict:
        """Extract metrics from rclone stats output."""
        metrics: dict = {"files_synced": 0, "bytes_transferred": 0, "errors": []}
        # Transferred: 42 / 42, 100%
        m = re.search(r"Transferred:\s+(\d+)\s*/\s*\d+", text)
        if m:
            metrics["files_synced"] = int(m.group(1))
        # Transferred: 1.234 GiB
        m = re.search(r"Transferred:\s+([\d.]+)\s*(B|KiB|MiB|GiB|TiB)", text)
        if m:
            val = float(m.group(1))
            unit = m.group(2)
            multipliers = {"B": 1, "KiB": 1024, "MiB": 1 << 20,
                           "GiB": 1 << 30, "TiB": 1 << 40}
            metrics["bytes_transferred"] = int(val * multipliers.get(unit, 1))
        # Errors: N
        m = re.search(r"Errors:\s+(\d+)", text)
        if m and int(m.group(1)) > 0:
            metrics["errors"].append(f"{m.group(1)} rclone errors")
        return metrics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gdrive_connector",
        description=(
            "Google Drive connector for LitigationOS — rclone-first, "
            "API-optional, local-fallback."
        ),
    )
    p.add_argument("--mode", choices=["rclone", "api", "local"], default="rclone",
                   help="Connector mode (default: rclone)")
    p.add_argument("--status", action="store_true",
                   help="Show connector status")
    p.add_argument("--list", nargs="?", const="Litigation_Intake", metavar="PATH",
                   help="List remote files (default folder: Litigation_Intake)")
    p.add_argument("--sync", nargs="?", const="Litigation_Intake", metavar="PATH",
                   help="Sync remote folder to local mirror")
    p.add_argument("--check-new", action="store_true",
                   help="Show files not yet ingested")
    p.add_argument("--dry-run", action="store_true",
                   help="Dry-run mode for sync")
    p.add_argument("--db", type=str, default=None,
                   help="Override database path")
    p.add_argument("--sync-dir", type=str, default=None,
                   help="Override local sync directory")
    p.add_argument("--json", action="store_true",
                   help="Output machine-readable JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    connector = GDriveConnector(
        mode=args.mode,
        sync_dir=args.sync_dir,
        db_path=args.db,
    )

    try:
        if args.status:
            data = connector.get_status()
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                for k, v in data.items():
                    print(f"  {k}: {v}")
            return 0

        if args.list is not None:
            if args.mode == "rclone":
                files = connector.rclone_list(args.list)
            elif args.mode == "api":
                files = connector.api_list_folder(folder_id=args.list, mime_filter="")
            else:
                files = connector._scan_local()
            if args.json:
                print(json.dumps(files, indent=2))
            else:
                for f in files:
                    name = f.get("name", f.get("path", "?"))
                    size = f.get("size", 0)
                    print(f"  {name}  ({size:,} bytes)")
                print(f"\n  Total: {len(files)} files")
            return 0

        if args.sync is not None:
            if args.mode != "rclone":
                print("ERROR: --sync only supported in rclone mode", file=sys.stderr)
                return 1
            result = connector.rclone_sync(args.sync, dry_run=args.dry_run)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"  Files synced:      {result['files_synced']}")
                print(f"  Bytes transferred: {result['bytes_transferred']:,}")
                if result["errors"]:
                    print(f"  Errors: {result['errors']}")
            return 0 if not result.get("errors") else 1

        if args.check_new:
            new_files = connector.scan()
            if args.json:
                print(json.dumps(new_files, indent=2))
            else:
                for f in new_files:
                    name = f.get("name", f.get("path", "?"))
                    print(f"  NEW: {name}")
                print(f"\n  {len(new_files)} files not yet ingested")
            return 0

        parser.print_help()
        return 0
    finally:
        connector.close()


if __name__ == "__main__":
    raise SystemExit(main())
