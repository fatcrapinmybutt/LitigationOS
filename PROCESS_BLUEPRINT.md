# LitigationOS PROCESS_BLUEPRINT.md - COMPREHENSIVE ARCHITECTURE DOCUMENTATION

## EXECUTIVE SUMMARY

LitigationOS is a **17-phase legal litigation processing pipeline** powered by:
- **OMEGA Master Orchestrator**: Phases 0-16 execution with checkpoint resume
- **DELTA9 Agent Fleet**: 56 agents across 7 tiers + convergence layer
- **MANBEARPIG AI Engine**: 54+ local skills, zero-network, 100% offline
- **MEEK Lane System**: 6 case lanes (A-F) with strict signal-based routing
- **Database-Backed Architecture**: SQLite with WAL, FTS5, and auto-healing

---

## 1. PIPELINE PHASES (0-16)

### Phase Orchestration
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\run_omega_pipeline.py

**All 17 phases defined in config.py PHASES list:**

| Phase | ID | Module | Label | Purpose |
|-------|-----|--------|-------|---------|
| 0 | "0" | safety | Safety Snapshot | Create backup checkpoint |
| 0.5 | "0.5" | phase0_5_drive_ingest | Drive Ingestion | Scan C/D/F/G/H/I drives |
| 1 | "1" | phase1_inventory | Recursive Inventory | Build file catalog |
| 2 | "2" | phase2_dedup | Hash-Cluster Dedup | Identify duplicates |
| 3 | "3" | phase3_classify | 3-Pass Classification | Tag categories & lanes |
| 4a | "4a" | phase4a_pdf_extract | PDF Extraction | Extract text from PDFs |
| 4b | "4b" | phase4b_docx_extract | DOCX Extraction | Extract text from DOCX |
| 4c | "4c" | phase4c_structured_extract | Structured Data | Parse JSON/CSV |
| 4d | "4d" | phase4d_atomize | Atom Generation | Create fact/citation atoms |
| 4e | "4e" | phase4e_archive_extract | Archive Extraction | Unzip/decompress |
| 5 | "5" | phase5_brain_feed | LEXOS Brain Feed | Index atoms into DB |
| 6 | "6" | phase6_gap_analysis | EGCP Gap Analysis | Find evidence gaps |
| 7a | "7a" | phase7a_graph_delta | Graph Delta | Update knowledge graph |
| 7b | "7b" | phase7b_synthesis_merge | Synthesis Merge | Consolidate atoms |
| 7c | "7c" | phase7c_knowledge_merge | Knowledge Merge | Merge KB sections |
| 8 | "8" | phase8_litigation_refresh | Litigation Refresh | Run analysis scripts |
| 9 | "9" | phase9_mcp_ingest | MCP Ingest | Index to MCP DB |
| 10 | "10" | phase10_judicial_analysis | Judicial Analysis | Profile judges/JTC |
| 11 | "11" | phase11_legal_action_discovery | Legal Action Discovery | Score case lanes |
| 12 | "12" | phase12_rule_audit | MCR/MCL Rule Audit | Verify citations |
| 13 | "13" | phase13_refinement | Document Refinement | Extract key facts |
| 14 | "14" | phase14_finalize | Filing Finalization | Match atoms to filings |
| 15 | "15" | phase15_validation | Court-Ready Validation | QA checks |
| 16 | "16" | phase16_desktop | Desktop Offload | Write to desktop |

**Execution Model:**
- Checkpoints stored in cycle_dir/checkpoints/ as JSON
- Resume from --start-phase flag (default: restart)
- --skip-phases comma-separated list allowed
- 600s timeout per phase (10 min max)
- Dry-run mode with --dry-run flag
- Dashboard printed to stderr after each phase

---

## 2. AGENT FLEET ARCHITECTURE (DELTA9 - 56 AGENTS)

File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\agent_orchestrator.py

### Agent Base Class: Agent9999
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\agent_base.py

