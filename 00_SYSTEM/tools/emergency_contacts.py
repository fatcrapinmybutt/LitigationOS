#!/usr/bin/env python3
"""
Tool #119 — Emergency Contact Card Generator
=================================================
🆕 NOVEL TOOL — Pocket-sized card with critical contacts
and numbers for every emergency scenario

Andrew should carry this AT ALL TIMES.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

CONTACTS = {
    'Courts': [
        {'name': '14th Circuit Court Clerk', 'phone': '(231) 724-6241', 'address': '990 Terrace St, Muskegon, MI 49442', 'note': 'Custody case 2024-001507-DC'},
        {'name': 'COA Clerk', 'phone': '(517) 373-0786', 'address': '925 W Ottawa, Lansing, MI 48915', 'note': 'COA 366810 — CALL to confirm brief deadline'},
        {'name': 'MSC Clerk', 'phone': '(517) 373-0120', 'address': '925 W Ottawa, Lansing, MI 48909', 'note': 'For F5 superintending control'},
        {'name': 'USDC WDMI Clerk', 'phone': '(616) 456-2381', 'address': '399 Federal Bldg, 110 Michigan St NW, Grand Rapids, MI 49503', 'note': 'For F4 federal §1983'},
    ],
    'Oversight Bodies': [
        {'name': 'Judicial Tenure Commission', 'phone': '(313) 875-5110', 'address': '3034 W Grand Blvd Ste 8-450, Detroit, MI 48202', 'note': 'F6 — judicial misconduct complaint'},
        {'name': 'Attorney Grievance Commission', 'phone': '(313) 961-6585', 'address': '535 Griswold St Ste 1700, Detroit, MI 48226', 'note': 'F10 — Barnes attorney grievance'},
        {'name': 'State Bar of Michigan', 'phone': '(517) 346-6300', 'address': '306 Townsend St, Lansing, MI 48933', 'note': 'General inquiries, pro se resources'},
    ],
    'Emergency Services': [
        {'name': 'Muskegon County Sheriff', 'phone': '(231) 724-6351', 'address': '', 'note': 'If custody order violated — ask for civil standby'},
        {'name': 'Michigan State Police', 'phone': '(231) 873-2171', 'address': '', 'note': 'Hart Post — covers Muskegon area'},
        {'name': 'CPS Hotline', 'phone': '(855) 444-3911', 'address': '', 'note': 'If you have concerns about L.D.W.\'s welfare'},
    ],
    'Legal Resources': [
        {'name': 'Michigan Legal Help', 'phone': '(888) 783-8190', 'address': 'michiganlegalhelp.org', 'note': 'Free self-help resources'},
        {'name': 'Lakeshore Legal Aid', 'phone': '(888) 783-8190', 'address': '', 'note': 'May provide free legal advice'},
        {'name': 'MiFILE (e-filing)', 'phone': '', 'address': 'mifile.courts.michigan.gov', 'note': 'Register HERE for electronic filing'},
        {'name': 'PACER (federal e-filing)', 'phone': '', 'address': 'pacer.uscourts.gov', 'note': 'Register HERE for federal filing'},
    ],
    'Case-Specific': [
        {'name': 'Andrew Pigors (self)', 'phone': '(231) 903-5690', 'address': '1977 Whitehall Rd Lot 17, N. Muskegon 49445', 'note': 'andrewjpigors@gmail.com'},
        {'name': 'Emily Watson (opposing)', 'phone': '', 'address': '2160 Garland Dr, Norton Shores 49441', 'note': 'Service address'},
    ],
}

def main():
    print("=" * 70)
    print("EMERGENCY CONTACT CARD — Tool #119")
    print("=" * 70)
    
    lines = [
        "# 📱 EMERGENCY CONTACT CARD",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #119*",
        "*PRINT THIS — Carry in wallet/phone case at all times*\n",
        "---\n",
    ]
    
    total_contacts = 0
    
    for category, contacts in CONTACTS.items():
        lines.append(f"## {category}\n")
        lines.append("| Name | Phone | Note |")
        lines.append("|------|-------|------|")
        
        for c in contacts:
            phone = c['phone'] if c['phone'] else '—'
            lines.append(f"| **{c['name']}** | {phone} | {c['note']} |")
            total_contacts += 1
            
            if c['phone']:
                print(f"  📞 {c['name'][:30]}: {c['phone']}")
        
        lines.append("")
    
    lines.extend([
        "---",
        "## 🚨 WHAT TO DO IN AN EMERGENCY\n",
        "### If Emily violates a court order:",
        "1. Document EVERYTHING (photos, screenshots, timestamps)",
        "2. Call Muskegon Sheriff for civil standby if needed",
        "3. File motion for contempt with 14th Circuit clerk",
        "4. Do NOT escalate in person — let the court handle it\n",
        
        "### If you receive unexpected court papers:",
        "1. READ everything immediately — note any response deadlines",
        "2. Call the issuing court clerk to verify authenticity",
        "3. Start preparing response immediately (most deadlines are 14-28 days)",
        "4. Calendar the deadline + a reminder 7 days before\n",
        
        "### If someone threatens you:",
        "1. Call 911 if immediate danger",
        "2. Document the threat (save messages, note witnesses)",
        "3. File police report",
        "4. Consider seeking your own PPO if warranted\n",
        
        "### Case Numbers (keep these handy):",
        "- **2024-001507-DC** — Custody (14th Circuit)",
        "- **2023-5907-PP** — PPO (14th Circuit)",
        "- **COA 366810** — Court of Appeals",
        "",
        f"*Emergency Contact Card — Tool #119 — {total_contacts} contacts*",
    ])
    
    md_path = REPORTS_DIR / "EMERGENCY_CONTACTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "emergency_contacts.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Emergency Contact Card (#119)',
        'total_contacts': total_contacts,
        'categories': list(CONTACTS.keys()),
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_contacts} contacts across {len(CONTACTS)} categories")
    print(f"   PRINT AND CARRY AT ALL TIMES")
    print(f"   Reports: EMERGENCY_CONTACTS.md + emergency_contacts.json")

if __name__ == '__main__':
    main()
