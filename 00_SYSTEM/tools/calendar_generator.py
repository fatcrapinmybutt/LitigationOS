#!/usr/bin/env python3
"""
Tool #85 — Court Calendar & Deadline ICS Generator
======================================================
Generates ICS (iCalendar) files for ALL litigation deadlines
that Andrew can import into Google Calendar, Outlook, or iPhone.

Each deadline becomes a calendar event with:
- Date/time
- Filing name
- Court
- Reminder (1 day + 1 week before)
- Description with action items
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta
from hashlib import md5

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

# Key deadlines (placeholders — Andrew must confirm actual dates)
DEADLINES = [
    {
        'summary': 'F1 Emergency Parenting Time — FILE',
        'description': 'File emergency motion for parenting time restoration (MCR 2.119). Court: 14th Circuit. Case: 2024-001507-DC. Priority: CRITICAL.',
        'location': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
        'category': 'FILING',
        'priority': 'CRITICAL',
        'days_from_now': 3,
    },
    {
        'summary': 'F3 Judicial Disqualification — FILE',
        'description': 'File MCR 2.003 motion to disqualify Judge McNeill. Must be filed BEFORE any other hearing. Case: 2024-001507-DC.',
        'location': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
        'category': 'FILING',
        'priority': 'CRITICAL',
        'days_from_now': 3,
    },
    {
        'summary': 'Register for MiFILE',
        'description': 'Register at mifile.courts.michigan.gov/register. Required for electronic filing in 14th Circuit. FREE.',
        'location': 'Online: mifile.courts.michigan.gov',
        'category': 'TASK',
        'priority': 'HIGH',
        'days_from_now': 1,
    },
    {
        'summary': 'Register for PACER / CM-ECF',
        'description': 'Register at pacer.uscourts.gov. Required for federal §1983 filing (F4). $0.10/page for access.',
        'location': 'Online: pacer.uscourts.gov',
        'category': 'TASK',
        'priority': 'HIGH',
        'days_from_now': 2,
    },
    {
        'summary': 'Review & Sign ALL Affidavits',
        'description': 'Review and sign all 10 affidavits. MUST be notarized (MCL 600.2922). Do NOT sign until you read every word. Sworn under penalty of perjury.',
        'location': 'Notary Public',
        'category': 'TASK',
        'priority': 'CRITICAL',
        'days_from_now': 2,
    },
    {
        'summary': 'F6 JTC Complaint — MAIL',
        'description': 'Mail JTC complaint re: Judge McNeill. Address: 3034 W Grand Blvd Ste 8-450, Detroit MI 48202. FREE to file.',
        'location': 'Post Office',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 5,
    },
    {
        'summary': 'F10 AGC Grievance — MAIL',
        'description': 'Mail AGC grievance re: Jennifer Barnes P55406. Address: 535 Griswold St Ste 1700, Detroit MI 48226. FREE to file.',
        'location': 'Post Office',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 5,
    },
    {
        'summary': 'F2 Fraud on Court — FILE',
        'description': 'File MCR 2.612(C) motion to set aside void orders. Court: 14th Circuit. Case: 2024-001507-DC.',
        'location': '14th Circuit Court',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 7,
    },
    {
        'summary': 'F7 Custody Modification — FILE',
        'description': 'File motion to modify custody/parenting time. MCL 722.27(1)(c). Court: 14th Circuit.',
        'location': '14th Circuit Court',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 8,
    },
    {
        'summary': 'F4 Federal §1983 Complaint — FILE',
        'description': 'File 42 USC §1983 complaint in federal court. USDC Western District MI. Include IFP application (AO 240).',
        'location': 'USDC WDMI, 399 Federal Building, 110 Michigan St NW, Grand Rapids MI 49503',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 14,
    },
    {
        'summary': 'F5 MSC Superintending Control — FILE',
        'description': 'File complaint for superintending control in MSC. Const 1963 Art 6 §4.',
        'location': 'Michigan Supreme Court, 925 W Ottawa St, Lansing MI 48915',
        'category': 'FILING',
        'priority': 'MEDIUM',
        'days_from_now': 21,
    },
    {
        'summary': 'Call COA Clerk — Confirm Brief Deadline',
        'description': 'Call (517) 373-0786 to confirm COA 366810 brief deadline and scheduling order.',
        'location': 'Phone',
        'category': 'TASK',
        'priority': 'HIGH',
        'days_from_now': 1,
    },
    {
        'summary': 'F9 COA Appeal Brief — FILE',
        'description': 'File appellant brief in COA 366810. Per scheduling order (confirm with clerk).',
        'location': 'Court of Appeals, TrueFiling',
        'category': 'FILING',
        'priority': 'HIGH',
        'days_from_now': 30,
    },
]

def generate_ics(deadlines):
    """Generate ICS calendar file."""
    now = datetime.now()
    
    cal_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//LitigationOS//Tool #85//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:Pigors v Watson Litigation",
    ]
    
    for dl in deadlines:
        event_date = now + timedelta(days=dl['days_from_now'])
        dt_str = event_date.strftime("%Y%m%dT090000")
        uid = md5(dl['summary'].encode()).hexdigest()
        
        cal_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}@litigationos",
            f"DTSTART:{dt_str}",
            f"DTEND:{(event_date + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{dl['summary']}",
            f"DESCRIPTION:{dl['description'][:200]}",
            f"LOCATION:{dl.get('location', '')}",
            f"CATEGORIES:{dl['category']}",
            f"PRIORITY:{1 if dl['priority'] == 'CRITICAL' else 5 if dl['priority'] == 'HIGH' else 9}",
            # 1-day reminder
            "BEGIN:VALARM",
            "TRIGGER:-P1D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:TOMORROW: {dl['summary']}",
            "END:VALARM",
            # 1-week reminder
            "BEGIN:VALARM",
            "TRIGGER:-P7D",
            "ACTION:DISPLAY",
            f"DESCRIPTION:IN 1 WEEK: {dl['summary']}",
            "END:VALARM",
            "END:VEVENT",
        ])
    
    cal_lines.append("END:VCALENDAR")
    return '\r\n'.join(cal_lines)

def main():
    print("=" * 70)
    print("COURT CALENDAR & DEADLINE ICS GENERATOR — Tool #85")
    print("=" * 70)
    
    now = datetime.now()
    
    lines = [
        "# 📅 LITIGATION CALENDAR",
        "## Pigors v. Watson — All Deadlines",
        f"*Generated: {now.strftime('%Y-%m-%d %H:%M')}*",
        f"*{len(DEADLINES)} events | Import .ics file into any calendar app*\n",
        "---\n",
        "⚠️ **Dates are RELATIVE from generation date — Andrew must confirm actual deadlines**\n",
        "| Day | Date | Event | Priority | Category |",
        "|-----|------|-------|----------|----------|",
    ]
    
    for dl in sorted(DEADLINES, key=lambda x: x['days_from_now']):
        event_date = now + timedelta(days=dl['days_from_now'])
        lines.append(f"| +{dl['days_from_now']}d | {event_date.strftime('%b %d')} | {dl['summary']} | {dl['priority']} | {dl['category']} |")
        print(f"  +{dl['days_from_now']:>2}d  [{dl['priority'][:4]}]  {dl['summary'][:50]}")
    
    lines.extend([
        "",
        "## Import Instructions",
        "1. Find `litigation_calendar.ics` in `00_SYSTEM/reports/`",
        "2. **Google Calendar**: Settings → Import & export → Import → Select file",
        "3. **Outlook**: File → Open & Export → Import → iCalendar file",
        "4. **iPhone**: Email the .ics file to yourself → tap to import",
        "",
        f"*Court Calendar Generator — Tool #85*",
    ])
    
    # Generate ICS file
    ics_content = generate_ics(DEADLINES)
    ics_path = REPORTS_DIR / "litigation_calendar.ics"
    ics_path.write_text(ics_content, encoding='utf-8')
    
    md_path = REPORTS_DIR / "CALENDAR.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "calendar.json"
    json_path.write_text(json.dumps({
        'generated': now.isoformat(),
        'tool': 'Court Calendar ICS Generator (#85)',
        'total_events': len(DEADLINES),
        'critical': sum(1 for d in DEADLINES if d['priority'] == 'CRITICAL'),
        'high': sum(1 for d in DEADLINES if d['priority'] == 'HIGH'),
        'medium': sum(1 for d in DEADLINES if d['priority'] == 'MEDIUM'),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(DEADLINES)} calendar events generated")
    print(f"   ICS file: litigation_calendar.ics (import to any calendar app)")
    print(f"   Reports: CALENDAR.md + calendar.json")

if __name__ == '__main__':
    main()
