"""
skill_business_corporate.py — Michigan Business/Corporate Law Skill
====================================================================
LitigationOS 2026 v1.0 — Pigors v. Watson

Covers:
  - MCL 450.1101+ (Business Corporation Act)
  - MCL 450.4101+ (Michigan LLC Act)
  - Corporate veil piercing — *Foodland Distributors v Al-Naimi*,
    220 Mich App 453 (1996)
  - Successor liability doctrines
  - Parent-subsidiary liability
  - Officer/director personal liability

Queries litigation_context.db for Michigan-specific authorities.
No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import json
import os
from typing import Optional, Dict, List, Any

DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Michigan Corporate Law Authorities ──────────────────────────────────────

VEIL_PIERCING = {
    "doctrine": "Corporate Veil Piercing",
    "leading_case": "Foodland Distributors v Al-Naimi, 220 Mich App 453 (1996)",
    "elements": [
        "(1) The corporate entity is a mere INSTRUMENTALITY of another entity or individual",
        "(2) The corporate form was used to COMMIT A FRAUD or WRONG",
        "(3) The plaintiff suffered an UNJUST LOSS or INJURY as a result",
    ],
    "instrumentality_factors": [
        "Undercapitalization of the corporation",
        "Failure to observe corporate formalities",
        "Absence of corporate records or minutes",
        "Commingling of personal and corporate funds",
        "Diversion of corporate assets for personal use",
        "Use of the corporation as a mere shell or conduit",
        "Identical directors/officers/shareholders between entities",
        "Non-functioning officers or directors",
        "Siphoning of corporate funds by dominant shareholder",
    ],
    "additional_cases": [
        "SCD Chemical Distributors v Medley, 203 Mich App 374 (1994)",
        "Seasword v Hilti Inc, 449 Mich 542 (1995) — single business enterprise",
        "Servo Dynamics Inc v Fanuc Ltd, 475 F3d 783 (6th Cir, 2007) — applying MI law",
    ],
}

ALTER_EGO_FACTORS = {
    "doctrine": "Alter Ego / Single Business Enterprise",
    "authority": "Seasword v Hilti Inc, 449 Mich 542 (1995)",
    "factors": [
        "Common ownership or control",
        "Common directors or officers",
        "Common business departments or employees",
        "Consolidated financial statements or tax returns",
        "One entity pays wages/expenses of the other",
        "One entity profits from the activities of the other",
        "Common office space, phone numbers, or addresses",
        "Intermingling of property or assets between entities",
    ],
}

BCA_KEY_PROVISIONS = {
    "MCL 450.1101": "Short title — Michigan Business Corporation Act",
    "MCL 450.1209": "Ultra vires — acts beyond corporate authority",
    "MCL 450.1489": "Shareholder derivative actions",
    "MCL 450.1505": "Corporate records — inspection rights",
    "MCL 450.1541a": "Director duty of care",
    "MCL 450.1541b": "Director duty of loyalty",
    "MCL 450.1561-567": "Indemnification of directors/officers",
    "MCL 450.1801-855": "Merger, consolidation, share exchange",
    "MCL 450.1921-931": "Dissolution — voluntary and involuntary",
}

LLC_KEY_PROVISIONS = {
    "MCL 450.4101": "Short title — Michigan Limited Liability Company Act",
    "MCL 450.4501": "LLC member liability — generally shielded",
    "MCL 450.4502": "LLC member as agent — authority to bind",
    "MCL 450.4507": "LLC member personal liability — piercing applies",
    "MCL 450.4515": "Duty of loyalty — LLC members/managers",
    "MCL 450.4516": "Duty of care — LLC members/managers",
    "MCL 450.4801-804": "Dissolution and winding up",
}

SUCCESSOR_LIABILITY = {
    "doctrine": "Successor Liability",
    "authority": "Foster v Cone-Blanchard Machine Co, 460 Mich 696 (1999)",
    "general_rule": "Purchaser of corporate assets generally NOT liable for seller's debts",
    "exceptions": [
        "(1) Express or implied ASSUMPTION of liability",
        "(2) Transaction amounts to a DE FACTO MERGER",
        "(3) Purchasing entity is a mere CONTINUATION of the seller",
        "(4) Transaction was entered into FRAUDULENTLY to escape liability",
    ],
    "de_facto_merger_factors": [
        "Continuity of the enterprise (management, personnel, location, assets)",
        "Continuity of shareholders/ownership",
        "Seller ceases operations and dissolves",
        "Buyer assumes obligations necessary to continue operations",
    ],
}


def _connect_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db with retry."""
    retries = 3
    for attempt in range(retries):
        try:
            if not os.path.exists(DB_PATH):
                return None
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error:
            if attempt < retries - 1:
                continue
            return None
    return None


def _fts_search(conn: sqlite3.Connection, fts_table: str, base_table: str,
                term: str, limit: int = 15) -> List[Dict]:
    """FTS5 search with LIKE fallback."""
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT ?",
            (term, limit)
        )
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


