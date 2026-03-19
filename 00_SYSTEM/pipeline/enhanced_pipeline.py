#!/usr/bin/env python3
"""
OPERATION OMEGA — Phase 3: Enhanced Pipeline Runner
Deep cross-referential analysis of all evidence in litigation_context.db
"""

import sys
import os
import sqlite3
import json
import re
from datetime import datetime, timezone
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Mapping from claim classifications to evidence categories/keywords ──
# Used to cross-reference claims with evidence_quotes
CLASSIFICATION_TO_EVIDENCE = {
    "judicial_misconduct":          {"categories": {"court_order", "transcript", "general_court_doc", "TRANSCRIPT", "JUDGE_ORDER"},
                                     "keywords": ["judge", "court", "ruling", "order", "bench", "judicial"]},
    "ex_parte_violation":           {"categories": {"ppo", "court_order", "EX_PARTE_ORDER", "PPO"},
                                     "keywords": ["ex parte", "without notice", "ppo", "protection order"]},
    "evidence_factual":             {"categories": {"evidence", "discovery", "exhibit"},
                                     "keywords": ["evidence", "exhibit", "document", "record"]},
    "procedural_event":             {"categories": {"court_filing", "motion", "general_court_doc"},
                                     "keywords": ["motion", "filing", "hearing", "docket"]},
    "impeachment_credibility":      {"categories": {"transcript", "TRANSCRIPT", "evidence"},
                                     "keywords": ["credibility", "inconsistent", "impeach", "contradict"]},
    "benchbook_violation":          {"categories": {"court_order", "JUDGE_ORDER", "general_court_doc"},
                                     "keywords": ["benchbook", "canon", "rule", "mcr"]},
    "record_contradiction":         {"categories": {"transcript", "TRANSCRIPT", "evidence", "discovery"},
                                     "keywords": ["contradict", "inconsistent", "record", "conflict"]},
    "mental_health_assessment":     {"categories": {"report", "evidence", "discovery"},
                                     "keywords": ["mental health", "assessment", "evaluation", "healthwest"]},
    "parenting_time_evidence":      {"categories": {"custody", "court_order", "CUSTODY_ORDER"},
                                     "keywords": ["parenting time", "custody", "visitation", "child"]},
    "violation_evidence":           {"categories": {"evidence", "discovery", "exhibit"},
                                     "keywords": ["violation", "contempt", "breach", "non-compliance"]},
    "custody_evidence":             {"categories": {"custody", "CUSTODY_ORDER", "court_order"},
                                     "keywords": ["custody", "child", "best interest", "placement"]},
    "denial_evidence":              {"categories": {"evidence", "discovery", "transcript"},
                                     "keywords": ["deny", "denial", "refused", "blocked"]},
    "contempt_or_violation":        {"categories": {"court_order", "motion", "evidence"},
                                     "keywords": ["contempt", "violation", "non-compliance", "order"]},
    "parenting_time_restriction":   {"categories": {"custody", "CUSTODY_ORDER", "court_order", "ppo"},
                                     "keywords": ["restrict", "suspend", "parenting time", "limitation"]},
    "parenting_time_statute_reference": {"categories": {"court_filing", "brief", "motion"},
                                     "keywords": ["statute", "mcl", "mcr", "law", "parenting time"]},
    "ex_parte_reference":           {"categories": {"ppo", "EX_PARTE_ORDER", "court_order", "PPO"},
                                     "keywords": ["ex parte", "ppo", "protection"]},
}

# Fallback for any classification not explicitly mapped
DEFAULT_MATCH = {"categories": {"evidence", "discovery", "general_court_doc"},
                 "keywords": ["evidence", "document"]}


def parse_date_ref(raw):
    """Try to extract (year, month) from various date_ref formats."""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()

    # Format: MM/DD/YYYY or M/D/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', raw)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2030:
            return (year, month)

    # Format: M/D/YY or MM/DD/YY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', raw)
    if m:
        month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year += 2000
        if 1 <= month <= 12 and 1 <= day <= 31 and 2000 <= year <= 2030:
            return (year, month)

    # Format: "Month DD, YYYY" or "Month  DD, YYYY"
    m = re.match(r'^(\w+)\s+(\d{1,2}),?\s+(\d{4})$', raw)
    if m:
        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        mn = month_names.get(m.group(1).lower())
        if mn:
            year = int(m.group(3))
            if 2000 <= year <= 2030:
                return (year, mn)

    return None


