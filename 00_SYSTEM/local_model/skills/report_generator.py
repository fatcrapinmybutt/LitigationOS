"""
Report Generator Skill (m50)
Generates comprehensive reports from LitigationOS database.

Functions:
    generate_case_status_report()      → current status of all lanes
    generate_evidence_summary()        → evidence strength across categories
    generate_filing_readiness_report() → which filings are ready
    generate_adversary_intel_report()  → adversary intelligence summary
    generate_full_litigation_report()  → master report combining all above
"""
import sys, io, sqlite3, os
from datetime import datetime
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'

def _connect():
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA busy_timeout=60000')
    return db


def generate_case_status_report(output_path=None):
    """Generate current status of all case lanes."""
    db = _connect()
    lines = []
    lines.append("# CASE STATUS REPORT")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append("")

    # Lane definitions
    lanes = {
        'A': ('2024-001507-DC', 'Custody', '14th Circuit', 'Hon. Jenny L. McNeill'),
        'B': ('Housing', 'Housing', 'Related', 'Various'),
        'D': ('2023-5907-PP', 'PPO', '14th Circuit', 'McNeill'),
        'E': ('Judicial Misconduct', 'JTC/MSC', 'JTC / MSC', 'Various'),
        'F': ('COA 366810', 'Appeal', 'MI Court of Appeals', 'Panel TBD'),
        'G': ('MSC Original Action', 'Superintending Control', 'MI Supreme Court', 'TBD'),
    }

    lines.append("## LANE STATUS")
    lines.append("")
    lines.append("| Lane | Case | Type | Court | Judge | Status |")
    lines.append("|------|------|------|-------|-------|--------|")

    # Get vehicles/filings status
    try:
        vehicles = {r[0]: r[1] for r in db.execute("SELECT vehicle_name, status FROM vehicles").fetchall()}
    except:
        vehicles = {}

    try:
        filing_status = {r[0]: (r[1], r[2]) for r in db.execute(
            "SELECT vehicle_name, status, total_score FROM filing_readiness"
        ).fetchall()}
    except:
        filing_status = {}

    for lane_id, (case_num, case_type, court, judge) in lanes.items():
        status = vehicles.get(case_num, 'Active')
        lines.append(f"| {lane_id} | {case_num} | {case_type} | {court} | {judge} | {status} |")

    lines.append("")

    # Deadlines
    lines.append("## UPCOMING DEADLINES")
    lines.append("")
    lines.append("| # | Case | Deadline | Due Date | Risk | Status |")
    lines.append("|---|------|----------|----------|------|--------|")
    deadlines = db.execute(
        "SELECT case_id, title, due_date_iso, risk_if_missed, status FROM deadlines ORDER BY due_date_iso"
    ).fetchall()
    for i, row in enumerate(deadlines, 1):
        lines.append(f"| {i} | {row[0]} | {row[1]} | {row[2]} | {(row[3] or '')[:50]} | {row[4]} |")
    lines.append("")

    # Claims summary
    total_claims = db.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    supported = db.execute("SELECT COUNT(*) FROM claims WHERE status='supported'").fetchone()[0]
    lines.append(f"## CLAIMS: {supported}/{total_claims} supported ({supported/max(total_claims,1)*100:.1f}%)")
    lines.append("")

    db.close()
    report = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


