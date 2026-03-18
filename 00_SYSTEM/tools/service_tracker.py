#!/usr/bin/env python3
"""
Service of Process Tracker — LitigationOS Novel Tool
======================================================
Tracks service requirements for all 10 filings per Michigan Court Rules.

For each filing generates:
  1. Who must be served (parties, courts, agencies)
  2. How they must be served (personal, mail, e-service, MiFILE)
  3. Deadlines for service (MCR 2.107 timelines)
  4. Certificate of Service template
  5. Service completion checklist

Michigan Service Rules:
  - MCR 2.105: Personal service methods
  - MCR 2.107: Service of pleadings/papers after first service
  - MCR 2.107(C)(3): Mail service adds 3 days
  - MCR 7.215: COA service requirements
  - FRCP 4: Federal service (§1983)

Usage:
  python service_tracker.py --dashboard        # Full service dashboard
  python service_tracker.py --filing F9        # Service reqs for one filing
  python service_tracker.py --generate-certs   # Generate all cert of service templates
  python service_tracker.py --checklist        # Print service checklist
"""

import sys, os, json, argparse
from datetime import datetime, date

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

# ─── PARTY REGISTRY (verified — NEVER fabricate) ─────────────────────

PARTIES = {
    'andrew': {
        'name': 'Andrew James Pigors',
        'role': 'Plaintiff / Petitioner / Appellant',
        'address': '1977 Whitehall Road, Lot 17, North Muskegon, MI 49445',
        'phone': '(231) 903-5690',
        'email': 'andrewjpigors@gmail.com',
        'pro_se': True,
    },
    'emily': {
        'name': 'Emily A. Watson',
        'role': 'Defendant / Respondent / Appellee',
        'address': '2160 Garland Drive, Norton Shores, MI 49441',
        'attorney': None,  # Barnes withdrew
        'service_method': 'First-class mail + Certificate of Mailing',
    },
    'mcneill': {
        'name': 'Hon. Jenny L. McNeill',
        'role': 'Respondent Judge',
        'address': '14th Circuit Court, 990 Terrace St, Muskegon, MI 49442',
        'service_method': 'Via court clerk',
    },
    'berry': {
        'name': 'Ronald T. Berry',
        'role': 'Co-Defendant (Emily\'s boyfriend)',
        'address': '[ADDRESS NEEDED — east side of MI]',
        'service_method': 'First-class mail',
    },
    'barnes': {
        'name': 'Jennifer Barnes (P55406)',
        'role': 'Former Attorney — WITHDREW',
        'address': 'Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440',
        'service_method': 'First-class mail',
    },
    'jtc': {
        'name': 'Michigan Judicial Tenure Commission',
        'role': 'Regulatory Body',
        'address': '3034 W Grand Blvd, Suite 8-450, Detroit, MI 48202',
        'service_method': 'First-class mail',
    },
    'shady_oaks': {
        'name': 'Shady Oaks MHP / Cricklewood MHP LLC',
        'role': 'Defendant (Housing)',
        'address': '[LARA REGISTERED AGENT ADDRESS NEEDED]',
        'service_method': 'Personal service or registered agent',
    },
    '14th_circuit_clerk': {
        'name': '14th Circuit Court Clerk',
        'role': 'Court Clerk',
        'address': '990 Terrace St, Muskegon, MI 49442',
        'service_method': 'Filing via MiFILE or in-person',
    },
}

# ─── SERVICE REQUIREMENTS PER FILING ─────────────────────────────────

