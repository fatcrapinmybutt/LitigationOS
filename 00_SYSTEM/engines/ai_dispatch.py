#!/usr/bin/env python3
"""
ai_dispatch.py — Unified AI/LLM Dispatch Layer for LitigationOS

Routes tasks to Gemini CLI, Ollama (Mistral/DeepSeek), and Copilot agents
with intelligent routing, fallback chains, caching, and quality scoring.

Usage:
    python ai_dispatch.py --task citation_verify --input "MCL 722.23"
    python ai_dispatch.py --task legal_analysis --input-file evidence.txt --model gemini
    python ai_dispatch.py --task batch --task-type extract_mcl --input-dir journals/ --output results.jsonl
    python ai_dispatch.py --status
"""

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DB_PATH = "D:/TEMP/ai_cache.db"
LOG_PATH = "D:/TEMP/ai_dispatch.log"
DEFAULT_TIMEOUT = 120  # seconds
GEMINI_RATE_LIMIT = 2.0  # seconds between requests
BATCH_PROGRESS_FILE = "D:/TEMP/ai_batch_progress.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
    ],
)
log = logging.getLogger("ai_dispatch")

# ---------------------------------------------------------------------------
# Prompt Templates — Michigan Legal Domain
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES: Dict[str, str] = {
    "citation_verify": (
        "You are a Michigan legal citation verification expert.\n"
        "Verify this Michigan citation is real and correctly formatted: {input}\n"
        "Check:\n"
        "1. Does this MCL section / MCR rule actually exist?\n"
        "2. Is the numbering format correct (e.g., MCL 722.23, MCR 2.119)?\n"
        "3. Is it currently in force or has it been repealed/amended?\n"
        "4. Provide the official title or heading of the cited provision.\n"
        "Return JSON: {{\"valid\": bool, \"citation\": str, \"title\": str, "
        "\"status\": \"active\"|\"repealed\"|\"amended\", \"notes\": str}}"
    ),
    "extract_mcl": (
        "You are a legal text extraction specialist for Michigan Compiled Laws.\n"
        "Extract ALL MCL (Michigan Compiled Laws) statute citations from the "
        "following text. Include the full citation number and any subsections.\n"
        "Text:\n{input}\n\n"
        "Return JSON array: [{{\"citation\": str, \"context\": str, \"subsection\": str|null}}]"
    ),
    "extract_mcr": (
        "You are a legal text extraction specialist for Michigan Court Rules.\n"
        "Extract ALL MCR (Michigan Court Rules) citations from the following text. "
        "Include rule numbers, subrules, and subsections.\n"
        "Text:\n{input}\n\n"
        "Return JSON array: [{{\"citation\": str, \"context\": str, \"subrule\": str|null}}]"
    ),
    "detect_violations": (
        "You are a Michigan family law violations analyst.\n"
        "Analyze the following text for violations including but not limited to:\n"
        "- Parental alienation (MCL 750.350a, custody interference)\n"
        "- Judicial misconduct (Canon 1, 2, 3 violations)\n"
        "- Due process violations (14th Amendment, MCR 2.119)\n"
        "- Discovery abuse (MCR 2.302–2.316)\n"
        "- Perjury or fraud upon the court\n"
        "- Failure to follow mandatory procedures\n"
        "Text:\n{input}\n\n"
        "Return JSON array: [{{\"violation_type\": str, \"description\": str, "
        "\"authority\": str, \"severity\": \"high\"|\"medium\"|\"low\", "
        "\"evidence_pointer\": str}}]"
    ),
    "score_bif": (
        "You are a Michigan Best Interest Factors scoring expert.\n"
        "Score this evidence against MCL 722.23 Best Interest Factors (a) through (l):\n"
        "(a) Love/affection/emotional ties\n(b) Capacity to give love/affection/guidance\n"
        "(c) Capacity to provide food/clothing/medical care\n"
        "(d) Length of time in stable environment\n(e) Permanence of family unit\n"
        "(f) Moral fitness\n(g) Mental/physical health\n"
        "(h) Home/school/community record\n(i) Reasonable preference of child\n"
        "(j) Willingness to facilitate relationship with other parent\n"
        "(k) Domestic violence\n(l) Any other relevant factor\n\n"
        "Evidence:\n{input}\n\n"
        "Return JSON: {{\"scores\": {{\"a\": int, ..., \"l\": int}}, "
        "\"summary\": str, \"strongest_factors\": [str], \"weakest_factors\": [str]}}"
    ),
    "draft_motion": (
        "You are a Michigan legal drafting expert.\n"
        "Draft a {motion_type} for Michigan {court} following MCR {rule}.\n"
        "Facts:\n{input}\n\n"
        "Include:\n1. Caption with proper court heading\n2. Statement of facts\n"
        "3. Legal argument with MCL/MCR citations\n4. Relief requested\n"
        "5. Verification / signature block\n"
        "Follow Michigan court formatting requirements strictly."
    ),
    "analyze_order": (
        "You are a Michigan appellate analysis expert.\n"
        "Analyze this court order for errors, inconsistencies, and appealable issues:\n"
        "{input}\n\n"
        "Check for:\n1. Errors of law (wrong legal standard applied)\n"
        "2. Clearly erroneous findings of fact\n3. Abuse of discretion\n"
        "4. Procedural defects (lack of notice, hearing violations)\n"
        "5. Inconsistencies with prior orders\n"
        "6. Constitutional issues\n\n"
        "Return JSON: {{\"errors\": [{{\"type\": str, \"description\": str, "
        "\"standard_of_review\": str, \"authority\": str}}], "
        "\"appealable\": bool, \"recommended_action\": str}}"
    ),
    "detect_bias": (
        "You are a judicial conduct analysis expert.\n"
        "Analyze the following for indicators of judicial bias per Michigan Code "
        "of Judicial Conduct Canons 1, 2, and 3:\n"
        "{input}\n\n"
        "Look for:\n- Predetermined outcomes\n- Ex parte communications\n"
        "- Failure to recuse when required\n- Disparate treatment of parties\n"
        "- Hostile or dismissive conduct toward one party\n"
        "- Ignoring evidence favorable to one side\n\n"
        "Return JSON: {{\"bias_indicators\": [{{\"indicator\": str, "
        "\"canon_violated\": str, \"severity\": str, \"evidence\": str}}], "
        "\"overall_assessment\": str, \"confidence\": float}}"
    ),
    "quantify_harm": (
        "You are a damages quantification expert for Michigan litigation.\n"
        "Quantify the harm/damages from these events:\n{input}\n\n"
        "Categories:\n- Economic damages (lost wages, costs, fees)\n"
        "- Non-economic damages (emotional distress, loss of consortium)\n"
        "- Punitive/exemplary damages potential\n"
        "- Attorney fees and costs recoverable\n"
        "- Statutory damages if applicable\n\n"
        "Return JSON: {{\"economic\": {{\"items\": [...], \"total\": float}}, "
        "\"non_economic\": {{\"items\": [...], \"estimated_range\": [float, float]}}, "
        "\"punitive_potential\": bool, \"total_estimated_range\": [float, float]}}"
    ),
    "build_timeline": (
        "You are a legal timeline construction specialist.\n"
        "Organize these events chronologically with precise dates where available:\n"
        "{input}\n\n"
        "For each event provide:\n1. Date (exact or estimated range)\n"
        "2. Event description\n3. Source document/evidence\n"
        "4. Legal significance\n5. Related parties\n\n"
        "Return JSON array sorted by date: [{{\"date\": str, \"event\": str, "
        "\"source\": str, \"significance\": str, \"parties\": [str]}}]"
    ),
    "contradiction_check": (
        "You are a legal contradiction detection specialist.\n"
        "Find contradictions between these statements or documents:\n{input}\n\n"
        "For each contradiction identify:\n1. Statement A and its source\n"
        "2. Statement B and its source\n3. Nature of the contradiction\n"
        "4. Which statement is better supported by evidence\n"
        "5. Legal implications of the contradiction\n\n"
        "Return JSON: {{\"contradictions\": [{{\"statement_a\": str, "
        "\"source_a\": str, \"statement_b\": str, \"source_b\": str, "
        "\"nature\": str, \"implication\": str}}]}}"
    ),
    "credibility_assess": (
        "You are a credibility assessment expert for legal proceedings.\n"
        "Assess credibility of these claims based on the provided evidence:\n"
        "{input}\n\n"
        "Evaluate against:\n- Internal consistency\n- Corroborating evidence\n"
        "- Prior inconsistent statements\n- Motive/bias of declarant\n"
        "- Specificity of details\n- Consistency with known facts\n\n"
        "Return JSON: {{\"claims\": [{{\"claim\": str, \"credibility_score\": int, "
        "\"supporting_evidence\": [str], \"undermining_evidence\": [str], "
        "\"assessment\": str}}], \"overall_credibility\": int}}"
    ),
    "pattern_detect": (
        "You are a behavioral pattern detection specialist for legal analysis.\n"
        "Detect patterns of behavior across these incidents:\n{input}\n\n"
        "Look for:\n- Escalating behavior patterns\n- Cyclical patterns\n"
        "- Coordinated actions\n- Systematic violations\n"
        "- Retaliatory patterns\n- Obstruction patterns\n\n"
        "Return JSON: {{\"patterns\": [{{\"pattern_type\": str, "
        "\"description\": str, \"incidents\": [str], \"frequency\": str, "
        "\"escalating\": bool, \"legal_significance\": str}}]}}"
    ),
    "remedy_map": (
        "You are a Michigan legal remedies expert.\n"
        "Map these violations to available legal remedies in Michigan:\n{input}\n\n"
        "For each violation identify:\n1. The specific remedy available\n"
        "2. The authority/statute providing the remedy\n"
        "3. The court/body with jurisdiction\n4. Filing requirements and deadlines\n"
        "5. Likelihood of success\n\n"
        "Return JSON: {{\"remedies\": [{{\"violation\": str, \"remedy\": str, "
        "\"authority\": str, \"jurisdiction\": str, \"deadline\": str, "
        "\"success_likelihood\": str}}]}}"
    ),
    "appeal_issue": (
        "You are a Michigan appellate advocacy specialist.\n"
        "Frame this as an appellate issue with the correct standard of review:\n"
        "{input}\n\n"
        "Provide:\n1. Issue statement (one sentence)\n"
        "2. Standard of review (de novo, clearly erroneous, abuse of discretion)\n"
        "3. Preservation (was it raised below? MCR 2.517)\n"
        "4. Key authorities\n5. Argument structure\n"
        "6. Relief requested\n\n"
        "Return JSON: {{\"issue\": str, \"standard_of_review\": str, "
        "\"preserved\": bool, \"preservation_citation\": str, "
        "\"authorities\": [str], \"argument_outline\": [str], \"relief\": str}}"
    ),
    "summarize": (
        "You are a legal document summarization specialist.\n"
        "Summarize the following legal text concisely, preserving all citations, "
        "key dates, party names, and legal conclusions:\n{input}\n\n"
        "Return JSON: {{\"summary\": str, \"key_citations\": [str], "
        "\"key_dates\": [str], \"parties\": [str], \"conclusions\": [str]}}"
    ),
    "classify": (
        "You are a legal document classification expert.\n"
        "Classify this document/text into appropriate legal categories:\n{input}\n\n"
        "Categories include: motion, order, opinion, brief, affidavit, exhibit, "
        "pleading, discovery, correspondence, transcript, statute, rule, other.\n\n"
        "Return JSON: {{\"primary_category\": str, \"subcategories\": [str], "
        "\"subject_areas\": [str], \"confidence\": float}}"
    ),
    "document_draft": (
        "You are a Michigan legal document drafting specialist.\n"
        "Draft the following legal document with proper formatting, citations, "
        "and Michigan court conventions:\n{input}\n\n"
        "Requirements:\n1. Use proper caption and heading format\n"
        "2. Include all required MCL/MCR citations\n"
        "3. Follow Michigan court filing conventions\n"
        "4. Include certificate of service template\n"
        "5. Use professional legal language throughout\n\n"
        "Return the complete document text ready for filing."
    ),
    "legal_analysis": (
        "You are a Michigan legal analysis expert.\n"
        "Perform a comprehensive legal analysis of the following:\n{input}\n\n"
        "Address:\n1. Applicable statutes (MCL) and court rules (MCR)\n"
        "2. Relevant case law from Michigan courts\n"
        "3. Legal standards and burdens of proof\n"
        "4. Strengths and weaknesses of the position\n"
        "5. Recommended strategy and next steps\n\n"
        "Return JSON: {{\"statutes\": [str], \"case_law\": [str], "
        "\"standard\": str, \"strengths\": [str], \"weaknesses\": [str], "
        "\"strategy\": str, \"next_steps\": [str]}}"
    ),
    "extract_entities": (
        "You are a legal named entity extraction specialist.\n"
        "Extract all named entities from this legal text:\n{input}\n\n"
        "Entity types: PERSON, JUDGE, ATTORNEY, COURT, STATUTE, CASE, DATE, "
        "LOCATION, ORGANIZATION, AMOUNT, EXHIBIT.\n\n"
        "Return JSON array: [{{\"entity\": str, \"type\": str, \"context\": str}}]"
    ),
    "score_evidence": (
        "You are a legal evidence scoring specialist.\n"
        "Score this evidence for admissibility and persuasive value:\n{input}\n\n"
        "Evaluate: relevance (MRE 401-402), authenticity (MRE 901), "
        "hearsay exceptions (MRE 803-804), prejudice vs probative (MRE 403).\n\n"
        "Return JSON: {{\"admissibility_score\": int, \"persuasive_score\": int, "
        "\"relevance\": str, \"hearsay_issues\": [str], "
        "\"authentication_method\": str, \"objection_risks\": [str]}}"
    ),
    "bif_analysis": (
        "You are a comprehensive MCL 722.23 Best Interest Factor analyst.\n"
        "Perform a deep BIF analysis using all available evidence:\n{input}\n\n"
        "For each factor (a)-(l) provide: current evidence supporting each parent, "
        "gaps in evidence, recommended discovery, and predicted judicial weighting.\n\n"
        "Return JSON: {{\"factors\": {{\"a\": {{\"parent1\": str, \"parent2\": str, "
        "\"gap\": str, \"recommendation\": str}}, ...}}, "
        "\"overall_assessment\": str, \"critical_gaps\": [str]}}"
    ),
}

