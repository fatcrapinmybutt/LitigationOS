#!/usr/bin/env python3
"""
Witness Credibility Scorer — Multi-factor credibility assessment.

Novel LitigationOS Tool #22

Scores each witness/actor on 8 credibility dimensions:
1. Internal Consistency — Do their statements contradict each other?
2. External Corroboration — Is their testimony supported by documents?
3. Prior False Statements — Have they been caught lying?
4. Bias/Interest — What stake do they have in the outcome?
5. Demeanor Indicators — Language patterns suggesting deception
6. Opportunity to Observe — Were they present for claimed events?
7. Record of Conduct — Prior legal/ethical violations
8. Pattern of Behavior — Consistent behavior over time

Output: Credibility score 0-100 per witness, impeachment ammunition,
and recommended cross-examination strategies.
"""
import sys, os, json, sqlite3, re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

# Known witnesses/actors in the case
WITNESSES = {
    'Emily Watson': {
        'role': 'Defendant/Opposing Party',
        'relationship': 'Mother of L.D.W.',
        'bias_level': 'EXTREME',
        'interest': 'Custody retention, PPO maintenance, financial',
        'known_false': ['PPO allegations', 'Straw incident fabrication', 'Stalking claims'],
    },
    'Ronald Berry': {
        'role': 'Non-Party Witness / Emily\'s Partner',
        'relationship': 'Emily\'s boyfriend/domestic partner',
        'bias_level': 'HIGH',
        'interest': 'Protecting Emily, maintaining household control',
        'known_false': ['Claimed legal authority', 'False statements to police'],
    },
    'Jennifer Barnes': {
        'role': 'Former Attorney (WITHDREW)',
        'relationship': 'Emily\'s former attorney (P55406)',
        'bias_level': 'HIGH',
        'interest': 'Professional reputation, avoiding malpractice',
        'known_false': ['Procedural misrepresentations'],
    },
    'Hon. Jenny McNeill': {
        'role': 'Judge — 14th Circuit',
        'relationship': 'Presiding judge',
        'bias_level': 'SUBJECT OF COMPLAINT',
        'interest': 'Judicial reputation, avoiding JTC complaint',
        'known_false': [],
    },
    'Lori Watson': {
        'role': 'Non-Party Witness',
        'relationship': 'Emily\'s mother, Kent County Prosecutor\'s Office',
        'bias_level': 'HIGH',
        'interest': 'Protecting daughter, maintaining access to grandchild',
        'known_false': [],
    },
    'Pamela Rusco': {
        'role': 'Judicial Secretary',
        'relationship': 'Judge McNeill\'s secretary (NOT FOC)',
        'bias_level': 'MODERATE',
        'interest': 'Job security, loyalty to judge',
        'known_false': [],
    },
}

# Deception language indicators (linguistic analysis)
DECEPTION_INDICATORS = [
    (r'\bi don\'?t recall\b', 'memory_evasion', 3),
    (r'\bi don\'?t remember\b', 'memory_evasion', 3),
    (r'\bto the best of my\b', 'hedging', 2),
    (r'\bi believe\b', 'hedging', 1),
    (r'\bi think\b', 'hedging', 1),
    (r'\bpossibly\b', 'hedging', 1),
    (r'\bperhaps\b', 'hedging', 1),
    (r'\bnever\b', 'absolute_denial', 2),
    (r'\balways\b', 'absolute_claim', 2),
    (r'\bhonestly\b', 'truthfulness_emphasis', 3),
    (r'\bto be honest\b', 'truthfulness_emphasis', 3),
    (r'\bfrankly\b', 'truthfulness_emphasis', 2),
    (r'\bbasically\b', 'minimization', 1),
    (r'\bjust\b', 'minimization', 1),
    (r'\bsort of\b', 'vagueness', 1),
    (r'\bkind of\b', 'vagueness', 1),
]


def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def table_exists(conn, name):
    r = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r[0] > 0


