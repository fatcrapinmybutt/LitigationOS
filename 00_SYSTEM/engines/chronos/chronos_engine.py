#!/usr/bin/env python3
"""CHRONOS — Chronological History Reconstruction and Ordered Narrative Operating System
Version 1.0.0 | LitigationOS Engine

CLI:
    python chronos_engine.py ingest <path> [--date-range 2023-01-01:2026-03-24]
    python chronos_engine.py build [--lane A|B|C|D|E|F|ALL]
    python chronos_engine.py gaps [--lane A] [--min-significance critical]
    python chronos_engine.py patterns [--type withholding|accusation|retaliation|judicial]
    python chronos_engine.py export [--format md|json|csv] [--lane ALL]
    python chronos_engine.py status
"""
import sys, os, re, json, sqlite3, hashlib, logging, argparse
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CHRONOS] %(levelname)s %(message)s")
log = logging.getLogger("chronos")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
SEPARATION_DATE = date(2025, 8, 8)
LANES = ["A", "B", "C", "D", "E", "F"]
LANE_CHOICES = LANES + ["ALL"]

LANE_REGISTRY = {
    "A": {"name": "Watson Custody", "case": "2024-001507-DC"},
    "B": {"name": "Shady Oaks Housing", "case": "2025-002760-CZ"},
    "C": {"name": "Convergence", "case": "multi-lane"},
    "D": {"name": "PPO / Protection Orders", "case": "2023-5907-PP"},
    "E": {"name": "Judicial Misconduct / JTC", "case": "2024-001507-DC"},
    "F": {"name": "Appellate", "case": "COA 366810"},
}
LANE_NAMES = {"A": "CUSTODY_CHRONOLOGY", "B": "HOUSING_CHRONOLOGY", "C": "CONVERGENCE_CHRONOLOGY",
              "D": "PPO_CHRONOLOGY", "E": "MISCONDUCT_CHRONOLOGY", "F": "APPELLATE_CHRONOLOGY"}
MEEK = {
    "A": re.compile(r"(?i)(custody|parenting|FOC|child|MCL\s+722|MCR\s+3\.20[67]|best.?interest|factor\s+[a-l])"),
    "B": re.compile(r"(?i)(shady.?oaks|homes.?of.?america|alden.?global|habitability|landlord|tenant|MCL\s+554|rent|mobile.?home)"),
    "D": re.compile(r"(?i)(PPO|protection.?order|contempt|MCL\s+600\.2950|MCR\s+3\.70[678]|bond|restrain)"),
    "E": re.compile(r"(?i)(bias|JTC|disqualif|MCR\s+2\.003|canon|judicial.?misconduct|superintend)"),
    "F": re.compile(r"(?i)(appell|COA|MSC|MCR\s+7\.|leave.?to.?appeal|standard.?of.?review|de.?novo)"),
}
DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "%Y-%m-%d"),
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), "%m/%d/%Y"),
    (re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b"), "%m-%d-%Y"),
    (re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b"), "%B %d %Y"),
    (re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})\b"), "%b %d %Y"),
]
ACTORS = [
    (re.compile(r"(?i)\b(Andrew\s+(?:J\.?\s+)?Pigors|Pigors|Plaintiff|Father|Dad)\b"), "Andrew Pigors"),
    (re.compile(r"(?i)\b(Emily\s+(?:A\.?\s+)?Watson|Watson|Defendant|Mother|Mom)\b"), "Emily Watson"),
    (re.compile(r"(?i)\b(Judge\s+McNeill|McNeill|Hon\.?\s+Jenny\s+L\.?\s+McNeill)\b"), "Hon. Jenny L. McNeill"),
    (re.compile(r"(?i)\b(Jennifer\s+Barnes|Barnes|P55406)\b"), "Jennifer Barnes (P55406)"),
    (re.compile(r"(?i)\b(Pamela\s+Rusco|Rusco|FOC)\b"), "Pamela Rusco (FOC)"),
    (re.compile(r"(?i)\b(Ronald\s+Berry|Ron\s+Berry)\b"), "Ronald Berry"),
    (re.compile(r"(?i)\bL\.?D\.?W\.?\b"), "L.D.W."),
]
CRITICAL_PERIODS = [
    ("2024-06-01", "2024-12-31"), ("2024-11-01", "2024-11-30"),
    ("2025-01-01", "2025-06-30"), ("2026-04-01", "2026-04-14"),
]