# ---------------------------------------------------------------------------
# Model Registry & Routing
# ---------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "cmd": "gemini",
        "args_template": ["-p", "{prompt}"],
        "strengths": ["reasoning", "verification", "long-context", "drafting"],
        "max_tokens": 100_000,
        "rate_limit": GEMINI_RATE_LIMIT,
    },
    "mistral": {
        "cmd": "ollama",
        "args_template": ["run", "mistral", "{prompt}"],
        "strengths": ["extraction", "tagging", "fast", "summarization"],
        "max_tokens": 8_000,
        "rate_limit": 0.0,
    },
    "deepseek": {
        "cmd": "ollama",
        "args_template": ["run", "deepseek-r1", "{prompt}"],
        "strengths": ["analysis", "math", "logic", "scoring"],
        "max_tokens": 8_000,
        "rate_limit": 0.0,
    },
}

TASK_ROUTING: Dict[str, List[str]] = {
    "citation_verify":  ["gemini", "deepseek"],
    "extract_entities":  ["mistral", "gemini"],
    "extract_mcl":       ["mistral", "gemini"],
    "extract_mcr":       ["mistral", "gemini"],
    "legal_analysis":    ["gemini", "deepseek"],
    "document_draft":    ["gemini", "mistral"],
    "draft_motion":      ["gemini", "mistral"],
    "summarize":         ["mistral", "gemini"],
    "classify":          ["mistral", "deepseek"],
    "score_evidence":    ["deepseek", "gemini"],
    "score_bif":         ["deepseek", "gemini"],
    "detect_violations": ["gemini", "deepseek"],
    "detect_bias":       ["gemini", "deepseek"],
    "analyze_order":     ["gemini", "deepseek"],
    "quantify_harm":     ["gemini", "deepseek"],
    "build_timeline":    ["mistral", "gemini"],
    "contradiction_check": ["gemini", "deepseek"],
    "credibility_assess":  ["gemini", "deepseek"],
    "pattern_detect":      ["gemini", "deepseek"],
    "remedy_map":          ["gemini", "deepseek"],
    "appeal_issue":        ["gemini", "deepseek"],
    "bif_analysis":        ["gemini", "deepseek"],
}

