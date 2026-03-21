"""Automatic database schema migration engine for LitigationOS.

Manages versioned schema changes with full rollback support, checksum
verification, dry-run mode, and automatic pre-migration backups.

Usage::

    from litigationos.db.schema_migrations import MigrationEngine

    engine = MigrationEngine("path/to/litigationos.db")
    result = engine.auto_migrate()          # backup → detect → apply → validate
    print(result["applied"])                # list of applied migrations

    engine.migrate_down(target=5)           # rollback to version 5
    engine.get_migration_history()          # full audit trail
    engine.validate_schema()                # verify schema integrity

Unlike :class:`MigrationManager` (which copies data between databases),
this engine evolves the *schema* of a single database across app versions.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Migration dataclass
# ---------------------------------------------------------------------------


@dataclass
class Migration:
    """A single versioned schema change.

    Attributes
    ----------
    id : int
        Monotonically increasing migration number (1-based).
    description : str
        Human-readable summary of what this migration does.
    up_sql : str
        SQL executed when migrating *up* (applying).
    down_sql : str
        SQL executed when migrating *down* (rolling back).
        May be empty if rollback is not supported.
    applied_at : str or None
        ISO-8601 timestamp when this migration was applied (``None`` if pending).
    """

    id: int
    description: str
    up_sql: str
    down_sql: str = ""
    applied_at: Optional[str] = None

    @property
    def checksum(self) -> str:
        """SHA-256 digest of the up-SQL — used for tamper detection."""
        return hashlib.sha256(self.up_sql.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Migration registry — initial schema bootstrap
# ---------------------------------------------------------------------------

MIGRATIONS: list[Migration] = [
    # ------------------------------------------------------------------
    # 1 — Bootstrap: the schema_migrations tracking table itself
    # ------------------------------------------------------------------
    Migration(
        id=1,
        description="Create schema_migrations table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS schema_migrations (
    id          INTEGER PRIMARY KEY,
    description TEXT    NOT NULL,
    applied_at  TEXT    DEFAULT (datetime('now')),
    checksum    TEXT
);
""",
        down_sql="DROP TABLE IF EXISTS schema_migrations;",
    ),
    # ------------------------------------------------------------------
    # 2 — Bates stamp assignments
    # ------------------------------------------------------------------
    Migration(
        id=2,
        description="Create bates_assignments table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS bates_assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    prefix      TEXT    NOT NULL DEFAULT 'EXHIBIT',
    number      INTEGER NOT NULL,
    suffix      TEXT    DEFAULT '',
    full_label  TEXT    GENERATED ALWAYS AS (prefix || '-' || printf('%04d', number) || suffix) STORED,
    assigned_at TEXT    DEFAULT (datetime('now')),
    UNIQUE(prefix, number)
);
CREATE INDEX IF NOT EXISTS idx_bates_evidence ON bates_assignments(evidence_id);
""",
        down_sql="DROP TABLE IF EXISTS bates_assignments;",
    ),
    # ------------------------------------------------------------------
    # 3 — Exhibit assignments
    # ------------------------------------------------------------------
    Migration(
        id=3,
        description="Create exhibit_assignments table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS exhibit_assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    case_id     INTEGER,
    exhibit_num TEXT    NOT NULL,
    tab_label   TEXT    DEFAULT '',
    description TEXT    DEFAULT '',
    page_count  INTEGER DEFAULT 0,
    assigned_at TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_exhibit_case ON exhibit_assignments(case_id);
CREATE INDEX IF NOT EXISTS idx_exhibit_evidence ON exhibit_assignments(evidence_id);
""",
        down_sql="DROP TABLE IF EXISTS exhibit_assignments;",
    ),
    # ------------------------------------------------------------------
    # 4 — Evidence ↔ filing linkage
    # ------------------------------------------------------------------
    Migration(
        id=4,
        description="Create evidence_filing_map table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS evidence_filing_map (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    filing_id   INTEGER NOT NULL,
    role        TEXT    DEFAULT 'exhibit',
    page_ref    TEXT    DEFAULT '',
    linked_at   TEXT    DEFAULT (datetime('now')),
    UNIQUE(evidence_id, filing_id)
);
CREATE INDEX IF NOT EXISTS idx_efm_filing ON evidence_filing_map(filing_id);
""",
        down_sql="DROP TABLE IF EXISTS evidence_filing_map;",
    ),
    # ------------------------------------------------------------------
    # 5 — Pipeline run tracking
    # ------------------------------------------------------------------
    Migration(
        id=5,
        description="Create pipeline_runs table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name     TEXT    NOT NULL,
    started_at   TEXT    DEFAULT (datetime('now')),
    finished_at  TEXT,
    status       TEXT    DEFAULT 'running'
                         CHECK(status IN ('running','success','failed','cancelled')),
    phase_start  TEXT,
    phase_end    TEXT,
    items_total  INTEGER DEFAULT 0,
    items_ok     INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_log    TEXT    DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_runs(status);
""",
        down_sql="DROP TABLE IF EXISTS pipeline_runs;",
    ),
    # ------------------------------------------------------------------
    # 6 — Notification history
    # ------------------------------------------------------------------
    Migration(
        id=6,
        description="Create notification_history table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS notification_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    body       TEXT    DEFAULT '',
    severity   TEXT    DEFAULT 'info'
                       CHECK(severity IN ('info','warning','error','success')),
    source     TEXT    DEFAULT '',
    read       INTEGER DEFAULT 0,
    created_at TEXT    DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notif_severity ON notification_history(severity);
CREATE INDEX IF NOT EXISTS idx_notif_read ON notification_history(read);
""",
        down_sql="DROP TABLE IF EXISTS notification_history;",
    ),
    # ------------------------------------------------------------------
    # 7 — User preferences (key-value, typed)
    # ------------------------------------------------------------------
    Migration(
        id=7,
        description="Create user_preferences table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS user_preferences (
    key         TEXT PRIMARY KEY,
    value       TEXT    NOT NULL DEFAULT '',
    value_type  TEXT    DEFAULT 'str'
                        CHECK(value_type IN ('str','int','float','bool','json')),
    category    TEXT    DEFAULT 'general',
    description TEXT    DEFAULT '',
    updated_at  TEXT    DEFAULT (datetime('now'))
);
""",
        down_sql="DROP TABLE IF EXISTS user_preferences;",
    ),
    # ------------------------------------------------------------------
    # 8 — Full-text search on evidence_quotes
    # ------------------------------------------------------------------
    Migration(
        id=8,
        description="Add FTS5 index on evidence_quotes",
        up_sql="""\
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_quotes_fts USING fts5(
    quote_text,
    source_document,
    category,
    content='evidence_quotes',
    content_rowid='rowid',
    tokenize='porter unicode61'
);
""",
        down_sql="DROP TABLE IF EXISTS evidence_quotes_fts;",
    ),
    # ------------------------------------------------------------------
    # 9 — Filing packages (assembled court bundles)
    # ------------------------------------------------------------------
    Migration(
        id=9,
        description="Create filing_packages table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS filing_packages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id       INTEGER,
    package_name  TEXT    NOT NULL,
    filing_type   TEXT    DEFAULT 'motion',
    lane          TEXT    DEFAULT 'A',
    status        TEXT    DEFAULT 'draft'
                          CHECK(status IN ('draft','review','ready','filed','rejected')),
    document_ids  TEXT    DEFAULT '[]',
    evidence_ids  TEXT    DEFAULT '[]',
    form_ids      TEXT    DEFAULT '[]',
    notes         TEXT    DEFAULT '',
    created_at    TEXT    DEFAULT (datetime('now')),
    filed_at      TEXT
);
CREATE INDEX IF NOT EXISTS idx_fp_case ON filing_packages(case_id);
CREATE INDEX IF NOT EXISTS idx_fp_status ON filing_packages(status);
CREATE INDEX IF NOT EXISTS idx_fp_lane ON filing_packages(lane);
""",
        down_sql="DROP TABLE IF EXISTS filing_packages;",
    ),
    # ------------------------------------------------------------------
    # 10 — Audit log (append-only, immutable)
    # ------------------------------------------------------------------
    Migration(
        id=10,
        description="Create audit_log table",
        up_sql="""\
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    DEFAULT (datetime('now')),
    actor       TEXT    DEFAULT 'system',
    action      TEXT    NOT NULL,
    entity_type TEXT    DEFAULT '',
    entity_id   TEXT    DEFAULT '',
    old_value   TEXT    DEFAULT '',
    new_value   TEXT    DEFAULT '',
    metadata    TEXT    DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
