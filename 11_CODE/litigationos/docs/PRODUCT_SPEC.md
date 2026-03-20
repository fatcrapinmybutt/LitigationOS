# LitigationOS — Product Specification

> **Version:** 0.2.0  
> **Tagline:** *The autonomous litigation intelligence system.*

---

## Vision

LitigationOS is the first local-first, AI-powered litigation management system designed for people who represent themselves in court. It turns raw evidence into court-ready filings — automatically.

The legal system is adversarial by design, but the tools available to self-represented litigants are not. LitigationOS levels the playing field by combining case management, document automation, deadline tracking, evidence cataloguing, and AI-assisted legal analysis into a single desktop application that runs entirely on your machine. No cloud. No subscriptions required. No data leaves your computer unless you choose to share it.

---

## Target Users

| Segment | Description | Pain Points Solved |
|---------|-------------|-------------------|
| **Pro se litigants** | Self-represented individuals in family, civil, or housing court | Deadline confusion, formatting errors, missed claims, evidence disorganization |
| **Solo attorneys** | Solo practitioners managing 10-50 active cases | Time-consuming document prep, MCR compliance checking, multi-case deadline tracking |
| **Legal aid organizations** | Nonprofits assisting underserved litigants | High caseloads, limited staff, need for standardized intake and filing workflows |
| **Law students / clinics** | Students learning litigation mechanics | Practice-ready filing assembly, court rules reference, case study tool |

---

## Core Features — The 13 Engines

LitigationOS is built around 13 specialized engines, each handling a distinct aspect of the litigation lifecycle:

