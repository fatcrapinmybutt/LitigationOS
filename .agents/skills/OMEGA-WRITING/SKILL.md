---
name: OMEGA-WRITING
description: >-
  Comprehensive writing skill for LitigationOS covering Michigan court filing
  format (caption blocks, verification, certificate of service), motion practice
  (MCR 2.119 compliance, 17+ motion types), appellate writing (COA/MSC brief
  format), technical documentation (README, API docs, architecture), case
  narratives (evidence-backed, DB-sourced), report generation (dashboards,
  filing readiness, gap analysis), persuasive writing (15 techniques, IRAC,
  CREAC, TEC frameworks), and anti-hallucination safeguards (every stat
  DB-traceable, every name from verified party table). Invoke for ANY
  document generation, legal writing, technical docs, or narrative task.
category: writing
version: "2.0.0"
triggers:
  - docs
  - README
  - spec
  - report
  - wiki
  - documentation
  - legal writing
  - brief
  - motion
  - filing
  - narrative
  - technical writing
  - case summary
  - persuasion
  - IRAC
  - appellate
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies:
  - litigation_context.db
  - evidence_quotes
  - claims
  - docket_events
  - deadlines
metadata:
  tier: 4
  fused_skills: 17
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# ✍️ OMEGA-WRITING — Precision Document Forge

> **Every word filed with the court carries the weight of law. Every fabricated
> statistic is potential perjury. Every misnamed party undermines credibility.**
> This skill forges court-ready documents from verified evidence, DB-sourced
> facts, and battle-tested legal frameworks — with zero hallucination tolerance.

---

## Forged from 17 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|-------------------|
| 1 | michigan-litigation-writer | Michigan court filing format and rules |
| 2 | document-forge-supreme | High-volume document generation |
| 3 | beautiful-prose | Clear, compelling narrative voice |
| 4 | legal-advisor | Legal strategy and argumentation |
| 5 | litigation-brief-writer | Brief structure and persuasion |
| 6 | litigation-motion-practice | 17+ motion types and MCR compliance |
| 7 | litigation-appeal-brief-engine | COA/MSC appellate brief format |
| 8 | litigation-complaint-drafter | Complaint and petition drafting |
| 9 | create-readme | README.md generation |
| 10 | se-technical-writer | Technical documentation standards |
| 11 | wiki-page-writer | Wiki and knowledge base content |
| 12 | wiki-architect | Documentation architecture |
| 13 | technical-blog-writing | Technical content creation |
| 14 | plan-writing | Strategic plan documentation |
| 15 | postmortem-writing | Incident and analysis reports |
| 16 | copy-editing | Proofreading and style consistency |
| 17 | writing-skills | Core writing craft and style |

---

## When to Apply

- **Drafting a motion** — any of 17+ motion types with MCR 2.119 compliance
- **Writing an appellate brief** — COA or MSC format with proper sections
- **Generating a case narrative** — evidence-backed chronological summary
- **Creating technical documentation** — README, API docs, architecture docs
- **Producing a report** — filing readiness, evidence coverage, gap analysis
- **Writing persuasive arguments** — IRAC, CREAC, TEC frameworks
- **Drafting a complaint or petition** — caption block, allegations, prayer for relief
- **Composing verification or certificate of service** — sworn statements
- **Any document requiring party names** — use VERIFIED TABLE ONLY
- **Any document citing statistics** — every number must trace to a DB query

---

## Decision Tree

