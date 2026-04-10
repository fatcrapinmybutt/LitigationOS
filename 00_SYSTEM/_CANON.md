# _CANON.md — THE CANONICAL FILESYSTEM LAW OF LITIGATIONOS

> **This document is the single source of truth for file organization.**
> Every AI agent, every script, every human MUST obey this structure.
> Violation = drift = chaos. Enforce ruthlessly.

---

## THE 13 FOLDERS

```
C:\Users\andre\LitigationOS\
│
├── 00_SYSTEM/         Engine: brains, tools, engines, model, HYDRA
├── 01_EVIDENCE/       Raw evidence: exhibits, police, photos, scans
├── 02_AUTHORITY/      Legal corpus: MCR, MCL, MRE, case law, forms
├── 03_COURT/          Court records: orders, judgments, docket, transcripts
├── 04_ANALYSIS/       Intelligence: timelines, impeachment, contradictions
├── 05_FILINGS/        Filing packages: F01-F10, drafts, court-ready
├── 06_DATA/           Structured data: databases, CSV, JSON, JSONL
├── 07_CODE/           Source code: apps, CLI, backend, UI
├── 08_MEDIA/          Visual: images, photos, screenshots, scans
├── 09_REFERENCE/      Documentation: guides, READMEs, benchbooks
├── 10_EXTERNAL/       Third-party: imported tools, libraries
├── 11_ARCHIVES/       Historical: backups, old versions, superseded
├── 12_WORKSPACE/      Active WIP: temp, logs, drafts, experiments
│
├── _CANON.md          THIS FILE — the law
├── README.md          Project overview
├── pyproject.toml     Python project config
├── requirements.txt   Python dependencies
├── mcp.json           MCP server config
├── .gitignore         Git ignore rules
│
├── .git/              (hidden) Version control
├── .github/           (hidden) Skills, workflows
├── .agents/           (hidden) Agent definitions
├── .claude/           (hidden) Claude config
├── .venv/             (hidden) Python virtual environment
├── .vscode/           (hidden) VS Code settings
├── .eide/             (hidden) EIDE config
├── .learnings/        (hidden) Learnings store
└── .superpower-copilot/ (hidden) Superpower config
```

**NOTHING ELSE exists at root level.** Every file belongs in one of the 13 folders.
Only config files (pyproject.toml, mcp.json, requirements.txt, .gitignore) stay at root.

---

## FOLDER SPECIFICATIONS

### 00_SYSTEM — The Engine
**What goes here:** Core system code, brains, engines, tools, scripts, HYDRA protocol, local model, inference engine, automation scripts, MCP server code, context loader, skill index.
**What does NOT go here:** Evidence, filings, analysis reports, images, third-party code.
**Internal structure:** KEEP AS-IS — already well-organized with 74 subdirectories.
**Protected:** YES — never reorganize internals without explicit instruction.

### 01_EVIDENCE — Raw Evidence
**What goes here:** Police reports, exhibits, evidence photos, document scans, witness statements, AppClose messages, correspondence, forensic data, PPO evidence, FOIA responses.
**What does NOT go here:** Analysis OF evidence (→ 04_ANALYSIS), court orders (→ 03_COURT), filing drafts (→ 05_FILINGS).
**Sub-directories:**
- `CUSTODY/` — Lane A custody evidence
- `HOUSING/` — Lane B Shady Oaks evidence
- `POLICE/` — Police reports (all departments)
- `EXHIBITS/` — Court exhibits (Bates-numbered)
- `FORENSIC/` — Digital forensics, metadata analysis
- `CORRESPONDENCE/` — Emails, letters, AppClose messages
- `PHOTOS/` — Evidence photographs
- `PPO/` — PPO-related evidence

**Rule:** If a file IS evidence, it goes here. Period. Format doesn't matter.

### 02_AUTHORITY — Legal Corpus
**What goes here:** Michigan Court Rules (MCR), Michigan Compiled Laws (MCL), Michigan Rules of Evidence (MRE), case law, benchbooks, SCAO forms, court forms, judicial canons, legal reference documents.
**What does NOT go here:** Our own legal analysis (→ 04_ANALYSIS), court filings (→ 05_FILINGS).
**Sub-directories:**
- `MCR/` — Michigan Court Rules full text
- `MCL/` — Michigan Compiled Laws
- `MRE/` — Michigan Rules of Evidence
- `CASE_LAW/` — Case citations and opinions
- `BENCHBOOKS/` — Judicial benchbooks
- `FORMS/` — SCAO forms, court form templates
- `CANONS/` — Code of Judicial Conduct

**Rule:** Authority = THE LAW ITSELF. Not our interpretation of it.

