"""
OMEGA Phase 15: Court-Ready Validation
Final validation of all pipeline outputs: atom integrity, citation format,
lane-mixing, touchlog coverage, and brain nucleus size limits.
"""
import json
import re
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, LEXOS_BIBLE, MASTER_MODIFIABLE, MEEK_SIGNALS,
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

MAX_BRAIN_BYTES = 500 * 1024  # 500 KB

# Lane A keywords (Watson/custody) vs Lane B (Shady Oaks/housing)
LANE_A_SIGNALS = MEEK_SIGNALS.get("MEEK2", re.compile(r"$^"))  # custody
LANE_B_SIGNALS = MEEK_SIGNALS.get("MEEK1", re.compile(r"$^"))  # housing


def _check_result(name: str, passed: bool, details: str = "") -> dict:
    return {
        "check": name,
        "result": "PASS" if passed else "FAIL",
        "details": details,
    }


def _warn_result(name: str, details: str = "") -> dict:
    return {"check": name, "result": "WARN", "details": details}


def _validate_atom_stores(cycle_dir: Path) -> list[dict]:
    """Check all atom stores have valid IDs and provenance."""
    results: list[dict] = []
    atom_files = ["fact_atoms.jsonl", "citation_atoms.jsonl",
                  "event_atoms.jsonl", "person_atoms.jsonl"]

    for fname in atom_files:
        fpath = cycle_dir / fname
        if not fpath.exists():
            fpath = cycle_dir / "atoms" / fname
        if not fpath.exists():
            results.append(_warn_result(f"atom_store_{fname}", "File not found"))
            continue

        total = 0
        missing_id = 0
        missing_source = 0
        for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                total += 1
                if not obj.get("atom_id") and not obj.get("id"):
                    missing_id += 1
                if not obj.get("source") and not obj.get("source_sha256") and not obj.get("source_path"):
                    missing_source += 1
            except json.JSONDecodeError:
                missing_id += 1

        passed = missing_id == 0 and missing_source == 0
        results.append(_check_result(
            f"atom_integrity_{fname}",
            passed,
            f"{total} atoms, {missing_id} missing ID, {missing_source} missing provenance",
        ))
    return results


def _validate_citation_format(cycle_dir: Path) -> dict:
    """Check all citations in citation_atoms.jsonl are correctly formatted."""
    fpath = cycle_dir / "citation_atoms.jsonl"
    if not fpath.exists():
        fpath = cycle_dir / "atoms" / "citation_atoms.jsonl"
    if not fpath.exists():
        return _warn_result("citation_format", "No citation_atoms.jsonl found")

    total = 0
    bad_format = 0
    for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            cite = obj.get("cite_text", "")
            ctype = obj.get("cite_type", "")
            total += 1
            if ctype in ("MCL", "MCR", "MRE"):
                # Verify the citation matches expected regex
                matched = False
                if ctype == "MCL" and MCL_PATTERN.search(cite):
                    matched = True
                elif ctype == "MCR" and MCR_PATTERN.search(cite):
                    matched = True
                elif ctype == "MRE" and MRE_PATTERN.search(cite):
                    matched = True
                if not matched:
                    bad_format += 1
        except json.JSONDecodeError:
            bad_format += 1

    return _check_result(
        "citation_format",
        bad_format == 0,
        f"{total} citations checked, {bad_format} bad format",
    )


def _validate_lane_mixing(cycle_dir: Path) -> list[dict]:
    """Detect lane-mixing violations: Watson evidence in Shady Oaks atoms etc."""
    results: list[dict] = []
    atom_files = ["fact_atoms.jsonl", "citation_atoms.jsonl",
                  "event_atoms.jsonl", "person_atoms.jsonl"]

    violations: list[dict] = []
    for fname in atom_files:
        fpath = cycle_dir / fname
        if not fpath.exists():
            fpath = cycle_dir / "atoms" / fname
        if not fpath.exists():
            continue

        for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text", "") or obj.get("content", "") or obj.get("context", "")
                meek_lanes = obj.get("meek_lanes", [])

                has_lane_a = LANE_A_SIGNALS.search(text) if text else None
                has_lane_b = LANE_B_SIGNALS.search(text) if text else None

                # Cross-contamination: atom tagged for one lane but has strong signals from the other
                if isinstance(meek_lanes, list):
                    tagged_a = "MEEK2" in meek_lanes
                    tagged_b = "MEEK1" in meek_lanes
                    if tagged_a and has_lane_b and not has_lane_a:
                        violations.append({
                            "atom_id": obj.get("atom_id", ""),
                            "file": fname,
                            "issue": "Custody-tagged atom has housing signals only",
                        })
                    if tagged_b and has_lane_a and not has_lane_b:
                        violations.append({
                            "atom_id": obj.get("atom_id", ""),
                            "file": fname,
                            "issue": "Housing-tagged atom has custody signals only",
                        })
            except json.JSONDecodeError:
                pass

    results.append(_check_result(
        "lane_mixing",
        len(violations) == 0,
        f"{len(violations)} lane-mixing violations detected",
    ))
    return results


