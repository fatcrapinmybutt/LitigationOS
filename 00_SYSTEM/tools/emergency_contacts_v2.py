#!/usr/bin/env python3
"""
Tool #204v2: Emergency Contact Quick Card v2
==============================================
All court, agency, and emergency phone numbers.
v2 — enhanced version with wallet-print format.
"""
import json, os, sys
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_contact_card():
    contacts = {
        "courts": [
            {"name": "14th Circuit Court — Family Division", "phone": "(231) 724-6241", "case": "2024-001507-DC", "priority": "HIGH"},
            {"name": "Michigan Court of Appeals", "phone": "(517) 373-0786", "case": "366810", "priority": "HIGH"},
            {"name": "Michigan Supreme Court", "phone": "(517) 373-0120", "priority": "MEDIUM"},
            {"name": "U.S. District Court — WDMI (Grand Rapids)", "phone": "(616) 456-2381", "priority": "MEDIUM"},
        ],
        "agencies": [
            {"name": "FOC — Pamela Rusco", "phone": "(231) 724-6200", "address": "990 Terrace St, Muskegon", "priority": "HIGH"},
            {"name": "Judicial Tenure Commission", "phone": "(313) 875-5110", "email": "jtc@michigan.gov", "priority": "HIGH"},
            {"name": "Attorney Grievance Commission", "phone": "(313) 961-6585", "priority": "MEDIUM"},
            {"name": "MI State Bar — UPL Unit", "phone": "(517) 346-6300", "priority": "MEDIUM"},
        ],
        "legal_aid": [
            {"name": "Legal Aid of Western Michigan", "phone": "(231) 726-4831", "priority": "HIGH"},
            {"name": "MI State Bar Lawyer Referral", "phone": "(800) 968-0738", "note": "$50/30min", "priority": "MEDIUM"},
            {"name": "Michigan Legal Help", "url": "michiganlegalhelp.org", "priority": "MEDIUM"},
        ],
        "emergency": [
            {"name": "CPS Hotline (24/7)", "phone": "(855) 444-3911", "priority": "CRITICAL"},
            {"name": "Muskegon DHHS", "phone": "(231) 733-3700", "priority": "HIGH"},
            {"name": "DV Hotline (24/7)", "phone": "(800) 799-7233", "priority": "CRITICAL"},
        ],
        "notary": [
            {"name": "UPS Store (Muskegon)", "phone": "(231) 798-4850", "note": "$5-10/sig", "priority": "HIGH"},
            {"name": "Muskegon Public Library", "phone": "(231) 724-6248", "note": "Free w/ card", "priority": "HIGH"},
        ],
        "efiling": [
            {"name": "MiFILE", "url": "mifile.courts.michigan.gov", "phone": "(517) 373-0130", "priority": "CRITICAL"},
            {"name": "PACER / CM-ECF", "url": "pacer.uscourts.gov", "phone": "(800) 676-6856", "priority": "HIGH"},
        ]
    }
    
    total = sum(len(v) for v in contacts.values())
    return {"tool_id": "204v2", "name": "Emergency Contact Quick Card v2", "generated": datetime.now().isoformat(),
            "contacts": contacts, "total_contacts": total}

def main():
    print("=" * 60)
    print("TOOL #204v2: EMERGENCY CONTACT QUICK CARD v2")
    print("=" * 60)
    
    card = build_contact_card()
    
    json_path = os.path.join(REPORT_DIR, 'EMERGENCY_CONTACTS_V2.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(card, f, indent=2, ensure_ascii=False)
    
    md_path = os.path.join(REPORT_DIR, 'EMERGENCY_CONTACTS_V2.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 📞 Emergency Contact Quick Card v2 (Tool #204v2)\n\n")
        f.write(f"**{card['total_contacts']} contacts** — *Print and carry to court*\n\n")
        
        emojis = {"courts": "⚖️", "agencies": "🏛️", "legal_aid": "🆓", "emergency": "🚨", "notary": "📝", "efiling": "💻"}
        for cat, items in card['contacts'].items():
            f.write(f"## {emojis.get(cat, '')} {cat.replace('_', ' ').title()}\n\n")
            for c in items:
                p = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(c.get('priority', ''), '')
                f.write(f"- {p} **{c['name']}**")
                if 'phone' in c: f.write(f" — 📞 {c['phone']}")
                if 'url' in c: f.write(f" — 🌐 {c['url']}")
                if 'case' in c: f.write(f" (Case #{c['case']})")
                if 'note' in c: f.write(f" *({c['note']})*")
                f.write("\n")
            f.write("\n")
    
    print(f"\n✅ Emergency Contact Card v2: {card['total_contacts']} contacts")
    print(f"   Reports: {md_path}")
    return card

if __name__ == '__main__':
    main()
