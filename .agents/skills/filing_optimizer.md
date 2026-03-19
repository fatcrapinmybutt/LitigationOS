# Filing Optimizer v13.0.0

## LitigationOS Skill Module — Court Filing Format & Compliance Optimization

---

## Purpose and Scope

The Filing Optimizer ensures every court filing meets Michigan Court Rule (MCR) formatting requirements, uses proper citation format, correctly references exhibits, and includes all required procedural elements. It transforms draft filings into court-ready documents.

This skill prevents:
- Rejection by the clerk's office for formatting defects
- Sanctions for non-compliant filings
- Missed legal arguments due to citation errors
- Exhibit reference mismatches that confuse the record

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `draft_path` | `FilePath` | Path to the draft filing document |
| `filing_type` | `str` | Type of filing (see Filing Types below) |
| `court` | `str` | Target court: `"circuit"`, `"coa"`, `"supreme"`, `"federal"` |
| `case_number` | `str` | Case number for caption |
| `parties` | `dict` | Party names and designations |
| `exhibits` | `List[ExhibitRef]` | Exhibits to be attached |
| `lane` | `str` | Case lane for context |
| `pro_se` | `bool` | Whether filer is pro se (default: `false`) |

### Filing Types
```
MOTION                    MCR 2.119
RESPONSE_TO_MOTION        MCR 2.119(C)(2)
REPLY_BRIEF               MCR 2.119(C)(3)
EMERGENCY_MOTION          MCR 3.207
BRIEF_IN_SUPPORT          MCR 2.119(A)(2)
COMPLAINT                 MCR 2.111
ANSWER                    MCR 2.111(D)
AFFIDAVIT                 MCR 2.119(B)
PROPOSED_ORDER            MCR 2.602
PROOF_OF_SERVICE          MCR 2.107
CLAIM_OF_APPEAL           MCR 7.204
APPLICATION_LEAVE_APPEAL  MCR 7.205
APPELLATE_BRIEF           MCR 7.212
```

---

## Processing Methodology

### Phase 1: Structural Formatting Compliance

**MCR 1.109 — General E-Filing Requirements:**
```
☐ Paper size: 8.5 × 11 inches
☐ Margins: 1 inch on all sides
☐ Font: 12-point, proportionally spaced (Times New Roman, Book Antiqua) 
    OR 12-point monospaced (Courier New)
☐ Line spacing: Double-spaced (except block quotes, footnotes)
☐ Page numbers: Centered at bottom of each page
☐ No colored text (black ink only)
☐ Caption on first page per MCR 2.113
```

**Caption Format Validation:**
```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF [COUNTY]
                                            Case No. [XX-XXXXX-XX]
[PLAINTIFF NAME],                           Hon. [Judge Name]
        Plaintiff/Petitioner,
v.
[DEFENDANT NAME],
        Defendant/Respondent.
________________________________________/

[TITLE OF DOCUMENT]
```

**MCR 7.212 — Appellate Brief Specific:**
```
☐ Table of Contents
☐ Index of Authorities
☐ Jurisdictional Statement
☐ Statement of Questions Presented
☐ Statement of Facts (with record citations)
☐ Argument (with standard of review for each issue)
☐ Relief Requested
☐ Word count certification (max 16,000 words for initial brief)
☐ Proof of Service
```

### Phase 2: Citation Format Validation

**Michigan Case Citations:**
```
Format: [Case Name], [Vol] Mich [Page] ([Year])
        [Case Name], [Vol] Mich App [Page] ([Year])
Example: Vodvarka v Grasmeyer, 259 Mich App 499; 675 NW2d 847 (2003)

Rules:
☐ Case name italicized (or underlined)
☐ Both Michigan and NW2d citations included (parallel citation)
☐ Pinpoint page references: 259 Mich App at 509
☐ Subsequent citations: Vodvarka, 259 Mich App at 509
```

**Michigan Statutes:**
```
Format: MCL [section]
Example: MCL 722.23
         MCL 722.23(a)–(l)

DO NOT USE: MCLA (obsolete)
```

**Michigan Court Rules:**
```
Format: MCR [rule]
Example: MCR 3.210(C)(8)
         MCR 2.119(A)(2)
```

**Federal Citations:**
```
Format: [Case Name], [Vol] US [Page] ([Year])
        [Case Name], [Vol] F3d [Page] ([Circuit] [Year])
        [Case Name], [Vol] F Supp 3d [Page] ([District] [Year])
Example: Troxel v Granville, 530 US 57 (2000)
```

**Citation Validation Checks:**
```
☐ All case citations have proper format
☐ Parallel citations included for Michigan cases
☐ Pinpoint citations used (no "see generally" without page number)
☐ Subsequent references shortened properly
☐ Signal usage correct (see, see also, cf., contra, etc.)
☐ String citations ordered by relevance then jurisdiction then date
☐ All cited authorities exist (validate against known case databases)
```

### Phase 3: Exhibit Reference Optimization

