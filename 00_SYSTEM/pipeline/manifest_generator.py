import sys; sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
"""
manifest_generator.py — Run manifest generator for the drive ingestion pipeline.

Generates detailed JSON manifests recording all inputs, outputs, errors, gaps,
and metrics after each pipeline run. Manifests are stored in:
    00_SYSTEM/pipeline/manifests/RUN_YYYYMMDD_HHMMSS.json

Also produces a human-readable .md summary alongside each JSON manifest.

Usage:
    python manifest_generator.py --run-id RUN_20260305_183200
    python manifest_generator.py --list
    python manifest_generator.py --compare RUN_A RUN_B
    python manifest_generator.py --help
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Failsafe import — graceful degradation if failsafe.py is unavailable
# ---------------------------------------------------------------------------
try:
    from failsafe import never_crash, safe_call, _log_incident
    # NOTE: We do NOT import get_robust_connection from failsafe because it
    # runs PRAGMA integrity_check which is prohibitively slow on the 10GB DB.
except ImportError:
    # Minimal stubs so the module works standalone
    def never_crash(fallback=None):
        def decorator(fn):
            def wrapper(*a, **kw):
                try:
                    return fn(*a, **kw)
                except Exception:
                    traceback.print_exc()
                    return fallback
            wrapper.__name__ = fn.__name__
            return wrapper
        return decorator

    def safe_call(fn, timeout_s=30, fallback=None):  # noqa: ARG001
        try:
            return fn()
        except Exception:
            traceback.print_exc()
            return fallback

    def _log_incident(component, incident, severity="ERROR", detail="", fallback=""):  # noqa: ARG001
        logging.error("[%s] %s — %s  (fallback=%s)", severity, component, incident, fallback)


def _fast_connect(db_path, timeout=120):
    """WAL connection WITHOUT integrity_check (safe for the 10GB DB)."""
    conn = sqlite3.connect(str(db_path), timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=120000")
    return conn


logger = logging.getLogger("manifest_generator")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")


class ManifestGenerator:
    """Generate run manifests for audit, reproducibility, and convergence tracking."""

    MANIFEST_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\manifests")

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = _fast_connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @never_crash(fallback=None)
    def generate(self, run_id: str) -> dict:
        """Generate a complete manifest for the given run_id.

        Queries ingest_logs, drive_files, file_atoms, provenance_refs, gap_tickets.
        Returns manifest dict and writes JSON + .md files.
        """
        logger.info("Generating manifest for %s …", run_id)

        manifest = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "system": "LitigationOS Drive Ingestion Pipeline v1.0",
            "inputs": self._collect_inputs(run_id),
            "outputs": self._collect_outputs(run_id),
            "metrics": self._collect_metrics(run_id),
            "phases": self._collect_phases(run_id),
            "errors": self._collect_errors(run_id),
            "gaps_opened": self._collect_gaps(run_id),
            "convergence": self._collect_convergence(run_id),
        }
        # Hash is computed over the rest of the manifest
        manifest["sha256_manifest"] = self._compute_manifest_hash(manifest)

        # Persist
        self._write_json(run_id, manifest)
        self._write_summary_md(run_id, manifest)

        logger.info("Manifest written for %s", run_id)
        return manifest

    @never_crash(fallback="")
    def generate_rebuild_script(self, run_id: str) -> str:
        """Generate a PowerShell script that can reproduce this run."""
        inputs = self._collect_inputs(run_id)
        paths = [i["path"] for i in inputs if i.get("path")]
        lines = [
            "# Auto-generated rebuild script for " + run_id,
            f"# Generated: {datetime.now().isoformat()}",
            "# LitigationOS Drive Ingestion Pipeline — Rebuild",
            "",
            "Set-StrictMode -Version Latest",
            "$ErrorActionPreference = 'Stop'",
            "",
            "# Verify source files exist",
        ]
        for p in paths:
            lines.append(f'if (-not (Test-Path "{p}")) {{ Write-Error "Missing: {p}"; exit 1 }}')
        lines += [
            "",
            "# Run pipeline with the same files",
            "cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\pipeline",
            f'python run_omega_pipeline.py --start-phase 0.5 --end-phase 9 # rebuild {run_id}',
            "",
            f'Write-Host "Rebuild for {run_id} complete."',
        ]
        script = "\n".join(lines)

        out_path = self.MANIFEST_DIR / f"{run_id}_rebuild.ps1"
        out_path.write_text(script, encoding="utf-8")
        logger.info("Rebuild script: %s", out_path)
        return script

    @never_crash(fallback=[])
    def list_manifests(self) -> list[dict]:
        """List all existing manifests with summary info."""
        results = []
        for fp in sorted(self.MANIFEST_DIR.glob("RUN_*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                results.append({
                    "file": fp.name,
                    "run_id": data.get("run_id", ""),
                    "timestamp": data.get("timestamp", ""),
                    "files_processed": (data.get("metrics") or {}).get("files_processed", 0),
                    "atoms_created": (data.get("metrics") or {}).get("atoms_created", 0),
                    "errors": (data.get("metrics") or {}).get("errors", 0),
                    "sha256": data.get("sha256_manifest", ""),
                })
            except Exception as exc:
                results.append({"file": fp.name, "error": str(exc)})
        return results

    @never_crash(fallback=None)
    def compare_runs(self, run_id_a: str, run_id_b: str) -> dict:
        """Compare two run manifests for convergence analysis."""
        ma = self._load_manifest(run_id_a)
        mb = self._load_manifest(run_id_b)
        if not ma or not mb:
            return {"error": "One or both manifests not found"}

        met_a = ma.get("metrics") or {}
        met_b = mb.get("metrics") or {}

        def _delta(key):
            return (met_b.get(key) or 0) - (met_a.get(key) or 0)

        return {
            "run_a": run_id_a,
            "run_b": run_id_b,
            "delta_files_processed": _delta("files_processed"),
            "delta_atoms_created": _delta("atoms_created"),
            "delta_quotes_added": _delta("quotes_added"),
            "delta_gaps_opened": _delta("gaps_opened"),
            "delta_errors": _delta("errors"),
            "converged": _delta("atoms_created") == 0 and _delta("quotes_added") == 0,
            "inputs_a_count": len(ma.get("inputs") or []),
            "inputs_b_count": len(mb.get("inputs") or []),
        }

    # ------------------------------------------------------------------
    # Internal collectors
    # ------------------------------------------------------------------
    @never_crash(fallback=[])
    def _collect_inputs(self, run_id: str) -> list[dict]:
        """List all files ingested in this run from drive_files."""
        if not self._table_exists("drive_files"):
            return []
        rows = self.conn.execute(
            """SELECT file_path, sha256, lane, drive_letter, size_bytes
               FROM drive_files WHERE run_id = ? ORDER BY file_path""",
            (run_id,),
        ).fetchall()
        return [
            {
                "path": r["file_path"],
                "sha256": r["sha256"] or "",
                "lane": r["lane"] or "",
                "source": r["drive_letter"] or "local",
                "file_size": r["size_bytes"] or 0,
            }
            for r in rows
        ]

    @never_crash(fallback={})
    def _collect_outputs(self, run_id: str) -> dict:
        """Summarize outputs: atoms created, quotes linked, etc."""
        result = {
            "files_ingested": 0,
            "atoms_created": 0,
            "quotes_linked": 0,
            "citations_found": 0,
        }

        if self._table_exists("drive_files"):
            row = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM drive_files WHERE run_id = ?", (run_id,)
            ).fetchone()
            result["files_ingested"] = row["cnt"] if row else 0

        if self._table_exists("file_atoms"):
            row = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM file_atoms WHERE run_id = ?", (run_id,)
            ).fetchone()
            result["atoms_created"] = row["cnt"] if row else 0

        if self._table_exists("provenance_refs"):
            row = self.conn.execute(
                "SELECT COUNT(*) AS cnt FROM provenance_refs WHERE run_id = ?", (run_id,)
            ).fetchone()
            result["quotes_linked"] = row["cnt"] if row else 0

        # Supplement from ingest_logs metrics_json
        if self._table_exists("ingest_logs"):
            rows = self.conn.execute(
                "SELECT metrics_json FROM ingest_logs WHERE run_id = ?", (run_id,),
            ).fetchall()
            for r in rows:
                m = self._parse_json_field(r["metrics_json"])
                result["atoms_created"] = max(result["atoms_created"], m.get("atoms_created", 0))
                result["quotes_linked"] = max(result["quotes_linked"], m.get("atoms_linked", 0))

        return result

    @never_crash(fallback={})
    def _collect_metrics(self, run_id: str) -> dict:
        """Aggregate metrics from ingest_logs for this run.

        ingest_logs stores per-phase metrics as JSON blobs in ``metrics_json``
        and timing/deltas in ``delta_json``.  We parse and aggregate them.
        """
        defaults = {
            "files_processed": 0,
            "atoms_created": 0,
            "quotes_added": 0,
            "gaps_opened": 0,
            "duration_seconds": 0.0,
            "errors": 0,
        }
        if not self._table_exists("ingest_logs"):
            return defaults

        rows = self.conn.execute(
            """SELECT phase, status, started_at, ended_at, metrics_json, delta_json
               FROM ingest_logs WHERE run_id = ? ORDER BY id""",
            (run_id,),
        ).fetchall()
        if not rows:
            return defaults

        totals = dict(defaults)
        for r in rows:
            m = self._parse_json_field(r["metrics_json"])
            d = self._parse_json_field(r["delta_json"])
            totals["files_processed"] += m.get("files_scanned", m.get("files_processed", 0))
            totals["atoms_created"] += m.get("atoms_created", 0)
            totals["quotes_added"] += m.get("atoms_linked", m.get("quotes_added", 0))
            totals["gaps_opened"] += m.get("gaps_created", m.get("gaps_opened", 0))
            totals["errors"] += m.get("errors", 0)
            # Duration from started_at / ended_at
            elapsed = self._elapsed(r["started_at"], r["ended_at"])
            if elapsed is not None:
                totals["duration_seconds"] += elapsed
            else:
                totals["duration_seconds"] += m.get("elapsed_seconds", d.get("elapsed_seconds", 0))
            if r["status"] and "error" in r["status"].lower():
                totals["errors"] += 1

        totals["duration_seconds"] = round(totals["duration_seconds"], 2)
        return totals

    @never_crash(fallback=[])
    def _collect_phases(self, run_id: str) -> list[dict]:
        """List each phase step and its status/timing."""
        if not self._table_exists("ingest_logs"):
            return []
        rows = self.conn.execute(
            """SELECT phase, status, started_at, ended_at, metrics_json, delta_json
               FROM ingest_logs WHERE run_id = ? ORDER BY id""",
            (run_id,),
        ).fetchall()
        results = []
        for r in rows:
            m = self._parse_json_field(r["metrics_json"])
            elapsed = self._elapsed(r["started_at"], r["ended_at"])
            results.append({
                "phase": r["phase"] or "",
                "step": "",
                "status": r["status"] or "unknown",
                "files": m.get("files_scanned", m.get("files_processed", 0)),
                "atoms": m.get("atoms_created", 0),
                "duration": round(elapsed, 2) if elapsed is not None else 0,
                "detail": m.get("detail", ""),
            })
        return results

    @never_crash(fallback=[])
    def _collect_errors(self, run_id: str) -> list[dict]:
        """Collect all errors from this run."""
        errors = []
        if self._table_exists("ingest_logs"):
            rows = self.conn.execute(
                """SELECT phase, status, metrics_json
                   FROM ingest_logs
                   WHERE run_id = ? AND status LIKE '%error%'
                   ORDER BY id""",
                (run_id,),
            ).fetchall()
            for r in rows:
                m = self._parse_json_field(r["metrics_json"])
                errors.append({
                    "file": "",
                    "phase": r["phase"] or "",
                    "message": m.get("detail", m.get("error", f"Error in {r['phase']}")),
                })

        if self._table_exists("drive_files"):
            rows = self.conn.execute(
                """SELECT file_path, status, '' as error_message
                   FROM drive_files
                   WHERE run_id = ? AND status LIKE '%error%'
                   ORDER BY file_path""",
                (run_id,),
            ).fetchall()
            for r in rows:
                errors.append({
                    "file": r["file_path"] or "",
                    "phase": "extract",
                    "message": r["error_message"] or r["status"] or "processing error",
                })
        return errors

    @never_crash(fallback=[])
    def _collect_gaps(self, run_id: str) -> list[str]:
        """List gap_tickets opened during this run.

        gap_tickets has no run_id column; correlate via the run's time window
        obtained from ingest_logs.
        """
        if not self._table_exists("gap_tickets"):
            return []
        start, end = self._run_time_window(run_id)
        if not start:
            return []
        rows = self.conn.execute(
            """SELECT ticket_id FROM gap_tickets
               WHERE created_at >= ? AND created_at <= ?
               ORDER BY ticket_id""",
            (start, end),
        ).fetchall()
        return [r["ticket_id"] for r in rows]

    @never_crash(fallback={})
    def _collect_convergence(self, run_id: str) -> dict:
        """Convergence metrics: delta from previous run."""
        previous = self._find_previous_run(run_id)
        if not previous:
            return {
                "previous_run": None,
                "delta_quotes": 0,
                "delta_atoms": 0,
                "instruction_changed": False,
                "converged": False,
            }
        cur = self._collect_metrics(run_id)
        prev = self._collect_metrics(previous)
        delta_atoms = (cur.get("atoms_created") or 0) - (prev.get("atoms_created") or 0)
        delta_quotes = (cur.get("quotes_added") or 0) - (prev.get("quotes_added") or 0)
        return {
            "previous_run": previous,
            "delta_quotes": delta_quotes,
            "delta_atoms": delta_atoms,
            "instruction_changed": False,
            "converged": delta_atoms == 0 and delta_quotes == 0,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    @staticmethod
    def _parse_json_field(raw) -> dict:
        """Safely parse a JSON text field; return {} on failure."""
        if not raw:
            return {}
        try:
            return json.loads(raw) if isinstance(raw, str) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @staticmethod
    def _elapsed(started: str | None, ended: str | None) -> float | None:
        """Compute seconds between two ISO timestamps; None if unparseable."""
        if not started or not ended:
            return None
        try:
            fmt_candidates = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
            s = e = None
            for fmt in fmt_candidates:
                try:
                    s = datetime.strptime(started, fmt)
                    break
                except ValueError:
                    continue
            for fmt in fmt_candidates:
                try:
                    e = datetime.strptime(ended, fmt)
                    break
                except ValueError:
                    continue
            if s and e:
                return max((e - s).total_seconds(), 0.0)
        except Exception:
            pass
        return None

    def _run_time_window(self, run_id: str) -> tuple[str | None, str | None]:
        """Return (min started_at, max ended_at) for a run from ingest_logs."""
        if not self._table_exists("ingest_logs"):
            return None, None
        row = self.conn.execute(
            """SELECT MIN(started_at) AS t0, MAX(COALESCE(ended_at, started_at)) AS t1
               FROM ingest_logs WHERE run_id = ?""",
            (run_id,),
        ).fetchone()
        if row and row["t0"]:
            return row["t0"], row["t1"]
        return None, None

    def _find_previous_run(self, run_id: str) -> str | None:
        """Find the run_id immediately before the given one."""
        if not self._table_exists("ingest_logs"):
            return None
        row = self.conn.execute(
            """SELECT DISTINCT run_id FROM ingest_logs
               WHERE run_id < ? ORDER BY run_id DESC LIMIT 1""",
            (run_id,),
        ).fetchone()
        return row["run_id"] if row else None

    def _load_manifest(self, run_id: str) -> dict | None:
        """Load a manifest JSON from disk by run_id."""
        for fp in self.MANIFEST_DIR.glob(f"{run_id}*.json"):
            try:
                return json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
        # Fallback: scan all manifests
        for fp in self.MANIFEST_DIR.glob("RUN_*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                if data.get("run_id") == run_id:
                    return data
            except Exception:
                continue
        return None

    @staticmethod
    def _compute_manifest_hash(manifest: dict) -> str:
        """SHA-256 of the manifest content (excluding the hash field itself) for integrity."""
        clone = {k: v for k, v in manifest.items() if k != "sha256_manifest"}
        raw = json.dumps(clone, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _write_json(self, run_id: str, manifest: dict) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{run_id}.json" if run_id.startswith("RUN_") else f"RUN_{ts}.json"
        out_path = self.MANIFEST_DIR / filename
        out_path.write_text(
            json.dumps(manifest, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("JSON manifest: %s", out_path)
        return out_path

    def _write_summary_md(self, run_id: str, manifest: dict) -> Path:
        """Write a human-readable Markdown summary alongside the JSON."""
        metrics = manifest.get("metrics") or {}
        outputs = manifest.get("outputs") or {}
        phases = manifest.get("phases") or []
        errors = manifest.get("errors") or []
        gaps = manifest.get("gaps_opened") or []
        conv = manifest.get("convergence") or {}

        lines = [
            f"# Run Manifest: {run_id}",
            "",
            f"**Generated:** {manifest.get('timestamp', '')}  ",
            f"**System:** {manifest.get('system', '')}",
            "",
            "## Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Files processed | {metrics.get('files_processed', 0)} |",
            f"| Atoms created | {metrics.get('atoms_created', 0)} |",
            f"| Quotes added | {metrics.get('quotes_added', 0)} |",
            f"| Gaps opened | {metrics.get('gaps_opened', 0)} |",
            f"| Duration (s) | {metrics.get('duration_seconds', 0)} |",
            f"| Errors | {metrics.get('errors', 0)} |",
            "",
            "## Outputs",
            "",
            f"- Files ingested: {outputs.get('files_ingested', 0)}",
            f"- Atoms created: {outputs.get('atoms_created', 0)}",
            f"- Quotes linked: {outputs.get('quotes_linked', 0)}",
            f"- Citations found: {outputs.get('citations_found', 0)}",
            "",
        ]

        if phases:
            lines += ["## Phases", "", "| Phase | Step | Status | Files | Duration |", "|-------|------|--------|-------|----------|"]
            for p in phases:
                lines.append(f"| {p.get('phase','')} | {p.get('step','')} | {p.get('status','')} | {p.get('files',0)} | {p.get('duration',0)}s |")
            lines.append("")

        if errors:
            lines += ["## Errors", ""]
            for e in errors:
                lines.append(f"- **{e.get('phase','')}**: {e.get('file','')} — {e.get('message','')}")
            lines.append("")

        if gaps:
            lines += ["## Gap Tickets Opened", ""]
            for g in gaps:
                lines.append(f"- `{g}`")
            lines.append("")

        lines += [
            "## Convergence",
            "",
            f"- Previous run: `{conv.get('previous_run', 'N/A')}`",
            f"- Delta atoms: {conv.get('delta_atoms', 0)}",
            f"- Delta quotes: {conv.get('delta_quotes', 0)}",
            f"- Converged: {'✅ Yes' if conv.get('converged') else '❌ No'}",
            "",
            "---",
            f"**SHA-256:** `{manifest.get('sha256_manifest', '')}`",
        ]

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{run_id}.md" if run_id.startswith("RUN_") else f"RUN_{ts}.md"
        out_path = self.MANIFEST_DIR / filename
        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Summary: %s", out_path)
        return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manifest_generator",
        description="Generate and manage run manifests for the LitigationOS drive ingestion pipeline.",
    )
    parser.add_argument("--run-id", type=str, help="Generate manifest for this run ID")
    parser.add_argument("--list", action="store_true", help="List all existing manifests")
    parser.add_argument(
        "--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
        help="Compare two run manifests for convergence analysis",
    )
    parser.add_argument("--rebuild-script", type=str, metavar="RUN_ID",
                        help="Generate a rebuild PowerShell script for a run")
    parser.add_argument("--db", type=str, default=None,
                        help=f"Path to litigation_context.db (default: {_DEFAULT_DB})")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    # If no action specified, show help
    if not args.run_id and not args.list and not args.compare and not args.rebuild_script:
        parser.print_help()
        return 0

    try:
        gen = ManifestGenerator(db_path=args.db)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.list:
        manifests = gen.list_manifests()
        if not manifests:
            print("No manifests found.")
            return 0
        print(json.dumps(manifests, indent=2, default=str))
        return 0

    if args.compare:
        result = gen.compare_runs(args.compare[0], args.compare[1])
        print(json.dumps(result, indent=2, default=str))
        return 0

    if args.rebuild_script:
        script = gen.generate_rebuild_script(args.rebuild_script)
        if script:
            print(script)
        else:
            print("ERROR: Could not generate rebuild script.", file=sys.stderr)
            return 1
        return 0

    if args.run_id:
        manifest = gen.generate(args.run_id)
        if manifest:
            print(json.dumps(manifest, indent=2, default=str))
            return 0
        else:
            print(f"ERROR: Failed to generate manifest for {args.run_id}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
