---
name: evidence-intelligence-nexus
description: "Use when processing, authenticating, or analyzing evidence — harvesting from drives, chain of custody, authentication under MRE 901-903, timeline forensics, deduplication, harm quantification, damages calculation, cause of action research, authority validation, and local legal search. Michigan evidence law focused (Pigors v Watson)."
category: discipline
version: "2.0.0"
triggers:
  - evidence
  - authentication
  - chain of custody
  - deduplication
  - damages
  - harm quantification
  - timeline
  - drive scan
  - exhibit
  - Bates
  - MRE 901
  - cause of action
  - authority validation
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County; Michigan COA; Michigan Supreme Court"
case: Pigors v Watson
dependencies: []
metadata:
  model: opus
  forged_from: 12
  forge_date: 2026-03-12
---

# EVIDENCE-INTELLIGENCE-NEXUS — Elite Composite Skill

> Forged from 12 individual skills into one supreme composite.
> Sources: litigation-evidence-harvester, litigation-evidence-authentication, evidence-context-injector, litigation-timeline-forensics, drive-forensic-scanner, drive-organizer-engine, litigation-harm-quantifier, litigation-damages-calculator, litigation-claim-researcher, litigation-cause-of-action-library, litigation-authority-validator, local-legal-search

## When to Apply

Activate this skill for ANY work related to:
- **Evidence Harvesting**: discovery, collection, preservation, chain of custody
- **Evidence Authentication**: foundation, business records, electronic evidence, MRE 901
- **Context Injection**: evidence-to-filing linking, contextual enrichment, Bates references
- **Timeline Forensics**: chronological reconstruction, gap detection, temporal analysis
- **Drive Forensic Scanning**: multi-drive scanning, file recovery, metadata extraction
- **Drive Organization**: file categorization, deduplication, lane assignment, inventory
- **Harm Quantification**: damages modeling, economic/non-economic, treble damages
- **Damages Calculation**: Michigan damages law, MCL 600.2911, housing MTHA, §1983
- **Claim Research**: cause of action identification, element mapping, evidence linking
- **Cause of Action Library**: 32 causes of action, elements, defenses, Michigan-specific
- **Authority Validation**: citation verification, currency checks, overruled detection
- **Local Legal Search**: offline legal research, statute/rule lookup, case law search

---

## §1. Evidence Harvesting

> discovery, collection, preservation, chain of custody

### Chain of Custody Documentation
*Source: litigation-evidence-authentication*

### Required Fields

```
Chain of Custody Record — Exhibit [#]

1. Item Description: [Full description]
2. Original Source: [Where item was obtained]
3. Date Obtained: [Date]
4. Obtained By: [Person]
5. Storage Location: [Where kept]
6. Access Log:
   - [Date] [Person] [Action] [Reason]
   - [Date] [Person] [Action] [Reason]
7. Alterations: [None / Description]
8. Copy Made: [Date] [Method] [By whom]
9. Current Location: [Location]
10. Hash (digital items): [SHA-256]
```

### Digital Evidence Preservation

| Step | Action | Purpose |
|------|--------|---------|
| 1 | Screenshot with metadata visible | Capture content + timestamp |
| 2 | Record URL and access date | Prove source and timing |
| 3 | Calculate SHA-256 hash | Integrity verification |
| 4 | Store original + copy separately | Redundancy |
| 5 | Create chain of custody entry | Admissibility |
| 6 | Notarize if critical | Additional authentication |

### Evidence Chain Methodology
*Source: litigation-evidence-harvester*

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

### Chain of Custody Documentation Requirements
*Source: litigation-evidence-harvester*

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

## §2. Evidence Authentication

> foundation, business records, electronic evidence, MRE 901

### Evidence Chain Methodology
*Source: litigation-evidence-harvester*

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

### MRE Admissibility Checklist
*Source: litigation-evidence-harvester*

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

### Evidence Categorization Taxonomy
*Source: litigation-evidence-harvester*

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

### MRE 901 — Authentication Requirements
*Source: litigation-evidence-authentication*

### General Rule

