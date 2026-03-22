---
name: document-forge-supreme
description: "Use when generating any document — PDF, DOCX, PPTX, XLSX, court filings, reports, professional writing, copy editing, documentation architecture, templates, technical writing, README, and API documentation."
category: discipline
version: "3.0.0-APEX-OMEGA"
triggers:
  - document
  - pdf
  - docx
  - template
  - report
  - filing-format
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: "Pigors v Watson"
dependencies: []
metadata:
  model: opus
  forged_from: 14
  forge_date: 2026-03-12
---

# DOCUMENT-FORGE-SUPREME — Elite Composite Skill

> Forged from 14 individual skills into one supreme composite.
> Sources: pdf, docx, pptx, xlsx, writing-skills, beautiful-prose, copy-editing, docs-architect, documentation-templates, technical-blog-writing, readme, api-documenter, api-documentation-generator, case-study-writing

## When to Apply

Activate this skill for ANY work related to:
- **PDF Generation**: reportlab, fpdf2, weasyprint, vector graphics, multi-page layouts
- **DOCX Generation**: python-docx, styles, tables, headers/footers, templates
- **Spreadsheet Generation**: openpyxl, formulas, conditional formatting, charts
- **Presentation Generation**: python-pptx, slide layouts, charts, animations
- **Professional Writing**: clarity, structure, audience, tone, persuasion
- **Copy Editing**: grammar, style, consistency, fact-checking, proofreading
- **Documentation Architecture**: information architecture, navigation, versioning
- **Technical Writing**: tutorials, how-tos, reference docs, API documentation
- **README & Project Docs**: README templates, changelogs, contributing guides

---

## Decision Tree

```
ENTRY: Document generation task received
│
├─ Q1: What type of document?
│   ├─ Court filing (motion, brief, petition) → BRANCH A
│   ├─ PDF report (non-court) → BRANCH B
│   ├─ DOCX document → BRANCH C
│   ├─ Spreadsheet (XLSX) → BRANCH D
│   ├─ Presentation (PPTX) → BRANCH E
│   └─ Technical documentation → BRANCH F
│
├─ BRANCH A: Court Filing
│   ├─ Step 1: Identify lane (A-F) and case number
│   ├─ Step 2: Select SCAO form template (query court_forms.db)
│   ├─ Step 3: Resolve ALL variables from litigation_context.db (DB-first!)
│   ├─ Step 4: Apply MCR formatting (caption, margins, spacing, font)
│   ├─ Step 5: Add certificate of service + pro se signature block
│   ├─ Step 6: Run pre-filing-qa agent for GO/NO-GO
│   └─ OUTPUT: Filing-ready court document (PDF)
│   ⚠️  NOTE: For complex filings, prefer OMEGA-LITIGATION-SUPREME M4
│
├─ BRANCH B: PDF Report
│   ├─ Step 1: Choose engine (reportlab, fpdf2, or weasyprint)
│   ├─ Step 2: Define layout (headers, footers, page numbers)
│   ├─ Step 3: Populate with data (DB queries, not placeholders)
│   ├─ Step 4: Add charts/tables if needed
│   └─ OUTPUT: Professional PDF report
│
├─ BRANCH C: DOCX Document
│   ├─ Step 1: Use python-docx with template
│   ├─ Step 2: Apply styles (headings, body, tables)
│   ├─ Step 3: Add headers/footers
│   └─ OUTPUT: Formatted Word document
│
├─ BRANCH D: Spreadsheet
│   ├─ Step 1: Use openpyxl
│   ├─ Step 2: Use FORMULAS, not hardcoded values (critical!)
│   ├─ Step 3: Add conditional formatting and charts
│   ├─ Step 4: Run recalc.py to verify formulas
│   └─ OUTPUT: Dynamic Excel spreadsheet
│
├─ BRANCH E: Presentation
│   ├─ Step 1: Use python-pptx with slide layouts
│   ├─ Step 2: Keep text concise, use visuals
│   └─ OUTPUT: Professional PowerPoint deck
│
└─ BRANCH F: Technical Documentation
    ├─ Step 1: Discovery (analyze codebase structure)
    ├─ Step 2: Structure (chapter hierarchy, progressive disclosure)
    ├─ Step 3: Write (overview → details, include rationale)
    └─ OUTPUT: Structured technical documentation
```

