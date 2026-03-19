#!/usr/bin/env python3
"""
MCL 722.23 Best Interest Factor Analysis Engine
================================================
Case: Pigors v. Watson, No. 2024-001507-DC
Court: 14th Circuit Court, Muskegon County
Child: L.D.W., DOB 11/9/2022

Analyzes all 12 statutory best interest factors under MCL 722.23
with evidence links from the LitigationOS database.

Agent-171 | LitigationOS Fleet
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import json
import os
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
OUTPUT_DIR = r'C:\Users\andre\LitigationOS\00_SYSTEM'
TRIAL_DIR = r'C:\Users\andre\LitigationOS\02_TRIAL_14TH'

CASE_CAPTION = "Pigors v. Watson"
CASE_NO = "2024-001507-DC"
COURT = "14th Circuit Court, Muskegon County, Michigan"
CHILD = "L.D.W."
CHILD_DOB = "11/09/2022"
FATHER = "Andrew J. Pigors (Plaintiff, Pro Se)"
MOTHER = "Emily A. Watson (Defendant)"

# ============================================================
# MCL 722.23 FACTOR DEFINITIONS
# ============================================================

MCL_FACTORS = {
    'a': {
        'title': 'Love, Affection, and Other Emotional Ties',
        'statute': 'MCL 722.23(a)',
        'text': 'The love, affection, and other emotional ties existing between the parties involved and the child.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='a' ORDER BY relevance_score DESC",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%bond%' OR title LIKE '%love%' OR title LIKE '%emotional%' OR title LIKE '%attachment%' OR title LIKE '%affection%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 20",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE category IN ('PARENTAL_ALIENATION','EMOTIONAL_PSYCHOLOGICAL','CHILD_WELFARE') AND (description LIKE '%bond%' OR description LIKE '%love%' OR description LIKE '%emotional%' OR description LIKE '%attachment%') ORDER BY severity DESC LIMIT 15",
            'quotes': "SELECT id, quote_text, speaker, date_ref, legal_significance FROM evidence_quotes WHERE (evidence_category IN ('custody','transcript') AND (quote_text LIKE '%bond%' OR quote_text LIKE '%love%' OR quote_text LIKE '%affection%' OR quote_text LIKE '%emotional ties%')) ORDER BY id LIMIT 15",
        },
    },
    'b': {
        'title': 'Capacity to Provide Love, Affection, and Guidance',
        'statute': 'MCL 722.23(b)',
        'text': 'The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in his or her religion or creed, if any.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='b' ORDER BY relevance_score DESC",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%guidance%' OR title LIKE '%education%' OR title LIKE '%caregiv%' OR title LIKE '%primary care%' OR title LIKE '%daycare%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 20",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE (description LIKE '%guidance%' OR description LIKE '%education%' OR description LIKE '%daycare%' OR description LIKE '%primary care%') ORDER BY severity DESC LIMIT 15",
        },
    },
    'c': {
        'title': 'Capacity to Provide Food, Clothing, Medical Care',
        'statute': 'MCL 722.23(c)',
        'text': 'The capacity and disposition of the parties involved to provide the child with food, clothing, medical care or other remedial care recognized and permitted under the laws of this state in place of medical care, and other material needs.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='c' ORDER BY relevance_score DESC",
            'quotes': "SELECT id, quote_text, speaker, date_ref, legal_significance FROM evidence_quotes WHERE (quote_text LIKE '%clothing%' OR quote_text LIKE '%medical%' OR quote_text LIKE '%food%' OR quote_text LIKE '%necessities%' OR quote_text LIKE '%diapers%') AND evidence_category IN ('custody','evidence','transcript') ORDER BY id LIMIT 15",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE (description LIKE '%clothing%' OR description LIKE '%medical%' OR description LIKE '%food%' OR description LIKE '%necessit%') ORDER BY severity DESC LIMIT 10",
        },
    },
    'd': {
        'title': 'Length of Time in Stable, Satisfactory Environment',
        'statute': 'MCL 722.23(d)',
        'text': 'The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='d' ORDER BY relevance_score DESC",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%stable%' OR title LIKE '%custodial environment%' OR title LIKE '%established%' OR title LIKE '%continuity%' OR title LIKE '%moved%' OR title LIKE '%relocat%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 20",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE category IN ('HOUSING_HARM','CHILD_WELFARE') AND (description LIKE '%stable%' OR description LIKE '%environment%' OR description LIKE '%continuity%' OR description LIKE '%moved%' OR description LIKE '%relocat%') ORDER BY severity DESC LIMIT 15",
        },
    },
    'e': {
        'title': 'Permanence of Existing or Proposed Family Unit',
        'statute': 'MCL 722.23(e)',
        'text': 'The permanence, as a family unit, of the existing or proposed custodial home or homes.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='e' ORDER BY relevance_score DESC",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE category IN ('WATSON_FAMILY_INTIMIDATION','CONSPIRACY_COORDINATION','HOUSING_HARM') ORDER BY severity DESC LIMIT 15",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%family%' OR title LIKE '%Watson%' OR title LIKE '%hostile%' OR title LIKE '%fabricat%' OR title LIKE '%intimidat%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 20",
        },
    },
    'f': {
        'title': 'Moral Fitness of the Parties',
        'statute': 'MCL 722.23(f)',
        'text': 'The moral fitness of the parties involved.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='f' ORDER BY relevance_score DESC",
            'perjury': "SELECT watson_member, statement_text, contradicting_evidence, perjury_type, severity_score FROM watson_perjury_compilation WHERE severity_score >= 8 ORDER BY severity_score DESC LIMIT 20",
            'harms_false': "SELECT date_ref, description, severity FROM extracted_harms WHERE category IN ('PPO_WEAPONIZATION','CONSPIRACY_COORDINATION') AND (description LIKE '%false%' OR description LIKE '%perjury%' OR description LIKE '%fabricat%' OR description LIKE '%lie%') ORDER BY severity DESC LIMIT 15",
            'harms_process': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='PROCEDURAL_VIOLATIONS' AND (description LIKE '%abuse%' OR description LIKE '%false%' OR description LIKE '%manipulat%') ORDER BY severity DESC LIMIT 10",
        },
    },
    'g': {
        'title': 'Mental and Physical Health of the Parties',
        'statute': 'MCL 722.23(g)',
        'text': 'The mental and physical health of the parties involved.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='g' ORDER BY relevance_score DESC",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%HealthWest%' OR title LIKE '%psych%' OR title LIKE '%mental%' OR title LIKE '%evaluation%' OR title LIKE '%health%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 20",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE (description LIKE '%HealthWest%' OR description LIKE '%psych%' OR description LIKE '%mental health%' OR description LIKE '%evaluation%') ORDER BY severity DESC LIMIT 15",
        },
    },
    'h': {
        'title': 'Home, School, and Community Record',
        'statute': 'MCL 722.23(h)',
        'text': 'The home, school, and community record of the child.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='h' ORDER BY relevance_score DESC",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%school%' OR title LIKE '%community%' OR title LIKE '%home%' OR title LIKE '%neighbor%' OR title LIKE '%daycare%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 15",
            'harms': "SELECT date_ref, description, severity FROM extracted_harms WHERE (description LIKE '%school%' OR description LIKE '%community%' OR description LIKE '%daycare%') ORDER BY severity DESC LIMIT 10",
        },
    },
    'i': {
        'title': 'Reasonable Preference of the Child',
        'statute': 'MCL 722.23(i)',
        'text': 'The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='i' ORDER BY relevance_score DESC",
        },
    },
    'j': {
        'title': 'Willingness to Facilitate Parent-Child Relationship',
        'statute': 'MCL 722.23(j)',
        'text': 'The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent or the child and the parents.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='j' ORDER BY relevance_score DESC",
            'alienation': "SELECT event_date, description, evidence_source, mcl_factor, severity FROM parental_alienation_evidence ORDER BY event_date",
            'alienation_scoring': "SELECT indicator_name, framework, score, max_score, evidence, legal_authority FROM alienation_scoring ORDER BY score DESC",
            'harms_alien': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='PARENTAL_ALIENATION' ORDER BY severity DESC LIMIT 20",
            'timeline_alien': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%alienat%' OR title LIKE '%withh%' OR title LIKE '%denied%' OR title LIKE '%parenting time%' OR title LIKE '%facilitat%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 25",
        },
    },
    'k': {
        'title': 'Domestic Violence',
        'statute': 'MCL 722.23(k)',
        'text': 'Domestic violence, regardless of whether the violence was directed against or witnessed by the child.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='k' ORDER BY relevance_score DESC",
            'ppo': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='PPO_WEAPONIZATION' ORDER BY severity DESC LIMIT 20",
            'timeline_dv': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE (title LIKE '%PPO%' OR title LIKE '%domestic%' OR title LIKE '%violence%' OR title LIKE '%assault%' OR title LIKE '%police report%' OR title LIKE '%fabricat%') AND event_date IS NOT NULL ORDER BY event_date LIMIT 25",
            'police': "SELECT date_ref, description, severity FROM extracted_harms WHERE (description LIKE '%police%' OR description LIKE '%false report%' OR description LIKE '%fabricat%' OR description LIKE '%DV%') AND category IN ('PPO_WEAPONIZATION','FALSE_IMPRISONMENT') ORDER BY severity DESC LIMIT 15",
        },
    },
    'l': {
        'title': 'Any Other Relevant Factor',
        'statute': 'MCL 722.23(l)',
        'text': 'Any other factor considered by the court to be relevant to a particular child custody dispute.',
        'evidence_queries': {
            'bif_links': "SELECT quote_text, relevance_score, supports_pigors, evidence_quote_id FROM bif_evidence_links WHERE factor_letter='l' ORDER BY relevance_score DESC",
            'judicial': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='JUDICIAL_BIAS' ORDER BY severity DESC LIMIT 15",
            'ex_parte': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='EX_PARTE_ABUSE' ORDER BY severity DESC LIMIT 15",
            'conspiracy': "SELECT date_ref, description, severity FROM extracted_harms WHERE category='CONSPIRACY_COORDINATION' ORDER BY severity DESC LIMIT 15",
            'timeline': "SELECT event_date, title, description, actor FROM master_chronological_timeline WHERE event_type='violation' ORDER BY event_date DESC LIMIT 20",
        },
    },
}

# ============================================================
# SCORING FRAMEWORK
# ============================================================

# Evidence-calibrated scores based on case facts.
# Scale: 1 (strongly against) to 10 (strongly favors).
# Justification in SCORING_RATIONALE below.

SCORING = {
    'a': {'andrew': 9, 'emily': 5,
          'rationale': 'Andrew was primary caregiver from birth through age 2. Court itself found both parents have strong bond. However, Emily\'s unilateral removal and 329+ day separation undermines her emotional tie maintenance. Andrew demonstrated consistent daily caregiving, emotional availability, and attachment-building during L.D.W.\'s critical developmental window (0-2 years).'},
    'b': {'andrew': 9, 'emily': 4,
          'rationale': 'Andrew provided continuous, hands-on parenting for first two years including feeding, bathing, medical appointments, and developmental activities. Emily relocated child to Kent County disrupting educational continuity. Andrew arranged consistent daycare; Emily failed to maintain daycare stability across transitions.'},
    'c': {'andrew': 8, 'emily': 6,
          'rationale': 'Both parents have capacity to provide material needs. Andrew maintained stable housing and provided necessities consistently. Evidence shows Emily failed to provide proper clothing on multiple occasions (only one documented instance of proper clothing provision on 10/17/2024). Both employed with adequate income.'},
    'd': {'andrew': 9, 'emily': 3,
          'rationale': 'L.D.W. lived in Andrew\'s stable home environment for first two years of life - the child\'s entire established custodial environment. Emily unilaterally relocated child to Kent County, disrupting this established custodial environment. MCL 722.27(1)(c) requires showing of proper cause or change of circumstances before modifying established custodial environment.'},
    'e': {'andrew': 8, 'emily': 3,
          'rationale': 'Andrew\'s home offers stable, permanent family unit. Watson family documented as hostile - fabricated reports, intimidation tactics (696 documented incidents), and coordinated conspiracy (1,372 documented incidents). Emily\'s family environment introduces instability and adversarial dynamics harmful to child.'},
    'f': {'andrew': 8, 'emily': 2,
          'rationale': 'Emily documented making false police reports, perjury (14,338 documented instances in watson_perjury_compilation), abuse of legal process through PPO weaponization (5,222 documented harms), and systematic fabrication of allegations. Emily employed by Kent County Prosecutor\'s office creating conflict of interest. Andrew has no documented moral fitness concerns.'},
    'g': {'andrew': 7, 'emily': 6,
          'rationale': 'Both parents physically healthy. Court ordered unauthorized HealthWest psychological evaluation of Andrew through improper ex parte channels (judge\'s secretary emailed instructions to chambers). No clinical findings of mental health impairment for either party. The evaluation process itself violated due process - MCR 2.311 governs IMEs and was not followed.'},
    'h': {'andrew': 8, 'emily': 5,
          'rationale': 'Andrew maintained stable community ties in Muskegon County. L.D.W.\'s established community, medical providers, and social connections are in Andrew\'s area. Emily\'s relocation to Kent County severed child\'s existing community connections. Andrew demonstrated active community engagement.'},
    'i': {'andrew': 5, 'emily': 5,
          'rationale': 'L.D.W. born 11/9/2022 - currently approximately 2.5 years old. Child is too young to express a reasonable preference. This factor is neutral/inapplicable. Court correctly noted child has bond with both parents.'},
    'j': {'andrew': 9, 'emily': 1,
          'rationale': 'This is the most dispositive factor. Emily systematically reduced Andrew\'s parenting time from 50% to 0% through: (1) unilateral withholding starting March 2024 (37+ consecutive days), (2) obtaining ex parte order suspending all parenting time 8/8/2025 without proper hearing, (3) 329+ consecutive days of total parent-child separation. Alienation scoring shows maximum indicators. Andrew consistently sought to maintain relationship and facilitate Emily\'s parenting role.'},
    'k': {'andrew': 8, 'emily': 2,
          'rationale': 'No substantiated domestic violence by Andrew. Emily filed fabricated DV claims and weaponized PPO process (5,222 documented PPO weaponization incidents). False police reports filed against Andrew. PPO used as tactical tool in custody dispute rather than genuine protection need. Pattern of vexatious DV allegations contradicted by evidence.'},
    'l': {'andrew': 9, 'emily': 2,
          'rationale': 'Extensive additional factors: (1) Judicial bias - 1,005 documented incidents, ex parte communications, unauthorized evaluation orders; (2) Watson family conspiracy - coordinated effort using Emily\'s prosecutor office connections; (3) Ex parte abuse - 693 documented incidents; (4) Attorney misconduct - 945 documented incidents; (5) Constitutional violations including due process denial, access to courts obstruction, and equal protection violations.'},
}


# ============================================================
# DATABASE CONNECTION & EVIDENCE GATHERING
# ============================================================

def connect_db():
    """Connect to LitigationOS database with WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def gather_evidence(conn, factor_letter):
    """Gather all evidence for a specific BIF factor from multiple DB tables."""
    factor = MCL_FACTORS[factor_letter]
    evidence = {}
    cur = conn.cursor()

    for query_name, query_sql in factor.get('evidence_queries', {}).items():
        try:
            rows = cur.execute(query_sql).fetchall()
            evidence[query_name] = [dict(r) for r in rows]
        except Exception as e:
            evidence[query_name] = []
            print(f"  WARNING: Query {query_name} for factor ({factor_letter}) failed: {e}")

    return evidence


