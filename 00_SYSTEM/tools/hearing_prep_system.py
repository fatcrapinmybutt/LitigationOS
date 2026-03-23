#!/usr/bin/env python3
"""Tool #256: Court Hearing Preparation System
================================================
Generates comprehensive hearing preparation packages for upcoming hearings.
For the next 3 upcoming hearings: creates agenda/checklist, key arguments,
anticipated opposing arguments with rebuttals, evidence to present,
witness examination outlines, objection cheat sheet (MRE), and logistics.

Queries: deadlines, authority_chains, evidence_quotes, d_drive_rebuttal_pack,
         claims, docket_events, filing_readiness, hearing_calendar
Outputs: MD + JSON reports to 00_SYSTEM/reports/
"""
import sys
import os
import json
import sqlite3
from datetime import datetime, date
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

# --- Verified identities ---
PLAINTIFF = "Andrew James Pigors"
DEFENDANT = "Emily A. Watson"
JUDGE = "Hon. Jenny L. McNeill"
COURT = "14th Circuit Court, Family Division, Muskegon County"
COURT_ADDRESS = "990 Terrace Street, Muskegon, MI 49442"

# --- MRE Objection Reference ---
OBJECTION_CHEATSHEET = [
    {"rule": "MRE 401/402", "objection": "Relevance",
     "when": "Evidence has no tendency to make a fact of consequence more or less probable",
     "response": "Explain the logical connection to a material issue"},
    {"rule": "MRE 403", "objection": "Unfair Prejudice",
     "when": "Probative value substantially outweighed by prejudice, confusion, or waste of time",
     "response": "Argue probative value outweighs and offer limiting instruction"},
    {"rule": "MRE 602", "objection": "Lack of Personal Knowledge",
     "when": "Witness testifying about matters they did not personally observe",
     "response": "Lay foundation showing witness's firsthand knowledge"},
    {"rule": "MRE 611(a)", "objection": "Leading Question",
     "when": "Question suggests the answer on direct examination",
     "response": "Rephrase as open-ended question; permissible on cross"},
    {"rule": "MRE 802", "objection": "Hearsay",
     "when": "Out-of-court statement offered to prove truth of matter asserted",
     "response": "Identify applicable exception (803, 804) or non-hearsay purpose"},
    {"rule": "MRE 803(1)", "objection": "N/A — Present Sense Impression Exception",
     "when": "Statement describing event made while perceiving it or immediately after",
     "response": "Foundation: show temporal connection to the event"},
    {"rule": "MRE 803(2)", "objection": "N/A — Excited Utterance Exception",
     "when": "Statement relating to startling event made under stress of excitement",
     "response": "Foundation: show the declarant was still under stress"},
    {"rule": "MRE 803(3)", "objection": "N/A — State of Mind Exception",
     "when": "Statement of declarant's then-existing state of mind, emotion, or physical condition",
     "response": "Show relevance of declarant's mental state"},
    {"rule": "MRE 803(4)", "objection": "N/A — Medical Diagnosis/Treatment Exception",
     "when": "Statements made for medical treatment/diagnosis",
     "response": "Show statement was pertinent to diagnosis/treatment"},
    {"rule": "MRE 803(6)", "objection": "N/A — Business Records Exception",
     "when": "Records kept in regular course of business",
     "response": "Foundation via custodian or qualified witness"},
    {"rule": "MRE 803(8)", "objection": "N/A — Public Records Exception",
     "when": "Records of public offices setting forth official activities",
     "response": "Authenticate as public record"},
    {"rule": "MRE 901", "objection": "Authentication / Foundation",
     "when": "Proponent has not shown evidence is what it claims to be",
     "response": "Lay proper foundation (testimony, distinctive characteristics, chain of custody)"},
    {"rule": "MRE 1002", "objection": "Best Evidence Rule",
     "when": "Copy offered instead of original document",
     "response": "Original unavailable; or duplicate admissible under MRE 1003"},
    {"rule": "MRE 404(a)", "objection": "Character Evidence",
     "when": "Evidence of person's character offered to prove action in conformity",
     "response": "Permissible exceptions: habit (406), motive, plan, identity (404(b))"},
    {"rule": "MRE 404(b)", "objection": "Prior Bad Acts",
     "when": "Evidence of other crimes/wrongs to show character/action in conformity",
     "response": "Offered for permissible purpose: motive, opportunity, intent, plan, knowledge"},
    {"rule": "MCR 2.302", "objection": "Privilege",
     "when": "Question calls for privileged communication (attorney-client, spousal, etc.)",
     "response": "Argue waiver, crime-fraud exception, or that privilege does not apply"},
    {"rule": "MRE 701", "objection": "Improper Lay Opinion",
     "when": "Lay witness giving opinion not rationally based on perception",
     "response": "Foundation showing opinion based on firsthand knowledge and helpful to trier of fact"},
    {"rule": "MRE 702", "objection": "Expert Qualification",
     "when": "Witness not qualified as expert in relevant field",
     "response": "Demonstrate education, training, experience, and methodology (Daubert/Davis)"},
]

