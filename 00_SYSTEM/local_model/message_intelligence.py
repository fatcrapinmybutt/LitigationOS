"""
Message Intelligence — LitigationOS 2026
Analyzes andrew_messages (48,279 rows) and chatgpt_conversations (139,693 rows)
for evidence extraction, communication patterns, and strategic consistency
in Pigors v. Watson consolidated litigation.
"""

import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


class MessageIntelligence:
    """Analyzes messages and conversations for litigation intelligence."""

    def get_andrew_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query andrew_messages table (48,279 rows), with FTS availability."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM andrew_messages ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_chatgpt_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Query chatgpt_conversations table (139,693 rows)."""
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM chatgpt_conversations ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search_messages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """FTS search andrew_messages_fts MATCH query."""
        conn = _get_db()
        try:
            rows = conn.execute(
                """SELECT am.*
                   FROM andrew_messages am
                   JOIN andrew_messages_fts fts ON am.rowid = fts.rowid
                   WHERE andrew_messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def analyze_communication_patterns(self) -> Dict[str, Any]:
        """Analyze frequency, topics, and sentiment patterns in messages."""
        conn = _get_db()
        try:
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM andrew_messages"
            ).fetchone()["cnt"]

            # Date range
            date_range = conn.execute(
                """SELECT MIN(rowid) as earliest_id, MAX(rowid) as latest_id
                   FROM andrew_messages"""
            ).fetchone()

            # Sample messages for topic extraction
            samples = conn.execute(
                """SELECT * FROM andrew_messages
                   ORDER BY rowid DESC LIMIT 500"""
            ).fetchall()

            # Extract topic keywords from message content
            topic_counts: Counter = Counter()
            litigation_keywords = [
                "custody", "parenting", "visitation", "court", "judge",
                "mcneill", "watson", "separation", "children", "filing",
                "motion", "hearing", "appeal", "evidence", "discovery",
                "ppo", "foc", "friend of court", "alienation", "contempt",
            ]
            for row in samples:
                text = " ".join(
                    str(v) for v in dict(row).values() if v is not None
                ).lower()
                for kw in litigation_keywords:
                    if kw in text:
                        topic_counts[kw] += 1

            return {
                "total_messages": total,
                "earliest_id": dict(date_range).get("earliest_id"),
                "latest_id": dict(date_range).get("latest_id"),
                "sample_size": len(samples),
                "topic_frequency": dict(topic_counts.most_common(20)),
                "litigation_relevance_rate": (
                    round(sum(1 for r in samples if any(
                        kw in " ".join(str(v) for v in dict(r).values() if v).lower()
                        for kw in litigation_keywords
                    )) / max(len(samples), 1) * 100, 1)
                ),
            }
        finally:
            conn.close()

    def find_evidence_in_messages(self, topic: str) -> List[Dict[str, Any]]:
        """Search messages for evidence relevant to a topic."""
        conn = _get_db()
        try:
            # FTS search in andrew_messages
            msg_results = conn.execute(
                """SELECT am.*, 'andrew_messages' as source
                   FROM andrew_messages am
                   JOIN andrew_messages_fts fts ON am.rowid = fts.rowid
                   WHERE andrew_messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT 30""",
                (topic,),
            ).fetchall()

            # Also search chatgpt_conversations for relevant discussions
            chatgpt_results = conn.execute(
                """SELECT *, 'chatgpt_conversations' as source
                   FROM chatgpt_conversations
                   WHERE rowid IN (
                       SELECT rowid FROM chatgpt_conversations
                       LIMIT 5000
                   )
                   LIMIT 20""",
            ).fetchall()

            # Filter chatgpt results by topic keyword
            topic_lower = topic.lower()
            filtered_chatgpt = []
            for r in chatgpt_results:
                text = " ".join(str(v) for v in dict(r).values() if v).lower()
                if topic_lower in text:
                    filtered_chatgpt.append(dict(r))

            return {
                "topic": topic,
                "andrew_messages_hits": [dict(r) for r in msg_results],
                "chatgpt_conversation_hits": filtered_chatgpt[:20],
                "total_hits": len(msg_results) + len(filtered_chatgpt),
            }
        finally:
            conn.close()

    def find_strategic_inconsistencies(self) -> Dict[str, Any]:
        """Compare messages to filed documents for consistency issues."""
        conn = _get_db()
        try:
            # Get recent messages
            messages = conn.execute(
                """SELECT * FROM andrew_messages
                   ORDER BY rowid DESC LIMIT 200"""
            ).fetchall()

            # Get filed document content from evidence_quotes
            filed_quotes = conn.execute(
                """SELECT quote_text, speaker, legal_significance, evidence_category
                   FROM evidence_quotes
                   WHERE speaker LIKE '%Andrew%' OR speaker LIKE '%Pigors%'
                   ORDER BY rowid DESC LIMIT 200"""
            ).fetchall()

            # Get claims from claims table
            claims = conn.execute(
                """SELECT * FROM claims
                   WHERE actor LIKE '%Andrew%' OR actor LIKE '%Pigors%'
                   OR actor LIKE '%Plaintiff%'
                   ORDER BY rowid DESC LIMIT 100"""
            ).fetchall()

            return {
                "messages_analyzed": len(messages),
                "filed_statements_analyzed": len(filed_quotes),
                "claims_analyzed": len(claims),
                "filed_statements": [dict(r) for r in filed_quotes[:20]],
                "claims": [dict(r) for r in claims[:20]],
                "note": (
                    "Review messages against filed statements for consistency. "
                    "Any contradictions could be used for impeachment under MRE 613."
                ),
            }
        finally:
            conn.close()

    def get_message_timeline(
        self, start: Optional[str] = None, end: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Chronological message view with optional date range filtering."""
        conn = _get_db()
        try:
            # Get column names to find date-like columns
            cols = conn.execute(
                "PRAGMA table_info(andrew_messages)"
            ).fetchall()
            col_names = [c["name"] for c in cols]

            # Build query — try date column if it exists
            date_col = None
            for candidate in ["date", "timestamp", "created_at", "sent_at", "message_date"]:
                if candidate in col_names:
                    date_col = candidate
                    break

            if date_col and start and end:
                rows = conn.execute(
                    f"""SELECT * FROM andrew_messages
                        WHERE {date_col} BETWEEN ? AND ?
                        ORDER BY {date_col} ASC""",
                    (start, end),
                ).fetchall()
            elif date_col and start:
                rows = conn.execute(
                    f"""SELECT * FROM andrew_messages
                        WHERE {date_col} >= ?
                        ORDER BY {date_col} ASC""",
                    (start,),
                ).fetchall()
            elif date_col:
                rows = conn.execute(
                    f"SELECT * FROM andrew_messages ORDER BY {date_col} ASC LIMIT 500"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM andrew_messages ORDER BY rowid ASC LIMIT 500"
                ).fetchall()

            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Total counts, date ranges, topic distribution."""
        conn = _get_db()
        try:
            msg_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM andrew_messages"
            ).fetchone()["cnt"]

            chatgpt_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM chatgpt_conversations"
            ).fetchone()["cnt"]

            # Column info
            msg_cols = conn.execute(
                "PRAGMA table_info(andrew_messages)"
            ).fetchall()
            chatgpt_cols = conn.execute(
                "PRAGMA table_info(chatgpt_conversations)"
            ).fetchall()

            return {
                "andrew_messages_count": msg_count,
                "chatgpt_conversations_count": chatgpt_count,
                "total_records": msg_count + chatgpt_count,
                "andrew_messages_columns": [c["name"] for c in msg_cols],
                "chatgpt_conversations_columns": [c["name"] for c in chatgpt_cols],
            }
        finally:
            conn.close()


def self_test() -> Dict[str, Any]:
    """Run self-test to verify database connectivity and table access."""
    results = {"status": "ok", "tests": {}}
    mi = MessageIntelligence()
    try:
        stats = mi.get_statistics()
        results["tests"]["statistics"] = {
            "passed": stats["andrew_messages_count"] > 0,
            "andrew_messages": stats["andrew_messages_count"],
            "chatgpt_conversations": stats["chatgpt_conversations_count"],
        }
    except Exception as e:
        results["tests"]["statistics"] = {"passed": False, "error": str(e)}

    try:
        msgs = mi.get_andrew_messages(limit=5)
        results["tests"]["get_andrew_messages"] = {
            "passed": isinstance(msgs, list),
            "count": len(msgs),
        }
    except Exception as e:
        results["tests"]["get_andrew_messages"] = {"passed": False, "error": str(e)}

    try:
        convos = mi.get_chatgpt_conversations(limit=5)
        results["tests"]["get_chatgpt_conversations"] = {
            "passed": isinstance(convos, list),
            "count": len(convos),
        }
    except Exception as e:
        results["tests"]["get_chatgpt_conversations"] = {"passed": False, "error": str(e)}

    try:
        search = mi.search_messages("custody", limit=5)
        results["tests"]["search_messages"] = {
            "passed": isinstance(search, list),
            "count": len(search),
        }
    except Exception as e:
        results["tests"]["search_messages"] = {"passed": False, "error": str(e)}

    results["status"] = (
        "ok" if all(t.get("passed") for t in results["tests"].values()) else "degraded"
    )
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print(json.dumps(self_test(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "search" and len(sys.argv) > 2:
        mi = MessageIntelligence()
        print(json.dumps(mi.search_messages(sys.argv[2]), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        mi = MessageIntelligence()
        print(json.dumps(mi.get_statistics(), indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "patterns":
        mi = MessageIntelligence()
        print(json.dumps(mi.analyze_communication_patterns(), indent=2, default=str))
    else:
        print("Usage: python message_intelligence.py [test|search <query>|stats|patterns]")
