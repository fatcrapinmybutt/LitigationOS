---
name: document-forge-supreme
description: "Use when generating any document — PDF, DOCX, PPTX, XLSX, court filings, reports, professional writing, copy editing, documentation architecture, templates, technical writing, README, and API documentation."
category: discipline
version: "2.0.0"
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