# --- Witness examination patterns ---
WITNESS_PATTERNS = {
    "FOC_caseworker": {
        "name": "FOC Caseworker (Pamela Rusco)",
        "direct_topics": [
            "Parenting time recommendations made",
            "Basis for any restrictions",
            "Observations of parent-child interaction",
            "Compliance with existing orders by both parties",
        ],
        "cross_topics": [
            "How many home visits were conducted?",
            "Did you interview the child privately?",
            "What specific evidence of harm did you observe?",
            "Were both parents given equal consideration?",
            "Did you review all submitted evidence?",
        ],
    },
    "teacher": {
        "name": "Child's Teacher / School Personnel",
        "direct_topics": [
            "Child's academic performance and behavior",
            "Changes observed over time",
            "Parent involvement in school activities",
            "Communications from each parent",
        ],
        "cross_topics": [
            "Have you observed the child with each parent?",
            "Any concerns about either parent?",
            "Is the child's performance consistent?",
        ],
    },
    "family_member": {
        "name": "Family Member / Character Witness",
        "direct_topics": [
            "Relationship to plaintiff and child",
            "Observations of plaintiff as parent",
            "Child's behavior during visits with plaintiff",
            "Changes observed since custody issues began",
        ],
        "cross_topics": [
            "Frequency of personal observations",
            "Any bias or interest in the outcome?",
        ],
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
def get_upcoming_hearings(conn, limit=3):
    """Get next upcoming hearings/deadlines."""
    hearings = []

    # Try hearing_calendar first
    if table_exists(conn, 'hearing_calendar'):
        cols = get_columns(conn, 'hearing_calendar')
        print(f"    hearing_calendar columns: {cols}")
        date_col = next((c for c in cols if 'date' in s(c)), None)
        if date_col:
            rows = safe_query(conn,
                f"SELECT * FROM hearing_calendar WHERE [{date_col}] >= ? ORDER BY [{date_col}] ASC LIMIT ?",
                (date.today().isoformat(), limit))
            for r in rows:
                d = dict(r)
                hearings.append({
                    "source": "hearing_calendar",
                    "date": d.get(date_col, 'TBD'),
                    "title": d.get('title', d.get('hearing_type', d.get('description', 'Hearing'))),
                    "case_id": d.get('case_id', d.get('case_number', '')),
                    "location": d.get('location', d.get('courtroom', COURT_ADDRESS)),
                    "raw": d,
                })

    # Also check deadlines table for hearing-type deadlines
    if table_exists(conn, 'deadlines') and len(hearings) < limit:
        cols = get_columns(conn, 'deadlines')
        print(f"    deadlines columns: {cols}")
        date_col = 'due_date_iso' if 'due_date_iso' in cols else ('due_date' if 'due_date' in cols else None)
        title_col = 'title' if 'title' in cols else ('description' if 'description' in cols else None)
        status_col = 'status' if 'status' in cols else None

        if date_col:
            conditions = [f"[{date_col}] >= ?"]
            params = [date.today().isoformat()]
            if status_col:
                conditions.append(f"([{status_col}] = 'upcoming' OR [{status_col}] = 'pending' OR [{status_col}] IS NULL)")
            sql = f"SELECT * FROM deadlines WHERE {' AND '.join(conditions)} ORDER BY [{date_col}] ASC LIMIT ?"
            params.append(limit * 2)
            rows = safe_query(conn, sql, tuple(params))

            for r in rows:
                d = dict(r)
                hearings.append({
                    "source": "deadlines",
                    "date": d.get(date_col, 'TBD'),
                    "title": d.get(title_col, 'Deadline') if title_col else 'Deadline',
                    "case_id": d.get('case_id', ''),
                    "basis": d.get('basis', d.get('basis_authority', '')),
                    "risk": d.get('risk_if_missed', ''),
                    "location": COURT_ADDRESS,
                    "raw": d,
                })

    # If no future dates found, get the most recent deadlines as examples
    if not hearings and table_exists(conn, 'deadlines'):
        cols = get_columns(conn, 'deadlines')
        date_col = 'due_date_iso' if 'due_date_iso' in cols else ('due_date' if 'due_date' in cols else None)
        title_col = 'title' if 'title' in cols else ('description' if 'description' in cols else None)
        if date_col:
            rows = safe_query(conn, f"SELECT * FROM deadlines ORDER BY [{date_col}] DESC LIMIT ?", (limit,))
            for r in rows:
                d = dict(r)
                hearings.append({
                    "source": "deadlines (historical — no future dates found)",
                    "date": d.get(date_col, 'TBD'),
                    "title": d.get(title_col, 'Deadline') if title_col else 'Deadline',
                    "case_id": d.get('case_id', ''),
                    "basis": d.get('basis', d.get('basis_authority', '')),
                    "risk": d.get('risk_if_missed', ''),
                    "location": COURT_ADDRESS,
                    "raw": d,
                })

    return hearings[:limit]


def get_relevant_authorities(conn, keywords, limit=10):
    """Get authority chains relevant to hearing topics."""
    if not table_exists(conn, 'authority_chains'):
        return []
    cols = get_columns(conn, 'authority_chains')
    results = []
    search_cols = [c for c in ['fact_claim', 'authority_cite', 'filing_vehicle', 'elements'] if c in cols]
    for kw in keywords[:5]:
        for col in search_cols[:3]:
            rows = safe_query(conn, f"SELECT * FROM authority_chains WHERE [{col}] LIKE ? LIMIT ?",
                              (f'%{kw}%', limit))
            results.extend(rows)
    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        d = dict(r)
        key = d.get('authority_cite', str(d.get('id', '')))
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique[:limit]


def get_rebuttals(conn, keywords, limit=10):
    """Get rebuttals from d_drive_rebuttal_pack."""
    if not table_exists(conn, 'd_drive_rebuttal_pack'):
        return []
    cols = get_columns(conn, 'd_drive_rebuttal_pack')
    results = []
    search_cols = [c for c in ['target_quote', 'rebuttal_theory', 'target_type'] if c in cols]
    if not search_cols:
        search_cols = cols[:3]
    for kw in keywords[:5]:
        for col in search_cols[:2]:
            rows = safe_query(conn, f"SELECT * FROM d_drive_rebuttal_pack WHERE [{col}] LIKE ? LIMIT ?",
                              (f'%{kw}%', limit))
            results.extend(rows)
    seen = set()
    unique = []
    for r in results:
        d = dict(r)
        key = d.get('pair_id', str(d.get('id', id(r))))
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique[:limit]


def get_evidence_for_hearing(conn, keywords, limit=15):
    """Get evidence quotes relevant to hearing topics."""
    if not table_exists(conn, 'evidence_quotes'):
        return []
    cols = get_columns(conn, 'evidence_quotes')
    text_col = 'quote_text' if 'quote_text' in cols else ('text' if 'text' in cols else None)
    if not text_col:
        return []
    results = []
    for kw in keywords[:5]:
        rows = safe_query(conn,
            f"SELECT * FROM evidence_quotes WHERE [{text_col}] LIKE ? LIMIT ?",
            (f'%{kw}%', limit))
        results.extend(rows)
    seen = set()
    unique = []
    hash_col = 'quote_hash' if 'quote_hash' in cols else None
    for r in results:
        d = dict(r)
        key = d.get(hash_col, str(d.get('id', id(r)))) if hash_col else str(d.get('id', id(r)))
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique[:limit]


def get_docket_history(conn, case_id, limit=10):
    """Get recent docket events for context."""
    if not table_exists(conn, 'docket_events'):
        return []
    cols = get_columns(conn, 'docket_events')
    case_col = 'case_id' if 'case_id' in cols else None
    date_col = 'event_date_iso' if 'event_date_iso' in cols else ('event_date' if 'event_date' in cols else None)
    if not case_col:
        return []
    sql = f"SELECT * FROM docket_events WHERE [{case_col}] LIKE ? ORDER BY [{date_col or 'rowid'}] DESC LIMIT ?"
    return [dict(r) for r in safe_query(conn, sql, (f'%{case_id}%', limit))]


# --- Report generation ---
def build_hearing_package(conn, hearing, index):
    """Build a full hearing prep package for one hearing."""
    h = hearing
    title = h.get('title', 'Hearing')
    hearing_date = h.get('date', 'TBD')
    case_id = h.get('case_id', '2024-001507-DC')

    # Extract keywords from hearing title for searching
    keywords = [w for w in s(title).split() if len(w) > 3 and w not in
                {'this', 'that', 'with', 'from', 'been', 'have', 'will', 'must', 'should', 'upon'}]
    # Add case-relevant keywords
    keywords.extend(['custody', 'parenting', 'child', 'order', 'motion'])
    keywords = list(set(keywords))[:10]

    print(f"    Searching for authorities, rebuttals, evidence...")
    authorities = get_relevant_authorities(conn, keywords, limit=8)
    rebuttals = get_rebuttals(conn, keywords, limit=8)
    evidence = get_evidence_for_hearing(conn, keywords, limit=12)
    docket = get_docket_history(conn, case_id, limit=8)

    print(f"    Found: {len(authorities)} authorities, {len(rebuttals)} rebuttals, "
          f"{len(evidence)} evidence quotes, {len(docket)} docket events")

    package = {
        "hearing_index": index,
        "title": title,
        "date": hearing_date,
        "case_id": case_id,
        "source": h.get('source', ''),
        "location": h.get('location', COURT_ADDRESS),
    }

    # --- 1. Agenda / Checklist ---
    agenda = {
        "pre_hearing": [
            "Review all evidence exhibits and organize by topic",
            "Prepare 3 copies of each exhibit (court, opposing, self)",
            "Print and review hearing outline",
            "Confirm hearing date/time with court clerk",
            f"File proof of service at least 7 days before hearing ({hearing_date})",
            "Prepare binder with tabbed sections",
            "Review applicable court rules and standards",
            "Practice opening statement (2-3 minutes max)",
        ],
        "day_of": [
            f"Arrive at {COURT_ADDRESS} at least 30 minutes early",
            "Check in with court clerk upon arrival",
            "Dress professionally (suit/business attire)",
            "Bring: photo ID, case file, exhibits, pen, notepad",
            "Silence phone before entering courtroom",
            "Stand when judge enters/exits; address as 'Your Honor'",
            "Speak clearly and at moderate pace",
        ],
        "during_hearing": [
            "State name and case number for the record",
            "Present evidence in organized, logical sequence",
            "Object promptly to inadmissible evidence (see Objection Cheatsheet)",
            "Take notes on judge's comments and opposing arguments",
            "Request clarification on any orders issued",
        ],
        "post_hearing": [
            "Request copy of any written orders",
            "Note deadline for any post-hearing submissions",
            "Write summary of what happened while fresh",
            "Identify any appeal issues to preserve",
        ],
    }
    package["agenda"] = agenda

    # --- 2. Key Arguments ---
    key_args = []
    for auth in authorities[:6]:
        cite = auth.get('authority_cite', auth.get('citation', ''))
        claim = auth.get('fact_claim', auth.get('claim', ''))
        elements = auth.get('elements', '')
        ev = auth.get('evidence_quote', '')
        key_args.append({
            "authority": cite,
            "claim": claim,
            "elements": elements,
            "supporting_evidence": ev[:200] + "..." if ev and len(ev) > 200 else (ev or ""),
            "chain_complete": bool(auth.get('chain_complete', 0)),
        })
    if not key_args:
        key_args.append({
            "authority": "MCL 722.27a / MCR 3.207",
            "claim": "Parenting time should be restored in the best interest of the child",
            "elements": "No finding of harm justifying denial; child needs both parents",
            "supporting_evidence": "[Insert strongest evidence quote here]",
            "chain_complete": False,
        })
    package["key_arguments"] = key_args

    # --- 3. Anticipated Opposition + Rebuttals ---
    opposition = []
    for reb in rebuttals[:8]:
        target = reb.get('target_quote', reb.get('assertion', ''))
        theory = reb.get('rebuttal_theory', reb.get('rebuttal', ''))
        proof = reb.get('proof_slots', '')
        status = reb.get('status', 'CANDIDATE')
        opposition.append({
            "opposing_argument": target[:300] if target else "Anticipated opposing point",
            "rebuttal_theory": theory[:300] if theory else "",
            "proof_needed": proof[:200] if proof else "",
            "status": status,
        })
    if not opposition:
        opposition.append({
            "opposing_argument": "Defendant may argue safety concerns justify restrictions",
            "rebuttal_theory": "No evidence of actual harm; restrictions lack statutory basis",
            "proof_needed": "Clean background, home study, character witnesses",
            "status": "PREPARED",
        })
    package["anticipated_opposition"] = opposition

    # --- 4. Evidence to Present ---
    evidence_list = []
    for i, ev in enumerate(evidence[:10], 1):
        text = ev.get('quote_text', ev.get('text', ''))
        category = ev.get('evidence_category', ev.get('category', ''))
        speaker = ev.get('speaker', '')
        page = ev.get('page_number', '')
        significance = ev.get('legal_significance', '')
        evidence_list.append({
            "exhibit_no": f"Exhibit {i}",
            "category": category,
            "quote_preview": text[:200] + "..." if text and len(text) > 200 else (text or ""),
            "speaker": speaker,
            "page": page,
            "legal_significance": significance[:200] if significance else "",
        })
    package["evidence_to_present"] = evidence_list

    # --- 5. Witnesses ---
    package["witness_outlines"] = WITNESS_PATTERNS

    # --- 6. Objection Cheatsheet ---
    package["objection_cheatsheet"] = OBJECTION_CHEATSHEET

    # --- 7. Logistics ---
    package["logistics"] = {
        "court": COURT,
        "address": COURT_ADDRESS,
        "judge": JUDGE,
        "case_numbers": {
            "custody": "2024-001507-DC",
            "ppo": "2023-5907-PP",
        },
        "filing_method": "MiFILE (mifile.courts.michigan.gov)",
        "service_requirements": {
            "method": "First-class mail or MiFILE electronic service",
            "deadline": "At least 7 days before hearing per MCR 2.107",
            "proof": "File proof of service with court before hearing",
        },
        "copies_needed": {
            "court_original": 1,
            "judge_copy": 1,
            "opposing_party": 1,
            "personal_copy": 1,
            "total": 4,
        },
        "what_to_bring": [
            "Photo ID",
            "Complete case file binder",
            "All exhibits (4 copies each)",
            "This hearing prep package",
            "Pen and notepad",
            "Copies of relevant court rules",
            "Proof of service",
        ],
    }

    # --- Recent docket context ---
    package["recent_docket"] = docket[:5]

    return package


def package_to_markdown(pkg):
    """Convert a hearing package to markdown."""
    lines = []
    lines.append(f"# HEARING PREP: {pkg['title']}")
    lines.append(f"**Date:** {pkg['date']} | **Case:** {pkg['case_id']}")
    lines.append(f"**Location:** {pkg['location']}")
    lines.append(f"**Source:** {pkg['source']}")
    lines.append("")

    # Agenda
    lines.append("## 1. HEARING AGENDA / CHECKLIST\n")
    for phase, items in pkg['agenda'].items():
        lines.append(f"### {phase.replace('_', ' ').title()}")
        for item in items:
            lines.append(f"- [ ] {item}")
        lines.append("")

    # Key Arguments
    lines.append("## 2. KEY ARGUMENTS WITH AUTHORITIES\n")
    for i, arg in enumerate(pkg['key_arguments'], 1):
        complete = "✅" if arg.get('chain_complete') else "⚠️"
        lines.append(f"### Argument {i}: {arg['authority']} {complete}\n")
        lines.append(f"**Claim:** {arg['claim']}")
        if arg.get('elements'):
            lines.append(f"**Elements:** {arg['elements']}")
        if arg.get('supporting_evidence'):
            lines.append(f"**Evidence:** \"{arg['supporting_evidence']}\"")
        lines.append("")

    # Opposition + Rebuttals
    lines.append("## 3. ANTICIPATED OPPOSITION & REBUTTALS\n")
    for i, opp in enumerate(pkg['anticipated_opposition'], 1):
        lines.append(f"### Opposition Point {i} [{opp['status']}]\n")
        lines.append(f"**They will argue:** {opp['opposing_argument']}")
        lines.append(f"**Our rebuttal:** {opp['rebuttal_theory']}")
        if opp.get('proof_needed'):
            lines.append(f"**Proof needed:** {opp['proof_needed']}")
        lines.append("")

    # Evidence
    lines.append("## 4. EVIDENCE TO PRESENT\n")
    lines.append("| # | Category | Quote Preview | Speaker | Significance |")
    lines.append("|---|----------|---------------|---------|-------------|")
    for ev in pkg['evidence_to_present']:
        preview = ev['quote_preview'][:80].replace('|', '/').replace('\n', ' ')
        lines.append(f"| {ev['exhibit_no']} | {ev.get('category', '')} | {preview} | {ev.get('speaker', '')} | {ev.get('legal_significance', '')[:50]} |")
    lines.append("")

    # Witnesses
    lines.append("## 5. WITNESS EXAMINATION OUTLINES\n")
    for wid, w in pkg['witness_outlines'].items():
        lines.append(f"### {w['name']}\n")
        lines.append("**Direct Examination:**")
        for t in w['direct_topics']:
            lines.append(f"- {t}")
        lines.append("\n**Cross-Examination Questions:**")
        for t in w['cross_topics']:
            lines.append(f"- {t}")
        lines.append("")

    # Objection Cheatsheet
    lines.append("## 6. OBJECTION CHEAT SHEET (MRE)\n")
    lines.append("| Rule | Objection | When to Object | Response |")
    lines.append("|------|-----------|---------------|----------|")
    for obj in pkg['objection_cheatsheet']:
        when_short = obj['when'][:60].replace('|', '/')
        resp_short = obj['response'][:60].replace('|', '/')
        lines.append(f"| {obj['rule']} | {obj['objection']} | {when_short} | {resp_short} |")
    lines.append("")

    # Logistics
    lines.append("## 7. COURTROOM LOGISTICS\n")
    lg = pkg['logistics']
    lines.append(f"**Court:** {lg['court']}")
    lines.append(f"**Address:** {lg['address']}")
    lines.append(f"**Judge:** {lg['judge']}")
    lines.append(f"**Filing:** {lg['filing_method']}")
    lines.append(f"\n**Service Requirements:**")
    sr = lg['service_requirements']
    lines.append(f"- Method: {sr['method']}")
    lines.append(f"- Deadline: {sr['deadline']}")
    lines.append(f"- Proof: {sr['proof']}")
    lines.append(f"\n**Copies needed:** {lg['copies_needed']['total']} total")
    lines.append(f"\n**What to bring:**")
    for item in lg['what_to_bring']:
        lines.append(f"- [ ] {item}")
    lines.append("")

    # Recent docket
    if pkg.get('recent_docket'):
        lines.append("## 8. RECENT DOCKET HISTORY\n")
        for evt in pkg['recent_docket']:
            d = evt.get('event_date_iso', evt.get('event_date', 'N/A'))
            t = evt.get('title', evt.get('event_title', 'Event'))
            lines.append(f"- **{d}**: {t}")
        lines.append("")

    return "\n".join(lines)


# --- Main ---
def main():
    print("=" * 70)
    print("  TOOL #256: COURT HEARING PREPARATION SYSTEM")
    print("  Generates comprehensive hearing preparation packages")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"  [ERROR] Database not found: {DB_PATH}")
        return

    conn = get_db()

    # Verify key tables
    key_tables = ['deadlines', 'authority_chains', 'evidence_quotes', 'd_drive_rebuttal_pack',
                  'hearing_calendar', 'docket_events', 'claims']
    for t in key_tables:
        exists = table_exists(conn, t)
        print(f"  [{'OK' if exists else 'WARN'}] Table '{t}': {'found' if exists else 'NOT FOUND'}")

    # Get upcoming hearings
    print(f"\n  Searching for upcoming hearings...")
    hearings = get_upcoming_hearings(conn, limit=3)
    print(f"  [OK] Found {len(hearings)} hearing/deadline entries")

    if not hearings:
        print("  [WARN] No hearings found — generating template packages for reference")
        hearings = [
            {"source": "template", "date": "TBD", "title": "Emergency Motion Hearing",
             "case_id": "2024-001507-DC", "location": COURT_ADDRESS},
            {"source": "template", "date": "TBD", "title": "Custody Modification Hearing",
             "case_id": "2024-001507-DC", "location": COURT_ADDRESS},
            {"source": "template", "date": "TBD", "title": "PPO Review Hearing",
             "case_id": "2023-5907-PP", "location": COURT_ADDRESS},
        ]

    report = {
        "tool": "#256 Court Hearing Preparation System",
        "generated": datetime.now().isoformat(),
        "case": "Pigors v. Watson",
        "hearings_found": len(hearings),
        "packages": [],
        "statistics": {},
    }

    md_lines = [
        "# TOOL #256: COURT HEARING PREPARATION SYSTEM",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Case:** Pigors v. Watson",
        f"**Hearings Prepared:** {len(hearings)}",
        "",
    ]

    total_authorities = 0
    total_rebuttals = 0
    total_evidence = 0

    for i, hearing in enumerate(hearings, 1):
        print(f"\n  [Hearing {i}/{len(hearings)}] {hearing.get('title', 'TBD')} — {hearing.get('date', 'TBD')}")

        package = build_hearing_package(conn, hearing, i)
        report["packages"].append(package)

        total_authorities += len(package['key_arguments'])
        total_rebuttals += len(package['anticipated_opposition'])
        total_evidence += len(package['evidence_to_present'])

        md_content = package_to_markdown(package)
        md_lines.append("---\n")
        md_lines.append(md_content)

        print(f"    [OK] Package built: {len(package['key_arguments'])} arguments, "
              f"{len(package['anticipated_opposition'])} rebuttals, "
              f"{len(package['evidence_to_present'])} exhibits")

    report["statistics"] = {
        "hearings_prepared": len(hearings),
        "total_arguments": total_authorities,
        "total_rebuttals": total_rebuttals,
        "total_evidence_items": total_evidence,
        "objection_rules_included": len(OBJECTION_CHEATSHEET),
        "witness_patterns_included": len(WITNESS_PATTERNS),
        "tables_queried": ["deadlines", "hearing_calendar", "authority_chains",
                           "d_drive_rebuttal_pack", "evidence_quotes", "docket_events"],
    }

    conn.close()

    # Write JSON report
    json_path = os.path.join(REPORT_DIR, "hearing_prep_system.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  [OK] JSON report: {json_path}")

    # Write Markdown report
    md_path = os.path.join(REPORT_DIR, "HEARING_PREP_SYSTEM.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    print(f"  [OK] Markdown report: {md_path}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Hearings prepared: {len(hearings)}")
    print(f"  Total arguments with authority: {total_authorities}")
    print(f"  Total rebuttals ready: {total_rebuttals}")
    print(f"  Total evidence items: {total_evidence}")
    print(f"  MRE objection rules: {len(OBJECTION_CHEATSHEET)}")
    print(f"  Witness patterns: {len(WITNESS_PATTERNS)}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
