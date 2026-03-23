#!/usr/bin/env python3
"""Tool #254: Motion Template Library
=====================================
Generates structured motion templates for ALL 10 filing packages (F1-F10).
For each filing: caption block, statement of facts, IRAC argument sections,
relief requested, certificate of service, and verification/affidavit template.

Queries: docket_events, authority_chains, claims, evidence_quotes, filing_readiness
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


# --- Paths (never set CWD to repo root — shadow modules) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(SCRIPT_DIR, '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

# --- Verified party identity (from copilot-instructions.md) ---
PLAINTIFF = {
    "name": "ANDREW JAMES PIGORS",
    "address": "1977 Whitehall Road, Lot 17\nNorth Muskegon, MI 49445",
    "phone": "(231) 903-5690",
    "email": "andrewjpigors@gmail.com",
    "status": "Plaintiff, In Propria Persona",
}
DEFENDANT = {
    "name": "EMILY A. WATSON",
    "address": "2160 Garland Drive\nNorton Shores, MI 49441",
}

# --- Filing packages with court assignments ---
FILING_MAP = {
    "F1": {
        "title": "Emergency Motion to Restore Parenting Time",
        "court": "14th_circuit_family",
        "type": "EMERGENCY_MOTION",
        "mcr": "MCR 3.207; MCL 722.27a",
        "vehicle": "EMERGENCY_MOTION_RESTORE_PT",
    },
    "F2": {
        "title": "Motion for Fraud Upon the Court / Sanctions",
        "court": "14th_circuit_family",
        "type": "MOTION",
        "mcr": "MCR 2.114(D); MCR 2.625",
        "vehicle": "FRAUD_UPON_COURT",
    },
    "F3": {
        "title": "Motion for Disqualification of Judge",
        "court": "14th_circuit_family",
        "type": "MOTION",
        "mcr": "MCR 2.003(C)",
        "vehicle": "JUDICIAL_DISQUALIFICATION",
    },
    "F4": {
        "title": "42 USC §1983 Civil Rights Complaint",
        "court": "usdc_wdmi",
        "type": "COMPLAINT",
        "mcr": "42 USC §1983; Monell v. Dept of Social Svcs",
        "vehicle": "SECTION_1983_COMPLAINT",
    },
    "F5": {
        "title": "MSC Complaint for Superintending Control",
        "court": "msc",
        "type": "COMPLAINT",
        "mcr": "MCR 7.306; MCR 3.302",
        "vehicle": "MSC_SUPERINTENDING_CONTROL",
    },
    "F6": {
        "title": "JTC Judicial Misconduct Complaint",
        "court": "jtc",
        "type": "COMPLAINT",
        "mcr": "MCR 9.205; Judicial Canons",
        "vehicle": "JTC_MISCONDUCT",
    },
    "F7": {
        "title": "Motion to Modify Custody",
        "court": "14th_circuit_family",
        "type": "MOTION",
        "mcr": "MCL 722.27; MCL 722.23",
        "vehicle": "CUSTODY_MODIFICATION",
    },
    "F8": {
        "title": "COA Application for Leave to Appeal",
        "court": "coa",
        "type": "APPLICATION",
        "mcr": "MCR 7.205",
        "vehicle": "COA_APPLICATION_LEAVE",
    },
    "F9": {
        "title": "COA Appeal Brief",
        "court": "coa",
        "type": "BRIEF",
        "mcr": "MCR 7.212",
        "vehicle": "COA_APPEAL_BRIEF",
    },
    "F10": {
        "title": "AGC Attorney Grievance Commission Complaint",
        "court": "agc",
        "type": "COMPLAINT",
        "mcr": "MRPC 3.3; MRPC 3.4; MRPC 8.4",
        "vehicle": "AGC_MISCONDUCT",
    },
}

COURTS = {
    "14th_circuit_family": {
        "name": "14TH JUDICIAL CIRCUIT COURT — FAMILY DIVISION",
        "county": "MUSKEGON COUNTY, MICHIGAN",
        "case_no": "2024-001507-DC",
        "judge": "Hon. Jenny L. McNeill",
    },
    "coa": {
        "name": "MICHIGAN COURT OF APPEALS",
        "county": "",
        "case_no": "COA 366810",
        "judge": "",
    },
    "msc": {
        "name": "MICHIGAN SUPREME COURT",
        "county": "",
        "case_no": "[TO BE ASSIGNED]",
        "judge": "",
    },
    "usdc_wdmi": {
        "name": "UNITED STATES DISTRICT COURT\nWESTERN DISTRICT OF MICHIGAN — SOUTHERN DIVISION",
        "county": "",
        "case_no": "[TO BE ASSIGNED]",
        "judge": "[TO BE ASSIGNED]",
    },
    "jtc": {
        "name": "MICHIGAN JUDICIAL TENURE COMMISSION",
        "county": "",
        "case_no": "[JTC FILE NO.]",
        "judge": "",
    },
    "agc": {
        "name": "ATTORNEY GRIEVANCE COMMISSION OF MICHIGAN",
        "county": "",
        "case_no": "[AGC FILE NO.]",
        "judge": "",
    },
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


# --- Data retrieval ---
def get_docket_events(conn, case_id):
    if not table_exists(conn, 'docket_events'):
        return []
    cols = get_columns(conn, 'docket_events')
    date_col = 'event_date_iso' if 'event_date_iso' in cols else ('event_date' if 'event_date' in cols else None)
    title_col = 'title' if 'title' in cols else ('event_title' if 'event_title' in cols else None)
    summary_col = 'summary' if 'summary' in cols else ('description' if 'description' in cols else None)
    case_col = 'case_id' if 'case_id' in cols else None

    if not case_col:
        return []
    select_parts = ['event_id' if 'event_id' in cols else 'rowid AS event_id']
    if date_col:
        select_parts.append(date_col)
    if title_col:
        select_parts.append(title_col)
    if summary_col:
        select_parts.append(summary_col)
    sql = f"SELECT {', '.join(select_parts)} FROM docket_events WHERE {case_col} = ? ORDER BY {date_col or 'rowid'} DESC LIMIT 20"
    return safe_query(conn, sql, (case_id,))


def get_authority_chains(conn, vehicle):
    if not table_exists(conn, 'authority_chains'):
        return []
    cols = get_columns(conn, 'authority_chains')
    veh_col = 'filing_vehicle' if 'filing_vehicle' in cols else ('vehicle_name' if 'vehicle_name' in cols else None)
    if not veh_col:
        return safe_query(conn, "SELECT * FROM authority_chains LIMIT 10")
    return safe_query(conn, f"SELECT * FROM authority_chains WHERE {veh_col} LIKE ?", (f'%{vehicle}%',))


def get_claims_for_vehicle(conn, vehicle):
    if not table_exists(conn, 'claims'):
        return []
    cols = get_columns(conn, 'claims')
    # Try to match vehicle in classification or issue_id
    results = []
    for search_col in ['classification', 'issue_id', 'claim_id']:
        if search_col in cols:
            rows = safe_query(conn, f"SELECT * FROM claims WHERE [{search_col}] LIKE ? LIMIT 20", (f'%{vehicle}%',))
            if rows:
                results.extend(rows)
    if not results:
        keywords = vehicle.lower().replace('_', ' ').split()
        for kw in keywords[:3]:
            for col in ['proposition', 'classification', 'issue_id']:
                if col in cols:
                    rows = safe_query(conn, f"SELECT * FROM claims WHERE [{col}] LIKE ? LIMIT 10", (f'%{kw}%',))
                    results.extend(rows)
    # Deduplicate by claim_id
    seen = set()
    unique = []
    id_col = 'claim_id' if 'claim_id' in cols else None
    for r in results:
        rid = dict(r).get(id_col or 'claim_id', id(r))
        if rid not in seen:
            seen.add(rid)
            unique.append(r)
    return unique[:20]


def get_evidence_for_keywords(conn, keywords, limit=10):
    if not table_exists(conn, 'evidence_quotes'):
        return []
    cols = get_columns(conn, 'evidence_quotes')
    text_col = 'quote_text' if 'quote_text' in cols else ('text' if 'text' in cols else None)
    if not text_col:
        return []
    conditions = " OR ".join([f"[{text_col}] LIKE ?" for _ in keywords[:5]])
    params = [f'%{kw}%' for kw in keywords[:5]]
    return safe_query(conn, f"SELECT * FROM evidence_quotes WHERE {conditions} LIMIT ?", (*params, limit))


def get_readiness(conn, vehicle):
    if not table_exists(conn, 'filing_readiness'):
        return None
    cols = get_columns(conn, 'filing_readiness')
    veh_col = 'vehicle_name' if 'vehicle_name' in cols else ('filing_vehicle' if 'filing_vehicle' in cols else None)
    if not veh_col:
        return None
    rows = safe_query(conn, f"SELECT * FROM filing_readiness WHERE [{veh_col}] LIKE ?", (f'%{vehicle}%',))
    return dict(rows[0]) if rows else None


# --- Template generators ---
def generate_caption(filing_id, info, court_info):
    case_no = court_info.get('case_no', '[CASE NO.]')
    county_line = f"\n{court_info['county']}" if court_info.get('county') else ""
    judge_line = f"\n{court_info['judge']}" if court_info.get('judge') else ""
    return f"""{'='*60}
{court_info['name']}{county_line}
{'='*60}