| # | Engine | Module | Description |
|---|--------|--------|-------------|
| 1 | **Case Engine** | `case_engine.py` | Universal case management with CRUD operations, party management, six-lane routing (Custody, Housing, Convergence, PPO, Misconduct, Appellate), evidence-to-claim linkage, and filing state machine. |
| 2 | **Filing Engine** | `filing.py` | Filing stack builder that assembles complete court packages — main document, exhibits, proof of service, fee waiver, proposed order. Validates MCR formatting (margins, font, spacing, page limits) with 0-100 compliance scoring. |
| 3 | **Document Engine** | `document.py` | Document generation pipeline: Jinja2 templates → DOCX → PDF. Court-formatted output (Times New Roman 12pt, double-spaced, 1-inch margins). Supports Markdown rendering, page numbering, and PDF merging. |
| 4 | **Deadline Engine** | `deadline.py` | Michigan Court Rules deadline calculator for Circuit Court, Court of Appeals, and Supreme Court. Adjusts for weekends and Michigan court holidays (2025–2027). Deadline CRUD, overdue alerts, and conflict detection. |
| 5 | **Evidence Engine** | `evidence.py` | Evidence cataloguing with SHA-256 integrity hashing, automatic Bates numbering (e.g., `PIGORS-000001`), FTS5 full-text search, MRE 901 authentication declarations, exhibit list generation, and gap analysis. |
| 6 | **Court Rules Engine** | `court_rules.py` | Michigan Court Rules (MCR) lookup and search. Seeds key rules on first use, provides FTS5 full-text search, filing format validation, and applicable-rule resolution for any filing type. |
| 7 | **Settings Engine** | `settings.py` | Application settings management — jurisdiction selection, file paths, LLM configuration, display theme. Backed by SQLite with Michigan defaults auto-seeded on first access. |
| 8 | **AI Legal Brain** | `ai_legal_brain.py` | "MANBEARPIG v10" — Production-grade offline legal AI. Document classification, named entity extraction (parties, judges, dates, amounts, case numbers), evidence scoring, lane detection, citation parsing, and argument drafting. Uses TF-IDF, BM25, regex, and keyword matching. Zero network dependencies. |
| 9 | **RAG Engine** | `rag.py` | Local retrieval-augmented generation via Ollama (LLM) + ChromaDB (vectors). Hybrid search combining vector similarity with SQLite FTS5. Classification, summarization, and structured Q&A with citations. Gracefully degrades when unavailable. |
| 10 | **Ollama Engine** | `ai.py` | Ollama LLM integration for AI-assisted features — filing classification, compliance suggestions, evidence summarization. Falls back gracefully when Ollama is not running. |
| 11 | **Filing Factory** | `filing_factory.py` | Autonomous end-to-end filing generation pipeline. Orchestrates the full lifecycle: draft → review → QA pass → ready → filed → served. Integrates FilingEngine and DocumentEngine with state-machine enforcement and QA loops. |
| 12 | **Onboarding Engine** | `onboarding.py` | Case onboarding wizard with 10 intake stages: case info → parties → evidence upload → classification → claim detection → filing suggestions → timeline build → deadline assignment → review → complete. Zero-to-case-ready in 30 minutes. |
| 13 | **Monetization Engine** | `monetization.py` | Subscription management for Free/Pro/Enterprise tiers. Usage tracking, tier-based feature gating, and payment integration stubs for Stripe. Per-filing charges and tier-specific limits. |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        LitigationOS                             │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │   CLI        │  │   GUI        │  │   API (future)         │ │
│  │  (Typer)     │  │ (CustomTkinter)│ │   (FastAPI)           │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────┘ │
│         │                 │                      │              │
│         └────────────┬────┴──────────────────────┘              │
│                      ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Engine Layer (13)                      │   │
│  │                                                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │   │
│  │  │  Case    │ │ Filing   │ │ Document │ │  Deadline   │  │   │
│  │  │  Engine  │ │ Engine   │ │ Engine   │ │  Engine     │  │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘  │   │
│  │       │            │            │              │         │   │
│  │  ┌────┴─────┐ ┌────┴─────┐ ┌───┴──────┐ ┌────┴──────┐  │   │
│  │  │ Evidence │ │  Court   │ │ Settings │ │ Onboarding │  │   │
│  │  │  Engine  │ │  Rules   │ │ Engine   │ │  Engine    │  │   │
│  │  └────┬─────┘ └──────────┘ └──────────┘ └───────────┘  │   │
│  │       │                                                  │   │
│  │  ┌────┴──────────────────────────────────────────────┐   │   │
│  │  │              AI Layer                             │   │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │   │   │
│  │  │  │ AI Legal │ │   RAG    │ │  Ollama  │          │   │   │
│  │  │  │  Brain   │ │  Engine  │ │  Engine  │          │   │   │
│  │  │  │(offline) │ │(optional)│ │(optional)│          │   │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘          │   │   │
│  │  └───────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌────────────────────┐  ┌────────────────────────────┐  │   │
│  │  │  Filing Factory    │  │  Monetization Engine       │  │   │
│  │  │  (orchestrator)    │  │  (tier gating)             │  │   │
│  │  └────────────────────┘  └────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                          │
│                      ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Data Layer                              │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │   │
│  │  │  SQLite  │  │  Pydantic    │  │  Jurisdiction     │  │   │
│  │  │  (WAL)   │  │  Models (9)  │  │  Plugins          │  │   │
│  │  │          │  │              │  │  ┌─────────────┐  │  │   │
│  │  │ cases    │  │ Case         │  │  │  Michigan   │  │  │   │
│  │  │ filings  │  │ Filing       │  │  │  (built-in) │  │  │   │
│  │  │ evidence │  │ Deadline     │  │  └─────────────┘  │  │   │
│  │  │ deadlines│  │ Claim        │  │  ┌─────────────┐  │  │   │
│  │  │ claims   │  │ Evidence     │  │  │  Other      │  │  │   │
│  │  │ parties  │  │ Party        │  │  │  (plugin)   │  │  │   │
│  │  │ documents│  │ Document     │  │  └─────────────┘  │  │   │
│  │  │ templates│  │ Template     │  │                   │  │   │
│  │  │ timeline │  │ TimelineEvent│  │                   │  │   │
│  │  └──────────┘  └──────────────┘  └───────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Engine Interaction Flow

