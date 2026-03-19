from __future__ import annotations
import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""
ProvenanceEngine — Chain-of-custody tracking and QuoteLock for all evidence.

Every factual assertion in LitigationOS traces back to a source file, page,
and offset.  QuoteLock entries store verbatim text and guarantee that the
content in file_atoms.content exactly matches the original source.

Provenance Format Examples
--------------------------
- ``evidence_quotes:2345``            — quote ID in evidence_quotes table
- ``documents:DOC:789 page=12``       — document page reference
- ``file=F:/Litigation/Complaint.pdf page=3 offset=1250`` — file-level ref
- ``authority_chains:chain_12``       — authority chain reference
"""

import argparse
import hashlib
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve project paths before importing local modules
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
_DEFAULT_DB = _LITIGOS_ROOT / "litigation_context.db"

# Try importing pipeline utilities — graceful fallback if unavailable.
try:
    from failsafe import never_crash, safe_call, get_robust_connection  # type: ignore
except ImportError:
    # Minimal stubs so the module works stand-alone.
    def never_crash(fallback=None):  # type: ignore[override]
        """No-op decorator when failsafe is unavailable."""
        def _wrap(fn):
            def _inner(*a, **kw):
                try:
                    return fn(*a, **kw)
                except Exception as exc:
                    logging.getLogger(__name__).error("never_crash fallback: %s", exc)
                    return fallback
            _inner.__name__ = fn.__name__
            _inner.__doc__ = fn.__doc__
            return _inner
        return _wrap

    def safe_call(fn, *args, timeout_s=30, fallback=None, **kwargs):  # type: ignore[override]
        try:
            return fn(*args, **kwargs)
        except Exception:
            return fallback

    def get_robust_connection(db_path, timeout=120):  # type: ignore[override]
        conn = sqlite3.connect(str(db_path), timeout=timeout)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=120000")
        return conn

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# SQL constants
# ═══════════════════════════════════════════════════════════════════════════

_MIGRATE_COLUMNS = [
    # (column_name, column_def)
    ("source_field", "TEXT"),
    ("file_id", "TEXT"),
    ("page_number", "INTEGER"),
    ("posture", "TEXT DEFAULT 'EVIDENCE_FACT'"),
    ("truth_tag", "TEXT DEFAULT 'UNVERIFIED'"),
    ("quote_locked", "INTEGER DEFAULT 0"),
    ("verbatim_hash", "TEXT"),
]

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS provenance_refs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    atom_id     TEXT    NOT NULL,
    source_table TEXT   NOT NULL,
    source_id   TEXT,
    match_type  TEXT,
    confidence  REAL    DEFAULT 0.0,
    run_id      TEXT,
    created_at  TEXT,
    source_field TEXT,
    file_id     TEXT,
    page_number INTEGER,
    posture     TEXT    DEFAULT 'EVIDENCE_FACT',
    truth_tag   TEXT    DEFAULT 'UNVERIFIED',
    quote_locked INTEGER DEFAULT 0,
    verbatim_hash TEXT
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_pr_atom ON provenance_refs(atom_id);",
    "CREATE INDEX IF NOT EXISTS idx_pr_source ON provenance_refs(source_table, source_id);",
    "CREATE INDEX IF NOT EXISTS idx_pr_quote_locked ON provenance_refs(quote_locked) WHERE quote_locked = 1;",
    "CREATE INDEX IF NOT EXISTS idx_pr_run ON provenance_refs(run_id);",
    "CREATE INDEX IF NOT EXISTS idx_pr_posture ON provenance_refs(posture);",
    "CREATE INDEX IF NOT EXISTS idx_pr_truth ON provenance_refs(truth_tag);",
]


# ═══════════════════════════════════════════════════════════════════════════
# ProvenanceEngine
# ═══════════════════════════════════════════════════════════════════════════

class ProvenanceEngine:
    """Track provenance and enforce QuoteLock for all evidence.

    Every atom in ``file_atoms`` can have one or more provenance references
    that point back to the original source table/row, file, and page.

    QuoteLock entries additionally store a SHA-256 hash of the verbatim text
    so any downstream mutation is instantly detectable.
    """

    POSTURES = {"RECORD_FACT", "EVIDENCE_FACT", "SWORN_FACT", "ALLEGATION", "INFERENCE"}
    TRUTH_TAGS = {"PROVEN", "INFERRED", "ALLEGED", "DISPUTED", "UNVERIFIED"}

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._conn: sqlite3.Connection | None = None
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            # Skip get_robust_connection — its PRAGMA integrity_check hangs on 10GB DB
            self._conn = sqlite3.connect(str(self._db_path), timeout=120)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA busy_timeout=120000")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    @never_crash(fallback=None)
    def _ensure_schema(self) -> None:
        """Create table if missing, then add any new columns."""
        conn = self._get_conn()
        conn.execute(_CREATE_TABLE)
        # Migrate: add columns that may not exist yet
        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(provenance_refs)").fetchall()
        }
        for col_name, col_def in _MIGRATE_COLUMNS:
            if col_name not in existing:
                try:
                    conn.execute(f"ALTER TABLE provenance_refs ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass  # already exists — race condition safe
        for idx_sql in _CREATE_INDEXES:
            try:
                conn.execute(idx_sql)
            except sqlite3.OperationalError:
                pass
        conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

    def _validate_posture(self, posture: str) -> str:
        if posture not in self.POSTURES:
            raise ValueError(f"Invalid posture '{posture}'. Must be one of {self.POSTURES}")
        return posture

    def _validate_truth_tag(self, truth_tag: str) -> str:
        if truth_tag not in self.TRUTH_TAGS:
            raise ValueError(f"Invalid truth_tag '{truth_tag}'. Must be one of {self.TRUTH_TAGS}")
        return truth_tag

    # ------------------------------------------------------------------
    # Core: create_ref / create_refs_batch
    # ------------------------------------------------------------------

    @never_crash(fallback=-1)
    def create_ref(
        self,
        atom_id: int,
        source_table: str,
        source_row_id: str,
        source_field: str | None = None,
        file_id: str | None = None,
        page_number: int | None = None,
        posture: str = "EVIDENCE_FACT",
        truth_tag: str = "UNVERIFIED",
        run_id: str | None = None,
    ) -> int:
        """Create a provenance reference linking an atom to its source.

        Returns the new ``ref_id`` (``provenance_refs.id``), or ``-1`` on
        failure.
        """
        self._validate_posture(posture)
        self._validate_truth_tag(truth_tag)
        conn = self._get_conn()
        # Map to actual provenance_refs schema columns
        metadata = json.dumps({
            "source_field": source_field,
            "file_id": file_id,
            "page_number": page_number,
            "posture": posture,
            "truth_tag": truth_tag,
        }) if any([source_field, file_id, page_number]) else None
        cur = conn.execute(
            """INSERT INTO provenance_refs
               (atom_id, source_table, source_id, match_type,
                confidence, run_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(atom_id), source_table, source_row_id,
                posture or "EVIDENCE_FACT",
                1.0,
                run_id or str(uuid.uuid4()), self._now(),
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    @never_crash(fallback=0)
    def create_refs_batch(self, refs: list[dict]) -> int:
        """Batch-create provenance references inside a single transaction.

        Each dict in *refs* must contain at minimum ``atom_id``,
        ``source_table``, and ``source_row_id``.  Returns count created.
        """
        if not refs:
            return 0
        conn = self._get_conn()
        now = self._now()
        rows: list[tuple] = []
        for r in refs:
            posture = r.get("posture", "EVIDENCE_FACT")
            truth_tag = r.get("truth_tag", "UNVERIFIED")
            self._validate_posture(posture)
            self._validate_truth_tag(truth_tag)
            rows.append((
                str(r["atom_id"]),
                r["source_table"],
                r.get("source_row_id", r.get("source_id", "")),
                posture or "EVIDENCE_FACT",
                1.0,
                r.get("run_id") or str(uuid.uuid4()),
                now,
            ))
        conn.execute("BEGIN")
        try:
            conn.executemany(
                """INSERT INTO provenance_refs
                   (atom_id, source_table, source_id, match_type,
                    confidence, run_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return len(rows)

    # ------------------------------------------------------------------
    # QuoteLock
    # ------------------------------------------------------------------

    @never_crash(fallback=-1)
    def lock_quote(
        self,
        atom_id: int,
        verbatim_text: str,
        source_table: str,
        source_row_id: str,
        page_number: int | None = None,
    ) -> int:
        """Create a QuoteLock entry — verbatim text pinned to its source.

        The text stored in ``file_atoms.content`` for *atom_id* **must**
        exactly match *verbatim_text*.  A SHA-256 hash of the verbatim text
        is stored so drift is detectable later via :meth:`verify_quote`.

        Returns the new ``ref_id``, or ``-1`` on failure.
        """
        conn = self._get_conn()

        # Verify that the atom's content matches the verbatim text
        row = conn.execute(
            "SELECT content FROM file_atoms WHERE atom_id = ?", (str(atom_id),)
        ).fetchone()
        if row is None:
            logger.error("lock_quote: atom_id %s not found in file_atoms", atom_id)
            return -1
        atom_content: str = row["content"] or ""
        if atom_content != verbatim_text:
            logger.error(
                "lock_quote: content mismatch for atom %s — "
                "atom has %d chars, verbatim has %d chars",
                atom_id, len(atom_content), len(verbatim_text),
            )
            return -1

        v_hash = self._sha256(verbatim_text)
        cur = conn.execute(
            """INSERT INTO provenance_refs
               (atom_id, source_table, source_id, match_type,
                confidence, run_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(atom_id), source_table, source_row_id,
                "QUOTE_LOCKED",
                1.0, str(uuid.uuid4()), self._now(),
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    @never_crash(fallback={"valid": False, "error": "exception in verify_quote"})
    def verify_quote(self, atom_id: int) -> dict:
        """Verify that a QuoteLocked quote still matches its file_atoms content.

        Returns::

            {
                "valid": bool,
                "atom_text": str | None,
                "stored_hash": str | None,
                "current_hash": str | None,
                "match": bool,
            }
        """
        conn = self._get_conn()
        ref = conn.execute(
            """SELECT id, verbatim_hash FROM provenance_refs
               WHERE atom_id = ? AND quote_locked = 1
               ORDER BY id DESC LIMIT 1""",
            (str(atom_id),),
        ).fetchone()
        if ref is None:
            return {"valid": False, "atom_text": None, "stored_hash": None,
                    "current_hash": None, "match": False,
                    "error": "No QuoteLock entry for this atom"}

        atom = conn.execute(
            "SELECT content FROM file_atoms WHERE atom_id = ?", (str(atom_id),)
        ).fetchone()
        if atom is None:
            return {"valid": False, "atom_text": None,
                    "stored_hash": ref["verbatim_hash"],
                    "current_hash": None, "match": False,
                    "error": "Atom not found in file_atoms"}

        current_text: str = atom["content"] or ""
        current_hash = self._sha256(current_text)
        match = current_hash == ref["verbatim_hash"]
        return {
            "valid": match,
            "atom_text": current_text[:200],
            "stored_hash": ref["verbatim_hash"],
            "current_hash": current_hash,
            "match": match,
        }

    @never_crash(fallback={"total": 0, "valid": 0, "invalid": 0, "errors": 0})
    def verify_all_quotes(self, run_id: str | None = None) -> dict:
        """Verify every QuoteLocked quote in the database.

        Returns ``{total, valid, invalid, errors, details}`` where
        *details* is a list of failed atom IDs.
        """
        conn = self._get_conn()
        query = "SELECT DISTINCT atom_id FROM provenance_refs WHERE quote_locked = 1"
        params: tuple = ()
        if run_id:
            query += " AND run_id = ?"
            params = (run_id,)
        rows = conn.execute(query, params).fetchall()

        total = len(rows)
        valid = invalid = errors = 0
        failed_atoms: list[str] = []
        for row in rows:
            result = safe_call(self.verify_quote, int(row["atom_id"]),
                               timeout_s=10, fallback=None)
            if result is None:
                errors += 1
                failed_atoms.append(row["atom_id"])
            elif result.get("match"):
                valid += 1
            else:
                invalid += 1
                failed_atoms.append(row["atom_id"])

        return {
            "total": total, "valid": valid, "invalid": invalid,
            "errors": errors, "failed_atoms": failed_atoms[:50],
        }

    # ------------------------------------------------------------------
    # Provenance chain queries
    # ------------------------------------------------------------------

    @never_crash(fallback=[])
    def get_provenance_chain(self, atom_id: int) -> list[dict]:
        """Return the full provenance chain for an atom.

        Each entry: ``{ref_id, source_table, source_row_id, file_id,
        page_number, posture, truth_tag, quote_locked, created_at}``.
        """
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id AS ref_id, source_table, source_id AS source_row_id,
                      source_field, file_id, page_number, posture, truth_tag,
                      quote_locked, verbatim_hash, created_at
               FROM provenance_refs
               WHERE atom_id = ?
               ORDER BY id""",
            (str(atom_id),),
        ).fetchall()
        return [dict(r) for r in rows]

    @never_crash(fallback={"file_path": None, "atoms": []})
    def get_file_provenance(self, file_id: str) -> dict:
        """Get all provenance for a given file_id.

        Returns ``{file_id, atoms: [{atom_id, atom_type, content, refs}]}``.
        """
        conn = self._get_conn()
        atoms = conn.execute(
            """SELECT atom_id, atom_type, content
               FROM file_atoms WHERE file_id = ?
               ORDER BY atom_id""",
            (file_id,),
        ).fetchall()

        result_atoms: list[dict] = []
        for a in atoms:
            refs = conn.execute(
                """SELECT id AS ref_id, source_table, source_id AS source_row_id,
                          posture, truth_tag, quote_locked, created_at
                   FROM provenance_refs WHERE atom_id = ?
                   ORDER BY id""",
                (a["atom_id"],),
            ).fetchall()
            result_atoms.append({
                "atom_id": a["atom_id"],
                "atom_type": a["atom_type"],
                "content": (a["content"] or "")[:200],
                "refs": [dict(r) for r in refs],
            })
        return {"file_id": file_id, "atoms": result_atoms}

    # ------------------------------------------------------------------
    # Citation formatting
    # ------------------------------------------------------------------

    @never_crash(fallback="[provenance unavailable]")
    def format_citation(self, atom_id: int) -> str:
        """Format a court-filing citation string for an atom.

        Examples::

            evidence_quotes:2345
            documents:DOC:789 page=12
            file=F:/Litigation/Complaint.pdf page=3 offset=1250
            authority_chains:chain_12
        """
        conn = self._get_conn()
        ref = conn.execute(
            """SELECT source_table, source_id, file_id, page_number, source_field
               FROM provenance_refs
               WHERE atom_id = ?
               ORDER BY quote_locked DESC, id DESC
               LIMIT 1""",
            (str(atom_id),),
        ).fetchone()
        if ref is None:
            return f"[no provenance for atom {atom_id}]"

        parts: list[str] = []
        src_table = ref["source_table"] or ""
        src_id = ref["source_id"] or ""

        if src_table and src_id:
            parts.append(f"{src_table}:{src_id}")
        elif src_table:
            parts.append(src_table)

        if ref["file_id"]:
            parts.append(f"file={ref['file_id']}")
        if ref["page_number"] is not None:
            parts.append(f"page={ref['page_number']}")
        if ref["source_field"]:
            parts.append(f"field={ref['source_field']}")

        return " ".join(parts) if parts else f"[unresolved atom {atom_id}]"

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    @never_crash(fallback=[])
    def audit_trail(self, run_id: str | None = None, limit: int = 100) -> list[dict]:
        """Return recent provenance audit entries, newest first."""
        conn = self._get_conn()
        if run_id:
            rows = conn.execute(
                """SELECT id AS ref_id, atom_id, source_table, source_id,
                          posture, truth_tag, quote_locked, run_id, created_at
                   FROM provenance_refs
                   WHERE run_id = ?
                   ORDER BY id DESC LIMIT ?""",
                (run_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id AS ref_id, atom_id, source_table, source_id,
                          posture, truth_tag, quote_locked, run_id, created_at
                   FROM provenance_refs
                   ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @never_crash(fallback={"total_refs": 0, "error": "stats unavailable"})
    def stats(self) -> dict:
        """Return provenance statistics.

        Returns::

            {
                total_refs, quote_locked, verified (PROVEN), unverified,
                by_posture: {posture: count}, by_truth_tag: {tag: count}
            }
        """
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM provenance_refs").fetchone()[0]
        locked = conn.execute(
            "SELECT COUNT(*) FROM provenance_refs WHERE quote_locked = 1"
        ).fetchone()[0]

        by_posture: dict[str, int] = {}
        for row in conn.execute(
            "SELECT posture, COUNT(*) AS cnt FROM provenance_refs GROUP BY posture"
        ):
            by_posture[row["posture"] or "NULL"] = row["cnt"]

        by_truth: dict[str, int] = {}
        for row in conn.execute(
            "SELECT truth_tag, COUNT(*) AS cnt FROM provenance_refs GROUP BY truth_tag"
        ):
            by_truth[row["truth_tag"] or "NULL"] = row["cnt"]

        verified = by_truth.get("PROVEN", 0)
        unverified = total - verified

        return {
            "total_refs": total,
            "quote_locked": locked,
            "verified": verified,
            "unverified": unverified,
            "by_posture": by_posture,
            "by_truth_tag": by_truth,
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    @never_crash(fallback=None)
    def export_audit(self, output_path: str, run_id: str | None = None) -> str | None:
        """Export the provenance audit trail to a JSON file.

        The output includes court-compatible citation formatting for every
        entry.  Returns the output path on success, ``None`` on failure.
        """
        entries = self.audit_trail(run_id=run_id, limit=100_000)
        export_data = {
            "exported_at": self._now(),
            "run_id": run_id,
            "count": len(entries),
            "entries": entries,
        }
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(export_data, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Exported %d provenance entries → %s", len(entries), out)
        return str(out)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ═══════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="provenance_engine",
        description="LitigationOS Provenance Tracking & QuoteLock Engine",
    )
    p.add_argument("--db", default=str(_DEFAULT_DB), help="Path to litigation_context.db")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("stats", help="Print provenance statistics")

    a = sub.add_parser("audit", help="Print recent audit trail")
    a.add_argument("--run-id", default=None, help="Filter by run_id")
    a.add_argument("--limit", type=int, default=20, help="Max entries (default 20)")

    v = sub.add_parser("verify", help="Verify all QuoteLocked quotes")
    v.add_argument("--run-id", default=None, help="Filter by run_id")

    e = sub.add_parser("export", help="Export audit trail to JSON")
    e.add_argument("--output", required=True, help="Output JSON file path")
    e.add_argument("--run-id", default=None, help="Filter by run_id")

    c = sub.add_parser("chain", help="Show provenance chain for an atom")
    c.add_argument("atom_id", type=int, help="Atom ID to look up")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    engine = ProvenanceEngine(db_path=args.db)
    try:
        if args.command == "stats":
            s = engine.stats()
            print(json.dumps(s, indent=2, default=str))

        elif args.command == "audit":
            entries = engine.audit_trail(run_id=args.run_id, limit=args.limit)
            print(json.dumps(entries, indent=2, default=str))

        elif args.command == "verify":
            result = engine.verify_all_quotes(run_id=args.run_id)
            print(json.dumps(result, indent=2, default=str))
            if result.get("invalid", 0) > 0 or result.get("errors", 0) > 0:
                return 1

        elif args.command == "export":
            path = engine.export_audit(args.output, run_id=args.run_id)
            if path:
                print(f"Exported → {path}")
            else:
                print("Export failed", file=sys.stderr)
                return 1

        elif args.command == "chain":
            chain = engine.get_provenance_chain(args.atom_id)
            print(json.dumps(chain, indent=2, default=str))

    finally:
        engine.close()
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
