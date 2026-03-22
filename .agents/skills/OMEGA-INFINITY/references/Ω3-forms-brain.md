# Ω3 Forms Brain — OMEGA-INFINITY Reference
> Module 3 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose
The forms brain catalogs every Michigan SCAO court form relevant to this litigation, maps forms to case lanes, defines the auto-fill protocol for party data injection, and governs filing package assembly. Every filing must use the correct form when a mandatory form exists — custom pleadings are appropriate only where no SCAO form covers the need.

---

## 1. SCAO Forms Catalog — Structure & Categories

Michigan's State Court Administrative Office (SCAO) publishes standardized court forms. Query for the current catalog:
```sql
SELECT form_number, form_name, category, court_level, is_mandatory
FROM court_forms_complete
ORDER BY category, form_number;
```

### Form Number Prefix Guide

| Prefix | Category | Description | Typical Use |
|--------|----------|-------------|-------------|
| **MC** | Multi-Court | Forms used across court levels | Service (MC 12), Subpoena (MC 11), General motions |
| **FOC** | Friend of the Court | FOC-specific forms | Support, custody evaluation, objections |
| **CC** | Circuit Court — Civil | Civil division forms | Complaints, answers, summary disposition |
| **DC** | District Court | District court forms | Small claims, landlord-tenant |
| **PC** | Probate Court | Probate and guardianship | Guardianship, conservatorship |
| **JC** | Juvenile Court | Juvenile/child protective | Abuse/neglect, delinquency |
| **COA** | Court of Appeals | Appellate forms | Claim of appeal, briefs, applications |
| **MSC** | Michigan Supreme Court | Supreme court forms | Applications for leave, extraordinary writs |
| **SCAO** | Administrative | Court admin forms | Fee waivers, interpreter requests |
| **TF** | Transfer | Case transfer forms | Venue change, consolidation |

### Category Counts (query for current numbers)
```sql
SELECT 
  SUBSTR(form_number, 1, INSTR(form_number, ' ') - 1) AS prefix,
  COUNT(*) AS form_count
FROM court_forms_complete
GROUP BY prefix
ORDER BY form_count DESC;
```

### Federal Forms (Lane C only)
Federal forms are NOT in `court_forms_complete` — they follow the USDC WDMI local rules:
- Civil Cover Sheet (JS 44)
- Complaint (no mandatory form — custom pleading)
- Summons (AO 440)
- IFP Application (AO 240)

---

## 2. Form-to-Lane Mapping

### Lane A — Custody (14th Circuit Family Division)

| Form | Name | Use | Priority |
|------|------|-----|----------|
| MC 12 | Proof of Service | Every filing | 1 |
| MC 11 | Subpoena | Compel witness attendance or document production | 1 |
| FOC 10 | Uniform Child Support Order | Support modification | 1 |
| FOC 10a | Uniform Support Order, Ex Parte and Order | Emergency support | 1 |
| FOC 13 | Order Regarding Parenting Time | Parenting time modification | 1 |
| CC 375 | Motion and Verification | General motion | 1 |
| MC 15 | Motion | Simple motion | 1 |
| MC 16 | General Order | Proposed order | 1 |
| FOC 30 | Verified Statement and Application for IV-D Services | IV-D services | 2 |
| FOC 50 | Objection to Ex Parte Order | FOC objection | 1 |
| FOC 51 | Response to Objection to Ex Parte Order | Response to FOC objection | 1 |
| MC 07 | Response to Motion | Respond to opposing motions | 1 |
| MC 20 | Fee Waiver Request | Indigency | 2 |
| SCAO 123 | Verified Statement of Inability to Pay | Fee waiver support | 2 |

### Lane B — Housing (14th Circuit Civil Division)

| Form | Name | Use | Priority |
|------|------|-----|----------|
| MC 12 | Proof of Service | Every filing | 1 |
| CC 375 | Motion and Verification | General motion | 1 |
| DC 104a | Complaint for Land Contract/Summary Proceedings | Property recovery | 1 |
| DC 107 | Summons and Complaint — Summary Proceedings | Eviction/possession | 1 |
| CC 250 | Complaint | Civil complaint | 1 |
| MC 01 | Case Inventory Addendum | Case management | 2 |

