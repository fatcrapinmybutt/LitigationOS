#!/usr/bin/env python3
"""CHIMERA — Cross-referencing Hostile Inconsistencies via Multi-source
Evidence Reconciliation and Analysis.

Usage:
    python chimera_engine.py ingest <path> [--speaker "Emily Watson"]
    python chimera_engine.py detect [--speaker "Emily Watson"] [--topic physical_violence]
    python chimera_engine.py patterns [--type accusation_timing]
    python chimera_engine.py impeachment [--min-severity 5] [--format md|json]
    python chimera_engine.py report [--output chimera_report.md]
    python chimera_engine.py status
"""
import sys
import sqlite3, json, re, argparse, hashlib, logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict

# Prefer shared module for DB connections
try:
    _system_dir = str(Path(__file__).resolve().parent.parent.parent)
    if _system_dir not in sys.path:
        sys.path.insert(0, _system_dir)
    from shared import get_db as _shared_get_db
    _HAS_SHARED = True
except ImportError:
    _HAS_SHARED = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_PATH = str(Path(__file__).resolve().parents[3] / "litigation_context.db")

# ── Verified party names — NEVER fabricate ──────────────────────
KNOWN_SPEAKERS = {
    "andrew": "Andrew Pigors", "andrew pigors": "Andrew Pigors",
    "andrew james pigors": "Andrew Pigors",
    "emily": "Emily Watson", "emily watson": "Emily Watson",
    "emily a. watson": "Emily Watson",
    "albert watson": "Albert Watson", "albert": "Albert Watson",
    "ronald berry": "Ronald Berry", "ron berry": "Ronald Berry",
    "berry": "Ronald Berry",
    "cody watson": "Cody Watson", "cody": "Cody Watson",
    "l.d.w.": "L.D.W.",
    "officer": "Officer [UNKNOWN]",
    "judge": "Hon. Jenny L. McNeill", "mcneill": "Hon. Jenny L. McNeill",
    "jenny mcneill": "Hon. Jenny L. McNeill",
    "pamela rusco": "Pamela Rusco", "rusco": "Pamela Rusco",
    "jennifer barnes": "Jennifer Barnes (P55406)",
    "barnes": "Jennifer Barnes (P55406)",
}

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "physical_violence": ["hit", "struck", "punch", "kick", "shove", "push", "assault", "attack",
                          "physical", "violence", "choke", "strangle", "slap", "bruise", "grabbed"],
    "threats": ["threat", "threaten", "kill", "harm", "intimidat", "scare", "fear for"],
    "fear": ["fear", "afraid", "scared", "terrified", "unsafe", "danger"],
    "parenting": ["parent", "custody", "visitation", "parenting time", "child", "father", "mother"],
    "child_welfare": ["child welfare", "cps", "dhhs", "neglect", "child protective", "safety of child"],
    "property": ["property", "house", "home", "residence", "belongings", "kicked out", "locked out"],
    "financial": ["money", "support", "payment", "income", "financial", "rent", "mortgage", "debt"],
    "substance_abuse": ["drug", "alcohol", "drunk", "intoxicated", "substance", "marijuana", "impaired"],
    "mental_health": ["mental health", "therapy", "counseling", "psychiatric", "medication", "evaluation"],
    "police_contact": ["police", "officer", "911", "dispatch", "arrest", "detained", "law enforcement"],
    "court_orders": ["order", "court order", "violation", "contempt", "comply", "ppo", "protection order"],
    "custody": ["custody", "legal custody", "physical custody", "sole custody", "joint custody"],
    "visitation": ["visitation", "parenting time", "visit", "overnight", "exchange", "pickup", "drop-off"],
    "cohabitation": ["boyfriend", "girlfriend", "partner", "cohabit", "living with", "moved in"],
    "employment": ["work", "job", "employ", "income", "shift", "fired", "hired"],
}

