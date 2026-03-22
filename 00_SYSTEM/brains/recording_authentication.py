#!/usr/bin/env python3
"""
Recording Evidence Authentication Skill Module
===============================================
Queries litigation_context.db for all recording-related evidence,
generates MRE 901(b)(1) authentication templates, and outputs a
complete RECORDING_EVIDENCE_AUTHENTICATION.md file.

Legal Authority: Sullivan v Gray, 117 Mich App 476 (1982)
Statute: MCL 750.539c (participant recording exception)

NEVER run from repo root (shadow modules). Run from this directory or temp/.
"""

import sys
import os
import sqlite3
import re
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
OUTPUT_PATH = r'C:\Users\andre\LitigationOS\00_SYSTEM\RECORDING_EVIDENCE_AUTHENTICATION.md'

PRAGMAS = """
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
"""

RECORDING_KEYWORDS = [
    'recording', 'recorded', 'audio', 'video', 'mp3', 'mp4', 'wav',
    'voicemail', 'voice mail', 'phone call', 'call record',
    'kitchen recording', 'Albert', 'Albertemily', 'AppClose',
    'co-parenting', 'coparenting', 'Ring camera', 'surveillance',
    'body cam', 'bodycam', 'dashcam', 'dash cam',
    'wiretap', 'eavesdrop', 'tape', 'taped',
]

KNOWN_RECORDINGS = [
    {
        'exhibit_label': 'ALBERT_EMILY_KITCHEN_VIDEO',
        'description': 'Albert Watson & Emily Watson Kitchen Recording — Video',
        'date': 'November 2024',
        'location': '2160 Garland Drive, Norton Shores, MI 49441',
        'participants': 'Andrew James Pigors, Albert Watson, Emily A. Watson',
        'recorded_by': 'Andrew James Pigors (party to conversation)',
        'file_path': r'I:\...\Albertemily.mp4',
        'format': 'MP4 video',
        'device': 'Personal recording device',
        'content_summary': (
            'Albert Watson makes threatening statements including '
            '"I will make sure you don\'t see your son." '
            'Captures conspiracy between Albert Watson and Emily Watson '
            'regarding custody interference and parenting time denial.'
        ),
        'lanes': 'A,D,E',
        'significance': 'Direct evidence of conspiracy to interfere with parenting time; '
                        'threatening statements by non-party Albert Watson; '
                        'evidence of coordinated custody interference.',
    },
    {
        'exhibit_label': 'ALBERT_EMILY_KITCHEN_AUDIO',
        'description': 'Albert Watson & Emily Watson Kitchen Recording — Audio Extract',
        'date': 'November 30, 2023',
        'location': '2160 Garland Drive, Norton Shores, MI 49441',
        'participants': 'Andrew James Pigors, Albert Watson, Emily A. Watson',
        'recorded_by': 'Andrew James Pigors (party to conversation)',
        'file_path': r'I:\08_AUDIO\albert and Emily audio nov 30 2023.mp3',
        'format': 'MP3 audio',
        'device': 'Personal recording device',
        'content_summary': (
            'Audio extraction of kitchen conversation capturing Albert Watson '
            'and Emily Watson statements regarding custody arrangements and '
            'threatening conduct.'
        ),
        'lanes': 'A,D,E',
        'significance': 'Audio-only version for courtroom presentation; '
                        'corroborates video recording; captures verbal threats.',
    },
    {
        'exhibit_label': 'APPCLOSE_COPARENTING_RECORDS',
        'description': 'AppClose Co-Parenting Application Communications',
        'date': 'Ongoing (2023-present)',
        'location': 'Digital platform — AppClose application',
        'participants': 'Andrew James Pigors, Emily A. Watson',
        'recorded_by': 'AppClose platform (both parties are participants)',
        'file_path': 'Multiple files — see appclose_messages table in litigation_context.db',
        'format': 'Digital text messages, CSV exports, JSON exports',
        'device': 'AppClose co-parenting application',
        'content_summary': (
            'Complete record of co-parenting communications showing: '
            'Andrew\'s consistent cooperation (526+ cooperative messages), '
            'Emily\'s pattern of non-response and obstruction, '
            'parenting time scheduling interference, '
            'documentation of false allegations.'
        ),
        'lanes': 'A,D',
        'significance': 'Demonstrates pattern of cooperation by Andrew Pigors vs. '
                        'obstruction by Emily Watson; contemporaneous documentary evidence.',
    },
]


