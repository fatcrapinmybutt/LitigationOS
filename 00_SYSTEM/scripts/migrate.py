"""
LitigationOS Drive Migration v2 — MOVE-based (zero extra disk space)
Since everything is on the same C: drive, os.rename() is instant.
Runs in numbered phases — each phase verified before proceeding.

Usage:
  python migrate.py --phase 1        # Move system infrastructure
  python migrate.py --phase 2        # Move case files
  python migrate.py --phase all      # Run all phases sequentially
  python migrate.py --status         # Show what's done
  python migrate.py --undo 1         # Reverse phase 1 moves
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime

# ── Paths ────────────────────────────────────────────────────────────
NEW_ROOT = Path(r"C:\Users\andre\LitigationOS")
OLD_MASTER = Path(r"C:\Users\andre\LITIGATIONOS_MASTER")
OLD_SCANS = Path(r"C:\Users\andre\scans")

PROVENANCE = NEW_ROOT / "00_SYSTEM" / "provenance"
LOG_PATH = PROVENANCE / "migration_log.jsonl"


# ── Logging ──────────────────────────────────────────────────────────
def log_action(action: str, src: str, dst: str, phase: int, status: str = "ok", note: str = ""):
    entry = {
        "ts": datetime.now().isoformat(),
        "phase": phase,
        "action": action,
        "src": src,
        "dst": dst,
        "status": status,
        "note": note,
    }
    PROVENANCE.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    tag = "✓" if status == "ok" else "✗" if status == "error" else "·"
    print(f"  {tag} {action}: {Path(src).name}")


# ── Move Helpers ─────────────────────────────────────────────────────
def move_file(src: Path, dst: Path, phase: int) -> bool:
    """Move a single file. Same-drive = instant rename."""
    if not src.exists():
        return False
    if dst.exists():
        log_action("skip_exists", str(src), str(dst), phase, "skip")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(src), str(dst))
        log_action("move", str(src), str(dst), phase)
        return True
    except (PermissionError, OSError) as e:
        log_action("move", str(src), str(dst), phase, "error", str(e))
        return False


def move_dir(src: Path, dst: Path, phase: int) -> int:
    """Move entire directory. If dst doesn't exist, single rename. Otherwise merge."""
    if not src.exists():
        print(f"  · skip: {src.name} (not found)")
        return 0
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            count = sum(1 for _ in dst.rglob("*") if _.is_file())
            log_action("move_dir", str(src), str(dst), phase, note=f"{count} files")
            print(f"  ✓ {src.name} → {dst.relative_to(NEW_ROOT)} ({count} files)")
            return count
        except (PermissionError, OSError) as e:
            log_action("move_dir", str(src), str(dst), phase, "error", str(e))
            print(f"  ✗ {src.name}: {e}")
            return 0
    else:
        # Merge into existing dir
        count = 0
        for item in list(src.rglob("*")):
            if item.is_file():
                rel = item.relative_to(src)
                target = dst / rel
                if move_file(item, target, phase):
                    count += 1
        # Clean empty source dirs
        _clean_empty_dirs(src)
        return count


def move_files_by_pattern(src_dir: Path, dst_dir: Path, patterns: list[str], phase: int) -> int:
    """Move files matching glob patterns."""
    count = 0
    for pat in patterns:
        for f in list(src_dir.glob(pat)):
            if f.is_file():
                if move_file(f, dst_dir / f.name, phase):
                    count += 1
    return count


def _clean_empty_dirs(root: Path):
    """Remove empty directories bottom-up."""
    for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
        if not filenames and not dirnames:
            try:
                os.rmdir(dirpath)
            except OSError:
                pass


# ── Phase Functions ──────────────────────────────────────────────────

def phase_1():
    """System infrastructure: pipeline, MCP, lexos, cyclepacks, scripts."""
    print("\n[PHASE 1] System Infrastructure")
    ph = 1
    total = 0

    total += move_dir(OLD_SCANS / "tooling", NEW_ROOT / "00_SYSTEM" / "pipeline", ph)
    total += move_dir(OLD_MASTER / "litigation_context_mcp", NEW_ROOT / "00_SYSTEM" / "mcp_server", ph)
    total += move_dir(OLD_MASTER / "lexos_bible", NEW_ROOT / "00_SYSTEM" / "lexos_bible", ph)
    total += move_dir(OLD_MASTER / "cyclepacks", NEW_ROOT / "00_SYSTEM" / "cyclepacks", ph)

    # Utility scripts from MASTER root
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "00_SYSTEM" / "scripts", ["*.py"], ph)

    print(f"  Phase 1 total: {total} files moved")
    return total