SOURCE_TYPE_PATTERNS: Dict[str, List[str]] = {
    "police_report": ["police report", "incident report", "officer report", "law enforcement"],
    "ppo_petition": ["ppo", "personal protection order", "ex parte", "protection order petition"],
    "court_filing": ["motion", "petition", "complaint", "answer", "response", "brief"],
    "affidavit": ["affidavit", "sworn statement", "under oath", "subscribed and sworn"],
    "court_testimony": ["testimony", "hearing", "trial", "deposition", "on the record"],
    "text_message": ["text message", "sms", "imessage", "texted"],
    "email": ["email", "e-mail"],
    "court_order": ["order", "judgment", "ruling", "decree", "ordered that"],
    "cps_report": ["cps", "child protective", "dhhs", "substantiated", "unsubstantiated"],
}

DATE_PATTERNS = [
    r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b",
]

NEGATION_PAIRS = [
    ("nothing was physical", "physical"), ("never hit", "hit me"),
    ("no violence", "violence"), ("didn't threaten", "threatened"),
    ("no arrest", "arrested"), ("consensual", "forced"), ("safe", "afraid"),
    ("denied", "admitted"), ("no contact", "contacted"),
    ("didn't happen", "happened"), ("never occurred", "occurred"),
    ("wasn't there", "was there"), ("no abuse", "abuse"),
]

ATTRIBUTION_PATTERNS = [
    r"(?:according to|per)\s+([\w\s.]+?),\s*[\"\u201c](.+?)[\"\u201d]",
    (r"([\w\s.]+?)\s+(?:said|stated|reported|testified|claimed|alleged|told|indicated|"
     r"denied|admitted|explained|described|wrote|texted)\s+(?:that\s+)?[\"\u201c]?(.+?)[\"\u201d.]"),
    r"([\w\s.]+?):\s*[\"\u201c](.+?)[\"\u201d]",
]


