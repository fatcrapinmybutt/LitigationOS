"""
DELTA99 Ω∞ — Autonomous Report Generator
==========================================
Generates comprehensive daily, weekly, and on-demand reports covering all
AUTONOMOS subsystems: drive health, filing readiness, evidence strength,
threat assessment, system integrity, and separation day count.

Depends on: d99-self-heal, d99-drive-fortress
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, date
from dataclasses import dataclass

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, LITIGOS_ROOT, AUTONOMOS_ROOT

REPORT_DIR = LITIGOS_ROOT / "00_SYSTEM" / "reports"
REPORT_DB = AUTONOMOS_ROOT / "auto_report.db"

SEPARATION_DATE = date(2025, 8, 8)


def _init_db() -> sqlite3.Connection:
    REPORT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(REPORT_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT NOT NULL,
            output_path TEXT DEFAULT '',
            sections_count INTEGER DEFAULT 0,
            total_size_bytes INTEGER DEFAULT 0,
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _separation_days() -> int:
    today = date.today()
    return (today - SEPARATION_DATE).days


def _db_health(central: sqlite3.Connection) -> dict:
    """Check central DB health."""
    health = {"size_gb": 0, "tables": 0, "integrity": "unknown"}
    try:
        db_path = Path(str(CENTRAL_DB))
        if db_path.exists():
            health["size_gb"] = round(db_path.stat().st_size / (1024**3), 2)
    except Exception:
        pass

    try:
        tables = central.execute("""
            SELECT COUNT(*) FROM sqlite_master WHERE type='table'
        """).fetchone()[0]
        health["tables"] = tables
    except sqlite3.Error:
        pass

    try:
        result = central.execute("PRAGMA integrity_check(1)").fetchone()
        health["integrity"] = str(result[0]) if result else "unknown"
    except sqlite3.Error:
        health["integrity"] = "error"

    return health


def _filing_status(central: sqlite3.Connection) -> dict:
    """Summarize filing readiness."""
    status = {"total": 0, "ready": 0, "not_ready": 0, "top_3": []}
    try:
        rows = central.execute("""
            SELECT action_name, forum, readiness_pct
            FROM filing_readiness
            ORDER BY readiness_pct DESC
        """).fetchall()
        status["total"] = len(rows)
        status["ready"] = sum(1 for r in rows if r[2] and int(r[2]) >= 80)
        status["not_ready"] = status["total"] - status["ready"]
        status["top_3"] = [
            {"name": str(r[0]), "forum": str(r[1] or ""), "readiness": int(r[2] or 0)}
            for r in rows[:3]
        ]
    except sqlite3.Error:
        pass
    return status


def _evidence_summary(central: sqlite3.Connection) -> dict:
    """Summarize evidence counts."""
    summary = {}
    table_counts = {
        "evidence_quotes": "quote_text",
        "claims": "claim_id",
        "judicial_violations": "rowid",
        "impeachment_items": "rowid",
        "extracted_harms": "rowid",
        "contradiction_map": "rowid",
        "master_chronological_timeline": "rowid",
    }
    for table, col in table_counts.items():
        try:
            count = central.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            summary[table] = count
        except sqlite3.Error:
            summary[table] = "N/A"
    return summary


def _deadline_summary(central: sqlite3.Connection) -> list[dict]:
    """Get upcoming deadlines."""
    deadlines = []
    try:
        rows = central.execute("""
            SELECT description, due_date_iso FROM deadlines
            WHERE due_date_iso >= date('now')
            ORDER BY due_date_iso ASC LIMIT 10
        """).fetchall()
        for r in rows:
            days_left = "?"
            try:
                dl = datetime.fromisoformat(str(r[1]).split("T")[0])
                days_left = (dl - datetime.now()).days
            except (ValueError, TypeError):
                pass
            deadlines.append({
                "description": str(r[0])[:100],
                "date": str(r[1]),
                "days_left": days_left,
            })
    except sqlite3.Error:
        pass
    return deadlines


def _autonomos_status() -> dict:
    """Check AUTONOMOS subsystem status."""
    status = {"modules": {}, "dbs": {}}

    # Check module databases
    module_dbs = {
        "self_heal": AUTONOMOS_ROOT / "sentinel" / "self_heal.db",
        "drive_fortress": AUTONOMOS_ROOT / "sentinel" / "drive_fortress.db",
        "evidence_chain": AUTONOMOS_ROOT / "inquisitor" / "chain_validation.db",
        "citation_validator": AUTONOMOS_ROOT / "inquisitor" / "citation_validation.db",
        "judicial_tracker": AUTONOMOS_ROOT / "inquisitor" / "judicial_tracker.db",
        "temporal_anomaly": AUTONOMOS_ROOT / "inquisitor" / "temporal_anomaly.db",
        "watson_pattern": AUTONOMOS_ROOT / "inquisitor" / "watson_patterns.db",
        "cross_lane_fusion": AUTONOMOS_ROOT / "inquisitor" / "cross_lane_fusion.db",
        "semantic_dedup": AUTONOMOS_ROOT / "inquisitor" / "semantic_dedup.db",
        "filing_optimizer": AUTONOMOS_ROOT / "inquisitor" / "filing_optimizer.db",
        "nuclear_assembler": AUTONOMOS_ROOT / "inquisitor" / "nuclear_assembler.db",
        "auto_impeach": AUTONOMOS_ROOT / "inquisitor" / "auto_impeach.db",
        "counter_intel": AUTONOMOS_ROOT / "inquisitor" / "counter_intel.db",
        "predict_filing": AUTONOMOS_ROOT / "inquisitor" / "predict_filing.db",
    }

    for name, db_path in module_dbs.items():
        if db_path.exists():
            size_kb = round(db_path.stat().st_size / 1024, 1)
            status["dbs"][name] = {"exists": True, "size_kb": size_kb}
        else:
            status["dbs"][name] = {"exists": False}

    return status


def generate_report(report_type: str = "daily") -> dict:
    """Generate comprehensive status report."""
    start = time.time()
    rdb = _init_db()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    sep_days = _separation_days()
    db_health = _db_health(central)
    filings = _filing_status(central)
    evidence = _evidence_summary(central)
    deadlines = _deadline_summary(central)
    autonomos = _autonomos_status()

    central.close()

    # Build report
    now = datetime.now()
    report = {
        "report_type": report_type,
        "generated_at": now.isoformat(),
        "separation_days": sep_days,
        "separation_message": f"Day {sep_days} of parent-child separation (since Aug 8, 2025)",
        "db_health": db_health,
        "filing_status": filings,
        "evidence_counts": evidence,
        "upcoming_deadlines": deadlines,
        "autonomos_status": autonomos,
    }

    # Write markdown report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORT_DIR / f"{report_type}_{now.strftime('%Y%m%d')}.md"

    md = f"""# LitigationOS {report_type.title()} Report
