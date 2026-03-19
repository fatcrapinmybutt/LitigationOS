# Pipeline Operations Manual

> **LitigationOS OMEGA Pipeline** — 24-phase evidence-to-filing pipeline with 56-agent DELTA9 fleet.
> Generated from `run_omega_pipeline.py`, `config.py`, and `agent_orchestrator.py`.

---

## Quick Start

```powershell
# 1. Full pipeline run (creates safety snapshot first)
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline
python run_omega_pipeline.py --create-snapshot

# 2. Dry run (no files written, validates phase chain)
python run_omega_pipeline.py --dry-run

# 3. Run specific phase range
python run_omega_pipeline.py --start-phase 4a --end-phase 7c
```

---

## Phase Reference Table

All 24 phases execute sequentially. Each phase checkpoints on completion and can be resumed.

| Phase ID | Module | Description |
|----------|--------|-------------|
| **0** | `safety` | Safety Snapshot — SHA-256 manifest + backup of all source files |
| **0.5** | `phase0_5_drive_ingest` | Drive Ingestion — scan all mounted drives (C/D/F/G/H/I) and catalog files |
| **1** | `phase1_inventory` | Recursive Inventory — deep-crawl all scan roots, build file index |
| **2** | `phase2_dedup` | Hash-Cluster Dedup — SHA-256 dedup, elect canonical copies, compute space savings |
| **3** | `phase3_classify` | 3-Pass Classification — assign MEEK lanes, categories, content scores via LocalAI |
| **4a** | `phase4a_pdf_extract` | PDF Extraction — OCR + text extraction from all PDF files |
| **4b** | `phase4b_docx_extract` | DOCX Extraction — structured text extraction from Word documents |
| **4c** | `phase4c_structured_extract` | Structured Data — parse CSV, JSON, JSONL, and tabular files |
| **4d** | `phase4d_atomize` | Atom Generation — break documents into citation/fact/violation atoms |
| **4e** | `phase4e_archive_extract` | Archive Extraction — crack ZIP/RAR/7z archives, catalog inner files |
| **5** | `phase5_brain_feed` | LEXOS Brain Feed — feed atoms to 50 micro-brains across 8 categories |
| **6** | `phase6_gap_analysis` | EGCP Gap Analysis — score evidence coverage per legal action (Evidence-Gap-Claim-Proof) |
| **7a** | `phase7a_graph_delta` | Graph Delta — compute changes to knowledge graph since last cycle |
| **7b** | `phase7b_synthesis_merge` | Synthesis Merge — merge all evidence, citations, and violations into master indexes |
| **7c** | `phase7c_knowledge_merge` | Knowledge Merge — consolidate knowledge shards into unified JSONL |
| **8** | `phase8_litigation_refresh` | Litigation Refresh — update litigation_context.db with latest pipeline data |
| **9** | `phase9_mcp_ingest` | MCP Ingest — push data to MCP server for tool access |
| **10** | `phase10_judicial_analysis` | Judicial Analysis — profile judges, detect bias patterns, map canon violations |
| **11** | `phase11_legal_action_discovery` | Legal Action Discovery — discover new legal actions from evidence patterns |
| **12** | `phase12_rule_audit` | MCR/MCL Rule Audit — validate compliance with Michigan Court Rules and statutes |
| **13** | `phase13_refinement` | Document Refinement — polish extracted content, resolve placeholders |
| **14** | `phase14_finalize` | Filing Finalization — assemble court-ready filing packages |
| **15** | `phase15_validation` | Court-Ready Validation — final lint, signature check, service verification |
| **16** | `phase16_desktop` | Desktop Offload — export outputs to desktop app and GUI |

---

## Agent Fleet Reference

The DELTA9 fleet has **56 agents** organized into 7 tiers across two parallel execution lanes plus convergence.

### Lane 1 — Infrastructure (I/O Bound)

