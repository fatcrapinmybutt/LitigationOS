#!/usr/bin/env python3
"""
Placeholder Resolution Script for LitigationOS Filing Stacks.
Scans, categorizes, auto-resolves, and reports on placeholder tags.
"""

import sys
import os
import re
import sqlite3
import json
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\andre\LitigationOS"
DB = os.path.join(BASE, "litigation_context.db")
REPORT_PATH = os.path.join(BASE, "00_SYSTEM", "PLACEHOLDER_RESOLUTION_REPORT.md")

FILING_DIRS = [
    "01_COA_366810",
    "02_TRIAL_14TH",
    "03_FEDERAL_1983",
    "04_JTC_MCNEILL",
    "05_BAR_BARNES",
    "06_EMERGENCY",
]

# Regex to match placeholder tags
TAG_PATTERN = re.compile(
    r'\[(VERIFY|ADDRESS|INSERT|TBD|TODO|PLACEHOLDER)[^\]]*\]',
    re.IGNORECASE
)

# ============================================================
# TASK 0: Explore DB schema for resolution data
# ============================================================
def explore_db():
    """Find relevant tables and their schemas."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    tables = [t[0] for t in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]

    keywords = ['case_law', 'mcl_auth', 'mcl_authority', 'chronol', 'timeline',
                'address', 'contact', 'party', 'person', 'citation', 'exhibit',
                'case_number', 'docket']
    relevant = []
    for t in tables:
        tl = t.lower()
        if any(k in tl for k in keywords):
            relevant.append(t)

    print(f"Total tables: {len(tables)}")
    print(f"\nRelevant tables ({len(relevant)}):")
    for t in relevant:
        cols = cur.execute(f"PRAGMA table_info([{t}])").fetchall()
        col_names = [c[1] for c in cols]
        row_count = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"  {t} ({row_count} rows): {col_names}")

    conn.close()
    return relevant


# ============================================================
# TASK 1: Scan and Categorize All Placeholders
# ============================================================
def scan_placeholders():
    """Scan all .md files for placeholder tags."""
    all_tags = []

    for dir_name in FILING_DIRS:
        dir_path = os.path.join(BASE, dir_name)
        if not os.path.isdir(dir_path):
            print(f"  SKIP: {dir_name} not found")
            continue

        for root, dirs, files in os.walk(dir_path):
            for fname in sorted(files):
                if not fname.lower().endswith('.md'):
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, BASE)

                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except Exception as e:
                    print(f"  ERROR reading {rel_path}: {e}")
                    continue

                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    for match in TAG_PATTERN.finditer(line):
                        tag_text = match.group(0)
                        tag_type = match.group(1).upper()
                        start = max(0, match.start() - 20)
                        end = min(len(line), match.end() + 20)
                        context = line[start:end]

                        all_tags.append({
                            'file': rel_path,
                            'dir': dir_name,
                            'line': line_num,
                            'tag': tag_text,
                            'type': tag_type,
                            'context': context,
                            'full_line': line.strip(),
                        })

    return all_tags


# ============================================================
# TASK 2: Auto-Resolve from DB
# ============================================================
def build_resolution_map(all_tags):
    """Build resolution map from DB data."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Get all table names for dynamic lookup
    tables = [t[0] for t in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]

    # --- Build case law lookup ---
    case_law_data = {}
    case_law_tables = [t for t in tables if 'case_law' in t.lower()]
    for t in case_law_tables:
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info([{t}])").fetchall()]
            # Look for citation-like columns
            cite_cols = [c for c in cols if any(k in c.lower() for k in ['cite', 'citation', 'name', 'title', 'case'])]
            if cite_cols:
                rows = cur.execute(f"SELECT * FROM [{t}] LIMIT 500").fetchall()
                for row in rows:
                    row_dict = dict(zip(cols, row))
                    for cc in cite_cols:
                        if row_dict.get(cc):
                            key = str(row_dict[cc]).strip().lower()
                            case_law_data[key] = row_dict
        except Exception as e:
            print(f"  Warning: error reading {t}: {e}")

    # --- Build MCL lookup ---
    mcl_data = {}
    mcl_tables = [t for t in tables if 'mcl' in t.lower()]
    for t in mcl_tables:
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info([{t}])").fetchall()]
            cite_cols = [c for c in cols if any(k in c.lower() for k in ['cite', 'citation', 'section', 'mcl', 'statute', 'title', 'name'])]
            if cite_cols:
                rows = cur.execute(f"SELECT * FROM [{t}] LIMIT 500").fetchall()
                for row in rows:
                    row_dict = dict(zip(cols, row))
                    for cc in cite_cols:
                        if row_dict.get(cc):
                            key = str(row_dict[cc]).strip().lower()
                            mcl_data[key] = row_dict
        except Exception as e:
            print(f"  Warning: error reading {t}: {e}")

    # --- Build timeline lookup ---
    timeline_data = []
    timeline_tables = [t for t in tables if any(k in t.lower() for k in ['timeline', 'chronol', 'event', 'calendar', 'date', 'deadline'])]
    for t in timeline_tables:
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info([{t}])").fetchall()]
            rows = cur.execute(f"SELECT * FROM [{t}] LIMIT 1000").fetchall()
            for row in rows:
                row_dict = dict(zip(cols, row))
                row_dict['_table'] = t
                timeline_data.append(row_dict)
        except Exception as e:
            print(f"  Warning: error reading {t}: {e}")

    conn.close()

    print(f"\n  Case law entries loaded: {len(case_law_data)}")
    print(f"  MCL entries loaded: {len(mcl_data)}")
    print(f"  Timeline entries loaded: {len(timeline_data)}")

    return {
        'case_law': case_law_data,
        'mcl': mcl_data,
        'timeline': timeline_data,
    }


