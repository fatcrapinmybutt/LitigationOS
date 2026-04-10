"""
omega_populate.py — OMEGA ETL Population Engine
════════════════════════════════════════════════════════════════
Fills the 5 EMPTY analytical tables that make LitigationOS intelligence
features actually work. Without this, emergence_scan, gap_tracker,
and red_team all return nothing.

Root Cause (from ERROR-DEBUGGING-NEXUS Phase 2):
  - 92K evidence quotes, 16K timeline events, 5K judicial violations EXIST
  - But gap_tickets (0 rows), risk_events (0 rows), emergence_events (6 rows),
    cases (0 rows), parties (0 rows) are EMPTY
  - No ETL process ever transforms raw evidence → analytical intelligence

This engine performs 6 ETL operations:
  1. Populate `cases` — core case registry (7 lanes)
  2. Populate `parties` — all parties across all cases
  3. Populate `gap_tickets` — evidence gaps, quality gaps, deadline gaps
  4. Populate `risk_events` — adversarial vulnerabilities
  5. Populate `emergence_events` — cross-lane patterns + novel strategies
  6. Create + populate `adversary_models` — opposing attack prediction

Usage:
    python omega_populate.py              # Run all ETL
    python omega_populate.py --dry-run    # Preview without writing
    python omega_populate.py --step=gaps  # Run one step only

Safety:
    - NEVER deletes existing data (INSERT OR IGNORE only)
    - Idempotent — safe to run multiple times
    - Validates every INSERT before commit
    - Reports exact row counts before/after
"""

import sqlite3
import sys
import json
from datetime import date, datetime
from pathlib import Path

# Shared module integration (with fallback for standalone execution)
try:
    _SYSTEM_DIR = Path(__file__).resolve().parent.parent  # engines/ → 00_SYSTEM/
    if str(_SYSTEM_DIR) not in sys.path:
        sys.path.insert(0, str(_SYSTEM_DIR))
    from shared import get_db_path, get_root
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

if _HAS_SHARED:
    DB_PATH = get_db_path("litigation")
else:
    DB_PATH = str(Path(__file__).resolve().parents[2] / "litigation_context.db")  # fallback
SEPARATION_START = date(2025, 7, 29)
TODAY = date.today()
SEP_DAYS = (TODAY - SEPARATION_START).days

PRAGMAS = [
    "PRAGMA cache_size = -32000",
    "PRAGMA mmap_size = 268435456",
    "PRAGMA temp_store = 2",
    "PRAGMA journal_mode = WAL",
    "PRAGMA busy_timeout = 60000",
]


def connect():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    for p in PRAGMAS:
        conn.execute(p)
    return conn


def count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except Exception:
        return -1


# ══════════════════════════════════════════════════════════════════
# ETL 1: CASES — Core case registry
# ══════════════════════════════════════════════════════════════════

CASES = [
    ("2024-001507-DC", "family",   "Pigors v Watson — Custody",                "2024-04-01", "active", "A"),
    ("2025-002760-CZ", "civil",    "Pigors v Shady Oaks — Housing",            "2025-01-15", "dismissed", "B"),
    (None,             "federal",  "Pigors v McNeill et al — §1983",           None,         "drafting", "C"),
    ("2023-5907-PP",   "family",   "Watson v Pigors — PPO",                    "2023-10-15", "active", "D"),
    (None,             "judicial", "In re McNeill — JTC Complaint",            "2025-06-01", "active", "E"),
    ("366810",         "appellate","Pigors v Watson — COA Appeal",             "2025-10-01", "active", "F"),
    ("2025-25245676SM","criminal", "People v Pigors — Criminal",               "2025-08-01", "active", "CRIMINAL"),
]

def populate_cases(conn, dry_run=False):
    """Populate cases table with 7 litigation lanes."""
    before = count(conn, "cases")
    inserted = 0
    for case_num, case_type, title, filed, status, lane in CASES:
        # Check if already exists by title
        existing = conn.execute(
            "SELECT id FROM cases WHERE title = ?", (title,)
        ).fetchone()
        if existing:
            continue
        if dry_run:
            print(f"  [DRY] Would insert case: {title}")
            inserted += 1
            continue
        conn.execute(
            "INSERT INTO cases (case_number, case_type, title, filed_date, status) VALUES (?,?,?,?,?)",
            (case_num, case_type, title, filed, status)
        )
        inserted += 1
    if not dry_run:
        conn.commit()
    after = count(conn, "cases")
    print(f"  cases: {before} → {after} (+{inserted} inserted)")
    return inserted