| Tier | Agents | Description |
|------|--------|-------------|
| **Tier 1** (Index) | A01–A04 | Index scouts — one per drive group (C, D, F, G/I) |
| **Tier 2** (Dedup) | A05–A08 | Legal dedup, data dedup, code dedup, archive cracker |
| **Tier 3** (Extract) | A09–A12 | Flatten commander, PDF harvester, text miner, struct parser |

### Lane 2 — Intelligence (CPU/AI Bound)

| Tier | Agents | Description |
|------|--------|-------------|
| **Tier J** (Judicial) | J01–J08 | McNeill profiler, Hoopes profiler, benchbook auditor, canon mapper, JTC compiler, disqualification engine, ex parte detector, transcript impeacher |
| **Tier K** (Case Intel) | K01–K11 | Lane A–F case intel, person profiler, timeline builder, authority harvester, contradiction detector |
| **Tier L** (Legal Warfare) | L01–L11 | Lane A–F scorers, gap detector, citation validator, damages calculator, filing readiness, red team scanner |

### Convergence

| Tier | Agents | Description |
|------|--------|-------------|
| **Convergence** | F01–F06 | Filing factory, brain feeder, graph builder, MSC architect, test runner, convergence certifier |

### Execution Order

```
Tier 1 (Index)
    ↓
Tier 2 (Dedup) ═══╦═══ Tier J (Judicial)     ← parallel
    ↓              ║
Tier 3 (Extract) ═╩═══ Tier K (Case Intel)   ← parallel
    ↓
Tier L (Legal Warfare)                         ← needs both lanes
    ↓
Convergence (F01–F06)                          ← final assembly
```

---

## Common Operations

### List All Phases

```powershell
python run_omega_pipeline.py --list-phases
```

### Check Pipeline Status

```powershell
python run_omega_pipeline.py --status
# Or for quick status:
python quick_status.py
```

### Dry Run (No Side Effects)

```powershell
python run_omega_pipeline.py --dry-run
python run_omega_pipeline.py --dry-run --create-snapshot
```

### Run Phase Range

```powershell
# Extraction phases only
python run_omega_pipeline.py --start-phase 4a --end-phase 4e

# Intelligence phases
python run_omega_pipeline.py --start-phase 10 --end-phase 12

# Everything from classification onward
python run_omega_pipeline.py --start-phase 3
```

### Skip Specific Phases

```powershell
# Skip desktop offload
python run_omega_pipeline.py --skip-phases 16

# Skip archive extraction and MCP ingest
python run_omega_pipeline.py --skip-phases 4e,9
```

### Resume After Interruption

The pipeline checkpoints each phase. Re-run the same command — completed phases are skipped automatically via checkpoint files in `cyclepacks/CYCLE_<ts>/checkpoints/`.

```powershell
# Just re-run — checkpoints handle resume
python run_omega_pipeline.py --cycle-ts 20260115_143000
```

### Agent Fleet Operations

```powershell
# Full 56-agent fleet
python -m agents.agent_orchestrator

# Dry run (list agents without executing)
python -m agents.agent_orchestrator --dry-run

# Single tier
python -m agents.agent_orchestrator --tier tier1
python -m agents.agent_orchestrator --tier tierJ
python -m agents.agent_orchestrator --tier convergence

# Single agent
python -m agents.agent_orchestrator --agent J01
python -m agents.agent_orchestrator --agent A05

# Create master_index.db schema only
python -m agents.agent_orchestrator --create-db
```

### Validation

```powershell
# Full validation against snapshot
python validate.py

# Syntax check all pipeline modules
cd ../scripts && python syntax_check.py

# Integration test phases 1-3
python integration_test_phase123.py
```

---

## Configuration Reference

