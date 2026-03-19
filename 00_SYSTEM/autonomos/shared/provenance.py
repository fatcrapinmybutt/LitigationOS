"""
AUTONOMOS Provenance & Manifest Tracker
========================================
Tracks the complete chain of custody for every file:
  original_location → detection → classification → destination → analysis → DB rows

Enabler 1.2: Manifest & Provenance Tracking
"""
import sqlite3
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional

from autonomos_config import PROVENANCE_DB


@dataclass
class ProvenanceRecord:
    """Complete provenance chain for a single file."""
    file_id: str                         # SHA-256 of original file
    original_path: str                   # Where the file was first detected
    original_drive: str                  # Drive letter (C, D, F, G, H, I)
    sha256: str                          # SHA-256 hash
    file_size: int = 0                   # Bytes
    detected_at: str = ""                # ISO timestamp
    classified_as: str = ""              # Document type
    lane: str = ""                       # A-F lane assignment
    confidence: float = 0.0             # Classification confidence (0-1)
    dest_path: str = ""                  # Where the file was moved to
    moved_at: str = ""                   # ISO timestamp of move
    analyzed_at: str = ""                # ISO timestamp of analysis
    analysis_phases: str = ""            # Comma-separated phase IDs that ran
    db_rows_created: int = 0            # Total DB rows created from this file
    status: str = "detected"            # detected → classified → moved → analyzed → indexed
    error: str = ""                      # Error message if failed


