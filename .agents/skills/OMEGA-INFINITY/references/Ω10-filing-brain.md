# Ω10 Filing Operations Brain — OMEGA-INFINITY Reference
> Module 10 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Govern all filing operations: package assembly, readiness scoring, court-specific compliance, service of process, e-filing via MiFILE, proposed order generation, and cross-lane filing coordination across 17 tracked vehicles.

---

## 1. Filing Package Registry (F1-F10)

### 1.1 Core Filing Packages

| ID | Title | Lane | Case Number | Status | Readiness | Exhibits | Dir |
|----|-------|------|-------------|--------|-----------|----------|-----|
| F1 | Emergency TRO / Custody Motion | A | 2024-001507-DC | ingested | 75.0 | 12 | PKG_F1_EMERGENCY_TRO |
| F2 | Shady Oaks Housing Complaint | B | 2025-002760-CZ | ingested | 75.0 | 11 | PKG_F2_SHADY_OAKS_COMPLAINT |
| F3 | Motion to Disqualify Judge McNeill (MCR 2.003) | A | 2024-001507-DC | ingested | 75.0 | 13 | PKG_F3_DISQUALIFICATION_MCR_2003 |
| F4 | Federal §1983 Civil Rights Complaint | A | NEW | ingested | 75.0 | 12 | PKG_F4_FEDERAL_S1983_COMPLAINT |
| F5 | Michigan Supreme Court Original Action | F | NEW | ingested | 75.0 | 12 | PKG_F5_MSC_ORIGINAL_ACTION |
| F6 | Judicial Tenure Commission Complaint | E | NEW | ingested | 75.0 | 11 | PKG_F6_JTC_COMPLAINT |
| F7 | Motion for Custody Modification | A | 2024-001507-DC | ingested | 75.0 | 13 | PKG_F7_CUSTODY_MODIFICATION |
| F8 | Motion to Terminate PPO | D | 2023-5907-PP | ingested | 75.0 | 12 | PKG_F8_PPO_TERMINATION |
| F9 | Court of Appeals Brief on Appeal | F | COA-366810 | ingested | 75.0 | 11 | PKG_F9_COA_BRIEF_ON_APPEAL |
| F10 | Court of Appeals Emergency Motion | F | COA-366810 | ingested | 75.0 | 11 | PKG_F10_COA_EMERGENCY_MOTION |

All packages stored under: `C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE\`

### 1.2 Extended Filing Vehicles (F-Series)

| ID | Title | Lane | Status | Readiness | Exhibits | Deadline |
|----|-------|------|--------|-----------|----------|----------|
| F-VAC | Omnibus Motion to Vacate | A | final_review | **95.0** | 38 | 2026-03-25 |
| F-MSC2 | MSC Bypass Application | F | complete | **90.0** | 17 | 2026-04-15 |
| F-DISQv2 | MCR 2.003 Disqualification v2 | E | draft | **82.0** | 39 | — |
| F-1983v2 | Amended 1983 Berry Conspiracy | C | draft | 80.0 | 25 | — |
| F-JTC | JTC Complaint McNeill | E | draft | 80.0 | 6 | 2026-05-01 |
| F-PPOterm | PPO Termination Motion | D | draft | 78.0 | 0 | — |
| F-CUSTmod | Custody Modification Motion | A | draft | 77.0 | 0 | — |

---

## 2. Filing Readiness Scoring System

### 2.1 Readiness Score Components

The `filing_readiness` table tracks 17 vehicles with composite scores from 0-100:

| Component | Weight | Measurement |
|-----------|--------|-------------|
| **Content completeness** | 30% | Word count, section coverage, argument density |
| **Exhibit attachment** | 20% | exhibit_count vs required exhibits |
| **Authority citation** | 15% | authority_count, citation verification status |
| **Placeholder resolution** | 15% | placeholder_count = 0 is target |
| **QA passage** | 10% | last_qa_date populated, qa_result = 'pass' |
| **Service readiness** | 10% | Service plan documented, MC 12 prepared |

### 2.2 Top Readiness Rankings (Current State)

| Rank | Vehicle | Score | Status | Blocker |
|------|---------|-------|--------|---------|
| 1 | **Omnibus Motion to Vacate (F-VAC)** | 95.0 | final_review | Final review before filing |
| 2 | **MSC Bypass Application (F-MSC2)** | 90.0 | complete | Deadline: 2026-04-15 |
| 3 | **MCR 2.003 Disqualification v2 (F-DISQv2)** | 82.0 | draft | Exhibits need finalization |
| 4 | **Amended 1983 Berry Conspiracy (F-1983v2)** | 80.0 | draft | Convergence lane coordination |
| 5 | **JTC Complaint McNeill (F-JTC)** | 80.0 | draft | 6 exhibits; deadline 2026-05-01 |

### 2.3 Readiness Query

```sql
SELECT vehicle_name, filing_id, status, readiness_score,
       placeholder_count, exhibit_count, authority_count,
       lane, deadline