SERVICE_REQUIREMENTS = {
    'F1': {
        'name': 'Emergency TRO (Housing)',
        'court': '14th Circuit Court',
        'filing_method': 'MiFILE (mifile.courts.michigan.gov) or in-person',
        'serve': [
            {'party': 'shady_oaks', 'method': 'Personal service — MCR 2.105(A)', 'timing': 'Before or at TRO hearing'},
            {'party': '14th_circuit_clerk', 'method': 'MiFILE e-filing', 'timing': 'With motion'},
        ],
        'rules': ['MCR 3.310(B)', 'MCR 2.105(A)'],
        'notes': 'Emergency TRO may be granted ex-parte; service within reasonable time after.',
    },
    'F2': {
        'name': 'Amended Complaint (Housing)',
        'court': '14th Circuit Court — Chief Judge Kenneth Hoopes',
        'filing_method': 'MiFILE',
        'serve': [
            {'party': 'shady_oaks', 'method': 'Personal service via process server — MCR 2.105(A)', 'timing': 'Within 91 days of filing — MCR 2.102(D)'},
        ],
        'rules': ['MCR 2.118(A)', 'MCR 2.105(A)', 'MCR 2.102(D)'],
        'notes': 'Amendment as of right within 21 days. After: leave of court needed.',
    },
    'F3': {
        'name': 'Disqualification Motion (MCR 2.003)',
        'court': '14th Circuit Court',
        'filing_method': 'MiFILE',
        'serve': [
            {'party': 'emily', 'method': 'First-class mail — MCR 2.107(C)(1)', 'timing': 'Same day as filing'},
            {'party': 'mcneill', 'method': 'Via court clerk — MCR 2.003(D)', 'timing': 'Filed with clerk, forwarded to judge'},
        ],
        'rules': ['MCR 2.003(D)', 'MCR 2.107(C)(1)'],
        'notes': 'MCR 2.003(D)(1): Motion must be filed and served promptly after grounds discovered.',
    },
    'F4': {
        'name': 'Federal §1983 Complaint',
        'court': 'US District Court, Western District of Michigan (Grand Rapids)',
        'filing_method': 'CM/ECF (pacer.uscourts.gov) or in-person',
        'serve': [
            {'party': 'emily', 'method': 'Personal service or waiver — FRCP 4(e)', 'timing': '90 days from filing — FRCP 4(m)'},
            {'party': 'berry', 'method': 'Personal service — FRCP 4(e)', 'timing': '90 days from filing'},
            {'party': 'barnes', 'method': 'Personal service — FRCP 4(e)', 'timing': '90 days from filing'},
            {'party': 'mcneill', 'method': 'State AG + judge personally — FRCP 4(j)', 'timing': '90 days from filing'},
        ],
        'rules': ['FRCP 4(c)-(m)', '42 USC §1983', '28 USC §1915 (IFP)'],
        'notes': 'IFP: if granted, USMS serves. Request waiver of service (FRCP 4(d)) to save costs.',
    },
    'F5': {
        'name': 'MSC Original Action',
        'court': 'Michigan Supreme Court',
        'filing_method': 'MiFILE or mail to MSC Clerk',
        'serve': [
            {'party': 'emily', 'method': 'First-class mail — MCR 7.306(B)', 'timing': 'Within 7 days of filing'},
            {'party': '14th_circuit_clerk', 'method': 'First-class mail — MCR 7.306(B)', 'timing': 'Within 7 days of filing'},
        ],
        'rules': ['MCR 7.306(B)', 'Const 1963 Art 6 §4'],
        'notes': 'Extraordinary action — must demonstrate lower court systemic failure.',
    },
    'F6': {
        'name': 'JTC Complaint',
        'court': 'Michigan Judicial Tenure Commission',
        'filing_method': 'Mail to JTC',
        'serve': [
            {'party': 'jtc', 'method': 'First-class mail to JTC office', 'timing': 'N/A — complaint to agency'},
        ],
        'rules': ['MCR 9.104', 'MCR 9.116'],
        'notes': 'JTC handles its own investigation and service. No party service required.',
    },
    'F7': {
        'name': 'Custody Modification Motion',
        'court': '14th Circuit Court',
        'filing_method': 'MiFILE',
        'serve': [
            {'party': 'emily', 'method': 'First-class mail — MCR 2.107(C)(1)', 'timing': 'At least 9 days before hearing — MCR 2.119(C)(1)'},
        ],
        'rules': ['MCR 2.119(C)(1)', 'MCL 722.27(1)(c)'],
        'notes': 'Motion hearing: 9 days notice by mail (MCR 2.119(C)(1) + 3 days for mail).',
    },
    'F8': {
        'name': 'PPO Termination / Modification',
        'court': '14th Circuit Court',
        'filing_method': 'MiFILE',
        'serve': [
            {'party': 'emily', 'method': 'First-class mail — MCR 2.107(C)(1)', 'timing': '9 days before hearing'},
        ],
        'rules': ['MCL 600.2950(8)', 'MCR 3.706(H)'],
        'notes': 'Motion to modify/terminate PPO under MCL 600.2950(8).',
    },
    'F9': {
        'name': 'COA Brief on Appeal',
        'court': 'Michigan Court of Appeals',
        'filing_method': 'MiFILE (COA e-filing)',
        'serve': [
            {'party': 'emily', 'method': 'First-class mail — MCR 7.215(B)', 'timing': 'Same day as filing'},
        ],
        'rules': ['MCR 7.212(A)(6)', 'MCR 7.215(B)'],
        'notes': 'COA Case No. 366810. Cert of Service must name method and date.',
    },
    'F10': {
        'name': 'COA Emergency Motion',
        'court': 'Michigan Court of Appeals',
        'filing_method': 'MiFILE + call COA clerk',
        'serve': [
            {'party': 'emily', 'method': 'Email + mail — MCR 7.211(C)(6)', 'timing': 'Same day — emergency'},
        ],
        'rules': ['MCR 7.211(C)(6)', 'MCR 7.215(B)'],
        'notes': 'Emergency: call COA clerk after filing. Opposing party must receive same-day notice.',
    },
}


