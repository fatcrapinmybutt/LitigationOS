"""
MBP LitigationOS 2026 — Master Orchestrator Engine
====================================================
THE MANBEARPIG litigation AI command center.

Coordinates ALL 25 engines through a unified pipeline with:
- Intelligent query routing by legal intent
- Circuit breaker pattern for fault tolerance
- Health monitoring across entire engine fleet
- Graceful degradation when engines are unavailable
- Parallel search with RRF result fusion
- Filing-type-specific pipeline selection
- Full-depth analysis across all engines

This is the BRAIN. It must NEVER crash.

Author: Andrew Pigors (pro se litigant)
System: MBP LitigationOS 2026 v1.0
"""

import collections
import concurrent.futures
import importlib
import json
import os
import sqlite3
import sys
import time
import traceback
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Engine registry: engine_name → (module_file, class_name, init_style)
# init_style: "db" = needs db_path, "none" = no args, "custom" = special handling
ENGINE_REGISTRY = {
    "inference_engine":           ("inference_engine",           "MichiganLegalModel",        "none"),
    "bm25_engine":                ("bm25_engine",                "BM25Engine",                "db"),
    "semantic_engine":            ("semantic_engine",            "SemanticEngine",             "none"),
    "hybrid_retriever":           ("hybrid_retriever",           "HybridRetriever",           "db"),
    "knowledge_graph":            ("knowledge_graph",            "KnowledgeGraphEngine",      "db"),
    "corrective_rag":             ("corrective_rag",             "CorrectiveRAG",             "db"),
    "graph_rag":                  ("graph_rag",                  "GraphRAG",                  "db"),
    "query_expander":             ("query_expander",             "QueryExpander",             "db"),
    "entity_resolver":            ("entity_resolver",            "EntityResolver",            "db"),
    "reranker":                   ("reranker",                   "Reranker",                  "none"),
    "litigation_fsm":             ("litigation_fsm",             "LitigationFSM",             "db"),
    "filing_optimizer":           ("filing_optimizer",           "FilingOptimizer",           "db"),
    "evidence_chains":            ("evidence_chains",            "EvidenceChainBuilder",      "db"),
    "contradiction_discovery":    ("contradiction_discovery",    "ContradictionDiscovery",    "db"),
    "temporal_analyzer":          ("temporal_analyzer",          "TemporalAnalyzer",          "db"),
    "authority_pagerank":         ("authority_pagerank",         "AuthorityPageRank",         "db"),
    "impeachment_generator":      ("impeachment_generator",      "ImpeachmentGenerator",      "db"),
    "judicial_violation_analyzer":("judicial_violation_analyzer","JudicialViolationAnalyzer", "db"),
    "timeline_engine":            ("timeline_engine",            "TimelineEngine",            "db"),
    "filing_assembler":           ("filing_assembler",           "FilingAssembler",           "db"),
    "adversarial_engine":         ("adversarial_engine",         "AdversarialEngine",         "db"),
    "citation_gap_finder":        ("citation_gap_finder",        "CitationGapFinder",         "db"),
    "compliance_engine":          ("compliance_engine",          "ComplianceEngine",          "db"),
    "admissibility_scorer":       ("admissibility_scorer",       "AdmissibilityScorer",       "db"),
    "persistent_memory":          ("persistent_memory",          "PersistentMemory",          "db"),
    # ═══ NEW: HF Legal AI + NEXUS Unified Engine ═══
    "hf_legal_engine":            ("hf_legal_engine",            "HFLegalEngine",             "none"),
    "nexus_engine":               ("nexus_engine",               "NexusEngine",               "none"),
}