```
Writing task received
│
├─ Is it a court filing? ──────────────────────────────── → W1 or W2 or W3
│   ├─ Motion? → W2: Motion Practice (MCR 2.119)
│   ├─ Appellate brief? → W3: Appellate Writing (COA/MSC)
│   ├─ Complaint/petition? → W1: Legal Document Writing
│   ├─ Response/reply? → W2: Motion Practice
│   └─ ALL filings → W8: Anti-Hallucination check MANDATORY
│
├─ Is it technical docs? ─────────────────────────────── → W4: Technical Docs
│   ├─ README? → Standard template with install/usage/API
│   ├─ API docs? → Endpoint documentation with examples
│   ├─ Architecture? → System design with diagrams
│   └─ Inline comments? → Minimal, purposeful only
│
├─ Is it a narrative? ────────────────────────────────── → W5: Case Narratives
│   ├─ Chronological? → Timeline with evidence citations
│   ├─ Thematic? → Organized by legal issue
│   └─ ALL narratives → W8: Anti-Hallucination check
│
├─ Is it a report? ───────────────────────────────────── → W6: Report Generation
│   ├─ Filing readiness? → Readiness scores with gaps
│   ├─ Evidence coverage? → Coverage matrix per claim
│   ├─ Gap analysis? → Missing evidence identification
│   └─ Dashboard? → Metrics with traceable queries
│
├─ Is it persuasive? ────────────────────────────────── → W7: Persuasive Writing
│   ├─ Court argument? → IRAC/CREAC/TEC framework
│   ├─ Strategic memo? → Analysis with recommendations
│   └─ ALL persuasion → ground every claim in evidence
│
└─ ALWAYS (every document) ───────────────────────────── → W8: Anti-Hallucination
    ├─ Party names from verified table? ✓
    ├─ Statistics from DB query? ✓
    ├─ Citations verified? ✓
    └─ No fabricated evidence? ✓
```

---

## W1: Legal Document Writing — Michigan Court Format

### Caption Block Template (14th Circuit)

```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW JAMES PIGORS,
        Plaintiff,                      Case No. 2024-001507-DC

v.                                      Hon. Jenny L. McNeill

EMILY A. WATSON,
        Defendant.
________________________________________/
```

### Mandatory Filing Components

| Component | Required By | Notes |
|-----------|------------|-------|
| **Caption** | MCR 2.113(C) | Full case style, case number, judge name |
| **Body** | MCR 2.113(A) | Numbered paragraphs, clear allegations |
| **Verification** | MCR 2.114(A) | Signed under penalty of perjury |
| **Certificate of Service** | MCR 2.107 | Method, date, recipient with address |
| **Proposed Order** | MCR 2.119(A)(2) | For motions — required with every motion |

### Verification Statement

```
VERIFICATION

I, Andrew James Pigors, declare under the penalty of perjury that the
statements contained in the foregoing [DOCUMENT TYPE] are true and correct
to the best of my knowledge, information, and belief.

Date: _______________          ________________________________
                               Andrew James Pigors, Plaintiff
                               1977 Whitehall Road, Lot 17
                               North Muskegon, MI 49445
                               (231) 903-5690
                               andrewjpigors@gmail.com
```

### Certificate of Service Template

```
CERTIFICATE OF SERVICE

I hereby certify that on [DATE], I served a true copy of the foregoing
[DOCUMENT NAME] upon:

    Emily A. Watson
    2160 Garland Drive
    Norton Shores, MI 49441

by [METHOD: first-class mail, postage prepaid / personal service /
e-filing notification / electronic mail].

                               ________________________________
                               Andrew James Pigors, Plaintiff
```

### Legal Writing Frameworks

| Framework | Structure | Best For |
|-----------|----------|---------|
| **IRAC** | Issue → Rule → Application → Conclusion | Standard legal analysis |
| **CREAC** | Conclusion → Rule → Explanation → Application → Conclusion | Persuasive briefs |
| **TEC** | Theme → Evidence → Conclusion | Narrative arguments |

### Filing Format Rules
- **Double-spaced** body text (court requirement)
- **1-inch margins** on all sides
- **Times New Roman 12pt** or equivalent (check local rules)
- **Numbered paragraphs** in complaints and motions
- **Page numbers** on every page except caption page
- **Footer**: Case No. [number] — [Document Type]

---

## W2: Motion Practice — 17+ Motion Types

### MCR 2.119 Requirements

Every motion MUST contain:
1. **Notice of Hearing** — date, time, location (if oral argument scheduled)
2. **Motion** — the request itself with legal basis
3. **Brief in Support** — legal argument (may be combined with motion)
4. **Proposed Order** — what you want the court to sign
5. **Certificate of Service** — proof of service on opposing party

### Motion Types Available