def generate_cert_of_service(filing_id, info):
    """Generate a Certificate of Service for a filing."""
    today = date.today().strftime('%B %d, %Y')
    
    lines = [
        f"## CERTIFICATE OF SERVICE",
        f"",
        f"**Case:** {info.get('court', '')}",
        f"**Filing:** {info['name']}",
        f"",
        f"I, Andrew James Pigors, certify that on {today}, I served a true and correct",
        f"copy of the foregoing {info['name']} upon the following parties by the method indicated:",
        f"",
    ]
    
    for s in info['serve']:
        party = PARTIES.get(s['party'], {})
        lines.append(f"**{party.get('name', s['party'])}**")
        lines.append(f"  {party.get('address', '[ADDRESS]')}")
        lines.append(f"  Method: {s['method']}")
        lines.append(f"  Timing: {s['timing']}")
        lines.append(f"")
    
    lines += [
        f"",
        f"/s/ Andrew James Pigors",
        f"Andrew James Pigors, Pro Se",
        f"1977 Whitehall Road, Lot 17",
        f"North Muskegon, MI 49445",
        f"(231) 903-5690",
        f"andrewjpigors@gmail.com",
        f"",
        f"Dated: {today}",
    ]
    
    return '\n'.join(lines)


def print_dashboard(verbose=False):
    """Print full service dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  SERVICE OF PROCESS TRACKER — LitigationOS")
    print(f"  {date.today().isoformat()}")
    print(f"{'═' * 78}\n")
    
    print(f"  {'Filing':<6} {'Name':<32} {'Serve To':<3} {'Method':<30} {'Court'}")
    print(f"  {'─' * 76}")
    
    for fid in ['F10', 'F3', 'F9', 'F1', 'F7', 'F5', 'F4', 'F8', 'F2', 'F6']:
        info = SERVICE_REQUIREMENTS.get(fid, {})
        serve_count = len(info.get('serve', []))
        name = info.get('name', '')[:32]
        method = info.get('filing_method', '')[:30]
        court = info.get('court', '')[:30]
        print(f"  {fid:<6} {name:<32} {serve_count:>3}   {method:<30} {court}")
    
    print()
    
    if verbose:
        for fid in sorted(SERVICE_REQUIREMENTS.keys()):
            info = SERVICE_REQUIREMENTS[fid]
            print(f"  ▓ {fid} — {info['name']}")
            print(f"    Court: {info['court']}")
            print(f"    Filing: {info['filing_method']}")
            print(f"    Rules: {', '.join(info['rules'])}")
            print(f"    Notes: {info['notes']}")
            print(f"    Service:")
            for s in info['serve']:
                party = PARTIES.get(s['party'], {})
                print(f"      → {party.get('name', s['party'])}")
                print(f"        Address: {party.get('address', '[NEEDED]')}")
                print(f"        Method: {s['method']}")
                print(f"        When: {s['timing']}")
            print()
    
    # Missing addresses
    print(f"  ⚠ ADDRESSES NEEDED:")
    for pid, p in PARTIES.items():
        if '[' in p.get('address', '') and 'NEEDED' in p.get('address', ''):
            filings_needing = [fid for fid, info in SERVICE_REQUIREMENTS.items()
                              if any(s['party'] == pid for s in info['serve'])]
            print(f"    {p['name']}: {p['address']} (needed for {', '.join(filings_needing)})")
    print()


def main():
    parser = argparse.ArgumentParser(description='Service of Process Tracker')
    parser.add_argument('--dashboard', '-d', action='store_true', help='Full dashboard')
    parser.add_argument('--filing', '-f', type=str, help='Service reqs for one filing')
    parser.add_argument('--generate-certs', '-g', action='store_true', help='Generate certs of service')
    parser.add_argument('--checklist', '-c', action='store_true', help='Print checklist')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not any([args.dashboard, args.filing, args.generate_certs, args.checklist]):
        args.dashboard = True
        args.verbose = True
    
    if args.dashboard:
        print_dashboard(args.verbose)
    
    if args.filing:
        fid = args.filing.upper()
        info = SERVICE_REQUIREMENTS.get(fid)
        if info:
            print(f"\n  {fid}: {info['name']}")
            for s in info['serve']:
                party = PARTIES.get(s['party'], {})
                print(f"  → {party.get('name')}: {s['method']}")
        else:
            print(f"  Filing {fid} not found")
    
    if args.generate_certs:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        for fid, info in SERVICE_REQUIREMENTS.items():
            cert = generate_cert_of_service(fid, info)
            cpath = os.path.join(REPORTS_DIR, f'cert_of_service_{fid}.md')
            with open(cpath, 'w', encoding='utf-8') as f:
                f.write(cert)
        print(f"\n  ✅ Generated {len(SERVICE_REQUIREMENTS)} certificates of service")
        print(f"     Location: {REPORTS_DIR}/cert_of_service_F*.md")
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'service_requirements.json')
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({
                'parties': {k: v for k, v in PARTIES.items()},
                'requirements': SERVICE_REQUIREMENTS,
                'generated': datetime.now().isoformat(),
            }, f, indent=2, default=str)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
