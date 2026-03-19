"""
skill_chess_mode.py — Chess Mode Anticipator
==============================================
LitigationOS 2026 v1.0 — Pigors v. Watson

For every claim we make, predict what the opponent will argue
and pre-build the counter:

  OUR_CLAIM → THEIR_DEFENSE → OUR_COUNTER → THEIR_REPLY → OUR_FINAL

Integrates with:
  - skill_landlord_tenant (housing authority)
  - skill_business_corporate (veil piercing / corporate liability)
  - skill_torts_claims (tort elements)
  - skill_defenses_setoffs (defenses and counters)

Queries adversary_models, auth_rules, evidence_quotes, impeachment_items,
and other tables in litigation_context.db.

No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import json
import os
import sys
from typing import Optional, Dict, List, Any

DB_PATH = r"C:\Users\andre\litigation_context.db"

# Add parent to path for sibling skill imports
_SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# ── Chess Move Templates ───────────────────────────────────────────────────

CHESS_CHAINS = {
    "conversion": {
        "our_claim": "Conversion of personal property — MCL 600.2919a (treble damages)",
        "their_defenses": [
            {
                "defense": "Property was abandoned",
                "our_counter": "Abandonment requires CLEAR, UNEQUIVOCAL intent to relinquish — "
                               "Byker v Mannes, 465 Mich 637 (2002). Mere absence ≠ abandonment. "
                               "Property remained in leased premises.",
                "their_reply": "Tenant left no forwarding address / stopped paying rent",
                "our_final": "Non-payment is separate from property rights. Landlord must follow "
                             "MCL 554.601+ procedures. No notice of intent to dispose was given. "
                             "Statutory non-compliance = per se conversion.",
            },
            {
                "defense": "Items had no value / de minimis damages",
                "our_counter": "Value is determined by fair market value OR replacement cost — "
                               "plaintiff's testimony on value is competent evidence. "
                               "MCL 600.2919a provides TREBLE damages regardless of amount.",
                "their_reply": "Plaintiff inflated values",
                "our_final": "Burden is on defendant to rebut. Plaintiff's itemized list with "
                             "documentation (receipts, photos) is competent. Treble damages apply "
                             "to whatever amount the factfinder determines.",
            },
        ],
    },
    "retaliatory_eviction": {
        "our_claim": "Retaliatory eviction — MCL 600.5720 (90-day presumption)",
        "their_defenses": [
            {
                "defense": "Eviction was for non-payment, not retaliation",
                "our_counter": "MCL 600.5720 creates REBUTTABLE PRESUMPTION when eviction follows "
                               "protected activity within 90 days. Non-payment was caused by "
                               "landlord's breach — rent withholding is a recognized remedy under MCL 554.139.",
                "their_reply": "Tenant has no right to withhold rent unilaterally",
                "our_final": "Michigan recognizes rent withholding as a remedy for habitability "
                             "violations. Tenant gave notice of defects. Landlord failed to repair. "
                             "MCL 554.139 duties are NON-WAIVABLE. Also: MCL 125.2319 provides "
                             "additional mobile home park retaliation protection.",
            },
        ],
    },
    "warranty_habitability": {
        "our_claim": "Breach of warranty of habitability — MCL 554.139 (non-waivable)",
        "their_defenses": [
            {
                "defense": "Tenant caused the conditions / comparative fault",
                "our_counter": "MCL 554.139 duties are NON-DELEGABLE. Landlord cannot shift duty "
                               "to maintain habitability to tenant. MCL 600.2959: comparative fault "
                               "does NOT apply to statutory duty claims.",
                "their_reply": "Tenant failed to report conditions / delayed reporting",
                "our_final": "Landlord had constructive notice through inspections and is deemed "
                             "to know conditions of own property. Building code violations are "
                             "per se notice. Failure to inspect is itself negligence.",
            },
            {
                "defense": "Tenant waived habitability through lease clause",
                "our_counter": "MCL 554.139(2): 'A covenant or agreement by or on behalf of a "
                               "tenant waiving the provisions of this section is VOID.' — End of analysis.",
                "their_reply": "Tenant accepted property in as-is condition",
                "our_final": "As-is acceptance does not waive ongoing duty to maintain. "
                             "MCL 554.139(1)(b) requires premises be kept in reasonable repair "
                             "DURING the lease term. Acceptance of initial condition is irrelevant "
                             "to ongoing maintenance duty.",
            },
        ],
    },
    "mcpa": {
        "our_claim": "MCPA violation — MCL 445.903 (treble damages + attorney fees)",
        "their_defenses": [
            {
                "defense": "Transaction was not 'trade or commerce'",
                "our_counter": "Rental of residential property IS trade or commerce. "
                               "Landlord is engaged in the business of renting property for profit. "
                               "MCL 445.902(1)(g) defines trade or commerce broadly.",
                "their_reply": "Small-scale landlord is not a 'business'",
                "our_final": "Size is irrelevant. Operating rental property for profit = trade or commerce. "
                             "Even a single rental unit operated for profit satisfies the statute. "
                             "Zine v Chrysler Corp, 236 Mich App 261 (1999).",
            },
        ],
    },
    "iied": {
        "our_claim": "IIED — *Roberts v Auto-Owners*, 422 Mich 594 (1985)",
        "their_defenses": [
            {
                "defense": "Conduct was not 'extreme and outrageous'",
                "our_counter": "Pattern of illegal entries, threats, utility disruptions, property "
                               "destruction, and retaliatory eviction collectively constitute conduct "
                               "'beyond all bounds of decency.' Roberts threshold met through cumulative "
                               "pattern, not isolated incidents.",
                "their_reply": "Each individual act is not extreme enough",
                "our_final": "Courts evaluate PATTERN of conduct, not just individual acts. "
                             "Cumulative harassment by person in position of power (landlord) over "
                             "vulnerable tenant = extreme and outrageous. "
                             "Graham v Ford, 237 Mich App 670 (1999).",
            },
        ],
    },
    "illegal_entry": {
        "our_claim": "Illegal entry / violation of quiet enjoyment — 24hr notice required",
        "their_defenses": [
            {
                "defense": "Entry was emergency maintenance",
                "our_counter": "Emergency exception requires IMMINENT danger to life or property. "
                               "No emergency documentation produced. No work orders generated. "
                               "Pattern of 'emergency' entries is pretextual.",
                "their_reply": "Water leak / gas leak / safety hazard required immediate action",
                "our_final": "Demand: (1) written emergency report, (2) work order, (3) repair invoice, "
                             "(4) photos of emergency condition. Absence of documentation = pretextual entry. "
                             "Multiple 'emergencies' without documentation = harassment pattern.",
            },
        ],
    },
    "veil_piercing": {
        "our_claim": "Corporate veil piercing — *Foodland Distributors v Al-Naimi*, 220 Mich App 453 (1996)",
        "their_defenses": [
            {
                "defense": "Corporate form was properly maintained",
                "our_counter": "Evidence shows: commingled funds, no corporate formalities, "
                               "undercapitalization, entity used as personal shell. "
                               "Instrumentality element satisfied.",
                "their_reply": "Some corporate records exist / entity filed annual reports",
                "our_final": "Filing annual reports alone is insufficient. Substantive formalities "
                             "matter: separate bank accounts, board meetings, arm's-length transactions. "
                             "Single factor (e.g., commingling) can be dispositive when combined "
                             "with fraud/wrong (element 2).",
            },
        ],
    },
    "mobile_home_violations": {
        "our_claim": "Mobile Home Commission Act violations — MCL 125.2301-2349",
        "their_defenses": [
            {
                "defense": "Park rules authorized the actions taken",
                "our_counter": "MCL 125.2307: Park rules must be FAIR and REASONABLE. "
                               "Unreasonable rules are unenforceable. Rules that violate "
                               "statutory tenant protections are void.",
                "their_reply": "Tenant agreed to park rules in lease",
                "our_final": "Agreement to unlawful rules is void. MHCA rights are statutory "
                             "and cannot be waived by contract. MCL 125.2312a limits eviction "
                             "to ENUMERATED grounds — rules cannot expand them.",
            },
        ],
    },
}


def _connect_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db with retry."""
    for attempt in range(3):
        try:
            if not os.path.exists(DB_PATH):
                return None
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error:
            if attempt < 2:
                continue
            return None
    return None