## Output Contract

```yaml
output:
  type: enum [document, code, config]
  format: pdf_docx_xlsx_pptx_or_markdown
  required_fields:
    - summary: string            # What document was generated
    - document_type: string      # PDF, DOCX, XLSX, PPTX, or Markdown
    - files_changed: list[str]   # All files created or modified
    - quality_score: float       # 0.0-1.0 self-assessment
  quality_gates:
    - no_hallucinated_names: boolean     # All party names from Verified Identity table
    - no_unresolved_placeholders: boolean # DB queried before any placeholder
    - mcr_formatting_compliant: boolean  # Michigan Court Rules followed (if court doc)
    - lane_verified: boolean             # Correct case lane and number
    - certificate_of_service: boolean    # Present with correct addresses (if filing)
    - signature_block: boolean           # Pro se block present (if filing)
    - statistics_traceable: boolean      # Every number tied to a DB query
```

---

## §1. PDF Generation

> reportlab, fpdf2, weasyprint, vector graphics, multi-page layouts

## §2. DOCX Generation

> python-docx, styles, tables, headers/footers, templates

## §3. Spreadsheet Generation

> openpyxl, formulas, conditional formatting, charts

### CRITICAL: Use Formulas, Not Hardcoded Values
*Source: xlsx*

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

### ❌ WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### ✅ CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

### Recalculating formulas
*Source: xlsx*

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `recalc.py` script to recalculate formulas:

```bash
python recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Works on both Linux and macOS

## §4. Presentation Generation

> python-pptx, slide layouts, charts, animations

### Converting Slides to Images
*Source: pptx*

To visually analyze PowerPoint slides, convert them to images using a two-step process:

1. **Convert PPTX to PDF**:
   ```bash
   soffice --headless --convert-to pdf template.pptx
   ```

2. **Convert PDF pages to JPEG images**:
   ```bash
   pdftoppm -jpeg -r 150 template.pdf slide
   ```
   This creates files like `slide-1.jpg`, `slide-2.jpg`, etc.

Options:
- `-r 150`: Sets resolution to 150 DPI (adjust for quality/size balance)
- `-jpeg`: Output JPEG format (use `-png` for PNG if preferred)
- `-f N`: First page to convert (e.g., `-f 2` starts from page 2)
- `-l N`: Last page to convert (e.g., `-l 5` stops at page 5)
- `slide`: Prefix for output files

Example for specific range:
```bash
pdftoppm -jpeg -r 150 -f 2 -l 5 template.pdf slide  # Converts only pages 2-5
```

## §5. Professional Writing

> clarity, structure, audience, tone, persuasion

### Blog Post Structure
*Source: technical-blog-writing*

### The Ideal Structure

```markdown
# Title (contains primary keyword, states outcome)

[Hero image or diagram]

**TL;DR:** [2-3 sentence summary with key takeaway]

## §6. Copy Editing

> grammar, style, consistency, fact-checking, proofreading

### Code Style Guidelines
*Source: pptx*

**IMPORTANT**: When generating code for PPTX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

## §7. Documentation Architecture

> information architecture, navigation, versioning

## §8. Technical Writing

> tutorials, how-tos, reference docs, API documentation

### Documentation Process
*Source: docs-architect*

1. **Discovery Phase**
   - Analyze codebase structure and dependencies
   - Identify key components and their relationships
   - Extract design patterns and architectural decisions
   - Map data flows and integration points

2. **Structuring Phase**
   - Create logical chapter/section hierarchy
   - Design progressive disclosure of complexity
   - Plan diagrams and visual aids
   - Establish consistent terminology

3. **Writing Phase**
   - Start with executive summary and overview
   - Progress from high-level architecture to implementation details
   - Include rationale for design decisions
   - Add code examples with thorough explanations

## §9. README & Project Docs

> README templates, changelogs, contributing guides

### 1. README Structure
*Source: documentation-templates*

### Essential Sections (Priority Order)