```
User uploads evidence
        │
        ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Evidence   │───▶│   AI Legal   │───▶│    Case      │
│   Engine     │    │   Brain      │    │   Engine     │
│ (catalog,    │    │ (classify,   │    │ (link to     │
│  hash, Bates)│    │  extract,    │    │  claims,     │
│              │    │  score)      │    │  route lane) │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐            │
                    │  Court Rules │◀───────────┘
                    │  Engine      │
                    │ (MCR lookup, │
                    │  validate)   │
                    └──────┬───────┘
                           │
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Deadline   │◀───│   Filing     │───▶│   Document   │
│   Engine     │    │   Factory    │    │   Engine     │
│ (calculate   │    │ (orchestrate │    │ (Jinja2 →    │
│  due dates)  │    │  lifecycle)  │    │  DOCX → PDF) │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Filing     │
                    │   Engine     │
                    │ (assemble    │
                    │  package,    │
                    │  compliance  │
                    │  score)      │
                    └──────────────┘
                           │
                           ▼
                    Court-Ready PDF
```

---

## Supported Jurisdictions

| Jurisdiction | Status | Plugin | Coverage |
|-------------|--------|--------|----------|
| **Michigan** | ✅ Shipped | `plugins/michigan/` | MCR rules, SCAO forms, court directory, deadline calculations, filing validation |
| **Federal (FRCP)** | 🔮 Planned | — | Federal Rules of Civil Procedure, PACER integration |
| **California** | 🔮 Planned | — | CRC rules, Judicial Council forms |
| **New York** | 🔮 Planned | — | CPLR, court system directory |

### Plugin Architecture

New jurisdictions are added by implementing the `JurisdictionPlugin` base class:

```python
from litigationos.plugins.base import JurisdictionPlugin

class CaliforniaPlugin(JurisdictionPlugin):
    jurisdiction_id = "CA"
    jurisdiction_name = "California"

    def get_rules(self, category): ...
    def get_forms(self, category): ...
    def get_courts(self, court_type): ...
    def calculate_deadline(self, filing_type, trigger_date, case_type, court_type): ...
    def validate_filing(self, filing, filing_type): ...
    def seed_database(self, db): ...
```

---

## Data Privacy Guarantees

LitigationOS is **local-first by design**:

| Guarantee | Implementation |
|-----------|---------------|
| **All data stays on your machine** | SQLite database stored at `~/.home/LitigationOS/litigationos.db`. No cloud sync, no remote storage. |
| **Zero telemetry by default** | No analytics, no usage tracking, no phone-home. Optional opt-in for anonymized crash reports only. |
| **No API keys required** | Core functionality (all 13 engines) works without any external API. AI Legal Brain runs fully offline using TF-IDF/BM25. |
| **Optional AI enhancement** | Ollama (local LLM) and ChromaDB (local vectors) run on your hardware. No data sent to OpenAI, Google, or any cloud provider. |
| **Evidence integrity** | Every imported file is SHA-256 hashed. Originals are append-only — never overwritten or modified. |
| **Encryption ready** | Database can be encrypted with SQLCipher (user-provided key). No key escrow. |
| **Full data export** | Users can export all data (cases, filings, evidence, deadlines) to JSON/CSV at any time. |
| **Right to delete** | Complete data deletion via `litigationos reset --confirm` removes all local data. |

---

## Pricing Tiers

| Feature | Free | Pro ($49/mo) | Enterprise ($199/mo) |
|---------|------|-------------|---------------------|
| **Cases** | 1 | Unlimited | Unlimited |
| **Evidence items** | 50 | Unlimited | Unlimited |
| **Filings per month** | 5 | 50 | Unlimited |
| **AI queries per day** | 5 | 100 | Unlimited |
| **Engines** | 7 core | All 13 | All 13 |
| **GUI screens** | 6 basic | All 11 | All 11 + custom |
| **Filing Factory** | — | ✅ | ✅ |
| **Onboarding Wizard** | — | ✅ | ✅ |
| **Compliance scoring** | Basic | Full MCR | Full MCR + custom rules |
| **Jurisdictions** | Michigan | Michigan | Michigan + custom plugins |
| **Document export** | PDF only | PDF + DOCX | PDF + DOCX + API |
| **Support** | Community (GitHub) | Priority email | Dedicated rep + SLA |
| **API access** | — | — | ✅ REST API |
| **White-label** | — | — | ✅ Custom branding |
| **Multi-user** | — | — | ✅ Team accounts |
| **Stripe billing** | — | Monthly/annual | Monthly/annual + invoicing |

