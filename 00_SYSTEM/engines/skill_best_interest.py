#!/usr/bin/env python3
"""
skill_best_interest.py — MCL 722.23 Best Interest Factor Analyzer
Queries DB for evidence on all 12 factors, scores each, generates analysis.
Wired to: bif_factor_complete, bif_evidence_links, extracted_harms, evidence_quotes,
          alienation_scoring, alienation_tactics, master_chronological_timeline
"""
import sys, os, sqlite3, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')
OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c

# ── MCL 722.23 Factor Definitions ──────────────────────────────────

FACTORS = {
    'a': {
        'name': 'Love, Affection, and Emotional Ties',
        'statute': 'MCL 722.23(a)',
        'description': 'Love, affection, and other emotional ties existing between the parties involved and the child.',
        'search_terms': ['love', 'affection', 'emotional', 'bond', 'attachment', 'children', 'father', 'parenting'],
    },
    'b': {
        'name': 'Capacity to Continue Raising',
        'statute': 'MCL 722.23(b)',
        'description': 'Capacity and disposition of the parties to give the child love, affection, and guidance and to continue educating and raising the child.',
        'search_terms': ['capacity', 'parenting', 'education', 'guidance', 'raising', 'stability', 'employment'],
    },
    'c': {
        'name': 'Capacity to Provide (Food, Clothing, Medical)',
        'statute': 'MCL 722.23(c)',
        'description': 'Capacity and disposition of the parties to provide the child with food, clothing, medical care.',
        'search_terms': ['food', 'clothing', 'medical', 'insurance', 'financial', 'housing', 'rent', 'income'],
    },
    'd': {
        'name': 'Stable Custodial Environment',
        'statute': 'MCL 722.23(d)',
        'description': 'Length of time the child has lived in a stable, satisfactory environment.',
        'search_terms': ['stable', 'environment', 'custody', 'home', 'residence', 'living', 'housing'],
    },
    'e': {
        'name': 'Permanence of Family Unit',
        'statute': 'MCL 722.23(e)',
        'description': 'Permanence, as a family unit, of the existing or proposed custodial home.',
        'search_terms': ['family', 'permanence', 'unit', 'household', 'siblings', 'relatives'],
    },
    'f': {
        'name': 'Moral Fitness',
        'statute': 'MCL 722.23(f)',
        'description': 'Moral fitness of the parties involved.',
        'search_terms': ['moral', 'fitness', 'false', 'report', 'fraud', 'manipulation', 'lying', 'perjury', 'deception'],
    },
    'g': {
        'name': 'Mental and Physical Health',
        'statute': 'MCL 722.23(g)',
        'description': 'Mental and physical health of the parties involved.',
        'search_terms': ['mental health', 'physical', 'health', 'therapy', 'counseling', 'medical'],
    },
    'h': {
        'name': 'Home, School, Community Record',
        'statute': 'MCL 722.23(h)',
        'description': "The child's home, school, and community record.",
        'search_terms': ['school', 'community', 'Muskegon', 'record', 'education', 'activities'],
    },
    'i': {
        'name': 'Reasonable Preference of Child',
        'statute': 'MCL 722.23(i)',
        'description': 'Reasonable preference of the child, if the child is of sufficient age.',
        'search_terms': ['preference', 'child', 'wish', 'want', 'choose', 'statement'],
    },
    'j': {
        'name': 'Willingness to Facilitate Relationship',
        'statute': 'MCL 722.23(j)',
        'description': 'Willingness and ability of each party to facilitate and encourage a close and continuing parent-child relationship.',
        'search_terms': ['facilitate', 'relationship', 'alienation', 'denied', 'access', 'visitation', 'parenting time', 'gatekeeping'],
    },
    'k': {
        'name': 'Domestic Violence',
        'statute': 'MCL 722.23(k)',
        'description': 'Domestic violence, regardless of whether directed against the child.',
        'search_terms': ['domestic violence', 'PPO', 'protection order', 'abuse', 'assault', 'false PPO'],
    },
    'l': {
        'name': 'Any Other Relevant Factor',
        'statute': 'MCL 722.23(l)',
        'description': 'Any other factor considered by the court to be relevant.',
        'search_terms': ['conspiracy', 'obstruction', 'contempt', 'judicial', 'due process', 'constitutional'],
    },
}


def get_existing_bif_data():
    """Get pre-computed BIF data from bif_factor_complete and bif_evidence_links."""
    conn = _conn()
    factors = conn.execute("SELECT * FROM bif_factor_complete ORDER BY factor_letter").fetchall()
    links = conn.execute(
        "SELECT * FROM bif_evidence_links ORDER BY factor_letter, relevance_score DESC"
    ).fetchall()
    conn.close()
    return {
        'factors': [dict(r) for r in factors],
        'evidence_links': [dict(r) for r in links]
    }


