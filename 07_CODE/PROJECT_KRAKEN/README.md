# PROJECT KRAKEN — Autonomous Evidence Hunting & Intelligence System

> **Codename:** KRACK-A-LACK (KAL)  
> **Version:** 2.0  
> **Created:** 2026-04-05  
> **Status:** Production — actively hunting across 241,000+ files on 6 drives  
> **Purpose:** Autonomous, self-evolving evidence discovery and legal intelligence harvesting

---

## Overview

PROJECT KRAKEN is an autonomous evidence hunting system that discovers, reads, analyzes, and persists legally relevant evidence from a multi-drive file corpus. Unlike traditional e-discovery tools that rely on filename keywords or metadata, KRAKEN uses a **content-first lottery method** — it randomly samples files, actually reads their content, and scores them against configurable detection patterns.

The system is self-evolving: it learns which file types, drives, and directories yield the highest-value evidence, and weights future sampling accordingly.

---

## Architecture

### Core Pipeline

```
File Discovery (fd Rust + DB file_inventory)
    → Random Lottery Sampling (weighted by historical yield)
    → Content Extraction (PDF/DOCX/TXT/CSV/HTML/JSON/MD)
    → Pattern Analysis (22 adversary + 6 legal authority + 8 evidence patterns)
    → Scoring (HIGH / MEDIUM / LOW)
    → Auto-Persistence (SQLite evidence_quotes table)
    → Auto-Dossier Expansion (markdown adversary profile files)
    → Evolution Metrics (learn yield rates per extension, per drive)
    → Condensation Pipeline (extract judicial + narrative intelligence)
    → MBP Bridge (feed structured graph data to THEMANBEARPIG visualization)
```

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    KRAKEN ORCHESTRATOR                    │
│                      (kraken.py)                         │
├─────────────┬──────────────┬──────────────┬─────────────┤
│  Discovery  │  Extraction  │   Analysis   │ Persistence │
│  fd (Rust)  │  pypdfium2   │  22 patterns │  SQLite DB  │
│  DB inv.    │  text parse  │  6 auth types│  dossier.md │
│  weighted   │  7 formats   │  8 evidence  │  graph JSON │
│  sampling   │              │  categories  │             │
├─────────────┴──────────────┴──────────────┴─────────────┤
│                  EVOLUTION ENGINE                         │
│  Track yield rates → Update weights → Improve sampling   │
├─────────────────────────────────────────────────────────┤
│               CONDENSATION PIPELINE                      │
│  8 judicial patterns + 6 narrative patterns → intel DB   │
├─────────────────────────────────────────────────────────┤
│                 MBP BRIDGE                               │
│  Intelligence → Graph nodes/links → THEMANBEARPIG viz    │
├─────────────────────────────────────────────────────────┤
│              CONTINUOUS DAEMON                            │
│  Autonomous rounds → sleep → repeat → shutdown hooks     │
└─────────────────────────────────────────────────────────┘
```

---

## Key Innovation: Content-First Lottery Method

### Problem
Traditional e-discovery tools filter by filename patterns (e.g., `*custody*.pdf`). This misses:
- Evidence in generically-named files (`scan001.pdf`, `document.txt`)
- Cross-domain evidence (a housing document containing custody admissions)
- Evidence in unexpected formats (CSV exports, JSON chat logs, HTML pages)

### Solution
KRAKEN's lottery method:

1. **Discover ALL files** using `fd` (Rust, 5-50x faster than `os.walk`) for fast drives + SQLite `file_inventory` table for slow USB/SD drives
2. **Randomly sample N files** per round (default 10, max 50)
3. **Actually READ the file content** — PDF text extraction, text parsing, etc.
4. **Score against 22+ adversary patterns, 6 legal authority types, 8 evidence categories**
5. **Persist HIGH findings** to database + expand adversary dossier files
6. **Learn from results** — evolution engine tracks which extensions/drives/directories yield best results

### Why Random Sampling Works
- With 241,000+ files, exhaustive reading is impractical
- Random sampling with content analysis finds evidence that keyword-based search misses
- The evolution engine converges on high-yield file types within ~20 rounds
- Each round takes 30-120 seconds depending on file sizes and formats

---

## Self-Evolution Engine

After each round, KRAKEN records yield metrics and updates sampling weights:

```python
# Yield tracking per extension
evolution_data = {
    ".pdf":  {"sampled": 45, "high": 12, "yield_rate": 0.267},
    ".txt":  {"sampled": 30, "high":  5, "yield_rate": 0.167},
    ".html": {"sampled": 20, "high":  0, "yield_rate": 0.000},
    ".docx": {"sampled": 15, "high":  3, "yield_rate": 0.200},
}