{PLAINTIFF['name']},                     Case No. {case_no}
    {PLAINTIFF['status']},              {judge_line}
        vs.

{DEFENDANT['name']},
    Defendant.
{'_'*40}/

{info['title'].upper()}
{'='*60}"""


def generate_facts_section(claims, docket_events):
    lines = ["## STATEMENT OF FACTS\n"]
    lines.append("### A. Procedural History\n")
    if docket_events:
        for i, evt in enumerate(docket_events[:10], 1):
            d = dict(evt)
            date = d.get('event_date_iso', d.get('event_date', 'N/A'))
            title = d.get('title', d.get('event_title', 'Event'))
            lines.append(f"{i}. **{date}** — {title}")
    else:
        lines.append("*[Docket events to be populated from court records]*\n")

    lines.append("\n### B. Factual Allegations\n")
    if claims:
        for i, c in enumerate(claims[:15], 1):
            d = dict(c)
            prop = d.get('proposition', d.get('classification', 'Allegation'))
            status = d.get('status', '')
            lines.append(f"{i}. {prop}")
            if status:
                lines.append(f"   *Status: {status}*")
    else:
        lines.append("*[Claims to be populated from evidence analysis]*\n")
    return "\n".join(lines)


def generate_irac_section(authorities, evidence, info):
    lines = ["## ARGUMENT\n"]
    if authorities:
        for i, auth in enumerate(authorities, 1):
            d = dict(auth)
            cite = d.get('authority_cite', d.get('citation', 'Authority'))
            claim = d.get('fact_claim', d.get('claim', ''))
            elements = d.get('elements', '')
            ev_quote = d.get('evidence_quote', '')
            complete = d.get('chain_complete', 0)

            lines.append(f"### Argument {i}: {cite}\n")
            lines.append("**ISSUE:**")
            lines.append(f"Whether {claim}\n" if claim else "Whether the court erred.\n")
            lines.append("**RULE:**")
            lines.append(f"{cite} provides: {elements}\n" if elements else f"{cite}\n")
            lines.append("**APPLICATION:**")
            if ev_quote:
                lines.append(f'The evidence establishes: "{ev_quote[:200]}..."')
            else:
                lines.append("*[Evidence to be inserted]*")
            lines.append(f"\n**CONCLUSION:**")
            completeness = "fully supported" if complete else "requires additional evidence"
            lines.append(f"This argument is {completeness} by the record.\n")
    else:
        lines.append(f"### Argument 1: {info['mcr']}\n")
        lines.append("**ISSUE:** Whether relief is warranted under the applicable standard.\n")
        lines.append(f"**RULE:** {info['mcr']} governs this motion.\n")
        lines.append("**APPLICATION:** *[To be populated from evidence]*\n")
        lines.append("**CONCLUSION:** Relief should be granted.\n")
    return "\n".join(lines)


def generate_relief_section(info):
    return f"""## RELIEF REQUESTED