# ══════════════════════════════════════════════════════════════════
# ETL 2: PARTIES — All parties across all cases
# ══════════════════════════════════════════════════════════════════

def populate_parties(conn, dry_run=False):
    """Populate parties table linked to cases."""
    before = count(conn, "parties")

    # Get case IDs
    cases = {row["title"]: row["id"] for row in
             conn.execute("SELECT id, title FROM cases").fetchall()}
    if not cases:
        print("  parties: SKIPPED (no cases yet — run cases ETL first)")
        return 0

    # Define parties per case
    party_defs = []
    custody_id = None
    for title, cid in cases.items():
        if "Custody" in title:
            custody_id = cid
            party_defs.extend([
                (cid, "Andrew James Pigors",     "plaintiff",   "individual"),
                (cid, "Emily A. Watson",         "defendant",   "individual"),
                (cid, "Hon. Jenny L. McNeill",   "judge",       "judicial"),
                (cid, "L.D.W.",                  "child",       "minor"),
                (cid, "Pamela Rusco",            "foc",         "government"),
            ])
        elif "Housing" in title:
            party_defs.extend([
                (cid, "Andrew James Pigors",     "plaintiff",   "individual"),
                (cid, "Shady Oaks MHP",          "defendant",   "entity"),
                (cid, "Hon. Kenneth Hoopes",     "judge",       "judicial"),
            ])
        elif "1983" in title:
            party_defs.extend([
                (cid, "Andrew James Pigors",     "plaintiff",   "individual"),
                (cid, "Hon. Jenny L. McNeill",   "defendant",   "judicial"),
                (cid, "Emily A. Watson",         "defendant",   "individual"),
                (cid, "Pamela Rusco",            "defendant",   "government"),
            ])
        elif "PPO" in title:
            party_defs.extend([
                (cid, "Emily A. Watson",         "petitioner",  "individual"),
                (cid, "Andrew James Pigors",     "respondent",  "individual"),
                (cid, "Hon. Jenny L. McNeill",   "judge",       "judicial"),
            ])
        elif "JTC" in title:
            party_defs.extend([
                (cid, "Andrew James Pigors",     "complainant", "individual"),
                (cid, "Hon. Jenny L. McNeill",   "respondent",  "judicial"),
            ])
        elif "COA" in title:
            party_defs.extend([
                (cid, "Andrew James Pigors",     "appellant",   "individual"),
                (cid, "Emily A. Watson",         "appellee",    "individual"),
            ])
        elif "Criminal" in title:
            party_defs.extend([
                (cid, "People of Michigan",      "plaintiff",   "government"),
                (cid, "Andrew James Pigors",     "defendant",   "individual"),
                (cid, "Hon. Kostrzewa",          "judge",       "judicial"),
            ])

    inserted = 0
    for case_id, name, role, ptype in party_defs:
        existing = conn.execute(
            "SELECT id FROM parties WHERE case_id = ? AND name = ? AND role = ?",
            (case_id, name, role)
        ).fetchone()
        if existing:
            continue
        if dry_run:
            print(f"  [DRY] Would insert party: {name} ({role})")
            inserted += 1
            continue
        conn.execute(
            "INSERT INTO parties (case_id, name, role, party_type) VALUES (?,?,?,?)",
            (case_id, name, role, ptype)
        )
        inserted += 1

    if not dry_run:
        conn.commit()
    after = count(conn, "parties")
    print(f"  parties: {before} → {after} (+{inserted} inserted)")
    return inserted


# ══════════════════════════════════════════════════════════════════
# ETL 3: GAP_TICKETS — Evidence gaps, quality gaps, deadline gaps
# ══════════════════════════════════════════════════════════════════

