#!/usr/bin/env python3
"""
Tool #231 — Fraud Upon the Court Chain Builder
Constructs the complete fraud chain: initial fraud → infected orders → void ab initio.
Maps every court order back to the fraudulent foundation.

Core legal theory: Everything stems from Emily's initial fabricated filings.
MCR 2.612(C)(3) independent action for fraud on the court = NO time bar.

LitigationOS — Pigors v. Watson
"""
import sys, os, sqlite3, json, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "litigation_context.db")

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

def s(val):
    return (val or "").lower()

def gather_fraud_evidence(conn):
    """Gather all evidence of fraud upon the court."""
    evidence = {}
    
    # 1. Fabricated allegations
    evidence['fabricated_allegations'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM evidence_quotes 
            WHERE quote_text LIKE '%fabricat%' OR quote_text LIKE '%false%allegat%'
            OR quote_text LIKE '%straw%' OR quote_text LIKE '%cocaine%'
            OR quote_text LIKE '%perjur%' OR quote_text LIKE '%lied%'
            LIMIT 200""").fetchall()
        evidence['fabricated_allegations'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: fabricated_allegations query: {e}")
    
    # 2. Perjury instances
    evidence['perjury'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM evidence_quotes 
            WHERE quote_text LIKE '%sworn%' OR quote_text LIKE '%under oath%'
            OR quote_text LIKE '%perjur%' OR quote_text LIKE '%false swearing%'
            LIMIT 200""").fetchall()
        evidence['perjury'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: perjury query: {e}")
    
    # 3. Ex parte violations
    evidence['ex_parte'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM evidence_quotes 
            WHERE quote_text LIKE '%ex parte%' OR quote_text LIKE '%without notice%'
            OR quote_text LIKE '%no hearing%'
            LIMIT 200""").fetchall()
        evidence['ex_parte'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: ex_parte query: {e}")
    
    # 4. Docket events showing order chain
    evidence['docket_events'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM docket_events 
            WHERE event_description LIKE '%order%' OR event_description LIKE '%judgment%'
            OR event_description LIKE '%PPO%' OR event_description LIKE '%custody%'
            ORDER BY event_date
            LIMIT 200""").fetchall()
        evidence['docket_events'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: docket_events query: {e}")
    
    # 5. Timeline events showing fraud pattern
    evidence['timeline_fraud'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM d_drive_events 
            WHERE category IN ('FRAUD', 'PPO_ABUSE') 
            ORDER BY event_date""").fetchall()
        evidence['timeline_fraud'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: timeline query: {e}")
    
    # 6. CIP contradictions (proof of lies)
    evidence['contradictions'] = []
    try:
        rows = conn.execute("SELECT * FROM d_drive_cip LIMIT 100").fetchall()
        evidence['contradictions'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: CIP query: {e}")
    
    # 7. Judicial violations (court's role in fraud)
    evidence['judicial_violations'] = []
    try:
        rows = conn.execute("""
            SELECT * FROM judicial_violations 
            LIMIT 200""").fetchall()
        evidence['judicial_violations'] = [dict(r) for r in rows]
    except Exception as e:
        print(f"  Warning: judicial_violations query: {e}")
    
    return evidence

def build_fraud_chain(evidence):
    """Build the fraud-upon-the-court chain."""
    chain = {
        'root_fraud': {
            'description': 'Emily Watson filed PPO (2023-5907-PP) based on fabricated allegations',
            'date': 'Late 2023',
            'evidence': [
                'Oct 15, 2023: Fabricated cocaine straw allegation — no evidence, no history',
                'Filed PPO citing baseless harassment claims',
                'Used professional knowledge (Kent County caseworker) to craft false narrative'
            ],
            'legal_status': 'FRAUDULENT FOUNDATION — everything built on this is tainted'
        },
        'infected_orders': [],
        'void_analysis': [],
        'fruit_of_poisonous_tree': []
    }
    
    # Build infected order chain
    chain['infected_orders'] = [
        {
            'order': 'PPO (2023-5907-PP)',
            'infection_path': 'Direct fraud — based on fabricated allegations',
            'status': 'VOID AB INITIO',
            'authority': 'MCR 2.612(C)(1)(c) — fraud; MCR 2.612(C)(1)(d) — void judgment'
        },
        {
            'order': 'Initial custody arrangement (2024-001507-DC)',
            'infection_path': 'PPO used as evidence of "danger" to support custody restrictions',
            'status': 'TAINTED — fruit of fraudulent PPO',
            'authority': 'MCR 2.612(C)(3) — independent action for fraud on the court'
        },
        {
            'order': "Emily's August 2025 Ex Parte Order",
            'infection_path': 'Built on manufactured police report NS2505044 (Albert Watson admitted premeditation)',
            'status': 'VOID — no required findings per MCL 722.27a(3)',
            'authority': 'MCL 722.27a(3) — ex parte requires specific findings; MCR 2.612(C)(1)(d) — void'
        },
        {
            'order': 'Parenting time restrictions',
            'infection_path': 'Based on void PPO + tainted custody order + fraudulent ex parte',
            'status': 'TAINTED — fruit of poisonous tree',
            'authority': 'Wong Sun v United States, 371 US 471 (1963) — fruit of poisonous tree doctrine'
        },
        {
            'order': 'All subsequent modifications',
            'infection_path': 'Built on foundation of fraudulent initial proceedings',
            'status': 'TAINTED',
            'authority': 'MCR 2.612(C)(3) — NO time bar for fraud on the court'
        }
    ]
    
    # Fruit of poisonous tree analysis
    chain['fruit_of_poisonous_tree'] = [
        {
            'original_poison': 'Fabricated PPO allegations (Oct 2023)',
            'fruit': 'PPO issued against Andrew',
            'consequence': 'Andrew restricted from contact, portrayed as dangerous'
        },
        {
            'original_poison': 'PPO used as evidence in custody proceedings',
            'fruit': 'Custody restrictions imposed',
            'consequence': 'Andrew lost parenting time based on false "danger" narrative'
        },
        {
            'original_poison': 'Manufactured police report NS2505044 (Aug 2025)',
            'fruit': 'Ex parte custody order granting Emily full custody',
            'consequence': 'Andrew completely cut off from child'
        },
        {
            'original_poison': 'HealthWest weaponized evaluation (Sep 2025)',
            'fruit': 'Court-ordered mental health restrictions',
            'consequence': 'Andrew pathologized for asserting legal rights'
        },
        {
            'original_poison': 'All preceding fraud',
            'fruit': 'Ongoing parenting time denial',
            'consequence': 'Child alienated from father — MCL 722.23(j) factor'
        }
    ]
    
    # Void analysis
    chain['void_analysis'] = {
        'void_ab_initio': [
            'PPO (2023-5907-PP) — based on fabricated evidence',
            "Emily's Aug 2025 Ex Parte — no MCL 722.27a(3) findings + manufactured basis"
        ],
        'voidable': [
            'Custody order (2024-001507-DC) — tainted by fraudulent PPO evidence',
            'Any order relying on HealthWest evaluation (weaponized/biased)',
            'Parenting time restrictions built on void orders'
        ],
        'relief_mechanism': {
            'primary': 'MCR 2.612(C)(3) — Independent action for fraud on the court (NO TIME LIMIT)',
            'secondary': 'MCR 2.612(C)(1)(d) — Void judgment (NO TIME LIMIT)',
            'tertiary': 'MCR 2.612(C)(1)(c) — Fraud (1 year from discovery)',
            'federal': '42 USC §1983 — Due process violation (3 years SOL)'
        }
    }
    
    return chain

def calculate_evidence_strength(evidence):
    """Calculate overall evidence strength for fraud claim."""
    scores = {
        'fabrication_evidence': min(len(evidence['fabricated_allegations']) / 20, 1.0) * 25,
        'perjury_evidence': min(len(evidence['perjury']) / 10, 1.0) * 20,
        'conspiracy_evidence': 20,  # Albert Watson NS2505044 = 20 points alone
        'pattern_evidence': min(len(evidence['timeline_fraud']) / 10, 1.0) * 15,
        'contradiction_evidence': min(len(evidence['contradictions']) / 50, 1.0) * 10,
        'judicial_complicity': min(len(evidence['judicial_violations']) / 50, 1.0) * 10
    }
    total = sum(scores.values())
    return scores, total

def main():
    print("=" * 70)
    print("TOOL #231 — FRAUD UPON THE COURT CHAIN BUILDER")
    print("Pigors v. Watson | LitigationOS")
    print("=" * 70)
    
    conn = get_conn()
    
    print("\n[1/4] Gathering fraud evidence from DB...")
    evidence = gather_fraud_evidence(conn)
    for key, items in evidence.items():
        print(f"  {key}: {len(items)} items")
    total_items = sum(len(v) for v in evidence.values())
    print(f"  TOTAL: {total_items} evidence items")
    
    print("\n[2/4] Building fraud chain...")
    chain = build_fraud_chain(evidence)
    print(f"  Infected orders: {len(chain['infected_orders'])}")
    print(f"  Fruit of poisonous tree: {len(chain['fruit_of_poisonous_tree'])}")
    print(f"  Void orders: {len(chain['void_analysis']['void_ab_initio'])}")
    print(f"  Voidable orders: {len(chain['void_analysis']['voidable'])}")
    
    print("\n[3/4] Calculating evidence strength...")
    scores, total_score = calculate_evidence_strength(evidence)
    for component, score in scores.items():
        print(f"  {component}: {score:.1f}/{'25' if 'fabric' in component else '20' if 'perjury' in component or 'conspiracy' in component else '15' if 'pattern' in component else '10'}")
    print(f"  OVERALL FRAUD SCORE: {total_score:.1f}/100")
    
    print("\n[4/4] Generating reports...")
    
    # Build MD
    report = []
    report.append("# Fraud Upon the Court — Complete Chain Analysis")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"Case: Pigors v. Watson | 14th Circuit Court")
    report.append(f"**Overall Fraud Evidence Score: {total_score:.1f}/100**\n")
    
    report.append("## THE FRAUD CHAIN")
    report.append("```")
    report.append("Fabricated PPO allegations (Oct 2023)")
    report.append("  └─→ PPO issued (2023-5907-PP) [VOID AB INITIO]")
    report.append("      └─→ PPO used as evidence in custody case")
    report.append("          └─→ Custody restrictions (2024-001507-DC) [TAINTED]")
    report.append("              └─→ Manufactured police report NS2505044 (Aug 2025)")
    report.append("                  └─→ Ex parte custody order [VOID]")
    report.append("                      └─→ Weaponized HealthWest evaluation")
    report.append("                          └─→ Total parental alienation [ONGOING]")
    report.append("```\n")
    
    report.append("## ROOT FRAUD")
    rf = chain['root_fraud']
    report.append(f"**{rf['description']}**")
    report.append(f"Date: {rf['date']}")
    for e in rf['evidence']:
        report.append(f"- {e}")
    report.append(f"\n**{rf['legal_status']}**\n")
    
    report.append("## INFECTED ORDERS")
    for io in chain['infected_orders']:
        report.append(f"\n### {io['order']}")
        report.append(f"- **Infection path:** {io['infection_path']}")
        report.append(f"- **Status:** {io['status']}")
        report.append(f"- **Authority:** {io['authority']}")
    
    report.append("\n## FRUIT OF THE POISONOUS TREE")
    for f in chain['fruit_of_poisonous_tree']:
        report.append(f"\n### {f['original_poison']}")
        report.append(f"→ **Fruit:** {f['fruit']}")
        report.append(f"→ **Consequence:** {f['consequence']}")
    
    report.append("\n## VOID vs. VOIDABLE ANALYSIS")
    report.append("\n### Void Ab Initio (NO TIME LIMIT to challenge)")
    for v in chain['void_analysis']['void_ab_initio']:
        report.append(f"- {v}")
    report.append("\n### Voidable (Require MCR 2.612 motion)")
    for v in chain['void_analysis']['voidable']:
        report.append(f"- {v}")
    
    report.append("\n## RELIEF MECHANISMS")
    for label, mechanism in chain['void_analysis']['relief_mechanism'].items():
        report.append(f"- **{label.upper()}:** {mechanism}")
    
    report.append("\n## EVIDENCE STRENGTH SCORING")
    report.append("| Component | Score | Max |")
    report.append("|-----------|-------|-----|")
    for component, score in scores.items():
        max_val = 25 if 'fabric' in component else 20 if 'perjury' in component or 'conspiracy' in component else 15 if 'pattern' in component else 10
        bar = "█" * int(score / max_val * 10)
        report.append(f"| {component} | {score:.1f} | {max_val} | {bar} |")
    report.append(f"| **TOTAL** | **{total_score:.1f}** | **100** |")
    
    report.append(f"\n## TOTAL EVIDENCE ITEMS: {total_items}")
    report.append("| Category | Count |")
    report.append("|----------|-------|")
    for key, items in evidence.items():
        report.append(f"| {key} | {len(items)} |")
    
    # Write
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    md_path = os.path.join(report_dir, "tool_231_fraud_chain_report.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"  MD:   {md_path}")
    
    json_data = {
        'tool': 231,
        'name': 'Fraud Upon the Court Chain Builder',
        'generated': datetime.now().isoformat(),
        'total_evidence_items': total_items,
        'fraud_score': total_score,
        'score_breakdown': scores,
        'chain': chain,
        'evidence_counts': {k: len(v) for k, v in evidence.items()}
    }
    
    json_path = os.path.join(report_dir, "tool_231_fraud_chain_report.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"  JSON: {json_path}")
    
    print(f"\n{'='*70}")
    print(f"FRAUD SCORE: {total_score:.1f}/100")
    print(f"EVIDENCE ITEMS: {total_items}")
    print(f"VOID ORDERS: {len(chain['void_analysis']['void_ab_initio'])}")
    print(f"TAINTED ORDERS: {len(chain['void_analysis']['voidable'])}")
    print(f"KEY: MCR 2.612(C)(3) — NO TIME LIMIT for fraud on the court")
    print(f"{'='*70}")
    
    conn.close()

if __name__ == '__main__':
    main()