WHEREFORE, {PLAINTIFF['name']}, appearing in propria persona, respectfully
requests that this Honorable Court:

1. Grant the relief sought in this {info['type'].title()};
2. Enter an Order consistent with the arguments above;
3. Grant such other and further relief as this Court deems just and proper.

Respectfully submitted,

_______________________________
{PLAINTIFF['name']}
{PLAINTIFF['address']}
{PLAINTIFF['phone']}
{PLAINTIFF['email']}

Date: ___________________
"""


def generate_certificate_of_service():
    return f"""## CERTIFICATE OF SERVICE

I hereby certify that on _________________, I served a true copy of this
document upon the following by [MiFILE / first-class mail / personal delivery]:

{DEFENDANT['name']}
{DEFENDANT['address']}

_______________________________
{PLAINTIFF['name']}
Date: ___________________
"""


def generate_verification():
    return f"""## VERIFICATION / AFFIDAVIT

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

I, {PLAINTIFF['name']}, being first duly sworn, depose and state:

1. I am the Plaintiff in the above-captioned matter.
2. I have personal knowledge of the facts stated in this document.
3. The statements made herein are true and accurate to the best of my
   knowledge, information, and belief.

Further affiant sayeth not.

_______________________________
{PLAINTIFF['name']}

Subscribed and sworn to before me
this ____ day of ____________, 20____.