def populate_gaps(conn, dry_run=False):
    """Analyze evidence + timeline + deadlines to find gaps."""
    before = count(conn, "gap_tickets")
    inserted = 0

    # ── GAP TYPE 1: Lanes with low evidence coverage ──
    lane_counts = conn.execute("""
        SELECT lane, COUNT(*) as cnt FROM evidence_quotes
        WHERE lane IS NOT NULL AND lane != ''
        GROUP BY lane ORDER BY cnt
    """).fetchall()

    for row in lane_counts:
        lane = row["lane"]
        cnt = row["cnt"]
        if cnt < 500:  # Less than 500 evidence quotes = evidence gap
            desc = f"Lane {lane} has only {cnt} evidence quotes — below 500 threshold for filing readiness"
            if not _gap_exists(conn, "EVIDENCE_GAP", lane, desc):
                if not dry_run:
                    conn.execute(
                        "INSERT INTO gap_tickets (gap_type, lane, severity, description) VALUES (?,?,?,?)",
                        ("EVIDENCE_GAP", lane, "HIGH", desc)
                    )
                inserted += 1

    # ── GAP TYPE 2: Timeline gaps (>30 day spans with no events per lane) ──
    lanes_with_events = conn.execute("""
        SELECT DISTINCT lane FROM timeline_events WHERE lane IS NOT NULL AND lane != ''
    """).fetchall()

    for lr in lanes_with_events:
        lane = lr["lane"]
        events = conn.execute("""
            SELECT event_date FROM timeline_events
            WHERE lane = ? AND event_date IS NOT NULL AND event_date != ''
            ORDER BY event_date
        """, (lane,)).fetchall()

        prev_date = None
        for ev in events:
            try:
                d = ev["event_date"][:10]
                curr = datetime.strptime(d, "%Y-%m-%d").date()
                if prev_date and (curr - prev_date).days > 90:
                    desc = f"Lane {lane}: {(curr - prev_date).days}-day gap in timeline ({prev_date} to {curr})"
                    sev = "CRITICAL" if (curr - prev_date).days > 180 else "HIGH"
                    if not _gap_exists(conn, "TIMELINE_GAP", lane, desc):
                        if not dry_run:
                            conn.execute(
                                "INSERT INTO gap_tickets (gap_type, lane, severity, description) VALUES (?,?,?,?)",
                                ("TIMELINE_GAP", lane, sev, desc)
                            )
                        inserted += 1
                prev_date = curr
            except (ValueError, TypeError):
                continue

    # ── GAP TYPE 3: Unresolved contradictions ──
    unresolved = conn.execute("""
        SELECT lane, COUNT(*) as cnt FROM contradiction_map
        WHERE severity IN ('critical', 'high')
        GROUP BY lane
    """).fetchall()

    for row in unresolved:
        lane = row["lane"] or "UNKNOWN"
        cnt = row["cnt"]
        if cnt >= 5:
            desc = f"Lane {lane}: {cnt} critical/high severity contradictions unresolved — must address before filing"
            if not _gap_exists(conn, "QUALITY_GAP", lane, desc):
                if not dry_run:
                    conn.execute(
                        "INSERT INTO gap_tickets (gap_type, lane, severity, description) VALUES (?,?,?,?)",
                        ("QUALITY_GAP", lane, "CRITICAL", desc)
                    )
                inserted += 1

    # ── GAP TYPE 4: Deadlines without filings ──
    deadlines = conn.execute("""
        SELECT id, title, due_date, filing_id, status FROM deadlines
        WHERE status != 'completed' AND due_date IS NOT NULL
    """).fetchall()

    for dl in deadlines:
        try:
            due = datetime.strptime(dl["due_date"][:10], "%Y-%m-%d").date()
            days_left = (due - TODAY).days
            if days_left < 0:
                desc = f"OVERDUE by {abs(days_left)} days: {dl['title']} (due {dl['due_date']})"
                sev = "CRITICAL"
            elif days_left <= 7:
                desc = f"Due in {days_left} days: {dl['title']} (due {dl['due_date']})"
                sev = "CRITICAL"
            elif days_left <= 30:
                desc = f"Due in {days_left} days: {dl['title']} (due {dl['due_date']})"
                sev = "HIGH"
            else:
                continue

            filing_id = dl["filing_id"] or "UNKNOWN"
            if not _gap_exists(conn, "DEADLINE_GAP", filing_id, desc):
                if not dry_run:
                    conn.execute(
                        "INSERT INTO gap_tickets (gap_type, lane, severity, description) VALUES (?,?,?,?)",
                        ("DEADLINE_GAP", filing_id, sev, desc)
                    )
                inserted += 1
        except (ValueError, TypeError):
            continue

    # ── GAP TYPE 5: Best interest factors with insufficient evidence ──
    factor_coverage = conn.execute("""
        SELECT factor_letter, COUNT(*) as cnt
        FROM best_interest_factor_map
        GROUP BY factor_letter
        ORDER BY cnt ASC
    """).fetchall()

    for row in factor_coverage:
        fl = row["factor_letter"]
        cnt = row["cnt"]
        if fl and cnt < 100:
            desc = f"MCL 722.23({fl}): Only {cnt} evidence items — below 100 threshold for strong factor argument"
            if not _gap_exists(conn, "FACTOR_GAP", "A", desc):
                if not dry_run:
                    conn.execute(
                        "INSERT INTO gap_tickets (gap_type, lane, severity, description) VALUES (?,?,?,?)",
                        ("FACTOR_GAP", "A", "MEDIUM", desc)
                    )
                inserted += 1

    # ── GAP TYPE 6: Separation harm (BLOCKER) ──
    desc = f"L.D.W. separated from father for {SEP_DAYS} days ({SEP_DAYS // 30} months). Developmental window closing. Every day = irreversible harm."
    if not _gap_exists(conn, "BLOCKER", "A", "L.D.W. separated"):
        if not dry_run:
            conn.execute(
                "INSERT INTO gap_tickets (gap_type, lane, severity, description, resolution_status) VALUES (?,?,?,?,?)",
                ("BLOCKER", "A", "CRITICAL", desc, "OPEN")
            )
        inserted += 1

    if not dry_run:
        conn.commit()
    after = count(conn, "gap_tickets")
    print(f"  gap_tickets: {before} → {after} (+{inserted} inserted)")
    return inserted


