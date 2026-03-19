#!/usr/bin/env python3
"""Brief Quality Engine - Legal writing quality scorer and analyzer.

Analyzes briefs for readability, citation density, argument structure,
persuasion balance, passive voice, and sentence length distribution.
Produces a comprehensive quality scorecard.

Usage:
    python brief_quality_engine.py --file path/to/brief.md
    python brief_quality_engine.py --file path/to/brief.md --benchmark --output md
    python brief_quality_engine.py --file path/to/brief.md --output json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import math
import os
import re
import sqlite3
import statistics
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

# Benchmark targets for appellate legal writing
BENCHMARKS = {
    'readability_grade': {'target': 14.0, 'min': 12.0, 'max': 16.0, 'weight': 15},
    'citation_density': {'target': 8.0, 'min': 4.0, 'max': 15.0, 'weight': 15},
    'passive_voice_pct': {'target': 15.0, 'min': 0.0, 'max': 20.0, 'weight': 10},
    'avg_sentence_length': {'target': 22.0, 'min': 15.0, 'max': 30.0, 'weight': 10},
    'argument_structure': {'target': 80.0, 'min': 50.0, 'max': 100.0, 'weight': 20},
    'persuasion_balance': {'target': 80.0, 'min': 50.0, 'max': 100.0, 'weight': 15},
    'record_citations': {'target': 5.0, 'min': 1.0, 'max': 20.0, 'weight': 10},
    'section_organization': {'target': 80.0, 'min': 50.0, 'max': 100.0, 'weight': 5},
}

# Patterns for analysis
CITATION_PATTERNS = [
    re.compile(r'\d+\s+(?:Mich(?:\s*App)?|NW2d|NW\.2d|F\.?\s*(?:2d|3d|4th)|S\.?\s*Ct\.?|U\.S\.)\s+\d+', re.IGNORECASE),
    re.compile(r'MCL\s+\d+\.\d+', re.IGNORECASE),
    re.compile(r'MCR\s+\d+\.\d+', re.IGNORECASE),
    re.compile(r'USC?\s+(?:Sec(?:tion)?\.?\s*)?\d+', re.IGNORECASE),
    re.compile(r'(?:Id\.|Ibid\.)', re.IGNORECASE),
    re.compile(r'\d+\s+(?:F\s*Supp|F\.?\s*Supp)\s*(?:2d|3d)?\s+\d+', re.IGNORECASE),
]

IRAC_INDICATORS = {
    'issue': re.compile(
        r'(?:the\s+issue\s+is|whether|the\s+question\s+(?:presented|is)|'
        r'this\s+(?:case|matter)\s+(?:presents|raises|involves))',
        re.IGNORECASE
    ),
    'rule': re.compile(
        r'(?:under\s+(?:Michigan|federal)\s+law|the\s+(?:applicable\s+)?(?:rule|standard|law)\s+(?:is|provides|requires)|'
        r'(?:MCL|MCR|USC)\s+\d+|(?:pursuant|according)\s+to)',
        re.IGNORECASE
    ),
    'application': re.compile(
        r'(?:here,?\s+(?:the|plaintiff|defendant)|in\s+(?:this|the\s+(?:present|instant))\s+case|'
        r'applying\s+(?:this|the)\s+(?:standard|rule|test)|the\s+(?:evidence|record)\s+(?:shows|demonstrates))',
        re.IGNORECASE
    ),
    'conclusion': re.compile(
        r'(?:therefore|accordingly|thus|for\s+these\s+reasons|'
        r'(?:this\s+Court|the\s+Court)\s+should|(?:it\s+is\s+)?(?:clear|evident)\s+that)',
        re.IGNORECASE
    ),
}

PERSUASION_CATEGORIES = {
    'factual': re.compile(
        r'(?:the\s+(?:record|evidence|facts?)\s+(?:show|demonstrate|establish|reveal)|'
        r'(?:undisputed|uncontroverted)\s+(?:evidence|facts?)|testimony\s+(?:shows|establishes))',
        re.IGNORECASE
    ),
    'legal': re.compile(
        r'(?:(?:the|Michigan|federal)\s+(?:law|statute|rule)\s+(?:requires|provides|mandates)|'
        r'(?:pursuant|according)\s+to|legal\s+(?:standard|authority|precedent))',
        re.IGNORECASE
    ),
    'policy': re.compile(
        r'(?:public\s+(?:policy|interest)|best\s+interest(?:s)?\s+of|'
        r'(?:justice|equity|fairness)\s+(?:requires|demands|dictates)|'
        r'(?:fundamental|constitutional)\s+(?:right|liberty|interest))',
        re.IGNORECASE
    ),
}

PASSIVE_VOICE_PATTERN = re.compile(
    r'\b(?:was|were|been|being|is|are|am)\s+(?:\w+ed|'
    r'(?:given|taken|made|done|shown|known|seen|found|held|brought|told|left|sent|kept))\b',
    re.IGNORECASE
)

RECORD_CITATION_PATTERN = re.compile(
    r'(?:\(?\s*(?:R\.|Rec\.|Record|Tr\.?|Transcript)\s*(?:at\s*|,\s*(?:p\.?\s*)?)?\d+)',
    re.IGNORECASE
)

SECTION_HEADERS = re.compile(
    r'^(?:#{1,4}\s+|[IVX]+\.\s+|[A-Z]\.\s+|\d+\.\s+)'
    r'(?:INTRODUCTION|STATEMENT\s+OF|ISSUES?\s+PRESENTED|STANDARD\s+OF\s+REVIEW|'
    r'ARGUMENT|FACTS|CONCLUSION|RELIEF\s+REQUESTED|SUMMARY\s+OF\s+ARGUMENT|'
    r'JURISDICTIONAL\s+STATEMENT|QUESTION|DISCUSSION)',
    re.IGNORECASE | re.MULTILINE
)


def get_db_connection():
    """Open DB connection with standard pragmas."""
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def read_brief(file_path):
    """Read brief content."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def split_sentences(text):
    """Split text into sentences."""
    clean = re.sub(r'\s+', ' ', text)
    clean = re.sub(r'(?:Mr|Mrs|Ms|Dr|Prof|Hon|Jr|Sr|Inc|Ltd|Corp|v|No|Vol|Rev|Stat|Supp|App|Mich|ed)\.',
                   lambda m: m.group().replace('.', '<DOT>'), clean)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean)
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences if len(s.strip()) > 10]
    return sentences