| Section | Purpose |
|---------|---------|
| **Title + One-liner** | What is this? |
| **Quick Start** | Running in <5 min |
| **Features** | What can I do? |
| **Configuration** | How to customize |
| **API Reference** | Link to detailed docs |
| **Contributing** | How to help |
| **License** | Legal |

### README Template

```markdown
# Project Name

Brief one-line description.

### The Three Purposes of a README
*Source: readme*

1. **Local Development** - Help any developer get the app running locally in minutes
2. **Understanding the System** - Explain in great detail how the app works
3. **Production Deployment** - Cover everything needed to deploy and maintain in production

---

### README Structure
*Source: readme*

Write the README with these sections in order:

### 1. Project Title and Overview

```markdown
# Project Name

Brief description of what the project does and who it's for. 2-3 sentences max.

---

# APEX-OMEGA v3.0 MODULES — Evidence-Grounded Document Intelligence

> Upgrade from v2.0 to v3.0 APEX-OMEGA tier. The following modules transform document generation
> from template-filling to evidence-grounded, contradiction-powered, multi-court adaptive synthesis.
> Every document section is now DB-linked, citation-verified, and anti-hallucination-hardened.

---

## Module D1: Evidence-Grounded Document Generation

> Every document section MUST link to evidence_quotes (308,704 rows) or master_evidence_timeline (24,859 events).
> Auto-populate from litigation_context.db BEFORE using any placeholder.

### D1 Principle: DB-First Evidence Injection

Before writing ANY substantive paragraph in a court document, execute the appropriate evidence query:

```
ENTRY: Document section requires factual support
│
├─ Step 1: Identify the lane (A-F) and claim category
├─ Step 2: Run evidence retrieval query (see SQL patterns below)
├─ Step 3: Select top evidence quotes by relevance_score
├─ Step 4: Embed quotes with Bates references and source attribution
├─ Step 5: ONLY if Step 2 returns 0 rows → insert placeholder with retrieval instructions
└─ OUTPUT: Evidence-grounded paragraph with citations
```

### D1 SQL Patterns for Evidence Retrieval

```sql
-- For custody motions (Lane A: Best Interest / Parenting Time)
SELECT quote_text, source_file, page_number, bates_number, category
FROM evidence_quotes
WHERE lane = 'A' AND category IN ('custody', 'best_interest', 'parenting_time')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 20;

-- For federal §1983 complaints (Lane C: Constitutional Violations)
SELECT quote_text, source_file, page_number, bates_number, category
FROM evidence_quotes
WHERE lane IN ('A','D','E') AND category IN ('due_process', 'constitutional', 'rights_violation')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 30;

-- For PPO-related filings (Lane D)
SELECT quote_text, source_file, page_number, bates_number
FROM evidence_quotes
WHERE lane = 'D' AND category IN ('ppo', 'protection_order', 'domestic_violence', 'false_allegations')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 20;

-- For judicial misconduct filings (Lane E)
SELECT quote_text, source_file, page_number, bates_number
FROM evidence_quotes
WHERE lane = 'E' AND category IN ('judicial_misconduct', 'bias', 'ex_parte', 'due_process')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 25;

-- For appellate briefs (Lane F)
SELECT quote_text, source_file, page_number, bates_number
FROM evidence_quotes
WHERE lane = 'F' AND category IN ('appellate', 'standard_of_review', 'preserved_error')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 25;

-- For housing/Shady Oaks filings (Lane B)
SELECT quote_text, source_file, page_number, bates_number
FROM evidence_quotes
WHERE lane = 'B' AND category IN ('housing', 'habitability', 'lockout', 'title', 'property')
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 20;

-- Timeline events for narrative sections (any lane)
SELECT event_date, event_description, source_document, actors, lane
FROM master_evidence_timeline
WHERE lane = ? AND event_date BETWEEN ? AND ?
ORDER BY event_date ASC;

-- Cross-lane pattern evidence (Lane C convergence)
SELECT eq.quote_text, eq.source_file, eq.lane, eq.category
FROM evidence_quotes eq
WHERE eq.category IN ('retaliation', 'pattern', 'escalation', 'weaponization')
AND eq.is_duplicate = 0
ORDER BY eq.lane, eq.relevance_score DESC LIMIT 30;
```

