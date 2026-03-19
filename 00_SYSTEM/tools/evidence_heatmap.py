#!/usr/bin/env python3
"""
Evidence Heat Map — Visual evidence density across timeline & categories.

Novel LitigationOS Tool #21

Generates ASCII heat maps showing:
1. Evidence density by month across the case timeline
2. Evidence strength by category (custody, PPO, housing, fraud, etc.)
3. Gap identification (periods with weak/missing evidence)
4. Cross-lane evidence correlation
5. Witness activity timelines
"""
import sys, os, json, sqlite3, re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

HEAT_CHARS = [' ', '░', '▒', '▓', '█']  # 0-4 intensity levels
HEAT_COLORS = {0: '⬜', 1: '🟦', 2: '🟩', 3: '🟧', 4: '🔴'}

CATEGORIES = [
    'custody', 'parenting', 'visitation', 'child',
    'ppo', 'protection', 'stalking', 'harassment',
    'housing', 'eviction', 'lease', 'shady oaks',
    'fraud', 'perjury', 'false', 'fabricat',
    'judicial', 'mcneill', 'ex parte', 'bias',
    'conspiracy', 'berry', 'barnes', 'watson',
]

CATEGORY_GROUPS = {
    'Custody/Parenting': ['custody', 'parenting', 'visitation', 'child'],
    'PPO/Protection': ['ppo', 'protection', 'stalking', 'harassment'],
    'Housing': ['housing', 'eviction', 'lease', 'shady oaks'],
    'Fraud/Perjury': ['fraud', 'perjury', 'false', 'fabricat'],
    'Judicial Misconduct': ['judicial', 'mcneill', 'ex parte', 'bias'],
    'Conspiracy': ['conspiracy', 'berry', 'barnes'],
}

LANE_MAP = {
    'A': 'Custody', 'B': 'Housing', 'C': 'Convergence',
    'D': 'PPO', 'E': 'Misconduct', 'F': 'Appellate',
}


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def table_exists(conn, name):
    r = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r[0] > 0


def extract_dates_from_text(text):
    """Extract date references from text."""
    dates = []
    # YYYY-MM-DD
    for m in re.finditer(r'(\d{4})-(\d{2})-(\d{2})', text or ''):
        try:
            d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if 2020 <= d.year <= 2027:
                dates.append(d)
        except ValueError:
            pass
    # Month DD, YYYY
    months = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
              'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}
    for m in re.finditer(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})', text or '', re.IGNORECASE):
        try:
            mon = months[m.group(1).lower()]
            d = datetime(int(m.group(3)), mon, int(m.group(2)))
            if 2020 <= d.year <= 2027:
                dates.append(d)
        except (ValueError, KeyError):
            pass
    # MM/DD/YYYY
    for m in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{4})', text or ''):
        try:
            d = datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            if 2020 <= d.year <= 2027:
                dates.append(d)
        except ValueError:
            pass
    return dates


def build_timeline_heatmap(conn):
    """Build evidence density by month."""
    monthly = defaultdict(int)
    
    # evidence_quotes
    if table_exists(conn, 'evidence_quotes'):
        try:
            rows = conn.execute(
                "SELECT quote_text FROM evidence_quotes LIMIT 20000"
            ).fetchall()
            for row in rows:
                for d in extract_dates_from_text(row[0]):
                    key = f"{d.year}-{d.month:02d}"
                    monthly[key] += 1
        except Exception:
            pass
    
    # docket_events
    if table_exists(conn, 'docket_events'):
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(docket_events)").fetchall()]
            date_col = None
            for c in cols:
                if 'date' in c.lower():
                    date_col = c
                    break
            if date_col:
                rows = conn.execute(f"SELECT {date_col} FROM docket_events WHERE {date_col} IS NOT NULL").fetchall()
                for row in rows:
                    for d in extract_dates_from_text(str(row[0])):
                        key = f"{d.year}-{d.month:02d}"
                        monthly[key] += 1
        except Exception:
            pass
    
    # judicial_violations
    if table_exists(conn, 'judicial_violations'):
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
            date_col = None
            for c in cols:
                if 'date' in c.lower():
                    date_col = c
                    break
            if date_col:
                rows = conn.execute(f"SELECT {date_col} FROM judicial_violations WHERE {date_col} IS NOT NULL LIMIT 5000").fetchall()
                for row in rows:
                    for d in extract_dates_from_text(str(row[0])):
                        key = f"{d.year}-{d.month:02d}"
                        monthly[key] += 1
        except Exception:
            pass
    
    return monthly


