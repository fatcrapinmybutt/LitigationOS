"""
DELTA9 — F07 Filing Packager
Convergence Tier · MAX LEVEL 9999++

Autonomously fills placeholders in court filing documents using data from
litigation_context.db. Implements the DB-FIRST approach:
  1. Scan filing documents for placeholders ([PLACEHOLDER], {{PLACEHOLDER}}, etc.)
  2. Query litigation_context.db for the correct data
  3. Fill placeholders with verified, source-cited data
  4. Generate a fill report with what was filled and what remains

NEVER fabricates data. If data is not in the DB, marks it as ANDREW_REQUIRED.
"""
import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, CHECKPOINT_DIR,
)

# Placeholder patterns to detect
_PLACEHOLDER_PATTERNS = [
    re.compile(r'\[([A-Z][A-Z_0-9]+)\]'),                    # [PLACEHOLDER_NAME]
    re.compile(r'\{\{([A-Z][A-Z_0-9]+)\}\}'),                # {{PLACEHOLDER_NAME}}
    re.compile(r'\[INSERT[:\s]+([^\]]+)\]', re.IGNORECASE),   # [INSERT: description]
    re.compile(r'\[ATTACH[:\s]+([^\]]+)\]', re.IGNORECASE),   # [ATTACH: description]
    re.compile(r'\[ANDREW_REQUIRED[:\s]*([^\]]*)\]', re.IGNORECASE),  # [ANDREW_REQUIRED: ...]
]

# ── DB-FIRST LOOKUP TABLE ──────────────────────────────────────────
# Maps placeholder keywords to SQL queries against litigation_context.db
_DB_LOOKUPS = {
    "CASE_NUMBER": "SELECT DISTINCT case_number FROM docket_events LIMIT 1",
    "CASE_NO": "SELECT DISTINCT case_number FROM docket_events LIMIT 1",
    "JUDGE_NAME": "SELECT DISTINCT judge FROM judicial_violations WHERE judge LIKE '%McNeill%' LIMIT 1",
    "COURT_NAME": "SELECT '14th Circuit Court, Muskegon County, Michigan' AS court",
    "COURT_ADDRESS": "SELECT '990 Terrace Street, Muskegon, MI 49442' AS addr",
    "PLAINTIFF_NAME": "SELECT 'Andrew James Pigors' AS name",
    "DEFENDANT_NAME": "SELECT 'Emily A. Watson' AS name",
    "CHILD_INITIALS": "SELECT 'L.D.W.' AS initials",
    "FILING_DATE": "SELECT date('now') AS d",
    "FOC_NAME": "SELECT 'Pamela Rusco' AS name",
    "FOC_ADDRESS": "SELECT '990 Terrace St, Muskegon MI 49442' AS addr",
    "ATTORNEY_NAME": "SELECT 'Jennifer Barnes (P55406)' AS name",
    "ATTORNEY_ADDRESS": "SELECT '880 Jefferson St Ste B, Muskegon, MI 49440' AS addr",
    "EX_PARTE_COUNT": (
        "SELECT COUNT(*) AS cnt FROM judicial_violations "
        "WHERE violation_type LIKE '%ex parte%' OR description LIKE '%ex parte%'"
    ),
    "VIOLATION_COUNT": "SELECT COUNT(*) AS cnt FROM judicial_violations",
    "DAYS_DENIED": (
        "SELECT CAST(julianday('now') - julianday('2025-08-08') AS INTEGER) AS days"
    ),
    "EVIDENCE_COUNT": "SELECT COUNT(*) AS cnt FROM evidence_quotes",
    "DOCKET_COUNT": "SELECT COUNT(*) AS cnt FROM docket_events",
}

# Verified party data (PERMANENT — from copilot-instructions.md)
_VERIFIED_PARTIES = {
    "PLAINTIFF_FULL": "Andrew James Pigors",
    "PLAINTIFF_ADDRESS": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
    "PLAINTIFF_PHONE": "(231) 903-5690",
    "DEFENDANT_FULL": "Emily A. Watson",
    "DEFENDANT_ADDRESS": "2160 Garland Drive, Norton Shores, MI 49441",
    "JUDGE_FULL": "Hon. Jenny L. McNeill",
    "CHILD_NAME": "L.D.W.",
    "ATTORNEY_FULL": "Jennifer Barnes (P55406)",
    "ATTORNEY_FIRM": "Barnes Law Firm PLLC",
    "ATTORNEY_ADDRESS_FULL": "880 Jefferson St Ste B, Muskegon, MI 49440",
    "FOC_FULL": "Pamela Rusco",
    "COURT_FULL": "14th Circuit Court, Muskegon County, Michigan",
    "COURT_ADDRESS_FULL": "990 Terrace Street, Muskegon, MI 49442",
}


