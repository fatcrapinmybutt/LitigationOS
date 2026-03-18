---
name: litigation-evidence-harvester
description: >-
  Use when performing deep evidence extraction, scanning and OCR processing documents, classifying evidence atoms, or building chain-of-custody records.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: evidence, harvest, extract, classify, OCR, scan
---

# litigation-evidence-harvester

## Metadata

```yaml
name: litigation-evidence-harvester
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when performing deep evidence extraction from large document collections,
  including scanning, OCR, classification, atom extraction, relevance scoring,
  and chain-of-custody tracking for Michigan 14th Judicial Circuit litigation
  across 427,956+ files.
triggers:
  - evidence extraction
  - document scan
  - OCR
  - classification
  - evidence scoring
  - chain of custody
  - document harvesting
  - atom extraction
  - file processing
```

## Purpose

This skill processes massive document collections (427,956+ files across scans/,
communications, records, and public documents) to extract, classify, score, and
organize evidence atoms for Pigors v Watson litigation in the 14th Judicial
Circuit, Muskegon County. It handles the full pipeline from raw file ingestion
to court-ready exhibit packages.

## Scale Context

| Metric | Value |
|--------|-------|
| Total files in collection | 427,956+ |
| Primary sources | scans/, communications/, court_records/, public_records/ |
| File types | PDF, JPEG, PNG, TIFF, DOCX, XLSX, TXT, HTML, EML, MSG |
| Estimated OCR required | ~180,000 image-based documents |
| Target output | Classified evidence atoms with scores + chain of custody |

## Decision Tree

```
INPUT: Document path(s) or collection identifier
  │
  ├─ Phase 1: INGESTION
  │   ├─ Enumerate files in target path(s)
  │   ├─ Detect file types (extension + magic bytes)
  │   ├─ Calculate checksums (SHA-256) for chain of custody
  │   ├─ Log ingestion metadata (timestamp, source, hash)
  │   └─ Deduplicate (exact + near-duplicate detection)
  │
  ├─ Phase 2: TEXT EXTRACTION
  │   ├─ Native text files (TXT, MD, HTML) → direct read
  │   ├─ Office documents (DOCX, XLSX) → parser extraction
  │   ├─ PDF documents
  │   │   ├─ Text-layer PDF → direct extraction
  │   │   └─ Image-only PDF → OCR pipeline
  │   ├─ Image files (JPEG, PNG, TIFF) → OCR pipeline
  │   ├─ Email files (EML, MSG) → header + body + attachment extraction
  │   └─ OCR pipeline
  │       ├─ Pre-processing (deskew, denoise, contrast)
  │       ├─ OCR engine (Tesseract / Azure AI)
  │       ├─ Confidence scoring per page
  │       └─ Manual review queue (confidence < 80%)
  │
  ├─ Phase 3: CLASSIFICATION
  │   ├─ Relevance classification (per document)
  │   │   ├─ HIGH: Directly supports/undermines a claim or defense
  │   │   ├─ MED: Provides context or corroboration
  │   │   ├─ LOW: Tangentially related, may support pattern
  │   │   └─ SKIP: Not relevant to any active case lane
  │   │
  │   ├─ Lane assignment
  │   │   ├─ A: Custody/Watson-related content
  │   │   ├─ B: Housing/Shady Oaks-related content
  │   │   ├─ C: Convergence/County-related content
  │   │   └─ MULTI: Relevant to multiple lanes
  │   │
  │   ├─ Document type classification
  │   │   ├─ COURT_FILING: Motion, brief, order, judgment
  │   │   ├─ COMMUNICATION: Email, letter, text message
  │   │   ├─ OFFICIAL_RECORD: Government document, report
  │   │   ├─ FINANCIAL: Invoice, receipt, bank record
  │   │   ├─ PHOTOGRAPH: Image evidence
  │   │   ├─ MEDICAL: Health record, evaluation
  │   │   ├─ TESTIMONY: Deposition, affidavit, declaration
  │   │   └─ OTHER: Unclassified
  │   │
  │   └─ Privilege screening
  │       ├─ Attorney-client privilege indicators
  │       ├─ Work product indicators
  │       ├─ Medical privilege (HIPAA)
  │       └─ Flag for manual review if detected
  │
  ├─ Phase 4: ATOM EXTRACTION
  │   ├─ Extract discrete evidentiary atoms from each document
  │   │   ├─ Factual assertions (who, what, when, where)
  │   │   ├─ Admissions (against interest)
  │   │   ├─ Contradictions (vs. other evidence)
  │   │   ├─ Timeline events (date-stamped facts)
  │   │   ├─ Financial data (amounts, accounts, transactions)
  │   │   └─ Relationship data (connections between persons/entities)
  │   │
  │   ├─ For each atom:
  │   │   ├─ Assign unique atom ID (ATM-XXXXXX)
  │   │   ├─ Link to source document (path + page + line/region)
  │   │   ├─ Classify by evidence type
  │   │   ├─ Assign lane(s)
  │   │   ├─ Score relevance (0–100)
  │   │   └─ Tag with related persons, entities, dates
  │   │
  │   └─ Build atom graph (relationships between atoms)
  │
  ├─ Phase 5: SCORING & RANKING
  │   ├─ Relevance score (0–100)
  │   │   ├─ Direct case impact: +0 to +40
  │   │   ├─ Corroboration value: +0 to +20
  │   │   ├─ Impeachment potential: +0 to +20
  │   │   ├─ Timeline significance: +0 to +10
  │   │   └─ Uniqueness (not duplicated elsewhere): +0 to +10
  │   │
  │   ├─ Admissibility score (0–100)
  │   │   ├─ Authentication strength: +0 to +30
  │   │   ├─ Hearsay exception applicability: +0 to +25
  │   │   ├─ Relevance under MRE 401/402: +0 to +25
  │   │   └─ Prejudice vs. probative (MRE 403): +0 to +20
  │   │
  │   └─ Priority score = (Relevance × 0.6) + (Admissibility × 0.4)
  │
  ├─ Phase 6: CHAIN OF CUSTODY
  │   ├─ For each evidence item:
  │   │   ├─ Origin record (where/when/how obtained)
  │   │   ├─ Hash chain (SHA-256 at each processing stage)
  │   │   ├─ Processing log (transformations applied)
  │   │   ├─ Access log (who viewed/modified)
  │   │   └─ Custodian declaration template
  │   │
  │   └─ Generate chain-of-custody certificate per exhibit
  │
  └─ OUTPUT: Evidence database + exhibit packages + reports
```