def score_internal_consistency(conn, witness_name):
    """Score: How often does this witness contradict themselves?"""
    contradictions = 0
    total_statements = 0
    
    # Check detected_contradictions
    if table_exists(conn, 'detected_contradictions'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM detected_contradictions WHERE LOWER(speaker) LIKE ?",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            contradictions += row[0]
        except Exception:
            pass
    
    # Check watson_perjury_compilation
    if table_exists(conn, 'watson_perjury_compilation'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM watson_perjury_compilation WHERE LOWER(watson_member) LIKE ?",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            total_statements += row[0]
        except Exception:
            pass
    
    if total_statements == 0:
        return 50, {'contradictions': contradictions, 'statements': total_statements}
    
    ratio = contradictions / max(total_statements, 1)
    # More contradictions = lower credibility
    score = max(0, min(100, 100 - int(ratio * 200)))
    return score, {'contradictions': contradictions, 'statements': total_statements, 'ratio': round(ratio, 3)}


def score_external_corroboration(conn, witness_name):
    """Score: Is their testimony supported by documents/records?"""
    corroborated = 0
    uncorroborated = 0
    
    if table_exists(conn, 'adversary_assertions'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM adversary_assertions WHERE LOWER(speaker) LIKE ? AND rebuttal_evidence IS NOT NULL AND rebuttal_evidence != ''",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            corroborated = row[0]
            
            row2 = conn.execute(
                "SELECT COUNT(*) FROM adversary_assertions WHERE LOWER(speaker) LIKE ? AND (rebuttal_evidence IS NULL OR rebuttal_evidence = '')",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            uncorroborated = row2[0]
        except Exception:
            pass
    
    total = corroborated + uncorroborated
    if total == 0:
        return 50, {'corroborated': 0, 'uncorroborated': 0}
    
    # More rebuttal evidence = LOWER credibility (their claims are disprovable)
    rebuttal_ratio = corroborated / total
    score = max(0, min(100, 100 - int(rebuttal_ratio * 100)))
    return score, {'with_rebuttal': corroborated, 'without_rebuttal': uncorroborated, 'rebuttal_ratio': round(rebuttal_ratio, 3)}


def score_prior_false_statements(conn, witness_name):
    """Score: How many false statements are documented?"""
    false_count = 0
    
    if table_exists(conn, 'watson_perjury_compilation'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM watson_perjury_compilation WHERE LOWER(watson_member) LIKE ? AND LOWER(perjury_type) IN ('perjury', 'false_statement', 'fabrication', 'inconsistency')",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            false_count += row[0]
        except Exception:
            pass
    
    if table_exists(conn, 'adversary_assertions'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM adversary_assertions WHERE LOWER(speaker) LIKE ? AND is_false = 1",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchone()
            false_count += row[0]
        except Exception:
            pass
    
    # Each false statement drops credibility significantly
    score = max(0, 100 - (false_count * 2))
    return score, {'documented_false_statements': false_count}


def score_bias_interest(witness_info):
    """Score: How biased is this witness?"""
    bias_scores = {'EXTREME': 10, 'HIGH': 25, 'MODERATE': 50, 'LOW': 75, 'NONE': 95, 'SUBJECT OF COMPLAINT': 15}
    score = bias_scores.get(witness_info.get('bias_level', 'MODERATE'), 50)
    return score, {'bias_level': witness_info.get('bias_level'), 'interest': witness_info.get('interest')}


def score_deception_language(conn, witness_name):
    """Score: Linguistic deception indicators in their statements."""
    indicators = defaultdict(int)
    total_words = 0
    
    tables = [
        ('watson_perjury_compilation', 'watson_member', 'statement_text'),
        ('adversary_assertions', 'speaker', 'assertion_text'),
    ]
    
    for table, actor_col, text_col in tables:
        if not table_exists(conn, table):
            continue
        try:
            rows = conn.execute(
                f"SELECT {text_col} FROM {table} WHERE LOWER({actor_col}) LIKE ? LIMIT 2000",
                (f'%{witness_name.lower().split()[0]}%',)
            ).fetchall()
            for row in rows:
                text = row[0] or ''
                total_words += len(text.split())
                for pattern, category, weight in DECEPTION_INDICATORS:
                    matches = len(re.findall(pattern, text, re.IGNORECASE))
                    indicators[category] += matches * weight
        except Exception:
            pass
    
    total_indicator_score = sum(indicators.values())
    # Normalize: more deception indicators per 1000 words = lower credibility
    if total_words > 0:
        per_1000 = (total_indicator_score / total_words) * 1000
        score = max(0, min(100, 100 - int(per_1000 * 5)))
    else:
        score = 50
    
    return score, {'indicators': dict(indicators), 'total_words_analyzed': total_words}


def score_judicial_violations(conn, witness_name):
    """Score for judicial actors: documented violations."""
    if 'mcneill' not in witness_name.lower() and 'judge' not in witness_name.lower():
        return None, {}
    
    violation_count = 0
    if table_exists(conn, 'judicial_violations'):
        try:
            row = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()
            violation_count = row[0]
        except Exception:
            pass
    
    if table_exists(conn, 'actor_violations'):
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM actor_violations WHERE LOWER(COALESCE(actor,'')) LIKE '%mcneill%'"
            ).fetchone()
            violation_count = max(violation_count, row[0])
        except Exception:
            pass
    
    score = max(0, 100 - min(violation_count, 50) * 2)
    return score, {'documented_violations': violation_count}


def generate_cross_exam_strategies(witness_name, scores, details):
    """Generate recommended cross-examination strategies."""
    strategies = []
    
    # Low internal consistency → impeach with prior inconsistent statements
    if scores.get('internal_consistency', 100) < 50:
        count = details.get('internal_consistency', {}).get('contradictions', 0)
        strategies.append({
            'strategy': 'Prior Inconsistent Statements (MRE 613)',
            'approach': f'Confront with {count} documented contradictions',
            'priority': 'HIGH',
        })
    
    # Many false statements → establish pattern of dishonesty
    if scores.get('prior_false_statements', 100) < 40:
        count = details.get('prior_false_statements', {}).get('documented_false_statements', 0)
        strategies.append({
            'strategy': 'Pattern of Dishonesty (MRE 608(b))',
            'approach': f'Establish pattern using {count} documented false statements',
            'priority': 'HIGH',
        })
    
    # High bias → expose interest in outcome
    if scores.get('bias_interest', 100) < 30:
        interest = details.get('bias_interest', {}).get('interest', '')
        strategies.append({
            'strategy': 'Bias/Interest Impeachment (MRE 616)',
            'approach': f'Expose financial/personal interest: {interest}',
            'priority': 'HIGH',
        })
    
    # Deception language → highlight hedging under oath
    if scores.get('deception_language', 100) < 50:
        top_indicator = max(details.get('deception_language', {}).get('indicators', {'none': 0}).items(),
                          key=lambda x: x[1], default=('none', 0))
        strategies.append({
            'strategy': 'Linguistic Impeachment',
            'approach': f'Highlight {top_indicator[0]} patterns ({top_indicator[1]} instances)',
            'priority': 'MEDIUM',
        })
    
    # External corroboration issues
    if scores.get('external_corroboration', 100) < 40:
        strategies.append({
            'strategy': 'Lack of Corroboration',
            'approach': 'Demand documentary proof for key claims — none exists',
            'priority': 'MEDIUM',
        })
    
    # Judicial violations
    if scores.get('judicial_violations') is not None and scores['judicial_violations'] < 50:
        count = details.get('judicial_violations', {}).get('documented_violations', 0)
        strategies.append({
            'strategy': 'Judicial Misconduct Record',
            'approach': f'{count} documented violations — pattern of bias',
            'priority': 'HIGH',
        })
    
    if not strategies:
        strategies.append({
            'strategy': 'Standard Cross-Examination',
            'approach': 'Focus on specifics — dates, times, exact words',
            'priority': 'STANDARD',
        })
    
    return strategies


def main():
    print("=" * 70)
    print("WITNESS CREDIBILITY SCORER — Multi-Factor Assessment")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    conn = get_connection()
    all_results = {}
    
    for witness_name, witness_info in WITNESSES.items():
        print(f"\n{'─' * 60}")
        print(f"  {witness_name} ({witness_info['role']})")
        print(f"{'─' * 60}")
        
        scores = {}
        details = {}
        
        # 1. Internal Consistency
        s, d = score_internal_consistency(conn, witness_name)
        scores['internal_consistency'] = s
        details['internal_consistency'] = d
        
        # 2. External Corroboration
        s, d = score_external_corroboration(conn, witness_name)
        scores['external_corroboration'] = s
        details['external_corroboration'] = d
        
        # 3. Prior False Statements
        s, d = score_prior_false_statements(conn, witness_name)
        scores['prior_false_statements'] = s
        details['prior_false_statements'] = d
        
        # 4. Bias/Interest
        s, d = score_bias_interest(witness_info)
        scores['bias_interest'] = s
        details['bias_interest'] = d
        
        # 5. Deception Language
        s, d = score_deception_language(conn, witness_name)
        scores['deception_language'] = s
        details['deception_language'] = d
        
        # 6. Judicial Violations (judges only)
        s, d = score_judicial_violations(conn, witness_name)
        if s is not None:
            scores['judicial_violations'] = s
            details['judicial_violations'] = d
        
        # Calculate overall credibility
        overall = sum(scores.values()) / len(scores) if scores else 50
        
        # Grade
        if overall >= 80: grade = 'A (Highly Credible)'
        elif overall >= 65: grade = 'B (Credible)'
        elif overall >= 50: grade = 'C (Questionable)'
        elif overall >= 35: grade = 'D (Low Credibility)'
        else: grade = 'F (Not Credible)'
        
        # Display
        print(f"  OVERALL: {overall:.1f}/100 — {grade}")
        print()
        for dim, score in sorted(scores.items(), key=lambda x: x[1]):
            bar_len = score // 5
            bar = '█' * bar_len + '░' * (20 - bar_len)
            print(f"    {dim:28s} [{bar}] {score}")
        
        # Cross-exam strategies
        strategies = generate_cross_exam_strategies(witness_name, scores, details)
        print(f"\n  CROSS-EXAM STRATEGIES:")
        for strat in strategies:
            icon = '🔴' if strat['priority'] == 'HIGH' else '🟡' if strat['priority'] == 'MEDIUM' else '⚪'
            print(f"    {icon} {strat['strategy']}")
            print(f"       → {strat['approach']}")
        
        all_results[witness_name] = {
            'role': witness_info['role'],
            'overall_score': round(overall, 1),
            'grade': grade,
            'dimension_scores': scores,
            'dimension_details': details,
            'cross_exam_strategies': strategies,
        }
    
    # Summary table
    print(f"\n{'=' * 70}")
    print(f"  CREDIBILITY RANKINGS")
    print(f"{'=' * 70}")
    ranked = sorted(all_results.items(), key=lambda x: x[1]['overall_score'])
    for witness, data in ranked:
        score = data['overall_score']
        grade = data['grade'].split('(')[0].strip()
        strat_count = len(data['cross_exam_strategies'])
        print(f"  {score:5.1f} {grade}  {witness:30s}  ({strat_count} strategies)")
    
    # Save reports
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "witness_credibility.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Report saved: {report_path}")
    
    # Generate markdown
    md_path = REPORT_DIR / "WITNESS_CREDIBILITY_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Witness Credibility Assessment\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Rankings\n\n")
        f.write("| Witness | Score | Grade | Strategies |\n")
        f.write("|---------|-------|-------|------------|\n")
        for w, d in ranked:
            f.write(f"| {w} | {d['overall_score']:.1f} | {d['grade']} | {len(d['cross_exam_strategies'])} |\n")
        
        for w, d in ranked:
            f.write(f"\n---\n\n## {w}\n\n")
            f.write(f"**Role:** {d['role']}\n\n")
            f.write(f"**Overall Score:** {d['overall_score']:.1f}/100 — {d['grade']}\n\n")
            f.write("### Dimension Scores\n\n")
            f.write("| Dimension | Score |\n")
            f.write("|-----------|-------|\n")
            for dim, score in sorted(d['dimension_scores'].items(), key=lambda x: x[1]):
                f.write(f"| {dim} | {score} |\n")
            f.write("\n### Cross-Examination Strategies\n\n")
            for strat in d['cross_exam_strategies']:
                f.write(f"- **{strat['strategy']}** [{strat['priority']}]\n")
                f.write(f"  - {strat['approach']}\n")
    
    print(f"  Markdown report saved: {md_path}")
    
    conn.close()


if __name__ == '__main__':
    main()
