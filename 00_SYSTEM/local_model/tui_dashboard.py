#!/usr/bin/env python3
"""
THE MANBEARPIG — LitigationOS TUI Dashboard
============================================
Rich terminal dashboard showing real-time litigation system status.

Usage:
    python tui_dashboard.py          # Launch interactive TUI (requires terminal)
    python tui_dashboard.py --text   # Plain-text fallback output
"""

import sqlite3
import json
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
SEPARATION_START = date(2024, 7, 1)

CASE_LANES = [
    ("A", "Watson Custody", "2024-001507-DC", "14th Circuit Court, Muskegon County", "Hon. Jenny L. McNeill", "Active"),
    ("B", "Shady Oaks Housing", "—", "Related proceedings", "—", "Active"),
    ("C", "Convergence", "MULTI", "Cross-lane coordination", "Various", "Active"),
    ("D", "PPO", "2023-5907-PP", "14th Circuit Court, Muskegon County", "Hon. Jenny L. McNeill", "Active"),
    ("E", "Judicial Misconduct", "MULTI", "JTC / MSC", "Various", "Active"),
    ("F", "Appellate", "COA 366810", "Michigan Court of Appeals", "Panel TBD", "Active"),
]

FILINGS_ROOT = r"C:\Users\andre\LitigationOS\04_COURT_FILINGS"

FILING_PACKAGES = [
    ("MSC Complaint Superintending Control", r"04_MSC\MSC_COMPLAINT_SUPERINTENDING_CONTROL_v2", "MSC"),
    ("JTC Formal Complaint", r"03_JTC\JTC_FORMAL_COMPLAINT_v2", "JTC"),
    ("Emergency Motion Restore Parenting", r"LANE_A\EMERGENCY_MOTION_RESTORE_PARENTING_TIME_v2", "14th Circuit"),
    ("Motion for Reconsideration", r"LANE_A\MOTION_FOR_RECONSIDERATION_v2", "14th Circuit"),
    ("Motion for Disqualification", r"LANE_A\MOTION_FOR_DISQUALIFICATION_v2", "Chief Judge"),
    ("COA Appellant Brief 366810", r"LANE_F\COA_APPELLANT_BRIEF_366810_v2", "COA"),
    ("COA Emergency Application", r"LANE_F\COA_EMERGENCY_APPLICATION_366810_v2", "COA"),
]

# ---------------------------------------------------------------------------
# Database helpers (read-only, error-safe)
# ---------------------------------------------------------------------------

def _connect_db():
    """Return a read-only SQLite connection or None on failure."""
    try:
        if not os.path.exists(DB_PATH):
            return None
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None


def _safe_query(conn, sql, params=(), default=None):
    """Execute a read-only query; return rows or *default* on error."""
    if conn is None:
        return default if default is not None else []
    try:
        cur = conn.execute(sql, params)
        return cur.fetchall()
    except Exception:
        return default if default is not None else []


def _safe_scalar(conn, sql, params=(), default=0):
    """Return a single scalar value from a query."""
    rows = _safe_query(conn, sql, params, default=[])
    if rows and len(rows) > 0:
        return rows[0][0] if rows[0][0] is not None else default
    return default


def separation_days():
    """Days of parent-child separation since July 1 2024."""
    return (date.today() - SEPARATION_START).days


# ---------------------------------------------------------------------------
# Data-gathering functions
# ---------------------------------------------------------------------------