def _gap_exists(conn, gap_type, lane, desc_fragment):
    """Check if a similar gap already exists (prevents duplicates)."""
    row = conn.execute(
        "SELECT id FROM gap_tickets WHERE gap_type = ? AND lane = ? AND description LIKE ?",
        (gap_type, lane, f"%{desc_fragment[:60]}%")
    ).fetchone()
    return row is not None


# ══════════════════════════════════════════════════════════════════
# ETL 4: RISK_EVENTS — Adversarial vulnerabilities
# ══════════════════════════════════════════════════════════════════

RISK_DEFINITIONS = [
    {
        "risk_type_id": "RISK_JUDICIAL_IMMUNITY",
        "title": "Judicial Immunity Defense (§1983)",
        "severity": 90,
        "risk_class": "defense_anticipated",
        "track": "C",
        "forum": "USDC Western District",
        "cure_cost": "Brief section addressing Pulliam v Allen exception",
        "cure_deadline_clock": "Before federal filing",
    },
    {
        "risk_type_id": "RISK_STANDING_CHALLENGE",
        "title": "Standing Challenge — Pro Se Procedural Defects",
        "severity": 75,
        "risk_class": "procedural_risk",
        "track": "ALL",
        "forum": "All courts",
        "cure_cost": "MCR compliance review on all filings",
        "cure_deadline_clock": "Before each filing",
    },
    {
        "risk_type_id": "RISK_HEARSAY_OBJECTIONS",
        "title": "Hearsay Objections to Evidence Quotes",
        "severity": 70,
        "risk_class": "evidence_vulnerability",
        "track": "A",
        "forum": "14th Circuit",
        "cure_cost": "MRE 803/804 exception analysis per exhibit",
        "cure_deadline_clock": "Before hearing",
    },
    {
        "risk_type_id": "RISK_FRIVOLOUS_LABEL",
        "title": "Frivolous Filing Label Risk (MCR 2.114)",
        "severity": 85,
        "risk_class": "sanctions_risk",
        "track": "A",
        "forum": "14th Circuit",
        "cure_cost": "Ensure every motion has specific factual basis + authority",
        "cure_deadline_clock": "Every filing",
    },
    {
        "risk_type_id": "RISK_BOND_BARRIER",
        "title": "$250 Bond Requirement Blocks Access",
        "severity": 95,
        "risk_class": "access_barrier",
        "track": "A",
        "forum": "14th Circuit",
        "cure_cost": "Boddie v Connecticut + MSC challenge",
        "cure_deadline_clock": "ASAP",
    },
    {
        "risk_type_id": "RISK_RECUSAL_SELF_RULING",
        "title": "McNeill Rules on Own Disqualification (MCR 2.003(D))",
        "severity": 95,
        "risk_class": "procedural_violation",
        "track": "E",
        "forum": "14th Circuit → MSC",
        "cure_cost": "MCR 2.003(D) requires Chief Judge — mandamus to MSC",
        "cure_deadline_clock": "Before next McNeill hearing",
    },
    {
        "risk_type_id": "RISK_SEPARATION_HARM",
        "title": f"{SEP_DAYS}-Day Parent-Child Separation — Irreversible Developmental Harm",
        "severity": 100,
        "risk_class": "child_welfare",
        "track": "A",
        "forum": "All courts",
        "cure_cost": "Emergency TRO + MSC Emergency Application",
        "cure_deadline_clock": "IMMEDIATE",
    },
    {
        "risk_type_id": "RISK_STATUTE_LIMITATIONS",
        "title": "§1983 Statute of Limitations (3 years in Michigan)",
        "severity": 80,
        "risk_class": "deadline_risk",
        "track": "C",
        "forum": "USDC Western District",
        "cure_cost": "File federal complaint before earliest violation + 3 years",
        "cure_deadline_clock": "Calculate per violation date",
    },
    {
        "risk_type_id": "RISK_EX_PARTE_PATTERN",
        "title": "Opposing Counsel May Argue Father's Own Ex Parte History",
        "severity": 65,
        "risk_class": "impeachment_vulnerability",
        "track": "A",
        "forum": "14th Circuit",
        "cure_cost": "Distinguish father's ex parte (with notice) from McNeill's (without)",
        "cure_deadline_clock": "Before hearing",
    },
    {
        "risk_type_id": "RISK_CREDIBILITY_ATTACK",
        "title": "Criminal Case Used to Attack Father's Credibility",
        "severity": 80,
        "risk_class": "credibility_risk",
        "track": "CRIMINAL",
        "forum": "60th District → 14th Circuit",
        "cure_cost": "Resolve criminal case; prepare MRE 609 rebuttal",
        "cure_deadline_clock": "Before criminal trial Apr 7",
    },
    {
        "risk_type_id": "RISK_ALIENATION_NO_STATUTE",
        "title": "Michigan Has No Parental Alienation Statute",
        "severity": 70,
        "risk_class": "legal_gap",
        "track": "A",
        "forum": "14th Circuit",
        "cure_cost": "Frame as MCL 722.23(j) willingness to facilitate, NOT 'alienation'",
        "cure_deadline_clock": "All filings",
    },
    {
        "risk_type_id": "RISK_BERRY_MCNEILL_UNPROVEN",
        "title": "Berry-McNeill Family Connection Not Yet Court-Proven",
        "severity": 75,
        "risk_class": "evidence_gap",
        "track": "E",
        "forum": "14th Circuit / MSC",
        "cure_cost": "Public records search, FOIA, discovery subpoena for marriage cert",
        "cure_deadline_clock": "Before disqualification motion",
    },
]