FROM filing_readiness
ORDER BY readiness_score DESC;
```

---

## 3. Filing Assembly Pipeline

### 3.1 Seven-Stage Pipeline

```
STAGE 1: DRAFT
  └─ Generate initial filing from template + narrative context
  └─ Insert placeholders for unknown data: [ANDREW_REQUIRED], [INSERT], [ATTACH]
  └─ Status: 'draft'

STAGE 2: PLACEHOLDER RESOLUTION
  └─ Query litigation_context.db for every placeholder
  └─ Search filesystem across drives for existing content
  └─ Check COMPLETE_FILING_DATA_SUMMARY.txt
  └─ Only leave placeholder if ALL three searches return nothing

STAGE 3: DATA FILL
  └─ Populate from evidence_quotes, docket_events, claims, deadlines
  └─ Link exhibits by filing_id through filing_documents
  └─ Verify every statistic against a traceable SQL query

STAGE 4: AUTHORITY VERIFICATION
  └─ Validate all citations via filing_rule_map
  └─ Check authority_type, authority_number, requirement fields
  └─ Flag mandatory authorities not yet cited (mandatory = 1)

STAGE 5: EXHIBIT ASSEMBLY
  └─ Build exhibit index from filing_documents WHERE filing_id = ?
  └─ Assign Bates stamps where applicable
  └─ Verify exhibit authentication chain

STAGE 6: QA REVIEW
  └─ Run pre-filing QA (filing_readiness.qa_result)
  └─ Check service plan completeness
  └─ Verify proposed order attached if required
  └─ Confirm word count compliance (COA: 16,000 word limit for briefs)

STAGE 7: FILE
  └─ E-file via MiFILE (state courts)
  └─ CM/ECF (federal — USDC WDMI)
  └─ Mail/personal delivery for JTC, agencies
  └─ Update filing_readiness.status → 'filed'
```

### 3.2 Pipeline Status Tracking

```sql
-- Track a filing through the pipeline
SELECT fr.vehicle_name, fr.filing_id, fr.status, fr.readiness_score,
       fr.placeholder_count, fr.exhibit_count, fr.last_qa_date, fr.qa_result
FROM filing_readiness fr
WHERE fr.filing_id = ?;

-- Count documents per filing
SELECT fd.filing_id, COUNT(*) AS doc_count,
       SUM(fd.word_count) AS total_words
FROM filing_documents fd
GROUP BY fd.filing_id
ORDER BY doc_count DESC;
```

---

## 4. Service of Process Requirements

### 4.1 Service Methods by Filing Type

| Filing | Court | Service Method | Form | Rule |
|--------|-------|---------------|------|------|
| F1 (TRO) | 14th Circuit | Personal service + court order | MC 12 | MCR 2.107, MCR 3.310 |
| F2 (Civil Complaint) | 60th District / Circuit | Personal service via process server | MC 12, MC 04 | MCR 2.105 |
| F3 (Disqualification) | 14th Circuit | Service on all parties | MC 12 | MCR 2.003(D) |
| F4 (§1983) | USDC WDMI | U.S. Marshal or waiver of service | Fed R Civ P 4 | FRCP 4(c)(3) |
| F5 (MSC Bypass) | Michigan Supreme Court | Service on all parties + lower court | MC 12 | MCR 7.305 |
| F6 (JTC) | JTC Administrative | Mail to JTC; copy to judge | — | Const 1963 Art 6 §30 |
| F7 (Custody Mod) | 14th Circuit | Service on opposing party/counsel | MC 12 | MCR 3.203 |
| F8 (PPO Term) | 14th Circuit | Service on all parties | MC 12 | MCL 600.2950 |
| F9 (COA Brief) | Court of Appeals | Service on all parties + lower court | MC 12 | MCR 7.211 |
| F10 (COA Emergency) | Court of Appeals | Immediate service + telephonic notice | MC 12 | MCR 7.211(C)(9) |

### 4.2 Proof of Service Form (MC 12)

Required elements:
- Title of document served
- Date and time of service
- Method of service (personal, mail, electronic)
- Name and address of person served
- Server signature and identification
- Certificate of mailing (if applicable)

### 4.3 Service Tracking Query

```sql
-- Check service status for all filings
SELECT fp.filing_id, fp.title, fp.lane,
       fr.status, fr.readiness_score
