#!/usr/bin/env python3
"""
master_timeline.py — Pigors v. Watson: Comprehensive Chronological Timeline Builder

Extracts date-bearing events from ALL tables in litigation_context.db,
deduplicates, categorises, and writes:
  • master_timeline table  (SQLite)
  • master_timeline.md     (human-readable)
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, date
from typing import List, Optional, Tuple

# ── paths ──────────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\litigation_context.db"
MD_OUT = r"C:\Users\andre\LitigationOS\06_ANALYSIS\master_timeline.md"
BATCH = 500

# ── date parsing ───────────────────────────────────────────────────────
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Compiled regexes for date extraction (order matters — most specific first)
RE_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
RE_SLASH_MDY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
RE_SLASH_MDY_SHORT = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2})\b")
RE_MONTH_DD_YYYY = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\s+(\d{1,2}),?\s+(\d{4})\b",
    re.IGNORECASE,
)
RE_DD_MONTH_YYYY = re.compile(
    r"\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)
RE_MONTH_YYYY = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)
RE_YEAR_ONLY = re.compile(r"\b(20[12]\d)\b")


def _safe_date(y: int, m: int, d: int) -> Optional[str]:
    """Return ISO date string or None if invalid."""
    try:
        if 1990 <= y <= 2030 and 1 <= m <= 12 and 1 <= d <= 31:
            return date(y, m, d).isoformat()
    except ValueError:
        pass
    return None


def parse_dates(text: str) -> List[str]:
    """Return a list of ISO date strings found in *text*."""
    if not text:
        return []
    results: list[str] = []

    for m in RE_ISO.finditer(text):
        d = _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            results.append(d)

    for m in RE_SLASH_MDY.finditer(text):
        d = _safe_date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        if d:
            results.append(d)

    for m in RE_SLASH_MDY_SHORT.finditer(text):
        yr = int(m.group(3))
        yr = yr + 2000 if yr < 50 else yr + 1900
        d = _safe_date(yr, int(m.group(1)), int(m.group(2)))
        if d:
            results.append(d)

    for m in RE_MONTH_DD_YYYY.finditer(text):
        mon = MONTH_MAP.get(m.group(1).lower())
        if mon:
            d = _safe_date(int(m.group(3)), mon, int(m.group(2)))
            if d:
                results.append(d)

    for m in RE_DD_MONTH_YYYY.finditer(text):
        mon = MONTH_MAP.get(m.group(2).lower())
        if mon:
            d = _safe_date(int(m.group(3)), mon, int(m.group(1)))
            if d:
                results.append(d)

    # deduplicate preserving order
    seen = set()
    out = []
    for d in results:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def parse_first_date(text: str) -> Optional[str]:
    """Return the first date found, or None."""
    dates = parse_dates(text)
    return dates[0] if dates else None


# ── category / lane helpers ────────────────────────────────────────────
LANE_KEYWORDS = {
    "MEEK1": ["custody", "parenting time", "best interest", "child support",
              "722.23", "722.27", "001507-DC", "DC"],
    "MEEK2": ["PPO", "personal protection", "600.2950", "5907-PP",
              "stalking", "protection order"],
    "MEEK3": ["COA", "court of appeals", "appeal", "appellate",
              "interlocutory"],
    "MEEK4": ["JTC", "judicial tenure", "MSC", "supreme court",
              "judicial misconduct", "canon"],
}

CATEGORY_KEYWORDS = {
    "filing":        ["motion", "filed", "filing", "complaint", "petition",
                      "brief", "reply", "response", "objection", "notice"],
    "hearing":       ["hearing", "evidentiary", "oral argument", "trial",
                      "conference", "status conference"],
    "order":         ["order", "ruling", "decision", "judgment", "opinion",
                      "stipulated", "granted", "denied"],
    "violation":     ["violation", "canon", "benchbook", "misconduct",
                      "bias", "ex parte"],
    "evidence":      ["exhibit", "evidence", "transcript", "deposition",
                      "affidavit", "declaration", "document"],
    "communication": ["email", "text", "message", "letter", "voicemail",
                      "call"],
    "incident":      ["assault", "false allegation", "police", "CPS",
                      "alienation", "withholding", "interference"],
    "deadline":      ["deadline", "due date", "time limit", "days to file"],
    "financial":     ["child support", "income", "payment", "arrears",
                      "deviation"],
}


def classify_lane(text: str) -> str:
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for lane, kws in LANE_KEYWORDS.items():
        scores[lane] = sum(1 for k in kws if k.lower() in text_lower)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "MULTI"


def classify_category(text: str) -> str:
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for k in kws if k in text_lower)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "general"


def severity_from_text(text: str) -> str:
    tl = text.lower()
    if any(w in tl for w in ["critical", "emergency", "constitutional",
                              "due process"]):
        return "critical"
    if any(w in tl for w in ["high", "severe", "canon", "violation",
                              "misconduct"]):
        return "high"
    if any(w in tl for w in ["medium", "moderate"]):
        return "medium"
    return "low"


def extract_citations(text: str) -> str:
    """Pull out MCL/MCR/MRE/Canon citations."""
    cites = re.findall(
        r"(?:MCL|MCR|MRE|Canon)\s*\d[\w.\-()]*",
        text,
        re.IGNORECASE,
    )
    return "; ".join(dict.fromkeys(cites)) if cites else ""


def trunc(text: str, n: int = 400) -> str:
    """Truncate text to n chars."""
    if not text:
        return ""
    text = " ".join(text.split())  # collapse whitespace
    return text[:n] + ("…" if len(text) > n else "")


# ── event container ───────────────────────────────────────────────────
class Event:
    __slots__ = ("date_iso", "description", "source_table", "category",
                 "severity", "case_lane", "citations", "_dedup_key")

    def __init__(self, date_iso: str, description: str, source_table: str,
                 category: str = "", severity: str = "",
                 case_lane: str = "", citations: str = ""):
        self.date_iso = date_iso
        self.description = trunc(description)
        self.source_table = source_table
        self.category = category or classify_category(description)
        self.severity = severity or severity_from_text(description)
        self.case_lane = case_lane or classify_lane(description)
        self.citations = citations or extract_citations(description)
        # dedup key: date + first 120 normalised chars of description
        norm = re.sub(r"\W+", "", self.description[:120]).lower()
        self._dedup_key = f"{self.date_iso}|{norm}"

    @property
    def event_id(self) -> str:
        return hashlib.md5(self._dedup_key.encode()).hexdigest()[:12]


# ── extractors ─────────────────────────────────────────────────────────
def _safe_str(val) -> str:
    if val is None:
        return ""
    return str(val)


def extract_global_chronology(cur: sqlite3.Cursor) -> List[Event]:
    """global_chronology — primary timeline (date is ISO or embedded)."""
    events: list[Event] = []
    for row in cur.execute(
        "SELECT date, time, issue, shortfact240, sourcefile, ts_local "
        "FROM global_chronology"
    ):
        dt, tm, issue, fact, src, ts = row
        dt_str = _safe_str(dt).strip()
        ts_str = _safe_str(ts).strip()
        fact_str = _safe_str(fact)
        issue_str = _safe_str(issue)

        # prefer the date column (ISO)
        date_iso = parse_first_date(dt_str) if dt_str else None
        if not date_iso and ts_str:
            date_iso = parse_first_date(ts_str)
        if not date_iso:
            date_iso = parse_first_date(fact_str)
        if not date_iso:
            continue

        desc = fact_str if fact_str else issue_str
        events.append(Event(date_iso, desc, "global_chronology",
                            case_lane=classify_lane(issue_str + " " + fact_str)))
    return events


def extract_chronological_misconduct(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute("SELECT issue, date FROM chronological_misconduct"):
        issue, dt = _safe_str(row[0]), _safe_str(row[1])
        combined = issue + " " + dt
        date_iso = parse_first_date(combined)
        if not date_iso:
            continue
        events.append(Event(date_iso, issue, "chronological_misconduct",
                            category="violation"))
    return events


def extract_benchbook_violations(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT rule, explanation, matching_text FROM benchbook_violation_findings"
    ):
        rule, explanation, matching = _safe_str(row[0]), _safe_str(row[1]), _safe_str(row[2])
        combined = matching + " " + explanation
        date_iso = parse_first_date(combined)
        if not date_iso:
            continue
        desc = f"[{rule}] {explanation}"
        events.append(Event(date_iso, desc, "benchbook_violation_findings",
                            category="violation", severity="high"))
    return events


def extract_global_harms(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT harmsviolations_text, sourcefile, ts_local "
        "FROM global_harms_violations"
    ):
        text, src, ts = _safe_str(row[0]), _safe_str(row[1]), _safe_str(row[2])
        date_iso = parse_first_date(ts) if ts else None
        if not date_iso:
            date_iso = parse_first_date(text)
        if not date_iso:
            continue
        events.append(Event(date_iso, text, "global_harms_violations",
                            category="violation"))
    return events


def extract_global_weaponization(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT category, fact240, authoritieshitsuggested, "
        "relief_lever, ts_local FROM global_weaponization"
    ):
        cat, fact, auth, relief, ts = [_safe_str(c) for c in row]
        date_iso = parse_first_date(ts) if ts else None
        if not date_iso:
            date_iso = parse_first_date(fact)
        if not date_iso:
            continue
        citations = auth if auth else ""
        events.append(Event(date_iso, fact, "global_weaponization",
                            citations=citations))
    return events


def extract_evidence_quotes(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT quote_text, evidence_category, speaker, date_ref, "
        "legal_significance FROM evidence_quotes"
    ):
        text, ecat, speaker, date_ref, sig = [_safe_str(c) for c in row]
        date_iso = parse_first_date(date_ref) if date_ref else None
        if not date_iso:
            date_iso = parse_first_date(text)
        if not date_iso:
            continue
        desc = f"[{ecat}] {speaker}: {text}" if speaker else f"[{ecat}] {text}"
        events.append(Event(date_iso, desc, "evidence_quotes",
                            category="evidence"))
    return events


def extract_narrative(cur: sqlite3.Cursor) -> List[Event]:
    """narrative table — has explicit 'date' column in various formats."""
    events: list[Event] = []
    for row in cur.execute(
        "SELECT date, name, tag, text_excerpt FROM narrative "
        "WHERE date IS NOT NULL AND date != ''"
    ):
        dt, name, tag, excerpt = [_safe_str(c) for c in row]
        date_iso = parse_first_date(dt)
        if not date_iso:
            continue
        desc = name if name else excerpt
        if not desc:
            continue
        events.append(Event(date_iso, desc, "narrative"))
    return events


def extract_master_citations(cur: sqlite3.Cursor) -> List[Event]:
    """master_citations — extract dates from context column (batch read)."""
    events: list[Event] = []
    batch_size = 10000
    offset = 0
    while True:
        rows = cur.execute(
            "SELECT source_file, cite_type, citation, context "
            "FROM master_citations WHERE context IS NOT NULL "
            f"LIMIT {batch_size} OFFSET {offset}"
        ).fetchall()
        if not rows:
            break
        for row in rows:
            src, ctype, cite, ctx = [_safe_str(c) for c in row]
            date_iso = parse_first_date(ctx)
            if not date_iso:
                continue
            desc = f"[{ctype}: {cite}] {ctx}"
            events.append(Event(date_iso, desc, "master_citations",
                                citations=cite))
        offset += batch_size
    return events


def extract_watsons_evidence(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT filename, substr(content, 1, 2000) FROM watsons_evidence_docs"
    ):
        fname, content = _safe_str(row[0]), _safe_str(row[1])
        dates = parse_dates(content)
        for d in dates[:3]:  # max 3 dates per doc to avoid flooding
            desc = f"[Watson Doc: {fname}] {content[:300]}"
            events.append(Event(d, desc, "watsons_evidence_docs",
                                category="evidence"))
    return events


def extract_alienation_tactics(cur: sqlite3.Cursor) -> List[Event]:
    """alienation_tactics — no dates in columns, skip unless embedded."""
    events: list[Event] = []
    for row in cur.execute("SELECT tactic, description FROM alienation_tactics"):
        tactic, desc = _safe_str(row[0]), _safe_str(row[1])
        date_iso = parse_first_date(desc)
        if not date_iso:
            continue
        events.append(Event(date_iso, f"[Alienation: {tactic}] {desc}",
                            "alienation_tactics", category="incident"))
    return events


def extract_md_sections(cur: sqlite3.Cursor) -> List[Event]:
    """md_sections — huge table; only scan sections with dates in title."""
    events: list[Event] = []
    for row in cur.execute(
        "SELECT section_title, substr(content, 1, 1000), source_file "
        "FROM md_sections "
        "WHERE section_title GLOB '*20[12][0-9]*' "
        "   OR section_title GLOB '*January*' OR section_title GLOB '*February*' "
        "   OR section_title GLOB '*March*' OR section_title GLOB '*April*' "
        "   OR section_title GLOB '*May*' OR section_title GLOB '*June*' "
        "   OR section_title GLOB '*July*' OR section_title GLOB '*August*' "
        "   OR section_title GLOB '*September*' OR section_title GLOB '*October*' "
        "   OR section_title GLOB '*November*' OR section_title GLOB '*December*' "
        "LIMIT 50000"
    ):
        title, content, src = [_safe_str(c) for c in row]
        date_iso = parse_first_date(title)
        if not date_iso:
            date_iso = parse_first_date(content[:300])
        if not date_iso:
            continue
        desc = title if len(title) > 10 else content[:300]
        events.append(Event(date_iso, desc, "md_sections"))
    return events


def extract_impeachment(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT statement, contradicting_text, speaker, severity "
        "FROM impeachment_items"
    ):
        stmt, contra, speaker, sev = [_safe_str(c) for c in row]
        combined = stmt + " " + contra
        date_iso = parse_first_date(combined)
        if not date_iso:
            continue
        desc = f"[Impeachment – {speaker}] {stmt}"
        events.append(Event(date_iso, desc, "impeachment_items",
                            category="evidence",
                            severity=sev.lower() if sev else ""))
    return events


def extract_documents_table(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT file_name, modified_date, evidence_category FROM documents"
    ):
        fname, mdate, ecat = [_safe_str(c) for c in row]
        date_iso = parse_first_date(mdate)
        if not date_iso:
            date_iso = parse_first_date(fname)
        if not date_iso:
            continue
        desc = f"[Document: {fname}] Category: {ecat}"
        events.append(Event(date_iso, desc, "documents",
                            category="evidence"))
    return events


def extract_scanned_pdf_triage(cur: sqlite3.Cursor) -> List[Event]:
    events: list[Event] = []
    for row in cur.execute(
        "SELECT relpath, dates, case_candidates, judge_candidate, first_line "
        "FROM scanned_pdf_triage WHERE dates IS NOT NULL AND dates != ''"
    ):
        relpath, dates_str, cases, judge, first_line = [_safe_str(c) for c in row]
        dates_found = parse_dates(dates_str + " " + _safe_str(first_line))
        for d in dates_found[:2]:
            desc = f"[Scanned PDF: {relpath}] {first_line}"
            events.append(Event(d, desc, "scanned_pdf_triage",
                                category="evidence"))
    return events


# ── deduplication ──────────────────────────────────────────────────────
def deduplicate(events: List[Event]) -> List[Event]:
    """Keep first event per dedup-key (date + normalised description prefix)."""
    seen: dict[str, Event] = {}
    for ev in events:
        if ev._dedup_key not in seen:
            seen[ev._dedup_key] = ev
    return sorted(seen.values(), key=lambda e: e.date_iso)


# ── DB write ───────────────────────────────────────────────────────────
def create_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS master_timeline")
    conn.execute("""
        CREATE TABLE master_timeline (
            event_id     TEXT PRIMARY KEY,
            date_iso     TEXT NOT NULL,
            description  TEXT NOT NULL,
            category     TEXT,
            severity     TEXT,
            case_lane    TEXT,
            source_table TEXT,
            citations    TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_mt_date ON master_timeline(date_iso)"
    )
    conn.commit()