### 03_COURT — Court Records
**What goes here:** Court orders (issued by judges), judgments, docket entries, hearing transcripts, PPO orders, criminal case records, FOC reports, custody evaluations.
**What does NOT go here:** Our filings (→ 05_FILINGS), evidence we submit (→ 01_EVIDENCE).
**Sub-directories:**
- `ORDERS/` — Court orders from all courts
- `JUDGMENTS/` — Judgments and dispositions
- `DOCKET/` — Docket entries and case registers
- `TRANSCRIPTS/` — Hearing and deposition transcripts
- `PPO/` — PPO orders and modifications
- `CRIMINAL/` — People v. Pigors records
- `FOC/` — Friend of Court reports and recommendations

**Rule:** If the COURT produced it, it goes here. If WE produced it, → 05_FILINGS.

### 04_ANALYSIS — Intelligence
**What goes here:** Analysis reports, timelines, impeachment packages, contradiction analysis, adversary intelligence, judicial analysis, damages calculations, best interest factor analysis, red team reports, wave analysis, strategic reports.
**What does NOT go here:** Raw evidence (→ 01_EVIDENCE), the law itself (→ 02_AUTHORITY).
**Sub-directories:**
- `TIMELINES/` — Chronological analysis, event sequences
- `IMPEACHMENT/` — Impeachment packages and cross-exam prep
- `CONTRADICTIONS/` — Contradiction detection results
- `ADVERSARY/` — Opposition intelligence (Watson, Barnes)
- `JUDICIAL/` — Judge McNeill analysis, bias metrics
- `DAMAGES/` — Damages calculations and exhibits
- `BEST_INTEREST/` — MCL 722.23 factor analysis
- `RED_TEAM/` — Vulnerability analysis and counter-arguments
- `WAVES/` — Wave analysis reports (wave2-wave19)

**Rule:** If it's OUR ANALYSIS of something, it goes here.

### 05_FILINGS — Filing Packages
**What goes here:** All court filings we create or plan to file: motions, briefs, complaints, proposed orders, certificates of service, cover sheets, exhibit indices.
**What does NOT go here:** Evidence supporting filings (→ 01_EVIDENCE), court responses to our filings (→ 03_COURT).
**Sub-directories:**
- `F01_EMERGENCY_TRO/` — Emergency TRO package
- `F02_SHADY_OAKS/` — Shady Oaks complaint package
- `F03_DISQUALIFICATION/` — MCR 2.003 disqualification
- `F04_FEDERAL_1983/` — §1983 federal complaint
- `F05_MSC_ORIGINAL/` — MSC original action
- `F06_JTC_COMPLAINT/` — Judicial Tenure Commission
- `F07_CUSTODY_MOD/` — Custody modification
- `F08_PPO_TERMINATION/` — PPO termination
- `F09_COA_BRIEF/` — Court of Appeals brief
- `F10_COA_EMERGENCY/` — COA emergency motion
- `DRAFTS/` — Work-in-progress filing drafts
- `TEMPLATES/` — Filing templates and shells
- `COURT_READY/` — Finalized, ready-to-file documents

**Rule:** If we're FILING it with a court, it goes here.

### 06_DATA — Structured Data
**What goes here:** ALL databases (.db, .sqlite), CSV datasets, JSONL atom files, JSON exports, XLSX spreadsheets, data manifests.
**What does NOT go here:** Source code (→ 07_CODE), documents meant for human reading (→ 09_REFERENCE).
**Internal structure:** FLAT — no subdirectories. File names are descriptive enough.
**Key files:**
- `litigation_context.db` — Primary 695MB database (CANONICAL)
- `authority_brain.db`, `narrative_brain.db`, etc. — 7 brain databases
- `master_index.db`, `cross_brain_index.db` — Index databases
- All CSV, JSONL, JSON data exports

**Rule:** If it's STRUCTURED DATA meant for machine consumption, it goes here.

### 07_CODE — Source Code
**What goes here:** Application source code, CLI tools, backend services, UI code, build scripts, launcher scripts, batch files, PowerShell scripts.
**What does NOT go here:** System engine code (→ 00_SYSTEM), third-party code (→ 10_EXTERNAL).
**Sub-directories:**
- `APPS/` — Desktop and web applications
- `CLI/` — Command-line tools
- `BACKEND/` — Backend services
- `UI/` — User interface code
- `LAUNCHERS/` — Launch scripts and .spec files
- `SCRIPTS/` — Utility scripts (.bat, .ps1)

**Rule:** If WE wrote it and it's executable code, it goes here. If it's the core engine → 00_SYSTEM. If someone else wrote it → 10_EXTERNAL.

### 08_MEDIA — Visual Media
**What goes here:** Images, screenshots, photos, webp files, scanned documents (visual), PDFs that are primarily visual/scanned.
**What does NOT go here:** Evidence photos (→ 01_EVIDENCE/PHOTOS), court document scans (→ 03_COURT).
**Internal structure:** FLAT.