FROM filing_packages fp
LEFT JOIN filing_readiness fr ON fp.filing_id = fr.filing_id
ORDER BY fp.filing_id;
```

---

## 5. Court-Specific Requirements

### 5.1 14th Circuit Court, Family Division (Lanes A, D, E)

| Requirement | Specification |
|-------------|--------------|
| **Judge** | Hon. Jenny L. McNeill |
| **Case Numbers** | 2024-001507-DC (custody), 2023-5907-PP (PPO) |
| **E-Filing** | MiFILE mandatory for all filings |
| **Caption** | Pigors v Watson; use L.D.W. for child (MCR 8.119(H)) |
| **Proposed Orders** | Required with all motions (MCR 2.119(A)(2)) |
| **Briefs** | 20 pages max unless leave granted (MCR 2.119(A)(3)) |
| **Exhibits** | Tabbed, indexed, Bates-stamped preferred |
| **Hearing Notice** | 9-day notice for motions (MCR 2.119(C)) |
| **FOC** | Custody matters referred to Pamela Rusco, FOC |

### 5.2 60th District Court (Lane B — if jurisdictional)

| Requirement | Specification |
|-------------|--------------|
| **Case Number** | 2025-002760-CZ (Shady Oaks housing) |
| **Jurisdiction** | Civil claims within jurisdictional limits |
| **E-Filing** | MiFILE |
| **Small Claims** | Up to $6,500; General Civil above |

### 5.3 Michigan Court of Appeals (Lane F)

| Requirement | Specification |
|-------------|--------------|
| **Case Number** | COA-366810 |
| **Brief Word Limit** | 16,000 words (MCR 7.212(B)) |
| **Appendix** | Required — relevant portions of lower court record (MCR 7.212(C)) |
| **Filing Deadline** | 56 days after claim of appeal filed (MCR 7.212(A)) |
| **Emergency Motion** | Immediate service + telephonic notice (MCR 7.211(C)(9)) |
| **Certificate of Service** | Required on every filing |
| **E-Filing** | MiFILE — mandatory |

### 5.4 Michigan Supreme Court (Lane F)

| Requirement | Specification |
|-------------|--------------|
| **Bypass Application** | MCR 7.305(H) — before COA decision |
| **Word Limit** | 15,000 words for application |
| **Appendix** | Key lower court orders + COA filings |
| **Service** | All parties + lower courts |
| **Filing Fee** | Check current fee schedule |

### 5.5 USDC Western District of Michigan (Lane C — §1983)

| Requirement | Specification |
|-------------|--------------|
| **E-Filing** | CM/ECF (mandatory for attorneys; pro se paper filing allowed) |
| **Service** | FRCP 4 — U.S. Marshal for IFP plaintiffs |
| **Complaint** | Federal form requirements; FRCP 8 notice pleading |
| **IFP Application** | 28 USC §1915 if applicable |
| **Local Rules** | W.D. Mich. L. Civ. R. compliance |

---

## 6. Proposed Order Requirements

### 6.1 When Required

Every motion filed in Michigan state court must include a proposed order (MCR 2.119(A)(2)). Federal practice differs — proposed orders submitted after ruling.

### 6.2 Proposed Order Template

```
STATE OF MICHIGAN
IN THE [COURT LEVEL] COURT FOR THE COUNTY OF MUSKEGON

ANDREW JAMES PIGORS,
    Plaintiff,                         Case No. [NUMBER]
v.                                     Hon. Jenny L. McNeill
EMILY A. WATSON,
    Defendant.
_________________________________/

ORDER [GRANTING/DENYING] [MOTION TYPE]

At a session of said Court held in [location]
on the ___ day of ____________, 20___.

PRESENT: HON. JENNY L. McNEILL, Circuit Court Judge

THIS MATTER having come before the Court on Plaintiff's
[Motion Type], and the Court being fully advised in the premises;

IT IS HEREBY ORDERED:

1. [Specific relief granted]
2. [Additional provisions]
3. [Effective date/implementation]

IT IS SO ORDERED.