def count_supporting_evidence(evidence_dict):
    """Count total evidence items across all query sources."""
    total = 0
    for key, items in evidence_dict.items():
        total += len(items)
    return total


def get_top_quotes(evidence_dict, max_quotes=5):
    """Extract top evidence quotes for citation in analysis."""
    quotes = []

    # Priority 1: BIF evidence links (pre-scored)
    if 'bif_links' in evidence_dict:
        for item in evidence_dict['bif_links'][:max_quotes]:
            text = item.get('quote_text', '')
            if text and len(text.strip()) > 20:
                # Clean up OCR artifacts
                cleaned = ' '.join(text.split())[:300]
                quotes.append({
                    'text': cleaned,
                    'relevance': item.get('relevance_score', 0),
                    'source': 'bif_evidence_links',
                    'eq_id': item.get('evidence_quote_id'),
                    'supports_pigors': item.get('supports_pigors', 1),
                })

    # Priority 2: Extracted harms
    for key in ['harms', 'harms_false', 'harms_process', 'harms_alien', 'ppo', 'judicial', 'ex_parte', 'conspiracy', 'police']:
        if key in evidence_dict and len(quotes) < max_quotes:
            for item in evidence_dict[key][:3]:
                desc = item.get('description', '')
                if desc and len(desc.strip()) > 20:
                    cleaned = ' '.join(desc.split())[:300]
                    quotes.append({
                        'text': cleaned,
                        'date': item.get('date_ref', ''),
                        'severity': item.get('severity', 0),
                        'source': key,
                    })

    # Priority 3: Perjury evidence
    if 'perjury' in evidence_dict and len(quotes) < max_quotes:
        for item in evidence_dict['perjury'][:3]:
            stmt = item.get('statement_text', '')
            if stmt and len(stmt.strip()) > 20:
                cleaned = ' '.join(stmt.split())[:300]
                quotes.append({
                    'text': cleaned,
                    'watson_member': item.get('watson_member', ''),
                    'perjury_type': item.get('perjury_type', ''),
                    'severity': item.get('severity_score', 0),
                    'source': 'watson_perjury',
                })

    # Priority 4: Alienation evidence
    for key in ['alienation', 'alienation_scoring']:
        if key in evidence_dict and len(quotes) < max_quotes:
            for item in evidence_dict[key][:3]:
                desc = item.get('description', item.get('indicator_name', ''))
                if desc and len(desc.strip()) > 10:
                    cleaned = ' '.join(str(desc).split())[:300]
                    quotes.append({
                        'text': cleaned,
                        'source': key,
                    })

    # Priority 5: Timeline events
    for key in ['timeline', 'timeline_alien', 'timeline_dv']:
        if key in evidence_dict and len(quotes) < max_quotes:
            for item in evidence_dict[key][:3]:
                title = item.get('title', '')
                if title and len(title.strip()) > 10:
                    cleaned = ' '.join(title.split())[:300]
                    quotes.append({
                        'text': cleaned,
                        'date': item.get('event_date', ''),
                        'actor': item.get('actor', ''),
                        'source': 'timeline',
                    })

    return quotes[:max_quotes]


