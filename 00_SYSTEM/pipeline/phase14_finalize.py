"""
OMEGA Phase 14: Filing Finalization
Cross-reference existing filings against new evidence atoms to identify
enhancements, new filings, and citation updates.
"""
import json
import re
import sys
import time
from pathlib import Path

from config import (
    MASTER_ROOT, MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    VIOLATION_KEYWORDS, PERSON_NAMES,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

COURT_FILINGS_DIR = MASTER_ROOT / "COURT_FILINGS_FINAL"
FILING_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".rtf"}


def _load_filing_index(filings_dir: Path) -> list[dict]:
    """Index existing filings by name and extracted text."""
    filings: list[dict] = []
    if not filings_dir.exists():
        return filings
    for fp in filings_dir.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in FILING_EXTENSIONS:
            text = ""
            if fp.suffix.lower() in (".txt", ".md"):
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
            filings.append({
                "path": str(fp),
                "name": fp.name,
                "stem": fp.stem,
                "suffix": fp.suffix.lower(),
                "size": fp.stat().st_size if fp.exists() else 0,
                "text": text,
            })
    return filings


def _extract_citations_from_text(text: str) -> list[str]:
    cites: list[str] = []
    for pat in (MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN):
        cites.extend(m.strip() for m in pat.findall(text))
    return list(set(cites))


def _load_atoms(cycle_dir: Path) -> list[dict]:
    atoms: list[dict] = []
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


_SEVERITY_WEIGHTS = {
    "SWORN_FACT": 3.0,
    "RECORD_FACT": 2.5,
    "EVIDENCE_FACT": 2.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}


def _match_atoms_to_filing(filing: dict, atoms: list[dict]) -> list[dict]:
    """Find atoms relevant to a filing based on keyword, citation, and severity overlap."""
    filing_text = (filing.get("text", "") + " " + filing.get("name", "")).lower()
    filing_citations = set(_extract_citations_from_text(filing.get("text", "") + " " + filing.get("name", "")))

    matched: list[dict] = []
    for atom in atoms:
        atom_text = (atom.get("text", "") or atom.get("content", "") or atom.get("context", "")).lower()
        if not atom_text:
            continue

        # Keyword overlap
        shared_kw = [kw for kw in VIOLATION_KEYWORDS if kw in filing_text and kw in atom_text]
        shared_persons = [n for n in PERSON_NAMES if n.lower() in filing_text and n.lower() in atom_text]
        has_keyword = bool(shared_kw or shared_persons)

        # Citation overlap — match atoms that cite the same statutes as the filing
        atom_raw = atom.get("text", "") or atom.get("content", "") or atom.get("context", "")
        atom_citations = set(_extract_citations_from_text(atom_raw))
        shared_cites = sorted(filing_citations & atom_citations)
        has_citation = bool(shared_cites)

        if not has_keyword and not has_citation:
            continue

        # Determine match strength
        if has_citation and has_keyword:
            match_strength = "strong"
        elif has_citation or has_keyword:
            match_strength = "moderate" if has_citation else "weak"
        else:
            match_strength = "weak"

        # Severity-weighted score
        atom_type = atom.get("type", atom.get("atom_type", ""))
        base_weight = _SEVERITY_WEIGHTS.get(atom_type, 1.0)
        score = base_weight * (len(shared_kw) + len(shared_persons) + 2 * len(shared_cites))

        matched.append({
            "atom_id": atom.get("atom_id", ""),
            "atom_type": atom_type,
            "shared_keywords": shared_kw,
            "shared_persons": shared_persons,
            "shared_citations": shared_cites,
            "match_strength": match_strength,
            "weighted_score": round(score, 2),
            "snippet": atom_text[:200],
        })

    # Sort by weighted score descending, return top 20
    matched.sort(key=lambda m: m["weighted_score"], reverse=True)
    return matched[:20]