**Core Features (Lines 46-875):**
- **Multi-tier error handling**: Try → specific exception → general catch → log + skip
- **Crash-resume checkpoints**: JSON files per agent, resume from N-th item
- **Deadman switch**: 120s no progress → self-diagnose
- **Per-item timeout**: 30s default, configurable
- **Parallel execution**: ThreadPoolExecutor with per-thread DB connections
- **Database locking resilience**: 8 retries with jitter backoff
- **ReAct loop**: Reason → Act → Observe for multi-step tasks
- **Agent memory**: Persistent key-value store in central DB (agent_memory table)
- **Tool registry**: Subclasses populate with custom tools

**Key Methods:**
- un(): Main entry point, handles full execution lifecycle
- _run_sequential(): Single-threaded with per-item timeout
- _run_parallel(): ThreadPoolExecutor with batch management
- _process_item(): Abstract method subclasses implement
- _validate_preconditions(): Pre-flight checks
- _finalize(): Post-execution cleanup
- eact_loop(): Multi-step reasoning loop with auto-checkpoint
- emember() / recall(): Persistent memory operations
- _read_file_content(): Smart reader (text direct, PDF/DOCX via extraction)

### Agent Tiers (7 tiers, 56 agents)

#### **Tier 1: Infrastructure (4 agents)**
Lane 1 - I/O Bound
- **IndexScoutC, IndexScoutD, IndexScoutF, IndexScoutGI**: Scan C/D/F/G/H/I drives

#### **Tier 2: Deduplication (4 agents)**
- **LegalDedup, DataDedup, CodeDedup, ArchiveCracker**: Hash clustering + near-dedup

#### **Tier 3: Extraction (4 agents)**
- **FlattenCommander, PdfHarvester, TextMiner, StructParser**: Extract text & data

#### **Tier J: Judicial Intelligence (8 agents)**
Lane 2 - CPU/AI Bound
- **McNeillProfiler, HoopesProfiler**: Judge pattern analysis
- **BenchbookAuditor, CanonMapper, JtcCompiler**: Judicial audit
- **DisqualificationEngine, ExParteDetector, TranscriptImpeacher**: Judicial violations

#### **Tier K: Case Intelligence (11 agents)**
- **LaneACustody, LaneAPpo, LaneBHousing, LaneCConvergence**: Lane-specific scoring
- **PersonProfiler, TimelineBuilder, AuthorityHarvester**: Case buildup
- **ContradictionDetector**: Cross-evidence contradictions
- **LaneDPPOIntel, LaneEMisconductIntel, LaneFAppellateIntel**: Lane D/E/F

#### **Tier L: Legal Warfare (11 agents)**
- **LaneAScorer, LaneBScorer, LaneCScorer, DamagesCalculator, FilingReadiness**
- **GapDetector, CitationValidator, RedTeamScanner**
- **LaneDScorer, LaneEScorer, LaneFScorer**: Lane scoring

#### **Convergence Tier (6 agents)**
- **FilingFactory, BrainFeeder, GraphBuilder, MscArchitect, TestRunner, ConvergenceCertifier**

### Master Index Database
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\agent_orchestrator.py (lines 25-151)

Location: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db

**Core Tables:**
- iles: ID, drive, full_path, extension, size_bytes, depth, sha256, category, meek_lane, is_canonical
- eady_queue: file_id, queue_type, priority, claimed_by, status
- dedup_clusters: sha256 (PK), file_count, canonical_id, space_saved_bytes
- zip_contents: zip_id, inner_path, inner_size, inner_ext, is_legal
- toms: id, atom_type, source_file_id, meek_lane, title, content, confidence, posture, created_by
- judicial_findings: judge, finding_type, severity, source_file_id, confidence, agent_id
- ction_scores: lane, evidence_score, authority_score, vulnerability_score, composite_score, gap_count
- gent_log: agent_id, level, action, detail, items_processed, items_errored

---

## 3. EVIDENCE PROCESSING & CLASSIFICATION (Phase 3)

File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\phase3_classify.py

### 3-Pass Classification System

#### **Pass 1: Extension + Path Pattern**
Function: classify_pass1(ext, file_path) (lines 37-57)