## Mode Switches

### Mode 1: FULL HARVEST
Complete pipeline from ingestion through scoring. Use for initial
processing of new document collections.

### Mode 2: INCREMENTAL
Process only new/modified files since last harvest run.
Compares checksums against prior ingestion log.

### Mode 3: TARGETED SCAN
Process specific files or directories for specific topics/keywords.
Use when investigating a particular claim or issue.

### Mode 4: RECLASSIFY
Re-run classification and scoring on previously extracted atoms.
Use when case strategy changes or new lanes are added.

### Mode 5: EXPORT
Generate court-ready exhibit packages from scored atoms.
Formats with exhibit labels, indexes, and chain-of-custody certificates.

### Mode 6: AUDIT
Verify chain-of-custody integrity across all processed evidence.
Reports any hash mismatches, missing records, or gaps.

## Output Contract

```yaml
output:
  evidence_database:
    type: structured_store
    tables:
      documents:
        - doc_id: string
        - file_path: string
        - file_type: string
        - sha256: string
        - ingested_at: ISO-8601
        - classification: HIGH | MED | LOW | SKIP
        - lane: A | B | C | MULTI
        - doc_type: enum (COURT_FILING, COMMUNICATION, etc.)
        - ocr_confidence: float | null
        - page_count: integer

      atoms:
        - atom_id: string (ATM-XXXXXX)
        - doc_id: string (FK → documents)
        - text: string
        - atom_type: FACT | ADMISSION | CONTRADICTION | TIMELINE | FINANCIAL | RELATIONSHIP
        - lane: A | B | C | MULTI
        - relevance_score: integer (0–100)
        - admissibility_score: integer (0–100)
        - priority_score: float (0–100)
        - persons: list[string]
        - entities: list[string]
        - dates: list[ISO-8601]
        - source_location: {page, line_start, line_end, region}

      chain_of_custody:
        - doc_id: string (FK → documents)
        - stage: INGESTION | EXTRACTION | CLASSIFICATION | EXPORT
        - timestamp: ISO-8601
        - sha256_at_stage: string
        - operator: string
        - notes: string

  harvest_report:
    type: summary
    fields:
      - total_files_processed: integer
      - files_by_classification: {HIGH: int, MED: int, LOW: int, SKIP: int}
      - files_by_lane: {A: int, B: int, C: int, MULTI: int}
      - total_atoms_extracted: integer
      - atoms_by_type: map[string, integer]
      - top_priority_atoms: list[atom_id] (top 50)
      - ocr_queue: list[doc_id] (low-confidence items)
      - processing_time: duration
      - error_log: list[{doc_id, error, stage}]

  exhibit_package:
    type: directory
    structure:
      - EXHIBIT_INDEX.md
      - CHAIN_OF_CUSTODY_CERT.md
      - exhibits/
        - EX_001_{description}.pdf
        - EX_002_{description}.pdf
        - ...
```