def calc_flesch_kincaid(text):
    """Calculate Flesch-Kincaid grade level."""
    sentences = split_sentences(text)
    if not sentences:
        return 0.0

    words = text.split()
    word_count = len(words)
    sentence_count = len(sentences)

    # Count syllables (approximation)
    def count_syllables(word):
        word = word.lower().strip('.,;:!?()[]{}"\'-')
        if len(word) <= 2:
            return 1
        count = 0
        vowels = 'aeiouy'
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith('e') and count > 1:
            count -= 1
        return max(count, 1)

    total_syllables = sum(count_syllables(w) for w in words)

    if sentence_count == 0 or word_count == 0:
        return 0.0

    grade = (0.39 * (word_count / sentence_count) +
             11.8 * (total_syllables / word_count) - 15.59)
    return round(max(0, grade), 1)


def count_citations(text):
    """Count legal citations in text."""
    total = 0
    by_type = {}
    for pattern in CITATION_PATTERNS:
        matches = pattern.findall(text)
        total += len(matches)
    return total


def analyze_citations(text, word_count):
    """Analyze citation density and types."""
    citation_count = count_citations(text)
    density = round((citation_count / max(word_count, 1)) * 1000, 1)
    record_cites = len(RECORD_CITATION_PATTERN.findall(text))

    return {
        'total_citations': citation_count,
        'density_per_1000': density,
        'record_citations': record_cites,
    }


def analyze_argument_structure(text):
    """Detect IRAC/CREAC argument patterns."""
    scores = {}
    for component, pattern in IRAC_INDICATORS.items():
        matches = pattern.findall(text)
        scores[component] = len(matches)

    # Score: all 4 components present = 100, each missing = -25
    components_present = sum(1 for v in scores.values() if v > 0)
    structure_score = min(100, components_present * 25)

    # Bonus for balanced structure
    if components_present == 4:
        values = list(scores.values())
        avg = statistics.mean(values)
        if avg > 0:
            cv = statistics.stdev(values) / avg if len(values) > 1 else 0
            balance_bonus = max(0, 10 - int(cv * 10))
            structure_score = min(100, structure_score + balance_bonus)

    return {
        'score': structure_score,
        'components': scores,
        'components_present': components_present,
        'pattern': 'IRAC' if components_present >= 3 else 'INCOMPLETE'
    }