def search_corporate_authority(topic: str) -> Dict[str, Any]:
    """
    Search for Michigan business/corporate law authority on a topic.

    Searches auth_rules, rules_text, master_citations, legal_reference_docs,
    plus hardcoded BCA/LLC/veil-piercing references.

    Args:
        topic: Search topic (e.g., 'veil piercing', 'LLC liability', 'director duty')

    Returns:
        Dict with matched authorities from DB and hardcoded references.
    """
    result = {
        "topic": topic,
        "hardcoded_matches": [],
        "db_auth_rules": [],
        "db_rules_text": [],
        "db_citations": [],
        "db_reference_docs": [],
    }

    topic_lower = topic.lower()

    # Match hardcoded
    if any(kw in topic_lower for kw in ["veil", "pierc", "instrumentality"]):
        result["hardcoded_matches"].append(VEIL_PIERCING)
    if any(kw in topic_lower for kw in ["alter ego", "single business", "enterprise"]):
        result["hardcoded_matches"].append(ALTER_EGO_FACTORS)
    if any(kw in topic_lower for kw in ["successor", "asset purchase", "de facto merger"]):
        result["hardcoded_matches"].append(SUCCESSOR_LIABILITY)

    # BCA provisions matching
    for mcl, desc in BCA_KEY_PROVISIONS.items():
        if topic_lower in desc.lower() or topic_lower in mcl.lower():
            result["hardcoded_matches"].append({"statute": mcl, "description": desc})

    # LLC provisions matching
    for mcl, desc in LLC_KEY_PROVISIONS.items():
        if topic_lower in desc.lower() or topic_lower in mcl.lower():
            result["hardcoded_matches"].append({"statute": mcl, "description": desc})

    # DB search
    conn = _connect_db()
    if not conn:
        result["db_error"] = "Could not connect to database"
        return result

    try:
        result["db_auth_rules"] = _fts_search(conn, "auth_rules_fts", "auth_rules", topic, 15)
        result["db_rules_text"] = _fts_search(conn, "rules_text_fts", "rules_text", topic, 10)

        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM master_citations WHERE citation LIKE ? OR context LIKE ? LIMIT 20",
            (f"%{topic}%", f"%{topic}%")
        )
        result["db_citations"] = [dict(row) for row in cur.fetchall()]

        cur.execute(
            "SELECT * FROM legal_reference_docs WHERE heading LIKE ? OR body LIKE ? LIMIT 10",
            (f"%{topic}%", f"%{topic}%")
        )
        result["db_reference_docs"] = [dict(row) for row in cur.fetchall()]

    except sqlite3.Error as e:
        result["db_error"] = str(e)
    finally:
        conn.close()

    return result


