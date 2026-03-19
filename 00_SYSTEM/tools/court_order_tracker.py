#!/usr/bin/env python3
"""
Tool #214 — Court Order Tracker
Tracks all court orders from litigation_context.db.
Classifies by type, checks compliance, flags void/voidable orders (MCR 2.612).
Two confirmed ex-parte orders: Andrew's May 2024, Emily's August 2025.
Output: COURT_ORDER_TRACKER.md + COURT_ORDER_TRACKER.json
"""
import sys, os, json, sqlite3, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOLS_DIR.parent.parent
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

ORDER_CATEGORIES = {
    "Custody": ["custody", "legal custody", "physical custody", "sole custody", "joint custody"],
    "PPO": ["ppo", "personal protection", "protection order", "stalking"],
    "Ex Parte": ["ex parte", "emergency order", "temporary order", "without notice"],
    "Support": ["child support", "support order", "income withholding", "arrearage"],
    "Parenting Time": ["parenting time", "visitation", "overnight", "holiday schedule",
                       "suspended parenting", "supervised parenting"],
    "Contempt": ["contempt", "show cause", "violation of order"],
    "FOC": ["friend of court", "foc recommendation", "foc order"],
    "Procedural": ["adjournment", "continuance", "scheduling", "case management"],
    "Attorney": ["withdrawal", "substitution of counsel", "appearance"],
}

MCR_2612_INDICATORS = [
    "without notice", "ex parte", "no hearing", "denied due process",
    "void", "voidable", "lack of jurisdiction", "fraud upon the court",
    "newly discovered evidence", "misconduct",
]

CONFIRMED_EX_PARTE = [
    {
        "description": "Andrew's Ex Parte Order — May 2024",
        "approximate_date": "2024-05",
        "party_affected": "Andrew James Pigors",
        "type": "Ex Parte",
        "case_number": "2024-001507-DC",
        "notes": "Confirmed ex-parte order affecting Plaintiff's rights",
        "mcr_2612_flags": ["ex parte", "without notice"],
    },
    {
        "description": "Emily's Ex Parte Order — August 2025",
        "approximate_date": "2025-08",
        "party_affected": "Emily A. Watson",
        "type": "Ex Parte",
        "case_number": "2024-001507-DC",
        "notes": "Confirmed ex-parte order obtained by Defendant",
        "mcr_2612_flags": ["ex parte", "without notice"],
    },
]


def get_db_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.row_factory = sqlite3.Row
    return conn