def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=120)
    for p in ["PRAGMA busy_timeout=60000", "PRAGMA journal_mode=WAL",
              "PRAGMA cache_size=-32000", "PRAGMA temp_store=MEMORY", "PRAGMA synchronous=NORMAL"]:
        conn.execute(p)
    conn.row_factory = sqlite3.Row
    return conn


def _init_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS chronos_events (
        event_id TEXT PRIMARY KEY, date_start TEXT NOT NULL, date_end TEXT,
        description TEXT NOT NULL, actors TEXT, source_path TEXT, source_type TEXT,
        lanes TEXT NOT NULL DEFAULT '[]', confidence REAL DEFAULT 0.8,
        days_since_separation INTEGER, content_hash TEXT,
        created_at TEXT DEFAULT (datetime('now')));
    CREATE INDEX IF NOT EXISTS idx_ce_date ON chronos_events(date_start);
    CREATE INDEX IF NOT EXISTS idx_ce_lanes ON chronos_events(lanes);
    CREATE TABLE IF NOT EXISTS chronos_links (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT, event_id_a TEXT NOT NULL,
        event_id_b TEXT NOT NULL, link_type TEXT NOT NULL, description TEXT,
        created_at TEXT DEFAULT (datetime('now')), UNIQUE(event_id_a, event_id_b, link_type));
    CREATE TABLE IF NOT EXISTS chronos_gaps (
        gap_id INTEGER PRIMARY KEY AUTOINCREMENT, gap_start TEXT NOT NULL,
        gap_end TEXT NOT NULL, gap_days INTEGER, lanes TEXT NOT NULL DEFAULT '[]',
        significance TEXT DEFAULT 'minor', acquisition_task TEXT,
        created_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS chronos_patterns (
        pattern_id INTEGER PRIMARY KEY AUTOINCREMENT, pattern_type TEXT NOT NULL,
        events_json TEXT NOT NULL, description TEXT, avg_interval_days REAL,
        confidence REAL DEFAULT 0.5, created_at TEXT DEFAULT (datetime('now')));
    """)
    conn.commit()


def _parse_iso(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _days_sep(d: str) -> int:
    dt = _parse_iso(d)
    return (dt - SEPARATION_DATE).days if dt else 0


class ChronosEngine:
    """Unified timeline engine for LitigationOS."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = _connect(db_path)
        _init_tables(self.conn)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    # ── 1. Event Ingester ────────────────────────────────────────────────
    def ingest(self, path: str, date_range: Optional[tuple] = None) -> dict:
        p = Path(path)
        files = list(p.rglob("*")) if p.is_dir() else [p]
        files = [f for f in files if f.is_file() and f.suffix.lower() in
                 (".txt", ".md", ".csv", ".json", ".log", ".jsonl")]
        stats = {"files_scanned": 0, "events_extracted": 0, "duplicates_skipped": 0}
        for f in files:
            stats["files_scanned"] += 1
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for ev in self._extract_events(text, str(f)):
                if date_range:
                    dt = _parse_iso(ev["date_start"])
                    if dt and not (date_range[0] <= dt <= date_range[1]):
                        continue
                if self.conn.execute("SELECT 1 FROM chronos_events WHERE date_start=? AND description=?",
                                     (ev["date_start"], ev["description"])).fetchone():
                    stats["duplicates_skipped"] += 1
                    continue
                ev["lanes"] = json.dumps(self._detect_lanes(ev["description"]))
                ev["days_since_separation"] = _days_sep(ev["date_start"])
                raw = f"{ev['date_start']}|{ev['description'][:80]}|{ev.get('source_path', '')}"
                ev["event_id"] = "CHR-" + hashlib.sha256(raw.encode()).hexdigest()[:12]
                ev["content_hash"] = hashlib.sha256(
                    f"{ev['date_start']}|{ev['description'][:120]}".encode()).hexdigest()[:16]
                self.conn.execute(
                    "INSERT OR IGNORE INTO chronos_events (event_id, date_start, date_end, "
                    "description, actors, source_path, source_type, lanes, confidence, "
                    "days_since_separation, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (ev["event_id"], ev["date_start"], ev.get("date_end"), ev["description"],
                     json.dumps(ev.get("actors", [])), ev.get("source_path"), ev.get("source_type"),
                     ev["lanes"], ev.get("confidence", 0.8), ev["days_since_separation"], ev["content_hash"]))
                stats["events_extracted"] += 1
        self.conn.commit()
        log.info("Ingested %d events from %d files (%d dups)", stats["events_extracted"],
                 stats["files_scanned"], stats["duplicates_skipped"])
        return stats

    def _extract_events(self, text: str, source_path: str) -> list:
        events, stype = [], Path(source_path).suffix.lstrip(".")
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 15:
                continue
            dates = self._parse_dates(line)
            if not dates:
                continue
            desc = line
            if len(line) < 60 and i + 1 < len(lines) and lines[i + 1].strip():
                desc = f"{line} {lines[i + 1].strip()}"
            events.append({"date_start": dates[0], "date_end": dates[1] if len(dates) > 1 else None,
                           "description": desc[:500], "actors": [n for p, n in ACTORS if p.search(line)],
                           "source_path": source_path, "source_type": stype,
                           "confidence": 0.9 if len(dates) == 1 else 0.7})
        return events

    def _parse_dates(self, text: str) -> list:
        found = []
        for pat, fmt in DATE_PATTERNS:
            for m in pat.finditer(text):
                try:
                    found.append(datetime.strptime(m.group(0).replace(",", ""), fmt).strftime("%Y-%m-%d"))
                except ValueError:
                    continue
        return sorted(set(found))

    @staticmethod
    def _detect_lanes(text: str) -> list:
        lanes = [l for l, p in MEEK.items() if p.search(text)]
        if len(lanes) > 1:
            lanes.append("C")
        return sorted(set(lanes)) or ["A"]

    # ── 2. Lane Tagger (batch re-tag) ───────────────────────────────────
    def retag_lanes(self) -> int:
        rows = self.conn.execute("SELECT event_id, description FROM chronos_events").fetchall()
        for r in rows:
            self.conn.execute("UPDATE chronos_events SET lanes=? WHERE event_id=?",
                              (json.dumps(self._detect_lanes(r["description"])), r["event_id"]))
        self.conn.commit()
        return len(rows)

    # ── 3. Master Chronology Builder ─────────────────────────────────────
    def build_chronology(self, lane: str = "ALL") -> list:
        if lane == "ALL":
            rows = self.conn.execute("SELECT * FROM chronos_events ORDER BY date_start, created_at").fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM chronos_events WHERE lanes LIKE ? ORDER BY date_start, created_at",
                                     (f'%"{lane}"%',)).fetchall()
        events = [dict(r) for r in rows]
        self._link_causal(events)
        self._find_clusters(events)
        return events

    def _link_causal(self, events: list) -> None:
        for i, a in enumerate(events):
            aa = set(json.loads(a.get("actors") or "[]"))
            for b in events[i + 1: i + 10]:
                if not aa & set(json.loads(b.get("actors") or "[]")):
                    continue
                da, db = _parse_iso(a["date_start"]), _parse_iso(b["date_start"])
                if da and db and abs((db - da).days) <= 3:
                    self.conn.execute("INSERT OR IGNORE INTO chronos_links (event_id_a, event_id_b, "
                                      "link_type, description) VALUES (?,?,'temporal_proximity','Within 3 days, shared actors')",
                                      (a["event_id"], b["event_id"]))
        self.conn.commit()

    def _find_clusters(self, events: list) -> None:
        if not events:
            return
        cs = 0
        for i in range(1, len(events)):
            d0, di = _parse_iso(events[cs]["date_start"]), _parse_iso(events[i]["date_start"])
            if not d0 or not di:
                continue
            if (di - d0).days > 7:
                if i - cs >= 3:
                    ids = [events[j]["event_id"] for j in range(cs, i)]
                    for cid in ids[1:]:
                        self.conn.execute("INSERT OR IGNORE INTO chronos_links (event_id_a, event_id_b, "
                                          "link_type, description) VALUES (?,?,'cluster','7-day cluster')",
                                          (ids[0], cid))
                cs = i
        self.conn.commit()

    # ── 4. Lane Chronology Generator ─────────────────────────────────────
    def build_lane_chronologies(self) -> dict:
        result = {}
        for lane, label in LANE_NAMES.items():
            events = self.build_chronology(lane)
            for ev in events:
                xrefs = self.conn.execute(
                    "SELECT e.event_id, e.date_start, e.lanes, substr(e.description,1,100) AS d "
                    "FROM chronos_links l JOIN chronos_events e ON e.event_id=l.event_id_b "
                    "WHERE l.event_id_a=? AND e.lanes NOT LIKE ?",
                    (ev["event_id"], f'%"{lane}"%')).fetchall()
                ev["cross_refs"] = [dict(r) for r in xrefs]
            result[label] = events
        return result

    # ── 5. Gap Detector ──────────────────────────────────────────────────
    def detect_gaps(self, lane: str = "ALL", min_days: int = 14) -> list:
        events = self.build_chronology(lane)
        if not events:
            return []
        self.conn.execute("DELETE FROM chronos_gaps WHERE lanes LIKE ?",
                          (f'%"{lane}"%' if lane != "ALL" else "%",))
        gaps = []
        for i in range(len(events) - 1):
            d1, d2 = _parse_iso(events[i]["date_start"]), _parse_iso(events[i + 1]["date_start"])
            if not d1 or not d2:
                continue
            delta = (d2 - d1).days
            if delta < min_days:
                continue
            sig = self._score_gap(d1, d2, delta)
            ltag = json.dumps([lane] if lane != "ALL" else ["ALL"])
            acq = self._acquisition_msg(d1, d2, sig)
            self.conn.execute("INSERT INTO chronos_gaps (gap_start,gap_end,gap_days,lanes,significance,"
                              "acquisition_task) VALUES (?,?,?,?,?,?)",
                              (d1.isoformat(), d2.isoformat(), delta, ltag, sig, acq))
            gaps.append({"gap_start": d1.isoformat(), "gap_end": d2.isoformat(),
                         "gap_days": delta, "significance": sig, "acquisition_task": acq})
        self.conn.commit()
        log.info("Detected %d gaps (lane=%s)", len(gaps), lane)
        return gaps

    @staticmethod
    def _score_gap(start: date, end: date, days: int) -> str:
        for cp_s, cp_e in CRITICAL_PERIODS:
            if start <= _parse_iso(cp_e) and end >= _parse_iso(cp_s):
                return "critical"
        return "critical" if days > 60 else ("moderate" if days > 30 else "minor")

    @staticmethod
    def _acquisition_msg(s: date, e: date, sig: str) -> str:
        r = f"{s.isoformat()} to {e.isoformat()}"
        if sig == "critical":
            return f"URGENT: Acquire records {r}. Check docket, FOC, email, texts."
        if sig == "moderate":
            return f"Review records {r}. Check personal records, social media, witnesses."
        return f"Low priority: check for activity {r}."

    # ── 6. Pattern Timeline ──────────────────────────────────────────────
    def detect_patterns(self, pattern_type: Optional[str] = None) -> list:
        types = [pattern_type] if pattern_type else ["accusation", "withholding", "retaliation", "judicial"]
        dispatch = {"accusation": self._pat_accusation, "withholding": self._pat_withholding,
                     "retaliation": self._pat_retaliation, "judicial": self._pat_judicial}
        results = []
        for t in types:
            if t in dispatch:
                results.extend(dispatch[t]())
        return results

    def _pat_accusation(self) -> list:
        return self._seq_pattern("accusation",
            re.compile(r"(?i)(accus|alleg|report|complain|CPS|police.?report)"),
            re.compile(r"(?i)(filed|motion|petition|order|PPO|hearing)"), 30)

    def _pat_retaliation(self) -> list:
        return self._seq_pattern("retaliation",
            re.compile(r"(?i)(pigors.?(?:filed|motion|petition)|plaintiff.?(?:filed|motion))"),
            re.compile(r"(?i)(watson.?(?:filed|motion|petition|PPO)|defendant.?(?:filed|motion))"), 14)

    def _pat_withholding(self) -> list:
        rows = self.conn.execute(
            "SELECT * FROM chronos_events WHERE description LIKE '%withh%' OR "
            "description LIKE '%denied%parent%' OR description LIKE '%no contact%' OR "
            "description LIKE '%refused%visit%' ORDER BY date_start").fetchall()
        return self._store_kw_pattern("withholding", rows, "Parenting time withholding episodes")

    def _pat_judicial(self) -> list:
        rows = self.conn.execute(
            "SELECT * FROM chronos_events WHERE (description LIKE '%McNeill%' OR "
            "description LIKE '%ruling%' OR description LIKE '%order%') AND "
            "actors LIKE '%McNeill%' ORDER BY date_start").fetchall()
        return self._store_kw_pattern("judicial", rows, "Judicial ruling clusters by Hon. McNeill")

    def _seq_pattern(self, ptype: str, kw_a, kw_b, max_gap: int) -> list:
        rows = self.conn.execute("SELECT * FROM chronos_events ORDER BY date_start").fetchall()
        pairs = []
        for ev in rows:
            if not kw_a.search(ev["description"]):
                continue
            da = _parse_iso(ev["date_start"])
            if not da:
                continue
            for ev2 in rows:
                if not kw_b.search(ev2["description"]):
                    continue
                db = _parse_iso(ev2["date_start"])
                if db and 0 < (db - da).days <= max_gap:
                    pairs.append({"trigger": ev["event_id"], "response": ev2["event_id"],
                                  "interval": (db - da).days})
        if not pairs:
            return []
        avg = sum(p["interval"] for p in pairs) / len(pairs)
        self.conn.execute("INSERT INTO chronos_patterns (pattern_type, events_json, description, "
                          "avg_interval_days, confidence) VALUES (?,?,?,?,?)",
                          (ptype, json.dumps(pairs), f"{ptype}: {len(pairs)} sequences, avg {avg:.1f} days",
                           avg, min(0.5 + len(pairs) * 0.1, 0.95)))
        self.conn.commit()
        return [{"type": ptype, "count": len(pairs), "avg_interval": avg}]

    def _store_kw_pattern(self, ptype: str, rows, desc: str) -> list:
        if len(rows) < 2:
            return []
        evs = [dict(r) for r in rows]
        intervals = []
        for i in range(len(evs) - 1):
            d1, d2 = _parse_iso(evs[i]["date_start"]), _parse_iso(evs[i + 1]["date_start"])
            if d1 and d2:
                intervals.append((d2 - d1).days)
        avg = sum(intervals) / len(intervals) if intervals else 0
        ids = [e["event_id"] for e in evs]
        self.conn.execute("INSERT INTO chronos_patterns (pattern_type, events_json, description, "
                          "avg_interval_days, confidence) VALUES (?,?,?,?,?)",
                          (ptype, json.dumps(ids), f"{desc}: {len(evs)} events, avg {avg:.0f} days apart",
                           avg, min(0.5 + len(evs) * 0.05, 0.95)))
        self.conn.commit()
        return [{"type": ptype, "count": len(evs), "avg_interval": avg}]

    # ── 7. Export ────────────────────────────────────────────────────────
    def export(self, fmt: str = "md", lane: str = "ALL") -> str:
        events = self.build_chronology(lane)
        if fmt == "json":
            return json.dumps(events, indent=2, default=str)
        if fmt == "csv":
            lines = ["event_id,date_start,date_end,description,actors,lanes,days_since_separation"]
            for e in events:
                d = e["description"].replace('"', '""')[:200]
                lines.append(f'"{e["event_id"]}","{e["date_start"]}","{e.get("date_end","")}","{d}",'
                             f'"{e.get("actors","")}","{e["lanes"]}",{e.get("days_since_separation",0)}')
            return "\n".join(lines)
        label = "MASTER" if lane == "ALL" else LANE_NAMES.get(lane, lane)
        hdr = f"# {label} CHRONOLOGY\n\nGenerated: {datetime.now():%Y-%m-%d %H:%M} | Events: {len(events)}\n"
        hdr += f"Separation date: {SEPARATION_DATE}\n\n| Date | DaySep | Description | Actors | Lanes |\n"
        hdr += "|------|--------|-------------|--------|-------|\n"
        for e in events:
            ac = ", ".join(json.loads(e.get("actors") or "[]"))
            ln = ", ".join(json.loads(e.get("lanes") or "[]"))
            hdr += f"| {e['date_start']} | {e.get('days_since_separation','')} | {e['description'][:100].replace('|','\\|')} | {ac} | {ln} |\n"
        return hdr

    # ── 8. Status ────────────────────────────────────────────────────────
    def status(self) -> dict:
        r = self.conn.execute("""SELECT
            (SELECT COUNT(*) FROM chronos_events) AS ec,
            (SELECT COUNT(*) FROM chronos_links) AS lc,
            (SELECT COUNT(*) FROM chronos_gaps) AS gc,
            (SELECT COUNT(*) FROM chronos_patterns) AS pc,
            (SELECT MIN(date_start) FROM chronos_events) AS mn,
            (SELECT MAX(date_start) FROM chronos_events) AS mx""").fetchone()
        lc = {l: self.conn.execute("SELECT COUNT(*) FROM chronos_events WHERE lanes LIKE ?",
              (f'%"{l}"%',)).fetchone()[0] for l in LANE_REGISTRY}
        return {"events": r["ec"], "links": r["lc"], "gaps": r["gc"], "patterns": r["pc"],
                "date_range": f"{r['mn'] or 'N/A'} → {r['mx'] or 'N/A'}",
                "days_since_separation": (date.today() - SEPARATION_DATE).days, "lanes": lc}


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(prog="chronos_engine",
         description="CHRONOS — Chronological History Reconstruction and Ordered Narrative OS")
    sp = ap.add_subparsers(dest="command", required=True)
    pi = sp.add_parser("ingest", help="Ingest events from files")
    pi.add_argument("path", help="File or directory to ingest")
    pi.add_argument("--date-range", help="YYYY-MM-DD:YYYY-MM-DD")
    pb = sp.add_parser("build", help="Build chronology")
    pb.add_argument("--lane", default="ALL", choices=LANE_CHOICES)
    pg = sp.add_parser("gaps", help="Detect evidence gaps")
    pg.add_argument("--lane", default="ALL", choices=LANE_CHOICES)
    pg.add_argument("--min-significance", default="minor", choices=["critical", "moderate", "minor"])
    pp = sp.add_parser("patterns", help="Detect behavioral patterns")
    pp.add_argument("--type", choices=["withholding", "accusation", "retaliation", "judicial"])
    pe = sp.add_parser("export", help="Export chronology")
    pe.add_argument("--format", default="md", choices=["md", "json", "csv"])
    pe.add_argument("--lane", default="ALL", choices=LANE_CHOICES)
    sp.add_parser("status", help="Show engine status")
    args = ap.parse_args()
    engine = ChronosEngine()
    try:
        if args.command == "ingest":
            dr = None
            if args.date_range:
                parts = args.date_range.split(":")
                dr = (_parse_iso(parts[0]), _parse_iso(parts[1])) if len(parts) == 2 else None
            print(json.dumps(engine.ingest(args.path, date_range=dr), indent=2))
        elif args.command == "build":
            evs = engine.build_chronology(args.lane)
            print(f"Built chronology: {len(evs)} events (lane={args.lane})")
            for e in evs[:20]:
                print(f"  {e['date_start']}  {e['description'][:80]}")
            if len(evs) > 20:
                print(f"  ... and {len(evs) - 20} more events")
        elif args.command == "gaps":
            md = {"critical": 30, "moderate": 14, "minor": 7}[args.min_significance]
            gaps = engine.detect_gaps(lane=args.lane, min_days=md)
            sr = {"minor": 0, "moderate": 1, "critical": 2}
            gaps = [g for g in gaps if sr.get(g["significance"], 0) >= sr.get(args.min_significance, 0)]
            print(f"Gaps detected: {len(gaps)}")
            for g in gaps:
                print(f"  [{g['significance'].upper()}] {g['gap_start']} → {g['gap_end']} ({g['gap_days']}d)")
                if g.get("acquisition_task"):
                    print(f"    → {g['acquisition_task']}")
        elif args.command == "patterns":
            pats = engine.detect_patterns(args.type)
            print(f"Patterns detected: {len(pats)}")
            for p in pats:
                print(f"  [{p['type'].upper()}] {p['count']} occurrences, avg {p['avg_interval']:.1f} days")
        elif args.command == "export":
            print(engine.export(fmt=args.format, lane=args.lane))
        elif args.command == "status":
            s = engine.status()
            print(f"CHRONOS Engine Status\n  Events: {s['events']}  Links: {s['links']}  "
                  f"Gaps: {s['gaps']}  Patterns: {s['patterns']}")
            print(f"  Date range: {s['date_range']}\n  Days since separation: {s['days_since_separation']}")
            print("  Events per lane:")
            for l, c in s["lanes"].items():
                print(f"    Lane {l} ({LANE_REGISTRY[l]['name']}): {c}")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