### D1 Evidence Embedding Format

Every evidence-backed paragraph must follow this format:
```
[Substantive statement]. (Ex. [Bates#], [Source File], p. [Page].)
```

Example:
```
Defendant Watson denied Plaintiff parenting time on November 15, 2024, in direct
violation of the Court's October 3, 2024 order. (Ex. A-047, AppClose_Messages_Nov2024.pdf, p. 3.)
```

### D1 Placeholder Insertion Protocol (Last Resort Only)

If AND ONLY IF the evidence query returns 0 rows:
```
[EVIDENCE NEEDED: Query evidence_quotes WHERE lane='X' AND category='Y' returned 0 rows.
 Search filesystem: rg -l "keyword" C:\Users\andre\LitigationOS\03_EVIDENCE\
 Check: COMPLETE_FILING_DATA_SUMMARY.txt for alternate sources.
 If still missing: This is an ACQUISITION TASK — document must be obtained.]
```

---

## Module D2: IRAC Auto-Structuring Engine

> Auto-detect legal issue from document type, auto-retrieve rules, auto-apply facts, auto-conclude.
> Supports IRAC, CREAC, and TEC structural variants.

### D2 Auto-Detection Matrix

```
ENTRY: Filing type identified
│
├─ Motion to Compel → IRAC (single issue)
│   Issue: "Whether [party] must comply with [discovery request]"
│   Rule: MCR 2.313 + MCR 2.302(B)
│
├─ Motion for Summary Judgment → CREAC (multi-factor)
│   Conclusion: "[Party] is entitled to judgment as a matter of law"
│   Rule: MCR 2.116(C)(10) + substantive law
│
├─ Emergency Motion → IRAC (compressed)
│   Issue: "Whether immediate relief is required to prevent irreparable harm"
│   Rule: MCR 2.119(F)(2) + substantive law
│
├─ Appellate Brief → CREAC + TEC (fact statement)
│   Standard of Review: MCR 7.212(C)(7)
│
├─ §1983 Complaint → TEC (constitutional narrative) + IRAC per count
│   Theme: "Systematic deprivation of constitutional rights under color of law"
│
├─ JTC Complaint → TEC (pattern narrative)
│   Theme: "Pattern of judicial misconduct violating Canons 1, 2, 3"
│
├─ Contempt Motion → IRAC (element-by-element)
│   Issue: "Whether [party] willfully violated [specific order]"
│   Rule: MCR 3.606 elements
│
└─ Default: IRAC (safest structure for any filing type)
```

### D2 Auto-Rule Retrieval

```sql
-- Retrieve applicable rules from authority_master_index
SELECT authority_name, citation, rule_text, relevance_score
FROM authority_master_index
WHERE lane = ? AND category = ?
ORDER BY relevance_score DESC LIMIT 10;

-- Retrieve court rules from court_rules table
SELECT rule_number, rule_title, rule_text, effective_date
FROM court_rules
WHERE rule_number LIKE ?
ORDER BY rule_number;

-- Retrieve case law authorities
SELECT case_name, citation, holding, court, year
FROM authority_master_index
WHERE authority_type = 'case_law' AND lane = ?
AND category = ?
ORDER BY year DESC, relevance_score DESC LIMIT 15;
```

### D2 IRAC Template (Auto-Populated)

```
I. ISSUE
   [Auto-detected from motion type + lane assignment]
   "Whether [legal question framed from filing context]."

R. RULE
   [Auto-retrieved from authority_master_index WHERE lane = X AND category = Y]
   "[Rule statement with pinpoint citations]."
   See [Case Name], [Citation] ("[holding excerpt]").

A. APPLICATION
   [Auto-populated from evidence_quotes + master_evidence_timeline]
   Here, [factual application supported by (Ex. [Bates#], [Source], p. [Page])].
   [Additional fact]. (Ex. [Bates#], [Source], p. [Page].)

C. CONCLUSION
   [Generated conclusion with strength assessment]
   Strength: [HIGH/MEDIUM/LOW based on evidence density and authority quality]
   Therefore, [specific relief requested].
```

### D2 CREAC Template (For Complex Arguments)

