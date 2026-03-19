#!/usr/bin/env python3
"""
Tool #212 — Evidence Timeline Generator
Builds a comprehensive chronological timeline from litigation_context.db.
Queries all date-bearing tables, cross-references events, flags turning points.
Output: EVIDENCE_TIMELINE.md + EVIDENCE_TIMELINE.json
"""
import sys, os, json, sqlite3, re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOLS_DIR.parent.parent
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATE_PATTERN = re.compile(r'\b(20[12]\d[-/]\d{1,2}[-/]\d{1,2})\b')
TURNING_POINTS = {
    "PPO": ["ppo", "personal protection", "protection order"],
    "Custody Order": ["custody", "legal custody", "physical custody"],
    "Parenting Time": ["parenting time", "visitation", "suspended"],
    "Ex Parte": ["ex parte", "emergency", "without notice"],
    "Attorney Withdrawal": ["withdrawal", "withdrew", "barnes"],
    "CPS/DHHS": ["cps", "dhhs", "protective services", "child abuse"],
    "Contempt": ["contempt", "violation", "non-compliance"],
    "FOC": ["friend of court", "foc", "rusco"],
}


def get_db_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row
    return conn


def get_tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts_%'").fetchall()
    return [r[0] for r in rows]


def normalize_date(date_str):
    """Try to parse a date string into YYYY-MM-DD format."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(date_str[:19], fmt).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            continue
    match = DATE_PATTERN.search(date_str)
    if match:
        extracted = match.group(1)
        if extracted != date_str:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
                try:
                    return datetime.strptime(extracted, fmt).strftime("%Y-%m-%d")
                except (ValueError, IndexError):
                    continue
    return None


def classify_event(text):
    """Classify an event into turning-point categories."""
    categories = []
    text_lower = (text or "").lower()
    for category, keywords in TURNING_POINTS.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(category)
    return categories if categories else ["General"]


def extract_events_from_table(conn, table_name):
    """Extract dated events from any table."""
    events = []
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]
    except Exception:
        return events

    date_cols = [c for c in cols if any(d in c.lower() for d in ["date", "created", "timestamp", "time", "when", "filed"])]
    text_cols = [c for c in cols if any(t in c.lower() for t in ["text", "description", "title", "name", "event",
                                                                   "quote", "content", "summary", "detail", "note",
                                                                   "significance", "type", "category", "status"])]
    if not date_cols:
        return events

    for dc in date_cols:
        select_cols = [dc] + [tc for tc in text_cols if tc != dc]
        if not select_cols:
            continue
        col_str = ", ".join(f'"{c}"' for c in select_cols)
        try:
            rows = conn.execute(f'SELECT {col_str} FROM "{table_name}" WHERE "{dc}" IS NOT NULL LIMIT 1000').fetchall()
        except Exception:
            continue

        for row in rows:
            raw_date = row[0]
            norm_date = normalize_date(raw_date)
            if not norm_date:
                continue
            text_parts = [str(row[i]) for i in range(1, len(select_cols)) if row[i]]
            description = " | ".join(text_parts)[:500] if text_parts else f"[{table_name} entry]"
            categories = classify_event(description)
            events.append({
                "date": norm_date,
                "source_table": table_name,
                "description": description,
                "categories": categories,
                "is_turning_point": categories != ["General"],
                "raw_date": str(raw_date),
            })
    return events


def extract_dates_from_evidence_quotes(conn):
    """Special extraction for evidence_quotes with date_ref field."""
    events = []
    try:
        rows = conn.execute("""
            SELECT date_ref, quote_text, evidence_category, speaker, legal_significance
            FROM evidence_quotes
            WHERE date_ref IS NOT NULL AND date_ref != ''
            LIMIT 2000
        """).fetchall()
    except Exception:
        return events

    for r in rows:
        norm_date = normalize_date(r[0])
        if not norm_date:
            continue
        desc_parts = []
        if r[2]:
            desc_parts.append(f"[{r[2]}]")
        if r[3]:
            desc_parts.append(f"({r[3]})")
        if r[1]:
            desc_parts.append(str(r[1])[:300])
        if r[4]:
            desc_parts.append(f"Significance: {r[4]}")
        description = " ".join(desc_parts)
        categories = classify_event(description)
        events.append({
            "date": norm_date,
            "source_table": "evidence_quotes",
            "description": description,
            "categories": categories,
            "is_turning_point": categories != ["General"],
            "raw_date": str(r[0]),
        })
    return events


def calculate_gaps(events):
    """Calculate days between consecutive events."""
    if len(events) < 2:
        return events
    for i in range(1, len(events)):
        try:
            d1 = datetime.strptime(events[i - 1]["date"], "%Y-%m-%d")
            d2 = datetime.strptime(events[i]["date"], "%Y-%m-%d")
            events[i]["days_since_previous"] = (d2 - d1).days
        except (ValueError, KeyError):
            events[i]["days_since_previous"] = None
    return events


def main():
    print("=" * 70)
    print("TOOL #212 — Evidence Timeline Generator")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = get_db_connection()
    if not conn:
        print("[ERROR] Database not found at", DB_PATH)
        return

    tables = get_tables(conn)
    print(f"[DB] {len(tables)} tables available.")

    all_events = []

    # Special handling for evidence_quotes
    if "evidence_quotes" in tables:
        eq_events = extract_dates_from_evidence_quotes(conn)
        all_events.extend(eq_events)
        print(f"  evidence_quotes: {len(eq_events)} dated events")

    # Scan all other tables for date columns
    for table in tables:
        if table == "evidence_quotes":
            continue
        events = extract_events_from_table(conn, table)
        if events:
            all_events.extend(events)
            print(f"  {table}: {len(events)} dated events")

    conn.close()

    # Deduplicate by (date, description[:100])
    seen = set()
    unique_events = []
    for e in all_events:
        key = (e["date"], e["description"][:100])
        if key not in seen:
            seen.add(key)
            unique_events.append(e)

    # Sort chronologically
    unique_events.sort(key=lambda x: x["date"])
    unique_events = calculate_gaps(unique_events)

    # Categorize
    turning_points = [e for e in unique_events if e["is_turning_point"]]
    by_category = defaultdict(list)
    for e in unique_events:
        for cat in e["categories"]:
            by_category[cat].append(e)

    # Date range
    date_range = {}
    if unique_events:
        date_range = {
            "earliest": unique_events[0]["date"],
            "latest": unique_events[-1]["date"],
            "span_days": (datetime.strptime(unique_events[-1]["date"], "%Y-%m-%d") -
                          datetime.strptime(unique_events[0]["date"], "%Y-%m-%d")).days,
        }

    print(f"\n[TIMELINE] {len(unique_events)} unique events extracted")
    print(f"  Turning points: {len(turning_points)}")
    print(f"  Date range: {date_range.get('earliest', 'N/A')} to {date_range.get('latest', 'N/A')}")
    if date_range:
        print(f"  Span: {date_range.get('span_days', 0)} days")

    # JSON report
    report = {
        "tool": "#212 — Evidence Timeline Generator",
        "generated": datetime.now().isoformat(),
        "total_events": len(unique_events),
        "turning_points_count": len(turning_points),
        "date_range": date_range,
        "category_counts": {k: len(v) for k, v in by_category.items()},
        "source_table_counts": dict(defaultdict(int, {e["source_table"]: 0 for e in unique_events})),
        "events": unique_events[:500],
        "turning_points": turning_points[:100],
    }
    # Fix source counts
    src_counts = defaultdict(int)
    for e in unique_events:
        src_counts[e["source_table"]] += 1
    report["source_table_counts"] = dict(src_counts)

    json_path = REPORTS_DIR / "EVIDENCE_TIMELINE.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[OK] JSON: {json_path}")

    # MD report
    md = []
    md.append("# EVIDENCE TIMELINE — Pigors v. Watson")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Total Events:** {len(unique_events)}")
    md.append(f"**Turning Points:** {len(turning_points)}")
    if date_range:
        md.append(f"**Date Range:** {date_range['earliest']} to {date_range['latest']} ({date_range['span_days']} days)")
    md.append("")

    # Category summary
    md.append("## Event Categories")
    md.append("")
    md.append("| Category | Count |")
    md.append("|----------|-------|")
    for cat, evts in sorted(by_category.items(), key=lambda x: -len(x[1])):
        md.append(f"| {cat} | {len(evts)} |")
    md.append("")

    # Source table summary
    md.append("## Source Tables")
    md.append("")
    md.append("| Table | Events |")
    md.append("|-------|--------|")
    for src, count in sorted(src_counts.items(), key=lambda x: -x[1]):
        md.append(f"| {src} | {count} |")
    md.append("")

    # Turning points
    if turning_points:
        md.append("## Key Turning Points")
        md.append("")
        for tp in turning_points[:50]:
            cats = ", ".join(tp["categories"])
            md.append(f"- **{tp['date']}** [{cats}] — {tp['description'][:200]}")
        md.append("")

    # Full chronological timeline (capped)
    md.append("## Chronological Timeline")
    md.append("")
    for e in unique_events[:200]:
        marker = " :star:" if e["is_turning_point"] else ""
        gap = f" (+{e.get('days_since_previous', '?')}d)" if e.get("days_since_previous") else ""
        md.append(f"- **{e['date']}**{gap}{marker} [{e['source_table']}] {e['description'][:250]}")
    if len(unique_events) > 200:
        md.append(f"\n*... {len(unique_events) - 200} additional events in JSON report ...*")
    md.append("")

    md.append("---")
    md.append(f"\n*Tool #212 — Evidence Timeline Generator — {datetime.now().isoformat()}*")

    md_path = REPORTS_DIR / "EVIDENCE_TIMELINE.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] MD:   {md_path}")
    print("[DONE] Tool #212 complete.")


if __name__ == "__main__":
    main()