### Lane D — PPO (14th Circuit)

| Form | Name | Use | Priority |
|------|------|-----|----------|
| MC 12 | Proof of Service | Every filing | 1 |
| CC 375 | Motion and Verification | General motion | 1 |
| CC 377 | Personal Protection Order (Domestic) | PPO petition or response | 1 |
| CC 378 | Personal Protection Order (Non-Domestic) | Non-domestic PPO | 1 |
| CC 380 | Motion to Terminate PPO | Terminate PPO | 1 |
| CC 381 | Order Following Hearing on PPO | Post-hearing order | 1 |
| MC 15 | Motion | Contempt motion | 1 |
| MC 255 | Order to Show Cause | Initiate contempt | 1 |

### Lane E — Judicial Misconduct (JTC)

| Form | Name | Use | Priority |
|------|------|-----|----------|
| JTC Complaint Form | Request for Investigation | JTC complaint (not SCAO — from JTC website) | 1 |
| MC 12 | Proof of Service | If filing motion in underlying case | 1 |
| CC 375 | Motion and Verification | Disqualification motion (MCR 2.003) | 1 |

### Lane F — Appellate (Michigan Court of Appeals)

| Form | Name | Use | Priority |
|------|------|-----|----------|
| COA Claim of Appeal | Claim of Appeal | Initiating appeal | 1 |
| COA Application for Leave | Application for Leave to Appeal | Discretionary appeal | 1 |
| COA Docket Statement | Docket Statement | Required with claim of appeal | 1 |
| COA Mediation Questionnaire | Mediation Questionnaire | Required with claim/application | 1 |
| MC 12 | Proof of Service | Every appellate filing | 1 |
| MC 20 | Fee Waiver Request | Appellate fee waiver | 2 |

---

## 3. Auto-Fill Protocol — Party Data Injection

Every form contains fields that must be populated with verified party data. NEVER fabricate names, addresses, or bar numbers.

### Verified Party Data (SINGLE SOURCE OF TRUTH)

```python
PARTY_DATA = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17",
        "city_state_zip": "North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "bar_number": None,  # Self-represented
        "role": "Plaintiff/Petitioner"
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive",
        "city_state_zip": "Norton Shores, MI 49441",
        "phone": None,  # Not available
        "email": None,   # Not available
        "bar_number": None,  # Self-represented (Barnes withdrew)
        "role": "Defendant/Respondent"
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Judicial Circuit Court",
        "division": "Family Division",
        "county": "Muskegon"
    },
    "child": {
        "initials": "L.D.W.",
        "full_name": "[REDACTED per MCR 8.119(H)]"
    },
    "foc": {
        "name": "Pamela Rusco",
        "address": "990 Terrace St, Muskegon, MI 49442"
    },
    "former_attorney": {
        "name": "Jennifer Barnes",
        "bar_number": "P55406",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW"
    }
}
```

### Auto-Fill Field Mapping

| Form Field | Source | Value |
|------------|--------|-------|
| Plaintiff/Petitioner Name | `PARTY_DATA.plaintiff.name` | Andrew James Pigors |
| Defendant/Respondent Name | `PARTY_DATA.defendant.name` | Emily A. Watson |
| Case Number | Lane-specific case number | See lane definitions in Ω1 |
| Court | `PARTY_DATA.judge.court` | 14th Judicial Circuit Court |
| County | `PARTY_DATA.judge.county` | Muskegon |
| Judge | `PARTY_DATA.judge.name` | Hon. Jenny L. McNeill |
| Plaintiff Address | `PARTY_DATA.plaintiff.address` | 1977 Whitehall Road, Lot 17 |
| Minor Child | `PARTY_DATA.child.initials` | L.D.W. |

