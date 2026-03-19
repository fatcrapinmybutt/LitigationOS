"""
ImpeachmentEngine — MBP LitigationOS
Mines litigation_context.db for impeachment items, contradictions,
credibility attacks, judicial misconduct, and timeline conflicts.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_PATH = Path(r"C:\Users\andre\LitigationOS\06_ANALYSIS\impeachment_report.md")

# ---------------------------------------------------------------------------
# Keyword sets for topical overlap detection
# ---------------------------------------------------------------------------
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "parenting_time": ["parenting time", "parenting-time", "visitation", "custody time",
                        "overnight", "weekend", "holiday"],
    "custody": ["custody", "legal custody", "physical custody", "sole custody",
                 "joint custody", "custodial"],
    "ex_parte": ["ex parte", "emergency order", "without notice", "unilateral"],
    "ppo": ["ppo", "personal protection order", "restraining", "no-contact"],
    "mental_health": ["mental health", "assessment", "evaluation", "psychological",
                       "therapy", "counselor", "therapist"],
    "abuse_allegations": ["abuse", "neglect", "endangerment", "harm", "violence",
                           "domestic violence", "assault"],
    "anger": ["anger", "rage", "temper", "volatile", "aggressive", "hostile",
              "threatening", "intimidat"],
    "compliance": ["comply", "compliance", "violat", "disobey", "contempt",
                    "failed to", "refused to", "did not"],
    "financial": ["support", "income", "financial", "payment", "arrearage",
                   "child support", "spousal"],
    "credibility": ["lied", "lying", "false", "fabricat", "mislead", "perjur",
                     "dishonest", "untruthful", "not credible"],
    "hearing": ["hearing", "evidentiary", "testimony", "testified", "sworn",
                 "under oath"],
    "best_interest": ["best interest", "best-interest", "factor", "stability",
                       "moral fitness", "reasonable preference"],
    "communication": ["communication", "contact", "phone", "text", "email",
                       "message", "called"],
    "child_welfare": ["child", "son", "daughter", "minor", "lincoln", "welfare",
                       "safety"],
}

BIAS_INDICATORS = [
    "financial interest", "custody motivation", "relationship to party",
    "animosity", "bias", "prejudice", "ex-wife", "ex-husband", "opposing party",
    "gain custody", "sole custody", "control", "revenge", "spite",
]

CREDIBILITY_NEGATIVES = [
    "false", "fabricat", "lied", "lying", "perjur", "inconsistent",
    "contradicted", "not credible", "unreliable", "mislead", "exaggerat",
    "unsubstantiated", "unverified", "no evidence", "unsupported",
]

JUDICIAL_IMPEACHMENT_CATEGORIES = [
    "EX_PARTE_VIOLATION", "BENCHBOOK_DEVIATION", "DUE_PROCESS_VIOLATION",
    "PROCEDURAL_MISCONDUCT", "MCJC_CANON_VIOLATION", "MCR_2003_DISQUALIFICATION",
    "CREDIBILITY_FAILURE", "PPO_WEAPONIZATION",
]

DATE_RE = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{2,4})",
    re.IGNORECASE,
)


def _short_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:10]


def _topics_for(text: str) -> set:
    """Return set of topic keys that appear in *text*."""
    if not text:
        return set()
    lower = text.lower()
    return {k for k, words in TOPIC_KEYWORDS.items() if any(w in lower for w in words)}


def _keyword_overlap(a: str, b: str) -> float:
    """Jaccard similarity on word-level tokens (length >= 4)."""
    wa = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", a or "")}
    wb = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", b or "")}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _contains_any(text: str, keywords: list) -> List[str]:
    if not text:
        return []
    lower = text.lower()
    return [k for k in keywords if k in lower]


def _extract_dates(text: str) -> List[str]:
    if not text:
        return []
    return DATE_RE.findall(text)


def _severity_from_overlap(overlap: float, topic_match: bool) -> str:
    if topic_match and overlap >= 0.15:
        return "CRITICAL"
    if topic_match or overlap >= 0.20:
        return "HIGH"
    if overlap >= 0.10:
        return "MEDIUM"
    return "LOW"


class ImpeachmentEngine:
    """Mines the litigation database for impeachment material."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.findings: List[Dict[str, Any]] = []
        self.contradictions: List[Dict[str, Any]] = []
        self._next_id: Optional[int] = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_next_id(self) -> int:
        if self._next_id is None:
            row = self.conn.execute("SELECT MAX(id) FROM impeachment_items").fetchone()
            self._next_id = (row[0] or 0) + 1
        nid = self._next_id
        self._next_id += 1
        return nid

    def _add_finding(self, item_type: str, speaker: str | None,
                     doc_id: int | None, page: int | None,
                     statement: str, contra_source: str | None,
                     contra_doc_id: int | None, contra_text: str,
                     legal_hook: str, severity: str):
        sig = _short_hash(f"{item_type}|{speaker}|{statement[:80]}|{contra_text[:80]}")
        self.findings.append({
            "id": self._get_next_id(),
            "item_type": item_type,
            "speaker": speaker,
            "transcript_doc_id": doc_id,
            "transcript_page": page,
            "statement": (statement or "")[:500],
            "contradicting_source": contra_source,
            "contradicting_doc_id": contra_doc_id,
            "contradicting_text": (contra_text or "")[:500],
            "legal_hook": legal_hook,
            "severity": severity,
            "sig": sig,
        })

    def _add_contradiction(self, src_a_type: str, src_a_doc: int | None,
                           src_a_text: str, src_b_type: str,
                           src_b_doc: int | None, src_b_text: str,
                           contra_type: str, severity: str,
                           legal_impact: str):
        sig = _short_hash(f"{src_a_text[:60]}|{src_b_text[:60]}")
        self.contradictions.append({
            "source_a_type": src_a_type,
            "source_a_doc_id": src_a_doc,
            "source_a_text": (src_a_text or "")[:500],
            "source_b_type": src_b_type,
            "source_b_doc_id": src_b_doc,
            "source_b_text": (src_b_text or "")[:500],
            "contradiction_type": contra_type,
            "severity": severity,
            "legal_impact": legal_impact,
            "sig": sig,
        })

    # ------------------------------------------------------------------
    # 1. INCONSISTENT STATEMENTS
    # ------------------------------------------------------------------
    def scan_inconsistencies(self) -> int:
        """Group evidence_quotes by speaker; flag contradictory statement pairs."""
        count_before = len(self.findings)
        rows = self.conn.execute(
            "SELECT id, document_id, page_number, evidence_category, quote_text, "
            "speaker, date_ref, legal_significance FROM evidence_quotes"
        ).fetchall()

        by_speaker: Dict[str, list] = defaultdict(list)
        for r in rows:
            key = (r["speaker"] or "UNKNOWN").upper().strip()
            by_speaker[key].append(dict(r))

        # Compare within each speaker
        for speaker, quotes in by_speaker.items():
            n = len(quotes)
            for i in range(n):
                topics_i = _topics_for(quotes[i]["quote_text"])
                dates_i = _extract_dates(quotes[i]["quote_text"])
                for j in range(i + 1, n):
                    if quotes[i]["document_id"] == quotes[j]["document_id"] and \
                       quotes[i]["page_number"] == quotes[j]["page_number"]:
                        continue  # same page, skip
                    topics_j = _topics_for(quotes[j]["quote_text"])
                    shared_topics = topics_i & topics_j
                    if not shared_topics:
                        continue
                    overlap = _keyword_overlap(quotes[i]["quote_text"],
                                              quotes[j]["quote_text"])
                    if overlap < 0.05:
                        continue
                    # Check for contradictory signals
                    txt_i = (quotes[i]["quote_text"] or "").lower()
                    txt_j = (quotes[j]["quote_text"] or "").lower()
                    contra_signals = (
                        ("not" in txt_i and "not" not in txt_j) or
                        ("not" in txt_j and "not" not in txt_i) or
                        ("denied" in txt_i and "denied" not in txt_j) or
                        ("granted" in txt_i and "denied" in txt_j) or
                        ("denied" in txt_i and "granted" in txt_j) or
                        any(d in txt_j for d in dates_i if d not in txt_i[:20]) or
                        overlap >= 0.15
                    )
                    if not contra_signals:
                        continue

                    sev = _severity_from_overlap(overlap, bool(shared_topics))
                    topic_str = ", ".join(sorted(shared_topics))
                    self._add_finding(
                        item_type="PRIOR_INCONSISTENT_STATEMENT",
                        speaker=speaker if speaker != "UNKNOWN" else None,
                        doc_id=quotes[i]["document_id"],
                        page=quotes[i]["page_number"],
                        statement=quotes[i]["quote_text"],
                        contra_source=f"evidence_quotes.id={quotes[j]['id']}",
                        contra_doc_id=quotes[j]["document_id"],
                        contra_text=quotes[j]["quote_text"],
                        legal_hook=f"MRE 613(b) — Prior inconsistent statement [{topic_str}]",
                        severity=sev,
                    )
                    if sev in ("CRITICAL", "HIGH"):
                        self._add_contradiction(
                            quotes[i]["evidence_category"] or "EVIDENCE",
                            quotes[i]["document_id"],
                            quotes[i]["quote_text"],
                            quotes[j]["evidence_category"] or "EVIDENCE",
                            quotes[j]["document_id"],
                            quotes[j]["quote_text"],
                            "INCONSISTENT_STATEMENTS",
                            sev,
                            f"Speaker {speaker} made inconsistent statements on: {topic_str}",
                        )

        # Cross-speaker contradictions: COURT vs WATSON vs PIGORS
        named_speakers = [s for s in by_speaker if s not in ("UNKNOWN", "")]
        for idx, sp_a in enumerate(named_speakers):
            for sp_b in named_speakers[idx + 1:]:
                for qa in by_speaker[sp_a]:
                    topics_a = _topics_for(qa["quote_text"])
                    if not topics_a:
                        continue
                    for qb in by_speaker[sp_b]:
                        topics_b = _topics_for(qb["quote_text"])
                        shared = topics_a & topics_b
                        if not shared:
                            continue
                        overlap = _keyword_overlap(qa["quote_text"], qb["quote_text"])
                        if overlap < 0.10:
                            continue
                        txt_a = (qa["quote_text"] or "").lower()
                        txt_b = (qb["quote_text"] or "").lower()
                        contra = (
                            ("not" in txt_a) != ("not" in txt_b) or
                            ("denied" in txt_a) != ("denied" in txt_b) or
                            ("granted" in txt_a and "denied" in txt_b) or
                            overlap >= 0.20
                        )
                        if not contra:
                            continue
                        topic_str = ", ".join(sorted(shared))
                        self._add_finding(
                            item_type="CROSS_SPEAKER_CONTRADICTION",
                            speaker=sp_a,
                            doc_id=qa["document_id"],
                            page=qa["page_number"],
                            statement=qa["quote_text"],
                            contra_source=f"{sp_b} | evidence_quotes.id={qb['id']}",
                            contra_doc_id=qb["document_id"],
                            contra_text=qb["quote_text"],
                            legal_hook=f"MRE 613/801(d)(1) — Cross-speaker conflict [{topic_str}]",
                            severity=_severity_from_overlap(overlap, True),
                        )
                        self._add_contradiction(
                            "TESTIMONY", qa["document_id"], qa["quote_text"],
                            "TESTIMONY", qb["document_id"], qb["quote_text"],
                            "CROSS_SPEAKER_CONFLICT",
                            _severity_from_overlap(overlap, True),
                            f"{sp_a} vs {sp_b} on: {topic_str}",
                        )

        return len(self.findings) - count_before

    # ------------------------------------------------------------------
    # 2. CREDIBILITY ATTACKS
    # ------------------------------------------------------------------
    def scan_credibility(self) -> int:
        """Mine for bias, false claims, testimony-vs-document contradictions, omissions."""
        count_before = len(self.findings)

        # 2a. Bias indicators in evidence_quotes
        quotes = self.conn.execute(
            "SELECT id, document_id, page_number, evidence_category, quote_text, "
            "speaker, legal_significance FROM evidence_quotes"
        ).fetchall()
        for q in quotes:
            hits = _contains_any(q["quote_text"], BIAS_INDICATORS)
            if hits:
                self._add_finding(
                    item_type="CREDIBILITY_BIAS",
                    speaker=q["speaker"],
                    doc_id=q["document_id"],
                    page=q["page_number"],
                    statement=q["quote_text"],
                    contra_source="bias_keyword_scan",
                    contra_doc_id=None,
                    contra_text=f"Bias indicators: {', '.join(hits)}",
                    legal_hook="MRE 616 — Bias of witness",
                    severity="HIGH" if len(hits) >= 2 else "MEDIUM",
                )

        # 2b. False/unverified claims pattern
        for q in quotes:
            hits = _contains_any(q["quote_text"], CREDIBILITY_NEGATIVES)
            if hits:
                self._add_finding(
                    item_type="CREDIBILITY_FALSE_CLAIM",
                    speaker=q["speaker"],
                    doc_id=q["document_id"],
                    page=q["page_number"],
                    statement=q["quote_text"],
                    contra_source="credibility_keyword_scan",
                    contra_doc_id=None,
                    contra_text=f"Credibility negatives: {', '.join(hits)}",
                    legal_hook="MRE 608(b) — Specific instances of conduct for credibility",
                    severity="HIGH" if len(hits) >= 2 else "MEDIUM",
                )

        # 2c. Testimony vs documentary evidence
        #     Compare TRANSCRIPT quotes against non-TRANSCRIPT (orders, PPOs, etc.)
        transcripts = [q for q in quotes
                       if (q["evidence_category"] or "").upper() == "TRANSCRIPT"]
        documents = [q for q in quotes
                     if (q["evidence_category"] or "").upper() != "TRANSCRIPT"]
        for tq in transcripts:
            topics_t = _topics_for(tq["quote_text"])
            if not topics_t:
                continue
            for dq in documents:
                topics_d = _topics_for(dq["quote_text"])
                shared = topics_t & topics_d
                if not shared:
                    continue
                overlap = _keyword_overlap(tq["quote_text"], dq["quote_text"])
                if overlap < 0.08:
                    continue
                txt_t = (tq["quote_text"] or "").lower()
                txt_d = (dq["quote_text"] or "").lower()
                contra = (
                    ("not" in txt_t) != ("not" in txt_d) or
                    ("denied" in txt_t) != ("denied" in txt_d) or
                    ("granted" in txt_t and "denied" in txt_d) or
                    overlap >= 0.18
                )
                if not contra:
                    continue
                topic_str = ", ".join(sorted(shared))
                self._add_finding(
                    item_type="TESTIMONY_VS_DOCUMENT",
                    speaker=tq["speaker"],
                    doc_id=tq["document_id"],
                    page=tq["page_number"],
                    statement=tq["quote_text"],
                    contra_source=f"{dq['evidence_category']} | eq.id={dq['id']}",
                    contra_doc_id=dq["document_id"],
                    contra_text=dq["quote_text"],
                    legal_hook=f"MRE 613/803(6) — Testimony contradicted by document [{topic_str}]",
                    severity="CRITICAL" if overlap >= 0.20 else "HIGH",
                )
                self._add_contradiction(
                    "TRANSCRIPT", tq["document_id"], tq["quote_text"],
                    dq["evidence_category"] or "DOCUMENT", dq["document_id"],
                    dq["quote_text"],
                    "TESTIMONY_VS_DOCUMENT", "HIGH",
                    f"Testimony contradicted by {dq['evidence_category']} on: {topic_str}",
                )

        # 2d. Forensic credibility failures
        cred_rows = self.conn.execute(
            "SELECT finding_id, category, severity, description, evidence_citations, "
            "mcr_violations FROM forensic_judicial_analysis "
            "WHERE category = 'CREDIBILITY_FAILURE'"
        ).fetchall()
        for r in cred_rows:
            self._add_finding(
                item_type="CREDIBILITY_FORENSIC",
                speaker=None,
                doc_id=None,
                page=None,
                statement=r["description"],
                contra_source=f"forensic_judicial_analysis.{r['finding_id']}",
                contra_doc_id=None,
                contra_text=r["evidence_citations"] or "",
                legal_hook=f"MRE 608 — Credibility failure | {r['mcr_violations'] or ''}",
                severity=r["severity"].upper() if r["severity"] else "HIGH",
            )

        return len(self.findings) - count_before

    # ------------------------------------------------------------------
    # 3. JUDICIAL IMPEACHMENT
    # ------------------------------------------------------------------
    def scan_judicial_impeachment(self) -> int:
        """Mine forensic_judicial_analysis + benchbook violations for judge impeachment."""
        count_before = len(self.findings)

        # 3a. Forensic judicial findings (ex parte, benchbook, due process, bias)
        for cat in JUDICIAL_IMPEACHMENT_CATEGORIES:
            rows = self.conn.execute(
                "SELECT finding_id, category, severity, description, "
                "evidence_citations, mcr_violations, date_iso "
                "FROM forensic_judicial_analysis WHERE category = ?", (cat,)
            ).fetchall()
            for r in rows:
                sev = (r["severity"] or "high").upper()
                self._add_finding(
                    item_type=f"JUDICIAL_{cat}",
                    speaker="COURT",
                    doc_id=None,
                    page=None,
                    statement=r["description"],
                    contra_source=f"forensic.{r['finding_id']}",
                    contra_doc_id=None,
                    contra_text=r["evidence_citations"] or "",
                    legal_hook=r["mcr_violations"] or f"MCR / Canon — {cat}",
                    severity=sev,
                )

        # 3b. Auth benchbook violations (direct table)
        bench_rows = self.conn.execute(
            "SELECT id, rule, explanation, matching_text, judge, severity, source_file "
            "FROM auth_benchbook_violations"
        ).fetchall()
        for r in bench_rows:
            self._add_finding(
                item_type="BENCHBOOK_VIOLATION",
                speaker=r["judge"] or "COURT",
                doc_id=None,
                page=None,
                statement=r["explanation"],
                contra_source=f"auth_benchbook.id={r['id']}",
                contra_doc_id=None,
                contra_text=r["matching_text"] or "",
                legal_hook=f"{r['rule']} — Benchbook violation",
                severity="HIGH",
            )

        return len(self.findings) - count_before

    # ------------------------------------------------------------------
    # 4. TIMELINE CONTRADICTIONS
    # ------------------------------------------------------------------
    def scan_timeline_contradictions(self) -> int:
        """Cross-reference master_timeline against evidence for date conflicts."""
        count_before = len(self.findings)

        timeline = self.conn.execute(
            "SELECT event_id, date_iso, description, category, severity "
            "FROM master_timeline WHERE date_iso IS NOT NULL AND date_iso != '' "
            "ORDER BY date_iso"
        ).fetchall()

        quotes = self.conn.execute(
            "SELECT id, document_id, page_number, evidence_category, quote_text, "
            "speaker, date_ref FROM evidence_quotes WHERE date_ref IS NOT NULL"
        ).fetchall()

        # 4a. Timeline events vs evidence quote dates
        for q in quotes:
            q_dates = _extract_dates(q["quote_text"] or "")
            q_topics = _topics_for(q["quote_text"])
            if not q_dates and not q_topics:
                continue
            for te in timeline:
                te_topics = _topics_for(te["description"])
                shared = q_topics & te_topics
                if not shared:
                    continue
                overlap = _keyword_overlap(q["quote_text"], te["description"])
                if overlap < 0.08:
                    continue
                # Check for date mismatch
                te_date = (te["date_iso"] or "")[:10]
                date_conflict = te_date and q_dates and all(
                    te_date not in d and d not in te_date for d in q_dates
                )
                if not date_conflict and overlap < 0.15:
                    continue
                topic_str = ", ".join(sorted(shared))
                sev = "CRITICAL" if date_conflict and overlap >= 0.12 else "HIGH"
                self._add_finding(
                    item_type="TIMELINE_CONTRADICTION",
                    speaker=q["speaker"],
                    doc_id=q["document_id"],
                    page=q["page_number"],
                    statement=q["quote_text"],
                    contra_source=f"timeline.{te['event_id']}",
                    contra_doc_id=None,
                    contra_text=f"[{te_date}] {te['description']}"[:500],
                    legal_hook=f"Timeline conflict [{topic_str}]",
                    severity=sev,
                )
                self._add_contradiction(
                    q["evidence_category"] or "EVIDENCE", q["document_id"],
                    q["quote_text"],
                    "TIMELINE", None, f"[{te_date}] {te['description']}",
                    "TIMELINE_DATE_CONFLICT", sev,
                    f"Date/event conflict on: {topic_str}",
                )

        # 4b. Internal timeline ordering anomalies (same category, severity conflicts)
        by_cat: Dict[str, list] = defaultdict(list)
        for te in timeline:
            by_cat[te["category"]].append(dict(te))
        for cat, events in by_cat.items():
            if cat in ("general",):
                continue
            for i in range(len(events)):
                for j in range(i + 1, min(i + 5, len(events))):
                    overlap = _keyword_overlap(
                        events[i]["description"], events[j]["description"])
                    if overlap < 0.15:
                        continue
                    topics_shared = _topics_for(events[i]["description"]) & \
                                    _topics_for(events[j]["description"])
                    if not topics_shared:
                        continue
                    d_i = events[i]["date_iso"] or ""
                    d_j = events[j]["date_iso"] or ""
                    if d_i and d_j and d_i == d_j:
                        continue  # same date, not a contradiction
                    self._add_finding(
                        item_type="TIMELINE_SEQUENCE_ANOMALY",
                        speaker=None,
                        doc_id=None,
                        page=None,
                        statement=f"[{d_i}] {events[i]['description']}"[:500],
                        contra_source=f"timeline.{events[j]['event_id']}",
                        contra_doc_id=None,
                        contra_text=f"[{d_j}] {events[j]['description']}"[:500],
                        legal_hook=f"Timeline sequence anomaly [{', '.join(sorted(topics_shared))}]",
                        severity="MEDIUM",
                    )

        return len(self.findings) - count_before

    # ------------------------------------------------------------------
    # DEDUPLICATE
    # ------------------------------------------------------------------
    def _deduplicate(self):
        """Remove findings with duplicate signatures."""
        seen_sigs = set()
        # Load existing items to avoid re-inserting
        existing = self.conn.execute(
            "SELECT statement, contradicting_text FROM impeachment_items"
        ).fetchall()
        for ex in existing:
            sig = _short_hash(
                f"|{(ex['statement'] or '')[:80]}|{(ex['contradicting_text'] or '')[:80]}"
            )
            seen_sigs.add(sig)

        unique = []
        for f in self.findings:
            if f["sig"] not in seen_sigs:
                seen_sigs.add(f["sig"])
                unique.append(f)
        self.findings = unique

        seen_csigs = set()
        existing_c = self.conn.execute(
            "SELECT source_a_text, source_b_text FROM contradiction_map"
        ).fetchall()
        for ec in existing_c:
            sig = _short_hash(
                f"{(ec['source_a_text'] or '')[:60]}|{(ec['source_b_text'] or '')[:60]}"
            )
            seen_csigs.add(sig)

        unique_c = []
        for c in self.contradictions:
            if c["sig"] not in seen_csigs:
                seen_csigs.add(c["sig"])
                unique_c.append(c)
        self.contradictions = unique_c

    # ------------------------------------------------------------------
    # PERSIST
    # ------------------------------------------------------------------
    def _persist(self):
        """Insert new findings into the database."""
        self._deduplicate()

        # Re-number IDs after dedup
        row = self.conn.execute("SELECT MAX(id) FROM impeachment_items").fetchone()
        next_id = (row[0] or 0) + 1
        for f in self.findings:
            f["id"] = next_id
            next_id += 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for f in self.findings:
            self.conn.execute(
                "INSERT INTO impeachment_items "
                "(id, item_type, speaker, transcript_doc_id, transcript_page, "
                "statement, contradicting_source, contradicting_doc_id, "
                "contradicting_text, legal_hook, severity, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (f["id"], f["item_type"], f["speaker"],
                 f["transcript_doc_id"], f["transcript_page"],
                 f["statement"], f["contradicting_source"],
                 f["contradicting_doc_id"], f["contradicting_text"],
                 f["legal_hook"], f["severity"], now),
            )

        # Get max contradiction_map id
        row_c = self.conn.execute("SELECT MAX(id) FROM contradiction_map").fetchone()
        next_cid = (row_c[0] or 0) + 1
        for c in self.contradictions:
            self.conn.execute(
                "INSERT INTO contradiction_map "
                "(id, source_a_type, source_a_doc_id, source_a_text, "
                "source_b_type, source_b_doc_id, source_b_text, "
                "contradiction_type, severity, legal_impact, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (next_cid, c["source_a_type"], c["source_a_doc_id"],
                 c["source_a_text"], c["source_b_type"], c["source_b_doc_id"],
                 c["source_b_text"], c["contradiction_type"], c["severity"],
                 c["legal_impact"], now),
            )
            next_cid += 1

        self.conn.commit()

    # ------------------------------------------------------------------
    # 5. REPORT
    # ------------------------------------------------------------------
    def generate_report(self) -> str:
        """Generate full impeachment inventory as markdown."""
        # Get final counts from DB
        total_imp = self.conn.execute(
            "SELECT COUNT(*) FROM impeachment_items").fetchone()[0]
        total_contra = self.conn.execute(
            "SELECT COUNT(*) FROM contradiction_map").fetchone()[0]

        type_counts = self.conn.execute(
            "SELECT item_type, severity, COUNT(*) "
            "FROM impeachment_items GROUP BY item_type, severity "
            "ORDER BY item_type, severity"
        ).fetchall()

        sev_counts = self.conn.execute(
            "SELECT severity, COUNT(*) FROM impeachment_items "
            "GROUP BY severity ORDER BY COUNT(*) DESC"
        ).fetchall()

        contra_counts = self.conn.execute(
            "SELECT contradiction_type, COUNT(*) FROM contradiction_map "
            "GROUP BY contradiction_type ORDER BY COUNT(*) DESC"
        ).fetchall()

        speaker_counts = self.conn.execute(
            "SELECT speaker, COUNT(*) FROM impeachment_items "
            "WHERE speaker IS NOT NULL "
            "GROUP BY speaker ORDER BY COUNT(*) DESC LIMIT 10"
        ).fetchall()

        # Critical items for highlight
        critical_items = self.conn.execute(
            "SELECT id, item_type, speaker, statement, contradicting_text, "
            "legal_hook FROM impeachment_items "
            "WHERE severity = 'CRITICAL' ORDER BY id DESC LIMIT 30"
        ).fetchall()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# MBP LitigationOS — Impeachment Inventory Report",
            f"**Generated:** {now}",
            f"",
            f"## Summary",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| **Total Impeachment Items** | **{total_imp}** |",
            f"| **Total Contradictions** | **{total_contra}** |",
            f"| New items this scan | {len(self.findings)} |",
            f"| New contradictions this scan | {len(self.contradictions)} |",
            f"",
            f"## Severity Distribution",
            f"| Severity | Count |",
            f"|----------|-------|",
        ]
        for row in sev_counts:
            lines.append(f"| {row[0]} | {row[1]} |")

        lines += [
            f"",
            f"## By Item Type",
            f"| Item Type | Severity | Count |",
            f"|-----------|----------|-------|",
        ]
        for row in type_counts:
            lines.append(f"| {row[0]} | {row[1]} | {row[2]} |")

        lines += [
            f"",
            f"## Contradiction Types",
            f"| Type | Count |",
            f"|------|-------|",
        ]
        for row in contra_counts:
            lines.append(f"| {row[0]} | {row[1]} |")

        lines += [
            f"",
            f"## By Speaker",
            f"| Speaker | Count |",
            f"|---------|-------|",
        ]
        for row in speaker_counts:
            lines.append(f"| {row[0]} | {row[1]} |")

        lines += [
            f"",
            f"## Critical Impeachment Items (Top 30)",
            f"",
        ]
        for item in critical_items:
            lines.append(f"### Item #{item[0]} — {item[1]}")
            lines.append(f"- **Speaker:** {item[2] or 'N/A'}")
            lines.append(f"- **Statement:** {(item[3] or '')[:200]}...")
            lines.append(f"- **Contradicted by:** {(item[4] or '')[:200]}...")
            lines.append(f"- **Legal Hook:** {item[5]}")
            lines.append(f"")

        # New items added this scan — breakdown
        lines += [
            f"## New Findings This Scan",
            f"",
        ]
        new_by_type: Dict[str, int] = defaultdict(int)
        for f in self.findings:
            new_by_type[f["item_type"]] += 1
        lines.append(f"| Type | New Count |")
        lines.append(f"|------|-----------|")
        for t, c in sorted(new_by_type.items(), key=lambda x: -x[1]):
            lines.append(f"| {t} | {c} |")

        lines += [
            f"",
            f"---",
            f"*Engine: ImpeachmentEngine v2.0 — MBP LitigationOS*",
        ]

        report = "\n".join(lines)
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        return report

    # ------------------------------------------------------------------
    # FULL SCAN
    # ------------------------------------------------------------------
    def run_full_scan(self) -> Dict[str, int]:
        """Execute all scan phases, persist, and generate report."""
        results = {}
        results["inconsistencies"] = self.scan_inconsistencies()
        results["credibility"] = self.scan_credibility()
        results["judicial"] = self.scan_judicial_impeachment()
        results["timeline"] = self.scan_timeline_contradictions()

        self._persist()
        self.generate_report()

        # Final totals from DB
        results["total_impeachment_items"] = self.conn.execute(
            "SELECT COUNT(*) FROM impeachment_items").fetchone()[0]
        results["total_contradictions"] = self.conn.execute(
            "SELECT COUNT(*) FROM contradiction_map").fetchone()[0]
        results["new_items_inserted"] = len(self.findings)
        results["new_contradictions_inserted"] = len(self.contradictions)

        return results


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("MBP LitigationOS — ImpeachmentEngine v2.0")
    print("=" * 60)
    engine = ImpeachmentEngine()
    results = engine.run_full_scan()
    print()
    for k, v in results.items():
        print(f"  {k:.<40s} {v}")
    print()
    print(f"Report saved to: {REPORT_PATH}")
    print("=" * 60)
    engine.conn.close()
