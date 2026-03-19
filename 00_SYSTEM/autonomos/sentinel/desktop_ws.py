"""
DELTA99 Ω∞ — Desktop WebSocket Bridge
=======================================
Real-time status push to Electron desktop app via WebSocket.
Broadcasts AUTONOMOS events (file organized, analysis complete,
filing updated, threat detected) as structured JSON messages.

Depends on: d99-windows-service
"""
import sys
import sqlite3
import json
import time
import threading
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import AUTONOMOS_ROOT, LITIGOS_ROOT

BRIDGE_DB = AUTONOMOS_ROOT / "desktop_bridge.db"
WS_PORT = 9876
POLL_INTERVAL = 2  # seconds

# ── Message Types ──────────────────────────────────────────────────
MSG_TYPES = {
    "FILE_ORGANIZED": {"icon": "📁", "priority": "low"},
    "FILE_ANALYZED": {"icon": "🔬", "priority": "medium"},
    "FILING_UPDATED": {"icon": "📋", "priority": "high"},
    "FILING_PUSHED": {"icon": "🚀", "priority": "high"},
    "THREAT_DETECTED": {"icon": "🚨", "priority": "critical"},
    "DEADLINE_ALERT": {"icon": "⏰", "priority": "critical"},
    "SYSTEM_HEALTH": {"icon": "💚", "priority": "low"},
    "EVIDENCE_GAP": {"icon": "🔍", "priority": "medium"},
    "CITATION_INVALID": {"icon": "⚠️", "priority": "medium"},
    "ANOMALY_DETECTED": {"icon": "🔴", "priority": "high"},
}


def _init_db() -> sqlite3.Connection:
    BRIDGE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(BRIDGE_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_type TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            priority TEXT DEFAULT 'low',
            delivered INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            delivered_at TEXT DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS ws_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT NOT NULL,
            connected_at TEXT DEFAULT (datetime('now')),
            last_ping TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'connected'
        );
        CREATE TABLE IF NOT EXISTS bridge_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            messages_queued INTEGER DEFAULT 0,
            messages_delivered INTEGER DEFAULT 0,
            clients_connected INTEGER DEFAULT 0,
            uptime_s REAL DEFAULT 0.0,
            recorded_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_outbox_delivered
            ON outbox(delivered, priority);
    """)
    conn.commit()
    return conn


def queue_message(msg_type: str, payload: dict) -> int:
    """Queue a message for delivery to desktop app."""
    meta = MSG_TYPES.get(msg_type, {"icon": "ℹ️", "priority": "low"})
    db = _init_db()

    enriched_payload = {
        "type": msg_type,
        "icon": meta["icon"],
        "priority": meta["priority"],
        "timestamp": datetime.now().isoformat(),
        "data": payload,
    }

    cursor = db.execute("""
        INSERT INTO outbox (msg_type, payload, priority)
        VALUES (?, ?, ?)
    """, (msg_type, json.dumps(enriched_payload), meta["priority"]))
    msg_id = cursor.lastrowid
    db.commit()
    db.close()
    return msg_id


def get_pending_messages(limit: int = 50) -> list[dict]:
    """Get undelivered messages (for polling-based clients)."""
    db = _init_db()
    rows = db.execute("""
        SELECT id, msg_type, payload, priority, created_at
        FROM outbox
        WHERE delivered = 0
        ORDER BY
            CASE priority
                WHEN 'critical' THEN 0
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            created_at ASC
        LIMIT ?
    """, (limit,)).fetchall()

    messages = []
    ids = []
    for r in rows:
        messages.append({
            "id": r[0],
            "type": r[1],
            "payload": json.loads(r[2]) if r[2] else {},
            "priority": r[3],
            "created_at": r[4],
        })
        ids.append(r[0])

    # Mark as delivered
    if ids:
        placeholders = ",".join("?" * len(ids))
        db.execute(f"""
            UPDATE outbox
            SET delivered = 1, delivered_at = datetime('now')
            WHERE id IN ({placeholders})
        """, ids)
        db.commit()

    db.close()
    return messages


def _generate_http_server_code() -> str:
    """Generate a simple HTTP polling server for desktop bridge."""
    return '''"""
