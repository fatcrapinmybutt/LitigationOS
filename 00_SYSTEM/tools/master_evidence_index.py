#!/usr/bin/env python3
"""Tool #199 — Master Evidence Index by Lane.
Complete index of all evidence organized by case lane,
with DB-verified counts and cross-references."""

import json, os, sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_evidence_index():
    index = {
        "tool_id": 199,
        "title": "MASTER EVIDENCE INDEX BY LANE",
        "subtitle": "All Evidence Organized by Case Lane — DB-Verified",
        "lanes": [],
        "db_stats": {}
    }

    try:
        conn = sqlite3.connect(DB, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        
        row = conn.execute("""SELECT
            (SELECT COUNT(*) FROM evidence_quotes) as total_quotes,
            (SELECT COUNT(*) FROM judicial_violations) as total_violations,
            (SELECT COUNT(*) FROM documents) as total_docs,
            (SELECT COUNT(*) FROM claims) as total_claims
        """).fetchone()
        
        if row:
            index["db_stats"] = {
                "total_evidence_quotes": row[0],
                "total_judicial_violations": row[1],
                "total_documents": row[2],
                "total_claims": row[3],
            }
        
        conn.close()
    except Exception as e:
        index["db_stats"] = {"error": str(e)}

    index["lanes"] = [
        {
            "lane": "A", "name": "Custody (2024-001507-DC)",
            "evidence_types": [
                {"type": "Parenting fitness evidence", "description": "Andrew's 26 strengths, pediatric records, daycare records"},
                {"type": "Alienation evidence", "description": "Emily blocking contact, denying visits, disparaging Andrew"},
                {"type": "Best interest factor evidence", "description": "12 factors per MCL 722.23 — evidence for each"},
                {"type": "Child development evidence", "description": "Attachment theory, developmental milestones for L.D.W."},
                {"type": "Financial evidence", "description": "Income, expenses, child support calculations"},
            ]
        },
        {
            "lane": "B", "name": "Housing (2025-002760-CZ)",
            "evidence_types": [
                {"type": "Lease/tenancy records", "description": "Lease agreements, payment history, correspondence"},
                {"type": "Retaliation evidence", "description": "Timeline of landlord actions after complaints"},
                {"type": "Housing code violations", "description": "Inspection reports, photos, repair requests"},
            ]
        },
        {
            "lane": "D", "name": "PPO (2023-5907-PP)",
            "evidence_types": [
                {"type": "False allegation evidence", "description": "Emily's PPO claims vs. reality — contradictions"},
                {"type": "Straw incident evidence", "description": "No police report, no witnesses, no injuries"},
                {"type": "Continued contact evidence", "description": "Emily's voluntary contact after alleged threats"},
                {"type": "Perjury evidence", "description": "Sworn statements contradicted by other evidence"},
            ]
        },
        {
            "lane": "E", "name": "Judicial Misconduct (McNeill)",
            "evidence_types": [
                {"type": "Judicial violations", "description": f"{index['db_stats'].get('total_judicial_violations', 'N/A')} documented in DB"},
                {"type": "Ex parte communications", "description": "Documented instances of off-record contacts"},
                {"type": "Bias pattern evidence", "description": "5 categories, 14 indicators per tool #175"},
                {"type": "Canon violations", "description": "Specific MI Code of Judicial Conduct violations"},
                {"type": "Procedural due process violations", "description": "10 categories per tool #196"},
            ]
        },
        {
            "lane": "F", "name": "Appellate (COA 366810)",
            "evidence_types": [
                {"type": "Trial court record", "description": "All filings, orders, transcripts from 14th Circuit"},
                {"type": "Preservation of error", "description": "Issues preserved for appeal per tool #172"},
                {"type": "Legal error evidence", "description": "McNeill's misapplication of law — specific instances"},
                {"type": "Abuse of discretion evidence", "description": "Orders outside range of reasonable outcomes"},
            ]
        },
        {
            "lane": "C", "name": "Federal §1983 / Convergence",
            "evidence_types": [
                {"type": "Conspiracy evidence", "description": "Berry-Watson-Barnes-McNeill coordination"},
                {"type": "Constitutional violation evidence", "description": "Due process, equal protection, 1st Amendment"},
                {"type": "Damages evidence", "description": "Emotional distress, lost wages, parent-child bond damage"},
                {"type": "Pattern evidence", "description": "Cross-lane evidence showing systematic rights deprivation"},
            ]
        },
    ]

    index["total_types"] = sum(len(l["evidence_types"]) for l in index["lanes"])
    return index

def main():
    idx = build_evidence_index()
    md_path = os.path.join(REPORT_DIR, 'MASTER_EVIDENCE_INDEX.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {idx['title']}\n\n*{idx['subtitle']}*\n\n")
        db = idx["db_stats"]
        f.write("## DB Totals\n\n")
        f.write(f"| Metric | Count |\n|--------|-------|\n")
        for k, v in db.items():
            f.write(f"| {k} | {v:,} |\n" if isinstance(v, int) else f"| {k} | {v} |\n")
        f.write(f"\n**{idx['total_types']} evidence types across {len(idx['lanes'])} lanes**\n\n")
        for lane in idx["lanes"]:
            f.write(f"## Lane {lane['lane']}: {lane['name']}\n\n")
            for et in lane["evidence_types"]:
                f.write(f"- **{et['type']}:** {et['description']}\n")
            f.write("\n")
        f.write(f"---\n*Tool #199 | {idx['total_types']} evidence types*\n")
    json_path = os.path.join(REPORT_DIR, 'master_evidence_index.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(idx, f, indent=2)
    print(f"Tool #199 — MASTER EVIDENCE INDEX")
    print(f"  {idx['total_types']} evidence types across {len(idx['lanes'])} lanes")
    print(f"  DB: {idx['db_stats'].get('total_evidence_quotes', 'N/A')} quotes, {idx['db_stats'].get('total_judicial_violations', 'N/A')} violations")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