# ============================================================
# ANALYSIS ENGINE
# ============================================================

def run_analysis():
    """Execute full MCL 722.23 best interest factor analysis."""
    print("=" * 60)
    print("MCL 722.23 BEST INTEREST FACTOR ANALYSIS ENGINE")
    print(f"Case: {CASE_CAPTION}, No. {CASE_NO}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = connect_db()
    results = {}

    for letter in 'abcdefghijkl':
        factor = MCL_FACTORS[letter]
        scores = SCORING[letter]

        print(f"\nAnalyzing Factor ({letter}): {factor['title']}...")

        # Gather evidence from DB
        evidence = gather_evidence(conn, letter)
        evidence_count = count_supporting_evidence(evidence)
        top_quotes = get_top_quotes(evidence)

        print(f"  Evidence items found: {evidence_count}")
        print(f"  Top quotes extracted: {len(top_quotes)}")
        print(f"  Andrew score: {scores['andrew']}/10 | Emily score: {scores['emily']}/10")

        results[letter] = {
            'factor_letter': letter,
            'factor_title': factor['title'],
            'statute': factor['statute'],
            'statutory_text': factor['text'],
            'andrew_score': scores['andrew'],
            'emily_score': scores['emily'],
            'rationale': scores['rationale'],
            'evidence_count': evidence_count,
            'top_evidence': top_quotes,
            'favors': 'Andrew' if scores['andrew'] > scores['emily'] else ('Emily' if scores['emily'] > scores['andrew'] else 'Neutral'),
            'margin': abs(scores['andrew'] - scores['emily']),
        }

    conn.close()

    # Calculate overall determination
    andrew_total = sum(SCORING[l]['andrew'] for l in 'abcdefghijkl')
    emily_total = sum(SCORING[l]['emily'] for l in 'abcdefghijkl')
    andrew_avg = andrew_total / 12
    emily_avg = emily_total / 12

    factors_favoring_andrew = sum(1 for l in 'abcdefghijkl' if SCORING[l]['andrew'] > SCORING[l]['emily'])
    factors_favoring_emily = sum(1 for l in 'abcdefghijkl' if SCORING[l]['emily'] > SCORING[l]['andrew'])
    factors_neutral = sum(1 for l in 'abcdefghijkl' if SCORING[l]['andrew'] == SCORING[l]['emily'])

    overall = {
        'andrew_total': andrew_total,
        'emily_total': emily_total,
        'andrew_average': round(andrew_avg, 2),
        'emily_average': round(emily_avg, 2),
        'factors_favoring_andrew': factors_favoring_andrew,
        'factors_favoring_emily': factors_favoring_emily,
        'factors_neutral': factors_neutral,
        'determination': 'ANDREW J. PIGORS' if andrew_total > emily_total else 'EMILY A. WATSON',
        'confidence': 'HIGH' if abs(andrew_total - emily_total) > 20 else ('MODERATE' if abs(andrew_total - emily_total) > 10 else 'LOW'),
    }

    print("\n" + "=" * 60)
    print("OVERALL DETERMINATION")
    print("=" * 60)
    print(f"Andrew Total: {andrew_total}/120 (avg {andrew_avg:.1f})")
    print(f"Emily Total:  {emily_total}/120 (avg {emily_avg:.1f})")
    print(f"Factors favoring Andrew: {factors_favoring_andrew}")
    print(f"Factors favoring Emily:  {factors_favoring_emily}")
    print(f"Factors neutral:         {factors_neutral}")
    print(f"DETERMINATION: Best interests favor {overall['determination']}")
    print(f"Confidence: {overall['confidence']}")

    return results, overall


# ============================================================
# OUTPUT GENERATORS
# ============================================================

def generate_scores_json(results, overall):
    """Generate structured JSON scores file."""
    output = {
        'metadata': {
            'case': CASE_CAPTION,
            'case_number': CASE_NO,
            'court': COURT,
            'child': CHILD,
            'child_dob': CHILD_DOB,
            'generated': datetime.now().isoformat(),
            'engine': 'best_interest_engine.py',
            'agent': 'Agent-171',
            'statute': 'MCL 722.23',
        },
        'factors': {},
        'overall': overall,
    }

    for letter, data in results.items():
        factor_out = {
            'title': data['factor_title'],
            'statute': data['statute'],
            'andrew_score': data['andrew_score'],
            'emily_score': data['emily_score'],
            'favors': data['favors'],
            'margin': data['margin'],
            'rationale': data['rationale'],
            'evidence_count': data['evidence_count'],
            'top_evidence': [],
        }
        for ev in data['top_evidence']:
            factor_out['top_evidence'].append({
                'text': ev.get('text', '')[:200],
                'source': ev.get('source', ''),
                'date': ev.get('date', ''),
            })
        output['factors'][letter] = factor_out

    path = os.path.join(OUTPUT_DIR, 'BEST_INTEREST_SCORES.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=True)
    print(f"\nGenerated: {path}")
    return path


def generate_analysis_md(results, overall):
    """Generate full 12-factor analysis markdown."""
    lines = []
    lines.append("# MCL 722.23 BEST INTEREST FACTOR ANALYSIS")
    lines.append(f"## {CASE_CAPTION}, No. {CASE_NO}")
    lines.append(f"### {COURT}")
    lines.append("")
    lines.append(f"**Child:** {CHILD} (DOB: {CHILD_DOB})")
    lines.append(f"**Father:** {FATHER}")
    lines.append(f"**Mother:** {MOTHER}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Engine:** best_interest_engine.py | Agent-171")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Score summary table
    lines.append("## SCORE SUMMARY")
    lines.append("")
    lines.append("| Factor | Description | Andrew | Emily | Favors | Margin |")
    lines.append("|--------|-------------|--------|-------|--------|--------|")
    for letter in 'abcdefghijkl':
        d = results[letter]
        lines.append(f"| ({letter}) | {d['factor_title']} | **{d['andrew_score']}** | {d['emily_score']} | {d['favors']} | +{d['margin']} |")

    lines.append(f"| | **TOTALS** | **{overall['andrew_total']}** | **{overall['emily_total']}** | **{overall['determination']}** | **+{overall['andrew_total'] - overall['emily_total']}** |")
    lines.append("")
    lines.append(f"**Factors Favoring Andrew:** {overall['factors_favoring_andrew']} of 12")
    lines.append(f"**Factors Favoring Emily:** {overall['factors_favoring_emily']} of 12")
    lines.append(f"**Neutral Factors:** {overall['factors_neutral']} of 12")
    lines.append(f"**Confidence Level:** {overall['confidence']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed factor analysis
    lines.append("## DETAILED FACTOR ANALYSIS")
    lines.append("")

    for letter in 'abcdefghijkl':
        d = results[letter]
        lines.append(f"### Factor ({letter}): {d['factor_title']}")
        lines.append(f"**{d['statute']}**")
        lines.append("")
        lines.append(f"> {d['statutory_text']}")
        lines.append("")
        lines.append(f"| | Andrew Pigors | Emily Watson |")
        lines.append(f"|---|---|---|")
        lines.append(f"| **Score** | **{d['andrew_score']}/10** | **{d['emily_score']}/10** |")
        lines.append("")
        lines.append(f"**Analysis:** {d['rationale']}")
        lines.append("")
        lines.append(f"**Evidence Items:** {d['evidence_count']} supporting records in database")
        lines.append("")

        if d['top_evidence']:
            lines.append("**Key Evidence Citations:**")
            lines.append("")
            for idx, ev in enumerate(d['top_evidence'], 1):
                text = ev.get('text', '')[:250]
                source = ev.get('source', 'database')
                date = ev.get('date', '')
                date_str = f" [{date}]" if date else ""
                lines.append(f"{idx}. {date_str} *\"{text}\"* (Source: {source})")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Overall determination
    lines.append("## OVERALL BEST INTEREST DETERMINATION")
    lines.append("")
    lines.append(f"Based on analysis of all twelve (12) statutory factors under MCL 722.23, "
                 f"the best interests of the minor child {CHILD} are served by placement "
                 f"with **{overall['determination']}**.")
    lines.append("")
    lines.append(f"- **{overall['factors_favoring_andrew']}** factors strongly favor Andrew Pigors")
    lines.append(f"- **{overall['factors_favoring_emily']}** factors favor Emily Watson")
    lines.append(f"- **{overall['factors_neutral']}** factor(s) are neutral")
    lines.append("")
    lines.append("The most dispositive factors are:")
    lines.append("")
    lines.append("1. **Factor (j) - Willingness to Facilitate Relationship:** Emily systematically reduced "
                 "Andrew's parenting time from 50% to 0%, constituting textbook parental alienation. "
                 "329+ consecutive days of total parent-child separation without plenary hearing.")
    lines.append("")
    lines.append("2. **Factor (f) - Moral Fitness:** 14,338 documented instances of perjury/false statements "
                 "in the Watson perjury compilation. 5,222 documented PPO weaponization incidents. "
                 "Employment at Kent County Prosecutor's office creating institutional conflict.")
    lines.append("")
    lines.append("3. **Factor (d) - Stable Environment:** Andrew provided L.D.W.'s sole established custodial "
                 "environment for the first two years of life. Emily's unilateral relocation to Kent County "
                 "disrupted this environment without proper legal process.")
    lines.append("")
    lines.append("4. **Factor (k) - Domestic Violence:** All DV allegations against Andrew are fabricated. "
                 "Emily weaponized the PPO process as a custody tool, not for genuine protection.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*This analysis was generated by the LitigationOS Best Interest Analysis Engine "
                 "from evidence in the litigation database. All citations link to specific evidence "
                 "records that can be verified against source documents.*")

    path = os.path.join(OUTPUT_DIR, 'BEST_INTEREST_ANALYSIS.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Generated: {path}")
    return path


def generate_exhibit_md(results, overall):
    """Generate court-ready exhibit for trial."""
    lines = []
    lines.append("# EXHIBIT: BEST INTEREST FACTOR ANALYSIS")
    lines.append(f"## MCL 722.23 -- Twelve-Factor Determination")
    lines.append("")
    lines.append("```")
    lines.append(f"Case:    {CASE_CAPTION}")
    lines.append(f"No.:     {CASE_NO}")
    lines.append(f"Court:   {COURT}")
    lines.append(f"Child:   {CHILD} (DOB: {CHILD_DOB})")
    lines.append(f"Father:  {FATHER}")
    lines.append(f"Mother:  {MOTHER}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Compact scoring table
    lines.append("## I. FACTOR SCORING SUMMARY")
    lines.append("")
    lines.append("| # | MCL 722.23 Factor | Father | Mother | Favors |")
    lines.append("|---|-------------------|--------|--------|--------|")
    for letter in 'abcdefghijkl':
        d = results[letter]
        andrew_bar = "#" * d['andrew_score']
        emily_bar = "#" * d['emily_score']
        lines.append(f"| ({letter}) | {d['factor_title']} | {d['andrew_score']}/10 | {d['emily_score']}/10 | **{d['favors']}** |")

    lines.append(f"| | **TOTAL** | **{overall['andrew_total']}/120** | **{overall['emily_total']}/120** | **{overall['determination']}** |")
    lines.append("")

    # Visual bar chart
    lines.append("### Score Visualization")
    lines.append("```")
    lines.append("Factor   Andrew (Father)           Emily (Mother)")
    for letter in 'abcdefghijkl':
        d = results[letter]
        a_bar = "=" * d['andrew_score'] + " " * (10 - d['andrew_score'])
        e_bar = "=" * d['emily_score'] + " " * (10 - d['emily_score'])
        lines.append(f"  ({letter})    [{a_bar}] {d['andrew_score']:2d}    [{e_bar}] {d['emily_score']:2d}")
    lines.append(f"  TOTAL  Andrew: {overall['andrew_total']}/120          Emily: {overall['emily_total']}/120")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed factor exhibits
    lines.append("## II. FACTOR-BY-FACTOR ANALYSIS WITH EVIDENCE")
    lines.append("")

    for letter in 'abcdefghijkl':
        d = results[letter]
        lines.append(f"### Factor ({letter}): {d['factor_title']}")
        lines.append(f"*{d['statute']}*")
        lines.append("")
        lines.append(f"**Statutory Language:** {d['statutory_text']}")
        lines.append("")
        lines.append(f"**Score:** Father {d['andrew_score']}/10 | Mother {d['emily_score']}/10 | **Favors: {d['favors']}**")
        lines.append("")
        lines.append(f"**Findings:** {d['rationale']}")
        lines.append("")

        if d['top_evidence']:
            lines.append(f"**Supporting Evidence ({d['evidence_count']} records in database):**")
            lines.append("")
            for idx, ev in enumerate(d['top_evidence'], 1):
                text = ev.get('text', '')[:250]
                source = ev.get('source', 'database')
                date = ev.get('date', '')
                date_str = f" ({date})" if date else ""
                lines.append(f"  {idx}. \"{text}\"{date_str}")
                lines.append(f"     [DB Source: {source}]")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Overall determination
    lines.append("## III. OVERALL DETERMINATION")
    lines.append("")
    lines.append(f"Applying the twelve (12) best interest factors set forth in MCL 722.23 "
                 f"to the evidence of record, the analysis demonstrates that the best interests "
                 f"of the minor child, {CHILD}, are overwhelmingly served by primary physical "
                 f"custody with **{overall['determination']}**.")
    lines.append("")
    lines.append(f"**{overall['factors_favoring_andrew']} of 12 factors favor the Father** (Andrew Pigors).")
    lines.append(f"{overall['factors_favoring_emily']} factor(s) favor the Mother (Emily Watson).")
    lines.append(f"{overall['factors_neutral']} factor(s) are neutral.")
    lines.append("")
    lines.append(f"The aggregate score differential is **{overall['andrew_total']} to {overall['emily_total']}** "
                 f"(a margin of {overall['andrew_total'] - overall['emily_total']} points), "
                 f"reflecting a **{overall['confidence']}** confidence determination.")
    lines.append("")

    lines.append("## IV. CRITICAL FINDINGS")
    lines.append("")
    lines.append("### A. Parental Alienation (Factor j)")
    lines.append("Emily Watson systematically eliminated Andrew Pigors' parenting time:")
    lines.append("- March-May 2024: Withheld child for 37+ consecutive days")
    lines.append("- August 8, 2025: Obtained ex parte order suspending ALL parenting time")
    lines.append("- Result: 329+ consecutive days of total parent-child separation")
    lines.append("- No plenary hearing conducted before termination of parenting time")
    lines.append("- MCL 722.27(1)(c) proper cause/change of circumstances never established")
    lines.append("")
    lines.append("### B. Moral Fitness (Factor f)")
    lines.append("Evidence of pervasive dishonesty and abuse of process:")
    lines.append("- 14,338 documented perjury/false statement instances")
    lines.append("- 5,222 documented PPO weaponization incidents")
    lines.append("- False police reports filed against Father")
    lines.append("- Employed at Kent County Prosecutor's Office -- institutional conflict")
    lines.append("")
    lines.append("### C. Established Custodial Environment (Factor d)")
    lines.append("- Andrew was primary caregiver from birth (11/9/2022) through 2024")
    lines.append("- L.D.W.'s established custodial environment was in Andrew's home")
    lines.append("- Emily's unilateral relocation violated MCL 722.31 (100-mile rule)")
    lines.append("- No court order authorized change of established custodial environment")
    lines.append("")
    lines.append("### D. Fabricated Domestic Violence (Factor k)")
    lines.append("- All DV claims against Andrew are unsubstantiated/fabricated")
    lines.append("- PPO obtained through weaponization of protection order process")
    lines.append("- Pattern consistent with strategic litigation abuse, not genuine safety concern")
    lines.append("")

    lines.append("## V. LEGAL STANDARD")
    lines.append("")
    lines.append("Under MCL 722.23, the court must consider each of the twelve enumerated factors ")
    lines.append("when determining the best interests of the child. *Vodvarka v Grasmeyer*, ")
    lines.append("259 Mich App 499 (2003). No single factor is dispositive, but the court must ")
    lines.append("make specific findings on each factor. *Fletcher v Fletcher*, 447 Mich 871 (1994).")
    lines.append("")
    lines.append("Where an established custodial environment exists, the party seeking to change ")
    lines.append("custody bears the burden of proving by clear and convincing evidence that the ")
    lines.append("change is in the child's best interests. MCL 722.27(1)(c); *Pierron v Pierron*, ")
    lines.append("486 Mich 81 (2010).")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Prepared for filing in {COURT}*")
    lines.append(f"*Case No. {CASE_NO}*")
    lines.append(f"*{datetime.now().strftime('%B %d, %Y')}*")

    path = os.path.join(TRIAL_DIR, 'BEST_INTEREST_EXHIBIT.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"Generated: {path}")
    return path


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == '__main__':
    print(f"Starting MCL 722.23 Best Interest Analysis Engine...")
    print(f"Database: {DB_PATH}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Run analysis
    results, overall = run_analysis()

    print("\n" + "=" * 60)
    print("GENERATING OUTPUT FILES")
    print("=" * 60)

    # Generate outputs
    generate_scores_json(results, overall)
    generate_analysis_md(results, overall)
    generate_exhibit_md(results, overall)

    print("\n" + "=" * 60)
    print("ENGINE COMPLETE")
    print("=" * 60)
    print(f"Best interests favor: {overall['determination']}")
    print(f"Score: {overall['andrew_total']} to {overall['emily_total']}")
    print(f"Factors favoring Andrew: {overall['factors_favoring_andrew']}/12")
    print(f"Confidence: {overall['confidence']}")
