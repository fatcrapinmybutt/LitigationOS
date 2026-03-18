#!/usr/bin/env python3
"""
Evidence Chain Mapper — LitigationOS Novel Tool
================================================
Maps every factual claim in filings to supporting evidence in the DB.
Identifies unsupported claims, weak evidence chains, and suggests
additional evidence from the 36,891-row evidence_quotes table.

Key capabilities:
  1. Extract factual claims from each filing
  2. Search evidence_quotes DB for supporting evidence
  3. Score evidence strength per claim (0-10)
  4. Identify UNSUPPORTED claims (potential vulnerability)
  5. Suggest additional evidence from DB that could strengthen claims
  6. Generate filing-specific evidence maps

Usage:
  python evidence_chain_mapper.py [--filing F9] [--all] [--json] [--verbose]
"""

import sys, os, re, json, sqlite3, argparse
from collections import defaultdict
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

FILING_BASE = r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE"
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

FILING_MAP = {
    "F1":  ("PKG_F1_EMERGENCY_TRO", "Emergency TRO (Housing)"),
    "F2":  ("PKG_F2_SHADY_OAKS_COMPLAINT", "Amended Complaint (Housing)"),
    "F3":  ("PKG_F3_DISQUALIFICATION_MCR_2003", "Disqualification Motion"),
    "F4":  ("PKG_F4_FEDERAL_S1983_COMPLAINT", "Federal §1983 Complaint"),
    "F5":  ("PKG_F5_MSC_ORIGINAL_ACTION", "MSC Original Action"),
    "F6":  ("PKG_F6_JTC_COMPLAINT", "JTC Complaint"),
    "F7":  ("PKG_F7_CUSTODY_MODIFICATION", "Custody Modification"),
    "F8":  ("PKG_F8_PPO_TERMINATION", "PPO Termination"),
    "F9":  ("PKG_F9_COA_BRIEF_ON_APPEAL", "COA Brief on Appeal"),
    "F10": ("PKG_F10_COA_EMERGENCY_MOTION", "COA Emergency Motion"),
}

# Claim extraction patterns — what constitutes a factual claim
CLAIM_PATTERNS = [
    # Direct factual assertions
    (r'(?:On|In|During|Since|Between|After|Before|By)\s+\w+\s+\d{1,2},?\s+\d{4}[,.]?\s+(.{20,120})', 'dated_assertion'),
    # Quantitative claims
    (r'(\d+)\s+(?:days?|months?|years?|times?|incidents?|violations?|orders?|hearings?)', 'quantitative'),
    # Named actor actions
    (r'(?:Judge\s+McNeill|McNeill|Rusco|Watson|Emily|Barnes|Berry|Martini|Hooker)\s+(?:did|has|had|was|were|filed|issued|ordered|denied|refused|failed|violated|entered|signed|sent)\s+(.{10,100})', 'actor_action'),
    # "The court" actions
    (r'(?:The\s+(?:court|trial\s+court|circuit\s+court))\s+(?:did|has|had|was|entered|issued|ordered|denied|refused|failed|violated)\s+(.{10,100})', 'court_action'),
    # Evidence references
    (r'(?:Exhibit|Ex\.)\s+(\w+)\s*(?:shows?|demonstrates?|proves?|establishes?|reveals?|confirms?)\s+(.{10,80})', 'exhibit_ref'),
    # Statistical claims
    (r'(\d+(?:,\d{3})*)\s+(?:documents?|emails?|texts?|messages?|records?|violations?|incidents?)', 'statistical'),
]

# Evidence search categories — maps claim types to DB search strategies
EVIDENCE_CATEGORIES = {
    'ex_parte': ['ex parte', 'without notice', 'unilateral', 'one-sided'],
    'bias': ['bias', 'prejudice', 'impartial', 'objective', 'disqualif'],
    'ppo': ['PPO', 'protection order', 'personal protection', 'no contact'],
    'custody': ['custody', 'parenting time', 'child', 'visitation', 'overnight'],
    'healthwest': ['healthwest', 'evaluation', 'mental health', 'delusional', 'psychological'],
    'contempt': ['contempt', 'show cause', 'jail', 'incarcerat', 'sentence'],
    'rusco': ['rusco', 'secretary', 'warrant', 'email'],
    'conspiracy': ['conspir', 'collu', 'coordinate', 'scheme'],
    'housing': ['rent', 'evict', 'mobile home', 'trailer', 'lot fee', 'Shady Oaks'],
    'employment': ['job', 'employ', 'work', 'fired', 'terminated', 'Metal Arc', 'IndiGrow', 'USPS'],
    'financial': ['damage', 'loss', 'income', 'salary', 'wage', 'cost', 'fee'],
    'due_process': ['due process', 'notice', 'hearing', 'opportunity', 'constitutional'],
}


def get_db_connection():
    """Get DB connection with proper PRAGMAs."""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.row_factory = sqlite3.Row
    return conn


