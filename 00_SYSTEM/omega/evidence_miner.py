#!/usr/bin/env python3
"""
Evidence Mining and Impeachment Package Engine
===============================================
Scans litigation_context.db for patterns, damaging quotes,
evidence gaps, and authority chains. Writes results to omega_* tables.
"""

import sys
import os
import sqlite3
import re
import hashlib
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
BATCH_SIZE = 10_000

# ── Keyword dictionaries ────────────────────────────────────────────

PATTERN_CATEGORIES = {
    "financial": [
        "income", "payment", "bank", "tax", "money", "asset", "employment",
        "wage", "salary", "debt", "fraud", "account", "finance", "support",
    ],
    "custodial_interference": [
        "visit", "parenting time", "denied", "cancel", "refuse", "access",
        "custody", "placement", "overnight", "schedule", "withhold",
    ],
    "judicial_misconduct": [
        "ex parte", "bias", "prejudice", "abuse of discretion",
        "due process", "impartial", "recusal", "misconduct",
    ],
    "attorney_ethics": [
        "conflict", "misrepresent", "incompetent", "malpractice",
        "ethics", "ineffective", "disqualif", "sanction",
    ],
}

ADVERSARIES = ["Watson", "Berry", "Barnes", "Martini", "McNeill"]

DAMAGE_SIGNALS = [
    (r"\badmit", 4),
    (r"\bconfess", 5),
    (r"\blie[ds]?\b", 4),
    (r"\bfalse\b", 3),
    (r"\bfraud", 4),
    (r"\bcontradict", 4),
    (r"\bviolat", 3),
    (r"\bfail(?:ed|ure)?\b", 2),
    (r"\brefus", 3),
    (r"\bdeni(?:ed|al)\b", 3),
    (r"\billegal", 3),
    (r"\bunlawful", 3),
    (r"\bwithout\s+(?:notice|hearing|authority|consent)", 4),
    (r"\bex\s*parte", 4),
    (r"\babuse", 3),
    (r"\bperjur", 5),
    (r"\bmisrepresent", 4),
    (r"\bconceal", 3),
    (r"\bdestroy", 3),
    (r"\bintimid", 3),
]

CITATION_PATTERNS = [
    (r"MCL\s*[\d]+\.[\d]+[a-z]*", "MCL"),
    (r"MCR\s*[\d]+\.[\d]+", "MCR"),
    (r"\d+\s+USC\s*§?\s*\d+", "USC"),
    (r"\d+\s+CFR\s*§?\s*\d+", "CFR"),
    (r"42\s+USC\s*§?\s*1983", "USC_1983"),
    (r"[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+", "CASE_LAW"),
    (r"Canon\s+\d+", "JUDICIAL_CANON"),
    (r"Const(?:itution)?\s+(?:1963\s+)?Art(?:icle)?\s+\d+", "CONSTITUTION"),
    (r"MRPC\s*[\d]+\.[\d]+", "MRPC"),
]


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def create_output_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS omega_evidence_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            keyword TEXT NOT NULL,
            match_count INTEGER DEFAULT 0,
            sample_quote_id INTEGER,
            sample_text TEXT,
            mined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS omega_damaging_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adversary TEXT NOT NULL,
            quote_id INTEGER,
            quote_text TEXT,
            speaker TEXT,
            damage_score INTEGER DEFAULT 0,
            damage_signals TEXT,
            evidence_category TEXT,
            date_ref TEXT,
            mined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS omega_intelligence_gaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_id TEXT,
            action_name TEXT,
            claim_category TEXT,
            supporting_quotes INTEGER DEFAULT 0,
            gap_severity TEXT,
            research_ticket TEXT,
            mined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS omega_authority_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citation TEXT NOT NULL,
            citation_type TEXT,
            quote_id INTEGER,
            quote_snippet TEXT,
            evidence_category TEXT,
            mined_at TEXT
        );
    """)
    # Clear previous runs
    for tbl in [
        "omega_evidence_patterns", "omega_damaging_quotes",
        "omega_intelligence_gaps", "omega_authority_inventory",
    ]:
        conn.execute(f"DELETE FROM {tbl}")
    conn.commit()


# ── 1. Pattern Detection ────────────────────────────────────────────

def mine_patterns(conn):
    print("\n" + "=" * 60)
    print("  PHASE 1: Pattern Detection")
    print("=" * 60)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence_quotes")
    total = cur.fetchone()[0]
    print(f"  Scanning {total:,} evidence quotes in batches of {BATCH_SIZE:,}...")

    # category -> keyword -> { count, sample_id, sample_text }
    results = {}
    for cat, keywords in PATTERN_CATEGORIES.items():
        for kw in keywords:
            results[(cat, kw)] = {"count": 0, "sample_id": None, "sample_text": None}

    offset = 0
    batches = 0
    while offset < total:
        cur.execute(
            "SELECT id, quote_text FROM evidence_quotes LIMIT ? OFFSET ?",
            (BATCH_SIZE, offset),
        )
        rows = cur.fetchall()
        if not rows:
            break
        for row_id, text in rows:
            if not text:
                continue
            text_lower = text.lower()
            for cat, keywords in PATTERN_CATEGORIES.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        entry = results[(cat, kw)]
                        entry["count"] += 1
                        if entry["sample_id"] is None:
                            entry["sample_id"] = row_id
                            entry["sample_text"] = text[:300]
        offset += BATCH_SIZE
        batches += 1
        pct = min(100, int(offset / total * 100))
        print(f"    Batch {batches}: {pct}% complete...")

    now = datetime.utcnow().isoformat()
    inserts = []
    for (cat, kw), data in results.items():
        if data["count"] > 0:
            inserts.append((
                cat, kw, data["count"],
                data["sample_id"], data["sample_text"], now,
            ))

    conn.executemany(
        """INSERT INTO omega_evidence_patterns
           (category, keyword, match_count, sample_quote_id, sample_text, mined_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        inserts,
    )
    conn.commit()

    print(f"\n  Pattern results saved: {len(inserts)} keyword hits")
    for cat in PATTERN_CATEGORIES:
        cat_total = sum(
            v["count"] for (c, _), v in results.items() if c == cat
        )
        print(f"    {cat:<25} {cat_total:>8,} matches")
    return results