def gather_system_health(conn):
    """Return dict of system health metrics."""
    health = {
        "db_connected": conn is not None,
        "db_size": "N/A",
        "table_count": 0,
        "total_rows": 0,
        "model_loaded": False,
        "cache_status": "unknown",
    }
    if conn is None:
        return health

    # DB file size
    try:
        size_bytes = os.path.getsize(DB_PATH)
        if size_bytes >= 1_073_741_824:
            health["db_size"] = f"{size_bytes / 1_073_741_824:.2f} GB"
        else:
            health["db_size"] = f"{size_bytes / 1_048_576:.1f} MB"
    except OSError:
        pass

    # Table count
    tables = _safe_query(
        conn,
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
    )
    health["table_count"] = len(tables)

    # Total rows across all tables (sample first 100 tables)
    total = 0
    for t in tables[:100]:
        tname = t[0]
        safe_name = tname.replace('"', '""')
        count = _safe_scalar(conn, f'SELECT COUNT(*) FROM "{safe_name}"', default=0)
        total += count
    health["total_rows"] = total

    # Model loaded check
    model_dir = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\model_data")
    health["model_loaded"] = model_dir.exists() and any(model_dir.iterdir()) if model_dir.exists() else False

    # Cache status
    cache_dir = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\cache")
    if cache_dir.exists():
        cache_files = list(cache_dir.glob("*"))
        health["cache_status"] = f"{len(cache_files)} entries"
    else:
        health["cache_status"] = "no cache dir"

    return health


def gather_deadlines(conn, limit=15):
    """Return list of deadline dicts sorted by date."""
    rows = _safe_query(
        conn,
        "SELECT title, due_date_iso, basis_authority, status "
        "FROM deadlines ORDER BY due_date_iso ASC LIMIT ?",
        (limit,),
    )
    deadlines = []
    today = date.today()
    for r in rows:
        title = r[0] or ""
        due = r[1] or ""
        authority = r[2] or ""
        status = r[3] or ""
        # Urgency
        urgency = "green"
        try:
            due_date = date.fromisoformat(due[:10])
            delta = (due_date - today).days
            if delta < 0:
                urgency = "red"
            elif delta <= 7:
                urgency = "yellow"
        except (ValueError, TypeError):
            pass
        deadlines.append({
            "title": title,
            "due_date": due,
            "authority": authority,
            "status": status,
            "urgency": urgency,
        })
    return deadlines


def gather_filing_readiness(conn, limit=5):
    """Return top filing candidates with readiness scores."""
    rows = _safe_query(
        conn,
        "SELECT action_name, lane, overall_score, gaps "
        "FROM legal_action_scores ORDER BY overall_score DESC LIMIT ?",
        (limit,),
    )
    results = []
    for r in rows:
        results.append({
            "action": r[0] or "",
            "lane": r[1] or "",
            "score": r[2] if r[2] is not None else 0,
            "gaps": r[3] or "",
        })
    return results


def gather_evidence_stats(conn):
    """Return evidence / intelligence counts."""
    stats = {}
    for table in ("contradiction_map", "impeachment_items", "evidence_quotes", "judicial_violations"):
        safe = table.replace('"', '""')
        stats[table] = _safe_scalar(conn, f'SELECT COUNT(*) FROM "{safe}"', default=0)
    return stats


def gather_retrieval_stats(conn):
    """Return retrieval engine statistics."""
    stats = {
        "fts5_tables": 0,
        "bm25_index": "N/A",
        "lsi_index": "N/A",
        "epoch_engines": "N/A",
    }
    # Count FTS5 virtual tables
    fts_rows = _safe_query(
        conn,
        "SELECT name FROM sqlite_master WHERE sql LIKE '%fts5%'",
    )
    stats["fts5_tables"] = len(fts_rows)

    # BM25 index size from tfidf_index
    bm25_count = _safe_scalar(conn, "SELECT COUNT(*) FROM tfidf_index", default=0)
    stats["bm25_index"] = f"{bm25_count:,} terms"

    # LSI / semantic engine check
    lsi_path = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\local_model\model_data")
    if lsi_path.exists():
        lsi_files = list(lsi_path.glob("*.index")) + list(lsi_path.glob("*.pkl"))
        stats["lsi_index"] = f"{len(lsi_files)} files"

    # EPOCH engines — count from system_registry if available
    epoch_count = _safe_scalar(
        conn,
        "SELECT COUNT(*) FROM system_registry WHERE name LIKE '%epoch%' OR name LIKE '%engine%'",
        default=0,
    )
    stats["epoch_engines"] = f"{epoch_count} registered" if epoch_count else "not registered"

    return stats


