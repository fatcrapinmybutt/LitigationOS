"""
OMEGA Phase 7A: Graph Delta Generation
Produces neo4j_nodes_delta.csv and neo4j_edges_delta.csv from atom stores.
"""
import csv
import hashlib
import io
import json
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, MCL_PATTERN, MCR_PATTERN, MRE_PATTERN,
    CASE_CITE_PATTERN, PERSON_NAMES, make_atom_id,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

NEO4J_NODES_MASTER = "neo4j_nodes.csv"
NEO4J_EDGES_MASTER = "neo4j_edges.csv"

NODE_FIELDS = ["node_id", "label", "name", "type", "source_sha256", "meek_lane", "content_preview"]
EDGE_FIELDS = ["edge_id", "source_id", "target_id", "relationship", "weight", "source_sha256"]


def _load_existing_node_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            nid = row.get("node_id")
            if nid:
                ids.add(nid)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"[PHASE7A] Warning: {e}", file=sys.stderr)
    return ids


def _load_existing_edge_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    if not path.exists():
        return ids
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            eid = row.get("edge_id")
            if eid:
                ids.add(eid)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"[PHASE7A] Warning: {e}", file=sys.stderr)
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


def _edge_id(src: str, tgt: str, rel: str) -> str:
    raw = f"{src}|{tgt}|{rel}"
    return f"E-{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def run_graph_delta(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase7a"):
        print("[PHASE7A] Already complete, skipping", file=sys.stderr)
        return

    atoms = _load_atoms(cycle_dir)
    if not atoms:
        print("[PHASE7A] No atom stores found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase7a", {"status": "done", "nodes": 0, "edges": 0, "reason": "no_atoms"})
        return

    print(f"[PHASE7A] Loaded {len(atoms):,} atoms, generating graph delta...", file=sys.stderr)
    start = time.time()

    existing_nodes = _load_existing_node_ids(MASTER_ROOT / NEO4J_NODES_MASTER)
    existing_edges = _load_existing_edge_ids(MASTER_ROOT / NEO4J_EDGES_MASTER)

    new_nodes: list[dict] = []
    new_edges: list[dict] = []
    seen_node_ids: set[str] = set()
    seen_edge_ids: set[str] = set()

    for idx, atom in enumerate(atoms):
        text = atom.get("text", "") or atom.get("content", "") or ""
        sha = atom.get("source_sha256", "")
        atype = atom.get("atom_type", "")

        # Create evidence node for each atom
        node_id = make_atom_id("N", atype, atype, sha + text[:100])
        if node_id not in existing_nodes and node_id not in seen_node_ids:
            label = "Evidence" if atype == "fact" else (
                "Authority" if atype == "citation" else (
                "Person" if atype == "person" else (
                "Event" if atype == "event" else "Atom")))
            new_nodes.append({
                "node_id": node_id, "label": label,
                "name": atom.get("title", text[:80]),
                "type": atype, "source_sha256": sha,
                "meek_lane": atom.get("meek_lane", ""),
                "content_preview": text[:200],
            })
            seen_node_ids.add(node_id)

        # Citation edges: CITES relationship
        for pat, pat_name in [(MCL_PATTERN, "MCL"), (MCR_PATTERN, "MCR"),
                              (MRE_PATTERN, "MRE"), (CASE_CITE_PATTERN, "CASELAW")]:
            for match in pat.findall(text):
                cite_node_id = make_atom_id("N", "authority", pat_name, match)
                # Authority node
                if cite_node_id not in existing_nodes and cite_node_id not in seen_node_ids:
                    new_nodes.append({
                        "node_id": cite_node_id, "label": "Authority",
                        "name": match, "type": pat_name,
                        "source_sha256": sha, "meek_lane": "",
                        "content_preview": match,
                    })
                    seen_node_ids.add(cite_node_id)
                # CITES edge
                eid = _edge_id(node_id, cite_node_id, "CITES")
                if eid not in existing_edges and eid not in seen_edge_ids:
                    new_edges.append({
                        "edge_id": eid, "source_id": node_id,
                        "target_id": cite_node_id, "relationship": "CITES",
                        "weight": 1.0, "source_sha256": sha,
                    })
                    seen_edge_ids.add(eid)

        # Person edges: MENTIONS relationship
        for name, role in PERSON_NAMES.items():
            if name.lower() in text.lower():
                person_node_id = make_atom_id("N", "person", role, name)
                if person_node_id not in existing_nodes and person_node_id not in seen_node_ids:
                    new_nodes.append({
                        "node_id": person_node_id, "label": "Person",
                        "name": name, "type": role,
                        "source_sha256": "", "meek_lane": "",
                        "content_preview": f"{name} ({role})",
                    })
                    seen_node_ids.add(person_node_id)
                eid = _edge_id(node_id, person_node_id, "MENTIONS")
                if eid not in existing_edges and eid not in seen_edge_ids:
                    new_edges.append({
                        "edge_id": eid, "source_id": node_id,
                        "target_id": person_node_id, "relationship": "MENTIONS",
                        "weight": 1.0, "source_sha256": sha,
                    })
                    seen_edge_ids.add(eid)

        # Event atoms get DOCUMENTS edges to their source
        if atype == "event" and sha:
            src_node_id = make_atom_id("N", "source", "document", sha)
            if src_node_id not in existing_nodes and src_node_id not in seen_node_ids:
                new_nodes.append({
                    "node_id": src_node_id, "label": "Document",
                    "name": atom.get("source_path", sha[:16]),
                    "type": "source_document", "source_sha256": sha,
                    "meek_lane": "", "content_preview": "",
                })
                seen_node_ids.add(src_node_id)
            eid = _edge_id(node_id, src_node_id, "DOCUMENTS")
            if eid not in existing_edges and eid not in seen_edge_ids:
                new_edges.append({
                    "edge_id": eid, "source_id": node_id,
                    "target_id": src_node_id, "relationship": "DOCUMENTS",
                    "weight": 1.0, "source_sha256": sha,
                })
                seen_edge_ids.add(eid)

        # Fact atoms with contradiction signals get CONTRADICTS edges
        if atype == "fact" and atom.get("contradicts"):
            for contra_ref in atom["contradicts"]:
                contra_id = make_atom_id("N", "fact", "fact", contra_ref)
                eid = _edge_id(node_id, contra_id, "CONTRADICTS")
                if eid not in existing_edges and eid not in seen_edge_ids:
                    new_edges.append({
                        "edge_id": eid, "source_id": node_id,
                        "target_id": contra_id, "relationship": "CONTRADICTS",
                        "weight": 1.0, "source_sha256": sha,
                    })
                    seen_edge_ids.add(eid)

        if (idx + 1) % 5000 == 0:
            report_progress("phase7a", idx + 1, len(atoms))

    elapsed = time.time() - start
    print(f"[PHASE7A] Generated {len(new_nodes):,} nodes, {len(new_edges):,} edges in {elapsed:.0f}s", file=sys.stderr)

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        nodes_path = cycle_dir / "neo4j_nodes_delta.csv"
        with open(nodes_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=NODE_FIELDS)
            w.writeheader()
            w.writerows(new_nodes)

        edges_path = cycle_dir / "neo4j_edges_delta.csv"
        with open(edges_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=EDGE_FIELDS)
            w.writeheader()
            w.writerows(new_edges)

        stats = {
            "atoms_processed": len(atoms), "new_nodes": len(new_nodes),
            "new_edges": len(new_edges), "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "graph_delta_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase7a", {"status": "done", "nodes": len(new_nodes), "edges": len(new_edges), "elapsed": f"{elapsed:.0f}s"})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 7A: Graph Delta")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_graph_delta(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