| # | Motion Type | MCR | Lane |
|---|------------|-----|------|
| 1 | Motion to Dismiss | 2.116(C) | A, B, D |
| 2 | Motion for Summary Disposition | 2.116(C)(10) | A, B |
| 3 | Motion to Compel Discovery | 2.313 | A, B, D |
| 4 | Motion for Contempt | 3.606 | A, D |
| 5 | Motion to Disqualify Judge | 2.003 | E |
| 6 | Motion for Change of Venue | 2.222 | A, B |
| 7 | Motion for Default Judgment | 2.603 | B |
| 8 | Motion for Protective Order | 2.302(C) | A, D |
| 9 | Motion for Temporary Relief | 3.207 | A |
| 10 | Motion to Modify Custody | MCL 722.27 | A |
| 11 | Motion to Modify Parenting Time | MCL 722.27a | A |
| 12 | Motion for Sanctions | 2.114(D)-(E) | A, B, E |
| 13 | Motion to Amend | 2.118 | A, B |
| 14 | Motion for Reconsideration | 2.119(F) | A, B, D, E |
| 15 | Motion to Set Aside Judgment | 2.612 | A, B |
| 16 | Emergency Motion (Ex Parte) | 2.119(B) | A, D |
| 17 | Motion for Stay Pending Appeal | 7.209 | F |

### Motion Body Structure

```markdown
## I. STATEMENT OF ISSUES PRESENTED
[One or more issues in question form]

## II. CONTROLLING AUTHORITY
[Key statutes, court rules, and case law]

## III. STATEMENT OF FACTS
[Chronological facts with evidence citations]
[Every fact must reference specific evidence: Exhibit A, DB record, testimony]

## IV. ARGUMENT
[IRAC analysis for each issue]
[Connect facts to law with evidence support]

## V. RELIEF REQUESTED
[Specific, actionable relief — what you want the court to do]
```

### Brief Page Limits (MCR 2.119)
- **Motion brief**: No specific page limit in MCR 2.119 (but be concise)
- **Response brief**: Filed within 21 days of service (MCR 2.119(A)(2))
- **Reply brief**: Filed within 7 days of response (MCR 2.119(A)(2))
- **Appellate briefs**: See W3 for COA/MSC limits

---

## W3: Appellate Writing — COA & MSC Format

### Court of Appeals (COA) Brief Format

```markdown
CLAIM OF APPEAL / APPLICATION FOR LEAVE TO APPEAL

I.   STATEMENT OF JURISDICTION
     [Basis for appellate jurisdiction — MCR 7.203 / 7.205]

II.  STATEMENT OF QUESTIONS PRESENTED
     [Each issue in question form, with short answer]

III. STATEMENT OF FACTS
     [Record-based facts with lower court record citations]
     [Format: (Record, p. XX) or (Tr., p. XX)]

IV.  ARGUMENT
     [Standard of review for each issue]
     [CREAC analysis with record citations]

V.   RELIEF REQUESTED
     [Specific appellate relief — reverse, remand, modify]
```

### COA Brief Requirements
- **Page limits**: 50 pages (brief), 10 pages (reply) — MCR 7.212
- **Record citations**: Every factual assertion must cite the lower court record
- **Standard of review**: State explicitly for each issue
  - De novo (legal questions)
  - Clear error (factual findings)
  - Abuse of discretion (discretionary rulings)
- **Preservation**: Show issue was raised below (or argue plain error)

### MSC Application Format

```markdown
APPLICATION FOR LEAVE TO APPEAL

I.   ORDER APPEALED AND RELIEF SOUGHT
II.  QUESTIONS PRESENTED
III. GROUNDS FOR GRANTING APPLICATION
     [Why this case meets MSC's discretionary review criteria]
IV.  STATEMENT OF FACTS
V.   ARGUMENT
VI.  CONCLUSION AND RELIEF
```

### MSC-Specific Rules
- Must show COA decision conflicts with another COA decision or MSC precedent
- Or presents a significant constitutional question
- Or involves an issue of major public significance
- Page limits: 50 pages — MCR 7.305(B)

### Appellate Citation Format
```
Michigan Court of Appeals:
  Smith v Jones, ___ Mich App ___; ___ NW3d ___ (2024)
  Smith v Jones, unpublished per curiam of the Court of Appeals,
    issued [date] (Docket No. XXXXXX)

Michigan Supreme Court:
  Smith v Jones, ___ Mich ___; ___ NW3d ___ (2024)

Federal:
  Smith v Jones, ___ F.4th ___ (6th Cir. 2024)
  Smith v Jones, ___ F Supp 3d ___ (WD Mich 2024)
```

---

## W4: Technical Documentation — Clear and Purposeful