**Rule:** If it's a visual file that ISN'T evidence or court records, it goes here. GitLens screenshots, UI mockups, diagrams, etc.

### 09_REFERENCE — Documentation
**What goes here:** README files, documentation, guides, how-tos, benchbook reference, legal reference library, project documentation.
**What does NOT go here:** Analysis reports (→ 04_ANALYSIS), filing drafts (→ 05_FILINGS).
**Internal structure:** FLAT.

**Rule:** If it's documentation meant to TEACH or EXPLAIN, it goes here.

### 10_EXTERNAL — Third-Party
**What goes here:** Imported repositories, third-party libraries, downloaded tools, external resources.
**What does NOT go here:** Our code (→ 07_CODE), our system (→ 00_SYSTEM).
**Sub-directories:** One per project/tool (e.g., `ripgrep-master/`, `capstone-develop/`).

**Rule:** If SOMEONE ELSE wrote it and we imported it, it goes here.

### 11_ARCHIVES — Historical
**What goes here:** Old backups, superseded files, dedup trash, junk, old versions, anything no longer actively needed but kept for reference.
**What does NOT go here:** Active evidence (→ 01_EVIDENCE), current filings (→ 05_FILINGS).
**Internal structure:** FLAT.

**Rule:** If it's OLD, SUPERSEDED, or EXPENDABLE, it goes here.

### 12_WORKSPACE — Active WIP
**What goes here:** Temporary files, pipeline logs, run outputs, session workspace, experiments, test data, import staging.
**What does NOT go here:** Completed analysis (→ 04_ANALYSIS), finalized filings (→ 05_FILINGS).
**Sub-directories:**
- `TEMP/` — Temporary processing files
- `LOGS/` — Pipeline and system logs
- `RUNS/` — Pipeline run outputs
- `SESSIONS/` — Session state and workspace

**Rule:** If it's TEMPORARY or IN-PROGRESS, it goes here. When done → move to final destination.

---

## THE PLACEMENT ALGORITHM

Given any file, determine its home using this decision tree:

```
Is it core system/engine code?           → 00_SYSTEM
Is it raw evidence?                      → 01_EVIDENCE
Is it a law/rule/statute/form?           → 02_AUTHORITY
Was it produced BY the court?            → 03_COURT
Is it our analysis/intelligence?         → 04_ANALYSIS
Is it a filing we created?               → 05_FILINGS
Is it structured data (db/csv/json)?     → 06_DATA
Is it our source code?                   → 07_CODE
Is it a visual/image file?              → 08_MEDIA
Is it documentation/reference?           → 09_REFERENCE
Was it written by a third party?         → 10_EXTERNAL
Is it old/superseded/backup?             → 11_ARCHIVES
Is it temporary/in-progress?             → 12_WORKSPACE
```

**Ambiguity resolution:** When a file could go in multiple places, use the FIRST match in the list above. Evidence trumps data. Court records trump analysis. The list is priority-ordered.

---

## ROOT-LEVEL FILES ALLOWED

ONLY these files may exist at the repository root:

| File | Purpose | Protected |
|------|---------|-----------|
| `_CANON.md` | This document — the filesystem law | YES |
| `README.md` | Project overview | YES |
| `pyproject.toml` | Python project configuration | YES |
| `requirements.txt` | Python dependencies | YES |
| `mcp.json` | MCP server configuration | YES |
| `.gitignore` | Git ignore rules | YES |
| `litigationos.config.jsonc` | LitigationOS config | YES |
| `master.code-workspace` | VS Code workspace | YES |

**Everything else at root MUST be sorted into the 13 folders.**

---

## NAMING CONVENTIONS

1. **Top-level folders:** `NN_NAME` — 2-digit prefix, ALL_CAPS, underscore separator
2. **Sub-directories:** `ALL_CAPS` — no number prefix, short descriptive name
3. **Index files:** `_INDEX.md` — underscore prefix marks it as system/meta file
4. **Files:** Preserve original names. Do not rename evidence or court documents.
5. **No spaces** in folder names. Underscores only.
6. **Max depth:** Root → Folder → Subfolder → File (3 levels max)

---

## ENFORCEMENT

Every AI agent session MUST:
1. Check `_CANON.md` exists at root
2. Never create new top-level directories
3. Place new files in the correct canonical folder
4. Update `_INDEX.md` in the target folder when adding files
5. Never move files from 00_SYSTEM without explicit instruction
6. Report any files found at root level that shouldn't be there

---

*Created: 2026-03-28 | Version: 1.0 | Authority: ABSOLUTE*
*This structure is permanent. It does not change without explicit human instruction.*
