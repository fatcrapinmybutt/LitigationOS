"""
skill_defenses_setoffs.py — Michigan Defenses & Setoffs Skill
==============================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Anticipate and counter opposing defenses:
  - Statute of limitations: MCL 600.5805 et seq
  - Laches, estoppel, waiver
  - Comparative fault: MCL 600.2957-2959
  - Failure to mitigate damages
  - Setoff / recoupment
  - Governmental immunity
  - Exhaustion of administrative remedies
  - "Emergency maintenance" defense to illegal entry
  - "Abandonment" defense to conversion
  - "Non-payment" defense to retaliatory eviction

Queries litigation_context.db for Michigan-specific authorities.
No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Statute of Limitations Reference (MCL 600.5805 et seq) ─────────────────

SOL_TABLE = {
    "conversion": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — injury to person or property",
    },
    "trespass": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — trespass to land or chattels",
    },
    "negligence": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — negligence causing injury to person or property",
    },
    "negligence_per_se": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — statutory violation causing injury",
    },
    "iied": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — intentional infliction of emotional distress",
    },
    "mcpa": {
        "period_years": 6,
        "authority": "MCL 445.911(7)",
        "description": "6 years — Michigan Consumer Protection Act claims",
    },
    "breach_of_contract": {
        "period_years": 6,
        "authority": "MCL 600.5807(8)",
        "description": "6 years — contract actions",
    },
    "warranty_habitability": {
        "period_years": 6,
        "authority": "MCL 600.5807(8) (statutory); MCL 600.5805(2) (tort theory)",
        "description": "6 years if contract theory; 3 years if tort theory",
    },
    "fraud": {
        "period_years": 6,
        "authority": "MCL 600.5813",
        "description": "6 years — fraud or deceit; discovery rule applies",
    },
    "nuisance": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — nuisance claims",
    },
    "premises_liability": {
        "period_years": 3,
        "authority": "MCL 600.5805(2)",
        "description": "3 years — premises liability / personal injury",
    },
    "security_deposit": {
        "period_years": 6,
        "authority": "MCL 600.5807(8) via MCL 554.601+",
        "description": "6 years — Security Deposit Act violations (statutory)",
    },
}

# ── Common Defenses and Counter-Arguments ───────────────────────────────────

DEFENSES = {
    "statute_of_limitations": {
        "defense": "Claim is time-barred under applicable statute of limitations",
        "authority": "MCL 600.5805 et seq",
        "counters": [
            "Discovery rule: SOL does not begin until plaintiff discovers or should have discovered the claim — "
            "MCL 600.5827; Trentadue v Buckler Lawn Sprinkler, 479 Mich 378 (2007)",
            "Continuing wrong doctrine: each new violation restarts the clock",
            "Fraudulent concealment tolls the SOL — MCL 600.5855",
            "Equitable tolling where defendant's conduct prevented timely filing",
            "Minority or disability tolling — MCL 600.5851",
        ],
    },
    "laches": {
        "defense": "Plaintiff unreasonably delayed in asserting rights, causing prejudice to defendant",
        "authority": "Equity — Gallagher v Keefe, 232 Mich App 363 (1998)",
        "counters": [
            "Laches requires BOTH unreasonable delay AND prejudice to defendant",
            "Delay was reasonable given ongoing attempts to resolve informally",
            "Defendant suffered no actual prejudice from the timing",
            "Laches does not apply where legal SOL has not expired",
            "Defendant's own wrongful conduct caused the delay",
        ],
    },
    "estoppel": {
        "defense": "Plaintiff is estopped from asserting claim due to prior conduct or representations",
        "authority": "Equity — Baar v Tighe, 184 Mich App 29 (1990)",
        "counters": [
            "Estoppel requires: (1) party's wrongful conduct or representation, (2) inducing reliance, "
            "(3) detrimental change of position by relying party",
            "No representation was made that could be relied upon",
            "No detrimental reliance by defendant",
            "Estoppel cannot shield illegal conduct",
        ],
    },
    "waiver": {
        "defense": "Plaintiff waived rights through conduct or agreement",
        "authority": "Quality Products & Concepts Co v Nagel Precision, 469 Mich 362 (2003)",
        "counters": [
            "Waiver requires intentional relinquishment of a KNOWN right",
            "MCL 554.139(2) rights are NON-WAIVABLE — any agreement to waive is VOID",
            "No knowing and voluntary waiver occurred",
            "Rights protected by statute cannot be waived by conduct",
            "Unconscionable lease provisions are void — MCL 554.139(2)",
        ],
    },
    "comparative_fault": {
        "defense": "Plaintiff's own negligence contributed to damages",
        "authority": "MCL 600.2957-2959 (Modified Comparative Fault)",
        "counters": [
            "Michigan uses MODIFIED comparative fault — plaintiff recovers if less than 50% at fault",
            "MCL 600.2959: fault is NOT a defense to intentional torts",
            "Comparative fault does NOT apply to: conversion, IIED, MCPA, or other intentional claims",
            "Even if some negligence exists, damages reduced proportionally, NOT eliminated",
            "Landlord's statutory duties (MCL 554.139) are non-delegable — tenant fault irrelevant",
        ],
    },
    "failure_to_mitigate": {
        "defense": "Plaintiff failed to mitigate damages",
        "authority": "Lawrence v Will Darrah & Assocs, 445 Mich 1 (1994)",
        "counters": [
            "Mitigation only requires REASONABLE efforts — not extraordinary measures",
            "Plaintiff made all reasonable efforts to mitigate (document specifics)",
            "Defendant's ongoing conduct prevented effective mitigation",
            "Burden is on DEFENDANT to prove failure to mitigate and amount of avoidable damages",
            "Financial inability to mitigate is a valid excuse",
        ],
    },
    "setoff_recoupment": {
        "defense": "Defendant entitled to offset plaintiff's recovery by amounts owed to defendant",
        "authority": "MCR 2.203(B) — compulsory counterclaims",
        "counters": [
            "Setoff requires valid, liquidated claim by defendant against plaintiff",
            "Any claimed setoff must be proven by defendant — burden is on them",
            "Disputed amounts cannot be set off until adjudicated",
            "Illegal charges cannot form basis of setoff",
            "Treble damages are not subject to setoff of underlying amount",
        ],
    },
    "emergency_maintenance": {
        "defense": "Entry was justified as emergency maintenance to prevent imminent harm",
        "authority": "Common Law — emergency exception to notice requirement",
        "counters": [
            "Emergency must be IMMINENT danger to life or property — not routine maintenance",
            "Landlord bears burden of proving actual emergency existed",
            "Repeated 'emergency' entries suggest pretextual excuse for harassment",
            "No written emergency report was generated (should have been if genuine)",
            "Entry occurred at unreasonable hours — inconsistent with genuine emergency",
            "No follow-up repair documentation — undermines emergency claim",
        ],
    },
    "abandonment": {
        "defense": "Tenant abandoned property, so taking/disposing was lawful",
        "authority": "Common Law — Byker v Mannes, 465 Mich 637 (2002)",
        "counters": [
            "Abandonment requires CLEAR, UNEQUIVOCAL intent to relinquish ownership",
            "Mere absence from premises ≠ abandonment of personal property",
            "Landlord must follow MCL 554.601+ procedures before disposing of property",
            "Property was in leased premises — tenant's right to possession continued",
            "No notice of intent to dispose was given as required",
        ],
    },
    "non_payment": {
        "defense": "Eviction was for non-payment of rent, not retaliation",
        "authority": "MCL 600.5714(1)(a)",
        "counters": [
            "MCL 600.5720: 90-day presumption of retaliation if eviction follows protected activity",
            "Non-payment was caused by landlord's breach (rent withholding is a remedy for habitability violations)",
            "Rent withholding is a recognized remedy under MCL 554.139",
            "Timing of non-payment claim coincides suspiciously with protected activity",
            "Landlord accepted partial payments — waived strict compliance",
            "MCL 125.2312a limits eviction grounds for mobile homes — non-payment must be proven",
        ],
    },
    "governmental_immunity": {
        "defense": "Defendant is immune from suit under governmental immunity act",
        "authority": "MCL 691.1401 et seq (Governmental Tort Liability Act)",
        "counters": [
            "Governmental immunity does not apply to PRIVATE parties (landlords, corporations)",
            "Exceptions: highway, motor vehicle, public building, proprietary function",
            "Gross negligence exception — MCL 691.1407(2)",
            "Intentional torts are NOT protected by governmental immunity",
            "If applicable, identify specific exception that applies",
        ],
    },
    "exhaustion_of_remedies": {
        "defense": "Plaintiff failed to exhaust administrative remedies before filing suit",
        "authority": "Calhoun Co v Blue Cross Blue Shield, 297 Mich App 1 (2012)",
        "counters": [
            "Exhaustion not required when administrative remedy is inadequate or futile",
            "Exhaustion not required for constitutional claims",
            "Exhaustion not required when agency lacks authority to grant requested relief",
            "Administrative complaint WAS filed (document if applicable)",
            "Exhaustion doctrine does not apply to this claim type",
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


def _fts_query(conn: sqlite3.Connection, fts_table: str, base_table: str,
               term: str, limit: int = 15) -> List[Dict]:
    """FTS5 search with LIKE fallback."""
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT ?", (term, limit))
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        try:
            cur = conn.cursor()
            like = f"%{term.split()[0]}%"
            if base_table == "auth_rules":
                cur.execute(f"SELECT * FROM {base_table} WHERE full_text LIKE ? OR title LIKE ? LIMIT ?",
                            (like, like, limit))
            elif base_table == "rules_text":
                cur.execute(f"SELECT * FROM {base_table} WHERE context LIKE ? OR rule LIKE ? LIMIT ?",
                            (like, like, limit))
            else:
                return []
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            return []


def get_defenses_for_claim(claim_type: str) -> Dict[str, Any]:
    """
    Get all likely defenses the opponent will raise for a given claim type,
    along with pre-built counter-arguments.

    Args:
        claim_type: Type of claim (e.g., 'conversion', 'iied', 'mcpa',
                    'warranty_habitability', 'retaliatory_eviction')

    Returns:
        Dict with applicable defenses, counter-arguments, and DB authority.
    """
    claim_lower = claim_type.lower().replace(" ", "_")

    # Map claim types to likely defenses
    claim_defense_map = {
        "conversion": [
            "statute_of_limitations", "abandonment", "comparative_fault",
            "failure_to_mitigate", "setoff_recoupment",
        ],
        "trespass": [
            "statute_of_limitations", "emergency_maintenance", "waiver",
        ],
        "iied": [
            "statute_of_limitations", "comparative_fault", "failure_to_mitigate",
        ],
        "mcpa": [
            "statute_of_limitations", "failure_to_mitigate", "exhaustion_of_remedies",
        ],
        "negligence": [
            "statute_of_limitations", "comparative_fault", "failure_to_mitigate",
        ],
        "negligence_per_se": [
            "statute_of_limitations", "comparative_fault",
        ],
        "warranty_habitability": [
            "statute_of_limitations", "waiver", "failure_to_mitigate",
            "comparative_fault",
        ],
        "retaliatory_eviction": [
            "non_payment", "statute_of_limitations",
        ],
        "nuisance": [
            "statute_of_limitations", "laches", "failure_to_mitigate", "comparative_fault",
        ],
        "premises_liability": [
            "statute_of_limitations", "comparative_fault", "failure_to_mitigate",
        ],
        "security_deposit": [
            "statute_of_limitations", "setoff_recoupment", "abandonment",
        ],
        "breach_of_contract": [
            "statute_of_limitations", "waiver", "estoppel", "failure_to_mitigate",
            "setoff_recoupment",
        ],
        "illegal_entry": [
            "emergency_maintenance", "waiver", "laches",
        ],
    }

    applicable_keys = claim_defense_map.get(claim_lower, list(DEFENSES.keys()))
    applicable_defenses = {}
    for key in applicable_keys:
        if key in DEFENSES:
            applicable_defenses[key] = DEFENSES[key]

    result = {
        "claim_type": claim_type,
        "applicable_defenses": applicable_defenses,
        "sol_info": SOL_TABLE.get(claim_lower, {"note": "SOL not mapped — check MCL 600.5805 et seq"}),
        "db_authority": [],
    }

    # Enrich from DB
    conn = _connect_db()
    if conn:
        try:
            result["db_authority"] = _fts_query(
                conn, "auth_rules_fts", "auth_rules",
                f"{claim_type} OR defense OR limitation", 10
            )

            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE context LIKE ? OR citation LIKE ? LIMIT 15",
                (f"%{claim_type}%", f"%{claim_type}%")
            )
            result["db_citations"] = [dict(row) for row in cur.fetchall()]

            # Check adversary_models table
            cur.execute(
                "SELECT * FROM adversary_models "
                "WHERE attack_description LIKE ? OR weakness_exploited LIKE ? LIMIT 10",
                (f"%{claim_type}%", f"%{claim_type}%")
            )
            adversary = [dict(row) for row in cur.fetchall()]
            if adversary:
                result["adversary_models"] = adversary

        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def build_counter_arguments(defense_type: str) -> Dict[str, Any]:
    """
    Build detailed counter-arguments for a specific defense.

    Args:
        defense_type: The defense to counter (e.g., 'statute_of_limitations',
                      'emergency_maintenance', 'abandonment')

    Returns:
        Dict with the defense, counter-arguments, and supporting authority.
    """
    defense_lower = defense_type.lower().replace(" ", "_")

    defense = DEFENSES.get(defense_lower)
    if not defense:
        # Fuzzy match
        for key, d in DEFENSES.items():
            if defense_lower in key or key in defense_lower:
                defense = d
                defense_lower = key
                break

    if not defense:
        return {
            "error": f"Defense type '{defense_type}' not found",
            "available_defenses": list(DEFENSES.keys()),
        }

    result = {
        "defense_type": defense_lower,
        "their_argument": defense["defense"],
        "their_authority": defense["authority"],
        "our_counter_arguments": defense["counters"],
        "recommended_strategy": "",
        "db_authority": [],
    }

    # Strategy recommendation
    if defense_lower == "statute_of_limitations":
        result["recommended_strategy"] = (
            "Lead with discovery rule and continuing wrong doctrine. "
            "If the violation is ongoing, each new instance creates a new SOL period. "
            "Also check for fraudulent concealment tolling — MCL 600.5855."
        )
    elif defense_lower == "emergency_maintenance":
        result["recommended_strategy"] = (
            "Demand documentation of the alleged emergency. Genuine emergencies produce "
            "repair records, work orders, and incident reports. Absence of documentation "
            "= pretextual entry. Pattern of 'emergencies' = harassment."
        )
    elif defense_lower == "abandonment":
        result["recommended_strategy"] = (
            "Abandonment requires CLEAR, UNEQUIVOCAL intent. Show any evidence of "
            "continuing possessory interest: rent payments, personal items on premises, "
            "communication about the property. One piece of evidence defeats this defense."
        )
    elif defense_lower == "non_payment":
        result["recommended_strategy"] = (
            "Rent withholding is a RECOGNIZED REMEDY for habitability violations under "
            "MCL 554.139. If non-payment was caused by landlord's breach, it is not "
            "a valid basis for eviction. Also invoke MCL 600.5720 presumption."
        )
    else:
        result["recommended_strategy"] = (
            f"Attack all elements of the defense — they must prove EVERY element. "
            f"Focus on the weakest element and build your argument there."
        )

    # DB enrichment
    conn = _connect_db()
    if conn:
        try:
            result["db_authority"] = _fts_query(
                conn, "auth_rules_fts", "auth_rules", defense_type, 10
            )
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def get_sol_for_claim(claim_type: str) -> Dict[str, Any]:
    """
    Return the statute of limitations for a specific claim type.

    Per MCL 600.5805 et seq — Michigan's general limitations statute.

    Args:
        claim_type: The claim type (e.g., 'conversion', 'iied', 'mcpa', 'fraud')

    Returns:
        Dict with SOL period, authority, and tolling doctrines.
    """
    claim_lower = claim_type.lower().replace(" ", "_")
    sol = SOL_TABLE.get(claim_lower)

    if not sol:
        # Fuzzy match
        for key, s in SOL_TABLE.items():
            if claim_lower in key or key in claim_lower:
                sol = s
                claim_lower = key
                break

    result = {
        "claim_type": claim_type,
        "sol": sol if sol else {"error": "Not found", "note": "Check MCL 600.5805-5813"},
        "tolling_doctrines": [
            {
                "doctrine": "Discovery Rule",
                "authority": "MCL 600.5827; Trentadue v Buckler Lawn Sprinkler, 479 Mich 378 (2007)",
                "effect": "SOL begins when plaintiff discovers or should have discovered the claim",
            },
            {
                "doctrine": "Fraudulent Concealment",
                "authority": "MCL 600.5855",
                "effect": "SOL tolled if defendant concealed the cause of action",
            },
            {
                "doctrine": "Continuing Wrong",
                "authority": "Common Law — each new violation restarts the clock",
                "effect": "Ongoing violations create new SOL periods for each occurrence",
            },
            {
                "doctrine": "Minority/Disability",
                "authority": "MCL 600.5851",
                "effect": "SOL tolled during minority or legal disability",
            },
            {
                "doctrine": "Equitable Tolling",
                "authority": "Equity — defendant's conduct prevented timely filing",
                "effect": "SOL tolled when defendant actively prevents suit",
            },
        ],
    }

    return result


def check_sol_expired(claim_type: str, incident_date: str) -> Dict[str, Any]:
    """
    Check if the statute of limitations has expired for a specific claim.

    Args:
        claim_type: The claim type (e.g., 'conversion', 'iied', 'mcpa')
        incident_date: Date of the incident (YYYY-MM-DD)

    Returns:
        Dict with expiration analysis, including discovery rule considerations.
    """
    claim_lower = claim_type.lower().replace(" ", "_")
    sol = SOL_TABLE.get(claim_lower)

    if not sol:
        for key, s in SOL_TABLE.items():
            if claim_lower in key or key in claim_lower:
                sol = s
                break

    if not sol:
        return {"error": f"SOL not found for claim type: {claim_type}"}

    try:
        incident_dt = datetime.strptime(incident_date, "%Y-%m-%d")
    except ValueError as e:
        return {"error": f"Invalid date format (use YYYY-MM-DD): {str(e)}"}

    today = datetime.now()
    expiry_dt = incident_dt + timedelta(days=sol["period_years"] * 365)
    days_remaining = (expiry_dt - today).days
    expired = today > expiry_dt

    result = {
        "claim_type": claim_type,
        "incident_date": incident_date,
        "sol_period_years": sol["period_years"],
        "sol_authority": sol["authority"],
        "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
        "days_remaining": days_remaining,
        "expired": expired,
        "analysis": "",
        "action_items": [],
    }

    if expired:
        result["analysis"] = (
            f"WARNING: SOL appears expired as of {today.strftime('%Y-%m-%d')} — "
            f"expired {abs(days_remaining)} days ago. "
            f"HOWEVER, check tolling doctrines before conceding."
        )
        result["action_items"] = [
            "Check discovery rule — when did plaintiff ACTUALLY discover the claim?",
            "Check fraudulent concealment — did defendant hide the cause of action? MCL 600.5855",
            "Check continuing wrong — is the violation ONGOING?",
            "Check minority/disability tolling — MCL 600.5851",
            "If any tolling applies, SOL may still be open",
        ]
    elif days_remaining <= 90:
        result["analysis"] = (
            f"URGENT: Only {days_remaining} days remaining on SOL. "
            f"File immediately or obtain tolling agreement."
        )
        result["action_items"] = [
            f"FILE COMPLAINT before {expiry_dt.strftime('%Y-%m-%d')}",
            "Consider filing protective complaint even if still investigating",
            "Obtain written tolling agreement from defendant if possible",
        ]
    elif days_remaining <= 365:
        result["analysis"] = (
            f"SOL expires in {days_remaining} days ({expiry_dt.strftime('%Y-%m-%d')}). "
            f"Begin preparing filing promptly."
        )
        result["action_items"] = [
            "Complete investigation and evidence gathering",
            "Draft complaint and have ready for filing",
            f"Calendar hard deadline: {expiry_dt.strftime('%Y-%m-%d')}",
        ]
    else:
        result["analysis"] = (
            f"SOL does not expire for {days_remaining} days ({expiry_dt.strftime('%Y-%m-%d')}). "
            f"Adequate time, but do not delay unnecessarily."
        )
        result["action_items"] = [
            "Continue building case — gather evidence and authority",
            f"Calendar SOL deadline: {expiry_dt.strftime('%Y-%m-%d')}",
        ]

    return result


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("skill_defenses_setoffs.py — Self-Test")
    print("=" * 70)

    print("\n[1] get_defenses_for_claim('conversion'):")
    r = get_defenses_for_claim("conversion")
    print(json.dumps({
        "defenses_count": len(r["applicable_defenses"]),
        "defenses": list(r["applicable_defenses"].keys()),
        "sol": r["sol_info"],
    }, indent=2))

    print("\n[2] build_counter_arguments('emergency_maintenance'):")
    ca = build_counter_arguments("emergency_maintenance")
    print(json.dumps({
        "their_argument": ca["their_argument"],
        "our_counters": len(ca["our_counter_arguments"]),
        "strategy": ca["recommended_strategy"][:100],
    }, indent=2))

    print("\n[3] get_sol_for_claim('mcpa'):")
    sol = get_sol_for_claim("mcpa")
    print(json.dumps({
        "period": sol["sol"]["period_years"],
        "authority": sol["sol"]["authority"],
        "tolling_count": len(sol["tolling_doctrines"]),
    }, indent=2))

    print("\n[4] check_sol_expired('conversion', '2023-01-15'):")
    chk = check_sol_expired("conversion", "2023-01-15")
    print(json.dumps({
        "expired": chk["expired"],
        "days_remaining": chk["days_remaining"],
        "analysis": chk["analysis"][:100],
    }, indent=2))

    print("\n✓ All self-tests completed.")