def generate_evidence_summary(output_path=None):
    """Generate evidence strength summary across all categories."""
    db = _connect()
    lines = []
    lines.append("# EVIDENCE SUMMARY REPORT")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append("")

    # Evidence quotes by category
    categories = db.execute("""
        SELECT evidence_category, COUNT(*), COUNT(DISTINCT document_id)
        FROM evidence_quotes
        WHERE evidence_category IS NOT NULL
        GROUP BY evidence_category
        ORDER BY COUNT(*) DESC
    """).fetchall()

    total_quotes = db.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
    total_docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    lines.append(f"## OVERVIEW")
    lines.append(f"- **Total Evidence Quotes:** {total_quotes:,}")
    lines.append(f"- **Total Documents:** {total_docs:,}")
    lines.append(f"- **Evidence Categories:** {len(categories)}")
    lines.append("")

    lines.append("## EVIDENCE BY CATEGORY")
    lines.append("")
    lines.append("| Category | Quotes | Documents |")
    lines.append("|----------|--------|-----------|")
    for cat, cnt, docs in categories[:25]:
        lines.append(f"| {cat} | {cnt:,} | {docs} |")
    lines.append("")

    # Source types
    sources = db.execute("""
        SELECT source_type, COUNT(*) FROM evidence_quotes
        WHERE source_type IS NOT NULL
        GROUP BY source_type ORDER BY COUNT(*) DESC
    """).fetchall()

    lines.append("## EVIDENCE BY SOURCE TYPE")
    lines.append("")
    lines.append("| Source Type | Count |")
    lines.append("|------------|-------|")
    for src, cnt in sources:
        lines.append(f"| {src} | {cnt:,} |")
    lines.append("")

    # Impeachment items
    imp_count = db.execute("SELECT COUNT(*) FROM impeachment_items").fetchone()[0]
    contradiction_count = db.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()[0]

    lines.append("## IMPEACHMENT & CONTRADICTIONS")
    lines.append(f"- **Impeachment Items:** {imp_count:,}")
    lines.append(f"- **Contradictions Mapped:** {contradiction_count:,}")
    lines.append("")

    # BIF evidence
    bif_count = db.execute("SELECT COUNT(*) FROM bif_evidence_links").fetchone()[0]
    lines.append(f"## BEST INTEREST FACTORS")
    lines.append(f"- **BIF Evidence Links:** {bif_count}")
    lines.append("")

    db.close()
    report = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


def generate_filing_readiness_report(output_path=None):
    """Generate filing readiness assessment."""
    db = _connect()
    lines = []
    lines.append("# FILING READINESS REPORT")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append("")

    filings = db.execute("""
        SELECT vehicle_name, status, authority_score, evidence_score, compliance_score,
               impeachment_score, total_score, gaps, strengths, best_source_path
        FROM filing_readiness
        ORDER BY total_score DESC
    """).fetchall()

    ready = sum(1 for f in filings if f[1] == 'READY')
    total = len(filings)

    lines.append(f"## OVERVIEW: {ready}/{total} filings READY")
    lines.append("")
    lines.append("| # | Filing | Status | Auth | Evid | Compl | Impeach | Total | Gaps |")
    lines.append("|---|--------|--------|------|------|-------|---------|-------|------|")
    for i, f in enumerate(filings, 1):
        status_emoji = "✅" if f[1] == 'READY' else "⚠️"
        lines.append(f"| {i} | {f[0]} | {status_emoji} {f[1]} | {f[2]} | {f[3]} | {f[4]} | {f[5]} | **{f[6]}** | {(f[7] or '')[:50]} |")
    lines.append("")

    # Authority chains
    chains = db.execute("SELECT COUNT(*) FROM authority_chains").fetchone()[0]
    complete = db.execute("SELECT COUNT(*) FROM authority_chains WHERE chain_complete=1").fetchone()[0]
    lines.append(f"## AUTHORITY CHAINS: {complete}/{chains} complete")
    lines.append("")

    # Gap tickets
    gaps = db.execute("SELECT COUNT(*) FROM gap_tickets").fetchone()[0]
    lines.append(f"## GAP TICKETS: {gaps} outstanding")
    lines.append("")

    db.close()
    report = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