def phase_2():
    """Case files routed to lanes by filename keywords."""
    print("\n[PHASE 2] Case Files → Lanes")
    ph = 2
    total = 0

    # Lane A: Watson/Custody
    kw_map_a = {
        "judge_mcneill/disqualification": ["*disqualification*", "*Disqualification*"],
        "judge_mcneill/jtc_complaint": ["*JTC*", "*jtc*"],
        "judge_mcneill/judicial_analysis": ["*McNeill*", "*mcneill*", "*SCANS_JUDICIAL*"],
        "cases/2023-5907-PP/filings": ["*PPO*", "*ppo*"],
    }
    lane_a = NEW_ROOT / "01_CASE_FILES" / "LANE_A_WATSON_CUSTODY"
    for subdir, patterns in kw_map_a.items():
        total += move_files_by_pattern(OLD_MASTER, lane_a / subdir, patterns, ph)

    # Lane B: Shady Oaks
    lane_b = NEW_ROOT / "01_CASE_FILES" / "LANE_B_SHADY_OAKS_HOUSING" / "cases" / "2025-002760-CZ" / "filings"
    total += move_files_by_pattern(OLD_MASTER, lane_b, ["*Shady*", "*shady*"], ph)

    # Lane C: Convergence
    lane_c = NEW_ROOT / "01_CASE_FILES" / "LANE_C_CONVERGENCE_COUNTY"
    total += move_files_by_pattern(OLD_MASTER, lane_c / "federal" / "42usc1983",
                                   ["*1983*", "*42USC*"], ph)

    print(f"  Phase 2 total: {total} files moved")
    return total


def phase_3():
    """Evidence from scans/."""
    print("\n[PHASE 3] Evidence")
    ph = 3
    total = 0

    total += move_dir(OLD_SCANS / "MEEK_HARVEST_EXTRACTED", NEW_ROOT / "02_EVIDENCE" / "meek_harvest", ph)
    total += move_dir(OLD_SCANS / "SESSION_EXPORT", NEW_ROOT / "02_EVIDENCE" / "session_exports", ph)
    total += move_dir(OLD_SCANS / "extracts", NEW_ROOT / "02_EVIDENCE" / "extracts", ph)
    total += move_dir(OLD_SCANS / "extracts_full", NEW_ROOT / "02_EVIDENCE" / "extracts", ph)

    print(f"  Phase 3 total: {total} files moved")
    return total


def phase_4():
    """Legal authorities: reference library, forms, court rules."""
    print("\n[PHASE 4] Legal Authorities")
    ph = 4
    total = 0

    total += move_dir(OLD_MASTER / "00_JUDICIAL_REFERENCE_LIBRARY",
                      NEW_ROOT / "03_LEGAL_AUTHORITIES" / "judicial_reference", ph)
    total += move_dir(OLD_SCANS / "04_FORMS", NEW_ROOT / "03_LEGAL_AUTHORITIES" / "forms", ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "03_LEGAL_AUTHORITIES" / "court_rules",
                                   ["michigan-court-rules*"], ph)
    move_file(OLD_MASTER / "MASTER_CITATIONS.csv",
              NEW_ROOT / "03_LEGAL_AUTHORITIES" / "case_citations" / "MASTER_CITATIONS.csv", ph)
    total += 1

    print(f"  Phase 4 total: {total} files moved")
    return total


def phase_5():
    """Court filings by lifecycle."""
    print("\n[PHASE 5] Court Filings")
    ph = 5
    total = 0

    total += move_dir(OLD_MASTER / "COURT_FILINGS_FINAL", NEW_ROOT / "04_COURT_FILINGS" / "03_FINAL", ph)
    total += move_dir(OLD_MASTER / "COURT_PACKETS_v3",
                      NEW_ROOT / "04_COURT_FILINGS" / "03_FINAL" / "packets_v3", ph)
    total += move_dir(OLD_SCANS / "PRIORITY_FILINGS_FEB17", NEW_ROOT / "04_COURT_FILINGS" / "01_DRAFTING", ph)
    total += move_dir(OLD_SCANS / "FINAL_FILINGS",
                      NEW_ROOT / "04_COURT_FILINGS" / "03_FINAL" / "legacy", ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "04_COURT_FILINGS" / "01_DRAFTING",
                                   ["FILING_*.md"], ph)

    print(f"  Phase 5 total: {total} files moved")
    return total