def gather_lane_fsm_states(conn):
    """Return FSM states for each lane if available."""
    states = {}
    rows = _safe_query(
        conn,
        "SELECT case_lane, status FROM vehicles GROUP BY case_lane",
    )
    for r in rows:
        states[r[0]] = r[1] or "unknown"
    return states


def gather_filing_packages():
    """Check v2 filing packages for .md and .docx versions."""
    results = []
    for name, rel_path, forum in FILING_PACKAGES:
        base = os.path.join(FILINGS_ROOT, rel_path)
        md_path = base + ".md"
        docx_path = base + ".docx"
        md_exists = os.path.isfile(md_path)
        md_size = "N/A"
        if md_exists:
            try:
                size = os.path.getsize(md_path)
                md_size = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
            except OSError:
                md_size = "err"
        docx_exists = os.path.isfile(docx_path)
        results.append({
            "name": name,
            "md_exists": md_exists,
            "md_size": md_size,
            "docx_exists": docx_exists,
            "forum": forum,
        })
    return results


def gather_engine_metrics(conn):
    """Return engine and operational metrics."""
    metrics = {
        "total_engines": _safe_scalar(
            conn, "SELECT COUNT(*) FROM engine_metrics", default=0,
        ),
        "persistent_memories": _safe_scalar(
            conn, "SELECT COUNT(*) FROM memory_store", default=0,
        ),
        "self_evolve_cycles": _safe_scalar(
            conn,
            "SELECT COUNT(*) FROM engine_metrics WHERE engine='self_evolve'",
            default=0,
        ),
        "recent_errors": _safe_scalar(
            conn,
            "SELECT COUNT(*) FROM error_telemetry "
            "WHERE timestamp >= datetime('now', '-1 day')",
            default=0,
        ),
        "scan_cataloged": _safe_scalar(
            conn, "SELECT COUNT(*) FROM scan_inventory", default=0,
        ),
        "scan_ingested": _safe_scalar(
            conn, "SELECT COUNT(*) FROM scan_inventory WHERE ingested=1", default=0,
        ),
    }
    return metrics


def gather_convergence_status(conn):
    """Return convergence / linking statistics."""
    status = {
        "claim_evidence_links": _safe_scalar(
            conn, "SELECT COUNT(*) FROM claim_evidence_links", default=0,
        ),
        "bif_evidence_links": _safe_scalar(
            conn, "SELECT COUNT(*) FROM bif_evidence_links", default=0,
        ),
        "authority_chains": _safe_scalar(
            conn, "SELECT COUNT(*) FROM authority_chains", default=0,
        ),
        "supported_claims": _safe_scalar(
            conn, "SELECT COUNT(*) FROM claims WHERE status='supported'", default=0,
        ),
        "citation_validation_rate": "N/A",
    }
    rows = _safe_query(
        conn, "SELECT AVG(authority_score) FROM filing_readiness",
    )
    if rows and rows[0][0] is not None:
        status["citation_validation_rate"] = f"{rows[0][0]:.1f}%"
    return status


# ---------------------------------------------------------------------------
# Plain-text fallback dashboard
# ---------------------------------------------------------------------------

