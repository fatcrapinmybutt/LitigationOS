#!/usr/bin/env python3
"""
Tool #235 — Rusco Ex Parte Communication Tracker
=================================================
Tracks Pamela Rusco (FOC) ex parte communications:
- Direct calls to HealthWest clinician about Andrew's evaluation
- Emailed subpoena without proper service
- Communications with Emily's side excluding Andrew

Maps each violation to:
  MCR 2.003 (disqualification), Canon 2 Rule 2.9 (ex parte contacts),
  MCL 552.507 (FOC duties/limitations)

Outputs: MD report + JSON to reports dir
LitigationOS — Pigors v. Watson (14th Circuit Court, Muskegon County)
"""
import sys
import os
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# Paths — NEVER set CWD to repo root (shadow modules)
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = SCRIPT_DIR.parent.parent
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_conn():
    """Open DB with mandatory PRAGMAs."""
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_trunc(text, maxlen=250):
    if not text:
        return ""
    text = str(text).replace('\n', ' ').replace('\r', '').strip()
    return text[:maxlen] + "..." if len(text) > maxlen else text


def table_exists(conn, name):
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] > 0


# ── Authority mapping for Rusco/FOC violations ──────────────────────────
AUTHORITY_MAP = {
    "MCR_2.003": {
        "cite": "MCR 2.003 (Disqualification of Judge)",
        "text": "A judge is disqualified when the judge cannot impartially hear a case, "
                "including when there have been ex parte communications.",
        "relevance": "Rusco's ex parte contacts with HealthWest and Emily's side taint "
                     "the entire proceeding — grounds for disqualification."
    },
    "CANON_2_RULE_2.9": {
        "cite": "MCJC Canon 2, Rule 2.9 (Ex Parte Communications)",
        "text": "A judge shall not initiate, permit, or consider ex parte communications. "
                "Court staff acting on judge's behalf are subject to same restrictions.",
        "relevance": "Rusco, as FOC acting under court authority, is bound by Canon 2 "
                     "restrictions on ex parte contacts."
    },
    "MCL_552.507": {
        "cite": "MCL 552.507 (FOC Duties and Limitations)",
        "text": "FOC shall investigate and make recommendations regarding custody, parenting "
                "time, and support. FOC must serve copies of recommendations on all parties.",
        "relevance": "Rusco failed to include Andrew in communications and bypassed "
                     "proper service requirements."
    },
    "MCL_552.501": {
        "cite": "MCL 552.501 (Friend of Court Act)",
        "text": "Establishes FOC duties including investigation of custody matters. "
                "FOC must act impartially.",
        "relevance": "Rusco's one-sided communications demonstrate bias in FOC role."
    },
    "MCR_3.208": {
        "cite": "MCR 3.208 (Friend of the Court)",
        "text": "FOC has duty to investigate and report to the court. Parties must "
                "receive copies of all FOC communications with the court.",
        "relevance": "Emailing subpoena to judge rather than serving through clerk "
                     "violates MCR service requirements."
    },
}


