# Analysis Methods — Michigan Litigation Reference

## Evidence Analysis Framework

### Tier 1: Factual Extraction Methods

#### Document-Level Extraction
Every document entering the analysis engine must pass through structured extraction:

1. **Metadata Extraction**: Filing date, case number, parties, judge, document type
2. **Content Extraction**: Full text with page/paragraph references for pinpoint citations
3. **Entity Extraction**: Names, dates, amounts, addresses, case numbers
4. **Relationship Extraction**: Who said what, when, to whom, in what context

#### Line-by-Line Analysis Protocol
Per MCR 7.212(C)(7) pinpoint citation requirements:
- Each factual assertion receives a source citation (document + page + line)
- Contradictions between documents are flagged with both sources
- Admissions against interest are tagged for impeachment use
- Hearsay statements are classified by MRE 801-807 exception applicability

### Tier 2: Legal Issue Identification

#### Michigan Family Law Analysis (Lane A)
```
Statute: MCL 722.23 — Best Interest of the Child
Factors (a) through (l):
  (a) Love, affection, emotional ties — weight: STANDARD
  (b) Capacity for love, affection, guidance — weight: STANDARD
  (c) Capacity for food, clothing, medical care — weight: STANDARD
  (d) Length of stable custodial environment — weight: ENHANCED
  (e) Permanence of family unit — weight: STANDARD
  (f) Moral fitness — weight: CONTEXT-DEPENDENT
  (g) Mental and physical health — weight: STANDARD
  (h) Home, school, community record — weight: STANDARD
  (i) Reasonable preference of child — weight: AGE-DEPENDENT
  (j) Willingness to facilitate relationship — weight: ENHANCED
  (k) Domestic violence — weight: ENHANCED
  (l) Other relevant factors — weight: CONTEXT-DEPENDENT
```

#### Standard of Review Analysis
| Court Level | Standard | MCR/MCL Authority |
|-------------|----------|-------------------|
| Trial Court — Custody | Best interest (MCL 722.23) | MCL 722.23, 722.27 |
| Trial Court — Support | Formula + deviation | MCL 552.517, 552.605(2) |
| COA — Custody findings | Great weight / clear error | MCL 722.28 |
| COA — Legal questions | De novo | MCR 7.215(J)(1) |
| COA — Discretionary | Abuse of discretion | MCR 7.216(A)(7) |
| MSC — All issues | De novo | MCR 7.302(B) |

### Tier 3: Authority Mapping

#### Chain Construction Pattern
For each legal proposition identified in analysis:
```
1. Identify controlling statute (MCL)
2. Find binding Michigan Supreme Court case interpreting statute
3. Find supporting Court of Appeals published opinion
4. Locate pinpoint page with specific holding
5. Check currency — not overruled, amended, or distinguished
6. Tag with lane assignment (A-F)
```

#### Weight Categories for Evidence
| Category | Weight | Examples |
|----------|--------|----------|
| Judicial Finding | HIGHEST | Court orders, bench rulings, written opinions |
| Sworn Testimony | HIGH | Depositions, affidavits, hearing transcripts |
| Official Record | HIGH | Police reports, CPS reports, school records |
| Expert Opinion | HIGH | Custody evaluations, financial analyses |
| Documentary | MEDIUM | Emails, texts, photographs with metadata |
| Third-Party Statement | LOW | Unsworn letters, social media posts |
| Self-Serving Statement | LOWEST | Party's own unsworn narrative |

### Tier 4: Strength Scoring (EGCP Method)

#### EGCP Score Components
- **E** — Evidence completeness (0-25): Do we have sufficient evidence for each element?
- **G** — Gap severity (0-25): How critical are the missing pieces?
- **C** — Citation strength (0-25): Is the authority chain complete and current?
- **P** — Persuasion potential (0-25): How compelling is the overall package?

#### Scoring by Claim Type
| Claim | Key Evidence | Minimum EGCP for Filing |
|-------|-------------|------------------------|
| Custody Modification (MCL 722.27) | Change in circumstances + best interest | 65/100 |
| PPO Violation (MCL 600.2950) | Violation evidence + order copy | 70/100 |
| Housing Code (MCL 554.139) | Inspection reports + notice to landlord | 60/100 |
| Judicial Misconduct (MCR 2.003) | Pattern evidence + specific instances | 75/100 |
| Civil Rights (42 USC § 1983) | Constitutional violation + color of law | 70/100 |

### Tier 5: Gap Identification

#### Required Evidence Checklist by Lane
**Lane A (Custody — 2024-001507-DC)**:
- [ ] Current parenting time schedule compliance records
- [ ] School records for L.D.W. (current academic year)
- [ ] Medical records demonstrating capacity (MCL 722.23(c))
- [ ] Communication logs showing facilitation willingness (MCL 722.23(j))
- [ ] Any DV documentation for Factor (k) analysis

**Lane B (Housing — 2025-002760-CZ)**:
- [ ] Lease agreement and amendments
- [ ] Inspection reports or habitability evidence
- [ ] Notice to landlord (date-stamped)
- [ ] Rent payment records
- [ ] Photographic evidence with EXIF metadata