def _init_db(db_path: Path = PROVENANCE_DB) -> sqlite3.Connection:
    """Initialize provenance database with schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS provenance (
            file_id TEXT PRIMARY KEY,
            original_path TEXT NOT NULL,
            original_drive TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            detected_at TEXT NOT NULL,
            classified_as TEXT DEFAULT '',
            lane TEXT DEFAULT '',
            confidence REAL DEFAULT 0.0,
            dest_path TEXT DEFAULT '',
            moved_at TEXT DEFAULT '',
            analyzed_at TEXT DEFAULT '',
            analysis_phases TEXT DEFAULT '',
            db_rows_created INTEGER DEFAULT 0,
            status TEXT DEFAULT 'detected',
            error TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_prov_status ON provenance(status);
        CREATE INDEX IF NOT EXISTS idx_prov_lane ON provenance(lane);
        CREATE INDEX IF NOT EXISTS idx_prov_drive ON provenance(original_drive);
        CREATE INDEX IF NOT EXISTS idx_prov_sha256 ON provenance(sha256);
        CREATE INDEX IF NOT EXISTS idx_prov_detected ON provenance(detected_at);

        CREATE TABLE IF NOT EXISTS provenance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT DEFAULT '',
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (file_id) REFERENCES provenance(file_id)
        );

        CREATE TABLE IF NOT EXISTS manifest (
            sha256 TEXT PRIMARY KEY,
            file_count INTEGER DEFAULT 1,
            first_seen TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now')),
            canonical_path TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


class ProvenanceTracker:
    """Manages file provenance records and manifests."""

    def __init__(self, db_path: Path = PROVENANCE_DB):
        self._conn = _init_db(db_path)

    def close(self):
        self._conn.close()

    def record_detection(self, path: str, drive: str, sha256: str, file_size: int = 0) -> str:
        """Record a newly detected file. Returns file_id."""
        file_id = sha256  # Use hash as ID for dedup
        now = datetime.now().isoformat()
        try:
            self._conn.execute("""
                INSERT OR IGNORE INTO provenance 
                (file_id, original_path, original_drive, sha256, file_size, detected_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'detected')
            """, (file_id, path, drive, sha256, file_size, now))
            self._conn.execute("""
                INSERT OR IGNORE INTO manifest (sha256, canonical_path)
                VALUES (?, ?)
            """, (sha256, path))
            self._log(file_id, "DETECTED", f"drive={drive} path={path}")
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass  # Already tracked
        return file_id

    def record_classification(self, file_id: str, doc_type: str, lane: str, confidence: float):
        """Record classification results."""
        self._conn.execute("""
            UPDATE provenance SET classified_as=?, lane=?, confidence=?, 
            status='classified', updated_at=datetime('now')
            WHERE file_id=?
        """, (doc_type, lane, confidence, file_id))
        self._log(file_id, "CLASSIFIED", f"type={doc_type} lane={lane} conf={confidence:.2f}")
        self._conn.commit()

    def record_move(self, file_id: str, dest_path: str):
        """Record file move to organized location."""
        now = datetime.now().isoformat()
        self._conn.execute("""
            UPDATE provenance SET dest_path=?, moved_at=?, status='moved',
            updated_at=datetime('now')
            WHERE file_id=?
        """, (dest_path, now, file_id))
        self._log(file_id, "MOVED", f"dest={dest_path}")
        self._conn.commit()

    def record_analysis(self, file_id: str, phases: list[str], db_rows: int):
        """Record analysis completion."""
        now = datetime.now().isoformat()
        phases_str = ",".join(phases)
        self._conn.execute("""
            UPDATE provenance SET analyzed_at=?, analysis_phases=?, db_rows_created=?,
            status='indexed', updated_at=datetime('now')
            WHERE file_id=?
        """, (now, phases_str, db_rows, file_id))
        self._log(file_id, "ANALYZED", f"phases={phases_str} rows={db_rows}")
        self._conn.commit()

    def record_error(self, file_id: str, error: str):
        """Record an error during processing."""
        self._conn.execute("""
            UPDATE provenance SET error=?, updated_at=datetime('now')
            WHERE file_id=?
        """, (error, file_id))
        self._log(file_id, "ERROR", error)
        self._conn.commit()

    def get_record(self, file_id: str) -> Optional[ProvenanceRecord]:
        """Get provenance record by file_id."""
        row = self._conn.execute(
            "SELECT * FROM provenance WHERE file_id=?", (file_id,)
        ).fetchone()
        if not row:
            return None
        cols = [d[0] for d in self._conn.execute("SELECT * FROM provenance LIMIT 0").description]
        d = dict(zip(cols, row))
        return ProvenanceRecord(**{k: d[k] for k in ProvenanceRecord.__dataclass_fields__ if k in d})

    def is_known(self, sha256: str) -> bool:
        """Check if a file hash is already tracked."""
        row = self._conn.execute(
            "SELECT 1 FROM provenance WHERE sha256=?", (sha256,)
        ).fetchone()
        return row is not None

    def stats(self) -> dict:
        """Get provenance statistics."""
        result = {}
        for status in ("detected", "classified", "moved", "analyzed", "indexed"):
            cnt = self._conn.execute(
                "SELECT COUNT(*) FROM provenance WHERE status=?", (status,)
            ).fetchone()[0]
            result[status] = cnt
        result["total"] = sum(result.values())
        result["errors"] = self._conn.execute(
            "SELECT COUNT(*) FROM provenance WHERE error != ''"
        ).fetchone()[0]
        return result

    def get_unprocessed(self, status: str = "detected", limit: int = 100) -> list[dict]:
        """Get files at a given status for processing."""
        rows = self._conn.execute("""
            SELECT file_id, original_path, original_drive, sha256, file_size
            FROM provenance WHERE status=? ORDER BY detected_at LIMIT ?
        """, (status, limit)).fetchall()
        return [{"file_id": r[0], "path": r[1], "drive": r[2], "sha256": r[3], "size": r[4]} for r in rows]

    def export_manifest(self, output_path: Path) -> int:
        """Export SHA-256 manifest to JSON file."""
        rows = self._conn.execute("""
            SELECT sha256, original_path, dest_path, lane, status, detected_at
            FROM provenance ORDER BY detected_at
        """).fetchall()
        records = [
            {"sha256": r[0], "original": r[1], "dest": r[2], "lane": r[3], "status": r[4], "detected": r[5]}
            for r in rows
        ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        return len(records)

    def _log(self, file_id: str, action: str, details: str = ""):
        """Append to provenance audit log."""
        self._conn.execute(
            "INSERT INTO provenance_log (file_id, action, details) VALUES (?, ?, ?)",
            (file_id, action, details)
        )