def get_veil_piercing_elements() -> Dict[str, Any]:
    """
    Return the three-element test for corporate veil piercing in Michigan.

    Per *Foodland Distributors v Al-Naimi*, 220 Mich App 453 (1996):
    (1) Mere instrumentality, (2) Used to commit fraud/wrong, (3) Unjust loss.

    Returns:
        Dict with elements, instrumentality factors, and case law.
    """
    result = {
        "test": VEIL_PIERCING,
        "alter_ego": ALTER_EGO_FACTORS,
        "successor_liability": SUCCESSOR_LIABILITY,
    }

    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%Foodland%' OR citation LIKE '%Al-Naimi%' "
                "OR citation LIKE '%Seasword%' OR citation LIKE '%veil%' "
                "OR context LIKE '%veil pierc%' OR context LIKE '%alter ego%' LIMIT 20"
            )
            result["db_case_law"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return result


def check_alter_ego_factors(facts_dict: Dict[str, bool]) -> Dict[str, Any]:
    """
    Evaluate alter ego / single business enterprise factors against provided facts.

    Per *Seasword v Hilti Inc*, 449 Mich 542 (1995).

    Args:
        facts_dict: Dict mapping factor descriptions to True/False.
            Keys should approximate the factor names (partial match used).
            Example: {"common_ownership": True, "commingled_funds": True, ...}

    Returns:
        Dict with factor-by-factor analysis, score, and legal conclusion.
    """
    all_factors = {
        "common_ownership": "Common ownership or control",
        "common_directors": "Common directors or officers",
        "common_departments": "Common business departments or employees",
        "consolidated_financials": "Consolidated financial statements or tax returns",
        "shared_wages": "One entity pays wages/expenses of the other",
        "shared_profits": "One entity profits from the activities of the other",
        "common_office": "Common office space, phone numbers, or addresses",
        "commingled_assets": "Intermingling of property or assets between entities",
        "undercapitalization": "Undercapitalization of the corporation",
        "no_formalities": "Failure to observe corporate formalities",
        "no_records": "Absence of corporate records or minutes",
        "commingled_funds": "Commingling of personal and corporate funds",
        "asset_diversion": "Diversion of corporate assets for personal use",
        "shell_conduit": "Use of the corporation as a mere shell or conduit",
        "siphoning": "Siphoning of corporate funds by dominant shareholder",
    }

    analysis = {
        "authority": "Seasword v Hilti Inc, 449 Mich 542 (1995); "
                     "Foodland Distributors v Al-Naimi, 220 Mich App 453 (1996)",
        "factors_present": [],
        "factors_absent": [],
        "factors_unknown": [],
        "score": 0,
        "total_factors": len(all_factors),
        "strength": "",
        "legal_conclusion": "",
    }

    for key, description in all_factors.items():
        matched = False
        for fact_key, fact_val in facts_dict.items():
            if fact_key.lower().replace(" ", "_") == key or key in fact_key.lower().replace(" ", "_"):
                matched = True
                if fact_val:
                    analysis["factors_present"].append(description)
                    analysis["score"] += 1
                else:
                    analysis["factors_absent"].append(description)
                break
        if not matched:
            analysis["factors_unknown"].append(description)

    pct = (analysis["score"] / analysis["total_factors"]) * 100 if analysis["total_factors"] > 0 else 0

    if pct >= 60:
        analysis["strength"] = "STRONG"
        analysis["legal_conclusion"] = (
            f"With {analysis['score']}/{analysis['total_factors']} factors present ({pct:.0f}%), "
            f"a strong argument exists for piercing the corporate veil. "
            f"Courts have pierced with fewer factors when fraud is shown."
        )
    elif pct >= 35:
        analysis["strength"] = "MODERATE"
        analysis["legal_conclusion"] = (
            f"With {analysis['score']}/{analysis['total_factors']} factors present ({pct:.0f}%), "
            f"a moderate argument for veil piercing exists. "
            f"Strengthen with evidence of fraud/wrong (element 2) and unjust loss (element 3)."
        )
    else:
        analysis["strength"] = "WEAK"
        analysis["legal_conclusion"] = (
            f"With {analysis['score']}/{analysis['total_factors']} factors present ({pct:.0f}%), "
            f"veil piercing argument is weak. Consider alternative theories: "
            f"personal liability, successor liability, or agency."
        )

    return analysis


def get_llc_liability_rules() -> Dict[str, Any]:
    """
    Return Michigan LLC liability rules and exceptions.

    Per MCL 450.4501+ — members generally shielded from personal liability,
    but piercing applies to LLCs as well as corporations.

    Returns:
        Dict with LLC liability rules, exceptions, and DB authorities.
    """
    rules = {
        "general_rule": {
            "authority": "MCL 450.4501",
            "rule": "LLC members are generally NOT personally liable for LLC debts or obligations.",
        },
        "exceptions_to_shield": [
            {
                "exception": "Veil Piercing Applies to LLCs",
                "authority": "Florence Cement Co v Vettraino, 292 Mich App 461 (2011)",
                "description": "Same Foodland three-element test applies to LLCs",
            },
            {
                "exception": "Personal Guarantees",
                "authority": "Contract Law / MCL 450.4501",
                "description": "Member who personally guarantees LLC debt is liable on the guarantee",
            },
            {
                "exception": "Tortious Conduct",
                "authority": "Common Law + MCL 450.4507",
                "description": "Member is personally liable for own tortious acts regardless of LLC form",
            },
            {
                "exception": "Statutory Liability",
                "authority": "Various MCL provisions",
                "description": "Certain statutes impose personal liability (e.g., tax withholding, environmental)",
            },
            {
                "exception": "Member as Agent with Authority",
                "authority": "MCL 450.4502",
                "description": "Member acting as agent can bind LLC and may incur personal liability if exceeds authority",
            },
        ],
        "llc_provisions": LLC_KEY_PROVISIONS,
    }

    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%450.4%' OR citation LIKE '%LLC%' "
                "OR context LIKE '%limited liability%' LIMIT 20"
            )
            rules["db_citations"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return rules


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("skill_business_corporate.py — Self-Test")
    print("=" * 70)

    print("\n[1] search_corporate_authority('veil piercing'):")
    r = search_corporate_authority("veil piercing")
    print(json.dumps({
        "hardcoded_matches": len(r["hardcoded_matches"]),
        "db_auth_rules": len(r["db_auth_rules"]),
        "db_citations": len(r["db_citations"]),
    }, indent=2))

    print("\n[2] get_veil_piercing_elements() — elements:")
    vp = get_veil_piercing_elements()
    print(json.dumps({
        "elements": vp["test"]["elements"],
        "db_case_law_count": len(vp.get("db_case_law", [])),
    }, indent=2))

    print("\n[3] check_alter_ego_factors():")
    facts = {
        "common_ownership": True,
        "commingled_funds": True,
        "no_formalities": True,
        "common_office": True,
        "undercapitalization": True,
    }
    ae = check_alter_ego_factors(facts)
    print(json.dumps({
        "score": f"{ae['score']}/{ae['total_factors']}",
        "strength": ae["strength"],
        "conclusion": ae["legal_conclusion"][:120],
    }, indent=2))

    print("\n[4] get_llc_liability_rules() — exceptions:")
    llc = get_llc_liability_rules()
    print(json.dumps({
        "exceptions": [e["exception"] for e in llc["exceptions_to_shield"]],
        "db_citations_count": len(llc.get("db_citations", [])),
    }, indent=2))

    print("\n✓ All self-tests completed.")