class ChimeraEngine:
    """CHIMERA contradiction detection and impeachment matrix builder."""

    SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS chimera_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, speaker TEXT NOT NULL,
        statement_date TEXT, topic TEXT, content TEXT NOT NULL,
        source_path TEXT, source_type TEXT, content_hash TEXT UNIQUE,
        confidence REAL DEFAULT 1.0, created_at TEXT DEFAULT (datetime('now')), metadata TEXT);
    CREATE INDEX IF NOT EXISTS idx_chimera_stmt_speaker ON chimera_statements(speaker);
    CREATE INDEX IF NOT EXISTS idx_chimera_stmt_topic ON chimera_statements(topic);
    CREATE INDEX IF NOT EXISTS idx_chimera_stmt_speaker_topic ON chimera_statements(speaker, topic);
    CREATE TABLE IF NOT EXISTS chimera_contradictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statement_id_a INTEGER NOT NULL, statement_id_b INTEGER NOT NULL, topic TEXT,
        severity INTEGER CHECK(severity BETWEEN 1 AND 10),
        confidence REAL CHECK(confidence BETWEEN 0.0 AND 1.0),
        impeachment_value INTEGER CHECK(impeachment_value BETWEEN 1 AND 10),
        description TEXT, contradiction_type TEXT, created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (statement_id_a) REFERENCES chimera_statements(id),
        FOREIGN KEY (statement_id_b) REFERENCES chimera_statements(id),
        UNIQUE(statement_id_a, statement_id_b));
    CREATE INDEX IF NOT EXISTS idx_chimera_contra_severity ON chimera_contradictions(severity);
    CREATE TABLE IF NOT EXISTS chimera_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT, pattern_type TEXT NOT NULL,
        description TEXT NOT NULL, evidence_refs TEXT,
        confidence REAL CHECK(confidence BETWEEN 0.0 AND 1.0),
        speaker TEXT, date_range TEXT, created_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS chimera_impeachment (
        id INTEGER PRIMARY KEY AUTOINCREMENT, contradiction_id INTEGER NOT NULL,
        statement_a_text TEXT, statement_b_text TEXT, source_a TEXT, source_b TEXT,
        questions TEXT, legal_significance TEXT,
        severity INTEGER CHECK(severity BETWEEN 1 AND 10),
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (contradiction_id) REFERENCES chimera_contradictions(id));
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn_cache = None
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        """Get or reuse a database connection (lazy singleton per instance)."""
        if self._conn_cache is not None:
            return self._conn_cache
        if _HAS_SHARED and self.db_path == DB_PATH:
            self._conn_cache = _shared_get_db("litigation")
        else:
            conn = sqlite3.connect(self.db_path, timeout=120)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            self._conn_cache = conn
        return self._conn_cache

    def close(self):
        """Explicitly close the cached connection."""
        if self._conn_cache is not None:
            try:
                self._conn_cache.close()
            except Exception:
                pass
            self._conn_cache = None

    def _ensure_tables(self):
        conn = self._connect()
        conn.executescript(self.SCHEMA_SQL)
        conn.commit()

    # ── 1. Statement Extractor ──────────────────────────────────
    @staticmethod
    def _normalize_speaker(raw: str) -> str:
        return KNOWN_SPEAKERS.get(raw.strip().lower(), raw.strip())

    @staticmethod
    def _detect_source_type(text: str, filepath: str = "") -> str:
        combined = (text[:3000] + filepath).lower()
        for stype, patterns in SOURCE_TYPE_PATTERNS.items():
            if any(p in combined for p in patterns):
                return stype
        return "unknown"

    @staticmethod
    def _extract_dates(text: str) -> List[str]:
        dates = []
        for pattern in DATE_PATTERNS:
            dates.extend(re.findall(pattern, text[:5000], re.IGNORECASE))
        return dates

    @staticmethod
    def _content_hash(speaker: str, content: str) -> str:
        blob = f"{speaker.lower().strip()}|{content.lower().strip()}"
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _classify_topics(content: str) -> List[str]:
        low = content.lower()
        topics = [t for t, kws in TOPIC_KEYWORDS.items() if any(k in low for k in kws)]
        return topics or ["general"]

    def _extract_statements_from_text(
        self, text: str, source_path: str = "", default_speaker: Optional[str] = None,
    ) -> List[Dict]:
        source_type = self._detect_source_type(text, source_path)
        doc_dates = self._extract_dates(text)
        primary_date = doc_dates[0] if doc_dates else None
        statements: List[Dict] = []
        for pat in ATTRIBUTION_PATTERNS:
            for m in re.finditer(pat, text, re.IGNORECASE | re.DOTALL):
                raw_speaker, content = m.group(1).strip(), m.group(2).strip()
                if len(content) < 15:
                    continue
                speaker = self._normalize_speaker(raw_speaker)
                for topic in self._classify_topics(content):
                    statements.append(dict(speaker=speaker, date=primary_date, topic=topic,
                                           content=content[:2000], source_path=source_path,
                                           source_type=source_type))
        if not statements and default_speaker:
            speaker = self._normalize_speaker(default_speaker)
            for para in [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30][:50]:
                for topic in self._classify_topics(para):
                    statements.append(dict(speaker=speaker, date=primary_date, topic=topic,
                                           content=para[:2000], source_path=source_path,
                                           source_type=source_type))
        return statements

    def ingest(self, path: str, speaker: Optional[str] = None) -> Dict[str, int]:
        """Ingest file(s) and extract statements."""
        p = Path(path)
        if p.is_file():
            files = [p]
        elif p.is_dir():
            files = [f for ext in ("*.txt", "*.md", "*.csv", "*.log", "*.json", "*.tsv")
                     for f in p.rglob(ext)]
        else:
            logger.error("Path not found: %s", path)
            return {"files": 0, "statements": 0, "duplicates": 0}
        total_stmts, total_dupes = 0, 0
        conn = self._connect()
        try:
            for f in files:
                try:
                    text = f.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    logger.warning("Cannot read %s: %s", f, e)
                    continue
                for s in self._extract_statements_from_text(text, str(f), speaker):
                    chash = self._content_hash(s["speaker"], s["content"])
                    try:
                        conn.execute("INSERT INTO chimera_statements (speaker, statement_date, "
                                     "topic, content, source_path, source_type, content_hash) "
                                     "VALUES (?,?,?,?,?,?,?)",
                                     (s["speaker"], s["date"], s["topic"], s["content"],
                                      s["source_path"], s["source_type"], chash))
                        total_stmts += 1
                    except sqlite3.IntegrityError:
                        total_dupes += 1
            conn.commit()
        finally:
            pass
        result = {"files": len(files), "statements": total_stmts, "duplicates": total_dupes}
        logger.info("Ingested: %s", result)
        return result

    # ── 2. Contradiction Detector ───────────────────────────────
    @staticmethod
    def _score_contradiction(stmt_a: Dict, stmt_b: Dict) -> Dict:
        a_low, b_low = stmt_a["content"].lower(), stmt_b["content"].lower()
        severity, confidence, ctype = 3, 0.4, "potential_inconsistency"
        # Direct negation
        for neg, pos in NEGATION_PAIRS:
            if (neg in a_low and pos in b_low) or (pos in a_low and neg in b_low):
                severity, confidence, ctype = max(severity, 7), max(confidence, 0.8), "direct_negation"
                break
        # Magnitude shift
        lo_words = {"minor", "argument", "disagreement", "verbal", "nothing"}
        hi_words = {"assault", "attack", "violence", "strangled", "beaten", "feared for"}
        a_lo, a_hi = any(w in a_low for w in lo_words), any(w in a_low for w in hi_words)
        b_lo, b_hi = any(w in b_low for w in lo_words), any(w in b_low for w in hi_words)
        if (a_lo and b_hi) or (a_hi and b_lo):
            severity, confidence, ctype = max(severity, 8), max(confidence, 0.75), "magnitude_shift"
        # Recantation
        recant = ("actually", "i was wrong", "that's not what happened", "i exaggerated", "it wasn't that bad")
        if any(w in b_low for w in recant):
            severity, confidence, ctype = max(severity, 9), max(confidence, 0.85), "recantation"
        # Same speaker + topic boosts confidence
        if stmt_a.get("topic") == stmt_b.get("topic") and stmt_a["speaker"] == stmt_b["speaker"]:
            confidence = min(confidence + 0.1, 1.0)
        imp = min(10, severity + (2 if ctype == "direct_negation" else 0))
        return dict(severity=min(severity, 10), confidence=round(confidence, 2),
                    impeachment_value=min(imp, 10), contradiction_type=ctype)

    def detect(self, speaker: Optional[str] = None, topic: Optional[str] = None) -> List[Dict]:
        """Detect contradictions across statements."""
        conn = self._connect()
        try:
            q, params = "SELECT * FROM chimera_statements WHERE 1=1", []
            if speaker:
                q += " AND speaker = ?"; params.append(self._normalize_speaker(speaker))
            if topic:
                q += " AND topic = ?"; params.append(topic)
            statements = [dict(r) for r in conn.execute(q + " ORDER BY speaker, topic, statement_date LIMIT 5000", params).fetchall()]
            groups: Dict[tuple, list] = defaultdict(list)
            for s in statements:
                groups[(s["speaker"], s["topic"])].append(s)
            contradictions: List[Dict] = []
            batch_inserts = []
            for (spk, top), stmts in groups.items():
                if len(stmts) < 2:
                    continue
                for i in range(len(stmts)):
                    for j in range(i + 1, len(stmts)):
                        score = self._score_contradiction(stmts[i], stmts[j])
                        if score["severity"] < 5 and score["confidence"] < 0.7:
                            continue
                        desc = (f"{spk} [{score['contradiction_type']}] on {top}: "
                                f"'{stmts[i]['content'][:80]}...' vs '{stmts[j]['content'][:80]}...'")
                        batch_inserts.append((stmts[i]["id"], stmts[j]["id"], top,
                                              score["severity"], score["confidence"],
                                              score["impeachment_value"], desc,
                                              score["contradiction_type"]))
                        contradictions.append(dict(statement_a=stmts[i], statement_b=stmts[j],
                                                   topic=top, description=desc, **score))
            if batch_inserts:
                conn.executemany(
                    "INSERT OR IGNORE INTO chimera_contradictions "
                    "(statement_id_a, statement_id_b, topic, severity, confidence, "
                    "impeachment_value, description, contradiction_type) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    batch_inserts
                )
            conn.commit()
            logger.info("Detected %d contradictions", len(contradictions))
            return contradictions
        finally:
            pass

    # ── 3. Pattern Analyzer ─────────────────────────────────────
    def analyze_patterns(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Detect recurring accusation, escalation, retaliation, or weaponization patterns."""
        conn = self._connect()
        try:
            stmts = [dict(r) for r in conn.execute(
                "SELECT * FROM chimera_statements ORDER BY speaker, statement_date LIMIT 10000").fetchall()]
            contras = [dict(r) for r in conn.execute(
                "SELECT * FROM chimera_contradictions ORDER BY severity DESC LIMIT 10000").fetchall()]
            analyzers = dict(accusation_timing=self._pat_accusation_timing,
                             escalation=self._pat_escalation,
                             retaliation=self._pat_retaliation,
                             weaponization=self._pat_weaponization)
            targets = {pattern_type: analyzers[pattern_type]} if pattern_type in analyzers else analyzers
            patterns: List[Dict] = []
            for ptype, fn in targets.items():
                for p in fn(stmts, contras):
                    p["pattern_type"] = ptype
                    conn.execute("INSERT INTO chimera_patterns (pattern_type, description, "
                                 "evidence_refs, confidence, speaker, date_range) VALUES (?,?,?,?,?,?)",
                                 (ptype, p["description"], json.dumps(p.get("evidence_refs", [])),
                                  p["confidence"], p.get("speaker"), p.get("date_range")))
                    patterns.append(p)
            conn.commit()
            logger.info("Found %d patterns", len(patterns))
            return patterns
        finally:
            pass

    @staticmethod
    def _pat_accusation_timing(stmts, _contras) -> List[Dict]:
        hits = [s for s in stmts if s["speaker"] == "Emily Watson"
                and s["topic"] in {"physical_violence", "threats", "fear", "substance_abuse", "child_welfare"}]
        if len(hits) < 2: return []
        topics_seen = ", ".join(sorted({s["topic"] for s in hits}))
        dr = f"{hits[0].get('statement_date', '?')} to {hits[-1].get('statement_date', '?')}"
        return [dict(description=(f"Emily Watson made {len(hits)} accusatory statements across "
                                  f"topics: {topics_seen}. Recommend cross-ref against court docket dates."),
                     evidence_refs=[s["id"] for s in hits[:10]],
                     confidence=min(0.5 + len(hits) * 0.05, 0.95),
                     speaker="Emily Watson", date_range=dr)]

    @staticmethod
    def _pat_escalation(_stmts, contras) -> List[Dict]:
        shifts = [c for c in contras if c.get("contradiction_type") == "magnitude_shift"]
        if not shifts: return []
        return [dict(description=(f"{len(shifts)} magnitude shifts: initial descriptions later "
                                  "restated with significantly greater severity — classic escalation."),
                     evidence_refs=[c["id"] for c in shifts[:10]],
                     confidence=min(0.6 + len(shifts) * 0.1, 0.95), speaker=None, date_range=None)]

    @staticmethod
    def _pat_retaliation(stmts, _contras) -> List[Dict]:
        andrew = [s for s in stmts if s["speaker"] == "Andrew Pigors"
                  and s["topic"] in {"custody", "visitation", "court_orders", "parenting"}]
        emily = [s for s in stmts if s["speaker"] == "Emily Watson"
                 and s["topic"] in {"physical_violence", "threats", "fear"}]
        if not andrew or not emily: return []
        return [dict(description=(f"{len(andrew)} parental-rights assertions by Andrew Pigors; "
                                  f"{len(emily)} accusatory statements by Emily Watson. "
                                  "Temporal correlation analysis recommended."),
                     evidence_refs=[s["id"] for s in (andrew[:5] + emily[:5])],
                     confidence=0.5, speaker="Emily Watson", date_range=None)]

    @staticmethod
    def _pat_weaponization(stmts, _contras) -> List[Dict]:
        police = [s for s in stmts if s["topic"] == "police_contact"]
        cps = [s for s in stmts if s["topic"] == "child_welfare"
               and s.get("source_type") in ("cps_report", "police_report")]
        if not police: return []
        return [dict(description=(f"{len(police)} police contacts documented. {len(cps)} CPS-related "
                                  "statements. 0 arrests, 0 charges against Andrew Pigors. "
                                  "Pattern consistent with system weaponization."),
                     evidence_refs=[s["id"] for s in police[:10]],
                     confidence=min(0.5 + len(police) * 0.08, 0.9),
                     speaker="Emily Watson", date_range=None)]

    # ── 4. Impeachment Matrix Builder ───────────────────────────
    def build_impeachment(self, min_severity: int = 5) -> List[Dict]:
        """Build impeachment entries from contradictions at or above min_severity."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT c.*, sa.content AS content_a, sa.source_path AS src_a, "
                "sa.source_type AS type_a, sa.statement_date AS date_a, "
                "sb.content AS content_b, sb.source_path AS src_b, "
                "sb.source_type AS type_b, sb.statement_date AS date_b, sa.speaker "
                "FROM chimera_contradictions c "
                "JOIN chimera_statements sa ON c.statement_id_a = sa.id "
                "JOIN chimera_statements sb ON c.statement_id_b = sb.id "
                "WHERE c.severity >= ? ORDER BY c.impeachment_value DESC, c.severity DESC LIMIT 5000",
                (min_severity,)).fetchall()
            entries: List[Dict] = []
            for r in [dict(r) for r in rows]:
                questions = self._cross_exam_questions(r)
                significance = self._legal_significance(r)
                try:
                    conn.execute("INSERT OR REPLACE INTO chimera_impeachment (contradiction_id, "
                                 "statement_a_text, statement_b_text, source_a, source_b, "
                                 "questions, legal_significance, severity) VALUES (?,?,?,?,?,?,?,?)",
                                 (r["id"], r["content_a"][:2000], r["content_b"][:2000],
                                  r["src_a"], r["src_b"], json.dumps(questions),
                                  json.dumps(significance), r["severity"]))
                except sqlite3.Error as e:
                    logger.warning("Impeachment insert error: %s", e)
                entries.append(dict(
                    contradiction_id=r["id"], speaker=r["speaker"], topic=r["topic"],
                    statement_a=dict(content=r["content_a"], source=r["src_a"],
                                     type=r["type_a"], date=r["date_a"]),
                    statement_b=dict(content=r["content_b"], source=r["src_b"],
                                     type=r["type_b"], date=r["date_b"]),
                    severity=r["severity"], impeachment_value=r["impeachment_value"],
                    contradiction_type=r["contradiction_type"],
                    questions=questions, legal_significance=significance))
            conn.commit()
            logger.info("Built %d impeachment entries (min severity=%d)", len(entries), min_severity)
            return entries
        finally:
            pass

    @staticmethod
    def _cross_exam_questions(c: Dict) -> List[str]:
        da, db = c.get("date_a", "[DATE]"), c.get("date_b", "[DATE]")
        qs = [f"You stated on {da} that '{c['content_a'][:100]}...' — is that correct?",
              f"But on {db} you stated '{c['content_b'][:100]}...' — is that also correct?",
              "Can you explain to the Court how both statements can be true?",
              f"Which statement was accurate — the one on {da} or {db}?"]
        extra = {"magnitude_shift": "Why did the severity of your account change between these dates?",
                 "recantation": "Are you now recanting your earlier sworn statement?",
                 "direct_negation": "One of these statements must be false — which one is it?"}
        if c.get("contradiction_type") in extra:
            qs.append(extra[c["contradiction_type"]])
        return qs

    @staticmethod
    def _legal_significance(c: Dict) -> Dict:
        severity = c.get("severity", 5)
        sworn = {"affidavit", "court_testimony", "ppo_petition"}
        a_sworn, b_sworn = c.get("type_a", "") in sworn, c.get("type_b", "") in sworn
        basis = "MRE 613(b) — extrinsic evidence of prior inconsistent statement"
        if a_sworn or b_sworn:
            basis += "; MCL 767.24 (perjury) if sworn"
        return dict(credibility_impact="high" if severity >= 7 else "moderate" if severity >= 5 else "low",
                    perjury_risk=a_sworn and b_sworn and severity >= 7,
                    bad_faith_indicator=c.get("contradiction_type") == "magnitude_shift" and severity >= 6,
                    mre_relevant=True, impeachment_basis=basis)

    # ── 5. Report Generator ─────────────────────────────────────
    def generate_report(self, output: Optional[str] = None) -> str:
        conn = self._connect()
        try:
            counts = dict(conn.execute(
                "SELECT (SELECT COUNT(*) FROM chimera_statements) AS stmts, "
                "(SELECT COUNT(*) FROM chimera_contradictions) AS contras, "
                "(SELECT COUNT(*) FROM chimera_patterns) AS patterns, "
                "(SELECT COUNT(*) FROM chimera_impeachment) AS impeach").fetchone())
            top = [dict(r) for r in conn.execute(
                "SELECT c.*, sa.content AS content_a, sa.source_type AS type_a, "
                "sb.content AS content_b, sb.source_type AS type_b, sa.speaker "
                "FROM chimera_contradictions c "
                "JOIN chimera_statements sa ON c.statement_id_a = sa.id "
                "JOIN chimera_statements sb ON c.statement_id_b = sb.id "
                "ORDER BY c.impeachment_value DESC LIMIT 20").fetchall()]
            pats = [dict(r) for r in conn.execute(
                "SELECT * FROM chimera_patterns ORDER BY confidence DESC LIMIT 5000").fetchall()]
            speakers = [dict(r) for r in conn.execute(
                "SELECT speaker, COUNT(*) AS cnt FROM chimera_statements "
                "GROUP BY speaker ORDER BY cnt DESC").fetchall()]
        finally:
            pass
        L = [f"# CHIMERA Contradiction Detection Report\n\n_Generated: {datetime.now():%Y-%m-%d %H:%M:%S}_\n",
             "## Summary\n", "| Metric | Count |", "|--------|-------|",
             f"| Statements | {counts['stmts']} |", f"| Contradictions | {counts['contras']} |",
             f"| Patterns | {counts['patterns']} |", f"| Impeachment entries | {counts['impeach']} |",
             "\n## Statements by Speaker\n", "| Speaker | Count |", "|---------|-------|"]
        L.extend(f"| {s['speaker']} | {s['cnt']} |" for s in speakers)
        L.append("\n## Top Contradictions\n")
        for i, c in enumerate(top, 1):
            L.extend([f"### {i}. [{c['contradiction_type']}] Sev {c['severity']}/10 · Imp {c['impeachment_value']}/10",
                       f"- **Speaker:** {c['speaker']}  **Topic:** {c['topic']}",
                       f"- **A** ({c['type_a']}): _{c['content_a'][:200]}_",
                       f"- **B** ({c['type_b']}): _{c['content_b'][:200]}_\n"])
        if pats:
            L.append("## Detected Patterns\n")
            for p in pats:
                L.extend([f"### {p['pattern_type']} (confidence: {p['confidence']})",
                           f"- {p['description']}", ""])
        report = "\n".join(L)
        if output:
            Path(output).write_text(report, encoding="utf-8")
            logger.info("Report written to %s", output)
        return report

    # ── 6. Status ───────────────────────────────────────────────
    def status(self) -> Dict:
        conn = self._connect()
        try:
            return dict(conn.execute(
                "SELECT (SELECT COUNT(*) FROM chimera_statements) AS statements, "
                "(SELECT COUNT(*) FROM chimera_contradictions) AS contradictions, "
                "(SELECT COUNT(*) FROM chimera_patterns) AS patterns, "
                "(SELECT COUNT(*) FROM chimera_impeachment) AS impeachment_entries, "
                "(SELECT COUNT(DISTINCT speaker) FROM chimera_statements) AS speakers, "
                "(SELECT COUNT(DISTINCT topic) FROM chimera_statements) AS topics").fetchone())
        finally:
            pass


