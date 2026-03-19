from __future__ import annotations
import sqlite3, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

def build_pack(db_path: Path, out_dir: Path, purpose: str, query: str, lane: Optional[str]=None, case_id: Optional[str]=None, max_quotes: int=120) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    where = ["corpus_fts MATCH ?"]
    params = [query]
    if lane:
        where.append("q.lane = ?")
        params.append(lane)
    if case_id:
        where.append("q.case_id = ?")
        params.append(case_id)

    sql = (
        "SELECT q.quote_id, q.atom_id, q.text, q.pinpoint_scheme, q.pinpoint_value, q.lane, q.case_id "
        "FROM corpus_fts JOIN quotes q ON q.quote_id = corpus_fts.quote_id "
        f"WHERE {' AND '.join(where)} LIMIT ?"
    )
    params.append(max_quotes)
    rows = con.execute(sql, params).fetchall()
    pack_id = "PACK_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    pack = {
        "pack_id": pack_id,
        "purpose": purpose,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {"lane": lane or "", "case_id": case_id or ""},
        "query": query,
        "quotes": [dict(r) for r in rows],
        "notes": []
    }
    pack_path = out_dir / f"{pack_id}.json"
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    snippets_path = out_dir / f"{pack_id}.snippets.txt"
    with snippets_path.open("w", encoding="utf-8") as f:
        for i, r in enumerate(rows, start=1):
            pp = r["pinpoint_value"] or "PINPOINT_MISSING"
            f.write(f"[{i}] {r['quote_id']} | {r['atom_id']} | {pp}\n{r['text']}\n\n")
    con.close()
    return pack_path