def step1_claim_evidence_map(ro_conn, rw_conn):
    """Cross-reference evidence_quotes with claims."""
    print("\n" + "=" * 70)
    print("  PHASE 3.1 — CLAIM ↔ EVIDENCE CROSS-REFERENCE")
    print("=" * 70)

    ro = ro_conn.cursor()
    rw = rw_conn.cursor()

    # Create output table
    rw.execute("DROP TABLE IF EXISTS omega_claim_evidence_map")
    rw.execute("""
        CREATE TABLE omega_claim_evidence_map (
            claim_id TEXT PRIMARY KEY,
            classification TEXT,
            proposition TEXT,
            matching_evidence_count INTEGER,
            category_match_count INTEGER,
            keyword_match_count INTEGER,
            completeness_score REAL,
            top_categories TEXT,
            has_gap INTEGER,
            analyzed_at TEXT
        )
    """)

    # Load all claims
    ro.execute("SELECT claim_id, classification, proposition FROM claims")
    claims = ro.fetchall()

    # Pre-compute category counts
    ro.execute("SELECT evidence_category, COUNT(*) FROM evidence_quotes GROUP BY evidence_category")
    cat_counts = dict(ro.fetchall())

    total_evidence = sum(cat_counts.values())
    gap_claims = []
    scores = []

    for claim_id, classification, proposition in claims:
        mapping = CLASSIFICATION_TO_EVIDENCE.get(classification, DEFAULT_MATCH)
        target_cats = mapping["categories"]
        keywords = mapping["keywords"]

        # Count evidence by matching categories
        cat_match = 0
        matched_cats = {}
        for cat in target_cats:
            if cat in cat_counts:
                cat_match += cat_counts[cat]
                matched_cats[cat] = cat_counts[cat]

        # Keyword search in proposition text against evidence (sampled for performance)
        kw_match = 0
        if proposition:
            prop_lower = proposition.lower()
            for kw in keywords:
                if kw in prop_lower:
                    kw_match += 1

        # Combined score: category evidence density + keyword alignment
        # Max theoretical: category covers large evidence pool + all keywords match
        cat_score = min(100, (cat_match / max(total_evidence * 0.01, 1)) * 50)
        kw_score = (kw_match / max(len(keywords), 1)) * 50
        completeness = round(min(100, cat_score + kw_score), 1)

        total_match = cat_match
        has_gap = 1 if total_match == 0 else 0

        if has_gap:
            gap_claims.append((claim_id, classification, (proposition or "")[:80]))

        scores.append(completeness)

        top_cats_json = json.dumps(dict(sorted(matched_cats.items(), key=lambda x: -x[1])[:5]))

        rw.execute("""
            INSERT INTO omega_claim_evidence_map
            (claim_id, classification, proposition, matching_evidence_count,
             category_match_count, keyword_match_count, completeness_score,
             top_categories, has_gap, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (claim_id, classification, proposition, total_match,
              cat_match, kw_match, completeness, top_cats_json, has_gap,
              datetime.now(timezone.utc).isoformat()))

    rw_conn.commit()

    avg_score = sum(scores) / len(scores) if scores else 0
    high_score = sum(1 for s in scores if s >= 70)
    med_score = sum(1 for s in scores if 30 <= s < 70)
    low_score = sum(1 for s in scores if s < 30)

    print(f"\n  Claims analyzed:         {len(claims):,}")
    print(f"  Total evidence quotes:   {total_evidence:,}")
    print(f"  Average completeness:    {avg_score:.1f}%")
    print(f"  High evidence (≥70):     {high_score}")
    print(f"  Medium evidence (30-69): {med_score}")
    print(f"  Low evidence (<30):      {low_score}")
    print(f"  Claims with ZERO match:  {len(gap_claims)}")

    if gap_claims:
        print(f"\n  ⚠ EVIDENCE GAPS (claims with no supporting evidence):")
        for cid, cls, prop in gap_claims[:10]:
            print(f"    • [{cls}] {cid}: {prop}")
        if len(gap_claims) > 10:
            print(f"    ... and {len(gap_claims) - 10} more")

    # Top classifications by evidence strength
    ro2 = rw_conn.cursor()
    ro2.execute("""
        SELECT classification, COUNT(*) cnt, ROUND(AVG(completeness_score),1) avg_score
        FROM omega_claim_evidence_map
        GROUP BY classification ORDER BY avg_score DESC LIMIT 10
    """)
    print(f"\n  Top claim types by evidence strength:")
    for cls, cnt, avg in ro2.fetchall():
        bar = "█" * int(avg / 5)
        print(f"    {cls:<40s} ({cnt:>3} claims) {avg:>5.1f}% {bar}")

    print(f"\n  ✓ Saved to omega_claim_evidence_map ({len(claims)} rows)")
    return len(claims), len(gap_claims), avg_score


def step2_violation_analysis(ro_conn, rw_conn):
    """Analyze judicial violations by type, pattern, and severity."""
    print("\n" + "=" * 70)
    print("  PHASE 3.2 — JUDICIAL VIOLATION ANALYSIS")
    print("=" * 70)

    ro = ro_conn.cursor()
    rw = rw_conn.cursor()

    rw.execute("DROP TABLE IF EXISTS omega_violation_analysis")
    rw.execute("""
        CREATE TABLE omega_violation_analysis (
            analysis_type TEXT,
            category TEXT,
            count INTEGER,
            percentage REAL,
            severity_breakdown TEXT,
            judges_involved TEXT,
            details TEXT,
            analyzed_at TEXT
        )
    """)

    # Total violations
    ro.execute("SELECT COUNT(*) FROM judicial_violations")
    total = ro.fetchone()[0]

    # ── Group by canon_number (violation type) ──
    ro.execute("""
        SELECT canon_number, COUNT(*) c,
               GROUP_CONCAT(DISTINCT severity) severities,
               GROUP_CONCAT(DISTINCT judge_name) judges
        FROM judicial_violations
        GROUP BY canon_number ORDER BY c DESC
    """)
    type_rows = ro.fetchall()

    print(f"\n  Total violations:  {total:,}")
    print(f"  Distinct types:    {len(type_rows)}")
    print(f"\n  Most frequent violation patterns:")
    for canon, cnt, sevs, judges in type_rows[:12]:
        pct = cnt / total * 100
        print(f"    {cnt:>4}× ({pct:>5.1f}%) │ {canon}")

        rw.execute("""
            INSERT INTO omega_violation_analysis
            (analysis_type, category, count, percentage, severity_breakdown, judges_involved, details, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("by_type", canon, cnt, round(pct, 2), sevs, judges, None,
              datetime.now(timezone.utc).isoformat()))

    # ── Severity distribution ──
    ro.execute("SELECT severity, COUNT(*) c FROM judicial_violations GROUP BY severity ORDER BY c DESC")
    sev_rows = ro.fetchall()
    print(f"\n  Severity distribution:")
    for sev, cnt in sev_rows:
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"    {sev:<12s} {cnt:>5,} ({pct:>5.1f}%) {bar}")

        rw.execute("""
            INSERT INTO omega_violation_analysis
            (analysis_type, category, count, percentage, severity_breakdown, judges_involved, details, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("by_severity", sev, cnt, round(pct, 2), None, None, None,
              datetime.now(timezone.utc).isoformat()))

    # ── Judge-level analysis ──
    ro.execute("""
        SELECT judge_name, COUNT(*) c,
               SUM(CASE WHEN severity='critical' THEN 1 ELSE 0 END) crit,
               SUM(CASE WHEN severity='high' THEN 1 ELSE 0 END) high,
               GROUP_CONCAT(DISTINCT canon_number) types
        FROM judicial_violations
        WHERE judge_name IS NOT NULL AND judge_name != ''
        GROUP BY judge_name ORDER BY c DESC LIMIT 10
    """)
    judge_rows = ro.fetchall()
    print(f"\n  Violations by judge:")
    for name, cnt, crit, high, types in judge_rows:
        type_list = types.split(",") if types else []
        print(f"    {name:<35s} {cnt:>4} violations ({crit} critical, {high} high) — {len(type_list)} types")

        rw.execute("""
            INSERT INTO omega_violation_analysis
            (analysis_type, category, count, percentage, severity_breakdown, judges_involved, details, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("by_judge", name, cnt, round(cnt / total * 100, 2),
              json.dumps({"critical": crit, "high": high}),
              name, f"{len(type_list)} distinct violation types",
              datetime.now(timezone.utc).isoformat()))

    rw_conn.commit()

    rows_written = len(type_rows) + len(sev_rows) + len(judge_rows)
    print(f"\n  ✓ Saved to omega_violation_analysis ({rows_written} rows)")
    return total, len(type_rows), sev_rows


def step3_temporal_analysis(ro_conn, rw_conn):
    """Build timeline density from date_ref field."""
    print("\n" + "=" * 70)
    print("  PHASE 3.3 — TEMPORAL ANALYSIS")
    print("=" * 70)

    ro = ro_conn.cursor()
    rw = rw_conn.cursor()

    rw.execute("DROP TABLE IF EXISTS omega_temporal_analysis")
    rw.execute("""
        CREATE TABLE omega_temporal_analysis (
            year_month TEXT PRIMARY KEY,
            event_count INTEGER,
            categories TEXT,
            is_gap INTEGER DEFAULT 0,
            density_rank INTEGER,
            analyzed_at TEXT
        )
    """)

    # Fetch all non-null date_refs with categories
    ro.execute("""
        SELECT date_ref, evidence_category
        FROM evidence_quotes
        WHERE date_ref IS NOT NULL AND date_ref != ''
    """)

    timeline = defaultdict(lambda: {"count": 0, "categories": defaultdict(int)})
    parsed = 0
    failed = 0

    for date_ref, cat in ro.fetchall():
        result = parse_date_ref(date_ref)
        if result:
            year, month = result
            key = f"{year}-{month:02d}"
            timeline[key]["count"] += 1
            timeline[key]["categories"][cat] += 1
            parsed += 1
        else:
            failed += 1

    print(f"\n  Date refs processed:  {parsed + failed:,}")
    print(f"  Successfully parsed:  {parsed:,}")
    print(f"  Parse failures:       {failed:,}")

    if not timeline:
        print("  ⚠ No valid dates found — skipping temporal analysis")
        rw_conn.commit()
        return 0, 0, []

    # Determine full date range
    all_months = sorted(timeline.keys())
    start_ym = all_months[0]
    end_ym = all_months[-1]

    # Generate all months in range
    sy, sm = int(start_ym[:4]), int(start_ym[5:])
    ey, em = int(end_ym[:4]), int(end_ym[5:])

    all_periods = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        all_periods.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1

    # Rank by density
    sorted_by_count = sorted(timeline.items(), key=lambda x: -x[1]["count"])
    rank_map = {}
    for i, (k, _) in enumerate(sorted_by_count):
        rank_map[k] = i + 1

    gaps = []
    for period in all_periods:
        data = timeline.get(period)
        if data:
            cats_json = json.dumps(dict(sorted(data["categories"].items(), key=lambda x: -x[1])[:5]))
            rw.execute("""
                INSERT INTO omega_temporal_analysis
                (year_month, event_count, categories, is_gap, density_rank, analyzed_at)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (period, data["count"], cats_json, rank_map.get(period, 0),
                  datetime.now(timezone.utc).isoformat()))
        else:
            gaps.append(period)
            rw.execute("""
                INSERT INTO omega_temporal_analysis
                (year_month, event_count, categories, is_gap, density_rank, analyzed_at)
                VALUES (?, 0, '{}', 1, ?, ?)
            """, (period, len(all_periods), datetime.now(timezone.utc).isoformat()))

    rw_conn.commit()

    # Print timeline
    print(f"\n  Timeline range:  {start_ym} → {end_ym}  ({len(all_periods)} months)")
    print(f"  Months with data:  {len(all_periods) - len(gaps)}")
    print(f"  Timeline gaps:     {len(gaps)}")

    if gaps:
        print(f"\n  ⚠ MONTHS WITH NO EVIDENCE:")
        for g in gaps:
            print(f"    • {g}")

    # Top 10 densest months
    print(f"\n  Top evidence-dense months:")
    for ym, data in sorted_by_count[:10]:
        bar = "█" * min(50, max(1, data["count"] // 500))
        print(f"    {ym}  {data['count']:>6,} events {bar}")

    print(f"\n  ✓ Saved to omega_temporal_analysis ({len(all_periods)} rows)")
    return parsed, len(gaps), sorted_by_count[:5]


def print_dashboard(claim_stats, violation_stats, temporal_stats):
    """Print the comprehensive OMEGA Phase 3 dashboard."""
    claims_analyzed, gaps, avg_completeness = claim_stats
    total_violations, violation_types, severity_dist = violation_stats
    dates_parsed, timeline_gaps, top_months = temporal_stats

    crit_count = next((c for s, c in severity_dist if s == "critical"), 0)
    high_count = next((c for s, c in severity_dist if s == "high"), 0)

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + "  OPERATION OMEGA — PHASE 3 DASHBOARD".center(68) + "║")
    print("╠" + "═" * 68 + "╣")

    print("║" + "  CLAIM ↔ EVIDENCE ANALYSIS".ljust(68) + "║")
    print("║" + f"    Claims analyzed:          {claims_analyzed:>6,}".ljust(68) + "║")
    print("║" + f"    Avg completeness score:   {avg_completeness:>6.1f}%".ljust(68) + "║")
    print("║" + f"    Evidence gaps found:       {gaps:>5,}".ljust(68) + "║")

    print("╠" + "═" * 68 + "╣")

    print("║" + "  JUDICIAL VIOLATION PATTERNS".ljust(68) + "║")
    print("║" + f"    Total violations:         {total_violations:>6,}".ljust(68) + "║")
    print("║" + f"    Distinct violation types:  {violation_types:>5,}".ljust(68) + "║")
    print("║" + f"    Critical severity:        {crit_count:>6,}".ljust(68) + "║")
    print("║" + f"    High severity:            {high_count:>6,}".ljust(68) + "║")

    print("╠" + "═" * 68 + "╣")

    print("║" + "  TEMPORAL ANALYSIS".ljust(68) + "║")
    print("║" + f"    Dates parsed:             {dates_parsed:>6,}".ljust(68) + "║")
    print("║" + f"    Timeline gaps (months):    {timeline_gaps:>5,}".ljust(68) + "║")
    if top_months:
        densest_ym, densest_data = top_months[0]
        print("║" + f"    Densest month:   {densest_ym} ({densest_data['count']:,} events)".ljust(68) + "║")

    print("╠" + "═" * 68 + "╣")
    status = "COMPLETE" if gaps == 0 and timeline_gaps == 0 else "GAPS DETECTED"
    print("║" + f"  STATUS: {status}".ljust(68) + "║")
    print("║" + f"  Timestamp: {datetime.now(timezone.utc).isoformat()}Z".ljust(68) + "║")
    print("╚" + "═" * 68 + "╝")


def main():
    print("╔" + "═" * 68 + "╗")
    print("║" + "  OPERATION OMEGA — PHASE 3: ENHANCED PIPELINE RUNNER".center(68) + "║")
    print("║" + f"  Database: {os.path.basename(DB_PATH)}".center(68) + "║")
    print("╚" + "═" * 68 + "╝")

    if not os.path.exists(DB_PATH):
        print(f"FATAL: Database not found at {DB_PATH}")
        sys.exit(1)

    size_gb = os.path.getsize(DB_PATH) / (1024 ** 3)
    print(f"\n  DB size: {size_gb:.2f} GB")

    # Read-only connection for all SELECT queries
    ro_conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    ro_conn.execute("PRAGMA query_only = ON")

    # Read-write connection for creating omega_ tables
    rw_conn = sqlite3.connect(DB_PATH)
    rw_conn.execute("PRAGMA journal_mode=WAL")
    rw_conn.execute("PRAGMA synchronous=NORMAL")

    try:
        claim_stats = step1_claim_evidence_map(ro_conn, rw_conn)
        violation_stats = step2_violation_analysis(ro_conn, rw_conn)
        temporal_stats = step3_temporal_analysis(ro_conn, rw_conn)
        print_dashboard(claim_stats, violation_stats, temporal_stats)
    finally:
        ro_conn.close()
        rw_conn.close()

    print("\n  Phase 3 pipeline complete.\n")


if __name__ == "__main__":
    main()

