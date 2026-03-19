#!/usr/bin/env python3
"""
Tool #218: Rebuttal Pack Analyzer
==================================
Analyze rebuttal evidence strength and coverage for each claim against Andrew.
Queries: rebuttal_matrix, adversary_assertions, claims, claim_evidence_links
Outputs: REBUTTAL_ANALYSIS.md + rebuttal_analysis.json
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


def classify_coverage(has_rebuttal_evidence, priority_score=None, is_false=None):
    """Classify rebuttal coverage level."""
    if not has_rebuttal_evidence:
        return "no_rebuttal"
    evidence = str(has_rebuttal_evidence).strip()
    if not evidence or evidence.lower() in ("none", "null", ""):
        return "no_rebuttal"
    if priority_score and priority_score >= 70:
        return "fully_rebutted"
    if is_false == 1:
        return "fully_rebutted"
    if len(evidence) > 50:
        return "fully_rebutted"
    return "partially_rebutted"


def main():
    print("=" * 70)
    print("  TOOL #218 — REBUTTAL PACK ANALYZER")
    print("  Analyzing rebuttal evidence strength & coverage")
    print("=" * 70)
    ts = datetime.now()

    conn = get_connection()

    # --- 1) Rebuttal Matrix analysis ---
    print("\n[1/4] Analyzing rebuttal_matrix...")
    rebuttal_items = []
    rebuttal_by_category = defaultdict(lambda: {"total": 0, "fully": 0, "partial": 0, "none": 0, "items": []})
    rebuttal_by_adversary = defaultdict(lambda: {"total": 0, "fully": 0, "partial": 0, "none": 0})
    try:
        rows = conn.execute("""
            SELECT id, adversary, assertion_text, assertion_category, assertion_severity,
                   is_false_statement, rebuttal_evidence, rebuttal_citation,
                   tort_cause, filing_target, priority_score
            FROM rebuttal_matrix
            ORDER BY priority_score DESC
        """).fetchall()
        for r in rows:
            coverage = classify_coverage(r["rebuttal_evidence"], r["priority_score"], r["is_false_statement"])
            cat = r["assertion_category"] or "UNCATEGORIZED"
            adv = r["adversary"] or "UNKNOWN"

            rebuttal_by_category[cat]["total"] += 1
            rebuttal_by_category[cat][coverage.replace("_rebutted", "").replace("no_rebuttal", "none")] += 1
            rebuttal_by_adversary[adv]["total"] += 1
            rebuttal_by_adversary[adv][coverage.replace("_rebutted", "").replace("no_rebuttal", "none")] += 1

            item = {
                "id": r["id"],
                "adversary": adv,
                "assertion": safe_trunc(r["assertion_text"], 250),
                "category": cat,
                "severity": r["assertion_severity"],
                "is_false": bool(r["is_false_statement"]),
                "rebuttal_evidence": safe_trunc(r["rebuttal_evidence"], 300),
                "rebuttal_citation": r["rebuttal_citation"],
                "tort_cause": r["tort_cause"],
                "filing_target": r["filing_target"],
                "priority_score": r["priority_score"],
                "coverage": coverage,
            }
            rebuttal_items.append(item)
            if len(rebuttal_by_category[cat]["items"]) < 3:
                rebuttal_by_category[cat]["items"].append(item)

        print(f"  {len(rebuttal_items)} rebuttal matrix entries analyzed")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 2) Adversary Assertions with rebuttal gaps ---
    print("\n[2/4] Analyzing adversary_assertions for rebuttal gaps...")
    assertion_stats = {"total": 0, "with_rebuttal": 0, "without_rebuttal": 0,
                       "false_claims": 0, "by_type": defaultdict(int), "gaps": []}
    try:
        rows = conn.execute("""
            SELECT assertion_text, assertion_type, speaker, is_false,
                   rebuttal_evidence, severity
            FROM adversary_assertions
            ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                     WHEN 'MEDIUM' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            assertion_stats["total"] += 1
            assertion_stats["by_type"][r["assertion_type"]] += 1
            if r["is_false"]:
                assertion_stats["false_claims"] += 1

            reb = str(r["rebuttal_evidence"] or "").strip()
            has_rebuttal = bool(reb and reb.lower() not in ("none", "null", ""))

            if has_rebuttal:
                assertion_stats["with_rebuttal"] += 1
            else:
                assertion_stats["without_rebuttal"] += 1
                if len(assertion_stats["gaps"]) < 20 and r["severity"] in ("HIGH", "CRITICAL"):
                    assertion_stats["gaps"].append({
                        "assertion": safe_trunc(r["assertion_text"], 250),
                        "type": r["assertion_type"],
                        "speaker": r["speaker"],
                        "severity": r["severity"],
                        "status": "NO REBUTTAL — EVIDENCE NEEDED",
                    })

        print(f"  {assertion_stats['total']:,} assertions: "
              f"{assertion_stats['with_rebuttal']:,} rebutted, "
              f"{assertion_stats['without_rebuttal']:,} gaps")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 3) Claims coverage analysis ---
    print("\n[3/4] Analyzing claims table for rebuttal coverage...")
    claims_analysis = {"total": 0, "supported": 0, "unsupported": 0, "by_class": defaultdict(int), "gaps": []}
    try:
        rows = conn.execute("""
            SELECT claim_id, classification, actor, proposition,
                   affirmative_counter_proposition, status
            FROM claims
            ORDER BY classification
        """).fetchall()
        for r in rows:
            claims_analysis["total"] += 1
            claims_analysis["by_class"][r["classification"]] += 1
            counter = str(r["affirmative_counter_proposition"] or "").strip()
            if counter and len(counter) > 20:
                claims_analysis["supported"] += 1
            else:
                claims_analysis["unsupported"] += 1
                if len(claims_analysis["gaps"]) < 15:
                    claims_analysis["gaps"].append({
                        "claim_id": r["claim_id"],
                        "classification": r["classification"],
                        "actor": r["actor"],
                        "proposition": safe_trunc(r["proposition"], 200),
                        "status": r["status"],
                        "gap": "COUNTER-PROPOSITION NEEDED",
                    })
        print(f"  {claims_analysis['total']} claims: "
              f"{claims_analysis['supported']} with counters, "
              f"{claims_analysis['unsupported']} gaps")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 4) Evidence link coverage ---
    print("\n[4/4] Analyzing claim_evidence_links coverage...")
    evidence_link_stats = {"total_links": 0, "claims_with_evidence": 0, "avg_relevance": 0,
                           "by_type": defaultdict(int)}
    try:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT claim_id) as unique_claims,
                   AVG(relevance_score) as avg_rel
            FROM claim_evidence_links
        """).fetchone()
        evidence_link_stats["total_links"] = row["total"]
        evidence_link_stats["claims_with_evidence"] = row["unique_claims"]
        evidence_link_stats["avg_relevance"] = round(row["avg_rel"] or 0, 1)

        type_rows = conn.execute("""
            SELECT claim_type, COUNT(*) as cnt
            FROM claim_evidence_links
            GROUP BY claim_type ORDER BY cnt DESC
        """).fetchall()
        for r in type_rows:
            evidence_link_stats["by_type"][r["claim_type"]] = r["cnt"]

        print(f"  {evidence_link_stats['total_links']:,} evidence links across "
              f"{evidence_link_stats['claims_with_evidence']} claims "
              f"(avg relevance: {evidence_link_stats['avg_relevance']})")
    except Exception as e:
        print(f"  Error: {e}")

    conn.close()

    # --- Aggregate scoring ---
    rm_total = len(rebuttal_items)
    rm_fully = sum(1 for i in rebuttal_items if i["coverage"] == "fully_rebutted")
    rm_partial = sum(1 for i in rebuttal_items if i["coverage"] == "partially_rebutted")
    rm_none = sum(1 for i in rebuttal_items if i["coverage"] == "no_rebuttal")
    coverage_pct = round(((rm_fully + rm_partial) / rm_total * 100) if rm_total > 0 else 0, 1)

    # === BUILD MARKDOWN ===
    lines = [
        "# 🛡️ REBUTTAL PACK ANALYSIS — Tool #218",
        f"*Generated: {ts.strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## Executive Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Rebuttal Matrix Entries | {rm_total} |",
        f"| Fully Rebutted | {rm_fully} ({round(rm_fully/rm_total*100, 1) if rm_total else 0}%) |",
        f"| Partially Rebutted | {rm_partial} ({round(rm_partial/rm_total*100, 1) if rm_total else 0}%) |",
        f"| No Rebuttal (GAPS) | **{rm_none}** ({round(rm_none/rm_total*100, 1) if rm_total else 0}%) |",
        f"| **Overall Coverage** | **{coverage_pct}%** |",
        f"| Adversary Assertions Total | {assertion_stats['total']:,} |",
        f"| Assertions With Rebuttal | {assertion_stats['with_rebuttal']:,} |",
        f"| Assertions Without Rebuttal | **{assertion_stats['without_rebuttal']:,}** |",
        f"| False Claims Identified | {assertion_stats['false_claims']:,} |",
        f"| Claims in DB | {claims_analysis['total']} |",
        f"| Evidence Links | {evidence_link_stats['total_links']:,} |",
        "",
        "---\n",
        "## Rebuttal Coverage by Category\n",
        "| Category | Total | Fully | Partial | None | Coverage % |",
        "|----------|-------|-------|---------|------|-----------|",
    ]

    for cat, data in sorted(rebuttal_by_category.items(), key=lambda x: -x[1]["total"]):
        t = data["total"]
        f_ = data["fully"]
        p = data["partial"]
        n = data["none"]
        pct = round((f_ + p) / t * 100, 1) if t > 0 else 0
        lines.append(f"| {cat} | {t} | {f_} | {p} | {n} | {pct}% |")

    lines.extend(["", "---\n", "## Rebuttal Coverage by Adversary\n",
                   "| Adversary | Total | Fully | Partial | None |",
                   "|-----------|-------|-------|---------|------|"])
    for adv, data in sorted(rebuttal_by_adversary.items(), key=lambda x: -x[1]["total"]):
        lines.append(f"| {adv} | {data['total']} | {data['fully']} | {data['partial']} | {data['none']} |")

    lines.extend(["", "---\n", "## ⚠️ CRITICAL GAPS — No Rebuttal Evidence\n",
                   "These HIGH/CRITICAL adversary assertions have NO rebuttal evidence:\n"])
    for i, gap in enumerate(assertion_stats.get("gaps", [])[:15], 1):
        lines.extend([
            f"### Gap {i}: [{gap['severity']}] {gap['type']}",
            f"- **Speaker**: {gap['speaker']}",
            f"- **Assertion**: {gap['assertion']}",
            f"- **Status**: 🔴 {gap['status']}",
            "",
        ])

    lines.extend(["---\n", "## Claims Without Counter-Propositions\n"])
    for gap in claims_analysis.get("gaps", [])[:10]:
        lines.extend([
            f"- **{gap['claim_id']}** [{gap['classification']}]: {gap['proposition']}",
            f"  - Status: {gap['status']} | Gap: {gap['gap']}",
        ])

    lines.extend(["", "---\n", "## Evidence Link Coverage\n",
                   "| Metric | Value |", "|--------|-------|",
                   f"| Total Links | {evidence_link_stats['total_links']:,} |",
                   f"| Unique Claims Linked | {evidence_link_stats['claims_with_evidence']} |",
                   f"| Avg Relevance Score | {evidence_link_stats['avg_relevance']} |",
                   "", "| Claim Type | Links |", "|------------|-------|"])
    for ct, cnt in sorted(evidence_link_stats["by_type"].items(), key=lambda x: -x[1])[:15]:
        lines.append(f"| {ct} | {cnt:,} |")

    lines.extend([
        "", "---\n", "## Adversary Assertion Types\n",
        "| Type | Count |", "|------|-------|",
    ])
    for t, cnt in sorted(assertion_stats["by_type"].items(), key=lambda x: -x[1])[:15]:
        lines.append(f"| {t} | {cnt:,} |")

    lines.extend([
        "", "---",
        f"*Tool #218 — rebuttal_pack_analyzer.py — {ts.strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    md_path = REPORTS_DIR / "REBUTTAL_ANALYSIS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Markdown: {md_path}")

    # === BUILD JSON ===
    json_data = {
        "generated": ts.isoformat(),
        "tool": "Rebuttal Pack Analyzer (#218)",
        "summary": {
            "rebuttal_matrix_total": rm_total,
            "fully_rebutted": rm_fully,
            "partially_rebutted": rm_partial,
            "no_rebuttal": rm_none,
            "coverage_percent": coverage_pct,
            "adversary_assertions_total": assertion_stats["total"],
            "assertions_with_rebuttal": assertion_stats["with_rebuttal"],
            "assertions_without_rebuttal": assertion_stats["without_rebuttal"],
            "false_claims": assertion_stats["false_claims"],
            "claims_total": claims_analysis["total"],
            "evidence_links_total": evidence_link_stats["total_links"],
        },
        "rebuttal_by_category": {cat: {"total": d["total"], "fully": d["fully"],
                                        "partial": d["partial"], "none": d["none"]}
                                  for cat, d in rebuttal_by_category.items()},
        "rebuttal_by_adversary": dict(rebuttal_by_adversary),
        "critical_gaps": assertion_stats.get("gaps", []),
        "claims_gaps": claims_analysis.get("gaps", []),
        "assertion_types": dict(assertion_stats["by_type"]),
        "evidence_link_stats": {
            "total": evidence_link_stats["total_links"],
            "unique_claims": evidence_link_stats["claims_with_evidence"],
            "avg_relevance": evidence_link_stats["avg_relevance"],
            "by_type": dict(evidence_link_stats["by_type"]),
        },
    }

    json_path = REPORTS_DIR / "rebuttal_analysis.json"
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding='utf-8')
    print(f"✅ JSON:     {json_path}")
    print(f"\n{'=' * 70}")
    print(f"  REBUTTAL ANALYSIS COMPLETE")
    print(f"  Coverage: {coverage_pct}% | Gaps: {rm_none} matrix + "
          f"{assertion_stats['without_rebuttal']:,} assertions")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
