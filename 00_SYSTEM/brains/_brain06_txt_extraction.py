"""
BRAIN-06: Extract high-confidence legal TXT files into Multi-Brain Universe databases.

Queues TXT files from 4 directories with skip-pattern filtering,
then processes up to 500 items in a single batch.

MUST be run with CWD set to the brains directory (shadow-module safety).
"""
import sys
import os
import re
import time
from datetime import datetime

try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
except (OSError, AttributeError):
    pass  # Handle redirected/piped stdout gracefully

BRAIN_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BRAIN_DIR)

if BRAIN_DIR not in sys.path:
    sys.path.insert(0, BRAIN_DIR)

from extraction_engine import ExtractionEngine, SUPPORTED_EXTENSIONS

# ── Configuration ──
SCAN_DIRS = [
    (r"C:\Users\andre\LitigationOS\08_TEXT\general", 2, "PRIMARY LITIGATION CONTENT"),
    (r"C:\Users\andre\LitigationOS\08_TEXT\analysis", 2, "Analysis reports"),
    (r"C:\Users\andre\LitigationOS\texts", 1, "Case documentation"),
    (r"C:\Users\andre\LitigationOS\Legal_Transcripts", 1, "Hearing transcripts"),
]

SKIP_PATTERNS = [
    re.compile(r'^__mount', re.IGNORECASE),
    re.compile(r'^__not_in_default_pythonpath', re.IGNORECASE),
    re.compile(r'_batch_execution_log', re.IGNORECASE),
]

PROCESS_LIMIT = 500
REPORT_PATH = r"C:\Users\andre\LitigationOS\temp\brain_txt_extraction_report.txt"


def should_skip(filename: str, file_size: int) -> str:
    """Return skip reason or empty string if file should be processed."""
    if file_size == 0:
        return "zero-byte"
    for pat in SKIP_PATTERNS:
        if pat.search(filename):
            return f"matches skip pattern: {pat.pattern}"
    return ""


def queue_directory(engine: ExtractionEngine, dir_path: str, priority: int) -> dict:
    """Queue files from a directory with skip-pattern filtering.
    Returns stats dict."""
    stats = {"queued": 0, "skipped": 0, "skip_reasons": {}, "missing": False}

    if not os.path.isdir(dir_path):
        print(f"  WARNING: Directory not found: {dir_path}")
        stats["missing"] = True
        return stats

    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            full_path = os.path.join(root, fname)
            try:
                file_size = os.path.getsize(full_path)
            except OSError:
                stats["skipped"] += 1
                continue

            reason = should_skip(fname, file_size)
            if reason:
                stats["skipped"] += 1
                stats["skip_reasons"][reason] = stats["skip_reasons"].get(reason, 0) + 1
                continue

            try:
                engine.bm.queue_extraction(
                    file_path=full_path,
                    priority=priority,
                    file_type=ext.lstrip('.'),
                    file_size=file_size,
                    extraction_method='auto',
                )
                stats["queued"] += 1
            except Exception as e:
                if "UNIQUE constraint" in str(e) or "already" in str(e).lower():
                    stats["skipped"] += 1
                    stats["skip_reasons"]["already queued"] = stats["skip_reasons"].get("already queued", 0) + 1
                else:
                    stats["skipped"] += 1
                    stats["skip_reasons"][f"error: {str(e)[:60]}"] = 1

    return stats


