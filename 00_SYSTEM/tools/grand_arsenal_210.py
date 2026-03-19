#!/usr/bin/env python3
"""
Tool #210: Grand Arsenal 210 Milestone
=========================================
210-tool milestone report. Focuses on the three active tracks:
1. Filing hardening (F3/F6/F10 court-ready)
2. Evidence processing (PDF scan + indexing)
3. Agent evolution (E03, E04 new agents)

Reports cumulative platform stats and next priorities.
"""
import json, os, sys, sqlite3, glob
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
TOOLS_DIR = os.path.dirname(__file__)
AGENTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'pipeline', 'agents')

def main():
    print("=" * 60)
    print("TOOL #210: GRAND ARSENAL 210 MILESTONE")
    print("=" * 60)
    
    tool_count = len(glob.glob(os.path.join(TOOLS_DIR, '*.py')))
    md_reports = len(glob.glob(os.path.join(REPORT_DIR, '*.md')))
    json_reports = len(glob.glob(os.path.join(REPORT_DIR, '*.json')))
    agent_count = len(glob.glob(os.path.join(AGENTS_DIR, '*.py'))) if os.path.isdir(AGENTS_DIR) else 0
    
    db_stats = {}
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        db_stats['tables'] = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        db_stats['size_gb'] = round(os.path.getsize(DB_PATH) / (1024**3), 1)
        
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM evidence_quotes) AS eq,
                (SELECT COUNT(*) FROM judicial_violations) AS jv
        """).fetchone()
        db_stats['evidence_quotes'] = row[0]
        db_stats['judicial_violations'] = row[1]
        
        try:
            db_stats['pdf_index'] = conn.execute("SELECT COUNT(*) FROM pdf_evidence_index").fetchone()[0]
        except:
            db_stats['pdf_index'] = 0
        
        conn.close()
    except Exception as e:
        db_stats['error'] = str(e)
    
    report = {
        "tool_id": 210,
        "milestone": "210 TOOLS — TRIPLE-TRACK CONVERGENCE",
        "generated": datetime.now().isoformat(),
        "platform_stats": {
            "tool_files": tool_count,
            "pipeline_agents": agent_count,
            "md_reports": md_reports,
            "json_reports": json_reports,
            "total_reports": md_reports + json_reports,
            "db_tables": db_stats.get('tables', 0),
            "db_size_gb": db_stats.get('size_gb', 0),
            "evidence_quotes": db_stats.get('evidence_quotes', 0),
            "judicial_violations": db_stats.get('judicial_violations', 0),
            "pdf_index_entries": db_stats.get('pdf_index', 0),
        },
        "active_tracks": {
            "track_2_filing": {
                "name": "Filing Hardening",
                "status": "IN PROGRESS",
                "details": "F3/F6/F10 GO packages being scanned for court-readiness. E04 agent deployed.",
                "new_tools": ["#206 Exhibit Compiler", "#207 Affidavit Guide", "#208 Service Calculator"]
            },
            "track_3_evidence": {
                "name": "Deep Evidence Processing",
                "status": "IN PROGRESS",
                "details": "E03 agent scanning C:/F:/G: drives. 8,422 PDFs found, indexing into pdf_evidence_index table.",
                "new_agents": ["E03 PDF Evidence Processor"]
            },
            "track_4_evolution": {
                "name": "Agent Fleet Evolution",
                "status": "IN PROGRESS",
                "details": "New pipeline agents E03, E04 created. Tools #201-210 built.",
                "new_agents": ["E03 PDF Evidence Processor", "E04 Filing Hardener"],
                "new_tools": ["#201-210 (mediation, experts, formatting, contacts, exhibits, affidavits, service, simulator)"]
            }
        },
        "milestones_achieved": [
            "50 tools (Wave 6)", "100 tools (Wave 11)", "120 tools (Wave 13)",
            "130 tools (Wave 14)", "140 tools (Wave 15)", "150 tools (Wave 16)",
            "160 tools (Wave 17)", "170 tools (Wave 18)", "180 tools (Wave 19)",
            "190 tools (Wave 19)", "200 tools (Wave 20)", "205 tools (Wave 21-pending)",
            "210 tools (THIS MILESTONE)"
        ],
        "next_priorities": [
            "Complete E03 PDF indexing across all drives",
            "Complete E04 filing hardening scan → fix blockers",
            "Build exhibit packages for F3/F6/F10 from indexed evidence",
            "Auto-fill court forms using DB data",
            "Create E05 agent: Form Auto-Filler",
            "Build tools #211-215: discovery tools, evidence timeline, witness list"
        ]
    }
    
    json_path = os.path.join(REPORT_DIR, 'GRAND_ARSENAL_210.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'GRAND_ARSENAL_210.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 🏆 Grand Arsenal 210 — Triple-Track Convergence (Tool #210)\n\n")
        f.write(f"Generated: {report['generated']}\n\n")
        f.write("## Platform Stats\n\n")
        f.write("| Metric | Count |\n|--------|-------|\n")
        for k, v in report['platform_stats'].items():
            f.write(f"| {k.replace('_', ' ').title()} | {v:,} |\n")
        
        f.write("\n## Active Tracks\n\n")
        for tid, track in report['active_tracks'].items():
            f.write(f"### {track['name']} — {track['status']}\n")
            f.write(f"{track['details']}\n\n")
        
        f.write("## Milestones\n\n")
        for m in report['milestones_achieved']:
            f.write(f"- ✅ {m}\n")
        
        f.write("\n## Next Priorities\n\n")
        for p in report['next_priorities']:
            f.write(f"- → {p}\n")
    
    print(f"\n✅ Grand Arsenal 210 Milestone")
    print(f"   Tools: {tool_count} | Agents: {agent_count}")
    print(f"   Reports: {md_reports + json_reports}")
    print(f"   DB: {db_stats.get('tables', 0)} tables, {db_stats.get('size_gb', 0)} GB")
    print(f"   PDF Index: {db_stats.get('pdf_index', 0)} entries")
    print(f"   Reports: {md_path}")
    return report

if __name__ == '__main__':
    main()
