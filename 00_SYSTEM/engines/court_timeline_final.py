#!/usr/bin/env python3
"""
COURT-GRADE TIMELINE — Final pass.
Takes condensed_timeline → produces tight ~300-500 event timeline
suitable for appendix to COA brief or standalone exhibit.
"""
import sqlite3, os
from datetime import datetime

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  COURT-GRADE TIMELINE — Final Condensation")
print("=" * 70)

# Only keep legally significant categories
KEEP_CATEGORIES = {
    'CONSTITUTIONAL', 'JUDICIAL_VIOLATION', 'COURT_ORDER', 'COURT_FILING',
    'MOTION', 'POLICE_REPORT', 'AFFIDAVIT', 'DAMAGES', 'COMMUNICATION',
    'CO_PARENT_COMMUNICATION', 'PSYCH', 'CONTRAST', 'PT_SUSPENSION',
    'CASE_FILED', 'LAST_PARENTING_TIME', 'PREMEDITATION', 'MAJOR_HEARING',
    'COURT_HEARING', 'manipulation_pattern', 'general_court_doc', 'discovery',
}

# Pull condensed + filter
c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, raw_event_count
    FROM condensed_timeline 
    WHERE severity >= 5 OR category IN ('CONSTITUTIONAL','JUDICIAL_VIOLATION','COURT_ORDER','COURT_FILING',
        'MOTION','POLICE_REPORT','AFFIDAVIT','COMMUNICATION','CO_PARENT_COMMUNICATION','PSYCH',
        'CASE_FILED','PT_SUSPENSION','LAST_PARENTING_TIME','PREMEDITATION','MAJOR_HEARING','COURT_HEARING',
        'DAMAGES','CONTRAST','manipulation_pattern','general_court_doc','discovery')
    ORDER BY event_date, severity DESC""")
rows = c.fetchall()
print(f"[1] Pulled {len(rows)} events (sev>=5 or key categories)")

# Group by date, take top 3 per day
from collections import defaultdict
by_date = defaultdict(list)
for row in rows:
    by_date[row[0]].append(row)

final = []
for date in sorted(by_date.keys()):
    events = by_date[date]
    # Skip pure FILE_EVENT / EVIDENCE only days
    significant = [e for e in events if e[1] not in ('FILE_EVENT', 'EVIDENCE', 'ANALYSIS', 'DB_RECORD')]
    if not significant:
        # Keep if high severity even if FILE_EVENT
        significant = [e for e in events if (e[6] or 0) >= 7]
    
    for evt in significant[:3]:
        final.append(evt)

print(f"[2] Court-grade events: {len(final)}")

# Store
c.execute('''CREATE TABLE IF NOT EXISTS court_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT, category TEXT, title TEXT, description TEXT,
    actors TEXT, evidence_ref TEXT, severity INTEGER, raw_event_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')
c.execute("DELETE FROM court_timeline")
for evt in final:
    c.execute("INSERT INTO court_timeline (event_date, category, title, description, actors, evidence_ref, severity, raw_event_count) VALUES (?,?,?,?,?,?,?,?)", evt)
conn.commit()

# Generate report
output = r'C:\Users\andre\LitigationOS\05_ANALYSIS\COURT_GRADE_TIMELINE.md'
c.execute("SELECT MIN(event_date), MAX(event_date) FROM court_timeline")
dmin, dmax = c.fetchone()
c.execute("SELECT category, COUNT(*) FROM court_timeline GROUP BY category ORDER BY COUNT(*) DESC")
cats = c.fetchall()

with open(output, 'w', encoding='utf-8') as f:
    f.write("# PROSECUTION TIMELINE\n")
    f.write("## *Exhibit ___*\n\n")
    f.write("**Andrew J. Pigors v. Tiffany Emily Watson (fka Pigors)**\n")
    f.write("**Case No. 2024-001507-DC** | **COA Case No. 366810**\n")
    f.write("**14th Judicial Circuit Court, Muskegon County, Michigan**\n\n")
    f.write(f"*This timeline contains {len(final)} documented events spanning {dmin} to {dmax},*\n")
    f.write(f"*condensed from 43,560 source records across court filings, communications,*\n")
    f.write(f"*police reports, evidence documents, and database analysis.*\n\n")
    f.write("---\n\n")
    
    # Summary stats
    f.write("## Event Summary\n\n")
    f.write("| Category | Count |\n|----------|-------|\n")
    for cat, cnt in cats:
        f.write(f"| {cat} | {cnt} |\n")
    f.write("\n---\n\n")
    
    # Key milestones callout
    f.write("## ⚡ KEY MILESTONES\n\n")
    c.execute("SELECT event_date, title, actors FROM court_timeline WHERE severity >= 9 ORDER BY event_date")
    for d, t, a in c.fetchall():
        f.write(f"- **{d}** — {t}\n")
    f.write("\n---\n\n")
    
    # Full timeline
    f.write("## CHRONOLOGICAL RECORD\n\n")
    c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, raw_event_count
        FROM court_timeline ORDER BY event_date, severity DESC""")
    
    current_month = None
    current_date = None
    entry_num = 0
    
    for date, cat, title, desc, actors, evidence, sev, raw_cnt in c.fetchall():
        month = date[:7]
        if month != current_month:
            current_month = month
            # Month header
            try:
                dt = datetime.strptime(month + '-01', '%Y-%m-%d')
                month_name = dt.strftime('%B %Y')
            except:
                month_name = month
            f.write(f"\n### {month_name}\n\n")
        
        if date != current_date:
            current_date = date
        
        entry_num += 1
        sev = sev or 5
        
        # Clean title
        title_clean = title.replace('\n', ' ').strip()
        if len(title_clean) > 200:
            title_clean = title_clean[:200] + "..."
        
        # Format entry
        f.write(f"**{entry_num}. [{date}]** ")
        if sev >= 9:
            f.write("🔴 ")
        elif sev >= 7:
            f.write("🟡 ")
        f.write(f"**{cat}** — {title_clean}")
        if actors and len(actors) > 2:
            f.write(f" *(Actors: {actors[:80]})*")
        f.write("\n")
        
        if desc and desc != title and len(desc.strip()) > 20:
            d = desc[:250].replace('\n', ' ').strip()
            if d != title_clean:
                f.write(f"   > {d}\n")
        
        if evidence and len(evidence.strip()) > 5:
            f.write(f"   > 📎 {evidence[:120]}\n")
        
        f.write("\n")
    
    f.write(f"\n---\n*Timeline entries: {entry_num} | Source records: 43,560 | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

fsize = os.path.getsize(output)

# Stats
c.execute("SELECT substr(event_date,1,7), COUNT(*) FROM court_timeline GROUP BY substr(event_date,1,7) ORDER BY substr(event_date,1,7)")
months = c.fetchall()

print(f"\n{'='*70}")
print(f"  COURT-GRADE TIMELINE COMPLETE")
print(f"  43,560 raw → 4,286 condensed → {len(final)} court-grade")
print(f"  Report: {fsize/1024:.0f}KB → {output}")
print(f"{'='*70}")
print(f"\nMonthly distribution:")
for ym, cnt in months:
    bar = '█' * min(cnt, 40)
    print(f"  {ym}: {cnt:3} {bar}")
print(f"\nCategories:")
for cat, cnt in cats[:10]:
    print(f"  {cat}: {cnt}")

conn.close()
