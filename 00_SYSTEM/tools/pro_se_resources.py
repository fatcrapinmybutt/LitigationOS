#!/usr/bin/env python3
"""
Tool #177 — Pro Se Resource Directory
=================================================
🆕 NOVEL TOOL — Comprehensive directory of free legal
resources available to pro se litigants in Michigan.
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

RESOURCES = {
    'legal_aid': {
        'title': '📞 Free Legal Aid',
        'entries': [
            {'name': 'Michigan Legal Help', 'url': 'michiganlegalhelp.org', 'desc': 'Free legal information, forms, and self-help tools'},
            {'name': 'Legal Aid of Western Michigan', 'url': 'lawestmi.org', 'desc': 'Free legal services for qualifying individuals — (888) 783-8190'},
            {'name': 'State Bar Lawyer Referral', 'url': 'michbar.org/LRS', 'desc': 'Low-cost initial consultations — (800) 968-0738'},
            {'name': 'Muskegon County Law Library', 'url': '990 Terrace St, Muskegon', 'desc': 'Free access to legal databases and research materials'},
        ],
    },
    'court_resources': {
        'title': '🏛️ Court Self-Help',
        'entries': [
            {'name': 'Michigan Courts Self-Help', 'url': 'courts.michigan.gov/self-help', 'desc': 'Official forms, instructions, and guides'},
            {'name': 'MiFILE E-Filing', 'url': 'mifile.courts.michigan.gov', 'desc': 'Electronic filing system — register for an account'},
            {'name': 'SCAO Forms', 'url': 'courts.michigan.gov/administration/scao/forms', 'desc': 'All approved court forms (MC, DC, CC, FOC series)'},
            {'name': '14th Circuit Court Clerk', 'url': '(231) 724-6241', 'desc': '990 Terrace St, Muskegon — hours: 8AM-5PM M-F'},
        ],
    },
    'federal_resources': {
        'title': '🇺🇸 Federal Court',
        'entries': [
            {'name': 'PACER', 'url': 'pacer.uscourts.gov', 'desc': 'Federal court electronic filing and case access'},
            {'name': 'USDC W.D. Michigan', 'url': 'miwd.uscourts.gov', 'desc': 'Western District Pro Se Handbook available online'},
            {'name': 'Federal Pro Se Clinic', 'url': 'Contact USDC clerk', 'desc': 'Free assistance with federal filings'},
        ],
    },
    'appellate_resources': {
        'title': '📖 Appellate Courts',
        'entries': [
            {'name': 'COA Clerk', 'url': '(517) 373-0786', 'desc': 'Court of Appeals — filing questions'},
            {'name': 'MSC Clerk', 'url': '(517) 373-0120', 'desc': 'Supreme Court — filing questions'},
            {'name': 'COA 366810', 'url': 'Already filed', 'desc': 'Andrew\'s appeal — call for status/deadlines'},
        ],
    },
    'domestic_violence': {
        'title': '🛡️ DV / Family Resources',
        'entries': [
            {'name': 'Every Woman\'s Place', 'url': '(231) 722-3333', 'desc': 'Muskegon — DV advocacy (NOTE: resources not gender-exclusive)'},
            {'name': 'Michigan DV Hotline', 'url': '(800) 799-7233', 'desc': 'National hotline — resources for all genders'},
            {'name': 'Fathers\' Rights Resources', 'url': 'fathers4justice.com', 'desc': 'Advocacy and support for father\'s custody rights'},
        ],
    },
    'mental_health': {
        'title': '🧠 Mental Health & Support',
        'entries': [
            {'name': 'HealthWest (Muskegon CMH)', 'url': '(231) 724-1111', 'desc': 'Community mental health — sliding scale fees'},
            {'name': 'Crisis Line', 'url': '988', 'desc': 'Suicide & Crisis Lifeline — call or text 988'},
            {'name': 'NAMI Muskegon', 'url': 'namimuskegon.org', 'desc': 'Support groups and mental health education'},
        ],
    },
}

def main():
    print("=" * 70)
    print("PRO SE RESOURCE DIRECTORY — Tool #177")
    print("=" * 70)

    lines = [
        "# 📚 PRO SE RESOURCE DIRECTORY",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #177*",
        f"*Free resources for pro se litigants in Michigan*\n",
        "---\n",
    ]

    total_resources = 0
    for key, section in RESOURCES.items():
        lines.append(f"## {section['title']}\n")
        lines.append("| Resource | Contact/URL | Description |")
        lines.append("|----------|-------------|-------------|")
        for entry in section['entries']:
            lines.append(f"| {entry['name']} | {entry['url']} | {entry['desc']} |")
        lines.append("")
        total_resources += len(section['entries'])
        print(f"  {section['title']}: {len(section['entries'])} resources")

    lines.extend([
        "---\n",
        f"*{len(RESOURCES)} categories · {total_resources} resources · All free or low-cost*",
    ])

    md_path = REPORTS_DIR / "PRO_SE_RESOURCES.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')

    json_path = REPORTS_DIR / "pro_se_resources.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Pro Se Resource Directory (#177)',
        'categories': len(RESOURCES),
        'total_resources': total_resources,
    }, indent=2), encoding='utf-8')

    print(f"\n✅ {len(RESOURCES)} categories, {total_resources} resources")
    print(f"   Reports: PRO_SE_RESOURCES.md + pro_se_resources.json")

if __name__ == '__main__':
    main()