def print_dashboard():
    """Print a plain-text dashboard to stdout (no TUI required)."""
    sep = "=" * 78
    thin = "-" * 78
    conn = _connect_db()

    health = gather_system_health(conn)
    deadlines = gather_deadlines(conn)
    filings = gather_filing_readiness(conn)
    ev_stats = gather_evidence_stats(conn)
    ret_stats = gather_retrieval_stats(conn)
    fsm_states = gather_lane_fsm_states(conn)
    pkg_stats = gather_filing_packages()
    eng_metrics = gather_engine_metrics(conn)
    conv_status = gather_convergence_status(conn)
    days = separation_days()

    print(sep)
    print("  THE MANBEARPIG — LitigationOS Command Center".center(78))
    print(sep)
    print()

    # Separation counter
    print(f"  *** {days} DAYS PARENT-CHILD SEPARATION (since 2024-07-01) ***".center(78))
    print()

    # System Health
    print(thin)
    print("  SYSTEM HEALTH")
    print(thin)
    print(f"  DB Connected:   {'YES' if health['db_connected'] else 'NO'}")
    print(f"  DB Size:        {health['db_size']}")
    print(f"  Tables:         {health['table_count']}")
    print(f"  Total Rows:     {health['total_rows']:,}")
    print(f"  Model Loaded:   {'YES' if health['model_loaded'] else 'NO'}")
    print(f"  Cache:          {health['cache_status']}")
    print()

    # Case Lanes
    print(thin)
    print("  CASE LANES")
    print(thin)
    print(f"  {'Lane':<5} {'Name':<22} {'Case #':<18} {'Court':<30} {'Status':<8} {'FSM'}")
    print(f"  {'----':<5} {'----':<22} {'------':<18} {'-----':<30} {'------':<8} {'---'}")
    for lane_id, name, case_num, court, judge, status in CASE_LANES:
        fsm = fsm_states.get(lane_id, "—")
        court_short = court[:28] + ".." if len(court) > 30 else court
        print(f"  {lane_id:<5} {name:<22} {case_num:<18} {court_short:<30} {status:<8} {fsm}")
    print()

    # Deadlines
    print(thin)
    print("  UPCOMING DEADLINES")
    print(thin)
    if deadlines:
        print(f"  {'Urgency':<9} {'Due Date':<14} {'Title':<35} {'Authority':<18}")
        print(f"  {'-------':<9} {'--------':<14} {'-----':<35} {'---------':<18}")
        for d in deadlines[:10]:
            tag = {"red": "[OVERDUE]", "yellow": "[< 7 DAY]", "green": "[  OK   ]"}.get(d["urgency"], "[  ?  ]")
            title_short = d["title"][:33] + ".." if len(d["title"]) > 35 else d["title"]
            print(f"  {tag:<9} {d['due_date'][:10]:<14} {title_short:<35} {d['authority'][:18]}")
    else:
        print("  No deadlines found in database.")
    print()

    # Filing Readiness
    print(thin)
    print("  FILING READINESS (Top 5)")
    print(thin)
    if filings:
        print(f"  {'Action':<35} {'Lane':<8} {'Score':<8} {'Gaps'}")
        print(f"  {'------':<35} {'----':<8} {'-----':<8} {'----'}")
        for f in filings:
            action_short = f["action"][:33] + ".." if len(f["action"]) > 35 else f["action"]
            print(f"  {action_short:<35} {f['lane']:<8} {f['score']:<8} {f['gaps'][:30]}")
    else:
        print("  No filing readiness scores found.")
    print()

    # Evidence Stats
    print(thin)
    print("  EVIDENCE & INTELLIGENCE")
    print(thin)
    print(f"  Contradictions:       {ev_stats.get('contradiction_map', 0):,}")
    print(f"  Impeachment Items:    {ev_stats.get('impeachment_items', 0):,}")
    print(f"  Evidence Quotes:      {ev_stats.get('evidence_quotes', 0):,}")
    print(f"  Judicial Violations:  {ev_stats.get('judicial_violations', 0):,}")
    print()

    # Retrieval Stats
    print(thin)
    print("  RETRIEVAL ENGINES")
    print(thin)
    print(f"  FTS5 Tables:    {ret_stats['fts5_tables']}")
    print(f"  BM25 Index:     {ret_stats['bm25_index']}")
    print(f"  LSI Index:      {ret_stats['lsi_index']}")
    print(f"  EPOCH Engines:  {ret_stats['epoch_engines']}")
    print()

    # Filing Package Status
    print(thin)
    print("  FILING PACKAGE STATUS (v2 Court-Ready)")
    print(thin)
    print(f"  {'Document':<40} {'MD Size':<10} {'DOCX':<6} {'Forum'}")
    print(f"  {'--------':<40} {'-------':<10} {'----':<6} {'-----'}")
    for p in pkg_stats:
        md_col = p["md_size"] if p["md_exists"] else "—"
        docx_col = "\u2713" if p["docx_exists"] else "\u2717"
        print(f"  {p['name']:<40} {md_col:<10} {docx_col:<6} {p['forum']}")
    print()

    # Engine Metrics
    print(thin)
    print("  ENGINE METRICS")
    print(thin)
    print(f"  Total Engines:          {eng_metrics['total_engines']:,}")
    print(f"  Persistent Memories:    {eng_metrics['persistent_memories']:,}")
    print(f"  Self-Evolve Cycles:     {eng_metrics['self_evolve_cycles']:,}")
    print(f"  Errors (last 24h):      {eng_metrics['recent_errors']:,}")
    print(f"  Scan Cataloged:         {eng_metrics['scan_cataloged']:,}")
    print(f"  Scan Ingested:          {eng_metrics['scan_ingested']:,}")
    print()

    # Convergence Status
    print(thin)
    print("  CONVERGENCE STATUS")
    print(thin)
    print(f"  Claim-Evidence Links:   {conv_status['claim_evidence_links']:,}")
    print(f"  BIF Factor Links:       {conv_status['bif_evidence_links']:,}")
    print(f"  Authority Chains:       {conv_status['authority_chains']:,}")
    print(f"  Supported Claims:       {conv_status['supported_claims']:,}")
    print(f"  Citation Valid. Rate:   {conv_status['citation_validation_rate']}")
    print()

    print(sep)
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(78))
    print(sep)

    if conn:
        conn.close()


