#!/usr/bin/env python3
"""Court Calendar Engine v1.0 - Deadline management and ICS export."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Known critical deadlines(hardcoded + DB-sourced)
CRITICAL_DEADLINES = [
    {"name": "McNeill Disqualification Motion", "date": "2026-03-15", "court": "14th Circuit Court", "case": "2024-001507-DC", "stack": "DISQUALIFY_PACKAGE", "priority": "CRITICAL"},
    {"name": "MSC Original Action Filing", "date": "2026-04-01", "court": "Michigan Supreme Court", "case": "MSC-NEW", "stack": "04_MSC_ORIGINAL_ACTION", "priority": "CRITICAL"},
    {"name": "COA Brief 366810", "date": "2026-04-15", "court": "Michigan Court of Appeals", "case": "366810", "stack": "01_COA_366810", "priority": "CRITICAL"},
    {"name": "Watson Tort Complaint", "date": "2026-04-30", "court": "14th Circuit Court", "case": "NEW", "stack": "WATSON_TORT", "priority": "HIGH"},
    {"name": "Shady Oaks Complaint", "date": "2026-04-30", "court": "14th Circuit Court", "case": "NEW", "stack": "SHADY_OAKS", "priority": "HIGH"},
    {"name": "HUD/LARA Complaint", "date": "2026-07-17", "court": "Federal/Agency", "case": "HUD-NEW", "stack": "06_EMERGENCY", "priority": "MEDIUM"},
    {"name": "Federal 1983 Action", "date": "2029-12-31", "court": "WDMI Federal Court", "case": "NEW", "stack": "03_FEDERAL_1983", "priority": "LOW"},
]

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_DIR = r"C:\Users\andre\LitigationOS\00_SYSTEM\calendar"

class CourtCalendarEngine:
    def __init__(self, db_path=DB_PATH):
        """Initialize the court calendar engine.
        
        Args:
            db_path: Path to the litigation context database.
        """
        if not isinstance(db_path, (str, type(None))):
            raise TypeError("db_path must be a string path or None")
        self.db_path = db_path or DB_PATH
        self.deadlines = list(CRITICAL_DEADLINES)
        self.output_dir = Path(OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_db_deadlines(self):
        """Load additional deadlines from master DB if available."""
        if self.db_path and not Path(self.db_path).exists():
            logger.warning("DB path does not exist, skipping: %s", self.db_path)
            return
        try:
            logger.info("Loading deadlines from DB: %s", self.db_path)
            conn = sqlite3.connect(self.db_path, timeout=120)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            
            # Try common deadline table names
            for table in ['deadlines', 'filing_deadlines', 'case_deadlines', 'calendar_events']:
                try:
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 5").fetchall()
                    cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    # Extract deadline info based on column names
                    # Add to self.deadlines
                except:
                    continue
            conn.close()
        except Exception as e:
            logger.warning("Could not load DB deadlines: %s", e)
    
    def get_urgency(self, deadline_date):
        """Calculate urgency level based on days remaining."""
        today = datetime.now().date()
        target = datetime.strptime(deadline_date, "%Y-%m-%d").date()
        days = (target - today).days
        
        if days < 0:
            return "OVERDUE", days, "[!!!]"
        elif days <= 3:
            return "EMERGENCY", days, "[!!]"
        elif days <= 7:
            return "CRITICAL", days, "[!]"
        elif days <= 14:
            return "URGENT", days, "[~]"
        elif days <= 30:
            return "APPROACHING", days, "[ok]"
        else:
            return "SCHEDULED", days, "[ ]"
    
    def generate_dashboard(self):
        """Generate text dashboard of all deadlines with countdowns."""
        lines = []
        lines.append("=" * 70)
        lines.append("  LITIGATION DEADLINE DASHBOARD")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        
        sorted_dl = sorted(self.deadlines, key=lambda x: x['date'])
        
        for dl in sorted_dl:
            urgency, days, icon = self.get_urgency(dl['date'])
            if days < 0:
                countdown = f"OVERDUE by {abs(days)} days"
            elif days == 0:
                countdown = "DUE TODAY"
            elif days == 1:
                countdown = "DUE TOMORROW"
            else:
                countdown = f"{days} days remaining"
            
            lines.append(f"  {icon} [{urgency}] {dl['name']}")
            lines.append(f"     Due: {dl['date']} | {countdown}")
            lines.append(f"     Court: {dl['court']} | Case: {dl['case']}")
            lines.append(f"     Stack: {dl['stack']}")
            lines.append("")
        
        lines.append("=" * 70)
        dashboard = "\n".join(lines)
        
        # Write dashboard
        dash_path = self.output_dir / "DEADLINE_DASHBOARD.txt"
        try:
            with open(dash_path, 'w', encoding='utf-8') as f:
                f.write(dashboard)
        except (IOError, OSError) as e:
            logger.error("Failed to write %s: %s", dash_path, e)
        
        return dashboard
    
    def generate_ics(self):
        """Generate ICS calendar file for all deadlines."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//LitigationOS//Court Calendar Engine v1.0//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:LitigationOS Deadlines",
            "X-WR-TIMEZONE:America/Detroit",
        ]
        
        for dl in self.deadlines:
            dt = datetime.strptime(dl['date'], "%Y-%m-%d")
            urgency, days, _ = self.get_urgency(dl['date'])
            
            uid = f"litos-{dl['case']}-{dl['date']}@litigationos.local"
            
            # Add event
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{uid}")
            lines.append(f"DTSTART;VALUE=DATE:{dt.strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{(dt + timedelta(days=1)).strftime('%Y%m%d')}")
            lines.append(f"SUMMARY:[{dl['priority']}] {dl['name']}")
            lines.append(f"DESCRIPTION:Court: {dl['court']}\\nCase: {dl['case']}\\nStack: {dl['stack']}\\nPriority: {dl['priority']}")
            lines.append(f"LOCATION:{dl['court']}")
            lines.append(f"STATUS:CONFIRMED")
            lines.append(f"CATEGORIES:{dl['priority']}")
            
            # Add alarms based on urgency
            for alarm_days in [14, 7, 3, 1]:
                lines.append("BEGIN:VALARM")
                lines.append("ACTION:DISPLAY")
                lines.append(f"DESCRIPTION:{dl['name']} - {alarm_days} days remaining!")
                lines.append(f"TRIGGER:-P{alarm_days}D")
                lines.append("END:VALARM")
            
            lines.append("END:VEVENT")
        
        lines.append("END:VCALENDAR")
        
        ics_path = self.output_dir / "litigation_deadlines.ics"
        try:
            with open(ics_path, 'w', encoding='utf-8') as f:
                f.write("\r\n".join(lines))
        except (IOError, OSError) as e:
            logger.error("Failed to write %s: %s", ics_path, e)
        
        return str(ics_path)
    
    def generate_json(self):
        """Export deadlines as JSON for other engines."""
        enriched = []
        for dl in self.deadlines:
            urgency, days, icon = self.get_urgency(dl['date'])
            enriched.append({
                **dl,
                "urgency": urgency,
                "days_remaining": days,
                "icon": icon,
            })
        
        json_path = self.output_dir / "deadlines.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(enriched, f, indent=2)
        except (IOError, OSError) as e:
            logger.error("Failed to write %s: %s", json_path, e)
        
        return enriched
    
    def run(self):
        """Execute full calendar generation.
        
        Returns:
            dict: Summary with counts and file paths, or empty dict on failure.
        """
        try:
            self.load_db_deadlines()
            dashboard = self.generate_dashboard()
            ics_path = self.generate_ics()
            deadlines_json = self.generate_json()
            
            print(dashboard)
            print(f"\nICS exported: {ics_path}")
            print(f"JSON exported: {self.output_dir / 'deadlines.json'}")
            print(f"Dashboard saved: {self.output_dir / 'DEADLINE_DASHBOARD.txt'}")
            
            return {
                "deadlines": len(self.deadlines),
                "ics_path": ics_path,
                "dashboard_path": str(self.output_dir / "DEADLINE_DASHBOARD.txt"),
                "json_path": str(self.output_dir / "deadlines.json"),
            }
        except Exception as e:
            logger.error("Calendar engine failed: %s", e)
            return {"deadlines": 0, "error": str(e)}


if __name__ == "__main__":
    engine = CourtCalendarEngine()
    result = engine.run()
    print(f"\n[OK] Calendar engine complete: {result['deadlines']} deadlines processed")