def build_category_heatmap(conn):
    """Build evidence strength by category."""
    category_counts = defaultdict(int)
    
    tables_to_scan = [
        ('evidence_quotes', 'quote_text'),
        ('detected_contradictions', 'statement_1'),
        ('watson_perjury_compilation', 'statement_text'),
        ('adversary_assertions', 'assertion_text'),
    ]
    
    for table, col in tables_to_scan:
        if not table_exists(conn, table):
            continue
        try:
            actual_cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            if col not in actual_cols:
                continue
            rows = conn.execute(f"SELECT {col} FROM {table} LIMIT 10000").fetchall()
            for row in rows:
                text = (row[0] or '').lower()
                for group_name, keywords in CATEGORY_GROUPS.items():
                    for kw in keywords:
                        if kw in text:
                            category_counts[group_name] += 1
                            break
        except Exception:
            pass
    
    return category_counts


def build_witness_activity(conn):
    """Build activity timelines per witness/actor."""
    witness_counts = defaultdict(lambda: defaultdict(int))
    
    # watson_perjury_compilation - watson_member field
    if table_exists(conn, 'watson_perjury_compilation'):
        try:
            rows = conn.execute(
                "SELECT watson_member, statement_text FROM watson_perjury_compilation LIMIT 10000"
            ).fetchall()
            for row in rows:
                actor = row[0] or 'Unknown'
                for d in extract_dates_from_text(row[1]):
                    key = f"{d.year}-{d.month:02d}"
                    witness_counts[actor][key] += 1
        except Exception:
            pass
    
    # adversary_assertions - speaker field
    if table_exists(conn, 'adversary_assertions'):
        try:
            rows = conn.execute(
                "SELECT speaker, assertion_text FROM adversary_assertions LIMIT 10000"
            ).fetchall()
            for row in rows:
                actor = row[0] or 'Unknown'
                for d in extract_dates_from_text(row[1]):
                    key = f"{d.year}-{d.month:02d}"
                    witness_counts[actor][key] += 1
        except Exception:
            pass
    
    return witness_counts


def find_evidence_gaps(monthly, start_year=2023, end_year=2026):
    """Identify months with weak or missing evidence."""
    gaps = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            key = f"{year}-{month:02d}"
            count = monthly.get(key, 0)
            if count < 5:
                gaps.append({
                    'month': key,
                    'count': count,
                    'severity': 'CRITICAL' if count == 0 else 'WARNING',
                    'recommendation': f"Search drives for evidence from {key}",
                })
    return gaps


def render_ascii_heatmap(data, title, start_year=2023, end_year=2026):
    """Render an ASCII heat map."""
    lines = []
    lines.append(f"\n{'─' * 60}")
    lines.append(f"  {title}")
    lines.append(f"{'─' * 60}")
    
    if not data:
        lines.append("  No data available")
        return '\n'.join(lines)
    
    max_val = max(data.values()) if data else 1
    
    # Header row
    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    lines.append(f"         {'  '.join(months)}")
    
    for year in range(start_year, end_year + 1):
        row = f"  {year}  "
        for month in range(1, 13):
            key = f"{year}-{month:02d}"
            val = data.get(key, 0)
            # Normalize to 0-4
            if max_val > 0:
                level = min(4, int((val / max_val) * 4.99)) if val > 0 else 0
            else:
                level = 0
            row += f" {HEAT_CHARS[level]}{HEAT_CHARS[level]}"
        row += f"  ({sum(data.get(f'{year}-{m:02d}', 0) for m in range(1, 13))})"
        lines.append(row)
    
    lines.append(f"  Scale: ' '=0  ░=low  ▒=med  ▓=high  █=max (max={max_val})")
    return '\n'.join(lines)


def render_category_bars(category_counts):
    """Render horizontal bar chart for categories."""
    lines = []
    lines.append(f"\n{'─' * 60}")
    lines.append(f"  EVIDENCE BY CATEGORY")
    lines.append(f"{'─' * 60}")
    
    if not category_counts:
        lines.append("  No data available")
        return '\n'.join(lines)
    
    max_val = max(category_counts.values())
    max_bar = 40
    
    for cat in sorted(category_counts.keys(), key=lambda x: -category_counts[x]):
        count = category_counts[cat]
        bar_len = int((count / max_val) * max_bar) if max_val > 0 else 0
        bar = '█' * bar_len
        lines.append(f"  {cat:22s} {bar} {count:,}")
    
    return '\n'.join(lines)


