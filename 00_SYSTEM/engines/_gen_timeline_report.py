#!/usr/bin/env python3
"""Generate report from master_timeline already in DB."""
import sqlite3, os
from datetime import datetime
from pathlib import Path

db_path = str(Path(__file__).resolve().parents[2] / "litigation_context.db")
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
c = conn.cursor()
LOS_ROOT = str(Path(__file__).resolve().parents[2])

output_path = os.path.join(LOS_ROOT, '05_ANALYSIS', 'MASTER_CHRONOLOGICAL_TIMELINE.md')

c.execute("SELECT COUNT(*) FROM master_timeline")
total = c.fetchone()[0]
c.execute("SELECT MIN(event_date), MAX(event_date) FROM master_timeline")
date_min, date_max = c.fetchone()
c.execute("SELECT category, COUNT(*) FROM master_timeline GROUP BY category ORDER BY COUNT(*) DESC")
cat_stats = c.fetchall()
c.execute("SELECT source, COUNT(*) FROM master_timeline GROUP BY source ORDER BY COUNT(*) DESC LIMIT 20")
source_stats = c.fetchall()
c.execute("SELECT event_date, COUNT(*) FROM master_timeline GROUP BY event_date ORDER BY COUNT(*) DESC LIMIT 10")
hottest_days = c.fetchall()
c.execute("SELECT substr(event_date,1,7) as ym, COUNT(*) FROM master_timeline GROUP BY ym ORDER BY ym")
monthly = c.fetchall()

print(f"Generating report for {total:,} events...")

with open(output_path, 'w', encoding='utf-8') as f:
    f.write("# MASTER CHRONOLOGICAL TIMELINE\n")
    f.write(f"## Andrew J. Pigors v. Tiffany Emily Watson\n")
    f.write(f"## Case No. 2024-001507-DC | COA 366810\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**Total Events:** {total:,}\n")
    f.write(f"**Date Range:** {date_min} to {date_max}\n\n")
    f.write("---\n\n")
    
    f.write("## EVENT STATISTICS\n\n")
    f.write("### By Category\n\n| Category | Count |\n|----------|-------|\n")
    for cat, cnt in cat_stats:
        f.write(f"| {cat} | {cnt:,} |\n")
    
    f.write("\n### By Month\n\n| Month | Events |\n|-------|--------|\n")
    for ym, cnt in monthly:
        f.write(f"| {ym} | {cnt:,} |\n")
    
    f.write("\n### Hottest Days\n\n| Date | Events |\n|------|--------|\n")
    for d, cnt in hottest_days:
        f.write(f"| {d} | {cnt:,} |\n")
    
    f.write("\n### Top Sources\n\n| Source | Events |\n|--------|--------|\n")
    for src, cnt in source_stats:
        f.write(f"| {src[:60]} | {cnt:,} |\n")
    
    f.write("\n---\n\n## FULL CHRONOLOGICAL TIMELINE\n\n")
    
    # Write HIGH severity events first as executive summary
    f.write("### 🔴 CRITICAL EVENTS (Severity 8+)\n\n")
    c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, source
        FROM master_timeline WHERE CAST(severity AS INTEGER) >= 8
        ORDER BY event_date, CAST(severity AS INTEGER) DESC""")
    for date, cat, title, desc, actors, evidence, severity, source in c.fetchall():
        f.write(f"**{date}** | **[{cat}]** {title}")
        if actors:
            f.write(f" *(Actors: {actors[:80]})*")
        f.write("\n")
        if desc and desc != title:
            f.write(f"> {desc[:400]}\n")
        f.write("\n")
    
    f.write("\n---\n\n### COMPLETE TIMELINE (All Events)\n\n")
    
    c.execute("""SELECT event_date, category, title, description, actors, evidence_ref, severity, source
        FROM master_timeline ORDER BY event_date, CAST(severity AS INTEGER) DESC""")
    
    current_month = None
    current_date = None
    
    for date, cat, title, desc, actors, evidence, severity, source in c.fetchall():
        month = date[:7] if date else 'Unknown'
        
        if month != current_month:
            current_month = month
            f.write(f"\n---\n## {month}\n\n")
        
        if date != current_date:
            current_date = date
            f.write(f"\n### {date}\n\n")
        
        sev = int(severity) if str(severity).isdigit() else 5
        if sev >= 9:
            icon = "🔴"
        elif sev >= 7:
            icon = "🟡"
        elif sev >= 5:
            icon = "🔵"
        else:
            icon = "⚪"
        
        f.write(f"{icon} **[{cat}]** {title}\n")
        if desc and desc != title and len(desc) > 10:
            f.write(f"> {desc[:300]}\n")
        f.write("\n")

file_size = os.path.getsize(output_path)
print(f"DONE: {file_size/1024:.0f}KB → {output_path}")
print(f"Events: {total:,} | Range: {date_min} → {date_max}")
print(f"Categories: {len(cat_stats)} | Sources: {len(source_stats)}+")

conn.close()