### Free Tier Engines

The Free tier includes these 7 engines: Case Engine, Filing Engine, Document Engine, Deadline Engine, Evidence Engine, Court Rules Engine, and Settings Engine.

### Pro Tier Additions

Pro unlocks: AI Legal Brain, RAG Engine, Ollama Engine, Filing Factory, Onboarding Engine, and Monetization Engine (self-service billing portal).

---

## Competitive Positioning

| Capability | LitigationOS | Clio | MyCase | LegalZoom |
|-----------|-------------|------|--------|-----------|
| **Target user** | Pro se + solo attorneys | Law firms | Law firms | Consumers (forms) |
| **Local-first / offline** | ✅ Full offline | ❌ Cloud-only | ❌ Cloud-only | ❌ Cloud-only |
| **Price (entry)** | Free | $49/mo | $39/mo | $9.99/doc |
| **AI legal analysis** | ✅ Built-in (offline) | ⚠️ Add-on | ❌ | ❌ |
| **Auto filing assembly** | ✅ Filing Factory | ❌ Manual | ❌ Manual | ⚠️ Templates only |
| **Court rules engine** | ✅ MCR built-in | ❌ | ❌ | ❌ |
| **Deadline calculator** | ✅ MCR-aware | ⚠️ Basic calendar | ⚠️ Basic calendar | ❌ |
| **Evidence management** | ✅ Bates + FTS5 + auth | ⚠️ Basic docs | ⚠️ Basic docs | ❌ |
| **Compliance scoring** | ✅ 0-100 MCR score | ❌ | ❌ | ❌ |
| **Data privacy** | ✅ Zero-cloud | ❌ Cloud-stored | ❌ Cloud-stored | ❌ Cloud-stored |
| **Open source** | ✅ Community edition | ❌ Proprietary | ❌ Proprietary | ❌ Proprietary |
| **Jurisdiction plugins** | ✅ Extensible | N/A | N/A | N/A |
| **Self-hosted** | ✅ Always | ❌ | ❌ | ❌ |

### Key Differentiators

1. **Local-first**: Your data never leaves your computer. Period.
2. **Pro se focused**: Built for people representing themselves, not law firms.
3. **Autonomous filing**: Upload evidence → AI analysis → court-ready PDF. No manual assembly.
4. **Court rules aware**: Knows Michigan Court Rules. Calculates deadlines. Validates formatting.
5. **Open and extensible**: Community edition is open source. Add your own jurisdiction plugins.

---

## Technical Requirements

| Requirement | Specification |
|------------|--------------|
| **Python** | ≥ 3.12 |
| **OS** | Windows 10+, macOS 12+, Linux (Ubuntu 22.04+) |
| **RAM** | 4 GB minimum, 8 GB recommended |
| **Disk** | 500 MB for app + database (varies with evidence volume) |
| **Display** | 1280×720 minimum for GUI |
| **Optional** | Ollama for local LLM, ChromaDB for vector search |

---

## Roadmap

| Quarter | Milestone |
|---------|-----------|
| **Q1** | v0.2.0 — Michigan launch, 13 engines, GUI, CLI, PyPI package |
| **Q2** | v0.3.0 — Federal jurisdiction plugin, API access (Enterprise), document templates marketplace |
| **Q3** | v0.4.0 — California + New York plugins, team collaboration (Enterprise), mobile companion app |
| **Q4** | v1.0.0 — Production release, 10+ jurisdictions, marketplace, certification program |
