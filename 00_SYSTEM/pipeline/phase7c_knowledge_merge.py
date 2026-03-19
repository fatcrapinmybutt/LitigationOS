"""
OMEGA Phase 7C: Knowledge Base Merge
Appends new entries to authority_shards_all.jsonl, EC_AUTHORITY_MAP.jsonl,
and KNOWLEDGE_ALL.jsonl with dedup and touchlog safety.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, sha256_file,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done, write_touchlog

# Master JSONL targets
TARGETS = {
    "authority_shards_all.jsonl": "shard_id",
    "EC_AUTHORITY_MAP (1) (1).jsonl": "entry_id",
    "KNOWLEDGE_ALL.jsonl": "sha256",
}


def _load_existing_ids(path: Path, id_field: str) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            val = obj.get(id_field) or obj.get("id") or obj.get("shard_id") or obj.get("entry_id")
            if val:
                ids.add(str(val))
        except json.JSONDecodeError:
            pass
    return ids


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


def _make_shard_id(atom: dict) -> str:
    raw = json.dumps(atom, sort_keys=True)
    return f"SHARD-{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def _make_entry_id(atom: dict) -> str:
    raw = json.dumps(atom, sort_keys=True)
    return f"EC-{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def _build_shard_entry(atom: dict) -> dict:
    return {
        "shard_id": _make_shard_id(atom),
        "atom_type": atom.get("atom_type", "unknown"),
        "citation": atom.get("citation", atom.get("text", ""))[:300],
        "cite_type": atom.get("cite_type", ""),
        "source_sha256": atom.get("source_sha256", ""),
        "meek_lane": atom.get("meek_lane", ""),
    }


def _build_ec_entry(atom: dict) -> dict:
    return {
        "entry_id": _make_entry_id(atom),
        "atom_type": atom.get("atom_type", "unknown"),
        "authority": atom.get("citation", atom.get("text", ""))[:300],
        "source_sha256": atom.get("source_sha256", ""),
        "relevance": atom.get("score", 0),
    }


def _build_knowledge_entry(atom: dict) -> dict:
    return {
        "sha256": atom.get("source_sha256", ""),
        "atom_type": atom.get("atom_type", "unknown"),
        "text": (atom.get("text", "") or atom.get("content", ""))[:2000],
        "source_path": atom.get("source_path", ""),
        "meek_lane": atom.get("meek_lane", ""),
    }


def _atomic_append(path: Path, new_lines: list[str], cycle_dir: Path, dry_run: bool) -> int:
    if not new_lines or dry_run:
        return len(new_lines)

    sha_before = sha256_file(path) if path.exists() else None
    write_touchlog(cycle_dir, "phase7c", str(path), "append_start", sha_before=sha_before)

    # Read existing content, append new lines, write atomically
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing and not existing.endswith("\n"):
            existing += "\n"

    new_content = existing + "\n".join(new_lines) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_content, encoding="utf-8")
    os.replace(str(tmp), str(path))

    sha_after = sha256_file(path)
    write_touchlog(cycle_dir, "phase7c", str(path), "append_done", sha_after=sha_after)
    return len(new_lines)


def run_knowledge_merge(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase7c"):
        print("[PHASE7C] Already complete, skipping", file=sys.stderr)
        return

    atoms = _load_atoms(cycle_dir)
    if not atoms:
        print("[PHASE7C] No atom stores found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase7c", {"status": "done", "appended": 0, "reason": "no_atoms"})
        return

    print(f"[PHASE7C] Loaded {len(atoms):,} atoms, merging into knowledge base...", file=sys.stderr)
    start = time.time()
    results: dict[str, int] = {}

    # ── authority_shards_all.jsonl ───────────────────────────────────
    shard_file = "authority_shards_all.jsonl"
    shard_path = MASTER_ROOT / shard_file
    existing_shard_ids = _load_existing_ids(shard_path, "shard_id")

    shard_lines: list[str] = []
    for atom in atoms:
        if atom.get("atom_type") == "citation":
            entry = _build_shard_entry(atom)
            if entry["shard_id"] not in existing_shard_ids:
                shard_lines.append(json.dumps(entry, ensure_ascii=False))
                existing_shard_ids.add(entry["shard_id"])

    results[shard_file] = _atomic_append(shard_path, shard_lines, cycle_dir, dry_run)
    report_progress("phase7c", 1, 3)

    # ── EC_AUTHORITY_MAP.jsonl ───────────────────────────────────────
    ec_file = "EC_AUTHORITY_MAP (1) (1).jsonl"
    ec_path = MASTER_ROOT / ec_file
    existing_ec_ids = _load_existing_ids(ec_path, "entry_id")

    ec_lines: list[str] = []
    for atom in atoms:
        if atom.get("atom_type") == "citation":
            entry = _build_ec_entry(atom)
            if entry["entry_id"] not in existing_ec_ids:
                ec_lines.append(json.dumps(entry, ensure_ascii=False))
                existing_ec_ids.add(entry["entry_id"])

    results[ec_file] = _atomic_append(ec_path, ec_lines, cycle_dir, dry_run)
    report_progress("phase7c", 2, 3)

    # ── KNOWLEDGE_ALL.jsonl ──────────────────────────────────────────
    ka_file = "KNOWLEDGE_ALL.jsonl"
    ka_path = MASTER_ROOT / ka_file
    existing_ka_ids = _load_existing_ids(ka_path, "sha256")

    ka_lines: list[str] = []
    seen_ka: set[str] = set()
    for atom in atoms:
        sha = atom.get("source_sha256", "")
        if sha and sha not in existing_ka_ids and sha not in seen_ka:
            entry = _build_knowledge_entry(atom)
            ka_lines.append(json.dumps(entry, ensure_ascii=False))
            seen_ka.add(sha)

    results[ka_file] = _atomic_append(ka_path, ka_lines, cycle_dir, dry_run)
    report_progress("phase7c", 3, 3)

    elapsed = time.time() - start
    total = sum(results.values())
    print(f"[PHASE7C] Knowledge merge complete: {total:,} entries appended across {len(results)} files in {elapsed:.0f}s", file=sys.stderr)
    for fname, cnt in results.items():
        if cnt > 0:
            print(f"  {fname}: +{cnt:,}", file=sys.stderr)

    if not dry_run:
        stats = {"results": results, "total_appended": total, "elapsed_seconds": round(elapsed, 1)}
        (cycle_dir / "knowledge_merge_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase7c", {"status": "done", "appended": total, "elapsed": f"{elapsed:.0f}s"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 7C: Knowledge Merge")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_knowledge_merge(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
