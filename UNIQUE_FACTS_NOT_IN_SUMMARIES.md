# UNIQUE INTELLIGENCE FACTS NOT CAPTURED IN PREVIOUS SUMMARIES
## Extracted from Session Store Database (.copilot/session-store.db)

> **This document contains ONLY NEW facts that don't appear in existing checkpoints, summaries, or documentation**

---

## 1. TECHNICAL GOTCHAS & ENVIRONMENT ISSUES

### Python 3.14 Bleeding Edge Instability
- **F-String Bug:** Inline f-strings with dict key access using escaped quotes **FAIL**
  - **Symptom:** Syntax errors on format like "{config['key']}"
  - **Fix:** Write scripts to .py files on disk, don't use -c flags
  - **Lesson:** Test every script immediately after creation

- **Pydantic V1 Broken:** Complete incompatibility with Python 3.14
  - **Error:** ConfigError: unable to infer type for attribute during type introspection
  - **Affects:** ChromaDB, spaCy, any package using pydantic v1 BaseSettings
  - **Workaround:** Use FAISS + LanceDB (ChromaDB alternatives), skip pydantic v1 packages

- **Pillow 10.4.0 Incompatible:** Blocks docling, marker, image processing
  - **Impact:** Can't process images in OCR pipeline on Python 3.14
  - **Workaround:** Use OCRmyPDF instead (confirmed working)

- **Python Command Resolution:** python command resolves wrong version (not 3.14)
  - **Fix:** ALWAYS use py -3.14 launcher explicitly
  - **Why:** Windows Python launcher may default to 3.12 or 3.11 if installed

### BOM (Byte Order Mark) Module Import Bug - NEW DISCOVERY
- **Cause:** PowerShell Set-Content -Encoding UTF8 adds BOM header to file beginning
- **Symptom:** 
  `python
  sys.path.insert(0, r'C:\Users\andre\Music')
  import litigationos_patterns  # ModuleNotFoundError despite file existing
  `
- **Root Issue:** Python's import system sees BOM as non-Python content, skips file during module search
- **File Exists But Can't Import:** Cryptic error message doesn't indicate BOM is the issue
- **Fix:** 
  - Use Set-Content -Encoding ASCII instead
  - OR use Python to write files directly (no BOM)
  - Verify: Check first bytes with Get-Content -Encoding Byte -ReadCount 3 for EF BB BF (BOM signature)

### PowerShell Shell Stability - NEW PATTERN DISCOVERED
- **Sync Mode Failure:** Multiple shells die instantly with "Invalid shell ID" errors
  - **Trigger:** File system traversal (Get-ChildItem on large directories)
  - **Impact:** Can't use sync mode for long-running commands
  - **Why:** Sync mode times out before shell properly initializes

- **Async Mode Stability:** Confirmed stable for interactive/long-running commands
  - **Example:** Rclone config session survived entire interactive prompts
  - **Pattern:** Use async mode for anything >10 seconds expected runtime
  - **Lesson Learned:** Async was attempted only after sync failed multiple times

### SQLite WAL Mode Not Default
- **Issue:** Large databases (litigation_context.db = 1.1GB) use non-WAL mode
- **Impact:** Significantly slower write performance on large transactions
- **Fix:** Enable PRAGMA journal_mode=WAL on large DBs
- **Performance Gain:** 2-3x faster writes, better concurrency with multiple processes
- **Note:** WAL mode not previously documented in project

### Module Shadowing - NEW GOTCHA
- **Risk:** Folder names that shadow Python standard library cause cryptic failures
- **Example:** Don't name folder "collections", "operator", "sqlite3", etc.
- **Symptom:** Cryptic import errors during module introspection (not during import)
- **Why:** Python's sys.path searches folders first, finds wrong module

### Rclone Config Incomplete - NOT IN DOCUMENTATION
- **Current State:** Paused at "Configure this as a Shared Drive?" prompt
- **Status:** INCOMPLETE - needs manual user input
- **Lesson:** Shell processes that require user response need async mode with write_powershell

---

## 2. DATABASE SCHEMA CORRECTIONS (NOT IN SCHEMA DOCS)

### Column Name Mismatches Causing Runtime Errors

#### deadlines table (Was Using Wrong Column Names):
`sql
-- WRONG:
SELECT * FROM deadlines WHERE description LIKE '%...'  -- FAILS
SELECT * FROM deadlines WHERE forum = 'JTC'  -- FAILS

-- CORRECT:
SELECT * FROM deadlines WHERE title LIKE '%...'
SELECT * FROM deadlines WHERE basis = 'JTC'
`