_______________________________
Notary Public, State of Michigan
County of ___________________
My commission expires: ___________
"""


# --- Main ---
def main():
    print("=" * 70)
    print("  TOOL #254: MOTION TEMPLATE LIBRARY")
    print("  Generates structured motion templates for F1-F10 filing packages")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"  [ERROR] Database not found: {DB_PATH}")
        return

    conn = get_db()
    report = {
        "tool": "#254 Motion Template Library",
        "generated": datetime.now().isoformat(),
        "case": "Pigors v. Watson",
        "templates": {},
        "statistics": {},
    }
    md_lines = [
        "# TOOL #254: MOTION TEMPLATE LIBRARY",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Case:** Pigors v. Watson",
        "",
    ]

    total_authorities = 0
    total_claims = 0
    total_evidence = 0
    total_docket = 0

    for fid, info in FILING_MAP.items():
        print(f"\n  [{fid}] {info['title']}...")
        court_info = COURTS.get(info['court'], {"name": "COURT", "county": "", "case_no": "N/A", "judge": ""})

        # Query DB for this filing
        vehicle = info.get('vehicle', '')
        case_id = court_info.get('case_no', '')
        docket = get_docket_events(conn, case_id)
        authorities = get_authority_chains(conn, vehicle)
        claims = get_claims_for_vehicle(conn, vehicle)
        keywords = vehicle.lower().replace('_', ' ').split()
        evidence = get_evidence_for_keywords(conn, keywords, limit=8)

        readiness = get_readiness(conn, vehicle)

        total_authorities += len(authorities)
        total_claims += len(claims)
        total_evidence += len(evidence)
        total_docket += len(docket)

        print(f"    Docket events: {len(docket)}, Authorities: {len(authorities)}, "
              f"Claims: {len(claims)}, Evidence quotes: {len(evidence)}")

        # Build template
        caption = generate_caption(fid, info, court_info)
        facts = generate_facts_section(claims, docket)
        argument = generate_irac_section(authorities, evidence, info)
        relief = generate_relief_section(info)
        cos = generate_certificate_of_service()
        verification = generate_verification()

        full_template = f"""{caption}

{facts}

{argument}

{relief}

{cos}

{verification}
"""
        # Store in report
        report["templates"][fid] = {
            "filing_id": fid,
            "title": info['title'],
            "court": court_info['name'].split('\n')[0],
            "case_no": court_info['case_no'],
            "type": info['type'],
            "authority": info['mcr'],
            "db_sourced": {
                "docket_events": len(docket),
                "authority_chains": len(authorities),
                "claims": len(claims),
                "evidence_quotes": len(evidence),
            },
            "readiness": {
                "total_score": readiness.get('total_score', 'N/A') if readiness else 'N/A',
                "status": readiness.get('status', 'N/A') if readiness else 'N/A',
                "authority_score": readiness.get('authority_score', 'N/A') if readiness else 'N/A',
                "evidence_score": readiness.get('evidence_score', 'N/A') if readiness else 'N/A',
            },
            "template_length_chars": len(full_template),
        }

        # Add to Markdown
        md_lines.append(f"---\n")
        md_lines.append(f"# {fid}: {info['title']}\n")
        md_lines.append(full_template)
        print(f"    [OK] Template generated ({len(full_template)} chars)")

    report["statistics"] = {
        "total_filings": len(FILING_MAP),
        "total_authorities_sourced": total_authorities,
        "total_claims_sourced": total_claims,
        "total_evidence_sourced": total_evidence,
        "total_docket_events": total_docket,
        "query_source": "litigation_context.db",
        "tables_queried": ["docket_events", "authority_chains", "claims", "evidence_quotes", "filing_readiness"],
    }

    conn.close()

    # Write JSON report
    json_path = os.path.join(REPORT_DIR, "motion_template_library.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  [OK] JSON report: {json_path}")

    # Write Markdown report
    md_path = os.path.join(REPORT_DIR, "MOTION_TEMPLATE_LIBRARY.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    print(f"  [OK] Markdown report: {md_path}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Templates generated: {len(FILING_MAP)}")
    print(f"  DB-sourced authorities: {total_authorities}")
    print(f"  DB-sourced claims: {total_claims}")
    print(f"  DB-sourced evidence: {total_evidence}")
    print(f"  DB-sourced docket events: {total_docket}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