> **MRE 901(a):** The requirement of authentication or identification as
> a condition precedent to admissibility is satisfied by evidence sufficient
> to support a finding that the matter in question is what its proponent claims.

### Authentication Methods (MRE 901(b))

| Method | MRE Section | Description | Common Use |
|--------|-------------|-------------|------------|
| Testimony of witness with knowledge | 901(b)(1) | Witness testifies item is what it's claimed to be | Photos, documents, physical items |
| Non-expert opinion on handwriting | 901(b)(2) | Lay witness familiar with handwriting | Handwritten notes, signatures |
| Comparison by expert or trier | 901(b)(3) | Expert compares to authenticated specimen | Disputed signatures, contested documents |
| Distinctive characteristics | 901(b)(4) | Appearance, contents, substance, internal patterns | Emails (sender, content, context) |
| Voice identification | 901(b)(5) | Opinion based on hearing voice | Phone recordings, voicemails |
| Telephone conversations | 901(b)(6) | Circumstances show person called | Phone records with content |
| Public records | 901(b)(7) | Authorized recording or filing | Court filings, government records |
| Ancient documents | 901(b)(8) | 20+ years old, found in natural place | Historical property records |
| Process or system | 901(b)(9) | Evidence of process producing accurate result | Computer-generated records |
| Methods provided by statute | 901(b)(10) | Authentication per applicable statute | Certified copies per MCL |

### Digital Evidence Authentication Matrix

| Evidence Type | Primary Method | Secondary Method | Foundation Requirements |
|--------------|----------------|------------------|----------------------|
| Text messages | 901(b)(4) — distinctive characteristics | 901(b)(1) — testimony | Phone owner, number, conversation context |
| Emails | 901(b)(4) — header + content | 901(b)(9) — system | Email addresses, metadata, reply chains |
| Screenshots | 901(b)(1) — testimony | 901(b)(9) — system | Who took it, when, what device, accuracy |
| Social media posts | 901(b)(4) — distinctive characteristics | 901(b)(1) — testimony | Account identification, content, timing |
| Photos/videos | 901(b)(1) — testimony | 901(b)(9) — system | Fair and accurate depiction testimony |
| Audio recordings | 901(b)(5) — voice ID | 901(b)(1) — testimony | Voice identification, accuracy, completeness |
| Website content | 901(b)(9) — process | 901(b)(1) — testimony | Wayback Machine, certified printout, metadata |
| Bank records | 901(b)(7) — public record | 803(6) — business record | Certification or custodian testimony |
| Medical records | 803(6) — business records | 902(11) — certification | Records custodian affidavit |
| Police reports | 803(8) — public records | 901(b)(7) | Certified copy from department |

### MRE 902 — Self-Authentication
*Source: litigation-evidence-authentication*

Documents that require **no extrinsic evidence** of authenticity:

| Category | MRE Section | Examples |
|----------|-------------|---------|
| Domestic public documents under seal | 902(1) | Court orders, certified vital records |
| Domestic public documents not under seal | 902(2) | With officer certification |
| Foreign public documents | 902(3) | With attestation |
| Certified copies of public records | 902(4) | Court-certified copies of filings |
| Official publications | 902(5) | MCL, MCR, published court rules |
| Newspapers and periodicals | 902(6) | Published articles |
| Trade inscriptions | 902(7) | Labels, signs, tags |
| Acknowledged documents | 902(8) | Notarized documents |
| Commercial paper | 902(9) | Checks, promissory notes |
| Presumptions under statute | 902(10) | As provided by Michigan law |
| Certified domestic records of activity | 902(11) | With custodian declaration |

### Best Evidence Rule (MRE 1001-1008)
*Source: litigation-evidence-authentication*

### MRE 1002 — Requirement of Original

> To prove the content of a writing, recording, or photograph, the original
> is required except as otherwise provided by these rules or by statute.

### When Copies Are Acceptable (MRE 1003)

> A duplicate is admissible to the same extent as an original unless a
> genuine question is raised as to the authenticity of the original or it
> would be unfair to admit the duplicate.

### Exceptions to Original Requirement (MRE 1004)