# Weight calculation with confidence scaling
# Full weight at 20+ samples, proportional below
confidence = min(1.0, samples / 20)
weight = base_weight + (yield_rate * confidence * boost_factor)
```

### What It Learns
- **File extensions**: PDFs yield ~27% HIGH vs HTML at 0% → sample more PDFs
- **Drive letters**: I:\ (organized evidence) yields 35% vs J:\ (reference) at 5%
- **Adversary co-occurrence**: Which adversaries appear together in documents
- **Directory hotspots**: Subdirectories with concentrated evidence

### Database Tables

| Table | Purpose |
|-------|---------|
| `kraken_processed` | Every file ever analyzed (path, score, round_id, timestamp) |
| `kraken_rounds` | Round metadata (id, file_count, high_count, medium_count, focus) |
| `kraken_evolution` | Per-round yield metrics by extension and drive |
| `kraken_weights` | Current learned sampling weights |
| `kraken_cooccurrence` | Adversary co-occurrence network |

---

## Condensation Pipeline

Extracts structured intelligence from HIGH/MEDIUM findings:

### Judicial Intelligence (8 patterns)

| Pattern | Detects |
|---------|---------|
| `ex_parte` | Orders without notice, ex parte communications |
| `bias` | Systematic favoritism, unequal treatment |
| `due_process` | Denial of procedural rights |
| `contempt_abuse` | Punitive contempt, disproportionate sanctions |
| `evidence_exclusion` | Improper exclusion of admissible evidence |
| `recusal_refusal` | Failure to disqualify despite conflicts |
| `cartel_connection` | Connections between judicial officers |
| `rights_denial` | Denial of constitutional rights |

### Narrative Intelligence (6 patterns)

| Pattern | Extracts |
|---------|----------|
| `dated_events` | Events with specific dates for timeline construction |
| `court_actions` | Motions, orders, hearings, rulings |
| `witness_statements` | Testimony and witness accounts |
| `false_allegations` | Pattern of debunked allegations |
| `harm_indicators` | Documented harms (financial, emotional, physical) |
| `separation_events` | Parent-child separation incidents |

---

## THEMANBEARPIG Bridge

Converts condensed intelligence into graph visualization data:

```
Judicial Violations  → JUDICIAL_CARTEL layer nodes
Timeline Events      → TIMELINE layer nodes
False Allegations    → WEAPON_CHAINS layer nodes
Documented Harms     → DAMAGES layer nodes
Witness Statements   → IMPEACHMENT layer nodes
```

### Idempotent Merge Protocol
- Removes all existing `krk_` prefixed nodes before adding new ones
- Ensures clean updates without duplicate data
- Preserves non-KRAKEN nodes from other data sources

---

## Components

| File | Lines | Size | Purpose |
|------|-------|------|---------|
| `kraken.py` | ~1,350 | 64 KB | Main orchestrator — rounds, evolution, condensation, MBP bridge, daemon |
| `lottery_harvest.py` | ~400 | 15 KB | Prototype v1 — os.walk-based lottery (kept for reference) |
| `lottery_v2.py` | ~350 | 13 KB | Apex v2 — fd (Rust) + DB inventory hybrid discovery |
| `shell_watchdog.py` | ~500 | 20 KB | Process management daemon — monitors and kills stale processes |
| `mbp/build_manbearpig_v7.py` | ~1,324 | 53 KB | Graph data extraction from litigation_context.db for THEMANBEARPIG |
| `mbp/mbp_intel.py` | ~800 | 29 KB | 18-command intelligence query tool for MBP graph data |
| `mbp/mbp_build.py` | ~180 | 7 KB | Unified MBP build pipeline (stats/data/html/exe/open/launch) |
| `mbp/adversary_blueprint.py` | ~984 | 48 KB | THEMANBEARPIG v8.0 launcher with embedded LitigationAPI |
| `spec/THEMANBEARPIG.spec` | ~30 | 1 KB | PyInstaller build spec for standalone .exe |
| `extension/extension.mjs` | ~360 | 20 KB | Copilot CLI extension — 7 tools including KAL command |
| `agents/kraken-hunter.agent.md` | ~80 | 3 KB | Copilot agent definition for KRAKEN hunting workflows |

**Total: ~6,350 lines of production code, 273 KB**

---

## Directory Structure

```
07_CODE/PROJECT_KRAKEN/
├── README.md                           ← This file (architecture & monetization docs)
├── kraken.py                           ← Main KRAKEN orchestrator (v2.0)
├── lottery_harvest.py                  ← Lottery method v1 prototype
├── lottery_v2.py                       ← Lottery method v2 (fd + DB hybrid)
├── shell_watchdog.py                   ← Process management daemon
├── mbp/
│   ├── build_manbearpig_v7.py          ← MBP graph data builder
│   ├── mbp_intel.py                    ← 18-command MBP intelligence CLI
│   ├── mbp_build.py                    ← Unified MBP build pipeline
│   └── adversary_blueprint.py          ← THEMANBEARPIG v8.0 + LitigationAPI
├── extension/
│   └── extension.mjs                   ← Copilot CLI extension (7 tools)
├── agents/
│   └── kraken-hunter.agent.md          ← Copilot agent definition
├── spec/
│   └── THEMANBEARPIG.spec              ← PyInstaller build specification
└── results/
    └── .gitkeep                        ← Example output directory