```
C. CONCLUSION (Thesis)
   [Opening thesis: state position definitively]

R. RULE
   [Full legal standard with authority chain — primary + supporting cases]

E. EXPLANATION
   [Show how courts have applied rule in analogous cases]
   In [Case 1], the court held [holding]. [Citation].
   Similarly, in [Case 2], [holding]. [Citation].

A. APPLICATION
   [Apply rule to Pigors v Watson facts with record citations]
   Here, [fact supported by exhibit]. (Ex. [Bates#].)
   Unlike in [distinguishable case], here [distinguishing fact].

C. CONCLUSION (Restatement)
   [Restate conclusion with specific relief requested]
```

### D2 TEC Template (For Narrative Sections)

```
T. THEME
   [Establish narrative frame — what this case is really about]
   "This case is about [thematic statement grounded in evidence]."

E. EVIDENCE
   [Marshal facts in thematic order with record citations]
   On [date], [actor] [conduct]. (Ex. [Bates#], [Source], p. [Page].)
   [Date range pattern]. (Exs. [Bates range].)
   [Continuing harm]. (Ex. [Bates#].)

C. CONCLUSION
   [Draw factual inference supporting legal theory]
   "The evidence establishes [inference] requiring [relief]."
```

---

## Module D3: Contradiction-Powered Impeachment Sections

> Auto-query contradictions (2,930 contradictions, 31 impeachment chains) for cross-examination
> briefs and credibility challenges.

### D3 Contradiction Retrieval

```sql
-- Retrieve contradictions for a specific actor
SELECT c.contradiction_id, c.actor, c.statement_1, c.source_1,
       c.statement_2, c.source_2, c.severity, c.category
FROM contradictions c
WHERE c.actor LIKE ?
ORDER BY c.severity DESC, c.category;

-- Retrieve impeachment chains (linked contradictions)
SELECT ic.chain_id, ic.chain_name, ic.target_actor,
       ic.contradiction_count, ic.overall_severity, ic.summary
FROM impeachment_chains ic
WHERE ic.target_actor LIKE ?
ORDER BY ic.overall_severity DESC;

-- Get chain details with linked contradictions
SELECT ic.chain_id, c.contradiction_id, c.statement_1, c.source_1,
       c.statement_2, c.source_2, c.severity
FROM impeachment_chains ic
JOIN chain_contradictions cc ON ic.chain_id = cc.chain_id
JOIN contradictions c ON cc.contradiction_id = c.contradiction_id
WHERE ic.chain_id = ?
ORDER BY c.severity DESC;

-- Cross-reference contradiction → evidence_quote → exhibit
SELECT c.contradiction_id, c.statement_1, eq.quote_text, eq.bates_number,
       eq.source_file, eq.page_number
FROM contradictions c
JOIN evidence_quotes eq ON c.source_1 = eq.source_file
WHERE c.actor LIKE ?
ORDER BY c.severity DESC LIMIT 20;
```

### D3 Impeachment Section Template

For each impeachment target in a credibility-challenge document:

```
IMPEACHMENT OF [ACTOR NAME]

Contradiction #[N]: [Category]
  Claimed: "[Statement 1]" (Source: [Source 1], [Date])
  But:     "[Statement 2]" (Source: [Source 2], [Date])
  Impact:  [Severity: HIGH/MEDIUM/LOW]
  Exhibit: Ex. [Bates#], p. [Page]

Cross-Examination Question Sequence:
  Q1: "You stated [Statement 1], correct?" → Commit to statement
  Q2: "And that was on [Date] in [Context]?" → Pin to time/place
  Q3: "But isn't it true that [Statement 2]?" → Confront with contradiction
  Q4: "And this [Source 2] shows [the contradiction]?" → Exhibit confrontation
```

### D3 Integration with Document Types

| Document Type | Impeachment Usage | Section Placement |
|---|---|---|
| Cross-Examination Brief | Full chain per witness | Main body, witness-by-witness |
| Trial Brief | Summary of key contradictions | Statement of Facts |
| Motion for Sanctions | Pattern of dishonesty | Argument section |
| Appellate Brief | Credibility undermining | Application section of CREAC |
| §1983 Complaint | Bad faith evidence | Factual allegations |
| JTC Complaint | Judicial inconsistency | Pattern section |