**File Categories (11 unique types):**
1. **LEGAL_DOC**: .pdf, .docx, .doc, .rtf
2. **LEGAL_TEXT**: .md, .txt
3. **STRUCTURED_DATA**: .json, .jsonl, .csv
4. **GRAPH_DATA**: .graphml, .cypher
5. **EVIDENCE_IMAGE**: .png, .jpg, .jpeg, .tiff, .tif, .bmp
6. **ARCHIVE**: .zip, .rar, .7z
7. **SCRIPT**: .py, .ps1, .bat, .sh
8. **WEB_DOC**: .html, .htm
9. **IRRELEVANT**: .pyc, .class, .dll, .exe, .so, .o, .obj, .h, .c, .cpp
10. **OTHER**: Unmatched
11. **SKIP**: System/build files

**Priority Assignment:**
- HIGH: Legal docs, structured data, high-priority patterns (complaint|motion|brief|affidavit|order)
- MEDIUM: Evidence images, archives
- LOW: Scripts, other

#### **Pass 2: Content Signal Scoring**
Function: classify_pass2(text) (lines 60-91)

**Signals Extracted:**
- MCL citations (Michigan Compiled Laws)
- MCR citations (Michigan Court Rules)
- MRE citations (Michigan Rules of Evidence)
- Case citations (NW2d, F.3d, US)
- USC citations (Federal)
- Canon citations (Judicial conduct)

**Scoring Formula:**
`
score = (citations × 3.0 + keywords × 1.5 + dollar_amounts + dates) × length_factor
`

**Signals Dict Output:**
`json
{
  "mcl": count, "mcr": count, "mre": count,
  "case_cites": count, "usc": count, "canons": count,
  "keywords": count, "persons": [names],
  "dates": count, "dollars": count
}
`

#### **Pass 3: MEEK Lane Assignment**
Function: classify_pass3(text) (lines 94-100)

**MEEK Signal Patterns** (config.py, lines 210-216):

| Lane | Regex Pattern | Examples |
|------|---------------|----------|
| MEEK1 | shady\.oaks\|homes\.of\.america\|MCL 554\|landlord\|tenant | Shady Oaks housing cases |
| MEEK2 | custody\|parenting\|FOC\|child\|MCL 722\|MCR 3.20[67]\|best.interest | Watson custody cases |
| MEEK3 | PPO\|protection.order\|contempt\|MCL 600.2950\|MCR 3.70[678] | Protection order/contempt |
| MEEK4 | bias\|JTC\|disqualif\|MCR 2.003\|canon\|judicial.misconduct | Judicial misconduct (McNeill) |
| MEEK5 | appell\|COA\|MSC\|MCR 7\.\|leave.to.appeal\|de.novo\|abuse.of.discretion | Appellate cases |

### Citation Patterns
`python
MCL_PATTERN = r"MCL\s+\d+[\.\d]*"
MCR_PATTERN = r"MCR\s+\d+[\.\d]*"
MRE_PATTERN = r"MRE\s+\d+[\.\d]*"
CASE_CITE_PATTERN = r"\b\d+\s+(Mich|NW2d|NW\.2d|US|F\.\d+d|F\.Supp)\b"
USC_PATTERN = r"\b\d+\s+USC\s+§?\s*\d+"
CANON_PATTERN = r"(?i)canon\s+\d+"
`

### Violation Keywords (30+ terms)
contempt, ex parte, bias, fraud, perjury, alienation, misconduct, deprivation, due process, fabricat*, obstruction, coercion, retaliation, suppress*, ...

### Person Name Mapping
`python
PERSON_NAMES = {
    "Pigors": "PLAINTIFF",
    "Watson": "DEFENDANT",
    "Emily": "DEFENDANT", 
    "McNeill": "JUDGE",
    "Hoopes": "JUDGE",
    "Rusco": "FOC/ATTORNEY",
    "Alden": "CORPORATE_DEFENDANT",
    ...
}
`

---

## 4. FILING GENERATION (Phases 8, 13, 14 + Engines)

### Phase 8: Litigation Refresh
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\phase8_litigation_refresh.py

**Runs existing scripts in sequence:**
1. i_impeachment.py - Extract witness contradictions
2. _authority_chains.py - Build authority citation chains
3. _readiness.py - Assess filing readiness per lane
4. k_adversary.py - Profile adversary strengths/weaknesses

