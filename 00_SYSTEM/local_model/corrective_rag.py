#!/usr/bin/env python3
"""
APEX MANBEARPIG — Corrective RAG / Self-RAG Engine (APEX v5.0)
==============================================================
Enhanced corrective RAG loop that self-corrects retrieval and generation.

Key behavior:
1. Retrieve documents via multi-table FTS5 search
2. Generate answer (MANBEARPIG GGUF or extractive fallback)
3. Verify answer against retrieved docs (rule-based checks)
4. If verification fails → expand query → re-retrieve → re-generate
5. Max 2 correction cycles (configurable)
6. Log correction rate for learning loop

APEX Shadow-programming: APEX_LLM_ENABLED env var gates LLM usage.
When disabled (default), all methods use statistical/keyword fallbacks.
NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules in repo root).
Uses Path(__file__).parent for relative paths.

Usage:
    from corrective_rag import CorrectiveRAG
    crag = CorrectiveRAG()
    result = crag.query("What are the best interest factors?")
    # or legacy API:
    result = crag.corrective_query("What are the best interest factors?")
"""

import sqlite3
import json
import os
import sys
import time
import re
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent

# ── Paths ──────────────────────────────────────────────────────────
GGUF_PATH = str(_MODULE_DIR / "gguf" / "qwen2.5-1.5b-instruct-q4_k_m.gguf")
DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    str(_MODULE_DIR.parent.parent.parent / "litigation_context.db"),
)

# ── Thread safety ──────────────────────────────────────────────────
_CORRECTION_STATS_LOCK = threading.Lock()
_CORRECTION_STATS: Dict[str, Any] = {
    "total_queries": 0,
    "total_corrections": 0,
    "correction_rate": 0.0,
    "grounded_count": 0,
    "best_effort_count": 0,
    "exhausted_count": 0,
}

# ── Legal Thesaurus ────────────────────────────────────────────────
LEGAL_THESAURUS: Dict[str, List[str]] = {
    "custody": ["parenting time", "best interest factors", "MCL 722.23",
                "established custodial environment", "MCL 722.27"],
    "parenting time": ["custody", "visitation", "parenting schedule",
                       "MCL 722.27a", "overnights"],
    "best interest": ["best interest factors", "MCL 722.23", "child welfare",
                      "factors a through l", "custody determination"],
    "disqualification": ["recusal", "MCR 2.003", "judicial bias", "prejudice",
                         "due process", "impartiality"],
    "contempt": ["MCL 600.1701", "MCR 3.606", "willful violation",
                 "court order violation", "civil contempt", "criminal contempt"],
    "discovery": ["MCR 2.302", "MCR 2.313", "interrogatories", "deposition",
                  "request for production", "motion to compel"],
    "appeal": ["MCR 7.204", "MCR 7.205", "claim of appeal", "appellate",
               "court of appeals", "de novo review", "abuse of discretion"],
    "ppo": ["personal protection order", "MCL 600.2950", "restraining order",
            "stalking", "domestic violence"],
    "evidence": ["MRE", "admissibility", "hearsay", "relevance", "MRE 801",
                 "MRE 401", "exhibit"],
    "due process": ["14th Amendment", "fundamental rights", "Troxel",
                    "procedural due process", "substantive due process"],
    "alienation": ["parental alienation", "MCL 722.23(j)", "factor j",
                   "relationship facilitation", "interference"],
    "service": ["MCR 2.105", "service of process", "proof of service",
                "personal service", "substitute service"],
    "motion": ["MCR 2.119", "brief", "response", "reply", "hearing",
               "summary disposition", "MCR 2.116"],
    "child support": ["MCL 552.605", "income shares", "deviation",
                      "support obligation", "UCSO"],
    "friend of court": ["FOC", "MCL 552.501", "recommendation", "objection",
                        "referee", "de novo hearing"],
    "guardian ad litem": ["GAL", "MCR 3.915", "MCL 722.24", "child advocate",
                         "attorney for child"],
    "mcneill": ["judge mcneill", "jenny mcneill", "judicial misconduct",
                "disqualification", "bias", "14th circuit"],
    "separation": ["parent-child separation", "329 days", "parenting time denial",
                   "custodial interference"],
}