### Auto-Fill Rules
1. **NEVER guess a party name.** If a field requires a name not in PARTY_DATA, insert `[VERIFY — name required]`
2. **NEVER invent a bar number.** If a field requires a bar number, query `litigation_context.db` or leave blank.
3. **Child's full name MUST NOT appear** on any form filed with the court. Use initials only.
4. **Ronald Berry is NOT an attorney.** He has no bar number. He should never appear in an attorney field.
5. **Case numbers are lane-specific.** Always verify the correct case number for the lane.

---

## 4. Filing Package Assembly

Every filing is a package, not a single document. The standard package structure:

### Package Components (in order)

1. **Lead Document** — The primary filing (motion, brief, petition, complaint)
   - Must be the correct SCAO form if a mandatory form exists
   - Custom pleading if no applicable SCAO form
   - Properly captioned with case number, parties, court, judge

2. **Supporting Affidavit** — Sworn statement of facts supporting the filing
   - Must be sworn under penalty of perjury
   - Every factual assertion must be traceable to `evidence_quotes`
   - Paragraph classes: IDENTITY_CAPACITY, DATE_SPECIFIC_EVENT, DOCUMENT_RECITAL, PERSONAL_KNOWLEDGE, EXHIBIT_AUTH, VERIFICATION
   - Signature block: `Andrew James Pigors, Plaintiff, In Propria Persona`

3. **Exhibit Index** — List of all attached exhibits with Bates numbers
   - Format: Exhibit [Letter/Number] — Description — Bates Range
   - Must match the exhibit references in the affidavit and motion
   - Must match the Bates stamps on the actual exhibits

4. **Exhibits** — The evidence items, Bates-stamped
   - Each exhibit tabbed and labeled
   - Bates numbers on every page
   - Pulled from `exhibit_index` and `bates_registry`

5. **Proposed Order** — The order the court is being asked to sign
   - Include all requested relief
   - Leave signature line for judge blank
   - Include IT IS SO ORDERED language

6. **Proof of Service (MC 12)** — REQUIRED FOR EVERY FILING
   - Must be completed AFTER service is effectuated
   - Record who was served, when, how (personal, mail, electronic)
   - If serving Emily A. Watson: use her address at 2160 Garland Drive, Norton Shores, MI 49441
   - If Barnes withdrew: serve Emily directly, not Barnes

7. **Brief/Memorandum of Law** (if applicable)
   - Legal argument supporting the motion
   - IRAC structure with authority citations
   - Not required for simple motions but strengthens complex ones

### Package Assembly Query
```sql
SELECT 
  fp.package_id, fp.vehicle_name, fp.status,
  fp.lead_document, fp.affidavit, fp.exhibit_index_path,
  fp.proposed_order, fp.proof_of_service, fp.brief,
  (SELECT COUNT(*) FROM exhibit_index ei WHERE ei.filing_id = fp.package_id) AS exhibit_count,
  (SELECT COUNT(*) FROM bates_registry br WHERE br.filing_id = fp.package_id) AS bates_pages
FROM filing_packages fp
ORDER BY fp.status, fp.vehicle_name;
```

---

## 5. Priority Forms — The Critical 47

Query for the full priority-1 form list:
```sql
SELECT form_number, form_name, category, court_level
FROM court_forms_complete
WHERE priority = 1
ORDER BY category, form_number;
```

### Universal Priority Forms (ALL lanes)

| Form | Name | When Required |
|------|------|---------------|
| **MC 12** | Proof of Service | EVERY filing without exception |
| **MC 11** | Subpoena | When compelling witness attendance or document production |
| **MC 15** | Motion | Simple motions in any court |
| **MC 16** | General Order | Proposed order for any motion |
| **MC 07** | Response to Motion | Responding to any opposing motion |
| **MC 20** | Fee Waiver Request | When unable to pay filing fees |
| **CC 375** | Motion and Verification | Verified motions (circuit court) |

### MC 12 — Proof of Service (Deep Reference)

MC 12 is the single most critical form. Without proper service, any filing is jurisdictionally defective.