# ---------------------------------------------------------------------------
# Cache Layer (SQLite)
# ---------------------------------------------------------------------------

class ResponseCache:
    """SQLite-backed LLM response cache with TTL support."""

    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    response TEXT NOT NULL,
                    quality_score INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    elapsed_sec REAL NOT NULL,
                    success INTEGER NOT NULL,
                    quality_score INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )"""
            )
            conn.commit()

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _cache_key(self, model: str, task: str, prompt: str) -> str:
        return f"{model}:{task}:{self._hash(prompt)}"

    def get(self, model: str, task: str, prompt: str) -> Optional[str]:
        key = self._cache_key(model, task, prompt)
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT response FROM cache WHERE key = ? AND expires_at > ?",
                (key, now),
            ).fetchone()
        if row:
            log.info("Cache HIT for %s/%s", model, task)
            return row[0]
        return None

    def put(
        self,
        model: str,
        task: str,
        prompt: str,
        response: str,
        quality_score: int = 0,
        ttl_hours: int = 72,
    ) -> None:
        key = self._cache_key(model, task, prompt)
        now = datetime.utcnow()
        expires = now + timedelta(hours=ttl_hours)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cache
                   (key, model, task, prompt_hash, response, quality_score, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    key,
                    model,
                    task,
                    self._hash(prompt),
                    response,
                    quality_score,
                    now.isoformat(),
                    expires.isoformat(),
                ),
            )
            conn.commit()

    def record_metric(
        self, model: str, task: str, elapsed: float, success: bool, quality: int = 0
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO metrics (model, task, elapsed_sec, success, quality_score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (model, task, elapsed, int(success), quality, datetime.utcnow().isoformat()),
            )
            conn.commit()

    def avg_latency(self, model: str, limit: int = 20) -> Optional[float]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT AVG(elapsed_sec) FROM (
                       SELECT elapsed_sec FROM metrics
                       WHERE model = ? AND success = 1
                       ORDER BY created_at DESC LIMIT ?
                   )""",
                (model, limit),
            ).fetchone()
        return row[0] if row and row[0] is not None else None

    def stats(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            by_model = conn.execute(
                "SELECT model, COUNT(*) FROM cache GROUP BY model"
            ).fetchall()
            metric_rows = conn.execute(
                """SELECT model,
                          COUNT(*) AS calls,
                          SUM(success) AS successes,
                          AVG(elapsed_sec) AS avg_sec,
                          AVG(quality_score) AS avg_quality
                   FROM metrics GROUP BY model"""
            ).fetchall()
        return {
            "cache_entries": total,
            "by_model": {r[0]: r[1] for r in by_model},
            "metrics": {
                r[0]: {
                    "calls": r[1],
                    "successes": r[2],
                    "avg_latency_sec": round(r[3], 2) if r[3] else None,
                    "avg_quality": round(r[4], 1) if r[4] else None,
                }
                for r in metric_rows
            },
        }

    def prune_expired(self) -> int:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE expires_at <= ?", (now,))
            conn.commit()
            return cursor.rowcount


# ---------------------------------------------------------------------------
# Quality Scorer
# ---------------------------------------------------------------------------

class QualityScorer:
    """Score LLM responses 0-100 for legal quality."""

    # Compiled regexes for citation detection
    _MCL_RE = re.compile(r"MCL\s+\d+\.\d+", re.IGNORECASE)
    _MCR_RE = re.compile(r"MCR\s+\d+\.\d+", re.IGNORECASE)
    _CASE_RE = re.compile(
        r"\d+\s+(Mich(?:\s+App)?|NW2d|NW\.2d)\s+\d+", re.IGNORECASE
    )
    _LEGAL_TERMS = [
        "motion", "order", "statute", "rule", "hearing", "jurisdiction",
        "plaintiff", "defendant", "petitioner", "respondent", "court",
        "custody", "parenting time", "best interest", "due process",
        "appeal", "standard of review", "abuse of discretion",
        "clearly erroneous", "de novo", "remand", "relief",
    ]

    @classmethod
    def score(cls, response: str, task: str = "") -> int:
        """Return a quality score 0-100."""
        if not response or not response.strip():
            return 0

        s = 0
        text_lower = response.lower()

        # Has real citations (+20)
        has_any_citation = bool(
            cls._MCL_RE.search(response)
            or cls._MCR_RE.search(response)
            or cls._CASE_RE.search(response)
        )
        if has_any_citation:
            s += 20

        # Cites specific MCL/MCR (+15)
        mcl_count = len(cls._MCL_RE.findall(response))
        mcr_count = len(cls._MCR_RE.findall(response))
        if mcl_count + mcr_count >= 1:
            s += 15

        # References case law (+15)
        if cls._CASE_RE.search(response):
            s += 15

        # Uses proper legal terminology (+10)
        term_hits = sum(1 for t in cls._LEGAL_TERMS if t in text_lower)
        if term_hits >= 3:
            s += 10

        # Addresses specific facts — heuristic: contains dates or names (+10)
        date_pattern = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
        if date_pattern.search(response) or len(response) > 500:
            s += 10

        # Identifies specific relief (+10)
        relief_terms = ["relief", "remedy", "damages", "injunction", "vacate", "remand"]
        if any(t in text_lower for t in relief_terms):
            s += 10

        # Follows filing format (+10) — has structured sections
        structure_markers = ["statement of facts", "argument", "conclusion",
                             "relief requested", "issue presented", "standard of review"]
        if any(m in text_lower for m in structure_markers):
            s += 10

        # No obvious hallucination signals (+10) — absence of hedging qualifiers
        hallucination_signals = [
            "i'm not sure", "i cannot verify", "this may not be accurate",
            "as an ai", "i don't have access",
        ]
        if not any(h in text_lower for h in hallucination_signals):
            s += 10

        return min(s, 100)

    @classmethod
    def extract_citations(cls, response: str) -> Dict[str, List[str]]:
        """Extract structured citations from response text."""
        return {
            "mcl": cls._MCL_RE.findall(response),
            "mcr": cls._MCR_RE.findall(response),
            "caselaw": cls._CASE_RE.findall(response),
        }


# ---------------------------------------------------------------------------
# Model Availability Checker
# ---------------------------------------------------------------------------

def check_model_available(model_name: str) -> Tuple[bool, str]:
    """Check if a model backend is reachable. Returns (available, message)."""
    cfg = MODEL_REGISTRY.get(model_name)
    if cfg is None:
        return False, f"Unknown model: {model_name}"

    cmd_bin = cfg["cmd"]
    if not shutil.which(cmd_bin):
        return False, f"Binary not found on PATH: {cmd_bin}"

    # Quick health probe
    try:
        if cmd_bin == "ollama":
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return False, f"ollama list failed: {result.stderr.strip()}"
            model_tag = cfg["args_template"][1]  # e.g. "mistral"
            if model_tag.split(":")[0] not in result.stdout.lower():
                return False, f"Model '{model_tag}' not pulled in Ollama"
            return True, "OK"
        elif cmd_bin == "gemini":
            # Just verify binary exists; actual auth checked at call time
            return True, "Binary found (auth checked at call time)"
        else:
            return False, f"Unknown backend binary: {cmd_bin}"
    except subprocess.TimeoutExpired:
        return False, "Health check timed out"
    except Exception as exc:
        return False, f"Health check error: {exc}"


# ---------------------------------------------------------------------------
# Core Dispatch Engine
# ---------------------------------------------------------------------------

class AIDispatch:
    """Unified AI/LLM dispatch with intelligent routing and fallback."""

    MODELS = MODEL_REGISTRY
    ROUTING = TASK_ROUTING
    TEMPLATES = PROMPT_TEMPLATES

    def __init__(self, cache_db: str = CACHE_DB_PATH):
        self.cache = ResponseCache(cache_db)
        self.scorer = QualityScorer()
        self._last_call_ts: Dict[str, float] = {}

    # -- routing helpers -----------------------------------------------------

    def _pick_chain(self, task: str) -> List[str]:
        """Return ordered model chain for a task, adjusted by latency."""
        chain = list(self.ROUTING.get(task, ["gemini", "mistral", "deepseek"]))

        # Re-order by historical latency if data exists
        latencies = {}
        for m in chain:
            avg = self.cache.avg_latency(m)
            if avg is not None:
                latencies[m] = avg

        if latencies:
            # Stable sort: faster model moves up only within same-priority tier
            chain.sort(key=lambda m: latencies.get(m, 999.0))

        return chain

    def _build_prompt(self, task: str, input_text: str, **kwargs: str) -> str:
        """Render the prompt template for a task."""
        template = self.TEMPLATES.get(task)
        if template is None:
            # Fallback: generic prompt
            return (
                f"Task: {task}\n\n"
                f"Input:\n{input_text}\n\n"
                "Provide a detailed, well-cited response in JSON where possible."
            )
        fmt_kwargs = {"input": input_text, **kwargs}
        try:
            return template.format(**fmt_kwargs)
        except KeyError:
            # If template has extra placeholders not supplied, fill with ''
            import string
            fields = [
                fn for _, fn, _, _ in string.Formatter().parse(template) if fn
            ]
            for f in fields:
                fmt_kwargs.setdefault(f, "")
            return template.format(**fmt_kwargs)

    # -- rate limiting -------------------------------------------------------

    def _wait_rate_limit(self, model: str) -> None:
        cfg = self.MODELS.get(model, {})
        rate = cfg.get("rate_limit", 0.0)
        if rate <= 0:
            return
        last = self._last_call_ts.get(model, 0.0)
        elapsed = time.time() - last
        if elapsed < rate:
            sleep_for = rate - elapsed
            log.debug("Rate-limiting %s: sleeping %.1fs", model, sleep_for)
            time.sleep(sleep_for)

    # -- subprocess call -----------------------------------------------------

    def _call_model(
        self, model: str, prompt: str, timeout: int = DEFAULT_TIMEOUT
    ) -> Tuple[bool, str, float]:
        """
        Call a model via subprocess.
        Returns (success, response_text, elapsed_seconds).
        """
        cfg = self.MODELS.get(model)
        if cfg is None:
            return False, f"Unknown model: {model}", 0.0

        self._wait_rate_limit(model)

        args = [cfg["cmd"]] + [
            a.replace("{prompt}", prompt) for a in cfg["args_template"]
        ]

        # Truncate prompt to model's max tokens (rough char estimate)
        max_chars = cfg.get("max_tokens", 8000) * 4
        if len(prompt) > max_chars:
            log.warning(
                "Prompt truncated from %d to %d chars for %s",
                len(prompt), max_chars, model,
            )
            prompt = prompt[:max_chars]
            args = [cfg["cmd"]] + [
                a.replace("{prompt}", prompt) for a in cfg["args_template"]
            ]

        log.info("Calling %s (timeout=%ds, prompt_len=%d)", model, timeout, len(prompt))
        t0 = time.time()

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "NO_COLOR": "1"},
            )
            elapsed = time.time() - t0
            self._last_call_ts[model] = time.time()

            if result.returncode != 0:
                err = result.stderr.strip() or result.stdout.strip()
                log.error("Model %s returned code %d: %s", model, result.returncode, err[:300])
                return False, err, elapsed

            response = result.stdout.strip()
            if not response:
                return False, "Empty response from model", elapsed

            return True, response, elapsed

        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            log.error("Model %s timed out after %.1fs", model, elapsed)
            return False, "TIMEOUT", elapsed
        except FileNotFoundError:
            return False, f"Binary not found: {cfg['cmd']}", 0.0
        except Exception as exc:
            elapsed = time.time() - t0
            log.error("Model %s error: %s", model, exc)
            return False, str(exc), elapsed

    # -- public interface ----------------------------------------------------

    def dispatch(
        self,
        task: str,
        input_text: str,
        model: Optional[str] = None,
        use_cache: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        **template_kwargs: str,
    ) -> Dict[str, Any]:
        """
        Dispatch a task to the best available model with fallback.

        Returns a result dict with keys:
            model, task, response, quality_score, citations, elapsed_sec,
            cached, fallback_used, errors
        """
        prompt = self._build_prompt(task, input_text, **template_kwargs)

        # Determine model chain
        if model:
            chain = [model]
        else:
            chain = self._pick_chain(task)

        # Check cache first (using primary model key)
        if use_cache:
            for m in chain:
                cached = self.cache.get(m, task, prompt)
                if cached is not None:
                    qscore = self.scorer.score(cached, task)
                    cites = self.scorer.extract_citations(cached)
                    return {
                        "model": m,
                        "task": task,
                        "response": cached,
                        "quality_score": qscore,
                        "citations": cites,
                        "elapsed_sec": 0.0,
                        "cached": True,
                        "fallback_used": False,
                        "errors": [],
                    }

        # Try each model in the chain
        errors: List[str] = []
        for idx, m in enumerate(chain):
            ok, response, elapsed = self._call_model(m, prompt, timeout)

            self.cache.record_metric(
                m, task, elapsed, ok,
                quality=self.scorer.score(response, task) if ok else 0,
            )

            if ok:
                qscore = self.scorer.score(response, task)
                cites = self.scorer.extract_citations(response)

                # Cache the successful response
                self.cache.put(m, task, prompt, response, quality_score=qscore)

                return {
                    "model": m,
                    "task": task,
                    "response": response,
                    "quality_score": qscore,
                    "citations": cites,
                    "elapsed_sec": round(elapsed, 2),
                    "cached": False,
                    "fallback_used": idx > 0,
                    "errors": errors,
                }
            else:
                errors.append(f"{m}: {response}")
                log.warning("Model %s failed, trying next in chain...", m)

        # All models failed
        return {
            "model": None,
            "task": task,
            "response": None,
            "quality_score": 0,
            "citations": {"mcl": [], "mcr": [], "caselaw": []},
            "elapsed_sec": 0.0,
            "cached": False,
            "fallback_used": True,
            "errors": errors,
        }

    def batch_dispatch(
        self,
        task: str,
        items: List[str],
        model: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        resume: bool = True,
        **template_kwargs: str,
    ) -> List[Dict[str, Any]]:
        """
        Process a list of items through dispatch with progress tracking.
        Supports resume by checking progress file.
        """
        results: List[Dict[str, Any]] = []
        completed_indices: set = set()

        # Load previous progress for resume
        if resume and os.path.exists(BATCH_PROGRESS_FILE):
            try:
                with open(BATCH_PROGRESS_FILE, "r", encoding="utf-8") as f:
                    prev = json.load(f)
                if prev.get("task") == task and prev.get("total") == len(items):
                    completed_indices = set(prev.get("completed_indices", []))
                    results = prev.get("results", [])
                    log.info(
                        "Resuming batch: %d/%d already done",
                        len(completed_indices), len(items),
                    )
            except Exception as exc:
                log.warning("Could not load batch progress: %s", exc)

        total = len(items)
        for idx, item in enumerate(items):
            if idx in completed_indices:
                continue

            log.info("Batch [%d/%d] processing...", idx + 1, total)
            result = self.dispatch(
                task, item, model=model, timeout=timeout, **template_kwargs
            )
            result["batch_index"] = idx
            results.append(result)
            completed_indices.add(idx)

            # Persist progress
            progress = {
                "task": task,
                "total": total,
                "completed_indices": sorted(completed_indices),
                "results": results,
                "updated_at": datetime.utcnow().isoformat(),
            }
            try:
                with open(BATCH_PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(progress, f, indent=2)
            except Exception as exc:
                log.warning("Could not save batch progress: %s", exc)

        # Cleanup progress file on full completion
        if len(completed_indices) == total:
            try:
                os.remove(BATCH_PROGRESS_FILE)
            except OSError:
                pass

        return results

    def status(self) -> Dict[str, Any]:
        """Return system status: model availability, cache stats, latencies."""
        model_status = {}
        for name in self.MODELS:
            avail, msg = check_model_available(name)
            avg_lat = self.cache.avg_latency(name)
            model_status[name] = {
                "available": avail,
                "message": msg,
                "avg_latency_sec": round(avg_lat, 2) if avg_lat else None,
                "strengths": self.MODELS[name]["strengths"],
                "max_tokens": self.MODELS[name]["max_tokens"],
            }

        return {
            "models": model_status,
            "cache": self.cache.stats(),
            "tasks_available": sorted(self.TEMPLATES.keys()),
            "routing_table": {k: v for k, v in self.ROUTING.items()},
        }


# ---------------------------------------------------------------------------
# Response Parser Utilities
# ---------------------------------------------------------------------------

def try_parse_json(text: str) -> Optional[Any]:
    """Attempt to extract and parse JSON from LLM response text."""
    if not text:
        return None

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fences
    json_block = re.search(r"```(?:json)?\s*\n([\s\S]*?)\n```", text)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find first { ... } or [ ... ] block
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break

    return None


def format_result(result: Dict[str, Any], output_json: bool = False) -> str:
    """Format a dispatch result for CLI output."""
    if output_json:
        return json.dumps(result, indent=2, default=str)

    lines = []
    lines.append(f"Model:    {result.get('model', 'N/A')}")
    lines.append(f"Task:     {result.get('task', 'N/A')}")
    lines.append(f"Quality:  {result.get('quality_score', 0)}/100")
    lines.append(f"Elapsed:  {result.get('elapsed_sec', 0)}s")
    lines.append(f"Cached:   {result.get('cached', False)}")
    lines.append(f"Fallback: {result.get('fallback_used', False)}")

    cites = result.get("citations", {})
    if any(cites.values()):
        lines.append("Citations:")
        for ctype, clist in cites.items():
            if clist:
                lines.append(f"  {ctype}: {', '.join(clist)}")

    if result.get("errors"):
        lines.append("Errors:")
        for e in result["errors"]:
            lines.append(f"  - {e[:200]}")

    lines.append("")
    lines.append("--- Response ---")
    resp = result.get("response") or "(no response)"
    lines.append(resp)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai_dispatch",
        description="LitigationOS Unified AI/LLM Dispatch Layer",
    )
    p.add_argument(
        "--task", "-t",
        choices=sorted(set(list(TASK_ROUTING.keys()) + list(PROMPT_TEMPLATES.keys()) + ["batch", "status"])),
        help="Task to perform",
    )
    p.add_argument("--input", "-i", help="Direct input text")
    p.add_argument("--input-file", "-f", help="Read input from file")
    p.add_argument("--input-dir", help="Directory of files for batch processing")
    p.add_argument("--model", "-m", choices=list(MODEL_REGISTRY.keys()), help="Force specific model")
    p.add_argument("--output", "-o", help="Output file path (JSONL for batch)")
    p.add_argument("--task-type", help="Task type for batch mode")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    p.add_argument("--no-cache", action="store_true", help="Skip cache lookup")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    p.add_argument("--status", action="store_true", help="Show system status")
    p.add_argument("--prune-cache", action="store_true", help="Remove expired cache entries")
    p.add_argument("--list-tasks", action="store_true", help="List available tasks")
    # Extra template kwargs
    p.add_argument("--motion-type", dest="motion_type", help="Motion type for draft_motion")
    p.add_argument("--court", help="Court for draft_motion")
    p.add_argument("--rule", help="MCR rule for draft_motion")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = AIDispatch()

    # -- status mode ---------------------------------------------------------
    if args.status or args.task == "status":
        status = dispatch.status()
        print(json.dumps(status, indent=2, default=str))
        return 0

    # -- prune cache ---------------------------------------------------------
    if args.prune_cache:
        removed = dispatch.cache.prune_expired()
        print(f"Pruned {removed} expired cache entries.")
        return 0

    # -- list tasks ----------------------------------------------------------
    if args.list_tasks:
        print("Available tasks:")
        for t in sorted(PROMPT_TEMPLATES.keys()):
            chain = TASK_ROUTING.get(t, ["gemini"])
            print(f"  {t:25s} -> {' > '.join(chain)}")
        return 0

    # -- validate task -------------------------------------------------------
    if not args.task:
        parser.print_help()
        return 1

    # -- batch mode ----------------------------------------------------------
    if args.task == "batch":
        batch_task = args.task_type
        if not batch_task:
            print("ERROR: --task-type required for batch mode", file=sys.stderr)
            return 1

        items: List[str] = []
        input_dir = args.input_dir
        if input_dir:
            input_path = Path(input_dir)
            if not input_path.is_dir():
                print(f"ERROR: Not a directory: {input_dir}", file=sys.stderr)
                return 1
            for fp in sorted(input_path.iterdir()):
                if fp.is_file() and fp.suffix in (".txt", ".md", ".json", ".csv"):
                    items.append(fp.read_text(encoding="utf-8", errors="replace"))
        elif args.input_file:
            # Treat each line or paragraph as an item
            text = Path(args.input_file).read_text(encoding="utf-8", errors="replace")
            items = [p.strip() for p in text.split("\n\n") if p.strip()]
        else:
            print("ERROR: --input-dir or --input-file required for batch", file=sys.stderr)
            return 1

        if not items:
            print("ERROR: No items found for batch processing", file=sys.stderr)
            return 1

        print(f"Processing {len(items)} items for task '{batch_task}'...")
        template_kwargs = {}
        if args.motion_type:
            template_kwargs["motion_type"] = args.motion_type
        if args.court:
            template_kwargs["court"] = args.court
        if args.rule:
            template_kwargs["rule"] = args.rule

        results = dispatch.batch_dispatch(
            batch_task, items, model=args.model, timeout=args.timeout,
            **template_kwargs,
        )

        # Write output
        if args.output:
            out_path = Path(args.output)
            with open(out_path, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(json.dumps(r, default=str) + "\n")
            print(f"Results written to {out_path}")
        else:
            for r in results:
                print(format_result(r, output_json=args.json))
                print("=" * 60)

        # Summary
        successes = sum(1 for r in results if r.get("response"))
        avg_quality = (
            sum(r.get("quality_score", 0) for r in results) / len(results)
            if results else 0
        )
        print(f"\nBatch complete: {successes}/{len(results)} succeeded, "
              f"avg quality: {avg_quality:.1f}/100")
        return 0

    # -- single dispatch mode ------------------------------------------------
    input_text = args.input
    if args.input_file:
        input_text = Path(args.input_file).read_text(encoding="utf-8", errors="replace")
    if not input_text:
        print("ERROR: --input or --input-file required", file=sys.stderr)
        return 1

    template_kwargs = {}
    if args.motion_type:
        template_kwargs["motion_type"] = args.motion_type
    if args.court:
        template_kwargs["court"] = args.court
    if args.rule:
        template_kwargs["rule"] = args.rule

    result = dispatch.dispatch(
        task=args.task,
        input_text=input_text,
        model=args.model,
        use_cache=not args.no_cache,
        timeout=args.timeout,
        **template_kwargs,
    )

    print(format_result(result, output_json=args.json))
    return 0 if result.get("response") else 1


# ---------------------------------------------------------------------------
# Self-Test (verifies model reachability and core logic)
# ---------------------------------------------------------------------------

def self_test() -> None:
    """Run self-diagnostics: check models, cache, scorer, and templates."""
    print("=" * 60)
    print("AI Dispatch — Self-Test")
    print("=" * 60)

    # 1. Template completeness
    print("\n[1] Prompt Templates")
    for task_name in sorted(TASK_ROUTING.keys()):
        has_tpl = task_name in PROMPT_TEMPLATES
        status = "OK" if has_tpl else "MISSING"
        print(f"  {task_name:25s} template: {status}")

    # 2. Model availability
    print("\n[2] Model Availability")
    for model_name in MODEL_REGISTRY:
        avail, msg = check_model_available(model_name)
        icon = "✓" if avail else "✗"
        print(f"  {icon} {model_name:12s} {msg}")

    # 3. Cache database
    print("\n[3] Cache Database")
    try:
        cache = ResponseCache()
        stats = cache.stats()
        print(f"  Path:    {CACHE_DB_PATH}")
        print(f"  Entries: {stats['cache_entries']}")
        print(f"  DB OK:   True")
    except Exception as exc:
        print(f"  DB ERROR: {exc}")

    # 4. Quality scorer
    print("\n[4] Quality Scorer")
    test_samples = [
        ("", 0),
        ("This is just random text with no legal content.", 10),
        (
            "Under MCL 722.23(a), the court must consider the love and affection "
            "between the parties. See Vodvarka v Grasmeyer, 259 Mich App 499 (2003). "
            "The motion for relief should be filed per MCR 2.119.",
            70,
        ),
    ]
    for sample_text, expected_min in test_samples:
        score = QualityScorer.score(sample_text)
        status = "OK" if score >= expected_min else "LOW"
        print(f"  Score={score:3d} (expect>={expected_min:2d}) [{status}] "
              f"'{sample_text[:60]}...'")

    # 5. JSON parser
    print("\n[5] JSON Response Parser")
    test_json_inputs = [
        ('{"valid": true}', True),
        ('Some text ```json\n{"a":1}\n``` more text', True),
        ('no json here', False),
        ('[{"x":1},{"x":2}]', True),
    ]
    for raw, should_parse in test_json_inputs:
        parsed = try_parse_json(raw)
        ok = (parsed is not None) == should_parse
        print(f"  {'OK' if ok else 'FAIL'}: parse={parsed is not None} "
              f"expected={should_parse} '{raw[:50]}'")

    # 6. Routing table
    print("\n[6] Routing Table")
    dispatch = AIDispatch()
    for task_name in sorted(TASK_ROUTING.keys()):
        chain = dispatch._pick_chain(task_name)
        print(f"  {task_name:25s} -> {' > '.join(chain)}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)
    sys.exit(main())
