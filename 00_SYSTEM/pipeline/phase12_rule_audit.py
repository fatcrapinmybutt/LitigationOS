"""
OMEGA Phase 12: MCR/MCL Rule Audit
Verifies every MCR and MCL citation has valid authority text, correct format,
and is currently in force.
"""
import json
import re
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, MCL_PATTERN, MCR_PATTERN, MRE_PATTERN,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

# Expected citation formats
MCL_FORMAT = re.compile(r"^MCL\s+\d+\.\d+[a-z]?$")
MCR_FORMAT = re.compile(r"^MCR\s+\d+\.\d+(\([A-Za-z0-9]+\))*$")
MRE_FORMAT = re.compile(r"^MRE\s+\d+(\.\d+)?$")

AUTHORITY_SHARDS = "authority_shards_all.jsonl"
KNOWLEDGE_ALL = "KNOWLEDGE_ALL.jsonl"


def _load_authority_index(path: Path) -> dict[str, dict]:
    """Load JSONL authority file into {citation_text: record} index."""
    idx: dict[str, dict] = {}
    if not path.exists():
        return idx
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            for field in ("citation", "cite_text", "rule", "shard_id", "title"):
                val = obj.get(field, "")
                if val:
                    idx[str(val).strip()] = obj
        except json.JSONDecodeError:
            pass
    return idx


def _check_format(cite_text: str, cite_type: str) -> bool:
    if cite_type == "MCL":
        return bool(MCL_FORMAT.match(cite_text))
    elif cite_type == "MCR":
        return bool(MCR_FORMAT.match(cite_text))
    elif cite_type == "MRE":
        return bool(MRE_FORMAT.match(cite_text))
    return True


def _check_in_force(record: dict) -> bool:
    """Check if an authority record has known repeal/amendment flags."""
    status = str(record.get("status", "")).lower()
    text = str(record.get("text", "") or record.get("content", "")).lower()
    if any(kw in status for kw in ("repealed", "superseded", "amended", "revoked")):
        return False
    if any(kw in text[:500] for kw in ("repealed by", "superseded by", "no longer in effect")):
        return False
    return True


def run_rule_audit(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase12"):
        print("[PHASE12] Already complete, skipping", file=sys.stderr)
        return

    # Load citation atoms
    cite_path = cycle_dir / "citation_atoms.jsonl"
    if not cite_path.exists():
        cite_path = cycle_dir / "atoms" / "citation_atoms.jsonl"
    if not cite_path.exists():
        print("[PHASE12] No citation_atoms.jsonl found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase12", {
            "status": "done", "reason": "no_citation_atoms", "audited": 0,
        })
        return

    citations: list[dict] = []
    for line in cite_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            try:
                citations.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    # Filter to MCR/MCL/MRE only
    rule_cites = [c for c in citations if c.get("cite_type") in ("MCL", "MCR", "MRE")]
    if not rule_cites:
        print("[PHASE12] No MCR/MCL/MRE citations found", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase12", {
            "status": "done", "reason": "no_rule_citations", "audited": 0,
        })
        return

    print(f"[PHASE12] Auditing {len(rule_cites):,} rule citations...", file=sys.stderr)
    start = time.time()

    # Load authority indexes
    auth_shards = _load_authority_index(MASTER_ROOT / AUTHORITY_SHARDS)
    knowledge = _load_authority_index(MASTER_ROOT / KNOWLEDGE_ALL)

    broken: list[dict] = []
    outdated: list[dict] = []
    format_errors: list[dict] = []
    valid_count = 0

    for idx, cite in enumerate(rule_cites):
        cite_text = cite.get("cite_text", "").strip()
        cite_type = cite.get("cite_type", "")
        source = cite.get("source", "")

        issues: list[str] = []

        # a) Check authority text exists
        record = auth_shards.get(cite_text) or knowledge.get(cite_text)
        if not record:
            issues.append("missing_authority_text")
            broken.append({
                "cite_text": cite_text, "cite_type": cite_type,
                "source": source, "issue": "missing_authority_text",
                "atom_id": cite.get("atom_id", ""),
            })

        # b) Check in force
        if record and not _check_in_force(record):
            issues.append("outdated_or_repealed")
            outdated.append({
                "cite_text": cite_text, "cite_type": cite_type,
                "source": source, "issue": "outdated_or_repealed",
                "status": record.get("status", "unknown"),
            })

        # c) Check format
        if not _check_format(cite_text, cite_type):
            issues.append("bad_format")
            format_errors.append({
                "cite_text": cite_text, "cite_type": cite_type,
                "source": source, "issue": "bad_format",
                "expected": f"MCL X.Y" if cite_type == "MCL" else f"MCR X.Y(Z)",
            })

        if not issues:
            valid_count += 1

        if (idx + 1) % 1000 == 0:
            report_progress("phase12", idx + 1, len(rule_cites))

    elapsed = time.time() - start
    total_audited = len(rule_cites)
    total_issues = len(broken) + len(outdated) + len(format_errors)
    health_score = round(valid_count / max(total_audited, 1) * 100, 1)

    print(
        f"[PHASE12] Done: {total_audited:,} audited, {valid_count:,} valid, "
        f"{total_issues:,} issues, health={health_score}% in {elapsed:.0f}s",
        file=sys.stderr,
    )

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        # rule_audit_report.json
        report = {
            "total_rule_citations": total_audited,
            "valid": valid_count,
            "broken_citations": len(broken),
            "outdated_rules": len(outdated),
            "format_errors": len(format_errors),
            "health_score_pct": health_score,
            "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "rule_audit_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8",
        )

        # broken_citations.jsonl
        all_broken = broken + outdated + format_errors
        with open(cycle_dir / "broken_citations.jsonl", "w", encoding="utf-8") as f:
            for entry in all_broken:
                f.write(json.dumps(entry) + "\n")

        # authority_health_score.json
        health = {
            "overall_score": health_score,
            "by_type": {},
            "authority_shards_count": len(auth_shards),
            "knowledge_all_count": len(knowledge),
        }
        for ctype in ("MCL", "MCR", "MRE"):
            subset = [c for c in rule_cites if c.get("cite_type") == ctype]
            bad = [b for b in all_broken if b.get("cite_type") == ctype]
            health["by_type"][ctype] = {
                "total": len(subset),
                "issues": len(bad),
                "score": round((len(subset) - len(bad)) / max(len(subset), 1) * 100, 1),
            }
        (cycle_dir / "authority_health_score.json").write_text(
            json.dumps(health, indent=2), encoding="utf-8",
        )

        write_phase_checkpoint(cycle_dir, "phase12", {
            "status": "done", "audited": total_audited,
            "valid": valid_count, "issues": total_issues,
            "health_score": health_score, "elapsed": f"{elapsed:.0f}s",
        })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 12: MCR/MCL Rule Audit")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_rule_audit(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
