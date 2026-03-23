#!/usr/bin/env python3
"""
Tool #271 — Exhibit Binder Builder
=====================================
Builds organized exhibit binders for each filing (F1-F10) with:
  - Bates numbering (PIGORS-NNNNN)
  - Exhibit indexes (table of contents)
  - Exhibit cover pages
  - DB tracking in bates_assignments table

Output: GENERATED_FILINGS/exhibits/<filing_id>/
"""
import sys, os, json, sqlite3, textwrap
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'GENERATED_FILINGS')
EXHIBITS_DIR = os.path.join(OUTPUT_DIR, 'exhibits')


def s(v):
    return (v or "").lower()


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception:
        return []


# ── Verified party information ────────────────────────────────────────────
PLAINTIFF_NAME = 'Andrew James Pigors'
CASE_CUSTODY = '2024-001507-DC'
CASE_PPO = '2023-5907-PP'
CASE_HOUSING = '2025-002760-CZ'

# ── Filing definitions with exhibit categories ────────────────────────────
FILINGS = {
    'F1': {
        'title': 'Custody — Enforcement of Parenting Time',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("PPO petition and related filings",
             "SELECT quote_text, evidence_category, source_type FROM evidence_quotes WHERE evidence_category LIKE '%ppo%' OR quote_text LIKE '%protection%order%' LIMIT 10",
             None),
            ("Ex parte orders",
             "SELECT quote_text, evidence_category FROM evidence_quotes WHERE quote_text LIKE '%ex parte%' LIMIT 10",
             None),
            ("Parenting time withholding",
             "SELECT description, evidence_source, date FROM actor_violations WHERE description LIKE '%parenting%' OR description LIKE '%withhold%' OR description LIKE '%visitation%' LIMIT 15",
             None),
            ("Best interest factors",
             "SELECT claim_description, evidence_text FROM claim_evidence_links WHERE vehicle_name LIKE '%F1%' OR claim_type LIKE '%custody%' LIMIT 10",
             None),
        ],
    },
    'F2': {
        'title': 'PPO — Motion to Modify/Terminate',
        'case': CASE_PPO,
        'evidence_queries': [
            ("Original PPO and allegations",
             "SELECT quote_text, evidence_category FROM evidence_quotes WHERE evidence_category LIKE '%ppo%' OR quote_text LIKE '%protection order%' LIMIT 10",
             None),
            ("False allegations evidence",
             "SELECT description, evidence_source FROM actor_violations WHERE description LIKE '%false%' OR description LIKE '%fabricat%' LIMIT 10",
             None),
            ("Threats and intimidation",
             "SELECT description, evidence_source, severity FROM actor_violations WHERE description LIKE '%threat%' OR description LIKE '%intimidat%' LIMIT 10",
             None),
        ],
    },
    'F3': {
        'title': 'Disqualification of Judge McNeill',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Canon violations",
             "SELECT description, evidence_source, severity FROM actor_violations WHERE description LIKE '%canon%' OR description LIKE '%bias%' OR description LIKE '%judicial%' LIMIT 15",
             None),
            ("Ex parte communications",
             "SELECT quote_text, evidence_category FROM evidence_quotes WHERE quote_text LIKE '%ex parte%' OR evidence_category LIKE '%judicial%' LIMIT 10",
             None),
            ("Muting / silencing incidents",
             "SELECT description, evidence_source FROM actor_violations WHERE description LIKE '%mute%' OR description LIKE '%silence%' OR description LIKE '%denied%speaking%' LIMIT 10",
             None),
        ],
    },
    'F4': {
        'title': '42 USC §1983 — Federal Civil Rights',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Due process violations",
             "SELECT description, evidence_source, severity FROM actor_violations WHERE description LIKE '%due process%' OR description LIKE '%constitutional%' OR violation_type LIKE '%due process%' LIMIT 15",
             None),
            ("Parenting time denial (209+ days)",
             "SELECT description, date, evidence_source FROM actor_violations WHERE description LIKE '%parenting%' OR description LIKE '%denied%' ORDER BY date LIMIT 15",
             None),
        ],
    },
    'F5': {
        'title': 'MSC — Application for Superintending Control',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Court rule violations",
             "SELECT description, evidence_source FROM actor_violations WHERE description LIKE '%MCR%' OR description LIKE '%court rule%' LIMIT 15",
             None),
        ],
    },
    'F6': {
        'title': 'JTC — Judicial Tenure Commission Complaint',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Judicial misconduct",
             "SELECT description, evidence_source, severity FROM actor_violations WHERE actor LIKE '%McNeill%' OR actor LIKE '%judge%' LIMIT 20",
             None),
        ],
    },
    'F7': {
        'title': 'COA — Court of Appeals',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Docket entries challenged",
             "SELECT title, event_date_iso, summary FROM docket_events WHERE case_id LIKE '%1507%' OR case_id LIKE '%custody%' ORDER BY event_date_iso LIMIT 20",
             None),
        ],
    },
    'F8': {
        'title': 'Contempt — Enforcement of Court Orders',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Emily's court order violations",
             "SELECT description, evidence_source, date, severity FROM actor_violations WHERE actor LIKE '%Watson%' OR actor LIKE '%Emily%' LIMIT 15",
             None),
        ],
    },
    'F9': {
        'title': 'Housing — Shady Oaks Conditions',
        'case': CASE_HOUSING,
        'evidence_queries': [
            ("Housing conditions / habitability",
             "SELECT quote_text, evidence_category FROM evidence_quotes WHERE quote_text LIKE '%shady%' OR quote_text LIKE '%sewer%' OR quote_text LIKE '%housing%' OR quote_text LIKE '%habitab%' LIMIT 15",
             None),
        ],
    },
    'F10': {
        'title': 'Criminal Evidence Referral',
        'case': CASE_CUSTODY,
        'evidence_queries': [
            ("Criminal evidence scanner results",
             "SELECT crime_name, perpetrator, evidence_count, satisfaction_pct, max_penalty FROM criminal_evidence_scan WHERE prosecutable = 1 ORDER BY satisfaction_pct DESC LIMIT 20",
             None),
            ("Perjury / conspiracy evidence",
             "SELECT conspirator, act_type, description, severity FROM watson_family_conspiracy ORDER BY severity DESC LIMIT 15",
             None),
        ],
    },
}