### README.md Template

```markdown
# Project Name

One-paragraph description of what this does and why it matters.

## Installation

\`\`\`bash
pip install -e ".[dev]"
\`\`\`

## Quick Start

\`\`\`python
from module import MainClass
result = MainClass.do_thing(input)
\`\`\`

## Architecture

Brief description with reference to architecture docs.

## Testing

\`\`\`bash
python -m pytest tests/ -q
\`\`\`

## Contributing

Guidelines for contributing.
```

### Code Documentation Rules
- **Inline comments**: Minimal and purposeful — explain WHY, not WHAT
- **Docstrings**: Required for public functions/classes, optional for private
- **Type hints**: Use Python typing for all public APIs
- **No comment novels**: If code needs a paragraph of explanation, refactor the code

### Architecture Documentation
- System diagrams using ASCII art or Mermaid
- Data flow descriptions with input/output specifications
- Component interaction maps
- Decision records for non-obvious architectural choices

### API Documentation
- Endpoint description with method and path
- Request/response schemas with examples
- Error codes and handling
- Authentication requirements (local-only for LitigationOS)

---

## W5: Case Narratives — Evidence-Backed Storytelling

### Purpose
Generate chronological or thematic narratives that are grounded in evidence
from `litigation_context.db` and referenced documents. Every assertion MUST
be traceable to a specific evidence item.

### Narrative Structure

```markdown
## Chronological Narrative: [Topic]

### Background
[Context — who, what, when, where, established with citations]

### [Date/Period 1]: [Event Description]
[Factual account with evidence citations]
- Evidence: [exhibit_id] — [description] (DB: evidence_quotes.id = XXX)
- Supporting: [document_path] — [relevant excerpt]

### [Date/Period 2]: [Event Description]
[Continue chronologically...]

### Impact and Consequences
[Connect events to legal claims with evidence support]
```

### Evidence Citation Format

```markdown
Internal citation (for work product):
  (Exhibit A-001, Bates #PIG-00123, DB: evidence_quotes WHERE id = 456)

Filing citation (for court documents):
  (Exhibit A, attached hereto)
  (See Plaintiff's Exhibit 1, p. 3)
```

### Narrative Rules
- **Every factual assertion** needs an evidence citation
- **Chronological accuracy** — verify dates against DB records
- **No speculation** — if something is inferred, label it as inference
- **No emotional language** in fact sections — save persuasion for argument sections
- **Child = L.D.W.** — initials only, every reference
- **Verify names** against the party identity table before writing

### DB Queries for Narrative Building

```sql
-- Get timeline events for a case lane
SELECT event_date, event_type, description, source_document
FROM docket_events
WHERE vehicle_name = 'lane_A_custody'
ORDER BY event_date;

-- Get evidence quotes supporting a claim
SELECT quote_text, source_file, page_number, relevance_score
FROM evidence_quotes
WHERE claim_id = 'X'
ORDER BY relevance_score DESC;

-- Get all claims for a lane
SELECT claim_id, claim_type, status, supporting_evidence_count
FROM claims
WHERE vehicle_name = 'lane_A_custody';
```

---

## W6: Report Generation — Data-Driven Dashboards

### Filing Readiness Report

```markdown
# Filing Readiness Report — [Date]

## Summary
| Lane | Filing | Readiness | Gaps | Blockers |
|------|--------|-----------|------|----------|
| A | Motion to Modify Custody | 78% | 3 | 1 |
| B | Motion for Default | 92% | 1 | 0 |

## Detailed Gap Analysis
### Lane A: Motion to Modify Custody
- ✅ Caption block — complete
- ✅ Statement of facts — 12 evidence items linked
- ⚠️ GAP: Need 2 more exhibits for best interest factors
- ❌ BLOCKER: Certificate of service pending — need Emily's current address

## Evidence Coverage Matrix
[Matrix showing which claims have sufficient evidence support]

## Recommendations
[Prioritized next steps to reach filing readiness]
```

### Evidence Coverage Report

