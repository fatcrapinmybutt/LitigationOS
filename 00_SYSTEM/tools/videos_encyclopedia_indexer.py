#!/usr/bin/env python3
"""Tool #265: VIDEOS ENCYCLOPEDIA INDEXER
Reads the markdown encyclopedias in the Videos folder and indexes their
sections into `encyclopedia_sections` table for section-level search.
"""
import sys, os, json, sqlite3, re
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []


# ── Lane detection from section content ─────────────────────────────
def detect_lane(text):
    t = s(text)
    lanes = []
    if any(k in t for k in ['custody', 'parenting', 'child', 'ldw', '001507']):
        lanes.append('A')
    if any(k in t for k in ['shady oaks', 'housing', 'eviction', '002760', 'sewer']):
        lanes.append('B')
    if any(k in t for k in ['ppo', 'protection', '5907', 'contempt']):
        lanes.append('D')
    if any(k in t for k in ['mcneill', 'judicial', 'misconduct', 'jtc', 'canon', 'bias']):
        lanes.append('E')
    if any(k in t for k in ['coa', 'appeal', 'appellate', 'msc', 'superintending']):
        lanes.append('F')
    if any(k in t for k in ['convergence', 'multi-lane', 'cross']):
        lanes.append('C')
    return ','.join(lanes) if lanes else 'A'


# ── Perpetrator detection ───────────────────────────────────────────
def detect_perpetrators(text):
    t = s(text)
    perps = []
    if any(k in t for k in ['emily', 'watson']):
        perps.append('emily')
    if any(k in t for k in ['berry', 'ronald']):
        perps.append('berry')
    if any(k in t for k in ['mcneill', 'judge mcneill']):
        perps.append('mcneill')
    if any(k in t for k in ['rusco', 'foc']):
        perps.append('rusco')
    if any(k in t for k in ['barnes', 'p55406']):
        perps.append('barnes')
    if any(k in t for k in ['albert', 'cody', 'lori']):
        perps.append('watson_family')
    return ','.join(perps) if perps else ''


# ── Topic extraction ────────────────────────────────────────────────
TOPIC_PATTERNS = {
    'custody': ['custody', 'parenting time', 'visitation', 'best interest'],
    'abuse': ['abuse', 'neglect', 'harm', 'domestic violence', 'dv'],
    'alienation': ['alienation', 'gatekeeping', 'interference', 'withholding'],
    'financial': ['income', 'support', 'financial', 'tax', 'employment'],
    'housing': ['housing', 'shady oaks', 'eviction', 'sewer', 'habitability'],
    'judicial': ['judicial', 'mcneill', 'bias', 'canon', 'misconduct', 'ex parte'],
    'evidence': ['evidence', 'exhibit', 'testimony', 'deposition', 'witness'],
    'ppo': ['ppo', 'protection order', 'restraining'],
    'appeal': ['appeal', 'coa', 'msc', 'superintending'],
    'police': ['police', 'nspd', 'dispatch', 'report', 'officer'],
    'medical': ['medical', 'healthwest', 'therapy', 'mental health', 'counseling'],
    'fraud': ['fraud', 'perjury', 'false', 'fabricat', 'lie'],
    'timeline': ['timeline', 'chronolog', 'date', 'sequence'],
    'strategy': ['strategy', 'priority', 'plan', 'filing', 'next step'],
}

def detect_topics(text):
    t = s(text)
    found = []
    for topic, keywords in TOPIC_PATTERNS.items():
        if any(k in t for k in keywords):
            found.append(topic)
    return ','.join(found) if found else 'general'


# ── Date detection ──────────────────────────────────────────────────
DATE_PATTERN = re.compile(
    r'\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}/\d{1,2}/20\d{2}|'
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2})\b',
    re.IGNORECASE
)

def has_dates(text):
    return 1 if DATE_PATTERN.search(text) else 0


# ── Citation detection ──────────────────────────────────────────────
CITE_PATTERN = re.compile(
    r'\b(?:MCL|MCR|MCL §|§)\s*\d+[\.\d]*|'
    r'\b\d+\s+Mich\s+(?:App\s+)?\d+|'
    r'\b\d+\s+NW\s*(?:2d\s+)?\d+|'
    r'\bMCR\s+\d+\.\d+',
    re.IGNORECASE
)

def has_citations(text):
    return 1 if CITE_PATTERN.search(text) else 0