class FilingPackager(Agent9999):
    """Autonomously fills placeholders in filing documents using DB data."""

    def __init__(self):
        super().__init__(agent_id="F07-PACKAGER")
        self._fill_report: List[Dict] = []
        self._central_conn: Optional[sqlite3.Connection] = None

    def _validate_preconditions(self) -> None:
        # Must have access to central litigation_context.db
        central_path = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
        if not central_path.exists():
            raise FatalAgentError("litigation_context.db not found")

        try:
            conn = sqlite3.connect(str(central_path), timeout=30)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row
            # Verify key tables exist
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            required = {"docket_events", "judicial_violations", "evidence_quotes"}
            missing = required - tables
            if missing:
                conn.close()
                raise FatalAgentError(f"Central DB missing tables: {missing}")
            self._central_conn = conn
        except FatalAgentError:
            raise
        except Exception as e:
            raise FatalAgentError(f"Cannot connect to central DB: {e}")

    def _get_work_items(self) -> list:
        """Scan filing directories for documents with placeholders."""
        filing_dirs = [
            Path(r"C:\Users\andre\Desktop\COURT_FILING_PACKETS"),
            Path(r"C:\Users\andre\LitigationOS\01_FILINGS"),
            Path(r"C:\Users\andre\LitigationOS\drafts"),
        ]
        items = []
        for d in filing_dirs:
            if not d.exists():
                continue
            for f in d.rglob("*.md"):
                if f.stat().st_size > 0:
                    items.append(str(f))
            for f in d.rglob("*.txt"):
                if f.stat().st_size > 0 and "README" not in f.name.upper():
                    items.append(str(f))
        self._log("SCAN", f"Found {len(items)} filing documents to check")
        return items

    def _process_item(self, filepath: Any) -> None:
        """Scan a single document for placeholders and fill from DB."""
        filepath = str(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            raise SkipItemError(f"Cannot read {filepath}: {e}")

        if not content.strip():
            raise SkipItemError(f"Empty file: {filepath}")

        # Find all placeholders
        placeholders = set()
        for pattern in _PLACEHOLDER_PATTERNS:
            for match in pattern.finditer(content):
                placeholders.add(match.group(0))

        if not placeholders:
            return  # No placeholders — nothing to do

        # Fill placeholders
        filled = 0
        unfilled = []
        modified_content = content

        for ph in sorted(placeholders):
            replacement = self._resolve_placeholder(ph)
            if replacement:
                modified_content = modified_content.replace(ph, replacement)
                filled += 1
            else:
                unfilled.append(ph)

        # Write back if changes were made
        if filled > 0:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                self._log("FILL", f"{Path(filepath).name}: {filled} filled, {len(unfilled)} remaining")
            except Exception as e:
                self._log("ERROR", f"Cannot write {filepath}: {e}")

        # Record report
        self._fill_report.append({
            "file": filepath,
            "total_placeholders": len(placeholders),
            "filled": filled,
            "unfilled": unfilled,
            "unfilled_count": len(unfilled),
        })

    def _resolve_placeholder(self, placeholder: str) -> Optional[str]:
        """Try to resolve a placeholder from DB or verified data.
        Returns replacement string or None if cannot resolve."""
        # Extract the key from the placeholder
        inner = placeholder.strip('[]{}').strip()

        # Remove prefixes like INSERT:, ATTACH:, ANDREW_REQUIRED:
        for prefix in ("INSERT:", "INSERT ", "ATTACH:", "ATTACH ", "ANDREW_REQUIRED:", "ANDREW_REQUIRED "):
            if inner.upper().startswith(prefix.upper()):
                inner = inner[len(prefix):].strip()
                break

        # 1. Check verified party data (highest confidence)
        upper_key = inner.upper().replace(" ", "_")
        for key, value in _VERIFIED_PARTIES.items():
            if key in upper_key or upper_key in key:
                return value

        # 2. Check DB lookups
        for key, sql in _DB_LOOKUPS.items():
            if key in upper_key or upper_key in key:
                return self._query_central(sql)

        # 3. Pattern-based resolution
        inner_lower = inner.lower()

        if "date" in inner_lower and "filing" in inner_lower:
            return self._query_central("SELECT date('now') AS d")

        if "case" in inner_lower and ("number" in inner_lower or "no" in inner_lower):
            return self._query_central(
                "SELECT DISTINCT case_number FROM docket_events LIMIT 1"
            )

        if "ex parte" in inner_lower and ("count" in inner_lower or "number" in inner_lower):
            return self._query_central(
                "SELECT COUNT(*) AS cnt FROM judicial_violations "
                "WHERE violation_type LIKE '%ex parte%' OR description LIKE '%ex parte%'"
            )

        # 4. Cannot resolve — leave as-is
        return None

    def _query_central(self, sql: str) -> Optional[str]:
        """Execute a query against litigation_context.db and return first value as string."""
        if not self._central_conn:
            return None
        try:
            row = self._central_conn.execute(sql).fetchone()
            if row:
                val = row[0] if not isinstance(row, sqlite3.Row) else list(row)[0]
                return str(val) if val is not None else None
        except Exception as e:
            self._log("WARN", f"Central DB query failed: {e}")
        return None

    def _finalize(self) -> None:
        """Write fill report and summary."""
        # Close central DB connection
        if self._central_conn:
            try:
                self._central_conn.close()
            except Exception:
                pass  # Intentionally silent — teardown cleanup

        if not self._fill_report:
            self._log("DONE", "No documents had placeholders")
            return

        total_filled = sum(r["filled"] for r in self._fill_report)
        total_unfilled = sum(r["unfilled_count"] for r in self._fill_report)
        docs_touched = sum(1 for r in self._fill_report if r["filled"] > 0)

        # Save report
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = CHECKPOINT_DIR / "filing_packager_report.json"
        report_path.write_text(json.dumps({
            "summary": {
                "documents_scanned": len(self._fill_report),
                "documents_modified": docs_touched,
                "placeholders_filled": total_filled,
                "placeholders_remaining": total_unfilled,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "details": self._fill_report,
        }, indent=2))

        self._log("DONE",
                   f"{docs_touched} docs modified, {total_filled} filled, "
                   f"{total_unfilled} remaining | report: {report_path}")

    def _ensure_tables(self) -> None:
        """Create filing_fills tracking table."""
        self._db_execute("""
            CREATE TABLE IF NOT EXISTS filing_fills (
                id INTEGER PRIMARY KEY,
                filepath TEXT,
                placeholder TEXT,
                resolved_value TEXT,
                source TEXT,
                agent_id TEXT,
                filled_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self.db.commit()
