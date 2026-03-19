#!/usr/bin/env python3
"""
Tool #221 — Filing Readiness Dashboard
========================================
Generates a comprehensive filing readiness dashboard for all 10 filings (F1-F10).

For each filing assesses:
  - Document completeness (% of required sections present)
  - Evidence attachment status
  - Court form requirements met
  - Service requirements identified
  - Physical action items remaining (signatures, notary, etc.)
  - Estimated filing fee
  - Priority order based on urgency + readiness

Output: FILING_READINESS_DASHBOARD.md + filing_readiness_dashboard.json
"""
import sys
import os
import json
import sqlite3
from datetime import datetime, date

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO, '00_SYSTEM', 'reports')

# Filing definitions (F1-F10)
FILING_DEFS = {
    "F1": {
        "name": "PPO Rescission Motion",
        "lane": "D",
        "case_number": "2023-5907-PP",
        "court": "14th Circuit Court",
        "description": "Motion to rescind/modify the PPO obtained by Emily on fabricated allegations.",
        "required_sections": ["motion_body", "brief_in_support", "affidavit", "proposed_order",
                              "proof_of_service", "exhibit_list"],
        "court_forms": ["MC 375", "CC 375"],
        "filing_fee": 0,
        "service_req": "Personal service on Emily A. Watson or her counsel",
    },
    "F2": {
        "name": "Parenting Time Enforcement",
        "lane": "A",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court, Family Division",
        "description": "Motion to enforce parenting time denied since August 2025.",
        "required_sections": ["motion_body", "brief_in_support", "affidavit", "proposed_order",
                              "proof_of_service", "parenting_time_log"],
        "court_forms": ["FOC 109", "FOC 104"],
        "filing_fee": 0,
        "service_req": "Service on FOC + Emily A. Watson",
    },
    "F3": {
        "name": "Motion to Disqualify Judge McNeill",
        "lane": "E",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court",
        "description": "Disqualification under MCR 2.003 for bias, ex parte contacts, selective evidence.",
        "required_sections": ["motion_body", "brief_in_support", "affidavit_of_bias",
                              "proposed_order", "proof_of_service", "exhibit_index"],
        "court_forms": ["MC 17"],
        "filing_fee": 0,
        "service_req": "Service on all parties + judge's clerk",
    },
    "F4": {
        "name": "Shady Oaks Housing Complaint",
        "lane": "B",
        "case_number": "2025-002760-CZ",
        "court": "14th Circuit Court, Civil Division",
        "description": "Civil complaint against Shady Oaks for housing discrimination/eviction.",
        "required_sections": ["complaint", "summons", "affidavit", "exhibit_list",
                              "proof_of_service", "civil_cover_sheet"],
        "court_forms": ["MC 01", "MC 11"],
        "filing_fee": 175,
        "service_req": "Process server on Shady Oaks management + registered agent",
    },
    "F5": {
        "name": "FOC Objection / Motion for De Novo Hearing",
        "lane": "A",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court, Family Division",
        "description": "Objection to FOC recommendation; request de novo hearing before judge.",
        "required_sections": ["objection", "brief_in_support", "proposed_order",
                              "proof_of_service", "foc_recommendation_copy"],
        "court_forms": ["FOC 13"],
        "filing_fee": 0,
        "service_req": "Service on FOC + Emily A. Watson",
    },
    "F6": {
        "name": "JTC Complaint (Judicial Tenure Commission)",
        "lane": "E",
        "case_number": "2024-001507-DC",
        "court": "Judicial Tenure Commission (Lansing)",
        "description": "Formal complaint against Judge McNeill for misconduct, ex parte contacts, bias.",
        "required_sections": ["complaint_letter", "factual_summary", "evidence_appendix",
                              "chronology", "authority_citations"],
        "court_forms": ["JTC Complaint Form"],
        "filing_fee": 0,
        "service_req": "Mail to JTC, 3034 W Grand Blvd Ste 8-450, Detroit MI 48202",
    },
    "F7": {
        "name": "Motion to Restore Custody / Parenting Time",
        "lane": "A",
        "case_number": "2024-001507-DC",
        "court": "14th Circuit Court, Family Division",
        "description": "Motion to modify custody and restore parenting time based on best interest factors.",
        "required_sections": ["motion_body", "brief_in_support", "best_interest_analysis",
                              "affidavit", "proposed_order", "proof_of_service", "exhibit_index"],
        "court_forms": ["FOC 89", "MC 17"],
        "filing_fee": 0,
        "service_req": "Service on Emily A. Watson + FOC (Pamela Rusco)",
    },
    "F8": {
        "name": "COA Application for Leave to Appeal",
        "lane": "F",
        "case_number": "COA 366810",
        "court": "Michigan Court of Appeals",
        "description": "Application for leave to appeal trial court orders.",
        "required_sections": ["application", "brief_on_appeal", "appendix",
                              "proof_of_service", "lower_court_orders", "claim_of_appeal"],
        "court_forms": ["COA Claim of Appeal", "COA Docketing Statement"],
        "filing_fee": 375,
        "service_req": "eFiling + service on all parties",
    },
    "F9": {
        "name": "MSC Application for Leave to Appeal",
        "lane": "F",
        "case_number": "Assigned on filing",
        "court": "Michigan Supreme Court",
        "description": "Application to the Supreme Court if COA denies leave.",
        "required_sections": ["application", "appendix", "proof_of_service",
                              "lower_court_opinion", "questions_presented"],
        "court_forms": ["MSC Application"],
        "filing_fee": 375,
        "service_req": "eFiling via TrueFiling + service on all parties",
    },
    "F10": {
        "name": "42 USC §1983 Federal Civil Rights Action",
        "lane": "A",
        "case_number": "To be assigned (W.D. Mich.)",
        "court": "US District Court, Western District of Michigan",
        "description": "Federal civil rights complaint for due process violations, 1A retaliation.",
        "required_sections": ["complaint", "civil_cover_sheet", "summons",
                              "affidavit_ifp", "exhibit_index", "proof_of_service"],
        "court_forms": ["AO 440 (Civil Cover Sheet)", "AO 239 (Summons)", "AO 240 (IFP Application)"],
        "filing_fee": 405,
        "service_req": "US Marshals Service for state actors; process server for private defendants",
    },
}


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_query(conn, sql, params=()):
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return []