def resolve_tag(tag_info, db_data):
    """
    Try to resolve a single placeholder tag. Returns (resolved_text, resolution_note) or (None, reason).
    """
    tag = tag_info['tag']
    tag_type = tag_info['type']
    tag_inner = tag[1:-1].strip()  # Remove brackets

    # --- ADDRESS tags ---
    if tag_type == 'ADDRESS':
        return ("Andrew J. Pigors, Pro Se, Muskegon, Michigan 49442",
                "Resolved: Pro Se address")

    # --- INSERT tags ---
    if tag_type == 'INSERT':
        inner_lower = tag_inner.lower()

        # Case numbers
        if 'case' in inner_lower and ('number' in inner_lower or 'no' in inner_lower or '#' in inner_lower):
            if '14th' in inner_lower or 'trial' in inner_lower or 'circuit' in inner_lower:
                return ("Case No. 2024-001507-DC", "Resolved: 14th Circuit case number")
            if 'coa' in inner_lower or 'appeal' in inner_lower or '366810' in inner_lower:
                return ("Case No. 366810", "Resolved: COA case number")
            # Default based on filing directory
            dir_name = tag_info['dir']
            if '01_COA' in dir_name:
                return ("Case No. 366810", "Resolved: COA case number (from dir context)")
            elif '02_TRIAL' in dir_name:
                return ("Case No. 2024-001507-DC", "Resolved: 14th Circuit case number (from dir context)")

        # Date insertions
        if 'date' in inner_lower:
            return (None, "MANUAL: Date insertion needs specific context")

        # Name insertions
        if any(k in inner_lower for k in ['name', 'appellant', 'petitioner', 'plaintiff', 'pro se']):
            return ("Andrew J. Pigors", "Resolved: Party name")

        # Judge
        if 'judge' in inner_lower:
            if 'coa' in tag_info['dir'].lower() or 'appeal' in inner_lower:
                return (None, "MANUAL: COA panel judges need verification")
            return (None, "MANUAL: Judge name needs verification")

        # Court name
        if 'court' in inner_lower:
            dir_name = tag_info['dir']
            if '01_COA' in dir_name:
                return ("Michigan Court of Appeals", "Resolved: Court name from dir context")
            elif '02_TRIAL' in dir_name:
                return ("14th Circuit Court, Muskegon County", "Resolved: Court name from dir context")
            elif '03_FEDERAL' in dir_name:
                return ("United States District Court, Western District of Michigan",
                        "Resolved: Court name from dir context")

        return (None, f"MANUAL: Cannot auto-resolve INSERT: {tag_inner}")

    # --- VERIFY tags ---
    if tag_type == 'VERIFY':
        inner_lower = tag_inner.lower()
        # Strip the VERIFY prefix
        verify_content = re.sub(r'^VERIFY\s*:?\s*', '', tag_inner, flags=re.IGNORECASE).strip()
        vc_lower = verify_content.lower()

        # Check if it's a case citation we can verify
        case_law = db_data.get('case_law', {})
        for key, data in case_law.items():
            # Fuzzy match: check if significant parts overlap
            if len(verify_content) > 5 and (vc_lower in key or key in vc_lower):
                # Found a match - extract the best citation
                cite_val = None
                for col_name in ['citation', 'cite', 'full_citation', 'name', 'title', 'case_name']:
                    if col_name in data and data[col_name]:
                        cite_val = str(data[col_name])
                        break
                if cite_val:
                    return (cite_val, f"VERIFIED from DB: {cite_val}")

        # Check MCL
        mcl = db_data.get('mcl', {})
        for key, data in mcl.items():
            if len(verify_content) > 3 and (vc_lower in key or key in vc_lower):
                cite_val = None
                for col_name in ['citation', 'cite', 'section', 'mcl', 'full_citation', 'name', 'title']:
                    if col_name in data and data[col_name]:
                        cite_val = str(data[col_name])
                        break
                if cite_val:
                    return (cite_val, f"VERIFIED from DB (MCL): {cite_val}")

        return (None, f"MANUAL: Cannot verify - {verify_content}")

    # --- TBD tags ---
    if tag_type == 'TBD':
        inner_lower = tag_inner.lower()
        tbd_content = re.sub(r'^TBD\s*:?\s*', '', tag_inner, flags=re.IGNORECASE).strip()

        if 'date' in inner_lower:
            # Try to find relevant dates from timeline
            timeline = db_data.get('timeline', [])
            if timeline:
                return (None, f"MANUAL: Date TBD - check timeline ({len(timeline)} entries available)")
            return (None, "MANUAL: Date TBD - no timeline data found")

        return (None, f"MANUAL: TBD - {tbd_content}")

    # --- TODO tags ---
    if tag_type == 'TODO':
        return (None, f"MANUAL: TODO item requires human action")

    # --- PLACEHOLDER tags ---
    if tag_type == 'PLACEHOLDER':
        inner_lower = tag_inner.lower()
        if 'exhibit' in inner_lower:
            return (None, "MANUAL: Exhibit placeholder needs real document reference")
        if 'signature' in inner_lower or 'sign' in inner_lower:
            return (None, "MANUAL: Signature placeholder - physical signing required")
        return (None, f"MANUAL: Placeholder - {tag_inner}")

    return (None, f"MANUAL: Unknown tag type - {tag}")


