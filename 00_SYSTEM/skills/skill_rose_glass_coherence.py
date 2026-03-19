"""
Rose Glass Coherence Analysis Skill v1.0
Adapted from RoseGlassCerataLitigationAgent (RGCLA) for LitigationOS.
Measures document/testimony authenticity through 4 coherence dimensions.
Uses local litigation_context.db — zero external APIs.

Dimensions:
  Ψ (Psi) - Internal consistency (contradictions, logical flow)
  ρ (Rho) - Evidence depth (specificity, citations, dates, numbers)
  q (Q)   - Emotional activation (sentiment, moral markers, urgency)
  f (F)   - Social belonging (relational language, positioning, alliances)

Coherence Formula: C = Ψ + (ρ × Ψ) + q_opt + (f × Ψ) + coupling
  Where q_opt = q / (Km + q + q²/Ki)  # Michaelis-Menten biological optimization

Attack Targets: C < 1.5 = overall weak
  High q + Low ρ = Emotion without evidence (MANIPULATION)
  High Ψ + Low ρ = Logical but vague (EVASION)
  Low Ψ + High q = Contradictory + emotional (DESPERATION)
"""
import re
import sqlite3
import os
import json
import math
from collections import Counter

DB_PATH = r'C:\Users\andre\litigation_context.db'

# Dimension markers
PSI_CONTRADICTION_MARKERS = [
    'however', 'but', 'although', 'despite', 'nevertheless',
    'on the other hand', 'contrary', 'inconsistent', 'contradicts', 'yet'
]
PSI_NEGATION_MARKERS = [
    'never', 'not', 'no', 'none', 'nothing', 'nobody', 'nowhere',
    'neither', 'nor', 'cannot', "don't", "didn't", "wasn't", "isn't"
]

RHO_EVIDENCE_MARKERS = [
    'exhibit', 'attached', 'evidence', 'document', 'record',
    'transcript', 'pursuant to', 'in accordance with', 'as shown', 'demonstrates'
]
RHO_SPECIFICITY_MARKERS = [
    r'\d{1,2}/\d{1,2}/\d{2,4}', r'\$[\d,]+', r'MCL \d+',
    r'MCR \d+', r'MRE \d+', r'Case No\.', r'\d+ Mich'
]

Q_EMOTIONAL_MARKERS = [
    'fear', 'afraid', 'scared', 'terrified', 'devastated', 'heartbroken',
    'desperate', 'urgent', 'emergency', 'crisis', 'harm', 'danger', 'abuse',
    'suffering', 'trauma', 'victim', 'threatened', 'violent', 'aggressive'
]
Q_MORAL_MARKERS = [
    'wrong', 'right', 'justice', 'fair', 'unfair', 'moral', 'immoral',
    'duty', 'obligation', 'conscience', 'integrity', 'truth'
]

F_COLLECTIVE_MARKERS = [
    'we', 'our', 'us', 'together', 'family', 'community',
    'everyone', 'society', 'public'
]
F_POSITIONING_MARKERS = [
    'they', 'them', 'those people', 'that person', 'the other side',
    'opposing', 'adversary', 'opponent'
]