## File Handler Matrix

| File Type | Extension(s) | Handler | OCR Required |
|-----------|-------------|---------|--------------|
| Plain text | .txt, .md, .csv | Direct read | No |
| HTML | .html, .htm | HTML parser | No |
| Word | .docx | python-docx | No |
| Excel | .xlsx, .xls | openpyxl | No |
| PDF (text) | .pdf | PyPDF2/pdfplumber | No |
| PDF (image) | .pdf | Tesseract + pdfplumber | Yes |
| JPEG | .jpg, .jpeg | Tesseract | Yes |
| PNG | .png | Tesseract | Yes |
| TIFF | .tif, .tiff | Tesseract | Yes |
| Email | .eml | email parser | No (attachments may) |
| Outlook | .msg | msg-extractor | No (attachments may) |

## Classification Rules Summary

### HIGH Classification Triggers
- Direct testimony or sworn statement by party/witness
- Court orders, judgments, or rulings in active cases
- Communications showing admissions against interest
- Evidence of conditions (housing photos, inspection reports)
- Financial records showing fraud or misrepresentation
- Records contradicting opposing party's sworn statements

### MED Classification Triggers
- Background context documents (prior filings, related cases)
- Third-party communications referencing case facts
- General correspondence between parties
- Public records confirming timeline events
- Supporting documentation for already-classified HIGH items

### LOW Classification Triggers
- General background on parties or entities
- Tangentially related legal research or articles
- Duplicate or near-duplicate of already-classified items
- Documents from unrelated time periods with minor relevance

### SKIP Classification Triggers
- Completely unrelated to any case lane
- System-generated files (logs, temp files, caches)
- Corrupted or unreadable files (after OCR attempt)
- Personal documents with no case relevance

## Integration Points

- **litigation-filing-architect**: Supplies classified evidence for filing population
- **litigation-red-team**: Provides evidence inventory for vulnerability assessment
- **litigation-judicial-analyst**: Supplies transcript/hearing evidence
- **litigation-impeachment-engine**: Feeds statement atoms for contradiction detection

## Usage Examples

```
# Full harvest of scans directory
invoke litigation-evidence-harvester --mode full --source ./scans/

# Incremental harvest (new files only)
invoke litigation-evidence-harvester --mode incremental --source ./scans/

# Targeted scan for housing conditions
invoke litigation-evidence-harvester --mode targeted --source ./scans/ --topic "habitability"

# Export top exhibits for Lane A
invoke litigation-evidence-harvester --mode export --lane A --min-score 70

# Audit chain of custody
invoke litigation-evidence-harvester --mode audit
```

## Related Skills