| Exception | Description |
|-----------|-------------|
| Lost or destroyed | Original lost/destroyed not in bad faith |
| Not obtainable | Cannot obtain by judicial process |
| In opponent's possession | Opponent was on notice and didn't produce |
| Collateral matters | Writing not closely related to controlling issue |

### Foundation Testimony Templates
*Source: litigation-evidence-authentication*

### For Photographs (MRE 901(b)(1))

```
Q: I'm showing you what has been marked as Exhibit [#]. Do you recognize it?
A: Yes.
Q: What is it?
A: It is a photograph of [description].
Q: How do you know that?
A: I [took the photograph / was present when it was taken / recognize the scene].
Q: Does this photograph fairly and accurately depict [subject] as it appeared
   on [date]?
A: Yes.
PROPONENT: Your Honor, I move to admit Exhibit [#].
```

### For Text Messages (MRE 901(b)(4))

```
Q: I'm showing you what has been marked as Exhibit [#]. Do you recognize it?
A: Yes, these are text messages between myself and [person].
Q: How do you recognize them?
A: I recognize my phone number [XXX-XXX-XXXX] and [person]'s number.
   The content of the messages is consistent with our conversation on [date].
Q: Did you take these screenshots from your phone?
A: Yes, on [date].
Q: Do they fairly and accurately represent the text conversation?
A: Yes.
PROPONENT: Your Honor, I move to admit Exhibit [#].
```

### For Business Records (MRE 803(6))

```
Q: What is your position at [organization]?
A: I am the [title/position].
Q: Are you the custodian of records for [type of records]?
A: Yes.
Q: I'm showing you what has been marked as Exhibit [#]. Do you recognize it?
A: Yes, it is a [description] from our records.
Q: Was this record made at or near the time of the events described?
A: Yes.
Q: Was it made by a person with knowledge or from information transmitted
   by a person with knowledge?
A: Yes.
Q: Is it the regular practice of [organization] to make this type of record?
A: Yes.
Q: Was this record kept in the regular course of business?
A: Yes.
PROPONENT: Your Honor, I move to admit Exhibit [#] as a business record
           under MRE 803(6).
```

### Evidence Authentication Report — Exhibit [#]
*Source: litigation-evidence-authentication*

### Item: [Description]
### Authentication Method: MRE [section] — [method name]

| Requirement | Status | Notes |
|------------|--------|-------|
| Foundation testimony | [Ready/Needed] | [Details] |
| Chain of custody | [Complete/Gap] | [Details] |
| Hearsay exception | [N/A/Identified] | MRE [section] |
| Best evidence rule | [Original/Copy OK] | [Details] |
| Self-authentication | [Yes/No] | MRE 902([subsection]) |

### Foundation Q&A
[Template for this exhibit type]

