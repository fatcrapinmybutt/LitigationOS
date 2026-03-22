#!/usr/bin/env python3
"""OMEGA-INFINITY Autonomous Agent Activator.

Takes gap detection results and generates an activation plan that maps
each gap to the best agent, creates ready-to-use prompts, and batches
into waves of max N agents.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
DEFAULT_DB = REPO_ROOT / "litigation_context.db"
DEFAULT_MAX_AGENTS = 3

LANE_LABELS: dict[str, str] = {
    "A": "Custody (2024-001507-DC)",
    "B": "Housing (2025-002760-CZ)",
    "C": "Convergence",
    "D": "PPO (2023-5907-PP)",
    "E": "Misconduct (JTC)",
    "F": "Appellate (COA 366810)",
}

# Gap type → best agent mapping
GAP_TO_AGENT: dict[str, dict[str, str]] = {
    "evidence": {
        "agent": "evidence-warfare-commander",
        "description": "Evidence triage, gap analysis, impeachment prep",
        "prompt_template": (
            "Investigate evidence gaps in LitigationOS. "
            "The following gap was detected: {description}. "
            "Search litigation_context.db and all 6 drives for relevant evidence. "
            "Catalog findings into evidence_quotes and evidence_consolidated tables. "
            "{lane_context}"
        ),
    },
    "form": {
        "agent": "court-form-finder",
        "description": "Find correct Michigan SCAO court forms",
        "prompt_template": (
            "Find the correct Michigan SCAO court form for the following need: {description}. "
            "Check court_forms.db and the SCAO website catalog. "
            "Ensure the form number, title, and instructions are captured in court_forms_complete."
        ),
    },
    "authority": {
        "agent": "legal-research-deep",
        "description": "Deep legal research with multi-source authority search",
        "prompt_template": (
            "Research the following missing legal authority: {description}. "
            "Find the full citation text, relevant MCR/MCL sections, and case law. "
            "Add results to authority_master_index in litigation_context.db. "
            "Verify citations are accurate — never fabricate case names or rule numbers."
        ),
    },
    "filing": {
        "agent": "filing-forge-master",
        "description": "Filing assembly, validation, service proof",
        "prompt_template": (
            "Complete the filing package: {description}. "
            "Check filing_readiness for current status. "
            "Identify missing components (affidavit, exhibits, proposed order, proof of service). "
            "Update filing_readiness with new score after improvements. "
            "{lane_context}"
        ),
    },
    "timeline": {
        "agent": "timeline-forensics",
        "description": "Build timelines from transcripts and records",
        "prompt_template": (
            "Fill the following timeline gap: {description}. "
            "Search court records, emails, and documents on all drives for events in this date range. "
            "Add findings to timeline_events and docket_events tables. "
            "Ensure each event has: date, actor, action, source_path, and case_lane."
        ),
    },
    "witness": {
        "agent": "subpoena-engine",
        "description": "Draft and track subpoenas for witnesses/documents",
        "prompt_template": (
            "Address the following witness gap: {description}. "
            "Search existing evidence for witness references (names, roles, testimony mentions). "
            "Catalog identified witnesses in witness_list with: name, role, relevance, lane, contact info. "
            "For key witnesses, draft subpoena language."
        ),
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------
def load_gaps(gap_source: str | None, conn: sqlite3.Connection | None = None) -> list[dict]:
    """Load gap detection results from JSON file or run inline detection."""
    if gap_source and Path(gap_source).is_file():
        with open(gap_source, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("gaps", data.get("acquisition_tasks", []))

    # If no file provided but we have a DB, run inline gap detection
    if conn is not None:
        # Import the gap detector functions inline
        script_dir = Path(__file__).parent
        gap_detector = script_dir / "omega_gap_detector.py"

        if gap_detector.is_file():
            import importlib.util

            spec = importlib.util.spec_from_file_location("omega_gap_detector", str(gap_detector))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]

                all_gaps: list[dict] = []
                all_gaps.extend(mod.detect_evidence_gaps(conn))
                all_gaps.extend(mod.detect_form_gaps(conn))
                all_gaps.extend(mod.detect_authority_gaps(conn))
                all_gaps.extend(mod.detect_filing_gaps(conn))
                all_gaps.extend(mod.detect_timeline_gaps(conn))
                all_gaps.extend(mod.detect_witness_gaps(conn))
                return all_gaps

    return []


def map_gap_to_agent(gap: dict) -> dict[str, str]:
    """Route each gap to the best agent."""
    gap_type = gap.get("type", "unknown")
    mapping = GAP_TO_AGENT.get(gap_type)

    if not mapping:
        return {
            "agent": "evidence-warfare-commander",
            "description": "General investigation",
            "prompt_template": "Investigate: {description}",
        }
    return mapping


def generate_agent_prompts(gaps: list[dict]) -> list[dict]:
    """Create ready-to-use prompts for each agent activation."""
    activations: list[dict] = []

    for gap in gaps:
        mapping = map_gap_to_agent(gap)

        lane = gap.get("lane", "")
        lane_context = ""
        if lane:
            lane_context = f"Focus on Lane {lane} ({LANE_LABELS.get(lane, '')})."

        prompt = mapping["prompt_template"].format(
            description=gap.get("description", "Unknown gap"),
            lane_context=lane_context,
        )

        activation: dict[str, Any] = {
            "agent": mapping["agent"],
            "agent_description": mapping["description"],
            "gap_type": gap.get("type", "unknown"),
            "severity": gap.get("severity", "MEDIUM"),
            "priority": gap.get("priority", 50) if "priority" in gap else _calc_priority(gap),
            "prompt": prompt,
        }

        if lane:
            activation["lane"] = lane
        if "vehicle" in gap:
            activation["vehicle"] = gap["vehicle"]

        activations.append(activation)

    # Sort by priority descending
    activations.sort(key=lambda a: a["priority"], reverse=True)
    return activations


def _calc_priority(gap: dict) -> int:
    base = {"evidence": 90, "filing": 95, "authority": 80, "witness": 75, "form": 70, "timeline": 60}.get(
        gap.get("type", ""), 50
    )
    bonus = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 0, "LOW": -10}.get(gap.get("severity", "MEDIUM"), 0)
    return min(base + bonus, 100)


def activation_plan(activations: list[dict], max_agents: int = DEFAULT_MAX_AGENTS) -> dict:
    """Prioritize and batch into waves of max N agents."""
    waves: list[list[dict]] = []

    for i in range(0, len(activations), max_agents):
        wave_items = activations[i : i + max_agents]
        waves.append(wave_items)

    plan: dict[str, Any] = {
        "total_activations": len(activations),
        "total_waves": len(waves),
        "max_agents_per_wave": max_agents,
        "waves": [],
    }

    for wave_idx, wave_items in enumerate(waves, 1):
        wave_summary: dict[str, Any] = {
            "wave": wave_idx,
            "agent_count": len(wave_items),
            "agents": [],
        }
        for item in wave_items:
            wave_summary["agents"].append({
                "agent": item["agent"],
                "gap_type": item["gap_type"],
                "severity": item["severity"],
                "priority": item["priority"],
                "prompt": item["prompt"],
                "lane": item.get("lane"),
                "vehicle": item.get("vehicle"),
            })
        plan["waves"].append(wave_summary)

    return plan


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def print_activation_plan(plan: dict, dry_run: bool = True, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(plan, indent=2, default=str))
        return

    mode = "DRY RUN" if dry_run else "ACTIVATION"
    print("=" * 70)
    print(f"  OMEGA-INFINITY AGENT ACTIVATOR — {mode}")
    print("=" * 70)

    print(f"\n  Total activations: {plan['total_activations']}")
    print(f"  Total waves:       {plan['total_waves']}")
    print(f"  Max per wave:      {plan['max_agents_per_wave']}")

    for wave in plan["waves"]:
        print(f"\n  {'─' * 60}")
        print(f"  WAVE {wave['wave']} ({wave['agent_count']} agents)")
        print(f"  {'─' * 60}")
        for agent_info in wave["agents"]:
            sev = agent_info["severity"]
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
            print(f"\n  {icon} Agent: {agent_info['agent']}")
            print(f"     Type:     {agent_info['gap_type']}")
            print(f"     Priority: {agent_info['priority']}")
            if agent_info.get("lane"):
                print(f"     Lane:     {agent_info['lane']}")
            # Truncate prompt for display
            prompt_preview = agent_info["prompt"][:200]
            print(f"     Prompt:   {prompt_preview}...")

    if dry_run:
        print(f"\n  ⚠️  DRY RUN — No agents were actually dispatched.")
        print(f"     Use without --dry-run to generate activation commands.")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="OMEGA-INFINITY Autonomous Agent Activator")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to primary DB")
    parser.add_argument("--gaps-file", type=str, default=None, help="Path to JSON gaps file (from omega_gap_detector.py --json)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without activating")
    parser.add_argument("--max-agents", type=int, default=DEFAULT_MAX_AGENTS, help="Max agents per wave (default: 3)")
    args = parser.parse_args()

    if not args.db.is_file():
        msg = f"DB not found: {args.db}"
        print(json.dumps({"error": msg}) if args.json else f"❌ {msg}")
        return 1

    try:
        conn = _connect(args.db)
        gaps = load_gaps(args.gaps_file, conn)

        if not gaps:
            msg = "No gaps detected — system is healthy or gap source is empty."
            print(json.dumps({"status": "no_gaps", "message": msg}) if args.json else f"✅ {msg}")
            conn.close()
            return 0

        activations = generate_agent_prompts(gaps)
        plan = activation_plan(activations, max_agents=args.max_agents)

        print_activation_plan(plan, dry_run=args.dry_run, as_json=args.json)
        conn.close()
    except Exception as exc:
        msg = str(exc)
        print(json.dumps({"error": msg}) if args.json else f"❌ Error: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
