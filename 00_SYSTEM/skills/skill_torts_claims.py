"""
skill_torts_claims.py — Michigan Tort Claims Skill
====================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Covers:
  - Conversion: MCL 600.2919a (treble damages)
  - Trespass to land/chattels
  - Negligence per se (statutory violation = negligence)
  - IIED: *Roberts v Auto-Owners*, 422 Mich 594 (1985)
  - MCPA: Michigan Consumer Protection Act, MCL 445.901+ (treble damages)
  - Warranty of habitability: MCL 554.139 (common law + statutory)
  - Nuisance: MCL 600.3801
  - Premises liability

Queries litigation_context.db for Michigan-specific authorities.
No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import json
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List, Any

DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Michigan Tort Authorities ───────────────────────────────────────────────

TORT_ELEMENTS = {
    "conversion": {
        "authority": "MCL 600.2919a",
        "definition": "Any distinct act of dominion wrongfully exerted over another's personal property "
                      "in denial of or inconsistent with the rights therein.",
        "elements": [
            "(1) Plaintiff had an ownership or possessory interest in the property",
            "(2) Defendant took dominion over the property inconsistent with plaintiff's rights",
            "(3) Damages resulted from the wrongful taking/interference",
        ],
        "damages": "MCL 600.2919a provides for TREBLE DAMAGES (3x actual) for conversion of property",
        "key_cases": [
            "Foremost Ins Co v Allstate Ins Co, 439 Mich 378 (1992)",
            "Aetna Cas & Sur Co v Peddlers Corner Inc, 189 Mich App 662 (1991)",
        ],
    },
    "trespass_land": {
        "authority": "Common Law — Cloverleaf Car Co v Phillips Petroleum Co, 213 Mich App 186 (1995)",
        "definition": "Unauthorized physical invasion of the property of another.",
        "elements": [
            "(1) Defendant intentionally entered plaintiff's land",
            "(2) Entry was unauthorized — without consent or legal privilege",
            "(3) Damages resulted (nominal damages available even without actual harm)",
        ],
    },
    "trespass_chattels": {
        "authority": "Common Law — Restatement (Second) of Torts § 217 (adopted in MI)",
        "definition": "Intentional interference with plaintiff's possessory interest in personal property.",
        "elements": [
            "(1) Defendant intentionally used or intermeddled with plaintiff's personal property",
            "(2) Interference was without authorization",
            "(3) Plaintiff was dispossessed or chattel was impaired/harmed",
        ],
    },
    "negligence_per_se": {
        "authority": "Klages v General Ordnance Equipment Corp, 240 Mich App 237 (2000)",
        "definition": "Violation of a statute designed to protect a class of persons constitutes "
                      "negligence as a matter of law.",
        "elements": [
            "(1) A statute or ordinance was violated",
            "(2) The statute was designed to protect a class of persons including plaintiff",
            "(3) The harm was the type the statute was designed to prevent",
            "(4) The statutory violation was a proximate cause of plaintiff's injury",
        ],
        "note": "Violation of MCL 554.139, MCL 125.2301+, or housing codes = negligence per se",
    },
    "iied": {
        "authority": "Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)",
        "definition": "Intentional infliction of emotional distress — extreme and outrageous conduct "
                      "causing severe emotional distress.",
        "elements": [
            "(1) Extreme and outrageous conduct — beyond all bounds of decency",
            "(2) Intent to cause distress OR reckless disregard of probability of causing distress",
            "(3) Severe emotional distress actually suffered by plaintiff",
            "(4) Conduct was the proximate cause of the distress",
        ],
        "threshold": "Conduct must be 'so outrageous in character, and so extreme in degree, "
                     "as to go beyond all possible bounds of decency' — Roberts, 422 Mich at 602-603",
        "key_cases": [
            "Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985) — foundational",
            "Graham v Ford, 237 Mich App 670 (1999)",
            "Haverbush v Powelson, 217 Mich App 228 (1996)",
        ],
    },
    "mcpa": {
        "authority": "MCL 445.901 et seq (Michigan Consumer Protection Act)",
        "definition": "Unfair, unconscionable, or deceptive methods, acts, or practices in trade or commerce.",
        "elements": [
            "(1) Defendant engaged in trade or commerce",
            "(2) Defendant committed an unfair, unconscionable, or deceptive act per MCL 445.903",
            "(3) Plaintiff suffered an ascertainable loss",
            "(4) Loss was caused by the prohibited conduct",
        ],
        "damages": "MCL 445.911: TREBLE DAMAGES available — actual damages × 3, plus attorney fees",
        "prohibited_acts_903": [
            "(a) Misrepresentation of source, sponsorship, approval",
            "(c) Representing goods/services as having characteristics they do not have",
            "(e) Representing goods/services are of a particular quality when they are not",
            "(n) Failure to reveal material facts",
            "(s) Failure to provide promised services",
            "(bb) Violation of other consumer protection statutes",
            "(cc) Failing to disclose material information known at time of transaction",
        ],
    },
    "warranty_habitability": {
        "authority": "MCL 554.139 + Common Law",
        "definition": "Implied warranty that leased premises are fit for habitation.",
        "elements": [
            "(1) Landlord-tenant relationship exists",
            "(2) Premises had defective conditions affecting habitability",
            "(3) Landlord had notice (actual or constructive) of the conditions",
            "(4) Landlord failed to repair within reasonable time",
            "(5) Tenant suffered damages",
        ],
        "note": "MCL 554.139(2): This warranty is NON-WAIVABLE — lease clauses purporting to waive are VOID",
    },
    "nuisance": {
        "authority": "MCL 600.3801 + Common Law",
        "definition": "Unreasonable interference with the use and enjoyment of land.",
        "elements": [
            "(1) Defendant's conduct (or condition of property) was unreasonable",
            "(2) Conduct interfered with plaintiff's use and enjoyment of land",
            "(3) Interference was substantial — not merely inconvenience",
        ],
        "types": {
            "private_nuisance": "Unreasonable interference with individual's property rights",
            "public_nuisance": "Unreasonable interference with rights common to the public — MCL 600.3801",
            "nuisance_per_se": "Activity that is a nuisance at all times regardless of circumstances (statutory violation)",
        },
    },
    "premises_liability": {
        "authority": "MCL 554.139 + Lugo v Ameritech Corp, 464 Mich 512 (2001)",
        "definition": "Liability of possessor of land for injuries caused by dangerous conditions.",
        "elements": [
            "(1) Defendant possessed or controlled the premises",
            "(2) A dangerous condition existed on the premises",
            "(3) Defendant knew or should have known of the condition — Lugo, 464 Mich at 516",
            "(4) Defendant failed to warn or make safe within reasonable time",
            "(5) The condition was a proximate cause of plaintiff's injury",
        ],
        "status_of_entrant": {
            "invitee": "Highest duty of care — must inspect and discover dangers",
            "licensee": "Duty to warn of known dangers",
            "trespasser": "Duty only to refrain from willful/wanton injury",
        },
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
    """FTS5 MATCH with LIKE fallback."""
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


def search_tort_authority(tort_type: str) -> Dict[str, Any]:
    """
    Search for Michigan tort authority by tort type.

    Searches hardcoded elements + auth_rules, rules_text, master_citations,
    legal_reference_docs in litigation_context.db.

    Args:
        tort_type: Type of tort (e.g., 'conversion', 'iied', 'mcpa', 'nuisance')

    Returns:
        Dict with matched tort elements and DB authority results.
    """
    result = {
        "tort_type": tort_type,
        "elements": None,
        "db_auth_rules": [],
        "db_rules_text": [],
        "db_citations": [],
        "db_reference_docs": [],
    }

    tort_lower = tort_type.lower().replace(" ", "_")
    for key, tort in TORT_ELEMENTS.items():
        if tort_lower in key or key in tort_lower:
            result["elements"] = tort
            break

    # Broader matching
    if not result["elements"]:
        for key, tort in TORT_ELEMENTS.items():
            if any(w in tort["definition"].lower() for w in tort_type.lower().split()):
                result["elements"] = tort
                break

    conn = _connect_db()
    if not conn:
        result["db_error"] = "Could not connect to database"
        return result

    try:
        result["db_auth_rules"] = _fts_query(conn, "auth_rules_fts", "auth_rules", tort_type, 15)
        result["db_rules_text"] = _fts_query(conn, "rules_text_fts", "rules_text", tort_type, 10)

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM master_citations WHERE citation LIKE ? OR context LIKE ? LIMIT 20",
            (f"%{tort_type}%", f"%{tort_type}%")
        )
        result["db_citations"] = [dict(row) for row in cur.fetchall()]

        cur.execute(
            "SELECT * FROM legal_reference_docs WHERE heading LIKE ? OR body LIKE ? LIMIT 10",
            (f"%{tort_type}%", f"%{tort_type}%")
        )
        result["db_reference_docs"] = [dict(row) for row in cur.fetchall()]

    except sqlite3.Error as e:
        result["db_error"] = str(e)
    finally:
        conn.close()

    return result


def get_conversion_elements() -> Dict[str, Any]:
    """
    Return conversion elements and treble damages authority.

    Per MCL 600.2919a — treble damages (3x actual) available for conversion.

    Returns:
        Dict with elements, damages info, and DB authorities.
    """
    result = {
        "tort": TORT_ELEMENTS["conversion"],
        "treble_damages": {
            "authority": "MCL 600.2919a",
            "formula": "Actual damages × 3",
            "note": "Treble damages are available as of right for conversion — not discretionary",
        },
    }

    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%2919%' OR citation LIKE '%conversion%' "
                "OR context LIKE '%conversion%' LIMIT 15"
            )
            result["db_citations"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def get_mcpa_violations() -> Dict[str, Any]:
    """
    Return MCPA (Michigan Consumer Protection Act) violation types and treble damages.

    Per MCL 445.901+ — MCL 445.903 lists prohibited acts.
    Per MCL 445.911 — treble damages + attorney fees available.

    Returns:
        Dict with MCPA elements, prohibited acts, damages formula.
    """
    result = {
        "tort": TORT_ELEMENTS["mcpa"],
        "treble_damages": {
            "authority": "MCL 445.911",
            "formula": "Actual damages × 3 + reasonable attorney fees",
            "note": "Court SHALL award treble damages if violation is found — mandatory, not discretionary",
        },
        "common_violations_in_housing": [
            "Misrepresenting condition of rental property — MCL 445.903(c)",
            "Failing to disclose known defects — MCL 445.903(n), (cc)",
            "Advertising services not actually provided — MCL 445.903(e)",
            "Failing to provide promised maintenance — MCL 445.903(s)",
            "Unconscionable lease terms — MCL 445.903(y)",
        ],
    }

    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%445.9%' OR citation LIKE '%consumer protection%' "
                "OR context LIKE '%consumer protection%' OR context LIKE '%MCPA%' LIMIT 15"
            )
            result["db_citations"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def get_iied_elements() -> Dict[str, Any]:
    """
    Return IIED elements per *Roberts v Auto-Owners*, 422 Mich 594 (1985).

    The 'extreme and outrageous' threshold is deliberately high — conduct must
    go 'beyond all possible bounds of decency.'

    Returns:
        Dict with elements, threshold analysis, and examples.
    """
    result = {
        "tort": TORT_ELEMENTS["iied"],
        "threshold_analysis": {
            "standard": "Beyond all possible bounds of decency — Roberts, 422 Mich at 602-603",
            "factors_courts_consider": [
                "Abuse of a position of power or authority over plaintiff",
                "Knowledge that plaintiff is particularly susceptible to distress",
                "Pattern of conduct rather than isolated incident",
                "Conduct directed at the plaintiff specifically",
                "Defendant knew or should have known distress would result",
            ],
            "examples_sufficient": [
                "Repeated harassment by landlord — illegal entry, threats, intimidation",
                "Deliberate destruction of tenant's property",
                "Retaliatory utility shutoffs in extreme weather",
                "Threats of violence against tenant or family",
            ],
            "examples_insufficient": [
                "Mere insults or rudeness (unless extreme pattern)",
                "Business disputes handled aggressively but lawfully",
                "Single instance of raised voice",
            ],
        },
    }

    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%Roberts%' OR citation LIKE '%422 Mich%' "
                "OR context LIKE '%emotional distress%' OR context LIKE '%IIED%' LIMIT 15"
            )
            result["db_citations"] = [dict(row) for row in cur.fetchall()]

            cur.execute(
                "SELECT quote_text, legal_significance FROM evidence_quotes "
                "WHERE quote_text LIKE '%harass%' OR quote_text LIKE '%distress%' "
                "OR legal_significance LIKE '%emotional%' LIMIT 10"
            )
            evidence = [dict(row) for row in cur.fetchall()]
            if evidence:
                result["supporting_evidence"] = evidence
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def calculate_treble_damages(actual_damages: float) -> Dict[str, Any]:
    """
    Calculate treble damages under MCL 600.2919a (conversion) and MCL 445.911 (MCPA).

    Args:
        actual_damages: The actual monetary damages suffered.

    Returns:
        Dict with breakdown: actual, treble, and combined totals.
    """
    actual = Decimal(str(actual_damages)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    treble = actual * 3

    return {
        "actual_damages": float(actual),
        "treble_multiplier": 3,
        "treble_damages": float(treble),
        "authorities": {
            "conversion": {
                "statute": "MCL 600.2919a",
                "treble_amount": float(treble),
                "note": "Treble damages available for conversion of property",
            },
            "mcpa": {
                "statute": "MCL 445.911",
                "treble_amount": float(treble),
                "note": "Treble damages + attorney fees for MCPA violations",
            },
        },
        "combined_if_both_claims": {
            "note": "If BOTH conversion AND MCPA apply to the same conduct, "
                    "damages may be limited to one treble recovery to avoid double counting. "
                    "However, MCPA also awards attorney fees — MCL 445.911(2).",
            "max_recovery": float(treble),
            "plus_attorney_fees": "Yes, under MCPA — MCL 445.911(2)",
        },
    }


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("skill_torts_claims.py — Self-Test")
    print("=" * 70)

    print("\n[1] search_tort_authority('conversion'):")
    r = search_tort_authority("conversion")
    print(json.dumps({
        "has_elements": r["elements"] is not None,
        "db_auth_rules": len(r["db_auth_rules"]),
        "db_citations": len(r["db_citations"]),
    }, indent=2))

    print("\n[2] get_conversion_elements():")
    ce = get_conversion_elements()
    print(json.dumps({
        "elements": ce["tort"]["elements"],
        "damages": ce["treble_damages"]["formula"],
    }, indent=2))

    print("\n[3] get_mcpa_violations():")
    mcpa = get_mcpa_violations()
    print(json.dumps({
        "prohibited_acts_count": len(mcpa["tort"]["prohibited_acts_903"]),
        "treble_formula": mcpa["treble_damages"]["formula"],
        "housing_violations": len(mcpa["common_violations_in_housing"]),
    }, indent=2))

    print("\n[4] get_iied_elements():")
    iied = get_iied_elements()
    print(json.dumps({
        "elements": iied["tort"]["elements"],
        "threshold": iied["threshold_analysis"]["standard"][:80],
    }, indent=2))

    print("\n[5] calculate_treble_damages(15000.00):")
    td = calculate_treble_damages(15000.00)
    print(json.dumps({
        "actual": td["actual_damages"],
        "treble": td["treble_damages"],
        "plus_attorney_fees": td["combined_if_both_claims"]["plus_attorney_fees"],
    }, indent=2))

    print("\n✓ All self-tests completed.")
