
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Dict, Any, List, Tuple, Optional

def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    # FTS5 table
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(chunk_id, doc_id, path, text);")
    cur.execute("CREATE TABLE IF NOT EXISTS docs(doc_id TEXT PRIMARY KEY, path TEXT, sha256 TEXT, mtime REAL, meta_json TEXT);")
    con.commit()
    con.close()

def upsert_doc(con: sqlite3.Connection, doc: Dict[str, Any]) -> None:
    con.execute(
        "INSERT OR REPLACE INTO docs(doc_id, path, sha256, mtime, meta_json) VALUES (?,?,?,?,?)",
        (doc["doc_id"], doc["path"], doc["sha256"], doc["mtime"], doc.get("meta_json","{}"))
    )

def upsert_chunks(con: sqlite3.Connection, chunks: List[Dict[str, Any]]) -> None:
    con.executemany(
        "INSERT INTO chunks(chunk_id, doc_id, path, text) VALUES (?,?,?,?)",
        [(c["chunk_id"], c["doc_id"], c["path"], c["text"]) for c in chunks]
    )

def search(db_path: Path, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute("SELECT chunk_id, doc_id, path, snippet(chunks, 3, '[', ']', '…', 20) as snip FROM chunks WHERE chunks MATCH ? LIMIT ?",
                       (query, limit)).fetchall()
    con.close()
    return [dict(r) for r in rows]