**Service Methods (MCR 2.105):**
1. **Personal Service** — Hand delivery to the party
2. **Service by Mail** — First-class mail to last known address (add 3 days to response time per MCR 2.108)
3. **Service by Electronic Means** — Only if parties consent (MCR 2.107(C)(4))
4. **Substituted Service** — At dwelling/business to person of suitable age (MCR 2.105(A)(2))

**MC 12 Required Fields:**
- Court name and case number
- Parties served (full name, address)
- Date of service
- Method of service
- Documents served (list each document)
- Signature of server
- If served by mail: date of mailing (service date = mailing date + 3 days)

**Service on Emily A. Watson:**
- Address: 2160 Garland Drive, Norton Shores, MI 49441
- Barnes WITHDREW — serve Emily directly
- Ronald Berry is NOT her attorney — do not serve him as agent

---

## 6. Form Validation Checklist

Before submitting any form, verify every item:

### Caption Validation
- [ ] Correct court name (14th Judicial Circuit Court / Michigan Court of Appeals / USDC WDMI)
- [ ] Correct division (Family / Civil / Criminal)
- [ ] Correct case number (Lane A: 2024-001507-DC, Lane D: 2023-5907-PP, Lane F: COA 366810)
- [ ] Correct county (Muskegon)
- [ ] Plaintiff name spelled correctly: Andrew James Pigors
- [ ] Defendant name spelled correctly: Emily A. Watson (NOT "Emily Ann", NOT "Emily M.", NOT "Tiffany")
- [ ] Judge name correct: Hon. Jenny L. McNeill (NOT "Amy McNeill")
- [ ] Child referred to by initials only: L.D.W.

### Content Validation
- [ ] All factual assertions traceable to `evidence_quotes` (query to verify)
- [ ] All legal citations exist in `authority_master_index` (query to verify)
- [ ] No placeholder text remaining: `[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`, `[VERIFY]`
- [ ] No hallucinated names (check against PARTY_DATA above)
- [ ] No hallucinated statistics (every number has a SQL query)
- [ ] Date references verified against `docket_events`

### Formatting Validation
- [ ] Proper font (Times New Roman 12pt or court-specified)
- [ ] Proper margins (1 inch or court-specified)
- [ ] Page numbers on every page
- [ ] Proper signature block with "In Propria Persona" designation
- [ ] Verification/notarization if required by form
- [ ] Bates numbers on all exhibits (check `bates_registry`)

### Service Validation
- [ ] MC 12 completed with correct service date
- [ ] Correct party served (Emily A. Watson, NOT Jennifer Barnes post-withdrawal)
- [ ] Correct address (2160 Garland Drive, Norton Shores, MI 49441)
- [ ] Correct method of service noted
- [ ] All documents listed on MC 12 match actual documents served

### E-Filing Validation (MiFILE)
- [ ] PDF format, text-searchable
- [ ] File size within MiFILE limits
- [ ] Correct filing type selected
- [ ] Correct case number selected in MiFILE
- [ ] Filing fee paid or fee waiver on file

---

## 7. SCAO Form URL Pattern

All SCAO forms are available online. URL construction:
```
https://www.courts.michigan.gov/siteassets/forms/scao/[form_number_lower_no_spaces].pdf
```

Examples:
- MC 12: `https://www.courts.michigan.gov/siteassets/forms/scao/mc12.pdf`
- CC 375: `https://www.courts.michigan.gov/siteassets/forms/scao/cc375.pdf`
- FOC 10: `https://www.courts.michigan.gov/siteassets/forms/scao/foc10.pdf`

Note: URL format may vary for some forms. Verify with:
```sql
SELECT form_number, url FROM court_forms_complete WHERE form_number = ?;
```

---

## 8. Key DB Tables

### court_forms_complete
The comprehensive SCAO form catalog.
- Key columns: `form_number`, `form_name`, `category`, `court_level`, `is_mandatory`, `url`, `description`, `instructions`, `priority`
- Query: `SELECT form_number, form_name, court_level FROM court_forms_complete WHERE category = ? ORDER BY form_number`

