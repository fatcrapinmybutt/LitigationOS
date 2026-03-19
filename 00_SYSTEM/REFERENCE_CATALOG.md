# LitigationOS — Reference Catalog

> **Extracted from copilot-instructions.md v15.0 by `/chronicle improve`**
> Detailed reference tables, directories, and command listings moved here to reduce context token usage in the main instructions file.

---

## 🔧 Delta999 Engine Directory

| Engine | File | Purpose |
|--------|------|---------|
| **LLM Classifier** | `llm_classifier_engine.py` | Ollama auto-classification of documents by type/lane/relevance |
| **Filing Validator** | `filing_validator_engine.py` | MCR compliance checking — format, citation, caption, service rules |
| **Brief Quality** | `brief_quality_engine.py` | Scoring briefs on persuasion, authority, IRAC structure, readability |
| **Opposing Analysis** | `opposing_analysis_engine.py` | Adversary pattern detection — Barnes/Watson tactics, response prediction |
| **Settlement Engine** | `settlement_engine.py` | Case valuation — damages, leverage, risk, settlement range calculation |
| **Doc Assembly** | `doc_assembly_engine.py` | MD → DOCX → PDF pipeline with template injection and Bates stamping |
| **Deadline Alert** | `deadline_alert_engine.py` | Deadline tracking with escalating urgency alerts and calendar sync |
| **DB Lock Manager** | `db_lock_manager.py` v3.0 | EAGAIN prevention — WAL enforcement, busy_timeout, connection pooling |

---

## 🛡️ EAGAIN Prevention Rules (Detailed)

SQLite EAGAIN/lock errors have been the #1 system stability issue. See top-of-file rules in `copilot-instructions.md` for the hard requirements. Additional technical details:

1. **Always use `managed_db()` context manager** from `db_lock_manager.py` for ALL database connections:
   ```python
   from db_lock_manager import managed_db
   with managed_db("litigation_context.db") as conn:
       conn.execute("SELECT ...")
   ```
2. **Connection pooling** — reuse connections within an agent's lifecycle, don't open/close per query
3. **Write serialization** — only one writer per database at a time; reads can be concurrent under WAL
4. **Pre-flight check** before spawning agents: count running agents via `list_agents()`. If >= 3, WAIT.

---

## 🧰 Skills & Tools Registry

### Skill Registry (50 skills)

The `local_model/skills/` directory contains **50 registered skills**. All lazy-loaded via `SKILL_REGISTRY` in `__init__.py`. Each skill connects to `litigation_context.db` and returns structured JSON. Skills cover: legal analysis, evidence scoring, filing production, judicial profiling, adversary prediction, timeline construction, authority graphing, IRAC analysis, forensic reporting, witness preparation, risk dashboards, alienation analysis, and more.

### Awesome-Copilot Skills (17 installed)

17 skills from the awesome-copilot ecosystem are installed and available:
- Code generation, refactoring, documentation, testing, debugging
- SQL query building, API design, security review
- Legal-domain-specific skills for Michigan family law

### Hooks (2 active)

| Hook | Purpose |
|------|---------|
| `governance-audit` | Logs all agent actions for compliance and audit trail |
| `session-logger` | Captures Copilot session events for cross-session learning |

### CLI Tools Available

| Tool | Purpose |
|------|---------|
| `pandoc` | Document conversion (MD → DOCX → PDF, HTML → MD, etc.) |
| `fd` | Fast file finder (rust-based, replaces `find`) |
| `rg` | ripgrep — fast content search (rust-based, replaces `grep`) |
| `jq` | JSON processor for pipeline data manipulation |

### MCP Tools (Extended)

| Tool | Purpose |
|------|---------|
| `litigation_upcoming_deadlines` | Query deadline tracker with urgency scores |
| `litigation_filing_search` | Search filing stacks by lane, court, status, readiness |
| `litigation_evidence_lookup` | Look up evidence atoms by Bates number, source, or claim |
| `litigation_scan_drives` | Scan configured drives for new evidence files |
| `litigation_ingest_pdf` | Ingest and classify a single PDF |
| `litigation_bulk_ingest` | Batch ingest with dedup and lane assignment |
| `litigation_search` | FTS5 full-text search across all indexed documents |
| `litigation_list_documents` | List documents with filters (lane, type, date) |
| `litigation_get_document` | Retrieve document metadata and content |
| `litigation_get_stats` | System-wide statistics dashboard |

