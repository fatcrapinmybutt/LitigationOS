#!/usr/bin/env python3
"""Tool #261: File Locations Inventory Ingestor
Parses Andrew's master file locations list (4,063 files on I:\ drive)
and creates a searchable DB table with categorization for evidence discovery.
"""
import sys, os, json, sqlite3, re
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def categorize(path):
    p = path.lower()
    cats = []
    if 'nspd' in p or 'police' in p: cats.append('police')
    if 'healthwest' in p: cats.append('healthwest')
    if 'ppo' in p: cats.append('ppo')
    if 'custody' in p: cats.append('custody')
    if 'exparte' in p or 'ex_parte' in p or 'ex parte' in p: cats.append('exparte')
    if 'transcript' in p: cats.append('transcript')
    if 'affidavit' in p: cats.append('affidavit')
    if 'shady' in p or 'oaks' in p: cats.append('shady_oaks')
    if 'rusco' in p or 'martini' in p: cats.append('rusco')
    if 'watson' in p: cats.append('watson')
    if 'mcneill' in p: cats.append('mcneill')
    if 'filing' in p or 'motion' in p or 'brief' in p: cats.append('filing')
    if 'noreply' in p: cats.append('noreply')
    if 'chatgpt' in p: cats.append('chatgpt')
    if 'court' in p: cats.append('court')
    if 'order' in p: cats.append('order')
    if 'judge' in p: cats.append('judge')
    if 'berry' in p: cats.append('berry')
    if 'barnes' in p: cats.append('barnes')
    if 'pigors' in p: cats.append('pigors')
    if not cats: cats.append('uncategorized')
    return ','.join(cats)