def _identify_new_filing_opportunities(atoms: list[dict], existing_names: set[str]) -> list[dict]:
    """Detect clusters of violation atoms that suggest new filings."""
    recs: list[dict] = []
    violation_clusters: dict[str, list[dict]] = {}
    for atom in atoms:
        text = (atom.get("text", "") or atom.get("content", "")).lower()
        for kw in VIOLATION_KEYWORDS:
            if kw in text:
                violation_clusters.setdefault(kw, []).append(atom)

    for kw, cluster in violation_clusters.items():
        if len(cluster) >= 3:
            # Check if existing filing already covers this
            covered = any(kw in name.lower() for name in existing_names)
            if not covered:
                recs.append({
                    "violation_type": kw,
                    "supporting_atoms": len(cluster),
                    "sample_atom_ids": [a.get("atom_id", "") for a in cluster[:5]],
                    "recommendation": f"New filing recommended: {kw.title()} motion/complaint",
                })
    return recs


def run_finalize(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase14"):
        print("[PHASE14] Already complete, skipping", file=sys.stderr)
        return

    print(f"[PHASE14] Loading filings from {COURT_FILINGS_DIR}...", file=sys.stderr)
    start = time.time()

    filings = _load_filing_index(COURT_FILINGS_DIR)
    atoms = _load_atoms(cycle_dir)

    if not filings:
        print("[PHASE14] No existing filings found", file=sys.stderr)
    if not atoms:
        print("[PHASE14] No atom stores found", file=sys.stderr)

    if not filings and not atoms:
        write_phase_checkpoint(cycle_dir, "phase14", {
            "status": "done", "reason": "no_filings_or_atoms",
        })
        return

    # Cross-reference filings against atoms
    enhancements: list[dict] = []
    citation_updates: list[dict] = []

    for idx, filing in enumerate(filings):
        matches = _match_atoms_to_filing(filing, atoms)
        if matches:
            enhancements.append({
                "filing_path": filing["path"],
                "filing_name": filing["name"],
                "new_evidence_count": len(matches),
                "matched_atoms": matches[:20],
            })

        # Check citation freshness
        if filing.get("text"):
            filing_cites = _extract_citations_from_text(filing["text"])
            atom_cites = set()
            for atom in atoms:
                if atom.get("cite_type") in ("MCL", "MCR", "MRE", "CASE"):
                    atom_cites.add(atom.get("cite_text", "").strip())
            new_cites = [c for c in atom_cites if c and c not in filing_cites]
            if new_cites:
                citation_updates.append({
                    "filing_path": filing["path"],
                    "filing_name": filing["name"],
                    "existing_citations": len(filing_cites),
                    "new_citations_available": new_cites[:20],
                })

        if (idx + 1) % 50 == 0:
            report_progress("phase14", idx + 1, len(filings))

    # Identify new filing opportunities
    existing_names = {f["name"] for f in filings}
    new_recs = _identify_new_filing_opportunities(atoms, existing_names)

    elapsed = time.time() - start
    print(
        f"[PHASE14] Done: {len(enhancements)} enhanceable, "
        f"{len(new_recs)} new recommendations, "
        f"{len(citation_updates)} citation updates in {elapsed:.0f}s",
        file=sys.stderr,
    )

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        report = {
            "filings_scanned": len(filings),
            "atoms_available": len(atoms),
            "filings_enhanceable": len(enhancements),
            "new_filing_recommendations": len(new_recs),
            "citation_updates_needed": len(citation_updates),
            "elapsed_seconds": round(elapsed, 1),
            "enhancements": enhancements,
            "citation_updates": citation_updates,
        }
        (cycle_dir / "filing_enhancement_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8",
        )

        with open(cycle_dir / "new_filing_recommendations.jsonl", "w", encoding="utf-8") as f:
            for rec in new_recs:
                f.write(json.dumps(rec) + "\n")

        write_phase_checkpoint(cycle_dir, "phase14", {
            "status": "done", "enhanced": len(enhancements),
            "new_recs": len(new_recs), "elapsed": f"{elapsed:.0f}s",
        })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 14: Filing Finalization")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_finalize(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
