"""
OMEGA Phase 13: Document Refinement
Read top-scored documents from inventory.db and generate refined structured summaries.
"""
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

from config import (
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    PERSON_NAMES, VIOLATION_KEYWORDS,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done

DEFAULT_SCORE_THRESHOLD = 3.0

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

LEGAL_THEORY_KEYWORDS = [
    "due process", "equal protection", "best interest", "abuse of discretion",
    "contempt", "fraud upon the court", "parental alienation",
    "judicial misconduct", "constitutional violation", "habeas corpus",
    "res judicata", "collateral estoppel", "mandamus", "superintending control",
]


def _extract_citations(text: str) -> list[str]:
    cites: list[str] = []
    for pat in (MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN):
        cites.extend(m.strip() for m in pat.findall(text))
    return list(set(cites))


def _extract_persons(text: str) -> list[dict]:
    found: list[dict] = []
    text_lower = text.lower()
    for name, role in PERSON_NAMES.items():
        if name.lower() in text_lower:
            found.append({"name": name, "role": role})
    return found


def _extract_dates(text: str) -> list[str]:
    return list(set(m.strip() for m in DATE_PATTERN.findall(text)))


def _extract_key_facts(text: str) -> list[str]:
    facts: list[str] = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 30:
            continue
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in VIOLATION_KEYWORDS):
            facts.append(sent[:500])
        elif any(pat.search(sent) for pat in (MCL_PATTERN, MCR_PATTERN, CASE_CITE_PATTERN)):
            facts.append(sent[:500])
    return facts[:50]


def _extract_legal_theories(text: str) -> list[str]:
    text_lower = text.lower()
    return [t for t in LEGAL_THEORY_KEYWORDS if t in text_lower]


def _read_extract_text(cycle_dir: Path, file_path: str) -> str | None:
    """Try to find extracted text for a given inventory file."""
    fp = Path(file_path)
    stem = fp.stem
    for subdir in ("pdf", "docx", "structured"):
        txt = cycle_dir / "extracts" / subdir / f"{stem}.txt"
        if txt.exists():
            try:
                return txt.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    return None


def run_refinement(cycle_dir: Path, dry_run: bool = False,
                   score_threshold: float = DEFAULT_SCORE_THRESHOLD):
    if is_phase_done(cycle_dir, "phase13"):
        print("[PHASE13] Already complete, skipping", file=sys.stderr)
        return

    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE13] No inventory.db found, skipping", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase13", {
            "status": "done", "reason": "no_inventory_db", "refined": 0,
        })
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT file_path, file_name, extension, sha256, content_score, "
            "category, priority, meek_lanes, signal_summary "
            "FROM files WHERE content_score > ? AND is_legal_content = 1 "
            "ORDER BY content_score DESC",
            (score_threshold,),
        ).fetchall()
    except sqlite3.OperationalError as e:
        print(f"[PHASE13] DB query error: {e}", file=sys.stderr)
        conn.close()
        write_phase_checkpoint(cycle_dir, "phase13", {
            "status": "done", "reason": "db_error", "refined": 0,
        })
        return

    if not rows:
        print(f"[PHASE13] No docs with content_score > {score_threshold}", file=sys.stderr)
        conn.close()
        write_phase_checkpoint(cycle_dir, "phase13", {
            "status": "done", "reason": "no_qualifying_docs", "refined": 0,
        })
        return

    print(f"[PHASE13] Refining {len(rows):,} top-scored documents...", file=sys.stderr)
    start = time.time()
    refined: list[dict] = []

    for idx, row in enumerate(rows):
        file_path = row["file_path"]
        text = _read_extract_text(cycle_dir, file_path)
        if not text:
            continue

        doc = {
            "source_file": file_path,
            "file_name": row["file_name"],
            "sha256": row["sha256"],
            "content_score": row["content_score"],
            "category": row["category"],
            "priority": row["priority"],
            "meek_lanes": row["meek_lanes"],
            "key_facts": _extract_key_facts(text),
            "citations": _extract_citations(text),
            "persons": _extract_persons(text),
            "dates": _extract_dates(text),
            "legal_theories": _extract_legal_theories(text),
            "summary_len": len(text),
            "provenance": {
                "inventory_db": str(db_path),
                "extract_source": file_path,
                "cycle_dir": str(cycle_dir),
            },
        }
        refined.append(doc)

        if (idx + 1) % 500 == 0:
            report_progress("phase13", idx + 1, len(rows))

    elapsed = time.time() - start
    conn.close()

    print(f"[PHASE13] Refined {len(refined):,} documents in {elapsed:.0f}s", file=sys.stderr)

    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)
        with open(cycle_dir / "refined_docs.jsonl", "w", encoding="utf-8") as f:
            for doc in refined:
                f.write(json.dumps(doc) + "\n")

        stats = {
            "total_qualifying": len(rows),
            "refined": len(refined),
            "score_threshold": score_threshold,
            "elapsed_seconds": round(elapsed, 1),
        }
        (cycle_dir / "refinement_stats.json").write_text(
            json.dumps(stats, indent=2), encoding="utf-8",
        )
        write_phase_checkpoint(cycle_dir, "phase13", {
            "status": "done", "refined": len(refined), "elapsed": f"{elapsed:.0f}s",
        })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 13: Document Refinement")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--score-threshold", type=float, default=DEFAULT_SCORE_THRESHOLD)
    args = parser.parse_args()
    from config import CYCLE_TS
    run_refinement(
        get_cyclepack_dir(args.cycle_ts or CYCLE_TS),
        args.dry_run,
        args.score_threshold,
    )