```sql
-- Query for evidence coverage per claim
SELECT
    c.claim_id,
    c.claim_type,
    COUNT(eq.id) as evidence_count,
    CASE
        WHEN COUNT(eq.id) >= 5 THEN 'STRONG'
        WHEN COUNT(eq.id) >= 3 THEN 'ADEQUATE'
        WHEN COUNT(eq.id) >= 1 THEN 'WEAK'
        ELSE 'NONE'
    END as coverage_level
FROM claims c
LEFT JOIN evidence_quotes eq ON c.claim_id = eq.claim_id
GROUP BY c.claim_id, c.claim_type
ORDER BY evidence_count ASC;
```

### Report Rules
- **Every number must come from a DB query** — include the query in report metadata
- **Never round up** — if the count is 47, say 47, not "nearly 50"
- **Date-stamp every report** — reports are point-in-time snapshots
- **Diff against previous report** — show what changed since last report

---

## W7: Persuasive Writing — 15 Techniques

### Persuasion Framework Arsenal

| # | Technique | Description | Use When |
|---|-----------|------------|----------|
| 1 | **Primacy** | Put strongest argument first | Opening briefs |
| 2 | **Recency** | End with memorable conclusion | Closing arguments |
| 3 | **Rule of Three** | Group arguments in threes | Any persuasive section |
| 4 | **Contrast** | Juxtapose opposing positions | Rebuttal briefs |
| 5 | **Narrative Arc** | Tell a story with conflict/resolution | Statement of facts |
| 6 | **Authority Anchoring** | Lead with strongest authority | Argument sections |
| 7 | **Concession & Pivot** | Acknowledge weakness, then redirect | Weak point mitigation |
| 8 | **Quantification** | Use specific numbers over vague claims | Damages, frequency |
| 9 | **Pattern Evidence** | Show recurring behavior | Custody/contempt motions |
| 10 | **Timeline Compression** | Show rapid escalation | Emergency motions |
| 11 | **Best Interest Focus** | Frame everything through child welfare | Custody proceedings |
| 12 | **Judicial Economy** | Show efficiency of granting relief | Dispositive motions |
| 13 | **Burden Shifting** | Establish burden, show it's met | Summary disposition |
| 14 | **Cumulative Impact** | Build evidence weight incrementally | Complex fact patterns |
| 15 | **Credibility Contrast** | Highlight reliability differences | Witness credibility |

### Ethos / Pathos / Logos Balance

```
COURT BRIEFS (formal):
  Logos: 60% — legal authority, statutory analysis, case law
  Ethos: 25% — credibility, consistency, professionalism
  Pathos: 15% — child welfare impact, fairness, equity

EMERGENCY MOTIONS:
  Pathos: 40% — immediate harm, urgent need
  Logos: 40% — legal basis, standard met
  Ethos: 20% — credibility of emergency claim

APPELLATE BRIEFS:
  Logos: 70% — standard of review, record citations, legal error
  Ethos: 20% — preservation, procedural compliance
  Pathos: 10% — just outcome, policy implications
```

### Judge-Specific Calibration (Hon. Jenny L. McNeill)
- Review past rulings for linguistic and reasoning patterns
- Identify preferred citation style and argument structure
- Note which types of arguments have succeeded/failed
- Adapt tone: formal but direct, evidence-heavy, precedent-focused
- **NEVER fabricate judicial tendencies** — base only on documented rulings

---

## W8: Anti-Hallucination Writing — The Truth Fortress

### Purpose
This is the MOST CRITICAL module. Past sessions fabricated party names
("CPS records [VERIFY — check actual CPS records for count]"), and pseudo-scientific scores ("documented pattern of parental alienation").
These appeared in 60+ files and could constitute perjury if filed. This module
ensures zero hallucination in every generated document.

### Verified Party Identity Table (ONLY SOURCE OF TRUTH)

| Role | Name | Details |
|------|------|---------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 |
| **Child** | L.D.W. | Initials ONLY per MCR 8.119(H) — NEVER full name |
| **Judge** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division |
| **Emily's Former Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC — WITHDREW |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's boyfriend. No bar number. No "Esq." EVER. |

### HALLUCINATION KILL LIST (these NEVER EXISTED)

```
❌ "CPS records [VERIFY — check actual CPS records for count]"  — Fabricated statistic. Check DB for actual count.
❌ "documented pattern of parental alienation"  — Pseudo-scientific fabrication. No such metric.
❌ "Emily Ann Watson"      — Wrong middle name. Correct: Emily A. Watson.
❌ "Emily M. Watson"       — Wrong middle initial. Correct: Emily A. Watson.
❌ "Tiffany"               — Not the defendant. Correct: Emily A. Watson.
❌ "Amy McNeill"           — Wrong first name. Correct: Hon. Jenny L. McNeill.
```