def extract_claims(text, filing_id):
    """Extract factual claims from filing text."""
    claims = []
    lines = text.split('\n')
    seen_claims = set()

    for line_num, line in enumerate(lines, 1):
        # Skip headers, blank lines, citations
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('---'):
            continue
        if len(stripped) < 30:
            continue

        for pattern, claim_type in CLAIM_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                claim_text = match.group(0).strip()
                # Deduplicate
                claim_key = claim_text[:50].lower()
                if claim_key in seen_claims:
                    continue
                seen_claims.add(claim_key)

                # Categorize the claim
                category = categorize_claim(claim_text)

                claims.append({
                    'filing': filing_id,
                    'line': line_num,
                    'text': claim_text[:200],
                    'type': claim_type,
                    'category': category,
                })

        # Also catch strong assertion sentences
        if any(kw in line.lower() for kw in ['violated', 'denied', 'refused', 'failed to',
                                               'without notice', 'ex parte', 'fabricat',
                                               'never', 'no evidence', 'contrary to']):
            # Strong assertion — extract the key clause
            clean = stripped[:200]
            claim_key = clean[:50].lower()
            if claim_key not in seen_claims:
                seen_claims.add(claim_key)
                claims.append({
                    'filing': filing_id,
                    'line': line_num,
                    'text': clean,
                    'type': 'strong_assertion',
                    'category': categorize_claim(clean),
                })

    return claims


def categorize_claim(text):
    """Categorize a claim into evidence search categories."""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in EVIDENCE_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return 'general'


def search_evidence(conn, claim, limit=5):
    """Search the evidence_quotes table for supporting evidence."""
    keywords = []
    # Extract significant words from claim
    words = re.findall(r'\b[a-zA-Z]{4,}\b', claim['text'])
    # Remove common words
    stopwords = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'which',
                 'their', 'there', 'about', 'would', 'could', 'should', 'after',
                 'before', 'during', 'between', 'without', 'under', 'through'}
    keywords = [w for w in words if w.lower() not in stopwords][:6]

    if not keywords:
        return []

    # Try FTS5 first (actual table: evidence_quotes_fts)
    try:
        fts_query = ' OR '.join(keywords[:4])
        rows = conn.execute("""
            SELECT eq.id, eq.quote_text, eq.evidence_category, eq.speaker, eq.source_type
            FROM evidence_quotes_fts fts
            JOIN evidence_quotes eq ON fts.rowid = eq.id
            WHERE fts.quote_text MATCH ?
            LIMIT ?
        """, (fts_query, limit)).fetchall()
        if rows:
            return [{'quote_text': r[1], 'source_file': r[4] or r[3] or 'unknown',
                      'relevance_score': 1.0, 'category': r[2]} for r in rows]
    except Exception:
        pass

    # Fallback: LIKE search on actual columns
    conditions = []
    params = []
    for kw in keywords[:3]:
        conditions.append("quote_text LIKE ?")
        params.append(f"%{kw}%")

    if not conditions:
        return []

    query = f"""
        SELECT id, quote_text, evidence_category, speaker, source_type
        FROM evidence_quotes
        WHERE {' OR '.join(conditions)}
        LIMIT ?
    """
    params.append(limit)

    try:
        rows = conn.execute(query, params).fetchall()
        return [{'quote_text': r[1], 'source_file': r[4] or r[3] or 'unknown',
                  'relevance_score': 0.7, 'category': r[2]} for r in rows]
    except Exception:
        return []


def score_evidence_strength(evidence_list):
    """Score how well the evidence supports the claim (0-10)."""
    if not evidence_list:
        return 0
    count = len(evidence_list)
    avg_relevance = sum(e.get('relevance_score', 0) or 0 for e in evidence_list) / count

    # Score based on count and quality
    if count >= 5:
        base = 8
    elif count >= 3:
        base = 6
    elif count >= 2:
        base = 4
    elif count >= 1:
        base = 2
    else:
        base = 0

    # Bonus for high relevance
    if avg_relevance > 0.8:
        base = min(10, base + 2)
    elif avg_relevance > 0.5:
        base = min(10, base + 1)

    return base