## {now.strftime('%B %d, %Y %H:%M')}

---

### 🚨 SEPARATION COUNTER: DAY {sep_days}
Parent-child separation since August 8, 2025

---

### 💾 Database Health
- **Size:** {db_health['size_gb']} GB
- **Tables:** {db_health['tables']}
- **Integrity:** {db_health['integrity']}

### 📋 Filing Status
- **Total filings tracked:** {filings['total']}
- **Ready (≥80%):** {filings['ready']}
- **Not ready:** {filings['not_ready']}
- **Top filings:**
"""
    for f in filings.get("top_3", []):
        md += f"  - {f['name']} ({f['forum']}) — {f['readiness']}% ready\n"

    md += f"\n### 📊 Evidence Intelligence\n"
    for table, count in evidence.items():
        md += f"- **{table}:** {count:,} records\n" if isinstance(count, int) else f"- **{table}:** {count}\n"

    md += f"\n### ⏰ Upcoming Deadlines\n"
    for dl in deadlines:
        urgency = "🔴" if dl.get("days_left", 999) <= 7 else "🟡" if dl.get("days_left", 999) <= 14 else "🟢"
        md += f"- {urgency} **{dl['description']}** — {dl['date']} ({dl['days_left']} days)\n"

    md += f"\n### 🤖 AUTONOMOS Module Status\n"
    active = sum(1 for v in autonomos["dbs"].values() if v.get("exists"))
    md += f"- **Active modules:** {active}/{len(autonomos['dbs'])}\n"
    for name, info in sorted(autonomos["dbs"].items()):
        status = f"✅ {info.get('size_kb', 0)}KB" if info.get("exists") else "❌ Not initialized"
        md += f"  - {name}: {status}\n"

    md += f"\n---\n*Generated in {round(time.time() - start, 2)}s by DELTA99 Auto-Report Engine*\n"

    report_file.write_text(md, encoding="utf-8")
    report["output_path"] = str(report_file)

    # Also write to system startup location
    startup_report = LITIGOS_ROOT / "00_SYSTEM" / "DAILY_HEALTH_REPORT.md"
    startup_report.write_text(md, encoding="utf-8")

    rdb.execute("""
        INSERT INTO reports (report_type, output_path, sections_count, total_size_bytes)
        VALUES (?, ?, 6, ?)
    """, (report_type, str(report_file), len(md)))
    rdb.commit()
    rdb.close()

    return report


if __name__ == "__main__":
    rtype = sys.argv[1] if len(sys.argv) > 1 else "daily"
    result = generate_report(rtype)
    print(json.dumps(result, indent=2, default=str))