### Phase 13: Document Refinement
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\phase13_refinement.py

**Extracts from top-scored documents:**
- Legal theories (due process, equal protection, best interest, contempt, fraud upon court, etc.)
- Key facts (sentences with violation keywords or citations)
- Cited persons and their roles
- Dates and financial amounts
- Citations to MCL/MCR/MRE/cases

### Phase 14: Filing Finalization
File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\phase14_finalize.py

**Matches atoms to existing filings:**
- Cross-reference atoms with COURT_FILINGS_FINAL directory
- Score relevance by: keyword overlap + person overlap + citation overlap
- Weight by atom severity (SWORN_FACT=3.0, RECORD_FACT=2.5, EVIDENCE_FACT=2.0, ALLEGATION=1.0, INFERENCE=0.5)
- Propose enhancements (additional citations, new claims, missing exhibits)

### Filing Engine
File: C:\Users\andre\LitigationOS\11_CODE\litigationos\src\litigationos\engines\filing.py

**Components:**
- FilingStack: Complete filing package with components
- StackComponent: Individual filing piece (main doc, exhibits, proof of service, etc.)
- FilingEngine: Assemble stacks, validate MCR compliance
- ValidationResult: Score (0-100) with issues/warnings

**MCR Format Requirements:**
`python
MCR_FORMAT = {
    "margin_top_inches": 1.0,
    "margin_bottom_inches": 1.0,
    "margin_left_inches": 1.0,
    "margin_right_inches": 1.0,
    "font": "Times New Roman",
    "font_size_pt": 12,
    "line_spacing": 2.0,  # double-spaced
    "page_limit_brief": 50,
    "page_limit_motion": 20,
    "page_limit_reply": 10,
}
`

---

## 5. QA PIPELINE & VALIDATION (Phase 15)

File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\phase15_validation.py

### Validation Checks

#### **1. Atom Store Integrity** (lines 38-75)
- Verify all atoms have atom_id or id
- Verify all atoms have source (source_sha256, source_path, or source)
- Files checked: fact_atoms.jsonl, citation_atoms.jsonl, event_atoms.jsonl, person_atoms.jsonl

#### **2. Citation Format** (lines 78-115)
- Validate MCL/MCR/MRE/CASE citations match regex
- Detect malformed citations

#### **3. Lane Mixing** (lines 118-180)
- Detect Lane A (Watson/custody) evidence in Lane B (Shady Oaks/housing) atoms
- Flag cross-contamination as WARN/FAIL

#### **4. Touchlog Coverage** (lines 184-248)
- Verify all modified master files (SYNTHESIS_DATA.json, etc.) have touchlog entries
- Touchlog entries must reference valid files

#### **5. Brain Nucleus Size Limit** (lines 250-280)
- Check LEXOS_BIBLE files ≤ 500 KB max
- Warn if exceeds threshold

**Result Format:**
`json
{
  "check": "atom_integrity_fact_atoms",
  "result": "PASS|FAIL|WARN",
  "details": "description"
}
`

**Prefiling QA** (implied from tools_v3.py):
- Check filing readiness %
- Verify gap count vs required evidence
- Validate proof of service
- Confirm exhibit list complete

---

## 6. DATABASE SCHEMA

### Central Database: litigation_context.db
File: C:\Users\andre\LitigationOS\00_SYSTEM\mcp_server\litigation_context_mcp\db.py (lines 47-199)

#### **Document Tables**
`sql
documents (id, file_path, file_name, file_size_bytes, modified_date, page_count, sha256_hash, ingested_at)
pages (id, document_id, page_number, text_content)
pages_fts (FTS5 virtual table)  -- full-text search on pages
`

#### **Knowledge Graph Tables**
`sql
graph_nodes (id, graph_source, label, node_type, data)
court_rules (id, rule, chapter, context, source_doc, authority_id)
risk_events (risk_type_id, track, forum, risk_class, severity, title, trigger_json, cure_cost, cure_deadline_clock, cure_packet_json)
rules_text (id, rule, chapter, context, source_doc)
rules_text_fts (FTS5 virtual table)
graph_load_log (graph_source, loaded_at, record_count, file_size_bytes)
`

