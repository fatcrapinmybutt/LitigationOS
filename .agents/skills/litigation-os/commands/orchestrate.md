# OMEGA Pipeline Orchestration Protocol

## When to Use

- Processing a new evidence directory (e.g., `C:\Users\andre\scans`)
- Re-running analysis after new evidence is discovered
- Rebuilding knowledge base after document updates
- Preparing for a new round of court filings

## Quick Start

```bash
# CLI Mode — Full pipeline
python tooling/safety.py --target C:\Users\andre\scans
python tooling/run_omega_pipeline.py --target C:\Users\andre\scans
python tooling/validate.py --snapshot SNAPSHOT_xxx

# CLI Mode — Single phase
python tooling/run_omega_pipeline.py --phase 3 --target C:\Users\andre\scans

# CLI Mode — Dry run (no writes)
python tooling/run_omega_pipeline.py --dry-run --target C:\Users\andre\scans

# Rollback — Full revert
python tooling/rollback.py --snapshot SNAPSHOT_xxx

# Rollback — Per-phase revert
python tooling/rollback.py --snapshot SNAPSHOT_xxx --phase 7b
```

## Pipeline Flow

```
PHASE 0 (Safety) → Snapshot verified
  ↓
PHASE 1 (Inventory) → Files cataloged in SQLite
  ↓
PHASE 2 (Dedup) → Canonical files elected
  ↓
PHASE 3 (Classify) → Files tagged HIGH/MED/LOW/SKIP + MEEK lanes
  ↓
PHASE 4A-E (Extract) → Text extractions + 5 atom stores
  ↓
PHASE 5 (Brains) → 50 LEXOS nuclei populated
  ↓
PHASE 6 (Gaps) → EGCP v2 gap tickets
  ↓
PHASE 7A-D (Merge) → Graph delta + SYNTHESIS + knowledge base
  ↓
PHASE 8 (Impeachment) → Contradiction/adversary refresh
  ↓
PHASE 9 (MCP) → Searchable PDF corpus
  ↓
PHASE 10 (Judicial) → Judge misconduct + benchbook audit
  ↓
PHASE 11 (Legal Actions) → 56 actions × 11 adversaries scored
  ↓
PHASE 12 (Rules) → MCR/MCL compliance verification
  ↓
PHASE 13 (Refine) → Filings enhanced with new evidence
  ↓
PHASE 14 (Finalize) → Court packets + DOCX + exhibits + POS
  ↓
PHASE 15 (Validate) → Final QA → ready_to_file.json
  ↓
PHASE 16 (Desktop) → Blueprint exported to LitigationOS-Desktop
```

## Phase Dependencies

| Phase | Depends On | Can Run Independently? |
|-------|-----------|----------------------|
| 0 (Safety) | Nothing | YES — always runs first |
| 1 (Inventory) | 0 | YES after safety |
| 2 (Dedup) | 1 | NO — needs inventory.db |
| 3 (Classify) | 2 | NO — needs canonical flags |
| 4A-E (Extract) | 3 | NO — needs classifications |
| 5 (Brains) | 4 | NO — needs atom stores |
| 6 (Gaps) | 4, 5 | NO — needs atoms + brains |
| 7A-D (Merge) | 4, 5, 6 | NO — needs all prior data |
| 8 (Impeachment) | 4, 7 | NO — needs new evidence + merged data |
| 9 (MCP) | 4A | YES after PDF extraction |
| 10 (Judicial) | 7, 8 | NO — needs merged + impeachment data |
| 11 (Legal Actions) | 10 | NO — needs judicial analysis |
| 12 (Rules) | 11 | NO — needs legal action matrix |
| 13 (Refine) | 12 | NO — needs rule audit results |
| 14 (Finalize) | 13 | NO — needs refined filings |
| 15 (Validate) | 14 | NO — needs finalized packets |
| 16 (Desktop) | 15 | NO — needs validated results |

## Resume After Failure

The orchestrator reads checkpoint files from `cyclepacks/CYCLE_{ts}/checkpoints/`:

```bash
# Pipeline resumes from last successful phase automatically
python tooling/run_omega_pipeline.py --target C:\Users\andre\scans
# ↑ Reads checkpoints, skips completed phases, resumes from failure point
```

## Adapting for New Cases

1. Edit `tooling/config.py`: person names, case numbers, adversaries, MEEK lane mappings
2. Edit scoring regexes for different legal domains
3. Run pipeline on new evidence directory
4. All outputs are case-agnostic — blueprint works for ANY litigation

## Output Location

All outputs go to `LITIGATIONOS_MASTER/cyclepacks/CYCLE_{timestamp}/`:
- `inventory.db` — SQLite catalog of all files
- `extracts/` — Text extractions by SHA-256
- `*_atoms.jsonl` — 5 atom stores (fact, citation, event, person, contradiction)
- `checkpoints/` — Per-phase completion records
- `touchlog_phase*.jsonl` — Per-phase file-write audit trail
- `lane_a_watson/`, `lane_b_housing/`, `lane_c_convergence/` — Per-lane legal action outputs
- `refined_filings/` — Enhanced court filings
- `COURT_PACKETS_v4/` — Court-ready filing packets

See [pipeline/README.md](references/pipeline/README.md) for detailed phase documentation.
