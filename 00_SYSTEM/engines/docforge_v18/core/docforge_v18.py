
#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, os, re, sqlite3, sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

APP_NAME = "LITIGATIONOS_MI_APPELLATE_DOCFORGE_MEEK1234_V18_BULKGRAFT_LINKLOCK"
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
DB_PATH = RUNTIME / "docforge_v18.sqlite3"
PACKS_ROOT = ROOT / "output" / "CourtPacks"
SAMPLES = ROOT / "sample_inputs"

def utcnow() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def ensure_runtime() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    PACKS_ROOT.mkdir(parents=True, exist_ok=True)

def connect() -> sqlite3.Connection:
    ensure_runtime()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def initdb(_: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS authority_triples(
        id INTEGER PRIMARY KEY,
        authority_family TEXT NOT NULL,
        citation TEXT NOT NULL,
        proposition TEXT NOT NULL,
        source_url TEXT,
        pinpoint TEXT,
        official_text_exact TEXT,
        graft_status TEXT NOT NULL DEFAULT 'UNRESOLVED',
        resolver_recipe TEXT,
        lane TEXT,
        created_at TEXT NOT NULL
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_authority_unique
      ON authority_triples(authority_family, citation, proposition);

    CREATE TABLE IF NOT EXISTS transcript_lines(
        id INTEGER PRIMARY KEY,
        transcript_id TEXT NOT NULL,
        page INTEGER NOT NULL,
        line_start INTEGER NOT NULL,
        line_end INTEGER NOT NULL,
        speaker TEXT,
        text TEXT NOT NULL,
        lane TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS ix_transcript_page ON transcript_lines(transcript_id, page, line_start);

    CREATE TABLE IF NOT EXISTS order_findings(
        id INTEGER PRIMARY KEY,
        finding_id TEXT NOT NULL UNIQUE,
        order_id TEXT NOT NULL,
        finding_text TEXT NOT NULL,
        lane TEXT,
        adverse_to TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS transcript_quote_links(
        id INTEGER PRIMARY KEY,
        finding_id TEXT,
        transcript_id TEXT,
        page INTEGER,
        line_start INTEGER,
        line_end INTEGER,
        speaker TEXT,
        quote_text TEXT,
        match_score REAL,
        proposition_cluster TEXT,
        lane TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS deadline_events(
        id INTEGER PRIMARY KEY,
        vehicle TEXT NOT NULL,
        event_id TEXT NOT NULL UNIQUE,
        lane TEXT,
        anchor_entered TEXT,
        anchor_signed TEXT,
        anchor_served TEXT,
        anchor_recorded TEXT,
        rule_citation TEXT,
        rule_label TEXT,
        due_entered TEXT,
        due_signed TEXT,
        due_served TEXT,
        due_recorded TEXT,
        notes TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS contradiction_pairs(
        id INTEGER PRIMARY KEY,
        proposition_cluster TEXT NOT NULL,
        lane_a TEXT,
        lane_b TEXT,
        source_a TEXT,
        source_b TEXT,
        text_a TEXT,
        text_b TEXT,
        polarity_a TEXT,
        polarity_b TEXT,
        score REAL,
        created_at TEXT NOT NULL
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
      transcript_id, lane, speaker, text
    );
    """)
    con.commit()
    con.close()
    print(f"INITDB_OK {DB_PATH}")

def _det_source_url(family: str, citation: str) -> str:
    fam = family.upper()
    if fam == "MCL":
        # simple deterministic legislature pattern; normalized path may vary, keep root+section
        sec = citation.upper().replace("MCL", "").strip()
        sec = sec.replace(" ", "")
        return f"https://www.legislature.mi.gov/doc.aspx?mcl-{sec}"
    if fam in {"MCR","MRE","SCAO"}:
        return "https://www.courts.michigan.gov/"
    if fam in {"JTC","JTC_CANON","MJI"}:
        return "https://www.courts.michigan.gov/"
    return "https://www.courts.michigan.gov/"

def ingest_official_text(args: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    path = Path(args.path)
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            fam = row["authority_family"].upper()
            citation = row["citation"]
            proposition = row["proposition"]
            source_url = row.get("source_url") or _det_source_url(fam, citation)
            pinpoint = row.get("pinpoint")
            text_exact = row.get("official_text_exact")
            graft_status = row.get("graft_status") or ("RESOLVED_VERIFIED" if text_exact and pinpoint else "PARTIAL")
            resolver_recipe = row.get("resolver_recipe") or f"Resolve exact text + pinpoint from official MI source for {citation}"
            lane = row.get("lane")
            cur.execute("""
            INSERT INTO authority_triples(authority_family,citation,proposition,source_url,pinpoint,official_text_exact,graft_status,resolver_recipe,lane,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(authority_family,citation,proposition) DO UPDATE SET
              source_url=excluded.source_url,
              pinpoint=COALESCE(excluded.pinpoint,authority_triples.pinpoint),
              official_text_exact=COALESCE(excluded.official_text_exact,authority_triples.official_text_exact),
              graft_status=CASE
                WHEN excluded.graft_status='RESOLVED_VERIFIED' THEN 'RESOLVED_VERIFIED'
                WHEN authority_triples.graft_status='RESOLVED_VERIFIED' THEN 'RESOLVED_VERIFIED'
                ELSE excluded.graft_status END,
              resolver_recipe=COALESCE(excluded.resolver_recipe,authority_triples.resolver_recipe),
              lane=COALESCE(excluded.lane,authority_triples.lane)
            """, (fam,citation,proposition,source_url,pinpoint,text_exact,graft_status,resolver_recipe,lane,utcnow()))
            count += 1
    con.commit()
    con.close()
    print(f"INGEST_OFFICIAL_TEXT_OK rows={count}")

def transcript_link(args: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    path = Path(args.path)
    inserted = 0
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            tid = row["transcript_id"]
            page = int(row["page"])
            ls = int(row["line_start"])
            le = int(row["line_end"])
            speaker = row.get("speaker") or ""
            text = row["text"].strip()
            lane = row.get("lane") or infer_lane(text)
            cur.execute("""INSERT INTO transcript_lines(transcript_id,page,line_start,line_end,speaker,text,lane,created_at)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (tid,page,ls,le,speaker,text,lane,utcnow()))
            cur.execute("""INSERT INTO transcript_fts(transcript_id,lane,speaker,text) VALUES(?,?,?,?)""",
                        (tid,lane,speaker,text))
            inserted += 1
    con.commit()
    con.close()
    print(f"TRANSCRIPT_LINK_OK rows={inserted}")

def ingest_order_findings(args: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    path = Path(args.path)
    count = 0
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            cur.execute("""INSERT OR REPLACE INTO order_findings(finding_id,order_id,finding_text,lane,adverse_to,created_at)
                           VALUES(?,?,?,?,?,?)""",
                        (row["finding_id"], row["order_id"], row["finding_text"], row.get("lane") or infer_lane(row["finding_text"]),
                         row.get("adverse_to") or "UNKNOWN", utcnow()))
            count += 1
    con.commit()
    con.close()
    print(f"INGEST_ORDER_FINDINGS_OK rows={count}")

def infer_lane(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["rent","lease","sewage","utility","housing","eviction","mhp","shady oaks"]):
        return "MEEK1"
    if any(k in t for k in ["parenting", "custody", "foc", "child", "lincoln"]):
        return "MEEK2"
    if any(k in t for k in ["ppo", "show cause", "harass", "stalk", "contact violation", "contempt"]):
        return "MEEK3"
    if any(k in t for k in ["judge", "bias", "canon", "jtc", "recusal"]):
        return "MEEK4"
    return "UNKNOWN"

PROP_CLUSTERS = {
    "PT_SUSPENSION": ["parenting time", "suspend", "suspension", "lincoln"],
    "PPO_CONTACT": ["ppo", "show cause", "contact", "violation", "harass", "stalk"],
    "CONTEMPT_JAIL": ["contempt", "jail", "sentence", "days"],
    "MENTAL_HEALTH_EVAL": ["healthwest", "evaluation", "assessment", "mental health"],
    "HOUSING_UTILITIES": ["rent", "utility", "sewage", "housing", "lease", "mhp", "shady oaks"],
    "JUDICIAL_BIAS": ["judge", "bias", "canon", "recusal", "jtc"]
}

NEG_WORDS = {"not","no","denied","deny","false","never","without","lacked","missing","refused","refusal"}
POS_WORDS = {"ordered","found","determined","violated","harassed","stalked","suspended","granted","required","threat"}

def cluster_text(text: str) -> str:
    t = text.lower()
    for c, words in PROP_CLUSTERS.items():
        if any(w in t for w in words):
            return c
    return "GENERAL"

def polarity(text: str) -> str:
    toks = set(re.findall(r"[a-zA-Z']+", text.lower()))
    n = len(toks & NEG_WORDS)
    p = len(toks & POS_WORDS)
    if n > p:
        return "NEG"
    if p > n:
        return "POS"
    return "NEUTRAL"

def similarity(a: str, b: str) -> float:
    sa = set(re.findall(r"[a-zA-Z0-9']+", a.lower()))
    sb = set(re.findall(r"[a-zA-Z0-9']+", b.lower()))
    if not sa or not sb:
        return 0.0
    return len(sa & sb)/len(sa | sb)

def link_order_findings(_: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    findings = cur.execute("SELECT * FROM order_findings ORDER BY id").fetchall()
    links = 0
    for f in findings:
        cluster = cluster_text(f["finding_text"])
        q = "SELECT rowid, transcript_id, lane, speaker, text FROM transcript_fts WHERE transcript_fts MATCH ? LIMIT 50"
        terms = " ".join([w for w in re.findall(r"[A-Za-z]{4,}", f["finding_text"])[:6]]) or "court"
        rows = cur.execute(q, (terms,)).fetchall()
        best = []
        for r in rows:
            score = similarity(f["finding_text"], r["text"])
            if score >= 0.08:
                best.append((score, r))
        best.sort(key=lambda x: x[0], reverse=True)
        for score, r in best[:3]:
            # resolve page/line from transcript_lines by matching text and transcript_id
            tl = cur.execute("""SELECT page,line_start,line_end,speaker,text,lane FROM transcript_lines
                                WHERE transcript_id=? AND text=? LIMIT 1""",
                             (r["transcript_id"], r["text"])).fetchone()
            if not tl:
                continue
            cur.execute("""INSERT INTO transcript_quote_links(finding_id,transcript_id,page,line_start,line_end,speaker,quote_text,match_score,proposition_cluster,lane,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (f["finding_id"], tl["transcript_id"], tl["page"], tl["line_start"], tl["line_end"], tl["speaker"], tl["text"],
                         round(score,4), cluster, tl["lane"], utcnow()))
            links += 1
    con.commit()
    con.close()
    print(f"LINK_ORDER_FINDINGS_OK links={links}")

def lock_deadlines(args: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    path = Path(args.path)
    count = 0
    with path.open("r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            vehicle = row["vehicle"]
            lane = row.get("lane") or "UNKNOWN"
            event_id = row["event_id"]
            rule_citation = row.get("rule_citation") or ""
            rule_label = row.get("rule_label") or ""
            offsets = {
                "entered": _safe_int(row.get("offset_days_entered")),
                "signed": _safe_int(row.get("offset_days_signed")),
                "served": _safe_int(row.get("offset_days_served")),
                "recorded": _safe_int(row.get("offset_days_recorded")),
            }
            anchors = {
                "entered": row.get("anchor_entered") or "",
                "signed": row.get("anchor_signed") or "",
                "served": row.get("anchor_served") or "",
                "recorded": row.get("anchor_recorded") or "",
            }
            dues = {}
            missing = []
            for k,v in anchors.items():
                if v and offsets[k] is not None:
                    dues[k] = add_days(v, offsets[k])
                elif v and offsets[k] is None:
                    dues[k] = ""
                    missing.append(f"RULE_MISSING:{k}")
                elif (not v) and offsets[k] is not None:
                    dues[k] = ""
                    missing.append(f"MISSING_ANCHOR:{k}")
                else:
                    dues[k] = ""
            status = "LOCKED" if not missing else "PARTIAL"
            notes = ";".join(missing) if missing else "OK"
            cur.execute("""INSERT OR REPLACE INTO deadline_events(vehicle,event_id,lane,anchor_entered,anchor_signed,anchor_served,anchor_recorded,rule_citation,rule_label,
                           due_entered,due_signed,due_served,due_recorded,notes,status,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (vehicle,event_id,lane,anchors["entered"],anchors["signed"],anchors["served"],anchors["recorded"],rule_citation,rule_label,
                         dues["entered"],dues["signed"],dues["served"],dues["recorded"],notes,status,utcnow()))
            count += 1
    con.commit()
    con.close()
    print(f"LOCK_DEADLINES_OK rows={count}")

def _safe_int(v):
    if v is None or v == "":
        return None
    return int(v)

def add_days(iso_date: str, days: int) -> str:
    d = dt.date.fromisoformat(iso_date)
    return (d + dt.timedelta(days=days)).isoformat()

def consolidate_contradictions(_: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    cur.execute("DELETE FROM contradiction_pairs")
    # Build source texts from order findings + transcript quote links
    items = []
    for r in cur.execute("SELECT finding_id AS src, lane, finding_text AS text FROM order_findings"):
        items.append({"source": f"ORDER:{r['src']}", "lane": r["lane"], "text": r["text"]})
    for r in cur.execute("SELECT id, lane, quote_text AS text FROM transcript_quote_links"):
        items.append({"source": f"TXLINK:{r['id']}", "lane": r["lane"], "text": r["text"]})
    out = 0
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            a, b = items[i], items[j]
            ca, cb = cluster_text(a["text"]), cluster_text(b["text"])
            if ca != cb or ca == "GENERAL":
                continue
            pa, pb = polarity(a["text"]), polarity(b["text"])
            if pa == pb or "NEUTRAL" in {pa,pb}:
                continue
            sc = similarity(a["text"], b["text"])
            if sc < 0.07:
                continue
            cur.execute("""INSERT INTO contradiction_pairs(proposition_cluster,lane_a,lane_b,source_a,source_b,text_a,text_b,polarity_a,polarity_b,score,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (ca, a["lane"], b["lane"], a["source"], b["source"], a["text"], b["text"], pa, pb, round(sc,4), utcnow()))
            out += 1
    con.commit()
    con.close()
    print(f"CONSOLIDATE_CONTRADICTIONS_OK pairs={out}")

def resolve_authority(_: argparse.Namespace) -> None:
    # upgrades statuses where pinpoint+text present
    con = connect()
    cur = con.cursor()
    cur.execute("""UPDATE authority_triples
                   SET graft_status='RESOLVED_VERIFIED'
                   WHERE COALESCE(pinpoint,'')<>'' AND COALESCE(official_text_exact,'')<>''""")
    cur.execute("""UPDATE authority_triples
                   SET graft_status='PARTIAL'
                   WHERE graft_status='UNRESOLVED' AND (COALESCE(pinpoint,'')<>'' OR COALESCE(official_text_exact,'')<>'')""")
    n = cur.rowcount
    con.commit()
    con.close()
    print(f"RESOLVE_AUTHORITY_OK updated={n}")

def _write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def courtpack(args: argparse.Namespace) -> None:
    con = connect()
    cur = con.cursor()
    lane = args.lane or "ALL"
    vehicle = args.vehicle or "MI_APPELLATE_DOCFORGE"
    run_id = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    pack_dir = PACKS_ROOT / lane / vehicle / run_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    lane_filter_sql = "" if lane == "ALL" else "WHERE lane = ?"
    lane_param = [] if lane == "ALL" else [lane]

    auth_rows = cur.execute(f"SELECT * FROM authority_triples {lane_filter_sql} ORDER BY authority_family,citation", lane_param).fetchall()
    tx_rows = cur.execute(f"SELECT * FROM transcript_quote_links {lane_filter_sql} ORDER BY proposition_cluster,match_score DESC", lane_param).fetchall()
    dl_rows = cur.execute(f"SELECT * FROM deadline_events {lane_filter_sql} ORDER BY vehicle,event_id", lane_param).fetchall()
    c_rows = cur.execute("""
        SELECT * FROM contradiction_pairs
        {} ORDER BY proposition_cluster, score DESC
    """.format("" if lane=="ALL" else "WHERE lane_a = ? OR lane_b = ?"), lane_param if lane=="ALL" else [lane,lane]).fetchall()

    # CASE_STATE
    _write_md(pack_dir/"CASE_STATE.md", "\n".join([
        "# CASE_STATE",
        f"- run_id: {run_id}",
        f"- lane_scope: {lane}",
        f"- authority_rows: {len(auth_rows)}",
        f"- transcript_links: {len(tx_rows)}",
        f"- deadline_events: {len(dl_rows)}",
        f"- contradictions: {len(c_rows)}",
        "- status: DRAFT_DROPIN_READY"
    ]))

    # AuthorityTriples
    lines = ["# AuthorityTriples", "|Family|Citation|Proposition|Pinpoint|Status|Source|", "|---|---|---|---|---|---|"]
    for r in auth_rows:
        lines.append(f"|{r['authority_family']}|{r['citation']}|{(r['proposition'] or '').replace('|','/')}|{r['pinpoint'] or ''}|{r['graft_status']}|{r['source_url'] or ''}|")
    _write_md(pack_dir/"AuthorityTriples.md", "\n".join(lines))
    (pack_dir/"AuthorityTriples.json").write_text(json.dumps([dict(r) for r in auth_rows], indent=2), encoding='utf-8')

    # Transcript SoF pins
    lines = ["# Transcript_StatementOfFacts_Pins"]
    for r in tx_rows:
        lines.append(f"- [{r['proposition_cluster']}] {r['transcript_id']} p.{r['page']} l.{r['line_start']}-{r['line_end']} ({r['speaker'] or 'UNK'}): {r['quote_text']}")
    _write_md(pack_dir/"Transcript_StatementOfFacts_Pins.md", "\n".join(lines))

    # Deadlines
    lines = ["# Deadlines", "|Vehicle|Event|Rule|Entered|Due(Entered)|Signed|Due(Signed)|Served|Due(Served)|Status|Notes|", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in dl_rows:
        lines.append(f"|{r['vehicle']}|{r['event_id']}|{r['rule_citation'] or r['rule_label'] or ''}|{r['anchor_entered'] or ''}|{r['due_entered'] or ''}|{r['anchor_signed'] or ''}|{r['due_signed'] or ''}|{r['anchor_served'] or ''}|{r['due_served'] or ''}|{r['status']}|{r['notes'] or ''}|")
    _write_md(pack_dir/"Deadlines.md", "\n".join(lines))

    # ContradictionMap
    lines = ["# ContradictionMap"]
    for r in c_rows:
        lines.append(f"## {r['proposition_cluster']} ({r['score']})")
        lines.append(f"- A [{r['lane_a']}] {r['source_a']} ({r['polarity_a']}): {r['text_a']}")
        lines.append(f"- B [{r['lane_b']}] {r['source_b']} ({r['polarity_b']}): {r['text_b']}")
    _write_md(pack_dir/"ContradictionMap.md", "\n".join(lines))
    (pack_dir/"ContradictionMap.json").write_text(json.dumps([dict(r) for r in c_rows], indent=2), encoding='utf-8')

    # ContextPack + VehicleMap + Validation + SBNA + DRAFT blocks
    _write_md(pack_dir/"ContextPack.md", "\n".join([
        "# ContextPack",
        "- MI-first authority routing active",
        "- Originals immutable / derived append-only",
        "- No SHA-256 default; IdentityKeyV1 provenance rail",
        f"- Lane scope: {lane}",
        "- Unknowns converted to acquisition tasks"
    ]))
    _write_md(pack_dir/"VehicleMap.md", "\n".join([
        "# VehicleMap",
        f"- Lane: {lane}",
        "- Trial corrective motions (if applicable)",
        "- COA claim of appeal / delayed / original action routes",
        "- MSC app leave / superintending pathways (when ripe)",
        "- JTC complaint narrative lane (MEEK4)",
        "- Exact vehicle selection remains rule/date-dependent; see Deadlines + AuthorityTriples"
    ]))
    red_flags = []
    if not any(r["graft_status"] == "RESOLVED_VERIFIED" for r in auth_rows):
        red_flags.append("No RESOLVED_VERIFIED authority texts/pinpoints yet.")
    if len(tx_rows) == 0:
        red_flags.append("No transcript quote links for statement-of-facts.")
    if any(r["status"] != "LOCKED" for r in dl_rows):
        red_flags.append("Some deadlines are PARTIAL due to missing anchors or rule offsets.")
    _write_md(pack_dir/"Validation_RedTeam.md", "\n".join(["# Validation_RedTeam"] + [f"- {x}" for x in (red_flags or ["No critical blockers detected in this synthetic run."])]))
    _write_md(pack_dir/"SBNA.md", "\n".join([
        "# SBNA",
        "1. Promote authority grafts to RESOLVED_VERIFIED with exact official text + pinpoint.",
        "2. Expand transcript/order finding link coverage for adverse findings.",
        "3. Lock missing deadline anchors (entered/signed/served) from stamped orders and proofs of service.",
        "4. Compile lane-specific COA/MSC/JTC filing packets."
    ]))
    _write_md(pack_dir/"DRAFT_BLOCKS_DROPIN.md", "\n".join([
        "# DRAFT_BLOCKS_DROPIN",
        "## Background",
        "- This matter arises from a pattern of proceedings spanning MEEK lanes, with overlapping factual and procedural predicates.",
        "## Statement of Facts",
        "- Use Transcript_StatementOfFacts_Pins and Quote IDs; do not recite unsupported facts.",
        "## Argument",
        "- Route by VehicleMap + AuthorityTriples; cite exact MI authority + pinpoints only.",
        "## Relief",
        "- Tailor to selected vehicle; include proposed order and service checklist."
    ]))
    _write_md(pack_dir/"ServiceChecklist.md", "\n".join([
        "# ServiceChecklist",
        "- Identify service method under governing rule.",
        "- Preserve proof of service artifact and service date for deadline locking.",
        "- Add served anchor into deadline_events if not yet present."
    ]))

    manifest = {
        "app": APP_NAME,
        "generated_at_utc": utcnow(),
        "lane": lane,
        "vehicle": vehicle,
        "run_id": run_id,
        "counts": {
            "authority_rows": len(auth_rows),
            "transcript_links": len(tx_rows),
            "deadline_events": len(dl_rows),
            "contradictions": len(c_rows)
        },
        "files": sorted([p.name for p in pack_dir.iterdir()])
    }
    (pack_dir/"PACK_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    con.close()
    print(f"COURTPACK_OK {pack_dir}")

def full_cycle(args: argparse.Namespace) -> None:
    initdb(args)
    ingest_official_text(argparse.Namespace(path=str(SAMPLES/"official_text_grafts.jsonl")))
    resolve_authority(args)
    transcript_link(argparse.Namespace(path=str(SAMPLES/"transcript_lines.csv")))
    ingest_order_findings(argparse.Namespace(path=str(SAMPLES/"order_findings.csv")))
    link_order_findings(args)
    lock_deadlines(argparse.Namespace(path=str(SAMPLES/"deadline_events.csv")))
    consolidate_contradictions(args)
    for lane in ["MEEK1","MEEK2","MEEK3","MEEK4","ALL"]:
        courtpack(argparse.Namespace(lane=lane, vehicle="MI_DOCFORGE_V18"))
    print("FULL_CYCLE_OK")

def autopilot(args: argparse.Namespace) -> None:
    # simple multi-cycle: re-run consolidation and courtpack twice to simulate convergence loops
    full_cycle(args)
    for _ in range(2):
        consolidate_contradictions(args)
        for lane in ["MEEK1","MEEK2","MEEK3","MEEK4","ALL"]:
            courtpack(argparse.Namespace(lane=lane, vehicle="MI_DOCFORGE_V18_AUTOPILOT"))
    print("AUTOPILOT_OK")

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=APP_NAME)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("initdb")
    sp = sub.add_parser("ingest-official-text"); sp.add_argument("--path", required=True)
    sub.add_parser("resolve-authority")
    sp = sub.add_parser("transcript-link"); sp.add_argument("--path", required=True)
    sp = sub.add_parser("ingest-order-findings"); sp.add_argument("--path", required=True)
    sub.add_parser("link-order-findings")
    sp = sub.add_parser("lock-deadlines"); sp.add_argument("--path", required=True)
    sub.add_parser("consolidate-contradictions")
    sp = sub.add_parser("courtpack"); sp.add_argument("--lane", default="ALL"); sp.add_argument("--vehicle", default="MI_DOCFORGE_V18")
    sub.add_parser("full-cycle")
    sub.add_parser("autopilot")
    return p

def main() -> None:
    p = parser()
    args = p.parse_args()
    cmd = args.cmd.replace("-", "_")
    fn = globals().get(cmd)
    if not fn:
        print(f"UNKNOWN_CMD {args.cmd}", file=sys.stderr); sys.exit(2)
    fn(args)

if __name__ == "__main__":
    main()