---

## 🤖 Copilot Agent Directory (31 agents in `.copilot/agents/`)

| # | Agent | Description |
|---|-------|-------------|
| 1 | `appellate-brief-writer` | Drafts COA/MSC appellate briefs with proper authority and IRAC structure |
| 2 | `authority-chain-validator` | Validates citation chains — MCL→MCR→case law completeness |
| 3 | `bates-stamp-manager` | Assigns and tracks Bates numbers (PIGORS-0001+) across exhibits |
| 4 | `brief-quality-scorer` | Scores briefs on persuasion, authority depth, readability (0-100) |
| 5 | `case-timeline-builder` | Constructs chronological timelines from evidence atoms |
| 6 | `citation-format-checker` | Validates Michigan/Bluebook citation format compliance |
| 7 | `claim-evidence-linker` | Links evidence atoms to legal claims with weight scoring |
| 8 | `court-filing-assembler` | Assembles complete filing packages (motion+brief+order+exhibits) |
| 9 | `court-rule-lookup` | MCR/MCL/MRE quick lookup with context and annotations |
| 10 | `damages-calculator` | Computes financial damages from documented harm events |
| 11 | `deadline-tracker` | Monitors and alerts on upcoming court deadlines |
| 12 | `deposition-prep` | Prepares deposition outlines with impeachment material |
| 13 | `discovery-request-drafter` | Drafts interrogatories, RFPs, and RFAs per MCR 2.309-2.312 |
| 14 | `docket-analyzer` | Parses and analyzes court docket entries for patterns |
| 15 | `evidence-gap-finder` | Identifies missing evidence for each legal element |
| 16 | `exhibit-index-builder` | Builds formatted exhibit indexes for court filings |
| 17 | `filing-readiness-auditor` | Audits filing stacks for completeness and MCR compliance |
| 18 | `impeachment-finder` | Locates contradictions and impeachment material in testimony |
| 19 | `irac-analyzer` | Structures legal arguments in Issue-Rule-Application-Conclusion format |
| 20 | `judicial-bias-detector` | Detects patterns of judicial bias from orders and transcripts |
| 21 | `lane-classifier` | Classifies documents into correct case lanes (A-F) |
| 22 | `legal-research-assistant` | Researches Michigan family law issues with authority support |
| 23 | `motion-drafter` | Drafts motions with proper caption, body, and prayer for relief |
| 24 | `narrative-builder` | Constructs persuasive factual narratives from evidence |
| 25 | `opposing-counsel-profiler` | Profiles opposing counsel tactics and predicts responses |
| 26 | `order-analyzer` | Analyzes court orders for errors, bias, and appeal issues |
| 27 | `ppo-specialist` | Handles PPO-specific filings and weaponization analysis |
| 28 | `pro-se-advisor` | Provides pro se procedural guidance for Michigan courts |
| 29 | `risk-assessor` | Evaluates litigation risk per claim and recommends strategy |
| 30 | `settlement-evaluator` | Evaluates settlement offers against case valuation model |
| 31 | `witness-prep-coach` | Prepares witness examination outlines with key questions |

---

## 🏗️ Superpower Agents (13 cross-cutting)

| # | Agent | Role |
|---|-------|------|
| 1 | `fleet-orchestrator` | Coordinates all 112 agents — scheduling, priority, conflict resolution |
| 2 | `self-evolution-controller` | Manages MANBEARPIG self-evolution cycles |
| 3 | `governance-auditor` | Compliance logging and audit trail for all agent actions |
| 4 | `session-continuity` | Cross-session memory and learning via session_recall.py |
| 5 | `db-health-monitor` | Monitors litigation_context.db integrity, WAL checkpointing, size |
| 6 | `pipeline-scheduler` | Schedules 16-phase pipeline runs with dependency resolution |
| 7 | `evidence-ingestion-coordinator` | Coordinates multi-drive evidence scanning and dedup |
| 8 | `filing-production-manager` | Manages 24+ filing stacks through review --> final --> filed workflow |
| 9 | `quality-gate-enforcer` | Enforces quality thresholds before filings reach COURT_READY |
| 10 | `backup-integrity-checker` | Verifies SHA-256 manifests and backup completeness |
| 11 | `conflict-resolver` | Detects and resolves lane cross-contamination and data conflicts |
| 12 | `metric-dashboard-generator` | Produces system health and case progress dashboards |
| 13 | `emergency-motion-accelerator` | Fast-tracks emergency filings with abbreviated review |