def run_mapping(filing_ids=None, verbose=False, output_json=False):
    """Run evidence chain mapping for specified filings."""
    if filing_ids is None:
        filing_ids = list(FILING_MAP.keys())

    print("═" * 70)
    print("  EVIDENCE CHAIN MAPPER — LitigationOS")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 70)
    print()

    # Check DB
    if not os.path.exists(DB_PATH):
        print(f"  ❌ Database not found: {DB_PATH}")
        return []

    conn = get_db_connection()

    # Check evidence_quotes exists
    try:
        count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
        print(f"  📊 Evidence database: {count:,} quotes available")
    except Exception as e:
        print(f"  ⚠ evidence_quotes table issue: {e}")
        count = 0

    print()

    all_results = []
    filing_summaries = {}

    for fid in filing_ids:
        if fid not in FILING_MAP:
            print(f"  ⚠ Unknown filing: {fid}")
            continue

        folder, name = FILING_MAP[fid]
        main_path = os.path.join(FILING_BASE, folder, "01_MAIN_FILING.md")

        if not os.path.exists(main_path):
            print(f"  ⚠ Filing not found: {main_path}")
            continue

        with open(main_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        claims = extract_claims(text, fid)

        print(f"{'═' * 70}")
        print(f"  {fid}: {name}")
        print(f"  Claims extracted: {len(claims)}")
        print(f"{'═' * 70}")

        supported = 0
        weak = 0
        unsupported = 0
        filing_results = []

        for claim in claims:
            evidence = search_evidence(conn, claim) if count > 0 else []
            strength = score_evidence_strength(evidence)

            result = {
                'filing': fid,
                'line': claim['line'],
                'claim': claim['text'][:150],
                'category': claim['category'],
                'evidence_count': len(evidence),
                'strength': strength,
                'status': 'STRONG' if strength >= 6 else 'WEAK' if strength >= 3 else 'UNSUPPORTED',
            }

            if strength >= 6:
                supported += 1
            elif strength >= 3:
                weak += 1
            else:
                unsupported += 1

            if verbose and strength < 6:
                icon = "🟡" if strength >= 3 else "🔴"
                print(f"\n  {icon} Line {claim['line']} [{claim['category']}] (strength: {strength}/10)")
                print(f"     Claim: \"{claim['text'][:100]}...\"")
                if evidence:
                    print(f"     Evidence found: {len(evidence)} quotes")
                    for ev in evidence[:2]:
                        src = ev.get('source_file', 'unknown')
                        print(f"       → [{src}] \"{str(ev.get('quote_text', ''))[:80]}...\"")
                else:
                    print(f"     ⚠ NO supporting evidence found in DB")

            filing_results.append(result)
            all_results.append(result)

        total = len(claims)
        pct_supported = (supported / total * 100) if total else 0
        pct_unsupported = (unsupported / total * 100) if total else 0

        filing_summaries[fid] = {
            'name': name,
            'total_claims': total,
            'supported': supported,
            'weak': weak,
            'unsupported': unsupported,
            'pct_supported': round(pct_supported, 1),
            'strength_grade': 'A' if pct_supported >= 80 else 'B' if pct_supported >= 60 else 'C' if pct_supported >= 40 else 'D' if pct_supported >= 20 else 'F',
        }

        print(f"\n  Summary: {supported} strong ✅ | {weak} weak 🟡 | {unsupported} unsupported 🔴")
        print(f"  Evidence coverage: {pct_supported:.0f}% | Grade: {filing_summaries[fid]['strength_grade']}")
        print()

    conn.close()

    # Overall summary
    print("═" * 70)
    print("  EVIDENCE CHAIN SUMMARY")
    print("═" * 70)
    print()
    print(f"  {'Filing':6s} {'Name':30s} {'Claims':>6s} {'Strong':>7s} {'Weak':>5s} {'None':>5s} {'Grade':>6s}")
    print(f"  {'─'*6} {'─'*30} {'─'*6} {'─'*7} {'─'*5} {'─'*5} {'─'*6}")

    for fid in filing_ids:
        if fid in filing_summaries:
            s = filing_summaries[fid]
            print(f"  {fid:6s} {s['name']:30s} {s['total_claims']:6d} {s['supported']:7d} {s['weak']:5d} {s['unsupported']:5d} {s['strength_grade']:>6s}")

    total_claims = sum(s['total_claims'] for s in filing_summaries.values())
    total_supported = sum(s['supported'] for s in filing_summaries.values())
    total_unsupported = sum(s['unsupported'] for s in filing_summaries.values())
    print(f"  {'─'*6} {'─'*30} {'─'*6} {'─'*7} {'─'*5} {'─'*5}")
    print(f"  {'TOTAL':6s} {'':30s} {total_claims:6d} {total_supported:7d} {'':5s} {total_unsupported:5d}")
    print()

    if total_unsupported > 0:
        print(f"  ⚠ {total_unsupported} claims have NO supporting evidence in DB")
        print(f"    These are vulnerability points opposing counsel may exploit.")
    print()

    # JSON output
    if output_json:
        report = {
            'generated': datetime.now().isoformat(),
            'db_evidence_count': count,
            'filing_summaries': filing_summaries,
            'total_claims': total_claims,
            'total_supported': total_supported,
            'total_unsupported': total_unsupported,
            'results': all_results,
        }
        json_path = os.path.join(os.path.dirname(__file__), '..', 'reports', 'evidence_chain_map.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  JSON report saved to: {json_path}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description='Evidence Chain Mapper')
    parser.add_argument('--filing', '-f', help='Specific filing (e.g., F9)')
    parser.add_argument('--all', '-a', action='store_true', help='Map all filings')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show weak/unsupported claims')
    args = parser.parse_args()

    if args.filing:
        filings = [args.filing.upper()]
    else:
        filings = None

    run_mapping(filing_ids=filings, verbose=args.verbose, output_json=args.json)


if __name__ == '__main__':
    main()
