"""
OMEGA Phase 4D: BRAIN_SPEC Atom Generation
Read all extracted text, generate fact/citation/event/person/contradiction atom stores.
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    get_cyclepack_dir, report_progress, make_atom_id,
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    USC_PATTERN, CANON_PATTERN, VIOLATION_KEYWORDS, POSTURE_TAGS,
    PERSON_NAMES, MEEK_SIGNALS,
)
from safety import write_phase_checkpoint, is_phase_done

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

EVENT_KEYWORDS = re.compile(
    r"(?i)(filed|hearing|order|ruling|motion|served|deposition|trial|arraignment|sentenced|dismissed|granted|denied)",
)

BRAIN_ID = "OMEGA_DEEP"


def _collect_extracts(cycle_dir: Path) -> list[tuple[str, str]]:
    """Collect all .txt files from extracts/pdf, extracts/docx, extracts/structured."""
    results: list[tuple[str, str]] = []
    for subdir in ("pdf", "docx", "structured"):
        ext_dir = cycle_dir / "extracts" / subdir
        if not ext_dir.exists():
            continue
        for txt_file in ext_dir.glob("*.txt"):
            try:
                text = txt_file.read_text(encoding="utf-8", errors="replace")
                results.append((txt_file.stem, text))
            except (OSError, PermissionError):
                continue
    return results


def _generate_fact_atoms(source: str, text: str) -> list[dict]:
    atoms: list[dict] = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 30:
            continue

        # Detect posture
        posture = "ALLEGATION"
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in ("affidavit", "sworn", "under oath", "testimony")):
            posture = "SWORN_FACT"
        elif any(kw in sent_lower for kw in ("court record", "docket", "filed", "entered")):
            posture = "RECORD_FACT"
        elif any(kw in sent_lower for kw in ("exhibit", "evidence", "document shows")):
            posture = "EVIDENCE_FACT"
        elif any(kw in sent_lower for kw in ("appears", "suggests", "likely", "inference")):
            posture = "INFERENCE"

        # Check violation keywords for relevance
        has_violation = any(kw in sent_lower for kw in VIOLATION_KEYWORDS)

        # Detect MEEK lane
        meek_lanes: list[str] = []
        for lane, pat in MEEK_SIGNALS.items():
            if pat.search(sent):
                meek_lanes.append(lane)

        atom_id = make_atom_id("FACT", BRAIN_ID, "fact", f"{source}|{sent[:80]}")
        atoms.append({
            "atom_id": atom_id,
            "type": "fact",
            "source": source,
            "text": sent[:500],
            "posture": posture,
            "has_violation": has_violation,
            "meek_lanes": meek_lanes,
            "ts": datetime.now().isoformat(),
        })
    return atoms


def _generate_citation_atoms(source: str, text: str) -> list[dict]:
    atoms: list[dict] = []
    patterns = {
        "MCL": MCL_PATTERN,
        "MCR": MCR_PATTERN,
        "MRE": MRE_PATTERN,
        "CASE": CASE_CITE_PATTERN,
        "USC": USC_PATTERN,
        "CANON": CANON_PATTERN,
    }
    for cite_type, pat in patterns.items():
        for m in pat.finditer(text):
            cite_text = m.group().strip()
            atom_id = make_atom_id("CITE", BRAIN_ID, "citation", f"{cite_type}|{cite_text}")
            # Get surrounding context (100 chars each side)
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ").strip()

            atoms.append({
                "atom_id": atom_id,
                "type": "citation",
                "cite_type": cite_type,
                "cite_text": cite_text,
                "source": source,
                "context": context[:300],
                "ts": datetime.now().isoformat(),
            })
    return atoms


def _generate_event_atoms(source: str, text: str) -> list[dict]:
    atoms: list[dict] = []
    for m in DATE_PATTERN.finditer(text):
        date_str = m.group().strip()
        # Get surrounding context for event type detection
        start = max(0, m.start() - 80)
        end = min(len(text), m.end() + 80)
        context = text[start:end].replace("\n", " ").strip()

        event_type = "UNKNOWN"
        ev_match = EVENT_KEYWORDS.search(context)
        if ev_match:
            event_type = ev_match.group(1).upper()

        atom_id = make_atom_id("EVT", BRAIN_ID, "event", f"{date_str}|{event_type}|{source}")
        atoms.append({
            "atom_id": atom_id,
            "type": "event",
            "date_raw": date_str,
            "event_type": event_type,
            "source": source,
            "context": context[:300],
            "ts": datetime.now().isoformat(),
        })
    return atoms


def _generate_person_atoms(source: str, text: str) -> list[dict]:
    atoms: list[dict] = []
    for name, role in PERSON_NAMES.items():
        # Case-insensitive search
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        for m in pattern.finditer(text):
            start = max(0, m.start() - 100)
            end = min(len(text), m.end() + 100)
            context = text[start:end].replace("\n", " ").strip()

            atom_id = make_atom_id("PER", BRAIN_ID, "person", f"{name}|{source}|{context[:40]}")
            atoms.append({
                "atom_id": atom_id,
                "type": "person",
                "name": name,
                "role": role,
                "source": source,
                "context": context[:300],
                "ts": datetime.now().isoformat(),
            })
    return atoms


def run_atomize(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase4d"):
        print("[PHASE4D] Already complete, skipping", file=sys.stderr)
        return

    extracts = _collect_extracts(cycle_dir)
    if not extracts:
        print("[PHASE4D] No extracted text found in extracts/", file=sys.stderr)
        return

    print(f"[PHASE4D] Processing {len(extracts):,} extracted documents...", file=sys.stderr)

    start = time.time()
    all_facts: dict[str, dict] = {}
    all_citations: dict[str, dict] = {}
    all_events: dict[str, dict] = {}
    all_persons: dict[str, dict] = {}

    for i, (source, text) in enumerate(extracts):
        if dry_run:
            continue

        for atom in _generate_fact_atoms(source, text):
            all_facts.setdefault(atom["atom_id"], atom)

        for atom in _generate_citation_atoms(source, text):
            all_citations.setdefault(atom["atom_id"], atom)

        for atom in _generate_event_atoms(source, text):
            all_events.setdefault(atom["atom_id"], atom)

        for atom in _generate_person_atoms(source, text):
            all_persons.setdefault(atom["atom_id"], atom)

        if (i + 1) % 100 == 0:
            report_progress("phase4d", i + 1, len(extracts))

    elapsed = time.time() - start

    if not dry_run:
        # Write atom stores
        stores = {
            "fact_atoms.jsonl": list(all_facts.values()),
            "citation_atoms.jsonl": list(all_citations.values()),
            "event_atoms.jsonl": list(all_events.values()),
            "person_atoms.jsonl": list(all_persons.values()),
            "contradiction_atoms.jsonl": [],  # Placeholder for Phase 8
        }

        for filename, atoms in stores.items():
            out_path = cycle_dir / filename
            with open(out_path, "w", encoding="utf-8") as fh:
                for atom in atoms:
                    fh.write(json.dumps(atom) + "\n")

        stats = {
            "sources_processed": len(extracts),
            "fact_atoms": len(all_facts),
            "citation_atoms": len(all_citations),
            "event_atoms": len(all_events),
            "person_atoms": len(all_persons),
            "contradiction_atoms": 0,
            "elapsed": round(elapsed, 1),
        }
        (cycle_dir / "atomize_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase4d", {"status": "done", **stats})

    print(
        f"[PHASE4D] Done: {len(all_facts):,} facts, {len(all_citations):,} citations, "
        f"{len(all_events):,} events, {len(all_persons):,} persons in {elapsed:.0f}s",
        file=sys.stderr,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4D: BRAIN_SPEC Atom Generation")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_atomize(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
