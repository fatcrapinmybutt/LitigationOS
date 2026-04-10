"""
Filing Engine CLI Entry Point
==============================

Usage:
    python -m filing_engine --scan-triggers
    python -m filing_engine --filing F1 --dry-run
    python -m filing_engine --filing F1 --court mi_circuit --execute
    python -m filing_engine --status
    python -m filing_engine --run-detail 1
    echo '{"action":"run","filing_id":"F1"}' | python -m filing_engine --json
"""

import argparse
import json
import sys
from pathlib import Path

from .engine import FilingEngine
from .triggers import TriggerConfig


def main():
    parser = argparse.ArgumentParser(
        prog="filing_engine",
        description="Autonomous Court Document Preparation Engine"
    )
    parser.add_argument("--filing", "-f", help="Filing ID to process (e.g., F1, V2)")
    parser.add_argument("--case", "-c", help="Case number")
    parser.add_argument("--court", default="mi_circuit",
                       choices=["mi_circuit", "mi_coa", "mi_msc",
                                "wdmi_federal", "mi_district"],
                       help="Court type (default: mi_circuit)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Validate only — don't produce files (default behavior)")
    parser.add_argument("--execute", action="store_true",
                       help="Execute full pipeline (produces output files)")
    parser.add_argument("--scan-triggers", action="store_true",
                       help="Scan for active filing triggers")
    parser.add_argument("--status", action="store_true",
                       help="Show engine status dashboard")
    parser.add_argument("--run-detail", type=int,
                       help="Show details for a specific run ID")
    parser.add_argument("--json", action="store_true",
                       help="Read JSON from stdin for action dispatch")
    parser.add_argument("--db", help="Path to engine state database")
    parser.add_argument("--lit-db", help="Path to litigation database")

    args = parser.parse_args()

    config = TriggerConfig()
    engine = FilingEngine(db_path=args.db, lit_db_path=args.lit_db,
                          config=config)

    try:
        if args.json:
            # JSON stdin mode (like HYDRA Governor pattern)
            request = json.loads(sys.stdin.read())
            action = request.get("action", "status")

            if action == "run":
                result = engine.run(
                    filing_id=request.get("filing_id", ""),
                    case_number=request.get("case_number", ""),
                    court_type=request.get("court_type", "mi_circuit"),
                    dry_run=request.get("dry_run", True),
                    document_text=request.get("document_text", ""),
                    components=request.get("components", {})
                )
            elif action == "validate":
                result = engine.validate(
                    filing_id=request.get("filing_id", ""),
                    document_text=request.get("document_text", ""),
                    court_type=request.get("court_type", "mi_circuit"),
                )
            elif action == "triggers":
                triggers = engine.scan_triggers()
                result = json.loads(engine.trigger_scanner.to_json(triggers))
            else:
                result = engine.status()

            json.dump(result, sys.stdout, indent=2, default=str)
            print()

        elif args.scan_triggers:
            print(engine.trigger_report())

        elif args.status:
            status = engine.status()
            print(json.dumps(status, indent=2, default=str))

        elif args.run_detail is not None:
            detail = engine.get_run_detail(args.run_detail)
            print(json.dumps(detail, indent=2, default=str))

        elif args.filing:
            # --execute means live run; otherwise default to dry-run
            dry_run = not args.execute
            result = engine.run(
                filing_id=args.filing,
                case_number=args.case or "",
                court_type=args.court,
                dry_run=dry_run,
                trigger_reason="cli"
            )
            print(json.dumps(result, indent=2, default=str))

        else:
            parser.print_help()

    finally:
        engine.close()


if __name__ == "__main__":
    main()