def get_table_schema(conn, table):
    rows = safe_query(conn, f"PRAGMA table_info([{table}])")
    return {r['name']: r['type'] for r in rows}


def query_filing_readiness(conn):
    """Query filing_readiness table for existing scores."""
    schema = get_table_schema(conn, 'filing_readiness')
    if not schema:
        return {}
    cols = list(schema.keys())
    rows = safe_query(conn, f"SELECT * FROM filing_readiness")
    result = {}
    # Try to key by vehicle_name or filing_id
    for r in rows:
        key = r.get('vehicle_name') or r.get('filing_id') or r.get('name', str(r.get('id', '')))
        result[str(key)] = r
    return result


def query_omega_filing_readiness(conn):
    """Query omega_filing_readiness for OMEGA-assessed scores."""
    schema = get_table_schema(conn, 'omega_filing_readiness')
    if not schema:
        return {}
    rows = safe_query(conn, "SELECT * FROM omega_filing_readiness")
    result = {}
    for r in rows:
        key = r.get('vehicle_name') or r.get('filing_id') or str(r.get('id', ''))
        result[str(key)] = r
    return result


def query_claims_for_filing(conn, filing_id):
    """Find claims associated with a filing."""
    schema = get_table_schema(conn, 'claims')
    if not schema:
        return []
    # Try vehicle_name match
    if 'vehicle_name' in schema:
        rows = safe_query(conn,
            "SELECT * FROM claims WHERE vehicle_name LIKE ?", (f'%{filing_id}%',))
        if rows:
            return rows
    # Broader search
    for col in ['claim_type', 'filing_id', 'category', 'name']:
        if col in schema:
            rows = safe_query(conn,
                f"SELECT * FROM claims WHERE [{col}] LIKE ?", (f'%{filing_id}%',))
            if rows:
                return rows
    return []


def query_deadlines(conn, filing_id):
    """Find deadlines associated with a filing."""
    schema = get_table_schema(conn, 'deadlines')
    if not schema:
        return []
    for col in ['vehicle_name', 'filing_id', 'description', 'title', 'name']:
        if col in schema:
            rows = safe_query(conn,
                f"SELECT * FROM deadlines WHERE [{col}] LIKE ?", (f'%{filing_id}%',))
            if rows:
                return rows
    return []


