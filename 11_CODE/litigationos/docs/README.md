# LitigationOS User Guide

**Pro se litigation management system for Michigan courts.**

LitigationOS is a local-first desktop application that helps self-represented litigants manage cases, build court filings, track deadlines, and organize evidence -- all running on your own machine with no cloud dependency.

---

## Table of Contents

1. [Installation](#1-installation)
2. [Quick Start](#2-quick-start)
3. [Dashboard Overview](#3-dashboard-overview)
4. [Managing Cases](#4-managing-cases)
5. [Building Filing Stacks](#5-building-filing-stacks)
6. [Evidence Management](#6-evidence-management)
7. [Evidence Map](#7-evidence-map)
8. [Timeline View](#8-timeline-view)
9. [Deadline Dashboard](#9-deadline-dashboard)
10. [Calendar View](#10-calendar-view)
11. [Document Editor](#11-document-editor)
12. [Filing Wizard](#12-filing-wizard)
13. [Complaint Filing Guide](#13-complaint-filing-guide)
14. [Deadline Tracking Guide](#14-deadline-tracking-guide)
15. [Settings Configuration](#15-settings-configuration)
16. [AI / RAG Features](#16-ai--rag-features)
17. [Keyboard Shortcuts](#17-keyboard-shortcuts)

---

## Feature Summary

LitigationOS provides a comprehensive litigation management platform:

| Category | Details |
|----------|---------|
| **Engines** | 9 core engines (Court Rules, Deadline, Filing, Evidence, Document, AI, RAG, Settings, + Phase 5-6 additions) |
| **GUI Screens** | 14 screens (Dashboard, Deadline Dashboard, Cases, Filings, Filing Wizard, Evidence Browser, Evidence Map, Document Editor, Calendar View, Timeline, Settings, Filing Manager, + placeholders) |
| **MCP Tools** | 45 Model Context Protocol tools for automation |
| **Test Coverage** | 266 tests across 12 test files |
| **Database** | SQLite with WAL mode, FTS5 full-text search, 14+ core tables |

---

## 1. Installation

### System Requirements

- **OS:** Windows 10/11 (primary), macOS, or Linux
- **Python:** 3.12 or newer
- **Disk:** ~100 MB for the application, plus storage for case data
- **Optional:** [Ollama](https://ollama.com) for local AI features

### Install from PyPI

`ash
pip install litigationos
`

### Install from Source (Development)

`ash
git clone https://github.com/yourusername/litigationos.git
cd litigationos
pip install -e ".[dev]"
`

### Windows-Specific Notes

- On Windows, you may need the [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) for some Python dependencies.
- If you see errors about 	kinter, ensure Python was installed with the "tcl/tk" option checked.
- The default data directory is %USERPROFILE%\LitigationOS\data\.

### Verify Installation

`ash
litigationos --help
`

---

## 2. Quick Start

### First Launch

`ash
litigationos
`

On first launch, LitigationOS will:
1. Create the data directory at ~/LitigationOS/data/
2. Initialize the SQLite database with the full schema
3. Seed Michigan jurisdiction data (courts, rules, default settings)
4. Open the GUI dashboard

### Create Your First Case

1. Click **New Case** on the dashboard
2. Enter the case details:
   - **Title:** e.g., "Pigors v. Watson"
   - **Case Number:** e.g., "2025-0001-FC"
   - **Case Type:** Family, Civil, Criminal, Appellate, or Federal
   - **Court:** Select from the Michigan courts list
3. Click **Save** -- the case appears on your dashboard

### Add Parties

1. Open the case and navigate to the **Parties** tab
2. Click **Add Party** for each participant:
   - **Petitioner/Plaintiff** (you)
   - **Respondent/Defendant**
   - **Judge** (assigned to the case)
   - **Opposing Attorney** (if applicable)
3. Include contact information and bar numbers where available

---

## 3. Dashboard Overview

The main dashboard displays:

| Section | Description |
|---------|-------------|
| **Active Cases** | Your open cases with status indicators |
| **Upcoming Deadlines** | Next 30 days of pending deadlines, sorted by urgency |
| **Recent Filings** | Latest filings across all cases |
| **Filing Readiness** | Compliance scores for filings in progress |
| **Evidence Coverage** | Percentage of claims with supporting evidence |
| **Placeholder Status** | Unresolved placeholders flagged as [ANDREW_REQUIRED] |
| **Emergency Alerts** | Critical deadlines and overdue items |
| **Quick Actions** | Buttons for common tasks (New Case, New Filing, Add Evidence) |

The dashboard is wired to all engines and provides a single-screen overview of your entire litigation posture.

### Status Indicators

- Green **Active** -- Case is in progress
- Yellow **Appealed** -- Case is under appeal
- Red **Critical Deadline** -- Deadline within 7 days
- Gray **Closed** -- Case is resolved

---

## 4. Managing Cases

### Case Types

LitigationOS supports these Michigan case categories:

| Type | Description | Common Courts |
|------|-------------|---------------|
| **Family** | Divorce, custody, parenting time, support | Circuit Court (Family Division) |
| **Civil** | Contract, tort, personal injury | Circuit Court, District Court |
| **Criminal** | Defense cases | Circuit Court, District Court |
| **Appellate** | Appeals from lower courts | Court of Appeals, Supreme Court |
| **Federal** | Federal civil, bankruptcy | U.S. District Court |

### Case Lifecycle

`
Created --> Active --> [Appealed] --> Closed/Settled
`

### Claims / Counts

Each case can have multiple claims or counts:
- **Title:** e.g., "Count I: Modification of Custody"
- **Legal Basis:** Cite the statute (e.g., MCL 722.27)
- **Against Party:** Which party the claim targets
- **Damages Sought:** Dollar amount if applicable

---

## 5. Building Filing Stacks

A "filing stack" is the complete package you submit to the court. LitigationOS helps you assemble and validate each stack.

### Filing Types

| Type | Description |
|------|-------------|
| motion | Request the court to take action |
| rief | Legal argument supporting a motion or appeal |
| complaint | Initial document that starts a case |
| 
esponse | Answer to a motion or complaint |
| 
eply | Reply to a response |
| 
otice | Notification to parties or the court |
| ffidavit | Sworn statement |
| xhibit_list | Index of evidence exhibits |
| proposed_order | Draft order for the judge to sign |

### Building a Stack

1. **Create the filing** -- Select case, type, and title
2. **Generate documents** -- Use templates to create the main document
3. **Attach exhibits** -- Link evidence items from your evidence library
4. **Add proof of service** -- Document how you served opposing parties
5. **Include proposed order** -- Draft the order you want the judge to sign
6. **Validate** -- Run compliance check against Michigan Court Rules
7. **Pre-filing QA** -- Run the GO/NO-GO gate check
8. **Export** -- Generate the court-ready PDF packet

### Compliance Validation

The filing engine validates your stack against MCR requirements:

- **Format checks:** Margins (1"), font (Times New Roman 12pt), double spacing
- **Page limits:** Briefs <= 50 pages, motions <= 20 pages, replies <= 10 pages
- **Required components:** Main document, proof of service, exhibits
- **Service requirements:** MCR 2.107 compliance
- **Brief compliance (MCR 7.212):** Table of contents, table of authorities, proper formatting

A score of 80+ with zero errors means the filing is ready to submit.

### Pre-Filing QA Gate

Before any filing goes out, the pre-filing QA engine runs a comprehensive checklist:

| Check | Description |
|-------|-------------|
| **Main Document** | Verifies the primary filing document exists |
| **Proof of Service** | Ensures MCR 2.107 service documentation is present |
| **Signature Block** | Checks for Signature, Printed Name, and Dated fields |
| **Exhibit References** | Verifies all evidence items are referenced with Bates numbers |
| **Format Compliance** | Validates margins, font, spacing per MCR requirements |

**Decision outcomes:**
- **GO** -- All checklist items present, score >= 80
- **CONDITIONAL** -- Partial completion, review recommended
- **NO-GO** -- Critical items missing (e.g., no main document)

### Backup and Versioning

Every filing stack can be snapshotted for version control:

- **Snapshot creation** -- Exports the full stack to a versioned directory with manifest.json
- **Hash verification** -- SHA-256 checksums ensure file integrity between versions
- **Manifest tracking** -- Each manifest records exported files, checklist status, and completeness
- **Restore** -- Any previous version can be fully restored (filing_id, case_id, filing_type, content)

---

## 6. Evidence Management

### Adding Evidence

1. Navigate to the case's **Evidence** tab
2. Click **Add Evidence**
3. Select the file and fill in metadata:
   - **Type:** document, photo, screenshot, recording, email, text_message, court_order, financial, declaration
   - **Description:** What the evidence shows
   - **Source:** Where it came from
   - **Date Created:** When the evidence was originally created
   - **Tags:** Searchable labels (e.g., "custody", "financial")

### Evidence Chain of Custody

The evidence chain engine tracks the complete provenance of each piece of evidence:

- **SHA-256 Hashing** -- Every evidence file gets a cryptographic hash at import time
- **Import Date Tracking** -- Automatic timestamp when evidence enters the system
- **Source Attribution** -- Records where each piece of evidence came from
- **Integrity Verification** -- Hash comparison detects any modifications

### Bates Numbering

Bates numbers provide unique, sequential identifiers for every exhibit:

1. Go to **Evidence** --> **Assign Bates Numbers**
2. Choose a prefix (default: EXHIBIT, or custom like PIGORS)
3. The engine assigns numbers sequentially: PIGORS-000001, PIGORS-000002, etc.
4. Numbers persist and new items continue the sequence
5. Assignment is idempotent -- running it again will not change existing numbers

### Authentication (MRE 901)

For each exhibit, you can generate an authentication declaration:

1. Select an evidence item
2. Click **Authenticate**
3. LitigationOS generates a declaration under MRE 901(a) stating:
   - You have personal knowledge of the exhibit
   - It is a true and accurate representation
   - It has not been altered
   - Includes perjury clause
4. The declaration is ready to include as an attachment to your filing

### Full-Text Search

Evidence descriptions, titles, sources, and tags are indexed with SQLite FTS5. Use the search bar to find exhibits across all cases by keyword.

### Exhibit List Generation

Click **Generate Exhibit List** to produce a formatted table listing all exhibits for a case, including Bates numbers, descriptions, types, and authentication status.

### Evidence Gap Detection

The evidence engine can automatically identify claims that lack supporting evidence:

- Analyzes claim keywords against evidence descriptions
- Highlights unsupported claims that need additional evidence
- Confirms when claims have adequate supporting documentation

---

## 7. Evidence Map

The **Evidence Map** screen provides a visual graph of claims linked to evidence:

- **Claim-to-Evidence Links** -- See which exhibits support each claim
- **Gap Highlighting** -- Claims without supporting evidence are visually flagged
- **Coverage Analysis** -- Percentage of claims with adequate support
- **Interactive Navigation** -- Click on claims or evidence to see details

Access via the sidebar: click **Evidence Map**.

---

## 8. Timeline View

The timeline provides a chronological view of all case events:

### Event Types

| Type | Description |
|------|-------------|
| iling | Court filing submitted |
| hearing | Court hearing or conference |
| order | Judge's order entered |
| communication | Letters, emails, phone calls |
| incident | Key factual events |
| deadline | Important due dates |

### Using the Timeline

1. Navigate to the case's **Timeline** tab
2. Events are displayed in chronological order with color coding by type
3. Each event can link to related filings and evidence
4. Importance levels: Critical, High, Normal, Low
5. Filter by date range, case, or keyword search
6. Create new events via the event creation dialog

---

## 9. Deadline Dashboard

The **Deadline Dashboard** provides a dedicated view of all court deadlines:

- **Visual Countdown Timers** -- Each deadline shows days remaining with color-coded urgency
- **Urgency Levels:**
  - **Critical** -- Answer deadlines, immediate filings
  - **High** -- Motion service deadlines
  - **Medium** -- Reply briefs, routine deadlines
  - **Low** -- Administrative tasks
- **Court Name Display** -- Shows which court each deadline belongs to
- **Overdue Detection** -- Past-due deadlines are highlighted in red
- **Upcoming Window** -- Configurable lookahead period for upcoming deadlines

Access via the sidebar: click **Deadlines**.

---

## 10. Calendar View

The **Calendar View** provides a month-grid calendar interface:

- **Month Grid Display** -- Traditional calendar layout with deadlines marked on their dates
- **Previous/Next Navigation** -- Browse forward and backward through months
- **Deadline Highlighting** -- Days with deadlines are visually distinguished
- **Real Deadline Data** -- Powered by the DeadlineEngine for accuracy
- **ICS Export** -- Generate ICS calendar files for import into Google Calendar, Outlook, Apple Calendar, etc.

### ICS Calendar Integration

LitigationOS can export deadlines as standard ICS (iCalendar) files:

1. Navigate to the **Calendar** screen
2. Click **Export ICS**
3. The generated .ics file contains VCALENDAR/VEVENT blocks with:
   - Deadline title and description
   - Due date in ISO format (YYYYMMDD)
   - Urgency level as event priority
4. Import the .ics file into any calendar application

---

## 11. Document Editor

The **Document Editor** provides an in-app document editing experience:

- **Plain-Text Editing** -- Edit filing documents directly within LitigationOS
- **Compliance Highlighting** -- Real-time highlighting of format issues
- **Word Count** -- Live word/page count against MCR limits
- **Placeholder Resolution** -- Automatically detects and resolves template placeholders:
  - Jinja2 patterns: {{ placeholder }}
  - Bracket patterns: [CASE_NUMBER]
  - Auto-resolves from database: jurisdiction, county, court, case title, party names
  - Unresolved items marked as [ANDREW_REQUIRED: key] for manual review
- **Word-Limit Checking** -- Warns when approaching or exceeding page limits

Access via the sidebar: click **Doc Editor**.

---

## 12. Filing Wizard

The **Filing Wizard** provides a step-by-step guided workflow for preparing court filings:

### Steps

1. **Select Filing Type** -- Choose motion, brief, complaint, response, etc.
2. **Choose Court** -- Select the target court from the Michigan courts directory
3. **Select Documents** -- Pick the main document and supporting documents
4. **Compliance Check** -- Automated validation against MCR requirements
5. **GO/NO-GO Gate** -- Pre-filing QA decision (GO, CONDITIONAL, or NO-GO)
6. **Generate PDFs** -- Create court-ready PDF documents
7. **Filing Instructions** -- Step-by-step instructions for e-filing or in-person submission

The wizard integrates with the FilingEngine, CourtRulesEngine, and pre-filing QA to ensure every filing meets Michigan court requirements before submission.

---

## 13. Complaint Filing Guide

LitigationOS supports filing complaints to multiple Michigan agencies and regulatory bodies. See the dedicated [Complaint Filing Guide](complaint_filing_guide.md) for complete step-by-step instructions.

### Supported Agencies

| Agency | Complaint Type |
|--------|---------------|
| **Michigan Department of Civil Rights (MDCR)** | Discrimination complaints |
| **Michigan Attorney General (AG)** | Consumer protection, fraud |
| **Judicial Tenure Commission (JTC)** | Judicial misconduct |
| **HIPAA / HHS Office for Civil Rights** | Health information privacy violations |
| **Michigan State Bar** | Attorney misconduct |
| **Friend of the Court (FOC)** | Support/parenting time enforcement |

### Quick Filing Steps

1. **Select complaint type** in the Filing Wizard
2. **Choose the target agency** from the dropdown
3. **Complete required fields** (respondent info, factual basis, dates)
4. **Attach supporting evidence** from your evidence library
5. **Generate the complaint packet** with all required forms
6. **Review filing instructions** for submission method and address

### Cross-Reference to Filing Stacks

Each complaint type has an associated filing stack template that includes:
- Agency-specific complaint form
- Supporting affidavit/declaration
- Evidence exhibits with Bates numbers
- Cover letter (where required)
- Proof of service (where required)

---

## 14. Deadline Tracking Guide

LitigationOS calculates and tracks court deadlines based on Michigan Court Rules.

### Automatic Deadline Calculation

The DeadlineEngine computes deadlines from MCR rules:

| Rule | Deadline | Days |
|------|----------|------|
| MCR 2.108 | Answer/Response to Complaint | 21 days |
| MCR 2.119 | Serve Motion + Brief | 9 days before hearing |
| MCR 2.119 | Serve Response Brief | 5 days before hearing |
| MCR 2.119 | Serve Reply Brief | 3 days before hearing |
| MCR 7.212 | Appellant's Brief | 56 days after claim of appeal |
| MCR 7.212 | Appellee's Brief | 35 days after appellant's brief |
| MCR 7.212 | Reply Brief | 21 days after appellee's brief |
| MCR 7.302 | Application for Leave (MSC) | 42 days after COA decision |
| MCR 3.206 | Divorce (no children) | 60-day waiting period |
| MCR 3.206 | Divorce (with children) | 180-day waiting period |

### Weekend and Holiday Adjustment

All deadlines are automatically adjusted for:
- **Weekends** -- If a deadline falls on Saturday or Sunday, it moves to the next Monday
- **Michigan court holidays** -- New Year's Day, MLK Day, Presidents' Day, Memorial Day, Independence Day, Labor Day, Columbus Day, Veterans Day, Thanksgiving, Christmas

### Conflict Detection

The deadline engine checks for scheduling conflicts:
- Multiple deadlines on the same day
- Deadlines that fall during court closures
- Overlapping filing windows

### Tracking Workflow

1. **Create a case** -- Deadlines are auto-calculated from case type and filing dates
2. **View on Deadline Dashboard** -- See all deadlines with countdown timers
3. **View on Calendar** -- See deadlines in monthly calendar format
4. **Export ICS** -- Sync deadlines to your phone or email calendar
5. **Mark complete** -- Update deadline status as you file

---

## 15. Settings Configuration

Access settings via **Settings** in the main menu or sidebar.

### Jurisdiction Settings

| Setting | Default | Description |
|---------|---------|-------------|
| jurisdiction.state | MI | State code |
| jurisdiction.county | Muskegon | County name |
| jurisdiction.court | 14th Circuit | Court circuit/name |

### Display Settings

| Setting | Default | Description |
|---------|---------|-------------|
| pp.theme | dark | UI theme (dark/light) |
| pp.font_size | 12 | Font size in points |

### AI Settings

| Setting | Default | Description |
|---------|---------|-------------|
| llm.model | qwen2.5:7b | Ollama model for generation |
| llm.embedding_model | nomic-embed-text | Embedding model for RAG |
| i_enabled | 0 | Enable/disable AI features |
| ollama_url | http://localhost:11434 | Ollama server URL |

### Path Settings

| Setting | Description |
|---------|-------------|
| paths.data_dir | Main data directory (auto-detected) |
| paths.output_dir | Generated document output |
| paths.template_dir | Custom template directory |
| paths.model_dir | AI model storage |

---

## 16. AI / RAG Features

> **Optional** -- Requires [Ollama](https://ollama.com) installed locally.

### Setup

1. Install Ollama from https://ollama.com
2. Pull the required models:
   `ash
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text
   `
3. In LitigationOS settings, set i_enabled to 1
4. Verify the Ollama URL is correct (default: http://localhost:11434)

### Features

- **Document Drafting:** Generate first drafts of motions, briefs, and responses using local LLM
- **Semantic Search (RAG):** Search your evidence and court rules using natural language queries powered by ChromaDB embeddings
- **Legal Research Assistance:** Ask questions about Michigan court rules and get cited answers
- **Compliance Suggestions:** AI-powered suggestions for improving filing compliance
- **Text Classification:** Automatically classify filing types and urgency levels
- **Summarization:** Generate concise summaries of lengthy documents

### Privacy

All AI processing happens locally on your machine. No data is sent to external servers. Your case information never leaves your computer.

---

## 17. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Case |
| Ctrl+F | Search |
| Ctrl+S | Save current item |
| Ctrl+D | Open Dashboard |
| Ctrl+E | Evidence Manager |
| Ctrl+T | Timeline View |
| Ctrl+, | Settings |
| Escape | Close dialog / Cancel |
| F1 | Help |
| F5 | Refresh current view |

---

## Getting Help

- **Documentation:** See the docs/ directory for developer and Michigan court reference guides
- **Complaint Filing:** See [complaint_filing_guide.md](complaint_filing_guide.md) for agency-specific instructions
- **Issues:** Report bugs on the project's GitHub Issues page
- **Architecture:** See [DEVELOPER.md](DEVELOPER.md) for technical details