def apply_resolutions_to_coa(all_tags, resolutions):
    """Apply resolved tags to COA brief files."""
    # Group COA resolutions by file
    coa_resolutions = defaultdict(list)
    for i, tag_info in enumerate(all_tags):
        if tag_info['dir'] != '01_COA_366810':
            continue
        resolved_text, note = resolutions[i]
        if resolved_text is not None:
            coa_resolutions[tag_info['file']].append({
                'tag': tag_info['tag'],
                'resolved': resolved_text,
                'note': note,
                'line': tag_info['line'],
            })
        else:
            # Mark unresolvable with comment
            coa_resolutions[tag_info['file']].append({
                'tag': tag_info['tag'],
                'resolved': None,
                'note': note,
                'line': tag_info['line'],
            })

    files_modified = 0
    tags_replaced = 0
    tags_commented = 0

    for rel_file, tag_list in coa_resolutions.items():
        fpath = os.path.join(BASE, rel_file)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"  ERROR reading {rel_file}: {e}")
            continue

        original = content
        for item in tag_list:
            tag = item['tag']
            escaped_tag = re.escape(tag)
            if item['resolved'] is not None:
                content = content.replace(tag, item['resolved'], 1)
                tags_replaced += 1
            else:
                # Wrap unresolvable in HTML comment
                replacement = f"<!-- MANUAL: {tag} -->{tag}"
                # Only add comment if not already there
                if f"<!-- MANUAL: {tag} -->" not in content:
                    content = content.replace(tag, replacement, 1)
                    tags_commented += 1

        if content != original:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_modified += 1
            except Exception as e:
                print(f"  ERROR writing {rel_file}: {e}")

    return files_modified, tags_replaced, tags_commented