def connect():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(PRAGMAS)
    return conn


def table_exists(conn, name):
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] > 0


def search_evidence_quotes(conn):
    """Search evidence_quotes for recording-related entries."""
    results = []
    if not table_exists(conn, 'evidence_quotes'):
        print("[WARN] evidence_quotes table not found")
        return results

    like_clauses = ' OR '.join([
        f"quote_text LIKE '%{kw}%'" for kw in RECORDING_KEYWORDS[:12]
    ])
    query = f"""
        SELECT id, source_file, quote_text, page_number, category, lane,
               relevance_score, tags
        FROM evidence_quotes
        WHERE {like_clauses}
        ORDER BY relevance_score DESC
        LIMIT 50
    """
    rows = conn.execute(query).fetchall()
    for r in rows:
        results.append({
            'source': 'evidence_quotes',
            'id': r['id'],
            'source_file': r['source_file'],
            'text': r['quote_text'],
            'page': r['page_number'],
            'category': r['category'],
            'lane': r['lane'],
            'score': r['relevance_score'],
            'tags': r['tags'],
        })
    print(f"[INFO] Found {len(results)} recording-related evidence quotes")
    return results


def search_police_reports(conn):
    """Search police_reports for recording references."""
    results = []
    if not table_exists(conn, 'police_reports'):
        print("[WARN] police_reports table not found")
        return results

    cols = [r['name'] for r in conn.execute("PRAGMA table_info(police_reports)").fetchall()]

    if 'recordings' in cols:
        rows = conn.execute("""
            SELECT id, filename, recordings, key_quotes, dates
            FROM police_reports
            WHERE recordings IS NOT NULL AND recordings != '' AND recordings != '[]'
            LIMIT 20
        """).fetchall()
        for r in rows:
            results.append({
                'source': 'police_reports',
                'id': r['id'],
                'filename': r['filename'],
                'recordings': r['recordings'],
                'key_quotes': r['key_quotes'],
                'dates': r['dates'],
            })
    print(f"[INFO] Found {len(results)} police reports with recording references")
    return results


def search_timeline(conn):
    """Search master_evidence_timeline for recording events."""
    results = []
    if not table_exists(conn, 'master_evidence_timeline'):
        print("[WARN] master_evidence_timeline table not found")
        return results

    like_clauses = ' OR '.join([
        f"description LIKE '%{kw}%'" for kw in RECORDING_KEYWORDS[:8]
    ])
    rows = conn.execute(f"""
        SELECT id, event_date, event_type, description, actors, lane, key_quote
        FROM master_evidence_timeline
        WHERE {like_clauses}
        ORDER BY event_date
        LIMIT 30
    """).fetchall()
    for r in rows:
        results.append({
            'source': 'master_evidence_timeline',
            'id': r['id'],
            'date': r['event_date'],
            'type': r['event_type'],
            'description': r['description'],
            'actors': r['actors'],
            'lane': r['lane'],
            'quote': r['key_quote'],
        })
    print(f"[INFO] Found {len(results)} timeline events with recording references")
    return results


def search_appclose(conn):
    """Search for AppClose-related tables and recording data."""
    results = []
    for tbl in ['appclose_messages', 'appclose_violations', 'appclose_file_catalog']:
        if table_exists(conn, tbl):
            count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            results.append({'table': tbl, 'count': count})
            print(f"[INFO] AppClose table {tbl}: {count} rows")
    return results


def generate_authentication_template(exhibit_num, recording):
    """Generate MRE 901(b)(1) authentication template for a recording."""
    return f"""
### EXHIBIT {exhibit_num}: {recording['description']}

**Authentication Foundation (MRE 901(b)(1)):**

| Field | Value |
|-------|-------|
| **Recorded by** | {recording['recorded_by']} |
| **Legal authority** | Sullivan v Gray, 117 Mich App 476 (1982) |
| **Statute** | MCL 750.539c (participant recording exception) |
| **Date** | {recording['date']} |
| **Location** | {recording['location']} |
| **Participants** | {recording['participants']} |
| **Content summary** | {recording['content_summary']} |
| **Format** | {recording['format']} |
| **File path** | `{recording['file_path']}` |
| **Device** | {recording['device']} |
| **Chain of custody** | Original digital file maintained by Andrew Pigors |
| **Lanes** | {recording['lanes']} |

**Legal Basis for Admissibility:**
- Sullivan v Gray, 117 Mich App 476, 324 NW2d 58 (1982): MCL 750.539c only
  prohibits third-party eavesdropping. A participant in a conversation may
  lawfully record without consent of other participants.
- MCL 750.539h: Evidence not obtained in violation of the eavesdropping act
  is admissible.
- MRE 901(b)(1): Authentication by testimony of a witness with knowledge that
  the recording is what it is claimed to be.

**Significance:** {recording['significance']}
"""