def _bates(n):
    """Format Bates number: PIGORS-00001."""
    return f"PIGORS-{n:05d}"


def _cover_page(exhibit_letter, description, bates_start, bates_end, page_count, source, case_num):
    return textwrap.dedent(f"""\
    +{'=' * 58}+
    |{'EXHIBIT ' + exhibit_letter:^58}|
    |{' ' * 58}|
    |  {description:<56}|
    |{' ' * 58}|
    |  Bates: {bates_start} through {bates_end:<40}|
    |  Pages: {page_count:<49}|
    |  Source: {source[:48]:<48}  |
    |{' ' * 58}|
    |  Pigors v. Watson{' ' * 40}|
    |  Case No. {case_num:<47}|
    +{'=' * 58}+
    """)


def build_binder(conn, filing_id, filing_info, bates_counter):
    """Build one exhibit binder. Returns (exhibits_list, new_bates_counter)."""
    filing_dir = os.path.join(EXHIBITS_DIR, filing_id)
    os.makedirs(filing_dir, exist_ok=True)

    exhibits = []
    letters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    letter_idx = 0

    for (desc, sql, params) in filing_info['evidence_queries']:
        rows = safe_query(conn, sql, params or ())
        if not rows:
            # Still create a placeholder exhibit
            rows = []

        page_count = max(len(rows), 1)
        bates_start = _bates(bates_counter)
        bates_end = _bates(bates_counter + page_count - 1)
        letter = letters[letter_idx] if letter_idx < 26 else f"A{letter_idx - 25}"

        # Determine evidence type from first row if available
        evidence_type = 'documentary'
        source_file = 'litigation_context.db'
        if rows:
            row_dict = dict(rows[0])
            for k in ('evidence_source', 'source_file', 'source_type'):
                if k in row_dict and row_dict[k]:
                    source_file = str(row_dict[k])[:120]
                    break
            for k in ('evidence_category', 'evidence_type', 'violation_type', 'act_type'):
                if k in row_dict and row_dict[k]:
                    evidence_type = str(row_dict[k])[:60]
                    break

        exhibit = {
            'letter': letter,
            'description': desc,
            'bates_start': bates_start,
            'bates_end': bates_end,
            'page_count': page_count,
            'source_file': source_file,
            'evidence_type': evidence_type,
            'row_count': len(rows),
        }
        exhibits.append(exhibit)

        # Write cover page
        cover = _cover_page(letter, desc, bates_start, bates_end,
                            page_count, source_file, filing_info['case'])
        cover_path = os.path.join(filing_dir, f"EXHIBIT_{letter}_COVER.txt")
        with open(cover_path, 'w', encoding='utf-8') as f:
            f.write(cover)

        # Write exhibit content summary
        content_path = os.path.join(filing_dir, f"EXHIBIT_{letter}_CONTENT.txt")
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(f"EXHIBIT {letter} — {desc}\n")
            f.write(f"Bates: {bates_start} through {bates_end}\n")
            f.write(f"Filing: {filing_id} — {filing_info['title']}\n")
            f.write(f"Case: {filing_info['case']}\n")
            f.write("=" * 60 + "\n\n")
            if rows:
                for i, row in enumerate(rows, 1):
                    f.write(f"--- Item {i} (Bates: {_bates(bates_counter + i - 1)}) ---\n")
                    row_dict = dict(row)
                    for k, v in row_dict.items():
                        if v is not None:
                            f.write(f"  {k}: {str(v)[:500]}\n")
                    f.write("\n")
            else:
                f.write("[No matching evidence found in DB — attach source documents manually]\n")

        # DB insert
        conn.execute("""\
            INSERT INTO bates_assignments
            (filing_id, exhibit_letter, description, bates_start, bates_end,
             page_count, source_file, evidence_type, generated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (filing_id, letter, desc, bates_start, bates_end,
             page_count, source_file, evidence_type,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        bates_counter += page_count
        letter_idx += 1

    # Write exhibit index
    index_path = os.path.join(filing_dir, "EXHIBIT_INDEX.txt")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"EXHIBIT INDEX — {filing_id}: {filing_info['title']}\n")
        f.write(f"Case No. {filing_info['case']}\n")
        f.write(f"Pigors v. Watson\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"{'Exhibit':<10}{'Description':<45}{'Bates Range':<25}{'Pages':>5}\n")
        f.write(f"{'-' * 10}{'-' * 45}{'-' * 25}{'-' * 5}\n")
        for ex in exhibits:
            bates_range = f"{ex['bates_start']}-{ex['bates_end']}"
            f.write(f"{ex['letter']:<10}{ex['description'][:44]:<45}{bates_range:<25}{ex['page_count']:>5}\n")
        f.write(f"\n{'=' * 80}\n")
        total_pages = sum(e['page_count'] for e in exhibits)
        f.write(f"Total Exhibits: {len(exhibits)}    Total Pages: {total_pages}\n")
        f.write(f"Bates Range: {exhibits[0]['bates_start']} through {exhibits[-1]['bates_end']}\n")

    return exhibits, bates_counter


def main():
    print("=" * 60)
    print("Tool #271 — Exhibit Binder Builder")
    print("=" * 60)

    os.makedirs(EXHIBITS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row

    conn.execute("""\
        CREATE TABLE IF NOT EXISTS bates_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT,
            exhibit_letter TEXT,
            description TEXT,
            bates_start TEXT,
            bates_end TEXT,
            page_count INTEGER,
            source_file TEXT,
            evidence_type TEXT,
            generated_date TEXT
        )""")
    conn.commit()

    bates_counter = 1
    all_results = {}
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for filing_id, filing_info in FILINGS.items():
        print(f"\n  Building binder: {filing_id} — {filing_info['title']}")
        exhibits, bates_counter = build_binder(conn, filing_id, filing_info, bates_counter)
        all_results[filing_id] = {
            'title': filing_info['title'],
            'case': filing_info['case'],
            'exhibits': exhibits,
            'exhibit_count': len(exhibits),
            'total_pages': sum(e['page_count'] for e in exhibits),
        }
        print(f"    Exhibits: {len(exhibits)}  |  Pages: {all_results[filing_id]['total_pages']}  |  Bates through {_bates(bates_counter - 1)}")

    conn.commit()

    # ── Master Bates Index ────────────────────────────────────────────
    master_path = os.path.join(EXHIBITS_DIR, "MASTER_BATES_INDEX.txt")
    with open(master_path, 'w', encoding='utf-8') as f:
        f.write("MASTER BATES INDEX — Pigors v. Watson\n")
        f.write(f"Generated: {now}\n")
        f.write("=" * 90 + "\n\n")
        f.write(f"{'Filing':<8}{'Exhibit':<8}{'Description':<40}{'Bates Range':<25}{'Pages':>5}\n")
        f.write("-" * 90 + "\n")
        for fid, fdata in all_results.items():
            for ex in fdata['exhibits']:
                br = f"{ex['bates_start']}-{ex['bates_end']}"
                f.write(f"{fid:<8}{ex['letter']:<8}{ex['description'][:39]:<40}{br:<25}{ex['page_count']:>5}\n")
            f.write("-" * 90 + "\n")
        total_pages = sum(d['total_pages'] for d in all_results.values())
        total_exhibits = sum(d['exhibit_count'] for d in all_results.values())
        f.write(f"\nTotal Filings: {len(all_results)}  |  Total Exhibits: {total_exhibits}  |  Total Pages: {total_pages}\n")
        f.write(f"Bates Range: PIGORS-00001 through {_bates(bates_counter - 1)}\n")

    # ── Reports ───────────────────────────────────────────────────────
    report_json = {
        'tool': 'exhibit_binder_builder',
        'tool_number': 271,
        'generated': now,
        'exhibits_dir': EXHIBITS_DIR,
        'filings': all_results,
        'total_filings': len(all_results),
        'total_exhibits': sum(d['exhibit_count'] for d in all_results.values()),
        'total_pages': sum(d['total_pages'] for d in all_results.values()),
        'final_bates': _bates(bates_counter - 1),
    }
    json_path = os.path.join(REPORTS_DIR, 'exhibit_binder_builder.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, indent=2)

    md_lines = [
        "# Exhibit Binder Builder Report",
        f"**Generated:** {now}",
        f"**Exhibits Directory:** `{EXHIBITS_DIR}`",
        f"**Bates Range:** PIGORS-00001 through {_bates(bates_counter - 1)}",
        "",
        "## Filing Summary",
        "",
        "| Filing | Title | Case | Exhibits | Pages |",
        "|--------|-------|------|----------|-------|",
    ]
    for fid, fdata in all_results.items():
        md_lines.append(
            f"| {fid} | {fdata['title'][:40]} | {fdata['case']} "
            f"| {fdata['exhibit_count']} | {fdata['total_pages']} |")
    total_ex = sum(d['exhibit_count'] for d in all_results.values())
    total_pg = sum(d['total_pages'] for d in all_results.values())
    md_lines += [
        f"| **TOTAL** | | | **{total_ex}** | **{total_pg}** |",
        "",
        "## Notes",
        "- Bates numbers are sequential across ALL filings (PIGORS-NNNNN).",
        "- Each filing subdirectory contains: EXHIBIT_INDEX.txt, cover pages, content summaries.",
        "- Attach actual source documents behind each cover page when assembling physical binders.",
        "- Evidence counts are based on DB query results — verify against source files.",
    ]
    md_path = os.path.join(REPORTS_DIR, 'EXHIBIT_BINDER_BUILDER.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    conn.close()

    print(f"\n  Total exhibits: {total_ex} across {len(all_results)} filings")
    print(f"  Total pages: {total_pg}")
    print(f"  Final Bates: {_bates(bates_counter - 1)}")
    print(f"  Master index: {master_path}")
    print(f"  Reports: {json_path}")
    print(f"           {md_path}")
    print("  Done.")


if __name__ == '__main__':
    main()