def query_filing_packages(conn, filing_id):
    """Find filing packages for this filing."""
    schema = get_table_schema(conn, 'filing_packages')
    if not schema:
        return []
    for col in ['vehicle_name', 'filing_id', 'package_name', 'name']:
        if col in schema:
            rows = safe_query(conn,
                f"SELECT * FROM filing_packages WHERE [{col}] LIKE ?", (f'%{filing_id}%',))
            if rows:
                return rows
    return []


def query_evidence_links(conn, filing_id):
    """Count evidence linked to this filing."""
    count = 0
    for table in ['claim_evidence_links', 'evidence_claim_links', 'omega_claim_evidence_map']:
        schema = get_table_schema(conn, table)
        if not schema:
            continue
        for col in schema:
            if 'filing' in col.lower() or 'vehicle' in col.lower() or 'claim' in col.lower():
                rows = safe_query(conn,
                    f"SELECT COUNT(*) as cnt FROM [{table}] WHERE [{col}] LIKE ?",
                    (f'%{filing_id}%',))
                if rows:
                    count += rows[0].get('cnt', 0)
    return count


def query_filing_qa(conn, filing_id):
    """Check QA results for this filing."""
    for table in ['filing_qa_results', 'pre_filing_validation', 'filing_compliance']:
        schema = get_table_schema(conn, table)
        if not schema:
            continue
        for col in schema:
            if 'filing' in col.lower() or 'vehicle' in col.lower() or 'name' in col.lower():
                rows = safe_query(conn,
                    f"SELECT * FROM [{table}] WHERE [{col}] LIKE ? LIMIT 5",
                    (f'%{filing_id}%',))
                if rows:
                    return rows
    return []


def assess_filing(conn, fid, fdef, readiness_data, omega_data):
    """Assess a single filing's readiness."""
    # Get DB readiness scores
    db_readiness = None
    for key, val in readiness_data.items():
        if fid.lower() in key.lower() or fdef['name'].lower()[:15] in key.lower():
            db_readiness = val
            break

    omega_readiness = None
    for key, val in omega_data.items():
        if fid.lower() in key.lower() or fdef['name'].lower()[:15] in key.lower():
            omega_readiness = val
            break

    claims = query_claims_for_filing(conn, fid)
    deadlines = query_deadlines(conn, fid)
    packages = query_filing_packages(conn, fid)
    evidence_count = query_evidence_links(conn, fid)
    qa_results = query_filing_qa(conn, fid)

    # Calculate document completeness
    required = fdef['required_sections']
    # Check what exists in packages/DB
    sections_found = 0
    for pkg in packages:
        for val in pkg.values():
            if isinstance(val, str):
                for sec in required:
                    if sec.replace('_', ' ') in val.lower() or sec in val.lower():
                        sections_found += 1
                        break
    completeness_pct = min(100, int((sections_found / max(1, len(required))) * 100))

    # If we have DB readiness data, use its score
    if db_readiness:
        for key in ['readiness_score', 'score', 'readiness_pct', 'completion_pct', 'pct_complete']:
            if key in db_readiness and db_readiness[key] is not None:
                try:
                    completeness_pct = max(completeness_pct, int(float(db_readiness[key])))
                except (ValueError, TypeError):
                    pass

    # Determine urgency (0-100)
    urgency = 50  # default
    if deadlines:
        for dl in deadlines:
            for col in ['due_date_iso', 'deadline_date', 'due_date', 'date']:
                if col in dl and dl[col]:
                    try:
                        due = datetime.fromisoformat(str(dl[col])[:10]).date()
                        days_left = (due - date.today()).days
                        if days_left < 0:
                            urgency = 100  # overdue
                        elif days_left < 7:
                            urgency = 95
                        elif days_left < 14:
                            urgency = 85
                        elif days_left < 30:
                            urgency = 70
                    except Exception:
                        pass

    # Physical actions remaining
    physical_actions = []
    if completeness_pct < 100:
        physical_actions.append("Complete missing document sections")
    physical_actions.append("Obtain signature (Andrew Pigors)")
    if fdef['filing_fee'] > 0:
        physical_actions.append(f"Pay filing fee: ${fdef['filing_fee']}")
    if 'affidavit' in str(fdef['required_sections']):
        physical_actions.append("Notarize affidavit")
    physical_actions.append("Prepare proof of service")
    if 'eFiling' in fdef.get('service_req', ''):
        physical_actions.append("Set up eFiling account")

    # Priority score = urgency * 0.6 + completeness * 0.4
    priority_score = int(urgency * 0.6 + completeness_pct * 0.4)

    # Status determination
    if completeness_pct >= 90 and urgency >= 70:
        status = "READY — FILE IMMEDIATELY"
    elif completeness_pct >= 70:
        status = "NEAR-READY — Minor gaps"
    elif completeness_pct >= 40:
        status = "IN PROGRESS — Significant work needed"
    else:
        status = "EARLY STAGE — Major assembly required"

    return {
        "filing_id": fid,
        "name": fdef['name'],
        "lane": fdef['lane'],
        "case_number": fdef['case_number'],
        "court": fdef['court'],
        "status": status,
        "completeness_pct": completeness_pct,
        "urgency": urgency,
        "priority_score": priority_score,
        "required_sections": required,
        "sections_found": sections_found,
        "court_forms": fdef['court_forms'],
        "filing_fee": fdef['filing_fee'],
        "service_requirement": fdef['service_req'],
        "claims_count": len(claims),
        "evidence_linked": evidence_count,
        "deadlines_count": len(deadlines),
        "packages_count": len(packages),
        "qa_checks": len(qa_results),
        "physical_actions": physical_actions,
        "db_readiness_data": db_readiness,
        "omega_readiness_data": omega_readiness,
    }