def analyze_persuasion(text):
    """Analyze persuasion balance across factual, legal, and policy arguments."""
    counts = {}
    for category, pattern in PERSUASION_CATEGORIES.items():
        counts[category] = len(pattern.findall(text))

    total = sum(counts.values())
    if total == 0:
        return {'score': 30, 'distribution': counts, 'balance': 'WEAK'}

    pcts = {k: round((v / total) * 100, 1) for k, v in counts.items()}

    # Ideal balance: 40% factual, 40% legal, 20% policy (roughly)
    # Score based on having all three represented
    categories_used = sum(1 for v in counts.values() if v > 0)
    if categories_used == 3:
        score = 85
    elif categories_used == 2:
        score = 65
    else:
        score = 40

    # Penalize extreme imbalance
    if total > 3:
        max_pct = max(pcts.values())
        if max_pct > 80:
            score = max(30, score - 20)

    balance = 'STRONG' if score >= 80 else 'MODERATE' if score >= 60 else 'WEAK'

    return {
        'score': score,
        'distribution': counts,
        'percentages': pcts,
        'balance': balance
    }


def analyze_passive_voice(text):
    """Calculate passive voice percentage."""
    sentences = split_sentences(text)
    if not sentences:
        return {'percentage': 0.0, 'count': 0, 'total_sentences': 0}

    passive_count = sum(1 for s in sentences if PASSIVE_VOICE_PATTERN.search(s))
    pct = round((passive_count / len(sentences)) * 100, 1)

    return {
        'percentage': pct,
        'count': passive_count,
        'total_sentences': len(sentences)
    }


def analyze_sentence_lengths(text):
    """Analyze sentence length distribution."""
    sentences = split_sentences(text)
    if not sentences:
        return {'avg': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'distribution': {}}

    lengths = [len(s.split()) for s in sentences]

    # Distribution buckets
    buckets = {'short(<15)': 0, 'medium(15-25)': 0, 'long(25-40)': 0, 'very_long(>40)': 0}
    for l in lengths:
        if l < 15:
            buckets['short(<15)'] += 1
        elif l <= 25:
            buckets['medium(15-25)'] += 1
        elif l <= 40:
            buckets['long(25-40)'] += 1
        else:
            buckets['very_long(>40)'] += 1

    return {
        'avg': round(statistics.mean(lengths), 1),
        'median': round(statistics.median(lengths), 1),
        'std': round(statistics.stdev(lengths), 1) if len(lengths) > 1 else 0.0,
        'min': min(lengths),
        'max': max(lengths),
        'total_sentences': len(lengths),
        'distribution': buckets
    }


def analyze_sections(text):
    """Analyze document section organization."""
    headers = SECTION_HEADERS.findall(text)
    expected_sections = ['INTRODUCTION', 'STATEMENT', 'ISSUE', 'STANDARD', 'ARGUMENT', 'CONCLUSION']

    found = set()
    for h in headers:
        h_upper = h.upper()
        for expected in expected_sections:
            if expected in h_upper:
                found.add(expected)

    coverage = round((len(found) / len(expected_sections)) * 100)
    return {
        'score': coverage,
        'sections_found': list(found),
        'sections_missing': [s for s in expected_sections if s not in found],
        'total_headers': len(headers)
    }


def calc_metric_score(value, benchmark):
    """Score a metric 0-100 based on benchmark target and range."""
    target = benchmark['target']
    bmin = benchmark['min']
    bmax = benchmark['max']

    if bmin <= value <= bmax:
        # Within acceptable range - score based on distance from target
        if value <= target:
            score = 70 + 30 * ((value - bmin) / max(target - bmin, 0.01))
        else:
            score = 70 + 30 * ((bmax - value) / max(bmax - target, 0.01))
        return min(100, max(0, round(score)))
    else:
        # Outside range - reduced score
        distance = min(abs(value - bmin), abs(value - bmax))
        range_size = bmax - bmin
        penalty = min(70, (distance / max(range_size, 1)) * 100)
        return max(0, round(70 - penalty))