#### **Markdown Knowledge Tables**
`sql
md_sections (id, source_file, source_path, section_level, section_title, section_path, content, char_count, sha256_hash, evolved_at)
md_sections_fts (FTS5 virtual table)
md_cross_refs (id, section_id, ref_type, ref_value, graph_node_id, graph_source, confidence)
`

#### **Convergence Tracking**
`sql
convergence_log (cycle_id, delta_new, blockers, next_patch, quality_score)
`

#### **MCP Views** (tools_v3.py, lines 32-245)
- _case_health: Case metrics (quotes, harms, contradictions, claims, deadlines)
- _adversary_threats: Ranked adversaries by harm count
- _filing_pipeline: Filing actions with phase, readiness %, risk score, gaps
- _drive_summary: Per-drive file counts/bytes/duplicates
- _clean_auth_rules: Deduplicated authority rules

#### **Performance & Operations Tables**
`sql
content_dedup_registry (file_path, file_size, sha256_hash, duplicate_of, action, drive_letter)
drive_organization_log (status, created_at)
query_performance_log (query_name, execution_time_ms, row_count, timestamp)
agent_memory (key, type, content, tags, confidence, source_session, created_at, updated_at)
agent_checkpoints (agent_id, checkpoint_data, created_at)
agent_log (agent_id, level, action, detail, items_processed, items_errored, timestamp)
`

---

## 7. CONFIGURATION & MEEK SIGNAL PATTERNS

File: C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\config.py

### Root Paths
`python
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
SCANS_ROOT = LITIGOS_ROOT / "02_EVIDENCE"
TOOLING_DIR = LITIGOS_ROOT / "00_SYSTEM" / "pipeline"
BACKUPS_DIR = LITIGOS_ROOT / "00_SYSTEM" / "backups"
LEXOS_BIBLE = LITIGOS_ROOT / "00_SYSTEM" / "lexos_bible"
`

### Drive Configuration
`python
DRIVE_SCAN_ROOTS = {
    "C": [Path(r"C:\Users\andre\LitigationOS"), ...],
    "D": [Path(r"D:\\")],
    "F": [Path(r"F:\\")],
    "G": [Path(r"G:\\")],
    "H": [Path(r"H:\\")],
    "I": [Path(r"I:\\")],
}
`

### Lane Registry
`python
LANE_REGISTRY = {
    "A": {"name": "Watson Custody", "meek": "MEEK2", "db": "lane_A_custody.db"},
    "B": {"name": "Shady Oaks Housing", "meek": "MEEK1", "db": "lane_B_housing.db"},
    "C": {"name": "Convergence", "meek": None, "db": "lane_C_convergence.db"},
    "D": {"name": "PPO / Protection Orders", "meek": "MEEK3", "db": "lane_D_ppo.db"},
    "E": {"name": "Judicial Misconduct / JTC", "meek": "MEEK4", "db": "lane_E_misconduct.db"},
    "F": {"name": "Appellate", "meek": "MEEK5", "db": "lane_F_appellate.db"},
}

LANE_A_CASES = {"2024-001507-DC", "2023-5907-PP"}
LANE_B_CASES = {"2025-002760-CZ"}
LANE_D_CASES = {"2024-001507-DC", "2023-5907-PP"}  # PPO overlap with A
LANE_E_CASES = {"2024-001507-DC"}  # McNeill misconduct
LANE_F_CASES = set()  # TBD on appellate filings
`

### Bucket Priority (Dedup Canonical Selection)
`python
BUCKET_PRIORITY = {
    "LITIGATIONOS_MASTER": 10,
    "PIGORS_CASE_MASTER": 9,
    "SCANNED_EVIDENCE": 8,
    "extracts_full": 7,
    "COURT_FILINGS_FINAL": 7,
    "COURT_PACKETS": 6,
    "discovery": 5,
    "Documents": 4,
}
`

### Evidence Posture Tags
`python
POSTURE_TAGS = ["RECORD_FACT", "EVIDENCE_FACT", "SWORN_FACT", "ALLEGATION", "INFERENCE"]
`

