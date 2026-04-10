"""Extract full text of critical emails from email_evidence table."""
import sqlite3, json, os

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT = r"J:\LitigationOS_CENTRAL\MBOX_EXTRACTED\CRITICAL_EMAILS.md"

# Critical email IDs identified from analysis
CRITICAL_IDS = [
    832,   # Martini forwarding Rusco's email about Andrew (CONDUIT EVIDENCE)
    1338,  # Rusco re: HealthWest exam — McNeill's order
    1400,  # Barnes threatening re: Joint Legal Custody
    1396,  # Barnes filing brief timing
    1394,  # Barnes cease and desist
    1145,  # Martini sympathizing re custody
    1148,  # Martini re: First Reply to submissions
    240,   # Martini warning about alleging bias
    237,   # Martini "I have issues with combined motion"
    235,   # Martini "I do not recall you being..."
]

# Also get ALL Rusco and gov emails
QUERIES = [
    ("RUSCO EMAILS (FOC)", "SELECT email_id, date_sent, sender, recipient, subject, body_text, has_attachment, attachment_names FROM email_evidence WHERE sender LIKE '%rusco%' ORDER BY date_sent"),
    ("MARTINI EMAILS (Public Defender)", "SELECT email_id, date_sent, sender, recipient, subject, body_text, has_attachment, attachment_names FROM email_evidence WHERE sender LIKE '%martini%' ORDER BY date_sent"),
    ("BARNES EMAILS (Former Attorney)", "SELECT email_id, date_sent, sender, recipient, subject, body_text, has_attachment, attachment_names FROM email_evidence WHERE sender LIKE '%barnes%' ORDER BY date_sent"),
    ("MDHHS / GOV EMAILS", "SELECT email_id, date_sent, sender, recipient, subject, body_text, has_attachment, attachment_names FROM email_evidence WHERE (sender LIKE '%michigan.gov%' OR sender LIKE '%mdhhs%' OR sender LIKE '%state.mi%') ORDER BY date_sent"),
    ("SAFEGUARD/HOUSING EMAILS", "SELECT email_id, date_sent, sender, recipient, subject, body_text, has_attachment, attachment_names FROM email_evidence WHERE (sender LIKE '%safeguard%' OR sender LIKE '%perham%' OR subject LIKE '%Shady%' OR subject LIKE '%evict%') ORDER BY date_sent"),
]

conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")

lines = ["# CRITICAL EMAIL EVIDENCE — Pigors v. Watson\n"]
lines.append(f"**Extracted from email_evidence table ({conn.execute('SELECT COUNT(*) FROM email_evidence').fetchone()[0]} total emails)**\n")
lines.append("**Generated for litigation use — MCR 8.119(H) compliant**\n\n---\n")

for section_title, query in QUERIES:
    lines.append(f"\n## {section_title}\n")
    rows = conn.execute(query).fetchall()
    lines.append(f"**{len(rows)} emails found**\n")
    
    for row in rows:
        eid, date_sent, sender, recipient, subject, body, has_att, att_names = row
        lines.append(f"\n### Email #{eid} — {date_sent or 'NO DATE'}")
        lines.append(f"- **From:** {sender}")
        lines.append(f"- **To:** {recipient or 'N/A'}")
        lines.append(f"- **Subject:** {subject or 'NO SUBJECT'}")
        if has_att:
            lines.append(f"- **Attachments:** {att_names or 'YES (names not captured)'}")
        lines.append(f"\n**Body:**\n```\n{body or '[EMPTY]'}\n```\n")

# Also extract highest-value keywords across ALL emails
lines.append("\n---\n## KEYWORD INTELLIGENCE\n")
keyword_queries = [
    ("ex parte", "body_text LIKE '%ex parte%'"),
    ("contempt", "body_text LIKE '%contempt%'"),
    ("custody", "body_text LIKE '%custody%'"),
    ("PPO", "body_text LIKE '%PPO%' OR body_text LIKE '%protection order%'"),
    ("HealthWest", "body_text LIKE '%HealthWest%' OR body_text LIKE '%health west%'"),
    ("parenting time", "body_text LIKE '%parenting time%'"),
    ("McNeill", "body_text LIKE '%McNeill%'"),
    ("jail", "body_text LIKE '%jail%' OR body_text LIKE '%incarcerat%'"),
    ("alienation", "body_text LIKE '%alienat%'"),
    ("eviction", "body_text LIKE '%evict%'"),
    ("meth", "body_text LIKE '%meth%'"),
]

for kw, where in keyword_queries:
    count = conn.execute(f"SELECT COUNT(*) FROM email_evidence WHERE {where}").fetchone()[0]
    if count > 0:
        lines.append(f"- **'{kw}'**: {count} emails")

conn.close()

output = "\n".join(lines)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(output)

# Also save to repo
repo_out = r"C:\Users\andre\LitigationOS\04_ANALYSIS\CRITICAL_EMAIL_EVIDENCE.md"
with open(repo_out, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Written {len(output):,} chars to {OUT}")
print(f"Written {len(output):,} chars to {repo_out}")
print(f"Total sections: {len(QUERIES)}")