### Pre-Generation Verification Protocol

Before generating ANY document, verify:

```
□ 1. PARTY NAMES — Every name from verified party table above
       If name unknown → insert [UNKNOWN — VERIFY]
       NEVER guess a name

□ 2. BAR NUMBERS — Query litigation_context.db
       If not in DB → leave blank
       NEVER fabricate a bar number

□ 3. CASE NUMBERS — From verified lane table
       Lane A: 2024-001507-DC
       Lane B: 2025-002760-CZ
       Lane D: 2023-5907-PP
       Lane F: COA 366810

□ 4. STATISTICS — Run DB query, record the query
       Before citing ANY count or number:
         SELECT COUNT(*) FROM [table] WHERE [condition]
       Document the query alongside the statistic

□ 5. EVIDENCE — Verify existence in DB
       Before citing ANY evidence:
         SELECT * FROM evidence_quotes WHERE id = X
       If not found → do NOT cite it

□ 6. DATES — Cross-reference with docket_events
       Before citing ANY date:
         SELECT * FROM docket_events WHERE event_date = 'YYYY-MM-DD'
       If not found → mark [DATE — VERIFY]

□ 7. CHILD REFERENCE — L.D.W. only
       Search generated text for child's full name
       Replace ALL instances with "L.D.W."
```

### The DB-First Rule (ABSOLUTE)

```
The database has hundreds of tables and millions of rows of REAL DATA.
Do NOT insert a placeholder if the data might be in the DB.

BEFORE inserting [ANDREW_REQUIRED] or [INSERT] or [ATTACH]:
  1. Query litigation_context.db for the data
  2. Search filesystem (rg, fd, grep) across all 6 drives
  3. Check COMPLETE_FILING_DATA_SUMMARY.txt
  4. Check QUICK_REFERENCE_FILING_PLACEHOLDERS.txt
  5. ONLY if ALL FOUR return nothing → insert placeholder with specific
     instructions on where the data might be found
```

### Statistic Traceability Template

When citing a statistic in any document, attach this metadata:

```markdown
<!-- STAT-TRACE
  Statistic: "47 documented interference incidents"
  Query: SELECT COUNT(*) FROM evidence_quotes
         WHERE claim_type = 'parenting_time_interference'
         AND vehicle_name = 'lane_A_custody'
  Result: 47
  Run date: 2026-03-21
  Table: evidence_quotes
-->
```

For dashboards and reports, include traceability in a metadata section at
the end of the document.

---

## Cross-Module Integration Patterns

### W1 + W2 + W8: Complete Motion Package
```
Motion drafting initiated
  → W8: Verify all party names from table
  → W8: Query DB for all statistics needed
  → W1: Generate caption block with correct case style
  → W2: Draft motion body (issue, authority, facts, argument, relief)
  → W8: Verify every evidence citation exists in DB
  → W1: Add verification statement
  → W1: Add certificate of service
  → W2: Draft proposed order
  → W8: Final hallucination sweep
  → Output: Complete motion package ready for filing
```

### W5 + W7 + W8: Persuasive Case Narrative
```
Narrative requested
  → W8: DB-source all facts and dates
  → W5: Build chronological framework with evidence citations
  → W7: Apply persuasion techniques (primacy, pattern evidence, contrast)
  → W8: Verify every statistic is DB-traceable
  → W8: Verify child referred to as L.D.W. only
  → W7: Calibrate ethos/pathos/logos balance for target audience
  → Output: Evidence-backed persuasive narrative
```

### W3 + W8: Appellate Brief
```
Appellate brief requested
  → W8: Verify all party names and case numbers
  → W3: Identify standard of review for each issue
  → W3: Draft statement of questions presented
  → W5: Build statement of facts from lower court record
  → W3: Draft argument with record citations
  → W8: Verify every record citation (Tr., p. XX) exists
  → W8: Final hallucination sweep
  → W3: Format per COA/MSC requirements
  → Output: Court-compliant appellate brief
```