### Master Modifiable Files
Files that phases can update:
- SYNTHESIS_DATA.json, SYNTHESIS_STATS.md
- MASTER_EVIDENCE_INDEX.csv, MASTER_VIOLATIONS.csv
- MASTER_PERSONS.csv, MASTER_TIMELINE.csv, MASTER_CITATIONS.csv
- authority_shards_all.jsonl, EC_AUTHORITY_MAP.jsonl
- KNOWLEDGE_ALL.jsonl, neo4j_nodes.csv, neo4j_edges.csv
- EVENT_HORIZON_DELTA_INTEGRATION_MAP.md, graph_contract.yml

---

## 8. LOCAL AI ENGINE: MANBEARPIG

File: C:\Users\andre\LitigationOS\00_SYSTEM\local_model\inference_engine.py

### Architecture
- **Type**: Michigan Legal Language Model (EPOCH v9.0)
- **Network**: 100% local, 100% offline, ZERO remote calls
- **Technology**: TF-IDF retrieval + Naive Bayes classification + entity extraction + legal KB + template generation
- **Vectorizer**: scikit-learn TfidfVectorizer (Porter stemmer, Unicode)
- **Retrieval**: Cosine similarity + optional BM25S + optional InvertedIndex
- **Safety**: Self-healing error recovery with per-component heal attempts

### 54+ MANBEARPIG Skills
Location: C:\Users\andre\LitigationOS\00_SYSTEM\local_model\skills\*.py

#### **Core Skills (20+)**
1. **adversary_war_room.py** - Adversary weakness modeling
2. **case_strength_scorer.py** - Lane-specific case scoring
3. **damages_calculator_skill.py** - Quantify monetary damages
4. **evidence_clusterer.py** - Group related evidence
5. **factor_analysis.py** - MCL 722 best interest factors (custody)
6. **filing_generator.py** - Draft filings
7. **harm_search_optimizer.py** - Find harm evidence
8. **hearing_prep.py** - Hearing preparation brief
9. **impeachment_engine.py** - Witness contradiction analysis
10. **index_of_authorities.py** - Build authority index
11. **jtc_complaint_generator.py** - Draft JTC/canonical complaints
12. **mifile_checker.py** - Michigan file format validation
13. **motion_generator.py** - Draft motions
14. **msc_fleet_engine.py** - Supreme Court brief assembly
15. **precedent_matcher.py** - Find applicable case law
16. **pre_filing_validator.py** - QA before filing
17. **proposed_order_generator.py** - Draft proposed orders
18. **response_drafter.py** - Draft responsive briefs
19. **timeline_builder.py** - Create fact timelines
20. **service_tracker.py** - Track service compliance

#### **Specialized Skills (34+)**
- **alienation_analyzer.py** - Parental alienation patterns
- **appellate_brief_builder.py** - COA/MSC brief assembly
- **appendix_builder.py** - Build record appendix
- **authority_graph_navigator.py** - Navigate authority networks
- **authority_search.py** - Authority retrieval
- **caption_engine.py** - Correct case caption format
- **certificate_of_service.py** - Generate COS
- **chat_harm_intelligence.py** - Query harm evidence
- **chronology_engine.py** - Build chronologies
- **citation_network.py** - Citation dependency mapping
- **cite_check.py** - Verify citations
- **contradiction_finder.py** - Multi-witness contradictions
- **deadline_calculator.py** - Appeal/motion deadlines
- **deadline_monitor.py** - Deadline tracking
- **discovery_engine.py** - Discovery request drafting
- **federal_jurisdiction.py** - 42 USC 1983 federal analysis
- **filing_package_generator.py** - Complete filing assembly
- **forensic_analyzer.py** - Digital forensics review
- **order_analyzer.py** - Analyze court orders
- **pro_se_trap_detector.py** - Identify pro se errors
- **report_generator.py** - Summary reports
- **scao_form_filler.py** - Fill SCAO forms
- **scao_forms_library.py** - SCAO form index
- **separation_counter.py** - Calculate separation counts
- **shell_management.py** - System integration
- **timeline_generator.py** - Generate timeline summaries
- **timeline_visualization.py** - Format timelines
- **weaponization_tracker.py** - Track weaponization patterns
- **scan_unprocessed_docs.py** - Find new documents
- **appellate_validator.py** - Appellate rule compliance
- **adversary_accountability.py** - Adversary record tracker
- **adversary_wargame_v2.py** - Litigation strategy simulation
- **contradiction_finder.py** (alternate) - Additional contradiction analysis
- **multi_forum_compliance.py** - Multi-forum rule compliance

