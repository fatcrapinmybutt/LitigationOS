"""
OMEGA Phase 16: Desktop Offload
Generate UI-formatted JSON packages for LitigationOS-Desktop (Electron app).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    MASTER_ROOT, get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

DESKTOP_APP_DIR = MASTER_ROOT / "LitigationOS-Desktop"


def _safe_load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def _safe_load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return items


def _transform_action_matrix(src: dict | list | None) -> dict:
    """Transform legal_action_matrix.json → actions_dashboard.json."""
    if not src:
        return {"actions": [], "generated_at": datetime.now().isoformat(), "count": 0}

    actions: list[dict] = []
    if isinstance(src, list):
        for item in src:
            actions.append({
                "id": item.get("id", item.get("action_id", "")),
                "title": item.get("title", item.get("action", "")),
                "status": item.get("status", "pending"),
                "priority": item.get("priority", "medium"),
                "lane": item.get("meek_lane", item.get("lane", "")),
                "description": item.get("description", item.get("details", ""))[:300],
            })
    elif isinstance(src, dict):
        for key, val in src.items():
            if isinstance(val, list):
                for item in val:
                    actions.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", key),
                        "status": item.get("status", "pending"),
                        "priority": item.get("priority", "medium"),
                        "lane": item.get("lane", ""),
                        "description": str(item.get("description", ""))[:300],
                    })

    return {
        "actions": actions,
        "count": len(actions),
        "generated_at": datetime.now().isoformat(),
    }


def _transform_judicial_analysis(src: dict | list | None) -> dict:
    """Transform judicial_analysis_report.json → judicial_dashboard.json."""
    if not src:
        return {"judges": [], "generated_at": datetime.now().isoformat()}

    if isinstance(src, dict):
        return {
            "summary": src.get("summary", ""),
            "judges": src.get("judges", src.get("analysis", [])),
            "total_findings": src.get("total_findings", 0),
            "risk_level": src.get("risk_level", "unknown"),
            "generated_at": datetime.now().isoformat(),
        }
    return {"judges": src if isinstance(src, list) else [], "generated_at": datetime.now().isoformat()}


def _transform_gap_report(cycle_dir: Path) -> dict:
    """Transform gap_report → gaps_dashboard.json."""
    tickets = _safe_load_jsonl(cycle_dir / "gap_tickets.jsonl")
    stats = _safe_load_json(cycle_dir / "gap_analysis_stats.json")

    by_type: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    for t in tickets:
        gt = t.get("gap_type", "unknown")
        by_type[gt] = by_type.get(gt, 0) + 1
        risk = t.get("deadline_risk", "unknown")
        by_risk[risk] = by_risk.get(risk, 0) + 1

    return {
        "total_gaps": len(tickets),
        "by_type": by_type,
        "by_risk": by_risk,
        "high_priority": [t for t in tickets if t.get("deadline_risk") == "high"][:20],
        "stats": stats or {},
        "generated_at": datetime.now().isoformat(),
    }


def _transform_pipeline_stats(cycle_dir: Path) -> dict:
    """Aggregate pipeline stats into pipeline_dashboard.json."""
    dashboard: dict = {
        "phases_completed": [],
        "total_elapsed_seconds": 0,
        "generated_at": datetime.now().isoformat(),
    }

    cp_dir = cycle_dir / "checkpoints"
    if cp_dir.exists():
        for cp_file in sorted(cp_dir.glob("*_complete.json")):
            try:
                data = json.loads(cp_file.read_text(encoding="utf-8"))
                phase_name = cp_file.stem.replace("_complete", "")
                dashboard["phases_completed"].append({
                    "phase": phase_name,
                    "completed_at": data.get("completed_at", ""),
                    "status": data.get("status", ""),
                })
            except (json.JSONDecodeError, OSError):
                pass

    # Collect individual stats files
    for stats_file in cycle_dir.glob("*_stats.json"):
        try:
            data = json.loads(stats_file.read_text(encoding="utf-8"))
            elapsed = data.get("elapsed_seconds", data.get("elapsed", 0))
            if isinstance(elapsed, str):
                elapsed = float(elapsed.rstrip("s")) if elapsed else 0
            dashboard["total_elapsed_seconds"] += elapsed
            dashboard[stats_file.stem] = data
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    dashboard["phase_count"] = len(dashboard["phases_completed"])
    return dashboard


def run_desktop_offload(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase16"):
        print("[PHASE16] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE16] Generating desktop offload package...", file=sys.stderr)
    start = time.time()

    out_dir = cycle_dir / "desktop_offload"
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, dict] = {}

    # a) legal_action_matrix → actions_dashboard
    lam = _safe_load_json(cycle_dir / "legal_action_matrix.json")
    if not lam:
        lam = _safe_load_json(MASTER_ROOT / "legal_action_matrix.json")
    outputs["actions_dashboard.json"] = _transform_action_matrix(lam)

    # b) judicial_analysis_report → judicial_dashboard
    jar = _safe_load_json(cycle_dir / "judicial_analysis_report.json")
    if not jar:
        jar = _safe_load_json(MASTER_ROOT / "judicial_analysis_report.json")
    outputs["judicial_dashboard.json"] = _transform_judicial_analysis(jar)

    # c) gap_report → gaps_dashboard
    outputs["gaps_dashboard.json"] = _transform_gap_report(cycle_dir)

    # d) Pipeline stats → pipeline_dashboard
    outputs["pipeline_dashboard.json"] = _transform_pipeline_stats(cycle_dir)

    elapsed = time.time() - start

    if not dry_run:
        for fname, data in outputs.items():
            (out_dir / fname).write_text(
                json.dumps(data, indent=2), encoding="utf-8",
            )

        # Write manifest
        manifest = {
            "cycle_dir": str(cycle_dir),
            "desktop_app_dir": str(DESKTOP_APP_DIR),
            "files": list(outputs.keys()),
            "generated_at": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 1),
        }
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8",
        )

        write_phase_checkpoint(cycle_dir, "phase16", {
            "status": "done", "files": len(outputs),
            "output_dir": str(out_dir), "elapsed": f"{elapsed:.0f}s",
        })

    print(f"[PHASE16] Exported {len(outputs)} dashboard files to {out_dir} in {elapsed:.0f}s",
          file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 16: Desktop Offload")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_desktop_offload(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
