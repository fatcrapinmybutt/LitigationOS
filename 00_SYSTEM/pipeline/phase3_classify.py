"""
OMEGA Phase 3: 3-Pass Classification Engine
Tags every canonical file with category, priority, MEEK lane, and content score.
"""
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

from config import (
    LEGAL_EXTENSIONS, HIGH_PRIORITY_PATTERNS, MCL_PATTERN, MCR_PATTERN,
    MRE_PATTERN, CASE_CITE_PATTERN, USC_PATTERN, CANON_PATTERN,
    VIOLATION_KEYWORDS, PERSON_NAMES, MEEK_SIGNALS,
    get_cyclepack_dir, report_progress,
)
from safety import write_phase_checkpoint, is_phase_done


# ── Pass 1: Extension + Path Pattern ────────────────────────────────
CATEGORY_MAP = {
    ".pdf": "LEGAL_DOC", ".docx": "LEGAL_DOC", ".doc": "LEGAL_DOC", ".rtf": "LEGAL_DOC",
    ".md": "LEGAL_TEXT", ".txt": "LEGAL_TEXT",
    ".json": "STRUCTURED_DATA", ".jsonl": "STRUCTURED_DATA", ".csv": "STRUCTURED_DATA",
    ".graphml": "GRAPH_DATA", ".cypher": "GRAPH_DATA",
    ".png": "EVIDENCE_IMAGE", ".jpg": "EVIDENCE_IMAGE", ".jpeg": "EVIDENCE_IMAGE",
    ".tiff": "EVIDENCE_IMAGE", ".tif": "EVIDENCE_IMAGE", ".bmp": "EVIDENCE_IMAGE",
    ".zip": "ARCHIVE", ".rar": "ARCHIVE", ".7z": "ARCHIVE",
    ".py": "SCRIPT", ".ps1": "SCRIPT", ".bat": "SCRIPT", ".sh": "SCRIPT",
    ".html": "WEB_DOC", ".htm": "WEB_DOC",
}

SKIP_CATEGORY_EXT = {".pyc", ".class", ".dll", ".exe", ".so", ".o", ".obj", ".h", ".c", ".cpp"}


def classify_pass1(ext: str, file_path: str) -> tuple[str, str]:
    """Returns (category, priority)."""
    if ext in SKIP_CATEGORY_EXT:
        return "IRRELEVANT", "SKIP"
    
    cat = CATEGORY_MAP.get(ext, "OTHER")
    lp = file_path.lower()
    
    # Check high-priority path patterns
    for pat in HIGH_PRIORITY_PATTERNS:
        if pat.search(lp):
            return cat, "HIGH"
    
    if cat in ("LEGAL_DOC", "LEGAL_TEXT", "STRUCTURED_DATA", "GRAPH_DATA"):
        return cat, "HIGH"
    elif cat in ("EVIDENCE_IMAGE", "ARCHIVE"):
        return cat, "MEDIUM"
    elif cat == "SCRIPT":
        return cat, "LOW"
    else:
        return cat, "LOW"


