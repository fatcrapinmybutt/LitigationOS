#!/usr/bin/env python3
"""
Tool #50 — Sanctions Risk Analyzer
====================================
Analyzes all 10 filings for potential sanctions risks under:
- MCR 1.109(E) — Signing of documents (frivolous filing sanctions)
- FRCP 11 — Federal sanctions for frivolous claims
- 28 USC §1927 — Vexatious multiplication of proceedings
- MCL 600.2591 — Frivolous civil action sanctions

A pro se litigant filing 10 simultaneous actions across 6 courts
faces SERIOUS sanctions risk if any filing is:
1. Factually unsupported (claims without evidence)
2. Legally frivolous (no legal basis)
3. Filed for improper purpose (harassment/delay)
4. Duplicative of other pending actions

This tool scans each filing for red flags and provides mitigation guidance.
"""
import sys, json, re, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

SANCTIONS_RULES = {
    'MCR 1.109(E)': 'Michigan — signing certification: factual basis, legal merit, not improper purpose',
    'FRCP 11': 'Federal — same as MCR 1.109(E) but with 21-day safe harbor',
    '28 USC 1927': 'Federal — attorney/party who multiplies proceedings unreasonably',
    'MCL 600.2591': 'Michigan — frivolous civil actions, prevailing party fees',
}

RED_FLAGS = {
    'inflammatory_language': {
        'patterns': [
            r'\b(corrupt|criminal|evil|insane|crazy|lunatic|psychopath|sociopath)\b',
            r'\b(kangaroo court|sham|witch hunt|vendetta|conspiracy to destroy)\b',
            r'\b(worst judge|incompetent|disgrace|outrageous|shocking|appalling)\b',
        ],
        'severity': 'HIGH',
        'description': 'Inflammatory or ad hominem language that judges view as improper',
        'mitigation': 'Replace with neutral factual descriptions. "Corrupt judge" → "The court\'s pattern of ex parte communications violated Canon 3(A)(4)"',
    },
    'unsupported_claims': {
        'patterns': [
            r'\[(?:CITE|SOURCE|EVIDENCE)\s*(?:NEEDED|REQUIRED|MISSING)\]',
            r'\[ANDREW_REQUIRED\]',
            r'\[INSERT\s',
            r'\[ATTACH\s',
            r'(?:no evidence|without evidence|unsubstantiated)',
        ],
        'severity': 'CRITICAL',
        'description': 'Claims without evidentiary support violate MCR 1.109(E)/FRCP 11',
        'mitigation': 'Every factual claim must cite specific evidence (exhibit number, DB record, document)',
    },
    'fabricated_stats': {
        'patterns': [
            r'(?:over|more than|approximately)\s+\d{3,}\s+(?:violations|incidents|episodes)',
            r'\d{2,}%\s+(?:of the time|chance|probability|score)',
            r'(?:hundreds|thousands)\s+of\s+(?:violations|incidents)',
        ],
        'severity': 'CRITICAL',
        'description': 'Aggregate statistics must be traceable to specific DB queries',
        'mitigation': 'Replace vague counts with specific DB-verified numbers or remove',
    },
    'duplicative_claims': {
        'patterns': [
            r'(?:as stated in|as argued in|see also)\s+(?:the|our)\s+(?:complaint|motion|petition)',
            r'(?:same|identical|similar)\s+(?:claims?|arguments?|issues?)\s+(?:as|in)',
        ],
        'severity': 'MEDIUM',
        'description': 'Cross-referencing other filings raises duplicative proceedings concern',
        'mitigation': 'Each filing must stand alone. Cross-references should be factual, not argumentative',
    },
    'conclusory_allegations': {
        'patterns': [
            r'(?:clearly|obviously|undeniably|unquestionably|indisputably)',
            r'(?:it is clear that|there is no doubt|without question)',
            r'(?:everyone knows|common knowledge|self-evident)',
        ],
        'severity': 'MEDIUM',
        'description': 'Conclusory statements without factual support are disfavored',
        'mitigation': 'Replace with specific factual allegations supported by evidence',
    },
    'improper_purpose': {
        'patterns': [
            r'(?:teach .+ a lesson|make .+ pay|punish|revenge|retaliate)',
            r'(?:destroy .+ reputation|ruin .+ career|embarrass)',
            r'(?:flood .+ with|overwhelm .+ court|bury .+ in)',
        ],
        'severity': 'HIGH',
        'description': 'Language suggesting improper purpose (harassment/delay/revenge)',
        'mitigation': 'All filings must seek legitimate legal relief, not personal revenge',
    },
    'judicial_immunity_issues': {
        'patterns': [
            r'(?:sue|damages? against|liability of)\s+(?:the judge|Judge McNeill|the court)',
            r'(?:personal liability|personally liable|hold .+ personally)',
        ],
        'severity': 'HIGH',
        'description': 'Judicial immunity claims need careful legal basis (§1983 conspiracy exception)',
        'mitigation': 'Must clearly invoke Dennis v Sparks conspiracy exception or declaratory/injunctive relief (not damages)',
    },
}