# ── 2. Most Damaging Quotes ─────────────────────────────────────────

def _score_damage(text):
    score = 0
    signals = []
    if not text:
        return 0, ""
    text_lower = text.lower()
    for pattern, weight in DAMAGE_SIGNALS:
        if re.search(pattern, text_lower):
            score += weight
            signals.append(pattern.replace("\\b", "").replace("\\s+", " "))
    # Bonus for length (longer = more detail = more damaging)
    if len(text) > 500:
        score += 2
    elif len(text) > 200:
        score += 1
    return score, "; ".join(signals)


def mine_damaging_quotes(conn):
    print("\n" + "=" * 60)
    print("  PHASE 2: Most Damaging Quotes per Adversary")
    print("=" * 60)

    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    grand_total = 0

    for adversary in ADVERSARIES:
        print(f"\n  Scanning for: {adversary}")
        # Use LIKE search across quote_text and speaker for this adversary
        cur.execute(
            """SELECT id, quote_text, speaker, evidence_category, date_ref
               FROM evidence_quotes
               WHERE quote_text LIKE ? OR speaker LIKE ?
               LIMIT 50000""",
            (f"%{adversary}%", f"%{adversary}%"),
        )
        rows = cur.fetchall()
        print(f"    Found {len(rows):,} mentions")

        scored = []
        for qid, text, speaker, ecat, dref in rows:
            score, signals = _score_damage(text)
            if score > 0:
                scored.append((score, signals, qid, text, speaker, ecat, dref))

        scored.sort(key=lambda x: x[0], reverse=True)
        top10 = scored[:10]

        inserts = []
        for score, signals, qid, text, speaker, ecat, dref in top10:
            inserts.append((
                adversary, qid, (text or "")[:1000], speaker,
                score, signals, ecat, dref, now,
            ))

        conn.executemany(
            """INSERT INTO omega_damaging_quotes
               (adversary, quote_id, quote_text, speaker,
                damage_score, damage_signals, evidence_category, date_ref, mined_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            inserts,
        )
        grand_total += len(inserts)
        if top10:
            print(f"    Top damage score: {top10[0][0]}  |  Saved {len(inserts)} quotes")
        else:
            print(f"    No damaging quotes found")

    conn.commit()
    print(f"\n  Total damaging quotes saved: {grand_total}")


# ── 3. Gap Discovery ────────────────────────────────────────────────

def mine_gaps(conn):
    print("\n" + "=" * 60)
    print("  PHASE 3: Intelligence Gap Discovery")
    print("=" * 60)

    cur = conn.cursor()

    # Get high-OMEGA actions (top tier)
    cur.execute(
        """SELECT action_id, name, total_score
           FROM omega_scores ORDER BY total_score DESC"""
    )
    actions = cur.fetchall()
    print(f"  Analyzing {len(actions)} OMEGA actions for evidence gaps...")

    # Get claim categories
    cur.execute(
        "SELECT DISTINCT classification FROM claims WHERE classification IS NOT NULL"
    )
    categories = [r[0] for r in cur.fetchall()]

    # Count quotes per category
    cat_quote_counts = {}
    for cat in categories:
        like_term = f"%{cat}%"
        cur.execute(
            """SELECT COUNT(*) FROM evidence_quotes
               WHERE evidence_category LIKE ? OR quote_text LIKE ?
               LIMIT 1""",
            (like_term, like_term),
        )
        cat_quote_counts[cat] = cur.fetchone()[0]

    # For each action, check coverage against related claim categories
    now = datetime.utcnow().isoformat()
    inserts = []
    weak_count = 0

    for action_id, action_name, score in actions:
        # Find claims that map to this action (keyword match on action name)
        action_words = set(action_name.lower().replace("-", " ").split())
        # Remove common filler words
        action_words -= {"the", "a", "an", "to", "for", "of", "and", "in", "on"}

        for cat in categories:
            cat_lower = cat.lower().replace("_", " ")
            # Check if category relates to this action
            overlap = action_words & set(cat_lower.split())
            if not overlap and not any(w in cat_lower for w in action_words):
                continue

            count = cat_quote_counts.get(cat, 0)
            if count < 3:
                severity = "CRITICAL" if count == 0 else "HIGH" if count < 2 else "MODERATE"
                ticket = (
                    f"RESEARCH NEEDED: Action '{action_name}' (score={score}) "
                    f"has only {count} supporting quotes for category '{cat}'. "
                    f"Gather depositions, discovery documents, or public records."
                )
                inserts.append((
                    action_id, action_name, cat, count, severity, ticket, now,
                ))
                weak_count += 1

    # Also scan claims directly for weak evidence support
    cur.execute(
        """SELECT classification, COUNT(*) as cnt
           FROM claims
           GROUP BY classification"""
    )
    claim_counts = cur.fetchall()

    for cat, claim_cnt in claim_counts:
        eq_count = cat_quote_counts.get(cat, 0)
        if eq_count < 3 and claim_cnt > 0:
            severity = "CRITICAL" if eq_count == 0 else "HIGH"
            ticket = (
                f"GAP: {claim_cnt} claims in '{cat}' supported by only "
                f"{eq_count} evidence quotes. Priority evidence collection needed."
            )
            # Avoid duplicates
            exists = any(r[2] == cat and r[0] is None for r in inserts)
            if not exists:
                inserts.append((
                    None, None, cat, eq_count, severity, ticket, now,
                ))

    conn.executemany(
        """INSERT INTO omega_intelligence_gaps
           (action_id, action_name, claim_category, supporting_quotes,
            gap_severity, research_ticket, mined_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        inserts,
    )
    conn.commit()
    print(f"  Gaps identified: {len(inserts)}")
    sev_counts = defaultdict(int)
    for row in inserts:
        sev_counts[row[4]] += 1
    for sev in ["CRITICAL", "HIGH", "MODERATE"]:
        if sev_counts[sev]:
            print(f"    {sev:<12} {sev_counts[sev]:>4}")


# ── 4. Authority Chain ──────────────────────────────────────────────

def mine_authorities(conn):
    print("\n" + "=" * 60)
    print("  PHASE 4: Authority Chain / Citation Inventory")
    print("=" * 60)

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM evidence_quotes")
    total = cur.fetchone()[0]
    print(f"  Scanning {total:,} quotes for legal citations...")

    # citation_text -> { type, count, sample_qid, sample_snippet }
    inventory = {}
    offset = 0
    batches = 0

    while offset < total:
        cur.execute(
            "SELECT id, quote_text, evidence_category FROM evidence_quotes LIMIT ? OFFSET ?",
            (BATCH_SIZE, offset),
        )
        rows = cur.fetchall()
        if not rows:
            break

        for qid, text, ecat in rows:
            if not text:
                continue
            for pattern, ctype in CITATION_PATTERNS:
                matches = re.findall(pattern, text)
                for m in matches:
                    key = m.strip()
                    if len(key) < 5:
                        continue
                    if key not in inventory:
                        snippet = text[:200]
                        inventory[key] = {
                            "type": ctype,
                            "qid": qid,
                            "snippet": snippet,
                            "ecat": ecat,
                            "count": 0,
                        }
                    inventory[key]["count"] += 1

        offset += BATCH_SIZE
        batches += 1
        pct = min(100, int(offset / total * 100))
        print(f"    Batch {batches}: {pct}% complete...")

    now = datetime.utcnow().isoformat()
    inserts = []
    for cite, data in inventory.items():
        inserts.append((
            cite, data["type"], data["qid"],
            data["snippet"], data["ecat"], now,
        ))

    conn.executemany(
        """INSERT INTO omega_authority_inventory
           (citation, citation_type, quote_id, quote_snippet, evidence_category, mined_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        inserts,
    )
    conn.commit()

    print(f"\n  Unique citations found: {len(inventory)}")
    type_counts = defaultdict(int)
    for data in inventory.values():
        type_counts[data["type"]] += data["count"]
    for ctype, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {ctype:<20} {cnt:>6,} occurrences")


# ── Dashboard ────────────────────────────────────────────────────────

def print_dashboard(conn):
    print("\n" + "=" * 60)
    print("  EVIDENCE MINING SUMMARY DASHBOARD")
    print("=" * 60)

    cur = conn.cursor()

    # Patterns
    cur.execute("SELECT COUNT(*), SUM(match_count) FROM omega_evidence_patterns")
    kw_rows, kw_total = cur.fetchone()
    print(f"\n  Patterns:    {kw_rows or 0} keywords matched  |  {kw_total or 0:,} total hits")

    cur.execute(
        """SELECT category, SUM(match_count) as s
           FROM omega_evidence_patterns GROUP BY category ORDER BY s DESC"""
    )
    for cat, total in cur.fetchall():
        print(f"    {cat:<28} {total:>8,}")

    # Damaging quotes
    cur.execute(
        """SELECT adversary, COUNT(*), MAX(damage_score)
           FROM omega_damaging_quotes GROUP BY adversary ORDER BY MAX(damage_score) DESC"""
    )
    rows = cur.fetchall()
    print(f"\n  Damaging Quotes:")
    for adv, cnt, mx in rows:
        print(f"    {adv:<20} {cnt:>3} quotes  |  max score: {mx}")

    # Gaps
    cur.execute("SELECT COUNT(*) FROM omega_intelligence_gaps")
    gap_cnt = cur.fetchone()[0]
    cur.execute(
        """SELECT gap_severity, COUNT(*)
           FROM omega_intelligence_gaps GROUP BY gap_severity"""
    )
    print(f"\n  Intelligence Gaps: {gap_cnt} total")
    for sev, cnt in cur.fetchall():
        print(f"    {sev:<12} {cnt:>4}")

    # Authorities
    cur.execute("SELECT COUNT(*) FROM omega_authority_inventory")
    auth_cnt = cur.fetchone()[0]
    cur.execute(
        """SELECT citation_type, COUNT(*)
           FROM omega_authority_inventory GROUP BY citation_type ORDER BY COUNT(*) DESC"""
    )
    print(f"\n  Authority Inventory: {auth_cnt} unique citations")
    for ctype, cnt in cur.fetchall():
        print(f"    {ctype:<20} {cnt:>6}")

    print("\n" + "=" * 60)
    print("  Mining complete. All results in omega_* tables.")
    print("=" * 60 + "\n")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("\n  Evidence Mining and Impeachment Package Engine")
    print("  " + "─" * 50)
    print(f"  Database: {DB_PATH}")
    print(f"  Started:  {datetime.utcnow().isoformat()}Z")

    if not os.path.exists(DB_PATH):
        print(f"  ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = connect_db()
    create_output_tables(conn)

    mine_patterns(conn)
    mine_damaging_quotes(conn)
    mine_gaps(conn)
    mine_authorities(conn)
    print_dashboard(conn)

    conn.close()


if __name__ == "__main__":
    main()