```

---

## Usage

### Run Evidence Hunting Rounds

```bash
# Basic: 3 rounds, 10 files per round
python -I kraken.py --rounds 3 --count 10

# Focused: 5 rounds targeting judicial misconduct
python -I kraken.py --rounds 5 --count 15 --focus judicial

# Heavy: 10 rounds, 25 files, custody focus
python -I kraken.py --rounds 10 --count 25 --focus custody

# Specific drives only
python -I kraken.py --rounds 3 --count 10 --drives C,I,D
```

### Focus Modes

| Focus | Boosts Scoring For |
|-------|-------------------|
| `all` | Equal weight across all patterns (default) |
| `adversary` | Adversary detection patterns |
| `judicial` | Judicial misconduct patterns |
| `housing` | Housing/property evidence |
| `custody` | Custody/parenting time evidence |
| `ppo` | Protection order evidence |
| `legal` | Legal authority citations |

### View Status & Metrics

```bash
# Current system status
python -I kraken.py --status

# Evolution metrics (yield rates, weights)
python -I kraken.py --evolve

# Run condensation pipeline
python -I kraken.py --condense

# Export to THEMANBEARPIG graph
python -I kraken.py --mbp-export
```

### Continuous Daemon Mode

```bash
# Run continuously: 5-minute intervals, max 100 cycles
python -I kraken.py --continuous --interval 300 --max-cycles 100

# Run with focus and custom parameters
python -I kraken.py --continuous --interval 600 --rounds 3 --count 20 --focus judicial
```

### THEMANBEARPIG Visualization

```bash
# Build graph data from litigation_context.db
python -I mbp/mbp_build.py data

# Build HTML visualization
python -I mbp/mbp_build.py html

# Build standalone .exe
python -I mbp/mbp_build.py exe

# Launch visualization
python -I mbp/mbp_build.py launch

# Full pipeline: stats → data → html → exe → open
python -I mbp/mbp_build.py all
```

### MBP Intelligence Queries

```bash
# Available commands (18 total)
python -I mbp/mbp_intel.py --help