Key settings in `config.py`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `LITIGOS_ROOT` | `C:\Users\andre\LitigationOS` | Repository root |
| `AI_PROVIDER` | `"local"` (hardcoded) | Local-only AI — no network calls |
| `_KNOWN_DRIVE_LETTERS` | `C, D, F, G, H, I` | Drives scanned by pipeline |
| `SKIP_DIRS` | `__pycache__`, `.git`, `node_modules`, etc. | Directories excluded from scan |
| `SKIP_EXTENSIONS` | `.pyc`, `.dll`, `.exe`, `.whl`, etc. | File types excluded from indexing |
| `LEGAL_EXTENSIONS` | `.pdf`, `.docx`, `.txt`, `.md`, `.json`, etc. | File types treated as legal documents |

### MEEK Lane Signals

| Signal | Lane | Pattern Match |
|--------|------|--------------|
| MEEK1 | B (Housing) | Shady Oaks, Homes of America, landlord, tenant, MCL 554 |
| MEEK2 | A (Custody) | Custody, parenting, FOC, child, MCL 722, best interest |
| MEEK3 | D (PPO) | PPO, protection order, contempt, MCL 600.2950 |
| MEEK4 | E (Misconduct) | Bias, JTC, disqualification, MCR 2.003, canon |
| MEEK5 | F (Appellate) | COA, MSC, MCR 7.*, leave to appeal, standard of review |

Detection priority: **E → D → F → C → A → B**

---

## Troubleshooting

### "No snapshot found"

```
[OMEGA] No snapshot found. Use --create-snapshot or run safety.py first.
```

**Fix:** Add `--create-snapshot` flag or run a previous snapshot cycle first. Dry runs skip snapshot verification.

### Phase Import Timeout

```
[OMEGA] Phase X import timed out or failed — SKIPPING
```

**Fix:** The failsafe wrapper gives each import 30s. Check for circular imports or missing dependencies in the phase module. Run `python -c "import phaseX_module"` directly to see the error.

### Phase Execution Timeout

```
[OMEGA] Phase X TIMED OUT after 600s
```

**Fix:** Each phase has a 10-minute max. For large datasets, run the phase directly (`python phase4a_pdf_extract.py`) without the timeout wrapper.

### SQLITE_BUSY / Database Locked

**Fix:** Only one pipeline instance can run at a time. Check for stale Python processes:

```powershell
Get-Process python* | Select-Object Id, ProcessName, StartTime
```

Kill orphans, then retry. All DB connections use `PRAGMA busy_timeout=60000` and WAL mode.

### Agent CRASH Status

```
✗ [tierJ] J03: CRASH: <error>
```

**Fix:** Individual agent crashes don't stop the fleet. Check `agents/checkpoints/fleet_report.json` for details. Re-run the single agent: `python -m agents.agent_orchestrator --agent J03`.

### Ctrl+C / Interrupted Run

The pipeline handles `SIGINT` gracefully — it finishes the current phase, writes a `CLEANUP_NEEDED.marker`, and exits. Resume by re-running with the same `--cycle-ts`.

### Drive Not Mounted

If a drive referenced in config is missing, Phase 0.5 (Drive Ingestion) and Tier 1 scouts will skip it. Files on unmounted drives become orphaned references in the DB until the drive is reconnected.

---

## File Locations

| Item | Path |
|------|------|
| Pipeline root | `00_SYSTEM/pipeline/` |
| Phase modules | `00_SYSTEM/pipeline/phase*.py` |
| Agent fleet | `00_SYSTEM/pipeline/agents/` |
| Agent DB | `00_SYSTEM/pipeline/agents/master_index.db` |
| Central DB | `litigation_context.db` (repo root) |
| Cycle outputs | `00_SYSTEM/cyclepacks/CYCLE_<timestamp>/` |
| Checkpoints | `00_SYSTEM/cyclepacks/CYCLE_<ts>/checkpoints/` |
| Backups/Snapshots | `00_SYSTEM/backups/SNAPSHOT_<ts>/` |
| Config | `00_SYSTEM/pipeline/config.py` |
| Failsafe wrapper | `00_SYSTEM/pipeline/failsafe.py` |
| Fleet report | `00_SYSTEM/pipeline/agents/checkpoints/fleet_report.json` |
