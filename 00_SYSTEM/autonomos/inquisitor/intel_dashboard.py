"""
APEX Ω∞ — Supreme Intelligence Dashboard
==========================================
Unified HTML+JSON command center aggregating ALL engine outputs.
Generates a comprehensive single-page intelligence report covering:
  - Case status overview with separation day counter
  - Deadline urgency matrix
  - Evidence strength by lane
  - Filing readiness scores
  - Adversary threat levels
  - Judicial violation severity
  - Financial damages totals
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime, date

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB, LITIGOS_ROOT

DASHBOARD_DB = Path(__file__).parent / "intel_dashboard.db"
OUTPUT_DIR = LITIGOS_ROOT / "00_SYSTEM" / "reports"

SEPARATION_DATE = date(2025, 8, 8)

def _init_db() -> sqlite3.Connection:
    DASHBOARD_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DASHBOARD_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dashboard_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_json TEXT NOT NULL,
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def _safe_count(cdb, query) -> int:
    try:
        return cdb.execute(query).fetchone()[0] or 0
    except Exception:
        return 0

def generate_dashboard() -> dict:
    """Generate comprehensive intelligence dashboard."""
    start = time.time()
    ddb = _init_db()
    today = date.today()
    sep_days = (today - SEPARATION_DATE).days
    if sep_days < 0:
        sep_days = 0

    dashboard = {
        "generated": datetime.now().isoformat(),
        "case": "Pigors v. Watson — 2024-001507-DC",
        "separation_days": sep_days,
        "separation_start": str(SEPARATION_DATE),
    }

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        # Evidence Intelligence
        dashboard["evidence"] = {
            "total_quotes": _safe_count(cdb, "SELECT COUNT(*) FROM evidence_quotes"),
            "total_harms": _safe_count(cdb, "SELECT COUNT(*) FROM extracted_harms"),
            "total_contradictions": _safe_count(cdb, "SELECT COUNT(*) FROM contradiction_map"),
            "total_impeachment": _safe_count(cdb, "SELECT COUNT(*) FROM impeachment_items"),
            "total_claims": _safe_count(cdb, "SELECT COUNT(*) FROM claims"),
            "total_timeline": _safe_count(cdb, "SELECT COUNT(*) FROM master_chronological_timeline"),
        }

        # Judicial Violations
        dashboard["judicial"] = {
            "total_violations": _safe_count(cdb, "SELECT COUNT(*) FROM judicial_violations"),
            "critical": _safe_count(cdb, "SELECT COUNT(*) FROM judicial_violations WHERE LOWER(COALESCE(severity,''))='critical'"),
            "high": _safe_count(cdb, "SELECT COUNT(*) FROM judicial_violations WHERE LOWER(COALESCE(severity,''))='high'"),
        }

        # Filing Readiness
        try:
            filings = cdb.execute("""
                SELECT vehicle_name, COALESCE(readiness_score, 0)
                FROM filing_readiness ORDER BY readiness_score DESC
            """).fetchall()
            dashboard["filings"] = [
                {"vehicle": f[0], "readiness": f[1]} for f in filings
            ]
        except Exception:
            dashboard["filings"] = []

        # Deadlines
        try:
            deadlines = cdb.execute("""
                SELECT description, due_date_iso, deadline_type
                FROM deadlines
                WHERE due_date_iso >= date('now')
                ORDER BY due_date_iso ASC LIMIT 15
            """).fetchall()
            dashboard["deadlines"] = []
            for d in deadlines:
                desc, due, dtype = d
                try:
                    days = (datetime.strptime(due, "%Y-%m-%d").date() - today).days
                except Exception:
                    days = -1
                urgency = "CRITICAL" if days <= 7 else "HIGH" if days <= 14 else "MEDIUM" if days <= 30 else "LOW"
                dashboard["deadlines"].append({
                    "description": desc, "due": due, "days": days,
                    "type": dtype, "urgency": urgency,
                })
        except Exception:
            dashboard["deadlines"] = []

        # OMEGA Scores
        try:
            scores = cdb.execute("""
                SELECT * FROM omega_scores ORDER BY rowid
            """).fetchall()
            cols = [d[0] for d in cdb.execute("SELECT * FROM omega_scores LIMIT 0").description]
            dashboard["omega_scores"] = [dict(zip(cols, s)) for s in scores]
        except Exception:
            dashboard["omega_scores"] = []

        # Adversary Summary
        try:
            adversaries = cdb.execute("""
                SELECT adversary_name, total_harms, harm_categories
                FROM adversary_harm_summary
                ORDER BY total_harms DESC
            """).fetchall()
            dashboard["adversaries"] = [
                {"name": a[0], "total_harms": a[1], "categories": a[2]}
                for a in adversaries
            ]
        except Exception:
            dashboard["adversaries"] = []

        # DB Health
        try:
            table_cnt = cdb.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table'
            """).fetchone()[0]
            dashboard["db_health"] = {
                "tables": table_cnt,
                "db_path": str(CENTRAL_DB),
            }
        except Exception:
            dashboard["db_health"] = {}

        cdb.close()
    except Exception as e:
        dashboard["db_error"] = str(e)

    # Generate HTML report
    html_parts = [
        "<!DOCTYPE html><html><head>",
        "<meta charset='utf-8'>",
        "<title>LitigationOS Intelligence Dashboard</title>",
        "<style>",
        "body{font-family:system-ui;margin:20px;background:#0a0a0a;color:#e0e0e0}",
        "h1{color:#ff4444;border-bottom:2px solid #ff4444;padding-bottom:10px}",
        "h2{color:#ffaa00;margin-top:30px}",
        ".metric{display:inline-block;background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:15px;margin:5px;min-width:150px;text-align:center}",
        ".metric .value{font-size:2em;font-weight:bold;color:#00ff88}",
        ".metric .label{color:#888;font-size:0.9em}",
        ".critical{color:#ff4444;font-weight:bold}",
        ".high{color:#ff8800}",
        ".medium{color:#ffaa00}",
        ".low{color:#00cc44}",
        "table{border-collapse:collapse;width:100%;margin:10px 0}",
        "th,td{border:1px solid #333;padding:8px;text-align:left}",
        "th{background:#1a1a2e;color:#ffaa00}",
        ".sep-counter{font-size:3em;color:#ff4444;text-align:center;padding:20px;background:#1a0000;border:2px solid #ff4444;border-radius:12px;margin:20px 0}",
        "</style></head><body>",
        f"<h1>⚖️ LitigationOS — Supreme Intelligence Dashboard</h1>",
        f"<p>Generated: {dashboard['generated']}</p>",
        f"<div class='sep-counter'>🚨 {sep_days} DAYS separated from child 🚨<br><small>Since {SEPARATION_DATE}</small></div>",
    ]

    ev = dashboard.get("evidence", {})
    html_parts.append("<h2>📊 Evidence Intelligence</h2>")
    for key, val in ev.items():
        label = key.replace("total_", "").replace("_", " ").title()
        html_parts.append(f"<div class='metric'><div class='value'>{val:,}</div><div class='label'>{label}</div></div>")

    jv = dashboard.get("judicial", {})
    html_parts.append(f"<h2>⚖️ Judicial Violations ({jv.get('total_violations', 0)} total)</h2>")
    html_parts.append(f"<div class='metric'><div class='value critical'>{jv.get('critical', 0)}</div><div class='label'>Critical</div></div>")
    html_parts.append(f"<div class='metric'><div class='value high'>{jv.get('high', 0)}</div><div class='label'>High</div></div>")

    dls = dashboard.get("deadlines", [])
    if dls:
        html_parts.append("<h2>📅 Upcoming Deadlines</h2><table><tr><th>Description</th><th>Due</th><th>Days</th><th>Urgency</th></tr>")
        for d in dls:
            u_class = d.get('urgency', 'low').lower()
            html_parts.append(f"<tr><td>{d.get('description','')}</td><td>{d.get('due','')}</td><td>{d.get('days','')}</td><td class='{u_class}'>{d.get('urgency','')}</td></tr>")
        html_parts.append("</table>")

    html_parts.append("</body></html>")

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_file = OUTPUT_DIR / "intelligence_dashboard.html"
    json_file = OUTPUT_DIR / "intelligence_dashboard.json"
    html_file.write_text("\n".join(html_parts), encoding="utf-8")
    json_file.write_text(json.dumps(dashboard, indent=2, default=str), encoding="utf-8")

    # Snapshot in DB
    ddb.execute("INSERT INTO dashboard_snapshots (snapshot_json) VALUES (?)",
                (json.dumps(dashboard, default=str),))
    ddb.commit()
    ddb.close()

    dashboard["outputs"] = {"html": str(html_file), "json": str(json_file)}
    dashboard["duration_s"] = round(time.time() - start, 2)
    return dashboard

if __name__ == "__main__":
    print(json.dumps(generate_dashboard(), indent=2, default=str))