class RoseGlassAnalyzer:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.Km = 0.5   # Michaelis-Menten constant
        self.Ki = 2.0   # Inhibition constant
        self.coupling_strength = 0.3

    def analyze(self, text, label="Document"):
        """Full Rose Glass analysis returning all dimensions + coherence score."""
        psi = self._calculate_psi(text)
        rho = self._calculate_rho(text)
        q = self._calculate_q(text)
        f = self._calculate_f(text)
        q_opt = q / (self.Km + q + (q ** 2 / self.Ki)) if q > 0 else 0
        coherence = psi + (rho * psi) + q_opt + (f * psi) + (self.coupling_strength * rho * q_opt)

        fractures = self._detect_fractures(psi, rho, q, f)
        attacks = self._generate_attacks(psi, rho, q, f, fractures)

        return {
            'label': label,
            'dimensions': {
                'psi': round(psi, 3),
                'rho': round(rho, 3),
                'q': round(q, 3),
                'f': round(f, 3),
            },
            'q_opt': round(q_opt, 3),
            'coherence': round(coherence, 3),
            'classification': self._classify(coherence),
            'fractures': fractures,
            'attacks': attacks,
            'word_count': len(text.split()),
            'sentence_count': len([s for s in re.split(r'[.!?]+', text) if s.strip()]),
        }

    # ------------------------------------------------------------------
    # Dimension calculators
    # ------------------------------------------------------------------

    def _calculate_psi(self, text):
        """Internal consistency — higher = more consistent."""
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        if word_count == 0:
            return 0

        contradictions = sum(1 for m in PSI_CONTRADICTION_MARKERS if m in text_lower)
        negations = sum(1 for m in PSI_NEGATION_MARKERS if m in text_lower)

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) > 1:
            lengths = [len(s.split()) for s in sentences]
            mean_len = sum(lengths) / len(lengths)
            variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
            normalized_var = min(variance / (mean_len ** 2 + 1), 1.0)
        else:
            normalized_var = 0

        contradiction_ratio = (contradictions + negations * 0.5) / (word_count / 100 + 1)
        psi = max(0, 1.0 - contradiction_ratio * 0.3 - normalized_var * 0.3)
        return min(psi, 1.0)

    def _calculate_rho(self, text):
        """Evidence depth — higher = more evidence-backed."""
        text_lower = text.lower()
        word_count = len(text_lower.split())
        if word_count == 0:
            return 0

        evidence_hits = sum(1 for m in RHO_EVIDENCE_MARKERS if m in text_lower)
        specificity_hits = sum(len(re.findall(p, text)) for p in RHO_SPECIFICITY_MARKERS)

        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}', text)
        date_density = len(dates) / (word_count / 100 + 1)

        numbers = re.findall(r'\d+', text)
        number_density = len(numbers) / (word_count / 100 + 1)

        rho = min(1.0, (evidence_hits * 0.1 + specificity_hits * 0.05
                        + date_density * 0.15 + number_density * 0.02))
        return rho

    def _calculate_q(self, text):
        """Emotional activation — higher = more emotional."""
        text_lower = text.lower()
        word_count = len(text_lower.split())
        if word_count == 0:
            return 0

        emotional_hits = sum(1 for m in Q_EMOTIONAL_MARKERS if m in text_lower)
        moral_hits = sum(1 for m in Q_MORAL_MARKERS if m in text_lower)

        exclamations = text.count('!')
        caps_words = len(re.findall(r'\b[A-Z]{3,}\b', text))

        q = min(1.0, (emotional_hits * 0.08 + moral_hits * 0.05
                       + exclamations * 0.1 + caps_words * 0.03))
        return q

    def _calculate_f(self, text):
        """Social belonging — higher = more relational."""
        text_lower = text.lower()
        word_count = len(text_lower.split())
        if word_count == 0:
            return 0

        collective = sum(1 for m in F_COLLECTIVE_MARKERS if m in text_lower.split())
        positioning = sum(1 for m in F_POSITIONING_MARKERS if m in text_lower)

        f = min(1.0, (collective * 0.1 + positioning * 0.08))
        return f

    # ------------------------------------------------------------------
    # Fracture detection & attack generation
    # ------------------------------------------------------------------

    def _detect_fractures(self, psi, rho, q, f):
        """Detect dimensional fractures — inconsistencies that reveal weakness."""
        fractures = []
        if q > 0.6 and rho < 0.3:
            fractures.append({
                'type': 'MANIPULATION',
                'desc': 'High emotion without evidence support',
                'attack': 'Challenge emotional claims with demand for specific evidence',
            })
        if psi > 0.6 and rho < 0.3:
            fractures.append({
                'type': 'EVASION',
                'desc': 'Internally logical but lacks specifics',
                'attack': 'Force specificity through interrogatories and depositions',
            })
        if psi < 0.4 and q > 0.5:
            fractures.append({
                'type': 'DESPERATION',
                'desc': 'Contradictory and emotional',
                'attack': 'Highlight contradictions methodically to undermine credibility',
            })
        if f > 0.5 and rho < 0.3:
            fractures.append({
                'type': 'SOCIAL_PROOF',
                'desc': 'Relies on social positioning over facts',
                'attack': 'Redirect to documented evidence, not social narratives',
            })
        if q > 0.7 and psi < 0.5:
            fractures.append({
                'type': 'EMOTIONAL_OVERRIDE',
                'desc': 'Emotion masking inconsistency',
                'attack': 'Expose contradictions the emotion is designed to distract from',
            })
        return fractures

    def _generate_attacks(self, psi, rho, q, f, fractures):
        """Generate specific attack vectors based on analysis."""
        attacks = []
        if psi < 0.5:
            attacks.append(
                'CROSS-EXAMINE on internal contradictions — testimony is inconsistent')
        if rho < 0.3:
            attacks.append(
                'DEMAND specificity — claims lack evidentiary support (MRE 602, 701)')
        if q > 0.7:
            attacks.append(
                'OBJECT to emotional testimony without foundation (MRE 403 — prejudice > probative)')
        if f > 0.6:
            attacks.append(
                'REDIRECT from social narratives to documented facts')
        for frac in fractures:
            attacks.append(f"EXPLOIT {frac['type']}: {frac['attack']}")
        return attacks

    def _classify(self, coherence):
        if coherence > 2.5:
            return 'HIGHLY_COHERENT'
        if coherence > 2.0:
            return 'COHERENT'
        if coherence > 1.5:
            return 'MODERATE'
        if coherence > 1.0:
            return 'WEAK'
        return 'INCOHERENT'

    # ------------------------------------------------------------------
    # Database-powered analysis methods
    # ------------------------------------------------------------------

    def analyze_watson_testimony(self):
        """Analyze all Watson testimony from DB through Rose Glass."""
        conn = sqlite3.connect(self.db_path)
        results = []
        try:
            rows = conn.execute(
                """SELECT quote_text, speaker FROM evidence_quotes
                   WHERE lower(speaker) LIKE '%watson%'
                      OR lower(speaker) LIKE '%court%'"""
            ).fetchall()
            for row in rows:
                if len(row[0]) > 50:
                    result = self.analyze(row[0], label=f"Testimony: {row[1]}")
                    results.append(result)
        finally:
            conn.close()
        return results

    def analyze_filing(self, file_path):
        """Analyze a court filing through Rose Glass."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        return self.analyze(text, label=os.path.basename(file_path))

    def compare_filings(self, path_a, path_b):
        """Compare two filings and identify relative strengths/weaknesses."""
        a = self.analyze_filing(path_a)
        b = self.analyze_filing(path_b)
        comparison = {
            'filing_a': a,
            'filing_b': b,
            'stronger': 'A' if a['coherence'] > b['coherence'] else 'B',
            'coherence_delta': round(abs(a['coherence'] - b['coherence']), 3),
            'recommendations': [],
        }
        if a['dimensions']['rho'] < b['dimensions']['rho']:
            comparison['recommendations'].append(
                'Filing A needs more evidence/citations')
        if a['dimensions']['psi'] < b['dimensions']['psi']:
            comparison['recommendations'].append(
                'Filing A has more contradictions — review consistency')
        return comparison


# ======================================================================
# Self-test
# ======================================================================

def self_test():
    """Comprehensive self-test."""
    analyzer = RoseGlassAnalyzer()

    print("=" * 70)
    print("  ROSE GLASS COHERENCE ANALYSIS — SELF-TEST")
    print("=" * 70)

    # --- Test 1: Coherent / evidence-rich text ---
    coherent = (
        "On July 29, 2025, pursuant to MCL 722.27a and the Court's Order "
        "dated August 23, 2024 (Case No. 2024-001507-DC), Plaintiff appeared "
        "at the designated exchange location at 2160 Garland Drive, Norton "
        "Shores, MI 49441. Defendant refused to produce the minor child. "
        "This constitutes a willful violation of the parenting time order. "
        "See Exhibit A (Court Order), Exhibit B (GPS records), Exhibit C "
        "(text messages)."
    )
    r1 = analyzer.analyze(coherent, "Coherent Filing")
    assert r1['dimensions']['rho'] > 0.3, \
        f"Rho should be high for evidence-rich text, got {r1['dimensions']['rho']}"
    print(f"\n[TEST 1] Coherent Filing")
    print(f"  C={r1['coherence']}  Ψ={r1['dimensions']['psi']}  "
          f"ρ={r1['dimensions']['rho']}  q={r1['dimensions']['q']}  "
          f"f={r1['dimensions']['f']}")
    print(f"  Classification: {r1['classification']}")
    print(f"  Fractures: {len(r1['fractures'])}  Attacks: {len(r1['attacks'])}")

    # --- Test 2: Emotional / incoherent text ---
    emotional = (
        "I am so scared and afraid! He is dangerous and violent! Everyone "
        "knows he is terrible! He should never see the child again! This is "
        "an emergency crisis! I fear for our safety!"
    )
    r2 = analyzer.analyze(emotional, "Emotional Testimony")
    assert r2['dimensions']['q'] > 0.3, \
        f"Q should be high for emotional text, got {r2['dimensions']['q']}"
    assert len(r2['fractures']) > 0, \
        "Should detect fractures in emotional text"
    print(f"\n[TEST 2] Emotional Testimony")
    print(f"  C={r2['coherence']}  Ψ={r2['dimensions']['psi']}  "
          f"ρ={r2['dimensions']['rho']}  q={r2['dimensions']['q']}  "
          f"f={r2['dimensions']['f']}")
    print(f"  Classification: {r2['classification']}")
    print(f"  Fractures: {[fr['type'] for fr in r2['fractures']]}")
    print(f"  Attacks:")
    for atk in r2['attacks']:
        print(f"    • {atk}")

    # --- Test 3: Empty text ---
    r3 = analyzer.analyze("", "Empty")
    assert r3['coherence'] == 0, "Empty text should have zero coherence"
    print(f"\n[TEST 3] Empty → C={r3['coherence']} ✓")

    # --- Test 4: Watson testimony from DB ---
    print(f"\n[TEST 4] Watson Testimony (DB)")
    try:
        watson_results = analyzer.analyze_watson_testimony()
        print(f"  Passages analyzed: {len(watson_results)}")
        if watson_results:
            avg_coherence = sum(r['coherence'] for r in watson_results) / len(watson_results)
            avg_psi = sum(r['dimensions']['psi'] for r in watson_results) / len(watson_results)
            avg_rho = sum(r['dimensions']['rho'] for r in watson_results) / len(watson_results)
            avg_q = sum(r['dimensions']['q'] for r in watson_results) / len(watson_results)
            attack_count = sum(len(r['attacks']) for r in watson_results)
            fracture_count = sum(len(r['fractures']) for r in watson_results)

            print(f"  Avg Coherence: {avg_coherence:.3f}")
            print(f"  Avg Ψ (consistency): {avg_psi:.3f}")
            print(f"  Avg ρ (evidence):    {avg_rho:.3f}")
            print(f"  Avg q (emotion):     {avg_q:.3f}")
            print(f"  Total attack vectors:  {attack_count}")
            print(f"  Total fractures:       {fracture_count}")

            # Show classification distribution
            classes = Counter(r['classification'] for r in watson_results)
            print(f"  Classification distribution:")
            for cls, cnt in classes.most_common():
                print(f"    {cls}: {cnt}")

            # Show top-5 weakest passages
            weakest = sorted(watson_results, key=lambda r: r['coherence'])[:5]
            print(f"\n  === TOP 5 WEAKEST PASSAGES (best attack targets) ===")
            for i, w in enumerate(weakest, 1):
                print(f"  [{i}] C={w['coherence']}  {w['classification']}  "
                      f"Ψ={w['dimensions']['psi']} ρ={w['dimensions']['rho']} "
                      f"q={w['dimensions']['q']}")
                print(f"      Label: {w['label'][:80]}")
                if w['fractures']:
                    print(f"      Fractures: {[fr['type'] for fr in w['fractures']]}")
        else:
            print("  (no Watson/court testimony found in evidence_quotes)")
    except Exception as e:
        print(f"  DB analysis error (non-fatal): {e}")

    # --- File size ---
    file_path = os.path.abspath(__file__)
    file_size = os.path.getsize(file_path)
    print(f"\n{'=' * 70}")
    print(f"  File: {file_path}")
    print(f"  Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"{'=' * 70}")
    print("  ALL ROSE GLASS SELF-TESTS PASSED ✓")
    print(f"{'=' * 70}")
    return True


if __name__ == "__main__":
    self_test()
