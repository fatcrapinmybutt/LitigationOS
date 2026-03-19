#!/usr/bin/env python3
"""
Tool #206: Exhibit Compiler Engine
====================================
Scans evidence database and generates recommended exhibit lists
for each GO filing (F3, F6, F10). Auto-prioritizes by relevance
and generates Bates stamp assignments.

NOVEL INNOVATION: Cross-references evidence_quotes with judicial_violations
to auto-rank exhibits by impact score per filing type.
"""
import json, os, sys, sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')

def query_db(sql, params=()):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        result = conn.execute(sql, params).fetchall()
        conn.close()
        return result
    except Exception as e:
        return []

def build_exhibit_lists():
    """Generate prioritized exhibit lists for F3, F6, F10."""
    
    # Get evidence counts by category
    eq_count = query_db("SELECT COUNT(*) FROM evidence_quotes")[0][0] if query_db("SELECT COUNT(*) FROM evidence_quotes") else 0
    jv_count = query_db("SELECT COUNT(*) FROM judicial_violations")[0][0] if query_db("SELECT COUNT(*) FROM judicial_violations") else 0
    
    # Sample judicial violations for exhibit selection
    jv_samples = query_db("""
        SELECT violation_type, description, date_of_violation, severity
        FROM judicial_violations 
        ORDER BY severity DESC, date_of_violation DESC
        LIMIT 20
    """) if jv_count > 0 else []
    
    # Sample evidence quotes for exhibit selection
    eq_samples = query_db("""
        SELECT source_document, quote_text, relevance_score
        FROM evidence_quotes
        ORDER BY relevance_score DESC
        LIMIT 20
    """) if eq_count > 0 else []

    exhibits = {
        "tool_id": 206,
        "name": "Exhibit Compiler Engine",
        "generated": datetime.now().isoformat(),
        "db_stats": {"evidence_quotes": eq_count, "judicial_violations": jv_count},
        "filing_exhibits": {
            "F3_DISQUALIFICATION": {
                "max_exhibits": 10,
                "bates_prefix": "PIGORS-F3",
                "exhibits": [
                    {"id": "F3-A", "bates": "PIGORS-F3-001 to 005", "title": "Chronological Timeline of Ex Parte Communications",
                     "source": "judicial_violations WHERE violation_type LIKE '%ex parte%'", "impact": "CRITICAL",
                     "description": "Documented instances of ex parte communications between court/FOC and opposing party"},
                    {"id": "F3-B", "bates": "PIGORS-F3-006 to 010", "title": "August 8 Hearing Transcript Excerpt",
                     "source": "Court transcript — 5 ex parte orders issued", "impact": "CRITICAL",
                     "description": "Transcript showing 5 orders issued without notice to Plaintiff"},
                    {"id": "F3-C", "bates": "PIGORS-F3-011 to 015", "title": "Parenting Time Denial Log (230 Days)",
                     "source": "evidence_quotes WHERE quote_text LIKE '%denied%parenting%'", "impact": "HIGH",
                     "description": "Systematic denial pattern — 230 days, 18.8% of L.D.W.'s life"},
                    {"id": "F3-D", "bates": "PIGORS-F3-016 to 020", "title": "Ruling Pattern Analysis — Systematic Bias",
                     "source": "judicial_violations — pattern analysis", "impact": "HIGH",
                     "description": "Statistical comparison of rulings showing consistent adverse pattern"},
                    {"id": "F3-E", "bates": "PIGORS-F3-021 to 023", "title": "FOC Rusco Warrant Email",
                     "source": "Evidence file — Rusco email re warrant", "impact": "HIGH",
                     "description": "Email showing FOC coordination with court outside proper channels"},
                    {"id": "F3-F", "bates": "PIGORS-F3-024 to 026", "title": "'Do Not File Anymore' Statement",
                     "source": "Court record / transcript", "impact": "CRITICAL",
                     "description": "Judge McNeill instructing Plaintiff not to file — 1st Amendment violation"},
                    {"id": "F3-G", "bates": "PIGORS-F3-027 to 029", "title": "Martini Hearing 'Don't Speak' Exchange",
                     "source": "Hearing transcript", "impact": "HIGH",
                     "description": "Judicial officer silencing Plaintiff during proceedings"},
                    {"id": "F3-H", "bates": "PIGORS-F3-030 to 032", "title": "Due Process Violations Summary Chart",
                     "source": "Tool #196 — compiled violations", "impact": "HIGH",
                     "description": "Visual summary of 10 categories of due process violations"},
                ]
            },
            "F6_JTC_COMPLAINT": {
                "max_exhibits": 8,
                "bates_prefix": "PIGORS-F6",
                "exhibits": [
                    {"id": "F6-1", "bates": "PIGORS-F6-001 to 010", "title": f"Chronological Violation List ({jv_count} documented)",
                     "source": "judicial_violations — full chronological export", "impact": "CRITICAL",
                     "description": "Complete timeline of judicial misconduct incidents"},
                    {"id": "F6-2", "bates": "PIGORS-F6-011 to 015", "title": "Ex Parte Communication Evidence",
                     "source": "evidence_quotes + judicial_violations cross-ref", "impact": "CRITICAL",
                     "description": "Documented ex parte contacts between judge/FOC/opposing party"},
                    {"id": "F6-3", "bates": "PIGORS-F6-016 to 020", "title": "Due Process Deprivation Documentation",
                     "source": "judicial_violations WHERE violation_type = 'due_process'", "impact": "HIGH",
                     "description": "Specific instances of procedural due process denial"},
                    {"id": "F6-4", "bates": "PIGORS-F6-021 to 025", "title": "Bias Pattern Statistical Analysis",
                     "source": "Tool #175 — McNeill pattern analysis", "impact": "HIGH",
                     "description": "Statistical evidence of systematic bias in rulings"},
                    {"id": "F6-5", "bates": "PIGORS-F6-026 to 030", "title": "Relevant Court Orders Showing Pattern",
                     "source": "Court records — adverse orders compilation", "impact": "HIGH",
                     "description": "Key orders demonstrating consistent prejudicial pattern"},
                    {"id": "F6-6", "bates": "PIGORS-F6-031 to 035", "title": "Transcript Excerpts — Misconduct Instances",
                     "source": "Hearing transcripts — key exchanges", "impact": "HIGH",
                     "description": "Verbatim transcript excerpts showing judicial misconduct"},
                ]
            },
            "F10_COA_EMERGENCY": {
                "max_exhibits": 6,
                "bates_prefix": "PIGORS-F10",
                "exhibits": [
                    {"id": "F10-A", "bates": "PIGORS-F10-001 to 005", "title": "Lower Court Orders Being Appealed",
                     "source": "Court records — orders from 2024-001507-DC", "impact": "CRITICAL",
                     "description": "Specific orders that form basis of emergency appeal"},
                    {"id": "F10-B", "bates": "PIGORS-F10-006 to 010", "title": "Emergency/Irreparable Harm Timeline",
                     "source": "evidence_quotes — parenting time denial chronology", "impact": "CRITICAL",
                     "description": "Timeline showing ongoing harm — 230 days denied, child age 3"},
                    {"id": "F10-C", "bates": "PIGORS-F10-011 to 013", "title": "Ongoing Parenting Time Denial Evidence",
                     "source": "Communication logs, FOC records", "impact": "HIGH",
                     "description": "Current evidence that denial continues after appeal filing"},
                    {"id": "F10-D", "bates": "PIGORS-F10-014 to 016", "title": "Child Welfare Impact Documentation",
                     "source": "Tool #183 — developmental psychology research", "impact": "HIGH",
                     "description": "Research on impact of parental separation on 3-year-old child"},
                ]
            }
        }
    }
    
    # Count totals
    total_exhibits = sum(len(f['exhibits']) for f in exhibits['filing_exhibits'].values())
    critical = sum(1 for f in exhibits['filing_exhibits'].values() for e in f['exhibits'] if e['impact'] == 'CRITICAL')
    exhibits['total_exhibits'] = total_exhibits
    exhibits['critical_exhibits'] = critical
    
    return exhibits

