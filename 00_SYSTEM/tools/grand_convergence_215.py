#!/usr/bin/env python3
"""
Tool #215 — Grand Convergence Report
Milestone report: total tools, agents, reports, DB stats, filing status,
evidence indexed. Celebrates reaching 215 tools in the LitigationOS arsenal.
Output: GRAND_CONVERGENCE_215.md + GRAND_CONVERGENCE_215.json
"""
import sys, os, json, sqlite3, glob as globmod
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOLS_DIR.parent.parent
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row
    return conn


def count_tools():
    """Count Python tools in the tools directory."""
    tools = list(TOOLS_DIR.glob("*.py"))
    # Exclude helper/init files
    tool_files = [t for t in tools if not t.name.startswith("_") and t.name != "__init__.py"]
    return len(tool_files), [t.name for t in sorted(tool_files)]


def count_agents():
    """Count agent definitions across the repo."""
    counts = {}
    # Copilot agents
    copilot_agents_dir = REPO / ".copilot" / "agents"
    if copilot_agents_dir.exists():
        agents = [d.name for d in copilot_agents_dir.iterdir() if d.is_dir()]
        counts["copilot_agents"] = len(agents)
    else:
        counts["copilot_agents"] = 0

    # Pipeline agents
    pipeline_agents_dir = REPO / "00_SYSTEM" / "pipeline" / "agents"
    if pipeline_agents_dir.exists():
        agent_files = list(pipeline_agents_dir.glob("*.py"))
        counts["pipeline_agents"] = len([f for f in agent_files if not f.name.startswith("_")])
    else:
        counts["pipeline_agents"] = 0

    # Skills
    skills_dir = REPO / ".agents" / "skills"
    if not skills_dir.exists():
        skills_dir = REPO / "skills"
    if skills_dir.exists():
        skill_count = sum(1 for _ in skills_dir.rglob("SKILL.md"))
        counts["skills"] = skill_count
    else:
        counts["skills"] = 0

    counts["total"] = sum(counts.values())
    return counts


def count_reports():
    """Count generated reports."""
    json_reports = list(REPORTS_DIR.glob("*.json"))
    md_reports = list(REPORTS_DIR.glob("*.md"))
    return {"json": len(json_reports), "md": len(md_reports), "total": len(json_reports) + len(md_reports)}


def get_db_stats(conn):
    """Get comprehensive DB statistics."""
    stats = {}

    # Table count
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts_%'"
    ).fetchall()
    stats["tables"] = len(tables)
    stats["table_names"] = [r[0] for r in tables]

    # Row counts for key tables (consolidated query)
    row_counts = {}
    for t in stats["table_names"]:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            row_counts[t] = count
        except Exception:
            row_counts[t] = -1
    stats["row_counts"] = row_counts
    stats["total_rows"] = sum(v for v in row_counts.values() if v > 0)

    # DB file size
    try:
        stats["db_size_mb"] = round(DB_PATH.stat().st_size / (1024 * 1024), 1)
    except Exception:
        stats["db_size_mb"] = 0

    # Evidence counts
    try:
        stats["documents_count"] = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    except Exception:
        stats["documents_count"] = 0
    try:
        stats["evidence_quotes_count"] = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    except Exception:
        stats["evidence_quotes_count"] = 0
    try:
        stats["impeachment_items_count"] = conn.execute("SELECT COUNT(*) FROM impeachment_items").fetchone()[0]
    except Exception:
        stats["impeachment_items_count"] = 0

    # Filing readiness
    try:
        rows = conn.execute("SELECT vehicle_name, total_score, status FROM filing_readiness ORDER BY total_score DESC LIMIT 20").fetchall()
        stats["filing_readiness"] = [{"vehicle": r[0], "score": r[1], "status": r[2]} for r in rows]
    except Exception:
        stats["filing_readiness"] = []

    # FTS5 indexes
    fts_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'").fetchall()
    stats["fts5_indexes"] = len(fts_tables)

    return stats


