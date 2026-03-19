from __future__ import annotations
import sqlite3, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

def _score_quote(row: sqlite3.Row, purpose: str) -> int:
    text = (row["text"] or "").lower()
    score = 0
    # Lightweight purpose-aware scoring
    if purpose == "rebuttal_map":
        if any(k in text for k in ["liar","crazy","threat","unstable","danger","violent","violation","harass"]):
            score += 10
    if purpose == "contradiction_map":
        if any(k in text for k in ["did not","never","not ","no "]):
            score += 6
    if any(k in text for k in ["order","hearing","court","judge","mcneill","ppo","custody","parenting time","shady oaks"]):
        score += 4
    return score

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
        "SELECT q.quote_id, q.atom_id, q.text, q.pinpoint_scheme, q.pinpoint_value, q.page_hint, q.lane, q.case_id "
        "FROM corpus_fts JOIN quotes q ON q.quote_id = corpus_fts.quote_id "
        f"WHERE {' AND '.join(where)} LIMIT ?"
    )
    # Pull more than needed, then score locally
    pull_limit = max(max_quotes * 3, max_quotes)
    rows = con.execute(sql, params + [pull_limit]).fetchall()
    ranked = sorted(rows, key=lambda r: _score_quote(r, purpose), reverse=True)[:max_quotes]

    event_rows = con.execute(
        "SELECT event_id, action, when_event_raw, truth_tag FROM events WHERE lane=? AND (?='' OR case_id=?) LIMIT 200",
        (lane or "", case_id or "", case_id or "")
    ).fetchall() if lane else []

    pack_id = "PACK_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    pack = {
        "pack_id": pack_id,
        "purpose": purpose,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {"lane": lane or "", "case_id": case_id or ""},
        "query": query,
        "quotes": [dict(r) for r in ranked],
        "events": [dict(r) for r in event_rows],
        "notes": [],
    }
    pack_path = out_dir / f"{pack_id}.json"
    pack_path.write_text(json.dumps(pack, indent=2), encoding="utf-8")

    snippets_path = out_dir / f"{pack_id}.snippets.txt"
    with snippets_path.open("w", encoding="utf-8") as f:
        for i, r in enumerate(ranked, start=1):
            pp = r["pinpoint_value"] or "PINPOINT_MISSING"
            pg = f" page={r['page_hint']}" if r["page_hint"] else ""
            f.write(f"[{i}] {r['quote_id']} | {r['atom_id']} | {pp}{pg}\n{r['text']}\n\n")
    con.close()
    return pack_path
