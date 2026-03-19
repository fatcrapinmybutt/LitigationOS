#!/usr/bin/env python3
"""
Tool #244 — Unified Case Chronology Builder
Build THE master chronology merging ALL sources: docket_events, d_drive_events,
evidence_quotes (date_ref), deadlines. Deduplicates by date+description similarity.
Categorizes events and flags timeline gaps.

LitigationOS — Pigors v. Watson
"""
import sys, os, sqlite3, json, re
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

def s(v):
    """Safe lowercase string — prevents NoneType crashes."""
    return (v or "").lower()

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def verify_table(conn, table_name):
    """Verify table exists and return column names."""
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    if not cols:
        return None
    return [c['name'] for c in cols]

def normalize_date(date_str):
    """Attempt to parse various date formats into YYYY-MM-DD."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S',
                '%m-%d-%Y', '%B %d, %Y', '%b %d, %Y', '%Y%m%d'):
        try:
            return datetime.strptime(date_str[:19], fmt).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            continue
    # Try extracting YYYY-MM-DD pattern
    match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
    if match:
        return match.group(1)
    return None

def categorize_event(description, event_type=None):
    """Categorize event based on description content."""
    desc = s(description) + " " + s(event_type)
    if any(w in desc for w in ['motion', 'filed', 'filing', 'petition', 'complaint', 'brief', 'appeal']):
        return 'legal_filing'
    if any(w in desc for w in ['order', 'ruling', 'judgment', 'hearing', 'court', 'judge', 'bench']):
        return 'court_action'
    if any(w in desc for w in ['interference', 'denied', 'withhold', 'blocked', 'alienat', 'custod']):
        return 'interference'
    if any(w in desc for w in ['medical', 'health', 'hospital', 'doctor', 'therapy', 'diagnosis']):
        return 'medical'
    if any(w in desc for w in ['threat', 'aggress', 'violen', 'harass', 'intimidat', 'assault']):
        return 'aggression'
    if any(w in desc for w in ['evidence', 'document', 'photo', 'video', 'text', 'email', 'record']):
        return 'evidence_event'
    return 'other'

def similarity_key(date_str, desc):
    """Generate a dedup key from date + first 60 normalized chars of description."""
    norm = re.sub(r'[^a-z0-9 ]', '', s(desc))[:60].strip()
    return f"{date_str}|{norm}"

def main():
    print("=" * 70)
    print("TOOL #244 — UNIFIED CASE CHRONOLOGY BUILDER")
    print("Pigors v. Watson | LitigationOS")
    print("=" * 70)

    if not os.path.exists(DB):
        print(f"ERROR: Database not found at {DB}")
        return

    conn = get_conn()
    events = []
    seen_keys = set()
    stats = defaultdict(int)

    # --- Source 1: docket_events ---
    print("\n[1/5] Loading docket_events...")
    cols = verify_table(conn, 'docket_events')
    if cols:
        print(f"  Columns: {cols}")
        date_col = 'event_date_iso' if 'event_date_iso' in cols else 'event_date' if 'event_date' in cols else None
        desc_col = 'title' if 'title' in cols else 'summary' if 'summary' in cols else None
        type_col = 'event_type' if 'event_type' in cols else None

        if date_col and desc_col:
            rows = conn.execute(f"SELECT * FROM docket_events").fetchall()
            for r in rows:
                d = normalize_date(r[date_col])
                desc = str(r[desc_col] or '')
                summary = str(r['summary'] if 'summary' in cols else '') if 'summary' in cols else ''
                full_desc = desc if not summary else f"{desc} — {summary}"
                key = similarity_key(d or '', full_desc)
                if key not in seen_keys and d:
                    seen_keys.add(key)
                    cat = categorize_event(full_desc, str(r[type_col]) if type_col else None)
                    events.append({
                        'date': d, 'event': full_desc[:300], 'source': 'docket_events',
                        'category': cat, 'evidence_count': 0, 'significance_score': 7,
                        'raw_type': str(r[type_col] or '') if type_col else ''
                    })
                    stats['docket_events'] += 1
            print(f"  Loaded {stats['docket_events']} events")
        else:
            print(f"  WARN: Missing date ({date_col}) or desc ({desc_col}) column")
    else:
        print("  TABLE NOT FOUND")

    # --- Source 2: d_drive_events ---
    print("\n[2/5] Loading d_drive_events...")
    cols = verify_table(conn, 'd_drive_events')
    if cols:
        print(f"  Columns: {cols}")
        date_col = 'event_date' if 'event_date' in cols else 'date' if 'date' in cols else None
        desc_col = 'event_description' if 'event_description' in cols else 'description' if 'description' in cols else None
        cat_col = 'category' if 'category' in cols else None
        sev_col = 'severity' if 'severity' in cols else None

        if date_col and desc_col:
            rows = conn.execute(f"SELECT * FROM d_drive_events").fetchall()
            for r in rows:
                d = normalize_date(r[date_col])
                desc = str(r[desc_col] or '')
                key = similarity_key(d or '', desc)
                if key not in seen_keys and d:
                    seen_keys.add(key)
                    raw_cat = str(r[cat_col] or '') if cat_col else ''
                    cat = categorize_event(desc, raw_cat)
                    sev = 5
                    if sev_col:
                        sev_val = s(str(r[sev_col] or ''))
                        if 'critical' in sev_val or 'high' in sev_val:
                            sev = 9
                        elif 'medium' in sev_val or 'moderate' in sev_val:
                            sev = 6
                        elif 'low' in sev_val:
                            sev = 3
                    events.append({
                        'date': d, 'event': desc[:300], 'source': 'd_drive_events',
                        'category': cat, 'evidence_count': 0, 'significance_score': sev,
                        'raw_type': raw_cat
                    })
                    stats['d_drive_events'] += 1
            print(f"  Loaded {stats['d_drive_events']} events")
        else:
            print(f"  WARN: Missing columns")
    else:
        print("  TABLE NOT FOUND")

    # --- Source 3: evidence_quotes with date_ref ---
    print("\n[3/5] Loading evidence_quotes (date_ref populated)...")
    cols = verify_table(conn, 'evidence_quotes')
    if cols:
        print(f"  Columns: {cols[:10]}... ({len(cols)} total)")
        has_date_ref = 'date_ref' in cols
        has_quote = 'quote_text' in cols
        has_cat = 'evidence_category' in cols

        if has_date_ref and has_quote:
            rows = conn.execute(
                "SELECT date_ref, quote_text, evidence_category, speaker, document_id "
                "FROM evidence_quotes WHERE date_ref IS NOT NULL AND date_ref != '' "
                "LIMIT 50000"
            ).fetchall()

            # Group by date for evidence counts
            date_evidence_counts = defaultdict(int)
            date_quotes = defaultdict(list)
            for r in rows:
                d = normalize_date(r['date_ref'])
                if d:
                    date_evidence_counts[d] += 1
                    if len(date_quotes[d]) < 3:
                        date_quotes[d].append(r)

            for d, quote_list in date_quotes.items():
                best = quote_list[0]
                qt = str(best['quote_text'] or '')[:200]
                cat_raw = str(best['evidence_category'] or '')
                cat = categorize_event(qt, cat_raw)
                speaker = str(best['speaker'] or 'Unknown')
                desc = f"[{speaker}] {qt}"
                key = similarity_key(d, desc)
                if key not in seen_keys:
                    seen_keys.add(key)
                    events.append({
                        'date': d, 'event': desc[:300], 'source': 'evidence_quotes',
                        'category': cat, 'evidence_count': date_evidence_counts[d],
                        'significance_score': min(10, 3 + date_evidence_counts[d] // 5),
                        'raw_type': cat_raw
                    })
                    stats['evidence_quotes'] += 1
            print(f"  Loaded {stats['evidence_quotes']} unique date entries ({sum(date_evidence_counts.values())} total quotes with dates)")
        else:
            print(f"  WARN: Missing date_ref or quote_text")
    else:
        print("  TABLE NOT FOUND")

    # --- Source 4: deadlines ---
    print("\n[4/5] Loading deadlines...")
    cols = verify_table(conn, 'deadlines')
    if cols:
        print(f"  Columns: {cols}")
        date_col = 'due_date_iso' if 'due_date_iso' in cols else 'due_date' if 'due_date' in cols else None
        title_col = 'title' if 'title' in cols else 'description' if 'description' in cols else None

        if date_col and title_col:
            rows = conn.execute(f"SELECT * FROM deadlines").fetchall()
            for r in rows:
                d = normalize_date(r[date_col])
                desc = f"DEADLINE: {r[title_col] or 'Unknown'}"
                basis = str(r['basis'] if 'basis' in cols else '') if 'basis' in cols else ''
                if basis:
                    desc += f" ({basis})"
                key = similarity_key(d or '', desc)
                if key not in seen_keys and d:
                    seen_keys.add(key)
                    events.append({
                        'date': d, 'event': desc[:300], 'source': 'deadlines',
                        'category': 'legal_filing', 'evidence_count': 0,
                        'significance_score': 8,
                        'raw_type': str(r['status'] if 'status' in cols else '') if 'status' in cols else ''
                    })
                    stats['deadlines'] += 1
            print(f"  Loaded {stats['deadlines']} deadlines")
        else:
            print(f"  WARN: Missing columns")
    else:
        print("  TABLE NOT FOUND")

    # --- Sort and analyze ---
    print("\n[5/5] Building unified chronology...")
    events.sort(key=lambda e: e['date'])

    # Update evidence_counts for docket/deadline events from evidence_quotes
    eq_cols = verify_table(conn, 'evidence_quotes')
    if eq_cols and 'date_ref' in eq_cols:
        eq_date_counts = {}
        for row in conn.execute(
            "SELECT date_ref, COUNT(*) as cnt FROM evidence_quotes "
            "WHERE date_ref IS NOT NULL AND date_ref != '' GROUP BY date_ref"
        ).fetchall():
            nd = normalize_date(row['date_ref'])
            if nd:
                eq_date_counts[nd] = eq_date_counts.get(nd, 0) + row['cnt']

        for evt in events:
            if evt['source'] != 'evidence_quotes':
                evt['evidence_count'] = eq_date_counts.get(evt['date'], 0)

    # Category summary
    cat_counts = defaultdict(int)
    for e in events:
        cat_counts[e['category']] += 1

    # Timeline gap analysis
    gaps = []
    if len(events) >= 2:
        for i in range(1, len(events)):
            try:
                d1 = datetime.strptime(events[i-1]['date'], '%Y-%m-%d')
                d2 = datetime.strptime(events[i]['date'], '%Y-%m-%d')
                delta = (d2 - d1).days
                if delta > 30:
                    gaps.append({
                        'start': events[i-1]['date'],
                        'end': events[i]['date'],
                        'days': delta,
                        'note': f"{delta}-day gap — potential evidence missing"
                    })
            except (ValueError, TypeError):
                continue

    # Source stats
    total_before_dedup = sum(stats.values())
    total_after = len(events)

    # Date range
    date_range_start = events[0]['date'] if events else 'N/A'
    date_range_end = events[-1]['date'] if events else 'N/A'

    # --- Generate MD Report ---
    md = []
    md.append("# 📅 UNIFIED CASE CHRONOLOGY")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case:** Pigors v. Watson | 14th Circuit Court")
    md.append(f"**Date Range:** {date_range_start} → {date_range_end}")
    md.append(f"**Total Events:** {total_after} (deduplicated from {total_before_dedup} raw)")
    md.append(f"**Timeline Gaps (>30 days):** {len(gaps)}\n")

    md.append("## SOURCE STATISTICS")
    md.append("| Source | Events | Query |")
    md.append("|--------|--------|-------|")
    md.append(f"| docket_events | {stats['docket_events']} | `SELECT * FROM docket_events` |")
    md.append(f"| d_drive_events | {stats['d_drive_events']} | `SELECT * FROM d_drive_events` |")
    md.append(f"| evidence_quotes | {stats['evidence_quotes']} | `SELECT ... FROM evidence_quotes WHERE date_ref IS NOT NULL` |")
    md.append(f"| deadlines | {stats['deadlines']} | `SELECT * FROM deadlines` |")
    md.append(f"| **TOTAL** | **{total_after}** | **Deduplicated by date+description** |")

    md.append("\n## CATEGORY BREAKDOWN")
    md.append("| Category | Count | Percentage |")
    md.append("|----------|-------|------------|")
    for cat in ['court_action', 'legal_filing', 'interference', 'medical', 'aggression', 'evidence_event', 'other']:
        cnt = cat_counts.get(cat, 0)
        pct = (cnt / total_after * 100) if total_after > 0 else 0
        emoji = {'court_action': '⚖️', 'legal_filing': '📄', 'interference': '🚫',
                 'medical': '🏥', 'aggression': '⚠️', 'evidence_event': '📎', 'other': '📌'}.get(cat, '📌')
        md.append(f"| {emoji} {cat} | {cnt} | {pct:.1f}% |")

    md.append("\n## MASTER TIMELINE")
    md.append("| # | Date | Category | Event | Source | Evidence | Significance |")
    md.append("|---|------|----------|-------|--------|----------|--------------|")
    for i, e in enumerate(events, 1):
        sig_bar = "█" * e['significance_score'] + "░" * (10 - e['significance_score'])
        cat_emoji = {'court_action': '⚖️', 'legal_filing': '📄', 'interference': '🚫',
                     'medical': '🏥', 'aggression': '⚠️', 'evidence_event': '📎', 'other': '📌'}.get(e['category'], '📌')
        event_text = e['event'].replace('|', '\\|')[:120]
        md.append(f"| {i} | {e['date']} | {cat_emoji} {e['category']} | {event_text} | {e['source']} | {e['evidence_count']} | {sig_bar} |")

    if gaps:
        md.append("\n## ⚠️ TIMELINE GAPS (>30 Days)")
        md.append("| # | Start | End | Gap (Days) | Note |")
        md.append("|---|-------|-----|------------|------|")
        for i, g in enumerate(gaps, 1):
            urgency = "🔴 CRITICAL" if g['days'] > 90 else "🟡 NOTABLE" if g['days'] > 60 else "🟢 MINOR"
            md.append(f"| {i} | {g['start']} | {g['end']} | {g['days']} | {urgency} — {g['note']} |")

    # Top significance events
    top_events = sorted(events, key=lambda e: e['significance_score'], reverse=True)[:15]
    md.append("\n## 🔥 HIGHEST SIGNIFICANCE EVENTS")
    md.append("| Date | Score | Category | Event | Evidence |")
    md.append("|------|-------|----------|-------|----------|")
    for e in top_events:
        event_text = e['event'].replace('|', '\\|')[:100]
        md.append(f"| {e['date']} | **{e['significance_score']}/10** | {e['category']} | {event_text} | {e['evidence_count']} |")

    md.append(f"\n---\n*Tool #244 — Unified Case Chronology Builder | LitigationOS*")
    md.append(f"*All data sourced from litigation_context.db — {total_after} events verified*")

    # Write outputs
    os.makedirs(REPORT_DIR, exist_ok=True)
    md_path = os.path.join(REPORT_DIR, "tool_244_unified_case_chronology.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    json_data = {
        'tool': 244, 'name': 'Unified Case Chronology Builder',
        'generated': datetime.now().isoformat(),
        'case': 'Pigors v. Watson',
        'date_range': {'start': date_range_start, 'end': date_range_end},
        'total_events': total_after,
        'source_stats': dict(stats),
        'category_counts': dict(cat_counts),
        'timeline_gaps': gaps,
        'events': events,
        'top_significance': [e for e in top_events],
        'dedup_method': 'date + first 60 normalized chars of description',
        'queries_used': {
            'docket_events': 'SELECT * FROM docket_events',
            'd_drive_events': 'SELECT * FROM d_drive_events',
            'evidence_quotes': "SELECT date_ref, quote_text, evidence_category, speaker, document_id FROM evidence_quotes WHERE date_ref IS NOT NULL AND date_ref != ''",
            'deadlines': 'SELECT * FROM deadlines',
            'evidence_counts': "SELECT date_ref, COUNT(*) FROM evidence_quotes WHERE date_ref IS NOT NULL GROUP BY date_ref"
        }
    }
    json_path = os.path.join(REPORT_DIR, "tool_244_unified_case_chronology.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")

    print(f"\n{'='*70}")
    print(f"CHRONOLOGY: {total_after} events | {date_range_start} → {date_range_end}")
    print(f"SOURCES: docket={stats['docket_events']} d_drive={stats['d_drive_events']} "
          f"evidence={stats['evidence_quotes']} deadlines={stats['deadlines']}")
    print(f"CATEGORIES: {dict(cat_counts)}")
    print(f"GAPS: {len(gaps)} periods >30 days with no evidence")
    print(f"{'='*70}")

    conn.close()

if __name__ == '__main__':
    main()
