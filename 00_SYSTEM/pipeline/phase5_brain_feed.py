"""
OMEGA Phase 5: LEXOS Brain Feed
Feeds 50 Brain Nuclei from atom stores produced by Phase 4d.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

from config import (
    LEXOS_BIBLE, MCL_PATTERN, MCR_PATTERN, MRE_PATTERN,
    CASE_CITE_PATTERN, USC_PATTERN, CANON_PATTERN,
    VIOLATION_KEYWORDS, PERSON_NAMES, MEEK_SIGNALS,
    get_cyclepack_dir, report_progress, make_atom_id,
)
from safety import write_phase_checkpoint, is_phase_done, write_touchlog

# ── Brain Group Ranges ──────────────────────────────────────────────
BRAIN_GROUPS = {
    "legal_authority": range(1, 9),    # 1-8
    "persons":         range(9, 18),   # 9-17
    "issues":          range(18, 26),  # 18-25
    "procedural":      range(26, 31),  # 26-30
    "analysis":        range(31, 41),  # 31-40
    "appellate":       range(41, 51),  # 41-50
}

LEGAL_AUTH_PATTERNS = [MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN, USC_PATTERN, CANON_PATTERN]
ISSUE_KEYWORDS = {
    "alienation": 18, "custody": 19, "parenting_time": 20, "PPO": 21,
    "contempt": 22, "due_process": 23, "fraud": 24, "bias": 25,
}

MAX_BRAIN_BYTES = 500 * 1024  # 500 KB


def _atom_sha1(atom: dict) -> str:
    raw = json.dumps(atom, sort_keys=True)
    return hashlib.sha1(raw.encode()).hexdigest()


def _score_atom_for_group(atom: dict, group: str) -> float:
    text = atom.get("text", "") or atom.get("content", "") or ""
    atype = atom.get("atom_type", "")
    score = 0.0

    if group == "legal_authority":
        for pat in LEGAL_AUTH_PATTERNS:
            score += len(pat.findall(text)) * 3.0
        if atype == "citation":
            score += 5.0

    elif group == "persons":
        for name in PERSON_NAMES:
            if name.lower() in text.lower():
                score += 2.0
        if atype == "person":
            score += 5.0

    elif group == "issues":
        for kw in ISSUE_KEYWORDS:
            if kw.lower().replace("_", " ") in text.lower():
                score += 3.0
        for kw in VIOLATION_KEYWORDS:
            if kw.lower() in text.lower():
                score += 1.5

    elif group == "procedural":
        for lane, pat in MEEK_SIGNALS.items():
            if pat.search(text):
                score += 2.0
        if atype in ("event", "filing"):
            score += 3.0

    elif group == "analysis":
        score += min(len(text) / 2000, 3.0)
        if atype in ("fact", "citation"):
            score += 2.0

    elif group == "appellate":
        if MEEK_SIGNALS.get("MEEK5", None) and MEEK_SIGNALS["MEEK5"].search(text):
            score += 5.0
        if atype == "citation":
            score += 2.0

    return score


def _assign_brain_id(atom: dict, group: str) -> int:
    """Deterministic brain assignment within a group range."""
    sha = _atom_sha1(atom)
    grp_range = BRAIN_GROUPS[group]
    idx = int(sha[:8], 16) % len(grp_range)
    return list(grp_range)[idx]


def _load_atoms(cycle_dir: Path) -> list[dict]:
    atoms = []
    for fname in ("fact_atoms.jsonl", "citation_atoms.jsonl",
                   "event_atoms.jsonl", "person_atoms.jsonl"):
        fpath = cycle_dir / fname
        if not fpath.exists():
            fpath = cycle_dir / "atoms" / fname
        if fpath.exists():
            for line in fpath.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line:
                    try:
                        atoms.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return atoms


def _load_brain(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"brain_id": path.stem, "entries": []}


def _trim_brain(brain: dict) -> dict:
    """Trim entries until serialised size <= MAX_BRAIN_BYTES."""
    while True:
        data = json.dumps(brain, ensure_ascii=False)
        if len(data.encode("utf-8")) <= MAX_BRAIN_BYTES:
            break
        if not brain.get("entries"):
            break
        # Drop lowest-scored entry
        brain["entries"].sort(key=lambda e: e.get("score", 0))
        brain["entries"].pop(0)
    return brain


def run_brain_feed(cycle_dir: Path, dry_run: bool = False):
    brains_dir = LEXOS_BIBLE / "brains"

    if is_phase_done(cycle_dir, "phase5"):
        print("[PHASE5] Already complete, skipping", file=sys.stderr)
        return

    if not brains_dir.exists():
        if dry_run:
            print(f"[PHASE5] DRY RUN: brains directory not found at {brains_dir}", file=sys.stderr)
            return
        brains_dir.mkdir(parents=True, exist_ok=True)
        print(f"[PHASE5] Created brains directory at {brains_dir}", file=sys.stderr)

    atoms = _load_atoms(cycle_dir)
    if not atoms:
        print("[PHASE5] No atom stores found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase5", {"status": "done", "fed": 0, "reason": "no_atoms"})
        return

    print(f"[PHASE5] Loaded {len(atoms):,} atoms, feeding brains...", file=sys.stderr)

    # Load all 50 brains
    brains: dict[int, dict] = {}
    for i in range(1, 51):
        bp = brains_dir / f"brain_{i:02d}.json"
        try:
            brains[i] = _load_brain(bp)
        except Exception as e:
            print(f"[PHASE5] WARNING: failed to load {bp.name}: {e}", file=sys.stderr)
            brains[i] = {"brain_id": f"brain_{i:02d}", "entries": []}
        brains[i].setdefault("brain_id", f"brain_{i:02d}")
        brains[i].setdefault("entries", [])

    # Build existing SHA1 sets for dedup
    existing_shas: dict[int, set] = {}
    for bid, brain in brains.items():
        existing_shas[bid] = {e.get("sha1") for e in brain["entries"] if e.get("sha1")}

    fed = 0
    modified_brains: set[int] = set()
    report_entries: list[dict] = []
    start = time.time()

    for idx, atom in enumerate(atoms):
        sha1 = _atom_sha1(atom)
        best_group = None
        best_score = 0.0

        for group in BRAIN_GROUPS:
            s = _score_atom_for_group(atom, group)
            if s > best_score:
                best_score = s
                best_group = group

        if best_group is None or best_score < 0.5:
            continue

        brain_id = _assign_brain_id(atom, best_group)

        if sha1 in existing_shas.get(brain_id, set()):
            continue

        entry = {
            "sha1": sha1,
            "atom_type": atom.get("atom_type", "unknown"),
            "score": round(best_score, 2),
            "group": best_group,
            "text": (atom.get("text", "") or atom.get("content", ""))[:2000],
            "source_sha256": atom.get("source_sha256", ""),
        }

        if not dry_run:
            brains[brain_id]["entries"].append(entry)
            existing_shas.setdefault(brain_id, set()).add(sha1)
            modified_brains.add(brain_id)

        report_entries.append({
            "sha1": sha1, "brain_id": brain_id, "group": best_group,
            "score": round(best_score, 2),
        })
        fed += 1

        if (idx + 1) % 5000 == 0:
            report_progress("phase5", idx + 1, len(atoms))

    # Trim and write modified brains
    written = 0
    for bid in sorted(modified_brains):
        brains[bid] = _trim_brain(brains[bid])
        bp = brains_dir / f"brain_{bid:02d}.json"

        if not dry_run:
            sha_before = None
            if bp.exists():
                sha_before = hashlib.sha256(bp.read_bytes()).hexdigest()

            bp.parent.mkdir(parents=True, exist_ok=True)
            tmp = bp.with_suffix(".tmp")
            tmp.write_text(json.dumps(brains[bid], indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(bp)

            sha_after = hashlib.sha256(bp.read_bytes()).hexdigest()
            write_touchlog(cycle_dir, "phase5", str(bp), "update_brain",
                           sha_before=sha_before, sha_after=sha_after)
            written += 1

    elapsed = time.time() - start
    print(f"[PHASE5] Fed {fed:,} atoms into {len(modified_brains)} brains ({written} written) in {elapsed:.0f}s", file=sys.stderr)

    # Write report
    if not dry_run:
        report_path = cycle_dir / "brain_feed_report.jsonl"
        with open(report_path, "w", encoding="utf-8") as f:
            for entry in report_entries:
                f.write(json.dumps(entry) + "\n")

        stats = {
            "atoms_loaded": len(atoms), "atoms_fed": fed,
            "brains_modified": len(modified_brains), "brains_written": written,
            "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "brain_feed_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase5", {"status": "done", "fed": fed, "elapsed": f"{elapsed:.0f}s"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 5: LEXOS Brain Feed")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_brain_feed(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
