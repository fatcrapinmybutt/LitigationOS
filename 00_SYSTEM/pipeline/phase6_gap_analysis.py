"""
OMEGA Phase 6: EGCP v2 Gap Analysis
Compares atom stores against master files to detect gaps and generate tickets.
"""
import csv
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, LEXOS_BIBLE, MCL_PATTERN, MCR_PATTERN, MRE_PATTERN,
    CASE_CITE_PATTERN, PERSON_NAMES, sha256_file,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

# ── Master file names ───────────────────────────────────────────────
KNOWLEDGE_ALL = "KNOWLEDGE_ALL.jsonl"
AUTHORITY_SHARDS = "authority_shards_all.jsonl"
EC_AUTHORITY_MAP = "EC_AUTHORITY_MAP (1) (1).jsonl"
NEO4J_NODES = "neo4j_nodes.csv"
SYNTHESIS_DATA = "SYNTHESIS_DATA.json"
MASTER_CSVS = [
    "MASTER_EVIDENCE_INDEX.csv", "MASTER_VIOLATIONS.csv",
    "MASTER_PERSONS.csv", "MASTER_TIMELINE.csv", "MASTER_CITATIONS.csv",
]


def _load_jsonl_ids(path: Path, id_field: str = "sha256") -> set[str]:
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


def _load_csv_column(path: Path, column: str) -> set[str]:
    vals: set[str] = set()
    if not path.exists():
        return vals
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            v = row.get(column)
            if v:
                vals.add(v.strip())
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[PHASE6] Warning: {e}", file=sys.stderr)
    return vals


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


def _extract_citations(text: str) -> list[str]:
    cites: list[str] = []
    for pat in (MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN):
        cites.extend(pat.findall(text))
    return cites


def _make_ticket_id(target: str, key: str) -> str:
    raw = f"{target}|{key}"
    return f"GAP-{hashlib.sha1(raw.encode()).hexdigest()[:12]}"