# ============================================================
# TASK 3: Generate Resolution Report
# ============================================================
def generate_report(all_tags, resolutions, files_modified, tags_replaced, tags_commented):
    """Generate the resolution report."""
    total = len(all_tags)
    resolved_count = sum(1 for r, _ in resolutions if r is not None)
    remaining_count = total - resolved_count

    # Per-file summary
    file_summary = defaultdict(lambda: {'total': 0, 'resolved': 0, 'remaining': 0})
    for i, tag_info in enumerate(all_tags):
        f = tag_info['file']
        file_summary[f]['total'] += 1
        if resolutions[i][0] is not None:
            file_summary[f]['resolved'] += 1
        else:
            file_summary[f]['remaining'] += 1

    # Per-directory summary
    dir_summary = defaultdict(lambda: {'total': 0, 'resolved': 0, 'remaining': 0})
    for i, tag_info in enumerate(all_tags):
        d = tag_info['dir']
        dir_summary[d]['total'] += 1
        if resolutions[i][0] is not None:
            dir_summary[d]['resolved'] += 1
        else:
            dir_summary[d]['remaining'] += 1

    # Per-type summary
    type_summary = defaultdict(lambda: {'total': 0, 'resolved': 0, 'remaining': 0})
    for i, tag_info in enumerate(all_tags):
        t = tag_info['type']
        type_summary[t]['total'] += 1
        if resolutions[i][0] is not None:
            type_summary[t]['resolved'] += 1
        else:
            type_summary[t]['remaining'] += 1

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(f"# Placeholder Resolution Report")
    lines.append(f"")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Script:** `_placeholder_resolve.py`")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total placeholder tags found | {total} |")
    lines.append(f"| Tags auto-resolved | {resolved_count} |")
    lines.append(f"| Tags remaining (manual) | {remaining_count} |")
    lines.append(f"| COA files modified | {files_modified} |")
    lines.append(f"| COA tags replaced in-file | {tags_replaced} |")
    lines.append(f"| COA tags commented (unresolvable) | {tags_commented} |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Per-directory breakdown
    lines.append(f"## Per-Directory Breakdown")
    lines.append(f"")
    lines.append(f"| Directory | Total | Resolved | Remaining |")
    lines.append(f"|-----------|-------|----------|-----------|")
    for d in FILING_DIRS:
        s = dir_summary[d]
        lines.append(f"| {d} | {s['total']} | {s['resolved']} | {s['remaining']} |")
    lines.append(f"")

    # Per-type breakdown
    lines.append(f"## Per-Type Breakdown")
    lines.append(f"")
    lines.append(f"| Tag Type | Total | Resolved | Remaining |")
    lines.append(f"|----------|-------|----------|-----------|")
    for t in sorted(type_summary.keys()):
        s = type_summary[t]
        lines.append(f"| [{t}] | {s['total']} | {s['resolved']} | {s['remaining']} |")
    lines.append(f"")

    # Auto-resolved list
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Auto-Resolved Tags ({resolved_count})")
    lines.append(f"")
    for i, tag_info in enumerate(all_tags):
        resolved_text, note = resolutions[i]
        if resolved_text is not None:
            lines.append(f"- **{tag_info['file']}** L{tag_info['line']}: `{tag_info['tag']}` → `{resolved_text}` ({note})")
    lines.append(f"")

    # Remaining tags (grouped by file, COA first)
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Remaining Tags Requiring Manual Resolution ({remaining_count})")
    lines.append(f"")

    remaining_by_file = defaultdict(list)
    for i, tag_info in enumerate(all_tags):
        resolved_text, note = resolutions[i]
        if resolved_text is None:
            remaining_by_file[tag_info['file']].append({
                'line': tag_info['line'],
                'tag': tag_info['tag'],
                'note': note,
                'context': tag_info['context'],
            })

    # Sort: COA files first
    sorted_files = sorted(remaining_by_file.keys(),
                          key=lambda f: ('1' if f.startswith('01_COA') else '0') + f,
                          reverse=True)
    for f in sorted_files:
        items = remaining_by_file[f]
        lines.append(f"### {f} ({len(items)} remaining)")
        lines.append(f"")
        for item in items:
            lines.append(f"- **L{item['line']}**: `{item['tag']}` — {item['note']}")
            lines.append(f"  - Context: `...{item['context']}...`")
        lines.append(f"")

    # Per-file summary table
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Per-File Summary")
    lines.append(f"")
    lines.append(f"| File | Total | Resolved | Remaining |")
    lines.append(f"|------|-------|----------|-----------|")
    for f in sorted(file_summary.keys()):
        s = file_summary[f]
        lines.append(f"| {f} | {s['total']} | {s['resolved']} | {s['remaining']} |")
    lines.append(f"")

    # Priority items
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## Priority: COA Brief Critical Remaining Tags")
    lines.append(f"")
    coa_remaining = [(i, all_tags[i]) for i in range(len(all_tags))
                     if all_tags[i]['dir'] == '01_COA_366810' and resolutions[i][0] is None]
    if coa_remaining:
        for idx, (i, tag_info) in enumerate(coa_remaining[:50]):
            _, note = resolutions[i]
            lines.append(f"{idx+1}. **{tag_info['file']}** L{tag_info['line']}: `{tag_info['tag']}` — {note}")
    else:
        lines.append(f"All COA tags resolved! ✅")
    lines.append(f"")

    report_text = '\n'.join(lines)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_text)

    return report_text


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("PLACEHOLDER RESOLUTION SCRIPT")
    print("=" * 60)

    # Step 0: Explore DB
    print("\n[STEP 0] Exploring database...")
    relevant_tables = explore_db()

    # Step 1: Scan
    print("\n[STEP 1] Scanning all .md files for placeholder tags...")
    all_tags = scan_placeholders()
    print(f"\n  TOTAL TAGS FOUND: {len(all_tags)}")

    # Print per-file counts
    file_counts = defaultdict(int)
    dir_counts = defaultdict(int)
    type_counts = defaultdict(int)
    for t in all_tags:
        file_counts[t['file']] += 1
        dir_counts[t['dir']] += 1
        type_counts[t['type']] += 1

    print(f"\n  Per-directory:")
    for d in FILING_DIRS:
        print(f"    {d}: {dir_counts[d]}")
    print(f"\n  Per-type:")
    for t in sorted(type_counts.keys()):
        print(f"    [{t}]: {type_counts[t]}")

    # Step 2: Build resolution map from DB
    print("\n[STEP 2] Loading DB data for resolution...")
    db_data = build_resolution_map(all_tags)

    # Step 2b: Resolve each tag
    print("\n[STEP 2b] Resolving tags...")
    resolutions = []
    for tag_info in all_tags:
        resolved_text, note = resolve_tag(tag_info, db_data)
        resolutions.append((resolved_text, note))

    resolved_count = sum(1 for r, _ in resolutions if r is not None)
    remaining_count = len(all_tags) - resolved_count
    print(f"  Resolved: {resolved_count}")
    print(f"  Remaining: {remaining_count}")

    # Step 2c: Apply to COA files
    print("\n[STEP 2c] Applying resolutions to COA brief files...")
    files_modified, tags_replaced, tags_commented = apply_resolutions_to_coa(all_tags, resolutions)
    print(f"  Files modified: {files_modified}")
    print(f"  Tags replaced: {tags_replaced}")
    print(f"  Tags commented: {tags_commented}")

    # Step 3: Generate report
    print("\n[STEP 3] Generating resolution report...")
    report = generate_report(all_tags, resolutions, files_modified, tags_replaced, tags_commented)
    print(f"  Report saved to: {REPORT_PATH}")

    # Step 4: Final summary
    print("\n" + "=" * 60)
    print(f"RESOLVED: {resolved_count} of {len(all_tags)} tags auto-resolved")
    print(f"REMAINING: {remaining_count} tags need manual attention")
    print("=" * 60)

    # Top 10 critical remaining (COA first)
    print("\nTop 10 Most Critical Remaining Tags:")
    coa_remaining = [(i, all_tags[i]) for i in range(len(all_tags))
                     if all_tags[i]['dir'] == '01_COA_366810' and resolutions[i][0] is None]
    other_remaining = [(i, all_tags[i]) for i in range(len(all_tags))
                       if all_tags[i]['dir'] != '01_COA_366810' and resolutions[i][0] is None]

    critical = (coa_remaining + other_remaining)[:10]
    for rank, (i, tag_info) in enumerate(critical, 1):
        _, note = resolutions[i]
        print(f"  {rank}. [{tag_info['dir']}] {tag_info['file']} L{tag_info['line']}: {tag_info['tag']}")
        print(f"     → {note}")

    print("\nDone.")


if __name__ == '__main__':
    main()