- [litigation-impeachment-engine](skill://litigation-impeachment-engine) — Detects contradictions for impeachment
- [litigation-pipeline-commander](skill://litigation-pipeline-commander) — Executes OMEGA 16-phase pipeline

---

## Live Database Statistics (litigation_context.db)

| Table | Row Count | Description |
|-------|-----------|-------------|
| `evidence_quotes` | 308,636 | Extracted evidence passages with speaker, legal significance, category |
| `pages` | 472,211 | Raw page text from all ingested documents |
| `evidence_file_index` | 153,000+ | File-level evidence index with metadata |
| `master_citations` | 3,600,000+ | All extracted citations across entire corpus |
| `documents` | 427,956+ | Ingested document inventory with checksums |
| `contradiction_map` | 10,558 | Cross-document contradictions |
| `impeachment_items` | 15,171 | Impeachment-ready statement inconsistencies |

### Key FTS5 Search Interfaces
```sql
-- Search evidence by topic
SELECT quote_text, speaker, legal_significance FROM evidence_quotes_fts
WHERE evidence_quotes_fts MATCH 'parenting time AND denied';

-- Search raw pages for specific content
SELECT text_content, document_id, page_number FROM pages_fts
WHERE pages_fts MATCH 'housing conditions AND uninhabitable';

-- Cross-reference citations
SELECT citation, cite_type, context, source_file FROM master_citations
WHERE citation LIKE 'MCL 722.23%';
```

---

## Evidence Chain Methodology

Evidence is only useful in court if it connects to a legal claim backed by authority. The harvester builds three-link chains:

```
EVIDENCE → CLAIM → AUTHORITY
   ↓          ↓         ↓
evidence_quotes → claims → auth_rules / master_citations
```

### Chain Construction Process
1. **Extract**: Pull evidence atom from source document (evidence_quotes)
2. **Classify**: Assign to case lane (A-F) and evidence category
3. **Link to Claim**: Map evidence to legal claim in claims table
4. **Link to Authority**: Find governing rule/case law for the claim
5. **Score**: Rate chain strength (evidence_score × claim_score × authority_score)
6. **Gap Detection**: If any link is missing → create gap_ticket

### Chain Strength Scoring
| Component | Score Range | Weight | Measurement |
|-----------|------------|--------|-------------|
| Evidence strength | 0-100 | 40% | Authentication + relevance + reliability |
| Claim strength | 0-100 | 30% | Specificity + legal viability + factual support |
| Authority strength | 0-100 | 30% | Binding vs. persuasive + recency + jurisdiction match |
| **Chain score** | 0-100 | — | Weighted composite; ≥70 = filing-ready |

```sql
-- Find evidence chains with gaps
SELECT c.classification, c.proposition, c.status,
       COALESCE(fr.evidence_score, 0) as ev_score,
       COALESCE(fr.authority_score, 0) as auth_score
FROM claims c
LEFT JOIN filing_readiness fr ON c.id = fr.claim_id
WHERE COALESCE(fr.evidence_score, 0) < 60
   OR COALESCE(fr.authority_score, 0) < 60;
```

---

## MRE Admissibility Checklist

Before any evidence atom enters a filing, it must pass this admissibility gauntlet:

### Gate 1: Relevance (MRE 401/402)
- [ ] Evidence has "any tendency" to make a material fact more or less probable
- [ ] The fact is "of consequence" to the determination of the action
- [ ] If irrelevant → EXCLUDE (MRE 402: irrelevant evidence is not admissible)

### Gate 2: Prejudice Balancing (MRE 403)
- [ ] Probative value is NOT substantially outweighed by:
  - Danger of unfair prejudice
  - Confusion of issues
  - Misleading the jury
  - Undue delay, waste of time, needless cumulation
- [ ] Document the probative-vs-prejudicial analysis

### Gate 3: Hearsay Analysis (MRE 801/802/803/804)
- [ ] Is the statement offered for truth of the matter asserted? (MRE 801(c))
- [ ] If YES → is it excluded from hearsay definition?
  - MRE 801(d)(1): Prior statements by witness (inconsistent under oath / consistent / identification)
  - MRE 801(d)(2): Admissions by party-opponent
- [ ] If hearsay → does an exception apply?
  - **MRE 803** (availability immaterial): present sense impression (1), excited utterance (2), state of mind (3), medical diagnosis (4), recorded recollection (5), business records (6), public records (8), learned treatises (18)
  - **MRE 804** (declarant unavailable): former testimony (1), dying declaration (2), statement against interest (3), family history (4)
- [ ] If no exception → EXCLUDE unless residual exception (MRE 803(24)/804(5))

### Gate 4: Authentication (MRE 901/902)
- [ ] Evidence is what proponent claims it is (MRE 901(a))
- [ ] Authentication method identified:
  - MRE 901(b)(1): Testimony of witness with knowledge
  - MRE 901(b)(3): Comparison by expert or trier of fact
  - MRE 901(b)(4): Distinctive characteristics (appearance, content, context)
  - MRE 901(b)(7): Public records
  - MRE 901(b)(9): Process or system evidence
  - MRE 902: Self-authenticating documents (certified copies, official publications, business records with certification)

### Gate 5: Best Evidence Rule (MRE 1002-1004)
- [ ] Original document produced (MRE 1002), OR
- [ ] Duplicate admissible (MRE 1003), OR
- [ ] Original unavailable through no fault of proponent (MRE 1004)

---

## Evidence Categorization Taxonomy

### By Legal Function
| Category | Description | MRE Basis | Example |
|----------|-------------|-----------|---------|
| **ADMISSION** | Statement against party's interest | MRE 801(d)(2) | Watson email admitting to denying parenting time |
| **IMPEACHMENT** | Prior inconsistent statement | MRE 613, 801(d)(1) | Deposition testimony contradicting affidavit |
| **CORROBORATION** | Supports existing evidence | MRE 401 | Third-party witness confirming timeline |
| **REBUTTAL** | Contradicts opposing claim | MRE 401 | Photo disproving housing condition claim |
| **FOUNDATION** | Establishes admissibility of other evidence | MRE 901 | Chain of custody certificate |
| **CHARACTER** | Pattern evidence (limited use) | MRE 404(b) | History of similar conduct |
| **EXPERT** | Expert opinion evidence | MRE 702-705 | Psychological evaluation, inspection report |

### By Source Type
| Source | Reliability Tier | Authentication Burden |
|--------|-----------------|----------------------|
| Court orders/filings | Tier 1 (highest) | Self-authenticating (MRE 902) |
| Sworn testimony | Tier 1 | Transcript certification |
| Government records | Tier 1 | Certified copy (MRE 902(4)) |
| Business records | Tier 2 | Custodian certification (MRE 803(6)) |
| Professional reports | Tier 2 | Expert foundation (MRE 702) |
| Communications (email) | Tier 3 | Distinctive characteristics (MRE 901(b)(4)) |
| Communications (text) | Tier 3 | Testimony + screenshots + metadata |
| Social media | Tier 4 (lowest) | Multiple authentication methods required |
| Photos/video | Tier 3 | Testimony of witness with knowledge |

---

## Chain of Custody Documentation Requirements

### Per-Item Requirements
Every piece of evidence must have a documented chain of custody:

| Field | Description | Required |
|-------|-------------|----------|
| `item_id` | Unique evidence identifier | Yes |
| `origin_source` | Where/how the item was obtained | Yes |
| `origin_date` | When the item was obtained | Yes |
| `custodian` | Current custodian (Andrew Pigors) | Yes |
| `sha256_hash` | Cryptographic hash at time of acquisition | Yes |
| `processing_log` | All transformations applied (OCR, conversion) | Yes |
| `hash_at_each_stage` | SHA-256 after each processing step | Yes |
| `storage_location` | Current file path in LitigationOS | Yes |
| `access_log` | Who accessed and when | Recommended |

### Chain of Custody Certificate Template
```
CHAIN OF CUSTODY CERTIFICATE

Evidence Item: [EXHIBIT ID]
Original Source: [Description of how obtained]
Date Obtained: [Date]
Original Hash (SHA-256): [hash]

Processing History:
Stage 1 — Ingestion: [date] | Hash: [hash] | Action: [description]
Stage 2 — OCR: [date] | Hash: [hash] | Action: [description]
Stage 3 — Classification: [date] | Hash: [hash] | Action: [description]

I certify that this evidence has been maintained in an unbroken chain of custody
and has not been altered, modified, or tampered with since acquisition.

Custodian: Andrew Pigors
Date: [date]
```

### Integrity Verification Query
```sql
-- Verify chain of custody integrity for an exhibit
SELECT doc_id, stage, timestamp, sha256_at_stage, operator, notes
FROM chain_of_custody
WHERE doc_id = '[exhibit_id]'
ORDER BY timestamp ASC;
```


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
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
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
  Ω-2 Deep Scan → Ω-3 Evidence Harvest → Ω-4 Citation Extraction
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

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

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

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