def _query_adversary_models(conn: sqlite3.Connection, claim_type: str) -> List[Dict]:
    """Query adversary_models table for anticipated attacks."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM adversary_models "
            "WHERE attack_description LIKE ? OR weakness_exploited LIKE ? "
            "OR rebuttal_strategy LIKE ? LIMIT 10",
            (f"%{claim_type}%", f"%{claim_type}%", f"%{claim_type}%")
        )
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        return []


def _query_impeachment(conn: sqlite3.Connection, claim_type: str) -> List[Dict]:
    """Query impeachment_items for cross-examination material."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM impeachment_items "
            "WHERE statement LIKE ? OR contradicting_text LIKE ? "
            "OR legal_hook LIKE ? LIMIT 10",
            (f"%{claim_type}%", f"%{claim_type}%", f"%{claim_type}%")
        )
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        return []


def _query_evidence(conn: sqlite3.Connection, claim_type: str) -> List[Dict]:
    """Query evidence_quotes for supporting evidence."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT quote_text, speaker, legal_significance, evidence_category "
            "FROM evidence_quotes "
            "WHERE quote_text LIKE ? OR legal_significance LIKE ? "
            "OR evidence_category LIKE ? LIMIT 10",
            (f"%{claim_type}%", f"%{claim_type}%", f"%{claim_type}%")
        )
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        return []


def _query_contradictions(conn: sqlite3.Connection, claim_type: str) -> List[Dict]:
    """Query contradiction_map for exploitable contradictions."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM contradiction_map "
            "WHERE source_a_text LIKE ? OR source_b_text LIKE ? "
            "OR contradiction_type LIKE ? LIMIT 10",
            (f"%{claim_type}%", f"%{claim_type}%", f"%{claim_type}%")
        )
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        return []


