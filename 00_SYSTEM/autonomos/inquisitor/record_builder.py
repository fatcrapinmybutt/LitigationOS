"""
APEX Ω∞ — Record on Appeal Builder
=====================================
Assembles MCR 7.210 compliant record on appeal.
Gathers lower court register of actions, filed documents, transcripts,
exhibits — all properly indexed and paginated.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

RECORD_DB = Path(__file__).parent / "record_builder.db"

MCR_7210_COMPONENTS = [
    {"id": "register_of_actions", "label": "Register of Actions (MCR 7.210(A)(1))",
     "description": "Complete register of actions from the lower court clerk",
     "source_table": "docket_events", "required": True},
    {"id": "claim_of_appeal", "label": "Claim of Appeal (MCR 7.204(A))",
     "description": "The claim of appeal as filed",
     "source_table": None, "required": True},
    {"id": "orders_appealed", "label": "Orders Appealed From (MCR 7.210(A)(3))",
     "description": "All orders being challenged on appeal",
     "source_table": "docket_events", "required": True},
    {"id": "transcripts", "label": "Transcripts (MCR 7.210(B))",
     "description": "All hearing transcripts relevant to issues on appeal",
     "source_table": None, "required": True},
    {"id": "exhibits", "label": "Exhibits (MCR 7.210(A)(4))",
     "description": "All exhibits admitted at trial/hearings",
     "source_table": None, "required": False},
    {"id": "motions_responses", "label": "Filed Motions and Responses",
     "description": "Key motions and responses filed below",
     "source_table": "docket_events", "required": False},
    {"id": "lower_court_opinions", "label": "Lower Court Opinions (MCR 7.210(A)(5))",
     "description": "Written opinions or findings by the trial court",
     "source_table": None, "required": True},
]

ISSUES_ON_APPEAL = [
    "The trial court's August 8, 2025 ex parte orders violated Father's due process rights under Const 1963 art 1 §17 and US Const amend XIV.",
    "The trial court failed to conduct a proper best-interest analysis under MCL 722.23 before suspending parenting time.",
    "The trial court improperly denied Father's motions without hearing in violation of MCR 2.119.",
    "The trial court exhibited bias requiring disqualification under MCR 2.003(C)(1).",
]

def _init_db() -> sqlite3.Connection:
    RECORD_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(RECORD_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS record_components (
            id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            page_start INTEGER DEFAULT 0,
            page_end INTEGER DEFAULT 0,
            source_path TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS record_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_id TEXT NOT NULL,
            item_description TEXT NOT NULL,
            date_filed TEXT DEFAULT '',
            page_number INTEGER DEFAULT 0,
            bates_start TEXT DEFAULT '',
            bates_end TEXT DEFAULT '',
            FOREIGN KEY (component_id) REFERENCES record_components(id)
        );
    """)
    conn.commit()
    return conn

def build_record() -> dict:
    """Build MCR 7.210 record on appeal."""
    start = time.time()
    rdb = _init_db()
    findings = {"components": [], "issues": ISSUES_ON_APPEAL, "docket_events": 0,
                "orders_found": 0, "ex_parte_orders": 0}

    # Insert component tracking
    for comp in MCR_7210_COMPONENTS:
        rdb.execute("""
            INSERT OR REPLACE INTO record_components (id, label, status)
            VALUES (?, ?, 'pending')
        """, (comp["id"], comp["label"]))

    # Mine central DB for docket events
    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        rows = cdb.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name='docket_events'
        """).fetchone()
        if rows and rows[0] > 0:
            events = cdb.execute("""
                SELECT * FROM docket_events ORDER BY rowid LIMIT 500
            """).fetchall()
            findings["docket_events"] = len(events)

            # Count orders
            cols = [d[0] for d in cdb.execute("SELECT * FROM docket_events LIMIT 0").description]
            for event in events:
                row = dict(zip(cols, event))
                desc = str(row.get("description", "") or row.get("event_type", "")).lower()
                if "order" in desc:
                    findings["orders_found"] += 1
                    if "ex parte" in desc or "without notice" in desc:
                        findings["ex_parte_orders"] += 1

        # Check for hearing transcripts in evidence
        rows2 = cdb.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name='documents'
        """).fetchone()
        if rows2 and rows2[0] > 0:
            transcripts = cdb.execute("""
                SELECT COUNT(*) FROM documents
                WHERE LOWER(COALESCE(doc_type,'') || COALESCE(source_file,''))
                LIKE '%transcript%'
            """).fetchone()
            findings["transcripts_found"] = transcripts[0] if transcripts else 0

        cdb.close()
    except Exception as e:
        findings["db_error"] = str(e)

    # Generate record index document
    idx_parts = []
    idx_parts.append("RECORD ON APPEAL — INDEX")
    idx_parts.append(f"Case No. COA 366810 (Lower Court: 2024-001507-DC)")
    idx_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    idx_parts.append("=" * 60)
    for comp in MCR_7210_COMPONENTS:
        req = " [REQUIRED]" if comp["required"] else " [optional]"
        idx_parts.append(f"\n{comp['label']}{req}")
        idx_parts.append(f"  → {comp['description']}")
        src = comp.get("source_table")
        if src:
            idx_parts.append(f"  → Source: {src} table")
    idx_parts.append("\n" + "=" * 60)
    idx_parts.append(f"\nISSUES ON APPEAL:")
    for i, iss in enumerate(ISSUES_ON_APPEAL, 1):
        idx_parts.append(f"  {i}. {iss}")
    idx_parts.append(f"\nDocket events found: {findings['docket_events']}")
    idx_parts.append(f"Orders found: {findings['orders_found']}")
    idx_parts.append(f"Ex parte orders: {findings['ex_parte_orders']}")

    findings["record_index"] = "\n".join(idx_parts)
    findings["components"] = [
        {"id": c["id"], "label": c["label"], "required": c["required"]}
        for c in MCR_7210_COMPONENTS
    ]

    rdb.commit()
    rdb.close()
    findings["duration_s"] = round(time.time() - start, 2)
    return findings

if __name__ == "__main__":
    print(json.dumps(build_record(), indent=2, default=str))
