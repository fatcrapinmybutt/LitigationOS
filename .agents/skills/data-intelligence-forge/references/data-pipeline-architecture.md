# LitigationOS Data Pipeline Architecture

## Overview

The LitigationOS pipeline is a 16-phase deterministic data processing system that
transforms raw evidence files from 6+ drives into court-ready filings. Every phase
has defined inputs, outputs, and PASS/FAIL gates. The pipeline writes exclusively
to `litigation_context.db` — the single source of truth.

---

## End-to-End Data Flow

```
Raw Files (C:\, D:\, F:\, G:\, H:\, I:\)
  → Phase 0:  Safety Snapshot (SHA-256 manifest + backup)
  → Phase 1:  Inventory (scan all drives, catalog every file)
  → Phase 2:  Dedup (content-based deduplication, move dupes to I:\)
  → Phase 3:  Classify (MEEK signal detection, lane assignment)
  → Phase 4a: Extract PDF (PyMuPDF, OCR fallback)
  → Phase 4b: Extract DOCX (python-docx, metadata extraction)
  → Phase 4c: Extract Structured (JSON, CSV, DB records)
  → Phase 4d: Atomize (break documents into evidence atoms)
  → Phase 4e: Archive (ZIP/RAR contents extraction)
  → Phase 5:  LEXOS Brain Feed (50 micro-brains, 8 categories)
  → Phase 6:  Gap Analysis (EGCP scoring per legal action)
  → Phase 7a: Graph Delta (knowledge graph diff)
  → Phase 7b: Synthesis Merge (cross-source evidence linking)
  → Phase 7c: Knowledge Merge (unified knowledge base)
  → Phase 8:  Litigation Refresh (update filing readiness)
  → Phase 9:  MCP Ingest (load into MCP server tools)
  → Phase 10: Judicial Analysis (bias detection, pattern analysis)
  → Phase 11: Legal Action Discovery (identify available actions)
  → Phase 12: Rule Audit (MCR compliance verification)
  → Phase 13: Refinement (quality improvement pass)
  → Phase 14: Finalization (court-ready output generation)
  → Phase 15: Validation (end-to-end consistency check)
  → Phase 16: Desktop Offload (GUI app data sync)
```

---

## Phase Dependencies

Phases must execute in order. Some phases have sub-dependencies:

| Phase | Depends On | Output Tables |
|-------|-----------|---------------|
| 0 | None | `safety_snapshots`, `file_manifests` |
| 1 | 0 | `documents`, `file_inventory` |
| 2 | 1 | `dedup_clusters`, `dedup_log` |
| 3 | 2 | `classified_documents`, `lane_assignments` |
| 4a-4e | 3 | `extracted_text`, `evidence_quotes`, `atoms` |
| 5 | 4a-4e | `brain_feeds`, `lexos_categories` |
| 6 | 5 | `gap_analysis`, `egcp_scores` |
| 7a-7c | 6 | `knowledge_graph`, `synthesis_results` |
| 8 | 7c | `filing_readiness`, `litigation_status` |
| 9 | 8 | MCP server cache refresh |
| 10-12 | 9 | `judicial_findings`, `legal_actions`, `rule_audit` |
| 13-16 | 12 | Final outputs, validation reports |

---

## Six Case Lanes

Every document is classified into exactly one lane via MEEK signal detection:

| Lane | Subject | MEEK Signal | Case Numbers |
|------|---------|-------------|-------------|
| A | Watson Custody | MEEK2 | 2024-001507-DC, 2023-5907-PP |
| B | Shady Oaks Housing | MEEK1 | 2025-002760-CZ |
| C | Convergence | — | Multi-lane cross-references |
| D | PPO / Protection | MEEK3 | 2024-001507-DC, 2023-5907-PP |
| E | Judicial Misconduct | MEEK4 | 2024-001507-DC |
| F | Appellate | MEEK5 | COA 366810 |

**Detection priority**: E → D → F → C → A → B
**Cross-contamination**: A `LaneCrossContaminationError` is raised (non-fatal) when
evidence from the wrong lane is detected. The item is skipped, not misclassified.

---

## MEEK Signal Detection

MEEK signals are compiled regexes defined in `config.py → MEEK_SIGNALS` dict.
Each signal maps document content patterns to case lanes:

- **MEEK1**: Housing-related terms (lease, eviction, habitability, Shady Oaks)
- **MEEK2**: Custody terms (parenting time, custody, visitation, child support)
- **MEEK3**: PPO terms (personal protection order, stalking, harassment)
- **MEEK4**: Judicial misconduct (bias, ex parte, recusal, disqualification)
- **MEEK5**: Appellate terms (appeal, COA, MSC, claim of appeal)

---

## Key Pipeline Commands

### Full Pipeline Run
```powershell
cd 00_SYSTEM\pipeline
python run_omega_pipeline.py
```

### Phase Range
```powershell
python run_omega_pipeline.py --start-phase 4a --end-phase 7c
```

### Single Phase
```powershell
python phase3_classify.py
```

### Dry Run
```powershell
python run_omega_pipeline.py --dry-run --create-snapshot
```

### Status Check
```powershell
python quick_status.py
```

---

## Output Formats

| Phase Group | Primary Output | Format |
|-------------|---------------|--------|
| Phases 0-3 | Inventory + Classification | SQLite tables |
| Phases 4a-4e | Extracted content | SQLite + text files |
| Phases 5-6 | Brain feeds + Gap analysis | JSON + SQLite |
| Phases 7a-7c | Knowledge graph | SQLite + graph export |
| Phases 8-9 | Filing readiness | SQLite + MCP cache |
| Phases 10-12 | Analysis results | SQLite + reports |
| Phases 13-16 | Court-ready filings | Markdown + PDF |

---

## Agent Fleet Integration

The pipeline is executed by the 155+ agent fleet:

| Fleet | Agents | Pipeline Role |
|-------|--------|--------------|
| Lane 1 (I/O) | A01-A12 | Phases 0-4 (inventory, dedup, extraction) |
| Lane 2 (Intelligence) | J01-L08 | Phases 10-12 (analysis, discovery, audit) |
| Convergence | F01-F06 | Phases 5-9, 13-16 (synthesis, filing) |

All agents inherit `Agent9999` from `agents/agent_base.py`.
Agent contract: `run() → AgentResult(agent_id, status, stats)`.
Status values: SUCCESS | FATAL | CRASH.

---

## Error Recovery

The pipeline uses the 7-Layer Error Protocol:
1. Try operation
2. Specific catch → targeted recovery
3. Broad catch → log + skip + continue
4. Checkpoint every N items → crash-resume capability
5. Deadman switch (120s no progress → self-diagnose)
6. Agent retry (3× exponential backoff)
7. Tier fallback → orchestrator flags and continues

### Crash Resume
Each phase writes checkpoint files. On restart, the pipeline reads the last
checkpoint and resumes from there — no re-processing of completed items.

---

## Database Write Discipline

- **Only the pipeline writes to litigation_context.db** (phases are the writers)
- **Apps, MCP tools, and agents READ from litigation_context.db** (consumers)
- **Lane-specific DBs** (`lane_A_custody.db` etc.) have their own write paths
- **Never bypass the pipeline** to write directly to litigation_context.db
- **All writes use WAL mode** with managed_db() from db_lock_manager.py