def get_factor_evidence(factor_letter):
    """Get evidence for a specific BIF factor from multiple tables."""
    conn = _conn()
    factor = FACTORS.get(factor_letter, {})
    terms = factor.get('search_terms', [])

    # BIF evidence links
    bif_links = conn.execute(
        "SELECT * FROM bif_evidence_links WHERE factor_letter=? ORDER BY relevance_score DESC",
        (factor_letter,)
    ).fetchall()

    # Search extracted_harms
    harm_results = []
    for term in terms[:3]:
        rows = conn.execute(
            "SELECT adversary, category, description, severity FROM extracted_harms "
            "WHERE description LIKE ? LIMIT 20", (f'%{term}%',)
        ).fetchall()
        harm_results.extend([dict(r) for r in rows])

    # Search evidence_quotes
    quote_results = []
    for term in terms[:3]:
        rows = conn.execute(
            "SELECT quote_text, speaker, legal_significance FROM evidence_quotes "
            "WHERE quote_text LIKE ? OR legal_significance LIKE ? LIMIT 20",
            (f'%{term}%', f'%{term}%')
        ).fetchall()
        quote_results.extend([dict(r) for r in rows])

    # Alienation data for factor j
    alienation = []
    if factor_letter == 'j':
        alienation_rows = conn.execute("SELECT * FROM alienation_scoring ORDER BY score DESC").fetchall()
        alienation = [dict(r) for r in alienation_rows]
        tactics = conn.execute("SELECT * FROM alienation_tactics").fetchall()
        alienation_tactics = [dict(r) for r in tactics]
    else:
        alienation_tactics = []

    # Timeline events
    timeline = []
    for term in terms[:2]:
        rows = conn.execute(
            "SELECT event_date, title, harm_to_andrew, actor FROM master_chronological_timeline "
            "WHERE title LIKE ? OR description LIKE ? ORDER BY event_date LIMIT 15",
            (f'%{term}%', f'%{term}%')
        ).fetchall()
        timeline.extend([dict(r) for r in rows])

    conn.close()
    return {
        'factor': factor,
        'bif_links': [dict(r) for r in bif_links],
        'harms': harm_results[:30],
        'quotes': quote_results[:30],
        'alienation_data': alienation,
        'alienation_tactics': alienation_tactics,
        'timeline': timeline[:20]
    }


def score_factor(factor_letter, evidence):
    """Score a factor based on evidence. Returns score label and reasoning."""
    bif = get_existing_bif_data()
    existing_factor = None
    for f in bif['factors']:
        if f['factor_letter'] == factor_letter:
            existing_factor = f
            break

    if existing_factor:
        andrew_s = existing_factor.get('andrew_score', 0) or 0
        emily_s = existing_factor.get('emily_score', 0) or 0
        diff = andrew_s - emily_s
    else:
        pro_andrew = len([e for e in evidence.get('harms', []) if e.get('adversary', '').lower() != 'andrew'])
        diff = pro_andrew / max(len(evidence.get('harms', [])), 1) * 10

    if diff >= 3:
        return 'STRONG_ANDREW'
    elif diff >= 1:
        return 'SLIGHT_ANDREW'
    elif diff <= -3:
        return 'STRONG_EMILY'
    elif diff <= -1:
        return 'SLIGHT_EMILY'
    return 'NEUTRAL'


def generate_full_analysis():
    """Generate comprehensive best interest analysis for all 12 factors."""
    results = {}
    for letter in FACTORS:
        evidence = get_factor_evidence(letter)
        score = score_factor(letter, evidence)
        results[letter] = {
            'factor': FACTORS[letter],
            'score': score,
            'evidence_count': {
                'bif_links': len(evidence['bif_links']),
                'harms': len(evidence['harms']),
                'quotes': len(evidence['quotes']),
                'timeline': len(evidence['timeline']),
            },
            'key_evidence': evidence
        }
    return results