---

## Phase 5-6 Engine Commands (Hardened v2.0)

All Phase 5-6 engines are hardened with: logging (`logging.getLogger(__name__)`), input validation, try/except on all DB/file operations, graceful degradation when DB is unavailable, and UTF-8 encoding on all file I/O. Each engine can be safely imported without side effects.

### Engine Commands

```powershell
# Court Calendar -- deadline management and ICS export
python 00_SYSTEM\engines\court_calendar_engine.py

# Brief Compliance -- MCR 7.212 validation
python 00_SYSTEM\engines\brief_compliance_engine.py [path_to_brief.md]

# Pre-Filing QA -- GO/NO-GO sweep across all stacks
python 00_SYSTEM\engines\prefiling_qa_engine.py

# Evidence Chain -- chain of custody and gap analysis
python 00_SYSTEM\engines\evidence_chain_engine.py

# Backup & Versioning -- scheduled snapshots and file tracking
python 00_SYSTEM\engines\backup_version_engine.py

# Placeholder Resolver v2 -- auto-fill from master DB
python 00_SYSTEM\engines\placeholder_resolver_v2.py

# E-Filing Prep -- TrueFiling/MiFILE/PACER packet assembly
python 00_SYSTEM\engines\efiling_prep_engine.py

# Authority Index -- searchable case law and citation graph
python 00_SYSTEM\engines\authority_index_engine.py
```

### Engine Error Recovery Protocol

Each engine follows this recovery pattern:
1. **Input validation** -- reject None, empty strings, invalid types at entry points
2. **DB availability check** -- if `litigation_context.db` is missing, return sensible defaults (empty lists, zero counts)
3. **Operation-level try/except** -- each DB query, file read, and file write is individually wrapped
4. **Logging** -- all errors logged via `logger.error()`, warnings via `logger.warning()`, debug via `logger.debug()`
5. **Graceful return** -- on failure, return error dict/string instead of crashing
6. **Safe import** -- no side effects at module level; all work happens in `run()` or explicit method calls

---

## Complaint Filing Workflow (9 Agency Types)

### Supported Agency Complaint Types

| # | Agency | Jurisdiction | Filing Method | Key Statute |
|---|--------|-------------|---------------|-------------|
| 1 | **14th Circuit Court** | Muskegon County | MiFILE e-filing | MCR 2.113 |
| 2 | **Michigan Court of Appeals** | Statewide | TrueFiling | MCR 7.212 |
| 3 | **Michigan Supreme Court** | Statewide | TrueFiling | MCR 7.305 |
| 4 | **Judicial Tenure Commission** | Statewide | Mail/Hand delivery | MCR 9.240 |
| 5 | **WDMI Federal Court** | Western District MI | PACER/CM/ECF | 42 USC 1983 |
| 6 | **HUD** | Federal Agency | Online complaint | Fair Housing Act |
| 7 | **LARA** | State Agency | Online/Mail | MCL 125.1501+ |
| 8 | **Attorney Grievance Commission** | Statewide | Written complaint | MCR 9.104 |
| 9 | **DHHS/CPS** | County | Phone/Online | MCL 722.623 |

### Filing Workflow Steps

```
1. Draft complaint (motion-drafter agent or manual)
2. Run brief_compliance_engine.py (MCR validation)
3. Run prefiling_qa_engine.py (GO/NO-GO check)
4. Run placeholder_resolver_v2.py (auto-fill known values)
5. Run efiling_prep_engine.py (packet assembly)
6. Review EFILING_CHECKLIST.md in packet directory
7. Convert MD → PDF via pandoc or doc_assembly_engine.py
8. Upload to appropriate e-filing system
9. File proof of service
```
