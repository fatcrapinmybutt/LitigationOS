"""
litigationos_patterns.py — Standalone Regex Pattern Library for LitigationOS
"""
import re
from collections import Counter
from typing import Dict, List, Tuple
from pathlib import Path

MCR_PATTERN = re.compile(r'MCR\s*(\d{1,2})\.(\d{3}(?:\([A-Za-z0-9]+\))*)', re.IGNORECASE)
MCL_PATTERN = re.compile(r'MCL\s*(\d{3,4})\.(\d{1,5}[a-z]?(?:\([A-Za-z0-9]+\))*)', re.IGNORECASE)
CASE_LAW_PATTERN = re.compile(r'(\d{1,3})\s+Mich\s+(?:App\s+)?(\d{1,4})', re.IGNORECASE)
FEDERAL_CASE_PATTERN = re.compile(r'(\d{1,3})\s+(?:U\.?S\.?|S\.?\s*Ct\.?|F\.?\s*(?:2d|3d|4th|Supp))\s+(\d{1,5})', re.IGNORECASE)
CANON_PATTERN = re.compile(r'Canon\s+(\d[A-Z]?)', re.IGNORECASE)
DATE_PATTERN = re.compile(r'\b(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+20\d{2}|\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b')
CASE_NUMBER_PATTERN = re.compile(r'\b(20\d{2})[- ]?(\d{4,6})[- ]?(PP|DC|CB|CZ|DM|GC|DO|FC|FH|FJ|AV|CK|CR)\b', re.IGNORECASE)

VIOLATION_PATTERNS = {
    'ex_parte': re.compile(r'\bex\s*parte\b', re.I),
    'bias': re.compile(r'\bbias(?:ed)?\b', re.I),
    'misconduct': re.compile(r'\bmisconduct\b', re.I),
    'due_process': re.compile(r'\bdue\s+process\b', re.I),
    'abuse_of_discretion': re.compile(r'\babuse\s+of\s+discretion\b', re.I),
    'perjury': re.compile(r'\bperjur[yied]+\b', re.I),
    'fraud': re.compile(r'\bfraud(?:ulent)?\b', re.I),
    'false_statement': re.compile(r'\bfalse\s+statement', re.I),
    'contempt': re.compile(r'\bcontempt\b', re.I),
    'violation': re.compile(r'\bviolation\b', re.I),
    'retaliation': re.compile(r'\bretaliat\w+\b', re.I),
    'alienation': re.compile(r'\balienat\w+\b', re.I),
    'domestic_violence': re.compile(r'\bdomestic\s+violence\b', re.I),
}

PEOPLE_PATTERNS = {
    'Pigors': re.compile(r'\bPigors\b', re.I),
    'Watson': re.compile(r'\bWatson\b', re.I),
    'McNeill': re.compile(r'\bMcNeill\b', re.I),
    'HealthWest': re.compile(r'\bHealthWest\b', re.I),
    'Rusco': re.compile(r'\bRusco\b', re.I),
    'Martini': re.compile(r'\bMartini\b', re.I),
    'Shady_Oaks': re.compile(r'\bShady\s*Oaks\b', re.I),
}

PATTERNS = {
    'MCR': MCR_PATTERN, 'MCL': MCL_PATTERN, 'CASE_LAW': CASE_LAW_PATTERN,
    'FEDERAL_CASE': FEDERAL_CASE_PATTERN, 'CANON': CANON_PATTERN,
    'DATE': DATE_PATTERN, 'CASE_NUMBER': CASE_NUMBER_PATTERN,
    **{f'VIOLATION_{k.upper()}': v for k, v in VIOLATION_PATTERNS.items()},
    **{f'PERSON_{k.upper()}': v for k, v in PEOPLE_PATTERNS.items()},
}

BEST_INTEREST_FACTORS = {
    'a': [re.compile(r'\blove\b', re.I), re.compile(r'\baffection\b', re.I), re.compile(r'\bemotional\s+tie', re.I)],
    'b': [re.compile(r'\bguidance\b', re.I), re.compile(r'\beducat\w+\b', re.I), re.compile(r'\bnurtur\w+\b', re.I)],
    'c': [re.compile(r'\bmedical\s+care\b', re.I), re.compile(r'\bfood\b', re.I), re.compile(r'\bcloth\w+\b', re.I)],
    'd': [re.compile(r'\bstab\w+\s+environment\b', re.I), re.compile(r'\bresiden\w+\b', re.I)],
    'e': [re.compile(r'\bpermanence\b', re.I), re.compile(r'\bcustodial\s+home\b', re.I), re.compile(r'\bhousing\b', re.I)],
    'f': [re.compile(r'\bmoral\s+fitness\b', re.I), re.compile(r'\bsubstance\s+abuse\b', re.I), re.compile(r'\bDUI\b', re.I)],
    'g': [re.compile(r'\bmental\s+health\b', re.I), re.compile(r'\bHealthWest\b', re.I), re.compile(r'\bpsych\w+\b', re.I)],
    'h': [re.compile(r'\bschool\s+record\b', re.I), re.compile(r'\bdaycare\b', re.I)],
    'i': [re.compile(r'\bchild.{0,10}prefer\b', re.I)],
    'j': [re.compile(r'\balienat\w+\b', re.I), re.compile(r'\bgatekeep\w+\b', re.I), re.compile(r'\binterfer\w+\b', re.I)],
    'k': [re.compile(r'\bdomestic\s+violence\b', re.I), re.compile(r'\bPPO\b'), re.compile(r'\bassault\b', re.I)],
    'l': [re.compile(r'\bfalse\s+statement\b', re.I), re.compile(r'\bperjur\w+\b', re.I), re.compile(r'\bfraud\b', re.I)],
}

def count_all(text):
    return {name: len(pattern.findall(text)) for name, pattern in PATTERNS.items()}

def best_interest_scan(text):
    results = {}
    for factor, patterns in BEST_INTEREST_FACTORS.items():
        total = sum(len(p.findall(text)) for p in patterns)
        if total > 0:
            results[f'factor_{factor}'] = total
    return results

def score_file(filepath, max_bytes=50_000_000):
    path = Path(filepath)
    if not path.exists() or path.stat().st_size > max_bytes:
        return {'error': 'File not found or too large', 'score': 0}
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return {'error': str(e), 'score': 0}
    counts = count_all(text)
    weights = {'MCR': 10, 'MCL': 10, 'CASE_LAW': 15, 'FEDERAL_CASE': 15, 'CANON': 20, 'DATE': 1, 'CASE_NUMBER': 5}
    for k in counts:
        if k.startswith('VIOLATION_'): weights[k] = 3
        elif k.startswith('PERSON_'): weights[k] = 2
    score = sum(counts.get(k, 0) * weights.get(k, 1) for k in counts)
    return {'file': str(path.name), 'chars': len(text), 'counts': {k: v for k, v in counts.items() if v > 0}, 'score': score}