---

## Module D4: Multi-Court Format Adapter

> Auto-detect court from lane assignment and apply correct formatting rules.

### D4 Court Detection & Format Selection

```
ENTRY: Lane assignment identified
│
├─ Lane A (Custody) → 14th Circuit Court, Muskegon County
│   Format: MCR 2.113 (state circuit court)
│   Case: 2024-001507-DC
│   Judge: Hon. Jenny L. McNeill
│   Filing: MiFile e-filing
│
├─ Lane B (Housing) → 14th Circuit Court, Muskegon County
│   Format: MCR 2.113 (state circuit court)
│   Case: 2025-002760-CZ
│   Filing: MiFile e-filing
│
├─ Lane C (Federal §1983) → U.S. District Court, W.D. Michigan
│   Format: FRCP + LCivR W.D. Mich.
│   Case: To be assigned
│   Filing: CM/ECF (PACER)
│
├─ Lane D (PPO) → 14th Circuit Court, Muskegon County
│   Format: MCR 2.113 + MCR 3.7xx (PPO-specific)
│   Case: 2023-5907-PP
│   Filing: MiFile e-filing
│
├─ Lane E (Judicial Misconduct) → Judicial Tenure Commission
│   Format: JTC complaint format (28-day rule)
│   Target: Hon. Jenny L. McNeill
│   Filing: Direct to JTC, Lansing
│
└─ Lane F (Appellate) → Michigan Court of Appeals / Supreme Court
    Format: MCR 7.212 (COA) / MCR 7.305 (MSC)
    Case: COA 366810
    Filing: MiFile e-filing
```

### D4 Format Specifications Per Court

#### Michigan State Court (Lanes A, B, D) — MCR 2.113
```
- Paper: 8.5" × 11"
- Margins: 1" minimum all sides
- Font: 12pt Times New Roman (or comparable serif)
- Spacing: Double-spaced body text
- Paragraphs: Consecutively numbered (Arabic numerals)
- Pages: Numbered bottom center
- Caption: MCR 2.113(C) format with court, case number, judge, parties
- Signature: Pro se block — name, address, phone, email, date
- Service: Certificate of Service on all parties
```

#### Federal Court (Lane C) — FRCP + LCivR W.D. Michigan
```
- Paper: 8.5" × 11"
- Margins: 1" top/bottom, 1.5" left, 1" right (LCivR check)
- Font: 14pt for body text (LCivR 5.7(a)), 12pt for footnotes
- Spacing: Double-spaced body text
- Paragraphs: Numbered
- Pages: Numbered bottom center
- Caption: FRCP format with district, division, case number
- Filing: CM/ECF electronic filing
- Signature: /s/ Andrew James Pigors (electronic signature)
- Certificate of Service: ECF service statement
```

#### Court of Appeals (Lane F) — MCR 7.212
```
- Page limit: 50 pages or 16,000 words (brief on appeal)
- Required sections: Table of Contents, Table of Authorities, Jurisdictional Statement,
  Questions Presented, Statement of Facts, Standard of Review, Argument, Relief Requested
- Appendix: MCR 7.212(H) — lower court orders, judgment, key transcript excerpts
- Cover: Color-coded per MCR 7.212(A)(2) — blue (appellant), red (appellee)
- Font: 12pt Times New Roman, double-spaced
```

#### Michigan Supreme Court (Lane F) — MCR 7.305
```
- Application for Leave: MCR 7.305(B) — concise statement of grounds
- Page limit: 50 pages (application)
- Required: Questions Presented, Statement of Facts, Argument for why leave should be granted
- Standard: Issue of significant public importance, COA clearly erred
```

#### JTC Complaint (Lane E) — Judicial Tenure Commission Format
```
- Letter format (not motion format)
- Addressed to: Judicial Tenure Commission, P.O. Box 30412, Lansing, MI 48909
- Content: Specific allegations with dates, supporting evidence references
- Standard: Misconduct, persistent failure to perform duties, conduct prejudicial to
  the administration of justice (Const. 1963 Art. 6, § 30)
- Include: Specific Canon violations (Michigan Code of Judicial Conduct)
- Supporting documents: Copies of orders, transcripts, evidence of bias
```

