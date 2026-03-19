#!/usr/bin/env python3
"""
Timeline Exhibit Engine - Pigors v. Watson (2024-001507-DC)
Generates court-ready chronological timeline exhibits from litigation DB.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import json
import hashlib
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
BASE_DIR = r'C:\Users\andre\LitigationOS\00_SYSTEM'
TRIAL_DIR = r'C:\Users\andre\LitigationOS\02_TRIAL_14TH'

CASE_CAPTION = "Pigors v. Watson, Case No. 2024-001507-DC"
COURT = "14th Circuit Court, Muskegon County, Michigan"
CHILD_DOB = "2022-11-09"

# Phase definitions: (label, start_date, end_date)
PHASES = [
    ("Pre-Filing: Relationship History & PPO Weaponization",
     "2022-01-01", "2024-03-31"),
    ("Case Filing: Custody Petition & Initial Orders",
     "2024-04-01", "2024-08-31"),
    ("Ex Parte Orders: McNeill's Unauthorized Proceedings",
     "2024-09-01", "2024-12-31"),
    ("Escalation: PPO Weaponization & False Police Reports",
     "2025-01-01", "2025-01-31"),
    ("First Jailing: February 2025 Incarceration",
     "2025-02-01", "2025-02-28"),
    ("Alienation: Parenting Time Reduction 50% -> 0%",
     "2025-03-01", "2025-10-31"),
    ("Second Jailing: November 2025 - January 2026",
     "2025-11-01", "2026-01-06"),
    ("Appeals & Current Filings",
     "2026-01-07", "2099-12-31"),
]

CATEGORY_PRIORITY = {
    'order': 10, 'ex_parte': 10, 'hearing': 9, 'filing': 8,
    'violation': 6, 'incident': 5, 'chronology_event': 4,
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-50000")
    conn.row_factory = sqlite3.Row
    return conn


def normalize_date(d):
    """Parse various date formats to YYYY-MM-DD."""
    if not d:
        return None
    d = str(d).strip()
    # Already ISO
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', d)
    if m:
        return m.group(1)
    # MM/DD/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', d)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return d[:10] if len(d) >= 10 else d


def clean_text(t):
    """Replace unicode with ASCII for court docs."""
    if not t:
        return ""
    t = str(t)
    replacements = {
        '\u2014': '--', '\u2013': '-', '\u2019': "'", '\u2018': "'",
        '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
        '\u2192': '->', '\u2190': '<-', '\u00a0': ' ', '\u200b': '',
        '\u2011': '-', '\u00b7': '*', '\u25cf': '*', '\u25cb': 'o',
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    # Strip remaining non-ASCII
    t = t.encode('ascii', 'replace').decode('ascii')
    return t.strip()


def truncate(t, maxlen=300):
    t = clean_text(t)
    if len(t) <= maxlen:
        return t
    return t[:maxlen-3] + "..."


def fingerprint(event):
    """Dedup fingerprint: date + type + first 60 chars of title."""
    title_norm = re.sub(r'\s+', ' ', clean_text(event['title'] or ''))[:60].lower()
    return f"{event['event_date']}|{event['event_type']}|{title_norm}"


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------
class TimelineExhibitEngine:
    def __init__(self):
        self.conn = get_connection()
        self.events = []
        self.evidence_map = defaultdict(list)  # event_date -> evidence quotes
        self.phase_events = defaultdict(list)
        self.stats = {}

    def load_events(self):
        print("[1/6] Loading timeline events...")
        cur = self.conn.execute("""
            SELECT id, event_date, case_id, case_type, event_type, actor,
                   title, description, harm_to_andrew, authority_violated,
                   relief_sought, source_table, source_id, evidence_refs,
                   verified_sources
            FROM master_chronological_timeline
            ORDER BY event_date, id
        """)
        raw = [dict(r) for r in cur.fetchall()]
        print(f"  Loaded {len(raw)} raw events")
        self.stats['raw_count'] = len(raw)
        return raw

    def deduplicate(self, raw_events):
        print("[2/6] Deduplicating events...")
        seen = {}
        deduped = []
        for ev in raw_events:
            fp = fingerprint(ev)
            if fp in seen:
                # Merge: keep the one with more description
                existing = seen[fp]
                if len(ev.get('description') or '') > len(existing.get('description') or ''):
                    seen[fp] = ev
                    # Replace in deduped list
                    for i, d in enumerate(deduped):
                        if fingerprint(d) == fp:
                            deduped[i] = ev
                            break
            else:
                seen[fp] = ev
                deduped.append(ev)
        print(f"  Deduplicated: {len(raw_events)} -> {len(deduped)} events")
        self.stats['deduped_count'] = len(deduped)
        return deduped

    def load_evidence(self):
        print("[3/6] Loading evidence quote counts by date...")
        # Only load counts per date, not full records (saves memory on 300K+ table)
        cur = self.conn.execute("""
            SELECT date_ref, COUNT(*) as cnt, 
                   GROUP_CONCAT(DISTINCT evidence_category) as cats
            FROM evidence_quotes
            WHERE date_ref IS NOT NULL AND date_ref != ''
            GROUP BY date_ref
        """)
        count = 0
        for row in cur:
            r = dict(row)
            d = normalize_date(r['date_ref'])
            if d and len(d) >= 10:
                self.evidence_map[d] = [{'count': r['cnt'], 'categories': r['cats']}]
                count += r['cnt']
        print(f"  Indexed {count} evidence quotes across {len(self.evidence_map)} dates")
        self.stats['evidence_linked'] = count

    def assign_phases(self, events):
        print("[4/6] Assigning phases...")
        for ev in events:
            d = normalize_date(ev['event_date'])
            if not d:
                continue
            assigned = False
            for phase_name, start, end in PHASES:
                if start <= d <= end:
                    self.phase_events[phase_name].append(ev)
                    ev['_phase'] = phase_name
                    assigned = True
                    break
            if not assigned:
                self.phase_events["Pre-Filing: Relationship History & PPO Weaponization"].append(ev)
                ev['_phase'] = PHASES[0][0]
        for p in PHASES:
            n = len(self.phase_events.get(p[0], []))
            print(f"  {p[0][:50]:50s} -> {n:5d} events")

    def rank_events(self, events, top_n=None):
        """Rank events by importance for court exhibit."""
        def score(ev):
            s = CATEGORY_PRIORITY.get(ev.get('event_type', ''), 3)
            if ev.get('authority_violated'):
                s += 3
            if ev.get('harm_to_andrew'):
                s += 2
            if ev.get('relief_sought'):
                s += 1
            d = normalize_date(ev['event_date'])
            if d and d in self.evidence_map:
                ec = self.get_evidence_count(d)
                s += min(ec, 3)
            return s
        ranked = sorted(events, key=lambda e: (-score(e), e['event_date']))
        if top_n:
            return ranked[:top_n]
        return ranked

    def get_evidence_for_date(self, date_str):
        """Returns list of evidence summary dicts for a date."""
        d = normalize_date(date_str)
        if not d:
            return []
        return self.evidence_map.get(d, [])

    def get_evidence_count(self, date_str):
        """Returns total evidence quote count for a date."""
        d = normalize_date(date_str)
        if not d:
            return 0
        entries = self.evidence_map.get(d, [])
        return entries[0]['count'] if entries else 0

    # ------ Output generators ------

    def generate_markdown(self, events):
        print("[5/6] Generating Markdown timeline...")
        lines = []
        lines.append(f"# MASTER CHRONOLOGICAL TIMELINE EXHIBIT")
        lines.append(f"## {CASE_CAPTION}")
        lines.append(f"### {COURT}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        lines.append(f"**Total Events:** {len(events)}")
        lines.append(f"**Date Range:** {normalize_date(events[0]['event_date'])} to {normalize_date(events[-1]['event_date'])}")
        lines.append(f"**Child DOB:** {CHILD_DOB}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for i, (phase_name, _, _) in enumerate(PHASES, 1):
            count = len(self.phase_events.get(phase_name, []))
            if count > 0:
                anchor = re.sub(r'[^a-z0-9]+', '-', phase_name.lower()).strip('-')
                lines.append(f"{i}. [{phase_name}](#{anchor}) ({count} events)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Phase sections
        for phase_name, start, end in PHASES:
            phase_evts = self.phase_events.get(phase_name, [])
            if not phase_evts:
                continue

            lines.append(f"## {phase_name}")
            lines.append(f"*Period: {start} to {end} | {len(phase_evts)} events*")
            lines.append("")

            # Event table header
            lines.append("| # | Date | Type | Actor | Event | Evidence |")
            lines.append("|---|------|------|-------|-------|----------|")

            for idx, ev in enumerate(phase_evts, 1):
                d = normalize_date(ev['event_date']) or '?'
                etype = clean_text(ev.get('event_type') or 'N/A')
                actor = truncate(ev.get('actor') or 'N/A', 30)
                title = truncate(ev.get('title') or '', 120)
                # Evidence refs
                ev_refs = []
                if ev.get('evidence_refs'):
                    ev_refs.append(clean_text(ev['evidence_refs'])[:40])
                linked_count = self.get_evidence_count(ev['event_date'])
                if linked_count:
                    ev_refs.append(f"{linked_count} quote(s)")
                ref_str = "; ".join(ev_refs) if ev_refs else "--"

                lines.append(f"| {idx} | {d} | {etype} | {actor} | {title} | {ref_str} |")

            lines.append("")

            # Key events detail (orders, hearings, ex parte)
            key_types = {'order', 'hearing', 'ex_parte', 'filing'}
            key_evts = [e for e in phase_evts if e.get('event_type') in key_types]
            if key_evts:
                lines.append(f"### Key Events Detail - {phase_name}")
                lines.append("")
                for ev in key_evts[:20]:
                    d = normalize_date(ev['event_date']) or '?'
                    lines.append(f"**{d} - {truncate(ev.get('title',''), 100)}**")
                    if ev.get('description'):
                        lines.append(f"> {truncate(ev['description'], 250)}")
                    if ev.get('harm_to_andrew'):
                        lines.append(f"> *Harm:* {truncate(ev['harm_to_andrew'], 150)}")
                    if ev.get('authority_violated'):
                        lines.append(f"> *Authority Violated:* {truncate(ev['authority_violated'], 150)}")
                    if ev.get('relief_sought'):
                        lines.append(f"> *Relief Sought:* {truncate(ev['relief_sought'], 150)}")
                    lines.append("")
            lines.append("---")
            lines.append("")

        # Summary statistics
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- Total raw events in database: {self.stats.get('raw_count', 'N/A')}")
        lines.append(f"- After deduplication: {self.stats.get('deduped_count', 'N/A')}")
        lines.append(f"- Evidence quotes linked by date: {self.stats.get('evidence_linked', 'N/A')}")
        lines.append("")
        lines.append("### Events by Type")
        type_counts = defaultdict(int)
        for ev in events:
            type_counts[ev.get('event_type', 'unknown')] += 1
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {t}: {c}")
        lines.append("")
        lines.append("### Events by Actor")
        actor_counts = defaultdict(int)
        for ev in events:
            a = (ev.get('actor') or 'Unknown')[:40]
            actor_counts[a] += 1
        for a, c in sorted(actor_counts.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"- {a}: {c}")
        lines.append("")
        lines.append("---")
        lines.append(f"*This exhibit was programmatically generated from the litigation database.*")
        lines.append(f"*{CASE_CAPTION} | {COURT}*")
        return "\n".join(lines)

    def generate_html(self, events):
        print("[5b/6] Generating HTML timeline...")
        phase_html_blocks = []
        for pi, (phase_name, start, end) in enumerate(PHASES):
            phase_evts = self.phase_events.get(phase_name, [])
            if not phase_evts:
                continue
            rows = []
            for idx, ev in enumerate(phase_evts, 1):
                d = normalize_date(ev['event_date']) or '?'
                etype = clean_text(ev.get('event_type') or 'N/A')
                actor = truncate(ev.get('actor') or 'N/A', 40)
                title = truncate(ev.get('title') or '', 150)
                desc = truncate(ev.get('description') or '', 200)
                harm = clean_text(ev.get('harm_to_andrew') or '')
                auth = clean_text(ev.get('authority_violated') or '')
                linked_count = self.get_evidence_count(ev['event_date'])
                ref_str = f"{linked_count} quote(s)" if linked_count else "--"
                if ev.get('evidence_refs'):
                    ref_str = clean_text(ev['evidence_refs'])[:50] + (f"; {ref_str}" if linked_count else "")

                type_class = etype.replace('_', '-')
                detail_html = ""
                if desc:
                    detail_html += f"<div class='detail'>{_esc(desc)}</div>"
                if harm:
                    detail_html += f"<div class='harm'><b>Harm:</b> {_esc(harm[:150])}</div>"
                if auth:
                    detail_html += f"<div class='auth'><b>Authority Violated:</b> {_esc(auth[:150])}</div>"

                rows.append(f"""<tr class="type-{type_class}">