# ── Parse markdown sections ─────────────────────────────────────────
def parse_markdown_sections(content, source_file):
    """Split markdown by headers, return list of section dicts."""
    sections = []
    lines = content.split('\n')

    current_title = os.path.basename(source_file)
    current_level = 1
    current_lines = []
    header_pattern = re.compile(r'^(#{1,6})\s+(.*)')

    def flush_section():
        if current_lines:
            full_text = '\n'.join(current_lines).strip()
            if len(full_text) > 10:  # Skip trivially short sections
                preview = full_text[:500]
                sections.append({
                    'source_file': source_file,
                    'section_title': current_title.strip(),
                    'section_level': current_level,
                    'content_preview': preview,
                    'content_length': len(full_text),
                    'case_lane': detect_lane(current_title + ' ' + preview),
                    'topics': detect_topics(current_title + ' ' + preview),
                    'perpetrator_mentions': detect_perpetrators(current_title + ' ' + preview),
                    'has_dates': has_dates(full_text),
                    'has_citations': has_citations(full_text),
                })

    for line in lines:
        m = header_pattern.match(line)
        if m:
            flush_section()
            current_level = len(m.group(1))
            current_title = m.group(2)
            current_lines = []
        else:
            current_lines.append(line)

    flush_section()  # Don't forget last section
    return sections


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #265: VIDEOS ENCYCLOPEDIA INDEXER")
    print("=" * 70)

    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS encyclopedia_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            section_title TEXT,
            section_level INTEGER,
            content_preview TEXT,
            content_length INTEGER,
            case_lane TEXT,
            topics TEXT,
            perpetrator_mentions TEXT,
            has_dates INTEGER DEFAULT 0,
            has_citations INTEGER DEFAULT 0,
            scan_date TEXT
        )
    """)
    conn.commit()

    cols = [r[1] for r in conn.execute("PRAGMA table_info(encyclopedia_sections)").fetchall()]
    print(f"  Table columns: {cols}")

    scan_date = datetime.now().isoformat()

    # Files to index
    encyclopedia_files = [
        r"C:\Users\andre\Videos\MASTER_LITIGATION_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\MASTER_LITIGATION_ENCYCLOPEDIA_v2.md",
        r"C:\Users\andre\Videos\CHATGPT_CHRONOLOGICAL_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\SHADY_OAKS_ENCYCLOPEDIA.md",
        r"C:\Users\andre\Videos\EVIDENTIARY_NARRATIVE_MCNEILL.md",
        r"C:\Users\andre\Videos\EVIDENTIARY_NARRATIVE_SHADY_OAKS.md",
        r"C:\Users\andre\Videos\JUDICIAL_DOSSIER_MCNEILL.md",
        r"C:\Users\andre\Videos\IMPEACHMENT_PACKAGES.md",
        r"C:\Users\andre\Videos\MEGA_HARVEST_REPORT.md",
    ]

    # Clear existing scan for re-indexing
    conn.execute("DELETE FROM encyclopedia_sections")
    conn.commit()

    all_sections = []
    file_stats = {}

    for fpath in encyclopedia_files:
        fname = os.path.basename(fpath)
        print(f"\n  Processing: {fname}")

        if not os.path.exists(fpath):
            print(f"    ⚠ File not found — skipping")
            file_stats[fname] = {"status": "NOT_FOUND", "sections": 0, "total_chars": 0}
            continue

        try:
            # Try UTF-8 first, fall back to latin-1
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(fpath, 'r', encoding='latin-1') as f:
                    content = f.read()

            sections = parse_markdown_sections(content, fpath)
            all_sections.extend(sections)

            total_chars = sum(sec['content_length'] for sec in sections)
            topics_found = set()
            perps_found = set()
            for sec in sections:
                for t in sec['topics'].split(','):
                    if t:
                        topics_found.add(t)
                for p in sec['perpetrator_mentions'].split(','):
                    if p:
                        perps_found.add(p)

            with_dates = sum(1 for sec in sections if sec['has_dates'])
            with_cites = sum(1 for sec in sections if sec['has_citations'])

            file_stats[fname] = {
                "status": "OK",
                "sections": len(sections),
                "total_chars": total_chars,
                "topics": sorted(topics_found),
                "perpetrators": sorted(perps_found),
                "sections_with_dates": with_dates,
                "sections_with_citations": with_cites,
            }

            print(f"    Sections: {len(sections)}")
            print(f"    Total chars: {total_chars:,}")
            print(f"    Topics: {', '.join(sorted(topics_found))}")
            print(f"    Perpetrators: {', '.join(sorted(perps_found))}")
            print(f"    With dates: {with_dates}, With citations: {with_cites}")

        except Exception as e:
            print(f"    ✗ Error: {e}")
            file_stats[fname] = {"status": f"ERROR: {e}", "sections": 0, "total_chars": 0}

    # ── Insert all sections into DB ─────────────────────────────────
    if all_sections:
        rows = [
            (sec['source_file'], sec['section_title'], sec['section_level'],
             sec['content_preview'], sec['content_length'], sec['case_lane'],
             sec['topics'], sec['perpetrator_mentions'], sec['has_dates'],
             sec['has_citations'], scan_date)
            for sec in all_sections
        ]
        conn.executemany("""
            INSERT INTO encyclopedia_sections
            (source_file, section_title, section_level, content_preview, content_length,
             case_lane, topics, perpetrator_mentions, has_dates, has_citations, scan_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

    total_in_db = conn.execute("SELECT COUNT(*) FROM encyclopedia_sections").fetchone()[0]

    # ── Summary ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  INDEXING SUMMARY")
    print(f"  Total sections indexed: {len(all_sections)}")
    print(f"  Total in DB: {total_in_db}")
    print(f"  Files processed: {len(file_stats)}")

    files_ok = sum(1 for v in file_stats.values() if v['status'] == 'OK')
    files_missing = sum(1 for v in file_stats.values() if v['status'] == 'NOT_FOUND')
    files_error = sum(1 for v in file_stats.values() if v['status'].startswith('ERROR'))
    print(f"  Files OK: {files_ok}, Missing: {files_missing}, Errors: {files_error}")

    # Top topics across all sections
    topic_counts = safe_query(conn, """
        SELECT value, COUNT(*) as cnt
        FROM encyclopedia_sections, json_each('["' || REPLACE(topics, ',', '","') || '"]')
        WHERE value != ''
        GROUP BY value ORDER BY cnt DESC LIMIT 15
    """)
    if not topic_counts:
        # Fallback: manual counting
        topic_agg = {}
        for sec in all_sections:
            for t in sec['topics'].split(','):
                t = t.strip()
                if t:
                    topic_agg[t] = topic_agg.get(t, 0) + 1
        topic_counts = sorted(topic_agg.items(), key=lambda x: -x[1])[:15]

    if topic_counts:
        print(f"\n  Top Topics Across All Encyclopedias:")
        for item in topic_counts:
            t, c = (item[0], item[1]) if isinstance(item, (list, tuple)) else (item['value'], item['cnt'])
            print(f"    {t}: {c} sections")

    # Sections by lane
    lane_counts = safe_query(conn,
        "SELECT case_lane, COUNT(*) FROM encyclopedia_sections GROUP BY case_lane ORDER BY COUNT(*) DESC")
    if lane_counts:
        print(f"\n  Sections by Case Lane:")
        for r in lane_counts:
            print(f"    {r[0]}: {r[1]} sections")

    # Largest sections (most content)
    biggest = safe_query(conn,
        "SELECT source_file, section_title, content_length FROM encyclopedia_sections ORDER BY content_length DESC LIMIT 10")
    if biggest:
        print(f"\n  Largest Sections (by content length):")
        for r in biggest:
            fname = os.path.basename(r[0])
            print(f"    {fname}: \"{r[1][:60]}\" — {r[2]:,} chars")

    # ── Generate reports ────────────────────────────────────────────
    report_data = {
        "tool": "#265 Videos Encyclopedia Indexer",
        "generated": scan_date,
        "total_sections": len(all_sections),
        "total_in_db": total_in_db,
        "files_processed": len(file_stats),
        "files_ok": files_ok,
        "files_missing": files_missing,
        "files_error": files_error,
        "file_details": file_stats,
        "top_topics": {item[0]: item[1] for item in topic_counts} if topic_counts else {},
        "by_lane": {r[0]: r[1] for r in lane_counts} if lane_counts else {},
    }

    json_path = os.path.join(report_dir, "tool_265_encyclopedia_index.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

    md_lines = [
        "# Tool #265: Videos Encyclopedia Indexer",
        f"Generated: {scan_date}",
        "",
        "## Summary",
        f"- **Total sections indexed**: {len(all_sections)}",
        f"- **Total in DB**: {total_in_db}",
        f"- **Files processed**: {len(file_stats)} (OK: {files_ok}, Missing: {files_missing}, Errors: {files_error})",
        "",
        "## File Details",
        "| File | Status | Sections | Total Chars |",
        "|------|--------|----------|-------------|",
    ]
    for fname, info in sorted(file_stats.items()):
        md_lines.append(
            f"| {fname} | {info['status']} | {info['sections']} | {info.get('total_chars', 0):,} |"
        )
    md_lines.append("")

    if topic_counts:
        md_lines.append("## Top Topics")
        md_lines.append("| Topic | Sections |")
        md_lines.append("|-------|----------|")
        for item in topic_counts:
            t, c = (item[0], item[1]) if isinstance(item, (list, tuple)) else (item['value'], item['cnt'])
            md_lines.append(f"| {t} | {c} |")
        md_lines.append("")

    if lane_counts:
        md_lines.append("## Sections by Case Lane")
        md_lines.append("| Lane | Sections |")
        md_lines.append("|------|----------|")
        for r in lane_counts:
            md_lines.append(f"| {r[0]} | {r[1]} |")
        md_lines.append("")

    if biggest:
        md_lines.append("## Largest Sections")
        md_lines.append("| File | Section | Length |")
        md_lines.append("|------|---------|--------|")
        for r in biggest:
            fname = os.path.basename(r[0])
            md_lines.append(f"| {fname} | {r[1][:60]} | {r[2]:,} |")

    md_path = os.path.join(report_dir, "tool_265_encyclopedia_index.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n  Reports written:")
    print(f"    {json_path}")
    print(f"    {md_path}")

    conn.close()
    print("\n" + "=" * 70)
    print("TOOL #265 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