def analyze_brief(file_path):
    """Run full quality analysis on a brief."""
    text = read_brief(file_path)
    word_count = len(text.split())

    print(f"[ANALYZE] {Path(file_path).name} ({word_count:,} words)")

    # Run all analyses
    readability = calc_flesch_kincaid(text)
    citations = analyze_citations(text, word_count)
    structure = analyze_argument_structure(text)
    persuasion = analyze_persuasion(text)
    passive = analyze_passive_voice(text)
    sentence_stats = analyze_sentence_lengths(text)
    sections = analyze_sections(text)

    # Score each metric
    metric_scores = {}
    metric_scores['readability_grade'] = {
        'value': readability,
        'score': calc_metric_score(readability, BENCHMARKS['readability_grade']),
        'target': f"{BENCHMARKS['readability_grade']['min']}-{BENCHMARKS['readability_grade']['max']}",
        'status': 'GOOD' if BENCHMARKS['readability_grade']['min'] <= readability <= BENCHMARKS['readability_grade']['max'] else 'NEEDS_WORK'
    }
    metric_scores['citation_density'] = {
        'value': citations['density_per_1000'],
        'score': calc_metric_score(citations['density_per_1000'], BENCHMARKS['citation_density']),
        'target': f"{BENCHMARKS['citation_density']['min']}-{BENCHMARKS['citation_density']['max']} per 1000 words",
        'total_citations': citations['total_citations'],
        'status': 'GOOD' if citations['density_per_1000'] >= BENCHMARKS['citation_density']['min'] else 'NEEDS_WORK'
    }
    metric_scores['passive_voice_pct'] = {
        'value': passive['percentage'],
        'score': calc_metric_score(100 - passive['percentage'], {'target': 85, 'min': 80, 'max': 100, 'weight': 10}),
        'target': '<20%',
        'count': passive['count'],
        'status': 'GOOD' if passive['percentage'] <= 20 else 'NEEDS_WORK'
    }
    metric_scores['avg_sentence_length'] = {
        'value': sentence_stats['avg'],
        'score': calc_metric_score(sentence_stats['avg'], BENCHMARKS['avg_sentence_length']),
        'target': '15-30 words',
        'stats': sentence_stats,
        'status': 'GOOD' if 15 <= sentence_stats['avg'] <= 30 else 'NEEDS_WORK'
    }
    metric_scores['argument_structure'] = {
        'value': structure['score'],
        'score': structure['score'],
        'pattern': structure['pattern'],
        'components': structure['components'],
        'status': 'GOOD' if structure['score'] >= 75 else 'NEEDS_WORK'
    }
    metric_scores['persuasion_balance'] = {
        'value': persuasion['score'],
        'score': persuasion['score'],
        'distribution': persuasion.get('percentages', persuasion['distribution']),
        'balance': persuasion['balance'],
        'status': 'GOOD' if persuasion['score'] >= 65 else 'NEEDS_WORK'
    }
    metric_scores['record_citations'] = {
        'value': citations['record_citations'],
        'score': calc_metric_score(citations['record_citations'], BENCHMARKS['record_citations']),
        'target': '1+ per argument section',
        'status': 'GOOD' if citations['record_citations'] >= 1 else 'NEEDS_WORK'
    }
    metric_scores['section_organization'] = {
        'value': sections['score'],
        'score': sections['score'],
        'found': sections['sections_found'],
        'missing': sections['sections_missing'],
        'status': 'GOOD' if sections['score'] >= 67 else 'NEEDS_WORK'
    }

    # Calculate weighted overall score
    overall = 0
    total_weight = 0
    for key, benchmark in BENCHMARKS.items():
        if key in metric_scores:
            weight = benchmark['weight']
            overall += metric_scores[key]['score'] * weight
            total_weight += weight

    overall_score = round(overall / max(total_weight, 1))

    # Grade
    if overall_score >= 90:
        grade = 'A'
    elif overall_score >= 80:
        grade = 'B'
    elif overall_score >= 70:
        grade = 'C'
    elif overall_score >= 60:
        grade = 'D'
    else:
        grade = 'F'

    report = {
        'file': str(file_path),
        'analyzed_at': datetime.now().isoformat(),
        'word_count': word_count,
        'overall_score': overall_score,
        'grade': grade,
        'metrics': metric_scores,
        'recommendations': generate_recommendations(metric_scores)
    }

    return report