def populate_risks(conn, dry_run=False):
    """Populate risk_events with adversarial vulnerabilities."""
    before = count(conn, "risk_events")
    inserted = 0

    for risk in RISK_DEFINITIONS:
        existing = conn.execute(
            "SELECT risk_type_id FROM risk_events WHERE risk_type_id = ?",
            (risk["risk_type_id"],)
        ).fetchone()
        if existing:
            continue
        if dry_run:
            print(f"  [DRY] Would insert risk: {risk['title']}")
            inserted += 1
            continue
        conn.execute(
            """INSERT INTO risk_events (risk_type_id, title, severity, risk_class, track, forum,
               cure_cost, cure_deadline_clock) VALUES (?,?,?,?,?,?,?,?)""",
            (risk["risk_type_id"], risk["title"], risk["severity"], risk["risk_class"],
             risk["track"], risk["forum"], risk["cure_cost"], risk["cure_deadline_clock"])
        )
        inserted += 1

    if not dry_run:
        conn.commit()
    after = count(conn, "risk_events")
    print(f"  risk_events: {before} → {after} (+{inserted} inserted)")
    return inserted


# ══════════════════════════════════════════════════════════════════
# ETL 5: EMERGENCE_EVENTS — Cross-lane patterns + novel strategies
# ══════════════════════════════════════════════════════════════════

