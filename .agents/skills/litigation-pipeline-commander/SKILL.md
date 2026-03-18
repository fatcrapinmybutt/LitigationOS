---
name: litigation-pipeline-commander
description: >-
  Use when executing the OMEGA 16-phase litigation pipeline, managing phase dependencies, recovering from checkpoint failures, or orchestrating intake-to-desktop workflows.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: pipeline, OMEGA, phase, checkpoint, orchestrate
---

# litigation-pipeline-commander

## Metadata

```yaml
name: litigation-pipeline-commander
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when executing the OMEGA 16-phase litigation pipeline, managing phase
  dependencies, recovering from checkpoint failures, or orchestrating the
  full intake-to-desktop workflow for Michigan litigation case processing.
metadata:
  triggers:
    - pipeline execution
    - OMEGA pipeline
    - phase management
    - checkpoint recovery
    - pipeline error
    - phase dependency
    - intake to desktop
    - 16-phase pipeline
    - pipeline restart
  lanes:
    - A: Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)
    - B: Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)
    - C: Convergence/County (Muskegon County, 14th Circuit)
  court: 14th Judicial Circuit, Muskegon County
  case: Pigors v Watson
  dependencies:
    - litigation-brain-spec
    - litigation-convergence-orchestrator
    - litigation-authority-validator
    - litigation-filing-packager
```

---

## Purpose

The OMEGA pipeline is the backbone of LitigationOS case processing. It takes
raw case data — documents, evidence, communications, court records — and
transforms it through 16 sequential phases into courtroom-ready work product.
Every phase has entry conditions, exit conditions, and checkpoint requirements.
This skill commands the pipeline: executing phases, managing dependencies,
recovering from errors, and ensuring no phase is skipped or corrupted.

---

## OMEGA 16-Phase Pipeline

```
Phase 0:  SAFETY         — Validate inputs, check for PII exposure, verify permissions
Phase 1:  INVENTORY      — Catalog all case materials, assign unique IDs
Phase 2:  DEDUP          — Remove duplicate documents, merge near-duplicates
Phase 3:  CLASSIFY       — Categorize documents by type, lane, relevance
Phase 4:  EXTRACT        — Pull structured data from unstructured documents
Phase 5:  BRAINS         — Build/update brain-spec knowledge graphs
Phase 6:  GAPS           — Identify missing evidence, authority, strategy gaps
Phase 7:  MERGE          — Consolidate cross-lane data, resolve conflicts
Phase 8:  IMPEACH        — Build impeachment packages for adverse witnesses
Phase 9:  MCP            — Sync with MCP tools, update litigation context
Phase 10: JUDICIAL       — Analyze judicial patterns, predict rulings
Phase 11: LEGAL ACTIONS  — Draft motions, briefs, complaints from processed data
Phase 12: RULES          — Validate all outputs against MCR/MCL/MRE
Phase 13: REFINE         — Polish language, check tone, verify persuasiveness
Phase 14: FINALIZE       — Final quality check, authority validation, formatting
Phase 15: VALIDATE       — Full convergence cycle on complete work product
Phase 16: DESKTOP        — Package for LitigationOS Desktop delivery
```

---

## Phase Dependency Graph

```
Phase 0 (Safety)
  └─→ Phase 1 (Inventory)
       └─→ Phase 2 (Dedup)
            └─→ Phase 3 (Classify)
                 ├─→ Phase 4 (Extract) ──→ Phase 5 (Brains)
                 │                              └─→ Phase 6 (Gaps)
                 │                                    └─→ Phase 7 (Merge)
                 └─────────────────────────────────────────┘
                                                           │
                 Phase 7 (Merge) ─────────────────────────→│
                   ├─→ Phase 8 (Impeach)                   │
                   ├─→ Phase 9 (MCP)                       │
                   └─→ Phase 10 (Judicial)                 │
                          └─→ Phase 11 (Legal Actions)     │
                               └─→ Phase 12 (Rules)
                                    └─→ Phase 13 (Refine)
                                         └─→ Phase 14 (Finalize)
                                              └─→ Phase 15 (Validate)
                                                   └─→ Phase 16 (Desktop)
```

### Parallel Execution Windows
- Phases 4-5 can run parallel to Phase 3 completion processing
- Phases 8, 9, 10 can run in parallel after Phase 7 completes
- All other phases are strictly sequential

---

## Decision Tree

```
ENTRY: Pipeline execution request
│
├─ Q1: Fresh run or resume?
│   ├─ FRESH ───────── → Start at Phase 0
│   └─ RESUME ────────── → Load last checkpoint → Resume at failed phase
│
├─ Q2: Which lanes?
│   ├─ Single lane ──── → Lane-specific pipeline
│   ├─ Multi-lane ───── → Parallel pipelines with merge at Phase 7
│   └─ Full (A+B+C) ── → Complete pipeline with convergence synthesis
│
├─ Q3: Phase override requested?
│   ├─ YES ────────────── → Validate override is safe → Execute specific phase
│   └─ NO ─────────────── → Execute sequentially from current position
│
├─ Q4: Error encountered?
│   ├─ RECOVERABLE ───── → Apply error recovery protocol → Retry phase
│   ├─ NON-RECOVERABLE → → Save checkpoint → Escalate → HALT
│   └─ DATA CORRUPTION → → Rollback to last good checkpoint → Alert
│
└─ Q5: All phases complete?
    ├─ YES ────────────── → Generate pipeline_completion_report
    └─ NO ─────────────── → Continue to next phase
```

---

## Phase Specifications