# Intent → engine chain mapping
INTENT_CHAINS = {
    "legal_search": [
        "query_expander", "hybrid_retriever", "reranker", "corrective_rag",
    ],
    "filing_help": [
        "compliance_engine", "filing_assembler", "citation_gap_finder",
    ],
    "impeachment": [
        "impeachment_generator", "admissibility_scorer", "adversarial_engine",
    ],
    "timeline": [
        "timeline_engine", "temporal_analyzer", "contradiction_discovery",
    ],
    "compliance": [
        "compliance_engine", "filing_optimizer",
    ],
    "evidence": [
        "entity_resolver", "hybrid_retriever", "evidence_chains",
        "admissibility_scorer",
    ],
    "risk": [
        "adversarial_engine", "litigation_fsm", "filing_optimizer",
    ],
    # ═══ NEXUS META-CHAINS: Route through unified engine ═══
    "nexus_full": [
        "nexus_engine",
    ],
    "deep_analysis": [
        "nexus_engine", "hf_legal_engine", "corrective_rag", "evidence_chains",
    ],
    "judicial_misconduct": [
        "judicial_violation_analyzer", "nexus_engine", "impeachment_generator",
        "temporal_analyzer", "evidence_chains",
    ],
    "appellate": [
        "nexus_engine", "authority_pagerank", "citation_gap_finder",
        "compliance_engine", "filing_assembler",
    ],
}

# Filing type → engine pipeline
FILING_PIPELINES = {
    "motion": [
        "citation_gap_finder", "authority_pagerank", "filing_assembler",
        "compliance_engine", "adversarial_engine",
    ],
    "brief": [
        "timeline_engine", "evidence_chains", "impeachment_generator",
        "filing_assembler", "compliance_engine",
    ],
    "jtc_complaint": [
        "judicial_violation_analyzer", "timeline_engine",
        "filing_assembler", "compliance_engine",
    ],
    "response": [
        "adversarial_engine", "citation_gap_finder", "evidence_chains",
        "filing_assembler", "compliance_engine",
    ],
    "appeal_brief": [
        "timeline_engine", "authority_pagerank", "evidence_chains",
        "citation_gap_finder", "filing_assembler", "compliance_engine",
    ],
}

# Keywords for intent classification
_INTENT_KEYWORDS = {
    "impeachment":  {"impeach", "cross-exam", "cross exam", "credibility",
                     "contradict", "lying", "inconsistent", "witness"},
    "timeline":     {"timeline", "chronolog", "when did", "sequence",
                     "dates", "temporal", "history"},
    "compliance":   {"comply", "compliance", "mcr", "rule", "format",
                     "deadline", "procedur"},
    "filing_help":  {"file", "filing", "motion", "brief", "draft",
                     "assemble", "prepare", "submit"},
    "evidence":     {"evidence", "exhibit", "document", "proof",
                     "admissib", "foundation", "hearsay"},
    "risk":         {"risk", "vulnerab", "attack", "weakness",
                     "danger", "threat", "opposing"},
    "legal_search": {"search", "find", "authority", "case law", "statute",
                     "mcl", "mre", "what is", "how does", "explain"},
}

# Circuit breaker states
CB_CLOSED = "CLOSED"
CB_OPEN = "OPEN"
CB_HALF_OPEN = "HALF_OPEN"

