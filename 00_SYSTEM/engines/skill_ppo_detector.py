#!/usr/bin/env python3
"""
skill_ppo_detector.py -- PPO Weaponization Pattern Detector

Scans evidence_quotes for PPO-related entries, detects false allegations,
timing manipulation, retaliatory PPO use. Scores severity 1-10.
"""
import sys, sqlite3, json, re
from datetime import datetime, date
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

DB = str(Path(__file__).resolve().parents[2] / "litigation_context.db")

def _connect():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

# -- PPO weaponization indicators ------------------------------------------

PPO_KEYWORDS = [
    'PPO', 'personal protection order', 'protection order',
    'domestic violence', 'stalking', 'harassment',
    'ex parte PPO', 'emergency PPO', 'restraining order',
]

WEAPONIZATION_INDICATORS = {
    'false_allegations': {
        'keywords': ['false', 'fabricat', 'lie', 'untrue', 'no evidence', 'recanted', 'contradict'],
        'weight': 3,
    },
    'timing_manipulation': {
        'keywords': ['before hearing', 'before custody', 'during divorce', 'retaliatory',
                     'after filing', 'same day', 'strategic'],
        'weight': 2,
    },
    'retaliatory_use': {
        'keywords': ['retaliation', 'retaliatory', 'in response to', 'after complaint',
                     'after motion', 'punish', 'weapon'],
        'weight': 3,
    },
    'custody_leverage': {
        'keywords': ['custody', 'parenting time', 'visitation', 'denied access',
                     'keep children', 'separate from children'],
        'weight': 2,
    },
    'procedural_abuse': {
        'keywords': ['no notice', 'ex parte', 'without hearing', 'denied opportunity',
                     'due process', 'no evidence presented'],
        'weight': 2,
    },
}


def scan_for_patterns() -> dict:
    """Scan evidence_quotes and related tables for PPO weaponization patterns."""
    conn = _connect()
    ppo_evidence = []

    # FTS search for PPO-related evidence
    for kw in PPO_KEYWORDS:
        try:
            rows = conn.execute(
                "SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ? "
                "ORDER BY rank LIMIT 20",
                (kw,)
            ).fetchall()
            ppo_evidence.extend([dict(r) for r in rows])
        except Exception:
            pass

    # Also search extracted_harms
    for kw in ['PPO', 'protection order', 'restraining']:
        try:
            rows = conn.execute(
                "SELECT * FROM extracted_harms_fts WHERE extracted_harms_fts MATCH ? "
                "ORDER BY rank LIMIT 10",
                (kw,)
            ).fetchall()
            ppo_evidence.extend([dict(r) for r in rows])
        except Exception:
            pass

    # Deduplicate by content hash
    seen = set()
    unique = []
    for e in ppo_evidence:
        key = str(e)[:200]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    ppo_evidence = unique

    conn.close()

    return {
        'total_ppo_evidence': len(ppo_evidence),
        'evidence': ppo_evidence[:50],
    }


def score_weaponization(evidence_list: list = None) -> dict:
    """Score each piece of PPO evidence for weaponization indicators."""
    if evidence_list is None:
        scan = scan_for_patterns()
        evidence_list = scan.get('evidence', [])

    scored = []
    for e in evidence_list:
        text = json.dumps(e, default=str).lower()
        score = 0
        matched_indicators = []

        for indicator_name, cfg in WEAPONIZATION_INDICATORS.items():
            for kw in cfg['keywords']:
                if kw.lower() in text:
                    score += cfg['weight']
                    matched_indicators.append(indicator_name)
                    break  # one match per indicator category

        # Normalize to 1-10 scale
        normalized = min(10, max(1, score))

        scored.append({
            'evidence_preview': str(e)[:300],
            'raw_score': score,
            'severity': normalized,
            'indicators_matched': list(set(matched_indicators)),
            'severity_label': (
                'CRITICAL' if normalized >= 8 else
                'HIGH' if normalized >= 6 else
                'MEDIUM' if normalized >= 4 else 'LOW'
            ),
        })

    scored.sort(key=lambda x: x['severity'], reverse=True)

    return {
        'total_scored': len(scored),
        'critical_count': len([s for s in scored if s['severity'] >= 8]),
        'high_count': len([s for s in scored if 6 <= s['severity'] < 8]),
        'medium_count': len([s for s in scored if 4 <= s['severity'] < 6]),
        'low_count': len([s for s in scored if s['severity'] < 4]),
        'scored_evidence': scored[:30],
    }


def generate_report() -> dict:
    """Generate comprehensive PPO weaponization report."""
    scan = scan_for_patterns()
    scores = score_weaponization(scan.get('evidence', []))

    summary = {
        'report_date': datetime.now().isoformat(),
        'title': 'PPO Weaponization Analysis Report',
        'total_ppo_evidence': scan['total_ppo_evidence'],
        'scoring_summary': {
            'critical': scores['critical_count'],
            'high': scores['high_count'],
            'medium': scores['medium_count'],
            'low': scores['low_count'],
        },
        'top_findings': scores['scored_evidence'][:10],
        'indicators_used': list(WEAPONIZATION_INDICATORS.keys()),
        'recommendation': (
            'STRONG PATTERN DETECTED -- PPO weaponization evidence sufficient for '
            'abuse-of-process and due-process claims'
            if scores['critical_count'] >= 2
            else 'Pattern indicators present -- further evidence gathering recommended'
        ),
        'legal_authority': [
            'MCL 600.2950 -- Personal Protection Orders',
            'MCL 600.2950a -- PPO against stalking',
            'US Const. Amend. XIV -- Due Process',
            'Kampf v Kampf, 237 Mich App 377 (1999) -- PPO standards',
        ],
    }
    return summary


# -- CLI -------------------------------------------------------------------

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='PPO Weaponization Pattern Detector')
    parser.add_argument('--action', default='report',
                        choices=['scan', 'score', 'report'])
    args = parser.parse_args()

    if args.action == 'scan':
        result = scan_for_patterns()
    elif args.action == 'score':
        result = score_weaponization()
    else:
        result = generate_report()

    print(json.dumps(result, indent=2, default=str))