def classify_pass2(text: str) -> tuple[float, dict]:
    """Content signal scoring. Returns (score, signals_dict)."""
    mcl_hits = len(MCL_PATTERN.findall(text))
    mcr_hits = len(MCR_PATTERN.findall(text))
    mre_hits = len(MRE_PATTERN.findall(text))
    case_hits = len(CASE_CITE_PATTERN.findall(text))
    usc_hits = len(USC_PATTERN.findall(text))
    canon_hits = len(CANON_PATTERN.findall(text))
    
    citations = mcl_hits + mcr_hits + mre_hits + case_hits + usc_hits + canon_hits
    
    kw_count = sum(1 for kw in VIOLATION_KEYWORDS if kw.lower() in text.lower())
    
    persons_found = []
    for name in PERSON_NAMES:
        if name.lower() in text.lower():
            persons_found.append(name)
    
    # Date pattern
    date_hits = len(re.findall(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", text))
    dollar_hits = len(re.findall(r"\$[\d,]+\.?\d*", text))
    
    length_factor = min(len(text) / 5000, 3.0)
    score = (citations * 3.0 + kw_count * 1.5 + dollar_hits + date_hits) * max(length_factor, 0.1)
    
    signals = {
        "mcl": mcl_hits, "mcr": mcr_hits, "mre": mre_hits,
        "case_cites": case_hits, "usc": usc_hits, "canons": canon_hits,
        "keywords": kw_count, "persons": persons_found,
        "dates": date_hits, "dollars": dollar_hits,
    }
    return score, signals


def classify_pass3(text: str) -> list[str]:
    """MEEK lane assignment."""
    lanes = []
    for lane, pattern in MEEK_SIGNALS.items():
        if pattern.search(text):
            lanes.append(lane)
    return lanes


def run_classify(cycle_dir: Path, dry_run: bool = False):
    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE3] inventory.db not found", file=sys.stderr)
        if dry_run:
            print("[PHASE3] DRY RUN: would classify files from inventory.db", file=sys.stderr)
            return
        sys.exit(1)

    if is_phase_done(cycle_dir, "phase3"):
        print("[PHASE3] Already complete, skipping", file=sys.stderr)
        return

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        start = time.time()

        # Pass 1: Extension + path for ALL canonical files
        print("[PHASE3] Pass 1: Extension + path classification...", file=sys.stderr)
        rows = conn.execute("SELECT id, file_path, extension FROM files WHERE is_canonical = 1").fetchall()
        total = len(rows)

        for i, (fid, fpath, ext) in enumerate(rows):
            ext = ext or ""
            cat, pri = classify_pass1(ext, fpath)
            if not dry_run:
                conn.execute("UPDATE files SET category = ?, priority = ? WHERE id = ?", (cat, pri, fid))
            if (i + 1) % 50000 == 0:
                conn.commit()
                report_progress("phase3-p1", i + 1, total)

        conn.commit()
        print(f"[PHASE3] Pass 1 done: {total:,} files classified", file=sys.stderr)

        # Pass 2 + 3: Content signals for readable text files
        print("[PHASE3] Pass 2+3: Content scoring + MEEK lanes...", file=sys.stderr)
        text_rows = conn.execute("""
            SELECT id, file_path, extension FROM files
            WHERE is_canonical = 1 AND priority != 'SKIP'
            AND extension IN ('.txt', '.md', '.json', '.jsonl', '.csv', '.html', '.htm')
            AND size_bytes < 10000000
        """).fetchall()

        scored = 0
        for i, (fid, fpath, ext) in enumerate(text_rows):
            try:
                text = Path(fpath).read_text(encoding="utf-8", errors="replace")[:100000]
                score, signals = classify_pass2(text)
                lanes = classify_pass3(text)

                if not dry_run:
                    conn.execute("""
                        UPDATE files SET content_score = ?, meek_lanes = ?, signal_summary = ?
                        WHERE id = ?
                    """, (score, ",".join(lanes) if lanes else None, json.dumps(signals), fid))

                    # Upgrade priority if high score
                    if score > 10.0:
                        conn.execute("UPDATE files SET priority = 'HIGH' WHERE id = ? AND priority != 'HIGH'", (fid,))

                scored += 1
            except (PermissionError, OSError, UnicodeDecodeError):
                pass

            if (i + 1) % 10000 == 0:
                conn.commit()
                report_progress("phase3-p2", i + 1, len(text_rows))

        conn.commit()
        elapsed = time.time() - start

        # Stats
        stats = {}
        for row in conn.execute("SELECT priority, COUNT(*) FROM files WHERE is_canonical=1 GROUP BY priority"):
            stats[row[0] or "NULL"] = row[1]

        lane_stats = {}
        for row in conn.execute("SELECT meek_lanes, COUNT(*) FROM files WHERE meek_lanes IS NOT NULL GROUP BY meek_lanes"):
            lane_stats[row[0]] = row[1]

        print(f"\n[PHASE3] Classification complete:", file=sys.stderr)
        print(f"  Priority: {stats}", file=sys.stderr)
        print(f"  MEEK lanes: {lane_stats}", file=sys.stderr)
        print(f"  Content scored: {scored:,}", file=sys.stderr)
        print(f"  Elapsed: {elapsed:.0f}s", file=sys.stderr)

        if not dry_run:
            all_stats = {"priority_counts": stats, "lane_counts": lane_stats, "content_scored": scored, "elapsed_seconds": round(elapsed, 1)}
            (cycle_dir / "classify_stats.json").write_text(json.dumps(all_stats, indent=2), encoding="utf-8")
            write_phase_checkpoint(cycle_dir, "phase3", {"status": "done", "scored": scored, "elapsed": f"{elapsed:.0f}s"})
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 3: Classify")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_classify(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
