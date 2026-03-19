"""
OMEGA Phase 4C: Structured Data Extraction
Parse JSON/JSONL for embedded legal text; CSV for authority refs, timeline data, persons.
"""
import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

from config import (
    get_cyclepack_dir, long_path, report_progress,
    MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN,
    USC_PATTERN, PERSON_NAMES,
)
from safety import write_phase_checkpoint, is_phase_done


def _extract_text_from_dict(obj: dict, depth: int = 0) -> list[str]:
    """Recursively pull string values that look like legal content."""
    if depth > 10:
        return []
    parts: list[str] = []
    for key, val in obj.items():
        if isinstance(val, str) and len(val) > 20:
            parts.append(val)
        elif isinstance(val, dict):
            parts.extend(_extract_text_from_dict(val, depth + 1))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str) and len(item) > 20:
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.extend(_extract_text_from_dict(item, depth + 1))
    return parts


def extract_json(file_path: str, output_dir: Path) -> dict | None:
    out_name = Path(file_path).stem
    txt_path = output_dir / f"{out_name}.txt"
    if txt_path.exists():
        return {"method": "cached", "path": str(txt_path)}

    try:
        raw = Path(long_path(file_path)).read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        parts: list[str] = []
        if isinstance(data, dict):
            parts = _extract_text_from_dict(data)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    parts.extend(_extract_text_from_dict(item))
                elif isinstance(item, str) and len(item) > 20:
                    parts.append(item)

        full_text = "\n".join(parts)
        if not full_text.strip():
            return {"method": "empty", "chars": 0}

        txt_path.write_text(full_text, encoding="utf-8")
        return {"method": "json", "entries": len(parts), "chars": len(full_text), "path": str(txt_path)}
    except Exception as e:
        return {"method": "error", "error": str(e)[:200]}


def extract_jsonl(file_path: str, output_dir: Path) -> dict | None:
    out_name = Path(file_path).stem
    txt_path = output_dir / f"{out_name}.txt"
    if txt_path.exists():
        return {"method": "cached", "path": str(txt_path)}

    try:
        parts: list[str] = []
        with open(long_path(file_path), "r", encoding="utf-8", errors="replace") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        parts.extend(_extract_text_from_dict(obj))
                except json.JSONDecodeError:
                    continue

        full_text = "\n".join(parts)
        if not full_text.strip():
            return {"method": "empty", "chars": 0}

        txt_path.write_text(full_text, encoding="utf-8")
        return {"method": "jsonl", "entries": len(parts), "chars": len(full_text), "path": str(txt_path)}
    except Exception as e:
        return {"method": "error", "error": str(e)[:200]}


def extract_csv(file_path: str, output_dir: Path) -> dict | None:
    out_name = Path(file_path).stem
    txt_path = output_dir / f"{out_name}.txt"
    if txt_path.exists():
        return {"method": "cached", "path": str(txt_path)}

    try:
        parts: list[str] = []
        authority_refs: list[str] = []
        dates_found: list[str] = []
        persons_found: list[str] = []

        with open(long_path(file_path), "r", encoding="utf-8", errors="replace", newline="") as fh:
            try:
                dialect = csv.Sniffer().sniff(fh.read(4096))
                fh.seek(0)
            except csv.Error:
                fh.seek(0)
                dialect = csv.excel

            reader = csv.reader(fh, dialect)
            for row_idx, row in enumerate(reader):
                row_text = " | ".join(cell.strip() for cell in row if cell.strip())
                if not row_text:
                    continue
                parts.append(row_text)

                # Authority references
                for pat in (MCL_PATTERN, MCR_PATTERN, MRE_PATTERN, CASE_CITE_PATTERN, USC_PATTERN):
                    for m in pat.finditer(row_text):
                        authority_refs.append(m.group())

                # Person mentions
                for name in PERSON_NAMES:
                    if name.lower() in row_text.lower():
                        persons_found.append(name)

        full_text = "\n".join(parts)
        if not full_text.strip():
            return {"method": "empty", "chars": 0}

        # Append extracted metadata as footer
        meta_lines: list[str] = []
        if authority_refs:
            meta_lines.append(f"\n--- AUTHORITY REFERENCES ({len(authority_refs)}) ---")
            for ref in sorted(set(authority_refs)):
                meta_lines.append(ref)
        if persons_found:
            meta_lines.append(f"\n--- PERSON MENTIONS ({len(set(persons_found))}) ---")
            for p in sorted(set(persons_found)):
                meta_lines.append(f"{p}: {PERSON_NAMES.get(p, 'UNKNOWN')}")

        full_text += "\n".join(meta_lines)
        txt_path.write_text(full_text, encoding="utf-8")

        return {
            "method": "csv",
            "rows": len(parts),
            "chars": len(full_text),
            "authority_refs": len(set(authority_refs)),
            "persons": len(set(persons_found)),
            "path": str(txt_path),
        }
    except Exception as e:
        return {"method": "error", "error": str(e)[:200]}


def run_structured_extract(cycle_dir: Path, dry_run: bool = False):
    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE4C] inventory.db not found", file=sys.stderr)
        sys.exit(1)

    if is_phase_done(cycle_dir, "phase4c"):
        print("[PHASE4C] Already complete, skipping", file=sys.stderr)
        return

    extracts_dir = cycle_dir / "extracts" / "structured"
    extracts_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("""
        SELECT id, file_path, sha256, size_bytes, extension FROM files
        WHERE is_canonical = 1 AND extension IN ('.json', '.jsonl', '.csv')
              AND priority = 'HIGH'
        ORDER BY content_score DESC, size_bytes ASC
    """).fetchall()

    start = time.time()
    extracted = 0
    errors = 0
    total_chars = 0
    log_path = cycle_dir / "extraction_log_structured.jsonl"

    print(f"[PHASE4C] Extracting {len(rows):,} structured files...", file=sys.stderr)

    extractors = {
        ".json": extract_json,
        ".jsonl": extract_jsonl,
        ".csv": extract_csv,
    }

    with open(log_path, "a", encoding="utf-8") as log:
        for i, (fid, fpath, sha, size, ext) in enumerate(rows):
            if dry_run:
                extracted += 1
                continue

            fn = extractors.get(ext)
            if fn is None:
                continue

            result = fn(fpath, extracts_dir)
            if result and result["method"] not in ("error", "empty"):
                total_chars += result.get("chars", 0)
                extracted += 1
            elif result and result["method"] == "error":
                errors += 1

            entry = {
                "sha256": sha,
                "source_path": fpath,
                "extension": ext,
                "result": result,
                "extraction_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            log.write(json.dumps(entry) + "\n")

            if (i + 1) % 1000 == 0:
                report_progress("phase4c", i + 1, len(rows))

    elapsed = time.time() - start
    print(f"[PHASE4C] Done: {extracted:,} extracted, {errors} errors, {total_chars:,} chars in {elapsed:.0f}s", file=sys.stderr)

    if not dry_run:
        stats = {"extracted": extracted, "errors": errors, "total_chars": total_chars, "elapsed": round(elapsed, 1)}
        (cycle_dir / "structured_extract_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        write_phase_checkpoint(cycle_dir, "phase4c", {"status": "done", "extracted": extracted, "elapsed": f"{elapsed:.0f}s"})

    conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4C: Structured Data Extract")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_structured_extract(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