### Recommendation
[Admit / Additional foundation needed / Challenge expected]
```

## §3. Context Injection

> evidence-to-filing linking, contextual enrichment, Bates references

### Cross-References
*Source: litigation-claim-researcher*

- **Skill 22** (litigation-cause-of-action-library): Element lists and SOL for each claim
- **Skill 23** (litigation-complaint-drafter): Draft the complaint once claims are identified
- **Skill 25** (litigation-service-engine): Service after filing

## §4. Timeline Forensics

> chronological reconstruction, gap detection, temporal analysis

## §5. Drive Forensic Scanning

> multi-drive scanning, file recovery, metadata extraction

### Metadata
*Source: litigation-evidence-harvester*

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

### File Handler Matrix
*Source: litigation-evidence-harvester*

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

## §6. Drive Organization

> file categorization, deduplication, lane assignment, inventory

### File Handler Matrix
*Source: litigation-evidence-harvester*

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

### Evidence Categorization Taxonomy
*Source: litigation-evidence-harvester*

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

## §7. Harm Quantification

> damages modeling, economic/non-economic, treble damages

### Damages Categories for Pigors v Watson
*Source: litigation-harm-quantifier*

### A. Custody-Related Damages

1. **Lost Parenting Time**: Value each missed day/hour; document with court orders vs. actual time received
2. **Parent-Child Bond Harm**: Non-economic; requires psychological testimony or detailed declaration
3. **Alienation Damages**: Emerging area; document behavioral changes in children, therapy costs
4. **Schedule Interference Costs**: Transportation, lost wages for rescheduling, childcare

### B. Housing/Consumer Damages

1. **Rent Differential**: Difference between rent paid and fair market value of defective unit
2. **Security Deposit**: Actual amount + statutory penalties under MCL 554.613 (double deposit)
3. **Repair Costs**: Out-of-pocket repairs tenant made; estimates for repairs landlord refused
4. **Moving/Relocation**: Actual costs forced by uninhabitable conditions
5. **MCPA Treble Damages**: MCL 445.911(2) — actual damages × 3 or $250 minimum

### C. Emotional Distress Damages

Michigan recognizes IIED and NIED as independent torts:

- **IIED**: Requires extreme and outrageous conduct; Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)
- **NIED**: Requires physical manifestation or zone of danger in negligence context
- **Parasitic**: Emotional distress attached to another tort (no independent showing needed)

Valuation factors:
- Severity and duration of distress
- Physical manifestations (insomnia, weight change, medical treatment)
- Impact on daily functioning and relationships
- Corroboration (therapist records, witness testimony, medication records)

### D. Federal Civil Rights Damages (42 USC § 1983)

- **Compensatory**: Full tort-style damages for constitutional violations
- **Nominal**: $1 where right violated but no actual damages proven; Carey v Piphus, 435 US 247 (1978)
- **Punitive**: Available against individuals (not municipalities); Smith v Wade, 461 US 30 (1983)
- **Attorney fees not applicable for pro se**: Kay v Ehrler, 499 US 432 (1991) — pro se litigants cannot recover attorney fees under § 1988

### Case-Specific Damages Ranges (Pigors v. Watson)
*Source: litigation-damages-calculator*

| Lane | Description | Conservative | Moderate | Aggressive |
|------|-------------|-------------|----------|------------|
| A | Custody (2024-001507-DC) | $393,000 | $1,200,000 | $2,670,000 |
| B | Housing (2025-002760-CZ) | $450,000 | $1,500,000 | $3,400,000 |
| D | PPO (2023-5907-PP) | $150,000 | $500,000 | $1,200,000 |
| E | Misconduct (JTC) | $250,000 | $750,000 | $2,000,000 |
| F | Appellate (COA 366810) | Reversal | Reversal + damages | Reversal + sanctions |
| C | Convergence (all lanes) | $1,243,000 | $3,950,000 | $22,900,000+ |

## §8. Damages Calculation

> Michigan damages law, MCL 600.2911, housing MTHA, §1983

### Michigan-Specific Rules
*Source: litigation-damages-calculator*

- **MCL 600.6013**: Prejudgment interest — accrues from date of filing complaint at statutory rate
- **MCL 438.31**: Statutory interest rate (5% per annum for most civil actions)
- **MCL 600.6304**: Joint and several liability — economic damages are joint/several; non-economic are several only unless defendant > 50% at fault
- **MCL 37.2801**: Housing discrimination damages — actual damages plus up to treble, attorney fees, and costs
- **MCL 600.2911**: Defamation damages — actual damages, exemplary damages if malice shown
- **MCL 722.28**: Family law — attorney fees when one party cannot afford to pay
- **42 USC §1983**: Civil rights damages — compensatory and punitive
- **42 USC §1988**: Attorney fee shifting in civil rights cases — lodestar method
- **MCL 600.6013(8)**: Interest calculation period — from date of filing to date of satisfaction
- **MCR 8.119(H)**: All references to minor child use initials only (L.D.W.)

### Case-Specific Damages Ranges (Pigors v. Watson)
*Source: litigation-damages-calculator*

| Lane | Description | Conservative | Moderate | Aggressive |
|------|-------------|-------------|----------|------------|
| A | Custody (2024-001507-DC) | $393,000 | $1,200,000 | $2,670,000 |
| B | Housing (2025-002760-CZ) | $450,000 | $1,500,000 | $3,400,000 |
| D | PPO (2023-5907-PP) | $150,000 | $500,000 | $1,200,000 |
| E | Misconduct (JTC) | $250,000 | $750,000 | $2,000,000 |
| F | Appellate (COA 366810) | Reversal | Reversal + damages | Reversal + sanctions |
| C | Convergence (all lanes) | $1,243,000 | $3,950,000 | $22,900,000+ |

### Damages Categories for Pigors v Watson
*Source: litigation-harm-quantifier*

### A. Custody-Related Damages

1. **Lost Parenting Time**: Value each missed day/hour; document with court orders vs. actual time received
2. **Parent-Child Bond Harm**: Non-economic; requires psychological testimony or detailed declaration
3. **Alienation Damages**: Emerging area; document behavioral changes in children, therapy costs
4. **Schedule Interference Costs**: Transportation, lost wages for rescheduling, childcare

### B. Housing/Consumer Damages

1. **Rent Differential**: Difference between rent paid and fair market value of defective unit
2. **Security Deposit**: Actual amount + statutory penalties under MCL 554.613 (double deposit)
3. **Repair Costs**: Out-of-pocket repairs tenant made; estimates for repairs landlord refused
4. **Moving/Relocation**: Actual costs forced by uninhabitable conditions
5. **MCPA Treble Damages**: MCL 445.911(2) — actual damages × 3 or $250 minimum

### C. Emotional Distress Damages

Michigan recognizes IIED and NIED as independent torts:

- **IIED**: Requires extreme and outrageous conduct; Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)
- **NIED**: Requires physical manifestation or zone of danger in negligence context
- **Parasitic**: Emotional distress attached to another tort (no independent showing needed)

Valuation factors:
- Severity and duration of distress
- Physical manifestations (insomnia, weight change, medical treatment)
- Impact on daily functioning and relationships
- Corroboration (therapist records, witness testimony, medication records)

### D. Federal Civil Rights Damages (42 USC § 1983)

- **Compensatory**: Full tort-style damages for constitutional violations
- **Nominal**: $1 where right violated but no actual damages proven; Carey v Piphus, 435 US 247 (1978)
- **Punitive**: Available against individuals (not municipalities); Smith v Wade, 461 US 30 (1983)
- **Attorney fees not applicable for pro se**: Kay v Ehrler, 499 US 432 (1991) — pro se litigants cannot recover attorney fees under § 1988

### Michigan-Specific Caps and Limits
*Source: litigation-harm-quantifier*

| Damages Type | Cap/Limit | Authority |
|---|---|---|
| Non-Economic (Med Mal) | $280,000–$500,000 (indexed) | MCL 600.1483 |
| Non-Economic (Other Torts) | **No cap** | |
| Punitive | No statutory cap; constitutional limit ~9:1 ratio | State Farm v Campbell, 538 US 408 (2003) |
| MCPA Statutory | Treble actual damages or $250 minimum | MCL 445.911(2) |
| Security Deposit | Double the deposit amount | MCL 554.613 |
| § 1983 Punitive | No cap against individuals | |

## §9. Claim Research

> cause of action identification, element mapping, evidence linking

## §10. Cause of Action Library

> 32 causes of action, elements, defenses, Michigan-specific

### Burden of Proof Standards (Michigan)
*Source: litigation-cause-of-action-library*

| Standard | Applies To | Description |
|----------|-----------|-------------|
| Preponderance of the evidence | Most civil claims | More likely than not (>50%) |
| Clear and convincing evidence | Fraud, reformation, punitive damages | Highly probable, firm belief |
| Beyond reasonable doubt | Criminal contempt only | Near certainty |

### Statute of Limitations Quick Reference
*Source: litigation-cause-of-action-library*

| Claim Type | SOL Period | Authority |
|-----------|-----------|-----------|
| Fraud | 6 years from discovery | MCL 600.5813; MCL 600.5855 |
| Negligence | 3 years | MCL 600.5805(10) |
| Contract (written) | 6 years | MCL 600.5807(8) |
| Contract (oral) | 6 years | MCL 600.5807(8) |
| IIED | 3 years | MCL 600.5805(2) |
| Consumer protection (MCPA) | 6 years | MCL 445.911(7) |
| Habitability | 6 years (contract theory) | MCL 600.5807(8) |
| Section 1983 | 3 years (borrowed MI personal injury) | MCL 600.5805(2); Owens v Okure |
| Property damage | 3 years | MCL 600.5805(2) |
| Conversion | 3 years | MCL 600.5805(2) |
| Malicious prosecution | 3 years | MCL 600.5805(2) |

### Michigan-Specific Caps and Limits
*Source: litigation-harm-quantifier*

| Damages Type | Cap/Limit | Authority |
|---|---|---|
| Non-Economic (Med Mal) | $280,000–$500,000 (indexed) | MCL 600.1483 |
| Non-Economic (Other Torts) | **No cap** | |
| Punitive | No statutory cap; constitutional limit ~9:1 ratio | State Farm v Campbell, 538 US 408 (2003) |
| MCPA Statutory | Treble actual damages or $250 minimum | MCL 445.911(2) |
| Security Deposit | Double the deposit amount | MCL 554.613 |
| § 1983 Punitive | No cap against individuals | |

### Michigan-Specific Rules
*Source: litigation-damages-calculator*

- **MCL 600.6013**: Prejudgment interest — accrues from date of filing complaint at statutory rate
- **MCL 438.31**: Statutory interest rate (5% per annum for most civil actions)
- **MCL 600.6304**: Joint and several liability — economic damages are joint/several; non-economic are several only unless defendant > 50% at fault
- **MCL 37.2801**: Housing discrimination damages — actual damages plus up to treble, attorney fees, and costs
- **MCL 600.2911**: Defamation damages — actual damages, exemplary damages if malice shown
- **MCL 722.28**: Family law — attorney fees when one party cannot afford to pay
- **42 USC §1983**: Civil rights damages — compensatory and punitive
- **42 USC §1988**: Attorney fee shifting in civil rights cases — lodestar method
- **MCL 600.6013(8)**: Interest calculation period — from date of filing to date of satisfaction
- **MCR 8.119(H)**: All references to minor child use initials only (L.D.W.)

## §11. Authority Validation

> citation verification, currency checks, overruled detection

### Michigan Citation Format Reference
*Source: litigation-authority-validator*

### Statute Format
```
MCL § 722.23         — Child custody factors (Lane A)
MCL § 600.2918       — Housing/contract claims (Lane B)
MCL § 125.534        — Housing code violations (Lane B)
```

### Court Rule Format
```
MCR 2.116(C)(10)     — Summary disposition
MCR 3.210            — Child custody proceedings (Lane A)
MCR 7.201-7.215      — Court of Appeals rules
MRE 801-807           — Hearsay rules
```

### Case Law Format
```
Michigan Supreme Court:    Smith v Jones, 500 Mich 123, 130; 900 NW2d 456 (2023)
Michigan Court of Appeals: Smith v Jones, 340 Mich App 123, 130; 900 NW2d 456 (2023)
Unpublished COA:          Smith v Jones, unpublished per curiam opinion of the
                          Court of Appeals, issued January 15, 2024
                          (Docket No. 365432)