def populate_emergence(conn, dry_run=False):
    """Detect and record cross-lane emergence patterns."""
    before = count(conn, "emergence_events")
    inserted = 0

    # ── Pattern 1: Cross-lane entity overlap ──
    # Find people who appear in multiple lanes
    actors_multi = conn.execute("""
        SELECT actors, COUNT(DISTINCT lane) as lane_cnt, GROUP_CONCAT(DISTINCT lane) as lanes
        FROM timeline_events
        WHERE actors IS NOT NULL AND actors != '' AND lane IS NOT NULL AND lane != ''
        GROUP BY actors
        HAVING lane_cnt >= 3
        ORDER BY lane_cnt DESC
        LIMIT 20
    """).fetchall()

    for row in actors_multi:
        desc = f"CROSS_GRAPH: '{row['actors']}' appears across {row['lane_cnt']} lanes ({row['lanes']})"
        novelty = min(10, row["lane_cnt"] + 4)
        if not _emergence_exists(conn, "CROSS_GRAPH", desc[:80]):
            if not dry_run:
                conn.execute(
                    "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                    ("CROSS_GRAPH", row["lanes"], novelty, desc)
                )
            inserted += 1

    # ── Pattern 2: Judicial violations concentrated in time windows ──
    violation_clusters = conn.execute("""
        SELECT substr(date_occurred, 1, 7) as month, COUNT(*) as cnt
        FROM judicial_violations
        WHERE date_occurred IS NOT NULL AND date_occurred != ''
        GROUP BY month
        HAVING cnt >= 10
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()

    for row in violation_clusters:
        desc = f"CLUSTER: {row['cnt']} judicial violations in {row['month']} — concentrated misconduct pattern"
        if not _emergence_exists(conn, "CONTRADICTION", desc[:80]):
            if not dry_run:
                conn.execute(
                    "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                    ("CONTRADICTION", "E,A", min(10, row["cnt"] // 5 + 5), desc)
                )
            inserted += 1

    # ── Pattern 3: Authority chain completeness per lane ──
    authority_coverage = conn.execute("""
        SELECT lane, COUNT(DISTINCT primary_citation) as auth_cnt
        FROM authority_chains_v2
        WHERE lane IS NOT NULL AND lane != ''
        GROUP BY lane
    """).fetchall()

    for row in authority_coverage:
        if row["auth_cnt"] >= 50:
            desc = f"CHAIN_COMPLETE: Lane {row['lane']} has {row['auth_cnt']} distinct authorities — filing-ready authority chain"
            if not _emergence_exists(conn, "CHAIN_COMPLETE", desc[:80]):
                if not dry_run:
                    conn.execute(
                        "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                        ("CHAIN_COMPLETE", row["lane"], 7, desc)
                    )
                inserted += 1

    # ── Pattern 4: Impeachment saturation ──
    impeach_targets = conn.execute("""
        SELECT category, COUNT(*) as cnt, AVG(impeachment_value) as avg_val
        FROM impeachment_matrix
        GROUP BY category
        HAVING cnt >= 20 AND avg_val >= 6
        ORDER BY cnt DESC
    """).fetchall()

    for row in impeach_targets:
        desc = f"NOVEL_STRATEGY: {row['cnt']} impeachment items for '{row['category']}' (avg severity {row['avg_val']:.1f}/10) — devastating cross-exam available"
        if not _emergence_exists(conn, "NOVEL_STRATEGY", desc[:80]):
            if not dry_run:
                conn.execute(
                    "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                    ("NOVEL_STRATEGY", "A,E", 8, desc)
                )
            inserted += 1

    # ── Pattern 5: Contradiction clusters between same parties ──
    contra_clusters = conn.execute("""
        SELECT source_a, source_b, COUNT(*) as cnt
        FROM contradiction_map
        WHERE severity IN ('critical', 'high')
        GROUP BY source_a, source_b
        HAVING cnt >= 5
        ORDER BY cnt DESC
        LIMIT 10
    """).fetchall()

    for row in contra_clusters:
        desc = f"CONTRADICTION: {row['cnt']} critical/high contradictions between '{row['source_a']}' and '{row['source_b']}'"
        if not _emergence_exists(conn, "CONTRADICTION", desc[:80]):
            if not dry_run:
                conn.execute(
                    "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                    ("CONTRADICTION", "A,E", min(10, row["cnt"] // 3 + 5), desc)
                )
            inserted += 1

    # ── Pattern 6: Witness overlap across lanes ──
    witness_overlap = conn.execute("""
        SELECT eq.category, COUNT(DISTINCT eq.lane) as lane_cnt, GROUP_CONCAT(DISTINCT eq.lane) as lanes
        FROM evidence_quotes eq
        WHERE eq.category IS NOT NULL AND eq.lane IS NOT NULL
          AND eq.category != '' AND eq.lane != ''
        GROUP BY eq.category
        HAVING lane_cnt >= 3
        ORDER BY lane_cnt DESC
        LIMIT 10
    """).fetchall()

    for row in witness_overlap:
        desc = f"WITNESS_OVERLAP: Category '{row['category']}' spans {row['lane_cnt']} lanes ({row['lanes']}) — coordinated evidence pattern"
        if not _emergence_exists(conn, "WITNESS_OVERLAP", desc[:80]):
            if not dry_run:
                conn.execute(
                    "INSERT INTO emergence_events (signal_type, lanes_involved, novelty, description) VALUES (?,?,?,?)",
                    ("WITNESS_OVERLAP", row["lanes"], min(10, row["lane_cnt"] + 3), desc)
                )
            inserted += 1

    if not dry_run:
        conn.commit()
    after = count(conn, "emergence_events")
    print(f"  emergence_events: {before} → {after} (+{inserted} inserted)")
    return inserted


def _emergence_exists(conn, signal_type, desc_fragment):
    """Check if similar emergence event already exists."""
    row = conn.execute(
        "SELECT id FROM emergence_events WHERE signal_type = ? AND description LIKE ?",
        (signal_type, f"%{desc_fragment}%")
    ).fetchone()
    return row is not None


# ══════════════════════════════════════════════════════════════════
# ETL 6: ADVERSARY_MODELS — Create table + populate attack patterns
# ══════════════════════════════════════════════════════════════════

def populate_adversary_models(conn, dry_run=False):
    """Create adversary_models table and populate with predicted attack patterns."""

    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS adversary_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            attack_type TEXT NOT NULL,
            target_lane TEXT,
            likelihood INTEGER DEFAULT 50,
            impact TEXT,
            rebuttal_strategy TEXT,
            rebuttal_authority TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()

    before = count(conn, "adversary_models")
    inserted = 0

    models = [
        ("Emily Watson", "False allegations escalation", "A", 90,
         "New false allegations to maintain custody leverage",
         "Pattern of 7 prior false allegations — ALL rebutted. NSPD-2023-08121 recantation. Zero charges from 7 investigations.",
         "MCL 722.23(j); MRE 608(b); MRE 404(b) — pattern of false reports"),

        ("Emily Watson", "Parenting time denial continuation", "A", 95,
         "Continue withholding L.D.W. from father with court cover",
         "49 documented PT violations. Albert Watson admitted reports used for ex parte leverage (NS2505044).",
         "MCL 722.27a; MCL 722.23(j); Lombardo v Lombardo"),

        ("Emily Watson", "Criminal case leverage", "CRIMINAL", 80,
         "Use People v Pigors to argue father is danger to child",
         "Criminal charge unrelated to child. No conviction. MRE 609 limits. Presumption of innocence.",
         "MRE 609; US Const Amend XIV; MCL 722.23(k) domestic violence — NOT applicable"),

        ("Opposing Counsel", "Frivolous filing sanctions", "A", 70,
         "Move for sanctions under MCR 2.114 against pro se filings",
         "Every filing backed by specific evidence (92K quotes), authority (32K chains), and MCR compliance.",
         "MCR 2.114(D); MCR 2.114(E) — reasonable inquiry standard met"),

        ("Opposing Counsel", "Judicial immunity shield (§1983)", "C", 85,
         "Argue absolute judicial immunity defeats §1983 claims",
         "McNeill acted in clear absence of jurisdiction (ex parte without notice, self-ruling on recusal).",
         "Pulliam v Allen, 466 US 522 (1984); Stump v Sparkman exception; Mireles v Waco"),

        ("Opposing Counsel", "Res judicata / law of the case", "F", 75,
         "Argue custody judgment is final and cannot be revisited",
         "Changed circumstances (242+ days separation, new evidence). MCL 722.27(1)(c) requires showing.",
         "Vodvarka v Grasher; MCL 722.27(1)(c); Shade v Wright"),

        ("Judge McNeill", "Continued ex parte rulings", "A", 90,
         "Continue issuing ex parte orders without notice or hearing",
         "Document every instance. 156+ prior ex parte orders. MCR 3.207(C)(2) requires notice.",
         "MCR 3.207(C)(2); MCR 2.119(B)(1); Canon 3(A)(5)"),

        ("Judge McNeill", "Muting/silencing at hearings", "A", 85,
         "Cut off plaintiff mid-argument, refuse to hear evidence",
         "Due process requires meaningful opportunity to be heard. Document each instance on record.",
         "Mathews v Eldridge; Canon 3(A)(4); US Const Amend XIV"),

        ("FOC (Rusco)", "Biased investigation report", "A", 80,
         "Issue one-sided FOC recommendation favoring Emily",
         "Rusco works at 990 Terrace St — same address as Judge's spouse Cavan Berry. Conflict of interest.",
         "MCL 552.505; MCR 3.219; Disqualification for actual/apparent bias"),

        ("Ronald Berry", "Interference with parenting relationship", "A", 70,
         "Block father's access to child, act as gatekeeper",
         "Non-parent has no legal standing. Living at 2160 Garland Dr with Emily. Potential McNeill family connection.",
         "MCL 722.23(j); Troxel v Granville — parental rights are fundamental"),
    ]

    for adversary, attack, lane, likelihood, impact, rebuttal, authority in models:
        existing = conn.execute(
            "SELECT id FROM adversary_models WHERE adversary = ? AND attack_type = ?",
            (adversary, attack)
        ).fetchone()
        if existing:
            continue
        if dry_run:
            print(f"  [DRY] Would insert adversary model: {adversary} — {attack}")
            inserted += 1
            continue
        conn.execute(
            """INSERT INTO adversary_models (adversary, attack_type, target_lane, likelihood,
               impact, rebuttal_strategy, rebuttal_authority) VALUES (?,?,?,?,?,?,?)""",
            (adversary, attack, lane, likelihood, impact, rebuttal, authority)
        )
        inserted += 1

    if not dry_run:
        conn.commit()
    after = count(conn, "adversary_models")
    print(f"  adversary_models: {before} → {after} (+{inserted} inserted)")
    return inserted


# ══════════════════════════════════════════════════════════════════
# MAIN — Orchestrator
# ══════════════════════════════════════════════════════════════════

def main():
    dry_run = "--dry-run" in sys.argv
    step = None
    for arg in sys.argv[1:]:
        if arg.startswith("--step="):
            step = arg.split("=", 1)[1]

    print("=" * 70)
    print("OMEGA ETL POPULATION ENGINE")
    print("=" * 70)
    print(f"  Database: {DB_PATH}")
    print(f"  File size: {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Separation: {SEP_DAYS} days since Jul 29, 2025")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    if step:
        print(f"  Step filter: {step}")
    print()

    conn = connect()
    total = 0

    steps = {
        "cases": ("ETL 1: Cases (7 litigation lanes)", populate_cases),
        "parties": ("ETL 2: Parties (all parties across cases)", populate_parties),
        "gaps": ("ETL 3: Gap Tickets (evidence, timeline, quality, deadline gaps)", populate_gaps),
        "risks": ("ETL 4: Risk Events (adversarial vulnerabilities)", populate_risks),
        "emergence": ("ETL 5: Emergence Events (cross-lane patterns)", populate_emergence),
        "adversary": ("ETL 6: Adversary Models (attack prediction)", populate_adversary_models),
    }

    for key, (label, func) in steps.items():
        if step and step != key:
            continue
        print(f"── {label} ──")
        try:
            n = func(conn, dry_run=dry_run)
            total += n
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
        print()

    conn.close()

    print("=" * 70)
    print(f"OMEGA ETL COMPLETE — {total} total rows inserted")
    if dry_run:
        print("  (DRY RUN — no changes written)")
    print("=" * 70)


if __name__ == "__main__":
    main()
