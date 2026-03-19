#!/usr/bin/env python3
"""
THE MANBEARPIG — Session Recall Module — EPOCH v9.0 OMEGA-INFINITY
===================================================================
Cross-session learning: reads Copilot CLI session history to provide
continuity across sessions. Indexes past decisions, file changes,
and key patterns for the litigation command center.
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Copilot session store paths (Windows)
COPILOT_DIR = Path(os.path.expanduser("~")) / ".copilot"
SESSION_STATE_DIR = COPILOT_DIR / "session-state"

# The global session store DB is managed by the Copilot CLI
# We look for session data in individual session directories
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = LITIGOS_ROOT / "litigation_context.db"


class SessionRecall:
    """
    Reads Copilot CLI session history for cross-session learning.
    Searches events.jsonl files in session-state directories.
    Also queries copilot_sessions table in litigation_context.db if available.
    """

    def __init__(self):
        self.session_dirs = self._discover_session_dirs()
        self._db_conn = None

    def _discover_session_dirs(self) -> List[Path]:
        """Find all Copilot session directories."""
        dirs = []
        if SESSION_STATE_DIR.exists():
            for d in SESSION_STATE_DIR.iterdir():
                if d.is_dir() and (d / "events.jsonl").exists():
                    dirs.append(d)
        dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return dirs

    def _get_db(self):
        """Get connection to litigation_context.db."""
        if self._db_conn is None:
            try:
                self._db_conn = sqlite3.connect(str(DB_PATH), timeout=10)
                self._db_conn.execute("PRAGMA journal_mode=WAL")
            except Exception as e:
                logger.debug(f"DB connection failed: {e}")
                return None
        return self._db_conn

    def get_recent_sessions(self, limit: int = 10) -> dict:
        """Get most recent Copilot sessions with summaries."""
        sessions = []
        for d in self.session_dirs[:limit]:
            session_id = d.name
            info = {"session_id": session_id, "path": str(d)}

            # Get modification time
            events_file = d / "events.jsonl"
            try:
                info["last_modified"] = datetime.fromtimestamp(
                    events_file.stat().st_mtime
                ).isoformat()
            except Exception:
                info["last_modified"] = None

            # Try to read plan.md for summary
            plan_file = d / "plan.md"
            if plan_file.exists():
                try:
                    text = plan_file.read_text(encoding="utf-8", errors="replace")[:500]
                    info["plan_summary"] = text.split("\n")[0][:200]
                except Exception:
                    pass

            # Try to read checkpoints for context
            checkpoint_dir = d / "checkpoints"
            if checkpoint_dir.exists():
                checkpoints = sorted(checkpoint_dir.glob("*.md"))
                if checkpoints:
                    info["checkpoint_count"] = len(checkpoints)
                    try:
                        latest = checkpoints[-1]
                        info["latest_checkpoint"] = latest.stem
                    except Exception:
                        pass

            # Count events
            try:
                with open(events_file, "r", encoding="utf-8", errors="replace") as f:
                    event_count = sum(1 for _ in f)
                info["event_count"] = event_count
            except Exception:
                info["event_count"] = 0

            sessions.append(info)

        return {
            "sessions": sessions,
            "total_discovered": len(self.session_dirs),
            "showing": len(sessions),
            "status": "ok"
        }

    def search_sessions(self, query: str, limit: int = 20) -> dict:
        """Search across session events for matching content."""
        if not query:
            return {"error": "Query required", "status": "error"}

        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]
        matches = []

        for d in self.session_dirs[:50]:  # Search last 50 sessions
            events_file = d / "events.jsonl"
            session_id = d.name
            session_matches = []

            try:
                with open(events_file, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f):
                        if i > 500:  # Cap per session
                            break
                        line_lower = line.lower()
                        if any(kw in line_lower for kw in keywords):
                            # Extract a meaningful snippet
                            try:
                                event = json.loads(line)
                                content = str(event.get("content", event.get("message", "")))[:300]
                                session_matches.append({
                                    "line": i,
                                    "snippet": content[:200],
                                    "type": event.get("type", "unknown")
                                })
                            except json.JSONDecodeError:
                                pass
            except Exception:
                continue

            if session_matches:
                # Get session age
                try:
                    mtime = datetime.fromtimestamp(events_file.stat().st_mtime).isoformat()
                except Exception:
                    mtime = None

                matches.append({
                    "session_id": session_id,
                    "match_count": len(session_matches),
                    "last_modified": mtime,
                    "top_matches": session_matches[:5]
                })

            if len(matches) >= limit:
                break

        matches.sort(key=lambda x: -x["match_count"])
        return {
            "query": query,
            "matches": matches,
            "total_matches": sum(m["match_count"] for m in matches),
            "sessions_searched": min(len(self.session_dirs), 50),
            "status": "ok"
        }

    def get_session_summary(self, session_id: str) -> dict:
        """Get detailed summary of a specific session."""
        session_dir = SESSION_STATE_DIR / session_id
        if not session_dir.exists():
            return {"error": f"Session {session_id} not found", "status": "error"}

        summary = {"session_id": session_id}

        # Plan
        plan_file = session_dir / "plan.md"
        if plan_file.exists():
            try:
                summary["plan"] = plan_file.read_text(encoding="utf-8", errors="replace")[:2000]
            except Exception:
                pass

        # Checkpoints
        checkpoint_dir = session_dir / "checkpoints"
        if checkpoint_dir.exists():
            checkpoints = []
            for cp in sorted(checkpoint_dir.glob("*.md")):
                try:
                    text = cp.read_text(encoding="utf-8", errors="replace")[:500]
                    checkpoints.append({"name": cp.stem, "preview": text[:200]})
                except Exception:
                    pass
            summary["checkpoints"] = checkpoints

        # Events summary
        events_file = session_dir / "events.jsonl"
        if events_file.exists():
            try:
                with open(events_file, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                summary["event_count"] = len(lines)
                # First and last events
                if lines:
                    try:
                        first = json.loads(lines[0])
                        summary["first_event"] = str(first.get("content", first.get("message", "")))[:200]
                    except Exception:
                        pass
                    try:
                        last = json.loads(lines[-1])
                        summary["last_event"] = str(last.get("content", last.get("message", "")))[:200]
                    except Exception:
                        pass
            except Exception:
                pass

        # Files in session
        files_dir = session_dir / "files"
        if files_dir.exists():
            try:
                summary["session_files"] = [f.name for f in files_dir.iterdir()][:20]
            except Exception:
                pass

        summary["status"] = "ok"
        return summary

    def get_cross_session_patterns(self) -> dict:
        """Analyze patterns across sessions — what files are frequently edited, what topics recur."""
        file_edits = {}
        topic_freq = {}
        session_count = 0

        for d in self.session_dirs[:30]:
            session_count += 1
            events_file = d / "events.jsonl"
            try:
                with open(events_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            # Track file edits
                            if event.get("type") in ("edit", "create"):
                                fp = event.get("path", event.get("file_path", ""))
                                if fp:
                                    file_edits[fp] = file_edits.get(fp, 0) + 1
                            # Track topics from content
                            content = str(event.get("content", "")).lower()
                            for topic in ["filing", "evidence", "deadline", "mcneill", "watson",
                                         "msc", "coa", "jtc", "custody", "ppo", "appeal",
                                         "impeachment", "contempt", "disqualification"]:
                                if topic in content:
                                    topic_freq[topic] = topic_freq.get(topic, 0) + 1
                        except json.JSONDecodeError:
                            pass
            except Exception:
                continue

        # Sort
        top_files = sorted(file_edits.items(), key=lambda x: -x[1])[:20]
        top_topics = sorted(topic_freq.items(), key=lambda x: -x[1])[:15]

        return {
            "sessions_analyzed": session_count,
            "top_edited_files": [{"path": f, "edits": c} for f, c in top_files],
            "topic_frequency": [{"topic": t, "count": c} for t, c in top_topics],
            "status": "ok"
        }

    def close(self):
        if self._db_conn:
            try:
                self._db_conn.close()
            except Exception:
                pass
            self._db_conn = None


# CLI interface
if __name__ == "__main__":
    sr = SessionRecall()
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "recent":
            result = sr.get_recent_sessions()
        elif action == "search" and len(sys.argv) > 2:
            result = sr.search_sessions(" ".join(sys.argv[2:]))
        elif action == "summary" and len(sys.argv) > 2:
            result = sr.get_session_summary(sys.argv[2])
        elif action == "patterns":
            result = sr.get_cross_session_patterns()
        else:
            result = {"error": "Usage: session_recall.py [recent|search <query>|summary <id>|patterns]"}
    else:
        result = sr.get_recent_sessions()

    print(json.dumps(result, indent=2, default=str))
    sr.close()