def get_tables(conn):
    return [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts_%'").fetchall()]


def classify_order(text):
    """Classify an order into categories."""
    text_lower = (text or "").lower()
    categories = []
    for cat, keywords in ORDER_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(cat)
    return categories if categories else ["Unclassified"]


def check_mcr_2612(text):
    """Check if an order has MCR 2.612 void/voidable indicators."""
    text_lower = (text or "").lower()
    flags = [indicator for indicator in MCR_2612_INDICATORS if indicator in text_lower]
    return flags


def extract_orders_from_db(conn, tables):
    """Extract order-related entries from all available tables."""
    orders = []

    # Check for docket_events table
    if "docket_events" in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(docket_events)").fetchall()]
        date_col = next((c for c in cols if "date" in c.lower()), None)
        text_cols = [c for c in cols if any(t in c.lower() for t in ["description", "event", "text", "type", "title"])]
        if date_col and text_cols:
            for tc in text_cols:
                rows = conn.execute(f"""
                    SELECT "{date_col}", "{tc}" FROM docket_events
                    WHERE "{tc}" IS NOT NULL
                    AND (lower("{tc}") LIKE '%order%' OR lower("{tc}") LIKE '%custody%'
                         OR lower("{tc}") LIKE '%ppo%' OR lower("{tc}") LIKE '%ex parte%')
                    LIMIT 500
                """).fetchall()
                for r in rows:
                    orders.append({
                        "date": str(r[0]) if r[0] else None,
                        "description": str(r[1])[:500],
                        "source": "docket_events",
                        "categories": classify_order(str(r[1])),
                        "mcr_2612_flags": check_mcr_2612(str(r[1])),
                    })

    # Mine evidence_quotes for order references
    if "evidence_quotes" in tables:
        rows = conn.execute("""
            SELECT date_ref, quote_text, evidence_category, legal_significance
            FROM evidence_quotes
            WHERE (lower(quote_text) LIKE '%order%' OR lower(quote_text) LIKE '%custody%'
                   OR lower(quote_text) LIKE '%ppo%' OR lower(quote_text) LIKE '%ex parte%'
                   OR lower(quote_text) LIKE '%parenting time%' OR lower(quote_text) LIKE '%support%'
                   OR lower(quote_text) LIKE '%contempt%')
            AND quote_text IS NOT NULL
            LIMIT 1000
        """).fetchall()
        for r in rows:
            orders.append({
                "date": str(r[0]) if r[0] else None,
                "description": str(r[1])[:500],
                "source": "evidence_quotes",
                "evidence_category": r[2],
                "legal_significance": str(r[3])[:200] if r[3] else None,
                "categories": classify_order(str(r[1])),
                "mcr_2612_flags": check_mcr_2612(str(r[1])),
            })

    # Mine filing_readiness for order-related vehicles
    if "filing_readiness" in tables:
        rows = conn.execute("""
            SELECT vehicle_name, status, total_score, gaps, strengths, created_at
            FROM filing_readiness
            WHERE lower(vehicle_name) LIKE '%order%' OR lower(vehicle_name) LIKE '%custody%'
                  OR lower(vehicle_name) LIKE '%ppo%' OR lower(vehicle_name) LIKE '%motion%'
            LIMIT 200
        """).fetchall()
        for r in rows:
            orders.append({
                "date": str(r[5]) if r[5] else None,
                "description": f"Filing: {r[0]} (Score: {r[2]}, Status: {r[1]})",
                "source": "filing_readiness",
                "categories": classify_order(str(r[0])),
                "gaps": str(r[3])[:200] if r[3] else None,
                "strengths": str(r[4])[:200] if r[4] else None,
                "mcr_2612_flags": check_mcr_2612(str(r[0])),
            })

    # Mine risk_events for order-related events
    if "risk_events" in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(risk_events)").fetchall()]
        text_cols = [c for c in cols if any(t in c.lower() for t in ["description", "event", "text", "type", "detail"])]
        date_cols = [c for c in cols if any(d in c.lower() for d in ["date", "time", "created"])]
        for tc in text_cols[:2]:
            dc = date_cols[0] if date_cols else None
            select = f'"{dc}", "{tc}"' if dc else f'NULL, "{tc}"'
            try:
                rows = conn.execute(f"""
                    SELECT {select} FROM risk_events
                    WHERE (lower("{tc}") LIKE '%order%' OR lower("{tc}") LIKE '%custody%'
                           OR lower("{tc}") LIKE '%ex parte%')
                    LIMIT 200
                """).fetchall()
                for r in rows:
                    orders.append({
                        "date": str(r[0]) if r[0] else None,
                        "description": str(r[1])[:500],
                        "source": "risk_events",
                        "categories": classify_order(str(r[1])),
                        "mcr_2612_flags": check_mcr_2612(str(r[1])),
                    })
            except Exception:
                continue

    # Mine court_rules for procedural requirements
    if "court_rules" in tables:
        rows = conn.execute("SELECT * FROM court_rules LIMIT 200").fetchall()
        for r in rows:
            d = dict(r)
            text_val = " ".join(str(v) for v in d.values() if v)
            if any(kw in text_val.lower() for kw in ["order", "custody", "ex parte", "ppo"]):
                orders.append({
                    "date": None,
                    "description": text_val[:500],
                    "source": "court_rules",
                    "categories": classify_order(text_val),
                    "mcr_2612_flags": [],
                })

    return orders


def main():
    print("=" * 70)
    print("TOOL #214 — Court Order Tracker")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = get_db_connection()
    db_orders = []
    db_stats = {}
    if conn:
        tables = get_tables(conn)
        db_orders = extract_orders_from_db(conn, tables)
        db_stats = {"tables_scanned": len(tables), "orders_found": len(db_orders)}
        conn.close()
        print(f"[DB] {len(tables)} tables scanned. {len(db_orders)} order-related entries found.")
    else:
        print("[WARN] DB not found — using confirmed orders only.")

    # Combine DB orders with confirmed ex-parte orders
    all_orders = CONFIRMED_EX_PARTE + db_orders

    # Categorize
    by_category = defaultdict(list)
    for o in all_orders:
        cats = o.get("categories", ["Unclassified"])
        for cat in cats:
            by_category[cat].append(o)

    # MCR 2.612 candidates
    mcr_2612_candidates = [o for o in all_orders if o.get("mcr_2612_flags")]

    # Sort by date where available
    dated_orders = sorted([o for o in all_orders if o.get("date")], key=lambda x: str(x["date"]))
    undated_orders = [o for o in all_orders if not o.get("date")]

    print(f"\n[ANALYSIS]")
    print(f"  Total order entries: {len(all_orders)}")
    print(f"  Confirmed ex-parte: {len(CONFIRMED_EX_PARTE)}")
    print(f"  DB-discovered: {len(db_orders)}")
    print(f"  MCR 2.612 candidates: {len(mcr_2612_candidates)}")
    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(items)}")

    # JSON report
    report = {
        "tool": "#214 — Court Order Tracker",
        "generated": datetime.now().isoformat(),
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "court": "14th Circuit Court, Family Division, Muskegon County",
        "judge": "Hon. Jenny L. McNeill",
        "total_orders": len(all_orders),
        "confirmed_ex_parte": CONFIRMED_EX_PARTE,
        "db_stats": db_stats,
        "category_counts": {k: len(v) for k, v in by_category.items()},
        "mcr_2612_candidates_count": len(mcr_2612_candidates),
        "mcr_2612_candidates": mcr_2612_candidates[:50],
        "dated_orders": dated_orders[:200],
        "undated_orders": undated_orders[:100],
    }
    json_path = REPORTS_DIR / "COURT_ORDER_TRACKER.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[OK] JSON: {json_path}")

    # MD report
    md = []
    md.append("# COURT ORDER TRACKER — Pigors v. Watson")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case Numbers:** 2024-001507-DC, 2023-5907-PP")
    md.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    md.append(f"**Judge:** Hon. Jenny L. McNeill")
    md.append(f"**Total Order Entries:** {len(all_orders)}")
    md.append("")

    # Category breakdown
    md.append("## Order Categories")
    md.append("")
    md.append("| Category | Count |")
    md.append("|----------|-------|")
    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        md.append(f"| {cat} | {len(items)} |")
    md.append("")

    # Confirmed Ex Parte Orders
    md.append("---")
    md.append("\n## Confirmed Ex Parte Orders")
    md.append("")
    for ep in CONFIRMED_EX_PARTE:
        md.append(f"### {ep['description']}")
        md.append(f"- **Approximate Date:** {ep['approximate_date']}")
        md.append(f"- **Party Affected:** {ep['party_affected']}")
        md.append(f"- **Case Number:** {ep['case_number']}")
        md.append(f"- **MCR 2.612 Flags:** {', '.join(ep['mcr_2612_flags'])}")
        md.append(f"- **Notes:** {ep['notes']}")
        md.append("")

    # MCR 2.612 Void/Voidable Analysis
    md.append("---")
    md.append("\n## MCR 2.612 — Relief from Judgment/Order Analysis")
    md.append("")
    md.append("> MCR 2.612(C)(1) provides grounds for relief from a final judgment or order:")
    md.append("> (a) Mistake, inadvertence, surprise, or excusable neglect")
    md.append("> (b) Newly discovered evidence")
    md.append("> (c) Fraud, misrepresentation, or other misconduct of an adverse party")
    md.append("> (d) The judgment is void")
    md.append("> (f) Any other reason justifying relief")
    md.append("")
    md.append(f"**{len(mcr_2612_candidates)} orders flagged as potential MCR 2.612 candidates:**")
    md.append("")
    for i, c in enumerate(mcr_2612_candidates[:30], 1):
        flags = ", ".join(c.get("mcr_2612_flags", []))
        md.append(f"{i}. **{c.get('date', 'Undated')}** [{c.get('source', '')}] — {c.get('description', '')[:200]}")
        md.append(f"   - MCR 2.612 indicators: {flags}")
        md.append("")

    # Chronological order list
    if dated_orders:
        md.append("---")
        md.append("\n## Chronological Order History")
        md.append("")
        for o in dated_orders[:100]:
            cats = ", ".join(o.get("categories", []))
            flag = " :warning:" if o.get("mcr_2612_flags") else ""
            md.append(f"- **{o['date']}** [{cats}]{flag} — {o['description'][:200]}")
        if len(dated_orders) > 100:
            md.append(f"\n*... {len(dated_orders) - 100} additional orders in JSON ...*")
        md.append("")

    md.append("---")
    md.append(f"\n*Tool #214 — Court Order Tracker — {datetime.now().isoformat()}*")

    md_path = REPORTS_DIR / "COURT_ORDER_TRACKER.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] MD:   {md_path}")
    print("[DONE] Tool #214 complete.")


if __name__ == "__main__":
    main()