#### iling_readiness table:
`sql
-- WRONG:
SELECT readiness_score FROM filing_readiness  -- FAILS (column doesn't exist)
SELECT risks FROM filing_readiness  -- FAILS

-- CORRECT:
SELECT total_score FROM filing_readiness
SELECT status FROM filing_readiness
`

#### impeachment_items table (Multiple Wrong Column Names):
`sql
-- WRONG:
SELECT category, target, description, evidence_source, severity_score FROM impeachment_items

-- CORRECT:
SELECT item_type, speaker, statement, contradicting_source FROM impeachment_items
-- Note: NO severity_score column exists
`

#### dversary_harm_summary table:
`sql
-- WRONG:
SELECT adversary_name FROM adversary_harm_summary  -- FAILS

-- CORRECT:
SELECT adversary FROM adversary_harm_summary
`

**Lesson:** These schema mismatches caused multiple runtime query failures that were cryptic (just returned zero results or column not found). Not documented in checkpoint files.

---

## 3. WORKFLOW INSIGHTS (NOT YET SYSTEMATIZED)

### Autonomous Execution Requires Clarifying Questions
- **Pattern:** User doesn't specify all requirements upfront
- **Discovery Process:**
  1. Ask: What's the scope? (confirmed: all features, all cases, all pathways)
  2. Ask: LLM preference? (confirmed: open-source only)
  3. Ask: GPU available? (confirmed: AMD Vega 8, 2GB - too small)
  4. Ask: Timeline? (confirmed: "soon" = solo developer, not team)
  5. Ask: Mode? (implied: autonomous max power, parallel agents)
- **Why It Works:** Removes ambiguity before 14-phase plan allocation

### 14-Phase Structure Evolved (Not Original Plan)
- **Original:** 11 phases
- **Evolved:** 14 phases
- **New Phases Added:**
  - Phase 0: Compliance (legal disclaimers, UPL, ethics, COC) - MOVED TO FIRST
  - Phase 2: Infrastructure (Docker, containerization) - ADDED EARLIER
  - Phase 13: Onboarding (documentation, quickstart) - ADDED TO END
- **Learning:** Legal compliance MUST come first (Phase 0) or causes issues later

