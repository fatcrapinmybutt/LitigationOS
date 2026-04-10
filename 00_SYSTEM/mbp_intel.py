#!/usr/bin/env python3
"""SINGULARITY Intel Toolkit — Direct DuckDB/SQLite CLI (ZERO MCP)
═══════════════════════════════════════════════════════════════════
Replaces all MCP litigation_context-* tools and extension bridge calls
with direct exec_python invocations. DuckDB for analytics (10-100×),
SQLite for FTS5 search, zero middleware overhead.

Usage:
  python mbp_intel.py <command> [args...]

MANBEARPIG Commands:
  mbp-layers                        Layer stats (nodes/links per layer)
  mbp-data-quality                  Data quality across all 12 extraction phases
  mbp-evidence-heatmap              Evidence density by lane + category (DuckDB)
  mbp-weapon-chains [--type TYPE]   Weapon chain analysis

Judicial Universe Commands:
  jud-violations [--type TYPE]      Violation breakdown (DuckDB aggregation)
  jud-cartel [--person NAME]        Berry-McNeill cartel network
  jud-canons                        Canon violations with full text
  jud-chronology [--limit N]        Bias chronology timeline
  jud-severity                      Severity distribution heatmap (DuckDB)
  jud-ex-parte [--limit N]          Ex parte violations deep dive

Cross-Domain Commands:
  search <QUERY> [--table TABLE]    FTS5 search (sanitized, with fallback)
  fuse <TOPIC>                      Cross-table evidence fusion (5 sources)
  timeline [--from DATE] [--to DATE] [--actor NAME]
  impeach <TARGET> [--min-sev N]    Impeachment arsenal for target
  contradict <ENTITY>               Contradiction map for entity
  authority <CITATION>              Authority chain lookup
  stats                             Full system stats dashboard (DuckDB)
  dashboard                         Complete analytical dashboard
"""
import sys, os, re, json, sqlite3, argparse
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict

# ═══════════════ CONFIG ═══════════════
DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
SEP_DATE = date(2025, 7, 29)

# ═══════════════ CONNECTIONS ═══════════════
_sqlite_conn = None
_duck_conn = None

def get_sqlite():
    global _sqlite_conn
    if _sqlite_conn is None:
        _sqlite_conn = sqlite3.connect(str(DB))
        _sqlite_conn.execute("PRAGMA busy_timeout=60000")
        _sqlite_conn.execute("PRAGMA journal_mode=WAL")
        _sqlite_conn.execute("PRAGMA cache_size=-32000")
        _sqlite_conn.execute("PRAGMA temp_store=MEMORY")
        _sqlite_conn.row_factory = sqlite3.Row
    return _sqlite_conn

def get_duck():
    """DuckDB in-memory with SQLite scanner — 10-100× faster for analytics."""
    global _duck_conn
    if _duck_conn is None:
        import duckdb
        _duck_conn = duckdb.connect(":memory:")
        _duck_conn.execute("INSTALL sqlite; LOAD sqlite;")
        _duck_conn.execute("SET sqlite_all_varchar = true;")
        _duck_conn.execute(f"ATTACH '{DB}' AS lit (TYPE SQLITE, READ_ONLY);")
    return _duck_conn

def sep_days():
    return (date.today() - SEP_DATE).days

def sanitize_fts5(q):
    return re.sub(r'[^\w\s*"]', ' ', q).strip()

def fmt_row(vals, widths, align=None):
    """Format a row with column widths."""
    parts = []
    for i, (v, w) in enumerate(zip(vals, widths)):
        s = str(v) if v is not None else ""
        if align and i < len(align) and align[i] == '>':
            parts.append(s.rjust(w))
        else:
            parts.append(s.ljust(w))
    return "  " + "  ".join(parts)

def hdr(title):
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")