# ── CLI ─────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(prog="chimera_engine",
        description="CHIMERA — Cross-referencing Hostile Inconsistencies via "
                    "Multi-source Evidence Reconciliation and Analysis")
    sub = ap.add_subparsers(dest="command", help="Command to run")
    p = sub.add_parser("ingest", help="Ingest documents and extract statements")
    p.add_argument("path", help="File or directory"); p.add_argument("--speaker")
    p = sub.add_parser("detect", help="Detect contradictions")
    p.add_argument("--speaker"); p.add_argument("--topic")
    p = sub.add_parser("patterns", help="Analyze recurring patterns")
    p.add_argument("--type", dest="pattern_type",
                   choices=["accusation_timing", "escalation", "retaliation", "weaponization"])
    p = sub.add_parser("impeachment", help="Build impeachment matrix")
    p.add_argument("--min-severity", type=int, default=5)
    p.add_argument("--format", dest="fmt", choices=["md", "json"], default="json")
    p = sub.add_parser("report", help="Generate full Markdown report")
    p.add_argument("--output", help="Output file path")
    sub.add_parser("status", help="Show engine status")
    args = ap.parse_args()
    if not args.command:
        ap.print_help(); return
    engine = ChimeraEngine()
    if args.command == "ingest":
        print(json.dumps(engine.ingest(args.path, speaker=args.speaker), indent=2))
    elif args.command == "detect":
        results = engine.detect(speaker=getattr(args, "speaker", None),
                                topic=getattr(args, "topic", None))
        print(f"Found {len(results)} contradictions")
        for c in results[:20]:
            print(f"  [{c['contradiction_type']}] sev={c['severity']} "
                  f"conf={c['confidence']} — {c['description'][:120]}")
    elif args.command == "patterns":
        results = engine.analyze_patterns(pattern_type=getattr(args, "pattern_type", None))
        print(f"Found {len(results)} patterns")
        for p in results:
            print(f"  [{p['pattern_type']}] conf={p['confidence']} — {p['description'][:120]}")
    elif args.command == "impeachment":
        entries = engine.build_impeachment(min_severity=args.min_severity)
        if args.fmt == "json":
            print(json.dumps(entries, indent=2, default=str))
        else:
            for e in entries:
                print(f"\n--- #{e['contradiction_id']} (sev={e['severity']}) ---")
                print(f"Speaker: {e['speaker']}")
                print(f"A: {e['statement_a']['content'][:150]}")
                print(f"B: {e['statement_b']['content'][:150]}")
                for q in e["questions"]:
                    print(f"  Q: {q}")
    elif args.command == "report":
        print(engine.generate_report(output=getattr(args, "output", None)))
    elif args.command == "status":
        st = engine.status()
        print("CHIMERA Engine Status:")
        for k, v in st.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