### court_forms
Simplified form reference (may be a subset of court_forms_complete).
- Query: `SELECT * FROM court_forms WHERE form_number = ?`

### form_filing_map
Maps forms to filing packages — which forms are included in which package.
- Key columns: `form_number`, `filing_id`, `role` (lead/attachment/service/exhibit_index/proposed_order)
- Query: `SELECT form_number, role FROM form_filing_map WHERE filing_id = ?`

### filing_packages
The assembled filing package records.
- Key columns: `package_id`, `vehicle_name`, `case_number`, `status`, `lead_document`, `affidavit`, `exhibit_index_path`, `proposed_order`, `proof_of_service`, `brief`, `created_date`
- Query: `SELECT package_id, vehicle_name, status FROM filing_packages WHERE status != 'filed' ORDER BY created_date DESC`

---

## Key DB Queries

### 1. Available forms for a lane
```sql
SELECT cf.form_number, cf.form_name, cf.is_mandatory
FROM court_forms_complete cf
WHERE cf.court_level = 'Circuit' 
  AND (cf.category = 'MC' OR cf.category = 'CC' OR cf.category = 'FOC')
ORDER BY cf.is_mandatory DESC, cf.form_number;
```

### 2. Missing forms in a filing package
```sql
SELECT cf.form_number, cf.form_name
FROM court_forms_complete cf
WHERE cf.is_mandatory = 1
  AND cf.form_number NOT IN (
    SELECT ffm.form_number FROM form_filing_map ffm WHERE ffm.filing_id = ?
  )
ORDER BY cf.form_number;
```

### 3. Filing packages missing MC 12
```sql
SELECT fp.package_id, fp.vehicle_name, fp.status
FROM filing_packages fp
WHERE fp.proof_of_service IS NULL
  AND fp.status NOT IN ('draft', 'template')
ORDER BY fp.vehicle_name;
```

### 4. Form usage frequency
```sql
SELECT ffm.form_number, cf.form_name, COUNT(*) AS usage_count
FROM form_filing_map ffm
JOIN court_forms_complete cf ON ffm.form_number = cf.form_number
GROUP BY ffm.form_number
ORDER BY usage_count DESC
LIMIT 20;
```

### 5. Complete package audit
```sql
SELECT 
  fp.package_id,
  fp.vehicle_name,
  CASE WHEN fp.lead_document IS NOT NULL THEN '✓' ELSE '✗' END AS has_lead,
  CASE WHEN fp.affidavit IS NOT NULL THEN '✓' ELSE '✗' END AS has_affidavit,
  CASE WHEN fp.exhibit_index_path IS NOT NULL THEN '✓' ELSE '✗' END AS has_exhibits,
  CASE WHEN fp.proposed_order IS NOT NULL THEN '✓' ELSE '✗' END AS has_order,
  CASE WHEN fp.proof_of_service IS NOT NULL THEN '✓' ELSE '✗' END AS has_mc12,
  CASE WHEN fp.brief IS NOT NULL THEN '✓' ELSE '✗' END AS has_brief
FROM filing_packages fp
WHERE fp.status != 'filed'
ORDER BY fp.vehicle_name;
```

---

## 9. E-Filing Protocol — MiFILE System

Michigan courts use the MiFILE e-filing system. All filings in the 14th Circuit must comply with MiFILE requirements.

### MiFILE Requirements
- **Format:** PDF (text-searchable preferred, scanned acceptable)
- **File size:** Maximum per document varies by court — check court website
- **Naming convention:** [FormNumber]_[Description]_[Date].pdf (e.g., MC12_ProofOfService_20260301.pdf)
- **Filing types:** Must select correct filing type from MiFILE dropdown
- **Case number:** Must select correct existing case or open new case
- **Service:** MiFILE can serve registered parties electronically (MCR 2.107(C)(4))