# Examples
python -I mbp/mbp_intel.py stats          # Graph statistics
python -I mbp/mbp_intel.py adversary      # Adversary network analysis
python -I mbp/mbp_intel.py judicial       # Judicial cartel intelligence
python -I mbp/mbp_intel.py weapons        # Weapon chain analysis
python -I mbp/mbp_intel.py timeline       # Timeline events
python -I mbp/mbp_intel.py impeachment    # Impeachment ammunition
python -I mbp/mbp_intel.py readiness      # Filing readiness scores
python -I mbp/mbp_intel.py damages        # Damages calculations
python -I mbp/mbp_intel.py egcp           # EGCP scoring breakdown
python -I mbp/mbp_intel.py convergence    # System convergence status
```

### Copilot CLI Integration

The extension at `extension/extension.mjs` provides 7 tools:

| Tool | Function |
|------|----------|
| `krack_a_lack` | Run KAL hunting rounds with configurable focus/drives/count |
| `lottery_harvest` | Single-round lottery harvest |
| `adversary_scan` | Deep adversary intelligence scan |
| `intel_dashboard` | Quick intelligence dashboard |
| `file_universe` | File counts by extension and drive |
| `separation_counter` | Father-son separation day counter |
| `dossier_status` | List all adversary dossier files |

---

## Dependencies

### Required

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.12+ | Runtime |
| pypdfium2 | 4.30+ | PDF text extraction (5x faster than PyMuPDF) |
| sqlite3 | built-in | Database storage |

### Required CLI Tools

| Tool | Version | Purpose |
|------|---------|---------|
| fd | 10.4+ | Rust file finder (5-50x faster than os.walk) |

### Optional (for THEMANBEARPIG)

| Package | Version | Purpose |
|---------|---------|---------|
| pywebview | 5.0+ | Desktop window for graph visualization |
| PyInstaller | 6.0+ | Build standalone .exe |

---

## Database Schema

### Core KRAKEN Tables

```sql
-- Every file ever analyzed
CREATE TABLE IF NOT EXISTS kraken_processed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE,
    file_ext TEXT,
    drive_letter TEXT,
    score TEXT,           -- HIGH, MEDIUM, LOW
    round_id TEXT,
    focus TEXT,
    adversaries_found TEXT,  -- JSON array
    authorities_found TEXT,  -- JSON array
    categories_found TEXT,   -- JSON array
    processed_at TEXT DEFAULT (datetime('now'))
);

-- Round metadata
CREATE TABLE IF NOT EXISTS kraken_rounds (
    round_id TEXT PRIMARY KEY,
    round_number INTEGER,
    file_count INTEGER,
    high_count INTEGER,
    medium_count INTEGER,
    low_count INTEGER,
    focus TEXT,
    drives TEXT,
    duration_seconds REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Per-round yield metrics
CREATE TABLE IF NOT EXISTS kraken_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id TEXT,
    extension TEXT,
    drive_letter TEXT,
    sampled INTEGER,
    high_count INTEGER,
    medium_count INTEGER,
    yield_rate REAL,
    recorded_at TEXT DEFAULT (datetime('now'))
);