# Circuit breaker thresholds
CB_FAILURE_THRESHOLD = 3
CB_FAILURE_WINDOW_SEC = 60
CB_RECOVERY_SEC = 120


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Master Orchestrator — coordinates all 25 engines through a unified
    pipeline with circuit breakers, health monitoring, and graceful
    degradation. This class must NEVER raise an unhandled exception.
    """

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._engines = {}              # name → instance (or None)
        self._unavailable = set()       # engines that failed import
        self._failure_counts = {}       # name → deque of timestamps
        self._circuit_states = {}       # name → CB_CLOSED | CB_OPEN | CB_HALF_OPEN
        self._circuit_opened_at = {}    # name → timestamp when circuit opened
        self._last_success = {}         # name → timestamp of last success
        self._op_log = []               # in-memory operation log
        self._start_time = time.time()

        # Ensure engine directory is on sys.path
        if _DIR not in sys.path:
            sys.path.insert(0, _DIR)

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _lazy_load(self, engine_name):
        """
        Lazy-load an engine on first use. Returns the engine instance or
        None if the engine is unavailable.
        """
        try:
            if engine_name in self._unavailable:
                return None
            if engine_name in self._engines:
                return self._engines[engine_name]

            reg = ENGINE_REGISTRY.get(engine_name)
            if reg is None:
                self._unavailable.add(engine_name)
                return None

            module_file, class_name, init_style = reg

            try:
                mod = importlib.import_module(module_file)
            except ImportError:
                self._unavailable.add(engine_name)
                self._log("import_fail", engine_name,
                          f"ImportError for {module_file}")
                return None
            except Exception as exc:
                self._unavailable.add(engine_name)
                self._log("import_fail", engine_name, str(exc))
                return None

            cls = getattr(mod, class_name, None)
            if cls is None:
                self._unavailable.add(engine_name)
                self._log("class_missing", engine_name,
                          f"{class_name} not found in {module_file}")
                return None

            try:
                if init_style == "db":
                    instance = cls(self.db_path)
                else:
                    instance = cls()
            except Exception as exc:
                self._unavailable.add(engine_name)
                self._log("init_fail", engine_name,
                          f"__init__ raised: {exc}")
                return None

            self._engines[engine_name] = instance
            self._circuit_states.setdefault(engine_name, CB_CLOSED)
            self._failure_counts.setdefault(
                engine_name, collections.deque(maxlen=50))
            self._log("loaded", engine_name)
            return instance

        except Exception:
            self._unavailable.add(engine_name)
            return None

    # ------------------------------------------------------------------
    # Circuit breaker
    # ------------------------------------------------------------------

    def _circuit_breaker(self, engine_name, func, *args, **kwargs):
        """
        Execute *func* with circuit-breaker protection for *engine_name*.

        Returns (result, was_fallback_used).
        - If circuit is OPEN and recovery time has not elapsed → (None, True)
        - If circuit is HALF_OPEN → try one request
        - On success → CLOSE circuit
        - On failure → increment failure count; OPEN if threshold exceeded
        """
        try:
            state = self._circuit_states.get(engine_name, CB_CLOSED)

            # OPEN → check if recovery period has elapsed
            if state == CB_OPEN:
                opened = self._circuit_opened_at.get(engine_name, 0)
                if time.time() - opened < CB_RECOVERY_SEC:
                    return (None, True)
                # Transition to HALF_OPEN
                self._circuit_states[engine_name] = CB_HALF_OPEN
                state = CB_HALF_OPEN

            # Execute the function
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                self._record_failure(engine_name, exc)
                return (None, True)

            # Success path
            if state == CB_HALF_OPEN:
                self._circuit_states[engine_name] = CB_CLOSED
                self._log("circuit_closed", engine_name,
                          "Recovered from HALF_OPEN")
            self._last_success[engine_name] = time.time()
            return (result, False)

        except Exception:
            return (None, True)

    def _record_failure(self, engine_name, exc=None):
        """Record a failure and potentially open the circuit."""
        try:
            now = time.time()
            dq = self._failure_counts.setdefault(
                engine_name, collections.deque(maxlen=50))
            dq.append(now)

            # Count failures within the window
            cutoff = now - CB_FAILURE_WINDOW_SEC
            recent = sum(1 for ts in dq if ts >= cutoff)

            if recent > CB_FAILURE_THRESHOLD:
                self._circuit_states[engine_name] = CB_OPEN
                self._circuit_opened_at[engine_name] = now
                self._log("circuit_opened", engine_name,
                          f"{recent} failures in {CB_FAILURE_WINDOW_SEC}s"
                          + (f" last_err={exc}" if exc else ""))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Query routing
    # ------------------------------------------------------------------

    def classify_intent(self, query_text):
        """
        Classify a query into one of the known intents by keyword matching.
        Returns (intent_name, confidence).
        """
        try:
            q_lower = query_text.lower()
            scores = {}
            for intent, keywords in _INTENT_KEYWORDS.items():
                score = sum(1 for kw in keywords if kw in q_lower)
                if score > 0:
                    scores[intent] = score

            if not scores:
                return ("legal_search", 0.3)

            best = max(scores, key=scores.get)
            confidence = min(1.0, scores[best] / 3.0)
            return (best, round(confidence, 2))
        except Exception:
            return ("legal_search", 0.1)

    def route_query(self, query_text, context=None):
        """
        Intelligent query routing:
        1. Classify intent
        2. Select engine chain
        3. Execute with circuit breakers
        4. Log to persistent_memory
        5. Return results with metadata
        """
        start = time.time()
        meta = {
            "query": query_text,
            "timestamp": datetime.now().isoformat(),
            "engines_used": [],
            "intent": None,
            "confidence": 0,
            "latency_ms": 0,
            "degraded": False,
            "errors": [],
        }

        try:
            intent, confidence = self.classify_intent(query_text)
            meta["intent"] = intent
            meta["confidence"] = confidence

            chain = INTENT_CHAINS.get(intent, INTENT_CHAINS["legal_search"])
            chain_result = self.execute_chain(chain, query_text, context)

            meta["engines_used"] = chain_result.get("engines_used", [])
            meta["degraded"] = chain_result.get("degraded", False)
            meta["latency_ms"] = int((time.time() - start) * 1000)

            # Log to persistent_memory if available
            self._log_to_memory(meta)

            return {
                "results": chain_result.get("results", []),
                "meta": meta,
            }

        except Exception as exc:
            meta["errors"].append(str(exc))
            meta["latency_ms"] = int((time.time() - start) * 1000)
            return {"results": [], "meta": meta}

    # ------------------------------------------------------------------
    # Chain execution
    # ------------------------------------------------------------------

    def execute_chain(self, chain, query, context=None):
        """
        Execute a chain of engines sequentially, passing output forward.
        If any engine fails, skip it and continue (graceful degradation).
        """
        results = []
        engines_used = []
        degraded = False
        start = time.time()
        current_input = query

        try:
            for engine_name in chain:
                try:
                    instance = self._lazy_load(engine_name)
                    if instance is None:
                        degraded = True
                        continue

                    output, was_fallback = self._invoke_engine(
                        engine_name, instance, current_input, context)

                    if was_fallback:
                        degraded = True
                        continue

                    if output is not None:
                        results.append({
                            "engine": engine_name,
                            "output": output,
                        })
                        engines_used.append(engine_name)
                        # Pass output forward as enriched context
                        current_input = self._merge_chain_input(
                            current_input, output)

                except Exception as exc:
                    degraded = True
                    self._log("chain_error", engine_name, str(exc))

        except Exception:
            degraded = True

        return {
            "results": results,
            "engines_used": engines_used,
            "latency_ms": int((time.time() - start) * 1000),
            "degraded": degraded,
        }

    def _invoke_engine(self, engine_name, instance, query, context=None):
        """
        Call the best available method on an engine instance.
        Returns (result, was_fallback).
        """
        # Determine the best method to call
        method = self._resolve_method(engine_name, instance)
        if method is None:
            return (None, True)

        def _call():
            # Build kwargs depending on what the method accepts
            try:
                return method(query)
            except TypeError:
                try:
                    return method(query, context=context)
                except TypeError:
                    return method(query)

        return self._circuit_breaker(engine_name, _call)

    def _resolve_method(self, engine_name, instance):
        """Find the primary callable method on an engine instance."""
        try:
            # Preferred method names in order of priority
            preferred = {
                "inference_engine":           "query",
                "bm25_engine":                "search",
                "semantic_engine":            "search",
                "hybrid_retriever":           "search",
                "knowledge_graph":            "find_related_authorities",
                "corrective_rag":             "corrective_query",
                "graph_rag":                  "query",
                "query_expander":             "expand",
                "entity_resolver":            "resolve",
                "reranker":                   "rerank",
                "litigation_fsm":             "get_next_actions",
                "filing_optimizer":           "score_filing",
                "evidence_chains":            "build_chain",
                "contradiction_discovery":    "full_scan",
                "temporal_analyzer":          "generate_anomaly_report",
                "authority_pagerank":         "get_top_authorities",
                "impeachment_generator":      "find_strongest_impeachment",
                "judicial_violation_analyzer":"analyze_violation_patterns",
                "timeline_engine":            "build_unified_timeline",
                "filing_assembler":           "assemble_filing_package",
                "adversarial_engine":         "vulnerability_scan",
                "citation_gap_finder":        "find_citation_gaps_by_topic",
                "compliance_engine":          "check_filing_compliance",
                "admissibility_scorer":       "score_admissibility",
                "persistent_memory":          "search",
            }

            method_name = preferred.get(engine_name)
            if method_name:
                m = getattr(instance, method_name, None)
                if callable(m):
                    return m

            # Fallback: try common names
            for name in ("query", "search", "analyze", "run",
                         "execute", "process", "score"):
                m = getattr(instance, name, None)
                if callable(m):
                    return m

            return None
        except Exception:
            return None

    @staticmethod
    def _merge_chain_input(original_query, engine_output):
        """
        Merge engine output back into the query for the next engine in the
        chain. Returns a string or dict that downstream engines can consume.
        """
        try:
            if isinstance(engine_output, str):
                return engine_output if len(engine_output) > len(
                    str(original_query)) else original_query
            if isinstance(engine_output, dict):
                # If the output has expanded terms or results, pass it
                for key in ("expanded_query", "query", "text", "results"):
                    if key in engine_output:
                        val = engine_output[key]
                        if isinstance(val, str) and val:
                            return val
            # Default: keep original
            return original_query
        except Exception:
            return original_query

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self):
        """
        Check all registered engines and return a comprehensive status dict.
        """
        report = {}
        try:
            for engine_name in ENGINE_REGISTRY:
                entry = {
                    "status": "unknown",
                    "importable": False,
                    "db_connectable": False,
                    "circuit_state": self._circuit_states.get(
                        engine_name, CB_CLOSED),
                    "last_success": self._last_success.get(engine_name),
                    "error_count": 0,
                    "error": None,
                }

                try:
                    # Check importability
                    module_file = ENGINE_REGISTRY[engine_name][0]
                    try:
                        importlib.import_module(module_file)
                        entry["importable"] = True
                    except Exception as exc:
                        entry["error"] = f"Import failed: {exc}"

                    # Check DB connectivity (for db-style engines)
                    init_style = ENGINE_REGISTRY[engine_name][2]
                    if init_style == "db":
                        try:
                            conn = sqlite3.connect(self.db_path)
                            conn.execute("SELECT 1")
                            conn.close()
                            entry["db_connectable"] = True
                        except Exception:
                            entry["db_connectable"] = False
                    else:
                        entry["db_connectable"] = True  # N/A

                    # Error count in window
                    dq = self._failure_counts.get(
                        engine_name, collections.deque())
                    cutoff = time.time() - CB_FAILURE_WINDOW_SEC
                    entry["error_count"] = sum(
                        1 for ts in dq if ts >= cutoff)

                    # Overall status
                    if engine_name in self._unavailable:
                        entry["status"] = "unavailable"
                    elif not entry["importable"]:
                        entry["status"] = "import_failed"
                    elif entry["circuit_state"] == CB_OPEN:
                        entry["status"] = "circuit_open"
                    elif entry["circuit_state"] == CB_HALF_OPEN:
                        entry["status"] = "recovering"
                    elif entry["importable"] and entry["db_connectable"]:
                        entry["status"] = "operational"
                    else:
                        entry["status"] = "degraded"

                except Exception as exc:
                    entry["status"] = "error"
                    entry["error"] = str(exc)

                report[engine_name] = entry

        except Exception:
            pass

        return report

    # ------------------------------------------------------------------
    # Engine inventory
    # ------------------------------------------------------------------

    def get_engine_inventory(self):
        """
        List all registered engines with capabilities, status, and metrics.
        """
        inventory = []
        try:
            health = self.health_check()
            for engine_name, (mod_file, cls_name, init_style) in \
                    ENGINE_REGISTRY.items():
                h = health.get(engine_name, {})
                inventory.append({
                    "name": engine_name,
                    "module": mod_file,
                    "class": cls_name,
                    "init_style": init_style,
                    "status": h.get("status", "unknown"),
                    "circuit_state": h.get("circuit_state", CB_CLOSED),
                    "error_count": h.get("error_count", 0),
                    "last_success": h.get("last_success"),
                    "loaded": engine_name in self._engines,
                })
        except Exception:
            pass
        return inventory

    # ------------------------------------------------------------------
    # Parallel search
    # ------------------------------------------------------------------

    def parallel_search(self, query, engines=None):
        """
        Run query against multiple engines in parallel, merge results via
        reciprocal rank fusion (RRF).
        """
        if engines is None:
            engines = [
                "bm25_engine", "semantic_engine", "hybrid_retriever",
                "knowledge_graph", "graph_rag",
            ]

        per_engine_results = {}
        start = time.time()

        def _search_one(eng_name):
            try:
                inst = self._lazy_load(eng_name)
                if inst is None:
                    return (eng_name, None, True)
                result, fallback = self._invoke_engine(
                    eng_name, inst, query)
                return (eng_name, result, fallback)
            except Exception:
                return (eng_name, None, True)

        # Use ThreadPoolExecutor for true parallel execution
        try:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(len(engines), 8)) as pool:
                futures = {
                    pool.submit(_search_one, e): e for e in engines
                }
                for fut in concurrent.futures.as_completed(futures, timeout=30):
                    try:
                        eng_name, result, fallback = fut.result(timeout=30)
                        if result is not None and not fallback:
                            per_engine_results[eng_name] = result
                    except Exception:
                        pass
        except Exception:
            # Fallback: sequential execution
            for eng_name in engines:
                try:
                    _, result, fallback = _search_one(eng_name)
                    if result is not None and not fallback:
                        per_engine_results[eng_name] = result
                except Exception:
                    pass

        merged = self._rrf_merge(per_engine_results)
        return {
            "results": merged,
            "sources": list(per_engine_results.keys()),
            "engine_count": len(per_engine_results),
            "latency_ms": int((time.time() - start) * 1000),
        }

    def _rrf_merge(self, per_engine_results, k=60):
        """
        Reciprocal Rank Fusion across engine results.
        Each engine's results are ranked; scores are 1/(k+rank).
        """
        scored = {}  # item_key → {score, item, sources}
        try:
            for engine_name, result in per_engine_results.items():
                items = self._extract_items(result)
                for rank, item in enumerate(items):
                    key = self._item_key(item)
                    if key not in scored:
                        scored[key] = {
                            "score": 0.0,
                            "item": item,
                            "sources": [],
                        }
                    scored[key]["score"] += 1.0 / (k + rank + 1)
                    scored[key]["sources"].append(engine_name)

            merged = sorted(
                scored.values(), key=lambda x: x["score"], reverse=True)
            return merged[:50]  # Top 50 results

        except Exception:
            # Fallback: just concatenate
            all_items = []
            for result in per_engine_results.values():
                all_items.extend(self._extract_items(result))
            return [{"score": 0, "item": it, "sources": ["unknown"]}
                    for it in all_items[:50]]

    @staticmethod
    def _extract_items(result):
        """Normalize engine output into a list of items."""
        try:
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                for key in ("results", "items", "matches", "documents",
                            "passages", "hits"):
                    if key in result and isinstance(result[key], list):
                        return result[key]
                return [result]
            if isinstance(result, str):
                return [{"text": result}]
            return []
        except Exception:
            return []

    @staticmethod
    def _item_key(item):
        """Generate a dedup key for an item."""
        try:
            if isinstance(item, dict):
                for key in ("id", "file_path", "text", "passage_text",
                            "quote_text", "citation"):
                    if key in item:
                        return str(item[key])[:200]
                return json.dumps(item, sort_keys=True, default=str)[:200]
            return str(item)[:200]
        except Exception:
            return str(id(item))

    # ------------------------------------------------------------------
    # Filing pipelines
    # ------------------------------------------------------------------

    def get_pipeline_for_filing(self, filing_type):
        """
        Return the optimal engine pipeline for a specific filing type.
        """
        try:
            ft = filing_type.lower().replace(" ", "_")
            pipeline = FILING_PIPELINES.get(ft)
            if pipeline:
                return list(pipeline)

            # Fuzzy match
            for key in FILING_PIPELINES:
                if key in ft or ft in key:
                    return list(FILING_PIPELINES[key])

            # Default pipeline
            return [
                "citation_gap_finder", "filing_assembler",
                "compliance_engine",
            ]
        except Exception:
            return ["filing_assembler", "compliance_engine"]

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def run_full_analysis(self, topic, lane=None):
        """
        Run ALL relevant engines on a topic for maximum-depth analysis.
        Returns a comprehensive dict from every applicable engine.
        """
        start = time.time()
        analysis = {
            "topic": topic,
            "lane": lane,
            "timestamp": datetime.now().isoformat(),
            "engines": {},
            "summary": {},
        }

        # Define analysis groups
        groups = {
            "retrieval": [
                "query_expander", "bm25_engine", "semantic_engine",
                "hybrid_retriever", "graph_rag", "corrective_rag",
            ],
            "knowledge": [
                "knowledge_graph", "authority_pagerank",
                "entity_resolver",
            ],
            "evidence": [
                "evidence_chains", "admissibility_scorer",
                "contradiction_discovery",
            ],
            "temporal": [
                "timeline_engine", "temporal_analyzer",
            ],
            "adversarial": [
                "adversarial_engine", "impeachment_generator",
            ],
            "compliance": [
                "compliance_engine", "filing_optimizer",
                "citation_gap_finder",
            ],
            "judicial": [
                "judicial_violation_analyzer",
            ],
        }

        # If lane specified, include FSM
        if lane:
            groups["state"] = ["litigation_fsm"]

        total_engines = 0
        successful = 0

        for group_name, engine_list in groups.items():
            group_results = {}
            for engine_name in engine_list:
                total_engines += 1
                try:
                    instance = self._lazy_load(engine_name)
                    if instance is None:
                        group_results[engine_name] = {
                            "status": "unavailable"}
                        continue

                    result, fallback = self._invoke_engine(
                        engine_name, instance, topic,
                        context={"lane": lane} if lane else None)

                    if fallback:
                        group_results[engine_name] = {
                            "status": "failed"}
                    else:
                        group_results[engine_name] = {
                            "status": "ok",
                            "output": result,
                        }
                        successful += 1

                except Exception as exc:
                    group_results[engine_name] = {
                        "status": "error",
                        "error": str(exc),
                    }

            analysis["engines"][group_name] = group_results

        analysis["summary"] = {
            "total_engines": total_engines,
            "successful": successful,
            "failed": total_engines - successful,
            "coverage_pct": round(
                (successful / max(total_engines, 1)) * 100, 1),
            "latency_ms": int((time.time() - start) * 1000),
        }

        self._log_to_memory({
            "operation": "full_analysis",
            "topic": topic,
            "lane": lane,
            "coverage": analysis["summary"]["coverage_pct"],
        })

        return analysis

    # ------------------------------------------------------------------
    # System status
    # ------------------------------------------------------------------

    def get_system_status(self):
        """
        Dashboard-ready system status with engine fleet health, DB stats,
        deadlines, risk, and FSM state.
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "uptime_sec": int(time.time() - self._start_time),
            "engines": {"total": 0, "operational": 0, "degraded": 0,
                        "unavailable": 0},
            "db": {"connected": False, "tables": 0, "size_bytes": 0},
            "deadlines": [],
            "fsm_states": {},
            "risk_summary": {},
            "memory_entries": 0,
        }

        try:
            # Engine fleet status
            health = self.health_check()
            status["engines"]["total"] = len(health)
            for eng, info in health.items():
                s = info.get("status", "unknown")
                if s == "operational":
                    status["engines"]["operational"] += 1
                elif s in ("unavailable", "import_failed"):
                    status["engines"]["unavailable"] += 1
                else:
                    status["engines"]["degraded"] += 1

            # DB stats
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                status["db"]["connected"] = True
                status["db"]["tables"] = len(tables)
                try:
                    status["db"]["size_bytes"] = os.path.getsize(
                        self.db_path)
                except OSError:
                    pass

                # Upcoming deadlines
                try:
                    if "deadlines" in tables:
                        rows = conn.execute(
                            "SELECT title, due_date_iso, status "
                            "FROM deadlines "
                            "WHERE status != 'completed' "
                            "ORDER BY due_date_iso ASC "
                            "LIMIT 10"
                        ).fetchall()
                        status["deadlines"] = [
                            {"title": r[0], "due_date": r[1],
                             "status": r[2]}
                            for r in rows
                        ]
                except Exception:
                    pass

                # FSM states per lane
                try:
                    fsm = self._lazy_load("litigation_fsm")
                    if fsm and hasattr(fsm, "get_all_states"):
                        status["fsm_states"] = fsm.get_all_states()
                except Exception:
                    pass

                # Memory entries
                try:
                    if "persistent_memory" in tables:
                        row = conn.execute(
                            "SELECT COUNT(*) FROM persistent_memory"
                        ).fetchone()
                        status["memory_entries"] = row[0] if row else 0
                except Exception:
                    pass

                conn.close()
            except Exception:
                pass

            # Risk summary
            try:
                conn = sqlite3.connect(self.db_path)
                tables_check = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()]
                if "risk_events" in tables_check:
                    rows = conn.execute(
                        "SELECT severity, COUNT(*) FROM risk_events "
                        "GROUP BY severity"
                    ).fetchall()
                    status["risk_summary"] = {
                        r[0]: r[1] for r in rows}
                conn.close()
            except Exception:
                pass

        except Exception:
            pass

        return status

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log(self, event, engine_name=None, detail=None):
        """Append to in-memory operation log."""
        try:
            entry = {
                "ts": datetime.now().isoformat(),
                "event": event,
                "engine": engine_name,
                "detail": detail,
            }
            self._op_log.append(entry)
            # Cap log at 5000 entries
            if len(self._op_log) > 5000:
                self._op_log = self._op_log[-2500:]
        except Exception:
            pass

    def _log_to_memory(self, data):
        """Persist operation data via persistent_memory engine if available."""
        try:
            mem = self._lazy_load("persistent_memory")
            if mem is None:
                return
            if hasattr(mem, "store"):
                mem.store(data)
            elif hasattr(mem, "save"):
                mem.save(data)
            elif hasattr(mem, "log"):
                mem.log(data)
        except Exception:
            pass

    def get_operation_log(self, last_n=100):
        """Return the last N operation log entries."""
        try:
            return list(self._op_log[-last_n:])
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def query(self, query_text, context=None):
        """Alias for route_query — primary entry point."""
        return self.route_query(query_text, context)

    def search(self, query_text, engines=None):
        """Alias for parallel_search."""
        return self.parallel_search(query_text, engines)

    def __repr__(self):
        try:
            loaded = len(self._engines)
            unavail = len(self._unavailable)
            total = len(ENGINE_REGISTRY)
            return (
                f"<Orchestrator engines={loaded}/{total} "
                f"unavailable={unavail} "
                f"db={os.path.basename(self.db_path)}>"
            )
        except Exception:
            return "<Orchestrator>"


