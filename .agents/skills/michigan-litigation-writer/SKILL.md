---
name: michigan-litigation-writer
description: "Judicial-grade Michigan court document writer. Knows MCR, MCL, MRE, all torts, all courts from 14th Circuit through Supreme Court, JTC, and Federal. Determines available filings from case evidence, writes IRAC-format briefs, motions, complaints, affidavits. Use when: write court document, draft motion, file complaint, analyze claims, determine available filings, legal strategy."
metadata:
  category: discipline
  author: andrew-pigors
  version: "2.0.0"
  triggers:
    - write court document
    - draft motion
    - file complaint
    - draft brief
    - legal writing
    - court filing
    - IRAC
    - caption
    - certificate of service
    - affidavit
    - proposed order
---

# Michigan Litigation Writer

**Role**: Judicial-grade court document production for all Michigan courts — 14th Circuit, Michigan Court of Appeals, Michigan Supreme Court, JTC, and USDC Western District.

Reads case databases, determines available legal actions, produces filing-ready documents that comply with Michigan Court Rules formatting, citation standards, and procedural requirements.

## Engine
C:\Users\andre\LitigationOS\00_SYSTEM\litigation_document_engine.py

## Usage
```bash
python litigation_document_engine.py analyze       # Strategy analysis
python litigation_document_engine.py list           # List available filings
python litigation_document_engine.py generate --all # Generate all documents
python litigation_document_engine.py report         # Case status
```

---

## IRAC Structure (Mandatory for Every Argument Section)

Every substantive argument in every filing MUST follow IRAC. No exceptions.

| Step | Requirement | Example |
|------|-------------|---------|
| **Issue** | State the precise legal question in one sentence | "Whether the trial court abused its discretion by modifying custody without finding a change of circumstances under Vodvarka v Grasher." |
| **Rule** | Cite the governing rule with pinpoint authority | "A court may not modify a prior custody order unless the moving party demonstrates proper cause or a change of circumstances. MCL 722.27(1)(c); Vodvarka v Grasher, 259 Mich App 499, 508-509 (2003)." |
| **Application** | Apply the rule to THIS case's specific facts | "Here, Defendant presented no evidence of changed circumstances. The FOC report dated [date] found no material change..." |
| **Conclusion** | State what the court should do and the relief sought | "Because no proper cause or change of circumstances was demonstrated, the trial court's order must be reversed and the prior custody arrangement reinstated." |

### IRAC Quality Gates
- Every Issue must be answerable yes/no
- Every Rule must have at least one pinpoint citation
- Every Application must reference specific record evidence (exhibit, transcript page, filing date)
- Every Conclusion must request specific relief

---

## Michigan Citation Format Standards

### Court Rules (MCR)
- Format: `MCR [chapter].[rule]([section])([subsection])`
- Examples: `MCR 2.003(C)(1)(b)`, `MCR 7.212(B)`, `MCR 2.116(C)(10)`
- Always include the deepest applicable subrule

### Statutes (MCL)
- Format: `MCL [chapter].[section]([subsection])`
- Examples: `MCL 722.23(a)-(l)`, `MCL 600.2950(1)`, `MCL 552.501`
- Always include the specific subsection — never cite a bare section

### Evidence Rules (MRE)
- Format: `MRE [rule]([subsection])`
- Examples: `MRE 801(d)(2)`, `MRE 613(b)`, `MRE 403`

### Published Case Law
- Format: `*Party v Party*, Vol Mich App/Mich Page; NW2d cite (Year)`
- Example: `*Vodvarka v Grasher*, 259 Mich App 499, 508-509; 675 NW2d 847 (2003)`
- Case name ALWAYS italicized
- Include pinpoint page(s) — never cite just the first page
- NW2d parallel citation preferred but not required

### Unpublished Case Law
- Format: `*Party v Party*, unpublished per curiam opinion of the Court of Appeals, issued [Month Day, Year] (Docket No. XXXXXX)`
- **MUST** note: not binding precedent per MCR 7.215(C)(1)
- Use only when no published authority exists on point
- Include parenthetical explaining relevance

### Federal Case Law
- Format: `*Party v Party*, Vol F.3d/F.Supp.3d Page (Circuit Year)`
- Example: `*Troxel v Granville*, 530 US 57, 65 (2000)`

### Constitutional Provisions
- Format: `US Const, Am [number]` or `Const 1963, art [number], § [section]`
- Example: `US Const, Am XIV` / `Const 1963, art 6, § 30`

---

## MCR 2.113 — Formatting Requirements

### Document Composition
| Element | Requirement |
|---------|-------------|
| **Font** | 12-point, Times New Roman or equivalent proportional serif |
| **Margins** | 1 inch on all sides |
| **Line spacing** | Double-spaced body text; single-spaced block quotes and footnotes |
| **Paragraphs** | Sequentially numbered, each containing ONE factual or legal assertion |
| **Page numbers** | Bottom center, Arabic numerals |
| **Paper** | 8½ × 11 inch (letter size) |

