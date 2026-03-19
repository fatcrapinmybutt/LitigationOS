#!/usr/bin/env python3
# LitigationOS Timeline Builder v1.0
# Generates 6 dense chronological timelines from litigation_context.db
# for Pigors v. Watson consolidated Michigan family law litigation.
# Output: LitigationOS/06_TIMELINES/
# Database: litigation_context.db

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = r"C:\Users\andre\litigation_context.db"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\06_TIMELINES"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def safe_query(conn, sql, params=None):
    """Execute query with error handling."""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        print(f"  [WARN] Query failed: {e}")
        return []


def normalize_date(date_str):
    """Normalize date strings to YYYY-MM-DD where possible."""
    if not date_str or date_str in ('Unknown', '', 'None', 'N/A'):
        return None
    date_str = str(date_str).strip()
    # Already in ISO format
    if len(date_str) >= 10 and date_str[4:5] == '-':
        return date_str[:10]
    # Try common formats
    for fmt in ('%m/%d/%Y', '%B %d, %Y', '%b %d, %Y', '%m/%d/%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def escape_pipe(text):
    """Escape pipe characters for markdown tables."""
    if not text:
        return ""
    return str(text).replace('|', '\\|').replace('\n', ' ').replace('\r', '').strip()


def truncate(text, maxlen=300):
    """Truncate text to maxlen."""
    if not text:
        return ""
    t = str(text).replace('\n', ' ').replace('\r', '').strip()
    if len(t) > maxlen:
        return t[:maxlen] + "..."
    return t


def write_header(f, title, subtitle, case_info):
    """Write standard timeline header."""
    f.write(f"# {title}\n\n")
    f.write(f"**{subtitle}**\n\n")
    f.write(f"**Case:** {case_info}\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}\n\n")
    f.write(f"**Source:** litigation_context.db (LitigationOS)\n\n")
    f.write("---\n\n")


def write_table_header(f):
    """Write markdown table header."""
    f.write("| # | Date | Event | Source | Legal Significance | Exhibit Ref |\n")
    f.write("|---|------|-------|--------|-------------------|-------------|\n")


def write_row(f, num, date, event, source, significance, exhibit):
    """Write a single timeline row."""
    f.write(f"| {num} | {escape_pipe(date or 'Unknown')} | {escape_pipe(truncate(event, 250))} | {escape_pipe(truncate(source, 100))} | {escape_pipe(truncate(significance, 150))} | {escape_pipe(truncate(exhibit, 80))} |\n")


# ============================================================
# TIMELINE 1: CUSTODY CASE TIMELINE
# ============================================================
def build_custody_timeline(conn):
    print("Building CUSTODY_CASE_TIMELINE.md...")
    events = []

    # 1. Docket events for custody case
    rows = safe_query(conn, """
        SELECT event_date_iso, title, event_type, summary, truth_tag
        FROM docket_events
        WHERE case_id LIKE '%1507%' OR case_id LIKE '%custody%' OR case_id LIKE '%DC%'
        ORDER BY event_date_iso
    """)
    for r in rows:
        events.append({
            'date': r['event_date_iso'],
            'event': f"[{r['event_type'].upper()}] {r['title']}: {r['summary']}",
            'source': f"docket_events ({r['truth_tag']})",
            'significance': '',
            'exhibit': r['event_type']
        })

    # 2. Master timeline - custody lane events
    rows = safe_query(conn, """
        SELECT date_iso, description, category, severity, case_lane, source_table, citations
        FROM master_timeline
        WHERE (case_lane IN ('MEEK1', 'A') OR description LIKE '%1507%' OR description LIKE '%custody%')
          AND category IN ('filing', 'order', 'hearing', 'violation', 'incident')
        ORDER BY date_iso
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[{r['category'].upper()}] {truncate(r['description'], 250)}",
            'source': f"master_timeline/{r['source_table']}",
            'significance': f"Severity: {r['severity'] or 'N/A'}",
            'exhibit': r['citations'] or ''
        })

    # 3. Evidence quotes - custody orders and transcripts
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, speaker, legal_significance, document_id, page_number
        FROM evidence_quotes
        WHERE evidence_category IN ('CUSTODY_ORDER', 'EX_PARTE_ORDER', 'TRANSCRIPT', 'JUDGE_ORDER')
        ORDER BY date_ref
    """)
    for r in rows:
        events.append({
            'date': r['date_ref'],
            'event': f"[{r['evidence_category']}] {r['speaker'] or 'N/A'}: {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes (doc:{r['document_id']}, p:{r['page_number']})",
            'significance': r['legal_significance'] or '',
            'exhibit': f"Doc {r['document_id']}"
        })

    # 4. Global chronology - custody related
    rows = safe_query(conn, """
        SELECT date, issue, shortfact240, sourcefile
        FROM global_chronology
        WHERE issue IN ('exchanges/denials', 'service/notice')
           OR shortfact240 LIKE '%custody%'
           OR shortfact240 LIKE '%1507%'
           OR shortfact240 LIKE '%parenting time%'
        ORDER BY date
        LIMIT 200
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': f"[{r['issue']}] {truncate(r['shortfact240'], 200)}",
            'source': f"global_chronology/{r['sourcefile'] or 'N/A'}",
            'significance': '',
            'exhibit': ''
        })

    # 5. Chronological misconduct - custody related
    rows = safe_query(conn, """
        SELECT date, issue FROM chronological_misconduct
        WHERE issue LIKE '%custody%' OR issue LIKE '%parenting%' OR issue LIKE '%ex parte%'
           OR issue LIKE '%1507%' OR issue LIKE '%order%'
        ORDER BY date
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': truncate(r['issue'], 250),
            'source': 'chronological_misconduct',
            'significance': 'Documented misconduct',
            'exhibit': ''
        })

    # Deduplicate and sort
    events = dedupe_and_sort(events)

    # Write file
    filepath = os.path.join(OUTPUT_DIR, "CUSTODY_CASE_TIMELINE.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "CUSTODY CASE TIMELINE",
            "Pigors v. Watson — Case No. 2024-001507-DC",
            "14th Circuit Court, Muskegon County | Hon. Jenny L. McNeill"
        )
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Events:** {len(events)}\n")
        f.write(f"- **Date Range:** {events[0]['date'] if events else 'N/A'} to {events[-1]['date'] if events else 'N/A'}\n")
        f.write(f"- **Data Sources:** docket_events, master_timeline, evidence_quotes, global_chronology, chronological_misconduct\n")
        f.write(f"- **Parent-Child Separation:** 211+ days (since July 29, 2025)\n\n")
        f.write("---\n\n")
        f.write("## Chronological Events\n\n")
        write_table_header(f)
        for i, ev in enumerate(events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

    print(f"  -> {filepath} ({len(events)} events)")
    return len(events)


# ============================================================
# TIMELINE 2: PPO CASE TIMELINE
# ============================================================
def build_ppo_timeline(conn):
    print("Building PPO_CASE_TIMELINE.md...")
    events = []

    # 1. Docket events for PPO case
    rows = safe_query(conn, """
        SELECT event_date_iso, title, event_type, summary, truth_tag
        FROM docket_events
        WHERE case_id LIKE '%5907%' OR case_id LIKE '%PP%'
        ORDER BY event_date_iso
    """)
    for r in rows:
        events.append({
            'date': r['event_date_iso'],
            'event': f"[{r['event_type'].upper()}] {r['title']}: {r['summary']}",
            'source': f"docket_events ({r['truth_tag']})",
            'significance': '',
            'exhibit': r['event_type']
        })

    # 2. Master timeline - PPO lane events
    rows = safe_query(conn, """
        SELECT date_iso, description, category, severity, case_lane, source_table, citations
        FROM master_timeline
        WHERE case_lane IN ('MEEK2', 'MEEK4', 'D')
           OR description LIKE '%PPO%'
           OR description LIKE '%5907%'
           OR description LIKE '%protection order%'
           OR description LIKE '%show cause%'
        ORDER BY date_iso
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[{r['category'].upper()}] {truncate(r['description'], 250)}",
            'source': f"master_timeline/{r['source_table']}",
            'significance': f"Severity: {r['severity'] or 'N/A'}",
            'exhibit': r['citations'] or ''
        })

    # 3. Evidence quotes - PPO related
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, speaker, legal_significance, document_id, page_number
        FROM evidence_quotes
        WHERE evidence_category = 'PPO'
        ORDER BY date_ref
    """)
    for r in rows:
        events.append({
            'date': r['date_ref'],
            'event': f"[PPO EVIDENCE] {r['speaker'] or 'N/A'}: {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes (doc:{r['document_id']}, p:{r['page_number']})",
            'significance': r['legal_significance'] or '',
            'exhibit': f"Doc {r['document_id']}"
        })

    # 4. Global chronology - PPO chain
    rows = safe_query(conn, """
        SELECT date, issue, shortfact240, sourcefile
        FROM global_chronology
        WHERE issue = 'PPO chain'
           OR shortfact240 LIKE '%PPO%'
           OR shortfact240 LIKE '%protection order%'
           OR shortfact240 LIKE '%show cause%'
        ORDER BY date
        LIMIT 200
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': f"[PPO CHAIN] {truncate(r['shortfact240'], 200)}",
            'source': f"global_chronology/{r['sourcefile'] or 'N/A'}",
            'significance': '',
            'exhibit': ''
        })

    # 5. Forensic analysis - PPO weaponization
    rows = safe_query(conn, """
        SELECT date_iso, description, category, severity, evidence_citations, mcr_violations, source_table
        FROM forensic_judicial_analysis
        WHERE category = 'PPO_WEAPONIZATION'
        ORDER BY date_iso
        LIMIT 100
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[PPO WEAPONIZATION] {truncate(r['description'], 200)}",
            'source': f"forensic_judicial_analysis/{r['source_table']}",
            'significance': f"{r['mcr_violations'] or ''} (Severity: {r['severity']})",
            'exhibit': r['evidence_citations'] or ''
        })

    # 6. Global weaponization evidence
    rows = safe_query(conn, """
        SELECT * FROM global_weaponization
        ORDER BY rowid
        LIMIT 50
    """)
    for r in rows:
        cols = dict(r)
        text = str(list(cols.values())[:3])
        events.append({
            'date': '',
            'event': f"[WEAPONIZATION] {truncate(text, 200)}",
            'source': 'global_weaponization',
            'significance': 'PPO as litigation weapon',
            'exhibit': ''
        })

    events = dedupe_and_sort(events)

    filepath = os.path.join(OUTPUT_DIR, "PPO_CASE_TIMELINE.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "PPO CASE TIMELINE",
            "Pigors v. Watson — Case No. 2023-5907-PP",
            "14th Circuit Court, Muskegon County | Hon. Jenny L. McNeill"
        )
        f.write("## Key Theme: PPO as Litigation Weapon\n\n")
        f.write("Watson obtained a PPO with alleged staged evidence, submitting a bruise TWO weeks after the alleged incident.\n")
        f.write("The PPO has been weaponized to restrict Andrew's parenting time and used as a tool for parental alienation.\n\n")
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Events:** {len(events)}\n")
        f.write(f"- **Data Sources:** docket_events, master_timeline, evidence_quotes, global_chronology, forensic_judicial_analysis\n\n")
        f.write("---\n\n")
        f.write("## Chronological Events\n\n")
        write_table_header(f)
        for i, ev in enumerate(events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

    print(f"  -> {filepath} ({len(events)} events)")
    return len(events)


# ============================================================
# TIMELINE 3: FATHER-SON SEPARATION TIMELINE
# ============================================================
def build_separation_timeline(conn):
    print("Building FATHER_SON_SEPARATION_TIMELINE.md...")

    # Start date: July 29, 2025
    # Current reference: Feb 25, 2026
    start = datetime(2025, 7, 29)
    today = datetime.now()
    days_separated = (today - start).days

    # Key milestones and holidays missed
    milestones = [
        ("2025-07-29", "LAST CONTACT", "Last day Andrew saw his son. Beginning of forced separation.", "Record", "Due Process — MCL 722.27(1)(c)"),
        ("2025-08-08", "EX PARTE ORDER", "Court suspends ALL parenting time without hearing, findings, or best interest analysis. No MCL 722.23 factors weighed.", "Court Order", "MCL 722.27(1)(c), MCL 722.23(a)-(l), Canon 3(B)(5)"),
        ("2025-08-22", "HEARING", "Hearing held 8/22/25 — Court orders assessment but does NOT restore any parenting time.", "Transcript", "MCL 722.27a(9) — mandatory remedies not applied"),
        ("2025-09-01", "LABOR DAY WEEKEND", "First major holiday missed. Day 34 of separation. No phone calls, no visits.", "Calendar", "MCL 722.27a — parenting time rights"),
        ("2025-09-12", "ASSESSMENT RECEIVED", "Court receives 2nd assessment on 9/12/25. Hearing set for 10/29/25 — 47 more days of separation.", "Transcript", "Unreasonable delay"),
        ("2025-09-22", "HEALTH WEST ORDER", "Court orders Health West assessment for Andrew. Still no parenting time restored.", "Court Order", "Due Process violation — burden on father"),
        ("2025-10-11", "ANDREW DECLARATION", "Andrew files declaration documenting surprise witness, service defects, ex parte flash drive audio.", "Declaration", "Canon 3(A)(4)"),
        ("2025-10-29", "HEARING", "Hearing held — both parties present. Day 92 of separation.", "Record", "MCL 722.23"),
        ("2025-10-31", "HALLOWEEN", f"Day {(datetime(2025,10,31)-start).days} — Son's 3rd Halloween. Andrew cannot take his son trick-or-treating.", "Calendar", "Emotional harm — MCL 722.23(f)"),
        ("2025-11-09", "SON'S 3RD BIRTHDAY", f"Day {(datetime(2025,11,9)-start).days} — Son turns 3 years old. Andrew cannot celebrate with his child.", "Calendar", "MCL 722.23(a) — love/affection/emotional ties"),
        ("2025-11-26", "HEARING", "Hearing on 11/26/2025 — Day 120 of separation.", "Transcript", "Continued delay"),
        ("2025-11-27", "THANKSGIVING", f"Day {(datetime(2025,11,27)-start).days} — Thanksgiving. Andrew cannot share a meal with his son.", "Calendar", "MCL 722.23(f) — emotional harm"),
        ("2025-12-25", "CHRISTMAS", f"Day {(datetime(2025,12,25)-start).days} — Christmas Day. Son opens presents without father.", "Calendar", "MCL 722.23(a)(f)(j) — devastating emotional harm"),
        ("2025-12-31", "NEW YEAR'S EVE", f"Day {(datetime(2025,12,31)-start).days} — New Year's Eve. Another year ends in separation.", "Calendar", "MCL 722.23(f)"),
        ("2026-01-01", "NEW YEAR'S DAY", f"Day {(datetime(2026,1,1)-start).days} — New Year's Day 2026. Separation continues into new year.", "Calendar", "Unreasonable duration"),
        ("2026-01-20", "MLK DAY", f"Day {(datetime(2026,1,20)-start).days} — Martin Luther King Jr. Day. No contact.", "Calendar", "MCL 722.23(f)"),
        ("2026-02-14", "VALENTINE'S DAY", f"Day {(datetime(2026,2,14)-start).days} — Valentine's Day. Father cannot tell his son he loves him in person.", "Calendar", "MCL 722.23(a) — love/affection/emotional ties"),
        ("2026-02-16", "PRESIDENTS' DAY", f"Day {(datetime(2026,2,16)-start).days} — Presidents' Day. Another school break without father.", "Calendar", "MCL 722.23(f)"),
    ]

    # Add current date milestone
    milestones.append((
        today.strftime('%Y-%m-%d'),
        "CURRENT STATUS",
        f"Day {days_separated} — Father-son separation continues. No parenting time. No phone calls. No contact whatsoever.",
        "Calendar/Record",
        "14th Amendment Due Process — fundamental parental rights"
    ))

    # Developmental milestones for a child aged ~2.5 to ~3.5 (DOB Nov 9, 2022)
    dev_milestones = [
        ("2025-08-15", "DEVELOPMENTAL", f"Day {(datetime(2025,8,15)-start).days} — Age ~2yr 9mo: Child developing complex sentences, imaginative play. Father absent for critical language development window.", "Child Development Research", "MCL 722.23(a)(b)(d)"),
        ("2025-10-01", "DEVELOPMENTAL", f"Day {(datetime(2025,10,1)-start).days} — Age ~2yr 11mo: Child approaching 3rd birthday. Developing sense of self, family identity. No father figure present.", "Child Development Research", "MCL 722.23(a)(b)(c)(d)"),
        ("2025-12-01", "DEVELOPMENTAL", f"Day {(datetime(2025,12,1)-start).days} — Age 3yr 1mo: Preschool socialization period. Child may be told father 'chose' to leave. Alienation risk critical.", "Child Development Research", "MCL 722.23(j) — Factor J"),
        ("2026-02-01", "DEVELOPMENTAL", f"Day {(datetime(2026,2,1)-start).days} — Age 3yr 3mo: Children this age form lasting memories. Every day without father creates permanent psychological gap.", "Child Development Research", "MCL 722.23(a)(b)(f) — permanent harm"),
    ]

    # Query DB for any separation-related evidence
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, speaker, legal_significance
        FROM evidence_quotes
        WHERE quote_text LIKE '%separat%' OR quote_text LIKE '%parenting time%'
           OR quote_text LIKE '%suspend%' OR quote_text LIKE '%deny%'
           OR legal_significance LIKE '%separat%'
        ORDER BY date_ref
    """)
    db_events = []
    for r in rows:
        db_events.append({
            'date': r['date_ref'],
            'event': f"[DB EVIDENCE] {r['speaker'] or 'N/A'}: {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes/{r['evidence_category']}",
            'significance': r['legal_significance'] or '',
            'exhibit': ''
        })

    # Parenting time denial from global_chronology
    rows = safe_query(conn, """
        SELECT date, issue, shortfact240, sourcefile
        FROM global_chronology
        WHERE issue = 'exchanges/denials'
        ORDER BY date
    """)
    for r in rows:
        db_events.append({
            'date': r['date'],
            'event': f"[DENIAL] {truncate(r['shortfact240'], 200)}",
            'source': f"global_chronology/{r['sourcefile'] or 'N/A'}",
            'significance': 'Parenting time denial',
            'exhibit': ''
        })

    # Forensic analysis - parenting time denial
    rows = safe_query(conn, """
        SELECT date_iso, description, severity, mcr_violations, evidence_citations
        FROM forensic_judicial_analysis
        WHERE category = 'PARENTING_TIME_DENIAL'
        ORDER BY date_iso
        LIMIT 50
    """)
    for r in rows:
        db_events.append({
            'date': r['date_iso'],
            'event': f"[PARENTING TIME DENIAL] {truncate(r['description'], 200)}",
            'source': 'forensic_judicial_analysis',
            'significance': f"{r['mcr_violations'] or ''} (Severity: {r['severity']})",
            'exhibit': r['evidence_citations'] or ''
        })

    filepath = os.path.join(OUTPUT_DIR, "FATHER_SON_SEPARATION_TIMELINE.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "FATHER-SON SEPARATION TIMELINE",
            f"211+ Days of Forced Separation — {days_separated} Days as of {today.strftime('%B %d, %Y')}",
            "Pigors v. Watson — 2024-001507-DC | 14th Circuit Court"
        )

        f.write("## ⚠️ CRITICAL: Constitutional Rights Violation in Progress\n\n")
        f.write(f"**{days_separated} CONSECUTIVE DAYS** without any father-son contact.\n\n")
        f.write("- **Last Contact:** July 29, 2025\n")
        f.write(f"- **Days Separated:** {days_separated}\n")
        f.write(f"- **Child's Age at Separation:** 2 years, 8 months\n")
        f.write(f"- **Child's Current Age:** {(today - datetime(2022, 11, 9)).days // 365} years, {((today - datetime(2022, 11, 9)).days % 365) // 30} months\n")
        f.write("- **Hearings Without Restoration:** Multiple\n")
        f.write("- **Best Interest Analysis Conducted:** NONE\n")
        f.write("- **MCL 722.27a(9) Remedies Applied:** NONE\n\n")
        f.write("### Constitutional Framework\n\n")
        f.write("- **14th Amendment Due Process:** Fundamental right to parent (Troxel v. Granville, 530 U.S. 57 (2000))\n")
        f.write("- **MCL 722.27(1)(c):** Change must be supported by clear and convincing evidence when ECE exists\n")
        f.write("- **MCL 722.23(a)-(l):** Mandatory best interest analysis — NEVER conducted\n")
        f.write("- **MCL 722.27a(9):** Mandatory remedies for parenting time denial — NEVER applied\n\n")
        f.write("---\n\n")

        # Section 1: Key events and milestones
        f.write("## Section 1: Key Events & Missed Milestones\n\n")
        write_table_header(f)
        for i, (date, label, desc, source, sig) in enumerate(milestones, 1):
            write_row(f, i, date, f"**{label}** — {desc}", source, sig, '')

        f.write("\n\n## Section 2: Developmental Milestones Missed\n\n")
        f.write("*Child development research establishes that ages 2.5-3.5 are critical for:\n")
        f.write("language development, emotional bonding, family identity formation, and secure attachment.*\n\n")
        write_table_header(f)
        for i, (date, label, desc, source, sig) in enumerate(dev_milestones, 1):
            write_row(f, i, date, f"**{label}** — {desc}", source, sig, '')

        # Section 3: DB evidence
        f.write("\n\n## Section 3: Database Evidence of Separation & Denial\n\n")
        write_table_header(f)
        for i, ev in enumerate(db_events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

        # Closing
        f.write(f"\n\n---\n\n## Impact Statement\n\n")
        f.write(f"Every day that passes is a day that **cannot be recovered**. After {days_separated} days:\n\n")
        f.write("1. The child's memory of his father is fading\n")
        f.write("2. The bond that existed is being systematically destroyed\n")
        f.write("3. The child is being conditioned to accept father's absence as normal\n")
        f.write("4. Reintegration becomes exponentially more difficult with each passing day\n")
        f.write("5. The psychological harm to both father and child may be irreversible\n\n")
        f.write("**This is not a custody dispute. This is the erasure of a parent.**\n")

    total = len(milestones) + len(dev_milestones) + len(db_events)
    print(f"  -> {filepath} ({total} events)")
    return total


# ============================================================
# TIMELINE 4: PARENTAL ALIENATION PATTERN
# ============================================================
def build_alienation_timeline(conn):
    print("Building PARENTAL_ALIENATION_PATTERN.md...")
    events = []

    # 1. Parental alienation evidence table
    rows = safe_query(conn, """
        SELECT event_date, description, evidence_source, mcl_factor, severity
        FROM parental_alienation_evidence
        ORDER BY event_date
    """)
    for r in rows:
        events.append({
            'date': r['event_date'],
            'event': f"[ALIENATION] {r['description']}",
            'source': r['evidence_source'] or '',
            'significance': f"{r['mcl_factor']} (Severity: {r['severity']})",
            'exhibit': ''
        })

    # 2. Evidence quotes - alienation related
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, speaker, legal_significance, document_id, page_number
        FROM evidence_quotes
        WHERE evidence_category LIKE '%alienat%'
           OR quote_text LIKE '%alienat%'
           OR quote_text LIKE '%withhold%'
           OR quote_text LIKE '%Factor J%'
           OR quote_text LIKE '%722.23(j)%'
           OR legal_significance LIKE '%alienat%'
        ORDER BY date_ref
    """)
    for r in rows:
        events.append({
            'date': r['date_ref'],
            'event': f"[EVIDENCE] {r['speaker'] or 'N/A'}: {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes/{r['evidence_category']} (doc:{r['document_id']})",
            'significance': r['legal_significance'] or '',
            'exhibit': f"Doc {r['document_id']}, p.{r['page_number']}"
        })

    # 3. Alienation tactics catalog
    rows = safe_query(conn, """
        SELECT tactic, description FROM alienation_tactics ORDER BY rowid
    """)
    tactics_list = [(r['tactic'], r['description']) for r in rows]

    # 4. Forensic analysis - alienation categories
    rows = safe_query(conn, """
        SELECT date_iso, description, severity, evidence_citations, mcr_violations, source_table
        FROM forensic_judicial_analysis
        WHERE category IN ('ALIENATION_ENABLEMENT', 'ALIENATION_TACTIC', 'PARENTING_TIME_DENIAL')
        ORDER BY date_iso
        LIMIT 150
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[FORENSIC] {truncate(r['description'], 200)}",
            'source': f"forensic_judicial_analysis/{r['source_table']}",
            'significance': f"{r['mcr_violations'] or ''} ({r['severity']})",
            'exhibit': r['evidence_citations'] or ''
        })

    # 5. Chronological misconduct - alienation related
    rows = safe_query(conn, """
        SELECT date, issue FROM chronological_misconduct
        WHERE issue LIKE '%alienat%' OR issue LIKE '%Factor J%'
           OR issue LIKE '%withhold%' OR issue LIKE '%deny%'
           OR issue LIKE '%parenting time%' OR issue LIKE '%relationship%'
        ORDER BY date
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': truncate(r['issue'], 250),
            'source': 'chronological_misconduct',
            'significance': 'MCL 722.23(j) pattern',
            'exhibit': ''
        })

    # 6. Global chronology - exchanges/denials
    rows = safe_query(conn, """
        SELECT date, shortfact240, sourcefile
        FROM global_chronology
        WHERE issue = 'exchanges/denials'
           OR shortfact240 LIKE '%alienat%'
           OR shortfact240 LIKE '%withhold%'
           OR shortfact240 LIKE '%refuse%'
        ORDER BY date
        LIMIT 100
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': f"[EXCHANGE/DENIAL] {truncate(r['shortfact240'], 200)}",
            'source': f"global_chronology/{r['sourcefile'] or 'N/A'}",
            'significance': 'Parenting time interference pattern',
            'exhibit': ''
        })

    events = dedupe_and_sort(events)

    filepath = os.path.join(OUTPUT_DIR, "PARENTAL_ALIENATION_PATTERN.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "PARENTAL ALIENATION PATTERN ANALYSIS",
            "Systematic Alienation by Watson — March 26, 2024 to Present",
            "Pigors v. Watson — 2024-001507-DC | MCL 722.23(j)"
        )

        f.write("## Legal Framework: Factor J Analysis\n\n")
        f.write("**MCL 722.23(j):** *The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent.*\n\n")
        f.write("This timeline documents a **systematic pattern** of parental alienation by Watson, enabled by judicial inaction, resulting in complete severance of the father-child bond.\n\n")
        f.write("### Pattern Summary\n\n")
        f.write("1. **Phase 1 (Mar 2024):** Onset — withholding begins under guise of 'safety'\n")
        f.write("2. **Phase 2 (2024):** Escalation — PPO weaponized to restrict all contact\n")
        f.write("3. **Phase 3 (Aug 2025):** Ex parte total suspension — zero contact ordered\n")
        f.write("4. **Phase 4 (Current):** 211+ days complete separation — bond destruction\n\n")

        f.write("---\n\n")
        f.write("## Identified Alienation Tactics\n\n")
        f.write("| # | Tactic | Description |\n")
        f.write("|---|--------|-------------|\n")
        for i, (tactic, desc) in enumerate(tactics_list[:30], 1):
            f.write(f"| {i} | {escape_pipe(tactic)} | {escape_pipe(truncate(desc, 200))} |\n")

        f.write(f"\n*Total tactics identified: {len(tactics_list)}*\n\n")

        f.write("---\n\n")
        f.write("## Chronological Alienation Evidence\n\n")
        write_table_header(f)
        for i, ev in enumerate(events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

    print(f"  -> {filepath} ({len(events)} events, {len(tactics_list)} tactics)")
    return len(events)


# ============================================================
# TIMELINE 5: JUDICIAL VIOLATIONS TIMELINE
# ============================================================
def build_judicial_violations_timeline(conn):
    print("Building JUDICIAL_VIOLATIONS_TIMELINE.md...")
    events = []

    # 1. Judicial violations table
    rows = safe_query(conn, """
        SELECT violation_id, judge_name, canon_number, canon_text, violation_description,
               evidence_refs, severity, jtc_exhibit_id
        FROM judicial_violations
        ORDER BY violation_id
    """)
    for r in rows:
        events.append({
            'date': '',
            'event': f"[{r['canon_number']}] {r['violation_description']}",
            'source': f"judicial_violations ({r['violation_id']})",
            'significance': f"{r['canon_text'] or ''} — {r['severity']}",
            'exhibit': r['jtc_exhibit_id'] or ''
        })

    # 2. Auth benchbook violations
    rows = safe_query(conn, """
        SELECT rule, explanation, matching_text, judge, severity, source_file
        FROM auth_benchbook_violations
        WHERE judge LIKE '%McNeill%' OR judge IS NULL
        ORDER BY severity DESC
        LIMIT 200
    """)
    for r in rows:
        events.append({
            'date': '',
            'event': f"[BENCHBOOK] {r['rule']}: {truncate(r['explanation'], 200)}",
            'source': f"auth_benchbook_violations ({r['source_file'] or 'N/A'})",
            'significance': f"Severity: {r['severity']}",
            'exhibit': truncate(r['matching_text'], 80)
        })

    # 3. Forensic judicial analysis - violations
    rows = safe_query(conn, """
        SELECT date_iso, description, category, severity, evidence_citations, mcr_violations, source_table
        FROM forensic_judicial_analysis
        WHERE category IN (
            'MCJC_CANON_VIOLATION', 'MCR_2003_DISQUALIFICATION', 'DUE_PROCESS_VIOLATION',
            'EX_PARTE_VIOLATION', 'PROCEDURAL_MISCONDUCT', 'BIAS_INDICATOR',
            'CREDIBILITY_FAILURE', 'JUDICIAL_ACTION'
        )
        ORDER BY category, date_iso
        LIMIT 300
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[{r['category']}] {truncate(r['description'], 200)}",
            'source': f"forensic_judicial_analysis/{r['source_table']}",
            'significance': f"{r['mcr_violations'] or ''} ({r['severity']})",
            'exhibit': r['evidence_citations'] or ''
        })

    # 4. Chronological misconduct
    rows = safe_query(conn, """
        SELECT date, issue FROM chronological_misconduct
        WHERE issue LIKE '%judge%' OR issue LIKE '%court%' OR issue LIKE '%McNeill%'
           OR issue LIKE '%canon%' OR issue LIKE '%MCR%' OR issue LIKE '%due process%'
           OR issue LIKE '%ex parte%' OR issue LIKE '%bias%'
        ORDER BY date
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': truncate(r['issue'], 250),
            'source': 'chronological_misconduct',
            'significance': 'Judicial misconduct pattern',
            'exhibit': ''
        })

    # 5. Evidence quotes from COURT speaker
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, legal_significance, document_id, page_number
        FROM evidence_quotes
        WHERE speaker = 'COURT'
        ORDER BY date_ref
    """)
    for r in rows:
        events.append({
            'date': r['date_ref'],
            'event': f"[COURT STATEMENT] {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes/{r['evidence_category']} (doc:{r['document_id']})",
            'significance': r['legal_significance'] or '',
            'exhibit': f"Doc {r['document_id']}, p.{r['page_number']}"
        })

    # 6. Global harms/violations
    rows = safe_query(conn, """
        SELECT harmsviolations_text, sourcefile, ts_local
        FROM global_harms_violations
        WHERE harmsviolations_text LIKE '%judge%' OR harmsviolations_text LIKE '%court%'
           OR harmsviolations_text LIKE '%McNeill%' OR harmsviolations_text LIKE '%canon%'
        ORDER BY ts_local
        LIMIT 100
    """)
    for r in rows:
        events.append({
            'date': '',
            'event': f"[HARM/VIOLATION] {truncate(r['harmsviolations_text'], 200)}",
            'source': f"global_harms_violations/{r['sourcefile'] or 'N/A'}",
            'significance': 'Judicial harm documented',
            'exhibit': ''
        })

    events = dedupe_and_sort(events)

    # Categorize violations for summary
    categories = defaultdict(int)
    for ev in events:
        for cat in ['CANON', 'MCR_2003', 'DUE_PROCESS', 'EX_PARTE', 'PROCEDURAL', 'BIAS', 'BENCHBOOK']:
            if cat in ev['event']:
                categories[cat] += 1
                break
        else:
            categories['OTHER'] += 1

    filepath = os.path.join(OUTPUT_DIR, "JUDICIAL_VIOLATIONS_TIMELINE.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "JUDICIAL VIOLATIONS TIMELINE",
            "Hon. Jenny L. McNeill — 14th Circuit Court, Muskegon County",
            "Cases: 2024-001507-DC, 2023-5907-PP | JTC Complaint Support"
        )

        f.write("## Violation Categories Summary\n\n")
        f.write("| Category | Count | Authority |\n")
        f.write("|----------|-------|----------|\n")
        cat_auth = {
            'CANON': 'MI Code of Judicial Conduct',
            'MCR_2003': 'MCR 2.003(C)(1)(b) — Disqualification',
            'DUE_PROCESS': '14th Amendment / MCL 722.27',
            'EX_PARTE': 'Canon 3(B)(7) / MCR 2.003',
            'PROCEDURAL': 'MCR various',
            'BIAS': 'MCR 2.003(C)(1)(b)',
            'BENCHBOOK': 'Michigan Judicial Benchbook',
            'OTHER': 'Multiple authorities'
        }
        for cat, cnt in sorted(categories.items(), key=lambda x: -x[1]):
            f.write(f"| {cat} | {cnt} | {cat_auth.get(cat, 'Various')} |\n")
        f.write(f"\n**Total Documented Violations:** {len(events)}\n\n")

        f.write("### Key Violations Pattern\n\n")
        f.write("1. **Ex parte communications and orders** without proper notice/hearing\n")
        f.write("2. **Failure to conduct best interest analysis** under MCL 722.23\n")
        f.write("3. **Bias indicators** — pattern of one-sided rulings favoring Watson\n")
        f.write("4. **Due process violations** — parenting time suspended without evidentiary hearing\n")
        f.write("5. **Benchbook deviations** — failure to follow mandatory judicial procedures\n\n")

        f.write("---\n\n")
        f.write("## Chronological Violations\n\n")
        write_table_header(f)
        for i, ev in enumerate(events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

    print(f"  -> {filepath} ({len(events)} events)")
    return len(events)


# ============================================================
# TIMELINE 6: WATSON EMPLOYMENT CONNECTIONS
# ============================================================
def build_watson_employment_timeline(conn):
    print("Building WATSON_EMPLOYMENT_CONNECTIONS.md...")
    events = []

    # 1. Berry investigation table
    rows = safe_query(conn, """
        SELECT source, evidence_text, connection_type, strength, source_page, discovered_date
        FROM berry_investigation
        ORDER BY id
    """)
    for r in rows:
        events.append({
            'date': r['discovered_date'] or '',
            'event': f"[{r['connection_type']}] {truncate(r['evidence_text'], 250)}",
            'source': f"berry_investigation/{r['source']}",
            'significance': f"Connection strength: {r['strength']}",
            'exhibit': r['source_page'] or ''
        })

    # 2. Parental alienation evidence - employment connection
    rows = safe_query(conn, """
        SELECT event_date, description, evidence_source, mcl_factor, severity
        FROM parental_alienation_evidence
        WHERE description LIKE '%Kent%' OR description LIKE '%Prosecutor%'
           OR description LIKE '%employ%' OR description LIKE '%caseworker%'
        ORDER BY event_date
    """)
    for r in rows:
        events.append({
            'date': r['event_date'],
            'event': f"[EMPLOYMENT] {r['description']}",
            'source': r['evidence_source'] or '',
            'significance': f"{r['mcl_factor']} ({r['severity']})",
            'exhibit': ''
        })

    # 3. Evidence quotes - Watson employment, Berry, Kent County
    rows = safe_query(conn, """
        SELECT date_ref, quote_text, evidence_category, speaker, legal_significance, document_id, page_number
        FROM evidence_quotes
        WHERE quote_text LIKE '%Kent%' OR quote_text LIKE '%Prosecutor%'
           OR quote_text LIKE '%Berry%' OR quote_text LIKE '%caseworker%'
           OR quote_text LIKE '%employ%'
        ORDER BY date_ref
    """)
    for r in rows:
        events.append({
            'date': r['date_ref'],
            'event': f"[EVIDENCE] {truncate(r['quote_text'], 200)}",
            'source': f"evidence_quotes/{r['evidence_category']} (doc:{r['document_id']})",
            'significance': r['legal_significance'] or '',
            'exhibit': f"Doc {r['document_id']}, p.{r['page_number']}"
        })

    # 4. Venue bias evidence
    rows = safe_query(conn, """
        SELECT person, role, connection_to_case, bias_type, evidence_source
        FROM venue_bias_evidence
        ORDER BY id
    """)
    for r in rows:
        events.append({
            'date': '',
            'event': f"[VENUE BIAS] {r['person']} ({r['role']}): {r['connection_to_case']}",
            'source': r['evidence_source'] or 'venue_bias_evidence',
            'significance': f"Bias type: {r['bias_type']}",
            'exhibit': ''
        })

    # 5. Forensic analysis - bias indicators
    rows = safe_query(conn, """
        SELECT date_iso, description, severity, evidence_citations, mcr_violations, source_table
        FROM forensic_judicial_analysis
        WHERE category = 'BIAS_INDICATOR'
           OR description LIKE '%Kent%' OR description LIKE '%Prosecutor%'
           OR description LIKE '%Berry%' OR description LIKE '%employ%'
        ORDER BY date_iso
        LIMIT 50
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[BIAS/EMPLOYMENT] {truncate(r['description'], 200)}",
            'source': f"forensic_judicial_analysis/{r['source_table']}",
            'significance': f"{r['mcr_violations'] or ''} ({r['severity']})",
            'exhibit': r['evidence_citations'] or ''
        })

    # 6. Master timeline - employment/bias related
    rows = safe_query(conn, """
        SELECT date_iso, description, category, source_table, citations
        FROM master_timeline
        WHERE description LIKE '%Kent%' OR description LIKE '%Prosecutor%'
           OR description LIKE '%Berry%' OR description LIKE '%employ%'
           OR description LIKE '%bias%' OR description LIKE '%conflict%'
        ORDER BY date_iso
        LIMIT 50
    """)
    for r in rows:
        events.append({
            'date': r['date_iso'],
            'event': f"[{r['category'].upper()}] {truncate(r['description'], 200)}",
            'source': f"master_timeline/{r['source_table']}",
            'significance': '',
            'exhibit': r['citations'] or ''
        })

    # 7. Chronological misconduct - Berry/employment
    rows = safe_query(conn, """
        SELECT date, issue FROM chronological_misconduct
        WHERE issue LIKE '%Berry%' OR issue LIKE '%Kent%' OR issue LIKE '%Prosecutor%'
           OR issue LIKE '%employ%' OR issue LIKE '%flash drive%' OR issue LIKE '%voicemail%'
        ORDER BY date
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': truncate(r['issue'], 250),
            'source': 'chronological_misconduct',
            'significance': 'Employment connection evidence',
            'exhibit': ''
        })

    # 8. Global chronology - bias/muting
    rows = safe_query(conn, """
        SELECT date, shortfact240, sourcefile
        FROM global_chronology
        WHERE issue = 'bias/muting'
           OR shortfact240 LIKE '%Berry%'
           OR shortfact240 LIKE '%Kent County%'
           OR shortfact240 LIKE '%prosecutor%'
        ORDER BY date
        LIMIT 50
    """)
    for r in rows:
        events.append({
            'date': r['date'],
            'event': f"[BIAS] {truncate(r['shortfact240'], 200)}",
            'source': f"global_chronology/{r['sourcefile'] or 'N/A'}",
            'significance': 'Bias/employment connection',
            'exhibit': ''
        })

    events = dedupe_and_sort(events)

    filepath = os.path.join(OUTPUT_DIR, "WATSON_EMPLOYMENT_CONNECTIONS.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        write_header(f,
            "WATSON EMPLOYMENT CONNECTIONS & BERRY INVESTIGATION",
            "Kent County Prosecutor's Office — Conflict of Interest Analysis",
            "Pigors v. Watson — MCR 2.003(C)(1)(b) Disqualification Basis"
        )

        f.write("## Key Finding\n\n")
        f.write("**Emily Watson (fka Pigors) was employed for 9 years at the Kent County Prosecutor's Office, Family Court Division, as a caseworker.** This employment creates:\n\n")
        f.write("1. **Insider knowledge** of family court procedures, judicial preferences, and system manipulation\n")
        f.write("2. **Professional relationships** with court officers, FOC staff, and judicial personnel\n")
        f.write("3. **Conflict of interest** — Watson's connections give her systemic advantage\n")
        f.write("4. **Ron Berry connection** — Berry voicemail submitted as ex parte evidence, pre-listened in chambers\n\n")

        f.write("### Berry Investigation Summary\n\n")
        f.write("Ron Berry's voicemail was:\n")
        f.write("- Listed as item #6 in LINE-BY-LINE OBJECTION to ex parte evidence\n")
        f.write("- Pre-listened in chambers (Canon 3(B)(5) violation)\n")
        f.write("- Part of the appellate record (COA 366810)\n")
        f.write("- Connected to Watson family network (P_RON alongside P_EMILY, P_LINCOLN, P_LORI, P_ALBERT)\n\n")

        f.write("### Legal Significance\n\n")
        f.write("- **MCR 2.003(C)(1)(b):** Judge disqualification for bias when party has prosecutorial connections\n")
        f.write("- **Canon 3(B)(5):** Prohibition on ex parte communications\n")
        f.write("- **Canon 3(B)(7):** Judge shall not initiate or consider ex parte communications\n")
        f.write("- **14th Amendment:** Due process requires impartial tribunal\n\n")

        f.write("---\n\n")
        f.write("## Connection Map\n\n")
        f.write("```\n")
        f.write("Emily Watson (Defendant)\n")
        f.write("  ├── 9yr Employment: Kent County Prosecutor's Office (Family Court Division)\n")
        f.write("  ├── Family: Lori Watson, Albert Watson, Cody Watson\n")
        f.write("  ├── Associate: Ron Berry\n")
        f.write("  │     └── Voicemail submitted as ex parte evidence\n")
        f.write("  │     └── Pre-listened in chambers (Canon 3(B)(5) violation)\n")
        f.write("  │     └── Part of appellate record COA 366810\n")
        f.write("  └── Austin Muratori (undisclosed child support income)\n")
        f.write("```\n\n")

        f.write("---\n\n")
        f.write("## Evidence Trail\n\n")
        write_table_header(f)
        for i, ev in enumerate(events, 1):
            write_row(f, i, ev['date'], ev['event'], ev['source'], ev['significance'], ev['exhibit'])

    print(f"  -> {filepath} ({len(events)} events)")
    return len(events)