# ---------------------------------------------------------------------------
# Main — health check and status report
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("  MBP LitigationOS 2026 — Master Orchestrator Engine")
    print("  THE MANBEARPIG System Health Report")
    print("=" * 70)
    print()

    orch = Orchestrator()

    # Health check
    print("[1/3] Engine Health Check")
    print("-" * 50)
    health = orch.health_check()
    operational = 0
    for name, info in sorted(health.items()):
        status = info.get("status", "unknown")
        circuit = info.get("circuit_state", "?")
        marker = "OK" if status == "operational" else status.upper()
        if status == "operational":
            operational += 1
        print(f"  {name:40s} [{marker:16s}] circuit={circuit}")
    print()
    print(f"  Fleet: {operational}/{len(health)} operational")
    print()

    # System status
    print("[2/3] System Status")
    print("-" * 50)
    sys_status = orch.get_system_status()
    eng = sys_status.get("engines", {})
    db = sys_status.get("db", {})
    print(f"  Engines:  {eng.get('operational', 0)}/{eng.get('total', 0)} "
          f"operational, {eng.get('degraded', 0)} degraded, "
          f"{eng.get('unavailable', 0)} unavailable")
    print(f"  Database: {'CONNECTED' if db.get('connected') else 'DISCONNECTED'}"
          f" — {db.get('tables', 0)} tables, "
          f"{db.get('size_bytes', 0) / (1024*1024):.1f} MB")

    deadlines = sys_status.get("deadlines", [])
    if deadlines:
        print(f"  Deadlines: {len(deadlines)} upcoming")
        for dl in deadlines[:5]:
            print(f"    - {dl.get('due_date', '?')}: {dl.get('title', '?')}"
                  f" [{dl.get('status', '?')}]")

    risk = sys_status.get("risk_summary", {})
    if risk:
        print(f"  Risks: {risk}")
    print()

    # Engine inventory
    print("[3/3] Engine Inventory")
    print("-" * 50)
    inv = orch.get_engine_inventory()
    for e in inv:
        loaded_tag = "LOADED" if e["loaded"] else "lazy"
        print(f"  {e['name']:40s} {e['status']:16s} [{loaded_tag}]")

    print()
    print(f"  {orch}")
    print()
    print("=" * 70)
    print("  329+ days parent-child separation. Every engine matters.")
    print("=" * 70)
