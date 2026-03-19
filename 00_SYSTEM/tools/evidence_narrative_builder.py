#!/usr/bin/env python3
"""
NOVEL TOOL #32: Evidence Narrative Builder
============================================
Automatically constructs a chronological narrative from evidence,
weaving together testimony, documents, and exhibits into a
cohesive story suitable for court filings.

This tool solves the #1 problem pro se litigants face:
taking a mountain of evidence and turning it into a
compelling, chronological story that a judge can follow.

Features:
- Auto-extracts date-stamped events from evidence DB
- Groups by theme (custody, housing, misconduct, etc.)
- Identifies narrative gaps (where story is weak)
- Generates both factual narrative and legal narrative
- Cross-references every claim to source evidence
- Produces exhibit-linked paragraphs ready to paste into filings

This is a STORY ENGINE for litigation — nothing like it exists.
"""

import sys
import os
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

NARRATIVE_THEMES = {
    "custody_interference": {
        "keywords": ["custody", "parenting time", "visitation", "child", "L.D.W.",
                      "birthday", "holiday", "contact", "phone call", "denied access"],
        "legal_framework": "MCL 722.27a — Parenting Time; MCL 722.23 — Best Interest Factors",
        "description": "Pattern of interference with parent-child relationship"
    },
    "fraud_perjury": {
        "keywords": ["perjury", "false", "fabricated", "lied", "sworn", "affidavit",
                      "contradicted", "inconsistent", "under oath", "misrepresented"],
        "legal_framework": "MCL 750.423 — Perjury; MCR 2.612(C)(1)(c) — Fraud",
        "description": "Pattern of fraud upon the court and perjury"
    },
    "judicial_misconduct": {
        "keywords": ["judge", "McNeill", "ex parte", "bias", "denied hearing",
                      "refused", "without notice", "canon", "recusal"],
        "legal_framework": "MCR 2.003 — Disqualification; MCJC Canons",
        "description": "Pattern of judicial bias and misconduct"
    },
    "housing_violations": {
        "keywords": ["eviction", "housing", "lease", "rent", "habitability",
                      "Shady Oaks", "maintenance", "repairs", "landlord"],
        "legal_framework": "MCL 125.534 — Habitability; MCL 554.601a — Security Deposits",
        "description": "Housing rights violations and retaliatory actions"
    },
    "conspiracy": {
        "keywords": ["conspiracy", "together", "coordinated", "Barnes", "Berry",
                      "Watson", "scheme", "plan", "agreed", "colluded"],
        "legal_framework": "42 USC §1985(3) — Conspiracy; MCL 750.157a",
        "description": "Coordinated conspiracy to deprive rights"
    },
    "due_process": {
        "keywords": ["notice", "hearing", "opportunity", "due process", "rights",
                      "without hearing", "ex parte", "no notice", "surprise"],
        "legal_framework": "US Const Amend XIV; Const 1963 Art 1 §17",
        "description": "Due process violations — notice and opportunity to be heard"
    }
}


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def extract_dated_events(conn):
    """Extract all date-stamped events from evidence tables."""
    events = []
    date_pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2}|\w+\s+\d{1,2},?\s+\d{4})')

    # Source 1: evidence_quotes
    try:
        eq_cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
        source_col = next((c for c in ["source_file", "source_doc", "source", "file_path"] if c in eq_cols), None)
        type_col = next((c for c in ["evidence_type", "type", "category"] if c in eq_cols), None)
        select_cols = "quote_text"
        if source_col:
            select_cols += f", {source_col}"
        if type_col:
            select_cols += f", {type_col}"

        rows = conn.execute(f"""
            SELECT {select_cols}
            FROM evidence_quotes
            WHERE LENGTH(quote_text) > 30
            ORDER BY RANDOM()
            LIMIT 3000
        """).fetchall()

        for r in rows:
            text = r["quote_text"] or ""
            dates = date_pattern.findall(text)
            if dates:
                events.append({
                    "date_raw": dates[0],
                    "text": text[:300],
                    "source": (r[source_col] if source_col else "evidence_quotes") or "evidence_quotes",
                    "type": (r[type_col] if type_col else "evidence") or "evidence",
                    "table": "evidence_quotes"
                })
    except Exception as e:
        print(f"  ⚠️ evidence_quotes: {e}")

    # Source 2: watson_perjury_compilation
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(watson_perjury_compilation)").fetchall()]

        date_col = None
        for c in ["date_of_statement", "date", "created_at"]:
            if c in cols:
                date_col = c
                break

        rows = conn.execute(f"""
            SELECT statement_text, contradicting_evidence, watson_member,
                   source_doc{', ' + date_col if date_col else ''}
            FROM watson_perjury_compilation
            WHERE LENGTH(statement_text) > 20
            ORDER BY severity_score DESC
            LIMIT 1000
        """).fetchall()

        for r in rows:
            text = r["statement_text"] or ""
            date_str = r[date_col] if date_col and date_col in [c[0] for c in conn.execute(f"SELECT * FROM watson_perjury_compilation LIMIT 0").description] else ""
            if not date_str:
                dates = date_pattern.findall(text)
                date_str = dates[0] if dates else ""

            events.append({
                "date_raw": str(date_str),
                "text": text[:300],
                "source": r["source_doc"] or "perjury_compilation",
                "type": "perjury",
                "actor": r["watson_member"],
                "contradiction": (r["contradicting_evidence"] or "")[:200],
                "table": "watson_perjury_compilation"
            })
    except Exception as e:
        print(f"  ⚠️ watson_perjury_compilation: {e}")

    # Source 3: detected_contradictions
    try:
        rows = conn.execute("""
            SELECT speaker, statement_1, source_1, date_1,
                   statement_2, source_2, date_2,
                   contradiction_type, severity
            FROM detected_contradictions
            WHERE severity >= 5
            ORDER BY severity DESC
            LIMIT 500
        """).fetchall()

        for r in rows:
            events.append({
                "date_raw": str(r["date_1"] or ""),
                "text": f"{r['speaker']}: '{(r['statement_1'] or '')[:150]}' vs '{(r['statement_2'] or '')[:150]}'",
                "source": r["source_1"] or "contradictions",
                "type": "contradiction",
                "actor": r["speaker"],
                "severity": r["severity"],
                "table": "detected_contradictions"
            })
    except Exception as e:
        print(f"  ⚠️ detected_contradictions: {e}")

    # Source 4: judicial_violations
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
        text_col = next((c for c in ["description", "violation_text", "details", "finding"] if c in cols), None)
        date_col = next((c for c in ["date", "violation_date", "created_at"] if c in cols), None)

        if text_col:
            query = f"SELECT {text_col}"
            if date_col:
                query += f", {date_col}"
            query += " FROM judicial_violations LIMIT 500"

            rows = conn.execute(query).fetchall()
            for r in rows:
                text = r[text_col] or ""
                date_str = r[date_col] if date_col else ""
                if not date_str:
                    dates = date_pattern.findall(text)
                    date_str = dates[0] if dates else ""

                events.append({
                    "date_raw": str(date_str),
                    "text": text[:300],
                    "source": "judicial_violations",
                    "type": "judicial_misconduct",
                    "table": "judicial_violations"
                })
    except Exception as e:
        print(f"  ⚠️ judicial_violations: {e}")

    return events