---

## Module D5: Hybrid Search Document Discovery

> Before drafting ANY document, auto-search for existing documents using hybrid FTS5 + sqlite-vec.
> Prevent duplicate creation. Reuse and improve prior work.

### D5 Pre-Drafting Search Protocol

```
ENTRY: Document generation task received
│
├─ Step 1: FTS5 search in litigation_context.db
│   SELECT doc_id, title, path, relevance FROM documents_fts
│   WHERE documents_fts MATCH '[filing type] [lane keywords]'
│   ORDER BY rank LIMIT 20;
│
├─ Step 2: Vector similarity search (if vec_evidence available)
│   SELECT rowid, distance FROM vec_evidence
│   WHERE embedding MATCH [query_vector]
│   ORDER BY distance LIMIT 10;
│
├─ Step 3: Filesystem search for existing filings
│   rg -l "[motion type]" C:\Users\andre\LitigationOS\01_FILINGS\ --type md --type txt
│   rg -l "[motion type]" C:\Users\andre\LitigationOS\GENERATED_FILINGS\ --type md --type txt
│   rg -l "[motion type]" C:\Users\andre\LitigationOS\COURT_READY\ --type md --type txt
│
├─ Step 4: Check filing_readiness table for existing packages
│   SELECT vehicle_name, status, completion_pct, last_updated
│   FROM filing_readiness
│   WHERE vehicle_name LIKE '%[filing type]%'
│   ORDER BY last_updated DESC;
│
├─ Decision:
│   ├─ Found exact match (>90% overlap) → UPDATE existing document
│   ├─ Found partial match (50-90%) → MERGE best content + improve
│   ├─ Found related but different → CROSS-REFERENCE for consistency
│   └─ Found nothing → CREATE new document (proceed with D1-D4)
│
└─ OUTPUT: Document creation/update decision with linked prior work
```

### D5 Deduplication Check

```sql
-- Check for existing filings of same type in same lane
SELECT d.doc_id, d.title, d.file_path, d.created_date, d.status
FROM documents d
WHERE d.lane = ? AND d.document_type = ?
ORDER BY d.created_date DESC LIMIT 5;

-- Check for similar content using FTS5
SELECT doc_id, title, snippet(documents_fts, 0, '<b>', '</b>', '...', 64) as preview
FROM documents_fts
WHERE documents_fts MATCH ?
ORDER BY rank LIMIT 10;
```

---

## Module D6: Sullivan v Gray Recording Authentication

> One-party consent doctrine: MCL 750.539c, Sullivan v Gray, 117 Mich App 476 (1982).
> Auto-generate authentication affidavit for recordings where Andrew was present.

### D6 Legal Foundation

**Michigan is a one-party consent state:**
- MCL 750.539c: It is lawful to record a private conversation if one party to the
  conversation consents to the recording.
- Sullivan v Gray, 117 Mich App 476 (1982): Established that one-party consent is
  sufficient under Michigan law. A participant in a conversation may record it without
  the knowledge or consent of the other participants.

### D6 Authentication Under MRE 901

**MRE 901(b)(1) — Testimony of witness with knowledge:**
The person who made the recording testifies that:
1. They were present and participated in the conversation
2. They activated the recording device
3. The recording is a fair and accurate representation of the conversation
4. The recording has not been altered

**MRE 901(b)(5) — Voice identification:**
A witness familiar with the speaker's voice identifies the voices on the recording.

### D6 Authentication Affidavit Template