def insert_events(conn: sqlite3.Connection, events: List[Event]) -> int:
    inserted = 0
    batch: list[tuple] = []
    for ev in events:
        batch.append((
            ev.event_id, ev.date_iso, ev.description, ev.category,
            ev.severity, ev.case_lane, ev.source_table, ev.citations,
        ))
        if len(batch) >= BATCH:
            conn.executemany(
                "INSERT OR IGNORE INTO master_timeline "
                "(event_id, date_iso, description, category, severity, "
                "case_lane, source_table, citations) VALUES (?,?,?,?,?,?,?,?)",
                batch,
            )
            inserted += len(batch)
            batch.clear()
    if batch:
        conn.executemany(
            "INSERT OR IGNORE INTO master_timeline "
            "(event_id, date_iso, description, category, severity, "
            "case_lane, source_table, citations) VALUES (?,?,?,?,?,?,?,?)",
            batch,
        )
        inserted += len(batch)
    conn.commit()
    return inserted


# ── Markdown output ────────────────────────────────────────────────────
def write_markdown(events: List[Event], stats: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write("# Pigors v. Watson — Master Chronological Timeline\n\n")
        f.write(f"*Generated: {datetime.now().isoformat(timespec='seconds')}*\n\n")
        f.write(f"**Total events:** {stats['total']:,}  \n")
        f.write(f"**Date range:** {stats['min_date']} → {stats['max_date']}  \n")
        f.write(f"**Source tables:** {stats['source_count']}\n\n")
        f.write("---\n\n")

        # Group by year-month
        by_month: dict[str, list[Event]] = defaultdict(list)
        for ev in events:
            ym = ev.date_iso[:7]
            by_month[ym].append(ev)

        for ym in sorted(by_month):
            f.write(f"## {ym}\n\n")
            for ev in sorted(by_month[ym], key=lambda e: e.date_iso):
                lane_tag = f"`{ev.case_lane}`" if ev.case_lane else ""
                sev_tag = f" **[{ev.severity.upper()}]**" if ev.severity not in ("", "low") else ""
                cite_tag = f" _{ev.citations}_" if ev.citations else ""
                f.write(
                    f"- **{ev.date_iso}** [{ev.category}]{sev_tag} {lane_tag}  \n"
                    f"  {ev.description[:250]}{cite_tag}  \n"
                    f"  <sub>src: {ev.source_table}</sub>\n\n"
                )

        # Summary statistics
        f.write("\n---\n\n## Summary Statistics\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total events | {stats['total']:,} |\n")
        f.write(f"| Date range | {stats['min_date']} → {stats['max_date']} |\n")
        f.write(f"| Source tables | {stats['source_count']} |\n\n")

        f.write("### Events by Category\n\n")
        f.write("| Category | Count |\n|---|---:|\n")
        for cat, cnt in sorted(stats["by_category"].items(),
                                key=lambda x: -x[1]):
            f.write(f"| {cat} | {cnt:,} |\n")

        f.write("\n### Events by Case Lane\n\n")
        f.write("| Lane | Count |\n|---|---:|\n")
        for lane, cnt in sorted(stats["by_lane"].items(),
                                  key=lambda x: -x[1]):
            f.write(f"| {lane} | {cnt:,} |\n")

        f.write("\n### Events by Month\n\n")
        f.write("| Month | Count |\n|---|---:|\n")
        for ym in sorted(by_month):
            f.write(f"| {ym} | {len(by_month[ym]):,} |\n")

        f.write("\n### Events by Source Table\n\n")
        f.write("| Source Table | Count |\n|---|---:|\n")
        for src, cnt in sorted(stats["by_source"].items(),
                                key=lambda x: -x[1]):
            f.write(f"| {src} | {cnt:,} |\n")


# ── main ───────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("Pigors v. Watson — Master Timeline Builder")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.text_factory = lambda b: b.decode("utf-8", "replace")
    cur = conn.cursor()

    all_events: list[Event] = []

    extractors = [
        ("global_chronology",            extract_global_chronology),
        ("chronological_misconduct",     extract_chronological_misconduct),
        ("benchbook_violation_findings", extract_benchbook_violations),
        ("global_harms_violations",      extract_global_harms),
        ("global_weaponization",         extract_global_weaponization),
        ("evidence_quotes",              extract_evidence_quotes),
        ("narrative",                    extract_narrative),
        ("master_citations",             extract_master_citations),
        ("watsons_evidence_docs",        extract_watsons_evidence),
        ("alienation_tactics",           extract_alienation_tactics),
        ("md_sections",                  extract_md_sections),
        ("impeachment_items",            extract_impeachment),
        ("documents",                    extract_documents_table),
        ("scanned_pdf_triage",           extract_scanned_pdf_triage),
    ]

    for name, func in extractors:
        try:
            evts = func(cur)
            print(f"  {name:40s} → {len(evts):>7,} events")
            all_events.extend(evts)
        except Exception as exc:
            print(f"  {name:40s} → ERROR: {exc}")

    print(f"\nRaw events collected: {len(all_events):,}")

    # Deduplicate
    events = deduplicate(all_events)
    print(f"After deduplication:  {len(events):,}")

    # Statistics
    dates = [e.date_iso for e in events]
    by_cat = Counter(e.category for e in events)
    by_lane = Counter(e.case_lane for e in events)
    by_src = Counter(e.source_table for e in events)
    stats = {
        "total": len(events),
        "min_date": min(dates) if dates else "N/A",
        "max_date": max(dates) if dates else "N/A",
        "source_count": len(by_src),
        "by_category": dict(by_cat),
        "by_lane": dict(by_lane),
        "by_source": dict(by_src),
    }

    # Write to DB
    print("\nWriting master_timeline table …")
    create_table(conn)
    inserted = insert_events(conn, events)
    print(f"  Inserted {inserted:,} rows")

    # Verify
    actual = cur.execute("SELECT COUNT(*) FROM master_timeline").fetchone()[0]
    print(f"  Verified: {actual:,} rows in master_timeline")

    conn.close()

    # Write Markdown
    print(f"\nWriting {MD_OUT} …")
    write_markdown(events, stats, MD_OUT)
    print("  Done.")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total unique events : {stats['total']:,}")
    print(f"  Date range          : {stats['min_date']} → {stats['max_date']}")
    print(f"  Source tables used   : {stats['source_count']}")
    print()
    print("  Events by category:")
    for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat:20s} {cnt:>7,}")
    print()
    print("  Events per month (top 15):")
    by_month: Counter = Counter()
    for e in events:
        by_month[e.date_iso[:7]] += 1
    for ym, cnt in by_month.most_common(15):
        print(f"    {ym}  {cnt:>6,}")
    print("\n✓ master_timeline.py complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)