def classify_event_theme(event):
    """Classify an event into narrative themes."""
    text = (event.get("text", "") + " " + event.get("type", "")).lower()
    themes = []

    for theme_id, theme_data in NARRATIVE_THEMES.items():
        score = sum(1 for kw in theme_data["keywords"] if kw.lower() in text)
        if score >= 1:
            themes.append((theme_id, score))

    themes.sort(key=lambda x: x[1], reverse=True)
    return [t[0] for t in themes[:2]] if themes else ["general"]


def parse_date(date_str):
    """Attempt to parse a date string."""
    if not date_str:
        return None

    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y", "%B %d %Y",
                "%b %d, %Y", "%b %d %Y", "%m/%d/%Y", "%m-%d-%Y"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def build_narrative(events_by_theme, theme_id):
    """Build a narrative from themed events."""
    theme = NARRATIVE_THEMES.get(theme_id, {})
    events = events_by_theme.get(theme_id, [])

    if not events:
        return None

    # Sort by date
    dated_events = []
    undated_events = []
    for e in events:
        parsed = parse_date(e.get("date_raw", ""))
        if parsed:
            dated_events.append((parsed, e))
        else:
            undated_events.append(e)

    dated_events.sort(key=lambda x: x[0])

    lines = []
    lines.append(f"### {theme.get('description', theme_id).upper()}")
    lines.append(f"*Legal Framework: {theme.get('legal_framework', 'N/A')}*")
    lines.append("")

    # Build chronological paragraphs
    para_num = 1
    for date, event in dated_events[:30]:  # Limit to 30 events per theme
        date_str = date.strftime("%B %d, %Y")
        text = event["text"]
        source = event.get("source", "")

        # Clean up text for narrative use
        text = text.replace("\n", " ").strip()
        if len(text) > 200:
            text = text[:200] + "..."

        lines.append(f"{para_num}. On **{date_str}**, {text}")
        if source:
            lines.append(f"   *(Source: {Path(source).name if '/' in source or '\\\\' in source else source})*")
        lines.append("")
        para_num += 1

    # Add undated evidence
    if undated_events:
        lines.append(f"\n**Additional Evidence (undated):**")
        for e in undated_events[:10]:
            text = e["text"].replace("\n", " ").strip()[:150]
            lines.append(f"- {text}")

    # Narrative gap analysis
    if dated_events:
        lines.append(f"\n**Narrative Coverage:**")
        first_date = dated_events[0][0]
        last_date = dated_events[-1][0]
        span_days = (last_date - first_date).days
        lines.append(f"- Time span: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')} ({span_days} days)")
        lines.append(f"- Dated events: {len(dated_events)}")
        lines.append(f"- Undated events: {len(undated_events)}")

        # Find gaps (>30 days between events)
        gaps = []
        for i in range(1, len(dated_events)):
            gap = (dated_events[i][0] - dated_events[i-1][0]).days
            if gap > 30:
                gaps.append((dated_events[i-1][0].strftime("%Y-%m-%d"),
                             dated_events[i][0].strftime("%Y-%m-%d"),
                             gap))

        if gaps:
            lines.append(f"- **{len(gaps)} narrative gaps** (>30 days):")
            for start, end, days in gaps[:5]:
                lines.append(f"  - {start} → {end} ({days} days) — NEEDS EVIDENCE")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("EVIDENCE NARRATIVE BUILDER v1.0")
    print("Chronological story construction from evidence database")
    print("=" * 60)

    conn = get_db_connection()

    # Extract all dated events
    print("\n📚 Extracting events from database...")
    events = extract_dated_events(conn)
    print(f"  Total events extracted: {len(events)}")

    conn.close()

    # Classify events by theme
    print("\n🏷️ Classifying events by narrative theme...")
    events_by_theme = defaultdict(list)
    for event in events:
        themes = classify_event_theme(event)
        for theme in themes:
            events_by_theme[theme].append(event)

    for theme_id, theme_events in sorted(events_by_theme.items()):
        print(f"  {theme_id:25s}  {len(theme_events):5d} events")

    # Build narratives for each theme
    print("\n📖 Building narratives...")
    narratives = {}
    master_doc = []
    master_doc.append("# EVIDENCE NARRATIVE — CHRONOLOGICAL COMPILATION")
    master_doc.append(f"# Pigors v. Watson — Case No. 2024-001507-DC")
    master_doc.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    master_doc.append("")
    master_doc.append("## TABLE OF CONTENTS")
    master_doc.append("")

    toc_entries = []
    for theme_id in NARRATIVE_THEMES:
        if theme_id in events_by_theme:
            theme = NARRATIVE_THEMES[theme_id]
            toc_entries.append(f"- [{theme['description']}](#{theme_id})")

    master_doc.extend(toc_entries)
    master_doc.append("")
    master_doc.append("---")
    master_doc.append("")

    for theme_id, theme_data in NARRATIVE_THEMES.items():
        if theme_id not in events_by_theme:
            continue

        narrative = build_narrative(events_by_theme, theme_id)
        if narrative:
            narratives[theme_id] = {
                "event_count": len(events_by_theme[theme_id]),
                "description": theme_data["description"],
                "legal_framework": theme_data["legal_framework"]
            }
            master_doc.append(f'<a id="{theme_id}"></a>')
            master_doc.append(narrative)
            master_doc.append("\n---\n")
            print(f"  ✅ {theme_id}: {len(events_by_theme[theme_id])} events → narrative built")

    # Summary statistics
    total_dated = sum(1 for e in events if parse_date(e.get("date_raw", "")))
    total_undated = len(events) - total_dated

    summary = {
        "generated": datetime.now().isoformat(),
        "total_events": len(events),
        "dated_events": total_dated,
        "undated_events": total_undated,
        "themes": len(narratives),
        "theme_details": narratives,
        "sources": dict(Counter(e.get("table", "unknown") for e in events))
    }

    # Save JSON
    json_path = REPORTS_DIR / "evidence_narrative.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    # Save master narrative
    md_path = REPORTS_DIR / "EVIDENCE_NARRATIVE.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(master_doc))

    print(f"\n{'='*60}")
    print(f"EVIDENCE NARRATIVE BUILDER — COMPLETE")
    print(f"{'='*60}")
    print(f"Total events:     {len(events)}")
    print(f"Dated events:     {total_dated}")
    print(f"Themes covered:   {len(narratives)}")
    print(f"Sources used:     {len(summary['sources'])}")
    print(f"\nNarrative file:   {md_path}")
    print(f"JSON data:        {json_path}")

    return summary


if __name__ == "__main__":
    main()