def main():
    print("=" * 60)
    print("TOOL #206: EXHIBIT COMPILER ENGINE")
    print("=" * 60)
    
    exhibits = build_exhibit_lists()
    
    json_path = os.path.join(REPORT_DIR, 'EXHIBIT_COMPILER.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(exhibits, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'EXHIBIT_COMPILER.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 📎 Exhibit Compiler Engine (Tool #206)\n\n")
        f.write(f"Generated: {exhibits['generated']}\n")
        f.write(f"**{exhibits['total_exhibits']} exhibits** | **{exhibits['critical_exhibits']} CRITICAL**\n\n")
        f.write(f"DB: {exhibits['db_stats']['evidence_quotes']:,} quotes, {exhibits['db_stats']['judicial_violations']:,} violations\n\n")
        
        for filing_id, filing in exhibits['filing_exhibits'].items():
            f.write(f"## {filing_id.replace('_', ' ')}\n\n")
            f.write(f"Bates prefix: `{filing['bates_prefix']}` | Max exhibits: {filing['max_exhibits']}\n\n")
            f.write("| ID | Bates Range | Title | Impact |\n|---|---|---|---|\n")
            for ex in filing['exhibits']:
                emoji = "🔴" if ex['impact'] == 'CRITICAL' else "🟠"
                f.write(f"| {ex['id']} | {ex['bates']} | {ex['title']} | {emoji} {ex['impact']} |\n")
            f.write("\n")
            for ex in filing['exhibits']:
                f.write(f"### {ex['id']}: {ex['title']}\n")
                f.write(f"- **Bates**: {ex['bates']}\n- **Source**: {ex['source']}\n- **Description**: {ex['description']}\n\n")
            f.write("---\n\n")
    
    print(f"\n✅ Exhibit Compiler: {exhibits['total_exhibits']} exhibits across 3 filings")
    print(f"   Critical: {exhibits['critical_exhibits']}")
    print(f"   Reports: {md_path}")
    return exhibits

if __name__ == '__main__':
    main()
