# LitigationOS — Quick Start Guide

Get from zero to court-ready filings in under 10 minutes.

---

## Installation

```bash
pip install litigationos
```

**Requirements:** Python 3.12 or later.

Verify the installation:

```bash
litigationos version
```

### Optional AI Features

For AI-powered analysis (local only — no cloud):

```bash
pip install litigationos[ai]
```

This adds Ollama (local LLM) and ChromaDB (local vector search) support. The core app works fully without these.

---

## First Case Setup

### 1. Initialize Your Database

```bash
litigationos init
```

This creates your local database at `~/.home/LitigationOS/litigationos.db` and seeds Michigan court rules, SCAO forms, and deadline calculation tables.

### 2. Create a Case

```bash
litigationos cases
```

Or launch the GUI for the full visual experience:

```bash
litigationos
```

### 3. Start the GUI

The GUI provides 11 screens for complete case lifecycle management:

```bash
litigationos
```

You'll see the **Dashboard** — your command center showing active cases, upcoming deadlines, filing status, and evidence summary.

---

## Core Workflow

### Upload Evidence → Auto-Analysis → Generated Filings

```
Step 1: Upload Evidence
┌─────────────────────────────────┐
│  📁 Evidence Browser            │
│                                 │
│  Drag & drop files or click     │
│  "Import Evidence" to add:      │
│  • PDFs, documents, images      │
│  • Emails, screenshots          │
│  • Court orders, transcripts    │
│                                 │
│  Each file is automatically:    │
│  ✓ SHA-256 hashed (integrity)   │
│  ✓ Bates numbered (PIGORS-0001) │
│  ✓ Full-text indexed (FTS5)     │
│  ✓ AI-classified (if enabled)   │
└─────────────────────────────────┘
            │
            ▼
Step 2: AI Analysis
┌─────────────────────────────────┐
│  🧠 AI Legal Brain              │
│                                 │
│  Automatically:                 │
│  ✓ Classifies document type     │
│  ✓ Extracts entities (parties,  │
│    dates, amounts, case #s)     │
│  ✓ Scores evidence relevance    │
│  ✓ Detects case lane            │
│  ✓ Links evidence to claims     │
│  ✓ Identifies gaps              │
└─────────────────────────────────┘
            │
            ▼
Step 3: Generate Filings
┌─────────────────────────────────┐
│  📝 Filing Wizard               │
│                                 │
│  1. Select filing type          │
│     (motion, brief, complaint)  │
│  2. Choose court & case         │
│  3. Attach exhibits             │
│  4. Auto-compliance check       │
│     (MCR formatting, margins,   │
│      font, spacing, page limit) │
│  5. Generate court-ready PDF    │
│  6. Create proof of service     │
└─────────────────────────────────┘
```

---

## Key Commands Reference

| Command | Description |
|---------|-------------|
| `litigationos` | Launch the GUI (default) |
| `litigationos version` | Show current version |
| `litigationos init` | Initialize database with Michigan defaults |
| `litigationos init --data-dir ~/my-cases` | Initialize with custom data directory |
| `litigationos cases` | List all active cases |
| `litigationos deadlines` | Show upcoming court deadlines |

---

## GUI Screens at a Glance

| Screen | What It Does |
|--------|-------------|
| **📊 Dashboard** | Command center — alerts, case overview, deadline countdown, quick actions |
| **⏰ Deadlines** | Color-coded urgency timers for every court deadline |
| **📁 Cases** | Create, edit, and manage cases with parties and claims |
| **📄 Filings** | Build, validate, and export court-ready filing packages |
| **📝 Filing Wizard** | Step-by-step guided filing creation with compliance scoring |
| **🔍 Evidence** | Search, browse, tag, and authenticate evidence items |
| **🗺 Evidence Map** | Visual graph showing which evidence supports which claims |
| **📃 Doc Editor** | View and edit documents with real-time compliance checking |
| **📅 Calendar** | Monthly calendar highlighting all deadline dates |
| **📅 Timeline** | Interactive case timeline with events, filings, and hearings |
| **⚙️ Settings** | Jurisdiction, file paths, AI configuration, display theme |

---

## Example: Filing a Motion in 5 Minutes

```
1. Open LitigationOS GUI
2. Navigate to Filing Wizard (📝 in sidebar)
3. Select: Type = "Motion", Court = "14th Circuit Court"
4. Enter motion title and select case
5. Attach exhibits from your evidence library
6. Click "Check Compliance" — see your MCR score (aim for 90+)
7. Click "Generate PDF" — court-formatted document ready
8. Click "Create Service Packet" — proof of service included
9. Print and file. Done.
```

---

## Data Privacy

- **All data stays on your machine.** No cloud, no sync, no telemetry.
- Database location: `~/.home/LitigationOS/litigationos.db`
- Evidence originals are never modified — append-only with SHA-256 verification.
- AI analysis runs locally via offline algorithms (no internet required).

---

## Getting Help

- **Documentation:** [litigationos.com/docs](https://litigationos.com/docs)
- **GitHub Issues:** Report bugs and request features
- **GitHub Discussions:** Community Q&A
- **Pro Support:** Priority email support for Pro/Enterprise subscribers

---

## What's Next?

- **Add more evidence** — The more evidence you import, the better the AI analysis.
- **Explore the Evidence Map** — See gaps in your case at a glance.
- **Set up deadlines** — Never miss a filing deadline again.
- **Try the Filing Factory** — Let the system assemble filings autonomously (Pro tier).

---

> ⚠️ **Important:** LitigationOS is a legal research and document preparation tool. It does not provide legal advice. Always consult with a licensed attorney for legal guidance. You are responsible for reviewing all generated documents before filing with any court.