def get_dashboard_data() -> dict:
    """Return dashboard data as a JSON-serializable dict (for JSON-RPC)."""
    conn = _connect_db()
    data = {
        "system_health": gather_system_health(conn),
        "deadlines": gather_deadlines(conn),
        "filing_readiness": gather_filing_readiness(conn),
        "evidence_stats": gather_evidence_stats(conn),
        "retrieval_stats": gather_retrieval_stats(conn),
        "lane_states": gather_lane_fsm_states(conn),
        "filing_packages": gather_filing_packages(),
        "engine_metrics": gather_engine_metrics(conn),
        "convergence_status": gather_convergence_status(conn),
        "separation_days": separation_days(),
    }
    # EPOCH v7.0: Add autonomous intelligence metrics
    if conn:
        try:
            mem_count = conn.execute("SELECT COUNT(*) FROM memory_store").fetchone()[0]
            data["persistent_memories"] = mem_count
        except Exception:
            data["persistent_memories"] = 0
        try:
            scan_total = conn.execute("SELECT COUNT(*) FROM scan_inventory").fetchone()[0]
            scan_ingested = conn.execute("SELECT COUNT(*) FROM scan_inventory WHERE ingested=1").fetchone()[0]
            data["scan_inventory"] = {"cataloged": scan_total, "ingested": scan_ingested}
        except Exception:
            data["scan_inventory"] = {"cataloged": 0, "ingested": 0}
        try:
            health_entries = conn.execute("SELECT COUNT(*) FROM system_health_log").fetchone()[0]
            data["health_log_entries"] = health_entries
        except Exception:
            data["health_log_entries"] = 0
        try:
            metrics = conn.execute("SELECT COUNT(*) FROM engine_metrics").fetchone()[0]
            data["engine_metrics_count"] = metrics
        except Exception:
            data["engine_metrics_count"] = 0
    data["epoch_version"] = "v7.0"
    data["total_engines"] = 52
    data["json_rpc_methods"] = 106
    if conn:
        conn.close()
    return data


# ---------------------------------------------------------------------------
# Textual TUI Dashboard
# ---------------------------------------------------------------------------

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import Header, Footer, Static, Label, DataTable
    from textual.binding import Binding
    from textual import on

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