def generate_recommendations(metrics):
    """Generate improvement recommendations based on scores."""
    recs = []
    for key, data in metrics.items():
        if data.get('status') == 'NEEDS_WORK':
            name = key.replace('_', ' ').title()
            if key == 'readability_grade':
                recs.append(f"Readability: Grade level {data['value']} - target 12-16 for appellate writing. "
                            f"Simplify complex sentences while maintaining legal precision.")
            elif key == 'citation_density':
                recs.append(f"Citation Density: {data['value']}/1000 words is {'low' if data['value'] < 4 else 'high'}. "
                            f"Target 4-15 citations per 1000 words.")
            elif key == 'passive_voice_pct':
                recs.append(f"Passive Voice: {data['value']}% - target <20%. "
                            f"Convert passive constructions to active voice for stronger advocacy.")
            elif key == 'avg_sentence_length':
                recs.append(f"Sentence Length: avg {data['value']} words - target 15-30. "
                            f"{'Break up long sentences.' if data['value'] > 30 else 'Combine short fragments.'}")
            elif key == 'argument_structure':
                recs.append(f"Argument Structure: Missing IRAC components. "
                            f"Ensure each argument has Issue, Rule, Application, and Conclusion.")
            elif key == 'persuasion_balance':
                recs.append(f"Persuasion Balance: {data['balance']}. "
                            f"Include factual, legal, and policy arguments for maximum persuasion.")
            elif key == 'record_citations':
                recs.append(f"Record Citations: Only {data['value']} record references found. "
                            f"Cite the lower court record throughout factual arguments.")
            elif key == 'section_organization':
                missing = data.get('missing', [])
                if missing:
                    recs.append(f"Organization: Missing sections: {', '.join(missing)}. "
                                f"Include standard appellate brief sections.")
    return recs


def format_scorecard_md(report):
    """Format quality scorecard as markdown."""
    lines = []
    lines.append(f"# Brief Quality Scorecard")
    lines.append(f"")
    lines.append(f"**File:** {report['file']}")
    lines.append(f"**Date:** {report['analyzed_at']}")
    lines.append(f"**Words:** {report['word_count']:,}")
    lines.append(f"")
    lines.append(f"## Overall: {report['overall_score']}/100 (Grade: {report['grade']})")
    lines.append(f"")

    lines.append(f"## Metric Breakdown")
    lines.append(f"")
    lines.append(f"| Metric | Value | Score | Status |")
    lines.append(f"|--------|-------|-------|--------|")
    for key, data in report['metrics'].items():
        name = key.replace('_', ' ').title()
        val = data['value']
        score = data['score']
        status = data.get('status', 'N/A')
        icon = '[OK]' if status == 'GOOD' else '[!!]'
        lines.append(f"| {name} | {val} | {score}/100 | {icon} {status} |")

    lines.append(f"")

    if report['recommendations']:
        lines.append(f"## Recommendations")
        lines.append(f"")
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        lines.append(f"")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Brief Quality Engine - Legal writing quality scorer'
    )
    parser.add_argument('--file', type=str, required=True, help='Path to brief file')
    parser.add_argument('--benchmark', action='store_true',
                        help='Compare against published appellate brief benchmarks')
    parser.add_argument('--output', type=str, choices=['json', 'md'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--save', type=str, help='Save report to file')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"[ERROR] File not found: {args.file}")
        sys.exit(1)

    print(f"[START] Brief Quality Engine - {datetime.now().isoformat()}")

    try:
        report = analyze_brief(args.file)

        # Print summary line
        score = report['overall_score']
        grade = report['grade']
        wc = report['word_count']
        recs = len(report['recommendations'])
        print(f"\n[RESULT] Score: {score}/100 | Grade: {grade} | Words: {wc:,} | Recommendations: {recs}")

        if args.benchmark:
            print("\n[BENCHMARK] Comparison against appellate brief standards:")
            for key, bm in BENCHMARKS.items():
                if key in report['metrics']:
                    val = report['metrics'][key]['value']
                    target = bm['target']
                    diff = val - target
                    direction = '+' if diff > 0 else ''
                    print(f"  {key:<25s} Value: {val:>6.1f}  Target: {target:>6.1f}  Delta: {direction}{diff:.1f}")

        # Output
        if args.output == 'md':
            output_text = format_scorecard_md(report)
        else:
            output_text = json.dumps(report, indent=2, ensure_ascii=True)

        if args.save:
            with open(args.save, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"[SAVED] Report written to {args.save}")
        else:
            print(f"\n{output_text}")

    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print(f"[DONE] {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