```
STATE OF MICHIGAN
IN THE [COURT NAME]

AFFIDAVIT OF ANDREW JAMES PIGORS
AUTHENTICATING AUDIO/VIDEO RECORDING

I, Andrew James Pigors, being duly sworn, state:

1. I am the Plaintiff in the above-captioned matter.

2. I am over 18 years of age and competent to testify to the matters stated herein
   based on my personal knowledge.

3. On [DATE], I was present at [LOCATION] and participated in a conversation with
   [OTHER PARTY/PARTIES].

4. During this conversation, I activated a recording device with my knowledge and consent
   as a participant in the conversation, consistent with Michigan's one-party consent
   law, MCL 750.539c, and Sullivan v Gray, 117 Mich App 476 (1982).

5. The recording attached hereto as Exhibit [X] (Bates [NUMBER]) is a fair, accurate,
   and unaltered recording of the conversation that took place on [DATE].

6. I can identify the voices on the recording as:
   - My own voice (Andrew James Pigors)
   - [OTHER SPEAKER(S)] — whom I know personally and whose voice I recognize

7. The recording has not been edited, altered, spliced, or modified in any way since
   it was made.

8. I offer this recording under MRE 901(b)(1) (testimony of witness with knowledge)
   and MRE 901(b)(5) (voice identification).

______________________________
Andrew James Pigors, Pro Se
[ADDRESS]
[PHONE]
[EMAIL]

Subscribed and sworn to before me this ____ day of ____________, 20___.
______________________________
Notary Public, State of Michigan
My Commission Expires: ____________
```

### D6 Applicable Recordings for Pigors v Watson

| Recording | Date | Location | Participants | Authentication Status |
|---|---|---|---|---|
| Albert/Emily kitchen recording | Nov 2024 | Albert Watson residence | Andrew present + Emily Watson + Albert Watson | Requires D6 affidavit |
| AppClose co-parenting calls | Various 2024-2025 | Phone/AppClose platform | Andrew + Emily Watson | Platform metadata available + D6 affidavit |
| All calls Andrew participated in | Various | Various | Andrew + other party | D6 affidavit per recording |

### D6 Foundation Motion Template

When a recording is challenged, file a motion establishing foundation:
```
MOTION TO ADMIT [RECORDING] UNDER MRE 901

I. ISSUE
   Whether [Recording Description] is properly authenticated and admissible.

II. RULE
   MRE 901(b)(1) permits authentication by testimony of a witness with knowledge.
   MRE 901(b)(5) permits voice identification by any person familiar with the voice.
   Michigan is a one-party consent state. MCL 750.539c; Sullivan v Gray, 117 Mich App
   476, 482 (1982) ("a participant to a private conversation may record that
   conversation without the knowledge of the other participant").

III. APPLICATION
   [Auto-populated from D6 affidavit content + evidence_quotes for context]

IV. CONCLUSION
   The recording is properly authenticated under MRE 901 and admissible. It was
   lawfully obtained under Michigan's one-party consent law.
```

---

## APEX Quality Gate (v3.0 Addition)

All documents generated by document-forge-supreme v3.0 MUST pass these gates:

```yaml
apex_quality_gates:
  D1_evidence_grounded:
    - every_factual_paragraph_has_citation: boolean
    - evidence_quotes_queried_before_placeholder: boolean
    - bates_numbers_present_where_applicable: boolean

  D2_structure_verified:
    - correct_structure_selected: enum [IRAC, CREAC, TEC]
    - rules_retrieved_from_authority_master_index: boolean
    - facts_retrieved_from_evidence_quotes: boolean
    - conclusion_strength_assessed: boolean

  D3_contradictions_checked:
    - impeachment_chains_queried_for_credibility_sections: boolean
    - cross_exam_questions_generated_where_applicable: boolean

  D4_format_correct:
    - court_auto_detected_from_lane: boolean
    - formatting_rules_applied: boolean
    - caption_matches_court_requirements: boolean

  D5_dedup_verified:
    - existing_documents_searched_before_creation: boolean
    - no_duplicate_filing_created: boolean

  D6_recordings_authenticated:
    - sullivan_v_gray_affidavit_generated_where_needed: boolean
    - mre_901_foundation_established: boolean

  anti_hallucination:
    - no_fabricated_names: boolean
    - blacklist_checked: ["Jane Berry", "Patricia Berry", "91% alienation score",
                          "Tiffany Watson", "Lincoln David Watson", "Ron Berry Esq",
                          "Amy McNeill", "P35878"]
    - all_party_names_from_verified_table: boolean
    - all_statistics_traceable_to_sql_query: boolean
    - all_bar_numbers_verified_in_db: boolean
```
