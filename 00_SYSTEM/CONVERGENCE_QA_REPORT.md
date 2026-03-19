# CONVERGENCE QA REPORT
**Generated:** 2026-03-04 21:49:59
**Agent:** Agent-141 (LitigationOS QA)
**Stacks Scanned:** 45

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| Total Stacks | 45 |
| GO (>=80) | 8 |
| CONDITIONAL (60-79) | 34 |
| NO-GO (<60) | 3 |
| Average Score | 75.0/100 |

---

## 01_COA - Court of Appeals #366810

### [COND] 01_COA/APEX_FILING_STACK -- Score: 77.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 98/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **77.2/100** |

- **Files:** 8 total (0 md, 8 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 48 incomplete/broken citations out of 2597 total
- 67 unresolved placeholders found (samples: [TBD], [TBD], [TBD], [PLACEHOLDERS], [Entered November 4, 1981;
    effective January 1, 1982; rescinded by order en
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1981-12
────────────────────────────────────────────────────────────

  [4], [Entered December 4, 1981;
    effective February 1, 1982; superseded by AO 201
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1984-03
────────────────────────────────────────────────────────────

  [5], [Entered March 15, 1989; superseded
    by AO 2017-3, entered November 15, 20
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1990-11
────────────────────────────────────────────────────────────

  [10], [DATE — PLACEHOLDER], [DATE], [NAME
    — PLACEHOLDER])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 48 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 67 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [ GO ] 01_COA/COA_DRAFT_STACK -- Score: 82.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 85/100 |
| Placeholders | 100/100 |
| Compliance | 70/100 |
| Evidence | 80/100 |
| Service | 90/100 |
| **OVERALL** | **82.0/100** |

- **Files:** 11 total (6 md, 0 txt, 0 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: filing_instructions, readiness_score

---

### [COND] 01_COA/CONVERGED_FILING_STACK -- Score: 77.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 98/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **77.2/100** |

- **Files:** 45 total (37 md, 8 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 61 incomplete/broken citations out of 3880 total
- 141 unresolved placeholders found (samples: [TBD], [TBD], [TBD], [PLACEHOLDERS], [Entered November 4, 1981;
    effective January 1, 1982; rescinded by order en
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1981-12
────────────────────────────────────────────────────────────

  [4], [Entered December 4, 1981;
    effective February 1, 1982; superseded by AO 201
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1984-03
────────────────────────────────────────────────────────────

  [5], [Entered March 15, 1989; superseded
    by AO 2017-3, entered November 15, 20
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1990-11
────────────────────────────────────────────────────────────

  [10], [DATE], [DATE], [DATE])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 61 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 141 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 01_COA/COURT_READY -- Score: 71.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 50/100 |
| Placeholders | 100/100 |
| Compliance | 50/100 |
| Evidence | 90/100 |
| Service | 90/100 |
| **OVERALL** | **71.8/100** |

- **Files:** 8 total (0 md, 0 txt, 7 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, filing_instructions, readiness_score
- Low compliance -- few court rule references found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Ensure MCR/FRCP rule references are included for procedural compliance

---

### [ GO ] 01_COA/FINAL_BRIEF_STACK -- Score: 91.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 95/100 |
| Placeholders | 85/100 |
| Compliance | 85/100 |
| Evidence | 90/100 |
| Service | 90/100 |
| **OVERALL** | **91.5/100** |

- **Files:** 13 total (11 md, 0 txt, 2 pdf)
- **Verdict:** GO

**Issues:**
- 1 unresolved placeholder(s): [NAME, ADDRESS]

---

### [COND] 01_COA/MSC_STACK -- Score: 75.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 95/100 |
| Placeholders | 10/100 |
| Compliance | 85/100 |
| Evidence | 80/100 |
| Service | 90/100 |
| **OVERALL** | **75.0/100** |

- **Files:** 6 total (6 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- 12 unresolved placeholders found (samples: [DATE], [DATE], [DATE])

**Fix Instructions:**
- CRITICAL: Resolve all 12 placeholders -- document not ready for filing

---

### [COND] 01_COA/SCOTUS_FRAMEWORK -- Score: 73.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 80/100 |
| Placeholders | 100/100 |
| Compliance | 60/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **73.8/100** |

- **Files:** 4 total (4 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, exhibits/evidence
- Found 2 incomplete/broken citations out of 8 total
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- FIX: Resolve 2 broken citations (missing page numbers, placeholder text)
- ADD: Create exhibit list and attach supporting evidence

---

### [COND] 01_COA/SERVICE_PACKET -- Score: 78.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 75/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **78.2/100** |

- **Files:** 2 total (2 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, readiness_score
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence

---

## 02_TRIAL - 14th Circuit Trial Court

### [COND] 02_TRIAL/APEX_FILING_STACK -- Score: 76.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 93/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **76.5/100** |

- **Files:** 8 total (0 md, 8 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 350 incomplete/broken citations out of 4294 total
- 48 unresolved placeholders found (samples: [XXX], [TBD], [TBD], [TBD], [Insert Email Address], [Insert Phone Number], [PLACEHOLDERS], [Entered April 19, 1988; rescinded
    February 23, 2006.], [Entered September 9, 1994;
    effective September 16, 1994.], [Entered December 21, 1994.])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 350 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 48 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 02_TRIAL/CONVERGED_FILING_STACK -- Score: 75.7/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 88/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **75.7/100** |

- **Files:** 77 total (69 md, 8 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 2334 incomplete/broken citations out of 16655 total
- 187 unresolved placeholders found (samples: [XXXX], [XXX], [TBD], [TBD], [TBD], [insert exemption cited], [Insert specific grounds for appeal, such as:
   - The records are not exempt because they concern matters of public record
   - The claimed exemption does not apply to the specific records requested
   - The public interest in disclosure outweighs any privacy interest
   - The agency failed to adequately segregate exempt from non-exempt material as required by MCL 15.244(1)], [Insert Email Address], [PLACEHOLDERS], [Entered April 19, 1988; rescinded
    February 23, 2006.])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 2334 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 187 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [ GO ] 02_TRIAL/DISCOVERY_STACK -- Score: 81.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 95/100 |
| Placeholders | 65/100 |
| Compliance | 85/100 |
| Evidence | 75/100 |
| Service | 90/100 |
| **OVERALL** | **81.5/100** |

- **Files:** 12 total (6 md, 0 txt, 6 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: readiness_score
- 4 unresolved placeholders found: [DATE], [DATE], [DATE]

---

### [ GO ] 02_TRIAL/DISQUALIFY_PACKAGE -- Score: 92.1/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 99/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 100/100 |
| Service | 90/100 |
| **OVERALL** | **92.1/100** |

- **Files:** 57 total (10 md, 0 txt, 42 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: readiness_score
- Found 1 incomplete/broken citations out of 129 total

---

### [COND] 02_TRIAL/FULL_14TH_STACK -- Score: 72.1/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 99/100 |
| Placeholders | 10/100 |
| Compliance | 80/100 |
| Evidence | 100/100 |
| Service | 70/100 |
| **OVERALL** | **72.1/100** |

- **Files:** 73 total (18 md, 0 txt, 50 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: readiness_score
- Found 1 incomplete/broken citations out of 269 total
- 13 unresolved placeholders found (samples: [Address on file], [Address], [Address on file])
- Service template has unfilled fields

**Fix Instructions:**
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 1 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 13 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [ GO ] 02_TRIAL/JUDICIAL_PACKET -- Score: 81.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 70/100 |
| Placeholders | 100/100 |
| Compliance | 70/100 |
| Evidence | 90/100 |
| Service | 90/100 |
| **OVERALL** | **81.2/100** |

- **Files:** 32 total (1 md, 2 txt, 9 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: verification/affidavit, readiness_score

---

### [COND] 02_TRIAL/JUDICIAL_PACKET_R2 -- Score: 61.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 42/100 |
| Citations | 70/100 |
| Placeholders | 85/100 |
| Compliance | 65/100 |
| Evidence | 75/100 |
| Service | 20/100 |
| **OVERALL** | **61.0/100** |

- **Files:** 14 total (1 md, 0 txt, 2 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, service/certificate, filing_instructions, readiness_score
- 1 unresolved placeholder(s): [address / phone / email]
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 1 remaining placeholder(s)
- ADD: Create proof of service / certificate of service document

---

### [NOGO] 02_TRIAL/PROBATE_STACK -- Score: 54.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 14/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 60/100 |
| Evidence | 40/100 |
| Service | 20/100 |
| **OVERALL** | **54.8/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** NO-GO

**Issues:**
- Missing components: caption/header, verification/affidavit, service/certificate, exhibits/evidence, filing_instructions, readiness_score
- No exhibit references or evidence files found
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add caption/header document to this stack
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence
- ADD: Create proof of service / certificate of service document

---

### [COND] 02_TRIAL/SHADY_OAKS -- Score: 72.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 98/100 |
| Placeholders | 10/100 |
| Compliance | 80/100 |
| Evidence | 100/100 |
| Service | 70/100 |
| **OVERALL** | **72.0/100** |

- **Files:** 446 total (22 md, 218 txt, 93 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: readiness_score
- Found 12 incomplete/broken citations out of 849 total
- 16 unresolved placeholders found (samples: [TBD -- Discovery], [TBD -- Discovery], [TBD -- Discovery], [Insert date], [Insert date], [date], [DATE], [date], [Address, Phone, Email], [Address])
- Service template has unfilled fields

**Fix Instructions:**
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 12 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 16 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [ GO ] 02_TRIAL/SHADY_OAKS_EXPANDED_STACK -- Score: 83.3/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 94/100 |
| Placeholders | 85/100 |
| Compliance | 80/100 |
| Evidence | 80/100 |
| Service | 70/100 |
| **OVERALL** | **83.3/100** |

- **Files:** 13 total (9 md, 0 txt, 0 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: verification/affidavit
- Found 3 incomplete/broken citations out of 45 total
- 1 unresolved placeholder(s): [Address]
- Service template has unfilled fields

---

### [COND] 02_TRIAL/WATSON_TORT -- Score: 76.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 99/100 |
| Placeholders | 44/100 |
| Compliance | 85/100 |
| Evidence | 100/100 |
| Service | 70/100 |
| **OVERALL** | **76.2/100** |

- **Files:** 18 total (9 md, 0 txt, 9 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: filing_instructions, readiness_score
- Found 2 incomplete/broken citations out of 281 total
- 7 unresolved placeholders found (samples: [Address on file with Court], [Address on file with Court], [address])
- Service template has unfilled fields

**Fix Instructions:**
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 2 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 7 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [ GO ] 02_TRIAL/WATSON_TORT_STACK -- Score: 87.7/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 98/100 |
| Placeholders | 85/100 |
| Compliance | 80/100 |
| Evidence | 80/100 |
| Service | 70/100 |
| **OVERALL** | **87.7/100** |

- **Files:** 11 total (9 md, 0 txt, 0 pdf)
- **Verdict:** GO

**Issues:**
- Found 2 incomplete/broken citations out of 84 total
- 1 unresolved placeholder(s): [ADDRESS]
- Service template has unfilled fields

---

## 03_FED - Federal Section 1983

### [COND] 03_FED/APEX_FILING_STACK -- Score: 76.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 95/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **76.8/100** |

- **Files:** 7 total (0 md, 7 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 39 incomplete/broken citations out of 779 total
- 22 unresolved placeholders found (samples: [Entered March 2, 1983.], [Entered March 28, 1983; rescinded
    February 6, 2007.], [Entered October 7, 1983.], [date], [DATE], [NAME], [ADDRESS TO BE PROVIDED UPON FILING], [ADDRESS PLACEHOLDER], [ADDRESS PLACEHOLDER], <<<  and  Denying  Post-Judgment Relief *   The  May  16, 2025  order
    imposing  a filing  >>)
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 39 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 22 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 03_FED/CONVERGED_FILING_STACK -- Score: 77.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 97/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **77.0/100** |

- **Files:** 35 total (28 md, 7 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 41 incomplete/broken citations out of 1423 total
- 135 unresolved placeholders found (samples: [Entered March 2, 1983.], [Entered March 28, 1983; rescinded
    February 6, 2007.], [Entered October 7, 1983.], [DATE — to be specified], [DATE], [DATE], [NAME], [NAME], [NAME], [Address to be served via Summons])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 41 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 135 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [NOGO] 03_FED/EDMI_STACK -- Score: 55.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 14/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 65/100 |
| Evidence | 40/100 |
| Service | 20/100 |
| **OVERALL** | **55.5/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** NO-GO

**Issues:**
- Missing components: caption/header, verification/affidavit, service/certificate, exhibits/evidence, filing_instructions, readiness_score
- No exhibit references or evidence files found
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add caption/header document to this stack
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence
- ADD: Create proof of service / certificate of service document

---

### [ GO ] 03_FED/FAIR_HOUSING_STACK -- Score: 85.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 95/100 |
| Placeholders | 85/100 |
| Compliance | 80/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **85.0/100** |

- **Files:** 5 total (5 md, 0 txt, 0 pdf)
- **Verdict:** GO

**Issues:**
- Missing components: verification/affidavit
- 1 unresolved placeholder(s): [Address]
- Service template has unfilled fields

---

### [COND] 03_FED/FINAL_1983_STACK -- Score: 78.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 80/100 |
| Service | 20/100 |
| **OVERALL** | **78.0/100** |

- **Files:** 5 total (5 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, service/certificate
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- ADD: Create proof of service / certificate of service document

---

### [COND] 03_FED/SIXTH_CIRCUIT_STACK -- Score: 74.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 75/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **74.8/100** |

- **Files:** 2 total (2 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, exhibits/evidence, readiness_score
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence

---

### [COND] 03_FED/WDMI_FULL_STACK -- Score: 79.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 95/100 |
| Placeholders | 20/100 |
| Compliance | 95/100 |
| Evidence | 100/100 |
| Service | 70/100 |
| **OVERALL** | **79.5/100** |

- **Files:** 32 total (15 md, 0 txt, 16 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- 10 unresolved placeholders found (samples: [ADDRESS], [ADDRESS], [ADDRESS per state records], [Number of copies])
- Service template has unfilled fields

**Fix Instructions:**
- CRITICAL: Resolve all 10 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

## 04_MSC - Michigan Supreme Court

### [COND] 04_MSC/ORIGINAL_ACTION -- Score: 76.7/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 99/100 |
| Placeholders | 44/100 |
| Compliance | 85/100 |
| Evidence | 90/100 |
| Service | 90/100 |
| **OVERALL** | **76.7/100** |

- **Files:** 7 total (7 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: filing_instructions, readiness_score
- Found 2 incomplete/broken citations out of 185 total
- 7 unresolved placeholders found (samples: [Date], [Date], [Date])

**Fix Instructions:**
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 2 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 7 placeholders -- document not ready for filing

---

## 06_EMER - Emergency Filings

### [COND] 06_EMER/ADMIN_COMPLAINTS -- Score: 60.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 95/100 |
| Placeholders | 10/100 |
| Compliance | 75/100 |
| Evidence | 90/100 |
| Service | 20/100 |
| **OVERALL** | **60.8/100** |

- **Files:** 7 total (7 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, service/certificate
- 28 unresolved placeholders found (samples: [DATE], [DATE], [DATE], [Address], [Address — verify registered agent], [Address — NYC-based])
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- CRITICAL: Resolve all 28 placeholders -- document not ready for filing
- ADD: Create proof of service / certificate of service document

---

### [COND] 06_EMER/APEX_FILING_STACK -- Score: 76.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 93/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **76.5/100** |

- **Files:** 7 total (0 md, 7 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 256 incomplete/broken citations out of 3068 total
- 60 unresolved placeholders found (samples: [XXX], [TBD], [TBD], [TBD], [Insert contents of Exhibit A
    here as filed or at
    Source: master_timeline | Ref: evidence_quotes

  [3500], [Entered October 7, 1983.], [Entered March 15, 1989; superseded
    by AO 2017-3, entered November 15, 20
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1989-07
────────────────────────────────────────────────────────────

  [45], [Entered October 10, 1995.], [DATE], [Date:
    September 19, 2024])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 256 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 60 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 06_EMER/CONVERGED_FILING_STACK -- Score: 75.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 100/100 |
| Citations | 87/100 |
| Placeholders | 10/100 |
| Compliance | 100/100 |
| Evidence | 90/100 |
| Service | 70/100 |
| **OVERALL** | **75.5/100** |

- **Files:** 37 total (30 md, 7 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Found 1819 incomplete/broken citations out of 11394 total
- 147 unresolved placeholders found (samples: [XXX], [TBD], [TBD], [TBD], [Insert contents of Exhibit A
    here as filed or at
    Source: master_timeline | Ref: evidence_quotes

  [3500], [Entered October 7, 1983.], [Entered March 15, 1989; superseded
    by AO 2017-3, entered November 15, 20
    Source: master_timeline | Ref: evidence_quotes

────────────────────────────────────────────────────────────
  1989-07
────────────────────────────────────────────────────────────

  [45], [Entered October 10, 1995.], [DATE], [DATE])
- Service template has unfilled fields

**Fix Instructions:**
- FIX: Resolve 1819 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 147 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 06_EMER/FINAL_EMERGENCY_PACKAGE -- Score: 68.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 95/100 |
| Placeholders | 36/100 |
| Compliance | 85/100 |
| Evidence | 60/100 |
| Service | 70/100 |
| **OVERALL** | **68.0/100** |

- **Files:** 9 total (7 md, 0 txt, 1 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, readiness_score
- 8 unresolved placeholders found (samples: [XXXX], [Date of Filing], [Date], [Date], [Address on file with the Court], [Address])
- Service template has unfilled fields

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add readiness_score document to this stack
- CRITICAL: Resolve all 8 placeholders -- document not ready for filing
- FIX: Fill in all party names and addresses in proof of service

---

### [COND] 06_EMER/FINAL_EMERGENCY_STACK -- Score: 71.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 85/100 |
| Citations | 99/100 |
| Placeholders | 52/100 |
| Compliance | 80/100 |
| Evidence | 40/100 |
| Service | 70/100 |
| **OVERALL** | **71.5/100** |

- **Files:** 11 total (10 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence
- Found 1 incomplete/broken citations out of 110 total
- 6 unresolved placeholders found (samples: [Address], [Address], [Address])
- No exhibit references or evidence files found
- Service template has unfilled fields

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- FIX: Resolve 1 broken citations (missing page numbers, placeholder text)
- CRITICAL: Resolve all 6 placeholders -- document not ready for filing
- ADD: Create exhibit list and attach supporting evidence
- FIX: Fill in all party names and addresses in proof of service

---

### [NOGO] 06_EMER/HEALTHWEST_INVESTIGATION -- Score: 53.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 28/100 |
| Citations | 50/100 |
| Placeholders | 100/100 |
| Compliance | 50/100 |
| Evidence | 60/100 |
| Service | 20/100 |
| **OVERALL** | **53.0/100** |

- **Files:** 98 total (0 md, 0 txt, 8 pdf)
- **Verdict:** NO-GO

**Issues:**
- Missing components: verification/affidavit, service/certificate, exhibits/evidence, filing_instructions, readiness_score
- Low compliance -- few court rule references found
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Ensure MCR/FRCP rule references are included for procedural compliance
- ADD: Create proof of service / certificate of service document

---

### [COND] 06_EMER/HUD_COMPLAINT -- Score: 76.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 60/100 |
| Evidence | 90/100 |
| Service | 20/100 |
| **OVERALL** | **76.5/100** |

- **Files:** 11 total (5 md, 0 txt, 6 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: service/certificate, readiness_score
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create proof of service / certificate of service document

---

### [COND] 06_EMER/LARA_COMPLAINT -- Score: 78.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 71/100 |
| Citations | 98/100 |
| Placeholders | 100/100 |
| Compliance | 60/100 |
| Evidence | 100/100 |
| Service | 20/100 |
| **OVERALL** | **78.5/100** |

- **Files:** 9 total (4 md, 0 txt, 5 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: service/certificate, readiness_score
- Found 2 incomplete/broken citations out of 113 total
- No proof of service document found

**Fix Instructions:**
- ADD: Create/add service/certificate document to this stack
- ADD: Create/add readiness_score document to this stack
- FIX: Resolve 2 broken citations (missing page numbers, placeholder text)
- ADD: Create proof of service / certificate of service document

---

## 06_CS - Complaint Stacks (New)

### [COND] 06_CS/AG_CIVIL_RIGHTS -- Score: 77.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 85/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 65/100 |
| Service | 90/100 |
| **OVERALL** | **77.8/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack

---

### [COND] 06_CS/BAR_GRIEVANCE -- Score: 65.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 30/100 |
| Placeholders | 100/100 |
| Compliance | 55/100 |
| Evidence | 65/100 |
| Service | 90/100 |
| **OVERALL** | **65.8/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score
- No legal citations found in any document
- Low compliance -- few court rule references found

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Insert proper legal citations (MCL, MCR, case law) throughout
- ADD: Ensure MCR/FRCP rule references are included for procedural compliance

---

### [COND] 06_CS/COA_EMERGENCY -- Score: 79.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 65/100 |
| Service | 90/100 |
| **OVERALL** | **79.2/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack

---

### [COND] 06_CS/COURT_MOTIONS -- Score: 71.8/100

| Criteria | Score |
|----------|-------|
| Completeness | 42/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **71.8/100** |

- **Files:** 3 total (3 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: verification/affidavit, exhibits/evidence, filing_instructions, readiness_score
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add verification/affidavit document to this stack
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence

---

### [COND] 06_CS/HHS_OCR_HIPAA -- Score: 75.5/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 85/100 |
| Placeholders | 100/100 |
| Compliance | 65/100 |
| Evidence | 65/100 |
| Service | 90/100 |
| **OVERALL** | **75.5/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack

---

### [COND] 06_CS/JTC_COMPLAINT -- Score: 77.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 70/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 75/100 |
| Service | 90/100 |
| **OVERALL** | **77.0/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack

---

### [COND] 06_CS/MDCR_COMPLAINT -- Score: 74.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 85/100 |
| Placeholders | 100/100 |
| Compliance | 80/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **74.0/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence

---

### [COND] 06_CS/MDHHS_RECIPIENT_RIGHTS -- Score: 73.2/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 65/100 |
| Evidence | 40/100 |
| Service | 90/100 |
| **OVERALL** | **73.2/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score
- No exhibit references or evidence files found

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack
- ADD: Create exhibit list and attach supporting evidence

---

### [COND] 06_CS/PROSECUTOR_ETHICS -- Score: 77.0/100

| Criteria | Score |
|----------|-------|
| Completeness | 57/100 |
| Citations | 95/100 |
| Placeholders | 100/100 |
| Compliance | 65/100 |
| Evidence | 65/100 |
| Service | 90/100 |
| **OVERALL** | **77.0/100** |

- **Files:** 1 total (1 md, 0 txt, 0 pdf)
- **Verdict:** CONDITIONAL

**Issues:**
- Missing components: exhibits/evidence, filing_instructions, readiness_score

**Fix Instructions:**
- ADD: Create/add exhibits/evidence document to this stack
- ADD: Create/add filing_instructions document to this stack
- ADD: Create/add readiness_score document to this stack

---

## PRIORITY ACTION LIST (Stacks Below 80)

| # | Stack | Score | Verdict | Top Fix |
|---|-------|-------|---------|---------|
| 1 | 06_EMER/HEALTHWEST_INVESTIGATION | 53.0/100 | NO-GO | ADD: Create/add verification/affidavit document to this stack |
| 2 | 02_TRIAL/PROBATE_STACK | 54.8/100 | NO-GO | ADD: Create/add caption/header document to this stack |
| 3 | 03_FED/EDMI_STACK | 55.5/100 | NO-GO | ADD: Create/add caption/header document to this stack |
| 4 | 06_EMER/ADMIN_COMPLAINTS | 60.8/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 5 | 02_TRIAL/JUDICIAL_PACKET_R2 | 61.0/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 6 | 06_CS/BAR_GRIEVANCE | 65.8/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 7 | 06_EMER/FINAL_EMERGENCY_PACKAGE | 68.0/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 8 | 06_EMER/FINAL_EMERGENCY_STACK | 71.5/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 9 | 01_COA/COURT_READY | 71.8/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 10 | 06_CS/COURT_MOTIONS | 71.8/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 11 | 02_TRIAL/SHADY_OAKS | 72.0/100 | CONDITIONAL | ADD: Create/add readiness_score document to this stack |
| 12 | 02_TRIAL/FULL_14TH_STACK | 72.1/100 | CONDITIONAL | ADD: Create/add readiness_score document to this stack |
| 13 | 06_CS/MDHHS_RECIPIENT_RIGHTS | 73.2/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 14 | 01_COA/SCOTUS_FRAMEWORK | 73.8/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 15 | 06_CS/MDCR_COMPLAINT | 74.0/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 16 | 03_FED/SIXTH_CIRCUIT_STACK | 74.8/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 17 | 01_COA/MSC_STACK | 75.0/100 | CONDITIONAL | CRITICAL: Resolve all 12 placeholders -- document not ready for filing |
| 18 | 06_CS/HHS_OCR_HIPAA | 75.5/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 19 | 06_EMER/CONVERGED_FILING_STACK | 75.5/100 | CONDITIONAL | FIX: Resolve 1819 broken citations (missing page numbers, placeholder text) |
| 20 | 02_TRIAL/CONVERGED_FILING_STACK | 75.7/100 | CONDITIONAL | FIX: Resolve 2334 broken citations (missing page numbers, placeholder text) |
| 21 | 02_TRIAL/WATSON_TORT | 76.2/100 | CONDITIONAL | ADD: Create/add filing_instructions document to this stack |
| 22 | 02_TRIAL/APEX_FILING_STACK | 76.5/100 | CONDITIONAL | FIX: Resolve 350 broken citations (missing page numbers, placeholder text) |
| 23 | 06_EMER/APEX_FILING_STACK | 76.5/100 | CONDITIONAL | FIX: Resolve 256 broken citations (missing page numbers, placeholder text) |
| 24 | 06_EMER/HUD_COMPLAINT | 76.5/100 | CONDITIONAL | ADD: Create/add service/certificate document to this stack |
| 25 | 04_MSC/ORIGINAL_ACTION | 76.7/100 | CONDITIONAL | ADD: Create/add filing_instructions document to this stack |
| 26 | 03_FED/APEX_FILING_STACK | 76.8/100 | CONDITIONAL | FIX: Resolve 39 broken citations (missing page numbers, placeholder text) |
| 27 | 03_FED/CONVERGED_FILING_STACK | 77.0/100 | CONDITIONAL | FIX: Resolve 41 broken citations (missing page numbers, placeholder text) |
| 28 | 06_CS/JTC_COMPLAINT | 77.0/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 29 | 06_CS/PROSECUTOR_ETHICS | 77.0/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 30 | 01_COA/APEX_FILING_STACK | 77.2/100 | CONDITIONAL | FIX: Resolve 48 broken citations (missing page numbers, placeholder text) |
| 31 | 01_COA/CONVERGED_FILING_STACK | 77.2/100 | CONDITIONAL | FIX: Resolve 61 broken citations (missing page numbers, placeholder text) |
| 32 | 06_CS/AG_CIVIL_RIGHTS | 77.8/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 33 | 03_FED/FINAL_1983_STACK | 78.0/100 | CONDITIONAL | ADD: Create/add verification/affidavit document to this stack |
| 34 | 01_COA/SERVICE_PACKET | 78.2/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 35 | 06_EMER/LARA_COMPLAINT | 78.5/100 | CONDITIONAL | ADD: Create/add service/certificate document to this stack |
| 36 | 06_CS/COA_EMERGENCY | 79.2/100 | CONDITIONAL | ADD: Create/add exhibits/evidence document to this stack |
| 37 | 03_FED/WDMI_FULL_STACK | 79.5/100 | CONDITIONAL | CRITICAL: Resolve all 10 placeholders -- document not ready for filing |

---
*Report generated by Agent-141 at 2026-03-04 21:49:59*