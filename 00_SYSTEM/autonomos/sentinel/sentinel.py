"""
SENTINEL — Autonomous Drive Organization Daemon
=================================================
Orchestrates: Monitor → Classify → Move → Provenance → Event Bridge
Ties together all SENTINEL components into a single daemon.

Usage:
  python sentinel.py start        # Start daemon (Ctrl+C to stop)
  python sentinel.py process      # Process pending queue once
  python sentinel.py status       # Show system status
  python sentinel.py stats        # Show detailed statistics
  python sentinel.py undo <id>    # Undo a move
"""
import sys
import os
import time
import json
import signal
from pathlib import Path
from datetime import datetime

_sentinel_dir = Path(__file__).parent
_shared = _sentinel_dir.parent / "shared"
for p in [str(_sentinel_dir), str(_shared)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from autonomos_config import (
    SENTINEL_QUEUE_DB, SENTINEL_OPS_DB, PROVENANCE_DB,
    EVENT_BRIDGE_DB, EVENT_FILE_ORGANIZED, EVENT_FILE_CLASSIFIED,
    EVENT_FILE_DETECTED, MAX_FILE_SIZE_MB, PROCESSING_RATE_LIMIT,
)
from sentinel_monitor import SentinelMonitor
from sentinel_classifier import classify_file, ClassificationResult
from sentinel_mover import SentinelMover, MoveResult
from provenance import ProvenanceTracker
from event_bridge import EventBridge


class Sentinel:
    """Main SENTINEL daemon — orchestrates drive organization."""

    def __init__(self):
        self._monitor = SentinelMonitor()
        self._mover = SentinelMover()
        self._provenance = ProvenanceTracker()
        self._bridge = EventBridge()
        self._running = False
        self._stats = {
            "files_detected": 0,
            "files_classified": 0,
            "files_moved": 0,
            "files_skipped": 0,
            "errors": 0,
            "started_at": "",
        }

    def start(self):
        """Start the SENTINEL daemon."""
        print("[SENTINEL] Starting autonomous drive organizer...", file=sys.stderr)
        self._stats["started_at"] = datetime.now().isoformat()
        self._running = True

        # Start file system monitor
        self._monitor.start()
        print("[SENTINEL] File system monitors active", file=sys.stderr)

        # Main processing loop
        try:
            while self._running:
                processed = self._process_batch()
                if processed == 0:
                    time.sleep(2)  # No work — sleep
                else:
                    time.sleep(0.1)  # More work available — brief pause
        except KeyboardInterrupt:
            print("\n[SENTINEL] Shutting down...", file=sys.stderr)
        finally:
            self.stop()

    def stop(self):
        """Stop the daemon gracefully."""
        self._running = False
        self._monitor.stop()
        self._mover.close()
        self._provenance.close()
        self._bridge.close()
        print("[SENTINEL] Stopped.", file=sys.stderr)

    def _process_batch(self, limit: int = 10) -> int:
        """Process a batch of pending files. Returns count processed."""
        pending = self._monitor.get_pending(limit)
        if not pending:
            return 0

        processed = 0
        for item in pending:
            try:
                self._process_file(item)
                processed += 1
            except Exception as e:
                self._stats["errors"] += 1
                self._monitor.mark_failed(item["id"], str(e))
                print(f"[SENTINEL] Error processing {item['path']}: {e}", file=sys.stderr)

        return processed

    def _process_file(self, item: dict):
        """Process a single queued file: classify → move → track → emit event."""
        file_path = item["path"]
        drive = item["drive"]
        sha256 = item["sha256"]
        queue_id = item["id"]

        # Skip if already tracked
        if self._provenance.is_known(sha256) and sha256 not in ("UNREADABLE", ""):
            self._monitor.mark_processed(queue_id, classification="KNOWN_DUPLICATE")
            self._stats["files_skipped"] += 1
            return

        # Record detection in provenance
        file_id = self._provenance.record_detection(
            file_path, drive, sha256, item.get("size", 0)
        )
        self._stats["files_detected"] += 1

        # Classify
        result = classify_file(file_path)
        self._stats["files_classified"] += 1

        # Record classification
        self._provenance.record_classification(
            file_id, result.doc_type, result.lane, result.confidence
        )

        # Emit classification event
        self._bridge.publish(EVENT_FILE_CLASSIFIED, {
            "file_id": file_id,
            "path": file_path,
            "lane": result.lane,
            "doc_type": result.doc_type,
            "confidence": result.confidence,
        })

        # Skip move for irrelevant files
        if result.priority == "SKIP" or result.category == "IRRELEVANT":
            self._monitor.mark_processed(queue_id, classification=result.category)
            self._stats["files_skipped"] += 1
            return

        # Move file to organized location
        move_result = self._mover.safe_move(
            file_path,
            lane=result.lane,
            doc_type=result.doc_type,
            confidence=result.confidence,
        )

        if move_result.success:
            self._stats["files_moved"] += 1
            self._provenance.record_move(file_id, move_result.destination)
            self._monitor.mark_processed(
                queue_id,
                classification=result.doc_type,
                lane=result.lane,
                confidence=result.confidence,
                dest_path=move_result.destination,
            )
            # Emit organized event for INQUISITOR
            self._bridge.publish(EVENT_FILE_ORGANIZED, {
                "file_id": file_id,
                "source_path": file_path,
                "dest_path": move_result.destination,
                "lane": result.lane,
                "doc_type": result.doc_type,
                "confidence": result.confidence,
                "sha256": sha256,
                "move_id": move_result.move_id,
            })
        else:
            self._stats["errors"] += 1
            self._provenance.record_error(file_id, move_result.error)
            self._monitor.mark_failed(queue_id, move_result.error)

    def process_once(self, limit: int = 100) -> dict:
        """Process pending queue once (non-daemon mode). Returns stats."""
        count = 0
        while count < limit:
            batch = self._process_batch(min(10, limit - count))
            if batch == 0:
                break
            count += batch
        return {"processed": count, **self._stats}

    def status(self) -> dict:
        """Get comprehensive status."""
        return {
            "running": self._running,
            "stats": dict(self._stats),
            "queue": self._monitor.queue_stats(),
            "drives": self._monitor.drive_stats(),
            "provenance": self._provenance.stats(),
            "moves": self._mover.stats(),
            "events": self._bridge.stats(),
        }


# ── CLI Entry Point ─────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="SENTINEL — Autonomous Drive Organizer")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("start", help="Start daemon (Ctrl+C to stop)")
    sub.add_parser("process", help="Process pending queue once")
    sub.add_parser("status", help="Show system status")
    sub.add_parser("stats", help="Show detailed statistics")

    undo_p = sub.add_parser("undo", help="Undo a move")
    undo_p.add_argument("move_id", help="Move ID to undo")

    hist_p = sub.add_parser("history", help="Show recent moves")
    hist_p.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    sentinel = Sentinel()

    if args.action == "start":
        sentinel.start()

    elif args.action == "process":
        result = sentinel.process_once()
        print(json.dumps(result, indent=2))

    elif args.action == "status":
        status = sentinel.status()
        print(json.dumps(status, indent=2))

    elif args.action == "stats":
        status = sentinel.status()
        print(f"\n=== SENTINEL Status ===")
        print(f"Queue:      {status['queue']}")
        print(f"Provenance: {status['provenance']}")
        print(f"Moves:      {status['moves']}")
        print(f"Events:     {status['events']}")

    elif args.action == "undo":
        result = sentinel._mover.undo(args.move_id)
        print(f"Undo {'OK' if result.success else 'FAILED'}: {result.error or ''}")

    elif args.action == "history":
        for m in sentinel._mover.recent_moves(args.limit):
            status = "↩" if m["undone"] else "→"
            print(f"  [{m['lane']}] {m['source']} {status} {m['dest']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
