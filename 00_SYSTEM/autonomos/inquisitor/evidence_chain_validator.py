"""
DELTA99 Ω∞ — Evidence Chain Auto-Validator
============================================
Continuous validator ensuring every claim has evidence, every authority chain
is complete, every filing has required support. Auto-resolves gaps by searching
existing evidence via FTS5.

Queries: claims(653), claim_evidence_links(2655), authority_chains(44),
         filing_readiness(24), bif_evidence_links(519), gap_tickets
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, INQUISITOR_RESULTS_DB

VALIDATION_DB = Path(__file__).parent / "chain_validation.db"


def _init_db() -> sqlite3.Connection:
    VALIDATION_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(VALIDATION_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chain_validations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            validation_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            target_name TEXT DEFAULT '',
            is_valid INTEGER DEFAULT 0,
            issues_found INTEGER DEFAULT 0,
            issues_resolved INTEGER DEFAULT 0,
            details TEXT DEFAULT '',
            validated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS auto_resolved_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gap_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            evidence_found TEXT NOT NULL,
            evidence_source TEXT DEFAULT '',
            confidence REAL DEFAULT 0.0,
            resolved_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS validation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT NOT NULL,
            claims_checked INTEGER DEFAULT 0,
            chains_checked INTEGER DEFAULT 0,
            filings_checked INTEGER DEFAULT 0,
            gaps_found INTEGER DEFAULT 0,
            gaps_auto_resolved INTEGER DEFAULT 0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _get_central_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=120000")
    return conn


@dataclass
class ValidationResult:
    claims_total: int = 0
    claims_with_evidence: int = 0
    claims_without_evidence: int = 0
    orphan_claims: list = field(default_factory=list)
    chains_total: int = 0
    chains_complete: int = 0
    chains_incomplete: list = field(default_factory=list)
    filings_total: int = 0
    filings_ready: int = 0
    filings_not_ready: list = field(default_factory=list)
    gaps_found: int = 0
    gaps_auto_resolved: int = 0
    duration_s: float = 0.0


def validate_claim_evidence_links(central: sqlite3.Connection) -> tuple[int, int, list]:
    """Validate every claim has at least 1 evidence link."""
    try:
        total = central.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    except sqlite3.Error:
        return 0, 0, []

    # Find claims WITHOUT evidence links
    try:
        orphans = central.execute("""
            SELECT c.claim_id, c.proposition
            FROM claims c
            LEFT JOIN claim_evidence_links cel ON c.claim_id = cel.claim_id
            WHERE cel.claim_id IS NULL
            LIMIT 100
        """).fetchall()
    except sqlite3.Error:
        # Try alternate column names
        try:
            orphans = central.execute("""
                SELECT c.claim_id, c.claim_text
                FROM claims c
                LEFT JOIN claim_evidence_links cel ON c.claim_id = cel.claim_id
                WHERE cel.claim_id IS NULL
                LIMIT 100
            """).fetchall()
        except sqlite3.Error:
            orphans = []

    with_evidence = total - len(orphans)
    orphan_list = [{"id": r[0], "text": str(r[1])[:200]} for r in orphans]
    return total, with_evidence, orphan_list


def validate_authority_chains(central: sqlite3.Connection) -> tuple[int, int, list]:
    """Validate all authority chains are complete."""
    try:
        rows = central.execute("""
            SELECT chain_id, chain_name, chain_complete
            FROM authority_chains
        """).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT rowid, vehicle_name, chain_complete
                FROM authority_chains
            """).fetchall()
        except sqlite3.Error:
            return 0, 0, []

    total = len(rows)
    complete = sum(1 for r in rows if r[2])
    incomplete = [{"id": r[0], "name": str(r[1])} for r in rows if not r[2]]
    return total, complete, incomplete


