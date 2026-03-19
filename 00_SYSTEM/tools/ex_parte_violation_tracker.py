#!/usr/bin/env python3
"""
Tool #219: Ex Parte Violation Tracker
======================================
Track and score all ex parte violations by Judge McNeill.
Queries: judicial_violations, actor_violations, docket_events,
         constitutional_violations, caselaw_ex_parte_reversal,
         benchbook_violation_findings
Outputs: EX_PARTE_TRACKER.md + ex_parte_tracker.json
"""
import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Force UTF-8 output on Windows
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# Path setup — NEVER set CWD to repo root (shadow modules)
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = SCRIPT_DIR.parent.parent
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Open DB with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_trunc(text, maxlen=200):
    """Truncate text safely for display."""
    if not text:
        return ""
    text = str(text).replace('\n', ' ').replace('\r', '').strip()
    return text[:maxlen] + "..." if len(text) > maxlen else text


def severity_to_score(severity):
    """Convert severity label to 1-5 numeric score."""
    sev = str(severity).upper().strip() if severity else ""
    mapping = {
        "CRITICAL": 5, "5": 5,
        "HIGH": 4, "4": 4,
        "MEDIUM": 3, "3": 3,
        "LOW": 2, "2": 2,
        "MINIMAL": 1, "1": 1,
    }
    return mapping.get(sev, 3)


