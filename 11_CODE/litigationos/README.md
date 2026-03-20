# LitigationOS v1.0.0-beta.1

**AI-powered, offline-first litigation management for Michigan courts.**

LitigationOS is a local-first Python desktop application for managing litigation cases, filings, evidence, deadlines, and court rules. It runs entirely on your machine — zero cloud dependency, zero API keys. The integrated MANBEARPIG AI engine provides intelligent document classification, evidence scoring, and legal research without ever sending data off your computer.

---

## Installation (Beta)

```bash
# Install from source (editable mode)
pip install -e .

# Launch the GUI (double-click friendly)
litigationos-gui

# Alternative launch methods
python -m litigationos          # Module launch
litigationos --help             # CLI commands
```

### System Requirements

- **OS:** Windows 10/11 (primary target)
- **Python:** 3.12 or newer
- **Disk:** ~100 MB for the application, plus storage for case data
- **AI:** Built-in MANBEARPIG engine — no external downloads, no Ollama, no internet required

---

## System Statistics

| Metric | Count |
|--------|-------|
| **Core Engines** | 9 (Court Rules, Deadline, Filing, Evidence, Document, Settings, AI, RAG, + Phase 5-6 extensions) |
| **GUI Screens** | 15 (Dashboard, Deadline Dashboard, Cases, Filings, Filing Wizard, Evidence Browser, Evidence Map, Document Editor, Calendar View, Timeline, Settings, Filing Manager, AI Chat, + more) |
| **AI Engine** | MANBEARPIG v9.0 — TF-IDF + Naive Bayes + BM25 + semantic embeddings, 50 skills, 140+ JSON-RPC methods |
| **MCP Tools** | 45 Model Context Protocol tools for automation |
| **Test Suite** | 266 tests across 12 test files |
| **Database Tables** | 14+ core tables with FTS5 full-text search |
| **Pydantic Models** | 9 data models (Case, Party, Claim, Filing, Deadline, Evidence, Document, Template, Timeline) |

---

## Features

### Core Capabilities
- **Case Management** — Track cases, parties, claims, and timelines
- **Filing Builder** — Create court filings with compliance checking and pre-filing QA
- **Deadline Calculator** — Rule-based deadline tracking with holiday adjustment and ICS export
- **Evidence Manager** — Bates numbering, chain of custody, full-text search, gap detection
- **Document Generation** — Jinja2 templates → DOCX/PDF output with placeholder resolution
- **Court Rules** — Michigan Court Rules (MCR) built-in with FTS5 search
- **AI Chat** — Conversational legal research powered by MANBEARPIG (100% offline)
- **AI Intelligence** — Document classification, evidence scoring, lane detection, entity extraction

### Phase 5-6 Additions
- **Court Calendar Engine** — ICS export, month-grid view, urgency levels, countdown formatting
- **Brief Compliance Engine** — MCR 7.212 validation, word/page counts, citation checking
- **Pre-Filing QA Engine** — GO/NO-GO gate, signature detection, service validation
- **Evidence Chain Engine** — SHA-256 hashing, chain of custody, integrity verification
- **Backup and Versioning** — Snapshot creation, hash verification, manifest tracking, restore
- **Placeholder Resolver** — Auto-resolution from database, [ANDREW_REQUIRED] tagging
- **E-Filing Prep** — PDF/A compliance, packet assembly, TrueFiling format validation
- **Authority Index** — Citation search, cross-reference graph, authority verification

### GUI Screens
- **Dashboard** — Central overview with all-engine integration and emergency alerts
- **Deadline Dashboard** — Visual countdown timers with urgency-colored display
- **Case Manager** — CRUD for cases, parties, and claims
- **Filing Wizard** — Step-by-step guided filing workflow with GO/NO-GO gate
- **Evidence Map** — Visual graph of claims linked to evidence with gap highlighting
- **Document Editor** — In-app editor with compliance highlighting and placeholder resolution
- **Calendar View** — Month-grid calendar with deadline highlighting and ICS export
- **Timeline View** — Chronological event visualization with filtering
- **Evidence Browser** — FTS5 search and browse with Bates assignment
- **Filing Manager** — Filing list with build/validate/export workflow
- **AI Chat** — Interactive legal research assistant with citation-backed responses
- **Settings** — Configuration form with live theme switching

### Complaint Filing Support
- Michigan Department of Civil Rights (MDCR)
- Michigan Attorney General (AG)
- Judicial Tenure Commission (JTC)
- HIPAA / HHS Office for Civil Rights
- Michigan State Bar (Attorney Grievance Commission)
- Friend of the Court (FOC)

---

## AI Engine: MANBEARPIG v9.0

LitigationOS ships with a fully integrated, offline AI engine — no API keys, no cloud services, no external model downloads required.

| Capability | Method |
|-----------|--------|
| **Document Classification** | TF-IDF + Naive Bayes |
| **Evidence Scoring** | BM25 ranking + semantic embeddings |
| **Legal Research** | 50 specialized skills, FTS5 search |
| **Entity Extraction** | Pattern matching + NLP heuristics |
| **Lane Detection** | MEEK signal regex classification |
| **Summarization** | Extractive + keyword-based |

All inference runs locally. Your litigation data never leaves your machine.

---

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/litigationos.git
cd litigationos

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=litigationos --cov-report=term-missing

# Run Phase 5-6 tests only
pytest tests/test_court_calendar.py tests/test_brief_compliance.py tests/test_prefiling_qa.py tests/test_evidence_chain.py tests/test_backup_version.py tests/test_placeholder_resolver.py tests/test_efiling_prep.py tests/test_authority_index.py tests/test_complaint_stacks.py
```

### Test Suite Breakdown

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| test_engines.py | 66 | Core engine business logic |
| test_models.py | 30 | Pydantic model validation |
| test_db.py | 21 | Database and schema |
| test_brief_compliance.py | 20 | MCR 7.212 brief compliance |
| test_complaint_stacks.py | 19 | Complaint templates and agency compliance |
| test_placeholder_resolver.py | 19 | Placeholder resolution |
| test_authority_index.py | 18 | Court rule lookup and cross-referencing |
| test_efiling_prep.py | 16 | E-filing preparation |
| test_court_calendar.py | 15 | Calendar and ICS features |
| test_evidence_chain.py | 15 | Evidence chain of custody |
| test_prefiling_qa.py | 14 | Pre-filing QA gate |
| test_backup_version.py | 13 | Backup and versioning |

---

## Architecture

```
src/litigationos/
├── engines/        # 9 business logic engines
├── gui/            # 15 CustomTkinter screens (incl. AI Chat)
├── models/         # 9 Pydantic data models
├── db/             # SQLite with WAL + FTS5
├── cli/            # Typer CLI (5 commands)
├── plugins/        # Jurisdiction extensions (Michigan built-in)
└── utils/          # Shared utilities
```

- **GUI:** CustomTkinter desktop interface with sidebar navigation
- **Database:** SQLite with WAL mode, FTS5 full-text search, 14+ tables
- **Plugins:** Jurisdiction-extensible (ships with Michigan)
- **CLI:** Typer-based command-line interface
- **AI:** MANBEARPIG v9.0 — 100% local, zero network, zero API keys

---

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/README.md) | Complete user manual with feature walkthroughs |
| [Developer Guide](docs/DEVELOPER.md) | Architecture, engine patterns, testing, building |
| [Michigan Court Reference](docs/MICHIGAN.md) | Court rules, statutes, forms, e-filing, fees |
| [Complaint Filing Guide](docs/complaint_filing_guide.md) | Agency-specific complaint procedures |

---

## License

Proprietary — © Andrew James Pigors. All rights reserved.