LitigationOS Desktop Bridge — HTTP Polling Server
Serves pending AUTONOMOS events to the desktop app.
Run: python desktop_bridge_server.py
"""
import sys
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PORT = 9876
DB_PATH = Path(__file__).parent / "desktop_bridge.db"


class BridgeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/events":
            self._serve_events(parsed)
        elif parsed.path == "/health":
            self._serve_health()
        elif parsed.path == "/stats":
            self._serve_stats()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_events(self, parsed):
        params = parse_qs(parsed.query)
        limit = int(params.get("limit", ["50"])[0])

        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        rows = conn.execute("""
            SELECT id, msg_type, payload, priority, created_at
            FROM outbox WHERE delivered = 0
            ORDER BY CASE priority
                WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                WHEN 'medium' THEN 2 WHEN 'low' THEN 3
            END, created_at ASC
            LIMIT ?
        """, (limit,)).fetchall()

        messages = []
        ids = []
        for r in rows:
            messages.append({
                "id": r[0], "type": r[1],
                "payload": json.loads(r[2]) if r[2] else {},
                "priority": r[3], "created_at": r[4],
            })
            ids.append(r[0])

        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(f"""
                UPDATE outbox SET delivered = 1, delivered_at = datetime('now')
                WHERE id IN ({placeholders})
            """, ids)
            conn.commit()
        conn.close()

        self._json_response({"events": messages, "count": len(messages)})

    def _serve_health(self):
        self._json_response({"status": "ok", "service": "desktop-bridge"})

    def _serve_stats(self):
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        total = conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM outbox WHERE delivered = 0").fetchone()[0]
        conn.close()
        self._json_response({"total": total, "pending": pending, "delivered": total - pending})

    def _json_response(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress logging


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), BridgeHandler)
    print(f"Desktop bridge server running on http://127.0.0.1:{PORT}")
    print(f"  GET /events  — Fetch pending events")
    print(f"  GET /health  — Health check")
    print(f"  GET /stats   — Message statistics")
    server.serve_forever()
'''


def install_bridge() -> dict:
    """Install the desktop bridge server."""
    server_file = AUTONOMOS_ROOT / "desktop_bridge_server.py"
    code = _generate_http_server_code()
    server_file.write_text(code, encoding="utf-8")

    return {
        "server_file": str(server_file),
        "port": WS_PORT,
        "start_cmd": f"python {server_file}",
        "endpoints": {
            "events": f"http://127.0.0.1:{WS_PORT}/events",
            "health": f"http://127.0.0.1:{WS_PORT}/health",
            "stats": f"http://127.0.0.1:{WS_PORT}/stats",
        },
    }


def bridge_stats() -> dict:
    """Get bridge statistics."""
    db = _init_db()
    total = db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM outbox WHERE delivered = 0").fetchone()[0]
    delivered = total - pending
    db.close()
    return {
        "total_messages": total,
        "pending": pending,
        "delivered": delivered,
        "msg_types": list(MSG_TYPES.keys()),
    }


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "install":
        print(json.dumps(install_bridge(), indent=2))
    elif cmd == "pending":
        msgs = get_pending_messages()
        print(json.dumps(msgs, indent=2, default=str))
    elif cmd == "queue":
        msg_type = sys.argv[2] if len(sys.argv) > 2 else "SYSTEM_HEALTH"
        msg_id = queue_message(msg_type, {"test": True})
        print(f"Queued message {msg_id} of type {msg_type}")
    elif cmd == "stats":
        print(json.dumps(bridge_stats(), indent=2))
    else:
        print(f"Usage: python desktop_ws.py install|pending|queue|stats")