```

---

## §12. Local Legal Search

> offline legal research, statute/rule lookup, case law search

### Research Protocol
*Source: litigation-claim-researcher*

### Phase 1 — Exhaustive Fact Extraction

Before analyzing ANY legal theories, extract every fact:

1. **Temporal facts**: Every dated event — create a chronological master list
2. **Actor facts**: Every person/entity involved and their role
3. **Document facts**: Every document, communication, contract, notice
4. **Harm facts**: Every harm suffered — physical, emotional, financial, property
5. **Relationship facts**: Every legal relationship (landlord-tenant, contractual, fiduciary)
6. **Regulatory facts**: Every applicable code, statute, regulation, ordinance
7. **Omission facts**: Every duty that was NOT performed

**Quality Gate:** The fact list should be comprehensive. If the user provides 10 facts, the analysis should identify at least 5 additional implied facts (e.g., if there was a lease, there was a habitability covenant — MCL 554.139).

### Phase 2 — Rights Mapping

For each fact, identify what legal rights it implicates:

| Fact Category | Rights Implicated | Source of Right |
|--------------|------------------|----------------|
| False statement by defendant | Right to truthful dealing | Common law fraud, MCPA |
| Unsafe premises | Right to habitable housing | MCL 554.139, building code |
| Unauthorized entry | Right to quiet enjoyment | Lease covenant, trespass |
| Deposit not returned | Right to deposit return | MCL 554.601 et seq. |
| Retaliation for complaint | Right to exercise legal rights | MCL 600.5720 |
| Discriminatory treatment | Right to equal treatment | Elliott-Larsen, FHA |

### Phase 3 — Cause of Action Identification

For each implicated right, identify ALL possible causes of action:

**Systematic Checklist:**

#### A. Tort Claims (cross-reference Skill 22, tort-elements.md):
- [ ] Fraud (6 elements)
- [ ] Silent fraud / concealment
- [ ] Negligence
- [ ] Negligence per se
- [ ] IIED
- [ ] NIED
- [ ] Conversion
- [ ] Trespass
- [ ] Defamation (per se / per quod)
- [ ] Invasion of privacy (4 types)
- [ ] Civil conspiracy
- [ ] Abuse of process
- [ ] Malicious prosecution
- [ ] Wrongful eviction

#### B. Contract Claims:
- [ ] Breach of express contract
- [ ] Breach of implied contract
- [ ] Breach of implied warranty of habitability (MCL 554.139)
- [ ] Breach of covenant of quiet enjoyment
- [ ] Unjust enrichment / quantum meruit

#### C. Statutory Claims (cross-reference Skill 22, statutory-elements.md):
- [ ] MCPA (MCL 445.903) — check ALL 29 subsections
- [ ] Truth in Renting (MCL 554.631)
- [ ] Security Deposit Act (MCL 554.601)
- [ ] Retaliatory Action (MCL 600.5720)
- [ ] Elliott-Larsen Civil Rights Act
- [ ] Manufactured Housing Act (MCL 125.2301)
- [ ] Building code violations

#### D. Federal Claims:
- [ ] 42 USC § 1983 (if state action present)
- [ ] Fair Housing Act (42 USC § 3601)

#### E. Derivative / Combination Claims:
- [ ] Civil conspiracy (requires underlying tort)
- [ ] Aiding and abetting
- [ ] Respondeat superior (employer liability)
- [ ] Piercing the corporate veil
- [ ] Joint venture liability

### Phase 4 — Element-by-Element Analysis

For each candidate cause of action, map facts to elements:


*[...35 more lines in source]*

## Michigan Legal Citations Index

### Michigan Court Rules (MCR)
- MCR 2.003
- MCR 2.003(C)(2)
- MCR 2.108
- MCR 2.116(C)(10)
- MCR 2.119(F)(1)
- MCR 2.313
- MCR 2.313(A)
- MCR 2.612
- MCR 3.206
- MCR 3.207
- MCR 3.210
- MCR 3.701
- MCR 7.201
- MCR 7.215(C)
- MCR 8.119(H)

### Michigan Compiled Laws (MCL)
- MCL 125.2301
- MCL 125.401
- MCL 37.2801
- MCL 438.31
- MCL 445.901
- MCL 445.903
- MCL 445.911
- MCL 554.139
- MCL 554.601
- MCL 554.613
- MCL 554.631
- MCL 600.1483
- MCL 600.1711
- MCL 600.2911
- MCL 600.2950
- MCL 600.5720
- MCL 600.5801
- MCL 600.5805
- MCL 600.5807
- MCL 600.5813
- MCL 600.5855
- MCL 600.6013
- MCL 600.6304
- MCL 722.1203
- MCL 722.21
- MCL 722.23
- MCL 722.27
- MCL 722.27a
- MCL 722.28


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
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |
| MCR 2.302 | 698 | 🆕 Verify & integrate |

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

---

## Decision Tree

```
ENTRY: Evidence task received
│
├─ Q1: What phase of evidence work?
│   ├─ Collection / Harvesting → BRANCH A: Evidence Collection
│   ├─ Processing / Dedup → BRANCH B: Evidence Processing
│   ├─ Authentication / Foundation → BRANCH C: Authentication
│   ├─ Analysis / Timeline → BRANCH D: Forensic Analysis
│   └─ Damages / Quantification → BRANCH E: Damages Calculation
│
├─ BRANCH A: Evidence Collection
│   ├─ Step 1: Identify target drives and directories (C:\, D:\, F:\, G:\, H:\, I:\)
│   ├─ Step 2: Scan with drive forensic scanner — catalog all files
│   ├─ Step 3: Compute SHA-256 hash for each file (for provenance, NOT dedup)
│   ├─ Step 4: Assign lane tag via MEEK signal detection (E→D→F→C→A→B priority)
│   ├─ Step 5: Record chain of custody entry for each file
│   └─ OUTPUT: Evidence inventory with hashes, lane tags, and custody records
│
├─ BRANCH B: Evidence Processing
│   ├─ Step 1: Content-based dedup — OPEN files and compare text (NOT hash-only)
│   ├─ Step 2: Move confirmed duplicates to I:\ drive dedup folder (NEVER delete)
│   ├─ Step 3: Extract text/metadata from PDFs, DOCX, images (OCR if needed)
│   ├─ Step 4: Index into litigation_context.db with proper lane tagging
│   ├─ Step 5: Verify counts with DISTINCT queries to prevent inflation
│   └─ OUTPUT: Deduplicated, indexed evidence with traceable counts
│
├─ BRANCH C: Authentication
│   ├─ Step 1: Identify evidence type (text, email, photo, document, recording)
│   ├─ Step 2: Determine applicable MRE rule (901(b)(1), 901(b)(4), 901(b)(9), 902)
│   ├─ Step 3: Identify foundation witness who can authenticate
│   ├─ Step 4: Draft foundation questions for each exhibit
│   ├─ Step 5: Check for hearsay issues and identify exceptions (MRE 803/804)
│   └─ OUTPUT: Authentication worksheet per exhibit with MRE citations
│
├─ BRANCH D: Forensic Analysis
│   ├─ Step 1: Build chronological timeline from all evidence sources
│   ├─ Step 2: Detect gaps in timeline — flag periods with no evidence
│   ├─ Step 3: Cross-reference evidence across lanes for contradictions
│   ├─ Step 4: Generate temporal analysis with event clustering
│   └─ OUTPUT: Evidence timeline with gap analysis and contradiction flags
│
└─ BRANCH E: Damages Calculation
    ├─ Step 1: Classify damage type (economic, non-economic, statutory, punitive)
    ├─ Step 2: Identify legal basis (MCL, USC, common law) for each claim
    ├─ Step 3: Document actual losses with supporting evidence references
    ├─ Step 4: Apply multiplier if treble damages apply (document statutory basis)
    ├─ Step 5: Map each damage to specific evidence in DB
    └─ OUTPUT: Damages calculation with methodology, evidence links, and totals
```

---

## Output Contract

```yaml
output:
  type: enum [evidence_report, authentication_worksheet, timeline, damages_calculation, inventory, dedup_report]
  format: markdown
  required_fields:
    - summary: string
    - citations: list[string]  # verified MRE/MCL citations only
    - confidence: float  # 0.0-1.0
    - lane: enum [A, B, C, D, E, F]
    - case_number: string
    - evidence_count: integer  # must use COUNT(DISTINCT ...)
    - dedup_method: string  # "content-based" (NEVER "hash-only")
    - chain_of_custody: boolean  # documented for all digital evidence
  quality_gates:
    - all_citations_verified: boolean
    - no_hallucinated_names: boolean
    - db_first_confirmed: boolean
    - traceable_statistics: boolean
    - content_based_dedup: boolean  # hash-only is forbidden
    - authentication_documented: boolean
    - chain_of_custody_complete: boolean
    - no_duplicate_counting: boolean
```