def main():
    start_time = time.time()
    report_lines = []

    def log(msg: str):
        print(msg)
        report_lines.append(msg)

    log("=" * 70)
    log("  BRAIN-06: TXT File Extraction into Multi-Brain Universe")
    log(f"  Started: {datetime.now().isoformat()}")
    log("=" * 70)

    # ── Pre-extraction baseline ──
    engine = ExtractionEngine()
    log("\n── PRE-EXTRACTION BASELINE ──")
    pre_status = engine.get_status()
    pre_rows = pre_status['total_rows']
    log(f"  Total brain rows before: {pre_rows}")
    queue_counts = pre_status['queue'].get('counts', {})
    pre_pending = queue_counts.get('pending', 0)
    log(f"  Queue pending before:    {pre_pending}")

    # ── Phase 1: Queue files from all directories ──
    log("\n── PHASE 1: QUEUING FILES ──")
    total_queued = 0
    total_skipped = 0

    for dir_path, priority, label in SCAN_DIRS:
        log(f"\n  Scanning: {dir_path}")
        log(f"    Label: {label} | Priority: {priority}")
        stats = queue_directory(engine, dir_path, priority)

        if stats["missing"]:
            log(f"    ⚠ DIRECTORY NOT FOUND — skipping")
            continue

        log(f"    Queued:  {stats['queued']}")
        log(f"    Skipped: {stats['skipped']}")
        if stats["skip_reasons"]:
            for reason, count in sorted(stats["skip_reasons"].items(), key=lambda x: -x[1]):
                log(f"      - {reason}: {count}")

        total_queued += stats["queued"]
        total_skipped += stats["skipped"]

    log(f"\n  TOTAL QUEUED:  {total_queued}")
    log(f"  TOTAL SKIPPED: {total_skipped}")

    # ── Phase 2: Process the queue ──
    log(f"\n── PHASE 2: PROCESSING QUEUE (limit={PROCESS_LIMIT}) ──")
    process_stats = engine.process_queue(limit=PROCESS_LIMIT)

    log(f"\n  Files processed: {process_stats['files_processed']}")
    log(f"  Files failed:    {process_stats['files_failed']}")
    log(f"  Pages extracted: {process_stats['pages_extracted']}")
    log(f"  Items inserted:  {process_stats['items_inserted']}")

    if process_stats['errors']:
        log(f"\n  Errors ({len(process_stats['errors'])}):")
        for err in process_stats['errors'][:20]:
            log(f"    - {err[:120]}")
        if len(process_stats['errors']) > 20:
            log(f"    ... and {len(process_stats['errors']) - 20} more")

    # ── Phase 3: Post-extraction status ──
    log("\n── POST-EXTRACTION STATUS ──")
    post_status = engine.get_status()
    post_rows = post_status['total_rows']
    new_rows = post_rows - pre_rows

    log(f"  Total brain rows after:  {post_rows}")
    log(f"  NEW ROWS ADDED:          {new_rows}")

    # Brain breakdown
    log("\n  Brain Breakdown:")
    for brain_name, tables in post_status['brains'].items():
        if isinstance(tables, dict) and 'error' not in tables:
            brain_rows = sum(c for c in tables.values() if c > 0)
            if brain_rows > 0:
                log(f"    {brain_name:<30} {brain_rows:>8} rows")
                for tbl, cnt in sorted(tables.items(), key=lambda x: -x[1]):
                    if cnt > 0:
                        log(f"      {tbl:<28} {cnt:>8}")

    # Inserter breakdown
    ins = post_status['inserter_stats']
    active = {k: v for k, v in ins.items() if v > 0}
    if active:
        log("\n  Insertion Breakdown (this run):")
        for k, v in sorted(active.items(), key=lambda x: -x[1]):
            log(f"    {k:<35} {v:>6}")

    # Queue status
    queue_post = post_status['queue'].get('counts', {})
    log("\n  Queue Status:")
    for status_name, count in sorted(queue_post.items()):
        log(f"    {status_name:<15} {count:>6}")

    elapsed = time.time() - start_time
    log(f"\n  Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    log(f"  Completed: {datetime.now().isoformat()}")
    log("=" * 70)

    # ── Save report ──
    try:
        with open(REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"\n  Report saved to: {REPORT_PATH}")
    except Exception as e:
        print(f"\n  WARNING: Could not save report: {e}")


if __name__ == '__main__':
    main()
