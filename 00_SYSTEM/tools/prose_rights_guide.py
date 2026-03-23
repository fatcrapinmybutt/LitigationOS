#!/usr/bin/env python3
"""Tool #253: Pro Se Litigant Rights Guide
Generates comprehensive guide for Andrew's rights as a pro se litigant.
Queries authority_chains, deadlines, docket_events for DB-grounded content.
Covers MCR protections, filing fee waivers, service rules, evidence preservation,
hearing rights, FOC access, and appellate procedures.

Output: PROSE_RIGHTS_GUIDE.md + prose_rights_guide.json
"""
import sys, os, json, sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

# --- Path setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
DB_PATH = os.path.join(REPO_ROOT, 'litigation_context.db')
REPORTS_DIR = os.path.join(REPO_ROOT, '00_SYSTEM', 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- Pro Se Rights Framework ---
RIGHTS_SECTIONS = {
    1: {
        'title': 'MCR and Statutory Protections for Self-Represented Parties',
        'keywords': ['pro se', 'self-represent', 'unrepresented', 'self represent',
                     'without attorney', 'without counsel', 'pro per',
                     'access to justice', 'equal access'],
        'authorities': [
            'MCR 2.002 — Waiver of fees for indigent parties',
            'MCR 2.107 — Service of pleadings and other documents',
            'MCR 2.111 — General rules of pleading',
            'MCR 2.119 — Motion practice',
            'Haines v Kerner, 404 US 519 (1972) — Pro se pleadings held to less stringent standard',
            'Erickson v Pardus, 551 US 89 (2007) — Pro se filings must be liberally construed',
            'Estelle v Gamble, 429 US 97 (1976) — Pro se allegations taken as true on motion',
            'Mich Const 1963, Art 1 §13 — Right of access to courts',
            'Mich Const 1963, Art 6 §1 — Judicial power vested in one court of justice',
        ],
        'content': [
            'Pro se litigants are entitled to the same procedural protections as represented parties.',
            'Courts must liberally construe pro se filings (Haines v Kerner).',
            'Pro se parties cannot be held to the technical standards of licensed attorneys.',
            'The court has an obligation to ensure pro se litigants understand procedures.',
            'Judges must remain neutral — may not advocate for either side but must explain process.',
        ],
    },
    2: {
        'title': 'Common Judicial Biases Against Pro Se Litigants',
        'keywords': ['bias', 'prejudice', 'discriminat', 'unfair', 'partial',
                     'ex parte', 'one-sided', 'unequal treatment'],
        'authorities': [
            'Mich Code of Judicial Conduct Canon 2 — Appearance of impropriety',
            'Mich Code of Judicial Conduct Canon 3(A)(4) — Patient, dignified, courteous treatment',
            'In re Hague, 412 Mich 532 (1982) — Judicial bias standard',
            'Armstrong v Ypsilanti Charter Twp, 248 Mich App 573 (2001) — Pro se parties entitled to same consideration',
            'MCR 2.003 — Disqualification of judges for bias or prejudice',
        ],
        'content': [
            'BIAS: Dismissing motions without reading because pro se (remedy: MCR 2.003 disqualification)',
            'BIAS: Imposing stricter formatting requirements on pro se filings (remedy: Haines v Kerner)',
            'BIAS: Allowing opposing counsel to interrupt pro se arguments (remedy: object on record)',
            'BIAS: Ex parte communication with opposing counsel (remedy: MCR 2.003(C)(1)(b))',
            'BIAS: Rushing hearings when pro se party is presenting (remedy: motion for adequate time)',
            'BIAS: Failure to explain legal proceedings (remedy: request clarification on record)',
            'COUNTER-STRATEGY: File everything in writing — creates reviewable appellate record.',
            'COUNTER-STRATEGY: Request verbatim transcript of every hearing.',
            'COUNTER-STRATEGY: Cite specific MCR rules — shows court familiarity with procedure.',
        ],
    },
    3: {
        'title': 'Filing Fee Waiver (IFP) Under MCR 2.002',
        'keywords': ['fee waiver', 'ifp', 'in forma pauperis', 'indigent',
                     'filing fee', 'inability to pay', 'waiver of fees',
                     'poverty', 'income', 'financial'],
        'authorities': [
            'MCR 2.002 — Waiver of fees and costs for indigent persons',
            'MCR 2.002(B) — Eligibility criteria for fee waiver',
            'MCR 2.002(C) — Procedure for requesting fee waiver',
            'MCR 2.002(D) — Scope of waiver (covers filing fees, service costs, transcripts)',
            'Boddie v Connecticut, 401 US 371 (1971) — Due process requires court access regardless of ability to pay',
        ],
        'content': [
            'MCR 2.002 allows waiver of ALL court fees and costs for indigent parties.',
            'Eligibility: receiving public assistance OR income below 125% of federal poverty guidelines.',
            'The waiver covers: filing fees, motion fees, jury fees, transcript costs, appeal fees.',
            'File MC 20 (Fee Waiver Request) with supporting financial documentation.',
            'The court MUST rule on fee waiver before dismissing any filing for non-payment.',
            'If denied, you have the right to a hearing on the denial.',
            'Fee waiver applies across all courts — circuit, COA, and MSC.',
        ],
    },
    4: {
        'title': 'Service Requirements Per MCR 2.105/2.107',
        'keywords': ['service', 'serve', 'service of process', 'certified mail',
                     'personal service', 'proof of service', 'mcr 2.105', 'mcr 2.107'],
        'authorities': [
            'MCR 2.105 — Manner of service of process',
            'MCR 2.107 — Service and filing of pleadings and other papers',
            'MCR 2.104 — Process; sufficiency',
            'MCR 2.106 — Publication of notice of action',
            'MCR 2.108 — Service of nonparty subpoenas',
        ],
        'content': [
            'ORIGINAL SERVICE (MCR 2.105): Personal service by process server or any adult non-party.',
            'SUBSEQUENT FILINGS (MCR 2.107): Service by first-class mail, email (if consented), or personal delivery.',
            'PROOF OF SERVICE: Must be filed with every document — include date, method, and address.',
            'TIMING: Service must be completed before or simultaneously with filing.',
            'E-SERVICE: If opposing party consents or court orders, email service is valid.',
            'TIP: Always use certified mail with return receipt for important motions — creates proof.',
            'TIP: Keep copies of all proof of service filings — critical for appellate record.',
        ],
    },
    5: {
        'title': 'Evidence Preservation Rights',
        'keywords': ['evidence preservation', 'spoliation', 'preserve', 'destroy evidence',
                     'litigation hold', 'document preservation', 'duty to preserve'],
        'authorities': [
            'MCR 2.302 — General rules of discovery',
            'MCR 2.310 — Request for production of documents',
            'MCR 2.313(B) — Sanctions for failure to comply with discovery order',
            'Brenner v Kolk, 226 Mich App 149 (1997) — Adverse inference for spoliation',
            'Bloemendaal v Town & Country Sports Center, 255 Mich App 207 (2002) — Spoliation sanctions',
        ],
        'content': [
            'Both parties have a DUTY to preserve evidence once litigation is reasonably anticipated.',
            'Send a written preservation demand to opposing party (creates obligation).',
            'If evidence is destroyed, request adverse inference instruction at trial.',
            'You may request sanctions under MCR 2.313(B) for failure to preserve.',
            'Digital evidence (texts, emails, social media) is subject to preservation duty.',
            'TIP: Screenshot and preserve YOUR OWN evidence immediately — timestamps matter.',
            'TIP: Use certified copies for critical documents (notarized where possible).',
        ],
    },
    6: {
        'title': 'Right to Full Hearing Before Custody Modifications (MCL 722.27)',
        'keywords': ['hearing', 'custody modification', 'evidentiary hearing',
                     'proper cause', 'change of circumstances', 'mcl 722.27',
                     'best interest', 'modification'],
        'authorities': [
            'MCL 722.27 — Custody modification standard',
            'MCL 722.27(1)(c) — Proper cause or change of circumstances required',
            'Vodvarka v Grasmeyer, 259 Mich App 499 (2003) — Proper cause/change of circumstances standard',
            'Shade v Wright, 291 Mich App 17 (2010) — Clear and convincing evidence for established custodial environment',
            'Pierron v Pierron, 486 Mich 81 (2010) — Burden of proof in custody modification',
            'MCR 3.210 — Custody proceedings procedure',
        ],
        'content': [
            'NO custody modification without a finding of proper cause or change of circumstances.',
            'If established custodial environment exists, burden is CLEAR AND CONVINCING evidence.',
            'The court MUST hold an evidentiary hearing before modifying custody.',
            'Both parties have the right to present witnesses, cross-examine, and submit evidence.',
            'Ex parte custody modifications are generally prohibited except in emergencies (MCL 722.27a).',
            'If the court modifies custody without proper hearing, this is reversible error on appeal.',
            'TIP: Always request an evidentiary hearing in writing — creates appellate preservation.',
        ],
    },
    7: {
        'title': 'Access to FOC Files (MCR 3.224)',
        'keywords': ['foc', 'friend of court', 'foc file', 'foc report',
                     'foc recommendation', 'mcr 3.224', 'access to records'],
        'authorities': [
            'MCR 3.224 — Friend of the Court records and access',
            'MCR 3.218 — Friend of the Court procedures',
            'MCR 3.219 — FOC objection and hearing process',
            'MCL 552.505 — FOC duties and responsibilities',
            'MCL 552.507 — Access to FOC files by parties',
        ],
        'content': [
            'Parties have a RIGHT to access their own FOC files (MCR 3.224).',
            'File a written request with the FOC office for complete file copy.',
            'FOC recommendations are NOT binding — you may object under MCR 3.219.',
            'Objections to FOC recommendations must be filed within 21 days of service.',
            'If FOC denies access, file motion to compel under MCR 3.224(C).',
            'FOC communications with the judge may be reviewable — request disclosure.',
            'TIP: Review the FOC file BEFORE every hearing — it may contain information shared with the judge.',
            'FOC Muskegon County: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442.',
        ],
    },
    8: {
        'title': 'Appellate Rights and Procedures',
        'keywords': ['appeal', 'appellate', 'court of appeals', 'coa', 'msc',
                     'supreme court', 'claim of appeal', 'application for leave',
                     'appellate brief', 'mcr 7'],
        'authorities': [
            'MCR 7.204 — Filing claim of appeal in Court of Appeals',
            'MCR 7.205 — Application for leave to appeal',
            'MCR 7.212 — Briefs in Court of Appeals',
            'MCR 7.215 — Court of Appeals decisions',
            'MCR 7.302 — Application for leave to appeal to Supreme Court',
            'MCR 7.305 — Supreme Court rule on applications',
            'Const 1963, Art 6 §4 — Right to appeal from circuit court',
        ],
        'content': [
            'CLAIM OF APPEAL: File within 21 days of final order (MCR 7.204(A)(1)).',
            'LEAVE TO APPEAL: File within 21 days for interlocutory orders (MCR 7.205(A)).',
            'REQUIRED DOCUMENTS: Claim of appeal, docket statement, proof of service, filing fee (or IFP).',
            'BRIEF: Due within 56 days of claim of appeal (MCR 7.212(A)(1)).',
            'STANDARD OF REVIEW: Custody decisions reviewed for abuse of discretion (MCL 722.28).',
            'ISSUE PRESERVATION: Must object at trial court level to preserve for appeal.',
            'TRANSCRIPT: Order transcript immediately — needed for appellate record.',
            'MSC: Application for leave within 42 days of COA decision (MCR 7.302(C)(2)).',
            'TIP: File motion to stay enforcement pending appeal if custody order changes.',
        ],
    },
}


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def table_exists(conn, name):
    r = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r[0] > 0


def get_columns(conn, name):
    return [row[1] for row in conn.execute(f"PRAGMA table_info([{name}])").fetchall()]


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []


def find_authorities_in_db(conn):
    """Find DB-stored authorities relevant to pro se rights."""
    if not table_exists(conn, 'authority_chains'):
        return {}
    cols = get_columns(conn, 'authority_chains')
    if 'authority_cite' not in cols or 'fact_claim' not in cols:
        return {}

    pro_se_keywords = ['pro se', 'self-represent', 'haines', 'erickson',
                       'mcr 2.002', 'mcr 2.003', 'mcr 2.105', 'mcr 2.107',
                       'mcr 7.204', 'mcr 7.205', 'mcr 3.224', 'mcl 722.27',
                       'fee waiver', 'indigent', 'custody modification',
                       'best interest', 'foc', 'friend of court',
                       'appellat', 'court of appeals', 'disqualif',
                       'evidence preservation', 'spoliation', 'discovery']

    results = defaultdict(list)
    rows = safe_query(conn, "SELECT id, filing_vehicle, fact_claim, authority_cite, "
                            "authority_type, chain_complete FROM authority_chains")

    for row in rows:
        combined = s(str(row['fact_claim'] or '')) + ' ' + s(str(row['authority_cite'] or ''))
        for kw in pro_se_keywords:
            if kw in combined:
                results[kw].append({
                    'id': row['id'],
                    'filing_vehicle': row['filing_vehicle'],
                    'fact_claim': str(row['fact_claim'] or '')[:200],
                    'authority_cite': row['authority_cite'],
                    'chain_complete': row['chain_complete'],
                })
                break  # avoid double-counting per row
    return dict(results)


def find_relevant_deadlines(conn):
    """Find deadlines relevant to pro se rights and procedures."""
    if not table_exists(conn, 'deadlines'):
        return []
    cols = get_columns(conn, 'deadlines')
    if 'title' not in cols or 'due_date_iso' not in cols:
        return []

    rows = safe_query(conn, "SELECT deadline_id, case_id, title, due_date_iso, "
                            "basis, status FROM deadlines ORDER BY due_date_iso")
    results = []
    for row in rows:
        results.append({
            'deadline_id': row['deadline_id'],
            'case_id': row['case_id'],
            'title': row['title'],
            'due_date': row['due_date_iso'],
            'basis': row['basis'],
            'status': row['status'],
        })
    return results


def find_relevant_docket_events(conn):
    """Find docket events showing pro se treatment."""
    if not table_exists(conn, 'docket_events'):
        return []

    pro_se_kws = ['pro se', 'self-represent', 'fee waiver', 'ifp', 'without attorney',
                  'unrepresented', 'hearing', 'denied', 'overruled', 'sustained']

    rows = safe_query(conn, "SELECT event_id, title, summary, event_date_iso, "
                            "event_type FROM docket_events ORDER BY event_date_iso")
    results = []
    for row in rows:
        combined = s(str(row['title'] or '')) + ' ' + s(str(row['summary'] or ''))
        if any(kw in combined for kw in pro_se_kws):
            results.append({
                'event_id': row['event_id'],
                'title': row['title'],
                'summary': str(row['summary'] or '')[:200],
                'date': row['event_date_iso'],
                'event_type': row['event_type'],
            })
    return results


def find_judicial_violations(conn):
    """Find judicial violations relevant to pro se bias."""
    if not table_exists(conn, 'judicial_violations'):
        return []
    cols = get_columns(conn, 'judicial_violations')
    if 'violation_description' not in cols:
        return []

    rows = safe_query(conn, "SELECT violation_id, judge_name, canon_number, "
                            "violation_description, severity FROM judicial_violations")
    return [dict(row) for row in rows]


def generate_md(db_authorities, deadlines, docket_events, judicial_violations):
    """Generate comprehensive pro se rights guide."""
    lines = [
        "# Pro Se Litigant Rights Guide",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**For:** Andrew James Pigors — Pro Se Plaintiff",
        f"**Case:** Pigors v. Watson — 2024-001507-DC",
        f"**Court:** 14th Circuit Court, Family Division, Muskegon County, MI",
        f"**Judge:** Hon. Jenny L. McNeill",
        "",
        "> *\"Pro se pleadings are to be construed liberally and held to less "
        "stringent standards than formal pleadings drafted by lawyers.\"* — "
        "Haines v. Kerner, 404 U.S. 519, 520 (1972)",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]
    for num in sorted(RIGHTS_SECTIONS.keys()):
        sec = RIGHTS_SECTIONS[num]
        lines.append(f"{num}. [{sec['title']}](#{num}-{sec['title'].lower().replace(' ', '-')[:30]})")
    lines.append("")

    # Each section
    for num in sorted(RIGHTS_SECTIONS.keys()):
        sec = RIGHTS_SECTIONS[num]
        lines += [
            f"## {num}. {sec['title']}",
            "",
        ]

        # Authorities
        lines.append("### Controlling Authorities")
        lines.append("")
        for auth in sec['authorities']:
            lines.append(f"- {auth}")
        lines.append("")

        # Content
        lines.append("### Key Rights & Strategies")
        lines.append("")
        for item in sec['content']:
            lines.append(f"- {item}")
        lines.append("")

        # DB-sourced authorities for this section
        section_db_hits = []
        for kw in sec['keywords']:
            if kw in db_authorities:
                section_db_hits.extend(db_authorities[kw])
        if section_db_hits:
            # Deduplicate by id
            seen = set()
            unique = []
            for h in section_db_hits:
                if h['id'] not in seen:
                    seen.add(h['id'])
                    unique.append(h)
            lines.append(f"### DB-Sourced Authority Chains ({len(unique)} found)")
            lines.append("")
            lines.append("| Authority | Fact Claim | Vehicle | Complete |")
            lines.append("|-----------|-----------|---------|----------|")
            for h in unique[:10]:
                complete = "✓" if h['chain_complete'] else "✗"
                lines.append(f"| {h['authority_cite']} | {h['fact_claim'][:60]} | "
                             f"{h['filing_vehicle']} | {complete} |")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Active Deadlines section
    if deadlines:
        lines += [
            "## Active Case Deadlines",
            "",
            "| Deadline | Case | Due Date | Basis | Status |",
            "|----------|------|----------|-------|--------|",
        ]
        for dl in deadlines[:20]:
            lines.append(f"| {dl['title']} | {dl['case_id']} | {dl['due_date']} | "
                         f"{dl.get('basis') or 'N/A'} | {dl['status']} |")
        lines += ["", "---", ""]

    # Judicial Violations section
    if judicial_violations:
        lines += [
            "## Documented Judicial Violations (Pro Se Relevance)",
            "",
            f"**{len(judicial_violations)} violations documented in DB.** "
            "These may support MCR 2.003 disqualification or JTC complaint.",
            "",
            "| Canon | Description | Severity |",
            "|-------|------------|----------|",
        ]
        for jv in judicial_violations[:15]:
            lines.append(f"| {jv.get('canon_number', 'N/A')} | "
                         f"{str(jv['violation_description'])[:80]} | "
                         f"{jv.get('severity', 'N/A')} |")
        lines += ["", "---", ""]

    # Docket events showing pro se treatment
    if docket_events:
        lines += [
            "## Docket Events Relevant to Pro Se Treatment",
            "",
            f"**{len(docket_events)} events** matched pro se keywords in docket.",
            "",
            "| Date | Event | Summary |",
            "|------|-------|---------|",
        ]
        for ev in docket_events[:15]:
            lines.append(f"| {ev['date']} | {ev['title']} | {ev['summary'][:60]} |")
        lines += ["", "---", ""]

    # Emergency reference card
    lines += [
        "## Quick Reference Card — Courtroom Survival",
        "",
        "### Before Every Hearing",
        "- [ ] Review FOC file (MCR 3.224)",
        "- [ ] Prepare written argument (never rely solely on oral)",
        "- [ ] Bring 3 copies of every exhibit (court, opposing party, self)",
        "- [ ] Bring court rules book (or phone with MCR access)",
        "- [ ] Request court reporter or bring recording device (if permitted)",
        "",
        "### During Hearing",
        "- [ ] State your name: \"Andrew Pigors, pro se plaintiff\"",
        "- [ ] Object immediately to any improper procedure — say: \"Objection, [basis]\"",
        "- [ ] If confused, say: \"Your Honor, as a pro se party, I request clarification\"",
        "- [ ] Never interrupt — wait for your turn, then speak clearly",
        "- [ ] Request everything in writing if the judge rules orally",
        "",
        "### After Hearing",
        "- [ ] File proposed order within 7 days (MCR 2.602)",
        "- [ ] Order transcript immediately",
        "- [ ] Note appeal deadline: 21 days from entry of order (MCR 7.204)",
        "- [ ] Preserve all issues by filing post-hearing motion if needed",
        "",
        "### Emergency Numbers",
        "- **14th Circuit Court Clerk:** (231) 724-6241",
        "- **FOC (Pamela Rusco):** 990 Terrace St, Muskegon, MI 49442",
        "- **Michigan Court of Appeals:** (517) 373-0786",
        "- **Michigan State Bar Self-Help:** (800) 968-1442",
        "",
        "---",
        f"*Generated by Tool #253 — Pro Se Litigant Rights Guide*",
    ]
    return '\n'.join(lines)


def main():
    print("=" * 70)
    print("TOOL #253: PRO SE LITIGANT RIGHTS GUIDE")
    print("=" * 70)
    print(f"DB: {DB_PATH}")
    print(f"Reports: {REPORTS_DIR}")
    print()

    if not os.path.exists(DB_PATH):
        print(f"[FATAL] Database not found: {DB_PATH}")
        sys.exit(1)

    conn = connect_db()

    # Verify tables
    for t in ['authority_chains', 'deadlines', 'docket_events', 'judicial_violations']:
        if table_exists(conn, t):
            cols = get_columns(conn, t)
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            print(f"  [OK] {t}: {len(cols)} columns, {cnt:,} rows")
        else:
            print(f"  [MISS] {t}: not found")

    print("\n[1/4] Searching authority_chains for pro se authorities...")
    db_authorities = find_authorities_in_db(conn)
    total_auth_hits = sum(len(v) for v in db_authorities.values())
    print(f"  => {total_auth_hits} authority chain matches across {len(db_authorities)} keywords")

    print("[2/4] Loading deadlines...")
    deadlines = find_relevant_deadlines(conn)
    print(f"  => {len(deadlines)} deadlines loaded")

    print("[3/4] Searching docket_events for pro se treatment...")
    docket_events = find_relevant_docket_events(conn)
    print(f"  => {len(docket_events)} relevant docket events")

    print("[4/4] Loading judicial violations...")
    judicial_violations = find_judicial_violations(conn)
    print(f"  => {len(judicial_violations)} judicial violations loaded")

    # Generate reports
    md_report = generate_md(db_authorities, deadlines, docket_events, judicial_violations)
    md_path = os.path.join(REPORTS_DIR, 'PROSE_RIGHTS_GUIDE.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"\n[OK] Markdown: {md_path}")

    json_data = {
        'tool': '#253 Pro Se Litigant Rights Guide',
        'generated': datetime.now().isoformat(),
        'for': 'Andrew James Pigors — Pro Se Plaintiff',
        'case': 'Pigors v. Watson — 2024-001507-DC',
        'sections': {str(k): {
            'title': v['title'],
            'authorities': v['authorities'],
            'content_points': len(v['content']),
        } for k, v in RIGHTS_SECTIONS.items()},
        'db_authority_matches': {k: len(v) for k, v in db_authorities.items()},
        'total_authority_chains': total_auth_hits,
        'deadlines_count': len(deadlines),
        'deadlines': deadlines[:20],
        'docket_events_count': len(docket_events),
        'judicial_violations_count': len(judicial_violations),
    }
    json_path = os.path.join(REPORTS_DIR, 'prose_rights_guide.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"[OK] JSON: {json_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("PRO SE RIGHTS GUIDE SUMMARY")
    print("=" * 70)
    for num in sorted(RIGHTS_SECTIONS.keys()):
        sec = RIGHTS_SECTIONS[num]
        auth_count = len(sec['authorities'])
        lines_count = len(sec['content'])
        print(f"  [{num}] {sec['title'][:50]:<50} {auth_count} authorities, {lines_count} points")
    print(f"\n  DB authority chains matched: {total_auth_hits}")
    print(f"  Active deadlines: {len(deadlines)}")
    print(f"  Judicial violations: {len(judicial_violations)}")
    print(f"  Pro se docket events: {len(docket_events)}")
    print("=" * 70)

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
