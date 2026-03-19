"""
LitigationOS Legal AI Package v4.9.0
=====================================
60-module legal NLP toolkit — 100% local, zero-API, CPU-first.

  Core NLP (4):
  - citation_extractor     : Michigan + federal citation extraction and validation
  - entity_extractor       : Legal named entity recognition (judges, parties, courts, statutes)
  - statute_parser         : MCL/MCR/MRE section parsing and cross-referencing
  - opinion_parser         : Court opinion structure extraction and defect detection

  Intelligence (5):
  - brain_evolver          : Multi-Brain auto-evolution engine (health, dedup, FTS sync)
  - cross_brain_optimizer  : Cross-brain query routing with RRF fusion and caching
  - rag_engine             : Evidence-aware corrective RAG pipeline with lane detection
  - reranker               : Cross-encoder reranking + MMR diversity selection
  - rag_evaluation         : RAG quality metrics (faithfulness, coverage, citation accuracy)

  Filing & QA (8):
  - completeness_scorer    : Filing completeness scoring (0-100) across 8 dimensions
  - deadline_integration   : Deadline sentinel integration with multi-tier alerting
  - chatgpt_parser         : ChatGPT export parser for legal content extraction
  - service_checker        : Proof of Service requirements per MCR 2.105/2.107
  - brief_compliance       : Michigan brief compliance engine (MCR 7.212, 2.119)
  - filing_state_machine   : 7-phase filing lifecycle with rollback and audit logging
  - quality_gate           : Phase-transition quality gates (25+ checks)
  - caption_generator      : Michigan court caption generator (8 jurisdictions)

  Evidence & Prediction (2):
  - evidence_gap_detector  : Evidence gap analysis per filing type and lane
  - outcome_predictor      : Bayesian + rules-based filing outcome prediction

  Output Pipeline (5):
  - pdf_generator          : MD → PDF with MCR-compliant formatting (reportlab + HTML fallback)
  - toc_toa_generator      : Table of Contents + Table of Authorities (MCR 7.212(C))
  - exhibit_stamper        : Bates numbering (PIGORS-XXXX), exhibit tabs, master index
  - efiling_formatter      : MiFILE + TrueFiling + PACER + manual formatting
  - provenance_tracker     : SHA-256 chain, DAG relationships, Mermaid visualization

  Autonomy Engines (5):
  - suggestion_engine      : Autonomous next-action suggestions based on case state
  - adversary_predictor    : ML adversary strategy prediction from filing patterns
  - financial_forensics    : Multi-lane damages calculation and forensic accounting
  - pattern_mining         : Judicial, adversary, and outcome pattern mining
  - timeline_visualizer    : Interactive HTML timeline with dark theme

  Evolution Layer (5):
  - skill_evolver          : Auto-analyze skill performance, evolution tracking
  - self_healing_monitor   : Engine health monitoring + auto-recovery
  - brain_evolver_daemon   : Content-based dedup, FTS rebuild, WAL checkpoint daemon
  - knowledge_graph_enricher : PageRank authority scoring, cluster detection
  - codebase_health_tracker : AST analysis, HTML dashboard, quality grading

  Context Engineering (3):
  - context_orchestrator   : Unified context hub — token budget, validation, compression, snapshots, quality
  - agent_context_protocol : Multi-agent coordination — registry, pub/sub, versioned handoffs, routing, lifecycle
  - context_harvester      : Multi-drive, multi-format context harvester (6 drives + Google Drive)

  Vector Database (5):
  - vector_index_optimizer : HNSW ANN index for 10-50x speedup over brute-force cosine
  - vector_search_bridge   : Drop-in bridge wiring HNSW into production retrieval pipeline
  - vector_monitor         : Latency/health/drift monitoring with HTML dashboard
  - embedding_manager      : Unified 4-model embedding manager (ONNX/ST/TF-IDF fallback)
  - chunk_optimizer        : 6-strategy legal document chunking with citation protection

  Litigation Intelligence (3):
  - deposition_strategist  : Deposition prep — witness profiling, question banks, impeachment sequences
  - damages_calculator     : Financial damages computation — per-defendant, per-lane, Decimal precision
  - timeline_forensics     : Chronological reconstruction — contradiction detection, gap analysis, Mermaid viz

  Litigation Operations (3):
  - subpoena_engine        : Subpoena generation, service tracking, MCR 2.305/2.506 compliance
  - settlement_analyzer    : Settlement valuation, demand letters, mediation briefs, BATNA analysis
  - court_order_tracker    : Order cataloging, compliance monitoring, violation detection, contempt prep

  Deep Litigation Intelligence (3):
  - parental_alienation_detector : Gardner 8-factor analysis, alienation behavior cataloging, MCL 722.23(j)
  - evidence_authenticator       : MRE 901/902 authentication, chain of custody, hearsay exceptions
  - judicial_recusal_engine      : MCR 2.003 disqualification, bias scoring, JTC complaint builder

  Litigation Operations II (3):
  - discovery_manager            : Discovery tracking, deadline calc (MCR 2.301-2.314), motion to compel
  - hearing_preparation          : Hearing planner, argument builder, exhibit organizer, proposed orders
  - compliance_auditor           : Filing format/content/citation/service audit (MCR 2.113, 7.212)

  Strategic Litigation (3):
  - case_strategy_architect      : Multi-lane SWOT strategy, game theory, cross-lane coordination
  - expert_witness_manager       : Expert identification, Daubert/MRE 702 analysis, deposition coordination
  - fee_petition_engine          : Lodestar calculation, fee shifting, cost bills, pro se fee recovery

  Litigation Procedures (3):
  - garnishment_engine           : Michigan garnishment, exemptions, wage/bank withholding, SCAO forms
  - appellate_record_builder     : Appellate record compilation, pagination, transcripts, MCR 7.210
  - default_judgment_engine      : Default judgment pursuit/defense, good cause, void judgment analysis

  Litigation Practice (3):
  - contempt_engine              : Civil/criminal contempt, show cause, purge conditions, MCR 3.606
  - interrogatory_engine         : Interrogatory drafting, objections, motions to compel, MCR 2.309
  - summary_judgment_engine      : Summary disposition, burden shifting, MCR 2.116, Maiden/Quinto

  Autonomous Fleet Intelligence (3):
  - autonomous_agent_framework   : Self-orchestrating agents — ReAct loops, Plan-and-Execute, tool registries, behavioral contracts
  - fleet_evolution_engine       : Fleet self-improvement — behavioral regression testing, capability assessment, skill gap analysis
  - workflow_automation_engine   : Batch processing, conditional routing, scheduling, retry logic, pipeline orchestration
"""

