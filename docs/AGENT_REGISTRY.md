# LitigationOS — Agent Registry

> Auto-generated agent catalog. Last updated: 2025.
> Total agents: **155+** across Delta9 pipeline, Copilot, and root orchestrator fleets.

---

## Table of Contents

1. [Delta9 Pipeline Agents (56)](#delta9-pipeline-agents)
2. [Root Orchestrator Agents (7)](#root-orchestrator-agents)
3. [Copilot Agents (53)](#copilot-agents)

---

## Delta9 Pipeline Agents

Located in `00_SYSTEM/pipeline/agents/`. All inherit from `Agent9999` (agent_base.py).

Agent contract: `run() → AgentResult(agent_id, status, stats)`.
Status values: `SUCCESS | FATAL | CRASH`.

### Base Infrastructure

| File | Class | Purpose |
|------|-------|---------|
| `agent_base.py` | `Agent9999` | Base class — parallel I/O, per-item timeout, adaptive checkpoint, deadman switch (120s) |
| `agent_models.py` | — | Data classes, constants, `AgentResult` model |
| `agent_orchestrator.py` | — | Fleet orchestration, tier sequencing, retry logic |

### Tier 1 — Index Scouts (Lane 1: Infrastructure)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| A01 | `a01_index_scout_c.py` | `IndexScoutC` | Crawls C:\Users\andre\scans AND C:\Users\andre\LitigationOS | Active |
| A02 | `a02_index_scout_d.py` | `IndexScoutD` | Crawls D:\ drive in its entirety | Active |
| A03 | `a03_index_scout_f.py` | `IndexScoutF` | Crawls F:\ drive in its entirety | Active |
| A04 | `a04_index_scout_gi.py` | `IndexScoutGI` | Crawls G:\CAPSTONE AND I:\ drive | Active |

### Tier 2 — Dedup Agents (Lane 1: Infrastructure)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| A05-LEGAL-DEDUP | `a05_legal_dedup.py` | `LegalDedup` | Hash legal files, cluster duplicates, elect canonical per cluster | Active |
| A06-DATA-DEDUP | `a06_data_dedup.py` | `DataDedup` | Hash data files, cluster duplicates, elect canonical per cluster | Active |
| A07-CODE-DEDUP | `a07_code_dedup.py` | `CodeDedup` | Hash code files, mark duplicates — never delete. Tag pipeline/framework | Active |
| A08-ARCHIVE-CRACKER | `a08_archive_cracker.py` | `ArchiveCracker` | Catalog archive contents into zip_contents, flag CRITICAL archives | Active |

### Tier 3 — Extraction Agents (Lane 1: Infrastructure)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| A09 | `a09_flatten_commander.py` | `FlattenCommander` | Computes dest_path for canonical files to flatten directory depth to ≤3 levels | Active |
| A10 | `a10_pdf_harvester.py` | `PdfHarvester` | Extracts text from canonical PDFs, classifies content, detects MEEK lane | Active |
| A11 | `a11_text_miner.py` | `TextMiner` | Classifies and extracts entities from canonical .md/.txt files | Active |
| A12 | `a12_struct_parser.py` | `StructParser` | Parses canonical .json, .jsonl, .csv files for legal content | Active |

### Tier J — Judicial Intelligence (Lane 2: Intelligence)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| J01-MCNEILL | `j01_mcneill_profiler.py` | `McNeillProfiler` | Profile Judge McNeill's judicial actions from ingested files | Active |
| J02-HOOPES | `j02_hoopes_profiler.py` | `HoopesProfiler` | Profile Judge Hoopes' judicial actions, especially housing case compliance | Active |
| J03 | `j03_benchbook_auditor.py` | `BenchbookAuditor` | Audits judicial actions against benchbook procedures | Active |
| J04 | `j04_canon_mapper.py` | `CanonMapper` | Maps judicial actions to Michigan Code of Judicial Conduct violations | Active |
| J05-JTC | `j05_jtc_compiler.py` | `JtcCompiler` | Compile JTC complaint exhibits from judicial findings | Active |
| J06 | `j06_disqualification.py` | `DisqualificationEngine` | Scores MCR 2.003(C) grounds for judicial disqualification | Active |
| J07 | `j07_exparte_detector.py` | `ExParteDetector` | Scans ALL content for ex parte communication indicators | Active |
| J08 | `j08_transcript_impeacher.py` | `TranscriptImpeacher` | Processes hearing transcripts to extract testimony & identify inconsistencies | Active |

### Tier K — Case Intelligence (Lane 2: Intelligence)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| K01 | `k01_lane_a_custody.py` | `LaneACustody` | Scores custody evidence per MCL 722.23 best interest factors (a–l) | Active |
| K02 | `k02_lane_a_ppo.py` | `LaneAPpo` | Analyzes PPO/contempt content: modification grounds, due process, overbreadth | Active |
| K03 | `k03_lane_b_housing.py` | `LaneBHousing` | Scores housing claims per MCL 554.139, MCL 445.903, MCL 554.602-612, MCL 600.5720 | Active |
| K04 | `k04_lane_c_convergence.py` | `LaneCConvergence` | Identifies cross-lane convergence evidence & builds Monell patterns | Active |
| K05 | `k05_person_profiler.py` | `PersonProfiler` | Builds adversary profiles: tracks every mention, statement, role | Active |
| K06 | `k06_timeline_builder.py` | `TimelineBuilder` | Extracts ALL dates/events across processed content | Active |
| K07 | `k07_authority_harvester.py` | `AuthorityHarvester` | Extracts ALL MCL/MCR/MRE/case/federal citations | Active |
| K08 | `k08_contradiction_detector.py` | `ContradictionDetector` | Cross-references statements across files to find contradictions | Active |
| K09 | `k09_lane_d_ppo.py` | `LaneDPPOIntel` | Identifies PPO violation evidence, contempt patterns, bond condition breaches | Active |
| K10 | `k10_lane_e_misconduct.py` | `LaneEMisconductIntel` | Identifies judicial bias, canon violations, procedural misconduct | Active |
| K11 | `k11_lane_f_appellate.py` | `LaneFAppellateIntel` | Identifies appellate preservation, standard-of-review markers | Active |

### Tier L — Legal Warfare Scoring (Lane 2: Intelligence)

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| L01 | `l01_lane_a_scorer.py` | `LaneAScorer` | Scores ALL evidence against Lane A legal actions (A1–A35) | Active |
| L02 | `l02_lane_b_scorer.py` | `LaneBScorer` | Scores ALL evidence against Lane B housing/tenant legal actions (B1–B14) | Active |
| L03 | `l03_lane_c_scorer.py` | `LaneCScorer` | Scores against Lane C convergence actions (C1–C7) | Active |
| L04 | `l04_gap_detector.py` | `GapDetector` | Compares discovered evidence against COMPLETE requirement list for all 56 actions | Active |
| L05 | `l05_citation_validator.py` | `CitationValidator` | Verifies every MCR/MCL/MRE citation found in atoms | Active |
| L06 | `l06_damages_calculator.py` | `DamagesCalculator` | Computes damages per lane: emotional distress, security deposit, punitive | Active |
| L07 | `l07_filing_readiness.py` | `FilingReadiness` | Scores each of 56 legal actions on evidence/authority/vulnerability/procedural readiness | Active |
| L08 | `l08_red_team_scanner.py` | `RedTeamScanner` | For each top-10 priority filing: simulates opposing counsel attacks & judge skepticism | Active |
| L09 | `l09_lane_d_scorer.py` | `LaneDScorer` | Scores against Lane D PPO actions (D1–D7) | Active |
| L10 | `l10_lane_e_scorer.py` | `LaneEScorer` | Scores against Lane E judicial misconduct actions (E1–E8) | Active |
| L11 | `l11_lane_f_scorer.py` | `LaneFScorer` | Scores against Lane F appellate actions (F1–F8) | Active |

### Convergence Tier — Filing Assembly & Certification

| Agent ID | File | Class | Purpose | Status |
|----------|------|-------|---------|--------|
| F01-FILING | `f01_filing_factory.py` | `FilingFactory` | Assembles court packets from scored legal actions | Active |
| F02 | `f02_brain_feeder.py` | `BrainFeeder` | Feeds atoms into the 50 LEXOS brain nuclei concept | Active |
| F03 | `f03_graph_builder.py` | `GraphBuilder` | Merges all atoms into knowledge graph deltas (Neo4j-compatible CSV) | Active |
| F04 | `f04_msc_architect.py` | `MscArchitect` | Evaluates Michigan Supreme Court filing paths for viability | Active |
| F05 | `f05_test_runner.py` | `TestRunner` | Runs 15 system verification tests across the entire pipeline | Active |
| F06 | `f06_convergence_certifier.py` | `ConvergenceCertifier` | Computes FINAL convergence scores and issues pipeline verdict | Active |

---

## Root Orchestrator Agents

Located in `agents/` (repo root). Lightweight orchestration layer for case processing.

| File | Purpose |
|------|---------|
| `agent_base.py` | Base class for root-level agents |
| `authority_agent.py` | Legal authority research and citation validation |
| `chronology_agent.py` | Chronological event extraction and timeline building |
| `evidence_agent.py` | Evidence atom extraction and classification |
| `feedback_agent.py` | Agent output quality feedback and iteration |
| `filing_agent.py` | Court filing packet assembly |
| `orchestrator.py` | End-to-end deterministic run: Evidence → Chronology → Filing → Manifest |
| `__init__.py` | Package init |

---

## Copilot Agents

Located in `.copilot/agents/` (backup preserved at `00_SYSTEM/backups/backup_20260304_212018/.copilot/agents/`).
53 specialized agents for litigation workflows, code quality, and research.

| # | Agent File | Purpose |
|---|-----------|---------|
| 1 | `adversary-war-room.agent.md` | Adversary strategy simulation and counter-argument preparation |
| 2 | `appellate-strategy.agent.md` | Appellate brief strategy, standard of review analysis |
| 3 | `brief-quality-scorer.agent.md` | Scores brief quality against court rules and persuasion metrics |
| 4 | `brief-writer.agent.md` | Drafts legal briefs with proper citation and argument structure |
| 5 | `citation-researcher.agent.md` | Deep citation research across MCL, MCR, MRE, and case law |
| 6 | `context-architect.agent.md` | Plans multi-file changes by mapping context and dependencies |
| 7 | `convergence-coordinator.agent.md` | Cross-lane convergence pattern identification and coordination |
| 8 | `cost-tracker.agent.md` | Tracks litigation costs: filing fees, service, copies, mileage |
| 9 | `court-form-finder.agent.md` | Finds correct Michigan SCAO court forms by filing type |
| 10 | `critical-thinking.agent.md` | Challenges assumptions, stress-tests ideas, finds flaws |
| 11 | `deadline-sentinel.agent.md` | Monitors and alerts on approaching filing deadlines |
| 12 | `debug.agent.md` | Application bug investigation and debugging |
| 13 | `deposition-prep.agent.md` | Prepares deposition questions and witness examination outlines |
| 14 | `devils-advocate.agent.md` | Counter-arguments, worst-case analysis, risk assessment |
| 15 | `discovery-manager.agent.md` | Discovery request/response management and compliance tracking |
| 16 | `document-classifier.agent.md` | Classifies documents by type, relevance, and case lane |
| 17 | `evidence-authenticator.agent.md` | Evidence authentication under MRE 901/902 |
| 18 | `evidence-harvester.agent.md` | Extracts and catalogs evidence from source documents |
| 19 | `exhibit-curator.agent.md` | Curates and organizes exhibit collections for court |
| 20 | `exhibit-formatter.agent.md` | Formats exhibits with Bates stamps, tabs, and indexes |
| 21 | `federal-1983-specialist.agent.md` | 42 U.S.C. § 1983 civil rights claim specialist |
| 22 | `filing-assembler.agent.md` | Assembles complete filing packages for court submission |
| 23 | `filing-countdown.agent.md` | Deadline countdown dashboard with urgency levels |
| 24 | `filing-router.agent.md` | Routes filings to correct court and lane |
| 25 | `financial-analyst.agent.md` | Financial analysis for damages calculations |
| 26 | `gdrive-watcher.agent.md` | Google Drive file monitoring and sync |
| 27 | `harm-tracker.agent.md` | Tracks and documents instances of harm for damages claims |
| 28 | `impeachment-commander.agent.md` | Witness impeachment strategy and material preparation |
| 29 | `janitor.agent.md` | Codebase cleanup, simplification, tech debt remediation |
| 30 | `judicial-bias-detector.agent.md` | Detects patterns of judicial bias from court records |
| 31 | `legal-phase-indexer.agent.md` | Structures complex litigation phases into machine-readable indexes |
| 32 | `legal-research-deep.agent.md` | Multi-source legal research with relevance ranking |
| 33 | `mcr-compliance-validator.agent.md` | Validates filings against Michigan Court Rules |
| 34 | `michigan-litigation-orchestrator.agent.md` | Multi-step Michigan filing workflow orchestration |
| 35 | `motion-drafter.agent.md` | Drafts motions with proper legal formatting and argument |
| 36 | `ms-sql-dba.agent.md` | Microsoft SQL Server database administration |
| 37 | `msc-fleet-commander.agent.md` | Michigan Supreme Court filing strategy coordination |
| 38 | `opposing-counsel-analyzer.agent.md` | Analyzes opposing counsel patterns and likely strategies |
| 39 | `order-compliance-monitor.agent.md` | Tracks compliance with existing court orders |
| 40 | `plan.agent.md` | Strategic planning and architecture analysis |
| 41 | `planner.agent.md` | Implementation plan generation for features/refactoring |
| 42 | `pre-filing-qa.agent.md` | Pre-filing quality assurance sweep — GO/NO-GO report |
| 43 | `principal-software-engineer.agent.md` | Principal-level engineering guidance and technical leadership |
| 44 | `pro-se-compliance.agent.md` | Pro se filing compliance and formatting validation |
| 45 | `redaction-agent.agent.md` | Auto-redacts PII and sensitive information |
| 46 | `repo-architect.agent.md` | Bootstraps and validates agentic project structures |
| 47 | `research-technical-spike.agent.md` | Systematic technical spike research and validation |
| 48 | `se-security-reviewer.agent.md` | Security-focused code review (OWASP, Zero Trust) |
| 49 | `se-technical-writer.agent.md` | Technical documentation and developer content |
| 50 | `service-tracker.agent.md` | Tracks proof of service across all cases and courts |
| 51 | `settlement-calculator.agent.md` | Settlement value calculation and negotiation ranges |
| 52 | `timeline-builder.agent.md` | Chronological event timeline construction |
| 53 | `transcript-analyzer.agent.md` | Extracts testimony, rulings, objections from transcripts |
| 54 | `witness-profiler.agent.md` | Builds witness profiles for examination preparation |

---

## Fleet Summary

| Fleet | Count | Location | Status |
|-------|-------|----------|--------|
| Delta9 Tier 1 (Index Scouts) | 4 | `00_SYSTEM/pipeline/agents/a01-a04` | Active |
| Delta9 Tier 2 (Dedup) | 4 | `00_SYSTEM/pipeline/agents/a05-a08` | Active |
| Delta9 Tier 3 (Extraction) | 4 | `00_SYSTEM/pipeline/agents/a09-a12` | Active |
| Delta9 Tier J (Judicial Intel) | 8 | `00_SYSTEM/pipeline/agents/j01-j08` | Active |
| Delta9 Tier K (Case Intel) | 11 | `00_SYSTEM/pipeline/agents/k01-k11` | Active |
| Delta9 Tier L (Legal Scoring) | 11 | `00_SYSTEM/pipeline/agents/l01-l11` | Active |
| Convergence | 6 | `00_SYSTEM/pipeline/agents/f01-f06` | Active |
| Root Orchestrator | 7 | `agents/` | Active |
| Copilot Agents | 54 | `.copilot/agents/` (backup) | Archived |
| **Total** | **109** | — | — |

> **Note:** The AGENTS.md system manifest references 155+ total agents including Delta999 (12),
> Superpower (13), and Convergence expansion (10) agents not yet enumerated in individual files.
> This registry covers only agents with discoverable source files.