def dedupe_and_sort(events):
    """Deduplicate events by event text and sort by date."""
    seen = set()
    unique = []
    for ev in events:
        # Create a dedup key from first 100 chars of event
        key = ev['event'][:100].strip()
        if key not in seen:
            seen.add(key)
            ev['_sort_date'] = normalize_date(ev.get('date', '')) or '9999-99-99'
            unique.append(ev)
    unique.sort(key=lambda x: x['_sort_date'])
    return unique


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("LitigationOS Timeline Builder v1.0")
    print(f"Database: {DB_PATH}")
    print(f"Output:   {OUTPUT_DIR}")
    print("=" * 60)

    conn = get_conn()

    totals = {}
    totals['custody'] = build_custody_timeline(conn)
    totals['ppo'] = build_ppo_timeline(conn)
    totals['separation'] = build_separation_timeline(conn)
    totals['alienation'] = build_alienation_timeline(conn)
    totals['judicial'] = build_judicial_violations_timeline(conn)
    totals['employment'] = build_watson_employment_timeline(conn)

    conn.close()

    print("\n" + "=" * 60)
    print("TIMELINE BUILD COMPLETE")
    print("=" * 60)
    total_events = sum(totals.values())
    for name, count in totals.items():
        print(f"  {name}: {count} events")
    print(f"\n  TOTAL: {total_events} events across 6 timelines")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