### Required Components (Every Filing)
1. **Caption** — full case caption (see court-specific templates below)
2. **Title** — clear document title (e.g., "PLAINTIFF'S MOTION TO COMPEL DISCOVERY")
3. **Body** — numbered paragraphs with IRAC arguments
4. **Signature block** — name, address, phone, email, date
5. **Certificate of Service** — MCR 2.107 compliance (see below)
6. **Verification** (if required) — sworn statement for affidavits

---

## Caption Templates by Court Level

### Circuit Court (14th Circuit, Muskegon County)
```
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR MUSKEGON COUNTY

ANDREW PIGORS,                          Case No. 2024-001507-DC
        Plaintiff,                      Hon. Jenny L. McNeill
v.

Emily A. Watson,
        Defendant.
________________________________________/
```

### Michigan Court of Appeals
```
STATE OF MICHIGAN
IN THE COURT OF APPEALS

ANDREW PIGORS,                          Court of Appeals No. 366810
        Plaintiff-Appellant,            Circuit Court No. 2024-001507-DC
v.

Emily A. Watson,
        Defendant-Appellee.
________________________________________/
```

### Michigan Supreme Court
```
STATE OF MICHIGAN
IN THE SUPREME COURT

ANDREW PIGORS,                          Supreme Court No. ________
        Plaintiff-Appellant,            Court of Appeals No. 366810
v.                                      Circuit Court No. 2024-001507-DC

Emily A. Watson,
        Defendant-Appellee.
________________________________________/
```

### USDC Western District of Michigan
```
UNITED STATES DISTRICT COURT
WESTERN DISTRICT OF MICHIGAN
SOUTHERN DIVISION

ANDREW PIGORS,                          Case No. ________________
        Plaintiff,                      Hon. ________________
v.

[DEFENDANTS],
        Defendants.
________________________________________/
```

---

## Certificate of Service — MCR 2.107

A Certificate of Service (COS) is **MANDATORY on every filing**. No exceptions. Omission = rejection.

### Template
```
CERTIFICATE OF SERVICE

I, Andrew Pigors, certify that on [Month Day, Year], I served a copy of the
foregoing [DOCUMENT TITLE] on the following by [METHOD]:

    [Opposing Party/Counsel Name]
    [Address Line 1]
    [Address Line 2]
    [Email if e-service]

Method: [ ] First-class mail  [ ] Personal service  [ ] Email (by agreement)
        [ ] MiFILE e-service

                                        ____________________________
                                        Andrew Pigors
                                        [Address]
                                        [Phone]
                                        [Email]
                                        Dated: [Month Day, Year]
```

### MCR 2.107 Service Methods
| Method | Rule | When Valid |
|--------|------|------------|
| Personal delivery | MCR 2.107(C)(1) | Always valid |
| First-class mail | MCR 2.107(C)(2) | +3 days for response time |
| Email/electronic | MCR 2.107(C)(4) | Only if parties agree or court orders |
| MiFILE e-service | MCR 1.109(G)(6)(a) | When both parties use MiFILE |

---

## Word and Page Limits

| Document Type | Limit | Authority |
|---------------|-------|-----------|
| COA brief (main) | 16,000 words or 50 pages | MCR 7.212(B) |
| COA reply brief | 8,000 words or 25 pages | MCR 7.212(G) |
| COA application for leave | 50 pages | MCR 7.205(D) |
| MSC application | 50 pages | MCR 7.305(A)(3) |
| Circuit Court motion | 20 pages (local custom) | Check local administrative order |
| Circuit Court brief | 20-30 pages (local custom) | Check local administrative order |
| Circuit Court response | Same as motion/brief | Matches moving party limit |

**Word count excludes:** caption, table of contents, table of authorities, signature block, COS, certificate of compliance, attachments/exhibits.

---

## Pro Se Formatting Considerations

### Haines v Kerner Standard
Pro se filings are held to "less stringent standards than formal pleadings drafted by lawyers." *Haines v Kerner*, 404 US 519, 520 (1972).

### Michigan Application
- Michigan courts apply *Haines* to pro se litigants: *Estelle v Gamble*, 429 US 97 (1976); *Jourdan v Pierson*, 428 Mich 132, 142 (1987)
- Pro se filings must be "liberally construed" — *Drayden v Anusbigian*, unpublished (COA 2018)
- However: pro se litigants are still bound by court rules and deadlines — *Totman v School Dist of Royal Oak*, 135 Mich App 121, 126 (1984)

### Practical Pro Se Requirements
1. **Extra clarity** — judges won't guess your argument; state it plainly
2. **Strict deadline compliance** — no leniency on filing deadlines
3. **Proper service** — COS on everything; no excuses
4. **Record preservation** — object on the record or it's waived
5. **Procedural knowledge** — "I didn't know" is never an excuse for MCR violations
6. **Professional tone** — courts penalize emotional/inflammatory language

---

## Document Type Templates

### Motion Template Structure
1. Caption
2. Title: "[PARTY]'S MOTION [TO/FOR] [RELIEF]"
3. "NOW COMES [Party], and for their Motion states:"
4. Numbered paragraphs — facts
5. Numbered paragraphs — legal argument (IRAC)
6. Prayer for relief: "WHEREFORE, [Party] respectfully requests..."
7. Signature block
8. Certificate of Service
9. Proposed Order (attached, separate document per MCR 2.602)