def query_evidence_quotes(conn):
    """Pull all Rusco/FOC evidence from evidence_quotes."""
    print("  [1/6] Querying evidence_quotes for Rusco/FOC references...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, document_id, page_number, evidence_category, quote_text,
                   speaker, date_ref, legal_significance, source_type
            FROM evidence_quotes
            WHERE quote_text LIKE '%Rusco%'
               OR quote_text LIKE '%FOC%'
               OR quote_text LIKE '%Friend of the Court%'
               OR quote_text LIKE '%friend of court%'
            ORDER BY date_ref
        """).fetchall()
        for r in rows:
            text = str(r["quote_text"] or "")
            # Classify communication type
            comm_type = classify_communication(text)
            results.append({
                "id": r["id"],
                "document_id": r["document_id"],
                "page": r["page_number"],
                "category": r["evidence_category"],
                "text": safe_trunc(text, 400),
                "speaker": r["speaker"],
                "date_ref": r["date_ref"],
                "source_type": r["source_type"],
                "communication_type": comm_type,
            })
        print(f"    Found {len(results)} evidence quotes")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def classify_communication(text):
    """Classify the type of ex parte communication."""
    t = text.lower()
    if any(w in t for w in ['healthwest', 'clinician', 'evaluation', 'assessment', 'mental health']):
        return "HEALTHWEST_CONTACT"
    if any(w in t for w in ['subpoena', 'emailed', 'email']):
        return "IMPROPER_SERVICE"
    if any(w in t for w in ['call', 'phone', 'contacted', 'spoke']):
        return "DIRECT_CONTACT"
    if any(w in t for w in ['emily', 'watson', 'barnes', 'defendant']):
        if 'without' in t or 'excluded' in t or 'not included' in t or 'not copied' in t:
            return "EXCLUDED_PARTY_COMMUNICATION"
        return "ONE_SIDED_COMMUNICATION"
    return "GENERAL_FOC_REFERENCE"


def query_actor_violations(conn):
    """Pull Rusco violations from actor_violations."""
    print("  [2/6] Querying actor_violations for Rusco...")
    results = []
    stats = {"total": 0, "by_type": defaultdict(int), "by_severity": defaultdict(int)}
    try:
        rows = conn.execute("""
            SELECT id, actor, role, violation_type, description, date,
                   evidence_source, severity, linked_actors, pattern_id
            FROM actor_violations
            WHERE actor LIKE '%Rusco%'
               OR actor LIKE '%FOC%'
               OR description LIKE '%Rusco%'
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            stats["total"] += 1
            stats["by_type"][r["violation_type"]] += 1
            stats["by_severity"][str(r["severity"])] += 1
            if len(results) < 100:
                results.append({
                    "id": r["id"],
                    "actor": r["actor"],
                    "type": r["violation_type"],
                    "description": safe_trunc(r["description"], 300),
                    "date": r["date"],
                    "severity": r["severity"],
                    "linked_actors": r["linked_actors"],
                })
        print(f"    Found {stats['total']} actor violations")
    except Exception as e:
        print(f"    Error: {e}")
    return results, dict(stats["by_type"]), dict(stats["by_severity"])


def query_judicial_violations(conn):
    """Pull FOC-related judicial violations."""
    print("  [3/6] Querying judicial_violations for FOC/Rusco/ex parte...")
    results = []
    try:
        rows = conn.execute("""
            SELECT violation_id, judge_name, canon_number, canon_text,
                   violation_description, evidence_refs, severity
            FROM judicial_violations
            WHERE violation_description LIKE '%Rusco%'
               OR violation_description LIKE '%FOC%'
               OR violation_description LIKE '%Friend of Court%'
               OR (canon_number LIKE '%ex%parte%' AND violation_description LIKE '%communicat%')
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            results.append({
                "violation_id": r["violation_id"],
                "judge": r["judge_name"],
                "canon": r["canon_number"],
                "description": safe_trunc(r["violation_description"], 350),
                "evidence_refs": r["evidence_refs"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} judicial violations")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_foc_authority(conn):
    """Pull FOC accountability authorities."""
    print("  [4/6] Querying foc_accountability_authority...")
    results = []
    if not table_exists(conn, 'foc_accountability_authority'):
        print("    Table not found")
        return results
    try:
        rows = conn.execute("""
            SELECT id, authority_type, citation, text_excerpt, relevance, filing_where_needed
            FROM foc_accountability_authority
            WHERE citation LIKE '%552%'
               OR citation LIKE '%MCR%'
               OR text_excerpt LIKE '%ex parte%'
               OR text_excerpt LIKE '%FOC%'
               OR relevance LIKE '%Rusco%'
            ORDER BY authority_type
            LIMIT 50
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "type": r["authority_type"],
                "citation": r["citation"],
                "text": safe_trunc(r["text_excerpt"], 300),
                "relevance": safe_trunc(r["relevance"], 200),
                "filing": r["filing_where_needed"],
            })
        print(f"    Found {len(results)} authority entries")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_d_drive_events(conn):
    """Pull d_drive_events mentioning Rusco/FOC."""
    print("  [5/6] Querying d_drive_events for FOC/Rusco...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, source_doc, event_date, event_description, actors, category, severity
            FROM d_drive_events
            WHERE event_description LIKE '%Rusco%'
               OR event_description LIKE '%FOC%'
               OR event_description LIKE '%Friend of Court%'
               OR actors LIKE '%Rusco%'
            ORDER BY event_date
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "date": r["event_date"],
                "description": safe_trunc(r["event_description"], 300),
                "actors": r["actors"],
                "category": r["category"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} d_drive events")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_docket_events(conn):
    """Pull docket events related to FOC/Rusco."""
    print("  [6/6] Querying docket_events for FOC references...")
    results = []
    try:
        rows = conn.execute("""
            SELECT event_id, case_id, event_date_iso, title, event_type, summary
            FROM docket_events
            WHERE title LIKE '%FOC%' OR title LIKE '%Rusco%'
               OR summary LIKE '%FOC%' OR summary LIKE '%Rusco%'
               OR summary LIKE '%Friend of Court%'
            ORDER BY event_date_iso
        """).fetchall()
        for r in rows:
            results.append({
                "event_id": r["event_id"],
                "case_id": r["case_id"],
                "date": r["event_date_iso"],
                "title": r["title"],
                "type": r["event_type"],
                "summary": safe_trunc(r["summary"], 250),
            })
        print(f"    Found {len(results)} docket events")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def map_to_authorities(evidence_quotes, actor_violations, judicial_violations):
    """Map each finding to applicable legal authorities."""
    mappings = []
    # Evidence quotes → authority mapping
    for eq in evidence_quotes:
        ct = eq["communication_type"]
        applicable = []
        if ct == "HEALTHWEST_CONTACT":
            applicable = ["CANON_2_RULE_2.9", "MCR_2.003", "MCL_552.507"]
        elif ct == "IMPROPER_SERVICE":
            applicable = ["MCR_3.208", "MCL_552.507"]
        elif ct in ("EXCLUDED_PARTY_COMMUNICATION", "ONE_SIDED_COMMUNICATION"):
            applicable = ["CANON_2_RULE_2.9", "MCL_552.501", "MCL_552.507"]
        elif ct == "DIRECT_CONTACT":
            applicable = ["CANON_2_RULE_2.9", "MCR_2.003"]
        else:
            applicable = ["MCL_552.501"]

        mappings.append({
            "evidence_id": eq["id"],
            "date": eq["date_ref"],
            "communication_type": ct,
            "text_excerpt": eq["text"][:200],
            "authorities": [AUTHORITY_MAP[a]["cite"] for a in applicable],
            "authority_keys": applicable,
        })
    return mappings


def build_timeline(evidence_quotes, actor_violations, d_events, docket_events):
    """Build chronological timeline of all Rusco ex parte communications."""
    timeline = []

    for eq in evidence_quotes:
        if eq["communication_type"] in ("HEALTHWEST_CONTACT", "IMPROPER_SERVICE",
                                         "DIRECT_CONTACT", "EXCLUDED_PARTY_COMMUNICATION"):
            timeline.append({
                "date": eq.get("date_ref", "Unknown"),
                "source": "evidence_quotes",
                "type": eq["communication_type"],
                "description": eq["text"][:200],
                "severity": "HIGH" if eq["communication_type"] == "HEALTHWEST_CONTACT" else "MEDIUM",
            })

    for av in actor_violations:
        if "ex parte" in (av.get("description") or "").lower() or \
           "healthwest" in (av.get("description") or "").lower():
            timeline.append({
                "date": av.get("date", "Unknown"),
                "source": "actor_violations",
                "type": av.get("type", "unknown"),
                "description": av["description"][:200],
                "severity": str(av.get("severity", "medium")).upper(),
            })

    for de in d_events:
        timeline.append({
            "date": de.get("date", "Unknown"),
            "source": "d_drive_events",
            "type": de.get("category", "unknown"),
            "description": de["description"][:200],
            "severity": "HIGH" if de.get("severity", 0) >= 3 else "MEDIUM",
        })

    for dk in docket_events:
        timeline.append({
            "date": dk.get("date", "Unknown"),
            "source": "docket_events",
            "type": dk.get("type", "unknown"),
            "description": f"{dk['title']}: {dk['summary'][:150]}",
            "severity": "MEDIUM",
        })

    # Sort by date (best effort)
    def sort_key(item):
        d = item.get("date") or "9999"
        return str(d)
    timeline.sort(key=sort_key)
    return timeline


def generate_filing_recommendations(ev_count, av_count, jv_count, timeline):
    """Generate specific filing recommendations based on findings."""
    recs = []
    if ev_count > 0 or av_count > 0:
        recs.append({
            "filing": "Motion for Disqualification (MCR 2.003)",
            "basis": "Rusco's ex parte communications with HealthWest and one-sided "
                     "contacts with Emily's side constitute grounds for judicial disqualification.",
            "authority": "MCR 2.003(C)(1)(b) — personal bias or prejudice; "
                         "Canon 2 Rule 2.9 — ex parte communications",
            "priority": "HIGH",
            "evidence_count": ev_count,
        })
        recs.append({
            "filing": "Motion to Strike FOC Recommendation",
            "basis": "FOC recommendations tainted by ex parte communications and "
                     "failure to include all parties in investigation.",
            "authority": "MCL 552.507 — FOC recommendation procedures; "
                         "MCR 3.208 — FOC duties",
            "priority": "HIGH",
            "evidence_count": av_count,
        })
        recs.append({
            "filing": "Complaint to FOC Ombudsman / Grievance",
            "basis": "Pattern of one-sided communications and procedural violations "
                     "by Pamela Rusco in her FOC capacity.",
            "authority": "MCL 552.501 et seq. — Friend of Court Act",
            "priority": "MEDIUM",
            "evidence_count": ev_count + av_count,
        })
    if jv_count > 0:
        recs.append({
            "filing": "JTC Complaint Supplement — FOC Collusion",
            "basis": "Judge McNeill's coordination with Rusco on ex parte "
                     "communications amplifies judicial misconduct pattern.",
            "authority": "Mich Const Art 6 §30; MCJC Canon 2 Rule 2.9",
            "priority": "MEDIUM",
            "evidence_count": jv_count,
        })
    healthwest = sum(1 for t in timeline if t.get("type") == "HEALTHWEST_CONTACT")
    if healthwest > 0:
        recs.append({
            "filing": "Motion to Suppress HealthWest Evaluation",
            "basis": f"HealthWest evaluation tainted by {healthwest} documented "
                     "ex parte contacts from Rusco. Fruit of poisoned tree.",
            "authority": "MRE 403 — prejudicial effect; Due Process Clause",
            "priority": "CRITICAL",
            "evidence_count": healthwest,
        })
    return recs


def main():
    ts = datetime.now()
    print("=" * 70)
    print("  TOOL #235 — RUSCO EX PARTE COMMUNICATION TRACKER")
    print(f"  Pigors v. Watson | {ts.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    conn = get_conn()

    # ── Gather data from all sources ──
    evidence_quotes = query_evidence_quotes(conn)
    actor_violations, av_by_type, av_by_severity = query_actor_violations(conn)
    judicial_violations = query_judicial_violations(conn)
    foc_authority = query_foc_authority(conn)
    d_events = query_d_drive_events(conn)
    docket_events = query_docket_events(conn)

    # ── Map to authorities ──
    print("\n  Mapping communications to legal authorities...")
    authority_mappings = map_to_authorities(evidence_quotes, actor_violations, judicial_violations)

    # ── Build timeline ──
    print("  Building chronological timeline...")
    timeline = build_timeline(evidence_quotes, actor_violations, d_events, docket_events)

    # ── Filing recommendations ──
    print("  Generating filing recommendations...")
    recommendations = generate_filing_recommendations(
        len(evidence_quotes), len(actor_violations), len(judicial_violations), timeline
    )

    # ── Communication type breakdown ──
    comm_types = defaultdict(int)
    for eq in evidence_quotes:
        comm_types[eq["communication_type"]] += 1

    conn.close()

    # ── Build JSON output ──
    json_data = {
        "tool": "#235 — Rusco Ex Parte Communication Tracker",
        "generated": ts.isoformat(),
        "case": "Pigors v. Watson (2024-001507-DC)",
        "summary": {
            "evidence_quotes_count": len(evidence_quotes),
            "actor_violations_count": len(actor_violations),
            "judicial_violations_count": len(judicial_violations),
            "foc_authority_count": len(foc_authority),
            "d_drive_events_count": len(d_events),
            "docket_events_count": len(docket_events),
            "timeline_entries": len(timeline),
            "communication_types": dict(comm_types),
            "actor_violation_types": av_by_type,
            "actor_violation_severity": av_by_severity,
        },
        "authority_map": {k: v for k, v in AUTHORITY_MAP.items()},
        "authority_mappings": authority_mappings[:50],
        "timeline": timeline[:100],
        "filing_recommendations": recommendations,
        "evidence_quotes_sample": evidence_quotes[:20],
        "actor_violations_sample": actor_violations[:20],
        "judicial_violations_detail": judicial_violations[:20],
        "foc_authority_entries": foc_authority[:20],
        "d_drive_events_detail": d_events[:20],
        "docket_events_detail": docket_events[:20],
    }

    # ── Write JSON ──
    json_path = REPORTS_DIR / "tool_235_rusco_exparte_tracker.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n  JSON → {json_path}")

    # ── Write MD report ──
    md_path = REPORTS_DIR / "tool_235_rusco_exparte_tracker.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Tool #235 — Rusco Ex Parte Communication Tracker\n\n")
        f.write(f"**Generated:** {ts.strftime('%Y-%m-%d %H:%M')}  \n")
        f.write("**Case:** Pigors v. Watson (2024-001507-DC)  \n")
        f.write("**Subject:** Pamela Rusco (FOC) — Ex Parte Communications  \n\n")

        f.write("---\n\n## Summary\n\n")
        f.write(f"| Source | Count |\n|--------|-------|\n")
        f.write(f"| Evidence Quotes (Rusco/FOC) | {len(evidence_quotes)} |\n")
        f.write(f"| Actor Violations (Rusco) | {len(actor_violations)} |\n")
        f.write(f"| Judicial Violations (FOC-related) | {len(judicial_violations)} |\n")
        f.write(f"| FOC Authority Entries | {len(foc_authority)} |\n")
        f.write(f"| D-Drive Events (FOC) | {len(d_events)} |\n")
        f.write(f"| Docket Events (FOC) | {len(docket_events)} |\n")
        f.write(f"| **Timeline Entries** | **{len(timeline)}** |\n\n")

        f.write("### Communication Type Breakdown\n\n")
        f.write("| Type | Count |\n|------|-------|\n")
        for ct, cnt in sorted(comm_types.items(), key=lambda x: -x[1]):
            f.write(f"| {ct} | {cnt} |\n")
        f.write("\n")

        # Authority mapping
        f.write("---\n\n## Applicable Legal Authorities\n\n")
        for key, auth in AUTHORITY_MAP.items():
            f.write(f"### {auth['cite']}\n")
            f.write(f"**Text:** {auth['text']}  \n")
            f.write(f"**Relevance:** {auth['relevance']}  \n\n")

        # Timeline
        f.write("---\n\n## Chronological Timeline of Violations\n\n")
        f.write("| # | Date | Source | Type | Severity | Description |\n")
        f.write("|---|------|--------|------|----------|-------------|\n")
        for i, t in enumerate(timeline[:60], 1):
            desc = safe_trunc(t["description"], 100).replace('|', '/')
            f.write(f"| {i} | {t['date'] or 'N/A'} | {t['source']} | "
                    f"{t['type']} | {t['severity']} | {desc} |\n")
        if len(timeline) > 60:
            f.write(f"\n*({len(timeline) - 60} additional entries in JSON)*\n")
        f.write("\n")

        # Filing recommendations
        f.write("---\n\n## Filing Recommendations\n\n")
        for i, rec in enumerate(recommendations, 1):
            f.write(f"### {i}. {rec['filing']} — Priority: {rec['priority']}\n\n")
            f.write(f"**Basis:** {rec['basis']}  \n")
            f.write(f"**Authority:** {rec['authority']}  \n")
            f.write(f"**Supporting Evidence Count:** {rec['evidence_count']}  \n\n")

        # Actor violation severity breakdown
        if av_by_severity:
            f.write("---\n\n## Actor Violation Severity Distribution\n\n")
            f.write("| Severity | Count |\n|----------|-------|\n")
            for sev, cnt in sorted(av_by_severity.items()):
                f.write(f"| {sev} | {cnt} |\n")
            f.write("\n")

        # Sample evidence
        f.write("---\n\n## Key Evidence Samples\n\n")
        shown = 0
        for eq in evidence_quotes:
            if eq["communication_type"] in ("HEALTHWEST_CONTACT", "IMPROPER_SERVICE",
                                             "DIRECT_CONTACT", "EXCLUDED_PARTY_COMMUNICATION"):
                f.write(f"**[EQ-{eq['id']}]** ({eq['communication_type']}) — {eq.get('date_ref', 'N/A')}  \n")
                f.write(f"> {safe_trunc(eq['text'], 300)}  \n\n")
                shown += 1
                if shown >= 15:
                    break
        if shown == 0:
            for eq in evidence_quotes[:10]:
                f.write(f"**[EQ-{eq['id']}]** ({eq['communication_type']}) — {eq.get('date_ref', 'N/A')}  \n")
                f.write(f"> {safe_trunc(eq['text'], 300)}  \n\n")

        f.write("\n---\n*Generated by LitigationOS Tool #235*\n")

    print(f"  MD  → {md_path}")

    # ── Console summary ──
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Total evidence items:     {len(evidence_quotes)}")
    print(f"  Actor violations:         {len(actor_violations)}")
    print(f"  Judicial violations:      {len(judicial_violations)}")
    print(f"  Timeline entries:         {len(timeline)}")
    print(f"  Filing recommendations:   {len(recommendations)}")
    for rec in recommendations:
        print(f"    [{rec['priority']}] {rec['filing']}")
    print("=" * 70)
    print("  COMPLETE")


if __name__ == "__main__":
    main()