def get_file_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.pdf',): return 'pdf'
    if ext in ('.txt',): return 'text'
    if ext in ('.csv',): return 'csv'
    if ext in ('.md',): return 'markdown'
    if ext in ('.html', '.htm'): return 'html'
    if ext in ('.docx', '.doc'): return 'word'
    if ext in ('.xlsx', '.xls'): return 'excel'
    if ext in ('.zip',): return 'archive'
    return ext.lstrip('.') or 'unknown'

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)
    source_file = r"C:\Users\andre\Documents\fileslocations.txt"

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #261: FILE LOCATIONS INVENTORY INGESTOR")
    print("=" * 70)

    # Create table
    conn.execute("""CREATE TABLE IF NOT EXISTS i_drive_file_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        file_name TEXT,
        file_ext TEXT,
        file_type TEXT,
        drive_letter TEXT,
        top_directory TEXT,
        in_archive INTEGER DEFAULT 0,
        archive_name TEXT,
        categories TEXT,
        lane_relevance TEXT,
        ingest_date TEXT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_idfi_categories ON i_drive_file_inventory(categories)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_idfi_type ON i_drive_file_inventory(file_type)")
    conn.commit()

    # Parse file
    print(f"\n[1/3] Reading {source_file}...")
    with open(source_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    rows = []
    stats = {'total': 0, 'in_archive': 0, 'direct': 0}
    cat_counts = {}
    type_counts = {}

    for line in lines:
        path = line.strip().strip('"')
        if not path or len(path) < 3:
            continue
        
        stats['total'] += 1
        fname = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()
        ftype = get_file_type(path)
        drive = path[0] if len(path) > 1 and path[1] == ':' else '?'
        
        parts = path.split('\\')
        top_dir = parts[1] if len(parts) > 1 else ''
        
        in_archive = 1 if '.zip\\' in path else 0
        archive_name = ''
        if in_archive:
            for p in parts:
                if p.lower().endswith('.zip'):
                    archive_name = p
                    break
            stats['in_archive'] += 1
        else:
            stats['direct'] += 1
        
        cats = categorize(path)
        
        # Lane relevance
        lane = []
        pl = path.lower()
        if any(k in pl for k in ['custody', 'parenting', 'visitation', 'foc']): lane.append('A')
        if any(k in pl for k in ['shady', 'housing', 'landlord', 'rico']): lane.append('B')
        if any(k in pl for k in ['1983', 'federal', 'civil_rights']): lane.append('C')
        if any(k in pl for k in ['ppo', 'protection']): lane.append('D')
        if any(k in pl for k in ['jtc', 'misconduct', 'mcneill', 'bias']): lane.append('E')
        if any(k in pl for k in ['coa', 'appeal', 'msc', 'supreme']): lane.append('F')
        lane_str = ','.join(lane) if lane else ''

        rows.append((path, fname, ext, ftype, drive, top_dir, in_archive, archive_name, cats, lane_str, datetime.now().isoformat()))
        
        for c in cats.split(','):
            cat_counts[c] = cat_counts.get(c, 0) + 1
        type_counts[ftype] = type_counts.get(ftype, 0) + 1

    print(f"  Parsed {stats['total']} files ({stats['direct']} direct, {stats['in_archive']} in archives)")

    # Insert
    print(f"\n[2/3] Inserting into i_drive_file_inventory...")
    conn.executemany("""INSERT OR IGNORE INTO i_drive_file_inventory
        (file_path, file_name, file_ext, file_type, drive_letter, top_directory,
         in_archive, archive_name, categories, lane_relevance, ingest_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", rows)
    conn.commit()
    
    actual = conn.execute("SELECT COUNT(*) FROM i_drive_file_inventory").fetchone()[0]
    print(f"  {actual} rows in table")

    # Summary
    print(f"\n[3/3] Generating reports...")
    
    # Lane distribution
    lane_counts = {}
    for row in rows:
        for l in row[9].split(','):
            if l:
                lane_counts[l] = lane_counts.get(l, 0) + 1

    results = {
        "tool": "#261 File Locations Inventory Ingestor",
        "generated": datetime.now().isoformat(),
        "source_file": source_file,
        "total_files": stats['total'],
        "direct_access": stats['direct'],
        "in_archives": stats['in_archive'],
        "db_rows": actual,
        "categories": dict(sorted(cat_counts.items(), key=lambda x: -x[1])),
        "file_types": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "lane_distribution": lane_counts,
        "high_value_targets": {
            "rusco_emails": cat_counts.get('rusco', 0),
            "healthwest_docs": cat_counts.get('healthwest', 0),
            "police_reports": cat_counts.get('police', 0),
            "ex_parte_docs": cat_counts.get('exparte', 0),
            "transcripts": cat_counts.get('transcript', 0)
        }
    }

    md_lines = [
        "# Tool #261: File Locations Inventory",
        f"Generated: {datetime.now().isoformat()}",
        f"Source: {source_file}",
        "",
        "## Summary",
        f"- **Total Files**: {stats['total']:,}",
        f"- **Directly Accessible**: {stats['direct']:,}",
        f"- **Inside Archives**: {stats['in_archive']:,}",
        f"- **DB Rows Created**: {actual:,}",
        "",
        "## Categories (by count)",
        "",
        "| Category | Count |",
        "|----------|-------|",
    ]
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1])[:20]:
        md_lines.append(f"| {cat} | {cnt:,} |")

    md_lines.extend(["", "## File Types", "", "| Type | Count |", "|------|-------|"])
    for ft, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {ft} | {cnt:,} |")
    
    md_lines.extend(["", "## Lane Distribution", "", "| Lane | Files |", "|------|-------|"])
    for lane, cnt in sorted(lane_counts.items()):
        md_lines.append(f"| {lane} | {cnt:,} |")
    
    md_lines.extend([
        "", "## High-Value Evidence Targets",
        f"- **Rusco/Martini Emails**: {cat_counts.get('rusco', 0)} files",
        f"- **HealthWest Records**: {cat_counts.get('healthwest', 0)} files",
        f"- **Police/NSPD Reports**: {cat_counts.get('police', 0)} files",
        f"- **Ex Parte Documents**: {cat_counts.get('exparte', 0)} files",
        f"- **Transcripts**: {cat_counts.get('transcript', 0)} files",
        f"- **PPO Documents**: {cat_counts.get('ppo', 0)} files",
        f"- **Custody Documents**: {cat_counts.get('custody', 0)} files",
    ])

    md_path = os.path.join(report_dir, "tool_261_file_inventory.md")
    json_path = os.path.join(report_dir, "tool_261_file_inventory.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")
    conn.close()

    print(f"\n{'='*70}")
    print(f"INDEXED: {actual:,} files | CATEGORIES: {len(cat_counts)} | TYPES: {len(type_counts)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