### W4 + W6: Technical Report Generation
```
Report or documentation requested
  → W6: Identify report type and required metrics
  → W6: Run all DB queries for statistics
  → W8: Attach query traceability to each metric
  → W4: Format with clear structure (headers, tables, code blocks)
  → W6: Include recommendations and next steps
  → Output: Data-driven report with full traceability
```

---

## LitigationOS-Specific Writing Invariants

These rules apply to EVERY document generated by this skill:

1. **NEVER fabricate party names** — verified table is the ONLY source
2. **NEVER fabricate bar numbers** — query DB or leave blank
3. **NEVER fabricate evidence statistics** — run the query, cite the query
4. **NEVER use child's full name** — L.D.W. only (MCR 8.119(H))
5. **Ronald Berry is NON-ATTORNEY** — no "Esq.", no bar number, ever
7. **DB-first before ANY placeholder** — search DB, filesystem, reference files
8. **Every stat traces to a query** — table name + WHERE clause documented
9. **No rounding up** — 47 is 47, not "nearly 50" or "approximately 50"
10. **No synthetic scores** — "91% alienation" is pseudo-scientific fabrication
11. **Verify dates against docket_events** — don't guess hearing dates
12. **Caption block accuracy** — case number, judge name, party names all verified
13. **Co-authored-by trailer** on commits that include generated documents
14. **Append-only** — never overwrite a filed document, create new version

---

## Document Quality Checklist (Run Before EVERY Output)

```
╔════════════════════════════════════════════════════════════════╗
║          OMEGA-WRITING — PRE-OUTPUT QUALITY GATE               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  IDENTITY VERIFICATION:                                        ║
║  □ Plaintiff = "Andrew James Pigors" (not Andrew J., not AJP)  ║
║  □ Defendant = "Emily A. Watson" (not Emily Ann, not Tiffany)  ║
║  □ Child = "L.D.W." (NEVER full name)                          ║
║  □ Judge = "Hon. Jenny L. McNeill" (not Amy McNeill)           ║
║  □ Ronald Berry = NON-ATTORNEY (no Esq., no bar number)        ║
║                                                                ║
║  STATISTICAL INTEGRITY:                                        ║
║  □ Every number traces to a DB query                           ║
║  □ No rounded-up counts                                        ║
║  □ No synthetic/fabricated scores                              ║
║  □ No extrapolated statistics                                  ║
║  □ Query + result documented for each stat                     ║
║                                                                ║
║  EVIDENCE INTEGRITY:                                           ║
║  □ Every cited exhibit exists in DB                            ║
║  □ Every date verified against docket_events                   ║
║  □ No fabricated evidence items                                ║
║  □ Citation format consistent throughout                       ║
║                                                                ║
║  LEGAL COMPLIANCE:                                             ║
║  □ MCR formatting requirements met                             ║
║  □ Caption block accurate                                      ║
║  □ Certificate of service included (if filing)                 ║
║  □ Verification statement included (if required)               ║
║  □ Proposed order attached (if motion)                         ║
║                                                                ║
║  ANTI-HALLUCINATION:                                           ║
║  □ No fabricated names                                         ║
║  □ No fabricated bar numbers                                   ║
║  □ No fabricated evidence statistics                           ║
║  □ All placeholders have specific lookup instructions          ║
║  □ DB was checked before every placeholder insertion           ║
║                                                                ║
║  RESULT: □ PASS — ready for review                             ║
║          □ FAIL — fix issues before output                     ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════════╗
║           OMEGA-WRITING v2.0 — QUICK REFERENCE                 ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  LEGAL DOCS (W1):                                              ║
║    Caption: 14th Circuit, Muskegon County format               ║
║    Components: Caption + Body + Verification + CoS + Order     ║
║    Frameworks: IRAC, CREAC, TEC                                ║
║                                                                ║
║  MOTIONS (W2):                                                 ║
║    17+ types available, MCR 2.119 compliant                    ║
║    Structure: Issues → Authority → Facts → Argument → Relief   ║
║    ALWAYS include: proposed order + certificate of service      ║
║                                                                ║
║  APPELLATE (W3):                                               ║
║    COA: 50-page limit, MCR 7.212                               ║
║    MSC: 50-page limit, MCR 7.305(B)                            ║
║    ALWAYS: standard of review + record citations               ║
║                                                                ║
║  TECH DOCS (W4):                                               ║
║    Comments: minimal, purposeful (WHY not WHAT)                ║
║    README: install → quick start → architecture → testing      ║
║                                                                ║
║  NARRATIVES (W5):                                              ║
║    Every fact → evidence citation                              ║
║    Every date → verified against DB                            ║
║    Child = L.D.W. always                                       ║
║                                                                ║
║  REPORTS (W6):                                                 ║
║    Every metric → DB query documented                          ║
║    No rounding, no extrapolation                               ║
║                                                                ║
║  PERSUASION (W7):                                              ║
║    15 techniques available                                     ║
║    Balance: logos/ethos/pathos calibrated to doc type           ║
║                                                                ║
║  ANTI-HALLUCINATION (W8) — APPLIES TO ALL:                     ║
║    Names: VERIFIED TABLE ONLY                                  ║
║    Stats: DB QUERY ONLY                                        ║
║    Evidence: DB-VERIFIED ONLY                                  ║
║    Unknown: [UNKNOWN — VERIFY] — never guess                   ║
║                                                                ║
║  GOLDEN RULE: If it's not in the DB, don't put it in           ║
║  the filing. A placeholder is honest. A fabrication is          ║
║  potential perjury.                                             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ═══════════════════════════════════════════════════════════════
## UPGRADE v2.1: MICHIGAN COURT FORMAT STANDARDS
## ═══════════════════════════════════════════════════════════════

### Circuit Court Filing Format (MCR 2.113)
```
Margins:       1 inch all sides
Font:          12pt proportional (Times New Roman) or 12pt monospace (Courier)
Line spacing:  Double-spaced (text body); single-spaced (block quotes, footnotes)
Page numbers:  Bottom center, starting page 1 on first page after caption
Paper:         8.5 x 11 (letter)
Caption:       STATE OF MICHIGAN, IN THE [COURT], COUNTY OF [COUNTY]
               Case No. [NUMBER], Hon. [JUDGE NAME]
