"""
Local inference client — drop-in replacement for `from inferencesh import inference`.

Routes all requests through MANBEARPIG (MichiganLegalModel) instead of cloud APIs.
Emulates the inference.sh SDK's run(), agent(), upload_file(), and get_task() methods.

Local App Registry:
    legal-search    → model.query()          (FTS5 + TF-IDF retrieval)
    legal-rag       → RAGPipeline.search()   (multi-source retrieval + synthesis)
    doc-analyzer    → model.analyze_document()
    doc-generator   → model.generate_document()
    authority-search→ model.find_authority()
    citation-check  → model.check_citations()
    timeline-build  → model.build_timeline()
    irac-analysis   → model.irac_analysis()
    evidence-map    → model.map_evidence_to_grounds()
    gap-detect      → model.evidence_gap_detector()
    filing-ready    → model.filing_readiness_optimizer()
    deadline-score  → model.deadline_urgency_score()
    mcneill-pattern → model.mcneill_pattern_analysis()
    msc-scan        → model.msc_original_action_scan()
    multi-juris     → model.multi_jurisdiction_query()
    classify        → model.classify_intent()
    entities        → model.extract_entities()
    concepts        → model.match_concepts()
    status          → model.status()
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

# Resolve MANBEARPIG path — avoid shadow modules in repo root
_LOCAL_MODEL_DIR = Path(__file__).resolve().parent.parent / "local_model"
_PIPELINE_DIR = Path(__file__).resolve().parent.parent / "pipeline"


def _lazy_load_model():
    """Lazy-load MichiganLegalModel to avoid import cost at module level."""
    sys.path.insert(0, str(_LOCAL_MODEL_DIR))
    try:
        from inference_engine import MichiganLegalModel
        return MichiganLegalModel()
    except Exception as e:
        logger.error(f"Failed to load MANBEARPIG: {e}")
        return None
    finally:
        if str(_LOCAL_MODEL_DIR) in sys.path:
            sys.path.remove(str(_LOCAL_MODEL_DIR))


# App registry: maps app IDs to (method_name, input_key_mapping)
_APP_REGISTRY: Dict[str, tuple] = {
    "legal-search":     ("query",                     {"query": "text"}),
    "legal-rag":        ("_rag_search",               None),  # special handler
    "doc-analyzer":     ("analyze_document",           {"text": "text"}),
    "doc-generator":    ("generate_document",          {"doc_type": "doc_type", "params": "params"}),
    "authority-search": ("find_authority",             {"topic": "topic", "limit": "limit"}),
    "citation-check":   ("check_citations",            {"text": "text"}),
    "timeline-build":   ("build_timeline",             {"case_id": "case_id"}),
    "irac-analysis":    ("irac_analysis",              {"issue": "issue", "facts": "facts"}),
    "evidence-map":     ("map_evidence_to_grounds",    {"grounds": "grounds"}),
    "gap-detect":       ("evidence_gap_detector",      {"vehicle_name": "vehicle_name"}),
    "filing-ready":     ("filing_readiness_optimizer",  {}),
    "deadline-score":   ("deadline_urgency_score",     {"days_threshold": "days_threshold"}),
    "mcneill-pattern":  ("mcneill_pattern_analysis",    {}),
    "msc-scan":         ("msc_original_action_scan",    {"action_type": "action_type"}),
    "multi-juris":      ("multi_jurisdiction_query",    {"topic": "topic", "jurisdictions": "jurisdictions"}),
    "classify":         ("classify_intent",             {"text": "text"}),
    "entities":         ("extract_entities",            {"text": "text"}),
    "concepts":         ("match_concepts",              {"text": "text"}),
    "status":           ("status",                      {}),
}

# Aliases for inference.sh-style app IDs
_APP_ALIASES: Dict[str, str] = {
    "tavily/search-assistant": "legal-search",
    "exa/search": "legal-search",
    "exa/answer": "legal-search",
    "openrouter/claude-sonnet-45": "legal-search",
    "openrouter/claude-haiku-45": "legal-search",
    "infsh/flux-schnell": "status",  # image gen → status (no GPU)
}


class _TaskResult:
    """Represents a completed or pending task."""

    def __init__(self, task_id: str, status: str, output: Any = None):
        self.id = task_id
        self.status = status
        self.output = output
        self.created_at = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "output": self.output,
            "created_at": self.created_at,
        }


class inference:
    """
    Local inference client — mirrors the inferencesh.inference() API.

    Usage:
        client = inference()  # no API key needed
        result = client.run({"app": "legal-search", "input": {"query": "MCR 2.003"}})
    """

    def __init__(self, api_key: str = None, **kwargs):
        # api_key accepted for compatibility but ignored locally
        self._model = None
        self._tasks: Dict[str, _TaskResult] = {}
        self._sessions: Dict[str, dict] = {}

    @property
    def model(self):
        """Lazy-load MANBEARPIG on first use."""
        if self._model is None:
            self._model = _lazy_load_model()
        return self._model

    def run(
        self,
        config: dict,
        wait: bool = True,
        stream: bool = False,
        **kwargs,
    ) -> dict | Generator:
        """
        Run a local app. Mirrors inferencesh client.run() API.

        Args:
            config: {"app": "app-id", "input": {...}, "session": "...", "setup": {...}}
            wait: If False, returns task ID immediately (fire-and-forget).
            stream: If True, yields progress updates.

        Returns:
            dict with "status", "output", and optionally "session_id", "task_id".
        """
        app_id = config.get("app", "legal-search")
        user_input = config.get("input", {})
        session = config.get("session")

        # Resolve aliases
        resolved_app = _APP_ALIASES.get(app_id, app_id)

        task_id = str(uuid.uuid4())[:12]

        if not wait:
            # Fire-and-forget: execute and store result
            result = self._execute_app(resolved_app, user_input)
            self._tasks[task_id] = _TaskResult(task_id, "completed", result)
            return {"id": task_id, "status": "queued"}

        if stream:
            return self._stream_execute(resolved_app, user_input, task_id)

        # Synchronous execution
        result = self._execute_app(resolved_app, user_input)

        response = {
            "status": "completed",
            "output": result,
            "task_id": task_id,
        }

        # Session management
        if session:
            session_id = session if session != "new" else str(uuid.uuid4())[:12]
            self._sessions[session_id] = {
                "created": time.time(),
                "last_used": time.time(),
                "history": self._sessions.get(session_id, {}).get("history", []),
            }
            self._sessions[session_id]["history"].append({
                "app": app_id,
                "input": user_input,
                "output": result,
                "ts": time.time(),
            })
            response["session_id"] = session_id

        return response

    def _execute_app(self, app_id: str, user_input: dict) -> Any:
        """Route app execution to the correct MANBEARPIG method."""
        if not self.model:
            return {"error": "MANBEARPIG model not loaded", "status": "error"}

        registry_entry = _APP_REGISTRY.get(app_id)
        if not registry_entry:
            return {"error": f"Unknown app: {app_id}", "available": list(_APP_REGISTRY.keys())}

        method_name, key_mapping = registry_entry

        # Special handler for RAG
        if method_name == "_rag_search":
            return self._handle_rag(user_input)

        method = getattr(self.model, method_name, None)
        if not method:
            return {"error": f"MANBEARPIG method '{method_name}' not found"}

        try:
            if key_mapping is None:
                return method(**user_input)
            elif not key_mapping:
                return method()
            else:
                # Map user input keys to method parameter names
                kwargs = {}
                for user_key, method_key in key_mapping.items():
                    if user_key in user_input:
                        kwargs[method_key] = user_input[user_key]
                return method(**kwargs) if kwargs else method()
        except TypeError as e:
            # Fallback: try positional arg
            query = user_input.get("query") or user_input.get("text") or user_input.get("topic", "")
            try:
                return method(query)
            except Exception:
                return {"error": str(e), "method": method_name}
        except Exception as e:
            return {"error": str(e), "method": method_name, "status": "error"}

    def _handle_rag(self, user_input: dict) -> dict:
        """RAG pipeline: retrieve from multiple sources, then synthesize."""
        query = user_input.get("query", "")
        if not query:
            return {"error": "query is required for RAG"}

        results = {
            "retrieval": self.model.retrieve(query, top_k=10),
            "authority": self.model.find_authority(query, limit=5),
            "concepts": self.model.match_concepts(query),
        }

        # Synthesize using the main query method
        synthesis = self.model.query(query)

        return {
            "sources": results,
            "synthesis": synthesis.get("response", ""),
            "confidence": synthesis.get("confidence", 0.0),
            "retrieval_count": len(results["retrieval"]),
            "authority_count": len(results["authority"]),
        }

    def _stream_execute(self, app_id: str, user_input: dict, task_id: str) -> Generator:
        """Yield progress updates (emulates streaming)."""
        yield {"status": "starting", "task_id": task_id, "progress": 0}
        yield {"status": "processing", "task_id": task_id, "progress": 30}

        result = self._execute_app(app_id, user_input)

        yield {"status": "processing", "task_id": task_id, "progress": 90}
        yield {"status": "completed", "task_id": task_id, "output": result, "progress": 100}

    def get_task(self, task_id: str) -> dict:
        """Check status of a fire-and-forget task."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        return task.to_dict()

    def upload_file(self, path: str, options: dict = None) -> dict:
        """
        'Upload' a file — locally this just validates and returns a URI.
        No actual upload; files are accessed by local path.
        """
        p = Path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}

        file_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        return {
            "uri": f"local://{p.resolve()}",
            "filename": p.name,
            "size": p.stat().st_size,
            "hash": file_hash,
            "content_type": _guess_content_type(p.suffix),
        }

    def agent(self, config) -> "LocalAgent":
        """
        Create a local agent. Mirrors inferencesh client.agent() API.

        Args:
            config: str (agent reference) or dict with agent configuration.
        """
        from sdk.agent_sdk import LocalAgent
        return LocalAgent(self, config)

    def list_apps(self) -> List[dict]:
        """List all available local apps."""
        apps = []
        for app_id, (method_name, _) in _APP_REGISTRY.items():
            apps.append({
                "id": app_id,
                "method": method_name,
                "type": "local",
                "description": _APP_DESCRIPTIONS.get(app_id, ""),
            })
        return apps


