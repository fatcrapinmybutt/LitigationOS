"""
AUTONOMOS — Master Orchestrator
=================================
Single entry point for the complete autonomous system:
  SENTINEL (drive org) + INQUISITOR (file analysis) + Publisher (My Docs push)

Usage:
  python autonomos.py start        # Start both SENTINEL and INQUISITOR
  python autonomos.py sentinel     # Start SENTINEL only
  python autonomos.py inquisitor   # Start INQUISITOR only
  python autonomos.py status       # Show full system status
  python autonomos.py classify <f> # Classify a single file
  python autonomos.py analyze <f>  # Analyze a single file
  python autonomos.py push         # Push filings to My Documents
  python autonomos.py health       # System health check
"""
import sys
import os
import json
import time
import threading
from pathlib import Path
from datetime import datetime

# Setup paths
_autonomos_root = Path(__file__).parent
_sentinel_dir = _autonomos_root / "sentinel"
_inquisitor_dir = _autonomos_root / "inquisitor"
_shared_dir = _autonomos_root / "shared"
for p in [str(_autonomos_root), str(_sentinel_dir), str(_inquisitor_dir), str(_shared_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from autonomos_config import (
    SENTINEL_QUEUE_DB, SENTINEL_OPS_DB, INQUISITOR_RESULTS_DB,
    EVENT_BRIDGE_DB, PROVENANCE_DB, CENTRAL_DB,
    LITIGOS_ROOT, DIR_MY_DOCS_FILINGS,
)


def _check_dependencies() -> dict:
    """Check that all required dependencies are available."""
    deps = {}
    for name in ["watchdog", "fitz", "docx", "plyer"]:
        try:
            __import__(name)
            deps[name] = "OK"
        except ImportError:
            deps[name] = "MISSING"
    return deps


def _check_databases() -> dict:
    """Check database accessibility."""
    dbs = {
        "central": CENTRAL_DB,
        "sentinel_queue": SENTINEL_QUEUE_DB,
        "sentinel_ops": SENTINEL_OPS_DB,
        "inquisitor_results": INQUISITOR_RESULTS_DB,
        "event_bridge": EVENT_BRIDGE_DB,
        "provenance": PROVENANCE_DB,
    }
    result = {}
    for name, path in dbs.items():
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            result[name] = {"exists": True, "size_mb": round(size_mb, 2)}
        else:
            result[name] = {"exists": False, "size_mb": 0}
    return result


def health_check() -> dict:
    """Run a comprehensive health check."""
    return {
        "timestamp": datetime.now().isoformat(),
        "dependencies": _check_dependencies(),
        "databases": _check_databases(),
        "litigos_root": str(LITIGOS_ROOT),
        "litigos_exists": LITIGOS_ROOT.exists(),
        "my_docs_exists": DIR_MY_DOCS_FILINGS.exists(),
        "python_version": sys.version,
    }


def start_sentinel():
    """Start SENTINEL daemon."""
    from sentinel import Sentinel
    s = Sentinel()
    s.start()


def start_inquisitor():
    """Start INQUISITOR daemon."""
    from inquisitor import Inquisitor
    i = Inquisitor()
    i.start()


def start_both():
    """Start both SENTINEL and INQUISITOR in parallel threads."""
    print("[AUTONOMOS] Starting full autonomous system...", file=sys.stderr)

    sentinel_thread = threading.Thread(target=start_sentinel, name="SENTINEL", daemon=True)
    inquisitor_thread = threading.Thread(target=start_inquisitor, name="INQUISITOR", daemon=True)

    sentinel_thread.start()
    time.sleep(2)  # Let SENTINEL initialize first
    inquisitor_thread.start()

    print("[AUTONOMOS] Both SENTINEL and INQUISITOR running.", file=sys.stderr)
    print("[AUTONOMOS] Press Ctrl+C to stop.", file=sys.stderr)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[AUTONOMOS] Shutting down...", file=sys.stderr)


def get_status() -> dict:
    """Get full system status."""
    status = health_check()

    # Queue stats
    try:
        from sentinel_monitor import SentinelMonitor
        m = SentinelMonitor()
        status["sentinel_queue"] = m.queue_stats()
    except Exception as e:
        status["sentinel_queue"] = {"error": str(e)}

    # Event bridge stats
    try:
        from event_bridge import EventBridge
        b = EventBridge()
        status["event_bridge"] = b.stats()
        b.close()
    except Exception as e:
        status["event_bridge"] = {"error": str(e)}

    # Provenance stats
    try:
        from provenance import ProvenanceTracker
        p = ProvenanceTracker()
        status["provenance"] = p.stats()
        p.close()
    except Exception as e:
        status["provenance"] = {"error": str(e)}

    return status


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="AUTONOMOS — Autonomous Intelligence & Filing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python autonomos.py start           Start full system
  python autonomos.py sentinel        Start SENTINEL only
  python autonomos.py inquisitor      Start INQUISITOR only
  python autonomos.py classify file.pdf   Classify a file
  python autonomos.py analyze file.pdf    Analyze a file
  python autonomos.py push            Push filings to My Documents
  python autonomos.py health          System health check
  python autonomos.py status          Full status report
        """
    )
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("start", help="Start SENTINEL + INQUISITOR")
    sub.add_parser("sentinel", help="Start SENTINEL only")
    sub.add_parser("inquisitor", help="Start INQUISITOR only")
    sub.add_parser("status", help="Full system status")
    sub.add_parser("health", help="Health check")
    sub.add_parser("push", help="Push filings to My Documents")

    classify_p = sub.add_parser("classify", help="Classify a file")
    classify_p.add_argument("file", help="File to classify")

    analyze_p = sub.add_parser("analyze", help="Analyze a file")
    analyze_p.add_argument("file", help="File to analyze")
    analyze_p.add_argument("--lane", default="")

    args = parser.parse_args()

    if args.action == "start":
        start_both()
    elif args.action == "sentinel":
        start_sentinel()
    elif args.action == "inquisitor":
        start_inquisitor()
    elif args.action == "status":
        print(json.dumps(get_status(), indent=2))
    elif args.action == "health":
        print(json.dumps(health_check(), indent=2))
    elif args.action == "push":
        from publisher import push_all_lanes, ensure_my_docs_structure
        ensure_my_docs_structure()
        print(json.dumps(push_all_lanes(), indent=2))
    elif args.action == "classify":
        from sentinel_classifier import classify_file
        from dataclasses import asdict
        result = classify_file(args.file)
        print(json.dumps(asdict(result), indent=2))
    elif args.action == "analyze":
        from inquisitor import analyze_file
        from dataclasses import asdict
        result = analyze_file(args.file, args.lane)
        print(json.dumps(asdict(result), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