### 140+ JSON-RPC Methods
Exposed via inference_engine.py:
- classify_document(text) - Intent/doctype classification
- detect_lane(text) - MEEK signal matching
- xtract_entities(text) - Person/location/concept extraction
- score_evidence(text) - Evidence quality scoring
- summarize(text) - Abstractive summarization
- generate(prompt) - Prompt completion
- ind_authority(rule_id) - Authority lookup
- match_concepts(keywords) - Concept matching
- get_error_report() - Self-healing diagnostics

### Model Data Files
Location: C:\Users\andre\LitigationOS\00_SYSTEM\local_model\model_data\

- manifest.json - Model metadata & timestamps
- ectorizer.pkl - Scikit TfidfVectorizer
- 	fidf_matrix.npz - Sparse TF-IDF matrix
- intent_clf.pkl - Intent classifier (Naive Bayes)
- doctype_clf.pkl - Document type classifier
- corpus_labels.json - Training corpus labels
- corpus_meta.json - Corpus metadata (sources, counts)
- corpus_texts.json - Corpus text samples (for similarity)
- legal_concepts.json - Legal keyword → concept mapping
- ntity_patterns.json - Regex patterns for entity types
- m25/vocab.index.json - BM25 vocabulary (optional)

### Self-Healing & Resilience
- Auto-reconnect on stale DB connection
- Per-component heal attempts (max 3)
- Error logging with component tracking
- Cache invalidation on heal
- Fallback to non-FTS5 queries if needed

### Performance Optimizations
- LRU caching (128 max for concept match, 256 for DB lookup)
- Hot cache for frequently-accessed data (auth_rules, evidence_quotes)
- 128MB query cache
- 12GB mmap for large file access
- WAL mode + NORMAL synchronous

---

## 9. MCP SERVER TOOLS

File: C:\Users\andre\LitigationOS\00_SYSTEM\mcp_server\tools_v3.py

### 9 Dashboard Tools

1. **litigation_case_health()** → dict
   - Return: quote_count, harm_count, impeachment_count, contradiction_count, claim_count, active_deadlines, past_deadlines

2. **litigation_adversary_threats(limit=20)** → list[dict]
   - Return: Ranked adversaries by harm_count with critical_counts, category_spread

3. **litigation_filing_pipeline()** → list[dict]
   - Return: Filing actions with phase, readiness %, risk_score, tier, gaps_filled, gaps_remaining, sequence_order

4. **litigation_dedup_status()** → dict
   - Return: total_files, unique_hashes, exact_duplicates, near_duplicates, pending_review, drives_scanned

5. **litigation_dedup_duplicates(drive=None, limit=50)** → list[dict]
   - Return: file_path, file_size, sha256_hash, duplicate_of, action (per duplicate)

6. **litigation_drive_summary()** → list[dict]
   - Return: Per-drive file_count, total_bytes, unique_names, duplicates_found, files_moved, files_pending

7. **litigation_drive_org_log(status=None, limit=50)** → list[dict]
   - Return: Drive organization action log (file moves) with status filter

8. **litigation_query_benchmarks(limit=20)** → list[dict]
   - Return: Query performance (query_name, execution_time_ms, row_count, timestamp)

9. **litigation_agent_inventory()** → dict
   - Return: total_agents, total_skills, inventory (sorted list)
   - Scans .copilot/agents/ and .copilot/skills/ for .md definitions

---

## 10. ASSET INVENTORY

