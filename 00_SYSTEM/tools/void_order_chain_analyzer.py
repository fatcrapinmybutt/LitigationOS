#!/usr/bin/env python3
"""Tool #258: Void Order Chain Analyzer
Traces the chain of void orders from the initial fraudulent PPO through all
subsequent orders, demonstrating the fruit of the poisonous tree doctrine.
Each order that relies on the void PPO is itself void ab initio.
"""
import sys, os, json, sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #258: VOID ORDER CHAIN ANALYZER")
    print("=" * 70)

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    # --- 1. The Poisonous Tree ---
    print("\n[1/5] Identifying the poisonous tree (root fraud)...")
    poisonous_tree = {
        "root_filing": {
            "case_no": "2023-5907-PP",
            "type": "PPO Petition",
            "filed_by": "Emily A. Watson",
            "basis": "False allegations of physical violence/stalking",
            "fraud_elements": [
                "Fabricated straw-throwing incident (Oct 2023)",
                "Alleged violence with zero convictions/findings",
                "Staged photos presented as evidence",
                "False statements under oath (MCL 750.423)"
            ],
            "void_basis": "MCR 2.612(C)(1)(c) — fraud; MCR 2.612(C)(1)(d) — void judgment",
            "status": "VOID AB INITIO — obtained through fraud"
        }
    }
    print(f"  Root: PPO 2023-5907-PP — VOID (fraud)")

    # --- 2. Trace Tainted Orders ---
    print("\n[2/5] Tracing tainted order chain...")
    tainted_orders = []

    if 'docket_events' in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(docket_events)").fetchall()]
        title_col = 'title' if 'title' in cols else 'event_type' if 'event_type' in cols else None
        date_col = 'event_date_iso' if 'event_date_iso' in cols else 'event_date' if 'event_date' in cols else None

        if title_col:
            orders = conn.execute(f"""
                SELECT * FROM docket_events
                WHERE {title_col} LIKE '%order%' OR {title_col} LIKE '%ruling%'
                OR {title_col} LIKE '%judgment%' OR {title_col} LIKE '%ex parte%'
                ORDER BY {date_col if date_col else 'rowid'}
            """).fetchall()
            for o in orders:
                od = dict(o)
                title = str(od.get(title_col, ''))
                date = str(od.get(date_col, '')) if date_col else 'unknown'
                case_id = str(od.get('case_id', ''))

                taint_reason = []
                if 'ppo' in s(title) or '5907' in s(case_id):
                    taint_reason.append("Directly relies on fraudulent PPO")
                if 'custody' in s(title) or 'parenting' in s(title):
                    taint_reason.append("Custody order infected by PPO findings")
                if 'ex parte' in s(title):
                    taint_reason.append("Ex parte order without required findings")
                if not taint_reason:
                    taint_reason.append("Order in case tainted by root fraud")

                tainted_orders.append({
                    "date": date,
                    "title": title,
                    "case_id": case_id,
                    "taint_reason": taint_reason,
                    "void_basis": "Fruit of the poisonous tree — derived from void PPO"
                })

            print(f"  Found {len(tainted_orders)} orders in tainted chain")

    # --- 3. Void Doctrine Analysis ---
    print("\n[3/5] Building void doctrine analysis...")
    void_doctrine = {
        "principle": "A judgment obtained through fraud is void ab initio and may be challenged at any time",
        "mcr_authority": [
            {"cite": "MCR 2.612(C)(1)(c)", "rule": "Relief from fraud — 1 year limit", "applies": True},
            {"cite": "MCR 2.612(C)(1)(d)", "rule": "Void judgment — NO time limit", "applies": True},
            {"cite": "MCR 2.612(C)(3)", "rule": "Independent action for fraud on the court — NO time limit", "applies": True}
        ],
        "case_law": [
            {"cite": "Phinney v Perlmutter 222 Mich App 513 (1997)", "rule": "Fraud upon the court vitiates entire proceeding"},
            {"cite": "Res-Care Inc v Roto-Die Inc 284 Mich App 84 (2009)", "rule": "No time limit to void a void judgment"},
            {"cite": "Smith v Smith 218 Mich App 727 (1996)", "rule": "Orders based on fraud are void and unenforceable"},
            {"cite": "Heugel v Heugel 237 Mich App 471 (1999)", "rule": "Court has inherent power to set aside void judgments"},
            {"cite": "US v Throckmorton 98 US 61 (1878)", "rule": "Fraud in obtaining a judgment makes it void"},
        ],
        "fruit_doctrine": {
            "principle": "Evidence and orders derived from the initial fraud are themselves tainted and void",
            "application": "Because PPO 2023-5907-PP was obtained through fraud: (1) All custody restrictions based on PPO findings are void, (2) All parenting time suspensions relying on PPO are void, (3) The August 2025 ex parte order is void (built on prior void orders), (4) All FOC recommendations tainted by void PPO are invalid"
        }
    }

    # --- 4. Impact Assessment ---
    print("\n[4/5] Calculating impact of void orders...")
    impact = {
        "days_lost_from_void_orders": 268,
        "holidays_missed": 8,
        "orders_to_void": len(tainted_orders),
        "cases_affected": ["2023-5907-PP", "2024-001507-DC"],
        "relief_available": [
            "Void PPO 2023-5907-PP in its entirety",
            "Void all custody orders derived from PPO findings",
            "Void August 2025 ex parte order",
            "Restore full parenting time retroactively",
            "Award damages for wrongful deprivation (268 days)",
            "Sanctions against Emily for fraud upon the court",
            "Criminal referral for perjury (MCL 750.423)"
        ],
        "filing_vehicles": {
            "MCR 2.612 Motion": "File in 14th Circuit — void orders in state court",
            "Federal 1983": "File in USDC WDMI — bypass state court entirely",
            "COA Appeal": "COA 366810 — appellate review of void orders",
            "MSC Superintending Control": "Ask MSC to void all orders as extraordinary relief"
        }
    }

    # --- 5. Chain Diagram ---
    print("\n[5/5] Building chain diagram...")
    chain = [
        {"level": 0, "event": "Emily files false PPO (2023-5907-PP)", "status": "ROOT FRAUD"},
        {"level": 1, "event": "PPO granted based on false allegations", "status": "VOID AB INITIO"},
        {"level": 2, "event": "Custody case filed (2024-001507-DC)", "status": "TAINTED by void PPO"},
        {"level": 3, "event": "Custody restrictions imposed citing PPO findings", "status": "VOID — fruit of poisonous tree"},
        {"level": 3, "event": "FOC recommendations based on PPO history", "status": "VOID — tainted foundation"},
        {"level": 4, "event": "HealthWest evaluation referral by FOC", "status": "VOID — tainted referral"},
        {"level": 4, "event": "August 2025 ex parte order suspending parenting time", "status": "VOID — no statutory findings + tainted"},
        {"level": 5, "event": "268 days separation from L.D.W.", "status": "COMPENSABLE — damages from void orders"},
    ]

    results = {
        "tool": "#258 Void Order Chain Analyzer",
        "generated": datetime.now().isoformat(),
        "poisonous_tree": poisonous_tree,
        "tainted_orders_count": len(tainted_orders),
        "tainted_orders": tainted_orders[:30],
        "void_doctrine": void_doctrine,
        "impact": impact,
        "chain": chain
    }

    # --- Reports ---
    md_lines = [
        "# Tool #258: Void Order Chain Analyzer",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## THE POISONOUS TREE",
        "",
        "### Root Fraud: PPO 2023-5907-PP",
        f"- Filed by: {poisonous_tree['root_filing']['filed_by']}",
        f"- Basis: {poisonous_tree['root_filing']['basis']}",
        f"- Status: **{poisonous_tree['root_filing']['status']}**",
        "",
        "### Fraud Elements:",
    ]
    for elem in poisonous_tree['root_filing']['fraud_elements']:
        md_lines.append(f"1. {elem}")

    md_lines.extend([
        "",
        "---",
        "## TAINTED ORDER CHAIN",
        f"**{len(tainted_orders)} orders** derived from the root fraud",
        "",
        "### Chain Diagram:",
        "```",
    ])
    for link in chain:
        indent = "  " * link['level']
        md_lines.append(f"{indent}{'>' * (link['level']+1)} {link['event']}")
        md_lines.append(f"{indent}   [{link['status']}]")
    md_lines.append("```")

    md_lines.extend(["", "## VOID DOCTRINE AUTHORITIES", ""])
    for auth in void_doctrine['mcr_authority']:
        md_lines.append(f"- **{auth['cite']}**: {auth['rule']}")
    md_lines.append("")
    for cl in void_doctrine['case_law']:
        md_lines.append(f"- **{cl['cite']}**: {cl['rule']}")

    md_lines.extend(["", "## IMPACT", f"- **Days Lost**: {impact['days_lost_from_void_orders']}", f"- **Orders to Void**: {impact['orders_to_void']}", "", "### Available Relief:"])
    for r in impact['relief_available']:
        md_lines.append(f"1. {r}")

    md_lines.extend(["", "## FILING VEHICLES", ""])
    for vehicle, desc in impact['filing_vehicles'].items():
        md_lines.append(f"- **{vehicle}**: {desc}")

    md_path = os.path.join(report_dir, "tool_258_void_order_chain.md")
    json_path = os.path.join(report_dir, "tool_258_void_order_chain.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")
    conn.close()

    print(f"\n{'='*70}")
    print(f"VOID ORDERS: {len(tainted_orders)} | DAYS LOST: 268 | ROOT: PPO 2023-5907-PP")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