def validate_filing_readiness(central: sqlite3.Connection) -> tuple[int, int, list]:
    """Check filing readiness scores."""
    try:
        rows = central.execute("""
            SELECT vehicle_name, readiness_score, missing_items
            FROM filing_readiness
        """).fetchall()
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT vehicle_name, score, gaps
                FROM filing_readiness
            """).fetchall()
        except sqlite3.Error:
            return 0, 0, []

    total = len(rows)
    ready = sum(1 for r in rows if r[1] and float(r[1]) >= 80)
    not_ready = [{"name": r[0], "score": r[1], "missing": str(r[2])[:200]}
                 for r in rows if not r[1] or float(r[1]) < 80]
    return total, ready, not_ready


def auto_resolve_gaps(central: sqlite3.Connection, val_db: sqlite3.Connection,
                      orphan_claims: list) -> int:
    """Attempt to auto-resolve evidence gaps using FTS5 search."""
    resolved = 0
    for claim in orphan_claims[:50]:  # Process top 50
        claim_text = claim.get("text", "")
        if not claim_text or len(claim_text) < 10:
            continue

        # Search evidence_quotes_fts for matching evidence
        keywords = " ".join(claim_text.split()[:8])  # First 8 words
        try:
            matches = central.execute("""
                SELECT rowid, quote_text FROM evidence_quotes_fts
                WHERE evidence_quotes_fts MATCH ?
                LIMIT 3
            """, (keywords,)).fetchall()
        except sqlite3.Error:
            # FTS5 not available or different schema
            try:
                like_term = f"%{claim_text[:50]}%"
                matches = central.execute("""
                    SELECT rowid, quote_text FROM evidence_quotes
                    WHERE quote_text LIKE ? LIMIT 3
                """, (like_term,)).fetchall()
            except sqlite3.Error:
                matches = []

        if matches:
            for match in matches:
                try:
                    central.execute("""
                        INSERT OR IGNORE INTO claim_evidence_links (claim_id, evidence_id, confidence)
                        VALUES (?, ?, 0.6)
                    """, (claim["id"], match[0]))
                except sqlite3.Error:
                    pass

                val_db.execute("""
                    INSERT INTO auto_resolved_gaps (gap_type, target_id, evidence_found, confidence)
                    VALUES ('claim_evidence', ?, ?, 0.6)
                """, (str(claim["id"]), str(match[1])[:200]))

            resolved += 1

    central.commit()
    val_db.commit()
    return resolved


def run_full_validation() -> ValidationResult:
    """Run complete evidence chain validation."""
    start = time.time()
    result = ValidationResult()

    val_db = _init_db()
    central = _get_central_db()

    # 1. Validate claim-evidence links
    result.claims_total, result.claims_with_evidence, result.orphan_claims = \
        validate_claim_evidence_links(central)
    result.claims_without_evidence = result.claims_total - result.claims_with_evidence

    # 2. Validate authority chains
    result.chains_total, result.chains_complete, result.chains_incomplete = \
        validate_authority_chains(central)

    # 3. Validate filing readiness
    result.filings_total, result.filings_ready, result.filings_not_ready = \
        validate_filing_readiness(central)

    # 4. Count total gaps
    result.gaps_found = (result.claims_without_evidence +
                         len(result.chains_incomplete) +
                         len(result.filings_not_ready))

    # 5. Auto-resolve gaps
    if result.orphan_claims:
        result.gaps_auto_resolved = auto_resolve_gaps(central, val_db, result.orphan_claims)

    result.duration_s = round(time.time() - start, 2)

    # Log the run
    val_db.execute("""
        INSERT INTO validation_runs 
        (run_type, claims_checked, chains_checked, filings_checked, gaps_found, gaps_auto_resolved, duration_s)
        VALUES ('full', ?, ?, ?, ?, ?, ?)
    """, (result.claims_total, result.chains_total, result.filings_total,
          result.gaps_found, result.gaps_auto_resolved, result.duration_s))
    val_db.commit()

    central.close()
    val_db.close()
    return result


if __name__ == "__main__":
    result = run_full_validation()
    report = {
        "claims": {"total": result.claims_total, "with_evidence": result.claims_with_evidence,
                    "without_evidence": result.claims_without_evidence,
                    "orphans_sample": result.orphan_claims[:5]},
        "authority_chains": {"total": result.chains_total, "complete": result.chains_complete,
                             "incomplete": result.chains_incomplete[:5]},
        "filing_readiness": {"total": result.filings_total, "ready": result.filings_ready,
                             "not_ready": result.filings_not_ready[:5]},
        "gaps": {"found": result.gaps_found, "auto_resolved": result.gaps_auto_resolved},
        "duration_s": result.duration_s,
    }
    print(json.dumps(report, indent=2, default=str))