def generate_adversary_intel_report(output_path=None):
    """Generate adversary intelligence summary."""
    db = _connect()
    lines = []
    lines.append("# ADVERSARY INTELLIGENCE REPORT")
    lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    lines.append("")

    # Adversary models
    models = db.execute("""
        SELECT filing_vehicle, attack_type, risk_level, COUNT(*)
        FROM adversary_models
        GROUP BY filing_vehicle, attack_type, risk_level
        ORDER BY filing_vehicle
    """).fetchall()

    total_models = db.execute("SELECT COUNT(*) FROM adversary_models").fetchone()[0]
    lines.append(f"## OVERVIEW: {total_models} adversary models across all filing vehicles")
    lines.append("")

    # By risk level
    risk_levels = db.execute("""
        SELECT risk_level, COUNT(*) FROM adversary_models GROUP BY risk_level ORDER BY COUNT(*) DESC
    """).fetchall()

    lines.append("## RISK DISTRIBUTION")
    lines.append("")
    lines.append("| Risk Level | Count |")
    lines.append("|-----------|-------|")
    for risk, cnt in risk_levels:
        lines.append(f"| {risk} | {cnt} |")
    lines.append("")

    # By filing vehicle
    vehicles = db.execute("""
        SELECT filing_vehicle, COUNT(*), GROUP_CONCAT(DISTINCT risk_level)
        FROM adversary_models GROUP BY filing_vehicle ORDER BY COUNT(*) DESC
    """).fetchall()

    lines.append("## ATTACKS BY FILING VEHICLE")
    lines.append("")
    lines.append("| Vehicle | Attacks | Risk Levels |")
    lines.append("|---------|---------|-------------|")
    for v, cnt, risks in vehicles:
        lines.append(f"| {v} | {cnt} | {risks} |")
    lines.append("")

    # Watson perjury
    perjury = db.execute("SELECT COUNT(*) FROM watson_perjury_compilation").fetchone()[0]
    lines.append(f"## WATSON PERJURY COMPILATION: {perjury:,} entries")
    lines.append("")

    # Berry ethics
    berry = db.execute("SELECT COUNT(*) FROM berry_ethics_violations").fetchone()[0]
    lines.append(f"## BERRY ETHICS VIOLATIONS: {berry} entries")
    lines.append("")

    # Judicial violations
    jv = db.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
    lines.append(f"## JUDICIAL VIOLATIONS (McNeill): {jv:,} documented")
    lines.append("")

    db.close()
    report = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
    return report


def generate_full_litigation_report(output_dir=None):
    """Generate master report combining all sub-reports."""
    if output_dir is None:
        output_dir = r'C:\Users\andre\LitigationOS\06_VISUALIZATIONS'
    os.makedirs(output_dir, exist_ok=True)

    reports = {}
    reports['case_status'] = generate_case_status_report(
        os.path.join(output_dir, 'REPORT_CASE_STATUS.md'))
    reports['evidence'] = generate_evidence_summary(
        os.path.join(output_dir, 'REPORT_EVIDENCE_SUMMARY.md'))
    reports['filing'] = generate_filing_readiness_report(
        os.path.join(output_dir, 'REPORT_FILING_READINESS.md'))
    reports['adversary'] = generate_adversary_intel_report(
        os.path.join(output_dir, 'REPORT_ADVERSARY_INTEL.md'))

    # Master combined report
    master = []
    master.append("# FULL LITIGATION REPORT — Pigors v. Watson")
    master.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    master.append(f"**System:** LitigationOS v8.0 — MANBEARPIG")
    master.append("")
    master.append("---")
    master.append("")
    for name, content in reports.items():
        master.append(content)
        master.append("")
        master.append("---")
        master.append("")

    master_path = os.path.join(output_dir, 'REPORT_FULL_LITIGATION.md')
    with open(master_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(master))

    return {
        'master': master_path,
        'sub_reports': list(reports.keys()),
        'total_lines': sum(r.count('\n') for r in reports.values())
    }


if __name__ == '__main__':
    print("Generating all reports...")
    result = generate_full_litigation_report()
    print(f"Master report: {result['master']}")
    print(f"Sub-reports: {result['sub_reports']}")
    print(f"Total lines: {result['total_lines']}")
    for f in os.listdir(r'C:\Users\andre\LitigationOS\06_VISUALIZATIONS'):
        if f.startswith('REPORT_'):
            fp = os.path.join(r'C:\Users\andre\LitigationOS\06_VISUALIZATIONS', f)
            print(f"  {f}: {os.path.getsize(fp):,} bytes")