# ═══════════════════════════════════════════════════════════════
# MANBEARPIG COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_mbp_layers(args):
    """Layer statistics from the built graph data."""
    hdr("MANBEARPIG v7 — Layer Statistics")
    gj = Path(r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\graph_data_v7.json")
    if not gj.exists():
        print("  ✗ graph_data_v7.json not found — run `mbp_build.py data` first")
        return
    with open(gj) as f:
        meta = json.load(f)
    print(f"  Version:  {meta.get('version','?')}")
    print(f"  Renderer: {meta.get('renderer','?')}")
    print(f"  Nodes:    {meta.get('nodes',0):,}")
    print(f"  Links:    {meta.get('links',0):,}")
    print(f"  Layers:   {len(meta.get('layers',[]))}")
    layers = meta.get('layers', [])
    if layers:
        print(f"\n  {'Layer':<30s} {'Tier':<12s}")
        print(f"  {'─'*42}")
        tier_map = {
            'ADVERSARY_CORE': 'COMBAT', 'ADVERSARY_NET': 'COMBAT', 'JUDICIAL_CARTEL': 'COMBAT',
            'WEAPON_CHAINS': 'COMBAT', 'IMPEACHMENT': 'COMBAT', 'CONTRADICTIONS': 'COMBAT',
            'EVIDENCE_A': 'EVIDENCE', 'EVIDENCE_B': 'EVIDENCE', 'EVIDENCE_C': 'EVIDENCE',
            'EVIDENCE_D': 'EVIDENCE', 'EVIDENCE_E': 'EVIDENCE', 'EVIDENCE_F': 'EVIDENCE',
            'AUTHORITY': 'LEGAL', 'TIMELINE': 'TEMPORAL', 'FILING': 'FILING',
            'DAMAGES': 'FILING', 'POLICE': 'EVIDENCE', 'FACTS': 'FOUNDATION',
            'BIF': 'FOUNDATION', 'INTEL': 'INTELLIGENCE',
        }
        for layer in layers:
            tier = tier_map.get(layer, 'OTHER')
            print(f"  {layer:<30s} {tier:<12s}")

def cmd_mbp_data_quality(args):
    """Data quality check across all MBP extraction sources."""
    hdr("MANBEARPIG — Data Quality Audit (DuckDB)")
    d = get_duck()
    checks = [
        ("evidence_quotes",     "COUNT(*)", "COUNT(DISTINCT source_file)", "SUM(CASE WHEN lane IS NULL OR lane='' THEN 1 ELSE 0 END)"),
        ("authority_chains_v2", "COUNT(*)", "COUNT(DISTINCT primary_citation)", "SUM(CASE WHEN lane IS NULL OR lane='' THEN 1 ELSE 0 END)"),
        ("timeline_events",     "COUNT(*)", "COUNT(DISTINCT event_date)", "SUM(CASE WHEN event_date IS NULL OR CAST(event_date AS VARCHAR)='' THEN 1 ELSE 0 END)"),
        ("impeachment_matrix",  "COUNT(*)", "COUNT(DISTINCT category)", "SUM(CASE WHEN quote_text IS NULL OR CAST(quote_text AS VARCHAR)='' THEN 1 ELSE 0 END)"),
        ("contradiction_map",   "COUNT(*)", "COUNT(DISTINCT claim_id)", "SUM(CASE WHEN severity IS NULL OR severity='' THEN 1 ELSE 0 END)"),
        ("judicial_violations", "COUNT(*)", "COUNT(DISTINCT violation_type)", "SUM(CASE WHEN severity IS NULL THEN 1 ELSE 0 END)"),
        ("police_reports",      "COUNT(*)", "1", "0"),
    ]
    print(f"\n  {'Table':<26s} {'Rows':>10s} {'Distinct':>10s} {'Gaps':>8s} {'Quality':>8s}")
    print(f"  {'─'*64}")
    for tbl, cnt_q, dist_q, gap_q in checks:
        try:
            row = d.execute(f"SELECT {cnt_q}, {dist_q}, {gap_q} FROM lit.{tbl}").fetchone()
            total, distinct, gaps = int(row[0]), int(row[1]), int(row[2])
            quality = max(0, 100 - (gaps * 100 // max(total, 1)))
            bar = "█" * (quality // 10) + "░" * (10 - quality // 10)
            print(f"  {tbl:<26s} {total:>10,} {distinct:>10,} {gaps:>8,} {bar} {quality}%")
        except Exception as e:
            print(f"  {tbl:<26s} {'ERROR':>10s} — {e}")

def cmd_mbp_evidence_heatmap(args):
    """Evidence density heatmap by lane + category (DuckDB)."""
    hdr("Evidence Heatmap (DuckDB Analytics)")
    d = get_duck()
    rows = d.execute("""
        SELECT COALESCE(lane,'?') as lane, COALESCE(category,'?') as cat,
               COUNT(*) as cnt, COUNT(DISTINCT source_file) as srcs
        FROM lit.evidence_quotes
        GROUP BY lane, category ORDER BY cnt DESC LIMIT 30
    """).fetchall()
    print(f"\n  {'Lane':<8s} {'Category':<30s} {'Count':>8s} {'Sources':>8s}")
    print(f"  {'─'*56}")
    for r in rows:
        print(f"  {r[0]:<8s} {str(r[1])[:29]:<30s} {int(r[2]):>8,} {int(r[3]):>8,}")

def cmd_mbp_weapon_chains(args):
    """Weapon chain analysis."""
    hdr("Weapon Chain Analysis (DuckDB)")
    d = get_duck()
    wtype = getattr(args, 'type', None)
    where = f"WHERE LOWER(CAST(weapon_type AS VARCHAR)) LIKE LOWER('%{wtype}%')" if wtype else ""
    try:
        rows = d.execute(f"""
            SELECT COALESCE(weapon_type,'?') as wt, COUNT(*) cnt,
                   ROUND(AVG(CAST(severity AS DOUBLE)),1) avg_sev
            FROM lit.weapon_chains {where}
            GROUP BY weapon_type ORDER BY cnt DESC
        """).fetchall()
        print(f"\n  {'Weapon Type':<35s} {'Count':>7s} {'Avg Sev':>8s}")
        print(f"  {'─'*52}")
        for r in rows:
            print(f"  {str(r[0])[:34]:<35s} {int(r[1]):>7,} {r[2]:>8}")
    except Exception as e:
        print(f"  weapon_chains table: {e}")

# ═══════════════════════════════════════════════════════════════
# JUDICIAL UNIVERSE COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_jud_violations(args):
    """Judicial violation breakdown (DuckDB aggregation)."""
    hdr(f"Judicial Violations — Separation Day {sep_days()}")
    d = get_duck()
    vtype = getattr(args, 'type', None)
    where = f"WHERE LOWER(CAST(violation_type AS VARCHAR)) = LOWER('{vtype}')" if vtype else ""

    # Aggregate by type
    rows = d.execute(f"""
        SELECT COALESCE(violation_type,'?') vt, COUNT(*) cnt,
               ROUND(AVG(CAST(severity AS DOUBLE)),1) avg_sev,
               MAX(CAST(severity AS INT)) max_sev,
               COUNT(DISTINCT source_file) srcs
        FROM lit.judicial_violations {where}
        GROUP BY violation_type ORDER BY cnt DESC
    """).fetchall()
    total = sum(int(r[1]) for r in rows)
    print(f"\n  Total violations: {total:,}")
    print(f"\n  {'Type':<26s} {'Count':>7s} {'%':>6s} {'AvgSev':>7s} {'MaxSev':>7s} {'Sources':>8s}")
    print(f"  {'─'*63}")
    for r in rows:
        pct = int(r[1]) * 100.0 / max(total, 1)
        print(f"  {str(r[0])[:25]:<26s} {int(r[1]):>7,} {pct:>5.1f}% {r[2]:>7} {int(r[3]):>7} {int(r[4]):>8,}")

    if not vtype:
        # Severity distribution
        sev_rows = d.execute("""
            SELECT CAST(severity AS INT) s, COUNT(*) cnt
            FROM lit.judicial_violations WHERE severity IS NOT NULL
            GROUP BY s ORDER BY s
        """).fetchall()
        print(f"\n  Severity Distribution:")
        for s, cnt in sev_rows:
            bar = "█" * max(1, cnt // 20)
            print(f"    Sev {int(s):>2d}: {bar} {int(cnt)}")

def cmd_jud_cartel(args):
    """Berry-McNeill judicial cartel intelligence network."""
    hdr("Berry-McNeill Cartel Intelligence")
    d = get_duck()
    person = getattr(args, 'person', None)
    where = ""
    if person:
        where = f"WHERE LOWER(CAST(person_a AS VARCHAR)) LIKE LOWER('%{person}%') OR LOWER(CAST(person_b AS VARCHAR)) LIKE LOWER('%{person}%')"

    rows = d.execute(f"""
        SELECT person_a, person_b, connection_type, relationship, evidence_source, confidence
        FROM lit.berry_mcneill_intelligence {where}
        ORDER BY connection_type, person_a
    """).fetchall()
    print(f"\n  {len(rows)} connections found")
    # Group by connection type
    by_type = defaultdict(list)
    for r in rows:
        by_type[str(r[2])].append(r)
    for ct, conns in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"\n  ┌─ {ct} ({len(conns)})")
        for c in conns:
            conf = f"[{c[5]}]" if c[5] else ""
            print(f"  │  {str(c[0]):>20s} ↔ {str(c[1]):<20s} {conf}")
            if c[3]:
                print(f"  │  {'':>20s}    {str(c[3])[:60]}")

def cmd_jud_canons(args):
    """Michigan Judicial Canon violations."""
    hdr("Michigan Judicial Canon Violations")
    c = get_sqlite()
    rows = c.execute("""
        SELECT canon_number, title, violation_type, LENGTH(full_text) as tlen
        FROM michigan_judicial_canons ORDER BY canon_number
    """).fetchall()
    for r in rows:
        print(f"  Canon {r['canon_number']}: {r['title']}")
        print(f"    Violation type: {r['violation_type']} | Text: {r['tlen']:,} chars")

def cmd_jud_chronology(args):
    """Judicial bias chronology timeline."""
    hdr("Judicial Bias Chronology")
    limit = getattr(args, 'limit', 30) or 30
    d = get_duck()
    rows = d.execute(f"""
        SELECT date, event_description, canon_violated, severity,
               mcr_violation, filing_relevance
        FROM lit.judicial_bias_chronology
        WHERE date IS NOT NULL AND CAST(date AS VARCHAR) != ''
        ORDER BY CAST(date AS VARCHAR) DESC
        LIMIT {int(limit)}
    """).fetchall()
    print(f"\n  {'Date':<12s} {'Sev':>4s} {'Canon':<12s} {'MCR':<12s} {'Event':<50s}")
    print(f"  {'─'*92}")
    for r in rows:
        print(f"  {str(r[0])[:11]:<12s} {str(r[3]):>4s} {str(r[2] or '')[:11]:<12s} {str(r[4] or '')[:11]:<12s} {str(r[1] or '')[:50]}")

def cmd_jud_severity(args):
    """Severity distribution heatmap across all violation types (DuckDB)."""
    hdr("Judicial Violation Severity Heatmap (DuckDB)")
    d = get_duck()
    rows = d.execute("""
        SELECT COALESCE(violation_type,'?') vt,
               CAST(severity AS INT) sev, COUNT(*) cnt
        FROM lit.judicial_violations
        WHERE severity IS NOT NULL
        GROUP BY violation_type, severity
        ORDER BY violation_type, severity
    """).fetchall()
    # Pivot: type → {severity: count}
    matrix = defaultdict(lambda: defaultdict(int))
    all_sevs = set()
    for vt, sev, cnt in rows:
        matrix[str(vt)][int(sev)] = int(cnt)
        all_sevs.add(int(sev))
    sevs = sorted(all_sevs)
    header = f"  {'Type':<26s}" + "".join(f"{s:>6d}" for s in sevs) + f"{'Total':>8s}"
    print(f"\n{header}")
    print(f"  {'─'*(26 + 6*len(sevs) + 8)}")
    for vt in sorted(matrix.keys()):
        line = f"  {vt[:25]:<26s}"
        total = 0
        for s in sevs:
            c = matrix[vt][s]
            total += c
            line += f"{c:>6d}" if c else f"{'·':>6s}"
        line += f"{total:>8d}"
        print(line)

def cmd_jud_ex_parte(args):
    """Deep dive into ex parte violations."""
    hdr("Ex Parte Violations — Deep Dive")
    limit = getattr(args, 'limit', 20) or 20
    d = get_duck()
    # Summary
    row = d.execute("""
        SELECT COUNT(*) total, ROUND(AVG(CAST(severity AS DOUBLE)),1) avg_s,
               COUNT(DISTINCT source_file) srcs,
               MIN(CAST(date_occurred AS VARCHAR)) earliest,
               MAX(CAST(date_occurred AS VARCHAR)) latest
        FROM lit.judicial_violations
        WHERE LOWER(CAST(violation_type AS VARCHAR)) LIKE '%ex_parte%'
           OR LOWER(CAST(violation_type AS VARCHAR)) LIKE '%ex parte%'
    """).fetchone()
    print(f"\n  Total: {int(row[0]):,} | Avg severity: {row[1]} | Sources: {int(row[2])}")
    print(f"  Range: {row[3]} → {row[4]}")
    # Recent high-severity
    rows = d.execute(f"""
        SELECT date_occurred, description, severity, source_file
        FROM lit.judicial_violations
        WHERE (LOWER(CAST(violation_type AS VARCHAR)) LIKE '%ex_parte%'
           OR LOWER(CAST(violation_type AS VARCHAR)) LIKE '%ex parte%')
          AND CAST(severity AS INT) >= 7
        ORDER BY CAST(date_occurred AS VARCHAR) DESC
        LIMIT {int(limit)}
    """).fetchall()
    print(f"\n  High-Severity Ex Parte ({len(rows)} shown, sev≥7):")
    print(f"  {'─'*80}")
    for r in rows:
        d_str = str(r[0])[:10] if r[0] else "?"
        desc = str(r[1])[:70] if r[1] else ""
        print(f"  [{r[2]}] {d_str}  {desc}")

# ═══════════════════════════════════════════════════════════════
# CROSS-DOMAIN COMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_search(args):
    """FTS5 search with sanitization + LIKE fallback across any table."""
    query = args.query
    table = getattr(args, 'table', 'evidence_quotes') or 'evidence_quotes'
    hdr(f"Search: '{query}' in {table}")

    fts_map = {
        'evidence_quotes': ('evidence_fts', 'quote_text'),
        'timeline_events': ('timeline_fts', 'event_description'),
        'judicial_violations': ('judicial_violations_fts', 'description'),
    }
    c = get_sqlite()
    clean = sanitize_fts5(query)
    results = []

    if table in fts_map:
        fts_tbl, col = fts_map[table]
        try:
            rows = c.execute(
                f"SELECT rowid, {col} FROM {fts_tbl} WHERE {fts_tbl} MATCH ? LIMIT 25",
                (clean,)
            ).fetchall()
            results = [(r[0], r[1]) for r in rows]
        except Exception:
            pass

    if not results:
        # LIKE fallback
        col_map = {
            'evidence_quotes': 'quote_text',
            'timeline_events': 'event_description',
            'judicial_violations': 'description',
            'impeachment_matrix': 'evidence_summary',
            'contradiction_map': 'contradiction_text',
            'berry_mcneill_intelligence': 'relationship',
            'police_reports': 'report_text',
        }
        col = col_map.get(table, 'description')
        try:
            # Verify column exists
            cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
            if col not in cols:
                col = next((c for c in cols if c not in ('id','created_at','rowid')), None)
            if col:
                rows = c.execute(
                    f"SELECT id, {col} FROM [{table}] WHERE {col} LIKE ? LIMIT 25",
                    (f"%{query}%",)
                ).fetchall()
                results = [(r[0], r[1]) for r in rows]
                if results:
                    print(f"  (LIKE fallback — FTS5 unavailable for {table})")
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n  {len(results)} results:")
    for rid, text in results:
        txt = str(text or "")[:100]
        print(f"  [{rid}] {txt}")

def cmd_fuse(args):
    """Cross-table evidence fusion — search 5 sources simultaneously."""
    topic = args.topic
    hdr(f"Evidence Fusion: '{topic}'")
    c = get_sqlite()
    clean = sanitize_fts5(topic)

    sources = [
        ("evidence_quotes", "evidence_fts", "quote_text", "lane"),
        ("timeline_events", "timeline_fts", "event_description", "lane"),
    ]
    like_sources = [
        ("impeachment_matrix", "evidence_summary", "target"),
        ("contradiction_map", "contradiction_text", "severity"),
        ("judicial_violations", "description", "violation_type"),
    ]

    total = 0
    for tbl, fts, col, extra in sources:
        try:
            rows = c.execute(
                f"SELECT rowid, {col}, {extra} FROM {fts} WHERE {fts} MATCH ? LIMIT 10",
                (clean,)
            ).fetchall()
        except Exception:
            rows = c.execute(
                f"SELECT id, {col}, {extra} FROM [{tbl}] WHERE {col} LIKE ? LIMIT 10",
                (f"%{topic}%",)
            ).fetchall()
        if rows:
            print(f"\n  ┌─ {tbl} ({len(rows)} hits)")
            for r in rows:
                print(f"  │  [{r[2] or '?'}] {str(r[1])[:80]}")
            total += len(rows)

    for tbl, col, extra in like_sources:
        try:
            rows = c.execute(
                f"SELECT id, {col}, {extra} FROM [{tbl}] WHERE {col} LIKE ? LIMIT 10",
                (f"%{topic}%",)
            ).fetchall()
            if rows:
                print(f"\n  ┌─ {tbl} ({len(rows)} hits)")
                for r in rows:
                    print(f"  │  [{r[2] or '?'}] {str(r[1])[:80]}")
                total += len(rows)
        except Exception:
            pass

    print(f"\n  ═ Fused: {total} results across 5 sources")

def cmd_timeline(args):
    """Timeline events with date/actor filters."""
    hdr("Timeline Events")
    c = get_sqlite()
    conditions, params = [], []
    if getattr(args, 'from_date', None):
        conditions.append("event_date >= ?"); params.append(args.from_date)
    if getattr(args, 'to_date', None):
        conditions.append("event_date <= ?"); params.append(args.to_date)
    if getattr(args, 'actor', None):
        conditions.append("actor LIKE ?"); params.append(f"%{args.actor}%")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = c.execute(
        f"SELECT event_date, actor, event_description, lane FROM timeline_events "
        f"{where} ORDER BY event_date DESC LIMIT 30", params
    ).fetchall()
    print(f"\n  {'Date':<12s} {'Actor':<20s} {'Lane':<6s} {'Event':<50s}")
    print(f"  {'─'*90}")
    for r in rows:
        print(f"  {str(r['event_date'] or '?')[:11]:<12s} {str(r['actor'] or '?')[:19]:<20s} "
              f"{str(r['lane'] or '?')[:5]:<6s} {str(r['event_description'] or '')[:50]}")

def cmd_impeach(args):
    """Impeachment arsenal for a target person."""
    target = args.target
    min_sev = getattr(args, 'min_sev', 5) or 5
    hdr(f"Impeachment Arsenal: {target} (min severity {min_sev})")
    d = get_duck()
    rows = d.execute(f"""
        SELECT category, evidence_summary, impeachment_value,
               cross_exam_question, source_file
        FROM lit.impeachment_matrix
        WHERE (LOWER(CAST(target AS VARCHAR)) LIKE LOWER('%{target}%')
           OR LOWER(CAST(category AS VARCHAR)) LIKE LOWER('%{target}%'))
          AND CAST(impeachment_value AS INT) >= {int(min_sev)}
        ORDER BY CAST(impeachment_value AS INT) DESC
        LIMIT 30
    """).fetchall()
    print(f"\n  {len(rows)} items (severity ≥ {min_sev})")
    for r in rows:
        print(f"\n  [{r[2]}] {r[0]}")
        print(f"     Evidence: {str(r[1])[:80]}")
        if r[3]:
            print(f"     Cross-Q:  {str(r[3])[:80]}")

def cmd_contradict(args):
    """Contradiction map for an entity."""
    entity = args.entity
    hdr(f"Contradictions: {entity}")
    c = get_sqlite()
    rows = c.execute("""
        SELECT claim_id, source_a, source_b, contradiction_text, severity, lane
        FROM contradiction_map
        WHERE source_a LIKE ? OR source_b LIKE ? OR contradiction_text LIKE ?
        ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                 WHEN 'medium' THEN 3 ELSE 4 END
        LIMIT 25
    """, (f"%{entity}%", f"%{entity}%", f"%{entity}%")).fetchall()
    print(f"\n  {len(rows)} contradictions found")
    for r in rows:
        sev = r['severity'] or '?'
        print(f"\n  [{sev:>8s}] {r['claim_id'] or '?'} (Lane {r['lane'] or '?'})")
        print(f"    A: {str(r['source_a'])[:60]}")
        print(f"    B: {str(r['source_b'])[:60]}")
        print(f"    → {str(r['contradiction_text'])[:90]}")

def cmd_authority(args):
    """Authority chain lookup."""
    cite = args.citation
    hdr(f"Authority Chain: {cite}")
    c = get_sqlite()
    rows = c.execute("""
        SELECT primary_citation, supporting_citation, relationship,
               source_document, lane
        FROM authority_chains_v2
        WHERE primary_citation LIKE ? OR supporting_citation LIKE ?
        LIMIT 25
    """, (f"%{cite}%", f"%{cite}%")).fetchall()
    print(f"\n  {len(rows)} chain links")
    for r in rows:
        print(f"  {r['primary_citation']:>30s} → {str(r['supporting_citation'])[:30]:<30s} [{r['lane'] or '?'}]")
        if r['relationship']:
            print(f"  {'':>30s}   {str(r['relationship'])[:60]}")

def cmd_stats(args):
    """Full system stats dashboard (single DuckDB query)."""
    hdr(f"System Stats — Day {sep_days()} of Separation")
    d = get_duck()
    row = d.execute("""
        SELECT
            (SELECT COUNT(*) FROM lit.evidence_quotes) as ev,
            (SELECT COUNT(*) FROM lit.authority_chains_v2) as auth,
            (SELECT COUNT(*) FROM lit.timeline_events) as tl,
            (SELECT COUNT(*) FROM lit.impeachment_matrix) as imp,
            (SELECT COUNT(*) FROM lit.contradiction_map) as con,
            (SELECT COUNT(*) FROM lit.judicial_violations) as jv,
            (SELECT COUNT(*) FROM lit.berry_mcneill_intelligence) as bmi,
            (SELECT COUNT(*) FROM lit.police_reports) as pr
    """).fetchone()
    labels = ["Evidence quotes", "Authority chains", "Timeline events",
              "Impeachment matrix", "Contradictions", "Judicial violations",
              "Cartel intelligence", "Police reports"]
    total = 0
    for label, val in zip(labels, row):
        v = int(val)
        total += v
        print(f"  {label:<25s} {v:>10,}")
    print(f"  {'─'*37}")
    print(f"  {'TOTAL':<25s} {total:>10,}")
    print(f"\n  ⚠️  Separation: {sep_days()} days since Jul 29, 2025")

def cmd_dashboard(args):
    """Complete analytical dashboard."""
    cmd_stats(args)
    cmd_jud_violations(args)
    cmd_mbp_layers(args)

# ═══════════════════════════════════════════════════════════════
# CLI PARSER
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="SINGULARITY Intel Toolkit — Direct DuckDB/SQLite CLI")
    sub = p.add_subparsers(dest='cmd')

    # MBP
    sub.add_parser('mbp-layers', help='Layer stats')
    sub.add_parser('mbp-data-quality', help='Data quality audit')
    sub.add_parser('mbp-evidence-heatmap', help='Evidence heatmap')
    wp = sub.add_parser('mbp-weapon-chains', help='Weapon chains')
    wp.add_argument('--type', help='Filter weapon type')

    # Judicial
    jv = sub.add_parser('jud-violations', help='Violation breakdown')
    jv.add_argument('--type', help='Filter violation type')
    jc = sub.add_parser('jud-cartel', help='Cartel network')
    jc.add_argument('--person', help='Filter by person')
    sub.add_parser('jud-canons', help='Canon violations')
    jch = sub.add_parser('jud-chronology', help='Bias chronology')
    jch.add_argument('--limit', type=int, default=30)
    sub.add_parser('jud-severity', help='Severity heatmap')
    jex = sub.add_parser('jud-ex-parte', help='Ex parte deep dive')
    jex.add_argument('--limit', type=int, default=20)

    # Cross-domain
    sp = sub.add_parser('search', help='FTS5 search')
    sp.add_argument('query')
    sp.add_argument('--table', default='evidence_quotes')
    fp = sub.add_parser('fuse', help='Cross-table fusion')
    fp.add_argument('topic')
    tp = sub.add_parser('timeline', help='Timeline events')
    tp.add_argument('--from', dest='from_date')
    tp.add_argument('--to', dest='to_date')
    tp.add_argument('--actor')
    ip = sub.add_parser('impeach', help='Impeachment arsenal')
    ip.add_argument('target')
    ip.add_argument('--min-sev', type=int, default=5)
    cp = sub.add_parser('contradict', help='Contradiction map')
    cp.add_argument('entity')
    ap = sub.add_parser('authority', help='Authority chain lookup')
    ap.add_argument('citation')
    sub.add_parser('stats', help='System stats')
    sub.add_parser('dashboard', help='Full dashboard')

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return

    dispatch = {
        'mbp-layers': cmd_mbp_layers, 'mbp-data-quality': cmd_mbp_data_quality,
        'mbp-evidence-heatmap': cmd_mbp_evidence_heatmap,
        'mbp-weapon-chains': cmd_mbp_weapon_chains,
        'jud-violations': cmd_jud_violations, 'jud-cartel': cmd_jud_cartel,
        'jud-canons': cmd_jud_canons, 'jud-chronology': cmd_jud_chronology,
        'jud-severity': cmd_jud_severity, 'jud-ex-parte': cmd_jud_ex_parte,
        'search': cmd_search, 'fuse': cmd_fuse, 'timeline': cmd_timeline,
        'impeach': cmd_impeach, 'contradict': cmd_contradict,
        'authority': cmd_authority, 'stats': cmd_stats, 'dashboard': cmd_dashboard,
    }
    dispatch[args.cmd](args)

if __name__ == '__main__':
    main()
