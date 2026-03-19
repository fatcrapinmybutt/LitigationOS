import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""
migrate_drive_pipeline.py — Create drive-pipeline tables in litigation_context.db.

Tables created:
  1. drive_files      — Tracks each ingested file with SHA-256 integrity
  2. file_atoms       — Extracted atomic content per file
  3. provenance_refs  — Audit trail for facts
  4. ingest_logs      — Pipeline run tracking

Usage:
    python migrate_drive_pipeline.py [--help]
"""

import argparse
import sqlite3
import os
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "litigation_context.db",
)

TABLES = ["drive_files", "file_atoms", "provenance_refs", "ingest_logs"]

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------
DDL_DRIVE_FILES = """
CREATE TABLE IF NOT EXISTS drive_files (
    file_id TEXT PRIMARY KEY,
    full_path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    extension TEXT,
    mime_type TEXT,
    sha256 TEXT NOT NULL,
    file_size INTEGER,
    file_modified TEXT,
    source TEXT DEFAULT 'local',
    gdrive_id TEXT,
    lane TEXT,
    meek_signal TEXT,
    relevance_score REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    page_count INTEGER,
    extracted_text_length INTEGER,
    atom_count INTEGER DEFAULT 0,
    ingest_run_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_df_sha256 ON drive_files(sha256);
CREATE INDEX IF NOT EXISTS idx_df_lane ON drive_files(lane);
CREATE INDEX IF NOT EXISTS idx_df_status ON drive_files(status);
CREATE INDEX IF NOT EXISTS idx_df_source ON drive_files(source);
CREATE INDEX IF NOT EXISTS idx_df_run ON drive_files(ingest_run_id);
"""

DDL_FILE_ATOMS = """
CREATE TABLE IF NOT EXISTS file_atoms (
    atom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL REFERENCES drive_files(file_id),
    atom_type TEXT NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    paragraph_index INTEGER,
    char_offset INTEGER,
    char_length INTEGER,
    lane TEXT,
    meek_signal TEXT,
    posture TEXT,
    confidence REAL DEFAULT 1.0,
    metadata TEXT,
    linked_table TEXT,
    linked_row_id TEXT,
    ingest_run_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fa_file ON file_atoms(file_id);
CREATE INDEX IF NOT EXISTS idx_fa_type ON file_atoms(atom_type);
CREATE INDEX IF NOT EXISTS idx_fa_lane ON file_atoms(lane);
CREATE INDEX IF NOT EXISTS idx_fa_linked ON file_atoms(linked_table, linked_row_id);
"""

DDL_PROVENANCE_REFS = """
CREATE TABLE IF NOT EXISTS provenance_refs (
    ref_id INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id INTEGER REFERENCES file_atoms(atom_id),
    source_table TEXT NOT NULL,
    source_row_id TEXT NOT NULL,
    source_field TEXT,
    source_offset INTEGER,
    file_id TEXT REFERENCES drive_files(file_id),
    page_number INTEGER,
    quote_locked INTEGER DEFAULT 1,
    posture TEXT,
    truth_tag TEXT,
    verification_status TEXT DEFAULT 'unverified',
    verified_by TEXT,
    verified_at TEXT,
    ingest_run_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pr_source ON provenance_refs(source_table, source_row_id);
CREATE INDEX IF NOT EXISTS idx_pr_atom ON provenance_refs(atom_id);
CREATE INDEX IF NOT EXISTS idx_pr_file ON provenance_refs(file_id);
"""

DDL_INGEST_LOGS = """
CREATE TABLE IF NOT EXISTS ingest_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    step TEXT,
    status TEXT NOT NULL DEFAULT 'started',
    files_processed INTEGER DEFAULT 0,
    atoms_created INTEGER DEFAULT 0,
    quotes_added INTEGER DEFAULT 0,
    gaps_opened INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    error_detail TEXT,
    duration_seconds REAL,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_il_run ON ingest_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_il_phase ON ingest_logs(phase);
CREATE INDEX IF NOT EXISTS idx_il_status ON ingest_logs(status);
"""

DDL_MAP = {
    "drive_files": DDL_DRIVE_FILES,
    "file_atoms": DDL_FILE_ATOMS,
    "provenance_refs": DDL_PROVENANCE_REFS,
    "ingest_logs": DDL_INGEST_LOGS,
}

# ---------------------------------------------------------------------------
# schema_reference registration data
# (table_name, column_name, column_type, common_mistake, correct_usage)
# ---------------------------------------------------------------------------
SCHEMA_REF_ROWS = [
    # drive_files
    ("drive_files", "file_id", "TEXT", "id", "WHERE file_id = ?"),
    ("drive_files", "full_path", "TEXT", "path", "WHERE full_path = ?"),
    ("drive_files", "sha256", "TEXT", "hash", "WHERE sha256 = ?"),
    ("drive_files", "file_modified", "TEXT", "modified_date", "ORDER BY file_modified"),
    ("drive_files", "meek_signal", "TEXT", "meek", "WHERE meek_signal = 'MEEK1'"),
    ("drive_files", "relevance_score", "REAL", "score", "ORDER BY relevance_score DESC"),
    ("drive_files", "status", "TEXT", "state", "WHERE status = 'ingested'"),
    ("drive_files", "ingest_run_id", "TEXT", "run_id", "WHERE ingest_run_id = ?"),
    ("drive_files", "atom_count", "INTEGER", "atoms", "SUM(atom_count)"),
    # file_atoms
    ("file_atoms", "atom_id", "INTEGER", "id", "WHERE atom_id = ?"),
    ("file_atoms", "file_id", "TEXT", "doc_id", "WHERE file_id = ?"),
    ("file_atoms", "atom_type", "TEXT", "type", "WHERE atom_type = 'quote'"),
    ("file_atoms", "content", "TEXT", "text", "WHERE content LIKE ?"),
    ("file_atoms", "posture", "TEXT", "tag", "WHERE posture = 'EVIDENCE_FACT'"),
    ("file_atoms", "linked_table", "TEXT", "link_table", "WHERE linked_table = 'evidence_quotes'"),
    ("file_atoms", "linked_row_id", "TEXT", "link_id", "WHERE linked_row_id = ?"),
    # provenance_refs
    ("provenance_refs", "ref_id", "INTEGER", "id", "WHERE ref_id = ?"),
    ("provenance_refs", "atom_id", "INTEGER", "atom", "WHERE atom_id = ?"),
    ("provenance_refs", "source_table", "TEXT", "table", "WHERE source_table = ?"),
    ("provenance_refs", "source_row_id", "TEXT", "row_id", "WHERE source_row_id = ?"),
    ("provenance_refs", "quote_locked", "INTEGER", "locked", "WHERE quote_locked = 1"),
    ("provenance_refs", "truth_tag", "TEXT", "tag", "WHERE truth_tag = 'PROVEN'"),
    ("provenance_refs", "verification_status", "TEXT", "status", "WHERE verification_status = 'verified'"),
    # ingest_logs
    ("ingest_logs", "log_id", "INTEGER", "id", "WHERE log_id = ?"),
    ("ingest_logs", "run_id", "TEXT", "run", "WHERE run_id = ?"),
    ("ingest_logs", "phase", "TEXT", "step", "WHERE phase = 'extract'"),
    ("ingest_logs", "status", "TEXT", "state", "WHERE status = 'success'"),
    ("ingest_logs", "files_processed", "INTEGER", "file_count", "SUM(files_processed)"),
    ("ingest_logs", "atoms_created", "INTEGER", "atom_count", "SUM(atoms_created)"),
    ("ingest_logs", "duration_seconds", "REAL", "duration", "SUM(duration_seconds)"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    """Open a WAL-mode connection with safe pragmas."""
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=120000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _row_count(conn: sqlite3.Connection, name: str) -> int:
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()
        return row[0] if row else 0
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# Core migration
# ---------------------------------------------------------------------------

def run_migration(db_path: str | None = None) -> dict:
    """Create the 4 drive-pipeline tables and register in schema_reference.

    Returns a dict with 'tables' (name → row_count) and 'registered' count.
    """
    db_path = db_path or DB_PATH

    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = _connect(db_path)
    results: dict = {"tables": {}, "registered": 0, "errors": []}

    try:
        # --- Create tables + indexes ---
        for table_name, ddl in DDL_MAP.items():
            already = _table_exists(conn, table_name)
            try:
                conn.executescript(ddl)
                action = "verified" if already else "created"
                count = _row_count(conn, table_name)
                results["tables"][table_name] = {"action": action, "rows": count}
                print(f"  [OK] {table_name:<20s} {action} ({count} rows)")
            except Exception as exc:
                msg = f"{table_name}: {exc}"
                results["errors"].append(msg)
                print(f"  [ERR] {msg}")

        # --- Register in schema_reference ---
        registered = 0
        for row in SCHEMA_REF_ROWS:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO schema_reference "
                    "(table_name, column_name, column_type, common_mistake, correct_usage) "
                    "VALUES (?, ?, ?, ?, ?)",
                    row,
                )
                registered += 1
            except Exception as exc:
                msg = f"schema_reference({row[0]}.{row[1]}): {exc}"
                results["errors"].append(msg)

        conn.commit()
        results["registered"] = registered
        print(f"\n  schema_reference: {registered} column entries registered")

    except Exception as exc:
        results["errors"].append(str(exc))
        print(f"\n  [FATAL] {exc}")
    finally:
        conn.close()

    return results


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create drive-pipeline tables in litigation_context.db"
    )
    parser.add_argument(
        "--db",
        default=DB_PATH,
        help=f"Path to SQLite database (default: {DB_PATH})",
    )
    parser.add_argument("--help-tables", action="store_true", help="List tables that will be created")
    args = parser.parse_args()

    if args.help_tables:
        for t in TABLES:
            print(f"  - {t}")
        return 0

    print(f"migrate_drive_pipeline  db={args.db}")
    print("-" * 60)

    t0 = time.time()
    try:
        results = run_migration(args.db)
    except FileNotFoundError as exc:
        print(f"[FATAL] {exc}")
        return 1
    except Exception as exc:
        print(f"[FATAL] Unexpected error: {exc}")
        return 1

    elapsed = time.time() - t0
    print("-" * 60)
    print(f"Done in {elapsed:.2f}s  tables={len(results['tables'])}  errors={len(results['errors'])}")

    return 1 if results["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