def run_gap_analysis(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase6"):
        print("[PHASE6] Already complete, skipping", file=sys.stderr)
        return

    atoms = _load_atoms(cycle_dir)
    if not atoms:
        print("[PHASE6] No atom stores found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase6", {"status": "done", "tickets": 0, "reason": "no_atoms"})
        return

    print(f"[PHASE6] Loaded {len(atoms):,} atoms, analysing gaps...", file=sys.stderr)
    start = time.time()

    # Load existing master IDs
    known_sha256s = _load_jsonl_ids(MASTER_ROOT / KNOWLEDGE_ALL, "sha256")
    known_shards = _load_jsonl_ids(MASTER_ROOT / AUTHORITY_SHARDS, "shard_id")
    known_ec = _load_jsonl_ids(MASTER_ROOT / EC_AUTHORITY_MAP, "entry_id")
    known_nodes = _load_csv_column(MASTER_ROOT / NEO4J_NODES, "node_id")
    known_persons = _load_csv_column(MASTER_ROOT / "MASTER_PERSONS.csv", "name")
    known_citations = _load_csv_column(MASTER_ROOT / "MASTER_CITATIONS.csv", "citation")
    known_timeline = _load_csv_column(MASTER_ROOT / "MASTER_TIMELINE.csv", "date")

    tickets: list[dict] = []
    new_files: list[dict] = []
    auth_plan: list[dict] = []

    for idx, atom in enumerate(atoms):
        text = atom.get("text", "") or atom.get("content", "") or ""
        sha = atom.get("source_sha256", "")
        atype = atom.get("atom_type", "")

        # File-level gap
        if sha and sha not in known_sha256s:
            tid = _make_ticket_id("file", sha)
            tickets.append({
                "ticket_id": tid, "gap_type": "file",
                "target_field": "KNOWLEDGE_ALL", "why_needed": "New SHA256 not in knowledge base",
                "acquisition_method": "ingest_from_cycle", "search_query_terms": sha[:16],
                "deadline_risk": "low",
            })
            new_files.append({"sha256": sha, "atom_type": atype, "source": atom.get("source_path", "")})
            known_sha256s.add(sha)

        # Citation gaps
        cites = _extract_citations(text)
        for cite in cites:
            cite_norm = cite.strip()
            if cite_norm and cite_norm not in known_citations:
                tid = _make_ticket_id("citation", cite_norm)
                is_mcl = bool(MCL_PATTERN.search(cite_norm))
                is_mcr = bool(MCR_PATTERN.search(cite_norm))
                tickets.append({
                    "ticket_id": tid, "gap_type": "citation",
                    "target_field": "MASTER_CITATIONS / authority_shards",
                    "why_needed": f"Citation '{cite_norm}' not in master citation index",
                    "acquisition_method": "legislature_lookup" if (is_mcl or is_mcr) else "westlaw_search",
                    "search_query_terms": cite_norm,
                    "deadline_risk": "high" if is_mcl else "medium",
                })
                auth_plan.append({
                    "citation": cite_norm, "type": "MCL" if is_mcl else ("MCR" if is_mcr else "caselaw"),
                    "method": "legislature_lookup" if (is_mcl or is_mcr) else "westlaw_search",
                })
                known_citations.add(cite_norm)

        # Person gaps
        for name, role in PERSON_NAMES.items():
            if name.lower() in text.lower() and name not in known_persons:
                tid = _make_ticket_id("person", name)
                tickets.append({
                    "ticket_id": tid, "gap_type": "person",
                    "target_field": "MASTER_PERSONS",
                    "why_needed": f"Person '{name}' ({role}) referenced but not in master persons",
                    "acquisition_method": "extract_from_atoms",
                    "search_query_terms": name,
                    "deadline_risk": "medium",
                })
                known_persons.add(name)

        # Timeline gaps (dates in text not in master)
        dates = re.findall(r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b", text)
        for d in dates:
            d_norm = d.replace("/", "-")
            if d_norm not in known_timeline:
                tid = _make_ticket_id("timeline", d_norm)
                tickets.append({
                    "ticket_id": tid, "gap_type": "timeline",
                    "target_field": "MASTER_TIMELINE",
                    "why_needed": f"Date {d_norm} referenced in atom but not in timeline",
                    "acquisition_method": "extract_from_atoms",
                    "search_query_terms": d_norm,
                    "deadline_risk": "low",
                })
                known_timeline.add(d_norm)

        # Authority / node gap
        node_id = atom.get("node_id") or atom.get("id")
        if node_id and str(node_id) not in known_nodes:
            tid = _make_ticket_id("authority", str(node_id))
            tickets.append({
                "ticket_id": tid, "gap_type": "authority",
                "target_field": "neo4j_nodes / EC_AUTHORITY_MAP",
                "why_needed": f"Node {node_id} not in graph or authority map",
                "acquisition_method": "graph_delta_gen",
                "search_query_terms": str(node_id),
                "deadline_risk": "medium",
            })
            known_nodes.add(str(node_id))

        if (idx + 1) % 5000 == 0:
            report_progress("phase6", idx + 1, len(atoms))

    elapsed = time.time() - start

    # Dedup tickets by ticket_id
    seen_ids: set[str] = set()
    deduped: list[dict] = []
    for t in tickets:
        if t["ticket_id"] not in seen_ids:
            deduped.append(t)
            seen_ids.add(t["ticket_id"])
    tickets = deduped

    print(f"[PHASE6] {len(tickets):,} gap tickets generated in {elapsed:.0f}s", file=sys.stderr)

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        # gap_tickets.jsonl
        with open(cycle_dir / "gap_tickets.jsonl", "w", encoding="utf-8") as f:
            for t in tickets:
                f.write(json.dumps(t) + "\n")

        # gap_report.md
        by_type: dict[str, int] = {}
        for t in tickets:
            by_type[t["gap_type"]] = by_type.get(t["gap_type"], 0) + 1
        lines = ["# EGCP v2 Gap Analysis Report\n", f"**Total tickets:** {len(tickets)}\n"]
        for gt, cnt in sorted(by_type.items()):
            lines.append(f"- **{gt}**: {cnt}")
        lines.append(f"\n*Generated in {elapsed:.0f}s from {len(atoms):,} atoms*\n")
        (cycle_dir / "gap_report.md").write_text("\n".join(lines), encoding="utf-8")

        # new_files_to_integrate.csv
        if new_files:
            with open(cycle_dir / "new_files_to_integrate.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["sha256", "atom_type", "source"])
                w.writeheader()
                w.writerows(new_files)

        # authority_acquisition_plan.csv
        if auth_plan:
            with open(cycle_dir / "authority_acquisition_plan.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["citation", "type", "method"])
                w.writeheader()
                w.writerows(auth_plan)

        stats = {
            "atoms_analysed": len(atoms), "tickets": len(tickets),
            "by_type": by_type, "new_files": len(new_files),
            "auth_plan_entries": len(auth_plan), "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "gap_analysis_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase6", {"status": "done", "tickets": len(tickets), "elapsed": f"{elapsed:.0f}s"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 6: EGCP v2 Gap Analysis")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_gap_analysis(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
