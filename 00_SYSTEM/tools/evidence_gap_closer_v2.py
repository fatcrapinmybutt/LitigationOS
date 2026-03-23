#!/usr/bin/env python3
"""Tool #255: Evidence Gap Closer
==================================
Identifies gaps in the evidence arsenal and generates acquisition plans.
For each of the 10 filings: analyzes available vs needed evidence across 5
categories: (1) Documents, (2) Witnesses, (3) FOIA/Subpoena, (4) Physical,
(5) Authentication gaps.

Queries: documents, claims, authority_chains, evidence_quotes, filing_readiness,
         evidence_gap_analysis, gap_tickets
Outputs: MD + JSON reports to 00_SYSTEM/reports/
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')


def s(v):
    """Safe string — prevent NoneType crashes."""
    return (v or "").lower()


# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(SCRIPT_DIR, '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

# --- Filing packages ---
FILING_MAP = {
    "F1": {
        "title": "Emergency Motion to Restore Parenting Time",
        "vehicle": "EMERGENCY_MOTION_RESTORE_PT",
        "evidence_needs": {
            "documents": ["Parenting time orders", "Denial communications", "School records showing exclusion",
                          "Supervised visit records", "FOC recommendations"],
            "witnesses": ["FOC caseworker (Pamela Rusco)", "Child's teacher", "Family members who witnessed denial"],
            "foia_subpoena": ["FOC parenting time logs", "School attendance records",
                              "CPS/DHHS investigation records"],
            "physical": ["Communication screenshots (texts, emails)", "Calendar of denied visits",
                         "Photos of child's room at father's home"],
            "authentication": ["Text message affidavit", "Email printout certification", "Calendar log sworn statement"],
        },
    },
    "F2": {
        "title": "Motion for Fraud Upon the Court",
        "vehicle": "FRAUD_UPON_COURT",
        "evidence_needs": {
            "documents": ["Original PPO application", "Contradicting prior statements",
                          "Police reports showing no violence", "Financial fraud documents"],
            "witnesses": ["Police officers from cited incidents", "Witnesses to false allegations"],
            "foia_subpoena": ["Police incident reports (FOIA)", "911 call recordings (FOIA)",
                              "Medical records contradicting claims"],
            "physical": ["Timeline of contradictory statements", "Side-by-side comparison exhibits"],
            "authentication": ["Certified police reports", "Court record certifications",
                               "Affidavit of perjury specifics"],
        },
    },
    "F3": {
        "title": "Motion for Disqualification of Judge",
        "vehicle": "JUDICIAL_DISQUALIFICATION",
        "evidence_needs": {
            "documents": ["Hearing transcripts showing bias", "Orders without statutory findings",
                          "Ex parte communication records", "Case assignment records"],
            "witnesses": ["Court reporter (transcript accuracy)", "Attorneys who witnessed bias"],
            "foia_subpoena": ["Judge's financial disclosures", "Court administrative records",
                              "Communication logs"],
            "physical": ["Transcript excerpts with bias highlighted", "Pattern analysis chart"],
            "authentication": ["Certified transcripts", "Court clerk certifications",
                               "Affidavit of personal experience"],
        },
    },
    "F4": {
        "title": "42 USC §1983 Civil Rights Complaint",
        "vehicle": "SECTION_1983_COMPLAINT",
        "evidence_needs": {
            "documents": ["All orders violating constitutional rights", "Due process violation records",
                          "Pattern of rights deprivation", "Similar cases in same court"],
            "witnesses": ["Constitutional law expert", "Other litigants with similar experiences"],
            "foia_subpoena": ["Court statistics on case outcomes", "Municipal insurance policies",
                              "Training records for officials"],
            "physical": ["Constitutional violation timeline", "Comparison with state statistics"],
            "authentication": ["Certified court records", "Expert declaration",
                               "Statistical analysis methodology affidavit"],
        },
    },
    "F5": {
        "title": "MSC Complaint for Superintending Control",
        "vehicle": "MSC_SUPERINTENDING_CONTROL",
        "evidence_needs": {
            "documents": ["Lower court orders exceeding jurisdiction", "Statutory mandate violations",
                          "Record of exhausted remedies"],
            "witnesses": ["N/A (documentary action)"],
            "foia_subpoena": ["Complete lower court file", "Administrative orders"],
            "physical": ["Complete chronological record index"],
            "authentication": ["Certified lower court record", "Affidavit of compliance with MCR 7.306"],
        },
    },
    "F6": {
        "title": "JTC Judicial Misconduct Complaint",
        "vehicle": "JTC_MISCONDUCT",
        "evidence_needs": {
            "documents": ["Hearing transcripts showing misconduct", "Orders violating canons",
                          "Ex parte communication evidence", "Prior complaints if any"],
            "witnesses": ["Attorneys, parties, court staff who witnessed misconduct"],
            "foia_subpoena": ["Prior JTC complaints against same judge", "Judicial discipline records"],
            "physical": ["Misconduct incident timeline", "Canon violation matrix"],
            "authentication": ["Certified transcripts", "Sworn statements from witnesses",
                               "Declaration under penalty of perjury"],
        },
    },
    "F7": {
        "title": "Motion to Modify Custody",
        "vehicle": "CUSTODY_MODIFICATION",
        "evidence_needs": {
            "documents": ["Current custody order", "Best interest factor evidence for each factor",
                          "School performance records", "Medical/mental health records",
                          "Communication records showing interference"],
            "witnesses": ["Child's therapist", "Teachers", "Pediatrician",
                          "Family members", "Community members"],
            "foia_subpoena": ["School records", "Medical records", "CPS investigation files",
                              "Police reports"],
            "physical": ["Father's home photos/video", "Activity documentation",
                         "Child's belongings at father's home"],
            "authentication": ["Medical records affidavit", "School records certification",
                               "Parenting time log sworn statement"],
        },
    },
    "F8": {
        "title": "COA Application for Leave to Appeal",
        "vehicle": "COA_APPLICATION_LEAVE",
        "evidence_needs": {
            "documents": ["Lower court decision/order appealed", "Trial court record",
                          "Transcript of relevant hearings", "Motion/objection preservation record"],
            "witnesses": ["N/A (appellate review of record)"],
            "foia_subpoena": ["Certified lower court file"],
            "physical": ["Issue preservation index", "Standard of review chart"],
            "authentication": ["Certified lower court order", "Certified transcripts",
                               "Verified statement in lieu of transcript (MCR 7.210(B)(3))"],
        },
    },
    "F9": {
        "title": "COA Appeal Brief (366810)",
        "vehicle": "COA_APPEAL_BRIEF",
        "evidence_needs": {
            "documents": ["Complete lower court record", "All relevant orders", "All transcripts",
                          "Exhibits admitted at trial", "Motions/briefs filed below"],
            "witnesses": ["N/A (appellate record only)"],
            "foia_subpoena": ["Any missing record items"],
            "physical": ["Appendix index", "Record page citations"],
            "authentication": ["Certified record on appeal", "Settlement statement if needed"],
        },
    },
    "F10": {
        "title": "AGC Attorney Grievance Commission Complaint",
        "vehicle": "AGC_MISCONDUCT",
        "evidence_needs": {
            "documents": ["Attorney filing containing false statements", "Contradicting evidence",
                          "Court records showing attorney misconduct", "Fee agreements if relevant"],
            "witnesses": ["Parties who witnessed misconduct", "Other attorneys familiar with case"],
            "foia_subpoena": ["Attorney discipline records", "Court filings by attorney"],
            "physical": ["Side-by-side false statement comparison", "MRPC violation matrix"],
            "authentication": ["Certified court records", "Declaration identifying false statements",
                               "Document comparison affidavit"],
        },
    },
}

# Evidence acquisition priority levels
PRIORITY_MAP = {
    "CRITICAL": "Must obtain before filing — without this, the claim fails",
    "HIGH": "Strongly needed — significantly strengthens the argument",
    "MEDIUM": "Helpful but not dispositive — filing possible without",
    "LOW": "Nice to have — adds depth but not essential",
}


# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def get_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    return [r[1] for r in rows]


def table_exists(conn, table):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone())


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []


# --- Analysis functions ---
def count_evidence_for_keywords(conn, keywords):
    """Count evidence quotes matching keywords."""
    if not table_exists(conn, 'evidence_quotes'):
        return 0
    cols = get_columns(conn, 'evidence_quotes')
    text_col = 'quote_text' if 'quote_text' in cols else ('text' if 'text' in cols else None)
    if not text_col:
        return 0
    total = 0
    for kw in keywords[:5]:
        rows = safe_query(conn, f"SELECT COUNT(*) FROM evidence_quotes WHERE [{text_col}] LIKE ?", (f'%{kw}%',))
        if rows:
            total += rows[0][0]
    return total


def count_documents_for_keywords(conn, keywords):
    """Count documents matching keywords."""
    if not table_exists(conn, 'documents'):
        return 0
    cols = get_columns(conn, 'documents')
    search_cols = [c for c in ['file_name', 'file_path', 'evidence_category'] if c in cols]
    if not search_cols:
        return 0
    total = 0
    for kw in keywords[:5]:
        for col in search_cols[:2]:
            rows = safe_query(conn, f"SELECT COUNT(*) FROM documents WHERE [{col}] LIKE ?", (f'%{kw}%',))
            if rows:
                total += rows[0][0]
    return total


def get_authority_gaps(conn, vehicle):
    """Find authority chains with gaps for this vehicle."""
    if not table_exists(conn, 'authority_chains'):
        return []
    cols = get_columns(conn, 'authority_chains')
    veh_col = 'filing_vehicle' if 'filing_vehicle' in cols else ('vehicle_name' if 'vehicle_name' in cols else None)
    complete_col = 'chain_complete' if 'chain_complete' in cols else None
    gap_col = 'gap_description' if 'gap_description' in cols else None

    if not veh_col:
        return []
    conditions = [f"[{veh_col}] LIKE ?"]
    params = [f'%{vehicle}%']
    if complete_col:
        conditions.append(f"[{complete_col}] = 0")
    sql = f"SELECT * FROM authority_chains WHERE {' AND '.join(conditions)}"
    return safe_query(conn, sql, tuple(params))


def get_claims_needing_evidence(conn, vehicle):
    """Find claims that need evidence."""
    if not table_exists(conn, 'claims'):
        return []
    cols = get_columns(conn, 'claims')
    status_col = 'status' if 'status' in cols else None
    results = []
    # Search by vehicle keywords in available columns
    keywords = vehicle.lower().replace('_', ' ').split()
    for kw in keywords[:3]:
        for search_col in ['classification', 'issue_id', 'proposition']:
            if search_col in cols:
                sql = f"SELECT * FROM claims WHERE [{search_col}] LIKE ?"
                if status_col:
                    sql += f" AND [{status_col}] LIKE '%need%'"
                sql += " LIMIT 10"
                rows = safe_query(conn, sql, (f'%{kw}%',))
                results.extend(rows)
    # Deduplicate
    seen = set()
    unique = []
    id_col = 'claim_id' if 'claim_id' in cols else None
    for r in results:
        d = dict(r)
        rid = d.get(id_col, str(d))
        if rid not in seen:
            seen.add(rid)
            unique.append(r)
    return unique[:15]


def get_existing_gaps(conn, vehicle):
    """Check evidence_gap_analysis and gap_tickets tables for existing gaps."""
    gaps = []
    for tbl in ['evidence_gap_analysis', 'gap_tickets', 'knowledge_gaps', 'convergence_gaps']:
        if not table_exists(conn, tbl):
            continue
        cols = get_columns(conn, tbl)
        # Search for vehicle-related gaps
        keywords = vehicle.lower().replace('_', ' ').split()
        for kw in keywords[:2]:
            for col in cols[:5]:
                try:
                    rows = safe_query(conn, f"SELECT * FROM [{tbl}] WHERE [{col}] LIKE ? LIMIT 5", (f'%{kw}%',))
                    for r in rows:
                        gaps.append({"table": tbl, "data": dict(r)})
                except Exception:
                    pass
    return gaps[:20]


def get_readiness(conn, vehicle):
    """Get filing readiness scores."""
    if not table_exists(conn, 'filing_readiness'):
        return None
    cols = get_columns(conn, 'filing_readiness')
    veh_col = 'vehicle_name' if 'vehicle_name' in cols else ('filing_vehicle' if 'filing_vehicle' in cols else None)
    if not veh_col:
        return None
    rows = safe_query(conn, f"SELECT * FROM filing_readiness WHERE [{veh_col}] LIKE ?", (f'%{vehicle}%',))
    return dict(rows[0]) if rows else None


def assess_gap_priority(category, available_count, needed_count):
    """Assign acquisition priority based on coverage."""
    if available_count == 0:
        return "CRITICAL"
    ratio = available_count / max(needed_count, 1)
    if ratio < 0.3:
        return "CRITICAL"
    elif ratio < 0.6:
        return "HIGH"
    elif ratio < 0.85:
        return "MEDIUM"
    return "LOW"


# --- Main analysis ---
def main():
    print("=" * 70)
    print("  TOOL #255: EVIDENCE GAP CLOSER")
    print("  Identifies evidence gaps and generates acquisition plans")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"  [ERROR] Database not found: {DB_PATH}")
        return

    conn = get_db()

    # Verify key tables exist
    key_tables = ['documents', 'claims', 'authority_chains', 'evidence_quotes', 'filing_readiness']
    for t in key_tables:
        exists = table_exists(conn, t)
        print(f"  [{'OK' if exists else 'WARN'}] Table '{t}': {'found' if exists else 'NOT FOUND'}")

    report = {
        "tool": "#255 Evidence Gap Closer",
        "generated": datetime.now().isoformat(),
        "case": "Pigors v. Watson",
        "filings": {},
        "global_statistics": {},
        "acquisition_plan": [],
    }

    md_lines = [
        "# TOOL #255: EVIDENCE GAP CLOSER",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Case:** Pigors v. Watson",
        "",
        "## Executive Summary\n",
    ]

    total_gaps = 0
    total_critical = 0
    total_available = 0
    filing_summaries = []

    for fid, info in FILING_MAP.items():
        print(f"\n  [{fid}] {info['title']}...")
        vehicle = info['vehicle']
        keywords = vehicle.lower().replace('_', ' ').split()

        # Count available evidence
        ev_count = count_evidence_for_keywords(conn, keywords)
        doc_count = count_documents_for_keywords(conn, keywords)
        auth_gaps = get_authority_gaps(conn, vehicle)
        claims_needing = get_claims_needing_evidence(conn, vehicle)
        existing_gaps = get_existing_gaps(conn, vehicle)
        readiness = get_readiness(conn, vehicle)

        available = ev_count + doc_count
        total_available += available

        print(f"    Evidence quotes: {ev_count}, Documents: {doc_count}")
        print(f"    Authority gaps: {len(auth_gaps)}, Claims needing evidence: {len(claims_needing)}")
        print(f"    Pre-existing gap records: {len(existing_gaps)}")

        # Analyze each category
        categories = {}
        filing_gaps = 0
        filing_critical = 0
        needs = info['evidence_needs']

        for cat_name, needed_items in needs.items():
            needed_count = len(needed_items)
            # Estimate coverage from DB
            cat_keywords = []
            for item in needed_items[:3]:
                cat_keywords.extend([w for w in item.lower().split() if len(w) > 3])
            cat_available = count_evidence_for_keywords(conn, cat_keywords[:5]) if cat_keywords else 0
            cat_docs = count_documents_for_keywords(conn, cat_keywords[:5]) if cat_keywords else 0
            combined = cat_available + cat_docs

            priority = assess_gap_priority(cat_name, combined, needed_count)
            gap_count = max(0, needed_count - min(combined, needed_count))
            filing_gaps += gap_count
            if priority == "CRITICAL":
                filing_critical += gap_count

            categories[cat_name] = {
                "needed_items": needed_items,
                "needed_count": needed_count,
                "available_evidence_quotes": cat_available,
                "available_documents": cat_docs,
                "coverage_estimate": min(combined, needed_count),
                "gap_count": gap_count,
                "priority": priority,
                "acquisition_actions": [
                    f"Obtain: {item}" for item in needed_items if combined < needed_count
                ],
            }

        total_gaps += filing_gaps
        total_critical += filing_critical

        # Add authority chain gaps
        auth_gap_details = []
        for ag in auth_gaps:
            d = dict(ag)
            auth_gap_details.append({
                "authority": d.get('authority_cite', d.get('citation', 'N/A')),
                "claim": d.get('fact_claim', d.get('claim', 'N/A')),
                "gap": d.get('gap_description', 'Missing evidence link'),
            })

        filing_data = {
            "filing_id": fid,
            "title": info['title'],
            "vehicle": vehicle,
            "available_evidence": {"quotes": ev_count, "documents": doc_count},
            "categories": categories,
            "authority_chain_gaps": auth_gap_details,
            "claims_needing_evidence": len(claims_needing),
            "readiness": {
                "evidence_score": readiness.get('evidence_score', 'N/A') if readiness else 'N/A',
                "total_score": readiness.get('total_score', 'N/A') if readiness else 'N/A',
                "status": readiness.get('status', 'N/A') if readiness else 'N/A',
            },
            "total_gaps": filing_gaps,
            "critical_gaps": filing_critical,
        }
        report["filings"][fid] = filing_data
        filing_summaries.append((fid, info['title'], filing_gaps, filing_critical, available))

        # Build Markdown for this filing
        md_lines.append(f"---\n## {fid}: {info['title']}\n")
        ev_score = readiness.get('evidence_score', '?') if readiness else '?'
        status_val = readiness.get('status', 'Unknown') if readiness else 'Unknown'
        md_lines.append(f"**Evidence Score:** {ev_score} | **Status:** {status_val}")
        md_lines.append(f"**Available:** {ev_count} quotes + {doc_count} documents")
        md_lines.append(f"**Total Gaps:** {filing_gaps} | **Critical:** {filing_critical}\n")

        for cat_name, cat_data in categories.items():
            icon = "🔴" if cat_data['priority'] == 'CRITICAL' else "🟡" if cat_data['priority'] == 'HIGH' else "🟢"
            md_lines.append(f"### {icon} {cat_name.replace('_', ' ').title()} [{cat_data['priority']}]\n")
            md_lines.append(f"Needed: {cat_data['needed_count']} | "
                            f"Found: ~{cat_data['coverage_estimate']} | "
                            f"Gap: {cat_data['gap_count']}\n")
            if cat_data['gap_count'] > 0:
                md_lines.append("**Acquisition Actions:**")
                for action in cat_data['acquisition_actions'][:5]:
                    md_lines.append(f"- [ ] {action}")
                md_lines.append("")

        if auth_gap_details:
            md_lines.append("### Authority Chain Gaps\n")
            for ag in auth_gap_details[:5]:
                md_lines.append(f"- **{ag['authority']}**: {ag['claim']} — *{ag['gap']}*")
            md_lines.append("")

        print(f"    [OK] Gaps: {filing_gaps} (critical: {filing_critical})")

    # --- Build prioritized acquisition plan ---
    plan = []
    for fid, info in FILING_MAP.items():
        for cat_name, cat_data in report["filings"][fid]["categories"].items():
            if cat_data['priority'] in ('CRITICAL', 'HIGH'):
                for action in cat_data['acquisition_actions'][:3]:
                    plan.append({
                        "priority": cat_data['priority'],
                        "filing": fid,
                        "category": cat_name,
                        "action": action,
                    })
    plan.sort(key=lambda x: 0 if x['priority'] == 'CRITICAL' else 1)
    report["acquisition_plan"] = plan[:50]

    # --- Executive summary ---
    exec_lines = []
    filing_summaries.sort(key=lambda x: x[3], reverse=True)
    for fid, title, gaps, critical, available in filing_summaries:
        bar = "█" * min(critical, 20) + "░" * max(0, min(gaps - critical, 20))
        exec_lines.append(f"| {fid} | {title[:40]} | {available} | {gaps} | {critical} | {bar} |")

    md_lines.insert(5, "| Filing | Title | Available | Gaps | Critical | Visual |")
    md_lines.insert(6, "|--------|-------|-----------|------|----------|--------|")
    for i, line in enumerate(exec_lines):
        md_lines.insert(7 + i, line)
    md_lines.insert(7 + len(exec_lines), "")

    # --- Prioritized acquisition plan in MD ---
    md_lines.append("\n---\n## PRIORITIZED ACQUISITION PLAN\n")
    md_lines.append("| # | Priority | Filing | Category | Action |")
    md_lines.append("|---|----------|--------|----------|--------|")
    for i, item in enumerate(plan[:30], 1):
        md_lines.append(f"| {i} | {item['priority']} | {item['filing']} | {item['category']} | {item['action']} |")

    report["global_statistics"] = {
        "total_filings_analyzed": len(FILING_MAP),
        "total_gaps_identified": total_gaps,
        "total_critical_gaps": total_critical,
        "total_available_evidence": total_available,
        "acquisition_actions_generated": len(plan),
        "tables_queried": ["documents", "claims", "authority_chains", "evidence_quotes",
                           "filing_readiness", "evidence_gap_analysis", "gap_tickets"],
    }

    conn.close()

    # Write reports
    json_path = os.path.join(REPORT_DIR, "evidence_gap_closer.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  [OK] JSON report: {json_path}")

    md_path = os.path.join(REPORT_DIR, "EVIDENCE_GAP_CLOSER.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    print(f"  [OK] Markdown report: {md_path}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Filings analyzed: {len(FILING_MAP)}")
    print(f"  Total gaps identified: {total_gaps}")
    print(f"  Critical gaps: {total_critical}")
    print(f"  Acquisition actions: {len(plan)}")
    print(f"  Available evidence items: {total_available}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