def _validate_touchlog_coverage(cycle_dir: Path) -> list[dict]:
    """Strict touchlog validation: modified masters must have entries, entries must reference valid files."""
    from config import sha256_file

    results: list[dict] = []

    # Collect all touchlog entries with full paths
    touchlog_names: set[str] = set()
    touchlog_paths: list[str] = []
    for tl in cycle_dir.glob("touchlog_*.jsonl"):
        for line in tl.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    entry = json.loads(line)
                    p = entry.get("path", "")
                    if p:
                        touchlog_names.add(Path(p).name)
                        touchlog_paths.append(p)
                except json.JSONDecodeError:
                    pass

    # Load safety snapshot hashes (written by phase 0)
    snapshot_hashes: dict[str, str] = {}
    snap_file = cycle_dir / "safety_snapshot.json"
    if snap_file.exists():
        try:
            snap = json.loads(snap_file.read_text(encoding="utf-8", errors="replace"))
            for entry in snap.get("files", []):
                snapshot_hashes[entry.get("name", "")] = entry.get("sha256", "")
        except (json.JSONDecodeError, KeyError):
            pass

    # Check 1: Modified MASTER_MODIFIABLE files MUST have a touchlog entry
    missing_touchlog: list[str] = []
    for fname in MASTER_MODIFIABLE:
        master = MASTER_ROOT / fname
        if not master.exists():
            continue
        snap_hash = snapshot_hashes.get(fname, "")
        if snap_hash:
            try:
                current_hash = sha256_file(master)
            except OSError:
                continue
            if current_hash != snap_hash and fname not in touchlog_names:
                missing_touchlog.append(fname)

    results.append(_check_result(
        "touchlog_modified_coverage",
        len(missing_touchlog) == 0,
        f"{len(missing_touchlog)} modified master files lack touchlog entries: "
        + (", ".join(missing_touchlog[:10]) if missing_touchlog else "none"),
    ))

    # Check 2: Every touchlog entry must reference a file that actually exists
    ghost_entries: list[str] = []
    for p in touchlog_paths:
        if not Path(p).exists():
            ghost_entries.append(p)

    results.append(_check_result(
        "touchlog_file_exists",
        len(ghost_entries) == 0,
        f"{len(ghost_entries)} touchlog entries reference non-existent files: "
        + (", ".join(Path(g).name for g in ghost_entries[:10]) if ghost_entries else "none"),
    ))

    # Check 3: No touchlog entry should reference a file outside MASTER_ROOT or cycle_dir
    master_resolved = MASTER_ROOT.resolve()
    cycle_resolved = cycle_dir.resolve()
    out_of_scope: list[str] = []
    for p in touchlog_paths:
        try:
            resolved = Path(p).resolve()
            if not (str(resolved).startswith(str(master_resolved))
                    or str(resolved).startswith(str(cycle_resolved))):
                out_of_scope.append(p)
        except (OSError, ValueError):
            out_of_scope.append(p)

    results.append(_check_result(
        "touchlog_scope",
        len(out_of_scope) == 0,
        f"{len(out_of_scope)} touchlog entries reference files outside allowed roots: "
        + (", ".join(Path(o).name for o in out_of_scope[:10]) if out_of_scope else "none"),
    ))

    return results


def _validate_brain_sizes() -> list[dict]:
    """Verify all brain nuclei are under 500KB."""
    results: list[dict] = []
    brains_dir = LEXOS_BIBLE / "brains"
    if not brains_dir.exists():
        return [_warn_result("brain_sizes", "No brains directory found")]

    oversized: list[str] = []
    total = 0
    for bp in brains_dir.glob("brain_*.json"):
        total += 1
        if bp.stat().st_size > MAX_BRAIN_BYTES:
            oversized.append(f"{bp.name} ({bp.stat().st_size / 1024:.0f}KB)")

    results.append(_check_result(
        "brain_nucleus_sizes",
        len(oversized) == 0,
        f"{total} brains checked, {len(oversized)} oversized: {', '.join(oversized[:5])}",
    ))
    return results


def run_validation(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase15"):
        print("[PHASE15] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE15] Running court-ready validation...", file=sys.stderr)
    start = time.time()
    all_checks: list[dict] = []

    # a) Atom store integrity
    all_checks.extend(_validate_atom_stores(cycle_dir))

    # b) Citation format
    all_checks.append(_validate_citation_format(cycle_dir))

    # c) Lane-mixing
    all_checks.extend(_validate_lane_mixing(cycle_dir))

    # d) Touchlog coverage
    all_checks.extend(_validate_touchlog_coverage(cycle_dir))

    # e) Brain nucleus sizes
    all_checks.extend(_validate_brain_sizes())

    elapsed = time.time() - start

    # Summarise
    passes = sum(1 for c in all_checks if c["result"] == "PASS")
    warns = sum(1 for c in all_checks if c["result"] == "WARN")
    fails = sum(1 for c in all_checks if c["result"] == "FAIL")

    overall = "PASS"
    if fails > 0:
        overall = "FAIL"
    elif warns > 0:
        overall = "WARN"

    print(f"[PHASE15] Validation: {overall} ({passes} pass, {warns} warn, {fails} fail) in {elapsed:.0f}s",
          file=sys.stderr)

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "overall": overall,
            "total_checks": len(all_checks),
            "pass": passes,
            "warn": warns,
            "fail": fails,
            "checks": all_checks,
            "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "court_ready_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8",
        )
        write_phase_checkpoint(cycle_dir, "phase15", {
            "status": "done", "overall": overall,
            "pass": passes, "warn": warns, "fail": fails,
            "elapsed": f"{elapsed:.0f}s",
        })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 15: Court-Ready Validation")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_validation(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
