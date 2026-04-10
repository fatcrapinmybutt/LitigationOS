"""
Phase 3: MBOX Email Extraction — Parse Starred.mbox, classify, persist to DB.
Extracts all emails from the 1.4 GB Gmail starred archive.
MEEK lane classification for evidence routing.
Persists to email_evidence table + FTS5 index in litigation_context.db.
"""
import mailbox
import os
import re
import json
import sqlite3
import time
from datetime import datetime
from collections import Counter

MBOX_PATH = r'C:\Users\andre\LitigationOS\10_EXTERNAL\Starred.mbox'
OUTPUT_DIR = r'J:\LitigationOS_CENTRAL\MBOX_EXTRACTED'
JSONL_PATH = os.path.join(OUTPUT_DIR, 'emails.jsonl')
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# MEEK lane patterns (priority order: E > D > F > C > A > B)
MEEK = [
    ('E', re.compile(r'McNeill|judicial|bias|JTC|canon|ex\s*parte|misconduct|benchbook|recus', re.I)),
    ('D', re.compile(r'PPO|protection\s*order|5907|contempt|stalk|harass', re.I)),
    ('F', re.compile(r'COA|366810|appeal|appellant|appell|brief.*court', re.I)),
    ('C', re.compile(r'federal|\u00a71983|civil\s*rights|conspiracy|1983', re.I)),
    ('A', re.compile(r'custody|parenting|001507|Watson|child|visitation|FOC|L\.D\.W|father|mother', re.I)),
    ('B', re.compile(r'Shady\s*Oaks|eviction|housing|trailer|002760|habitability|landlord|rent', re.I)),
]

def classify_lane(text):
    for lane, pat in MEEK:
        if pat.search(text):
            return lane
    return 'UNKNOWN'

def get_body(msg):
    """Extract plain text body, falling back to stripped HTML."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    cs = part.get_content_charset() or 'utf-8'
                    return payload.decode(cs, errors='replace')
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    cs = part.get_content_charset() or 'utf-8'
                    html = payload.decode(cs, errors='replace')
                    return re.sub(r'<[^>]+>', ' ', html)[:50000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            cs = msg.get_content_charset() or 'utf-8'
            return payload.decode(cs, errors='replace')
    return ''

def get_attachments(msg):
    names = []
    if msg.is_multipart():
        for part in msg.walk():
            fn = part.get_filename()
            if fn:
                names.append(fn)
    return names

t0 = time.time()
file_mb = os.path.getsize(MBOX_PATH) / 1048576

print("=" * 70)
print(f"PHASE 3: MBOX EMAIL EXTRACTION — {datetime.now():%Y-%m-%d %H:%M}")
print(f"Source: {MBOX_PATH} ({file_mb:.0f} MB)")
print("=" * 70)

# ══════════════════════════════════════════════════════════════
# PARSE MBOX
# ══════════════════════════════════════════════════════════════
print("\n▸ Parsing emails...")
mbox = mailbox.mbox(MBOX_PATH)

records = []
senders = Counter()
recipients_ctr = Counter()
lanes = Counter()
subjects_list = []
err_ct = 0

for i, msg in enumerate(mbox):
    try:
        sender = str(msg.get('From', 'Unknown'))
        recipient = str(msg.get('To', ''))
        date_str = str(msg.get('Date', ''))
        subject = str(msg.get('Subject', '(no subject)'))
        body = get_body(msg)
        attachments = get_attachments(msg)

        search_text = f"{subject} {body[:5000]}"
        lane = classify_lane(search_text)

        records.append({
            'email_id': i + 1,
            'sender': sender[:500],
            'recipient': recipient[:500],
            'date_sent': date_str[:200],
            'subject': subject[:500],
            'body_text': body[:50000],
            'body_length': len(body),
            'lane': lane,
            'has_attachment': 1 if attachments else 0,
            'attachment_names': '|'.join(attachments)[:1000] if attachments else '',
        })

        senders[sender[:80]] += 1
        if recipient:
            recipients_ctr[recipient[:80]] += 1
        lanes[lane] += 1
        subjects_list.append(subject[:120])
    except Exception as e:
        err_ct += 1
        if err_ct <= 5:
            print(f"  ⚠ Email {i+1} error: {e}")

    if (i + 1) % 500 == 0:
        print(f"  Processed {i + 1} emails...")

mbox.close()
total = len(records)
parse_time = time.time() - t0
print(f"\n  Total: {total} emails parsed in {parse_time:.1f}s ({err_ct} errors)")

# ══════════════════════════════════════════════════════════════
# WRITE JSONL ARCHIVE
# ══════════════════════════════════════════════════════════════
print(f"\n▸ Writing JSONL → {JSONL_PATH}")
with open(JSONL_PATH, 'w', encoding='utf-8') as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + '\n')
jsonl_mb = os.path.getsize(JSONL_PATH) / 1048576
print(f"  Written: {jsonl_mb:.1f} MB ({total} records)")

# ══════════════════════════════════════════════════════════════
# PERSIST TO litigation_context.db
# ══════════════════════════════════════════════════════════════
print(f"\n▸ Persisting to DB...")
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA busy_timeout = 60000")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA cache_size = -32000")

conn.execute("""
    CREATE TABLE IF NOT EXISTS email_evidence (
        email_id INTEGER PRIMARY KEY,
        sender TEXT,
        recipient TEXT,
        date_sent TEXT,
        subject TEXT,
        body_text TEXT,
        body_length INTEGER,
        lane TEXT,
        has_attachment INTEGER DEFAULT 0,
        attachment_names TEXT,
        source_file TEXT DEFAULT 'Starred.mbox',
        extracted_at TEXT
    )