class async_inference(inference):
    """Async version — same API but methods are awaitable (thin wrapper)."""

    async def run(self, config: dict, **kwargs) -> dict:
        return super().run(config, **kwargs)

    async def get_task(self, task_id: str) -> dict:
        return super().get_task(task_id)

    async def upload_file(self, path: str, options: dict = None) -> dict:
        return super().upload_file(path, options)


# ── Helpers ────────────────────────────────────────────────────────

_APP_DESCRIPTIONS = {
    "legal-search": "Full-text + TF-IDF legal search over 694-table litigation DB",
    "legal-rag": "Multi-source RAG pipeline (retrieval + authority + concepts + synthesis)",
    "doc-analyzer": "Analyze legal documents for citations, claims, strengths/weaknesses",
    "doc-generator": "Generate court-ready documents from templates + DB authority",
    "authority-search": "Search MCR, MCL, case law, and statute authority chains",
    "citation-check": "Verify legal citations (MCR, MCL, MRE) against the database",
    "timeline-build": "Build chronological case timeline from evidence + docket events",
    "irac-analysis": "Structured IRAC legal reasoning with authority chain",
    "evidence-map": "Map evidence to legal grounds (3-pass: direct, FTS, pattern)",
    "gap-detect": "Detect evidence gaps per filing vehicle",
    "filing-ready": "Filing readiness optimizer — recommends next actions",
    "deadline-score": "Score all deadlines by urgency (CRITICAL/URGENT/APPROACHING)",
    "mcneill-pattern": "Deep analysis of Judge McNeill's pattern of conduct",
    "msc-scan": "Michigan Supreme Court original action viability scan",
    "multi-juris": "Multi-jurisdiction query across MI Circuit, COA, MSC, Federal, JTC",
    "classify": "Classify intent using Naive Bayes",
    "entities": "Extract legal entities (MCR, MCL, case names) from text",
    "concepts": "Match legal concepts (best-interest factors, disqualification, etc.)",
    "status": "MANBEARPIG engine status and health check",
}


def _guess_content_type(suffix: str) -> str:
    return {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".csv": "text/csv",
        ".html": "text/html",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix.lower(), "application/octet-stream")
