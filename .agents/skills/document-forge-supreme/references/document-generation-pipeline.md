# Document Generation Pipeline — document-forge-supreme

## Pipeline Overview

Document generation in LitigationOS follows a structured pipeline from template selection through quality assurance to filing-ready output.

```
1. TEMPLATE SELECTION
   │  Identify document type → select template → verify lane assignment
   │
2. DATA COLLECTION
   │  Query litigation_context.db → search filesystem → resolve all variables
   │
3. VARIABLE INJECTION
   │  Replace template variables → verify party names → validate case numbers
   │
4. CONTENT GENERATION
   │  Draft substantive content → apply MCR formatting → add citations
   │
5. QA GATES
   │  Pre-filing QA → formatting check → completeness audit
   │
6. ASSEMBLY
   │  Combine components → add exhibits → certificate of service → signature
   │
7. OUTPUT
   │  Generate PDF/DOCX → validate e-filing format → ready for TrueFiling
```

## Template System

### Template Variable Syntax

```
{{VARIABLE_NAME}}          — required variable (error if unresolved)
{{?OPTIONAL_VARIABLE}}     — optional variable (blank if unresolved)
{{#SECTION_START}}...{{/SECTION_END}}  — conditional section
{{LOOP:items}}...{{/LOOP}} — repeating section
```

### Core Variables (Always Available)

| Variable | Source | Value |
|----------|--------|-------|
| `{{PLAINTIFF}}` | Verified Party Table | Andrew James Pigors |
| `{{DEFENDANT}}` | Verified Party Table | Emily A. Watson |
| `{{CHILD_INITIALS}}` | MCR 8.119(H) | L.D.W. |
| `{{JUDGE}}` | Verified Party Table | Hon. Jenny L. McNeill |
| `{{COURT}}` | System config | Circuit Court for the County of Muskegon |
| `{{CIRCUIT}}` | System config | 14th Judicial Circuit |
| `{{PLAINTIFF_ADDRESS}}` | Verified Party Table | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 |
| `{{PLAINTIFF_PHONE}}` | Verified Party Table | (231) 903-5690 |
| `{{PLAINTIFF_EMAIL}}` | Verified Party Table | andrewjpigors@gmail.com |

### Lane-Specific Variables

| Lane | Case Number Variable | Additional Variables |
|------|---------------------|---------------------|
| A (Custody) | `{{CASE_NO_A}}` = 2024-001507-DC | custody schedule, FOC info |
| B (Housing) | `{{CASE_NO_B}}` = 2025-002760-CZ | property details, lease info |
| D (PPO) | `{{CASE_NO_D}}` = 2023-5907-PP | protection order details |
| E (Misconduct) | `{{CASE_NO_E}}` = 2024-001507-DC | judicial findings |
| F (Appellate) | `{{CASE_NO_F}}` = COA 366810 | lower court record |

## Variable Resolution Protocol

Before inserting ANY placeholder, follow this protocol:

```
STEP 1: Query litigation_context.db
  → Try: docket_events, evidence_quotes, claims, deadlines, documents, judicial_violations
  → Try: schema_reference table for column names
  → Found? → Use the data. DONE.

STEP 2: Search filesystem
  → rg -l "search_term" across all drives (C:\, D:\, F:\, G:\, H:\, I:\)
  → fd --type f "filename_pattern" across all drives
  → Found? → Extract the data. DONE.

STEP 3: Check reference files
  → COMPLETE_FILING_DATA_SUMMARY.txt
  → QUICK_REFERENCE_FILING_PLACEHOLDERS.txt
  → Found? → Use the data. DONE.

STEP 4: Only NOW insert placeholder
  → Format: [DATA_NEEDED: specific description of what's needed and where to find it]
  → NOT: [INSERT], [ANDREW_REQUIRED], [ATTACH] (too vague)
```

## QA Gates (Pre-Filing Checklist)

Every document must pass ALL gates before filing:

### Gate 1: Party Verification
- [ ] Plaintiff name matches: Andrew James Pigors
- [ ] Defendant name matches: Emily A. Watson
- [ ] Child referenced by initials only: L.D.W.
- [ ] Judge name matches: Hon. Jenny L. McNeill
- [ ] No fabricated names (check for "Jane Berry", "Patricia Berry", "Amy McNeill")
- [ ] All bar numbers verified against actual records

### Gate 2: Case Number & Lane
- [ ] Case number matches assigned lane
- [ ] No cross-lane contamination
- [ ] MEEK signal verified for lane assignment

### Gate 3: Formatting Compliance
- [ ] Caption per MCR 2.113
- [ ] Brief formatting per MCR 7.212 (if applicable)
- [ ] Page limit compliance
- [ ] Font size and spacing correct
- [ ] Margins minimum 1 inch

### Gate 4: Service & Signature
- [ ] Certificate of service present
- [ ] Correct parties listed in service
- [ ] Current addresses verified (note: Barnes WITHDREW)
- [ ] Pro se signature block present
- [ ] Date line present

### Gate 5: Content Integrity
- [ ] All statistics traceable to DB queries
- [ ] No fabricated evidence counts
- [ ] All citations verified
- [ ] No remaining unresolved placeholders
- [ ] Exhibits attached and Bates-stamped

### Gate 6: E-Filing Readiness
- [ ] PDF format (or required format per court)
- [ ] File size within TrueFiling limits
- [ ] Document title matches filing type
- [ ] Correct filing category selected

## Using pre-filing-qa Agent

```
Invoke: task(agent_type="pre-filing-qa", prompt="Review [document] for filing readiness")

Output: GO / NO-GO report with:
  - Party name verification results
  - Case number verification
  - Formatting compliance score
  - Missing components list
  - Recommended fixes (if NO-GO)
```

## Document Types and Templates

| Document Type | Template Source | MCR Reference | Required Components |
|--------------|----------------|---------------|-------------------|
| Motion | MC 280 / custom | MCR 2.119 | Caption, issues, brief, proposed order, COS |
| Response | MC 281 / custom | MCR 2.119 | Caption, response, brief, COS |
| Brief (COA) | COA template | MCR 7.212 | TOC, index of authorities, statement of questions, statement of facts, argument, relief, COS |
| Affidavit | Custom | MCR 2.119 | Caption, verification, notary block |
| Proposed Order | MC 282 / custom | MCR 2.602 | Caption, order text, date/signature lines for judge |
| Proof of Service | CC 381 | MCR 2.107 | Method, date, recipient, address, signature |
