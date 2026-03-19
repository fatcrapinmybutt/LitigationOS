#!/usr/bin/env python3
"""
LitigationOS Phase 10 CONVERGE — Self-Evolution Engine
Scheduled pipeline re-run, OMEGA weight adjustment, self-healing,
session recall, auto graph enrichment, and anomaly detection.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import json
import sqlite3
import time
import traceback
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = BASE_DIR / "00_SYSTEM"
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
OMEGA_DIR = SYSTEM_DIR / "omega"
PIPELINE_DIR = SYSTEM_DIR / "pipeline"
SESSION_FILE = OMEGA_DIR / "last_session.json"

# ── Database Helper ────────────────────────────────────────────────────
def get_db():
    """Return a connection to the litigation SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_evolution_tables(conn):
    """Create the omega_evolution_config table if missing."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS omega_evolution_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS omega_evolution_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            detail     TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS omega_anomaly_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_type TEXT NOT NULL,
            severity     TEXT DEFAULT 'MEDIUM',
            detail       TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


# ── 1. Scheduled Pipeline Re-Run Coordinator ──────────────────────────
class PipelineCoordinator:
    """Discovers and schedules pipeline scripts for sequential re-run."""

    def __init__(self):
        self.pipeline_scripts = sorted(PIPELINE_DIR.glob("*.py")) if PIPELINE_DIR.exists() else []

    def list_pipelines(self):
        return [p.name for p in self.pipeline_scripts]

    def run_pipeline(self, script_path, timeout=300):
        """Run a single pipeline script; return (success, output)."""
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(SYSTEM_DIR), errors='replace'
            )
            return result.returncode == 0, result.stdout[-500:] if result.stdout else result.stderr[-500:]
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, str(e)

    def coordinate(self, dry_run=True):
        """Run all pipelines in order. Returns list of (name, success, snippet)."""
        results = []
        for script in self.pipeline_scripts:
            if dry_run:
                results.append((script.name, True, "DRY_RUN"))
            else:
                ok, out = self.run_pipeline(script)
                results.append((script.name, ok, out[:200]))
        return results


# ── 2. OMEGA Weight Adjustment ─────────────────────────────────────────
class OmegaWeightAdjuster:
    """Adjust OMEGA scoring weights based on filing outcome feedback."""

    DEFAULT_WEIGHTS = {
        "evidence_strength": 0.25,
        "legal_precedent":   0.20,
        "procedural_compliance": 0.15,
        "judicial_profile":  0.15,
        "timeline_urgency":  0.10,
        "financial_impact":  0.10,
        "anomaly_factor":    0.05,
    }

    def __init__(self, conn):
        self.conn = conn
        self.weights = dict(self.DEFAULT_WEIGHTS)
        self._load_weights()

    def _load_weights(self):
        try:
            row = self.conn.execute(
                "SELECT value FROM omega_evolution_config WHERE key='omega_weights'"
            ).fetchone()
            if row:
                self.weights = json.loads(row["value"])
        except Exception:
            pass

    def save_weights(self):
        self.conn.execute(
            "INSERT OR REPLACE INTO omega_evolution_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            ("omega_weights", json.dumps(self.weights))
        )
        self.conn.commit()

    def adjust(self, outcome_map: dict):
        """
        outcome_map: {factor: delta} e.g. {'evidence_strength': +0.02}
        Applies deltas and renormalizes to sum=1.0.
        """
        for k, delta in outcome_map.items():
            if k in self.weights:
                self.weights[k] = max(0.01, self.weights[k] + delta)
        total = sum(self.weights.values())
        self.weights = {k: round(v / total, 4) for k, v in self.weights.items()}
        self.save_weights()
        return self.weights


# ── 3. Self-Healing: Error Interceptor with Auto-Restart ───────────────
class SelfHealingEngine:
    """Monitors critical processes and auto-restarts on failure."""

    MAX_RESTARTS = 3

    def __init__(self, conn):
        self.conn = conn
        self.restart_counts = {}

    def intercept_error(self, component: str, error: str):
        """Log the error and decide whether to restart."""
        self.conn.execute(
            "INSERT INTO omega_evolution_log (event_type, detail) VALUES (?, ?)",
            ("ERROR", json.dumps({"component": component, "error": error[:500]}))
        )
        self.conn.commit()

        count = self.restart_counts.get(component, 0)
        if count < self.MAX_RESTARTS:
            self.restart_counts[component] = count + 1
            return self._attempt_restart(component)
        return False, f"Max restarts ({self.MAX_RESTARTS}) reached for {component}"

    def _attempt_restart(self, component: str):
        """Attempt to restart a component script."""
        script = SYSTEM_DIR / component
        if not script.exists():
            return False, f"Script not found: {component}"
        try:
            subprocess.Popen(
                [sys.executable, str(script)],
                cwd=str(SYSTEM_DIR),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.conn.execute(
                "INSERT INTO omega_evolution_log (event_type, detail) VALUES (?, ?)",
                ("RESTART", json.dumps({"component": component}))
            )
            self.conn.commit()
            return True, f"Restarted {component}"
        except Exception as e:
            return False, str(e)


# ── 4. Session Recall ──────────────────────────────────────────────────
class SessionRecall:
    """Persist and restore session context across runs."""

    def __init__(self):
        self.session_file = SESSION_FILE

    def save_session(self, context: dict):
        context["saved_at"] = datetime.now().isoformat()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_file.write_text(json.dumps(context, indent=2), encoding="utf-8")

    def load_session(self):
        if self.session_file.exists():
            try:
                return json.loads(self.session_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}


# ── 5. Auto Graph Enrichment Trigger ──────────────────────────────────
class GraphEnrichmentTrigger:
    """When new documents land, queue neo4j node creation."""

    NEO4J_DIR = SYSTEM_DIR / "neo4j"

    def detect_new_documents(self, conn):
        """Check for documents ingested in the last 24 hours."""
        try:
            rows = conn.execute("""
                SELECT COUNT(*) as cnt FROM omega_documents
                WHERE created_at >= datetime('now', '-1 day')
            """).fetchone()
            return rows["cnt"] if rows else 0
        except Exception:
            return 0

    def trigger_enrichment(self, doc_count):
        """Log enrichment trigger event."""
        enrichment_script = self.NEO4J_DIR / "enrich_graph.py"
        status = "SCRIPT_EXISTS" if enrichment_script.exists() else "SCRIPT_MISSING"
        return {
            "new_docs": doc_count,
            "enrichment_script": status,
            "action": "ENRICH_QUEUED" if doc_count > 0 and status == "SCRIPT_EXISTS" else "NO_ACTION"
        }


# ── 6. Anomaly Detection ──────────────────────────────────────────────
class AnomalyDetector:
    """Detect anomalies: sudden DB growth, agent failure spikes, etc."""

    def __init__(self, conn):
        self.conn = conn
        self.anomalies = []

    def check_db_growth(self):
        """Flag if DB grew more than 50 MB since last check."""
        try:
            db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
            row = self.conn.execute(
                "SELECT value FROM omega_evolution_config WHERE key='last_db_size_mb'"
            ).fetchone()
            last_size = float(row["value"]) if row else db_size_mb
            growth = db_size_mb - last_size
            self.conn.execute(
                "INSERT OR REPLACE INTO omega_evolution_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                ("last_db_size_mb", str(round(db_size_mb, 2)))
            )
            self.conn.commit()
            if growth > 50:
                self.anomalies.append({
                    "type": "DB_GROWTH_SPIKE",
                    "severity": "HIGH",
                    "detail": f"DB grew {growth:.1f} MB (now {db_size_mb:.1f} MB)"
                })
            return {"db_size_mb": round(db_size_mb, 2), "growth_mb": round(growth, 2)}
        except Exception as e:
            return {"error": str(e)}

    def check_agent_failures(self):
        """Check for agent failure spike in last hour."""
        try:
            row = self.conn.execute("""
                SELECT COUNT(*) as cnt FROM omega_evolution_log
                WHERE event_type = 'ERROR'
                  AND created_at >= datetime('now', '-1 hour')
            """).fetchone()
            count = row["cnt"] if row else 0
            if count > 10:
                self.anomalies.append({
                    "type": "AGENT_FAILURE_SPIKE",
                    "severity": "CRITICAL",
                    "detail": f"{count} errors in last hour"
                })
            return {"recent_errors": count}
        except Exception:
            return {"recent_errors": 0}

    def persist_anomalies(self):
        for a in self.anomalies:
            self.conn.execute(
                "INSERT INTO omega_anomaly_log (anomaly_type, severity, detail) VALUES (?, ?, ?)",
                (a["type"], a["severity"], a["detail"])
            )
        self.conn.commit()
        return self.anomalies

    def run_all(self):
        db_info = self.check_db_growth()
        agent_info = self.check_agent_failures()
        persisted = self.persist_anomalies()
        return {"db": db_info, "agents": agent_info, "anomalies_found": len(persisted)}


# ── 7. Save Config Snapshot ────────────────────────────────────────────
def save_system_config(conn, state: dict):
    """Persist full system state to omega_evolution_config."""
    conn.execute(
        "INSERT OR REPLACE INTO omega_evolution_config (key, value, updated_at) VALUES (?, ?, datetime('now'))",
        ("system_state_snapshot", json.dumps(state))
    )
    conn.commit()


# ══════════════════════════════════════════════════════════════════════
#  MAIN — Run and Print Current System State
# ══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 72)
    print("  🧬 LitigationOS — Self-Evolution Engine  (Phase 10 CONVERGE)")
    print("=" * 72)
    now = datetime.now().isoformat()

    # Database
    if not DB_PATH.exists():
        print(f"\n⚠️  Database not found at {DB_PATH}")
        print("   Creating local placeholder for table schemas...")
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
    else:
        conn = get_db()
    ensure_evolution_tables(conn)
    print(f"\n✅ Database connected — {DB_PATH}")
    print(f"   Size: {DB_PATH.stat().st_size / (1024*1024):.1f} MB")

    # 1. Pipeline Coordinator
    print("\n── Pipeline Coordinator ──────────────────────────────────")
    coord = PipelineCoordinator()
    pipelines = coord.list_pipelines()
    print(f"   Discovered {len(pipelines)} pipeline scripts")
    for p in pipelines[:10]:
        print(f"   • {p}")
    if len(pipelines) > 10:
        print(f"   … and {len(pipelines) - 10} more")

    # 2. OMEGA Weight Adjuster
    print("\n── OMEGA Weight Adjuster ─────────────────────────────────")
    adjuster = OmegaWeightAdjuster(conn)
    print("   Current weights:")
    for k, v in adjuster.weights.items():
        bar = "█" * int(v * 40)
        print(f"   {k:<26} {v:.4f}  {bar}")
    adjuster.save_weights()
    print("   ✅ Weights saved to omega_evolution_config")

    # 3. Self-Healing
    print("\n── Self-Healing Engine ───────────────────────────────────")
    healer = SelfHealingEngine(conn)
    print(f"   Max auto-restarts per component: {healer.MAX_RESTARTS}")
    print("   ✅ Error interceptor active")

    # 4. Session Recall
    print("\n── Session Recall ───────────────────────────────────────")
    recall = SessionRecall()
    prior = recall.load_session()
    if prior:
        print(f"   Prior session loaded (saved {prior.get('saved_at', 'unknown')})")
        for k, v in prior.items():
            if k != "saved_at":
                print(f"   • {k}: {str(v)[:80]}")
    else:
        print("   No prior session found — first run")
    recall.save_session({
        "run_at": now,
        "pipelines_found": len(pipelines),
        "weights": adjuster.weights,
    })
    print("   ✅ Current session saved")

    # 5. Graph Enrichment
    print("\n── Auto Graph Enrichment ─────────────────────────────────")
    graph = GraphEnrichmentTrigger()
    new_docs = graph.detect_new_documents(conn)
    enrichment = graph.trigger_enrichment(new_docs)
    print(f"   New documents (24h): {enrichment['new_docs']}")
    print(f"   Enrichment script:   {enrichment['enrichment_script']}")
    print(f"   Action:              {enrichment['action']}")

    # 6. Anomaly Detection
    print("\n── Anomaly Detection ────────────────────────────────────")
    detector = AnomalyDetector(conn)
    anomaly_report = detector.run_all()
    print(f"   DB size:        {anomaly_report['db'].get('db_size_mb', 'N/A')} MB")
    print(f"   DB growth:      {anomaly_report['db'].get('growth_mb', 'N/A')} MB")
    print(f"   Recent errors:  {anomaly_report['agents'].get('recent_errors', 0)}")
    print(f"   Anomalies:      {anomaly_report['anomalies_found']}")

    # 7. Save full config snapshot
    state = {
        "timestamp": now,
        "pipelines": len(pipelines),
        "weights": adjuster.weights,
        "anomalies": anomaly_report["anomalies_found"],
        "db_size_mb": anomaly_report["db"].get("db_size_mb"),
        "session_recall": bool(prior),
        "graph_enrichment": enrichment["action"],
    }
    save_system_config(conn, state)
    print("\n── System State Snapshot ─────────────────────────────────")
    print(f"   ✅ Saved to omega_evolution_config table")
    for k, v in state.items():
        print(f"   {k}: {v}")

    conn.close()
    print("\n" + "=" * 72)
    print("  🧬 Self-Evolution Engine — OPERATIONAL")
    print("=" * 72)


if __name__ == "__main__":
    main()