### MiFILE Checklist Before Submission
- [ ] All documents converted to PDF
- [ ] PDF is text-searchable (run OCR if scanned)
- [ ] Correct case number selected in MiFILE
- [ ] Correct filing type selected (motion, response, brief, etc.)
- [ ] All exhibits attached as separate PDFs or combined per court preference
- [ ] Filing fee paid or fee waiver (MC 20) on file
- [ ] MC 12 (Proof of Service) uploaded with filing or separately
- [ ] Confidential information redacted per MCR 1.109(D)(9)
- [ ] Child's full name does NOT appear anywhere — L.D.W. only

### Confidential Information (MCR 1.109(D)(9))
The following must be redacted from all public filings:
- Social Security numbers (use last 4 digits only)
- Financial account numbers (use last 4 digits only)
- Driver's license numbers
- Minor children's names (use initials per MCR 8.119(H))
- Dates of birth of minors (use year only if needed)

---

## 10. Form Substitution Rules

### When to Use SCAO Forms vs. Custom Pleadings

**MANDATORY SCAO Forms** — Must use the form, no custom alternative:
- MC 12 (Proof of Service) — always required
- PPO petition forms (CC 377, CC 378) — statutory requirement
- FOC forms (FOC 10, FOC 13) — required by FOC procedures
- COA forms (Claim of Appeal, Docket Statement) — required by appellate rules

**PREFERRED SCAO Forms** — Should use the form, custom is acceptable:
- MC 15 / CC 375 (Motion) — SCAO form preferred for simple motions
- MC 16 (General Order) — SCAO form preferred for proposed orders
- MC 07 (Response to Motion) — SCAO form acceptable but custom response is common

**Custom Pleading Required** — No applicable SCAO form:
- Complex motions with extensive factual argument
- Legal briefs and memoranda of law
- §1983 federal complaints (no Michigan SCAO form)
- JTC complaints (use JTC's own complaint form, not SCAO)
- Appellate briefs (formatted per MCR 7.212, not a fill-in form)

### Form Version Control
SCAO periodically updates forms. Always verify you are using the current version:
```sql
SELECT form_number, form_name, last_updated, url
FROM court_forms_complete
WHERE form_number = ?;
```
If the database version date is older than 6 months, check the SCAO website for updates before filing.

---

## 11. Emergency Filing Protocol

Certain situations require emergency or ex parte filings with compressed timelines.

### Ex Parte Motion Requirements (MCR 2.119(B))
- Must demonstrate irreparable injury or imminent danger
- Must show that giving notice to opposing party is impracticable or would defeat purpose
- Court may issue ex parte order but must schedule hearing within 14 days
- File MC 12 with proof of service on opposing party as soon as practicable after ex parte order

### Emergency Motion in Court of Appeals (MCR 7.216(A))
- Must file motion and supporting brief
- Must serve opposing party simultaneously (or explain why impossible)
- Must include: nature of emergency, irreparable harm if relief not granted, likelihood of success on merits

### Emergency Custody/PPO Filings
- Contact court clerk for emergency hearing availability
- File motion + affidavit + proposed order
- Serve Emily A. Watson at 2160 Garland Drive, Norton Shores, MI 49441
- File MC 12 immediately upon service

---

## Cross-Wiring Points

| This Brain | Links To | Via Column(s) |
|------------|----------|---------------|
| Ω3 Forms → Ω1 Litigation | `form_filing_map.filing_id` → `filing_packages.package_id` → lane routing |
| Ω3 Forms → Ω2 Evidence | `exhibit_index.filing_id` pulls exhibits into form package |
| Ω3 Forms → Ω2 Evidence | `bates_registry.filing_id` stamps pages for exhibit attachments |
| Ω3 Forms → Ω4 Rules | `court_forms_complete.court_level` determines which MCR rules govern form use |
| Ω1 Litigation → Ω3 Forms | `filing_readiness.vehicle_name` identifies which forms are needed |
| Ω2 Evidence → Ω3 Forms | Exhibit index is a form package component |
| Ω4 Rules → Ω3 Forms | MCR 2.113 (signing), MCR 2.107 (service), MCR 2.119 (motions) govern form requirements |
