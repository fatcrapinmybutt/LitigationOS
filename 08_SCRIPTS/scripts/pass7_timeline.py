"""PASS 7: Master Case Timeline from DB + filings."""
import sqlite3, json, re, os
from datetime import datetime

MAIN_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
DELTA99 = r"I:\LitigationOS_Delta99"
LOG = r"I:\DRIVE_ORG\operations.log"
TIMELINE_OUT = os.path.join(DELTA99, "MASTER_TIMELINE.json")
TIMELINE_MD = os.path.join(DELTA99, "MASTER_TIMELINE.md")

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run():
    log("=" * 60)
    log("PASS 7: MASTER CASE TIMELINE")
    log("=" * 60)
    
    events = []
    
    # Known critical events
    known = [
        ("2022-11-09", "Lincoln Watson born", "BIRTH", "Critical"),
        ("2024-01-01", "Case 2024-001507-DC filed, 14th Circuit Muskegon County", "FILING", "Critical"),
        ("2024-07-29", "Last contact between father and son (571+ days separation begins)", "SEPARATION", "Critical"),
        ("2025-08-08", "Ex parte orders entered based on unsworn motion with inadmissible hearsay", "ORDER", "Critical"),
        ("2025-08-08", "Drug screen ordered (result: NEGATIVE)", "EVIDENCE", "High"),
        ("2026-04-15", "COA Case 366810 deadline", "DEADLINE", "Critical"),
    ]
    
    for date, desc, cat, sig in known:
        events.append({"date": date, "event": desc, "category": cat, "significance": sig, "source": "case_records"})
    
    # Pull from DB
    try:
        uri = f"file:{MAIN_DB}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        
        # Get deadlines
        try:
            deadlines = conn.execute("SELECT deadline_date, description, priority FROM deadlines WHERE deadline_date IS NOT NULL ORDER BY deadline_date").fetchall()
            for d, desc, pri in deadlines:
                if d and len(d) >= 8:
                    events.append({"date": d[:10], "event": desc or "Deadline", "category": "DEADLINE", "significance": pri or "Medium", "source": "deadlines_table"})
            log(f"  Deadlines: {len(deadlines)}")
        except:
            log("  No deadlines table")
        
        # Get filing events
        try:
            filings = conn.execute("SELECT filing_date, filing_type, court FROM filing_packages WHERE filing_date IS NOT NULL ORDER BY filing_date").fetchall()
            for d, ftype, court in filings:
                if d and len(d) >= 8:
                    events.append({"date": d[:10], "event": f"{ftype} filed in {court}", "category": "FILING", "significance": "Medium", "source": "filing_packages"})
            log(f"  Filing events: {len(filings)}")
        except:
            log("  No filing_packages table")
        
        # Get judicial violations with dates
        try:
            violations = conn.execute("""
                SELECT date, violation_type, description 
                FROM judicial_violations 
                WHERE date IS NOT NULL 
                ORDER BY date LIMIT 50
            """).fetchall()
            for d, vtype, desc in violations:
                if d and len(d) >= 8:
                    events.append({"date": d[:10], "event": f"Violation: {vtype} - {(desc or '')[:80]}", "category": "VIOLATION", "significance": "High", "source": "judicial_violations"})
            log(f"  Violations with dates: {len(violations)}")
        except:
            log("  No judicial_violations with dates")
        
        conn.close()
    except Exception as e:
        log(f"  DB error: {e}")
    
    # Deduplicate and sort
    seen = set()
    unique_events = []
    for e in events:
        key = (e["date"], e["event"][:50])
        if key not in seen:
            seen.add(key)
            unique_events.append(e)
    
    unique_events.sort(key=lambda x: x["date"])
    
    # Write JSON
    with open(TIMELINE_OUT, "w") as f:
        json.dump({"generated": datetime.now().isoformat(), "event_count": len(unique_events), "events": unique_events}, f, indent=2)
    
    # Write markdown
    with open(TIMELINE_MD, "w", encoding="utf-8") as f:
        f.write("# MASTER CASE TIMELINE\n")
        f.write(f"**Pigors v. Watson, Case 2024-001507-DC**\n")
        f.write(f"**14th Judicial Circuit, Muskegon County**\n")
        f.write(f"**Generated: {datetime.now().strftime('%B %d, %Y')}**\n\n")
        f.write(f"Total events: {len(unique_events)}\n\n---\n\n")
        
        current_year = ""
        for e in unique_events:
            year = e["date"][:4]
            if year != current_year:
                f.write(f"\n## {year}\n\n")
                current_year = year
            
            sig_icon = "🔴" if e["significance"] == "Critical" else "🟡" if e["significance"] == "High" else "⚪"
            f.write(f"**{e['date']}** {sig_icon} [{e['category']}] {e['event']}\n\n")
    
    log(f"\n  Timeline: {len(unique_events)} events")
    log(f"  Output: {TIMELINE_MD}")
    log(f"PASS 7 COMPLETE")

if __name__ == "__main__":
    run()