def build_dashboard(conn):
    print("=" * 70)
    print("  Tool #221 — Filing Readiness Dashboard")
    print("=" * 70)

    # Pre-fetch readiness data
    print("\n[1/4] Querying filing_readiness tables...")
    readiness_data = query_filing_readiness(conn)
    print(f"  filing_readiness: {len(readiness_data)} records")
    omega_data = query_omega_filing_readiness(conn)
    print(f"  omega_filing_readiness: {len(omega_data)} records")

    # Get global counts
    print("\n[2/4] Querying global filing statistics...")
    global_stats = {}
    for table, label in [
        ('claims', 'Total claims'),
        ('deadlines', 'Active deadlines'),
        ('filing_packages', 'Filing packages'),
        ('evidence_quotes', 'Evidence quotes'),
    ]:
        rows = safe_query(conn, f"SELECT COUNT(*) as cnt FROM [{table}]")
        global_stats[label] = rows[0]['cnt'] if rows else 0
        print(f"  {label}: {global_stats[label]}")

    # Assess each filing
    print("\n[3/4] Assessing each filing (F1-F10)...")
    filings = {}
    for fid in sorted(FILING_DEFS.keys(), key=lambda x: int(x[1:])):
        fdef = FILING_DEFS[fid]
        assessment = assess_filing(conn, fid, fdef, readiness_data, omega_data)
        filings[fid] = assessment
        print(f"  {fid}: {assessment['status']} "
              f"(completeness={assessment['completeness_pct']}%, "
              f"urgency={assessment['urgency']}, "
              f"priority={assessment['priority_score']})")

    # Sort by priority
    print("\n[4/4] Generating priority order...")
    priority_order = sorted(filings.keys(),
                            key=lambda x: filings[x]['priority_score'], reverse=True)

    dashboard = {
        "tool": "Tool #221 — Filing Readiness Dashboard",
        "generated": datetime.now().isoformat(),
        "global_stats": global_stats,
        "total_filings": len(filings),
        "priority_order": priority_order,
        "filings": filings,
        "status_summary": {
            "ready": sum(1 for f in filings.values() if 'READY' in f['status'] and 'NEAR' not in f['status']),
            "near_ready": sum(1 for f in filings.values() if 'NEAR-READY' in f['status']),
            "in_progress": sum(1 for f in filings.values() if 'IN PROGRESS' in f['status']),
            "early_stage": sum(1 for f in filings.values() if 'EARLY STAGE' in f['status']),
        },
        "total_filing_fees": sum(f['filing_fee'] for f in filings.values()),
        "lane_breakdown": {},
    }

    # Lane breakdown
    for fid, f in filings.items():
        lane = f['lane']
        if lane not in dashboard['lane_breakdown']:
            dashboard['lane_breakdown'][lane] = []
        dashboard['lane_breakdown'][lane].append(fid)

    return dashboard


