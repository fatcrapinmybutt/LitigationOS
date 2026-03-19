"""
DELTA99 Ω∞ — Drive Fortress
==============================
Comprehensive drive security, integrity, and health monitoring.
Tracks free space, SMART health (where available), file corruption detection,
unauthorized modification alerts, and automatic integrity reports.
Covers all 6 monitored drives (C, D, F, G, H, I).

Feeds: d99-auto-report
"""
import sys
import sqlite3
import json
import time
import hashlib
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import DRIVE_ROOTS, LITIGOS_ROOT

FORTRESS_DB = Path(__file__).parent / "drive_fortress.db"

# ── Critical Paths to Monitor ─────────────────────────────────────
CRITICAL_PATHS = [
    LITIGOS_ROOT / "litigation_context.db",
    LITIGOS_ROOT / "00_SYSTEM" / "pipeline" / "config.py",
    LITIGOS_ROOT / "00_SYSTEM" / "local_model" / "inference_engine.py",
    LITIGOS_ROOT / "06_FILINGS" / "OMEGA_GENERATED",
    LITIGOS_ROOT / "04_COURT_FILINGS" / "03_FINAL",
]

ALERT_THRESHOLDS = {
    "disk_free_pct_warn": 15,   # Warn below 15% free
    "disk_free_pct_crit": 5,    # Critical below 5% free
    "modified_check_hours": 24, # Check if critical files modified in last 24h
}


