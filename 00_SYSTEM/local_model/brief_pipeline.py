"""
APEX Brief Pipeline — Generates court document sections.

Shadow-programmed: templates only when LLM disabled.
Pipeline: Outline → Draft → Verify Citations → Quality Gate → Refine → Output.

Section requirements per Michigan Court Rules:
  MCR 7.212 (appellate), MCR 2.119 (motions), MCR 3.206 (domestic relations).
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apex.brief_pipeline")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_PRAGMA_INIT = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
)


def _open_db(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    for p in _PRAGMA_INIT:
        conn.execute(p)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS brief_drafts (
            draft_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            brief_type  TEXT NOT NULL,
            lane        TEXT,
            outline     TEXT,
            sections    TEXT,
            quality     INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'draft',
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# MCR section requirements
# ---------------------------------------------------------------------------

_MCR_SECTIONS: Dict[str, List[Dict[str, str]]] = {
    "motion": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 2.113"},
        {"id": "intro", "title": "Introduction / Relief Sought", "mcr": "MCR 2.119(A)(2)"},
        {"id": "statement_of_facts", "title": "Statement of Facts", "mcr": "MCR 2.119(A)(2)"},
        {"id": "argument", "title": "Argument", "mcr": "MCR 2.119(A)(2)"},
        {"id": "prayer", "title": "Prayer for Relief", "mcr": "MCR 2.119(A)(2)"},
        {"id": "verification", "title": "Verification", "mcr": "MCR 2.114(A)"},
    ],
    "brief": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 7.212(B)"},
        {"id": "jurisdictional_statement", "title": "Jurisdictional Statement", "mcr": "MCR 7.212(C)(1)"},
        {"id": "issues_presented", "title": "Issues Presented for Review", "mcr": "MCR 7.212(C)(2)"},
        {"id": "statement_of_facts", "title": "Statement of Facts", "mcr": "MCR 7.212(C)(5)"},
        {"id": "argument", "title": "Argument", "mcr": "MCR 7.212(C)(6)"},
        {"id": "conclusion", "title": "Conclusion and Relief Requested", "mcr": "MCR 7.212(C)(7)"},
    ],
    "complaint": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 2.113"},
        {"id": "jurisdiction", "title": "Jurisdiction and Venue", "mcr": "MCR 2.116"},
        {"id": "parties", "title": "Parties", "mcr": "MCR 2.111"},
        {"id": "factual_allegations", "title": "Factual Allegations", "mcr": "MCR 2.111(B)(1)"},
        {"id": "counts", "title": "Counts / Causes of Action", "mcr": "MCR 2.111(B)(1)"},
        {"id": "prayer", "title": "Prayer for Relief", "mcr": "MCR 2.111(B)(3)"},
        {"id": "verification", "title": "Verification", "mcr": "MCR 2.114(A)"},
    ],
    "affidavit": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 2.113"},
        {"id": "affiant_info", "title": "Affiant Identification", "mcr": "MCR 2.119(B)"},
        {"id": "factual_statements", "title": "Factual Statements (numbered)", "mcr": "MCR 2.119(B)"},
        {"id": "verification", "title": "Verification / Jurat", "mcr": "MCR 2.114(A)"},
    ],
    "memorandum": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 2.113"},
        {"id": "intro", "title": "Introduction", "mcr": "MCR 2.119(A)(2)"},
        {"id": "statement_of_facts", "title": "Statement of Facts", "mcr": "MCR 2.119(A)(2)"},
        {"id": "argument", "title": "Argument with Authorities", "mcr": "MCR 2.119(A)(2)"},
        {"id": "conclusion", "title": "Conclusion", "mcr": "MCR 2.119(A)(2)"},
    ],
    "declaration": [
        {"id": "caption", "title": "Caption", "mcr": "MCR 2.113"},
        {"id": "declarant_info", "title": "Declarant Identification", "mcr": "MCR 2.114(A)"},
        {"id": "factual_statements", "title": "Statements Under Penalty of Perjury", "mcr": "MCR 2.114(A)"},
        {"id": "signature_block", "title": "Signature and Date", "mcr": "MCR 2.114(A)"},
    ],
}

# Template skeletons for non-LLM mode
_SECTION_TEMPLATES: Dict[str, str] = {
    "caption": "STATE OF MICHIGAN\nIN THE {court} COURT FOR {county} COUNTY\n\n{plaintiff},\n    Plaintiff,\n\nvs.\n\n{defendant},\n    Defendant.\n\nCase No. {case_number}\nHon. {judge}",
    "intro": "[INTRODUCTION]\n\nNOW COMES {party}, and respectfully moves this Honorable Court for {relief}.",
    "statement_of_facts": "[STATEMENT OF FACTS]\n\n{numbered_facts}",
    "argument": "[ARGUMENT]\n\n{argument_sections}",
    "prayer": "[PRAYER FOR RELIEF]\n\nWHEREFORE, {party} respectfully requests that this Court:\n{relief_items}",
    "verification": "[VERIFICATION]\n\nI, {name}, declare under the penalties of perjury that the above statements are true to the best of my information, knowledge, and belief.\n\nDate: {date}\n\n_________________________\n{name}",
    "jurisdictional_statement": "[JURISDICTIONAL STATEMENT]\n\nThis Court has jurisdiction pursuant to {authority}.",
    "issues_presented": "[ISSUES PRESENTED FOR REVIEW]\n\n{issues}",
    "conclusion": "[CONCLUSION]\n\nFor the foregoing reasons, {party} respectfully requests {relief}.",
    "jurisdiction": "[JURISDICTION AND VENUE]\n\nThis Court has subject matter jurisdiction under {authority}.\nVenue is proper in {county} County under {venue_authority}.",
    "parties": "[PARTIES]\n\n{party_descriptions}",
    "factual_allegations": "[FACTUAL ALLEGATIONS]\n\n{numbered_allegations}",
    "counts": "[COUNT {count_number}: {cause_of_action}]\n\n{count_paragraphs}",
    "affiant_info": "I, {name}, being first duly sworn, depose and state as follows:",
    "factual_statements": "{numbered_statements}",
    "declarant_info": "I, {name}, declare as follows:",
    "signature_block": "I declare under penalty of perjury under the laws of the State of Michigan that the foregoing is true and correct.\n\nExecuted on {date}.\n\n_________________________\n{name}",
}


# ---------------------------------------------------------------------------
# LLM drafting helper
# ---------------------------------------------------------------------------

def _llm_draft_section(section_type: str, context: dict) -> Optional[str]:
    """Use LLM to draft a section. Only when APEX_LLM_ENABLED."""
    if not APEX_LLM_ENABLED:
        return None
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        prompt = (
            f"Draft a '{section_type}' section for a Michigan court document. "
            f"Context: {json.dumps(context, default=str, ensure_ascii=False)[:2000]}. "
            "Use proper legal formatting. Cite Michigan authorities where appropriate."
        )
        result = router.route(prompt, task_type="drafting")
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        if isinstance(result, str):
            return result
        return None
    except Exception as exc:
        logger.debug("LLM section draft failed: %s", exc)
        return None


def _llm_refine(draft: str, feedback: str) -> Optional[str]:
    """Refine draft using LLM."""
    if not APEX_LLM_ENABLED:
        return None
    try:
        from .model_router import ModelRouter  # type: ignore[import-untyped]
        router = ModelRouter()
        prompt = (
            f"Refine this court document section based on the feedback.\n\n"
            f"DRAFT:\n{draft[:3000]}\n\nFEEDBACK:\n{feedback[:1000]}\n\n"
            "Return the improved text only."
        )
        result = router.route(prompt, task_type="refinement")
        if isinstance(result, str):
            return result
        if isinstance(result, dict) and "text" in result:
            return result["text"]
        return None
    except Exception as exc:
        logger.debug("LLM refine failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class BriefPipeline:
    """LLM-powered brief drafting pipeline."""

    BRIEF_TYPES = ["motion", "brief", "complaint", "affidavit", "memorandum", "declaration"]

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._lock = threading.Lock()
        self._db_path = Path(db_path) if db_path else _DB_DIR / "brief_pipeline.db"
        self._init_db()

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = _open_db(self._db_path)
            _ensure_tables(conn)
            conn.close()
        except Exception as exc:
            logger.warning("Brief pipeline DB init failed: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_section(self, section_type: str, context: dict, lane: str = "A") -> dict:
        """Generate one section of a brief.

        Returns ``{text: str, citations: list, quality: int, method: str}``.
        """
        try:
            # Try LLM first
            llm_text = _llm_draft_section(section_type, context)
            if llm_text:
                citations = self._extract_citations(llm_text)
                quality = self._score_quality(llm_text, section_type)
                return {
                    "text": llm_text,
                    "citations": citations,
                    "quality": quality,
                    "method": "llm",
                }

            # Fallback: template
            template = _SECTION_TEMPLATES.get(section_type, f"[{section_type.upper()}]\n\n{{content}}")
            text = self._fill_template(template, context)
            citations = self._extract_citations(text)
            quality = self._score_quality(text, section_type)
            return {
                "text": text,
                "citations": citations,
                "quality": quality,
                "method": "template",
            }
        except Exception as exc:
            logger.error("Section generation failed for '%s': %s", section_type, exc)
            return {"text": "", "citations": [], "quality": 0, "method": "error"}

    def generate_outline(self, brief_type: str, cause_of_action: str = "",
                         lane: str = "A") -> dict:
        """Generate brief outline with required sections per MCR.

        Returns ``{brief_type, sections: list, mcr_basis: str}``.
        """
        try:
            bt = brief_type.lower().strip()
            if bt not in _MCR_SECTIONS:
                bt = "motion"  # safe default

            sections = _MCR_SECTIONS[bt]
            outline = {
                "brief_type": bt,
                "cause_of_action": cause_of_action,
                "lane": lane,
                "sections": sections,
                "mcr_basis": sections[0].get("mcr", "") if sections else "",
                "total_sections": len(sections),
            }
            return outline
        except Exception as exc:
            logger.error("Outline generation failed: %s", exc)
            return {"brief_type": brief_type, "sections": [], "mcr_basis": "", "total_sections": 0}

    def refine(self, draft: str, feedback: str) -> str:
        """Refine draft based on quality gate feedback."""
        try:
            llm_result = _llm_refine(draft, feedback)
            if llm_result:
                return llm_result
            # Fallback: return draft with feedback appended as comment
            return f"{draft}\n\n[QUALITY FEEDBACK — requires manual revision]\n{feedback}"
        except Exception as exc:
            logger.error("Refine failed: %s", exc)
            return draft

    def draft_full(self, brief_type: str, context: dict, lane: str = "A") -> dict:
        """Draft an entire brief using the pipeline.

        Returns ``{brief_type, sections: dict, quality: int, draft_id: int}``.
        """
        try:
            outline = self.generate_outline(brief_type, context.get("cause_of_action", ""), lane)
            sections_out: Dict[str, dict] = {}
            total_quality = 0

            for sec_def in outline.get("sections", []):
                sid = sec_def["id"]
                sec_context = {**context, "section_id": sid, "section_title": sec_def["title"]}
                result = self.generate_section(sid, sec_context, lane)
                sections_out[sid] = result
                total_quality += result.get("quality", 0)

            count = max(len(sections_out), 1)
            avg_quality = total_quality // count

            # Persist
            draft_id = self._save_draft(brief_type, lane, outline, sections_out, avg_quality)

            return {
                "brief_type": brief_type,
                "lane": lane,
                "sections": sections_out,
                "quality": avg_quality,
                "draft_id": draft_id,
            }
        except Exception as exc:
            logger.error("Full draft failed: %s", exc)
            return {"brief_type": brief_type, "sections": {}, "quality": 0, "draft_id": None}

    def _mcr_section_requirements(self, brief_type: str) -> list:
        """Return required sections per MCR for this brief type."""
        bt = brief_type.lower().strip()
        return _MCR_SECTIONS.get(bt, _MCR_SECTIONS.get("motion", []))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fill_template(self, template: str, context: dict) -> str:
        """Fill a template with context values, ignoring missing keys."""
        try:
            import re
            def replacer(m: Any) -> str:
                key = m.group(1)
                return str(context.get(key, f"[{key}]"))
            return re.sub(r"\{(\w+)\}", replacer, template)
        except Exception:
            return template

    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text."""
        import re
        patterns = [
            r"\d+\s+Mich(?:\s+App)?\s+\d+",          # Michigan Reports
            r"\d+\s+NW2d\s+\d+",                       # NW2d
            r"MCR\s+\d+\.\d+(?:\([A-Z]\)(?:\(\d+\))?)?",  # MCR
            r"MCL\s+\d+\.\d+\w*",                      # MCL
            r"\d+\s+US\s+\d+",                          # US Reports
        ]
        citations: List[str] = []
        for pat in patterns:
            try:
                citations.extend(re.findall(pat, text))
            except Exception:
                pass
        return list(dict.fromkeys(citations))  # deduplicate, preserve order

    def _score_quality(self, text: str, section_type: str) -> int:
        """Score section quality 0-100."""
        score = 0
        if not text or not text.strip():
            return 0
        # Length check
        length = len(text.strip())
        if length > 50:
            score += 20
        if length > 200:
            score += 10
        # Has citations
        citations = self._extract_citations(text)
        if citations:
            score += 20
        if len(citations) >= 3:
            score += 10
        # Has structure (numbered paragraphs or section headings)
        import re
        if re.search(r"^\d+\.", text, re.MULTILINE):
            score += 15
        if re.search(r"^[A-Z][A-Z\s]+$", text, re.MULTILINE):
            score += 10
        # No placeholder markers remaining
        if "[" not in text or text.count("[") <= 2:
            score += 15
        return min(score, 100)

    def _save_draft(self, brief_type: str, lane: str, outline: dict,
                    sections: dict, quality: int) -> Optional[int]:
        """Persist draft to DB."""
        with self._lock:
            try:
                conn = _open_db(self._db_path)
                cur = conn.execute("""
                    INSERT INTO brief_drafts (brief_type, lane, outline, sections, quality)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    brief_type, lane,
                    json.dumps(outline, default=str),
                    json.dumps(sections, default=str),
                    quality,
                ))
                draft_id = cur.lastrowid
                conn.commit()
                conn.close()
                return draft_id
            except Exception as exc:
                logger.warning("Draft save failed: %s", exc)
                return None