def write_markdown(dashboard, path):
    d = dashboard
    ss = d['status_summary']
    lines = [
        "# Filing Readiness Dashboard",
        f"*Generated: {d['generated']}*\n",
        "## Status Overview\n",
        "| Status | Count |",
        "|--------|-------|",
        f"| 🟢 READY — File Immediately | {ss['ready']} |",
        f"| 🟡 NEAR-READY — Minor gaps | {ss['near_ready']} |",
        f"| 🟠 IN PROGRESS — Significant work | {ss['in_progress']} |",
        f"| 🔴 EARLY STAGE — Major assembly | {ss['early_stage']} |",
        f"| **Total Filings** | **{d['total_filings']}** |",
        f"| **Total Filing Fees** | **${d['total_filing_fees']}** |",
        "",
        "## Global Database Statistics\n",
        "| Metric | Count |",
        "|--------|-------|",
    ]
    for label, count in d['global_stats'].items():
        lines.append(f"| {label} | {count:,} |")

    lines.extend(["", "## Priority Filing Order\n",
                   "| # | Filing | Status | Complete | Urgency | Priority | Fee |",
                   "|---|--------|--------|----------|---------|----------|-----|"])

    for i, fid in enumerate(d['priority_order'], 1):
        f = d['filings'][fid]
        lines.append(
            f"| {i} | **{fid}** {f['name']} | {f['status']} | "
            f"{f['completeness_pct']}% | {f['urgency']} | {f['priority_score']} | "
            f"${f['filing_fee']} |"
        )

    lines.extend(["", "## Detailed Filing Assessments\n"])

    for fid in d['priority_order']:
        f = d['filings'][fid]
        lines.append(f"### {fid}: {f['name']}")
        lines.append(f"**Status:** {f['status']}  ")
        lines.append(f"**Lane:** {f['lane']} | **Case:** {f['case_number']} | **Court:** {f['court']}\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Document Completeness | {f['completeness_pct']}% ({f['sections_found']}/{len(f['required_sections'])} sections) |")
        lines.append(f"| Evidence Linked | {f['evidence_linked']} items |")
        lines.append(f"| Claims in DB | {f['claims_count']} |")
        lines.append(f"| Deadlines | {f['deadlines_count']} |")
        lines.append(f"| Filing Packages | {f['packages_count']} |")
        lines.append(f"| QA Checks | {f['qa_checks']} |")
        lines.append(f"| Filing Fee | ${f['filing_fee']} |")
        lines.append(f"| Court Forms | {', '.join(f['court_forms'])} |")
        lines.append(f"| Service | {f['service_requirement']} |")
        lines.append("")

        if f['physical_actions']:
            lines.append("**Action Items:**")
            for action in f['physical_actions']:
                lines.append(f"- [ ] {action}")
            lines.append("")

    # Lane breakdown
    lines.append("## Lane Breakdown\n")
    lane_names = {"A": "Custody", "B": "Housing", "C": "Convergence",
                  "D": "PPO", "E": "Misconduct", "F": "Appellate"}
    for lane in sorted(d['lane_breakdown'].keys()):
        fids = d['lane_breakdown'][lane]
        lines.append(f"### Lane {lane} — {lane_names.get(lane, 'Unknown')}")
        for fid in fids:
            f = d['filings'][fid]
            lines.append(f"- **{fid}**: {f['name']} — {f['status']}")
        lines.append("")

    lines.append("---")
    lines.append("*Tool #221 — Filing Readiness Dashboard — LitigationOS*")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = get_connection()
    try:
        dashboard = build_dashboard(conn)

        json_path = os.path.join(REPORTS_DIR, 'filing_readiness_dashboard.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, default=str, ensure_ascii=False)
        print(f"\n[OK] JSON → {json_path}")

        md_path = os.path.join(REPORTS_DIR, 'FILING_READINESS_DASHBOARD.md')
        write_markdown(dashboard, md_path)
        print(f"[OK] MD   → {md_path}")

        ss = dashboard['status_summary']
        print(f"\n{'=' * 70}")
        print(f"  FILING READINESS DASHBOARD COMPLETE")
        print(f"  Ready: {ss['ready']} | Near: {ss['near_ready']} | "
              f"InProgress: {ss['in_progress']} | Early: {ss['early_stage']}")
        print(f"  Total fees: ${dashboard['total_filing_fees']} | "
              f"Priority #1: {dashboard['priority_order'][0] if dashboard['priority_order'] else 'N/A'}")
        print(f"{'=' * 70}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