### Phase 0: SAFETY
```yaml
entry_conditions:
  - Raw case materials available
  - Lane assignment confirmed
  - Permissions verified
actions:
  - Scan all inputs for PII exposure risks
  - Verify file integrity (checksums)
  - Check for privileged material markers
  - Validate input format compatibility
exit_conditions:
  - All inputs pass safety checks
  - PII inventory logged
  - No privilege violations detected
checkpoint: phase_0_safety_complete.json
```

### Phase 1: INVENTORY
```yaml
entry_conditions:
  - Phase 0 checkpoint exists and valid
actions:
  - Assign unique document IDs (DOC-LANE-NNNN format)
  - Catalog: filename, type, date, source, lane, size
  - Build master document index
  - Tag with preliminary relevance scores
exit_conditions:
  - All documents have unique IDs
  - Master index complete
  - No orphaned files
checkpoint: phase_1_inventory_complete.json
```

### Phase 2: DEDUP
```yaml
entry_conditions:
  - Phase 1 checkpoint exists and valid
actions:
  - Hash-based exact duplicate detection
  - Fuzzy matching for near-duplicates (>90% similarity)
  - Merge near-duplicates with provenance tracking
  - Log all dedup decisions with rationale
exit_conditions:
  - Zero exact duplicates remain
  - Near-duplicates merged or flagged
  - Dedup log complete
checkpoint: phase_2_dedup_complete.json
```

### Phase 3: CLASSIFY
```yaml
entry_conditions:
  - Phase 2 checkpoint exists and valid
actions:
  - Classify by document type (motion, exhibit, correspondence, etc.)
  - Assign lane (A, B, C, or multi-lane)
  - Score relevance (0-100)
  - Tag with legal category codes
exit_conditions:
  - All documents classified
  - Lane assignments complete
  - Relevance scores assigned
checkpoint: phase_3_classify_complete.json
```

### Phases 4-16: See references/phase-specs.md for full specifications

---

## Checkpoint Format

```yaml
checkpoint:
  phase: integer         # 0-16
  phase_name: string
  timestamp: ISO-8601
  status: enum [complete, failed, partial]
  lane: enum [A, B, C, ALL]
  documents_processed: integer
  documents_total: integer
  errors: list[error_record]
  metrics:
    duration_seconds: integer
    memory_peak_mb: integer
  hash: string           # SHA-256 of checkpoint data
  previous_checkpoint: string  # hash of prior checkpoint
  resumable: boolean
```

---

## Error Recovery Protocol

```
ERROR DETECTED
│
├─ LEVEL 1: Transient Error (timeout, temp file lock)
│   ├─ Wait 30 seconds
│   ├─ Retry phase from last sub-checkpoint
│   └─ Max 3 retries → escalate to Level 2
│
├─ LEVEL 2: Data Error (malformed input, parse failure)
│   ├─ Quarantine problematic document
│   ├─ Continue phase with remaining documents
│   ├─ Log quarantined items for manual review
│   └─ Phase completes with quarantine report
│
├─ LEVEL 3: Logic Error (unexpected state, assertion failure)
│   ├─ Save full state dump
│   ├─ Rollback to previous checkpoint
│   ├─ Attempt phase restart with diagnostic logging
│   └─ If restart fails → escalate to Level 4
│
└─ LEVEL 4: Critical Failure (data corruption, system error)
    ├─ HALT pipeline immediately
    ├─ Save all state for forensic analysis
    ├─ Rollback to last known-good checkpoint
    └─ REQUIRE manual intervention before resume
```

---

## Output Contract

```yaml
pipeline_completion_report:
  pipeline_id: string
  start_time: ISO-8601
  end_time: ISO-8601
  total_duration_minutes: integer
  lanes_processed: list[enum[A, B, C]]
  phases_completed: list[integer]  # 0-16
  phases_skipped: list[integer]    # should be empty
  phases_failed: list[integer]     # should be empty
  documents:
    total_input: integer
    total_output: integer
    quarantined: integer
    deduplicated: integer
  quality_score: float    # from Phase 15 convergence
  checkpoints: list[checkpoint]
  errors: list[error_record]
  deliverables:
    filings_generated: integer
    briefs_generated: integer
    impeachment_packages: integer
    desktop_package_path: string
```

---

## Lane-Specific Pipeline Considerations

### Lane A: Watson/Custody
- Phase 3 must classify parenting time logs separately
- Phase 5 builds custody-specific brain with 12 best-interest factors
- Phase 8 impeachment focused on Watson's contradictory statements
- Phase 10 analyzes Judge McNeill's custody ruling patterns

### Lane B: Shady Oaks/Housing
- Phase 1 must inventory all housing inspection reports
- Phase 4 extracts lease terms, violation dates, repair records
- Phase 6 gaps focused on damage quantification evidence
- Phase 10 analyzes Judge Hoopes' housing case patterns

### Lane C: Convergence/County
- Phase 7 merge is CRITICAL — this is where lanes converge
- Phase 5 builds cross-lane entity graph
- Phase 6 gaps focused on cross-lane contradictions
- Phase 11 generates convergence-aware legal actions

---

## Pipeline Monitoring

```
EVERY 60 SECONDS during active pipeline:
  - Report current phase and sub-step
  - Report documents processed / total
  - Report elapsed time vs estimated completion
  - Check for stalls (no progress in 5 minutes)
  - If stalled: trigger diagnostic → attempt recovery
```

## Related Skills

- [litigation-convergence-orchestrator](skill://litigation-convergence-orchestrator) — Orchestrates convergence quality cycles
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Extracts and classifies case evidence


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E | Verified |
| Contempt | 70/100 | A,B,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E | Verified |
| Default Judgment | 60/100 | A,B,C,D,E | Verified |
| TRO Application | 60/100 | A,B,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
