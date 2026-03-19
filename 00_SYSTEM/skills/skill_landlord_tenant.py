"""
skill_landlord_tenant.py — Michigan Landlord/Tenant Law Skill
=============================================================
LitigationOS 2026 v1.0 — Pigors v. Watson (Lane B: Shady Oaks Housing)

Covers:
  - MCL 554.139: Warranty of habitability (NON-WAIVABLE)
  - MCL 600.5714-5744: Summary proceedings / eviction
  - MCL 554.601-614: Security Deposit Act
  - MCL 125.2301-2349: Mobile Home Commission Act (Shady Oaks)
  - MCL 600.5720: Retaliatory eviction (90-day presumption)
  - Illegal entry (24hr written notice required)
  - Constructive eviction elements

Queries litigation_context.db for Michigan-specific authorities.
No network calls. Pure SQLite + text analysis.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

DB_PATH = r"C:\Users\andre\litigation_context.db"

# ── Michigan Landlord/Tenant Authorities (hardcoded reference) ──────────────

HOUSING_AUTHORITIES = {
    "warranty_of_habitability": {
        "statute": "MCL 554.139",
        "title": "Warranty of Fitness and Habitability",
        "key_points": [
            "Landlord must keep premises fit for intended use",
            "Landlord must keep premises in reasonable repair",
            "NON-WAIVABLE — any lease clause purporting to waive is VOID",
            "Applies to all residential leases",
            "Tenant remedies: rent withholding, repair-and-deduct, damages",
        ],
        "subsections": {
            "(1)(a)": "Premises and common areas fit for use intended by parties",
            "(1)(b)": "Premises kept in reasonable repair during lease term",
            "(2)": "Covenants imposed by this section are non-waivable — any agreement to waive is VOID",
        },
    },
    "summary_proceedings": {
        "statute": "MCL 600.5714-5744",
        "title": "Summary Proceedings to Recover Possession",
        "key_points": [
            "MCL 600.5714: Grounds for summary proceeding",
            "MCL 600.5718: Demand for possession required before filing",
            "MCL 600.5720: Retaliatory eviction defense — 90 day presumption",
            "MCL 600.5726: Service of summons requirements",
            "MCL 600.5744: Judgment and writ of restitution",
            "Strict procedural requirements — defects are jurisdictional",
        ],
    },
    "security_deposit": {
        "statute": "MCL 554.601-614",
        "title": "Security Deposit Act",
        "key_points": [
            "MCL 554.602: Deposit cannot exceed 1.5 months' rent",
            "MCL 554.603: Landlord must provide itemized list of damages within 30 days",
            "MCL 554.604: Return within 30 days of termination or forfeit",
            "MCL 554.609: Tenant may recover DOUBLE the withheld amount if landlord fails to comply",
            "MCL 554.610: Landlord must notify tenant of deposit location",
        ],
    },
    "mobile_home_commission_act": {
        "statute": "MCL 125.2301-2349",
        "title": "Mobile Home Commission Act",
        "key_points": [
            "MCL 125.2302: Definitions — mobile home park, licensee, mobile home",
            "MCL 125.2307: Park rules must be fair and reasonable",
            "MCL 125.2310: 30-day notice required for rule changes",
            "MCL 125.2312a: Grounds for eviction are LIMITED and enumerated",
            "MCL 125.2312b: Eviction procedures — must follow statutory process",
            "MCL 125.2316: Park owner must maintain common areas and utilities",
            "MCL 125.2317: Tenant right to sell home in place",
            "MCL 125.2319: Retaliatory action prohibited",
            "MCL 125.2340: Penalties for violations",
            "Mobile home tenants have ADDITIONAL protections beyond standard L/T law",
        ],
    },
    "retaliatory_eviction": {
        "statute": "MCL 600.5720",
        "title": "Retaliatory Eviction",
        "key_points": [
            "90-day rebuttable presumption of retaliation",
            "Protected activities: complaints to govt, tenant organizing, requesting repairs",
            "If eviction filed within 90 days of protected activity = PRESUMED retaliatory",
            "Landlord must prove legitimate non-retaliatory reason",
            "Also see MCL 125.2319 for mobile home park retaliation",
        ],
    },
    "illegal_entry": {
        "statute": "Common Law + MCL 554.139 + Lease Terms",
        "title": "Illegal Entry / Right to Quiet Enjoyment",
        "key_points": [
            "24-hour WRITTEN notice required before non-emergency entry",
            "Entry only during reasonable hours",
            "Emergency exception: imminent danger to life/property ONLY",
            "Repeated illegal entry = harassment, potential constructive eviction",
            "Violation supports IIED claim if extreme and outrageous",
            "Tenant may change locks if landlord enters illegally (with notice to landlord)",
        ],
    },
    "constructive_eviction": {
        "statute": "Common Law — Blackett v Olanoff, 371 Mass 714 (1977); MI adoption",
        "title": "Constructive Eviction",
        "key_points": [
            "Elements: (1) landlord act/omission, (2) substantially interferes with beneficial enjoyment",
            "(3) tenant abandons premises within reasonable time",
            "Does NOT require physical expulsion — conditions that render uninhabitable suffice",
            "Failure to maintain per MCL 554.139 can support constructive eviction",
            "Utility shutoffs, harassment, failure to repair = potential constructive eviction",
        ],
    },
}


def _connect_db() -> Optional[sqlite3.Connection]:
    """Connect to litigation_context.db with retry."""
    retries = 3
    for attempt in range(retries):
        try:
            if not os.path.exists(DB_PATH):
                print(json.dumps({"error": f"Database not found at {DB_PATH}"}))
                return None
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            if attempt < retries - 1:
                continue
            print(json.dumps({"error": f"DB connection failed: {str(e)}"}))
            return None
    return None


def _safe_fts_query(conn: sqlite3.Connection, table: str, fts_table: str,
                    match_term: str, limit: int = 20) -> List[Dict]:
    """Run FTS5 MATCH query with fallback to LIKE."""
    results = []
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM {fts_table} WHERE {fts_table} MATCH ? LIMIT ?",
            (match_term, limit)
        )
        results = [dict(row) for row in cur.fetchall()]
    except sqlite3.Error:
        try:
            cur = conn.cursor()
            like_term = f"%{match_term.split()[0]}%"
            if table == "auth_rules":
                cur.execute(
                    f"SELECT * FROM {table} WHERE full_text LIKE ? OR title LIKE ? LIMIT ?",
                    (like_term, like_term, limit)
                )
            elif table == "rules_text":
                cur.execute(
                    f"SELECT * FROM {table} WHERE context LIKE ? OR rule LIKE ? LIMIT ?",
                    (like_term, like_term, limit)
                )
            else:
                cur.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
            results = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
    return results


def search_housing_authority(topic: str) -> Dict[str, Any]:
    """
    Search litigation_context.db for Michigan housing/landlord-tenant authority.

    Searches: auth_rules, rules_text, master_citations, legal_reference_docs,
    plus hardcoded Michigan L/T authority references.

    Args:
        topic: Search topic (e.g., 'habitability', 'eviction', 'security deposit')

    Returns:
        Dict with 'hardcoded_authority', 'db_rules', 'db_rules_text',
        'db_citations', 'db_reference_docs' keys.
    """
    result = {
        "topic": topic,
        "hardcoded_authority": [],
        "db_rules": [],
        "db_rules_text": [],
        "db_citations": [],
        "db_reference_docs": [],
    }

    # Match hardcoded authorities
    topic_lower = topic.lower()
    for key, auth in HOUSING_AUTHORITIES.items():
        if (topic_lower in key or
            topic_lower in auth["title"].lower() or
            any(topic_lower in p.lower() for p in auth["key_points"])):
            result["hardcoded_authority"].append(auth)

    # Search DB
    conn = _connect_db()
    if not conn:
        result["db_error"] = "Could not connect to database"
        return result

    try:
        search_terms = f"{topic} OR landlord OR tenant OR housing OR habitability OR eviction"

        result["db_rules"] = _safe_fts_query(conn, "auth_rules", "auth_rules_fts", search_terms, 15)

        result["db_rules_text"] = _safe_fts_query(conn, "rules_text", "rules_text_fts", topic, 15)

        # master_citations — LIKE search
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM master_citations WHERE citation LIKE ? OR context LIKE ? LIMIT 20",
                (f"%{topic}%", f"%{topic}%")
            )
            result["db_citations"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass

        # legal_reference_docs — LIKE search
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM legal_reference_docs WHERE heading LIKE ? OR body LIKE ? LIMIT 10",
                (f"%{topic}%", f"%{topic}%")
            )
            result["db_reference_docs"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass

    finally:
        conn.close()

    return result


def get_tenant_rights() -> Dict[str, Any]:
    """
    Return comprehensive Michigan tenant rights summary.

    Covers MCL 554.139 (habitability), MCL 554.601+ (security deposits),
    MCL 600.5720 (retaliation protection), MCL 125.2301+ (mobile home rights).

    Returns:
        Dict with categorized tenant rights and authorities.
    """
    rights = {
        "habitability": {
            "authority": "MCL 554.139",
            "rights": [
                "Premises must be fit for intended use — MCL 554.139(1)(a)",
                "Premises must be kept in reasonable repair — MCL 554.139(1)(b)",
                "These covenants are NON-WAIVABLE — MCL 554.139(2)",
                "Remedies: rent withholding, repair-and-deduct, sue for damages",
            ],
        },
        "security_deposit": {
            "authority": "MCL 554.601-614",
            "rights": [
                "Deposit limited to 1.5 months rent — MCL 554.602",
                "Itemized damage list within 30 days — MCL 554.603",
                "Refund within 30 days or forfeit — MCL 554.604",
                "DOUBLE damages for wrongful withholding — MCL 554.609",
            ],
        },
        "retaliation_protection": {
            "authority": "MCL 600.5720",
            "rights": [
                "90-day presumption of retaliation after protected activity",
                "Protected: complaints to government, organizing, repair requests",
                "Burden shifts to landlord to prove non-retaliatory motive",
            ],
        },
        "mobile_home_additional": {
            "authority": "MCL 125.2301-2349",
            "rights": [
                "Eviction grounds are LIMITED and enumerated — MCL 125.2312a",
                "30-day notice required for rule changes — MCL 125.2310",
                "Right to sell home in place — MCL 125.2317",
                "Park must maintain common areas — MCL 125.2316",
                "Retaliatory actions prohibited — MCL 125.2319",
            ],
        },
        "quiet_enjoyment": {
            "authority": "Common Law + MCL 554.139",
            "rights": [
                "24-hour written notice before non-emergency entry",
                "Entry only during reasonable hours",
                "Freedom from harassment by landlord",
                "Constructive eviction claim if conditions render unit uninhabitable",
            ],
        },
    }

    # Enrich with DB search
    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%554.139%' OR citation LIKE '%554.60%' "
                "OR citation LIKE '%600.5720%' OR citation LIKE '%125.23%' LIMIT 20"
            )
            rights["db_citations"] = [dict(row) for row in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return rights


def get_landlord_obligations() -> Dict[str, Any]:
    """
    Return comprehensive Michigan landlord obligations.

    Returns:
        Dict with categorized landlord obligations per MCL authority.
    """
    obligations = {
        "habitability_maintenance": {
            "authority": "MCL 554.139",
            "obligations": [
                "Keep premises fit for intended use at ALL times",
                "Keep premises in reasonable repair throughout lease",
                "Cannot contract away these obligations — they are NON-WAIVABLE",
                "Must address repair requests in reasonable time",
            ],
        },
        "security_deposit_handling": {
            "authority": "MCL 554.601-614",
            "obligations": [
                "Collect no more than 1.5 months rent as deposit — MCL 554.602",
                "Provide written notice of deposit location — MCL 554.610",
                "Return deposit within 30 days of lease termination — MCL 554.604",
                "Provide ITEMIZED list of any deductions within 30 days — MCL 554.603",
            ],
        },
        "entry_and_access": {
            "authority": "Common Law + Lease Terms",
            "obligations": [
                "Provide 24-hour WRITTEN notice before entry",
                "Enter only during reasonable hours",
                "Emergency entry ONLY for imminent danger to life/property",
                "Cannot use entry as harassment or intimidation",
            ],
        },
        "mobile_home_park_specific": {
            "authority": "MCL 125.2301-2349",
            "obligations": [
                "Maintain common areas and infrastructure — MCL 125.2316",
                "Follow enumerated eviction grounds ONLY — MCL 125.2312a",
                "Give 30-day notice for rule changes — MCL 125.2310",
                "Allow tenant to sell home in place — MCL 125.2317",
                "No retaliatory actions — MCL 125.2319",
                "Comply with Mobile Home Commission regulations",
            ],
        },
        "eviction_procedures": {
            "authority": "MCL 600.5714-5744",
            "obligations": [
                "Provide proper demand for possession before filing — MCL 600.5718",
                "Serve summons per statutory requirements — MCL 600.5726",
                "Cannot engage in self-help eviction (lockouts, utility shutoffs)",
                "Must obtain court order and writ of restitution — MCL 600.5744",
            ],
        },
    }
    return obligations


def check_retaliation_timeline(complaint_date: str, eviction_date: str) -> Dict[str, Any]:
    """
    Analyze whether an eviction falls within the 90-day retaliatory presumption.

    Per MCL 600.5720, if eviction proceedings are initiated within 90 days
    of a protected tenant activity, retaliation is PRESUMED.

    Args:
        complaint_date: Date of protected activity (YYYY-MM-DD)
        eviction_date: Date eviction was filed/initiated (YYYY-MM-DD)

    Returns:
        Dict with timeline analysis and legal conclusion.
    """
    try:
        complaint_dt = datetime.strptime(complaint_date, "%Y-%m-%d")
        eviction_dt = datetime.strptime(eviction_date, "%Y-%m-%d")
    except ValueError as e:
        return {"error": f"Invalid date format (use YYYY-MM-DD): {str(e)}"}

    days_between = (eviction_dt - complaint_dt).days
    within_90 = days_between <= 90 and days_between >= 0
    presumption_expires = complaint_dt + timedelta(days=90)

    analysis = {
        "complaint_date": complaint_date,
        "eviction_date": eviction_date,
        "days_between": days_between,
        "within_90_day_window": within_90,
        "presumption_expiry": presumption_expires.strftime("%Y-%m-%d"),
        "authority": "MCL 600.5720",
        "analysis": "",
        "legal_conclusion": "",
        "recommended_arguments": [],
    }

    if days_between < 0:
        analysis["analysis"] = "Eviction predates complaint — retaliation presumption does not apply."
        analysis["legal_conclusion"] = "Timeline does not support retaliation claim."
    elif within_90:
        analysis["analysis"] = (
            f"STRONG RETALIATION CASE: Only {days_between} days between protected activity "
            f"and eviction. MCL 600.5720 creates a REBUTTABLE PRESUMPTION of retaliation "
            f"when eviction is filed within 90 days of protected tenant activity."
        )
        analysis["legal_conclusion"] = (
            "Retaliation is PRESUMED. Burden shifts to landlord to prove "
            "legitimate, non-retaliatory reason for eviction."
        )
        analysis["recommended_arguments"] = [
            f"Per MCL 600.5720, eviction filed {days_between} days after protected activity triggers 90-day presumption",
            "Landlord bears burden of proving legitimate non-retaliatory purpose",
            "Also cite MCL 125.2319 if mobile home park — additional retaliation protections",
            "Request eviction be dismissed as retaliatory",
            "Seek damages for retaliatory conduct",
        ]
    else:
        analysis["analysis"] = (
            f"{days_between} days between events — outside 90-day presumption window. "
            f"Retaliation may still be argued but without statutory presumption."
        )
        analysis["legal_conclusion"] = (
            "Outside 90-day presumption. Must prove retaliation through "
            "circumstantial evidence — pattern, timing, motive."
        )
        analysis["recommended_arguments"] = [
            "Argue pattern of retaliatory conduct even outside 90-day window",
            "Document any other evidence of retaliatory motive",
            "Check for additional protected activities closer to eviction date",
        ]

    # Check DB for related evidence
    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT quote_text, legal_significance FROM evidence_quotes "
                "WHERE quote_text LIKE '%retaliat%' OR quote_text LIKE '%evict%' "
                "OR legal_significance LIKE '%retaliat%' LIMIT 10"
            )
            db_evidence = [dict(row) for row in cur.fetchall()]
            if db_evidence:
                analysis["supporting_evidence_from_db"] = db_evidence
        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return analysis


def get_mobile_home_act_provisions() -> Dict[str, Any]:
    """
    Return detailed Mobile Home Commission Act provisions (MCL 125.2301-2349).

    Critical for Shady Oaks mobile home park litigation (Lane B).
    Mobile home tenants have ADDITIONAL protections beyond standard L/T law.

    Returns:
        Dict with categorized provisions, tenant protections, and DB results.
    """
    provisions = {
        "act": "Mobile Home Commission Act — MCL 125.2301-2349",
        "relevance": "Shady Oaks Mobile Home Park — Lane B litigation",
        "key_sections": {
            "MCL 125.2302": {
                "title": "Definitions",
                "content": "Defines mobile home, mobile home park, licensee, lot, tenant",
            },
            "MCL 125.2307": {
                "title": "Park Rules",
                "content": "Park rules must be FAIR and REASONABLE. Unreasonable rules unenforceable.",
            },
            "MCL 125.2310": {
                "title": "Rule Changes — 30 Day Notice",
                "content": "Park owner must give 30 days written notice before implementing new rules or changing existing rules.",
            },
            "MCL 125.2312a": {
                "title": "Grounds for Eviction — ENUMERATED",
                "content": (
                    "Eviction ONLY for: (a) nonpayment of rent, (b) violation of park rules after notice, "
                    "(c) conviction of offense threatening health/safety, (d) condemnation, "
                    "(e) change of use of park. Grounds are LIMITED — no at-will eviction."
                ),
            },
            "MCL 125.2312b": {
                "title": "Eviction Procedures",
                "content": "Must follow specific statutory eviction process. Self-help eviction prohibited.",
            },
            "MCL 125.2316": {
                "title": "Park Maintenance Obligations",
                "content": "Park owner must maintain common areas, roads, utilities, drainage, and infrastructure.",
            },
            "MCL 125.2317": {
                "title": "Right to Sell Home in Place",
                "content": "Tenant has right to sell mobile home in place — park cannot force removal to sell.",
            },
            "MCL 125.2319": {
                "title": "Retaliatory Actions PROHIBITED",
                "content": (
                    "Park owner may not retaliate for: complaints to government, organizing, "
                    "exercising legal rights. Broader than general MCL 600.5720 protection."
                ),
            },
            "MCL 125.2340": {
                "title": "Penalties",
                "content": "Violations subject to penalties. MHCA enforced by Mobile Home Commission.",
            },
        },
        "tenant_additional_protections": [
            "Mobile home tenants own their HOME even if they rent the LOT",
            "Eviction of lot ≠ eviction from home — different legal framework",
            "Park cannot unreasonably withhold approval of home sale",
            "Park must provide written lease with specific terms",
            "Seasonal/annual rent increases must comply with MHCA",
        ],
    }

    # Enrich from DB
    conn = _connect_db()
    if conn:
        try:
            cur = conn.cursor()

            # Search auth_rules for mobile home provisions
            provisions["db_auth_rules"] = _safe_fts_query(
                conn, "auth_rules", "auth_rules_fts", "mobile home park", 15
            )

            # Search rules_text
            provisions["db_rules_text"] = _safe_fts_query(
                conn, "rules_text", "rules_text_fts", "mobile home", 10
            )

            # Search master_citations for MHCA cites
            cur.execute(
                "SELECT citation, context FROM master_citations "
                "WHERE citation LIKE '%125.23%' LIMIT 20"
            )
            provisions["db_citations"] = [dict(row) for row in cur.fetchall()]

            # Search Shady Oaks specific tables
            for tbl in ["shadyoaks_claim_table", "shadyoaks_evidence", "shadyoaks_claim_table_2"]:
                try:
                    cur.execute(f"SELECT * FROM {tbl} LIMIT 10")
                    rows = [dict(row) for row in cur.fetchall()]
                    if rows:
                        provisions[f"db_{tbl}"] = rows
                except sqlite3.Error:
                    pass

        except sqlite3.Error:
            pass
        finally:
            conn.close()

    return provisions


# ── Self-test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("skill_landlord_tenant.py — Self-Test")
    print("=" * 70)

    print("\n[1] search_housing_authority('habitability'):")
    r = search_housing_authority("habitability")
    print(json.dumps({
        "hardcoded_count": len(r["hardcoded_authority"]),
        "db_rules_count": len(r["db_rules"]),
        "db_citations_count": len(r["db_citations"]),
    }, indent=2))

    print("\n[2] get_tenant_rights() — categories:")
    rights = get_tenant_rights()
    print(json.dumps(list(rights.keys()), indent=2))

    print("\n[3] get_landlord_obligations() — categories:")
    oblig = get_landlord_obligations()
    print(json.dumps(list(oblig.keys()), indent=2))

    print("\n[4] check_retaliation_timeline('2024-06-01', '2024-07-15'):")
    rt = check_retaliation_timeline("2024-06-01", "2024-07-15")
    print(json.dumps({
        "days_between": rt["days_between"],
        "within_90_day_window": rt["within_90_day_window"],
        "legal_conclusion": rt["legal_conclusion"][:100],
    }, indent=2))

    print("\n[5] get_mobile_home_act_provisions() — sections:")
    mh = get_mobile_home_act_provisions()
    print(json.dumps({
        "key_sections": list(mh["key_sections"].keys()),
        "db_tables_found": [k for k in mh if k.startswith("db_") and mh[k]],
    }, indent=2))

    print("\n✓ All self-tests completed.")