### Key Directories
`
C:\Users\andre\LitigationOS\
├── 00_SYSTEM/
│   ├── pipeline/           # OMEGA orchestrator + phases 0-16
│   ├── pipeline/agents/    # DELTA9 agent fleet (56 agents)
│   ├── local_model/        # MANBEARPIG inference + 54+ skills
│   ├── mcp_server/         # MCP database + tools
│   └── backups/            # Safety snapshots
├── 01_CASE_DATA/           # Case metadata
├── 01_FILINGS/             # Draft filings
├── 02_COURT_FORMS/         # Court form templates
├── 04_COURT_FILINGS/       # Final submitted filings
├── 05_ANALYSIS/            # Analysis outputs
├── 07_PDF/                 # Extracted PDFs
├── 08_TEXT/                # Extracted text
├── 10_Exhibits/            # Exhibit images
├── 11_CODE/                # Source code
└── COURT_FILINGS_FINAL/    # Final filing versions
`

### Critical Databases
- litigation_context.db (500MB+) - Central knowledge graph + documents
- master_index.db - Agent fleet state (files, atoms, scores)
- Lane-specific DBs: lane_A_custody.db, lane_B_housing.db, etc.
- Cycle DBs: cycle_dir/inventory.db (per run)

### Configuration Files
- config.py - MEEK_SIGNALS, lane registry, paths
- safety.py - Snapshot creation & verification
- ailsafe.py - Timeout management & incident logging

---

## EXECUTION FLOW (COMPLETE EXAMPLE)

`ash
# Run full pipeline from scratch
python run_omega_pipeline.py --create-snapshot

# Run phases 1-7 only (inventory through knowledge merge)
python run_omega_pipeline.py --start-phase 1 --end-phase 7c

# Resume from phase 8 (skip 0-7)
python run_omega_pipeline.py --start-phase 8

# Dry run to see what would happen
python run_omega_pipeline.py --dry-run

# List all phases
python run_omega_pipeline.py --list-phases

# Check status of last cycle
python run_omega_pipeline.py --status

# Run agent fleet in parallel
cd 00_SYSTEM/pipeline/agents
python -m agent_orchestrator --dry-run  # dry run
python -m agent_orchestrator              # run all 56 agents
python -m agent_orchestrator --tier tier1 # run Tier 1 only
python -m agent_orchestrator --agent IndexScoutC  # run one agent
`

---

## KEY DESIGN PRINCIPLES

1. **Failsafe Everything**: All blocking operations wrapped with timeouts (10-600s)
2. **Checkpoint Resume**: Every phase & agent can resume from last checkpoint
3. **Zero Network**: MANBEARPIG is 100% local/offline — no API calls
4. **Lane Isolation**: MEEK signals enforce strict case lane separation
5. **Self-Healing**: Components diagnose & repair themselves (max 3 attempts)
6. **Database Locking**: 8-retry backoff for high-concurrency agents
7. **Modular Phases**: 17 independent phases, run any subset in any order
8. **Rich Logging**: JSONL + stderr + central DB for debugging

---

## MEEK SIGNALS QUICK REFERENCE

| Lane | Case | Keywords | Rules |
|------|------|----------|-------|
| A | Watson Custody (2024-001507, 2023-5907) | custody, FOC, child, best interest | MCL 722, MCR 3.206-3.210 |
| B | Shady Oaks Housing (2025-002760) | shady oaks, landlord, tenant, habitability | MCL 554, MCL 445.903 |
| C | Convergence (cross-lane) | muskegon, 14th circuit, bias, civil rights | 42 USC 1983, MCR 2.003 |
| D | PPO/Contempt | protection order, contempt, no contact | MCL 600.2950, MCR 3.706-3.708 |
| E | Judicial Misconduct | bias, JTC, disqualification, canon | MCR 2.003, MCR 9.200 |
| F | Appellate | appeal, COA, MSC, standard of review | MCR 7.*, de novo, abuse of discretion |

---

**Document Generated**: Feb 2026  
**Pipeline Version**: OMEGA INFINITY EDITION  
**Agent Fleet**: DELTA9 (MAX LEVEL 9999++)  
**AI Engine**: MANBEARPIG v9.0  
**Status**: PRODUCTION READY