```
Exhibit Labeling Convention:
  Petitioner's Exhibits: A, B, C, ... Z, AA, AB, ...
  Respondent's Exhibits: 1, 2, 3, ... 100, ...
  Joint Exhibits:        JE-1, JE-2, ...

Validation Rules:
☐ Every exhibit referenced in text is included in exhibit list
☐ Every exhibit in the list is referenced in text at least once
☐ Exhibit references are consistent (no "Exhibit A" and "Ex. A" mixed randomly)
☐ Exhibits listed in order of first reference
☐ Each exhibit has a descriptive title in the exhibit list
☐ Page references within exhibits use "Exhibit A, p 3" format
☐ Authentication statement included where required (MRE 901)

Exhibit Index Format:
  EXHIBIT LIST
  Exhibit A — Order Modifying Custody dated March 15, 2024 (3 pages)
  Exhibit B — Docket Sheet for Case No. 24-1847-FC (2 pages)
  Exhibit C — Email from Opposing Counsel dated March 10, 2024 (1 page)
```

### Phase 4: Proof of Service Requirements

**MCR 2.107 Compliance:**
```
PROOF OF SERVICE

I, [Name], certify that on [Date], I served a copy of the foregoing 
[Document Title] on the following by [Method]:

[Name of Served Party]
[Address / Email / Fax]
[Method: First-class mail / Personal service / Electronic service / Fax]

______________________________
[Signature]
[Name]
[Address]
[Phone]
[Date]

Service Methods per MCR 2.107(C):
☐ Personal service — MCR 2.105
☐ Mail service (add 3 days to response deadline) — MCR 2.107(C)(3)
☐ Electronic service (if consented or e-filing) — MCR 1.109(G)(6)(a)
☐ Fax service (if consented) — MCR 2.107(C)(4)
```

### Phase 5: Content Completeness Check

**Motion Requirements (MCR 2.119):**
```
☐ Statement of issues presented
☐ Controlling authority cited for each issue
☐ Statement of facts (supported by evidence, affidavits, or record)
☐ Brief in support (may be combined with motion)
☐ Proposed order attached
☐ Proof of service
☐ Notice of hearing (if applicable)
☐ Filing fee (or fee waiver)
```

**Affidavit Requirements (MCR 2.119(B)):**
```
☐ Based on personal knowledge
☐ Facts admissible in evidence stated
☐ Affiant competent to testify
☐ Signed under oath or penalty of perjury
☐ Notarized (or signed under MCL 600.2922a)
```

---

## Output Format

```json
{
  "optimizer": "filing_optimizer_v13",
  "document": "drafts\\motion_to_disqualify.docx",
  "filing_type": "MOTION",
  "court": "circuit",
  "compliance_score": 0.82,
  "issues": [
    {
      "category": "FORMATTING",
      "severity": "HIGH",
      "rule": "MCR 1.109(D)",
      "description": "Font size is 11pt, must be 12pt",
      "location": "Global",
      "auto_fixable": true
    },
    {
      "category": "CITATION",
      "severity": "MEDIUM",
      "rule": "Michigan citation format",
      "description": "Missing NW2d parallel citation for Vodvarka",
      "location": "Page 4, paragraph 2",
      "auto_fixable": false,
      "suggestion": "Add: ; 675 NW2d 847 (2003)"
    },
    {
      "category": "EXHIBIT",
      "severity": "HIGH",
      "rule": "Exhibit consistency",
      "description": "Exhibit D referenced on page 6 but not in exhibit list",
      "location": "Page 6, line 12",
      "auto_fixable": false
    },
    {
      "category": "PROOF_OF_SERVICE",
      "severity": "CRITICAL",
      "rule": "MCR 2.107",
      "description": "Proof of service missing from filing",
      "location": "End of document",
      "auto_fixable": true,
      "template": "[Generated proof of service template]"
    }
  ],
  "auto_fixes_applied": [
    "Adjusted font to 12pt Times New Roman",
    "Set margins to 1 inch on all sides",
    "Added page numbers centered at bottom",
    "Generated proof of service template"
  ],
  "missing_elements": [
    "Proposed order not attached",
    "Notice of hearing not included"
  ],
  "optimized_path": "drafts\\motion_to_disqualify_OPTIMIZED.docx"
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `evidence_chain_builder` | Exhibit references map to evidence chain documents |
| `case_lane_router` | Filing type determines lane for routing |
| `emergency_motion_generator` | Emergency motions pass through optimizer before filing |
| `judicial_pattern_analyzer` | Disqualification motions reference pattern analysis output |
| `harm_quantifier` | Harm metrics formatted as exhibits |
| `filing_assembler` (engine) | Assembles final PDF from optimized components |
| `filing_converter` (engine) | Converts between formats (DOCX → PDF) |
| `filing_quality_validator` (engine) | Final validation before submission |
| `compliance_checker` (engine) | Cross-references compliance rules |

---

## Michigan-Specific Legal References

- **MCR 1.109** — Court records; filing and service standards
- **MCR 2.107** — Service and filing of pleadings and other papers
- **MCR 2.111** — General rules of pleading
- **MCR 2.113** — Form of pleadings, motions, and other papers (caption requirements)
- **MCR 2.119** — Motion practice
- **MCR 2.517** — Findings by the court (required elements in orders)
- **MCR 2.602** — Entry of judgments and orders
- **MCR 3.206** — Initiating a case (family division specific)
- **MCR 3.207** — Emergency and ex parte orders
- **MCR 7.204** — Claim of appeal
- **MCR 7.205** — Application for leave to appeal
- **MCR 7.212** — Briefs (appellate)
- **Michigan Appellate Opinion Manual** — Citation format authority