if TEXTUAL_AVAILABLE:

    class ManbearpigDashboard(App):
        """THE MANBEARPIG — LitigationOS TUI Command Center."""

        TITLE = "THE MANBEARPIG — LitigationOS Command Center"
        SUB_TITLE = "Pigors v. Watson | Michigan Consolidated Litigation"

        CSS = """
        Screen {
            background: $surface-darken-1;
        }

        #separation-banner {
            width: 100%;
            height: 3;
            content-align: center middle;
            text-align: center;
            background: $error;
            color: $text;
            text-style: bold;
            margin-bottom: 1;
        }

        .panel-title {
            text-style: bold;
            color: $accent;
            padding: 0 1;
            margin-bottom: 0;
        }

        .section-box {
            border: solid $primary;
            padding: 1 2;
            margin: 0 1 1 1;
            height: auto;
        }

        #health-panel {
            border: solid $success;
        }

        #evidence-panel {
            border: solid $warning;
        }

        #retrieval-panel {
            border: solid $primary;
        }

        #deadlines-panel {
            border: solid $error;
            height: auto;
            max-height: 18;
        }

        #lanes-panel {
            border: solid $accent;
            height: auto;
            max-height: 14;
        }

        #filing-panel {
            border: solid $success;
            height: auto;
            max-height: 14;
        }

        .top-row {
            height: auto;
            max-height: 14;
        }

        .mid-row {
            height: auto;
            max-height: 18;
        }

        .bot-row {
            height: auto;
            max-height: 14;
        }

        .stat-label {
            padding: 0 1;
        }

        .stat-value {
            color: $text;
            text-style: bold;
            padding: 0 1;
        }

        .urgency-red {
            color: red;
            text-style: bold;
        }

        .urgency-yellow {
            color: yellow;
        }

        .urgency-green {
            color: green;
        }

        DataTable {
            height: auto;
            max-height: 12;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit", show=True),
            Binding("r", "refresh_data", "Refresh", show=True),
            Binding("d", "toggle_dark", "Dark Mode", show=True),
        ]

        def compose(self) -> ComposeResult:
            yield Header()

            with ScrollableContainer():
                # Separation banner
                yield Static(
                    f"★  {separation_days()} DAYS PARENT-CHILD SEPARATION  ★",
                    id="separation-banner",
                )

                # Top row: System Health | Evidence Stats | Retrieval Stats
                with Horizontal(classes="top-row"):
                    with Vertical(id="health-panel", classes="section-box"):
                        yield Label("⚙ SYSTEM HEALTH", classes="panel-title")
                        yield Static("Loading…", id="health-content")

                    with Vertical(id="evidence-panel", classes="section-box"):
                        yield Label("🔍 EVIDENCE & INTELLIGENCE", classes="panel-title")
                        yield Static("Loading…", id="evidence-content")

                    with Vertical(id="retrieval-panel", classes="section-box"):
                        yield Label("📡 RETRIEVAL ENGINES", classes="panel-title")
                        yield Static("Loading…", id="retrieval-content")

                # Mid row: Case Lanes
                with Vertical(id="lanes-panel", classes="section-box mid-row"):
                    yield Label("⚖ CASE LANES", classes="panel-title")
                    yield DataTable(id="lanes-table")

                # Mid row: Deadlines
                with Vertical(id="deadlines-panel", classes="section-box mid-row"):
                    yield Label("📅 UPCOMING DEADLINES", classes="panel-title")
                    yield DataTable(id="deadlines-table")

                # Bottom row: Filing Readiness
                with Vertical(id="filing-panel", classes="section-box bot-row"):
                    yield Label("📋 FILING READINESS (Top 5)", classes="panel-title")
                    yield DataTable(id="filing-table")

            yield Footer()

        def on_mount(self) -> None:
            """Load all data on first mount."""
            self._setup_tables()
            self._load_data()

        def _setup_tables(self) -> None:
            """Configure DataTable columns."""
            lanes_tbl = self.query_one("#lanes-table", DataTable)
            lanes_tbl.add_columns("Lane", "Name", "Case #", "Court", "Judge", "Status", "FSM")

            deadlines_tbl = self.query_one("#deadlines-table", DataTable)
            deadlines_tbl.add_columns("Urgency", "Due Date", "Title", "Authority", "Status")

            filing_tbl = self.query_one("#filing-table", DataTable)
            filing_tbl.add_columns("Action", "Lane", "Score", "Gaps")

        def _load_data(self) -> None:
            """Query the DB and populate all panels."""
            conn = _connect_db()

            # --- System Health ---
            health = gather_system_health(conn)
            health_text = (
                f"DB Connected:  {'✅ YES' if health['db_connected'] else '❌ NO'}\n"
                f"DB Size:       {health['db_size']}\n"
                f"Tables:        {health['table_count']}\n"
                f"Total Rows:    {health['total_rows']:,}\n"
                f"Model Loaded:  {'✅ YES' if health['model_loaded'] else '❌ NO'}\n"
                f"Cache:         {health['cache_status']}"
            )
            self.query_one("#health-content", Static).update(health_text)

            # --- Evidence Stats ---
            ev = gather_evidence_stats(conn)
            ev_text = (
                f"Contradictions:      {ev.get('contradiction_map', 0):,}\n"
                f"Impeachment Items:   {ev.get('impeachment_items', 0):,}\n"
                f"Evidence Quotes:     {ev.get('evidence_quotes', 0):,}\n"
                f"Judicial Violations: {ev.get('judicial_violations', 0):,}"
            )
            self.query_one("#evidence-content", Static).update(ev_text)

            # --- Retrieval Stats ---
            ret = gather_retrieval_stats(conn)
            ret_text = (
                f"FTS5 Tables:   {ret['fts5_tables']}\n"
                f"BM25 Index:    {ret['bm25_index']}\n"
                f"LSI Index:     {ret['lsi_index']}\n"
                f"EPOCH Engines: {ret['epoch_engines']}"
            )
            self.query_one("#retrieval-content", Static).update(ret_text)

            # --- Case Lanes ---
            fsm_states = gather_lane_fsm_states(conn)
            lanes_tbl = self.query_one("#lanes-table", DataTable)
            lanes_tbl.clear()
            for lane_id, name, case_num, court, judge, status in CASE_LANES:
                fsm = fsm_states.get(lane_id, "—")
                court_short = court[:35] + "…" if len(court) > 35 else court
                lanes_tbl.add_row(lane_id, name, case_num, court_short, judge, status, fsm)

            # --- Deadlines ---
            deadlines = gather_deadlines(conn)
            deadlines_tbl = self.query_one("#deadlines-table", DataTable)
            deadlines_tbl.clear()
            for d in deadlines:
                tag = {
                    "red": "🔴 OVERDUE",
                    "yellow": "🟡 < 7 DAYS",
                    "green": "🟢 OK",
                }.get(d["urgency"], "⚪ ???")
                deadlines_tbl.add_row(
                    tag,
                    d["due_date"][:10],
                    d["title"][:50],
                    d["authority"][:25],
                    d["status"],
                )

            # --- Filing Readiness ---
            filings = gather_filing_readiness(conn)
            filing_tbl = self.query_one("#filing-table", DataTable)
            filing_tbl.clear()
            for f in filings:
                filing_tbl.add_row(
                    f["action"][:45],
                    f["lane"],
                    str(f["score"]),
                    f["gaps"][:35],
                )

            # --- Separation Banner (update in case day rolled over) ---
            self.query_one("#separation-banner", Static).update(
                f"★  {separation_days()} DAYS PARENT-CHILD SEPARATION  ★"
            )

            if conn:
                conn.close()

        def action_refresh_data(self) -> None:
            """Re-query DB for latest stats (bound to 'r')."""
            self._load_data()
            self.notify("Dashboard refreshed", severity="information")

        def action_toggle_dark(self) -> None:
            """Toggle dark/light mode (bound to 'd')."""
            self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if "--text" in sys.argv:
        print_dashboard()
    elif not TEXTUAL_AVAILABLE:
        print("[WARN] textual not installed — falling back to text mode.\n")
        print_dashboard()
    else:
        app = ManbearpigDashboard()
        app.run()


if __name__ == "__main__":
    main()