### Brief in Support Template Structure
1. Caption
2. Title: "BRIEF IN SUPPORT OF [PARTY]'S MOTION [TO/FOR] [RELIEF]"
3. Table of Contents
4. Table of Authorities
5. Statement of Issues Presented
6. Statement of Facts (with record citations)
7. Argument (IRAC per issue)
8. Conclusion and Relief Requested
9. Signature block
10. Certificate of Service

### Affidavit Template Structure
1. Caption
2. Title: "AFFIDAVIT OF [NAME]"
3. "STATE OF MICHIGAN )\n                    ) ss.\nCOUNTY OF MUSKEGON  )"
4. "I, [Name], being first duly sworn, depose and state:"
5. Numbered paragraphs — factual statements (personal knowledge only)
6. "Further affiant sayeth naught."
7. Signature line with notary block
8. (No COS required on affidavit itself if attached to a served filing)

---

## Anti-Rationalization Table

| # | Rationalization | Why It Fails | Correct Practice |
|---|----------------|--------------|------------------|
| 1 | "I'll add the Certificate of Service later" | Filing may be stricken or rejected at intake. MCR 2.107 requires COS on EVERY document served. No do-overs. | Draft COS FIRST, then write the motion. COS is part of the document, not an afterthought. |
| 2 | "Unpublished cases are fine to cite" | MCR 7.215(C)(1): unpublished opinions are NOT binding precedent. Citing them as if binding undermines credibility. | Always note "unpublished" and add "not binding precedent." Use only when no published authority exists. Parenthetical required explaining relevance. |
| 3 | "Close enough on the citation format" | Judges and clerks notice sloppy citations. Incorrect pinpoints signal lazy research. Opposing counsel will attack your credibility. | Exact pinpoint pages required. Verify every cite against the original source. Use `MCR 2.003(C)(1)(b)` not `MCR 2.003`. |
| 4 | "The judge will understand what I mean" | Pro se status doesn't excuse ambiguity. *Totman*, 135 Mich App at 126: pro se litigants are bound by the same rules. If the court has to guess your argument, you've already lost. | State every argument explicitly. One legal proposition per numbered paragraph. Never assume the reader fills in gaps. |
| 5 | "I don't need a proposed order" | MCR 2.602(B)(3): the court may require a proposed order with any motion. Many courts (including 14th Circuit) expect one. Omission signals inexperience. | Always attach a proposed order to every motion. Keep it simple: caption + "IT IS HEREBY ORDERED that [specific relief]." |
| 6 | "I'll preserve the issue on appeal later" | If you don't raise it in the trial court, it's forfeited on appeal. *Walters v Nadell*, 481 Mich 377, 387 (2008). MCR 2.517(A)(7): objections must be timely and specific. | Object on the record at the time of the ruling. State the specific ground. If denied, make an offer of proof. |
| 7 | "Emotional language will persuade the judge" | Inflammatory rhetoric destroys credibility. Courts expect dispassionate legal analysis. Judges discount emotional arguments. | Let the facts speak. Use clinical, precise language. "The evidence demonstrates..." not "This outrageous injustice..." |

---

## Filing Readiness Checklist

Before ANY document leaves this engine, verify:

- [ ] Caption matches the exact court, case number, and judge
- [ ] Document title is clear and identifies the filing party
- [ ] All paragraphs are sequentially numbered
- [ ] Every legal assertion has a pinpoint citation
- [ ] Every factual assertion references a record source (exhibit, transcript, filing)
- [ ] IRAC structure is followed for each argument
- [ ] Certificate of Service is present with date, method, and recipient
- [ ] Proposed order attached (for motions)
- [ ] Word/page count within limits
- [ ] Font: 12pt Times New Roman, double-spaced, 1" margins
- [ ] Signature block complete with name, address, phone, email, date
- [ ] Verification/notary block included (if affidavit or verified filing)
- [ ] All exhibits labeled and referenced in text
- [ ] No emotional/inflammatory language
- [ ] Spell-checked and proofread

---

## Integration Points

- **litigation-analysis-engine**: Supplies case intelligence for factual sections
- **litigation-evidence-harvester**: Provides exhibit packages and evidence citations
- **litigation-impeachment-engine**: Feeds impeachment material for cross-exam briefs
- **litigation-judicial-analyst**: Provides judicial analysis for recusal/JTC filings
- **litigation-filing-architect**: Coordinates multi-document filing packages
- **litigation-red-team**: Reviews drafts for adversarial weaknesses before filing

## Related Skills

- [litigation-filing-architect](skill://litigation-filing-architect) — Multi-document filing orchestration
- [litigation-red-team](skill://litigation-red-team) — Adversarial review of draft filings
- [litigation-analysis-engine](skill://litigation-analysis-engine) — Case intelligence pipeline


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D,E,F | Verified |
| Emergency Custody | 55/100 | A,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,E,F | Verified |
| Contempt | 70/100 | A,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,D,E,F | Verified |
| Appeal Brief | 70/100 | A,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,D,E,F | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