def scan_filing(filepath):
    """Scan a filing for sanctions risks."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except:
        return {'error': f'Could not read {filepath}'}
    
    findings = []
    content_lower = content.lower()
    
    for flag_name, flag_info in RED_FLAGS.items():
        for pattern in flag_info['patterns']:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for m in matches:
                # Get context (surrounding text)
                start = max(0, m.start() - 50)
                end = min(len(content), m.end() + 50)
                context = content[start:end].replace('\n', ' ').strip()
                
                # Find line number
                line_num = content[:m.start()].count('\n') + 1
                
                findings.append({
                    'flag': flag_name,
                    'severity': flag_info['severity'],
                    'match': m.group(),
                    'context': context,
                    'line': line_num,
                    'description': flag_info['description'],
                    'mitigation': flag_info['mitigation'],
                })
    
    return {
        'file': filepath.name,
        'word_count': len(content.split()),
        'findings': findings,
        'critical': sum(1 for f in findings if f['severity'] == 'CRITICAL'),
        'high': sum(1 for f in findings if f['severity'] == 'HIGH'),
        'medium': sum(1 for f in findings if f['severity'] == 'MEDIUM'),
    }

def assess_multi_filing_risk(all_results):
    """Assess systemic risk of filing 10 actions simultaneously."""
    risks = []
    
    total_filings = len(all_results)
    if total_filings > 5:
        risks.append({
            'risk': f'Filing {total_filings} simultaneous actions across multiple courts',
            'severity': 'HIGH',
            'rule': '28 USC §1927 / MCR 1.109(E)',
            'mitigation': (
                'Stagger filings over 2-4 weeks. File the strongest cases first (F3, F4, F6). '
                'Each filing must clearly articulate WHY it cannot be consolidated with others '
                '(different courts, different legal theories, different parties).'
            ),
        })
    
    # Check for overlapping claims
    courts = {}
    for fid, result in all_results.items():
        court = get_court_for_filing(fid)
        if court not in courts:
            courts[court] = []
        courts[court].append(fid)
    
    for court, fids in courts.items():
        if len(fids) > 2:
            risks.append({
                'risk': f'{len(fids)} filings in {court}: {", ".join(fids)}',
                'severity': 'MEDIUM',
                'rule': 'Duplicative proceedings concern',
                'mitigation': f'Consider consolidating {", ".join(fids)} or filing sequentially',
            })
    
    return risks

def get_court_for_filing(fid):
    """Map filing ID to court."""
    courts = {
        'F1': '14th Circuit', 'F2': '14th Circuit', 'F3': '14th Circuit',
        'F4': 'USDC WDMI', 'F5': 'MSC', 'F6': 'JTC',
        'F7': '14th Circuit', 'F8': 'COA', 'F9': 'COA', 'F10': 'AGC',
    }
    return courts.get(fid, 'Unknown')

def calculate_risk_score(results, systemic_risks):
    """Calculate overall sanctions risk score."""
    critical_total = sum(r.get('critical', 0) for r in results.values())
    high_total = sum(r.get('high', 0) for r in results.values())
    medium_total = sum(r.get('medium', 0) for r in results.values())
    
    score = critical_total * 10 + high_total * 5 + medium_total * 2
    score += len(systemic_risks) * 8
    
    if score == 0:
        level = "🟢 MINIMAL"
    elif score <= 20:
        level = "🟡 LOW"
    elif score <= 50:
        level = "🟠 MODERATE"
    elif score <= 100:
        level = "🔴 HIGH"
    else:
        level = "⛔ CRITICAL"
    
    return score, level

def main():
    print("=" * 70)
    print("SANCTIONS RISK ANALYZER — Tool #50")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Scan all filing packages
    pkg_dirs = sorted(PKG_BASE.glob("PKG_F*"))
    print(f"\n📁 Found {len(pkg_dirs)} filing packages")
    
    all_results = {}
    
    for pkg_dir in pkg_dirs:
        fid = pkg_dir.name.split('_')[1]
        print(f"\n🔍 Scanning {fid}...")
        
        # Scan main filing and brief
        for pattern in ['01_MAIN_FILING.md', '01B_BRIEF_IN_SUPPORT.md']:
            filepath = pkg_dir / pattern
            if filepath.exists():
                result = scan_filing(filepath)
                key = f"{fid}_{filepath.stem}"
                all_results[key] = {**result, 'filing_id': fid}
                
                c, h, m = result['critical'], result['high'], result['medium']
                total = c + h + m
                print(f"  {filepath.name}: {total} flags (C:{c} H:{h} M:{m})")
    
    # Assess systemic risks
    print("\n⚠️ Assessing systemic multi-filing risks...")
    fid_results = {}
    for key, result in all_results.items():
        fid = result['filing_id']
        if fid not in fid_results:
            fid_results[fid] = result
        else:
            # Merge findings
            fid_results[fid]['findings'].extend(result['findings'])
            fid_results[fid]['critical'] += result['critical']
            fid_results[fid]['high'] += result['high']
            fid_results[fid]['medium'] += result['medium']
    
    systemic_risks = assess_multi_filing_risk(fid_results)
    for risk in systemic_risks:
        print(f"  [{risk['severity']}] {risk['risk']}")
    
    # Calculate overall risk
    score, level = calculate_risk_score(all_results, systemic_risks)
    print(f"\n📊 Overall Risk Score: {score} — {level}")
    
    # Generate report
    lines = [
        "# SANCTIONS RISK ANALYSIS REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Overall Risk: {level} (Score: {score})",
        "",
        "### Applicable Sanctions Rules",
        "| Rule | Scope |",
        "|------|-------|",
    ]
    for rule, desc in SANCTIONS_RULES.items():
        lines.append(f"| {rule} | {desc} |")
    
    lines.extend([
        "",
        "## Per-Filing Risk Summary",
        "| Filing | Court | Critical | High | Medium | Total |",
        "|--------|-------|----------|------|--------|-------|",
    ])
    
    for fid in sorted(fid_results.keys()):
        r = fid_results[fid]
        court = get_court_for_filing(fid)
        lines.append(f"| {fid} | {court} | {r['critical']} | {r['high']} | {r['medium']} | {r['critical']+r['high']+r['medium']} |")
    
    if systemic_risks:
        lines.extend(["", "## Systemic Risks"])
        for risk in systemic_risks:
            lines.extend([
                f"### [{risk['severity']}] {risk['risk']}",
                f"**Rule:** {risk['rule']}",
                f"**Mitigation:** {risk['mitigation']}",
                "",
            ])
    
    # Top findings
    all_findings = []
    for key, result in all_results.items():
        for f in result.get('findings', []):
            all_findings.append({**f, 'source': key})
    
    critical_findings = [f for f in all_findings if f['severity'] == 'CRITICAL']
    high_findings = [f for f in all_findings if f['severity'] == 'HIGH']
    
    if critical_findings:
        lines.extend(["", "## ⛔ CRITICAL Findings (Fix Before Filing)"])
        for f in critical_findings[:20]:
            lines.extend([
                f"- **{f['source']}** line {f['line']}: `{f['match']}`",
                f"  *{f['description']}*",
                f"  Fix: {f['mitigation']}",
                "",
            ])
    
    if high_findings:
        lines.extend(["", "## 🔴 HIGH Findings (Strongly Recommend Fixing)"])
        for f in high_findings[:20]:
            lines.extend([
                f"- **{f['source']}** line {f['line']}: `{f['match']}`",
                f"  *{f['description']}*",
                f"  Fix: {f['mitigation']}",
                "",
            ])
    
    lines.extend([
        "",
        "## Recommendations",
        "",
        "1. **Fix all CRITICAL findings** before filing — these are sanctionable",
        "2. **Stagger filings** — don't file all 10 on the same day",
        "3. **Each filing must stand alone** — don't assume judges read other filings",
        "4. **Keep tone professional** — remove inflammatory language",
        "5. **Every claim needs evidence** — cite specific exhibits/records",
        "6. **Federal FRCP 11 has 21-day safe harbor** — serve F4 first, wait 21 days before filing",
    ])
    
    md_path = REPORTS_DIR / "SANCTIONS_RISK_REPORT.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "sanctions_risk.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Sanctions Risk Analyzer (#50)',
        'overall_score': score,
        'overall_level': level,
        'per_filing': {k: {'critical': v['critical'], 'high': v['high'], 'medium': v['medium']} for k, v in fid_results.items()},
        'systemic_risks': systemic_risks,
        'total_findings': len(all_findings),
        'critical_count': len(critical_findings),
        'high_count': len(high_findings),
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ Reports: {md_path.name}, {json_path.name}")
    print(f"📊 {len(all_findings)} total flags | {len(critical_findings)} critical | {len(high_findings)} high")

if __name__ == '__main__':
    main()
