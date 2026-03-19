#!/usr/bin/env python3
"""
OMEGA Predictive Outcome Model
Calculates per-action success probabilities, Monte Carlo simulations,
decision trees, and expected value rankings from litigation data.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sqlite3
import random
import statistics
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', '..', 'litigation_context.db')

random.seed(42)


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────
# 1. Load data from all OMEGA tables
# ─────────────────────────────────────────────
def load_data(conn):
    scores = {r['action_id']: dict(r)
              for r in conn.execute('SELECT * FROM omega_scores ORDER BY total_score DESC')}

    court = {}
    for r in conn.execute('SELECT * FROM omega_court_assessment'):
        court[r['id']] = dict(r)

    readiness = {}
    for r in conn.execute('SELECT * FROM omega_filing_readiness'):
        readiness[r['id']] = dict(r)

    evidence_patterns = [dict(r) for r in conn.execute('SELECT * FROM omega_evidence_patterns')]

    claims = [dict(r) for r in conn.execute('SELECT * FROM omega_claim_evidence_map')]

    return scores, court, readiness, evidence_patterns, claims


# ─────────────────────────────────────────────
# 2. Build unified action list with cross-table joins
# ─────────────────────────────────────────────
def build_action_map(scores, court, readiness, claims):
    """Map court_assessment rows to omega_scores and filing_readiness via fuzzy name matching."""

    # Build keyword-to-score-id lookup
    score_lookup = {}
    for aid, s in scores.items():
        score_lookup[aid] = s
        # Also index by lowercase keywords from the name
        score_lookup[s['name'].lower()] = s

    def find_score(action_name, forum):
        """Best-effort match court_assessment action_name → omega_scores."""
        alow = action_name.lower()
        # Direct keyword matching
        for aid, s in scores.items():
            slow = s['name'].lower()
            # Check overlap of significant words
            a_words = set(alow.replace('—', ' ').replace('-', ' ').split())
            s_words = set(slow.replace('—', ' ').replace('-', ' ').split())
            overlap = a_words & s_words - {'for', 'the', 'of', 'to', 'a', 'an', 'motion', 'complaint'}
            if len(overlap) >= 2:
                return s
            # Forum + partial match
            if s['forum'] == forum and (
                any(w in slow for w in a_words if len(w) > 4)
            ):
                return s
        return None

    def find_readiness(action_name, forum):
        for rid, r in readiness.items():
            if r['action_name'] == action_name:
                return r
            rlow = r['action_name'].lower()
            alow = action_name.lower()
            if r['forum'] == forum:
                a_words = set(alow.replace('—', ' ').replace('-', ' ').split())
                r_words = set(rlow.replace('—', ' ').replace('-', ' ').split())
                overlap = a_words & r_words - {'for', 'the', 'of', 'to', 'a', 'an', 'motion'}
                if len(overlap) >= 2:
                    return r
        return None

    # Classify claims by relevance to action categories
    classification_to_forum = {
        'judicial_misconduct': ['JTC', 'MSC', '14TH'],
        'ex_parte_violation': ['14TH', 'MSC'],
        'ex_parte_reference': ['14TH', 'MSC'],
        'ex_parte_evidence': ['14TH', 'MSC'],
        'parenting_time_restriction': ['14TH'],
        'parenting_time_denial': ['14TH'],
        'parenting_time_evidence': ['14TH'],
        'benchbook_violation': ['JTC', 'MSC'],
        'procedural_due_process': ['USDC', 'MSC', 'COA'],
        'substantive_due_process': ['USDC', 'MSC'],
        'equal_protection': ['USDC'],
        'canon_1_violation': ['JTC'],
        'canon_2_violation': ['JTC'],
        'canon_3_violation': ['JTC'],
        'canon_3B4_violation': ['JTC'],
        'canon_3B5_violation': ['JTC'],
        'judicial_bias': ['JTC', '14TH', 'MSC'],
        'judicial_disqualification': ['14TH'],
        'judicial_sanction_abuse': ['JTC', 'MSC'],
        'record_contradiction': ['COA', 'MSC'],
        'denial_evidence': ['COA', '14TH'],
        'violation_evidence': ['JTC', 'MSC'],
        'liberty_interest': ['USDC', 'MSC'],
        'ppo_due_process': ['14TH', 'COA'],
        'impeachment_credibility': ['14TH', 'COA'],
        'contempt_or_violation': ['14TH'],
        'custody_evidence': ['14TH', 'COA'],
    }

    # Pre-compute per-forum evidence completeness and violation counts
    forum_evidence = {}
    forum_violations = {}
    for cl in claims:
        cats = classification_to_forum.get(cl['classification'], [])
        for f in cats:
            forum_evidence.setdefault(f, []).append(cl['completeness_score'] / 100.0)
        if 'violation' in cl['classification']:
            for f in cats:
                forum_violations.setdefault(f, []).append(cl['matching_evidence_count'])

    # Also compute global averages as fallback
    all_completeness = [cl['completeness_score'] / 100.0 for cl in claims]
    global_avg_completeness = statistics.mean(all_completeness) if all_completeness else 0.5
    all_violations = [cl['matching_evidence_count'] for cl in claims
                      if 'violation' in cl['classification']]
    max_violations = max(all_violations) if all_violations else 1

    actions = []
    for cid, ca in court.items():
        s = find_score(ca['action_name'], ca['forum'])
        r = find_readiness(ca['action_name'], ca['forum'])

        omega_score = s['total_score'] if s else ca['enhanced_omega']
        readiness_pct = r['readiness_pct'] if r else ca.get('readiness_pct', 80)
        evidence_depth = ca.get('evidence_depth', 80) / 100.0
        violation_support = ca.get('violation_support', 50) / 100.0

        # Per-forum evidence completeness
        f = ca['forum']
        if f in forum_evidence and forum_evidence[f]:
            evidence_completeness = statistics.mean(forum_evidence[f])
        else:
            evidence_completeness = global_avg_completeness

        # Violation factor: normalized count of violation evidence for this forum
        if f in forum_violations and forum_violations[f]:
            viol_count = sum(forum_violations[f])
            violation_factor = min(viol_count / max_violations, 1.0)
        else:
            violation_factor = violation_support

        actions.append({
            'court_id': cid,
            'action_name': ca['action_name'],
            'forum': ca['forum'],
            'tier': ca['tier'],
            'omega_score': omega_score,
            'readiness_pct': readiness_pct,
            'evidence_depth': evidence_depth,
            'violation_support': violation_support,
            'evidence_completeness': evidence_completeness,
            'violation_factor': violation_factor,
            'risk_score': ca.get('risk_score', 3.0),
            'score_row': s,
            'readiness_row': r,
            'sequence_order': r['sequence_order'] if r else 99,
        })

    return actions


# ─────────────────────────────────────────────
# 3. Per-action success probability
# ─────────────────────────────────────────────
def calculate_base_probability(action):
    base = (action['omega_score'] / 100.0) * 0.40
    evidence = action['evidence_completeness'] * 0.25
    violations = action['violation_factor'] * 0.20
    filing = (action['readiness_pct'] / 100.0) * 0.15
    composite = base + evidence + violations + filing
    return min(max(composite, 0.0), 1.0)


# ─────────────────────────────────────────────
# 4. Monte Carlo simulation (1000 iterations)
# ─────────────────────────────────────────────
def monte_carlo(action, base_prob, n=1000):
    results = []
    base_evidence = action['evidence_completeness']

    for _ in range(n):
        # Vary evidence admissibility
        ev = max(0.0, min(1.0, random.gauss(base_evidence, 0.15)))
        # Judge behavior: neutral mean, uncertain
        judge = max(0.0, min(1.0, random.gauss(0.5, 0.2)))
        # Defense strength
        defense = max(0.0, min(1.0, random.gauss(0.3, 0.1)))

        # Outcome score: weighted combination
        outcome = (
            base_prob * 0.35 +
            ev * 0.25 +
            judge * 0.25 +
            (1.0 - defense) * 0.15
        )
        results.append(min(max(outcome, 0.0), 1.0))

    results.sort()
    return {
        'mean': statistics.mean(results),
        'median': statistics.median(results),
        'std': statistics.stdev(results),
        'p5': results[int(n * 0.05)],
        'p95': results[int(n * 0.95) - 1],
        'min': results[0],
        'max': results[-1],
    }


# ─────────────────────────────────────────────
# 5. Decision tree with cascading effects
# ─────────────────────────────────────────────
CASCADE_RULES = {
    'Formal Complaint (Multi-Count)': {
        'win': {'desc': 'Judge disqualified → new judge → improved outcomes on 14TH motions',
                'boost_forums': ['14TH'], 'boost_amount': 0.15},
        'partial': {'desc': 'Investigation opened → pressure on judge → moderate improvement',
                    'boost_forums': ['14TH'], 'boost_amount': 0.07},
        'lose': {'desc': 'Complaint dismissed → no cascade', 'boost_forums': [], 'boost_amount': 0.0},
    },
    'Motion for Disqualification': {
        'win': {'desc': 'Judge removed → new judge assigned → fresh evaluation of all motions',
                'boost_forums': ['14TH'], 'boost_amount': 0.20},
        'partial': {'desc': 'Recusal under consideration → delays but possible reassignment',
                    'boost_forums': ['14TH'], 'boost_amount': 0.05},
        'lose': {'desc': 'Denied → potential appellate issue', 'boost_forums': ['COA'], 'boost_amount': 0.03},
    },
    'Emergency Application for Leave to Appeal': {
        'win': {'desc': 'MSC accepts → case remanded with instructions → strong precedent',
                'boost_forums': ['14TH', 'COA'], 'boost_amount': 0.18},
        'partial': {'desc': 'Leave granted, limited review → moderate improvement',
                    'boost_forums': ['COA'], 'boost_amount': 0.08},
        'lose': {'desc': 'Denied → COA appeal continues as primary path',
                 'boost_forums': [], 'boost_amount': 0.0},
    },
    'Emergency Motion to Restore Parenting Time': {
        'win': {'desc': 'Parenting time restored → direct relief, strengthens federal claims',
                'boost_forums': ['USDC'], 'boost_amount': 0.10},
        'partial': {'desc': 'Limited/supervised time → partial relief',
                    'boost_forums': [], 'boost_amount': 0.0},
        'lose': {'desc': 'Denied → strengthens irreparable harm showing for appellate/federal',
                 'boost_forums': ['COA', 'MSC', 'USDC'], 'boost_amount': 0.05},
    },
    '42 USC §1983 — Civil Rights (Multi-Count)': {
        'win': {'desc': 'Federal relief → damages + injunction → systemic change',
                'boost_forums': ['14TH'], 'boost_amount': 0.12},
        'partial': {'desc': 'Some counts survive → partial relief + discovery pressure',
                    'boost_forums': ['14TH'], 'boost_amount': 0.05},
        'lose': {'desc': 'Dismissed (immunity/abstention) → limited impact',
                 'boost_forums': [], 'boost_amount': 0.0},
    },
}


def build_decision_tree(actions, probabilities):
    """For top 5 actions, map win/partial/lose outcomes with cascading effects."""
    # Sort by composite probability descending
    ranked = sorted(zip(actions, probabilities),
                    key=lambda x: x[1]['composite'], reverse=True)
    top5 = ranked[:5]

    trees = []
    for action, prob in top5:
        name = action['action_name']
        cp = prob['composite']

        # Find matching cascade rule
        cascade = None
        for rule_key, rule_val in CASCADE_RULES.items():
            if rule_key.lower() in name.lower() or name.lower() in rule_key.lower():
                cascade = rule_val
                break

        # Default cascade if none matched
        if cascade is None:
            cascade = {
                'win': {'desc': 'Successful → positive momentum', 'boost_forums': [], 'boost_amount': 0.05},
                'partial': {'desc': 'Partial success → moderate benefit', 'boost_forums': [], 'boost_amount': 0.02},
                'lose': {'desc': 'Denied → limited impact', 'boost_forums': [], 'boost_amount': 0.0},
            }

        # Outcome probabilities based on composite
        win_prob = cp * 0.6
        partial_prob = cp * 0.3
        lose_prob = 1.0 - win_prob - partial_prob

        tree = {
            'action_name': name,
            'forum': action['forum'],
            'composite_probability': round(cp, 4),
            'outcomes': {
                'win':     {'probability': round(win_prob, 4), **cascade['win']},
                'partial': {'probability': round(partial_prob, 4), **cascade['partial']},
                'lose':    {'probability': round(lose_prob, 4), **cascade['lose']},
            }
        }
        trees.append(tree)

    return trees


# ─────────────────────────────────────────────
# 6. Expected value ranking
# ─────────────────────────────────────────────
def calculate_expected_value(actions, probabilities):
    """EV = probability × impact_score. Risk-adjusted = EV / risk_score."""
    rankings = []
    for action, prob in zip(actions, probabilities):
        impact = action['omega_score'] / 10.0  # 0-10 scale
        ev = prob['composite'] * impact
        risk = action['risk_score'] if action['risk_score'] > 0 else 1.0
        risk_adjusted = ev / risk

        rankings.append({
            'action_name': action['action_name'],
            'forum': action['forum'],
            'tier': action['tier'],
            'probability': round(prob['composite'], 4),
            'impact': round(impact, 2),
            'expected_value': round(ev, 4),
            'risk_score': round(risk, 2),
            'risk_adjusted_rank': round(risk_adjusted, 4),
            'mc_mean': round(prob['mc']['mean'], 4),
            'mc_median': round(prob['mc']['median'], 4),
            'mc_std': round(prob['mc']['std'], 4),
            'mc_p5': round(prob['mc']['p5'], 4),
            'mc_p95': round(prob['mc']['p95'], 4),
            'confidence_interval': f"{prob['mc']['p5']:.1%} – {prob['mc']['p95']:.1%}",
            'sequence_order': action['sequence_order'],
        })

    rankings.sort(key=lambda x: x['risk_adjusted_rank'], reverse=True)
    for i, r in enumerate(rankings, 1):
        r['rank'] = i

    return rankings


# ─────────────────────────────────────────────
# 7. Save to database
# ─────────────────────────────────────────────
def save_predictions(conn, rankings, decision_trees):
    conn.execute('DROP TABLE IF EXISTS omega_predictions')
    conn.execute('''
        CREATE TABLE omega_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            action_name TEXT,
            forum TEXT,
            tier TEXT,
            probability REAL,
            impact REAL,
            expected_value REAL,
            risk_score REAL,
            risk_adjusted_rank REAL,
            mc_mean REAL,
            mc_median REAL,
            mc_std REAL,
            mc_p5 REAL,
            mc_p95 REAL,
            confidence_interval TEXT,
            decision_tree_json TEXT,
            sequence_order INTEGER,
            predicted_at TEXT
        )
    ''')

    ts = datetime.now().isoformat()
    tree_map = {t['action_name']: t for t in decision_trees}

    for r in rankings:
        tree_json = json.dumps(tree_map.get(r['action_name']), indent=2) if r['action_name'] in tree_map else None
        conn.execute('''
            INSERT INTO omega_predictions
            (rank, action_name, forum, tier, probability, impact, expected_value,
             risk_score, risk_adjusted_rank, mc_mean, mc_median, mc_std,
             mc_p5, mc_p95, confidence_interval, decision_tree_json,
             sequence_order, predicted_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (r['rank'], r['action_name'], r['forum'], r['tier'],
              r['probability'], r['impact'], r['expected_value'],
              r['risk_score'], r['risk_adjusted_rank'],
              r['mc_mean'], r['mc_median'], r['mc_std'],
              r['mc_p5'], r['mc_p95'], r['confidence_interval'],
              tree_json, r['sequence_order'], ts))

    conn.commit()


# ─────────────────────────────────────────────
# 8. Dashboard output
# ─────────────────────────────────────────────
def print_dashboard(rankings, decision_trees):
    W = 100
    print('=' * W)
    print('  OMEGA PREDICTIVE OUTCOME MODEL'.center(W))
    print(f'  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'.center(W))
    print('=' * W)

    # ── Probability & Confidence Intervals ──
    print('\n  PREDICTED SUCCESS PROBABILITIES & CONFIDENCE INTERVALS')
    print('  ' + '-' * (W - 4))
    print(f'  {"Rk":<4}{"Action":<46}{"Forum":<6}{"Prob":>7}{"95% CI":>18}{"EV":>7}{"Risk-Adj":>10}')
    print('  ' + '-' * (W - 4))

    for r in rankings:
        name = r['action_name'][:44]
        print(f'  {r["rank"]:<4}{name:<46}{r["forum"]:<6}'
              f'{r["probability"]:>6.1%} {r["confidence_interval"]:>17}'
              f'{r["expected_value"]:>7.2f}{r["risk_adjusted_rank"]:>10.3f}')

    # ── Monte Carlo Summary ──
    print(f'\n  MONTE CARLO SIMULATION RESULTS (1,000 iterations each)')
    print('  ' + '-' * (W - 4))
    print(f'  {"Action":<46}{"Mean":>7}{"Median":>8}{"StdDev":>8}{"P5":>7}{"P95":>7}{"Spread":>8}')
    print('  ' + '-' * (W - 4))

    for r in rankings:
        name = r['action_name'][:44]
        spread = r['mc_p95'] - r['mc_p5']
        print(f'  {name:<46}{r["mc_mean"]:>6.1%}{r["mc_median"]:>7.1%}'
              f'{r["mc_std"]:>8.3f}{r["mc_p5"]:>6.1%}{r["mc_p95"]:>6.1%}'
              f'{spread:>8.3f}')

    # ── Decision Trees ──
    print(f'\n  DECISION TREES — TOP 5 ACTIONS (Cascading Effects)')
    print('  ' + '-' * (W - 4))

    for tree in decision_trees:
        print(f'\n  [{tree["forum"]}] {tree["action_name"]}  '
              f'(Composite: {tree["composite_probability"]:.1%})')
        for outcome, details in tree['outcomes'].items():
            tag = {'win': 'WIN    ', 'partial': 'PARTIAL', 'lose': 'LOSE   '}[outcome]
            bar_len = int(details['probability'] * 30)
            bar = '\u2588' * bar_len + '\u2591' * (30 - bar_len)
            print(f'    {tag} [{bar}] {details["probability"]:>6.1%}')
            desc = details['desc'][:70]
            boost = details.get('boost_forums', [])
            amt = details.get('boost_amount', 0)
            print(f'            {desc}')
            if boost and amt > 0:
                print(f'            Cascade: +{amt:.0%} to {", ".join(boost)} actions')

    # ── Expected Value Rankings ──
    print(f'\n  RISK-ADJUSTED EXPECTED VALUE RANKINGS')
    print('  ' + '-' * (W - 4))
    print(f'  {"Rk":<4}{"Action":<40}{"Forum":<6}{"Tier":<10}'
          f'{"Prob":>6}{"Impact":>7}{"EV":>7}{"RiskAdj":>8}')
    print('  ' + '-' * (W - 4))

    for r in rankings:
        name = r['action_name'][:38]
        print(f'  {r["rank"]:<4}{name:<40}{r["forum"]:<6}{r["tier"]:<10}'
              f'{r["probability"]:>5.0%}{r["impact"]:>7.1f}'
              f'{r["expected_value"]:>7.2f}{r["risk_adjusted_rank"]:>8.3f}')

    # ── Summary stats ──
    avg_prob = statistics.mean(r['probability'] for r in rankings)
    avg_ev = statistics.mean(r['expected_value'] for r in rankings)
    top_action = rankings[0]
    print(f'\n  SUMMARY')
    print('  ' + '-' * (W - 4))
    print(f'  Actions analyzed:     {len(rankings)}')
    print(f'  Average probability:  {avg_prob:.1%}')
    print(f'  Average expected val: {avg_ev:.2f}')
    print(f'  Top-ranked action:    [{top_action["forum"]}] {top_action["action_name"]}')
    print(f'  Top risk-adj score:   {top_action["risk_adjusted_rank"]:.3f}')
    print(f'  Results saved to:     omega_predictions table ({len(rankings)} rows)')
    print('=' * W)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    conn = connect_db()

    # Load all data
    scores, court, readiness, evidence_patterns, claims = load_data(conn)

    # Build unified action map
    actions = build_action_map(scores, court, readiness, claims)

    # Calculate probabilities & run Monte Carlo for each action
    probabilities = []
    for action in actions:
        composite = calculate_base_probability(action)
        mc = monte_carlo(action, composite)
        probabilities.append({'composite': composite, 'mc': mc})

    # Decision trees for top 5
    decision_trees = build_decision_tree(actions, probabilities)

    # Expected value ranking
    rankings = calculate_expected_value(actions, probabilities)

    # Save to DB
    save_predictions(conn, rankings, decision_trees)

    # Print dashboard
    print_dashboard(rankings, decision_trees)

    conn.close()


if __name__ == '__main__':
    main()