__version__ = "5.1.0"
__all__ = [
    # Core NLP
    "citation_extractor",
    "entity_extractor",
    "statute_parser",
    "opinion_parser",
    # Intelligence
    "brain_evolver",
    "cross_brain_optimizer",
    "rag_engine",
    "reranker",
    "rag_evaluation",
    # Filing & QA
    "completeness_scorer",
    "deadline_integration",
    "chatgpt_parser",
    "service_checker",
    "brief_compliance",
    "filing_state_machine",
    "quality_gate",
    "caption_generator",
    # Evidence & Prediction
    "evidence_gap_detector",
    "outcome_predictor",
    # Output Pipeline
    "pdf_generator",
    "toc_toa_generator",
    "exhibit_stamper",
    "efiling_formatter",
    "provenance_tracker",
    # Autonomy Engines
    "suggestion_engine",
    "adversary_predictor",
    "financial_forensics",
    "pattern_mining",
    "timeline_visualizer",
    # Evolution Layer
    "skill_evolver",
    "self_healing_monitor",
    "brain_evolver_daemon",
    "knowledge_graph_enricher",
    "codebase_health_tracker",
    # Context Engineering
    "context_orchestrator",
    "agent_context_protocol",
    "context_harvester",
    # Vector Search
    "vector_index_optimizer",
    "vector_search_bridge",
    "vector_monitor",
    "embedding_manager",
    "chunk_optimizer",
    # Litigation Intelligence (Wave 7)
    "deposition_strategist",
    "damages_calculator",
    "timeline_forensics",
    # Litigation Operations (Wave 8)
    "subpoena_engine",
    "settlement_analyzer",
    "court_order_tracker",
    # Deep Litigation Intelligence (Wave 9)
    "parental_alienation_detector",
    "evidence_authenticator",
    "judicial_recusal_engine",
    # Litigation Operations II (Wave 10)
    "discovery_manager",
    "hearing_preparation",
    "compliance_auditor",
    # Strategic Litigation (Wave 11)
    "case_strategy_architect",
    "expert_witness_manager",
    "fee_petition_engine",
    # Litigation Procedures (Wave 12)
    "garnishment_engine",
    "appellate_record_builder",
    "default_judgment_engine",
    # Litigation Practice (Wave 13)
    "contempt_engine",
    "interrogatory_engine",
    "summary_judgment_engine",
    # Autonomous Fleet Intelligence (Wave 14)
    "autonomous_agent_framework",
    "fleet_evolution_engine",
    "workflow_automation_engine",
]