def render_witness_heatmap(witness_counts, start_year=2023, end_year=2026):
    """Render witness activity heatmap."""
    lines = []
    lines.append(f"\n{'─' * 60}")
    lines.append(f"  WITNESS ACTIVITY TIMELINE")
    lines.append(f"{'─' * 60}")
    
    if not witness_counts:
        lines.append("  No data available")
        return '\n'.join(lines)
    
    # Get top 8 witnesses by total activity
    witness_totals = {w: sum(months.values()) for w, months in witness_counts.items()}
    top_witnesses = sorted(witness_totals.keys(), key=lambda x: -witness_totals[x])[:8]
    
    all_vals = [v for w in top_witnesses for v in witness_counts[w].values()]
    max_val = max(all_vals) if all_vals else 1
    
    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    
    for year in range(start_year, end_year + 1):
        lines.append(f"\n  --- {year} ---     {'  '.join(months)}")
        for witness in top_witnesses:
            name_short = witness[:16].ljust(16)
            row = f"  {name_short} "
            for month in range(1, 13):
                key = f"{year}-{month:02d}"
                val = witness_counts[witness].get(key, 0)
                if max_val > 0:
                    level = min(4, int((val / max_val) * 4.99)) if val > 0 else 0
                else:
                    level = 0
                row += f" {HEAT_CHARS[level]}{HEAT_CHARS[level]}"
            total = sum(witness_counts[witness].get(f'{year}-{m:02d}', 0) for m in range(1, 13))
            if total > 0:
                row += f"  ({total})"
            lines.append(row)
    
    return '\n'.join(lines)


def main():
    print("=" * 70)
    print("EVIDENCE HEAT MAP — Visual Evidence Density Analysis")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn = get_connection()
    
    # 1. Timeline heatmap
    print("\n📊 Building timeline heatmap...")
    monthly = build_timeline_heatmap(conn)
    print(render_ascii_heatmap(monthly, "EVIDENCE DENSITY BY MONTH"))
    
    # 2. Category heatmap
    print("\n📊 Building category analysis...")
    categories = build_category_heatmap(conn)
    print(render_category_bars(categories))
    
    # 3. Witness activity
    print("\n📊 Building witness activity timeline...")
    witnesses = build_witness_activity(conn)
    print(render_witness_heatmap(witnesses))
    
    # 4. Gap analysis
    print(f"\n{'─' * 60}")
    print(f"  EVIDENCE GAPS (months with <5 items)")
    print(f"{'─' * 60}")
    gaps = find_evidence_gaps(monthly)
    critical_gaps = [g for g in gaps if g['severity'] == 'CRITICAL']
    warning_gaps = [g for g in gaps if g['severity'] == 'WARNING']
    print(f"  CRITICAL (zero evidence): {len(critical_gaps)} months")
    for g in critical_gaps[:12]:
        print(f"    🔴 {g['month']}: NO evidence found")
    if len(critical_gaps) > 12:
        print(f"    ...and {len(critical_gaps) - 12} more")
    print(f"  WARNING (1-4 items): {len(warning_gaps)} months")
    for g in warning_gaps[:6]:
        print(f"    🟡 {g['month']}: only {g['count']} items")
    
    # 5. Summary stats
    total_evidence = sum(monthly.values())
    peak_month = max(monthly.items(), key=lambda x: x[1]) if monthly else ('N/A', 0)
    
    print(f"\n{'─' * 60}")
    print(f"  SUMMARY")
    print(f"{'─' * 60}")
    print(f"  Total evidence items with dates: {total_evidence:,}")
    print(f"  Peak month: {peak_month[0]} ({peak_month[1]:,} items)")
    print(f"  Months covered: {len([v for v in monthly.values() if v > 0])}")
    print(f"  Evidence gaps (critical): {len(critical_gaps)}")
    print(f"  Evidence gaps (warning): {len(warning_gaps)}")
    print(f"  Top category: {max(categories.items(), key=lambda x: x[1])[0] if categories else 'N/A'}")
    print(f"  Witnesses tracked: {len(witnesses)}")
    
    # Save reports
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        'generated': datetime.now().isoformat(),
        'timeline': dict(monthly),
        'categories': dict(categories),
        'gaps': gaps,
        'witness_totals': {w: sum(m.values()) for w, m in witnesses.items()},
        'summary': {
            'total_dated_evidence': total_evidence,
            'peak_month': peak_month[0],
            'peak_count': peak_month[1],
            'months_covered': len([v for v in monthly.values() if v > 0]),
            'critical_gaps': len(critical_gaps),
            'warning_gaps': len(warning_gaps),
        }
    }
    
    report_path = REPORT_DIR / "evidence_heatmap.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved: {report_path}")
    
    conn.close()


if __name__ == '__main__':
    main()