```

### Caption Block Template (14th Circuit Family)
```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
FAMILY DIVISION

ANDREW JAMES PIGORS,
        Plaintiff,                     Case No. 2024-001507-DC

v.                                     Hon. Jenny L. McNeill

EMILY A. WATSON,
        Defendant.
__________________________________/
```

### Affidavit Format (MCR 2.119(B))
```
STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

AFFIDAVIT OF ANDREW JAMES PIGORS

I, Andrew James Pigors, being first duly sworn, depose and state:
1. [Personal knowledge statement]
2. [Factual paragraphs — numbered, chronological]
...
FURTHER AFFIANT SAYETH NOT.

____________________________
Andrew James Pigors
Dated: [DATE]

Subscribed and sworn to before me
this ___ day of ________, 2026.
____________________________
Notary Public, Muskegon County, Michigan
My commission expires: ____________
```

### Proposed Order Template
```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

[CAPTION — same as motion]

ORDER [GRANTING/DENYING] [MOTION TYPE]

At a session of said Court held in the City of Muskegon,
County of Muskegon, State of Michigan on ____________, 2026.

PRESENT: HON. JENNY L. McNEILL, Circuit Court Judge

This matter having come before the Court on [motion type],
IT IS HEREBY ORDERED:
1. [Relief granted/denied]
2. [Additional provisions]

IT IS SO ORDERED.

____________________________
Hon. Jenny L. McNeill
Circuit Court Judge
Date: ________________
```

### Certificate of Service (MC 12 / MCR 2.107)
```
CERTIFICATE OF SERVICE

I certify that on [DATE], I served a copy of this [DOCUMENT NAME]
upon all parties or their attorneys of record by:

[ ] First-class mail, postage prepaid
[ ] Personal delivery
[ ] Electronic service (email)
[ ] MiFILE e-filing service

upon:

[Party/Attorney name and address]

____________________________
Andrew James Pigors
[Address]
Dated: [DATE]
```

### COA Brief Format (MCR 7.212)
```
Required sections (in order):
1. Table of Contents
2. Index of Authorities
3. Statement of Jurisdiction
4. Statement of Questions Presented
5. Statement of Facts
6. Argument (with headings matching questions presented)
7. Relief Requested
8. Appendix (separate volume if needed)

Appendix MUST include:
- Lower court opinions/orders being appealed
- Relevant docket entries
- Relevant statutory/rule text
- Pertinent documents from lower court record
```