_________________________________
Hon. Jenny L. McNeill
Circuit Court Judge
Date: _______________
```

---

## 7. E-Filing Procedures (MiFILE)

### 7.1 MiFILE Workflow

| Step | Action | Notes |
|------|--------|-------|
| 1 | Log in to MiFILE (mi.gov/mifile) | Pro se or attorney account |
| 2 | Select court and case number | Match exact case number from filing_packages |
| 3 | Select filing type | Motion, Brief, Complaint, etc. |
| 4 | Upload lead document | PDF format, text-searchable |
| 5 | Upload attachments | Exhibits, proposed order, MC 12, index |
| 6 | Enter service information | All parties to be served electronically |
| 7 | Pay filing fee (if applicable) | Credit card or fee waiver |
| 8 | Submit | System generates confirmation with timestamp |
| 9 | Track status | MiFILE provides filing status updates |

### 7.2 MiFILE Document Requirements

- **Format:** PDF only, text-searchable preferred
- **Size limit:** 25 MB per document (split if larger)
- **Naming:** Descriptive filenames (no spaces recommended)
- **Accessibility:** Text layer required for court indexing
- **Signature:** /s/ electronic signature acceptable (MCR 2.114)

### 7.3 Filing Fee Schedule

| Court | Filing Type | Fee |
|-------|------------|-----|
| Circuit Court | Motion | $20.00 |
| Circuit Court | New case | $175.00+ |
| Court of Appeals | Claim of appeal | $375.00 |
| Court of Appeals | Emergency motion | $0 (with claim) |
| Supreme Court | Application | $375.00 |
| Federal (WDMI) | New civil case | $405.00 |
| Federal (WDMI) | IFP waiver | $0 if granted |

---

## 8. Filing Database Tables

### 8.1 Primary Tables

| Table | PK | Rows | Purpose |
|-------|-----|------|---------|
| `filing_packages` | filing_id (TEXT) | 10 | Master filing package registry |
| `filing_documents` | doc_id (TEXT) | per-package | Individual documents within packages |
| `filing_readiness` | vehicle_name (TEXT) | 17 | Readiness scoring and tracking |
| `filing_rule_map` | id (INTEGER) | per-filing | Authority requirements per filing |
| `filing_cross_reference` | id (INTEGER) | varies | Cross-filing dependencies and conflicts |
| `filing_vulnerability_scores` | filing_id (TEXT) | per-filing | Vulnerability assessment per filing |
| `filings` | id (INTEGER) | varies | General filing registry with dates and status |

### 8.2 Schema Reference — filing_packages

```sql
CREATE TABLE filing_packages (
    filing_id TEXT PRIMARY KEY,        -- F1, F2, ..., F10
    title TEXT NOT NULL,               -- Human-readable title
    lane TEXT,                         -- Case lane (A-F)
    case_number TEXT,                  -- Court case number
    pkg_directory TEXT,                -- Filesystem path to package
    doc_count INTEGER DEFAULT 0,       -- Documents in package
    total_size_kb REAL DEFAULT 0,      -- Total size
    status TEXT DEFAULT 'ingested',    -- ingested, draft, review, filed
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.3 Schema Reference — filing_readiness

```sql
CREATE TABLE filing_readiness (
    vehicle_name TEXT PRIMARY KEY,     -- Full filing name
    filing_id TEXT,                    -- Links to filing_packages
    status TEXT DEFAULT 'draft',       -- draft, ingested, review, final_review, complete, filed
    readiness_score REAL DEFAULT 0,    -- 0-100 composite score
    blockers TEXT,                     -- Current blockers (JSON or text)
    last_qa_date TEXT,                 -- Last QA run timestamp
    qa_result TEXT,                    -- pass, fail, pending
    placeholder_count INTEGER DEFAULT 0,
    exhibit_count INTEGER DEFAULT 0,
    authority_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    lane TEXT,                         -- Case lane
    deadline TEXT,                     -- Filing deadline if known
    updated_at TEXT DEFAULT datetime('now')
);
```

### 8.4 Schema Reference — filing_rule_map

```sql
CREATE TABLE filing_rule_map (
    id INTEGER PRIMARY KEY,
    filing_id TEXT NOT NULL,           -- Links to filing_packages
    authority_type TEXT,               -- MCR, MCL, MRE, FRCP, USC, Const
    authority_number TEXT,             -- e.g., "2.003", "600.2950"
    requirement TEXT,                  -- What the rule requires
    mandatory INTEGER DEFAULT 1,       -- 1=must cite, 0=recommended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.5 Schema Reference — filing_vulnerability_scores

```sql
CREATE TABLE filing_vulnerability_scores (
    filing_id TEXT PRIMARY KEY,
    filing_name TEXT,
    procedural_vulnerability REAL,     -- 0-10 scale
    substantive_vulnerability REAL,
    evidentiary_vulnerability REAL,
    overall_vulnerability REAL,
    top_threat TEXT,                    -- Highest-risk category
    recommended_fix TEXT,              -- Specific remediation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.6 The filing_id Hub Column

The `filing_id` column is the primary join key across the filing system. It connects to at least these tables:

```
filing_packages.filing_id ──┬── filing_documents.filing_id
                            ├── filing_readiness.filing_id
                            ├── filing_rule_map.filing_id
                            ├── filing_cross_reference.filing_a / filing_b
                            ├── filing_vulnerability_scores.filing_id
                            ├── witness_list.filing_ids (comma-separated)
                            ├── evidence_quotes.filing_refs
                            └── filings (via title/case_id correlation)
```

---

## Key DB Queries

```sql
-- Q1: Filing readiness dashboard (top vehicles first)
SELECT vehicle_name, filing_id, status, readiness_score,
       exhibit_count, placeholder_count, lane, deadline
FROM filing_readiness
ORDER BY readiness_score DESC;

-- Q2: Filing package with document inventory
SELECT fp.filing_id, fp.title, fp.lane, fp.case_number,
       fp.doc_count, fp.total_size_kb, fp.status,
       fr.readiness_score, fr.placeholder_count
FROM filing_packages fp
LEFT JOIN filing_readiness fr ON fp.filing_id = fr.filing_id;

-- Q3: Authority requirements per filing
SELECT frm.filing_id, frm.authority_type, frm.authority_number,
       frm.requirement, frm.mandatory
FROM filing_rule_map frm
WHERE frm.filing_id = ?
ORDER BY frm.mandatory DESC, frm.authority_type;

-- Q4: Vulnerability assessment
SELECT filing_id, filing_name, overall_vulnerability,
       top_threat, recommended_fix
FROM filing_vulnerability_scores
ORDER BY overall_vulnerability DESC;

-- Q5: Cross-filing dependencies
SELECT fcr.filing_a, fcr.filing_b, fcr.relationship_type,
       fcr.description, fcr.severity, fcr.recommendation
FROM filing_cross_reference fcr
ORDER BY fcr.severity DESC;
```

---

## 9. Filing Workflow Agents

| Agent | Role | Trigger |
|-------|------|---------|
| **filing-forge-master** | Assembly, QA, Bates stamps, service tracking | Any filing workflow |
| **omega-litigation-commander** | Complex multi-step filing orchestration | COA dockets, compliance proofs |
| **court-form-finder** | Michigan SCAO form identification | Form number lookup |
| **compliance-auditor** | PII redaction, pre-submission compliance | Pre-filing audit |
| **appellate-record-builder** | COA/MSC record assembly | Building appendices |
| **motion-practice** | Draft/review any motion type | General motions |

---

## 10. Filing Priority Matrix

### 10.1 Deadline-Driven Priority

| Priority | Vehicle | Deadline | Action |
|----------|---------|----------|--------|
| **CRITICAL** | F-VAC (Omnibus Motion) | 2026-03-25 | Final review → file |
| **URGENT** | F-MSC2 (MSC Bypass) | 2026-04-15 | Complete → service → file |
| **HIGH** | F-JTC (JTC Complaint) | 2026-05-01 | Draft → exhibits → review |
| **MEDIUM** | F-DISQv2, F-1983v2 | No hard deadline | Continue drafting |
| **STANDARD** | F1-F10 (core packages) | Various | Pipeline processing |

### 10.2 Filing Sequencing Strategy

```
Wave 1 (Immediate):   F-VAC → F-MSC2
Wave 2 (30 days):     F-DISQv2 → F-JTC → F-PPOterm
Wave 3 (60 days):     F-1983v2 → F-CUSTmod
Wave 4 (As ready):    F1-F10 core packages
```

---

## Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|-----------|-----------|
| **Ω9 Witness Brain** | witness_list.filing_ids → filing_packages | Each filing lists required witnesses; witness testimony supports filing content |
| **Ω11 Agent Brain** | Filing agents orchestrate assembly | filing-forge-master, compliance-auditor, motion-practice execute pipeline stages |
| **Ω12 Context Brain** | Filing state persists across sessions | filing_readiness tracks progress; session_handoff logs filing work |
| **Ω1 Evidence Brain** | evidence_quotes.filing_refs → filing_id | Evidence supports filing arguments; exhibits assembled from evidence |
| **Ω4 Authority Brain** | filing_rule_map mandates citations | Every filing must cite mandatory authorities tracked in filing_rule_map |
| **Ω5 Deadline Brain** | deadlines drive filing priority | Filing priority derived from deadline urgency scores |