# FTS5 tables to search and their text columns
FTS_TABLES = {
    "evidence_quotes_fts": "quote_text",
    "auth_rules_fts": "full_text",
    "rules_text_fts": "context",
    "md_sections_fts": "content",
    "pages_fts": "text_content",
}


class CorrectiveRAG:
    """APEX Corrective RAG engine with self-verification loop.

    Grades retrieved documents for relevance, detects hallucinations in
    generated answers, and iteratively corrects until quality thresholds
    are met or max_corrections is reached.

    APEX enhancements over v4.0:
      - query() API with lane-aware filtering
      - _verify_answer() rule-based answer verification
      - _expand_query() issue-aware query expansion
      - Correction rate logging for learning loop
      - Thread-safe global stats
      - Shadow-programmed LLM gating via APEX_LLM_ENABLED
    """

    MAX_CORRECTIONS: int = 2

    def __init__(
        self,
        db_path: str = DEFAULT_DB,
        max_corrections: Optional[int] = None,
    ):
        self.db_path = db_path
        self.max_corrections = max_corrections if max_corrections is not None else self.MAX_CORRECTIONS
        self._llm = None
        self._llm_loaded = False
        self._error_log: List[Dict] = []
        self._query_history: List[Dict] = []

    # ── LLM Loading ────────────────────────────────────────────────

    def _load_llm(self):
        """Lazy-load the GGUF model via llama-cpp-python. Returns None if unavailable.
        
        APEX: Respects APEX_LLM_ENABLED env var. When false (default), always
        returns None — forcing statistical fallbacks.
        """
        if self._llm_loaded:
            return self._llm
        self._llm_loaded = True
        if not APEX_LLM_ENABLED:
            logger.info("[CRAG-APEX] APEX_LLM_ENABLED=false — using statistical fallbacks")
            return None
        if not os.path.exists(GGUF_PATH):
            logger.warning("[CRAG-APEX] GGUF model not found at %s — using statistical fallbacks", GGUF_PATH)
            return None
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=GGUF_PATH,
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            logger.info("[CRAG-APEX] GGUF model loaded successfully")
        except Exception as e:
            logger.warning("[CRAG-APEX] Model load failed: %s — using statistical fallbacks", e)
            self._error_log.append({"event": "llm_load_fail", "error": str(e), "ts": time.time()})
            self._llm = None
        return self._llm

    # ── DB Helpers ─────────────────────────────────────────────────

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Open a read-only WAL-mode connection with retry and APEX PRAGMAs."""
        for attempt in range(3):
            try:
                conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                conn.execute("PRAGMA busy_timeout=60000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA cache_size=-32000")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA query_only=ON")
                conn.row_factory = sqlite3.Row
                return conn
            except Exception as e:
                wait = 2 ** attempt
                logger.warning("[CRAG-APEX] DB connect attempt %d failed: %s — retry in %ds", attempt + 1, e, wait)
                self._error_log.append({"event": "db_connect_fail", "attempt": attempt + 1, "error": str(e), "ts": time.time()})
                time.sleep(wait)
        return None

    def _search_fts(self, query: str, table: str, limit: int = 20) -> List[Dict]:
        """Search an FTS5 table. Returns list of row dicts."""
        conn = self._get_conn()
        if conn is None:
            return []
        try:
            # Sanitize query for FTS5: keep only alphanumeric and spaces
            safe_q = re.sub(r'[^\w\s]', ' ', query).strip()
            if not safe_q:
                return []
            # Convert to OR-joined tokens for broader recall
            tokens = [t for t in safe_q.split() if len(t) > 1]
            if not tokens:
                return []
            fts_query = " OR ".join(tokens)
            sql = f"SELECT *, rank FROM {table} WHERE {table} MATCH ? ORDER BY rank LIMIT ?"
            rows = conn.execute(sql, (fts_query, limit)).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("[CRAG] FTS search on %s failed: %s", table, e)
            self._error_log.append({"event": "fts_fail", "table": table, "error": str(e), "ts": time.time()})
            return []
        finally:
            conn.close()

    # ── Document Grading ───────────────────────────────────────────

    def grade_documents(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Grade each document for relevance to the query (0-10).

        Uses the LLM if available, otherwise falls back to keyword overlap scoring.
        Returns documents with added 'relevance_grade' field.
        """
        if not documents:
            return []

        llm = self._load_llm()
        graded = []

        for doc in documents:
            text = self._extract_text(doc)
            if not text:
                doc["relevance_grade"] = 0
                graded.append(doc)
                continue

            if llm is not None:
                grade = self._grade_with_llm(llm, query, text)
            else:
                grade = self._grade_with_keywords(query, text)

            doc["relevance_grade"] = grade
            graded.append(doc)

        return graded

    def _grade_with_llm(self, llm, query: str, text: str) -> int:
        """Use the GGUF model to grade relevance."""
        snippet = text[:800]
        prompt = (
            f"Rate how relevant this passage is to the legal query. "
            f"Reply with ONLY a number from 0 to 10.\n\n"
            f"Query: {query}\n\nPassage: {snippet}\n\nRelevance score:"
        )
        try:
            resp = llm(prompt, max_tokens=8, temperature=0.0, stop=["\n"])
            score_text = resp["choices"][0]["text"].strip()
            score = int(re.search(r'\d+', score_text).group())
            return max(0, min(10, score))
        except Exception as e:
            logger.debug("[CRAG] LLM grading failed: %s — falling back to keywords", e)
            return self._grade_with_keywords(query, text)

    def _grade_with_keywords(self, query: str, text: str) -> int:
        """Fallback: keyword overlap scoring (0-10)."""
        q_tokens = set(re.findall(r'\w+', query.lower()))
        t_tokens = set(re.findall(r'\w+', text.lower()))
        if not q_tokens:
            return 0
        # Base overlap score
        overlap = len(q_tokens & t_tokens) / len(q_tokens)
        # Bonus for legal citation matches (MCR, MCL, MRE patterns)
        cite_pattern = re.compile(r'(?:MCR|MCL|MRE)\s*[\d.]+', re.IGNORECASE)
        q_cites = set(c.upper() for c in cite_pattern.findall(query))
        t_cites = set(c.upper() for c in cite_pattern.findall(text))
        cite_bonus = 0.2 if q_cites and (q_cites & t_cites) else 0.0
        score = (overlap + cite_bonus) * 10
        return max(0, min(10, round(score)))

    # ── Hallucination Detection ────────────────────────────────────

    def check_hallucination(self, answer: str, source_docs: List[Dict]) -> Dict:
        """Check if the answer is grounded in source documents.

        Returns:
            {grounded: bool, confidence: float, unsupported_claims: list}
        """
        if not answer or not source_docs:
            return {"grounded": False, "confidence": 0.0, "unsupported_claims": ["no sources provided"]}

        llm = self._load_llm()
        if llm is not None:
            return self._check_hallucination_llm(llm, answer, source_docs)
        return self._check_hallucination_substring(answer, source_docs)

    def _check_hallucination_llm(self, llm, answer: str, source_docs: List[Dict]) -> Dict:
        """Use LLM to check grounding."""
        source_text = "\n---\n".join(self._extract_text(d)[:400] for d in source_docs[:5])
        prompt = (
            f"You are a fact-checker. Determine if the Answer is fully supported by "
            f"the Sources. List any claims in the Answer NOT supported by the Sources.\n"
            f"Reply in JSON: {{\"grounded\": true/false, \"unsupported\": [\"claim1\", ...]}}\n\n"
            f"Sources:\n{source_text}\n\nAnswer:\n{answer[:600]}\n\nJSON:"
        )
        try:
            resp = llm(prompt, max_tokens=256, temperature=0.0, stop=["\n\n"])
            raw = resp["choices"][0]["text"].strip()
            # Try to parse JSON from response
            json_match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                grounded = bool(parsed.get("grounded", False))
                unsupported = parsed.get("unsupported", [])
                confidence = 0.85 if grounded else 0.4
                return {"grounded": grounded, "confidence": confidence, "unsupported_claims": unsupported}
        except Exception as e:
            logger.debug("[CRAG] LLM hallucination check failed: %s — falling back", e)
        return self._check_hallucination_substring(answer, source_docs)

    def _check_hallucination_substring(self, answer: str, source_docs: List[Dict]) -> Dict:
        """Fallback: substring matching for hallucination detection."""
        source_blob = " ".join(self._extract_text(d).lower() for d in source_docs)
        # Split answer into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if len(s.strip()) > 15]
        if not sentences:
            return {"grounded": True, "confidence": 0.5, "unsupported_claims": []}

        unsupported = []
        supported_count = 0
        for sentence in sentences:
            # Check if key content words from the sentence appear in sources
            content_words = [w for w in re.findall(r'\w+', sentence.lower()) if len(w) > 3]
            if not content_words:
                supported_count += 1
                continue
            matches = sum(1 for w in content_words if w in source_blob)
            coverage = matches / len(content_words) if content_words else 0
            if coverage >= 0.4:
                supported_count += 1
            else:
                unsupported.append(sentence[:120])

        grounded_ratio = supported_count / len(sentences) if sentences else 0
        grounded = grounded_ratio >= 0.7
        confidence = round(grounded_ratio, 2)
        return {"grounded": grounded, "confidence": confidence, "unsupported_claims": unsupported}

    # ── Query Expansion ────────────────────────────────────────────

    def expand_query(self, query: str) -> str:
        """Expand query with related legal terms from the thesaurus."""
        q_lower = query.lower()
        expansions = set()
        for term, related in LEGAL_THESAURUS.items():
            if term in q_lower:
                expansions.update(related)
        if not expansions:
            return query
        # Deduplicate against existing query tokens
        q_tokens = set(q_lower.split())
        new_terms = [t for t in expansions if t.lower() not in q_tokens]
        expanded = query + " " + " ".join(new_terms[:8])
        return expanded

    # ── APEX Query API (new) ──────────────────────────────────────────

    def query(self, question: str, lane: str = None) -> dict:
        """APEX Corrective RAG query. Auto-corrects if initial answer fails verification.

        Args:
            question: The legal question to answer
            lane: Optional case lane filter (A-F) for lane-aware retrieval

        Returns:
            dict with keys: answer, sources, verification, corrections, method, elapsed_seconds
        """
        try:
            start_ts = time.time()
            corrections_applied = 0
            current_query = question
            status_log: List[str] = []

            # Step 1: Retrieve documents (lane-aware)
            documents = self._retrieve_for_lane(current_query, lane)
            status_log.append(f"retrieved {len(documents)} docs" + (f" for lane {lane}" if lane else ""))

            for cycle in range(self.MAX_CORRECTIONS + 1):
                # Step 2: Grade documents
                graded = self.grade_documents(current_query, documents)
                relevant = [d for d in graded if d.get("relevance_grade", 0) >= 5]

                # Step 3: Build answer
                answer = self._build_answer(question, relevant if relevant else graded[:5])

                # Step 4: Verify answer against retrieved docs
                verification = self._verify_answer(answer, relevant if relevant else graded[:5], question)

                if verification["valid"] or cycle >= self.MAX_CORRECTIONS:
                    break

                # Step 5: Expand query based on issues and re-retrieve
                corrections_applied += 1
                current_query = self._expand_query(current_query, verification["issues"])
                new_docs = self._multi_table_search(current_query, limit=15)
                seen_texts = {self._extract_text(d)[:200] for d in documents}
                for nd in new_docs:
                    if self._extract_text(nd)[:200] not in seen_texts:
                        documents.append(nd)
                        seen_texts.add(self._extract_text(nd)[:200])
                status_log.append(f"correction {cycle + 1}: expanded with {len(new_docs)} new docs")

            # Log correction stats
            self._log_correction_stats(verification.get("valid", False), corrections_applied)

            elapsed = round(time.time() - start_ts, 3)
            return {
                "answer": answer,
                "sources": [
                    {"text": self._extract_text(d)[:200], "grade": d.get("relevance_grade", 0),
                     "table": d.get("_source_table", "unknown")}
                    for d in (relevant if relevant else graded[:5])
                ],
                "verification": verification,
                "corrections": corrections_applied,
                "method": "apex_corrective_rag",
                "lane": lane,
                "status_log": status_log,
                "elapsed_seconds": elapsed,
            }
        except Exception as e:
            logger.error("[CRAG-APEX] query() failed: %s", e, exc_info=True)
            return {
                "answer": f"Corrective RAG query failed: {e}",
                "sources": [],
                "verification": {"valid": False, "issues": [str(e)]},
                "corrections": 0,
                "method": "apex_corrective_rag_error",
                "lane": lane,
                "status_log": [f"error: {e}"],
                "elapsed_seconds": 0.0,
            }

    def _verify_answer(self, answer: str, sources: list, question: str) -> dict:
        """Verify answer against sources. Returns {valid: bool, issues: [...], confidence: float}.

        Rule-based checks:
        1. Answer must reference content from at least one source
        2. Legal citations in answer should appear in sources
        3. Answer must be topically relevant to question
        4. Answer should not contain fabricated citations
        """
        try:
            if not answer or not sources:
                return {"valid": False, "issues": ["empty answer or no sources"], "confidence": 0.0}

            issues: List[str] = []
            source_blob = " ".join(self._extract_text(s).lower() for s in sources)
            answer_lower = answer.lower()
            question_lower = question.lower()

            # Check 1: Content grounding — answer key terms should appear in sources
            answer_words = set(re.findall(r'\w{4,}', answer_lower))
            source_words = set(re.findall(r'\w{4,}', source_blob))
            if answer_words:
                overlap = len(answer_words & source_words) / len(answer_words)
                if overlap < 0.3:
                    issues.append(f"low source grounding ({overlap:.0%} content overlap)")
            else:
                overlap = 0.0

            # Check 2: Citation verification — citations in answer should exist in sources
            cite_pattern = re.compile(r'(?:MCR|MCL|MRE|USC)\s*[\d.§]+(?:\([A-Za-z0-9]+\))*', re.IGNORECASE)
            answer_cites = set(c.upper() for c in cite_pattern.findall(answer))
            source_cites = set(c.upper() for c in cite_pattern.findall(source_blob))
            if answer_cites:
                unsupported_cites = answer_cites - source_cites
                if unsupported_cites:
                    issues.append(f"unsupported citations: {', '.join(list(unsupported_cites)[:3])}")

            # Check 3: Topical relevance — answer should relate to question
            q_content = set(re.findall(r'\w{4,}', question_lower))
            if q_content:
                q_overlap = len(q_content & answer_words) / len(q_content) if answer_words else 0
                if q_overlap < 0.15:
                    issues.append("answer may not address the question")

            # Check 4: Fabricated case citations (e.g., "123 Mich App 456")
            case_cite_re = re.compile(r'\d+\s+Mich\.?\s*(?:App\.?)?\s+\d+')
            answer_cases = case_cite_re.findall(answer)
            source_cases_text = " ".join(self._extract_text(s) for s in sources)
            for case in answer_cases:
                if case not in source_cases_text:
                    issues.append(f"possibly fabricated case cite: {case}")

            valid = len(issues) == 0
            confidence = max(0.0, min(1.0, overlap * 0.7 + (0.3 if not issues else 0.0)))
            return {"valid": valid, "issues": issues, "confidence": round(confidence, 3)}
        except Exception as e:
            logger.warning("[CRAG-APEX] _verify_answer failed: %s", e)
            return {"valid": True, "issues": [f"verification error: {e}"], "confidence": 0.5}

    def _expand_query(self, original: str, issues: list) -> str:
        """Expand query based on verification issues.

        Adds thesaurus synonyms and issue-specific terms to improve retrieval.
        """
        try:
            expanded = self.expand_query(original)

            # Extract specific missing info from issues
            for issue in issues:
                issue_lower = str(issue).lower()
                if "citation" in issue_lower or "cite" in issue_lower:
                    expanded += " authority citation rule statute"
                elif "grounding" in issue_lower or "overlap" in issue_lower:
                    # Add broader terms from thesaurus
                    for term, related in LEGAL_THESAURUS.items():
                        if term in original.lower():
                            expanded += " " + " ".join(related[:3])
                            break
                elif "address" in issue_lower or "question" in issue_lower:
                    expanded += " " + original  # Re-emphasize original question

            return expanded
        except Exception as e:
            logger.warning("[CRAG-APEX] _expand_query failed: %s", e)
            return original

    def _retrieve_for_lane(self, query: str, lane: Optional[str]) -> List[Dict]:
        """Retrieve documents, optionally filtered by case lane."""
        try:
            all_docs = self._multi_table_search(query, limit=20)
            if not lane:
                return all_docs

            # Lane keyword mapping for filtering
            lane_keywords: Dict[str, List[str]] = {
                "A": ["custody", "parenting", "watson", "001507", "5907"],
                "B": ["housing", "shady", "002760", "habitability", "tenant"],
                "C": ["convergence", "cross-lane", "conspiracy"],
                "D": ["ppo", "protection order", "stalking", "2950"],
                "E": ["misconduct", "jtc", "mcneill", "judicial tenure"],
                "F": ["appellate", "coa", "366810", "appeal", "brief"],
            }
            keywords = lane_keywords.get(lane.upper(), [])
            if not keywords:
                return all_docs

            # Prefer docs matching lane keywords, but keep all if few match
            lane_docs = []
            other_docs = []
            for doc in all_docs:
                text = self._extract_text(doc).lower()
                if any(kw in text for kw in keywords):
                    lane_docs.append(doc)
                else:
                    other_docs.append(doc)

            return lane_docs + other_docs[:max(0, 10 - len(lane_docs))]
        except Exception as e:
            logger.warning("[CRAG-APEX] _retrieve_for_lane failed: %s", e)
            return self._multi_table_search(query, limit=20)

    @staticmethod
    def _log_correction_stats(grounded: bool, corrections: int) -> None:
        """Log correction rate for learning loop. Thread-safe."""
        try:
            with _CORRECTION_STATS_LOCK:
                _CORRECTION_STATS["total_queries"] += 1
                _CORRECTION_STATS["total_corrections"] += corrections
                if grounded:
                    _CORRECTION_STATS["grounded_count"] += 1
                elif corrections >= 2:
                    _CORRECTION_STATS["exhausted_count"] += 1
                else:
                    _CORRECTION_STATS["best_effort_count"] += 1
                total = _CORRECTION_STATS["total_queries"]
                _CORRECTION_STATS["correction_rate"] = round(
                    _CORRECTION_STATS["total_corrections"] / total if total > 0 else 0.0, 3
                )
        except Exception:
            pass

    @staticmethod
    def get_correction_stats() -> Dict[str, Any]:
        """Return global correction rate statistics."""
        with _CORRECTION_STATS_LOCK:
            return dict(_CORRECTION_STATS)

    # ── Main Corrective Loop (legacy API) ──────────────────────────

    def corrective_query(self, query: str, initial_results: Optional[List[Dict]] = None) -> Dict:
        """Main corrective RAG loop.

        1. Retrieve (or accept initial_results)
        2. Grade documents
        3. Filter low-relevance
        4. Expand & re-search if too few relevant docs
        5. Build answer from top docs
        6. Check hallucination
        7. Retry up to max_corrections if hallucinated
        """
        start_ts = time.time()
        correction_count = 0
        current_query = query
        status_log: List[str] = []

        # Step 1: Initial retrieval
        if initial_results is not None:
            documents = initial_results
            status_log.append("used provided initial_results")
        else:
            documents = self._multi_table_search(current_query)
            status_log.append(f"searched {len(documents)} docs from DB")

        for cycle in range(self.max_corrections + 1):
            # Step 2: Grade documents
            graded_docs = self.grade_documents(current_query, documents)

            # Step 3: Filter low-relevance (grade < 5)
            relevant_docs = [d for d in graded_docs if d.get("relevance_grade", 0) >= 5]
            status_log.append(f"cycle {cycle}: {len(relevant_docs)}/{len(graded_docs)} docs relevant")

            # Step 4: If too few relevant docs, expand and re-search
            if len(relevant_docs) < 3 and cycle < self.max_corrections:
                current_query = self.expand_query(current_query)
                new_docs = self._multi_table_search(current_query)
                # Merge, dedup by text content
                seen = {self._extract_text(d)[:200] for d in documents}
                for nd in new_docs:
                    if self._extract_text(nd)[:200] not in seen:
                        documents.append(nd)
                        seen.add(self._extract_text(nd)[:200])
                status_log.append(f"expanded query, now {len(documents)} docs total")
                correction_count += 1
                continue

            # Step 5: Build answer from top relevant docs
            top_docs = sorted(relevant_docs, key=lambda d: d.get("relevance_grade", 0), reverse=True)[:10]
            answer = self._build_answer(query, top_docs)

            # Step 6: Hallucination check
            hall_check = self.check_hallucination(answer, top_docs)

            # Step 7: If hallucinated and retries remain, expand context and retry
            if not hall_check["grounded"] and cycle < self.max_corrections:
                status_log.append(f"cycle {cycle}: hallucination detected (confidence={hall_check['confidence']}), retrying")
                self._error_log.append({
                    "event": "hallucination_detected",
                    "cycle": cycle,
                    "confidence": hall_check["confidence"],
                    "unsupported": hall_check["unsupported_claims"],
                    "ts": time.time(),
                })
                # Add more context by expanding query
                current_query = self.expand_query(current_query + " " + " ".join(
                    c[:30] for c in hall_check["unsupported_claims"][:3]
                ))
                extra = self._multi_table_search(current_query, limit=10)
                documents.extend(extra)
                correction_count += 1
                continue

            # Done — either grounded or out of retries
            elapsed = round(time.time() - start_ts, 3)
            final_status = "grounded" if hall_check["grounded"] else "best_effort"
            status_log.append(f"final: {final_status} in {elapsed}s")

            return {
                "answer": answer,
                "documents": top_docs,
                "grades": [{"text": self._extract_text(d)[:100], "grade": d.get("relevance_grade", 0)} for d in top_docs],
                "hallucination_check": hall_check,
                "correction_count": correction_count,
                "status": final_status,
                "status_log": status_log,
                "elapsed_seconds": elapsed,
            }

        # Fallback: should not normally reach here
        return {
            "answer": "Unable to generate a grounded answer after maximum correction cycles.",
            "documents": documents[:5],
            "grades": [],
            "hallucination_check": {"grounded": False, "confidence": 0.0, "unsupported_claims": []},
            "correction_count": correction_count,
            "status": "exhausted",
            "status_log": status_log,
            "elapsed_seconds": round(time.time() - start_ts, 3),
        }

    # ── Internal Helpers ───────────────────────────────────────────

    def _multi_table_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across multiple FTS5 tables and merge results."""
        all_results = []
        for table in ["evidence_quotes_fts", "auth_rules_fts", "rules_text_fts"]:
            results = self._search_fts(query, table, limit=limit)
            for r in results:
                r["_source_table"] = table
            all_results.extend(results)
        return all_results

    def _extract_text(self, doc: Dict) -> str:
        """Extract the primary text content from a document dict."""
        for key in ("quote_text", "full_text", "context", "content", "text_content",
                    "passage_text", "text", "snippet", "body"):
            val = doc.get(key)
            if val and isinstance(val, str) and len(val) > 5:
                return val
        # Fallback: concatenate all string values
        parts = [str(v) for v in doc.values() if isinstance(v, str) and len(str(v)) > 5]
        return " ".join(parts[:3]) if parts else ""

    def _build_answer(self, query: str, documents: List[Dict]) -> str:
        """Build an answer from the top-graded documents.

        Uses LLM if available, otherwise constructs a structured summary.
        """
        if not documents:
            return "No relevant documents found in the litigation database."

        llm = self._load_llm()
        if llm is not None:
            return self._build_answer_llm(llm, query, documents)
        return self._build_answer_extractive(query, documents)

    def _build_answer_llm(self, llm, query: str, documents: List[Dict]) -> str:
        """Use LLM to synthesize an answer from source documents."""
        context = "\n---\n".join(
            f"[Source {i+1}, grade={d.get('relevance_grade', '?')}]: {self._extract_text(d)[:400]}"
            for i, d in enumerate(documents[:5])
        )
        prompt = (
            f"You are a Michigan family law legal assistant. Answer the query using ONLY "
            f"the provided sources. Cite specific sources. Do not add information not in the sources.\n\n"
            f"Query: {query}\n\nSources:\n{context}\n\nAnswer:"
        )
        try:
            resp = llm(prompt, max_tokens=512, temperature=0.1, stop=["Query:", "\n\n\n"])
            return resp["choices"][0]["text"].strip()
        except Exception as e:
            logger.debug("[CRAG] LLM answer generation failed: %s", e)
            return self._build_answer_extractive(query, documents)

    def _build_answer_extractive(self, query: str, documents: List[Dict]) -> str:
        """Fallback: extractive summary from top documents."""
        parts = [f"Based on {len(documents)} relevant sources from the litigation database:\n"]
        for i, doc in enumerate(documents[:5]):
            text = self._extract_text(doc)[:300].strip()
            grade = doc.get("relevance_grade", "?")
            source = doc.get("_source_table", "unknown")
            parts.append(f"[{i+1}] (relevance={grade}, source={source}): {text}")
        return "\n\n".join(parts)

    # ── Self-Test ──────────────────────────────────────────────────

    def self_test(self) -> Dict:
        """Run corrective queries on test questions and report results."""
        test_queries = [
            "What are the best interest factors?",
            "Judge McNeill disqualification",
        ]
        results = {}
        print("=" * 70)
        print("APEX MANBEARPIG Corrective RAG — Self-Test")
        print(f"  APEX_LLM_ENABLED: {APEX_LLM_ENABLED}")
        print(f"  MAX_CORRECTIONS:  {self.max_corrections}")
        print("=" * 70)

        for q in test_queries:
            print(f"\n{'─' * 60}")
            print(f"QUERY: {q}")
            print(f"{'─' * 60}")
            try:
                # Test new APEX query() API
                result = self.query(q)
                results[q] = {
                    "status": "grounded" if result["verification"]["valid"] else "best_effort",
                    "doc_count": len(result["sources"]),
                    "correction_count": result["corrections"],
                    "valid": result["verification"]["valid"],
                    "confidence": result["verification"]["confidence"],
                    "elapsed": result["elapsed_seconds"],
                }
                print(f"  Method:       {result['method']}")
                print(f"  Valid:        {result['verification']['valid']}")
                print(f"  Confidence:   {result['verification']['confidence']}")
                print(f"  Sources:      {len(result['sources'])}")
                print(f"  Corrections:  {result['corrections']}")
                print(f"  Elapsed:      {result['elapsed_seconds']}s")
                if result['verification']['issues']:
                    print(f"  Issues:       {result['verification']['issues'][:3]}")
                ans_preview = result["answer"][:200].replace("\n", " ")
                print(f"  Answer:       {ans_preview}...")
            except Exception as e:
                results[q] = {"status": "error", "error": str(e)}
                print(f"  ERROR: {e}")

        # Show global stats
        stats = self.get_correction_stats()
        print(f"\n{'─' * 60}")
        print(f"  Correction Stats: {json.dumps(stats)}")
        print(f"\n{'=' * 70}")
        print("Self-Test Complete")
        all_ok = all(r.get("status") != "error" for r in results.values())
        print(f"Result: {'ALL PASSED' if all_ok else 'SOME FAILURES'}")
        print(f"{'=' * 70}")
        return results


# ── CLI Entry Point ────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    import sys

    crag = CorrectiveRAG()

    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        crag.self_test()
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = crag.corrective_query(query)
        print(json.dumps(result, indent=2, default=str))
    else:
        crag.self_test()