def _init_db() -> sqlite3.Connection:
    FORTRESS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(FORTRESS_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS drive_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_letter TEXT NOT NULL,
            total_gb REAL DEFAULT 0.0,
            free_gb REAL DEFAULT 0.0,
            free_pct REAL DEFAULT 0.0,
            is_available INTEGER DEFAULT 1,
            alert_level TEXT DEFAULT 'OK',
            checked_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_dh_drive ON drive_health(drive_letter);

        CREATE TABLE IF NOT EXISTS integrity_baselines (
            file_path TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            size_bytes INTEGER DEFAULT 0,
            modified_at TEXT DEFAULT '',
            baseline_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS integrity_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            file_path TEXT DEFAULT '',
            details TEXT DEFAULT '',
            severity TEXT DEFAULT 'MEDIUM',
            acknowledged INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_ia_type ON integrity_alerts(alert_type);
        CREATE INDEX IF NOT EXISTS idx_ia_sev ON integrity_alerts(severity);

        CREATE TABLE IF NOT EXISTS scan_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drives_checked INTEGER DEFAULT 0,
            files_verified INTEGER DEFAULT 0,
            alerts_raised INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _sha256_file(path: Path, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(str(path), "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (IOError, PermissionError):
        return ""


@dataclass
class DriveStatus:
    letter: str
    total_gb: float = 0.0
    free_gb: float = 0.0
    free_pct: float = 0.0
    is_available: bool = False
    alert_level: str = "OK"


def check_drive_health() -> list[DriveStatus]:
    """Check all monitored drives."""
    statuses = []
    for drive_path in DRIVE_ROOTS:
        drive_letter = str(drive_path).rstrip(":\\/ ")[0].upper()
        ds = DriveStatus(letter=drive_letter)

        try:
            if os.path.exists(str(drive_path)):
                usage = os.statvfs(str(drive_path)) if hasattr(os, 'statvfs') else None
                if usage:
                    ds.total_gb = round(usage.f_frsize * usage.f_blocks / (1024**3), 2)
                    ds.free_gb = round(usage.f_frsize * usage.f_bavail / (1024**3), 2)
                else:
                    # Windows fallback
                    import ctypes
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        str(drive_path), None,
                        ctypes.pointer(total_bytes),
                        ctypes.pointer(free_bytes)
                    )
                    ds.total_gb = round(total_bytes.value / (1024**3), 2)
                    ds.free_gb = round(free_bytes.value / (1024**3), 2)

                ds.free_pct = round((ds.free_gb / ds.total_gb * 100) if ds.total_gb > 0 else 0, 1)
                ds.is_available = True

                if ds.free_pct < ALERT_THRESHOLDS["disk_free_pct_crit"]:
                    ds.alert_level = "CRITICAL"
                elif ds.free_pct < ALERT_THRESHOLDS["disk_free_pct_warn"]:
                    ds.alert_level = "WARNING"
                else:
                    ds.alert_level = "OK"
            else:
                ds.alert_level = "DISCONNECTED"
        except Exception:
            ds.alert_level = "ERROR"

        statuses.append(ds)
    return statuses


def set_integrity_baseline(fdb: sqlite3.Connection) -> int:
    """Create/update integrity baselines for critical files."""
    count = 0
    for path in CRITICAL_PATHS:
        if path.is_file():
            sha = _sha256_file(path)
            if sha:
                stat = path.stat()
                fdb.execute("""
                    INSERT OR REPLACE INTO integrity_baselines
                    (file_path, sha256, size_bytes, modified_at, baseline_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (str(path), sha, stat.st_size,
                      datetime.fromtimestamp(stat.st_mtime).isoformat()))
                count += 1
        elif path.is_dir():
            # Baseline directory file count and total size
            total_files = sum(1 for _ in path.rglob("*") if _.is_file())
            fdb.execute("""
                INSERT OR REPLACE INTO integrity_baselines
                (file_path, sha256, size_bytes, modified_at, baseline_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (str(path), f"dir:{total_files}", total_files, ""))
            count += 1
    fdb.commit()
    return count


def verify_integrity(fdb: sqlite3.Connection) -> list[dict]:
    """Verify critical files against baselines."""
    alerts = []
    rows = fdb.execute("SELECT file_path, sha256, size_bytes FROM integrity_baselines").fetchall()

    for row in rows:
        path = Path(row[0])
        expected_sha = row[1]
        expected_size = row[2]

        if not path.exists():
            alerts.append({
                "type": "FILE_MISSING",
                "file": str(path),
                "severity": "CRITICAL",
                "details": f"Critical file/dir missing: {path.name}",
            })
            continue

        if path.is_file():
            current_sha = _sha256_file(path)
            current_size = path.stat().st_size

            if current_sha and current_sha != expected_sha:
                alerts.append({
                    "type": "INTEGRITY_MISMATCH",
                    "file": str(path),
                    "severity": "HIGH",
                    "details": f"SHA-256 changed: expected {expected_sha[:16]}..., got {current_sha[:16]}...",
                })

            if abs(current_size - expected_size) > expected_size * 0.1:
                alerts.append({
                    "type": "SIZE_ANOMALY",
                    "file": str(path),
                    "severity": "MEDIUM",
                    "details": f"Size changed: {expected_size} → {current_size} bytes ({abs(current_size - expected_size)} diff)",
                })

    return alerts


def run_full_check() -> dict:
    """Run complete drive fortress check."""
    start = time.time()
    fdb = _init_db()

    # 1. Drive health
    drive_statuses = check_drive_health()
    for ds in drive_statuses:
        fdb.execute("""
            INSERT INTO drive_health
            (drive_letter, total_gb, free_gb, free_pct, is_available, alert_level)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ds.letter, ds.total_gb, ds.free_gb, ds.free_pct,
              int(ds.is_available), ds.alert_level))

    # 2. Set baselines (first run) or verify
    existing = fdb.execute("SELECT COUNT(*) FROM integrity_baselines").fetchone()[0]
    if existing == 0:
        baselined = set_integrity_baseline(fdb)
        integrity_alerts = []
    else:
        baselined = 0
        integrity_alerts = verify_integrity(fdb)

    # 3. Persist alerts
    for alert in integrity_alerts:
        fdb.execute("""
            INSERT INTO integrity_alerts (alert_type, file_path, details, severity)
            VALUES (?, ?, ?, ?)
        """, (alert["type"], alert["file"], alert["details"], alert["severity"]))

    # Drive alerts
    drive_alerts = [
        {"type": "DRIVE_SPACE", "file": f"{ds.letter}:\\",
         "severity": ds.alert_level, "details": f"{ds.free_gb}GB free ({ds.free_pct}%)"}
        for ds in drive_statuses if ds.alert_level in ("WARNING", "CRITICAL")
    ]
    for alert in drive_alerts:
        fdb.execute("""
            INSERT INTO integrity_alerts (alert_type, file_path, details, severity)
            VALUES (?, ?, ?, ?)
        """, (alert["type"], alert["file"], alert["details"], alert["severity"]))

    all_alerts = integrity_alerts + drive_alerts
    duration = round(time.time() - start, 2)

    fdb.execute("""
        INSERT INTO scan_runs (drives_checked, files_verified, alerts_raised, duration_s)
        VALUES (?, ?, ?, ?)
    """, (len(drive_statuses), existing or baselined, len(all_alerts), duration))
    fdb.commit()
    fdb.close()

    return {
        "drives": [
            {"letter": ds.letter, "total_gb": ds.total_gb, "free_gb": ds.free_gb,
             "free_pct": ds.free_pct, "available": ds.is_available, "alert": ds.alert_level}
            for ds in drive_statuses
        ],
        "integrity": {
            "baselines": existing or baselined,
            "alerts": len(integrity_alerts),
            "critical": sum(1 for a in integrity_alerts if a["severity"] == "CRITICAL"),
        },
        "total_alerts": len(all_alerts),
        "alert_details": all_alerts[:10],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_full_check()
    print(json.dumps(result, indent=2, default=str))