def phase_6():
    """Analysis: briefs, graphs, legal output."""
    print("\n[PHASE 6] Analysis")
    ph = 6
    total = 0

    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "05_ANALYSIS" / "briefs",
                                   ["*BRIEF*.md", "*INTELLIGENCE*.md"], ph)
    total += move_dir(OLD_MASTER / "GRAPH MASTER OMEGA", NEW_ROOT / "05_ANALYSIS" / "graphs", ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "05_ANALYSIS" / "graphs",
                                   ["*.graphml", "*.cypher", "*graph*.html", "*GRAPH*.html",
                                    "*SUPERGRAPH*", "*graph_viewer*"], ph)
    total += move_dir(OLD_SCANS / "LEGAL_ANALYSIS_OUTPUT", NEW_ROOT / "05_ANALYSIS" / "legal_output", ph)
    total += move_dir(OLD_SCANS / "LEGAL_OUTPUT", NEW_ROOT / "05_ANALYSIS" / "legal_output", ph)
    total += move_dir(OLD_SCANS / "reports", NEW_ROOT / "05_ANALYSIS" / "reports", ph)

    print(f"  Phase 6 total: {total} files moved")
    return total


def phase_7():
    """Master data: CSVs, JSONL, neo4j, synthesis."""
    print("\n[PHASE 7] Data")
    ph = 7
    total = 0

    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "06_DATA" / "master",
                                   ["MASTER_*.csv"], ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "06_DATA" / "knowledge",
                                   ["*.jsonl"], ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "06_DATA" / "neo4j",
                                   ["neo4j_*"], ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "06_DATA" / "synthesis",
                                   ["SYNTHESIS_*", "violations.json", "bloom_perspective.json"], ph)

    print(f"  Phase 7 total: {total} files moved")
    return total


def phase_8():
    """Specs: brain specs, blueprints, strategy, delta map."""
    print("\n[PHASE 8] Specs & Docs")
    ph = 8
    total = 0

    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "07_SPECS" / "brain_specs",
                                   ["BRAIN_SPEC*"], ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "07_SPECS" / "blueprints",
                                   ["*BLUEPRINT*", "*ARCHITECTURE*", "MEGA_*"], ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "07_SPECS" / "strategy",
                                   ["*STRATEGY*", "*LEXVAULT*"], ph)
    move_file(OLD_MASTER / "EVENT_HORIZON_DELTA_INTEGRATION_MAP.md",
              NEW_ROOT / "07_SPECS" / "delta_map" / "EVENT_HORIZON_DELTA_INTEGRATION_MAP.md", ph)
    total += 1

    print(f"  Phase 8 total: {total} files moved")
    return total


def phase_9():
    """Apps — SKIP node_modules, move only source code."""
    print("\n[PHASE 9] Apps (source only, no node_modules)")
    ph = 9
    total = 0

    for app_name, app_dir_name in [
        ("desktop", "LitigationOS-Desktop"),
        ("mobile", "LitigationOS-Mobile"),
        ("web", "LitigationOS-Commercial-Website"),
    ]:
        src = OLD_MASTER / app_dir_name
        dst = NEW_ROOT / "08_APPS" / app_name
        if not src.exists():
            print(f"  · skip: {app_dir_name} (not found)")
            continue
        # Move files but skip node_modules, .git, dist, build
        skip_dirs = {"node_modules", ".git", "dist", "build", "__pycache__", ".next", ".venv"}
        count = 0
        for item in list(src.rglob("*")):
            if item.is_file():
                # Check if any parent is in skip_dirs
                rel_parts = item.relative_to(src).parts
                if any(part in skip_dirs for part in rel_parts):
                    continue
                rel = item.relative_to(src)
                if move_file(item, dst / rel, ph):
                    count += 1
        # Clean empty dirs in source
        _clean_empty_dirs(src)
        print(f"  {app_name}: {count} source files moved")
        total += count

    print(f"  Phase 9 total: {total} files moved")
    return total


