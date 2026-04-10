"""P3E Timeline Enrichment — Mine 5 tables for undiscovered timeline events.

Sources:
  1. judicial_violations (308 dated) -> lane E
  2. impeachment_matrix (57 dated) -> lane by category
  3. berry_mcneill_intelligence (222) -> lane E
  4. evidence_quotes (high relevance, recent) -> lane by lane col
  5. police_reports full_text -> lane D/A via date extraction

Target: 16.9K -> 20K+ events
"""
import sqlite3
import re
import json
import sys
from datetime import datetime, date
from pathlib import Path

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# ── Date extraction patterns ────────────────────────────────────
DATE_PATTERNS = [
    # ISO: 2025-08-07
    (re.compile(r'\b(20[12]\d)-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b'), 'iso'),
    # US: 08/07/2025 or 8/7/2025
    (re.compile(r'\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(20[12]\d)\b'), 'us'),
    # Written: August 7, 2025  or  Aug 7, 2025
    (re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(20[12]\d)\b', re.I), 'written'),
]

MONTH_MAP = {
    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
    'november': 11, 'nov': 11, 'december': 12, 'dec': 12,
}

def parse_date(text):
    """Extract first valid date from text. Returns ISO string or None."""
    if not text:
        return None
    for pat, fmt in DATE_PATTERNS:
        m = pat.search(str(text))
        if m:
            try:
                if fmt == 'iso':
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                elif fmt == 'us':
                    mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                elif fmt == 'written':
                    mo = MONTH_MAP.get(m.group(1).lower(), 0)
                    d, y = int(m.group(2)), int(m.group(3))
                else:
                    continue
                if 2020 <= y <= 2026 and 1 <= mo <= 12 and 1 <= d <= 31:
                    return f"{y:04d}-{mo:02d}-{d:02d}"
            except (ValueError, IndexError):
                continue
    return None


def extract_dates_from_json_list(json_str):
    """Parse JSON list of date strings, return list of ISO dates."""
    if not json_str or json_str == '[]':
        return []
    try:
        items = json.loads(json_str) if isinstance(json_str, str) else json_str
    except (json.JSONDecodeError, TypeError):
        return []
    results = []
    for item in items:
        d = parse_date(str(item))
        if d:
            results.append(d)
    return results


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row
    return conn


def get_existing_fingerprints(conn):
    """Build a set of (date, desc_prefix) tuples for dedup."""
    fps = set()
    rows = conn.execute(
        "SELECT event_date, event_description FROM timeline_events WHERE event_date IS NOT NULL"
    ).fetchall()
    for r in rows:
        d = r['event_date']
        desc = (r['event_description'] or '')[:80].lower().strip()
        if d and desc:
            fps.add((d[:10], desc))
    return fps


def is_duplicate(fps, event_date, desc):
    """Check if event already exists (date + first 80 chars of desc)."""
    if not event_date or not desc:
        return True
    key = (event_date[:10], desc[:80].lower().strip())
    return key in fps


def truncate(text, maxlen=500):
    if not text:
        return ''
    t = str(text).strip()
    return t[:maxlen] if len(t) > maxlen else t


# ── Source 1: judicial_violations ────────────────────────────────
def mine_judicial_violations(conn, fps):
    """Extract dated judicial violations not yet in timeline."""
    new_events = []
    rows = conn.execute("""
        SELECT id, violation_type, description, date_occurred, mcr_rule, severity, lane, source_quote
        FROM judicial_violations
        WHERE date_occurred IS NOT NULL AND LENGTH(date_occurred) >= 8
    """).fetchall()

    for r in rows:
        d = parse_date(r['date_occurred'])
        if not d:
            continue
        vtype = r['violation_type'] or 'judicial_violation'
        desc_parts = [f"Judicial violation ({vtype})"]
        if r['description']:
            desc_parts.append(truncate(r['description'], 300))
        if r['mcr_rule']:
            desc_parts.append(f"[{r['mcr_rule']}]")
        desc = ': '.join(desc_parts)

        if is_duplicate(fps, d, desc):
            continue

        sev = 5
        try:
            sev = max(1, min(10, int(r['severity'] or 5)))
        except (ValueError, TypeError):
            pass

        new_events.append((
            d, desc, 'Hon. Jenny L. McNeill',
            r['lane'] or 'E', 'Judicial_Violation',
            'judicial_violations', str(r['id']),
            str(sev), f"Lane {r['lane'] or 'E'}"
        ))
        fps.add((d[:10], desc[:80].lower().strip()))

    return new_events


# ── Source 2: impeachment_matrix ─────────────────────────────────
def mine_impeachment_matrix(conn, fps):
    """Extract dated impeachment entries not yet in timeline."""
    new_events = []
    rows = conn.execute("""
        SELECT id, category, evidence_summary, event_date, impeachment_value, filing_relevance
        FROM impeachment_matrix
        WHERE event_date IS NOT NULL AND event_date != '' AND LENGTH(event_date) >= 6
    """).fetchall()

    for r in rows:
        d = parse_date(r['event_date'])
        if not d:
            continue
        cat = r['category'] or 'impeachment'
        desc = f"Impeachment ({cat}): {truncate(r['evidence_summary'], 350)}"

        if is_duplicate(fps, d, desc):
            continue

        sev = 5
        try:
            sev = max(1, min(10, int(r['impeachment_value'] or 5)))
        except (ValueError, TypeError):
            pass

        # Guess lane from category/filing_relevance
        lane = 'A'
        fr = (r['filing_relevance'] or '').lower()
        if 'judicial' in fr or 'mcneill' in fr or 'bias' in fr:
            lane = 'E'
        elif 'ppo' in fr or 'contempt' in fr:
            lane = 'D'
        elif 'housing' in fr or 'shady' in fr:
            lane = 'B'
        elif 'federal' in fr or '1983' in fr:
            lane = 'C'
        elif 'appeal' in fr or 'coa' in fr:
            lane = 'F'

        new_events.append((
            d, desc, '',
            lane, 'Impeachment',
            'impeachment_matrix', str(r['id']),
            str(sev), f"Lane {lane}"
        ))
        fps.add((d[:10], desc[:80].lower().strip()))

    return new_events


# ── Source 3: berry_mcneill_intelligence ─────────────────────────
def mine_cartel_intel(conn, fps):
    """Extract cartel intelligence entries as timeline events."""
    new_events = []
    rows = conn.execute("""
        SELECT id, connection_type, person_a, person_b, relationship, evidence_source,
               confidence, notes, discovered_at
        FROM berry_mcneill_intelligence
        WHERE discovered_at IS NOT NULL
    """).fetchall()

    for r in rows:
        d = parse_date(r['discovered_at'])
        if not d:
            continue
        ctype = r['connection_type'] or 'connection'
        pa = r['person_a'] or 'Unknown'
        pb = r['person_b'] or 'Unknown'
        rel = r['relationship'] or ''
        desc = f"Cartel intel ({ctype}): {pa} <-> {pb}"
        if rel:
            desc += f" - {truncate(rel, 200)}"

        if is_duplicate(fps, d, desc):
            continue

        conf = 5
        try:
            cf = float(r['confidence'] or 0.5)
            conf = max(1, min(10, int(cf * 10)))
        except (ValueError, TypeError):
            pass

        actors = f"{pa}, {pb}"
        new_events.append((
            d, desc, actors,
            'E', 'Cartel_Intelligence',
            'berry_mcneill_intelligence', str(r['id']),
            str(conf), 'Lane E'
        ))
        fps.add((d[:10], desc[:80].lower().strip()))

    return new_events


# ── Source 4: evidence_quotes (high relevance, recent KAL) ──────
def mine_evidence_quotes(conn, fps):
    """Mine high-relevance evidence quotes for date-extractable timeline events."""
    new_events = []

    # Focus on high-relevance recent entries
    rows = conn.execute("""
        SELECT id, source_file, quote_text, category, lane, relevance_score, tags, created_at
        FROM evidence_quotes
        WHERE relevance_score >= 0.6
          AND is_duplicate = 0
          AND quote_text IS NOT NULL
          AND LENGTH(quote_text) > 50
        ORDER BY relevance_score DESC
        LIMIT 5000
    """).fetchall()

    for r in rows:
        qt = r['quote_text'] or ''
        d = parse_date(qt)
        if not d:
            # Try source_file for date hints
            d = parse_date(r['source_file'] or '')
        if not d:
            continue

        cat = r['category'] or 'Evidence'
        lane = r['lane'] or 'A'
        desc = f"Evidence ({cat}): {truncate(qt, 350)}"

        if is_duplicate(fps, d, desc):
            continue

        sev = 5
        try:
            sev = max(1, min(10, int(float(r['relevance_score'] or 0.5) * 10)))
        except (ValueError, TypeError):
            pass

        new_events.append((
            d, desc, '',
            lane, 'Evidence',
            'evidence_quotes', str(r['id']),
            str(sev), f"Lane {lane}"
        ))
        fps.add((d[:10], desc[:80].lower().strip()))

    return new_events


# ── Source 5: police_reports full_text ───────────────────────────
def mine_police_reports(conn, fps):
    """Mine police report full text for dated events."""
    new_events = []

    # Only actual police reports (not file maps, inventories, etc.)
    rows = conn.execute("""
        SELECT id, filename, full_text, dates, incident_numbers, officers,
               allegations, exculpatory, key_quotes
        FROM police_reports
        WHERE full_text IS NOT NULL AND LENGTH(full_text) > 200
          AND (filename LIKE '%nspd%' OR filename LIKE '%police%' OR filename LIKE '%report%'
               OR filename LIKE '%incident%' OR filename LIKE '%NS2%')
        LIMIT 100
    """).fetchall()

    for r in rows:
        ft = r['full_text'] or ''
        fname = r['filename'] or ''

        # Extract all dates from the report
        dates_found = []
        for pat, fmt in DATE_PATTERNS:
            for m in pat.finditer(ft[:10000]):  # First 10K chars
                try:
                    if fmt == 'iso':
                        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    elif fmt == 'us':
                        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    elif fmt == 'written':
                        mo = MONTH_MAP.get(m.group(1).lower(), 0)
                        d, y = int(m.group(2)), int(m.group(3))
                    else:
                        continue
                    if 2020 <= y <= 2026 and 1 <= mo <= 12 and 1 <= d <= 31:
                        iso = f"{y:04d}-{mo:02d}-{d:02d}"
                        # Get surrounding context (100 chars around match)
                        start = max(0, m.start() - 80)
                        end = min(len(ft), m.end() + 150)
                        ctx = ft[start:end].replace('\n', ' ').strip()
                        dates_found.append((iso, ctx))
                except (ValueError, IndexError):
                    continue

        # Also try JSON dates column
        json_dates = extract_dates_from_json_list(r['dates'])
        for jd in json_dates:
            if jd not in [df[0] for df in dates_found]:
                dates_found.append((jd, f"Police report date from {fname}"))

        # Create events from extracted dates
        for event_date, context in dates_found:
            desc = f"Police report ({fname}): {truncate(context, 350)}"

            if is_duplicate(fps, event_date, desc):
                continue

            # Determine lane: if PPO/contempt -> D, custody -> A, default A
            lane = 'A'
            ctx_lower = context.lower()
            if any(kw in ctx_lower for kw in ['ppo', 'protection order', 'contempt', 'stalking']):
                lane = 'D'
            elif any(kw in ctx_lower for kw in ['judicial', 'mcneill', 'judge', 'court order']):
                lane = 'E'
            elif any(kw in ctx_lower for kw in ['shady oaks', 'eviction', 'housing']):
                lane = 'B'

            new_events.append((
                event_date, desc, '',
                lane, 'Police/Agency',
                'police_reports', str(r['id']),
                '5', f"Lane {lane}"
            ))
            fps.add((event_date[:10], desc[:80].lower().strip()))

    return new_events


def main():
    print("=" * 70)
    print("P3E TIMELINE ENRICHMENT — Mining 5 tables for undiscovered events")
    print("=" * 70)

    conn = get_conn()

    # Current baseline
    baseline = conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
    print(f"\nBaseline: {baseline:,} timeline events")

    # Build dedup fingerprints
    print("Building dedup fingerprint index...")
    fps = get_existing_fingerprints(conn)
    print(f"  {len(fps):,} existing fingerprints loaded")

    # Mine all 5 sources
    all_new = []

    print("\n[1/5] Mining judicial_violations (308 dated)...")
    jv = mine_judicial_violations(conn, fps)
    print(f"  -> {len(jv)} new events extracted")
    all_new.extend(jv)

    print("\n[2/5] Mining impeachment_matrix (57 dated)...")
    im = mine_impeachment_matrix(conn, fps)
    print(f"  -> {len(im)} new events extracted")
    all_new.extend(im)

    print("\n[3/5] Mining berry_mcneill_intelligence (222 entries)...")
    ci = mine_cartel_intel(conn, fps)
    print(f"  -> {len(ci)} new events extracted")
    all_new.extend(ci)

    print("\n[4/5] Mining evidence_quotes (top 5000 by relevance)...")
    eq = mine_evidence_quotes(conn, fps)
    print(f"  -> {len(eq)} new events extracted")
    all_new.extend(eq)

    print("\n[5/5] Mining police_reports full_text...")
    pr = mine_police_reports(conn, fps)
    print(f"  -> {len(pr)} new events extracted")
    all_new.extend(pr)

    print(f"\n{'=' * 70}")
    print(f"TOTAL new events to insert: {len(all_new):,}")

    if not all_new:
        print("No new events found. Timeline already comprehensive.")
        conn.close()
        return

    # Insert in batches
    print(f"\nInserting {len(all_new):,} events...")
    inserted = 0
    batch_size = 500
    for i in range(0, len(all_new), batch_size):
        batch = all_new[i:i + batch_size]
        try:
            conn.executemany("""
                INSERT INTO timeline_events
                    (event_date, event_description, actors, lane, category,
                     source_table, source_id, severity, filing_relevance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            inserted += len(batch)
            print(f"  Batch {i // batch_size + 1}: {len(batch)} inserted (total: {inserted:,})")
        except Exception as e:
            print(f"  Batch {i // batch_size + 1} ERROR: {e}")
            conn.rollback()

    # Rebuild FTS5 if it exists
    try:
        conn.execute("INSERT INTO timeline_fts(timeline_fts) VALUES('rebuild')")
        conn.commit()
        print("\nFTS5 index rebuilt.")
    except Exception as e:
        print(f"\nFTS5 rebuild skipped: {e}")

    # Final count
    final = conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
    print(f"\n{'=' * 70}")
    print(f"RESULTS:")
    print(f"  Before: {baseline:,}")
    print(f"  Added:  {inserted:,}")
    print(f"  After:  {final:,}")
    print(f"  Growth: +{final - baseline:,} events ({(final - baseline) / max(baseline, 1) * 100:.1f}%)")

    # Lane distribution
    print(f"\nLane distribution (post-enrichment):")
    for row in conn.execute(
        "SELECT lane, COUNT(*) as cnt FROM timeline_events GROUP BY lane ORDER BY cnt DESC"
    ).fetchall():
        print(f"  {row['lane']}: {row['cnt']:,}")

    # Category distribution
    print(f"\nCategory distribution (post-enrichment):")
    for row in conn.execute(
        "SELECT category, COUNT(*) as cnt FROM timeline_events GROUP BY category ORDER BY cnt DESC LIMIT 15"
    ).fetchall():
        print(f"  {row['category']}: {row['cnt']:,}")

    conn.close()
    print(f"\n{'=' * 70}")
    print("P3E TIMELINE ENRICHMENT COMPLETE")


if __name__ == '__main__':
    main()