<td class="num">{idx}</td>
<td class="date">{_esc(d)}</td>
<td class="type"><span class="badge badge-{type_class}">{_esc(etype)}</span></td>
<td class="actor">{_esc(actor)}</td>
<td class="event">{_esc(title)}{detail_html}</td>
<td class="evidence">{_esc(ref_str)}</td>
</tr>""")

            table_rows = "\n".join(rows)
            phase_html_blocks.append(f"""
<div class="phase" id="phase-{pi}">
  <div class="phase-header" onclick="togglePhase({pi})">
    <span class="toggle" id="toggle-{pi}">[-]</span>
    <h2>{_esc(phase_name)}</h2>
    <span class="phase-meta">{start} to {end} | {len(phase_evts)} events</span>
  </div>
  <div class="phase-body" id="body-{pi}">
    <table>
      <thead><tr><th>#</th><th>Date</th><th>Type</th><th>Actor</th><th>Event</th><th>Evidence</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </div>
</div>""")

        phases_html = "\n".join(phase_html_blocks)
        gen_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Master Chronological Timeline - {_esc(CASE_CAPTION)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; background: #f5f5f5; color: #222; line-height: 1.5; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
header {{ background: #1a237e; color: white; padding: 30px 20px; margin-bottom: 20px; border-radius: 8px; }}
header h1 {{ font-size: 1.8em; margin-bottom: 8px; }}
header .meta {{ opacity: 0.85; font-size: 0.95em; }}
.stats {{ display: flex; gap: 15px; flex-wrap: wrap; margin: 15px 0; }}
.stat {{ background: white; padding: 12px 20px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.stat .num {{ font-size: 1.6em; font-weight: bold; color: #1a237e; }}
.stat .label {{ font-size: 0.85em; color: #666; }}
.phase {{ background: white; margin-bottom: 12px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }}
.phase-header {{ padding: 15px 20px; cursor: pointer; display: flex; align-items: center; gap: 12px; background: #e8eaf6; border-bottom: 2px solid #c5cae9; }}
.phase-header:hover {{ background: #d1d5f0; }}
.phase-header h2 {{ font-size: 1.1em; flex: 1; }}
.phase-meta {{ font-size: 0.85em; color: #555; white-space: nowrap; }}
.toggle {{ font-family: monospace; font-size: 1.2em; color: #1a237e; min-width: 25px; }}
.phase-body {{ padding: 0; }}
.phase-body.collapsed {{ display: none; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.88em; }}
thead {{ background: #f5f5f5; position: sticky; top: 0; }}
th {{ padding: 10px 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; }}
td {{ padding: 8px; border-bottom: 1px solid #eee; vertical-align: top; }}
.num {{ width: 40px; text-align: center; color: #999; }}
.date {{ width: 100px; font-weight: 600; white-space: nowrap; }}
.type {{ width: 90px; }}
.actor {{ width: 120px; }}
.evidence {{ width: 140px; font-size: 0.85em; color: #666; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }}
.badge-order {{ background: #ffcdd2; color: #b71c1c; }}
.badge-hearing {{ background: #fff9c4; color: #f57f17; }}
.badge-filing {{ background: #c8e6c9; color: #2e7d32; }}
.badge-incident {{ background: #e1bee7; color: #6a1b9a; }}
.badge-violation {{ background: #ffccbc; color: #bf360c; }}
.badge-ex-parte {{ background: #ff8a80; color: #d50000; }}
.badge-chronology-event {{ background: #b3e5fc; color: #01579b; }}
.detail {{ font-size: 0.85em; color: #555; margin-top: 4px; padding-left: 8px; border-left: 2px solid #ddd; }}
.harm {{ font-size: 0.85em; color: #c62828; margin-top: 3px; }}
.auth {{ font-size: 0.85em; color: #4a148c; margin-top: 3px; }}
tr.type-order {{ background: #fff8f8; }}
tr.type-ex-parte {{ background: #fff0f0; }}
tr.type-hearing {{ background: #fffde7; }}
footer {{ text-align: center; padding: 20px; color: #999; font-size: 0.85em; margin-top: 20px; }}
.filter-bar {{ padding: 10px 20px; background: white; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.filter-bar input {{ padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; width: 300px; font-size: 0.95em; }}
.filter-bar label {{ margin-left: 15px; font-size: 0.9em; }}
@media print {{
  .phase-header {{ cursor: default; }}
  .toggle {{ display: none; }}
  .filter-bar {{ display: none; }}
  .phase-body.collapsed {{ display: block !important; }}
  body {{ font-size: 10pt; }}
}}
</style>
</head>
<body>
<div class="container">
<header>
  <h1>MASTER CHRONOLOGICAL TIMELINE EXHIBIT</h1>
  <div class="meta">{_esc(CASE_CAPTION)} | {_esc(COURT)}</div>
  <div class="meta">Generated: {gen_date}</div>
</header>

<div class="stats">
  <div class="stat"><div class="num">{len(events)}</div><div class="label">Total Events</div></div>
  <div class="stat"><div class="num">{self.stats.get('raw_count','?')}</div><div class="label">Raw DB Events</div></div>
  <div class="stat"><div class="num">{self.stats.get('evidence_linked','?')}</div><div class="label">Evidence Links</div></div>
  <div class="stat"><div class="num">{len(PHASES)}</div><div class="label">Case Phases</div></div>
</div>

<div class="filter-bar">
  <input type="text" id="searchBox" placeholder="Search events..." onkeyup="filterEvents()">
  <label><input type="checkbox" id="keyOnly" onchange="filterEvents()"> Key events only (orders/hearings/filings)</label>
</div>

{phases_html}

<footer>
  <p>This exhibit was programmatically generated from the litigation database.</p>
  <p>{_esc(CASE_CAPTION)} | {_esc(COURT)}</p>
</footer>
</div>

<script>
function togglePhase(i) {{
  var body = document.getElementById('body-' + i);
  var toggle = document.getElementById('toggle-' + i);
  if (body.classList.contains('collapsed')) {{
    body.classList.remove('collapsed');
    toggle.textContent = '[-]';
  }} else {{
    body.classList.add('collapsed');
    toggle.textContent = '[+]';
  }}
}}

function filterEvents() {{
  var query = document.getElementById('searchBox').value.toLowerCase();
  var keyOnly = document.getElementById('keyOnly').checked;
  var keyTypes = ['order', 'hearing', 'filing', 'ex_parte', 'ex-parte'];
  var rows = document.querySelectorAll('tbody tr');
  rows.forEach(function(row) {{
    var text = row.textContent.toLowerCase();
    var matchSearch = !query || text.indexOf(query) >= 0;
    var matchKey = true;
    if (keyOnly) {{
      var typeBadge = row.querySelector('.badge');
      var rowType = typeBadge ? typeBadge.textContent.toLowerCase().trim() : '';
      matchKey = keyTypes.some(function(t) {{ return rowType.indexOf(t) >= 0; }});
    }}
    row.style.display = (matchSearch && matchKey) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
        return html

    def generate_court_exhibit(self, events):
        """Top 100 events formatted for court filing."""
        print("[5c/6] Generating court exhibit (top 100)...")
        ranked = self.rank_events(events, top_n=100)
        ranked.sort(key=lambda e: e['event_date'])

        lines = []
        lines.append("# CHRONOLOGICAL TIMELINE EXHIBIT")
        lines.append("")
        lines.append(f"**{CASE_CAPTION}**")
        lines.append(f"**{COURT}**")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("The following chronological timeline sets forth the key events")
        lines.append("relevant to this matter, drawn from court records, transcripts,")
        lines.append("and documentary evidence in the case file.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("| No. | Date | Event | Category | Evidence Reference | Filing Relevance |")
        lines.append("|-----|------|-------|----------|-------------------|------------------|")

        for idx, ev in enumerate(ranked, 1):
            d = normalize_date(ev['event_date']) or '?'
            title = truncate(ev.get('title') or '', 100)
            cat = clean_text(ev.get('event_type') or 'N/A')
            # Evidence
            ref_parts = []
            if ev.get('evidence_refs'):
                ref_parts.append(clean_text(ev['evidence_refs'])[:50])
            linked_count = self.get_evidence_count(ev['event_date'])
            if linked_count:
                ref_parts.append(f"{linked_count} supporting quote(s)")
            ref_str = "; ".join(ref_parts) if ref_parts else "See case file"
            # Filing relevance
            relevance_parts = []
            if ev.get('authority_violated'):
                relevance_parts.append(truncate(ev['authority_violated'], 60))
            if ev.get('harm_to_andrew'):
                relevance_parts.append(truncate(ev['harm_to_andrew'], 60))
            if ev.get('relief_sought'):
                relevance_parts.append(truncate(ev['relief_sought'], 60))
            relevance = "; ".join(relevance_parts) if relevance_parts else "Background"

            lines.append(f"| {idx} | {d} | {title} | {cat} | {ref_str} | {relevance} |")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**CERTIFICATION**")
        lines.append("")
        lines.append("I certify that the above timeline accurately reflects events")
        lines.append("documented in the case record for the above-captioned matter.")
        lines.append("")
        lines.append(f"Date: {datetime.now().strftime('%B %d, %Y')}")
        lines.append("")
        lines.append("_____________________________")
        lines.append("Andrew J. Pigors, Plaintiff")
        lines.append("")
        lines.append(f"*{CASE_CAPTION}*")
        return "\n".join(lines)

    def generate_json(self, events):
        print("[5d/6] Generating JSON summary...")
        phases_data = []
        for phase_name, start, end in PHASES:
            phase_evts = self.phase_events.get(phase_name, [])
            if not phase_evts:
                continue
            phase_entries = []
            for ev in phase_evts:
                ec = self.get_evidence_count(ev['event_date'])
                phase_entries.append({
                    'id': ev['id'],
                    'date': normalize_date(ev['event_date']),
                    'type': ev.get('event_type'),
                    'actor': clean_text(ev.get('actor') or ''),
                    'title': clean_text(ev.get('title') or ''),
                    'description': truncate(ev.get('description') or '', 200),
                    'case_type': ev.get('case_type'),
                    'harm': clean_text(ev.get('harm_to_andrew') or ''),
                    'authority_violated': clean_text(ev.get('authority_violated') or ''),
                    'relief_sought': clean_text(ev.get('relief_sought') or ''),
                    'evidence_refs': clean_text(ev.get('evidence_refs') or ''),
                    'evidence_quote_count': ec,
                })
            phases_data.append({
                'phase': phase_name,
                'start': start,
                'end': end,
                'event_count': len(phase_evts),
                'events': phase_entries,
            })

        return {
            'case': CASE_CAPTION,
            'court': COURT,
            'child_dob': CHILD_DOB,
            'generated': datetime.now().isoformat(),
            'stats': {
                'raw_events': self.stats.get('raw_count', 0),
                'deduped_events': self.stats.get('deduped_count', 0),
                'evidence_linked': self.stats.get('evidence_linked', 0),
                'phases': len([p for p in PHASES if self.phase_events.get(p[0])]),
            },
            'phases': phases_data,
        }

    def run(self):
        print(f"=" * 60)
        print(f"TIMELINE EXHIBIT ENGINE")
        print(f"{CASE_CAPTION}")
        print(f"=" * 60)
        print()

        raw = self.load_events()
        events = self.deduplicate(raw)
        self.load_evidence()
        self.assign_phases(events)
        self.events = events

        # Generate outputs
        md = self.generate_markdown(events)
        html = self.generate_html(events)
        court_md = self.generate_court_exhibit(events)
        json_data = self.generate_json(events)

        print("\n[6/6] Writing output files...")

        md_path = os.path.join(BASE_DIR, "MASTER_TIMELINE_EXHIBIT.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  -> {md_path} ({len(md):,} chars)")

        html_path = os.path.join(BASE_DIR, "MASTER_TIMELINE_EXHIBIT.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  -> {html_path} ({len(html):,} chars)")

        json_path = os.path.join(BASE_DIR, "TIMELINE_SUMMARY.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=True, indent=2)
        print(f"  -> {json_path}")

        court_path = os.path.join(TRIAL_DIR, "CHRONOLOGICAL_TIMELINE_EXHIBIT.md")
        with open(court_path, 'w', encoding='utf-8') as f:
            f.write(court_md)
        print(f"  -> {court_path} ({len(court_md):,} chars)")

        self.conn.close()

        print(f"\n{'=' * 60}")
        print(f"COMPLETE - {len(events)} events across {len([p for p in PHASES if self.phase_events.get(p[0])])} phases")
        print(f"{'=' * 60}")
        return events


def _esc(s):
    """HTML-escape."""
    if not s:
        return ""
    s = str(s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    engine = TimelineExhibitEngine()
    engine.run()
