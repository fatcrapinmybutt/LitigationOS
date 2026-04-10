# Filing Engine — Autonomous Court Document Preparation

> `00_SYSTEM/engines/filing_engine/` · LitigationOS Engine · v1.1.0

## Overview

The Filing Engine automates court document preparation through a 6-phase pipeline:

```
TRIGGER → SCAN → VALIDATE → FORMAT → ASSEMBLE → QA → OUTPUT
```

It activates automatically when conditions are met (deadline proximity, EGCP readiness threshold, manual trigger) and produces court-ready filing packages with MCR/FRCP compliance validation.

## Architecture

| Module | Purpose |
|--------|---------|
| `engine.py` | Main `FilingEngine` class — primary API |
| `pipeline.py` | 6-phase orchestrator with template integration |
| `state.py` | Persistent SQLite state machine (crash-resilient) |
| `triggers.py` | Auto-activation scanner (deadline, readiness, orders) |
| `validator.py` | 12 MCR/FRCP compliance checks across 5 court types |
| `__main__.py` | CLI entry point |

## Template Integration

Pipeline Phase 4 (ASSEMBLE) calls modules from `00_SYSTEM/templates/filing_framework/`:

- **caption_generator** — 5 court types (circuit, COA, MSC, WDMI, district)
- **cos_generator** — Certificate of Service (4 service methods)
- **signature_block** — Pro se and attorney signature blocks
- **exhibit_indexer** — Exhibit index with Bates number ranges
- **michigan_format_specs** — Court-specific formatting (WDMI = 14pt per LCivR 10.6)
- **filing_checklist** — Pre-filing QA (7 types × 5 courts)
- **deadline_calculator** — MCR 1.108 day-counting with MI holidays

## Court Types Supported

| Key | Court | Font | Page Limit |
|-----|-------|------|------------|
| `mi_circuit` | Michigan Circuit Court | 12pt TNR | 20 pages |
| `mi_coa` | Michigan Court of Appeals | 12pt TNR | 50 pages |
| `mi_msc` | Michigan Supreme Court | 12pt TNR | 50 pages |
| `wdmi_federal` | USDC Western District MI | **14pt proportional** | Per local rule |
| `mi_district` | Michigan District Court | 12pt TNR | 10 pages |

## Usage

### Python API

```python
from filing_engine import FilingEngine

engine = FilingEngine()

# Scan for what needs attention
triggers = engine.scan_triggers()

# Dry run (validate only)
result = engine.run("F1", case_number="2024-001507-DC", dry_run=True,
                    document_text="MOTION FOR ...", components={"has_cos": True})

# Full run with assembly
result = engine.run("F1",
    case_number="2024-001507-DC",
    court_type="mi_circuit",
    dry_run=False,
    document_text="MOTION FOR ...",
    case_info={"case_number": "2024-001507-DC", "court": "14th Circuit",
               "plaintiff": "Andrew J. Pigors", "defendant": "Emily A. Watson",
               "document_title": "Emergency Motion"},
    parties_served=[{"name": "Emily A. Watson", "address": "2160 Garland Dr"}],
    signer_info={"name": "Andrew J. Pigors", "pro_se": True},
    output_dir="05_FILINGS/F1/")
```

### CLI

```bash
python -m filing_engine --filing F1 --dry-run
python -m filing_engine --scan-triggers
python -m filing_engine --status
```

## Dependencies

- **shared module** (`00_SYSTEM/shared/`) — DB access, path resolution
- **filing_framework** (`00_SYSTEM/templates/filing_framework/`) — Document templates
- Python 3.10+ (stdlib only — no external packages required)

## State Persistence

Engine state is stored in `filing_engine.db` (auto-created) with 4 tables:
- `filing_runs` — Run history with status tracking
- `phase_log` — Per-phase timing and results
- `component_inventory` — Components generated per run
- `qa_findings` — Validation findings per run