def phase_10():
    """Archive: old packet versions, offloads, zips."""
    print("\n[PHASE 10] Archive")
    ph = 10
    total = 0

    total += move_dir(OLD_MASTER / "COURT_PACKETS", NEW_ROOT / "99_ARCHIVE" / "court_packets_v1", ph)
    total += move_dir(OLD_MASTER / "COURT_PACKETS_v2", NEW_ROOT / "99_ARCHIVE" / "court_packets_v2", ph)
    total += move_dir(OLD_MASTER / "OFFLOAD_20260219", NEW_ROOT / "99_ARCHIVE" / "offload_20260219", ph)
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "99_ARCHIVE" / "zips",
                                   ["*.zip", "*.rar"], ph)
    total += move_dir(OLD_SCANS / "LITIGATIONOS_MASTER",
                      NEW_ROOT / "99_ARCHIVE" / "scans_reference", ph)
    total += move_dir(OLD_SCANS / "PIGORS_CASE_MASTER",
                      NEW_ROOT / "99_ARCHIVE" / "pigors_case_master", ph)

    # Remaining loose files from MASTER root
    total += move_files_by_pattern(OLD_MASTER, NEW_ROOT / "99_ARCHIVE" / "superseded",
                                   ["*.html", "*.txt", "*.docx", "*.yml", "manifest.json",
                                    "*.skill", "tail_preview.csv"], ph)

    # AGENT_JOURNALS
    total += move_dir(OLD_MASTER / "AGENT_JOURNALS", NEW_ROOT / "99_ARCHIVE" / "agent_journals", ph)

    print(f"  Phase 10 total: {total} files moved")
    return total


# ── Status & Undo ────────────────────────────────────────────────────

def show_status():
    """Show migration progress."""
    if not LOG_PATH.exists():
        print("No migration log found.")
        return
    phase_stats: dict[int, dict] = {}
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            ph = e.get("phase", 0)
            if ph not in phase_stats:
                phase_stats[ph] = {"ok": 0, "skip": 0, "error": 0}
            phase_stats[ph][e.get("status", "ok")] += 1
        except json.JSONDecodeError:
            pass

    print("Migration Status:")
    for ph in sorted(phase_stats):
        s = phase_stats[ph]
        print(f"  Phase {ph:2d}: {s['ok']} moved, {s['skip']} skipped, {s['error']} errors")
    total_ok = sum(s["ok"] for s in phase_stats.values())
    print(f"  Total moved: {total_ok}")


def undo_phase(phase_num: int):
    """Reverse all moves from a specific phase."""
    if not LOG_PATH.exists():
        print("No migration log found.")
        return
    moves = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            if e.get("phase") == phase_num and e.get("status") == "ok" and "move" in e.get("action", ""):
                moves.append(e)
        except json.JSONDecodeError:
            pass

    print(f"Undoing phase {phase_num}: {len(moves)} moves to reverse")
    reversed_count = 0
    for entry in reversed(moves):
        src = Path(entry["dst"])  # current location
        dst = Path(entry["src"])  # original location
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(src), str(dst))
                reversed_count += 1
            except OSError as e:
                print(f"  ✗ Could not reverse: {src.name} → {e}")
    print(f"  Reversed {reversed_count} moves")


# ── Main ─────────────────────────────────────────────────────────────

PHASE_MAP = {
    1: phase_1, 2: phase_2, 3: phase_3, 4: phase_4, 5: phase_5,
    6: phase_6, 7: phase_7, 8: phase_8, 9: phase_9, 10: phase_10,
}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LitigationOS Drive Migration v2")
    parser.add_argument("--phase", help="Phase number (1-10) or 'all'")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--undo", type=int, help="Undo a specific phase number")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.undo:
        undo_phase(args.undo)
    elif args.phase:
        # Clear old log if starting fresh
        start = time.time()
        if args.phase == "all":
            for i in range(1, 11):
                PHASE_MAP[i]()
        else:
            ph = int(args.phase)
            if ph in PHASE_MAP:
                PHASE_MAP[ph]()
            else:
                print(f"Unknown phase: {ph}. Valid: 1-10")
                sys.exit(1)
        elapsed = time.time() - start
        print(f"\nDone in {elapsed:.1f}s")
        show_status()
    else:
        parser.print_help()