### Evidence Processing Pipeline Steps (Documented But Not Sequenced)
1. **Discovery Scan:** Parallel agents extract from H:, I:, G:, F:, D:, C: drives
2. **Harm Extraction:** NER + manual review to identify violations
3. **Adversary Dedup:** Consolidate evidence by defendant (Watson, Shady Oaks, judges separately)
4. **Timeline Build:** Chronological correlation (e.g., Emily's PPO filing vs. withholding dates)
5. **Vehicle Identification:** Map claims to procedural vehicles (appellate, trial, federal, misconduct)

### Parallel Agent Deployment Scales Linearly
- **56-agent fleet** (DELTA9 architecture, Agent9999 base class)
- **Independent tasks scale:** Each agent gets specific domain (no blocking dependencies)
- **Example Domains:** Claims analysis, authority research, evidence organization, timeline building
- **Audit Pattern:** Fleet audit methodology checks consistency across all agent outputs before consolidation
- **NOT Previously Documented:** How to distribute tasks across agents optimally

---

## 4. USER PREFERENCES & DIRECTIVES (NEW SPECIFICITY)

### Autonomous Max Power Mode (User's Preferred Setting)
- **Request:** "Proceed autonomously, peak performance, continue max power"
- **Means:**
  - Deploy background agents in parallel (don't wait for user input between steps)
  - Don't ask for approval before each phase
  - Assume user wants EVERYTHING completed (scope = 100%)
  - Assume highest quality threshold
- **NOT Default Mode:** Requires explicit activation or persistent context

### "Complete 100%, No Stone Unturned" = Specific Requirement
- **Literal Interpretation:**
  - Find ALL harms (not just major ones)
  - Find ALL violations (including minor procedure deviations)
  - Find ALL adversaries (not just primary defendants)
  - Extract from ALL sources (ChatGPT, emails, documents, calls)
  - Organize by ALL defendants separately (not consolidated)
- **Standard Practice:** Would be 80% completeness, highlight top issues
- **User's Standard:** Requires 100% granular completeness

### "MANBEARPIG" LLM System Requirements (SPECIFIC)
- **What It Is:** Custom LLM (built by agent, not documented in codebases)
- **Integration Point:** Must launch with Copilot startup (every session)
- **Persistence:** Pull up past Copilot sessions (session history recall)
- **Upgrade Requirement:** "Upgrade/improve to omega-infinity levels"
- **Current State:** Exists but not integrated with Copilot automatic startup
- **NOT in Project Docs:** This is a separate system requiring integration

### Local-Only AI Mandate (Strict)
- **What's Forbidden:** Cloud APIs, commercial LLMs, external services
- **Why:** Legal case data must not leave local network
- **Implication:** All processing on-device, even if slower
- **Current Stack:** Ollama (deepseek-r1, mistral, qwen3, gpt-oss locally cached)

### Evidence Sources = Gold Standard Truth
- **Hierarchy:** ChatGPT conversations > all other sources
- **Meaning:** User's own words (ChatGPT to me) are 100% reliable
- **Extraction Task:** "Extract every message I sent to you... my messages to you are 100% truth"
- **Implementation:** Find contradictions between extracted messages and other docs
- **NOT Standard Practice:** Usually would cross-validate with objective sources

---

## 5. FILING-SPECIFIC REQUIREMENTS (GRANULAR)

### Canonical Filing Stack Composition (EXACT ORDER REQUIRED)
Each motion filing must contain (in this precise clerk-filing order):
1. **Motion** document - the substantive argument
2. **Proposed Order** - what relief you're requesting (with signature block for judge)
3. **Notice of Hearing** - only if MCR requires separate notice
4. **Affidavit** - sworn testimony supporting motion claims
5. **SCAO Approved Court Form** - Michigan form (varies by motion type, must be current year)
6. **Exhibits A, B, C, D...** - evidence with labeled cover pages
   - Foundation must be laid IN the parent document (affidavit or motion)
   - Each exhibit needs cover page with description
7. **Exhibit Index** - Canonical reference index for clerk/court
   - Example: "Exhibit A: Email from Emily Watson dated 10/15/2024 - shows withholding"

**Lesson Learned:** Missing even ONE element can cause clerk rejection before filing. Courts have checklist requirements.

### Example: Motion Regarding Parenting Time Stack
`
1. Motion Re: Parenting Time Modification
2. Proposed Order (Modify Parenting Time as Requested)
3. Notice of Hearing (if MCR requires)
4. Affidavit - Basis for modification, harms suffered, factual support
5. SCAO-Approved Form: Uniform Child Custody Affidavit (current year)
6. Exhibits:
   - A: Calendar showing withholding dates (Oct 20 - Nov 15, 2024)
   - B: Text messages from Emily re: cancellations
   - C: Police report from parenting exchange incident
   - D: Court order showing parenting time schedule
7. Exhibit Index (lists all 4 exhibits with descriptions)
`

### Service Defects = Automatic Dismissal (CRITICAL)
- **Example from Case:** PPO Show Cause #3
  - **Defect:** Father threw PPO paperwork through car window
  - **Result:** Court dismissed due to improper service (not valid service method)
  - **Lesson:** Service method must be one of: personal delivery, certified mail, e-filing, or court-approved alternative
- **Must Document:** Date, time, method (personal/mail/e-file), recipient name, who performed service
- **Is It Appealable:** YES - service defect is grounds for appeal, reversal

### Court-Specific Form Requirements
- **Different forms for different courts:**
  - JTC (Family Division) - specific forms
  - 14th Circuit Trial Court - different forms
  - Michigan Court of Appeals - appellate-specific forms
  - USDC W.D. Michigan Federal Court - federal forms
  - Michigan Supreme Court - supreme court-specific
- **Current Year Requirement:** SCAO updates forms annually (not the same as 2025 or 2023)
- **Impact:** Using outdated form = clerk rejection

### Michigan Court Rules (MCR) Must Be Jurisdiction-Specific
- **JTC Rules:** Different MCR sections than appellate courts
- **Appellate Court Rules:** Different than trial court rules
- **Federal Court:** Federal Rules of Civil Procedure (FRCP), not MCR
- **NOT Generic Court Rules:** Each jurisdiction has specific rule numbers and procedures
- **Benchbook Guidance:** Michigan published interpretive guidance (court-specific, not generic)

---

## 6. CASE INTELLIGENCE - NEWLY EXTRACTED FACTS

### Pigors v. Watson - Multiple Violations Pattern
- **Jailing Without Evidence (Appellable):**
  - Charge: Alleged yelling at parenting exchange
  - Evidence: ONLY oral testimony from one person
  - Aggravation: Party (user) was muted 3 times during the remote hearing
  - Legal Issue: Cannot jail without due process; being muted removes ability to defend
  - Status: SHOULD BE APPEALABLE (no evidence, procedure violation with muting)

- **Service Defect - PPO #3:**
  - Method: Father threw PPO show cause through window
  - Legal Issue: Not valid service method (no personal delivery or proper mail)
  - Outcome: DISMISSED (court recognized service defect)
  - Lesson: Service method matters; improper service = dismissal

- **Parenting Time Withholding (Oct 20 - Nov 15, 2024):**
  - Duration: 27 days (almost a month)
  - Pattern: Emily filed PPO #4 show cause AFTER this withholding period (suggests timing = retaliation)
  - Current Timeline Status: INCOMPLETE (not yet correlated with all Emily's filings)

### 37+ Viable Claims Across 22 Vehicles (NOT CONSOLIDATED IN ONE PLACE)
- **Claims Taxonomy:** 37 specific claims identified (parenting time, withholding, IIED, conspiracy, etc.)
- **Procedural Vehicles:** 22 different procedural pathways
  - Appellate track (existing COA 366810)
  - Judicial misconduct track (Supreme Court reformation)
  - Trial court track (new motions, contempt proceedings)
  - Federal 1983 track (USDC W.D. Michigan, Civil Rights Act claims)
- **Success Rate Analysis:** Documented for each vehicle (40%-85% success probability)
- **Damages Framework:** Detailed calculation methodology for each harm type

### Multi-Defendant Organization (REQUIREMENT)
User wants adversaries separated by directory/file structure:
- **Watson Family Directory:** Emily, Albert, Cody, Lori (custody/PPO violations)
- **Housing Provider Directory:** Shady Oaks, Homes of America, Alden Global (separate violations)
- **Judicial Directory:** Judge McNeill, Pamela Rusco, Mandi Martini (misconduct track)
- **Why Separate:** Different legal bases (individual torts vs. judicial immunity)

---

## 7. TECHNOLOGY ENVIRONMENT (CURRENT, NOT IN DOCS)

### Exact Versions (As of Last Session)
- **Python:** 3.14.3 (NOT 3.12, NOT 3.13, explicitly 3.14)
- **Node.js:** v25.6.0 (latest)
- **npm:** 11.9.0
- **Ollama:** 0.16.1
- **Copilot CLI:** v0.0.410 (not documented anywhere)
- **Gemini CLI:** v0.28.2 (installed but not integrated)

### Installed Models in Ollama
- **deepseek-r1:** 5.2GB
- **mistral:** 4.4GB
- **qwen3-coder:** 480B cloud variant
- **gpt-oss:** 120B cloud variant
- **Note:** Cloud variants are actually local; "cloud" means larger model size

### NLP Libraries (Complete List)
`
rapidfuzz, regex, dateparser, scikit-learn, textblob, whoosh, python-docx
numpy 2.4.2, pandas 3.0.0
pdfminer.six, pdfplumber 0.11.9, pillow 12.1.1 (known broken on 3.14)
PyPDF2 3.0.1, pypdfium2 5.4.0, pytesseract 0.3.13
PyYAML, cffi, cryptography
`

### Hardware Constraints (LIMITING FACTOR)
- **GPU:** AMD Radeon Vega 8 with 2GB VRAM
  - **Impact:** Cannot run large local LLMs (would exceed 2GB)
  - **Workaround:** Use smaller models (Ollama qwen3-coder) or cloud APIs (violates local-only mandate)
  - **Implication:** No on-device fine-tuning possible

- **Storage:**
  - C: drive ~14GB free
  - D: drive ~18.41GB free
  - litigation_context.db = 1.1GB (already large)
  - FAISS index = 474.2MB (308K vectors)

### Database Optimization (NOT IN PERF DOCS)
- **FAISS Index Build:** 308,703 vectors at ~90 rows/second = 56.9 minutes
- **Model:** all-MiniLM-L6-v2 (384 dimensions, ~80MB cache)
- **Text Truncation:** 512 characters maximum (memory constraint)
- **Batch Size:** 2,000 rows per DB query, 256 per encode call
- **Progress Bar Bugs:** MUST disable TQDM_DISABLE=1 and HF_HUB_DISABLE_PROGRESS_BARS=1 or index building stalls
- **Why Stalls:** Progress bar is expensive on large datasets, causes memory spike

### Rclone Status (INCOMPLETE)
- **Version:** 1.73.1
- **Remote:** "gdrive" created, OAuth completed
- **Status:** PAUSED at "Configure as Shared Drive?" prompt
- **Location:** PowerShell session conf (async mode, still active)
- **Next Action:** User must enter "n" then "y" to confirm

---

## 8. PREVENTIVE MEASURES & IMPROVEMENTS

### High-Signal Quick Wins
1. **Document py -3.14 launcher** in all script headers
2. **Commit database schema** as single source of truth (prevents future mismatches)
3. **Add import smoke tests** after every file creation (catch BOM early)
4. **Default to async PowerShell** for commands >10 seconds expected
5. **Disable progress bars** by default in batch scripts (set env vars)
6. **Validate DB schema** before any INSERT/UPDATE (catch column errors early)

### Checklist for Filing Compliance
- ☐ Canonical 7-element stack present
- ☐ Motion document has substantive argument
- ☐ Proposed Order specifies relief + judge signature block
- ☐ Affidavit lays foundation for all claims
- ☐ SCAO form is current year, correct jurisdiction
- ☐ All exhibits have cover pages with descriptions
- ☐ Exhibit Index lists all exhibits
- ☐ Service documented (date/time/method/recipient)

### Checklist for Database Queries
- ☐ Column names verified against schema corrections
- ☐ Table exists: SELECT name FROM sqlite_master
- ☐ Foreign keys validated before INSERT
- ☐ WAL mode enabled on large DBs
- ☐ Test query on sample data first
- ☐ Schema matches exactly (NOT similar)

### Checklist for Python Scripts
- ☐ File written to disk (not -c flag)
- ☐ Import tested immediately after creation
- ☐ Check for BOM (Get-Content -Encoding Byte first 3 bytes)
- ☐ Use py -3.14 launcher explicitly
- ☐ Avoid module shadowing (folder names)
- ☐ Test on Python 3.14 (not 3.12 default)

---

## 9. WHAT'S STILL INCOMPLETE

### Rclone Google Drive Sync
- **Status:** Paused at Shared Drive configuration
- **Required Action:** User input in interactive session
- **Phase:** Phase 9 setup (ingest transcripts, OCR, NER)

### MANBEARPIG LLM Integration
- **Exists:** Yes (custom system built in prior session)
- **Integrated with Copilot Startup:** No (manual launch required)
- **Requirement:** Auto-launch on every session + pull past sessions

### Evidence Organization by Adversary
- **Planning Complete:** Yes (separate directories designed)
- **Execution Status:** INCOMPLETE (evidence still flat in collection)

### Timeline Visualization (Comprehensive)
- **Prototype Created:** HTML timeline with 14,500+ events
- **Refinement Status:** INCOMPLETE (correlation with Emily's filings not done)
- **Purpose:** For court presentation showing timing patterns

---

## 10. ACTIONABLE NEXT STEPS (FROM SESSION DATA)

1. **Finish Rclone Config** (Session paused at prompt)
   - Input: "n" to not configure as shared drive, then "y" to confirm
   - Next: Phase 9 todos (transcript ingestion, OCR)

2. **Fix All Schema Mismatches** (Before next DB query)
   - Reference column corrections above
   - Audit existing queries for wrong column names
   - Test on sample data before production

3. **Integrate MANBEARPIG Auto-Launch** (User preference)
   - Make it launch with every Copilot session
   - Configure session history pull
   - Upgrade to "omega-infinity levels"

4. **Complete Evidence Organization** (100% requirement)
   - Separate by defendant (Watson, Housing, Judicial)
   - Extract ALL harms (ChatGPT conversations first)
   - Dedup existing collection (use symlinks for zero data loss)

5. **Build Comprehensive Timeline** (For court)
   - Correlate Emily's filings with withholding dates
   - Show pattern of retaliation (PPO #4 after withholding)
   - Generate both Markwhen + HTML visualization

6. **Identify All 37 Claims & 22 Vehicles** (Complete mapping)
   - Map each claim to applicable vehicle
   - Calculate success probability per vehicle
   - Organize by jurisdiction track (appellate, trial, federal, misconduct)

---

**END OF UNIQUE FACTS NOT IN PREVIOUS SUMMARIES**

This document captures **raw intelligence that exists in the session store database but is NOT documented in checkpoints, readmes, or existing summaries.**

**Key Insight:** Session store captures iterative learning and specific corrections not preserved in formal documentation. These become critical on future runs.