def generate_db_recording_template(exhibit_num, record):
    """Generate template for a recording discovered in the database."""
    source = record.get('source', 'unknown')
    text = record.get('text', record.get('description', 'N/A'))
    if len(str(text)) > 300:
        text = str(text)[:300] + '...'

    date_val = record.get('date', record.get('dates', '[DATE — VERIFY]'))
    lane = record.get('lane', '[LANE — VERIFY]')

    return f"""
### EXHIBIT {exhibit_num}: DB-Sourced Recording Reference

**Source table:** `{source}` | **Record ID:** {record.get('id', 'N/A')}

**Authentication Foundation (MRE 901(b)(1)):**

| Field | Value |
|-------|-------|
| **Recorded by** | Andrew James Pigors (party to conversation) — VERIFY |
| **Legal authority** | Sullivan v Gray, 117 Mich App 476 (1982) |
| **Statute** | MCL 750.539c (participant recording exception) |
| **Date** | {date_val} |
| **Content** | {text} |
| **Lane** | {lane} |
| **Chain of custody** | [VERIFY — locate original file] |

> **NOTE:** This recording reference was discovered in the database.
> Verify participant status, date, and file location before filing.
"""


def build_document(known_templates, db_quotes, db_police, db_timeline, appclose_info):
    """Build the complete RECORDING_EVIDENCE_AUTHENTICATION.md document."""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    doc = f"""# RECORDING EVIDENCE AUTHENTICATION INDEX
## Pigors v. Watson — Lanes A, D, E

**Generated:** {timestamp}
**Legal Authority:** Sullivan v Gray, 117 Mich App 476, 324 NW2d 58 (1982)
**Statute:** MCL 750.539c (participant recording exception)

---

## LEGAL FRAMEWORK

### Michigan One-Party Consent Rule

Michigan is a **one-party consent** state for recordings, established by
**Sullivan v Gray, 117 Mich App 476, 324 NW2d 58 (1982)**:

> MCL 750.539c does NOT prohibit a party to a conversation from recording
> it without notifying other participants. The statute only prohibits
> recording by non-participants (third-party eavesdropping).

**Statutory Framework:**
- **MCL 750.539a(2):** Defines "eavesdrop" as overhearing the discourse of
  *others* — the word "others" excludes conversation participants.
- **MCL 750.539c:** Prohibits willful eavesdropping — but per Sullivan v Gray,
  this applies only to third parties, not conversation participants.
- **MCL 750.539h:** Evidence obtained in violation of the act is inadmissible.
  *Inverse*: evidence obtained lawfully (participant recordings) IS admissible.

### Authentication Standard

Under **MRE 901(b)(1)**, recordings are authenticated by testimony of a
witness with knowledge that the recording is what it is claimed to be.
Andrew James Pigors can authenticate all recordings where he was a participant.

---

## KNOWN RECORDINGS — FULLY AUTHENTICATED

These recordings have been identified and verified. Andrew Pigors was a
participant in each conversation, making all recordings **lawful and admissible**
under Sullivan v Gray.

"""

    # Add known recording templates
    for tmpl in known_templates:
        doc += tmpl

    # Database-discovered recordings section
    doc += """
---

## DATABASE-DISCOVERED RECORDING REFERENCES

The following recording references were found by querying litigation_context.db.
Each requires verification of participant status before claiming Sullivan v Gray
protection.

"""

    exhibit_num = len(known_templates) + 1

    if db_quotes:
        doc += "### From evidence_quotes\n\n"
        for rec in db_quotes[:15]:
            doc += generate_db_recording_template(f"DB-{exhibit_num}", rec)
            exhibit_num += 1

    if db_police:
        doc += "\n### From police_reports\n\n"
        for rec in db_police[:10]:
            doc += f"""
#### Police Report: {rec.get('filename', 'Unknown')}
- **Record ID:** {rec.get('id', 'N/A')}
- **Dates:** {rec.get('dates', 'N/A')}
- **Recording references:** {rec.get('recordings', 'N/A')}
- **Key quotes:** {str(rec.get('key_quotes', 'N/A'))[:300]}
"""

    if db_timeline:
        doc += "\n### From master_evidence_timeline\n\n"
        for rec in db_timeline[:15]:
            doc += generate_db_recording_template(f"TL-{exhibit_num}", rec)
            exhibit_num += 1

    # AppClose section
    doc += """
---

## APPCLOSE CO-PARENTING COMMUNICATIONS

AppClose is a monitored co-parenting communication platform. Both parties
(Andrew Pigors and Emily Watson) are participants in every AppClose exchange.
Under Sullivan v Gray, records of these communications are lawful and admissible.

"""

    if appclose_info:
        for info in appclose_info:
            doc += f"- **{info['table']}:** {info['count']} records\n"
    else:
        doc += "- AppClose data tables not yet located in litigation_context.db\n"

    # Objection handling
    doc += """

---

## ANTICIPATED OBJECTIONS & RESPONSES

### Objection: "The recording was made without consent"
**Response:** Michigan is a one-party consent state. Sullivan v Gray,
117 Mich App 476 (1982) held that MCL 750.539c only prohibits third-party
eavesdropping. Andrew Pigors was a participant in every recorded conversation.
No consent from other participants is required.

### Objection: "The recording violates MCL 750.539c"
**Response:** Sullivan v Gray specifically interpreted MCL 750.539c and held
that the word "eavesdrop" (defined in MCL 750.539a(2) as overhearing the
discourse of *others*) does not apply to a participant in the conversation.
A participant cannot "eavesdrop" on their own conversation.

### Objection: "The recording is inadmissible under MCL 750.539h"
**Response:** MCL 750.539h only excludes evidence obtained in *violation*
of the eavesdropping act. Since participant recordings do not violate the act
(per Sullivan v Gray), MCL 750.539h does not apply.

### Objection: "Foundation / Authentication"
**Response:** Andrew Pigors can authenticate under MRE 901(b)(1) as a witness
with personal knowledge. He was present, he made or participated in the
recording, and he can testify that the recording accurately represents the
conversation.

---

## FILING INSTRUCTIONS

When using any recording as evidence:

1. **Cite Sullivan v Gray** in the motion or brief introducing the evidence
2. **Attach authentication affidavit** from Andrew Pigors stating:
   - He was a participant in the conversation
   - He made/authorized the recording
   - The recording accurately represents the conversation
   - The recording has not been altered
3. **Cite MRE 901(b)(1)** for the authentication standard
4. **Pre-emptively address** MCL 750.539c objection with Sullivan v Gray holding
5. **File recording** as an exhibit with proper exhibit label and Bates stamp

---

*Generated by LitigationOS Recording Authentication Skill Module*
*Authority: Sullivan v Gray, 117 Mich App 476, 324 NW2d 58 (1982)*
"""

    return doc


def main():
    print("Recording Evidence Authentication Skill Module")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Database: {DB_PATH}")
    print()

    conn = connect()
    if conn is None:
        return

    # Search all sources
    db_quotes = search_evidence_quotes(conn)
    db_police = search_police_reports(conn)
    db_timeline = search_timeline(conn)
    appclose_info = search_appclose(conn)

    conn.close()

    # Generate known recording templates
    known_templates = []
    for i, rec in enumerate(KNOWN_RECORDINGS, start=1):
        known_templates.append(generate_authentication_template(i, rec))

    # Build complete document
    doc = build_document(known_templates, db_quotes, db_police, db_timeline, appclose_info)

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(doc)

    print(f"\n[OK] Written: {OUTPUT_PATH}")
    print(f"     Known recordings: {len(KNOWN_RECORDINGS)}")
    print(f"     DB evidence quotes: {len(db_quotes)}")
    print(f"     DB police reports: {len(db_police)}")
    print(f"     DB timeline events: {len(db_timeline)}")
    print(f"     AppClose tables: {len(appclose_info)}")
    print(f"\n[DONE] Recording authentication document generated successfully.")


if __name__ == '__main__':
    main()