def anticipate_defenses(claim: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    For a given claim and facts, anticipate all defenses the opponent will raise.

    This is the primary Chess Mode function — maps:
    OUR_CLAIM → THEIR_DEFENSE → OUR_COUNTER → THEIR_REPLY → OUR_FINAL

    Args:
        claim: The claim type (e.g., 'conversion', 'iied', 'retaliatory_eviction')
        facts: Dict of relevant facts for the claim.

    Returns:
        Dict with full chess chain, DB intelligence, and strategic recommendations.
    """
    claim_lower = claim.lower().replace(" ", "_")

    result = {
        "claim": claim,
        "facts_provided": facts,
        "chess_chain": None,
        "adversary_models": [],
        "impeachment_material": [],
        "supporting_evidence": [],
        "contradictions": [],
        "strategic_recommendation": "",
    }

    # Get chess chain
    chain = CHESS_CHAINS.get(claim_lower)
    if not chain:
        # Fuzzy match
        for key, c in CHESS_CHAINS.items():
            if claim_lower in key or key in claim_lower:
                chain = c
                break

    result["chess_chain"] = chain if chain else {
        "note": f"No pre-built chain for '{claim}'. Building from defenses skill.",
        "suggestion": "Use get_defenses_for_claim() from skill_defenses_setoffs.py",
    }

    # Enrich from DB
    conn = _connect_db()
    if conn:
        try:
            result["adversary_models"] = _query_adversary_models(conn, claim)
            result["impeachment_material"] = _query_impeachment(conn, claim)
            result["supporting_evidence"] = _query_evidence(conn, claim)
            result["contradictions"] = _query_contradictions(conn, claim)
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    # Strategic recommendation
    evidence_count = len(result["supporting_evidence"])
    impeach_count = len(result["impeachment_material"])
    contradiction_count = len(result["contradictions"])

    if evidence_count >= 3 and chain:
        result["strategic_recommendation"] = (
            f"STRONG POSITION: {evidence_count} supporting evidence items found. "
            f"Chess chain is pre-built with {len(chain.get('their_defenses', []))} "
            f"anticipated defense paths. Recommend filing."
        )
    elif chain:
        result["strategic_recommendation"] = (
            f"MODERATE POSITION: Chess chain available but only {evidence_count} "
            f"evidence items found. Strengthen evidence base before filing. "
            f"Focus on gathering documentation for weakest counter-arguments."
        )
    else:
        result["strategic_recommendation"] = (
            f"DEVELOPING: No pre-built chess chain. Use skill_defenses_setoffs.py "
            f"to map defenses. Evidence items: {evidence_count}. "
            f"Build the attack/defense chain before filing."
        )

    if impeach_count > 0:
        result["strategic_recommendation"] += (
            f" BONUS: {impeach_count} impeachment items available for cross-examination."
        )
    if contradiction_count > 0:
        result["strategic_recommendation"] += (
            f" EXPLOIT: {contradiction_count} contradictions in opponent's positions."
        )

    return result


def build_counter_chain(claim_type: str) -> Dict[str, Any]:
    """
    Build the full 5-move chess chain for a claim type.

    Move 1: OUR_CLAIM (with authority)
    Move 2: THEIR_DEFENSE (anticipated)
    Move 3: OUR_COUNTER (with authority)
    Move 4: THEIR_REPLY (anticipated escalation)
    Move 5: OUR_FINAL (closing argument)

    Args:
        claim_type: The claim type to build the chain for.

    Returns:
        Dict with the full 5-move chain and supporting materials.
    """
    claim_lower = claim_type.lower().replace(" ", "_")
    chain = CHESS_CHAINS.get(claim_lower)

    if not chain:
        for key, c in CHESS_CHAINS.items():
            if claim_lower in key or key in claim_lower:
                chain = c
                break

    if not chain:
        return {
            "error": f"No chess chain for '{claim_type}'",
            "available_chains": list(CHESS_CHAINS.keys()),
        }

    formatted_chains = []
    for i, defense_path in enumerate(chain.get("their_defenses", []), 1):
        formatted_chains.append({
            "path_number": i,
            "move_1_our_claim": chain["our_claim"],
            "move_2_their_defense": defense_path["defense"],
            "move_3_our_counter": defense_path["our_counter"],
            "move_4_their_reply": defense_path["their_reply"],
            "move_5_our_final": defense_path["our_final"],
        })

    result = {
        "claim_type": claim_type,
        "total_defense_paths": len(formatted_chains),
        "chains": formatted_chains,
    }

    # DB enrichment
    conn = _connect_db()
    if conn:
        try:
            result["adversary_intelligence"] = _query_adversary_models(conn, claim_type)
            result["available_impeachment"] = _query_impeachment(conn, claim_type)
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def get_full_chess_analysis(filing_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full Chess Mode analysis on a filing / set of claims.

    Takes a dict describing the filing and its claims, then produces a
    comprehensive attack/defense analysis for EACH claim.

    Args:
        filing_dict: Dict with at minimum:
            - "claims": List of claim types (e.g., ["conversion", "iied", "mcpa"])
            - "facts": Dict of relevant facts (optional)
            - "defendant": Defendant name (optional)

    Returns:
        Dict with per-claim chess analysis, cross-claim synergies, and overall score.
    """
    claims = filing_dict.get("claims", [])
    facts = filing_dict.get("facts", {})
    defendant = filing_dict.get("defendant", "Unknown")

    result = {
        "filing_summary": {
            "defendant": defendant,
            "claim_count": len(claims),
            "claims": claims,
        },
        "per_claim_analysis": {},
        "cross_claim_synergies": [],
        "overall_assessment": "",
        "overall_score": 0,
    }

    total_score = 0
    for claim in claims:
        chain = build_counter_chain(claim)
        defense_analysis = anticipate_defenses(claim, facts)

        claim_score = 50  # Base score
        if chain.get("chains"):
            claim_score += 20  # Has chess chain
        if defense_analysis.get("supporting_evidence"):
            claim_score += len(defense_analysis["supporting_evidence"]) * 5
        if defense_analysis.get("impeachment_material"):
            claim_score += len(defense_analysis["impeachment_material"]) * 10
        if defense_analysis.get("contradictions"):
            claim_score += len(defense_analysis["contradictions"]) * 8

        claim_score = min(claim_score, 100)
        total_score += claim_score

        result["per_claim_analysis"][claim] = {
            "chess_chain": chain,
            "defense_anticipation": defense_analysis,
            "claim_strength_score": claim_score,
        }

    # Cross-claim synergies
    if "conversion" in claims and "mcpa" in claims:
        result["cross_claim_synergies"].append({
            "claims": ["conversion", "mcpa"],
            "synergy": "Both provide treble damages. File BOTH — if one fails, the other provides "
                       "the treble multiplier. MCPA also awards attorney fees (MCL 445.911).",
        })
    if "warranty_habitability" in claims and "negligence_per_se" in claims:
        result["cross_claim_synergies"].append({
            "claims": ["warranty_habitability", "negligence_per_se"],
            "synergy": "MCL 554.139 violation = negligence per se. Habitability breach automatically "
                       "establishes the duty and breach elements of negligence.",
        })
    if "retaliatory_eviction" in claims and "iied" in claims:
        result["cross_claim_synergies"].append({
            "claims": ["retaliatory_eviction", "iied"],
            "synergy": "Pattern of retaliation supports IIED 'extreme and outrageous' threshold. "
                       "Each strengthens the other.",
        })
    if "veil_piercing" in claims:
        result["cross_claim_synergies"].append({
            "claims": ["veil_piercing", "ALL_OTHER_CLAIMS"],
            "synergy": "If veil is pierced, ALL claims attach to the individual behind the entity. "
                       "This is the force multiplier — file veil piercing alongside every substantive claim.",
        })

    avg_score = total_score / len(claims) if claims else 0
    result["overall_score"] = round(avg_score)

    if avg_score >= 75:
        result["overall_assessment"] = (
            f"STRONG FILING: Average claim strength {avg_score:.0f}/100. "
            f"Multiple claims with pre-built defense chains. Recommend filing."
        )
    elif avg_score >= 50:
        result["overall_assessment"] = (
            f"MODERATE FILING: Average claim strength {avg_score:.0f}/100. "
            f"Some claims need evidence strengthening. Address gaps before filing."
        )
    else:
        result["overall_assessment"] = (
            f"DEVELOPING: Average claim strength {avg_score:.0f}/100. "
            f"Significant evidence gaps. Continue investigation before filing."
        )

    return result


def score_claim_strength(claim: str, evidence_list: List[str]) -> Dict[str, Any]:
    """
    Score the strength of a specific claim based on available evidence.

    Evaluates: (1) elements coverage, (2) authority support, (3) evidence quality,
    (4) defense vulnerability, (5) damages potential.

    Args:
        claim: The claim type (e.g., 'conversion', 'iied', 'mcpa')
        evidence_list: List of evidence descriptions / summaries.

    Returns:
        Dict with scored breakdown and overall strength assessment.
    """
    claim_lower = claim.lower().replace(" ", "_")

    scoring = {
        "claim": claim,
        "evidence_count": len(evidence_list),
        "scores": {
            "elements_coverage": 0,
            "authority_support": 0,
            "evidence_quality": 0,
            "defense_vulnerability": 0,
            "damages_potential": 0,
        },
        "max_per_category": 20,
        "total_score": 0,
        "max_total": 100,
        "strength_rating": "",
        "recommendations": [],
    }

    # Elements coverage — do we have a chess chain?
    chain = CHESS_CHAINS.get(claim_lower)
    if chain:
        scoring["scores"]["elements_coverage"] = 15
        if len(chain.get("their_defenses", [])) >= 2:
            scoring["scores"]["elements_coverage"] = 20

    # Authority support — check DB
    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM master_citations WHERE context LIKE ?",
                (f"%{claim}%",)
            )
            cite_count = cur.fetchone()[0]
            scoring["scores"]["authority_support"] = min(20, cite_count * 2)

            # Evidence quality
            evidence = _query_evidence(conn, claim)
            scoring["scores"]["evidence_quality"] = min(20, len(evidence) * 4)

            # Defense vulnerability — check adversary_models
            adversary = _query_adversary_models(conn, claim)
            if adversary:
                # If we have adversary intel, we can prepare — higher score
                scoring["scores"]["defense_vulnerability"] = min(20, 10 + len(adversary) * 3)
            else:
                scoring["scores"]["defense_vulnerability"] = 10  # Unknown = moderate

        except sqlite3.Error:
            pass
        finally:
            conn.close()

    # Damages potential based on claim type
    treble_claims = {"conversion", "mcpa"}
    if claim_lower in treble_claims:
        scoring["scores"]["damages_potential"] = 20
    elif claim_lower in {"iied", "warranty_habitability", "nuisance"}:
        scoring["scores"]["damages_potential"] = 15
    else:
        scoring["scores"]["damages_potential"] = 10

    # Evidence list bonus
    evidence_bonus = min(10, len(evidence_list) * 2)
    scoring["scores"]["evidence_quality"] = min(20, scoring["scores"]["evidence_quality"] + evidence_bonus)

    # Calculate total
    total = sum(scoring["scores"].values())
    scoring["total_score"] = total

    if total >= 80:
        scoring["strength_rating"] = "STRONG — Ready to file"
    elif total >= 60:
        scoring["strength_rating"] = "MODERATE — Needs some strengthening"
    elif total >= 40:
        scoring["strength_rating"] = "DEVELOPING — Significant gaps remain"
    else:
        scoring["strength_rating"] = "WEAK — Major evidence/authority gaps"

    # Recommendations
    for category, score in scoring["scores"].items():
        if score < 10:
            scoring["recommendations"].append(
                f"CRITICAL GAP in {category} (score: {score}/20) — address before filing"
            )
        elif score < 15:
            scoring["recommendations"].append(
                f"Improve {category} (score: {score}/20) — gather additional support"
            )

    return scoring


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("skill_chess_mode.py — Self-Test (Chess Mode Anticipator)")
    print("=" * 70)

    print("\n[1] anticipate_defenses('conversion', {'property': 'personal belongings'}):")
    r = anticipate_defenses("conversion", {"property": "personal belongings"})
    print(json.dumps({
        "has_chain": r["chess_chain"] is not None,
        "adversary_models": len(r["adversary_models"]),
        "evidence": len(r["supporting_evidence"]),
        "strategy": r["strategic_recommendation"][:120] if r["strategic_recommendation"] else "N/A",
    }, indent=2))

    print("\n[2] build_counter_chain('retaliatory_eviction'):")
    cc = build_counter_chain("retaliatory_eviction")
    print(json.dumps({
        "paths": cc.get("total_defense_paths", 0),
        "first_move": cc["chains"][0]["move_1_our_claim"][:80] if cc.get("chains") else "N/A",
    }, indent=2))

    print("\n[3] get_full_chess_analysis():")
    filing = {
        "claims": ["conversion", "mcpa", "warranty_habitability", "iied"],
        "defendant": "Shady Oaks / Watson",
        "facts": {"property_destroyed": True, "habitability_violations": True},
    }
    full = get_full_chess_analysis(filing)
    print(json.dumps({
        "claims_analyzed": list(full["per_claim_analysis"].keys()),
        "synergies": len(full["cross_claim_synergies"]),
        "overall_score": full["overall_score"],
        "assessment": full["overall_assessment"][:120],
    }, indent=2))

    print("\n[4] score_claim_strength('conversion', ['photos of items', 'receipts', 'witness statement']):")
    sc = score_claim_strength("conversion", ["photos of items", "receipts", "witness statement"])
    print(json.dumps({
        "total_score": f"{sc['total_score']}/{sc['max_total']}",
        "strength": sc["strength_rating"],
        "scores": sc["scores"],
        "recommendations": sc["recommendations"][:3],
    }, indent=2))

    print("\n✓ All self-tests completed.")
