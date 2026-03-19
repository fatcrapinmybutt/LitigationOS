#!/usr/bin/env python3
"""
Tool #217: Impeachment Engine
==============================
Cross-reference witness statements for contradictions and impeachment opportunities.
Queries: impeachment_items, impeachment_index, impeachment_packages,
         contradiction_map, watson_perjury_compilation, evidence_quotes
Outputs: IMPEACHMENT_ENGINE.md + impeachment_engine.json
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


def score_impeachment(severity, contradiction_type=None, perjury_type=None):
    """Score impeachment opportunity: strong / moderate / weak."""
    sev = str(severity).upper() if severity else ""
    if sev in ("CRITICAL", "5") or (perjury_type and "perjury" in str(perjury_type).lower()):
        return "strong"
    if sev in ("HIGH", "4") or contradiction_type in ("FALSE_ALLEGATION", "BEHAVIORAL_INCONSISTENCY"):
        return "strong"
    if sev in ("MEDIUM", "3"):
        return "moderate"
    return "weak"


def main():
    print("=" * 70)
    print("  TOOL #217 — IMPEACHMENT ENGINE")
    print("  Cross-referencing witness statements for contradictions")
    print("=" * 70)
    ts = datetime.now()

    conn = get_connection()

    # --- 1) Impeachment Index (curated high-value items) ---
    print("\n[1/5] Reading impeachment_index...")
    curated = []
    try:
        rows = conn.execute("SELECT * FROM impeachment_index ORDER BY id").fetchall()
        for r in rows:
            curated.append({
                "id": r["id"],
                "target": r["target_witness"],
                "statement_a": safe_trunc(r["statement_a"], 300),
                "source_a": r["source_a"],
                "date_a": r["date_a"],
                "statement_b": safe_trunc(r["statement_b"], 300),
                "source_b": r["source_b"],
                "date_b": r["date_b"],
                "type": r["contradiction_type"],
                "value": r["impeachment_value"],
                "legal_use": r["legal_use"],
                "score": score_impeachment(r["impeachment_value"], r["contradiction_type"]),
            })
        print(f"  Found {len(curated)} curated impeachment entries")
    except Exception as e:
        print(f"  Error reading impeachment_index: {e}")

    # --- 2) Impeachment Items by speaker ---
    print("\n[2/5] Analyzing impeachment_items by speaker...")
    speaker_stats = defaultdict(lambda: {"total": 0, "critical": 0, "high": 0, "medium": 0, "types": defaultdict(int)})
    top_items = []
    try:
        rows = conn.execute("""
            SELECT speaker, item_type, severity, statement, contradicting_text, legal_hook
            FROM impeachment_items
            ORDER BY CASE severity
                WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            sp = r["speaker"] or "UNKNOWN"
            sev = (r["severity"] or "").upper()
            speaker_stats[sp]["total"] += 1
            if sev == "CRITICAL":
                speaker_stats[sp]["critical"] += 1
            elif sev == "HIGH":
                speaker_stats[sp]["high"] += 1
            elif sev == "MEDIUM":
                speaker_stats[sp]["medium"] += 1
            speaker_stats[sp]["types"][r["item_type"]] += 1

            if len(top_items) < 25 and sev in ("CRITICAL", "HIGH"):
                top_items.append({
                    "speaker": sp,
                    "type": r["item_type"],
                    "severity": r["severity"],
                    "statement": safe_trunc(r["statement"], 250),
                    "contradicting": safe_trunc(r["contradicting_text"], 250),
                    "legal_hook": r["legal_hook"],
                    "score": score_impeachment(r["severity"]),
                })
        print(f"  Processed {sum(s['total'] for s in speaker_stats.values())} items across {len(speaker_stats)} speakers")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 3) Impeachment Packages by party ---
    print("\n[3/5] Analyzing impeachment_packages...")
    packages_by_party = defaultdict(lambda: {"total": 0, "by_category": defaultdict(int), "by_severity": defaultdict(int)})
    try:
        rows = conn.execute("""
            SELECT target_party, category, mre_rule, severity, COUNT(*) as cnt
            FROM impeachment_packages
            GROUP BY target_party, category, severity
        """).fetchall()
        for r in rows:
            party = r["target_party"]
            packages_by_party[party]["total"] += r["cnt"]
            packages_by_party[party]["by_category"][r["category"]] += r["cnt"]
            packages_by_party[party]["by_severity"][r["severity"]] += r["cnt"]
        for party, data in packages_by_party.items():
            print(f"  {party}: {data['total']} packages")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 4) Contradiction Map analysis ---
    print("\n[4/5] Analyzing contradiction_map...")
    contradiction_stats = {"total": 0, "by_type": defaultdict(int), "by_severity": defaultdict(int), "top_items": []}
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()[0]
        contradiction_stats["total"] = cnt

        type_rows = conn.execute("""
            SELECT contradiction_type, severity, COUNT(*) as cnt
            FROM contradiction_map
            GROUP BY contradiction_type, severity
            ORDER BY cnt DESC
        """).fetchall()
        for r in type_rows:
            contradiction_stats["by_type"][r["contradiction_type"]] += r["cnt"]
            contradiction_stats["by_severity"][r["severity"]] += r["cnt"]

        top_contradictions = conn.execute("""
            SELECT source_a_type, source_a_text, source_b_type, source_b_text,
                   contradiction_type, severity, legal_impact
            FROM contradiction_map
            WHERE severity IN ('HIGH', 'CRITICAL')
            ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 ELSE 2 END
            LIMIT 15
        """).fetchall()
        for r in top_contradictions:
            contradiction_stats["top_items"].append({
                "source_a": f"{r['source_a_type']}: {safe_trunc(r['source_a_text'], 150)}",
                "source_b": f"{r['source_b_type']}: {safe_trunc(r['source_b_text'], 150)}",
                "type": r["contradiction_type"],
                "severity": r["severity"],
                "legal_impact": safe_trunc(r["legal_impact"], 200),
                "score": score_impeachment(r["severity"], r["contradiction_type"]),
            })
        print(f"  {cnt} contradictions mapped ({dict(contradiction_stats['by_severity'])})")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 5) Watson Perjury Compilation ---
    print("\n[5/5] Analyzing watson_perjury_compilation...")
    perjury_stats = {"total": 0, "by_member": defaultdict(int), "by_type": defaultdict(int),
                     "by_severity": defaultdict(int), "top_items": []}
    try:
        cnt = conn.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()[0]
        perjury_stats["total"] = cnt

        rows = conn.execute("""
            SELECT watson_member, perjury_type, severity_score, COUNT(*) as cnt
            FROM watson_perjury_compilation
            GROUP BY watson_member, perjury_type, severity_score
        """).fetchall()
        for r in rows:
            perjury_stats["by_member"][r["watson_member"]] += r["cnt"]
            perjury_stats["by_type"][r["perjury_type"]] += r["cnt"]
            perjury_stats["by_severity"][str(r["severity_score"])] += r["cnt"]

        top_perjury = conn.execute("""
            SELECT watson_member, statement_text, contradicting_evidence,
                   perjury_type, severity_score, mcr_mre_authority
            FROM watson_perjury_compilation
            WHERE severity_score >= 4
            ORDER BY severity_score DESC
            LIMIT 10
        """).fetchall()
        for r in top_perjury:
            perjury_stats["top_items"].append({
                "member": r["watson_member"],
                "statement": safe_trunc(r["statement_text"], 200),
                "contradicting": safe_trunc(r["contradicting_evidence"], 200),
                "type": r["perjury_type"],
                "severity": r["severity_score"],
                "authority": r["mcr_mre_authority"],
                "score": score_impeachment(r["severity_score"], perjury_type=r["perjury_type"]),
            })
        print(f"  {cnt} perjury entries ({dict(perjury_stats['by_member'])})")
    except Exception as e:
        print(f"  Error: {e}")

    conn.close()

    # --- Aggregate scoring ---
    total_strong = sum(1 for i in top_items if i["score"] == "strong")
    total_strong += sum(1 for i in contradiction_stats.get("top_items", []) if i["score"] == "strong")
    total_strong += sum(1 for i in perjury_stats.get("top_items", []) if i["score"] == "strong")
    total_strong += sum(1 for i in curated if i["score"] == "strong")

    total_moderate = sum(1 for i in top_items if i["score"] == "moderate")
    total_items = (sum(s["total"] for s in speaker_stats.values()) +
                   contradiction_stats["total"] + perjury_stats["total"])

    # === BUILD MARKDOWN REPORT ===
    lines = [
        "# ⚔️ IMPEACHMENT ENGINE — Tool #217",
        f"*Generated: {ts.strftime('%Y-%m-%d %H:%M')}*\n",
        "---\n",
        "## Executive Summary\n",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Impeachment Items (all) | {sum(s['total'] for s in speaker_stats.values()):,} |",
        f"| Contradiction Map Entries | {contradiction_stats['total']:,} |",
        f"| Perjury Compilation Entries | {perjury_stats['total']:,} |",
        f"| Impeachment Packages | {sum(d['total'] for d in packages_by_party.values()):,} |",
        f"| Curated Index Entries | {len(curated)} |",
        f"| **STRONG Impeachment Opps** | **{total_strong}** |",
        "",
        "---\n",
        "## Curated Impeachment Index (Highest Value)\n",
    ]

    for c in curated:
        lines.extend([
            f"### [{c['score'].upper()}] {c['target']} — {c['type']}",
            f"- **Statement A** ({c['source_a']}, {c['date_a']}): {c['statement_a']}",
            f"- **Statement B** ({c['source_b']}, {c['date_b']}): {c['statement_b']}",
            f"- **Legal Use**: {c['legal_use']}",
            "",
        ])

    lines.extend(["---\n", "## Speaker Breakdown\n",
                   "| Speaker | Total | Critical | High | Medium | Top Types |",
                   "|---------|-------|----------|------|--------|-----------|"])
    for sp, data in sorted(speaker_stats.items(), key=lambda x: x[1]["total"], reverse=True):
        top_types = ", ".join(f"{k}({v})" for k, v in sorted(data["types"].items(), key=lambda x: -x[1])[:3])
        lines.append(f"| {sp} | {data['total']:,} | {data['critical']:,} | {data['high']:,} | {data['medium']:,} | {top_types} |")

    lines.extend(["", "---\n", "## Impeachment Packages by Party\n"])
    for party, data in sorted(packages_by_party.items(), key=lambda x: x[1]["total"], reverse=True):
        lines.append(f"### {party} ({data['total']:,} packages)")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, cnt in sorted(data["by_category"].items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {cnt:,} |")
        lines.append("")

    lines.extend(["---\n", "## Contradiction Map Summary\n",
                   f"**Total contradictions**: {contradiction_stats['total']:,}\n",
                   "| Severity | Count |", "|----------|-------|"])
    for sev, cnt in sorted(contradiction_stats["by_severity"].items(), key=lambda x: -x[1]):
        lines.append(f"| {sev} | {cnt:,} |")
    lines.extend(["", "| Type | Count |", "|------|-------|"])
    for t, cnt in sorted(contradiction_stats["by_type"].items(), key=lambda x: -x[1]):
        lines.append(f"| {t} | {cnt:,} |")

    lines.extend(["", "---\n", "## Top STRONG Impeachment Opportunities\n"])
    for i, item in enumerate(top_items[:15], 1):
        lines.extend([
            f"### {i}. [{item['score'].upper()}] {item['speaker']} — {item['type']}",
            f"- **Severity**: {item['severity']}",
            f"- **Statement**: {item['statement']}",
            f"- **Contradicted by**: {item['contradicting']}",
            f"- **Legal hook**: {item['legal_hook']}",
            "",
        ])

    lines.extend(["---\n", "## Watson Perjury Summary\n",
                   f"**Total entries**: {perjury_stats['total']:,}\n",
                   "| Member | Count |", "|--------|-------|"])
    for m, cnt in sorted(perjury_stats["by_member"].items(), key=lambda x: -x[1]):
        lines.append(f"| {m} | {cnt:,} |")
    lines.extend(["", "| Type | Count |", "|------|-------|"])
    for t, cnt in sorted(perjury_stats["by_type"].items(), key=lambda x: -x[1]):
        lines.append(f"| {t} | {cnt:,} |")

    lines.extend([
        "",
        "---",
        f"*Tool #217 — impeachment_engine.py — {ts.strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    md_path = REPORTS_DIR / "IMPEACHMENT_ENGINE.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Markdown: {md_path}")

    # === BUILD JSON ===
    json_data = {
        "generated": ts.isoformat(),
        "tool": "Impeachment Engine (#217)",
        "summary": {
            "impeachment_items_total": sum(s["total"] for s in speaker_stats.values()),
            "contradiction_map_total": contradiction_stats["total"],
            "perjury_compilation_total": perjury_stats["total"],
            "impeachment_packages_total": sum(d["total"] for d in packages_by_party.values()),
            "curated_index_total": len(curated),
            "strong_opportunities": total_strong,
            "moderate_opportunities": total_moderate,
        },
        "curated_index": curated,
        "speaker_breakdown": {sp: {"total": d["total"], "critical": d["critical"],
                                    "high": d["high"], "medium": d["medium"],
                                    "top_types": dict(d["types"])}
                              for sp, d in speaker_stats.items()},
        "packages_by_party": {p: {"total": d["total"],
                                   "by_category": dict(d["by_category"]),
                                   "by_severity": dict(d["by_severity"])}
                              for p, d in packages_by_party.items()},
        "contradiction_stats": {
            "total": contradiction_stats["total"],
            "by_type": dict(contradiction_stats["by_type"]),
            "by_severity": dict(contradiction_stats["by_severity"]),
            "top_items": contradiction_stats["top_items"],
        },
        "perjury_stats": {
            "total": perjury_stats["total"],
            "by_member": dict(perjury_stats["by_member"]),
            "by_type": dict(perjury_stats["by_type"]),
            "by_severity": dict(perjury_stats["by_severity"]),
            "top_items": perjury_stats["top_items"],
        },
        "top_impeachment_items": top_items,
    }

    json_path = REPORTS_DIR / "impeachment_engine.json"
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding='utf-8')
    print(f"✅ JSON:     {json_path}")
    print(f"\n{'=' * 70}")
    print(f"  IMPEACHMENT ENGINE COMPLETE")
    print(f"  {total_strong} STRONG | {total_moderate} MODERATE | {total_items:,} total items processed")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
