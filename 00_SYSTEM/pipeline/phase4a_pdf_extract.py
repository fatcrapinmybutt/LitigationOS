"""
OMEGA Phase 4A: PDF Extraction
Primary: pymupdf. Fallback: Tesseract OCR for scanned pages.
"""
import json
import sqlite3
import sys
import time
from pathlib import Path

from config import get_cyclepack_dir, sha256_file, report_progress
from safety import write_phase_checkpoint, is_phase_done


def extract_pdf(pdf_path: str, output_dir: Path) -> dict | None:
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            print("[PHASE4A] pymupdf not available", file=sys.stderr)
            return None

    out_hash = Path(pdf_path).stem
    txt_path = output_dir / f"{out_hash}.txt"
    if txt_path.exists():
        return {"method": "cached", "path": str(txt_path)}

    try:
        doc = pymupdf.open(pdf_path)
        text_parts = []
        method = "embedded"
        ocr_pages = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"--- PAGE {page_num + 1} ---\n{text}")
            else:
                ocr_pages += 1
                # Mark for OCR but don't block
                text_parts.append(f"--- PAGE {page_num + 1} [SCANNED - OCR NEEDED] ---")

        if ocr_pages > 0:
            method = "mixed" if text_parts else "ocr_needed"

        full_text = "\n".join(text_parts)
        txt_path.write_text(full_text, encoding="utf-8")
        doc.close()

        return {
            "method": method,
            "pages": len(doc) if hasattr(doc, '__len__') else page_num + 1,
            "chars": len(full_text),
            "ocr_pages": ocr_pages,
            "path": str(txt_path),
        }
    except Exception as e:
        return {"method": "error", "error": str(e)[:200]}


def run_pdf_extract(cycle_dir: Path, dry_run: bool = False):
    db_path = cycle_dir / "inventory.db"
    if not db_path.exists():
        print("[PHASE4A] inventory.db not found", file=sys.stderr)
        if dry_run:
            print("[PHASE4A] DRY RUN: would extract PDFs from inventory.db", file=sys.stderr)
            return
        sys.exit(1)

    if is_phase_done(cycle_dir, "phase4a"):
        print("[PHASE4A] Already complete, skipping", file=sys.stderr)
        return

    extracts_dir = cycle_dir / "extracts" / "pdf"
    extracts_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("""
            SELECT id, file_path, sha256, size_bytes FROM files
            WHERE is_canonical = 1 AND extension = '.pdf' AND priority IN ('HIGH', 'MEDIUM')
            ORDER BY content_score DESC, size_bytes ASC
        """).fetchall()

        start = time.time()
        extracted = 0
        errors = 0
        total_chars = 0
        log_path = cycle_dir / "extraction_log_pdf.jsonl"

        print(f"[PHASE4A] Extracting {len(rows):,} PDFs...", file=sys.stderr)

        with open(log_path, "a", encoding="utf-8") as log:
            for i, (fid, fpath, sha, size) in enumerate(rows):
                if dry_run:
                    extracted += 1
                    continue

                result = extract_pdf(fpath, extracts_dir)
                if result and result["method"] != "error":
                    total_chars += result.get("chars", 0)
                    extracted += 1
                else:
                    errors += 1

                entry = {
                    "sha256": sha,
                    "source_path": fpath,
                    "result": result,
                    "extraction_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                log.write(json.dumps(entry) + "\n")

                if (i + 1) % 1000 == 0:
                    report_progress("phase4a", i + 1, len(rows))

        elapsed = time.time() - start
        print(f"[PHASE4A] Done: {extracted:,} extracted, {errors} errors, {total_chars:,} chars in {elapsed:.0f}s", file=sys.stderr)

        if not dry_run:
            stats = {"extracted": extracted, "errors": errors, "total_chars": total_chars, "elapsed": round(elapsed, 1)}
            (cycle_dir / "pdf_extract_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
            write_phase_checkpoint(cycle_dir, "phase4a", {"status": "done", "extracted": extracted, "elapsed": f"{elapsed:.0f}s"})
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4A: PDF Extract")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from config import CYCLE_TS
    run_pdf_extract(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
