"""
Legal AI Tool Registry — Lazy-loading dispatcher for 66 legal analysis modules.
================================================================================

Maps task_type strings → module metadata and provides lazy instantiation.
No modules are imported at load time — each is imported on first use only.

Categories:
  core_nlp           — Citation extraction, entity recognition, statute parsing
  intelligence       — Brain evolution, cross-brain optimization, RAG pipelines
  filing_qa          — Filing compliance, quality gates, service checking
  evidence_analysis  — Evidence authentication, gap detection, alienation
  output_pipeline    — PDF generation, exhibits, TOC/TOA, e-filing
  litigation_ops     — Contempt, discovery, hearings, orders, subpoenas, etc.
  strategy           — Damages, prediction, adversary analysis, strategy
  infra              — Context orchestration, vector search, embeddings, fleet
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Optional

logger = logging.getLogger("legal_ai.registry")

# ── Module-level constants ──────────────────────────────────────────────────

_PACKAGE = "legal_ai"

# Method names tried in priority order when no explicit method is requested.
_METHOD_PRIORITY = (
    "run",
    "analyze",
    "execute",
    "generate",
    "check",
    "score",
    "search",
    "predict",
    "parse",
    "extract",
    "audit",
    "evaluate",
    "mine",
    "prepare",
    "build",
    "stamp",
    "evolve",
    "scan",
    "harvest",
    "monitor",
    "maintain",
    "calculate",
    "detect",
    "assess",
)


# ── Registry ────────────────────────────────────────────────────────────────
# Each entry:  tool_name → {module, class_name, description, category, method}
#
# `method` is the recommended primary entry point.  The dispatcher falls back
# to _METHOD_PRIORITY if the named method doesn't exist.

LEGAL_AI_REGISTRY: dict[str, dict[str, str]] = {
    # ── Core NLP ────────────────────────────────────────────────────────────
    "citation_extractor": {
        "module": "citation_extractor",
        "class_name": "CitationExtractor",
        "description": "Michigan + federal citation extraction and validation",
        "category": "core_nlp",
        "method": "extract",
    },
    "entity_extractor": {
        "module": "entity_extractor",
        "class_name": "EntityExtractor",
        "description": "Legal named entity recognition (judges, parties, courts, statutes)",
        "category": "core_nlp",
        "method": "extract",
    },
    "statute_parser": {
        "module": "statute_parser",
        "class_name": "StatuteParser",
        "description": "MCL/MCR/MRE section parsing and cross-referencing",
        "category": "core_nlp",
        "method": "parse",
    },
    "opinion_parser": {
        "module": "opinion_parser",
        "class_name": "OpinionParser",
        "description": "Court opinion structure extraction and defect detection",
        "category": "core_nlp",
        "method": "parse",
    },

    # ── Intelligence ────────────────────────────────────────────────────────
    "brain_evolver": {
        "module": "brain_evolver",
        "class_name": "BrainEvolver",
        "description": "Multi-Brain auto-evolution engine (health, dedup, FTS sync)",
        "category": "intelligence",
        "method": "evolve",
    },
    "cross_brain_optimizer": {
        "module": "cross_brain_optimizer",
        "class_name": "CrossBrainOptimizer",
        "description": "Cross-brain query routing with RRF fusion and caching",
        "category": "intelligence",
        "method": "search",
    },
    "rag_engine": {
        "module": "rag_engine",
        "class_name": "LegalRAGEngine",
        "description": "Evidence-aware corrective RAG pipeline with lane detection",
        "category": "intelligence",
        "method": "generate",
    },
    "reranker": {
        "module": "reranker",
        "class_name": "LegalReranker",
        "description": "Cross-encoder reranking + MMR diversity selection",
        "category": "intelligence",
        "method": "rerank",
    },
    "rag_evaluation": {
        "module": "rag_evaluation",
        "class_name": "RAGEvaluator",
        "description": "RAG quality metrics (faithfulness, coverage, citation accuracy)",
        "category": "intelligence",
        "method": "evaluate_single",
    },

    # ── Filing & QA ─────────────────────────────────────────────────────────
    "completeness_scorer": {
        "module": "completeness_scorer",
        "class_name": "CompletenessScorer",
        "description": "Filing completeness scoring (0-100) across 8 dimensions",
        "category": "filing_qa",
        "method": "score_filing",
    },
    "deadline_integration": {
        "module": "deadline_integration",
        "class_name": "DeadlineSentinelIntegration",
        "description": "Deadline sentinel integration with multi-tier alerting",
        "category": "filing_qa",
        "method": "scan",
    },
    "chatgpt_parser": {
        "module": "chatgpt_parser",
        "class_name": "ChatGPTParser",
        "description": "ChatGPT export parser for legal content extraction",
        "category": "filing_qa",
        "method": "parse_export",
    },
    "service_checker": {
        "module": "service_checker",
        "class_name": "ServiceChecker",
        "description": "Proof of Service requirements per MCR 2.105/2.107",
        "category": "filing_qa",
        "method": "check_all",
    },
    "brief_compliance": {
        "module": "brief_compliance",
        "class_name": "BriefComplianceEngine",
        "description": "Michigan brief compliance engine (MCR 7.212, 2.119)",
        "category": "filing_qa",
        "method": "check",
    },
    "filing_state_machine": {
        "module": "filing_state_machine",
        "class_name": "FilingStateMachine",
        "description": "7-phase filing lifecycle with rollback and audit logging",
        "category": "filing_qa",
        "method": "get_dashboard",
    },
    "quality_gate": {
        "module": "quality_gate",
        "class_name": "QualityGateEngine",
        "description": "Phase-transition quality gates (25+ checks)",
        "category": "filing_qa",
        "method": "run_gate",
    },
    "caption_generator": {
        "module": "caption_generator",
        "class_name": "CaptionGenerator",
        "description": "Michigan court caption generator (8 jurisdictions)",
        "category": "filing_qa",
        "method": "generate",
    },

    # ── Evidence & Analysis ─────────────────────────────────────────────────
    "evidence_gap_detector": {
        "module": "evidence_gap_detector",
        "class_name": "EvidenceGapDetector",
        "description": "Evidence gap analysis per filing type and lane",
        "category": "evidence_analysis",
        "method": "detect_gaps",
    },
    "evidence_authenticator": {
        "module": "evidence_authenticator",
        "class_name": "EvidenceAuthenticator",
        "description": "MRE 901/902 authentication, chain of custody, hearsay exceptions",
        "category": "evidence_analysis",
        "method": "analyse_all",
    },
    "parental_alienation_detector": {
        "module": "parental_alienation_detector",
        "class_name": "ParentalAlienationDetector",
        "description": "Gardner 8-factor analysis, alienation behavior cataloging, MCL 722.23(j)",
        "category": "evidence_analysis",
        "method": "analyse",
    },
    "compliance_auditor": {
        "module": "compliance_auditor",
        "class_name": "ComplianceAuditor",
        "description": "Filing format/content/citation/service audit (MCR 2.113, 7.212)",
        "category": "evidence_analysis",
        "method": "full_audit",
    },

    # ── Output Pipeline ─────────────────────────────────────────────────────
    "pdf_generator": {
        "module": "pdf_generator",
        "class_name": "LitigationPDFGenerator",
        "description": "MD → PDF with MCR-compliant formatting (reportlab + HTML fallback)",
        "category": "output_pipeline",
        "method": "generate",
    },
    "toc_toa_generator": {
        "module": "toc_toa_generator",
        "class_name": "TOCTOAGenerator",
        "description": "Table of Contents + Table of Authorities (MCR 7.212(C))",
        "category": "output_pipeline",
        "method": "generate",
    },
    "exhibit_stamper": {
        "module": "exhibit_stamper",
        "class_name": "ExhibitStamper",
        "description": "Bates numbering (PIGORS-XXXX), exhibit tabs, master index",
        "category": "output_pipeline",
        "method": "stamp_exhibits",
    },
    "efiling_formatter": {
        "module": "efiling_formatter",
        "class_name": "EFilingFormatter",
        "description": "MiFILE + TrueFiling + PACER + manual formatting",
        "category": "output_pipeline",
        "method": "prepare_packet",
    },
    "provenance_tracker": {
        "module": "provenance_tracker",
        "class_name": "ProvenanceTracker",
        "description": "SHA-256 chain, DAG relationships, Mermaid visualization",
        "category": "output_pipeline",
        "method": "generate_report",
    },

    # ── Litigation Operations ───────────────────────────────────────────────
    "contempt_engine": {
        "module": "contempt_engine",
        "class_name": "ContemptEngine",
        "description": "Civil/criminal contempt, show cause, purge conditions, MCR 3.606",
        "category": "litigation_ops",
        "method": "identify_violations",
    },
    "discovery_manager": {
        "module": "discovery_manager",
        "class_name": "DiscoveryManager",
        "description": "Discovery tracking, deadline calc (MCR 2.301-2.314), motion to compel",
        "category": "litigation_ops",
        "method": "generate_discovery_report",
    },
    "hearing_preparation": {
        "module": "hearing_preparation",
        "class_name": "HearingPreparation",
        "description": "Hearing planner, argument builder, exhibit organizer, proposed orders",
        "category": "litigation_ops",
        "method": "prepare_full_hearing",
    },
    "court_order_tracker": {
        "module": "court_order_tracker",
        "class_name": "CourtOrderTracker",
        "description": "Order cataloging, compliance monitoring, violation detection, contempt prep",
        "category": "litigation_ops",
        "method": "monitor_compliance",
    },
    "timeline_forensics": {
        "module": "timeline_forensics",
        "class_name": "TimelineForensics",
        "description": "Chronological reconstruction — contradiction detection, gap analysis",
        "category": "litigation_ops",
        "method": "generate_forensic_report",
    },
    "subpoena_engine": {
        "module": "subpoena_engine",
        "class_name": "SubpoenaEngine",
        "description": "Subpoena generation, service tracking, MCR 2.305/2.506 compliance",
        "category": "litigation_ops",
        "method": "generate_subpoena_report",
    },
    "judicial_recusal_engine": {
        "module": "judicial_recusal_engine",
        "class_name": "JudicialRecusalEngine",
        "description": "MCR 2.003 disqualification, bias scoring, JTC complaint builder",
        "category": "litigation_ops",
        "method": "analyse",
    },
    "interrogatory_engine": {
        "module": "interrogatory_engine",
        "class_name": "InterrogatoryEngine",
        "description": "Interrogatory drafting, objections, motions to compel, MCR 2.309",
        "category": "litigation_ops",
        "method": "create_interrogatories",
    },
    "garnishment_engine": {
        "module": "garnishment_engine",
        "class_name": "GarnishmentEngine",
        "description": "Michigan garnishment, exemptions, wage/bank withholding, SCAO forms",
        "category": "litigation_ops",
        "method": "calculate_amounts",
    },
    "appellate_record_builder": {
        "module": "appellate_record_builder",
        "class_name": "AppellateRecordBuilder",
        "description": "Appellate record compilation, pagination, transcripts, MCR 7.210",
        "category": "litigation_ops",
        "method": "build_record",
    },
    "default_judgment_engine": {
        "module": "default_judgment_engine",
        "class_name": "DefaultJudgmentEngine",
        "description": "Default judgment pursuit/defense, good cause, void judgment analysis",
        "category": "litigation_ops",
        "method": "pursue_default",
    },

    # ── Strategy & Prediction ───────────────────────────────────────────────
    "damages_calculator": {
        "module": "damages_calculator",
        "class_name": "DamagesCalculator",
        "description": "Financial damages computation — per-defendant, per-lane, Decimal precision",
        "category": "strategy",
        "method": "calculate_all_lanes",
    },
    "outcome_predictor": {
        "module": "outcome_predictor",
        "class_name": "OutcomePredictor",
        "description": "Bayesian + rules-based filing outcome prediction",
        "category": "strategy",
        "method": "predict",
    },
    "adversary_predictor": {
        "module": "adversary_predictor",
        "class_name": "AdversaryPredictor",
        "description": "ML adversary strategy prediction from filing patterns",
        "category": "strategy",
        "method": "predict_response",
    },
    "financial_forensics": {
        "module": "financial_forensics",
        "class_name": "FinancialForensicsEngine",
        "description": "Multi-lane damages calculation and forensic accounting",
        "category": "strategy",
        "method": "calculate_all",
    },
    "pattern_mining": {
        "module": "pattern_mining",
        "class_name": "PatternMiner",
        "description": "Judicial, adversary, and outcome pattern mining",
        "category": "strategy",
        "method": "mine_all",
    },
    "suggestion_engine": {
        "module": "suggestion_engine",
        "class_name": "SuggestionEngine",
        "description": "Autonomous next-action suggestions based on case state",
        "category": "strategy",
        "method": "analyze",
    },
    "settlement_analyzer": {
        "module": "settlement_analyzer",
        "class_name": "SettlementAnalyzer",
        "description": "Settlement valuation, demand letters, mediation briefs, BATNA analysis",
        "category": "strategy",
        "method": "analyze_case_value",
    },
    "case_strategy_architect": {
        "module": "case_strategy_architect",
        "class_name": "CaseStrategyArchitect",
        "description": "Multi-lane SWOT strategy, game theory, cross-lane coordination",
        "category": "strategy",
        "method": "create_master_plan",
    },
    "expert_witness_manager": {
        "module": "expert_witness_manager",
        "class_name": "ExpertWitnessManager",
        "description": "Expert identification, Daubert/MRE 702 analysis, deposition coordination",
        "category": "strategy",
        "method": "identify_experts",
    },
    "fee_petition_engine": {
        "module": "fee_petition_engine",
        "class_name": "FeePetitionEngine",
        "description": "Lodestar calculation, fee shifting, cost bills, pro se fee recovery",
        "category": "strategy",
        "method": "create_petition",
    },
    "summary_judgment_engine": {
        "module": "summary_judgment_engine",
        "class_name": "SummaryJudgmentEngine",
        "description": "Summary disposition, burden shifting, MCR 2.116, Maiden/Quinto",
        "category": "strategy",
        "method": "prepare_motion",
    },
    "deposition_strategist": {
        "module": "deposition_strategist",
        "class_name": "DepositionStrategist",
        "description": "Deposition prep — witness profiling, question banks, impeachment sequences",
        "category": "strategy",
        "method": "prepare_full_deposition",
    },

    # ── Infrastructure & Autonomy ───────────────────────────────────────────
    "timeline_visualizer": {
        "module": "timeline_visualizer",
        "class_name": "TimelineVisualizer",
        "description": "Interactive HTML timeline with dark theme",
        "category": "infra",
        "method": "generate",
    },
    "skill_evolver": {
        "module": "skill_evolver",
        "class_name": "SkillEvolver",
        "description": "Auto-analyze skill performance, evolution tracking",
        "category": "infra",
        "method": "scan_skills",
    },
    "self_healing_monitor": {
        "module": "self_healing_monitor",
        "class_name": "SelfHealingMonitor",
        "description": "Engine health monitoring + auto-recovery",
        "category": "infra",
        "method": "run_full_health_check",
    },
    "brain_evolver_daemon": {
        "module": "brain_evolver_daemon",
        "class_name": "BrainEvolverDaemon",
        "description": "Content-based dedup, FTS rebuild, WAL checkpoint daemon",
        "category": "infra",
        "method": "maintain_all",
    },
    "knowledge_graph_enricher": {
        "module": "knowledge_graph_enricher",
        "class_name": "KnowledgeGraphEnricher",
        "description": "PageRank authority scoring, cluster detection",
        "category": "infra",
        "method": "enrich_from_seeds",
    },
    "codebase_health_tracker": {
        "module": "codebase_health_tracker",
        "class_name": "CodebaseHealthTracker",
        "description": "AST analysis, HTML dashboard, quality grading",
        "category": "infra",
        "method": "scan_codebase",
    },
    "context_orchestrator": {
        "module": "context_orchestrator",
        "class_name": "ContextOrchestrator",
        "description": "Unified context hub — token budget, validation, compression, snapshots",
        "category": "infra",
        "method": "assemble",
    },
    "agent_context_protocol": {
        "module": "agent_context_protocol",
        "class_name": "AgentContextProtocol",
        "description": "Multi-agent coordination — registry, pub/sub, versioned handoffs",
        "category": "infra",
        "method": "health",
    },
    "context_harvester": {
        "module": "context_harvester",
        "class_name": "ContextHarvester",
        "description": "Multi-drive, multi-format context harvester (6 drives + Google Drive)",
        "category": "infra",
        "method": "harvest_all",
    },
    "vector_index_optimizer": {
        "module": "vector_index_optimizer",
        "class_name": "VectorIndexOptimizer",
        "description": "HNSW ANN index for 10-50x speedup over brute-force cosine",
        "category": "infra",
        "method": "search",
    },
    "vector_search_bridge": {
        "module": "vector_search_bridge",
        "class_name": "VectorSearchBridge",
        "description": "Drop-in bridge wiring HNSW into production retrieval pipeline",
        "category": "infra",
        "method": "search",
    },
    "vector_monitor": {
        "module": "vector_monitor",
        "class_name": "VectorMonitor",
        "description": "Latency/health/drift monitoring with HTML dashboard",
        "category": "infra",
        "method": "check_all_health",
    },
    "embedding_manager": {
        "module": "embedding_manager",
        "class_name": "EmbeddingManager",
        "description": "Unified 4-model embedding manager (ONNX/ST/TF-IDF fallback)",
        "category": "infra",
        "method": "embed_text",
    },
    "chunk_optimizer": {
        "module": "chunk_optimizer",
        "class_name": "ChunkOptimizer",
        "description": "6-strategy legal document chunking with citation protection",
        "category": "infra",
        "method": "chunk_legal_document",
    },
    "autonomous_agent_framework": {
        "module": "autonomous_agent_framework",
        "class_name": "AutonomousAgentFramework",
        "description": "Self-orchestrating agents — ReAct loops, Plan-and-Execute, tool registries",
        "category": "infra",
        "method": "run_agent",
    },
    "fleet_evolution_engine": {
        "module": "fleet_evolution_engine",
        "class_name": "FleetEvolutionEngine",
        "description": "Fleet self-improvement — regression testing, capability assessment",
        "category": "infra",
        "method": "evolve_fleet",
    },
    "workflow_automation_engine": {
        "module": "workflow_automation_engine",
        "class_name": "WorkflowAutomationEngine",
        "description": "Batch processing, conditional routing, scheduling, retry logic",
        "category": "infra",
        "method": "execute_workflow",
    },
}

# ── Category metadata ───────────────────────────────────────────────────────

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "core_nlp": "Citation extraction, entity recognition, statute and opinion parsing",
    "intelligence": "Brain evolution, cross-brain optimization, RAG pipelines and evaluation",
    "filing_qa": "Filing compliance, quality gates, deadlines, service checking, captions",
    "evidence_analysis": "Evidence authentication, gap detection, alienation, compliance audit",
    "output_pipeline": "PDF generation, exhibits/Bates, TOC/TOA, e-filing, provenance",
    "litigation_ops": "Contempt, discovery, hearings, orders, subpoenas, garnishment, appeals",
    "strategy": "Damages, prediction, adversary analysis, settlement, strategy, depositions",
    "infra": "Context orchestration, vector search, embeddings, agents, fleet, monitoring",
}

# ── Instance cache for lazy singletons ──────────────────────────────────────
_instance_cache: dict[str, Any] = {}


def _resolve_db_path() -> str:
    """Resolve the default litigation database path (same logic as daemon)."""
    import os
    from pathlib import Path

    try:
        from shared import get_db_path  # type: ignore[import-untyped]
        return str(get_db_path("litigation"))
    except (ImportError, KeyError):
        pass

    env_path = os.environ.get("LITIGATION_DB_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    current = Path(__file__).resolve().parent
    for _ in range(6):
        candidate = current / "litigation_context.db"
        if candidate.exists():
            return str(candidate)
        current = current.parent

    return str(Path(__file__).resolve().parent.parent.parent / "litigation_context.db")


def get_legal_ai_tool(
    task_type: str,
    *,
    use_cache: bool = True,
    init_kwargs: Optional[dict[str, Any]] = None,
) -> Any:
    """Lazy-import and instantiate a legal AI tool by task_type.

    Args:
        task_type: Registry key (e.g. "damages_calculator").
        use_cache: If True, return a cached singleton on repeat calls.
        init_kwargs: Explicit keyword arguments for the class constructor.
                     Overrides the default db_path injection when provided.

    Returns:
        An instantiated tool object ready to call.

    Raises:
        KeyError: If task_type is not in the registry.
        ImportError: If the module cannot be imported.
        AttributeError: If the expected class is not found in the module.
    """
    if task_type not in LEGAL_AI_REGISTRY:
        raise KeyError(
            f"Unknown legal_ai tool: {task_type!r}. "
            f"Available: {', '.join(sorted(LEGAL_AI_REGISTRY))}"
        )

    if use_cache and task_type in _instance_cache:
        return _instance_cache[task_type]

    entry = LEGAL_AI_REGISTRY[task_type]
    module_name = entry["module"]
    class_name = entry["class_name"]

    full_module = f"{_PACKAGE}.{module_name}"
    logger.debug("Importing %s.%s for task_type=%r", full_module, class_name, task_type)

    mod = importlib.import_module(full_module)
    cls = getattr(mod, class_name)

    # Build init kwargs — inject db_path if the class accepts it
    kwargs: dict[str, Any] = {}
    if init_kwargs:
        kwargs.update(init_kwargs)
    else:
        # Introspect __init__ to see if it accepts db_path
        import inspect
        sig = inspect.signature(cls.__init__)
        params = sig.parameters
        if "db_path" in params:
            kwargs["db_path"] = _resolve_db_path()

    try:
        instance = cls(**kwargs)
    except TypeError as exc:
        # Fallback: try no-arg construction if kwargs failed
        logger.debug(
            "Init with kwargs failed for %s (%s), trying no-arg fallback",
            class_name, exc,
        )
        instance = cls()

    if use_cache:
        _instance_cache[task_type] = instance

    return instance


def resolve_method(instance: Any, task_type: str, method_name: Optional[str] = None) -> str:
    """Determine which method to call on a tool instance.

    Args:
        instance: The tool object.
        task_type: Registry key — used to look up the recommended method.
        method_name: Explicit override from the caller.

    Returns:
        The name of a callable method on the instance.

    Raises:
        AttributeError: If no suitable method is found.
    """
    if method_name and hasattr(instance, method_name):
        return method_name

    entry = LEGAL_AI_REGISTRY.get(task_type, {})
    recommended = entry.get("method", "")
    if recommended and hasattr(instance, recommended):
        return recommended

    for candidate in _METHOD_PRIORITY:
        if hasattr(instance, candidate) and callable(getattr(instance, candidate)):
            return candidate

    raise AttributeError(
        f"No callable method found on {type(instance).__name__} "
        f"(tried: {method_name!r}, {recommended!r}, and {len(_METHOD_PRIORITY)} fallbacks)"
    )


def list_legal_ai_tools(category: Optional[str] = None) -> list[dict[str, str]]:
    """Return available tools with descriptions, optionally filtered by category.

    Args:
        category: If provided, only return tools in this category.

    Returns:
        List of dicts with keys: tool_name, class_name, description, category, method.
    """
    results: list[dict[str, str]] = []
    for tool_name, entry in sorted(LEGAL_AI_REGISTRY.items()):
        if category and entry.get("category") != category:
            continue
        results.append({
            "tool_name": tool_name,
            "class_name": entry["class_name"],
            "description": entry["description"],
            "category": entry["category"],
            "method": entry["method"],
        })
    return results


def list_categories() -> dict[str, dict[str, Any]]:
    """Return category metadata with tool counts.

    Returns:
        Dict mapping category → {description, tool_count, tools}.
    """
    cat_tools: dict[str, list[str]] = {}
    for tool_name, entry in LEGAL_AI_REGISTRY.items():
        cat = entry.get("category", "uncategorized")
        cat_tools.setdefault(cat, []).append(tool_name)

    result: dict[str, dict[str, Any]] = {}
    for cat, tools in sorted(cat_tools.items()):
        result[cat] = {
            "description": CATEGORY_DESCRIPTIONS.get(cat, ""),
            "tool_count": len(tools),
            "tools": sorted(tools),
        }
    return result


def clear_cache() -> int:
    """Clear the instance cache. Returns the number of entries cleared."""
    count = len(_instance_cache)
    _instance_cache.clear()
    return count
