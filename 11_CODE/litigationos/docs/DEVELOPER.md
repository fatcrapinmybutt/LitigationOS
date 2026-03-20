# LitigationOS Developer Guide

Technical reference for developers contributing to or extending LitigationOS.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Phase 5-6 Engine Architecture](#2-phase-5-6-engine-architecture)
3. [MCP Server v2 Documentation](#3-mcp-server-v2-documentation)
4. [GUI Screen Architecture](#4-gui-screen-architecture)
5. [Engine Integration Patterns](#5-engine-integration-patterns)
6. [Adding a Jurisdiction Plugin](#6-adding-a-jurisdiction-plugin)
7. [Adding a New Engine](#7-adding-a-new-engine)
8. [Database Schema](#8-database-schema)
9. [Testing](#9-testing)
10. [Building the Installer](#10-building-the-installer)

---

## 1. Architecture Overview

LitigationOS follows a layered architecture with 9 engines, 14 GUI screens, and a comprehensive test suite.

`
+-----------------------------------------------------+
|  GUI Layer (CustomTkinter) - 14 Screens              |
|  CLI Layer (Typer + Rich) - 5 Commands               |
+-----------------------------------------------------+
|  Engine Layer (Business Logic) - 9 Engines           |
|  +-------------+ +------------+ +-------------+     |
|  | CourtRules  | |  Deadline  | |   Filing    |     |
|  |   Engine    | |   Engine   | |   Engine    |     |
|  +-------------+ +------------+ +-------------+     |
|  +-------------+ +------------+ +-------------+     |
|  |  Evidence   | |  Document  | |  Settings   |     |
|  |   Engine    | |   Engine   | |   Engine    |     |
|  +-------------+ +------------+ +-------------+     |
|  +-------------+ +------------+                      |
|  |  AI Engine  | | RAG Engine |  (Optional)          |
|  +-------------+ +------------+                      |
|  Phase 5-6 Extensions:                               |
|  +-------------+ +------------+ +-------------+     |
|  |  Calendar   | | Compliance | |  Pre-Filing |     |
|  |   Engine    | |   Engine   | |  QA Engine  |     |
|  +-------------+ +------------+ +-------------+     |
|  +-------------+ +------------+ +-------------+     |
|  |  Evidence   | |   Backup   | | Placeholder |     |
|  |   Chain     | |  Version   | |  Resolver   |     |
|  +-------------+ +------------+ +-------------+     |
|  +-------------+ +------------+                      |
|  |  E-Filing   | | Authority  |                      |
|  |   Prep      | |   Index    |                      |
|  +-------------+ +------------+                      |
+-----------------------------------------------------+
|  Model Layer (Pydantic)                              |
|  Case, Party, Claim, Filing, Deadline,               |
|  Evidence, Document, Template, TimelineEvent         |
+-----------------------------------------------------+
|  Database Layer (SQLite + FTS5)                      |
|  DatabaseManager, Migrations, Seed Data              |
+-----------------------------------------------------+
|  Plugin Layer (Jurisdiction Extensions)              |
|  Michigan (ships built-in)                           |
+-----------------------------------------------------+
`

### Directory Structure

`
src/litigationos/
+-- __init__.py          # Version and app name
+-- app.py               # Application entry point and App container
+-- config.py            # Settings manager (DB-backed key-value)
+-- cli/                 # Typer CLI commands
|   +-- main.py          # 5 commands: version, init, cases, deadlines, gui
+-- db/                  # Database layer
|   +-- connection.py    # DatabaseManager (WAL, FKs, busy timeout)
|   +-- schema.sql       # Full DDL (tables, indexes, FTS5, triggers)
|   +-- migrations.py    # Schema migration runner
|   +-- seed.py          # Michigan seed data
+-- engines/             # Business logic (9 engines)
|   +-- court_rules.py   # MCR lookup, FTS5 search, validation
|   +-- deadline.py      # Date calculation with holiday adjustment
|   +-- document.py      # Jinja2 --> DOCX --> PDF generation
|   +-- evidence.py      # Cataloguing, Bates, authentication, chain
|   +-- filing.py        # Stack assembly and compliance scoring
|   +-- settings.py      # Configuration engine
|   +-- ai.py            # Ollama LLM integration
|   +-- rag.py           # ChromaDB semantic search
+-- gui/                 # CustomTkinter desktop UI (14 screens)
|   +-- app.py           # Main window, sidebar navigation, screen switching
|   +-- dashboard.py     # Central overview with all-engine integration
|   +-- deadline_dashboard.py  # Countdown timers, urgency levels
|   +-- case_manager.py  # CRUD for cases, parties, claims
|   +-- filing_manager.py     # Filing list, detail, build/validate/export
|   +-- filing_wizard.py      # Step-by-step guided filing workflow
|   +-- evidence_browser.py   # FTS5 search, filter, Bates, authentication
|   +-- evidence_map.py       # Visual claim-to-evidence graph
|   +-- document_editor.py    # In-app editor with compliance highlighting
|   +-- calendar_view.py      # Month-grid calendar with ICS export
|   +-- timeline_view.py      # Chronological event visualization
|   +-- settings_screen.py    # Settings form with live theme switching
|   +-- widgets/              # Shared widget components
+-- models/              # Pydantic data models
|   +-- case.py, party.py, claim.py, filing.py
|   +-- deadline.py, evidence.py, document.py
|   +-- template.py, timeline.py
+-- plugins/             # Jurisdiction plugins
|   +-- base.py          # Base plugin interface
|   +-- michigan/        # Michigan jurisdiction (built-in)
+-- utils/               # Shared utilities
`

### Key Design Decisions

- **SQLite with WAL mode** -- High concurrency, no server needed, file-portable
- **FTS5 full-text search** -- Fast evidence and court rule search without external dependencies
- **Pydantic models** -- Type-safe data validation at the model boundary
- **Engine pattern** -- Each domain area has a dedicated engine class that owns its business logic and DB queries
- **Local-first AI** -- All AI features use Ollama (local) to ensure case data never leaves the user's machine
- **Phase 5-6 convergence** -- New engines extend existing patterns; GUI screens compose multiple engines

---

## 2. Phase 5-6 Engine Architecture

Phase 5-6 introduced 8 new logical engine capabilities. These are implemented as extensions to the existing engine classes and as tested patterns in the test suite.

### 2.1 Court Calendar Engine

**Test file:** 	est_court_calendar.py (15 tests)

Extends the DeadlineEngine with calendar-specific features:

| Feature | Description |
|---------|-------------|
| **ICS Export** | Generates standard iCalendar (.ics) files from deadlines |
| **VEVENT Generation** | Each deadline becomes a VEVENT block with ISO dates |
| **Urgency Levels** | Critical / High / Medium priority assignment |
| **Countdown Formatting** | Days-remaining calculation with overdue detection |
| **Deadline Accuracy** | MCR-based computation (21-day answer, 56-day brief, etc.) |

### 2.2 Brief Compliance Engine

**Test file:** 	est_brief_compliance.py (20 tests)

Extends the CourtRulesEngine and FilingEngine with MCR 7.212 compliance:

| Feature | Description |
|---------|-------------|
| **Word/Page Count Validation** | Brief <= 50, Motion <= 20, Reply <= 10 pages |
| **Required Section Detection** | Double-spacing, brief attachment for motions (MCR 2.119) |
| **Citation Format Checking** | MCR rule format validation via FTS5 |
| **MCR 7.212 Validation** | Appellate brief timeline (56/35/21 days), format scoring |

### 2.3 Pre-Filing QA Engine

**Test file:** 	est_prefiling_qa.py (14 tests)

Implements the GO/NO-GO gate before filing submission:

| Feature | Description |
|---------|-------------|
| **GO/NO-GO Decision** | GO (score >= 80), CONDITIONAL (partial), NO-GO (missing critical items) |
| **Signature Detection** | Checks for Signature, Printed Name, Dated fields |
| **Service Address Validation** | MCR 2.107 compliance, party address verification |
| **Exhibit Reference Verification** | Bates number cross-referencing |

### 2.4 Evidence Chain Engine

**Test file:** 	est_evidence_chain.py (15 tests)

Extends the EvidenceEngine with chain-of-custody tracking:

| Feature | Description |
|---------|-------------|
| **SHA-256 Hashing** | Cryptographic hash at import for integrity verification |
| **Chain of Custody** | Import date, source, and hash tracking |
| **Gap Detection** | Identifies claims without supporting evidence |
| **Authentication Metadata** | MRE 901 declarations with perjury clause |
| **Bates Numbering** | Sequential assignment (PREFIX-000001), idempotent |

### 2.5 Backup and Versioning Engine

**Test file:** 	est_backup_version.py (13 tests)

Provides filing stack version control:

| Feature | Description |
|---------|-------------|
| **Snapshot Creation** | Export stacks to versioned directories with manifest.json |
| **Hash Verification** | SHA-256 consistency between versions |
| **Manifest Tracking** | Records exported files, checklist, completeness flag |
| **Restore Logic** | Full roundtrip export/import preserving all metadata |

### 2.6 Placeholder Resolver Engine

**Test file:** 	est_placeholder_resolver.py (19 tests)

Resolves template placeholders from database values:

| Feature | Description |
|---------|-------------|
| **Pattern Detection** | Jinja2 {{ placeholder }} and bracket [CASE_NUMBER] patterns |
| **DB Cross-Reference** | Resolves jurisdiction.state, county, court, case titles, party names |
| **Auto-Resolution** | Replaces placeholders with settings/case values automatically |
| **ANDREW_REQUIRED Tagging** | Unresolved placeholders marked as [ANDREW_REQUIRED: key] |

### 2.7 E-Filing Prep Engine

**Test file:** 	est_efiling_prep.py (16 tests)

Prepares court-ready filing packets:

| Feature | Description |
|---------|-------------|
| **PDF/A Compliance** | Validates margins, font, spacing per MCR format rules |
| **Packet Assembly** | Builds complete stacks (main doc, exhibits, proof of service, proposed order) |
| **Cover Sheet Generation** | Filing metadata (title, court, case number, status) |
| **TrueFiling Format** | Validates completeness for appellate e-filing (score >= 80) |

### 2.8 Authority Index Engine

**Test file:** 	est_authority_index.py (18 tests)

Manages court rule lookup and cross-referencing:

| Feature | Description |
|---------|-------------|
| **Citation Search** | FTS5 full-text search for rules by keyword |
| **Citation Graph** | Cross-references between related MCR rules |
| **Authority Verification** | Lookup and verify cited rules exist |
| **Format Validation** | Michigan-specific format checks (margins, spacing, verified statement) |

---

## 3. MCP Server v2 Documentation

The MCP (Model Context Protocol) server exposes 45 tools for AI-powered automation of LitigationOS operations.

### Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **Case Management** | 6 | Create, read, update, delete, list, search cases |
| **Filing Operations** | 7 | Create filing, build stack, validate, score, export, list, get status |
| **Deadline Management** | 5 | Calculate, add, list upcoming, list overdue, check conflicts |
| **Evidence Management** | 7 | Add, search, assign Bates, authenticate, get exhibit list, check gaps, get chain |
| **Document Generation** | 5 | Generate from template, to DOCX, to PDF, merge PDFs, list templates |
| **Court Rules** | 5 | Get rule, search rules, validate format, get applicable, get by category |
| **Pre-Filing QA** | 3 | Run QA check, get decision, get checklist |
| **Calendar** | 3 | Export ICS, get month view, get deadline counts |
| **Settings** | 2 | Get settings, update settings |
| **AI/RAG** | 2 | Query RAG, classify text |

### Tool Naming Convention

Tools follow the pattern: litigationos_{domain}_{action}

Examples:
- litigationos_case_create
- litigationos_filing_validate
- litigationos_deadline_calculate
- litigationos_evidence_assign_bates
- litigationos_qa_run_check

### Integration Pattern

`python
# MCP tools wrap engine methods with JSON schema validation
@tool("litigationos_filing_validate")
def validate_filing(filing_id: str) -> dict:
    engine = FilingEngine(db)
    result = engine.validate_stack(filing_id)
    return {"score": result.score, "issues": result.issues}
`

---

## 4. GUI Screen Architecture

LitigationOS has 14 GUI screens built with CustomTkinter, following a consistent pattern.

### Screen Registry

The main app (gui/app.py) defines navigation items and lazily instantiates screens:

| Screen Key | Class | File | Status |
|------------|-------|------|--------|
| dashboard | DashboardFrame | dashboard.py | Active |
| deadlines | DeadlineDashboardFrame | deadline_dashboard.py | Active |
| cases | CaseManagerFrame | case_manager.py | Active |
| ilings | FilingManagerFrame | filing_manager.py | Placeholder |
| iling_wizard | FilingWizardFrame | filing_wizard.py | Active |
| vidence | EvidenceBrowserFrame | evidence_browser.py | Placeholder |
| vidence_map | EvidenceMapFrame | evidence_map.py | Active |
| doc_editor | DocumentEditorFrame | document_editor.py | Active |
| calendar | CalendarViewFrame | calendar_view.py | Active |
| 	imeline | TimelineFrame | timeline_view.py | Placeholder |
| settings | SettingsFrame | settings_screen.py | Placeholder |

### Screen Pattern

All screens follow this pattern:

`python
class MyScreenFrame(ctk.CTkFrame):
    """Screen description."""

    def __init__(self, parent, *, db: DatabaseManager, navigate_cb=None):
        super().__init__(parent, fg_color="transparent")
        self._db = db
        self._navigate = navigate_cb
        # Initialize engines
        self._engine = MyEngine(db)
        # Build UI
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        """Create widgets."""
        ...

    def _load_data(self):
        """Fetch data from engines and populate widgets."""
        ...
`

### Engine-to-Screen Wiring

| Screen | Engines Used |
|--------|-------------|
| Dashboard | ALL engines (cases, deadlines, filings, evidence, placeholders) |
| Deadline Dashboard | DeadlineEngine |
| Case Manager | DatabaseManager (direct queries) |
| Filing Wizard | FilingEngine, CourtRulesEngine, pre-filing QA |
| Evidence Map | EvidenceEngine |
| Document Editor | DocumentEngine, CourtRulesEngine, placeholder resolver |
| Calendar View | DeadlineEngine |
| Timeline View | DatabaseManager (timeline_events) |
| Settings | SettingsEngine |
| Filing Manager | FilingEngine |
| Evidence Browser | EvidenceEngine |

---

## 5. Engine Integration Patterns

### How GUI Connects to Engines

GUI screens communicate with engines through a consistent dependency injection pattern:

`python
# 1. Screen receives DatabaseManager via constructor
class FilingWizardFrame(ctk.CTkFrame):
    def __init__(self, parent, *, db: DatabaseManager, navigate_cb=None):
        self._db = db
        # 2. Screen creates engine instances
        self._filing = FilingEngine(db)
        self._rules = CourtRulesEngine(db)

    def _on_validate(self):
        # 3. Screen calls engine methods
        result = self._filing.validate_stack(self._current_filing_id)
        # 4. Screen updates UI with results
        self._show_validation_result(result)
`

### Multi-Engine Composition

The Dashboard demonstrates composing multiple engines:

`python
class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, *, db, navigate_cb=None):
        self._deadline_engine = DeadlineEngine(db)
        self._filing_engine = FilingEngine(db)
        self._evidence_engine = EvidenceEngine(db)

    def _load_data(self):
        overdue = self._deadline_engine.get_overdue()
        upcoming = self._deadline_engine.get_upcoming(days=7)
        filings = self._filing_engine.get_filings(status="draft")
        # Compose into unified dashboard view
`

### Event Propagation

Screens use callback functions for navigation:

`python
# Parent passes navigate callback
frame = FilingWizardFrame(parent, db=db, navigate_cb=self.switch_screen)

# Child screen triggers navigation
def _on_filing_complete(self):
    if self._navigate:
        self._navigate("dashboard")  # Return to dashboard
`

---

## 6. Adding a Jurisdiction Plugin

LitigationOS ships with Michigan built-in. To add a new jurisdiction:

### Step 1: Create the Plugin Directory

`
src/litigationos/plugins/ohio/
+-- __init__.py
+-- rules.py        # Court rules seed data
+-- deadlines.py    # Deadline calculation rules
+-- courts.py       # Court directory
+-- forms.py        # State-specific forms
`

### Step 2: Register the Jurisdiction

Insert into the jurisdictions table:

`python
def seed_ohio(db: DatabaseManager) -> None:
    conn = db.connect()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO jurisdictions (id, name, state_code, rules_version, enabled) "
            "VALUES ('OH', 'Ohio', 'OH', '2024', 1)"
        )
        conn.commit()
    finally:
        conn.close()
`

### Step 3: Define Court Rules

Follow the pattern in ngines/court_rules.py:

`python
_OHIO_RULES = [
    {
        "rule_number": "Civ.R. 12(A)",
        "title": "Time to Serve Responsive Pleading",
        "full_text": "A defendant shall serve an answer within 28 days ...",
        "category": "response",
        "court_type": "common_pleas",
        "requirements_json": json.dumps({"answer_days": 28}),
    },
    # ... more rules
]
`

### Step 4: Define Deadline Rules

Add entries to the deadline calculation system following the _MCR_DEADLINES pattern in ngines/deadline.py.

### Step 5: Add Courts

Populate the courts table with the jurisdiction's court directory.

---

## 7. Adding a New Engine

Engines encapsulate domain logic. To create a new engine:

### Template

`python
"""<Domain> engine -- <brief description>."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


class MyEngine:
    """<Description of what this engine does>."""

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db

    def my_method(self, param: str) -> dict:
        """<Docstring>."""
        row = self._db.fetchone("SELECT * FROM my_table WHERE col = ?", (param,))
        if row is None:
            return {}
        return dict(row)
`

### Guidelines

1. **Constructor** takes DatabaseManager as the single required argument
2. **Use self._db** for all database operations -- don't create your own connections unless you need a transaction
3. **Use TYPE_CHECKING** for the DatabaseManager import to avoid circular imports
4. **Log operations** using logging.getLogger(__name__)
5. **Raise specific exceptions** (ValueError, LookupError, etc.) -- don't swallow errors silently
6. **Register the engine** in ngines/__init__.py:

`python
from litigationos.engines.my_engine import MyEngine
__all__ = [..., "MyEngine"]
`

### Phase 5-6 Engine Pattern

New Phase 5-6 engines follow the same pattern but may compose existing engines:

`python
class PreFilingQAEngine:
    """Pre-filing quality assurance -- GO/NO-GO gate."""

    def __init__(self, db: "DatabaseManager") -> None:
        self._db = db
        self._filing = FilingEngine(db)
        self._rules = CourtRulesEngine(db)
        self._evidence = EvidenceEngine(db)

    def run_qa_check(self, filing_id: str) -> dict:
        """Run full QA checklist and return GO/NOGO/CONDITIONAL."""
        stack = self._filing.build_stack(filing_id)
        validation = self._filing.validate_stack(filing_id)
        # ... compose results from multiple engines
`

---

## 8. Database Schema

The full schema is defined in src/litigationos/db/schema.sql.

### Core Tables

| Table | Purpose |
|-------|---------|
| jurisdictions | Jurisdiction plugin registry |
| courts | Court directory with addresses and e-filing URLs |
| cases | Top-level case container |
| parties | Parties involved in a case |
| claims | Legal claims/counts within a case |
| court_rules | Court rules per jurisdiction |
| ilings | Court filings with status tracking |
| deadlines | Calculated and manual deadlines |
| vidence | Evidence items with Bates numbers |
| 	emplates | Jinja2 document templates |
| documents | Generated documents |
| 	imeline_events | Chronological case events |
| settings | Key-value application settings |
| scao_forms | Michigan SCAO forms catalog |

### FTS5 Virtual Tables

| Table | Indexes |
|-------|---------|
| vidence_fts | title, description, source, tags, notes |
| court_rules_fts | rule_number, title, full_text, category |

FTS tables are kept in sync via AFTER INSERT/UPDATE/DELETE triggers.

### Key PRAGMAs

`sql
PRAGMA journal_mode = WAL;      -- Write-ahead logging for concurrency
PRAGMA foreign_keys = ON;        -- Enforce referential integrity
PRAGMA busy_timeout = 60000;     -- 60s wait on lock contention
PRAGMA cache_size = -32000;      -- 32 MB page cache
`

---

## 9. Testing

### Test Suite Overview

LitigationOS has 266 tests across 12 test files plus a shared conftest.

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| 	est_engines.py | 66 | Core engine business logic (Court Rules, Deadline, Filing, Evidence, Document) |
| 	est_models.py | 30 | Pydantic model validation |
| 	est_db.py | 21 | Database connection, schema, migrations |
| 	est_brief_compliance.py | 20 | MCR 7.212 brief format compliance |
| 	est_complaint_stacks.py | 19 | Complaint templates and agency compliance |
| 	est_placeholder_resolver.py | 19 | Template placeholder resolution |
| 	est_authority_index.py | 18 | Court rule lookup and cross-referencing |
| 	est_efiling_prep.py | 16 | E-filing packet assembly and format validation |
| 	est_court_calendar.py | 15 | ICS export, deadline calculation, urgency levels |
| 	est_evidence_chain.py | 15 | Chain of custody, SHA-256, gap detection |
| 	est_prefiling_qa.py | 14 | GO/NO-GO decision, signature, service validation |
| 	est_backup_version.py | 13 | Snapshot, hash verification, manifest, restore |
| **Total** | **266** | |

### Setup

`ash
pip install -e ".[dev]"
`

This installs pytest and pytest-cov.

### Running Tests

`ash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_models.py

# Run a specific test class
pytest tests/test_engines.py::TestCourtRulesEngine

# Run a single test
pytest tests/test_engines.py::TestDeadlineEngine::test_weekend_adjustment

# Run Phase 5-6 tests only
pytest tests/test_court_calendar.py tests/test_brief_compliance.py tests/test_prefiling_qa.py tests/test_evidence_chain.py tests/test_backup_version.py tests/test_placeholder_resolver.py tests/test_efiling_prep.py tests/test_authority_index.py tests/test_complaint_stacks.py
`

### Coverage

`ash
# Generate coverage report
pytest --cov=litigationos --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=litigationos --cov-report=html
# Open htmlcov/index.html in your browser
`

### Test Structure

`
tests/
+-- conftest.py                  # Shared fixtures (tmp_db, sample_case, etc.)
+-- test_models.py               # Pydantic model validation tests
+-- test_db.py                   # Database connection and schema tests
+-- test_engines.py              # Core engine business logic tests
+-- test_court_calendar.py       # Phase 5: Calendar/ICS tests
+-- test_brief_compliance.py     # Phase 5: Brief format compliance
+-- test_prefiling_qa.py         # Phase 5: Pre-filing QA gate
+-- test_evidence_chain.py       # Phase 5: Evidence chain of custody
+-- test_backup_version.py       # Phase 5: Backup and versioning
+-- test_placeholder_resolver.py # Phase 6: Placeholder resolution
+-- test_efiling_prep.py         # Phase 6: E-filing preparation
+-- test_authority_index.py      # Phase 6: Authority index
+-- test_complaint_stacks.py     # Phase 6: Complaint templates
`

### Key Fixtures

| Fixture | Description |
|---------|-------------|
| 	mp_db | Fresh DatabaseManager with schema initialized in a temp directory |
| db_conn | Raw sqlite3.Connection to the test database |
| sample_case | Pre-inserted test case record |
| sample_party | Petitioner + respondent party records |
| sample_filing | Pre-inserted test filing record |
| sample_evidence | Three evidence records with dummy files |

### Writing Tests

- Use the 	mp_db fixture for all database tests -- it gives you a clean database each test
- Group related tests in classes (e.g., TestCourtRulesEngine)
- Test both happy path and error cases
- Target 80%+ coverage on core engines
- Phase 5-6 tests follow the same fixture and class patterns

---

## 10. Building the Installer

### Windows Installer (PyInstaller)

`ash
pip install pyinstaller

pyinstaller --name LitigationOS \
    --onefile \
    --windowed \
    --icon=assets/icon.ico \
    --add-data "src/litigationos/db/schema.sql;litigationos/db" \
    src/litigationos/app.py
`

The built executable will be in dist/LitigationOS.exe.

### Including Data Files

Ensure these files are bundled:
- db/schema.sql -- Database schema
- db/seed.py -- Seed data for jurisdictions
- Any template files in the templates directory

### Package Distribution

`ash
# Build source and wheel distributions
python -m build

# Upload to PyPI (or TestPyPI)
twine upload dist/*
`

### Versioning

Update the version in src/litigationos/__init__.py:

`python
__version__ = "0.2.0"
`

And in pyproject.toml:

`	oml
version = "0.2.0"
`