""")

now = datetime.now().isoformat()
rows = [(r['email_id'], r['sender'], r['recipient'], r['date_sent'],
         r['subject'], r['body_text'], r['body_length'], r['lane'],
         r['has_attachment'], r['attachment_names'], 'Starred.mbox', now)
        for r in records]

conn.executemany("""
    INSERT OR REPLACE INTO email_evidence
    (email_id, sender, recipient, date_sent, subject, body_text, body_length,
     lane, has_attachment, attachment_names, source_file, extracted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", rows)
conn.commit()

# FTS5 index
try:
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS email_evidence_fts USING fts5(
            subject, body_text, sender, recipient,
            content=email_evidence, content_rowid=email_id,
            tokenize='porter unicode61'
        )
    """)
    conn.execute("INSERT INTO email_evidence_fts(email_evidence_fts) VALUES('rebuild')")
    conn.commit()
    print("  FTS5 index built ✓")
except Exception as e:
    print(f"  FTS5 warning: {e}")

# Verify
db_count = conn.execute("SELECT COUNT(*) FROM email_evidence").fetchone()[0]
print(f"  DB verified: {db_count} rows in email_evidence")

conn.close()

# ══════════════════════════════════════════════════════════════
# ANALYSIS & REPORT
# ══════════════════════════════════════════════════════════════
elapsed = time.time() - t0

print(f"\n{'=' * 70}")
print(f"EXTRACTION COMPLETE — {elapsed:.1f}s total")
print(f"{'=' * 70}")

print(f"\n▸ Lane Distribution:")
for lane, ct in sorted(lanes.items(), key=lambda x: -x[1]):
    pct = ct * 100 / total if total else 0
    bar = '█' * int(pct / 2)
    print(f"  {lane:8s} {ct:5d} ({pct:5.1f}%) {bar}")

print(f"\n▸ Top 20 Senders:")
for sender, ct in senders.most_common(20):
    print(f"  {ct:4d}  {sender}")

print(f"\n▸ Top 20 Recipients:")
for recip, ct in recipients_ctr.most_common(20):
    print(f"  {ct:4d}  {recip}")

print(f"\n▸ Sample Subjects (first 30):")
for s in subjects_list[:30]:
    print(f"  - {s}")

# Attachment analysis
attach_ct = sum(1 for r in records if r['has_attachment'])
all_attachments = []
for r in records:
    if r['attachment_names']:
        all_attachments.extend(r['attachment_names'].split('|'))
attach_ext = Counter(os.path.splitext(a)[1].lower() for a in all_attachments if a)

print(f"\n▸ Attachments: {attach_ct} emails with attachments, {len(all_attachments)} total files")
if attach_ext:
    print("  By type:")
    for ext, ct in attach_ext.most_common(15):
        print(f"    {ext or '(none)'}: {ct}")

# Evidence highlights
print(f"\n▸ Potential Evidence Emails:")
evidence_keywords = re.compile(r'custody|PPO|court|order|hearing|judge|McNeill|Watson|police|NSPD|abuse|threat|assault|protection|contempt', re.I)
evidence_hits = []
for r in records:
    text = f"{r['subject']} {r['body_text'][:2000]}"
    if evidence_keywords.search(text):
        evidence_hits.append(r)

print(f"  {len(evidence_hits)} emails match evidence keywords out of {total}")
for r in evidence_hits[:15]:
    print(f"  [{r['lane']}] {r['date_sent'][:25]:25s} | {r['subject'][:70]}")

# Write comprehensive report
report_path = os.path.join(OUTPUT_DIR, 'MBOX_EXTRACTION_REPORT.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(f"# MBOX Extraction Report\n")
    f.write(f"> Extracted: {datetime.now():%Y-%m-%d %H:%M}\n")
    f.write(f"> Source: {MBOX_PATH} ({file_mb:.0f} MB)\n")
    f.write(f"> Emails: {total} | Errors: {err_ct}\n\n")

    f.write(f"## Output\n")
    f.write(f"- JSONL: `{JSONL_PATH}` ({jsonl_mb:.1f} MB)\n")
    f.write(f"- DB: `email_evidence` ({db_count} rows) + FTS5 index\n\n")

    f.write(f"## Lane Distribution\n")
    f.write(f"| Lane | Count | % |\n|------|-------|---|\n")
    for lane, ct in sorted(lanes.items(), key=lambda x: -x[1]):
        f.write(f"| {lane} | {ct} | {ct*100/total:.1f}% |\n")

    f.write(f"\n## Top Senders\n")
    for sender, ct in senders.most_common(30):
        f.write(f"- **{ct}**: {sender}\n")

    f.write(f"\n## Evidence Emails ({len(evidence_hits)} matches)\n")
    for r in evidence_hits[:50]:
        f.write(f"- [{r['lane']}] {r['date_sent'][:25]} — {r['subject'][:80]}\n")

    f.write(f"\n## Attachments ({len(all_attachments)} files in {attach_ct} emails)\n")
    for ext, ct in attach_ext.most_common(20):
        f.write(f"- {ext or '(none)'}: {ct}\n")

print(f"\nReport: {report_path}")

# Copy report into LitigationOS
report_copy = r'C:\Users\andre\LitigationOS\04_ANALYSIS\MBOX_EXTRACTION_REPORT.md'
with open(report_copy, 'w', encoding='utf-8') as f2:
    with open(report_path, 'r', encoding='utf-8') as f1:
        f2.write(f1.read())
print(f"Report copy: {report_copy}")
