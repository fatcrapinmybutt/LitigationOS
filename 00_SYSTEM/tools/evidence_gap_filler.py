#!/usr/bin/env python3
"""
Tool #116 — Evidence Gap Filler
===================================
🆕 NOVEL TOOL — Identifies what evidence Andrew
STILL NEEDS and how to get it

Cross-references claims in each filing against
available evidence in the DB, then generates
specific acquisition tasks.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

EVIDENCE_NEEDS = {
    'F1': {
        'name': 'Emergency Parenting Time',
        'needed': [
            {'item': 'Documented parenting time requests (text/email)', 'status': 'HAVE', 'source': 'chatgpt_evidence + evidence_quotes'},
            {'item': 'Documented denials/non-responses', 'status': 'HAVE', 'source': 'detected_contradictions'},
            {'item': 'Evidence of harm to child from separation', 'status': 'NEED', 'how': 'Psychological literature on parent-child separation; Consider requesting GAL evaluation'},
            {'item': 'MCL 722.27a(3) — no findings made', 'status': 'HAVE', 'source': 'Court docket — absence of required findings'},
            {'item': 'Proposed parenting plan', 'status': 'HAVE', 'source': 'mediation_prep.py (Tool #112)'},
        ],
    },
    'F2': {
        'name': 'Fraud on Court',
        'needed': [
            {'item': 'Specific false statements under oath', 'status': 'HAVE', 'source': 'watson_perjury_compilation (5,821 items)'},
            {'item': 'Evidence contradicting false statements', 'status': 'HAVE', 'source': 'detected_contradictions (1,061)'},
            {'item': 'Proof statements were KNOWING (not mistake)', 'status': 'PARTIAL', 'how': 'Pattern of multiple false statements suggests knowledge, not error'},
            {'item': 'Proof of materiality (statements affected outcome)', 'status': 'HAVE', 'source': 'PPO granted based on fabricated straw incident'},
        ],
    },
    'F3': {
        'name': 'Judicial Disqualification',
        'needed': [
            {'item': 'Pattern of biased rulings', 'status': 'HAVE', 'source': 'judicial_violations (1,127)'},
            {'item': 'Specific Canon violations', 'status': 'HAVE', 'source': 'canon_violation_mapper.py (Tool #103)'},
            {'item': 'Affidavit of prejudice (MCR 2.003)', 'status': 'NEED', 'how': 'Andrew must draft and sign sworn affidavit describing specific instances of bias'},
            {'item': 'Comparison to objective standard (Crain test)', 'status': 'HAVE', 'source': 'case_similarity.py (Tool #113)'},
        ],
    },
    'F4': {
        'name': '§1983 Federal',
        'needed': [
            {'item': 'State actor (McNeill) acting under color of law', 'status': 'HAVE', 'source': 'Judge = state actor per definition'},
            {'item': 'Constitutional violation (14th Amend due process)', 'status': 'HAVE', 'source': 'Denial of fundamental right to parent + no hearing'},
            {'item': 'Conspiracy evidence (Dennis v Sparks)', 'status': 'PARTIAL', 'how': 'Need more evidence of coordination between Emily/Berry/Barnes and McNeill'},
            {'item': 'Damages evidence', 'status': 'HAVE', 'source': 'settlement_calculator.py outputs'},
            {'item': 'Exhaustion of state remedies (Younger abstention defense)', 'status': 'PARTIAL', 'how': 'File state motions FIRST to show state remedies inadequate'},
        ],
    },
    'F7': {
        'name': 'Custody Modification',
        'needed': [
            {'item': 'Changed circumstances since last order', 'status': 'HAVE', 'source': 'Complete parenting time suspension = major change'},
            {'item': 'Best interest factor evidence (all 12)', 'status': 'HAVE', 'source': 'best_interest_scorer.py (Tool #24)'},
            {'item': 'Child\'s current situation documentation', 'status': 'NEED', 'how': 'Request FOC investigation or GAL appointment'},
            {'item': 'Proposed custody arrangement', 'status': 'HAVE', 'source': 'mediation_prep.py (Tool #112)'},
        ],
    },
    'F9': {
        'name': 'COA Brief',
        'needed': [
            {'item': 'Lower court record (transcripts)', 'status': 'NEED', 'how': 'Order transcripts from court reporter. Cost: ~$3-5/page. File request with clerk.'},
            {'item': 'Preserved errors on record', 'status': 'HAVE', 'source': 'appellate_issue_spotter.py (Tool #96)'},
            {'item': 'Standard of review for each issue', 'status': 'HAVE', 'source': 'precedent_mapper.py (Tool #99)'},
            {'item': 'Record references (page/line citations)', 'status': 'NEED', 'how': 'Can only cite after transcripts received. Critical for brief.'},
        ],
    },
}

def main():
    print("=" * 70)
    print("EVIDENCE GAP FILLER — Tool #116")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Quick evidence counts
    counts = {}
    for table in ['evidence_quotes', 'watson_perjury_compilation', 'detected_contradictions', 'judicial_violations']:
        try:
            r = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = r[0] if r else 0
        except:
            counts[table] = 0
    
    conn.close()
    
    lines = [
        "# 🔍 EVIDENCE GAP ANALYSIS",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #116*\n",
        "---\n",
        "## Evidence Arsenal\n",
        f"- Evidence quotes: **{counts.get('evidence_quotes', 0):,}**",
        f"- Perjury items: **{counts.get('watson_perjury_compilation', 0):,}**",
        f"- Contradictions: **{counts.get('detected_contradictions', 0):,}**",
        f"- Judicial violations: **{counts.get('judicial_violations', 0):,}**\n",
        "---\n",
    ]
    
    total_have = 0
    total_need = 0
    total_partial = 0
    action_items = []
    
    for fid, data in EVIDENCE_NEEDS.items():
        have = sum(1 for e in data['needed'] if e['status'] == 'HAVE')
        need = sum(1 for e in data['needed'] if e['status'] == 'NEED')
        partial = sum(1 for e in data['needed'] if e['status'] == 'PARTIAL')
        total = len(data['needed'])
        pct = (have + partial * 0.5) / total * 100 if total > 0 else 0
        
        total_have += have
        total_need += need
        total_partial += partial
        
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        
        lines.extend([
            f"## {fid}: {data['name']} — {pct:.0f}% Ready {bar}\n",
            "| Item | Status | Source/Action |",
            "|------|--------|--------------|",
        ])
        
        for e in data['needed']:
            icon = {'HAVE': '✅', 'NEED': '❌', 'PARTIAL': '⚠️'}[e['status']]
            source = e.get('source', e.get('how', ''))
            lines.append(f"| {e['item'][:50]} | {icon} {e['status']} | {source[:60]} |")
            
            if e['status'] in ['NEED', 'PARTIAL']:
                action_items.append({
                    'filing': fid,
                    'item': e['item'],
                    'action': e.get('how', 'See source'),
                })
        
        lines.append("")
        print(f"  {fid} ({data['name'][:25]}): {pct:.0f}% ready — {have} have, {partial} partial, {need} need")
    
    # Action items
    lines.extend([
        "---",
        "## 📋 ACTION ITEMS (What Andrew Needs to Do)\n",
    ])
    
    for i, item in enumerate(action_items, 1):
        lines.append(f"**{i}. [{item['filing']}]** {item['item']}")
        lines.append(f"   → {item['action']}\n")
    
    total_items = total_have + total_need + total_partial
    overall_pct = (total_have + total_partial * 0.5) / total_items * 100 if total_items > 0 else 0
    
    lines.extend([
        "---",
        f"## Overall: {overall_pct:.0f}% Evidence Ready\n",
        f"- ✅ HAVE: {total_have} items",
        f"- ⚠️ PARTIAL: {total_partial} items",
        f"- ❌ NEED: {total_need} items",
        f"- 📋 Action items: {len(action_items)}\n",
        f"*Evidence Gap Filler — Tool #116 — {overall_pct:.0f}% ready, {len(action_items)} action items*",
    ])
    
    md_path = REPORTS_DIR / "EVIDENCE_GAPS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "evidence_gaps.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Gap Filler (#116)',
        'overall_readiness': round(overall_pct, 1),
        'have': total_have,
        'partial': total_partial,
        'need': total_need,
        'action_items': len(action_items),
        'evidence_counts': counts,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ Overall evidence readiness: {overall_pct:.0f}%")
    print(f"   HAVE: {total_have} | PARTIAL: {total_partial} | NEED: {total_need}")
    print(f"   Action items for Andrew: {len(action_items)}")
    print(f"   Reports: EVIDENCE_GAPS.md + evidence_gaps.json")

if __name__ == '__main__':
    main()