def main():
    print("=" * 70)
    print("  TOOL #219 — EX PARTE VIOLATION TRACKER")
    print("  Tracking & scoring Judge McNeill ex parte violations")
    print("=" * 70)
    ts = datetime.now()

    conn = get_connection()

    # === 1) judicial_violations — ex parte related ===
    print("\n[1/6] Querying judicial_violations for ex parte...")
    jv_ex_parte = []
    jv_all_stats = {"total": 0, "ex_parte_count": 0, "by_canon": defaultdict(int), "by_severity": defaultdict(int)}
    try:
        # Total stats first
        row = conn.execute("SELECT COUNT(*) as t FROM judicial_violations").fetchone()
        jv_all_stats["total"] = row["t"]

        # Ex parte specific
        rows = conn.execute("""
            SELECT violation_id, judge_name, canon_number, canon_text,
                   violation_description, evidence_refs, severity, created_at
            FROM judicial_violations
            WHERE canon_number LIKE '%EX_PARTE%'
               OR violation_description LIKE '%ex parte%'
               OR canon_number LIKE '%ex parte%'
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            sev_score = severity_to_score(r["severity"])
            item = {
                "violation_id": r["violation_id"],
                "judge": r["judge_name"],
                "canon": r["canon_number"],
                "description": safe_trunc(r["violation_description"], 300),
                "evidence_refs": r["evidence_refs"],
                "severity_label": r["severity"],
                "severity_score": sev_score,
                "date": r["created_at"],
            }
            jv_ex_parte.append(item)
            jv_all_stats["by_canon"][r["canon_number"]] += 1
            jv_all_stats["by_severity"][r["severity"]] += 1

        jv_all_stats["ex_parte_count"] = len(jv_ex_parte)
        print(f"  {len(jv_ex_parte)} ex parte violations out of {jv_all_stats['total']} total")
    except Exception as e:
        print(f"  Error: {e}")

    # === 2) actor_violations — ex_parte type ===
    print("\n[2/6] Querying actor_violations for ex_parte type...")
    actor_ex_parte = []
    actor_stats = {"total": 0, "by_actor": defaultdict(int), "by_severity": defaultdict(int)}
    try:
        rows = conn.execute("""
            SELECT actor, role, violation_type, description, date,
                   evidence_source, severity, linked_actors, pattern_id
            FROM actor_violations
            WHERE violation_type = 'ex_parte'
               OR violation_type LIKE '%ex_parte%'
               OR description LIKE '%ex parte%'
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            actor_stats["total"] += 1
            actor_stats["by_actor"][r["actor"]] += 1
            actor_stats["by_severity"][r["severity"]] += 1
            if len(actor_ex_parte) < 30:
                actor_ex_parte.append({
                    "actor": r["actor"],
                    "type": r["violation_type"],
                    "description": safe_trunc(r["description"], 250),
                    "date": r["date"],
                    "severity": r["severity"],
                    "severity_score": severity_to_score(r["severity"]),
                    "linked_actors": r["linked_actors"],
                })
        print(f"  {actor_stats['total']} actor violation entries")
    except Exception as e:
        print(f"  Error: {e}")

    # === 3) docket_events — ex parte orders ===
    print("\n[3/6] Querying docket_events for ex parte orders...")
    docket_ex_parte = []
    try:
        rows = conn.execute("""
            SELECT event_id, case_id, event_date_iso, title, event_type,
                   summary, truth_tag
            FROM docket_events
            WHERE title LIKE '%ex parte%' OR summary LIKE '%ex parte%'
            ORDER BY event_date_iso
        """).fetchall()
        for r in rows:
            docket_ex_parte.append({
                "event_id": r["event_id"],
                "case_id": r["case_id"],
                "date": r["event_date_iso"],
                "title": r["title"],
                "type": r["event_type"],
                "summary": safe_trunc(r["summary"], 250),
                "truth_tag": r["truth_tag"],
            })
        print(f"  {len(docket_ex_parte)} ex parte docket events")
    except Exception as e:
        print(f"  Error: {e}")

    # === 4) constitutional_violations — ex parte related ===
    print("\n[4/6] Querying constitutional_violations...")
    const_violations = []
    try:
        rows = conn.execute("""
            SELECT amendment, clause, violation_type, description,
                   incident_date, actors, evidence_ref,
                   controlling_caselaw, michigan_authority, severity
            FROM constitutional_violations
            WHERE violation_type LIKE '%EX_PARTE%'
               OR description LIKE '%ex parte%'
            ORDER BY severity DESC
        """).fetchall()
        for r in rows:
            const_violations.append({
                "amendment": r["amendment"],
                "clause": r["clause"],
                "type": r["violation_type"],
                "description": safe_trunc(r["description"], 300),
                "date": r["incident_date"],
                "actors": r["actors"],
                "evidence": r["evidence_ref"],
                "caselaw": safe_trunc(r["controlling_caselaw"], 200),
                "michigan_auth": safe_trunc(r["michigan_authority"], 200),
                "severity": r["severity"],
                "severity_score": severity_to_score(r["severity"]),
            })
        print(f"  {len(const_violations)} constitutional violation entries related to ex parte")
    except Exception as e:
        print(f"  Error: {e}")

    # === 5) Benchbook violations — ex parte related ===
    print("\n[5/6] Querying benchbook_violation_findings...")
    benchbook_items = []
    benchbook_stats = {"total": 0, "by_rule": defaultdict(int)}
    try:
        total = conn.execute("SELECT COUNT(*) FROM benchbook_violation_findings").fetchone()[0]
        benchbook_stats["total"] = total
        rows = conn.execute("""
            SELECT rule, explanation, matching_text
            FROM benchbook_violation_findings
            WHERE explanation LIKE '%ex parte%'
               OR matching_text LIKE '%ex parte%'
               OR rule LIKE '%ex parte%'
        """).fetchall()
        for r in rows:
            benchbook_stats["by_rule"][r["rule"]] += 1
            if len(benchbook_items) < 15:
                benchbook_items.append({
                    "rule": r["rule"],
                    "explanation": safe_trunc(r["explanation"], 200),
                    "matching_text": safe_trunc(r["matching_text"], 200),
                })
        print(f"  {len(benchbook_items)} ex parte benchbook findings (of {total} total)")
    except Exception as e:
        print(f"  Error: {e}")

    # === 6) Relevant case law ===
    print("\n[6/6] Querying caselaw_ex_parte_reversal...")
    caselaw_items = []
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM caselaw_ex_parte_reversal").fetchone()[0]
        rows = conn.execute("""
            SELECT case_name, citation, holding, reversal_basis, relevance
            FROM caselaw_ex_parte_reversal
            LIMIT 20
        """).fetchall()
        for r in rows:
            caselaw_items.append({
                "case_name": r["case_name"],
                "citation": r["citation"],
                "holding": safe_trunc(r["holding"], 200),
                "basis": r["reversal_basis"],
                "relevance": safe_trunc(r["relevance"], 150),
            })
        print(f"  {cnt} total case law entries for ex parte reversal")
    except Exception as e:
        print(f"  Error: {e}")

    conn.close()

    # --- Pattern analysis ---
    total_ex_parte_events = len(docket_ex_parte)
    date_pattern = defaultdict(int)
    for ev in docket_ex_parte:
        if ev["date"]:
            year_month = ev["date"][:7]
            date_pattern[year_month] += 1

    # Aggregate severity
    all_severity_scores = ([i["severity_score"] for i in jv_ex_parte] +
                           [i["severity_score"] for i in actor_ex_parte] +
                           [i["severity_score"] for i in const_violations])
    avg_severity = round(sum(all_severity_scores) / len(all_severity_scores), 2) if all_severity_scores else 0
    max_severity = max(all_severity_scores) if all_severity_scores else 0

    # Bias score: weighted combination
    bias_score = round(min(10.0, (
        (len(jv_ex_parte) * 0.02) +
        (actor_stats["total"] * 0.005) +
        (total_ex_parte_events * 0.05) +
        (len(const_violations) * 0.5) +
        (avg_severity * 0.5)
    )), 2)

    # === BUILD MARKDOWN ===
    lines = [
        "# ⚖️ EX PARTE VIOLATION TRACKER — Tool #219",
        f"*Generated: {ts.strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## Executive Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Judicial Violations (ex parte) | {len(jv_ex_parte)} of {jv_all_stats['total']} total |",
        f"| Actor Violations (ex parte) | {actor_stats['total']:,} |",
        f"| Docket Events (ex parte orders) | {total_ex_parte_events} |",
        f"| Constitutional Violations | {len(const_violations)} |",
        f"| Benchbook Findings | {len(benchbook_items)} of {benchbook_stats['total']} |",
        f"| Supporting Case Law | {len(caselaw_items)} entries |",
        f"| **Average Severity Score** | **{avg_severity}/5** |",
        f"| **Aggregate Bias Score** | **{bias_score}/10** |",
        "",
        "---\n",
        "## Docket Timeline — Ex Parte Orders\n",
        "| Date | Event | Type | Summary |",
        "|------|-------|------|---------|",
    ]

    for ev in docket_ex_parte:
        lines.append(f"| {ev['date']} | {ev['title']} | {ev['type']} | {safe_trunc(ev['summary'], 100)} |")

    lines.extend(["", "### Frequency Pattern\n",
                   "| Month | Ex Parte Events |", "|-------|----------------|"])
    for ym, cnt in sorted(date_pattern.items()):
        bar = "█" * cnt
        lines.append(f"| {ym} | {cnt} {bar} |")

    lines.extend(["", "---\n", "## Judicial Violations — Canon Breakdown\n",
                   "| Canon/MCR | Count |", "|-----------|-------|"])
    for canon, cnt in sorted(jv_all_stats["by_canon"].items(), key=lambda x: -x[1]):
        lines.append(f"| {canon} | {cnt} |")

    lines.extend(["", "### Severity Distribution\n",
                   "| Severity | Count |", "|----------|-------|"])
    for sev, cnt in sorted(jv_all_stats["by_severity"].items(), key=lambda x: -x[1]):
        lines.append(f"| {sev} | {cnt} |")

    lines.extend(["", "---\n", "## Constitutional Violations (Ex Parte)\n"])
    for cv in const_violations:
        lines.extend([
            f"### [{cv['severity']}] {cv['amendment']} — {cv['clause']}",
            f"- **Type**: {cv['type']}",
            f"- **Date**: {cv['date']}",
            f"- **Actors**: {cv['actors']}",
            f"- **Description**: {cv['description']}",
            f"- **Controlling Caselaw**: {cv['caselaw']}",
            f"- **Michigan Authority**: {cv['michigan_auth']}",
            f"- **Evidence**: {cv['evidence']}",
            "",
        ])

    lines.extend(["---\n", "## Actor Violation Breakdown\n",
                   "| Actor | Ex Parte Violations |", "|-------|-------------------|"])
    for actor, cnt in sorted(actor_stats["by_actor"].items(), key=lambda x: -x[1]):
        lines.append(f"| {actor} | {cnt:,} |")
    lines.extend(["", "| Severity | Count |", "|----------|-------|"])
    for sev, cnt in sorted(actor_stats["by_severity"].items(), key=lambda x: -x[1]):
        lines.append(f"| {sev} | {cnt:,} |")

    lines.extend(["", "---\n", "## Top Judicial Violations (Ex Parte)\n"])
    for i, item in enumerate(jv_ex_parte[:15], 1):
        lines.extend([
            f"### {i}. [{item['severity_label'].upper()}] {item['canon']}",
            f"- **Judge**: {item['judge']}",
            f"- **Description**: {item['description']}",
            f"- **MCR/MCL Cited**: {item['evidence_refs']}",
            f"- **Severity Score**: {item['severity_score']}/5",
            "",
        ])

    lines.extend(["---\n", "## Benchbook Violation Findings (Ex Parte)\n"])
    for bk in benchbook_items[:10]:
        lines.extend([
            f"- **{bk['rule']}**: {bk['explanation']}",
            f"  - Match: {bk['matching_text']}",
        ])

    lines.extend(["", "---\n", "## Supporting Case Law for Reversal\n",
                   "| Case | Citation | Basis |", "|------|----------|-------|"])
    seen_cases = set()
    for cl in caselaw_items:
        key = cl["case_name"]
        if key not in seen_cases:
            seen_cases.add(key)
            lines.append(f"| {cl['case_name']} | {cl['citation']} | {cl['basis']} |")

    lines.extend(["", "---\n",
                   "## Bias Score Methodology\n",
                   f"The aggregate bias score of **{bias_score}/10** is calculated from:\n",
                   f"- {len(jv_ex_parte)} judicial violations × 0.02 weight",
                   f"- {actor_stats['total']:,} actor violations × 0.005 weight",
                   f"- {total_ex_parte_events} docket events × 0.05 weight",
                   f"- {len(const_violations)} constitutional violations × 0.5 weight",
                   f"- {avg_severity} avg severity × 0.5 weight",
                   f"- Score capped at 10.0\n",
                   "Each component is traceable to specific DB queries above.",
                   "",
                   "---",
                   f"*Tool #219 — ex_parte_violation_tracker.py — {ts.strftime('%Y-%m-%d %H:%M:%S')}*"])

    md_path = REPORTS_DIR / "EX_PARTE_TRACKER.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Markdown: {md_path}")

    # === BUILD JSON ===
    json_data = {
        "generated": ts.isoformat(),
        "tool": "Ex Parte Violation Tracker (#219)",
        "summary": {
            "judicial_violations_ex_parte": len(jv_ex_parte),
            "judicial_violations_total": jv_all_stats["total"],
            "actor_violations_ex_parte": actor_stats["total"],
            "docket_ex_parte_events": total_ex_parte_events,
            "constitutional_violations": len(const_violations),
            "benchbook_findings": len(benchbook_items),
            "caselaw_entries": len(caselaw_items),
            "avg_severity_score": avg_severity,
            "max_severity_score": max_severity,
            "aggregate_bias_score": bias_score,
        },
        "docket_timeline": docket_ex_parte,
        "frequency_pattern": dict(date_pattern),
        "judicial_violations": {
            "by_canon": dict(jv_all_stats["by_canon"]),
            "by_severity": dict(jv_all_stats["by_severity"]),
            "top_items": jv_ex_parte[:20],
        },
        "actor_violations": {
            "by_actor": dict(actor_stats["by_actor"]),
            "by_severity": dict(actor_stats["by_severity"]),
            "top_items": actor_ex_parte,
        },
        "constitutional_violations": const_violations,
        "benchbook_findings": benchbook_items,
        "caselaw_for_reversal": caselaw_items,
    }

    json_path = REPORTS_DIR / "ex_parte_tracker.json"
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding='utf-8')
    print(f"✅ JSON:     {json_path}")
    print(f"\n{'=' * 70}")
    print(f"  EX PARTE TRACKER COMPLETE")
    print(f"  {len(jv_ex_parte)} judicial + {actor_stats['total']:,} actor + "
          f"{total_ex_parte_events} docket violations")
    print(f"  Bias Score: {bias_score}/10 | Avg Severity: {avg_severity}/5")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
