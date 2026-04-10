"""
Intake Engine CLI — Command-line interface for the intake pipeline.
===================================================================

Usage:
    # Process a single file
    python -m intake --file evidence.pdf --db litigation.db

    # Process a folder
    python -m intake --folder /path/to/intake/ --db litigation.db

    # Process with case config
    python -m intake --folder /intake/ --config case_config.yaml --db case.db

    # Dry run (analyze only, no DB writes)
    python -m intake --folder /intake/ --dry-run

    # Process with max file limit
    python -m intake --folder /intake/ --max-files 50 --db litigation.db
"""

import argparse
import json
import sys
from pathlib import Path

from .pipeline import IntakePipeline
from .case_config import CaseConfig


def main():
    parser = argparse.ArgumentParser(
        description="LitigationOS Intake Engine — Ingest, classify, analyze, and route documents",
    )
    parser.add_argument("--file", type=str, help="Single file to process")
    parser.add_argument("--folder", type=str, help="Folder to process (recursive)")
    parser.add_argument("--db", type=str, required=True, help="Database path")
    parser.add_argument("--config", type=str, help="Case config YAML/JSON path")
    parser.add_argument("--max-files", type=int, default=0, help="Max files (0=unlimited)")
    parser.add_argument("--no-skip", action="store_true", help="Don't skip existing files")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, no DB writes")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.file and not args.folder:
        parser.error("Specify --file or --folder")

    # Load case config
    case_config = None
    if args.config:
        config_path = Path(args.config)
        if config_path.suffix in (".yaml", ".yml"):
            case_config = CaseConfig.from_yaml(config_path)
        else:
            case_config = CaseConfig.from_json(config_path)
    elif args.folder:
        case_config = CaseConfig.auto_detect(args.folder)

    # Initialize pipeline
    db_path = None if args.dry_run else args.db
    pipeline = IntakePipeline(
        db_path=db_path,
        case_config=case_config,
        ocr_enabled=not args.no_ocr,
    )

    # If dry-run, still need to connect for schema but use temp DB
    if args.dry_run:
        import tempfile
        temp_db = Path(tempfile.mkdtemp()) / "dry_run.db"
        pipeline.router.connect(temp_db)

    try:
        if args.file:
            result = pipeline.process_file(args.file)
            if args.json:
                print(json.dumps(result.__dict__, indent=2, default=str))
            else:
                _print_file_result(result)

        elif args.folder:
            batch = pipeline.process_folder(
                args.folder,
                max_files=args.max_files,
                skip_existing=not args.no_skip,
            )
            if args.json:
                print(json.dumps({
                    "total_files": batch.total_files,
                    "processed": batch.processed,
                    "skipped": batch.skipped,
                    "errors": batch.errors,
                    "duration_sec": batch.duration_sec,
                    "total_quotes": batch.total_quotes,
                    "total_events": batch.total_events,
                    "total_authorities": batch.total_authorities,
                    "total_impeachment": batch.total_impeachment,
                    "total_entities": batch.total_entities,
                }, indent=2))
            else:
                _print_batch_result(batch)

    finally:
        pipeline.close()


def _print_file_result(r):
    """Pretty-print a single file result."""
    icon = "✅" if r.status == "completed" else "⏭️" if r.status == "skipped" else "❌"
    print(f"\n{icon} {r.file_name}")
    print(f"   Status: {r.status}")
    if r.error:
        print(f"   Error: {r.error}")
    print(f"   Type: {r.doc_type} | Lanes: {', '.join(r.lanes) or 'none'} | Urgency: {r.urgency}")
    print(f"   Extracted: {r.page_count} pages, {r.char_count:,} chars ({r.extraction_method})")
    print(f"   Topics: {', '.join(r.legal_topics) or 'none'}")
    print(f"   Found: {r.quotes_found} quotes, {r.events_found} events, "
          f"{r.authorities_found} authorities, {r.impeachment_found} impeachment")
    print(f"   Stored: {r.quotes_inserted} quotes, {r.events_inserted} events, "
          f"{r.authorities_inserted} authorities, {r.impeachment_inserted} impeachment, "
          f"{r.entities_inserted} entities")
    print(f"   Time: {r.duration_sec:.3f}s")


def _print_batch_result(b):
    """Pretty-print a batch result."""
    print(f"\n{'='*60}")
    print(f"  INTAKE PIPELINE — BATCH COMPLETE")
    print(f"{'='*60}")
    print(f"  Files:      {b.total_files} total, {b.processed} processed, "
          f"{b.skipped} skipped, {b.errors} errors")
    print(f"  Quotes:     {b.total_quotes} inserted")
    print(f"  Events:     {b.total_events} inserted")
    print(f"  Authorities:{b.total_authorities} inserted")
    print(f"  Impeachment:{b.total_impeachment} inserted")
    print(f"  Entities:   {b.total_entities} inserted")
    print(f"  Duration:   {b.duration_sec:.1f}s")
    print(f"{'='*60}")

    # Show errors
    errors = [r for r in b.results if r.status == "error"]
    if errors:
        print(f"\n  ❌ ERRORS ({len(errors)}):")
        for r in errors[:10]:
            print(f"    • {r.file_name}: {r.error}")


if __name__ == "__main__":
    main()