def scan_filesystem():
    """Quick scan of LitigationOS filesystem."""
    fs_stats = {}

    # Count files by extension in key directories
    for subdir in ["00_SYSTEM", "11_CODE"]:
        dir_path = REPO / subdir
        if dir_path.exists():
            py_files = list(dir_path.rglob("*.py"))
            md_files = list(dir_path.rglob("*.md"))
            json_files = list(dir_path.rglob("*.json"))
            fs_stats[subdir] = {"py": len(py_files), "md": len(md_files), "json": len(json_files)}

    # Count databases
    db_dir = REPO / "databases"
    if db_dir.exists():
        dbs = list(db_dir.glob("*.db"))
        fs_stats["jurisdiction_dbs"] = len(dbs)
        fs_stats["jurisdiction_db_names"] = [d.name for d in dbs]
    else:
        fs_stats["jurisdiction_dbs"] = 0

    return fs_stats


def main():
    print("=" * 70)
    print("TOOL #215 — GRAND CONVERGENCE REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # 1. Tool count
    tool_count, tool_names = count_tools()
    print(f"[TOOLS] {tool_count} Python tools in 00_SYSTEM/tools/")

    # 2. Agent count
    agent_counts = count_agents()
    print(f"[AGENTS] {agent_counts['total']} total agents")
    for k, v in agent_counts.items():
        if k != "total":
            print(f"  {k}: {v}")

    # 3. Reports
    report_counts = count_reports()
    print(f"[REPORTS] {report_counts['total']} generated reports ({report_counts['json']} JSON, {report_counts['md']} MD)")

    # 4. DB stats
    conn = get_db_connection()
    db_stats = {}
    if conn:
        db_stats = get_db_stats(conn)
        conn.close()
        print(f"[DB] {db_stats['db_size_mb']} MB, {db_stats['tables']} tables, {db_stats['total_rows']:,} total rows")
        print(f"  Documents: {db_stats['documents_count']:,}")
        print(f"  Evidence Quotes: {db_stats['evidence_quotes_count']:,}")
        print(f"  Impeachment Items: {db_stats['impeachment_items_count']:,}")
        print(f"  FTS5 Indexes: {db_stats['fts5_indexes']}")
        if db_stats.get("filing_readiness"):
            print(f"  Filing Readiness Entries: {len(db_stats['filing_readiness'])}")
            for fr in db_stats["filing_readiness"][:5]:
                print(f"    {fr['vehicle']}: {fr['score']} ({fr['status']})")
    else:
        print("[WARN] DB not found.")

    # 5. Filesystem stats
    fs_stats = scan_filesystem()
    print(f"[FILESYSTEM]")
    for k, v in fs_stats.items():
        if isinstance(v, dict):
            print(f"  {k}: {v}")
        elif k == "jurisdiction_db_names":
            print(f"  Jurisdiction DBs: {', '.join(v)}")
        else:
            print(f"  {k}: {v}")

    # JSON report
    report = {
        "tool": "#215 — Grand Convergence Report",
        "milestone": "215 Tools Operational",
        "generated": datetime.now().isoformat(),
        "system": "LitigationOS — Event Horizon",
        "case": "Pigors v. Watson",
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "court": "14th Circuit Court, Family Division, Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "tools": {"count": tool_count, "names": tool_names},
        "agents": agent_counts,
        "reports": report_counts,
        "database": db_stats,
        "filesystem": fs_stats,
        "convergence_metrics": {
            "tools_target": 215,
            "tools_actual": tool_count,
            "milestone_reached": tool_count >= 215,
            "db_tables": db_stats.get("tables", 0),
            "evidence_indexed": db_stats.get("evidence_quotes_count", 0),
            "documents_ingested": db_stats.get("documents_count", 0),
        },
    }

    json_path = REPORTS_DIR / "GRAND_CONVERGENCE_215.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\n[OK] JSON: {json_path}")

    # MD report
    md = []
    md.append("# GRAND CONVERGENCE 215 — LitigationOS Milestone Report")
    md.append("")
    md.append("```")
    md.append("  _     _ _   _             _   _              ___  ____  ")
    md.append(" | |   (_) | (_)           | | (_)            / _ \\/ ___| ")
    md.append(" | |    _| |_ _  __ _  __ _| |_ _  ___  _ __| | | \\___ \\ ")
    md.append(" | |   | | __| |/ _` |/ _` | __| |/ _ \\| '_ \\ | | |___) |")
    md.append(" | |___| | |_| | (_| | (_| | |_| | (_) | | | | |_| |____/ ")
    md.append(" |_____|_|\\__|_|\\__, |\\__,_|\\__|_|\\___/|_| |_|\\___/|_____|")
    md.append("                 __/ |                                     ")
    md.append("                |___/     215 TOOLS OPERATIONAL            ")
    md.append("```")
    md.append("")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**System:** LitigationOS — Event Horizon")
    md.append(f"**Case:** Pigors v. Watson")
    md.append("")

    md.append("---")
    md.append("\n## Arsenal Summary")
    md.append("")
    md.append(f"| Component | Count |")
    md.append(f"|-----------|-------|")
    md.append(f"| Python Tools | **{tool_count}** |")
    md.append(f"| Total Agents | **{agent_counts['total']}** |")
    md.append(f"| Copilot Agents | {agent_counts.get('copilot_agents', 0)} |")
    md.append(f"| Pipeline Agents | {agent_counts.get('pipeline_agents', 0)} |")
    md.append(f"| Skills | {agent_counts.get('skills', 0)} |")
    md.append(f"| Generated Reports | **{report_counts['total']}** |")
    md.append("")

    if db_stats:
        md.append("---")
        md.append("\n## Database Intelligence")
        md.append("")
        md.append(f"| Metric | Value |")
        md.append(f"|--------|-------|")
        md.append(f"| Database Size | **{db_stats.get('db_size_mb', 0)} MB** |")
        md.append(f"| Tables | **{db_stats.get('tables', 0)}** |")
        md.append(f"| Total Rows | **{db_stats.get('total_rows', 0):,}** |")
        md.append(f"| Documents Ingested | **{db_stats.get('documents_count', 0):,}** |")
        md.append(f"| Evidence Quotes | **{db_stats.get('evidence_quotes_count', 0):,}** |")
        md.append(f"| Impeachment Items | **{db_stats.get('impeachment_items_count', 0):,}** |")
        md.append(f"| FTS5 Search Indexes | **{db_stats.get('fts5_indexes', 0)}** |")
        md.append("")

        # Top tables by row count
        if db_stats.get("row_counts"):
            md.append("### Top Tables by Row Count")
            md.append("")
            md.append("| Table | Rows |")
            md.append("|-------|------|")
            top_tables = sorted(db_stats["row_counts"].items(), key=lambda x: -x[1])[:20]
            for t, c in top_tables:
                if c > 0:
                    md.append(f"| {t} | {c:,} |")
            md.append("")

        # Filing readiness
        if db_stats.get("filing_readiness"):
            md.append("### Filing Readiness Scores")
            md.append("")
            md.append("| Vehicle | Score | Status |")
            md.append("|---------|-------|--------|")
            for fr in db_stats["filing_readiness"]:
                md.append(f"| {fr['vehicle']} | {fr['score']} | {fr['status']} |")
            md.append("")

    md.append("---")
    md.append("\n## Convergence Status")
    md.append("")
    reached = tool_count >= 215
    md.append(f"- Tool count target: **215**")
    md.append(f"- Actual tool count: **{tool_count}**")
    md.append(f"- Milestone: **{'REACHED' if reached else 'IN PROGRESS'}** {'!!!' if reached else ''}")
    md.append("")

    md.append("---")
    md.append(f"\n*Tool #215 — Grand Convergence Report — {datetime.now().isoformat()}*")

    md_path = REPORTS_DIR / "GRAND_CONVERGENCE_215.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] MD:   {md_path}")
    print(f"\n{'=' * 70}")
    print(f"GRAND CONVERGENCE 215 — MILESTONE {'REACHED' if reached else 'IN PROGRESS'}")
    print(f"  Tools: {tool_count} | Agents: {agent_counts['total']} | Reports: {report_counts['total']}")
    print(f"  DB: {db_stats.get('db_size_mb', 0)}MB / {db_stats.get('tables', 0)} tables / {db_stats.get('total_rows', 0):,} rows")
    print(f"{'=' * 70}")
    print("[DONE] Tool #215 complete.")


if __name__ == "__main__":
    main()