""",
        down_sql="DROP TABLE IF EXISTS audit_log;",
    ),
]


# ---------------------------------------------------------------------------
# Migration engine
# ---------------------------------------------------------------------------


class MigrationEngine:
    """Automatic schema migration engine for a single SQLite database.

    Tracks applied migrations in a ``schema_migrations`` table, supports
    forward migration, rollback, dry-run, checksum verification, and
    pre-migration backup.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.
    migrations : list[Migration] or None
        Custom migration list.  Defaults to the built-in :data:`MIGRATIONS`.
    """

    def __init__(
        self,
        db_path: str,
        migrations: list[Migration] | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self._migrations = sorted(
            migrations or MIGRATIONS, key=lambda m: m.id
        )
        self._ensure_tracking_table()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with LitigationOS-standard PRAGMAs."""
        conn = sqlite3.connect(str(self.db_path), timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tracking_table(self) -> None:
        """Create the ``schema_migrations`` table if it doesn't exist."""
        conn = self._connect()
        try:
            conn.execute("""\
CREATE TABLE IF NOT EXISTS schema_migrations (
    id          INTEGER PRIMARY KEY,
    description TEXT    NOT NULL,
    applied_at  TEXT    DEFAULT (datetime('now')),
    checksum    TEXT
);
""")
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_version(self) -> int:
        """Return the highest applied migration number, or 0 if none."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT MAX(id) AS ver FROM schema_migrations"
            ).fetchone()
            return row["ver"] if row and row["ver"] is not None else 0
        finally:
            conn.close()

    def get_pending_migrations(self) -> list[dict]:
        """Return metadata for every migration not yet applied.

        Returns
        -------
        list[dict]
            Each dict has keys ``id``, ``description``, ``checksum``.
        """
        current = self.get_current_version()
        return [
            {
                "id": m.id,
                "description": m.description,
                "checksum": m.checksum,
            }
            for m in self._migrations
            if m.id > current
        ]

    def apply_migration(self, migration_id: int) -> bool:
        """Apply a single migration inside a SAVEPOINT transaction.

        Parameters
        ----------
        migration_id : int
            The ID of the migration to apply.

        Returns
        -------
        bool
            ``True`` on success, ``False`` on failure (logged, not raised).
        """
        migration = self._find_migration(migration_id)
        if migration is None:
            logger.error("Migration %d not found in registry", migration_id)
            return False

        conn = self._connect()
        try:
            sp_name = f"migration_{migration_id}"
            conn.execute(f"SAVEPOINT {sp_name}")
            try:
                conn.executescript(migration.up_sql)
                conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations "
                    "(id, description, applied_at, checksum) "
                    "VALUES (?, ?, datetime('now'), ?)",
                    (migration.id, migration.description, migration.checksum),
                )
                conn.execute(f"RELEASE {sp_name}")
                conn.commit()
                logger.info(
                    "Applied migration %d: %s",
                    migration.id,
                    migration.description,
                )
                return True
            except Exception:
                conn.execute(f"ROLLBACK TO {sp_name}")
                conn.execute(f"RELEASE {sp_name}")
                logger.exception(
                    "Failed to apply migration %d: %s",
                    migration.id,
                    migration.description,
                )
                return False
        finally:
            conn.close()

    def migrate_up(
        self,
        target: int | None = None,
        *,
        dry_run: bool = False,
    ) -> list[dict]:
        """Apply all pending migrations, optionally up to *target*.

        Parameters
        ----------
        target : int or None
            Stop after applying this migration ID.  ``None`` = apply all.
        dry_run : bool
            If ``True``, return what *would* be applied without touching the DB.

        Returns
        -------
        list[dict]
            Applied (or would-be-applied) migration metadata.
        """
        pending = self.get_pending_migrations()
        if target is not None:
            pending = [m for m in pending if m["id"] <= target]

        if dry_run:
            logger.info(
                "Dry-run: %d migration(s) would be applied", len(pending)
            )
            return pending

        applied: list[dict] = []
        for meta in pending:
            ok = self.apply_migration(meta["id"])
            if ok:
                applied.append(meta)
            else:
                logger.error(
                    "Stopping migration at %d due to failure", meta["id"]
                )
                break
        return applied

    def migrate_down(self, target: int) -> list[dict]:
        """Rollback migrations down to (but not including) *target*.

        Migrations are rolled back in reverse order.  Only migrations whose
        ``down_sql`` is non-empty can be rolled back.

        Parameters
        ----------
        target : int
            The version to roll back to.  Migration *target* stays applied.

        Returns
        -------
        list[dict]
            Metadata for each successfully rolled-back migration.
        """
        current = self.get_current_version()
        if target >= current:
            logger.info(
                "Nothing to rollback: target=%d, current=%d", target, current
            )
            return []

        # Collect migrations to rollback in reverse order
        to_rollback = sorted(
            [m for m in self._migrations if target < m.id <= current],
            key=lambda m: m.id,
            reverse=True,
        )

        rolled_back: list[dict] = []
        for migration in to_rollback:
            if not migration.down_sql.strip():
                logger.warning(
                    "Migration %d has no rollback SQL — stopping",
                    migration.id,
                )
                break
            ok = self._rollback_one(migration)
            if ok:
                rolled_back.append(
                    {
                        "id": migration.id,
                        "description": migration.description,
                        "rolled_back_at": _utcnow_iso(),
                    }
                )
            else:
                logger.error(
                    "Stopping rollback at migration %d due to failure",
                    migration.id,
                )
                break

        return rolled_back

    def get_migration_history(self) -> list[dict]:
        """Return every row from ``schema_migrations`` ordered by ID.

        Returns
        -------
        list[dict]
            Keys: ``id``, ``description``, ``applied_at``, ``checksum``.
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, description, applied_at, checksum "
                "FROM schema_migrations ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def validate_schema(self) -> dict:
        """Validate that every applied migration's checksum still matches.

        Also detects orphan rows (in the DB but not in the registry) and
        missing rows (in the registry but not in the DB).

        Returns
        -------
        dict
            ``valid`` (bool), ``current_version``, ``errors`` (list[str]),
            ``warnings`` (list[str]), ``tables_found`` (int).
        """
        errors: list[str] = []
        warnings: list[str] = []
        history = {r["id"]: r for r in self.get_migration_history()}
        registry = {m.id: m for m in self._migrations}

        # Checksum verification
        for mid, row in history.items():
            if mid not in registry:
                warnings.append(
                    f"Migration {mid} exists in DB but not in registry "
                    f"(orphan row)"
                )
                continue
            expected = registry[mid].checksum
            actual = row["checksum"]
            if actual and actual != expected:
                errors.append(
                    f"Migration {mid} checksum mismatch — "
                    f"expected {expected[:12]}…, got {actual[:12]}…"
                )

        # Missing from DB
        current = self.get_current_version()
        for mid, migration in registry.items():
            if mid <= current and mid not in history:
                warnings.append(
                    f"Migration {mid} ({migration.description}) is within "
                    f"current version range but not recorded in DB"
                )

        # Table census
        conn = self._connect()
        try:
            table_count = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
        finally:
            conn.close()

        return {
            "valid": len(errors) == 0,
            "current_version": current,
            "registered_migrations": len(registry),
            "applied_migrations": len(history),
            "pending_migrations": len(self.get_pending_migrations()),
            "tables_found": table_count,
            "errors": errors,
            "warnings": warnings,
        }

    def create_migration(self, description: str) -> dict:
        """Generate a new migration template with the next available ID.

        The migration is appended to the in-memory registry but **not**
        applied.  Callers should persist the SQL to their migration list.

        Parameters
        ----------
        description : str
            Human-readable summary of the migration.

        Returns
        -------
        dict
            ``id``, ``description``, ``template_up``, ``template_down``.
        """
        next_id = max((m.id for m in self._migrations), default=0) + 1
        template_up = (
            f"-- Migration {next_id}: {description}\n"
            f"-- TODO: Add your UP SQL here\n"
        )
        template_down = (
            f"-- Rollback for migration {next_id}\n"
            f"-- TODO: Add your DOWN SQL here\n"
        )

        new_migration = Migration(
            id=next_id,
            description=description,
            up_sql=template_up,
            down_sql=template_down,
        )
        self._migrations.append(new_migration)
        self._migrations.sort(key=lambda m: m.id)

        logger.info("Created migration template %d: %s", next_id, description)
        return {
            "id": next_id,
            "description": description,
            "template_up": template_up,
            "template_down": template_down,
            "checksum": new_migration.checksum,
        }

    def backup_before_migrate(self, backup_dir: str = "") -> str:
        """Create a timestamped backup of the database file.

        Parameters
        ----------
        backup_dir : str
            Directory to write the backup into.  Defaults to a ``backups``
            subdirectory next to the database.

        Returns
        -------
        str
            Absolute path to the backup file.

        Raises
        ------
        FileNotFoundError
            If the source database does not exist.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        if backup_dir:
            dest_dir = Path(backup_dir)
        else:
            dest_dir = self.db_path.parent / "backups"

        dest_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"{self.db_path.stem}_v{self.get_current_version()}_{stamp}.db"
        backup_path = dest_dir / backup_name

        # Use SQLite online backup API for WAL-safe copy
        src_conn = sqlite3.connect(str(self.db_path))
        dst_conn = sqlite3.connect(str(backup_path))
        try:
            src_conn.backup(dst_conn)
            logger.info("Backup created: %s", backup_path)
        finally:
            dst_conn.close()
            src_conn.close()

        return str(backup_path)

    def auto_migrate(self, *, dry_run: bool = False) -> dict:
        """Full auto-migration workflow: backup → detect → apply → validate.

        Parameters
        ----------
        dry_run : bool
            If ``True``, skip backup and application — just report what
            would happen.

        Returns
        -------
        dict
            ``backup_path``, ``before_version``, ``after_version``,
            ``applied`` (list), ``validation``, ``dry_run`` (bool).
        """
        before = self.get_current_version()
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("Schema is up to date (version %d)", before)
            return {
                "backup_path": None,
                "before_version": before,
                "after_version": before,
                "applied": [],
                "validation": self.validate_schema(),
                "dry_run": dry_run,
            }

        if dry_run:
            logger.info(
                "Dry-run: %d pending migration(s) from version %d",
                len(pending),
                before,
            )
            return {
                "backup_path": None,
                "before_version": before,
                "after_version": pending[-1]["id"] if pending else before,
                "applied": pending,
                "validation": self.validate_schema(),
                "dry_run": True,
            }

        # 1. Backup
        backup_path: str | None = None
        if self.db_path.exists():
            try:
                backup_path = self.backup_before_migrate()
            except Exception:
                logger.exception("Backup failed — aborting migration")
                return {
                    "backup_path": None,
                    "before_version": before,
                    "after_version": before,
                    "applied": [],
                    "validation": {"valid": False, "errors": ["Backup failed"]},
                    "dry_run": False,
                }

        # 2. Apply
        applied = self.migrate_up()

        # 3. Validate
        after = self.get_current_version()
        validation = self.validate_schema()

        summary = {
            "backup_path": backup_path,
            "before_version": before,
            "after_version": after,
            "applied": applied,
            "validation": validation,
            "dry_run": False,
        }

        if validation["valid"]:
            logger.info(
                "Auto-migration complete: v%d → v%d (%d applied)",
                before,
                after,
                len(applied),
            )
        else:
            logger.warning(
                "Auto-migration finished with validation errors: %s",
                validation["errors"],
            )

        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_migration(self, migration_id: int) -> Migration | None:
        """Look up a migration by ID in the registry."""
        for m in self._migrations:
            if m.id == migration_id:
                return m
        return None

    def _rollback_one(self, migration: Migration) -> bool:
        """Execute the down_sql for a single migration."""
        conn = self._connect()
        try:
            sp_name = f"rollback_{migration.id}"
            conn.execute(f"SAVEPOINT {sp_name}")
            try:
                conn.executescript(migration.down_sql)
                conn.execute(
                    "DELETE FROM schema_migrations WHERE id = ?",
                    (migration.id,),
                )
                conn.execute(f"RELEASE {sp_name}")
                conn.commit()
                logger.info(
                    "Rolled back migration %d: %s",
                    migration.id,
                    migration.description,
                )
                return True
            except Exception:
                conn.execute(f"ROLLBACK TO {sp_name}")
                conn.execute(f"RELEASE {sp_name}")
                logger.exception(
                    "Failed to rollback migration %d: %s",
                    migration.id,
                    migration.description,
                )
                return False
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
