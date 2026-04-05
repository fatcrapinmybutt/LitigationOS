#!/usr/bin/env python3
"""
skill_authority_validator.py -- Citation & Authority Validator

Cross-references every citation against authority libraries.
Validates case name, citation format, current good law status.
Flags overruled, distinguished, limited cases.
"""
import sys, sqlite3, json, re
from datetime import datetime
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

# -- Citation format patterns-----------------------------------------------

CITATION_PATTERNS = {
    'michigan_supreme': re.compile(r'(\d+)\s+Mich\s+(\d+)\s*\((\d{4})\)'),
    'michigan_appeals': re.compile(r'(\d+)\s+Mich\s+App\s+(\d+)\s*\((\d{4})\)'),
    'federal_supreme': re.compile(r'(\d+)\s+US\s+(\d+)\s*\((\d{4})\)'),
    'federal_reporter': re.compile(r'(\d+)\s+F\.\s*(?:2d|3d|4th)?\s+(\d+)'),
    'mcl': re.compile(r'MCL\s+([\d.]+)'),
    'mcr': re.compile(r'MCR\s+([\d.]+)'),
    'usc': re.compile(r'(\d+)\s+USC\s+(\d+)'),
    'nw2d': re.compile(r'(\d+)\s+NW\s*2d\s+(\d+)'),
}

AUTHORITY_TABLES = [
    'auth_rules', 'auth_passages', 'caselaw_unified',
    'constitutional_provisions', 'authority_library',
]

FTS_TABLES = [
    'auth_rules_fts', 'auth_passages_fts', 'caselaw_unified_fts',
]

# -- Status flags ----------------------------------------------------------

NEGATIVE_SIGNALS = [
    'overruled', 'reversed', 'vacated', 'abrogated',
    'superseded', 'disapproved', 'no longer good law',
]

CAUTION_SIGNALS = [
    'distinguished', 'limited', 'criticized', 'questioned',
    'modified', 'narrowed', 'clarified',
]


def validate_citation(citation: str) -> dict:
    """Validate a single citation for format and substance."""
    conn = _connect()

    # Determine citation type
    citation_type = 'unknown'
    parsed = {}
    for ctype, pattern in CITATION_PATTERNS.items():
        match = pattern.search(citation)
        if match:
            citation_type = ctype
            parsed = {'groups': match.groups(), 'matched': match.group()}
            break

    # Search authority tables for the citation
    found_in = []
    authority_data = []
    for tbl in AUTHORITY_TABLES:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{tbl}] WHERE "
                f"CAST(* AS TEXT) LIKE ? LIMIT 5",
                (f'%{citation}%',)
            ).fetchall()
            if rows:
                found_in.append(tbl)
                authority_data.extend([dict(r) for r in rows])
        except Exception:
            pass

    # FTS search
    for fts in FTS_TABLES:
        try:
            # Clean citation for FTS
            clean = re.sub(r'[^\w\s]', ' ', citation).strip()
            if clean:
                rows = conn.execute(
                    f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 5",
                    (clean,)
                ).fetchall()
                if rows:
                    authority_data.extend([dict(r) for r in rows])
                    found_in.append(fts)
        except Exception:
            pass

    conn.close()

    # Check for negative treatment
    negative_flags = []
    caution_flags = []
    for entry in authority_data:
        text = json.dumps(entry, default=str).lower()
        for signal in NEGATIVE_SIGNALS:
            if signal in text:
                negative_flags.append(signal)
        for signal in CAUTION_SIGNALS:
            if signal in text:
                caution_flags.append(signal)

    status = (
        'BAD_LAW' if negative_flags else
        'CAUTION' if caution_flags else
        'GOOD' if authority_data else
        'NOT_FOUND'
    )

    return {
        'citation': citation,
        'citation_type': citation_type,
        'parsed': parsed,
        'format_valid': citation_type != 'unknown',
        'found_in_tables': list(set(found_in)),
        'authority_matches': len(authority_data),
        'status': status,
        'negative_signals': list(set(negative_flags)),
        'caution_signals': list(set(caution_flags)),
        'preview': [str(a)[:200] for a in authority_data[:3]],
    }


def check_good_law(citation: str) -> dict:
    """Deep check whether a citation is still good law."""
    base = validate_citation(citation)

    # Enhanced search for treatment history
    conn = _connect()
    treatment = []

    for fts in FTS_TABLES:
        try:
            clean = re.sub(r'[^\w\s]', ' ', citation).strip()
            if clean:
                rows = conn.execute(
                    f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 15",
                    (clean,)
                ).fetchall()
                for r in rows:
                    text = json.dumps(dict(r), default=str).lower()
                    for signal in NEGATIVE_SIGNALS + CAUTION_SIGNALS:
                        if signal in text:
                            treatment.append({
                                'signal': signal,
                                'source': fts,
                                'preview': str(dict(r))[:200],
                            })
        except Exception:
            pass

    conn.close()

    base['treatment_history'] = treatment
    base['good_law'] = base['status'] in ('GOOD', 'NOT_FOUND')
    base['recommendation'] = (
        'SAFE TO CITE' if base['status'] == 'GOOD' else
        'USE WITH CAUTION -- check treatment' if base['status'] == 'CAUTION' else
        'DO NOT CITE -- negative treatment detected' if base['status'] == 'BAD_LAW' else
        'VERIFY INDEPENDENTLY -- not found in authority library'
    )

    return base


def batch_validate(citations_text: str) -> dict:
    """Validate multiple citations from a text block."""
    # Extract all citations from text
    found_citations = []
    for ctype, pattern in CITATION_PATTERNS.items():
        for match in pattern.finditer(citations_text):
            found_citations.append({
                'type': ctype,
                'citation': match.group(),
                'position': match.start(),
            })

    # Validate each
    results = []
    for fc in found_citations:
        validation = validate_citation(fc['citation'])
        results.append({
            'citation': fc['citation'],
            'type': fc['type'],
            'status': validation['status'],
            'format_valid': validation['format_valid'],
            'negative_signals': validation['negative_signals'],
        })

    # Summary
    summary = {
        'total_citations_found': len(results),
        'good': len([r for r in results if r['status'] == 'GOOD']),
        'caution': len([r for r in results if r['status'] == 'CAUTION']),
        'bad_law': len([r for r in results if r['status'] == 'BAD_LAW']),
        'not_found': len([r for r in results if r['status'] == 'NOT_FOUND']),
        'format_errors': len([r for r in results if not r['format_valid']]),
    }

    return {
        'validation_date': datetime.now().isoformat(),
        'summary': summary,
        'results': results,
        'flagged_citations': [r for r in results if r['status'] in ('BAD_LAW', 'CAUTION')],
    }


# -- CLI -------------------------------------------------------------------

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Citation & Authority Validator')
    parser.add_argument('--action', default='validate',
                        choices=['validate', 'check_good_law', 'batch_validate'])
    parser.add_argument('--citation', type=str, help='Citation to validate')
    parser.add_argument('--text', type=str, help='Text block for batch validation')
    args = parser.parse_args()

    if args.action == 'validate':
        if not args.citation:
            parser.error('--citation required')
        result = validate_citation(args.citation)
    elif args.action == 'check_good_law':
        if not args.citation:
            parser.error('--citation required')
        result = check_good_law(args.citation)
    elif args.action == 'batch_validate':
        if not args.text:
            parser.error('--text required')
        result = batch_validate(args.text)

    print(json.dumps(result, indent=2, default=str))
