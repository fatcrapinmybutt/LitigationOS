#!/usr/bin/env python3
"""
Tool #49 — MCR 7.210(B)(2) Settled Statement Builder
========================================================
When no transcript is available, Michigan appellate rules allow a
"settled statement" as substitute for the record on appeal.

MCR 7.210(B)(2): "If no transcript was made of the proceedings,
the appellant may prepare a statement from the best available
sources, including the appellant's recollection."

This tool generates a proper settled statement for COA 366810
by mining the database for hearing events, orders, and findings.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

CASE_INFO = {
    'lower_case': '2024-001507-DC',
    'coa_case': '366810',
    'plaintiff': 'Andrew James Pigors',
    'defendant': 'Emily A. Watson',
    'judge': 'Hon. Jenny L. McNeill',
    'court': '14th Circuit Court, Muskegon County',
    'division': 'Family Division',
}

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

def get_docket_events(conn):
    """Get chronological docket events."""
    events = []
    try:
        # Check which tables exist with date info
        tables_to_try = [
            ("docket_events", "event_date", "description"),
            ("timeline_events", "event_date", "description"),
            ("case_events", "date", "event"),
        ]
        
        for table, date_col, desc_col in tables_to_try:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                if date_col in cols and desc_col in cols:
                    rows = conn.execute(f"""
                        SELECT {date_col}, {desc_col} FROM {table}
                        WHERE {date_col} IS NOT NULL
                        ORDER BY {date_col}
                        LIMIT 200
                    """).fetchall()
                    for r in rows:
                        events.append({'date': r[0], 'description': r[1]})
                    if events:
                        break
            except:
                continue
    except Exception as e:
        events.append({'date': 'ERROR', 'description': str(e)})
    
    return events

def get_judicial_violations(conn):
    """Get McNeill violations for the settled statement."""
    violations = []
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(judicial_violations)").fetchall()]
        
        # Build query dynamically
        date_col = next((c for c in cols if 'date' in c.lower()), None)
        desc_col = next((c for c in cols if c in ('description', 'violation', 'violation_type', 'finding')), None)
        
        if desc_col:
            q = f"SELECT {date_col + ',' if date_col else ''} {desc_col} FROM judicial_violations"
            if date_col:
                q += f" ORDER BY {date_col}"
            q += " LIMIT 50"
            
            rows = conn.execute(q).fetchall()
            for r in rows:
                if date_col:
                    violations.append({'date': r[0], 'violation': r[1]})
                else:
                    violations.append({'violation': r[0]})
    except Exception as e:
        violations.append({'error': str(e)})
    
    return violations

def get_orders(conn):
    """Get court orders from the case."""
    orders = []
    tables = ['court_orders', 'orders', 'docket_events']
    
    for table in tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            date_col = next((c for c in cols if 'date' in c.lower()), None)
            desc_col = next((c for c in cols if c in ('description', 'order_type', 'title', 'event')), None)
            
            if desc_col:
                q = f"SELECT * FROM {table}"
                if 'order' in table or any('order' in c.lower() for c in cols):
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 100").fetchall()
                    for r in rows:
                        order = dict(r) if hasattr(r, 'keys') else {'data': str(r)}
                        orders.append(order)
                    if orders:
                        break
        except:
            continue
    
    return orders

def build_settled_statement(events, violations, orders):
    """Build the MCR 7.210(B)(2) settled statement."""
    lines = [
        "# SETTLED STATEMENT OF PROCEEDINGS",
        f"## Pursuant to MCR 7.210(B)(2)",
        "",
        "---",
        "",
        f"**Court of Appeals Case No.:** {CASE_INFO['coa_case']}",
        f"**Lower Court Case No.:** {CASE_INFO['lower_case']}",
        f"**Lower Court:** {CASE_INFO['court']}, {CASE_INFO['division']}",
        f"**Lower Court Judge:** {CASE_INFO['judge']}",
        f"**Appellant:** {CASE_INFO['plaintiff']}",
        f"**Appellee:** {CASE_INFO['defendant']}",
        "",
        "---",
        "",
        "## INTRODUCTION",
        "",
        "Appellant Andrew James Pigors respectfully submits this Settled Statement",
        "of Proceedings pursuant to MCR 7.210(B)(2). No transcripts of the lower",
        "court proceedings are available to Appellant. This statement has been",
        "prepared from the best available sources, including court records, filed",
        "documents, and Appellant's recollection of the proceedings.",
        "",
        "## PROCEDURAL HISTORY",
        "",
    ]
    
    if events:
        lines.append("The following is a chronological account of significant proceedings:")
        lines.append("")
        for i, evt in enumerate(events[:50], 1):
            date = evt.get('date', 'Unknown date')
            desc = evt.get('description', 'No description')
            lines.append(f"{i}. **{date}** — {desc}")
        lines.append("")
    else:
        lines.extend([
            "1. **2023** — Emily A. Watson filed a Personal Protection Order (PPO)",
            "   petition (Case No. 2023-5907-PP) containing fabricated allegations",
            "   of violence and stalking against Appellant.",
            "",
            "2. **May 2024** — Appellant filed an ex parte motion in the custody",
            "   proceeding (Case No. 2024-001507-DC).",
            "",
            "3. **August 2025** — Emily Watson obtained an ex parte order suspending",
            "   ALL of Appellant's parenting time without the required findings",
            "   under MCL 722.27a(3).",
            "",
            "[ANDREW_REQUIRED: Review and supplement with specific hearing dates,",
            "motions filed, and orders entered from your court records]",
            "",
        ])
    
    lines.extend([
        "## ISSUES PRESERVED FOR APPEAL",
        "",
        "The following issues were raised in the lower court and are preserved for appeal:",
        "",
        "1. Whether the trial court abused its discretion by suspending all parenting",
        "   time without making the required findings under MCL 722.27a(3).",
        "",
        "2. Whether the trial court violated Appellant's due process rights by",
        "   entering ex parte orders without notice or opportunity to be heard.",
        "",
        "3. Whether the trial court demonstrated actual bias requiring disqualification",
        "   under MCR 2.003(C)(1).",
        "",
        "4. Whether the trial court's reliance on unverified allegations, without",
        "   evidentiary hearing, constituted an abuse of discretion.",
        "",
        "5. Whether the trial court's pattern of conduct toward Appellant created",
        "   an appearance of impropriety under Canon 2 of the Michigan Code of",
        "   Judicial Conduct.",
        "",
    ])
    
    if violations:
        lines.extend([
            "## JUDICIAL CONDUCT CONCERNS",
            "",
            "The following conduct by the trial court is relevant to the issues on appeal:",
            "",
        ])
        for i, v in enumerate(violations[:20], 1):
            if 'violation' in v:
                lines.append(f"{i}. {v['violation']}")
            elif 'error' not in v:
                lines.append(f"{i}. {v}")
        lines.append("")
    
    lines.extend([
        "## CERTIFICATION",
        "",
        "I, Andrew James Pigors, hereby certify that this Settled Statement",
        "of Proceedings is true and accurate to the best of my knowledge,",
        "information, and belief. I have prepared this statement from the best",
        "available sources as permitted by MCR 7.210(B)(2).",
        "",
        "I further certify that no transcript of the proceedings described",
        "herein was made or is available to me.",
        "",
        "Respectfully submitted,",
        "",
        "",
        "___________________________",
        "Andrew James Pigors",
        "Appellant, In Propria Persona",
        "1977 Whitehall Road, Lot 17",
        "North Muskegon, MI 49445",
        "(231) 903-5690",
        "andrewjpigors@gmail.com",
        "",
        f"Dated: _______________",
        "",
        "---",
        "",
        "## SERVICE",
        "",
        "I certify that a copy of this Settled Statement was served on all",
        "parties as required by MCR 7.210(B)(2). The opposing party has 14 days",
        "from service to object to or propose amendments to this statement.",
        "If no objections are filed, the statement shall be settled as filed.",
        "",
        "Served on:",
        "- Emily A. Watson, 2160 Garland Drive, Norton Shores, MI 49441",
        "  Method: [First-class mail / Personal service]",
        "  Date: _______________",
    ])
    
    return '\n'.join(lines)

def main():
    print("=" * 70)
    print("SETTLED STATEMENT BUILDER — Tool #49")
    print(f"MCR 7.210(B)(2) — Substitute for Transcript")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = get_db_connection()
    
    # Gather data
    print("\n📋 Gathering docket events...")
    events = get_docket_events(conn)
    print(f"  Found {len(events)} events")
    
    print("\n⚖️ Gathering judicial violations...")
    violations = get_judicial_violations(conn)
    print(f"  Found {len(violations)} violations")
    
    print("\n📜 Gathering court orders...")
    orders = get_orders(conn)
    print(f"  Found {len(orders)} orders")
    
    conn.close()
    
    # Build the document
    print("\n📝 Building settled statement...")
    statement = build_settled_statement(events, violations, orders)
    word_count = len(statement.split())
    print(f"  {word_count} words generated")
    
    # Save to F9 package (COA brief package)
    f9_dirs = list(PKG_BASE.glob("PKG_F9_*"))
    if f9_dirs:
        output_path = f9_dirs[0] / "01D_SETTLED_STATEMENT.md"
        output_path.write_text(statement, encoding='utf-8')
        print(f"\n✅ Saved to: {output_path}")
    
    # Also save to reports
    report_path = REPORTS_DIR / "SETTLED_STATEMENT.md"
    report_path.write_text(statement, encoding='utf-8')
    print(f"✅ Report: {report_path}")
    
    # JSON report
    json_path = REPORTS_DIR / "settled_statement.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Settled Statement Builder (#49)',
        'case_info': CASE_INFO,
        'events_found': len(events),
        'violations_found': len(violations),
        'orders_found': len(orders),
        'word_count': word_count,
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n📊 Summary:")
    print(f"  Events: {len(events)} | Violations: {len(violations)} | Orders: {len(orders)}")
    print(f"  Words: {word_count} | Output: F9 package + reports")

if __name__ == '__main__':
    main()