-- Learned sampling weights
CREATE TABLE IF NOT EXISTS kraken_weights (
    key TEXT PRIMARY KEY,    -- 'ext:.pdf' or 'drive:I'
    weight REAL,
    samples INTEGER,
    highs INTEGER,
    yield_rate REAL,
    confidence REAL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Adversary co-occurrence network
CREATE TABLE IF NOT EXISTS kraken_cooccurrence (
    adversary_a TEXT,
    adversary_b TEXT,
    count INTEGER DEFAULT 1,
    last_seen TEXT,
    PRIMARY KEY (adversary_a, adversary_b)
);
```

### Evidence Output Table

HIGH-scoring findings are auto-persisted to the main `evidence_quotes` table:

```sql
INSERT INTO evidence_quotes (
    quote_text, source_file, page_number, category,
    lane, confidence, extracted_by, extracted_at
) VALUES (?, ?, ?, ?, ?, ?, 'KRAKEN', datetime('now'));
```

---

## Detection Patterns (Configurable)

### 22 Adversary Detection Patterns

Patterns are compiled regex applied against file content. Each adversary has:
- Name (e.g., "Emily Watson", "Judge McNeill")
- Aliases (e.g., ["Emily A. Watson", "Emily Pigors", "Watson"])
- Role (e.g., "opposing_party", "judge", "witness")
- Keywords (e.g., ["custody", "PPO", "contempt"])

### 6 Legal Authority Types

| Type | Pattern Examples |
|------|-----------------|
| MCR | `MCR \d+\.\d+` — Michigan Court Rules |
| MCL | `MCL \d+\.\d+` — Michigan Compiled Laws |
| MRE | `MRE \d+` — Michigan Rules of Evidence |
| USC | `\d+ USC` — United States Code |
| FRCP | `FRCP \d+` — Federal Rules of Civil Procedure |
| Case Law | `v\.` pattern + reporter citations |

### 8 Evidence Categories

| Category | Detects |
|----------|---------|
| Financial | Income, expenses, assets, debts, support |
| Medical | Health records, evaluations, diagnoses |
| Communication | Emails, texts, messages, recordings |
| Legal | Court filings, orders, judgments |
| Police | Police reports, incident numbers, officers |
| Custody | Parenting time, visitation, child welfare |
| Housing | Property, eviction, habitability, title |
| Employment | Jobs, income loss, workplace |

---

## Monetization Architecture

This system is designed as a **generic legal intelligence platform** suitable for commercialization.

### What Makes It Valuable

1. **Content-first discovery** — No existing e-discovery tool uses lottery sampling with actual content reading
2. **Self-evolving intelligence** — The system gets smarter over time without manual tuning
3. **Multi-format support** — Handles PDF, DOCX, TXT, CSV, HTML, JSON, MD out of the box
4. **Graph visualization** — THEMANBEARPIG turns raw data into interactive adversary network graphs
5. **Copilot integration** — Natural language evidence hunting via CLI extension

### Generalization Path

To convert from a single-case tool to a multi-tenant platform:

#### 1. Configurable Detection Profiles
```python
# Replace hardcoded ADVERSARIES dict with:
class DetectionProfile:
    adversaries: list[AdversaryConfig]     # Per-case adversary definitions
    legal_patterns: list[LegalPattern]     # Per-jurisdiction authority patterns
    evidence_categories: list[Category]    # Per-domain evidence taxonomies
    focus_modes: dict[str, list[str]]      # Custom focus mode definitions
```

#### 2. Multi-Tenant Database
```python
# Replace single litigation_context.db with:
class TenantDB:
    def get_db(self, tenant_id: str) -> sqlite3.Connection:
        return sqlite3.connect(f"data/{tenant_id}/evidence.db")
```

#### 3. Web Dashboard (replacing desktop exe)
```python
# Replace pywebview with:
# - FastAPI backend serving graph data as JSON API
# - React/D3.js frontend for THEMANBEARPIG visualization
# - WebSocket for live round progress updates
```

#### 4. Package Distribution
```toml
# pyproject.toml
[project]
name = "kraken-legal-intelligence"
version = "1.0.0"

[project.scripts]
kraken = "kraken.cli:main"
kraken-mbp = "kraken.mbp.cli:main"
```

### Revenue Model Options

| Model | Target | Price Point |
|-------|--------|-------------|
| SaaS (per-case) | Solo practitioners, pro se litigants | $49-199/month |
| SaaS (firm) | Small law firms (1-10 attorneys) | $499-999/month |
| Enterprise | Large firms, legal departments | $2,500-10,000/month |
| On-premise | Government, high-security clients | $25,000-100,000/year |
| API | Legal tech integrations | Usage-based pricing |

### Competitive Advantages

1. **No cloud dependency** — runs entirely local, critical for attorney-client privilege
2. **Self-evolving** — no manual rule tuning needed
3. **Content-first** — finds evidence that keyword search misses
4. **Open architecture** — SQLite + Python + Rust CLI = portable and extensible
5. **Graph visualization** — makes complex adversary networks comprehensible
6. **AI-agent integration** — Copilot CLI extension pattern is reusable

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-04-05 | Initial lottery method — 3 rounds, 30 files, 16 DB inserts |
| v2.0 | 2026-04-05 | Added Evolution Engine, Condensation Pipeline, MBP Bridge, Continuous Daemon |

---

## File Origins

All files in this directory were preserved from `D:\LitigationOS_tmp\` (the active development directory) for reproduction and monetization purposes. Source files on D:\ remain untouched.

| Destination | Source |
|-------------|--------|
| `kraken.py` | `D:\LitigationOS_tmp\kraken.py` |
| `lottery_harvest.py` | `D:\LitigationOS_tmp\lottery_harvest.py` |
| `lottery_v2.py` | `D:\LitigationOS_tmp\lottery_v2.py` |
| `shell_watchdog.py` | `D:\LitigationOS_tmp\shell_watchdog.py` |
| `mbp/build_manbearpig_v7.py` | `D:\LitigationOS_tmp\build_manbearpig_v7.py` |
| `mbp/mbp_intel.py` | `D:\LitigationOS_tmp\mbp_intel.py` |
| `mbp/mbp_build.py` | `D:\LitigationOS_tmp\mbp_build.py` |
| `mbp/adversary_blueprint.py` | `D:\LitigationOS_tmp\blueprint_build\adversary_blueprint.py` |
| `spec/THEMANBEARPIG.spec` | `D:\LitigationOS_tmp\blueprint_build\THEMANBEARPIG.spec` |
| `extension/extension.mjs` | `.github/extensions/litigation-arsenal/extension.mjs` |
| `agents/kraken-hunter.agent.md` | `.github/agents/kraken-hunter.agent.md` |

---

## License

Proprietary. All rights reserved. This system and its components are the intellectual property of Andrew James Pigors. Unauthorized reproduction, distribution, or use is prohibited.