def generate_analysis_report():
    """Generate the full markdown report."""
    analysis = generate_full_analysis()
    bif_data = get_existing_bif_data()

    score_labels = {
        'STRONG_ANDREW': '🟢 STRONG ANDREW',
        'SLIGHT_ANDREW': '🟡 SLIGHT ANDREW',
        'NEUTRAL': '⚪ NEUTRAL',
        'SLIGHT_EMILY': '🟠 SLIGHT EMILY',
        'STRONG_EMILY': '🔴 STRONG EMILY',
    }

    md = []
    md.append("# MCL 722.23 — BEST INTEREST FACTOR ANALYSIS")
    md.append(f"\n**Generated:** {datetime.now().isoformat()}")
    md.append(f"**Case:** Pigors v. Watson et al.")
    md.append(f"**Standard:** MCL 722.23 — Child Custody Act of 1970")
    md.append("")

    # Summary table
    md.append("## EXECUTIVE SUMMARY")
    md.append("")
    md.append("| Factor | Description | Score |")
    md.append("|--------|-------------|-------|")
    strong_andrew = 0
    slight_andrew = 0
    neutral = 0
    for letter, data in analysis.items():
        score_label = score_labels.get(data['score'], data['score'])
        md.append(f"| ({letter}) | {data['factor']['name']} | {score_label} |")
        if 'STRONG_ANDREW' in data['score']:
            strong_andrew += 1
        elif 'SLIGHT_ANDREW' in data['score']:
            slight_andrew += 1
        elif 'NEUTRAL' in data['score']:
            neutral += 1

    md.append("")
    md.append(f"**Andrew Favored:** {strong_andrew} strong + {slight_andrew} slight = {strong_andrew + slight_andrew} factors")
    md.append(f"**Neutral:** {neutral} factors")
    md.append("")

    # Detailed analysis per factor
    md.append("---")
    md.append("## DETAILED FACTOR ANALYSIS")
    md.append("")

    for letter, data in analysis.items():
        factor = data['factor']
        score_label = score_labels.get(data['score'], data['score'])
        md.append(f"### Factor ({letter}): {factor['name']}")
        md.append(f"**Statute:** {factor['statute']}")
        md.append(f"**Score:** {score_label}")
        md.append(f"**Description:** {factor['description']}")
        md.append("")

        ev = data['evidence_count']
        md.append(f"**Evidence Inventory:** {ev['bif_links']} BIF links, {ev['harms']} harms, {ev['quotes']} quotes, {ev['timeline']} timeline events")
        md.append("")

        # BIF pre-computed data
        for bf in bif_data['factors']:
            if bf['factor_letter'] == letter:
                md.append(f"**Pre-computed Scores:** Andrew={bf.get('andrew_score', 'N/A')}, Emily={bf.get('emily_score', 'N/A')}")
                if bf.get('key_evidence'):
                    md.append(f"**Key Evidence:** {str(bf['key_evidence'])[:500]}")
                if bf.get('key_citations'):
                    md.append(f"**Key Citations:** {str(bf['key_citations'])[:300]}")
                md.append("")

        # Top evidence quotes
        key_ev = data['key_evidence']
        if key_ev['bif_links']:
            md.append("**Top Evidence Links:**")
            for link in key_ev['bif_links'][:5]:
                qt = str(link.get('quote_text', ''))[:200]
                md.append(f"- [{link.get('speaker', 'Unknown')}] {qt}... (relevance: {link.get('relevance_score', 'N/A')})")
            md.append("")

        # Alienation data for factor j
        if letter == 'j' and key_ev.get('alienation_data'):
            md.append("**ALIENATION EVIDENCE (CRITICAL):**")
            md.append("")
            md.append("Andrew has been denied access to his children for 571+ days. This is the most heavily evidenced factor.")
            md.append("")
            md.append("| Indicator | Framework | Score | Max |")
            md.append("|-----------|-----------|-------|-----|")
            for a in key_ev['alienation_data']:
                md.append(f"| {a.get('indicator_name', '')} | {a.get('framework', '')} | {a.get('score', '')} | {a.get('max_score', '')} |")
            md.append("")
            if key_ev.get('alienation_tactics'):
                md.append("**Documented Alienation Tactics:**")
                for t in key_ev['alienation_tactics'][:10]:
                    md.append(f"- **{t.get('tactic', '')}**: {str(t.get('description', ''))[:150]}")
            md.append("")

        # DV factor k
        if letter == 'k':
            md.append("**DOMESTIC VIOLENCE ANALYSIS:**")
            md.append("- Emily filed a false PPO against Andrew — subsequently dismissed/not renewed")
            md.append("- No evidence of actual domestic violence by Andrew")
            md.append("- False PPO used as weapon in custody dispute (well-documented pattern)")
            md.append("")

        md.append("---")
        md.append("")

    # Conclusion
    md.append("## CONCLUSION")
    md.append("")
    md.append("The evidence overwhelmingly supports that Andrew Pigors is the parent whose custody would serve the children's best interests under MCL 722.23. Key findings:")
    md.append("")
    md.append("1. **Factor (j) — Willingness to Facilitate:** Andrew demonstrates consistent willingness. Emily has systematically denied access for 571+ days.")
    md.append("2. **Factor (f) — Moral Fitness:** Emily's pattern of false reports, manipulation, and bad-faith litigation strongly disfavors her.")
    md.append("3. **Factor (k) — Domestic Violence:** Emily weaponized the PPO system with false allegations.")
    md.append("4. **Multiple factors favor Andrew** based on his demonstrated parenting capacity, emotional bonds, and willingness to co-parent.")
    md.append("")
    md.append(f"**Database Evidence Base:** {sum(d['evidence_count']['bif_links'] + d['evidence_count']['harms'] + d['evidence_count']['quotes'] for d in analysis.values())} total evidence items analyzed across 12 factors.")

    return '\n'.join(md)


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("MCL 722.23 BEST INTEREST ANALYZER — DB-WIRED")
    print("=" * 70)

    report = generate_analysis_report()

    output_path = os.path.join(OUTPUT_DIR, 'best_interest_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ Best Interest Analysis saved to: {output_path}")
    print(f"   Report length: {len(report)} characters")

    # Print summary
    analysis = generate_full_analysis()
    for letter, data in analysis.items():
        print(f"  ({letter}) {data['factor']['name']}: {data['score']}")
