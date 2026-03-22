---
name: multi-court-filing-coordinator
description: |
  Multi-court filing coordinator and deadline tracker for Pigors v. Watson litigation
  spanning 14th Circuit (Family & Civil), 60th District, Michigan COA, potential MSC,
  USDC W.D. Michigan, JTC, and Attorney Grievance Commission. Coordinates deadlines,
  service, evidence sharing, and strategic filing sequencing across all courts.
  Use PROACTIVELY when any filing, deadline, service, or cross-court strategy question arises.
category: litigation
version: "3.0.0-APEX-OMEGA"
metadata:
  model: inherit
  tier: 1
  modules: 7
  courts: 8
  lanes: [A, B, C, D, E, F]
  case: Pigors v Watson
  primary_db: litigation_context.db
triggers:
  - multi-court
  - cross-court
  - deadline
  - filing coordinator
  - service coordination
  - court calendar
  - conflict detection
  - filing sequence
  - deadline tracker
  - court registry
  - evidence sharing
  - exhibit numbering
  - bates stamps
  - res judicata
  - Rooker-Feldman
  - Younger abstention
  - collateral estoppel
  - filing strategy
  - parallel filing
  - court dashboard
lanes:
  A: "Watson custody — 14th Circuit Family — 2024-001507-DC"
  B: "Shady Oaks housing — 14th Circuit Civil — 2025-002760-CZ"
  C: "Convergence — cross-lane coordination"
  D: "PPO / Protection Orders — 14th Circuit — 2023-5907-PP"
  E: "Judicial misconduct — JTC / AG — 2024-001507-DC"
  F: "Appellate — COA 366810 / potential MSC"
court: |
  14th Judicial Circuit (Family & Civil), Muskegon County;
  60th District Court, Muskegon County;
  Michigan Court of Appeals;
  Michigan Supreme Court (potential);
  USDC Western District of Michigan (potential);
  Judicial Tenure Commission (potential);
  Attorney Grievance Commission (potential)
dependencies:
  - OMEGA-LITIGATION-SUPREME
  - filing-forge-master
  - appellate-record-builder
---

# Multi-Court Filing Coordinator & Deadline Tracker

> **Tier 1 — Strategic Coordination Skill** — Manages the complexity of simultaneous
> litigation across 8 courts/bodies. Prevents missed deadlines, coordinates service,
> optimizes filing sequence, and detects cross-court conflicts that could be fatal
> to Andrew Pigors' cases.

## Use this skill when

- Filing deadlines approach in ANY court
- Planning what to file next across multiple proceedings
- Coordinating service on parties who appear in multiple cases
- Sharing evidence or exhibits between courts
- Assessing whether a filing in one court could harm another case
- Building a master calendar of all litigation deadlines
- Detecting conflicts: same-day filings, res judicata risks, abstention issues
- Preparing for the April 7, 2026 criminal trial while managing civil/family cases
- Evaluating parallel vs. sequential filing strategies (federal + state + JTC)
- Generating cross-court status dashboards from litigation_context.db

## Do not use this skill when

- Working on a single filing in a single court with no cross-court implications
- Pure evidence analysis with no filing/deadline component (use OMEGA-EVIDENCE)
- Code or infrastructure tasks (use OMEGA-ENGINEER)
- Agent fleet management (use self-evolving-fleet-manager)

## Safety

- **VERIFIED PARTIES ONLY** — Use exclusively:
  - Plaintiff: **Andrew James Pigors** (1977 Whitehall Road, Lot 17, North Muskegon, MI 49445)
  - Defendant: **Emily A. Watson** (2160 Garland Drive, Norton Shores, MI 49441)
  - Child: **L.D.W.** (initials only per MCR 8.119(H) — NEVER full name)
  - Judge: **Hon. Jenny L. McNeill** (14th Circuit, Family Division)
  - Emily's former attorney: **Jennifer Barnes (P55406)** — WITHDREW
  - FOC: **Pamela Rusco** (990 Terrace St, Muskegon, MI 49442)
  - Ronald Berry: NON-ATTORNEY domestic partner — no bar number, no "Esq."
- **NEVER fabricate** party names, bar numbers, case numbers, or deadlines
- **DB-FIRST** — Query litigation_context.db before inserting any placeholder
- **TRACEABLE STATS** — Every deadline count or status must cite a SQL query
- **NO HARD DELETIONS** — Append-only; move superseded filings to archive

---

## Module MC1: Court Registry

### 1.1 Active Court Matrix

| Court | Division | Case Number | Judge | Lane | Status | Filing Method |
|-------|----------|-------------|-------|------|--------|---------------|
| **14th Circuit Court** | Family Division | 2024-001507-DC | Hon. Jenny L. McNeill | A | Active — custody/parenting | MiFILE e-filing |
| **14th Circuit Court** | Civil Division | 2025-002760-CZ | TBD | B | Dismissed — appeal window | MiFILE e-filing |
| **60th District Court** | Criminal | 2025-25245676SM | TBD | — | Active — trial April 7, 2026 | MiFILE e-filing |
| **Michigan Court of Appeals** | — | 366810 | Panel TBD | F | Active — appeal pending | MiFILE e-filing |
| **Michigan Supreme Court** | — | TBD (bypass application) | — | F | Potential | MiFILE e-filing |
| **USDC W.D. Michigan** | Civil | TBD (§1983) | TBD | — | Potential | CM/ECF e-filing |
| **Judicial Tenure Commission** | — | TBD | — | E | Potential | Paper + mail |
| **Attorney Grievance Commission** | — | TBD | — | E | Potential | Paper + mail |

### 1.2 Court-Specific Rules Engine

#### Michigan State Courts (MCR)
- **Formatting**: MCR 1.109 — 8.5×11, double-spaced body, 1-inch margins, 12pt Times New Roman or similar
- **Caption**: Case number top right; court name, parties, attorney info per MCR 1.109(D)
- **Page limits**: Motions — no hard MCR limit (local rules may cap at 20 pages); Briefs on appeal — MCR 7.212(B) 50 pages
- **Filing hours**: MiFILE accepts 24/7; clerk stamps next business day if filed after 11:59 PM
- **Service**: MCR 2.107 — serve all parties; MCR 2.105 for initial process service
- **Signatures**: `/s/ Andrew James Pigors` with typed name and address below

#### 14th Circuit Court — Muskegon County
- **Address**: Michael E. Kobza Hall of Justice, 990 Terrace St, Muskegon, MI 49442
- **E-filing**: MiFILE (https://mifile.courts.michigan.gov)
- **Local rules**: Check 14th Circuit local administrative orders
- **Family Division clerk**: (231) 724-6241
- **Civil Division clerk**: (231) 724-6241

#### 60th District Court — Muskegon County
- **Address**: 990 Terrace St, Muskegon, MI 49442
- **E-filing**: MiFILE
- **Criminal division**: Misdemeanor/felony arraignments, pretrial, trial
- **Trial date**: April 7, 2026 — ALL prep deadlines cascade from this date

#### Michigan Court of Appeals
- **Address**: Cadillac Place, 3020 W Grand Blvd, Suite 14-300, Detroit, MI 48202
- **E-filing**: MiFILE (COA division)
- **Formatting**: MCR 7.212 — specific cover page, table of contents, table of authorities
- **Page limit**: 50 pages for briefs (MCR 7.212(B))
- **Appendix**: Required per MCR 7.212(C) — lower court orders, relevant pleadings

#### Michigan Supreme Court (Potential)
- **Address**: Michigan Hall of Justice, 925 W Ottawa St, Lansing, MI 48909
- **E-filing**: MiFILE (MSC division)
- **Bypass application**: MCR 7.305(B)(2) — leave to appeal before COA decision if issue of major significance
- **Page limit**: Applications — 50 pages; supplemental briefs vary

#### USDC Western District of Michigan (Potential)
- **Address**: Gerald R. Ford Federal Building, 110 Michigan St NW, Grand Rapids, MI 49503
- **E-filing**: CM/ECF (https://ecf.miwd.uscourts.gov)
- **Rules**: FRCP + W.D. Mich. Local Rules
- **Formatting**: LCivR 10.1 — similar to state but check local requirements
- **§1983 complaint**: Must plead specific constitutional violations, identify each defendant's personal involvement
- **Service**: FRCP 4 — personal service or waiver of service; U.S. Marshals for IFP plaintiffs

#### Judicial Tenure Commission (Potential)
- **Address**: 3034 W Grand Blvd, Suite 8-450, Detroit, MI 48202
- **Filing method**: Paper filing by mail or hand delivery (NO e-filing)
- **Rules**: MCR 9.200 et seq.; JTC Rules of Procedure
- **Format**: Letter complaint + supporting documentation
- **Service**: JTC serves the judge; complainant does NOT serve judge directly
- **Confidential**: All proceedings confidential until formal charges filed

#### Attorney Grievance Commission (Potential)
- **Address**: 535 Griswold St, Suite 1700, Detroit, MI 48226
- **Filing method**: Paper or online complaint form (https://agcmi.com)
- **Target**: Jennifer Barnes (P55406) — potential grievance for conduct during representation
- **Rules**: MCR 9.100 et seq.
- **Confidential**: Investigation is confidential

### 1.3 Auto-Detect Court from Case Number

```
DETECTION RULES (regex-based):
  /2024-001507-DC/i     → 14th Circuit, Family Division    → Lane A
  /2025-002760-CZ/i     → 14th Circuit, Civil Division     → Lane B
  /2023-5907-PP/i        → 14th Circuit (PPO)              → Lane D
  /2025-25245676SM/i     → 60th District Court             → (Criminal)
  /366810/               → Michigan Court of Appeals        → Lane F
  /^\d{2}-\d{5,6}$/     → Potential federal case number    → (Federal)
  /JTC/i                 → Judicial Tenure Commission       → Lane E
  /AGC|grievance/i       → Attorney Grievance Commission    → Lane E
```

### 1.4 Court Registry SQL Queries

```sql
-- List all courts in the registry
SELECT id, name, type, county, address, phone, efiling_url
FROM courts
ORDER BY name;

-- Find court by case number
SELECT c.name, c.type, c.address, c.efiling_url
FROM courts c
JOIN docket_events de ON de.case_number LIKE '%' || c.jurisdiction_id || '%'
WHERE de.case_number = ?
LIMIT 1;

-- All docket events for a specific court/case
SELECT event_date, event_type, description, filed_by
FROM docket_events
WHERE case_number = ?
ORDER BY event_date DESC;
```

---

## Module MC2: Cross-Court Deadline Engine

### 2.1 Master Deadline Calendar

All deadlines across all courts, ranked by urgency:

```sql
-- MASTER DEADLINE VIEW: All upcoming deadlines across courts, urgency-ranked
SELECT
    d.id,
    d.title,
    d.due_date,
    d.court,
    d.case_number,
    d.status,
    d.urgency,
    d.filing_id,
    d.notes,
    julianday(d.due_date) - julianday('now') AS days_remaining
FROM deadlines d
WHERE d.status != 'completed'
ORDER BY d.urgency DESC, d.due_date ASC;
```

```sql
-- CONFLICT DETECTION: Multiple deadlines on the same day
SELECT
    due_date,
    COUNT(*) AS filing_count,
    GROUP_CONCAT(court || ': ' || title, ' | ') AS filings_due
FROM deadlines
WHERE status != 'completed'
GROUP BY due_date
HAVING COUNT(*) > 1
ORDER BY due_date ASC;
```

```sql
-- URGENCY TRIAGE: Deadlines within the next 14 days
SELECT
    d.title,
    d.due_date,
    d.court,
    d.case_number,
    d.urgency,
    julianday(d.due_date) - julianday('now') AS days_remaining
FROM deadlines d
WHERE d.status = 'pending'
  AND julianday(d.due_date) - julianday('now') BETWEEN 0 AND 14
ORDER BY d.due_date ASC;
```

### 2.2 Deadline Dependency Rules

Deadlines are not independent — they cascade. Key dependency chains:

#### MCR Appeal Deadlines (State)
| Trigger Event | Deadline | Rule | Calculation |
|---------------|----------|------|-------------|
| Entry of order/judgment | Claim of appeal | MCR 7.204(A)(1) | 21 days from entry |
| Claim of appeal filed | Ordering transcript | MCR 7.210(B)(1) | 14 days from filing claim |
| Transcript filed | Appellant's brief due | MCR 7.212(A)(1) | 56 days from transcript |
| Appellant's brief served | Appellee's brief due | MCR 7.212(A)(2) | 35 days from service |
| Mail service (add 3 days) | Any MCR deadline | MCR 1.108(1) | +3 calendar days |
| Court closure/weekend | Any deadline | MCR 1.108(2) | Extends to next business day |

#### Criminal Trial Deadlines (60th District)
| Event | Deadline | Notes |
|-------|----------|-------|
| Trial date | **April 7, 2026** | FIXED — all other deadlines cascade backward |
| Witness list due | ~14 days before trial | Check local rules |
| Exhibit list due | ~14 days before trial | Check local rules |
| Motions in limine | ~21 days before trial | File early for judicial consideration |
| Plea negotiations | Ongoing until trial | Coordinate with custody strategy |

#### Federal Deadlines (FRCP — if §1983 filed)
| Trigger Event | Deadline | Rule |
|---------------|----------|------|
| Complaint filed | Service on defendant | FRCP 4(m) — 90 days |
| Service complete | Answer/motion to dismiss | FRCP 12(a)(1) — 21 days (60 days for government) |
| Answer filed | Initial disclosures | FRCP 26(a)(1) — 14 days after Rule 26(f) conference |
| Scheduling conference | Discovery period | FRCP 16 — per court scheduling order |

#### JTC / AGC Deadlines
| Body | Deadline | Notes |
|------|----------|-------|
| JTC | No strict filing deadline | But file while pattern is fresh and documented |
| AGC | 3-year limitation on grievances | MCR 9.113(A) — from date of conduct |

### 2.3 Deadline Calculator Functions

```
FUNCTION: calculate_appeal_deadline(order_entry_date, service_method)
  base_days = 21  -- MCR 7.204(A)(1)
  IF service_method == 'mail': base_days += 3  -- MCR 1.108(1)
  deadline = order_entry_date + base_days
  IF deadline falls on weekend/holiday: deadline = next_business_day
  RETURN deadline

FUNCTION: calculate_response_deadline(service_date, filing_type, court)
  IF court == 'federal':
    IF filing_type == 'complaint': RETURN service_date + 21  -- FRCP 12(a)
    IF filing_type == 'discovery': RETURN service_date + 30  -- FRCP 33/34
  IF court == 'state':
    IF filing_type == 'motion': RETURN service_date + 21  -- MCR 2.108
    IF filing_type == 'interrogatory': RETURN service_date + 28  -- MCR 2.309
  ADJUST for mail (+3 days) and weekends/holidays

FUNCTION: calculate_trial_prep_deadlines(trial_date)
  -- Backward cascade from April 7, 2026
  witness_list    = trial_date - 14 days
  exhibit_list    = trial_date - 14 days
  motions_limine  = trial_date - 21 days
  pretrial_conf   = trial_date - 7 days  (check scheduling order)
  RETURN all dates adjusted for weekends/holidays
```

### 2.4 Priority Ranking Matrix

When multiple filings are due simultaneously:

| Priority | Category | Rationale |
|----------|----------|-----------|
| **P0 — EMERGENCY** | Child safety, imminent harm, emergency PPO | File immediately in highest-authority court |
| **P1 — JURISDICTIONAL** | Appeal deadlines, statute of limitations | Miss these = permanently waived |
| **P2 — CRIMINAL** | 60th District trial prep (April 7, 2026) | Criminal consequences > civil consequences |
| **P3 — STRATEGIC** | Federal complaint, MSC bypass application | Timing affects all other courts |
| **P4 — OFFENSIVE** | JTC complaint, AGC grievance, new motions | Important but not deadline-critical |
| **P5 — MAINTENANCE** | Responses, discovery, status updates | Necessary but flexible |

---

## Module MC3: Strategic Filing Sequencer

### 3.1 Decision Tree

```
                    ┌─────────────────────┐
                    │  NEW FILING NEEDED   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Is child in danger? │
                    └──────────┬──────────┘
                          YES/ \NO
                         /     \
            ┌───────────▼┐   ┌─▼────────────────────┐
            │ FILE NOW   │   │ Is a deadline about   │
            │ Emergency  │   │ to expire (<7 days)?  │
            │ Ex Parte   │   └──────────┬────────────┘
            │ in highest │         YES/ \NO
            │ authority  │        /     \
            │ court      │  ┌────▼───┐ ┌▼──────────────────┐
            └────────────┘  │FILE the│ │Strategic analysis: │
                            │expiring│ │Which court first?  │
                            │item NOW│ └─────────┬─────────┘
                            └────────┘           │
                               ┌─────────────────┼──────────────────┐
                               │                 │                  │
                    ┌──────────▼──┐   ┌──────────▼──┐   ┌──────────▼──┐
                    │ SEQUENTIAL  │   │  PARALLEL   │   │  PRESERVE   │
                    │State first  │   │File in all  │   │Record-build │
                    │then Federal │   │courts at    │   │before filing│
                    │Build record │   │once for max │   │Gather more  │
                    └─────────────┘   │pressure     │   │evidence     │
                                      └─────────────┘   └─────────────┘
```

### 3.2 Filing Strategy Matrix

| Strategy | When to Use | Courts | Risk Level |
|----------|-------------|--------|------------|
| **Sequential (Record-Builder)** | Build state court record → then use it in federal/appellate | State → COA → MSC → Federal | Low — methodical, documented |
| **Parallel (Overwhelming Force)** | Maximum pressure; adversary can't respond everywhere | All courts simultaneously | Medium — requires resources, may dilute focus |
| **Staggered (Wave Attack)** | Strategic timing; each filing cites the others | File 2-3 per week across courts | Medium — requires careful sequencing |
| **Preservation-First** | Deadlines approaching but record incomplete | File protective motions; buy time | Low — preserves rights without overcommitting |
| **Emergency Protocol** | Child safety, imminent irreparable harm | Highest authority court immediately | High — emergency standards are strict |

### 3.3 Cross-Court Impact Analysis

Every filing should be evaluated for impact on other courts:

```
BEFORE FILING in any court, ask:

1. ADMISSIONS RISK: Does this filing contain admissions that could
   be used against me in another court?
   → Especially: criminal court statements affecting family court
   → Especially: state court admissions affecting federal §1983

2. PRECLUSION RISK: Could the outcome in this court preclude
   claims in another court?
   → Res judicata: same parties + same claim = barred
   → Collateral estoppel: same issue actually litigated = barred

3. ABSTENTION RISK: Will filing in federal court trigger Younger
   abstention if state proceedings are ongoing?
   → Yes if: ongoing state judicial proceedings + important state
     interests + adequate opportunity to raise federal claims in state court
   → Exception: bad faith prosecution, patently unconstitutional statute

4. ROOKER-FELDMAN RISK: Am I asking federal court to review a
   state court judgment?
   → Can't do that — only SCOTUS reviews state court final judgments
   → BUT: can challenge the constitutionality of the PROCESS
     (due process violation ≠ appeal of the judgment)

5. STRATEGIC BENEFIT: Does filing in this court help my other cases?
   → JTC complaint → creates pressure that may change judge's behavior
   → Federal filing → opens discovery tools not available in state court
   → COA reversal → undermines opposing party's state court victories
```

### 3.4 Recommended Filing Sequence (Current Posture)

Based on active cases and strategic considerations:

```
PHASE 1 — PRESERVE & PROTECT (Immediate)
  ├── File any expiring appeal deadlines (Lane F)
  ├── Criminal trial prep for April 7, 2026 (60th District)
  └── Emergency motions if child safety at issue (Lane A)

PHASE 2 — BUILD THE RECORD (Weeks 1-4)
  ├── File strong custody motions in 14th Circuit Family (Lane A)
  ├── Document judicial misconduct pattern (Lane E — preparation)
  └── Organize evidence for cross-court use (Lane C)

PHASE 3 — EXPAND THE FRONT (Weeks 4-8)
  ├── File JTC complaint against Hon. Jenny L. McNeill (Lane E)
  ├── File AGC complaint against Jennifer Barnes (P55406) (Lane E)
  └── Perfect COA briefing (Lane F)

PHASE 4 — FEDERAL FRONT (After state record established)
  ├── File §1983 complaint in USDC W.D. Michigan
  ├── Name specific defendants with personal involvement
  └── Use state court record as evidence of constitutional violations

PHASE 5 — SUPREME AUTHORITY (If needed)
  ├── MSC bypass application if COA is unfavorable
  └── Or MSC application for leave after COA decision
```

---

## Module MC4: Service Coordination

### 4.1 Multi-Party Service Matrix

| Party | Role | Courts | Service Method | Address |
|-------|------|--------|----------------|---------|
| **Emily A. Watson** | Defendant/Respondent | 14th Circuit (A, D) | MiFILE e-service if registered; otherwise mail to 2160 Garland Dr, Norton Shores, MI 49441 | 2160 Garland Dr, Norton Shores, MI 49441 |
| **Jennifer Barnes (P55406)** | Former attorney (WITHDREW) | 14th Circuit (A, D) | Check if still attorney of record; if withdrawn, serve Emily directly | Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 |
| **Pamela Rusco (FOC)** | Friend of the Court | 14th Circuit Family (A) | Mail or hand-deliver to FOC office | 990 Terrace St, Muskegon, MI 49442 |
| **Hon. Jenny L. McNeill** | Judge (JTC complaint) | JTC (E) | DO NOT serve directly — JTC serves judge | N/A — JTC handles service |
| **Michigan Attorney General** | Constitutional challenges | Federal (§1983) | FRCP 5.1 — serve AG when challenging constitutionality of state statute | Michigan AG, P.O. Box 30212, Lansing, MI 48909 |
| **Individual state defendants** | §1983 defendants | Federal | FRCP 4 — personal service or waiver; U.S. Marshals if IFP | Per defendant |
| **Attorney Grievance Commission** | Barnes complaint target | AGC (E) | File complaint with AGC; they investigate and serve respondent | 535 Griswold St, Suite 1700, Detroit, MI 48226 |

### 4.2 Certificate of Service Templates

#### Michigan State Courts (MCR 2.107)
```
CERTIFICATE OF SERVICE

I, Andrew James Pigors, certify that on [DATE], I served a copy of the
foregoing [DOCUMENT TITLE] upon:

  [PARTY NAME]
  [ADDRESS LINE 1]
  [ADDRESS LINE 2]

by [  ] First-class U.S. Mail, postage prepaid
   [  ] Personal delivery
   [  ] MiFILE electronic service
   [  ] Email to [address] (by agreement/court order)

                                    /s/ Andrew James Pigors
                                    Andrew James Pigors
                                    1977 Whitehall Road, Lot 17
                                    North Muskegon, MI 49445
                                    (231) 903-5690
                                    andrewjpigors@gmail.com
```

#### Federal Court (FRCP 5)
```
CERTIFICATE OF SERVICE

I hereby certify that on [DATE], I electronically filed the foregoing
with the Clerk of Court using the CM/ECF system, which will send
notification of such filing to all parties registered to receive
electronic notification. I further certify that I served the
following non-CM/ECF participants by [mail/personal service]:

  [PARTY NAME AND ADDRESS]

Dated: [DATE]                       /s/ Andrew James Pigors
                                    Andrew James Pigors, Pro Se
                                    1977 Whitehall Road, Lot 17
                                    North Muskegon, MI 49445
                                    (231) 903-5690
                                    andrewjpigors@gmail.com
```

### 4.3 Service Tracking SQL

```sql
-- Track all service events (query docket_events for service-related entries)
SELECT
    de.case_number,
    de.event_date,
    de.event_type,
    de.description,
    de.filed_by
FROM docket_events de
WHERE de.event_type LIKE '%service%'
   OR de.description LIKE '%served%'
   OR de.description LIKE '%certificate of service%'
ORDER BY de.event_date DESC;

-- Service gaps: filings without corresponding proof of service
SELECT
    d.title AS filing,
    d.court,
    d.case_number,
    d.due_date
FROM deadlines d
WHERE d.status = 'pending'
  AND NOT EXISTS (
    SELECT 1 FROM docket_events de
    WHERE de.case_number = d.case_number
      AND de.event_type LIKE '%service%'
      AND de.event_date >= d.due_date
  );
```

---

## Module MC5: Cross-Court Evidence Sharing

### 5.1 Evidence Reuse Strategy

The same evidence frequently applies across multiple courts. Key principles:

1. **One Source, Multiple Uses**: A court order entered in family court can be an
   exhibit in COA appeal, evidence in §1983 federal complaint, and attachment to
   JTC complaint
2. **Authentication Once, Certify Per Court**: Authenticate evidence once with
   proper foundation; obtain certified copies for each court as needed
3. **Bates Stamp Continuity**: Use a UNIFIED Bates numbering scheme across all
   courts so references remain consistent
4. **Cross-Reference, Don't Duplicate**: When evidence is already filed in one
   court, reference it by exhibit number rather than re-filing

### 5.2 Unified Bates Numbering Strategy

```
FORMAT: PIGORS-[LANE]-[SEQUENCE]

  PIGORS-A-0001 through PIGORS-A-9999  → Lane A (Custody)
  PIGORS-B-0001 through PIGORS-B-9999  → Lane B (Housing)
  PIGORS-C-0001 through PIGORS-C-9999  → Lane C (Convergence)
  PIGORS-D-0001 through PIGORS-D-9999  → Lane D (PPO)
  PIGORS-E-0001 through PIGORS-E-9999  → Lane E (Misconduct)
  PIGORS-F-0001 through PIGORS-F-9999  → Lane F (Appellate)

CROSS-COURT REFERENCE:
  When citing an exhibit from Lane A in a Lane F filing:
  "See Exhibit PIGORS-A-0042, previously filed in 14th Circuit Court,
   Case No. 2024-001507-DC, and incorporated by reference herein."
```

### 5.3 Exhibit Cross-Reference SQL

```sql
-- Master exhibit index across all lanes
SELECT
    ei.filing_id,
    ei.exhibit_label,
    ei.exhibit_title,
    ei.bates_start,
    ei.bates_end,
    ei.page_count_estimate,
    ei.description
FROM exhibit_index ei
ORDER BY ei.bates_start;

-- Exhibits used in multiple filings (cross-court sharing candidates)
SELECT
    ecr.source_table,
    ecr.source_id,
    ecr.filing_ids,
    ecr.filing_count,
    ecr.bates_numbers
FROM exhibit_cross_references ecr
WHERE ecr.filing_count > 1
ORDER BY ecr.filing_count DESC;

-- Evidence quotes usable across multiple lanes
SELECT
    eq.quote_text,
    eq.source_file,
    eq.page_number,
    eq.category,
    eq.lane,
    eq.relevance_score,
    eq.filing_refs
FROM evidence_quotes eq
WHERE eq.is_duplicate = 0
  AND eq.relevance_score >= 7.0
ORDER BY eq.relevance_score DESC
LIMIT 50;
```

### 5.4 Court-Specific Authentication Requirements

| Court | Requirement | How to Satisfy |
|-------|-------------|----------------|
| **14th Circuit** | MRE 901(a) — sufficient to support finding of authenticity | Affidavit or testimony establishing source and custody |
| **Michigan COA** | Appendix per MCR 7.212(C) — copies of relevant lower court documents | Certified copies from clerk; or copies already in lower court record |
| **USDC W.D. Mich** | FRE 901(a) — same standard; FRE 902 self-authenticating docs | Certified copies (FRE 902(4)), official publications (FRE 902(5)) |
| **JTC** | Copies acceptable for complaint | Attach copies to complaint letter; JTC investigates independently |
| **AGC** | Copies acceptable for grievance | Attach copies to complaint form |

### 5.5 Original vs. Certified Copy Requirements

```
RULE OF THUMB:
  - State trial court: originals preferred, copies acceptable with authentication
  - COA: copies in appendix (certified copies of orders/judgments)
  - Federal: copies acceptable under FRE 1003 unless genuine question of authenticity
  - JTC/AGC: copies acceptable — they conduct independent investigation

WHEN TO GET CERTIFIED COPIES:
  - Court orders and judgments → always get certified copies from clerk
  - Transcripts → court reporter certification suffices
  - Public records → certified copies from issuing agency
  - Everything else → self-authentication via affidavit
```

---

## Module MC6: Status Dashboard Queries

### 6.1 Master Multi-Court Dashboard

```sql
-- ═══════════════════════════════════════════════════════════
-- MULTI-COURT STATUS DASHBOARD
-- Run against: litigation_context.db
-- PRAGMAs: busy_timeout=60000; journal_mode=WAL; cache_size=-32000
-- ═══════════════════════════════════════════════════════════

-- 1. ALL UPCOMING DEADLINES (cross-court, urgency-ranked)
SELECT
    d.title,
    d.due_date,
    d.court,
    d.case_number,
    d.urgency,
    d.status,
    CAST(julianday(d.due_date) - julianday('now') AS INTEGER) AS days_left,
    CASE
        WHEN julianday(d.due_date) - julianday('now') < 0 THEN '🔴 OVERDUE'
        WHEN julianday(d.due_date) - julianday('now') < 7 THEN '🟠 CRITICAL'
        WHEN julianday(d.due_date) - julianday('now') < 14 THEN '🟡 SOON'
        WHEN julianday(d.due_date) - julianday('now') < 30 THEN '🟢 UPCOMING'
        ELSE '⚪ DISTANT'
    END AS urgency_level
FROM deadlines d
WHERE d.status != 'completed'
ORDER BY d.due_date ASC;
```

```sql
-- 2. FILING READINESS PER COURT/LANE
SELECT
    fr.vehicle_name,
    fr.lane,
    fr.status,
    fr.readiness_score,
    fr.placeholder_count,
    fr.exhibit_count,
    fr.authority_count,
    fr.word_count,
    fr.blockers,
    fr.deadline
FROM filing_readiness fr
ORDER BY
    CASE fr.lane
        WHEN 'A' THEN 1
        WHEN 'B' THEN 2
        WHEN 'C' THEN 3
        WHEN 'D' THEN 4
        WHEN 'E' THEN 5
        WHEN 'F' THEN 6
    END,
    fr.readiness_score DESC;
```

```sql
-- 3. RECENT DOCKET ACTIVITY ACROSS ALL COURTS
SELECT
    de.case_number,
    de.event_date,
    de.event_type,
    de.description,
    de.filed_by
FROM docket_events de
ORDER BY de.event_date DESC
LIMIT 20;
```

```sql
-- 4. CLAIMS STRENGTH PER LANE
SELECT
    c.lane,
    c.claim_type,
    c.description,
    c.status,
    c.evidence_count,
    c.strength_score
FROM claims c
WHERE c.status = 'active'
ORDER BY c.strength_score DESC;
```

```sql
-- 5. JUDICIAL VIOLATIONS LOG (for JTC/misconduct tracking)
SELECT
    jv.violation_type,
    jv.date_occurred,
    jv.mcr_rule,
    jv.canon,
    jv.severity,
    jv.description,
    jv.source_file
FROM judicial_violations jv
WHERE jv.lane IN ('E', 'A', 'D')
ORDER BY jv.severity DESC, jv.date_occurred DESC;
```

```sql
-- 6. CROSS-COURT SUMMARY STATISTICS
SELECT
    (SELECT COUNT(*) FROM deadlines WHERE status = 'pending') AS pending_deadlines,
    (SELECT COUNT(*) FROM deadlines WHERE status = 'completed') AS completed_deadlines,
    (SELECT COUNT(*) FROM filing_readiness WHERE status = 'draft') AS draft_filings,
    (SELECT COUNT(*) FROM filing_readiness WHERE readiness_score >= 80) AS ready_filings,
    (SELECT COUNT(*) FROM docket_events) AS total_docket_events,
    (SELECT COUNT(*) FROM claims WHERE status = 'active') AS active_claims,
    (SELECT COUNT(*) FROM judicial_violations) AS violation_count,
    (SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate = 0) AS unique_evidence_quotes,
    (SELECT COUNT(DISTINCT filing_id) FROM exhibit_index) AS filings_with_exhibits;
```

### 6.2 Lane-to-Court Status Map

```sql
-- Lane health dashboard with filing readiness
SELECT
    fr.lane,
    CASE fr.lane
        WHEN 'A' THEN 'Watson custody — 14th Circuit Family — 2024-001507-DC'
        WHEN 'B' THEN 'Shady Oaks housing — 14th Circuit Civil — 2025-002760-CZ'
        WHEN 'C' THEN 'Convergence — cross-lane'
        WHEN 'D' THEN 'PPO — 14th Circuit — 2023-5907-PP'
        WHEN 'E' THEN 'Judicial misconduct — JTC/AG'
        WHEN 'F' THEN 'Appellate — COA 366810'
    END AS court_description,
    COUNT(*) AS total_filings,
    SUM(CASE WHEN fr.status = 'ready' THEN 1 ELSE 0 END) AS ready,
    SUM(CASE WHEN fr.status = 'draft' THEN 1 ELSE 0 END) AS drafts,
    SUM(CASE WHEN fr.status = 'blocked' THEN 1 ELSE 0 END) AS blocked,
    ROUND(AVG(fr.readiness_score), 1) AS avg_readiness,
    SUM(fr.placeholder_count) AS total_placeholders
FROM filing_readiness fr
GROUP BY fr.lane
ORDER BY
    CASE fr.lane
        WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3
        WHEN 'D' THEN 4 WHEN 'E' THEN 5 WHEN 'F' THEN 6
    END;
```

---

## Module MC7: Conflict Detection

### 7.1 Preclusion Doctrine Cheat Sheet

#### Res Judicata (Claim Preclusion)
```
ELEMENTS (all must be met for preclusion):
  1. Same parties (or privies)
  2. Same cause of action (transactional test in Michigan)
  3. Final judgment on the merits in prior action
  4. Prior court had jurisdiction

RISK AREAS for Pigors:
  - Custody claims in family court vs. custody-related claims in §1983
    → FRAME DIFFERENTLY: family court = best interests of L.D.W.;
      federal court = due process violation by state actors
  - Housing claims dismissed in civil court vs. housing-related federal claims
    → If 2025-002760-CZ was dismissed WITHOUT prejudice, no preclusion
    → If dismissed WITH prejudice, those specific claims ARE precluded
    → BUT: constitutional violations in the PROCESS are separate claims

SAFE FRAMING:
  State court → family law rights, parenting time, best interests
  Federal court → constitutional rights, due process, equal protection, §1983
  JTC → judicial conduct standards, Canons of Judicial Conduct
  AGC → attorney professional responsibility, MRPC violations
```

#### Collateral Estoppel (Issue Preclusion)
```
ELEMENTS:
  1. Same issue actually litigated in prior proceeding
  2. Issue was actually decided
  3. Resolution was necessary to the judgment
  4. Party against whom estoppel is invoked had full and fair opportunity to litigate

RISK:
  If family court FINDS certain facts (e.g., "Andrew engaged in X behavior"),
  those findings COULD be used against him in other courts.

MITIGATION:
  - Challenge factual findings in family court vigorously (appeal if adverse)
  - In federal court, argue lack of "full and fair opportunity" if due process
    was denied in state court (this is a recognized exception)
  - Document all instances where state court denied due process
    (denied discovery, ex parte communications, no hearing, etc.)
```

#### Rooker-Feldman Doctrine
```
RULE: Federal district courts cannot hear cases that are effectively
      appeals of state court judgments.

APPLIES WHEN:
  - State court loser (Andrew, if he lost in state court)
  - Asks federal court to review/reject state court judgment
  - Injury caused BY the state court judgment itself

DOES NOT APPLY WHEN:
  - Challenging the PROCESS, not the judgment
  - Alleging independent constitutional violations by state actors
  - Claims existed BEFORE the state court judgment
  - Filing was independent of (not an appeal of) state proceedings

SAFE FRAMING FOR §1983:
  ✅ "The judge violated my due process rights BY [specific conduct]"
  ✅ "State actors conspired to deprive me of constitutional rights"
  ✅ "The process used to reach the judgment was unconstitutional"
  ❌ "The state court got the custody decision wrong"
  ❌ "The family court should have ruled in my favor"
```

#### Younger Abstention
```
RULE: Federal courts abstain from interfering with ONGOING state
      judicial proceedings that involve important state interests.

THREE-PART TEST (Middlesex):
  1. Ongoing state judicial proceeding — YES (2024-001507-DC is active)
  2. Important state interest — YES (family law, child welfare)
  3. Adequate opportunity to raise federal claims in state court

CRITICAL EXCEPTIONS (when federal court WILL hear the case):
  - BAD FAITH prosecution or proceeding
  - PATENTLY UNCONSTITUTIONAL statute being enforced
  - EXTRAORDINARY circumstances (no adequate state remedy)

STRATEGY:
  → Build the record showing state court denied adequate opportunity
    to raise constitutional claims (motions denied without hearing,
    due process violations, ex parte proceedings)
  → This defeats the third prong of Younger
  → Alternatively: file §1983 AFTER state proceedings conclude
    (Younger only applies to ONGOING proceedings)
```

### 7.2 Cross-Court Framing Guide

| Claim/Issue | Family Court (14th Circuit) | Federal Court (§1983) | COA/MSC | JTC | AGC |
|-------------|---------------------------|----------------------|---------|-----|-----|
| Custody interference | Best interests of L.D.W.; parenting time rights under CCA | Due process violation; substantive/procedural liberty interest in parent-child relationship | Error of law; abuse of discretion by trial court | Pattern of bias; failure to follow MCR | N/A |
| Ex parte communications | MCR 2.003 disqualification; judicial misconduct | Due process — denied right to be heard; §1983 conspiracy | Preserved error for appeal | Canon 2(B), Canon 3(A)(4) violation | If attorney participated: MRPC 3.5 |
| Denial of hearing | MCR 2.119 motion practice; right to be heard | Procedural due process (Mathews v. Eldridge) | Preserved error | Failure to follow court rules | N/A |
| Biased rulings | MCR 2.003 actual bias; appearance of impropriety | §1983 judicial immunity (qualified) — BUT conspiracy exception | Pattern of error; bias on the record | Canon 1, Canon 2, Canon 3 | N/A |
| PPO abuse/weaponization | Show cause for abuse of PPO process | §1983 malicious prosecution (if involved state actor) | Appeal PPO issuance/denial | If judge enabled weaponization | If attorney filed false PPO |
| Nonservice | MCR 2.105/2.107 — void proceedings if not served | Due process — no notice | Jurisdictional error | Failure to ensure service | If attorney failed service obligations |

### 7.3 What Can Be Said Where

```
COMMUNICATION BOUNDARIES:

JTC COMPLAINT:
  ✅ Factual recitation of judge's conduct
  ✅ Citations to specific MCR rules and Canons violated
  ✅ Dates, courtroom events, orders, transcripts
  ❌ Legal arguments about case outcome
  ❌ Advocacy for how custody should be decided
  ❌ Anything that looks like an appeal

STATE COURT MOTION:
  ✅ Legal arguments under MCR, case law
  ✅ Factual record citations
  ✅ Requests for relief
  ❌ Threats to file in other courts (unprofessional)
  ❌ Reference to JTC complaint (could be seen as threatening judge)
  ❌ Detailed federal constitutional analysis (wrong forum)

FEDERAL §1983 COMPLAINT:
  ✅ Constitutional violations with specificity
  ✅ Each defendant's personal involvement
  ✅ Pattern and practice allegations
  ✅ State court record as evidence
  ❌ Re-litigating custody merits
  ❌ Asking federal court to change custody order
  ❌ Naming judge as defendant without overcoming immunity

COA BRIEF:
  ✅ Errors of law by trial court
  ✅ Abuse of discretion
  ✅ Preserved issues (raised below)
  ✅ Record citations (transcript pages, exhibits)
  ❌ New evidence not in the record
  ❌ Issues not raised/preserved below (with limited exceptions)
  ❌ Personal attacks on the judge (keep it about legal error)
```

### 7.4 Conflict Detection SQL

```sql
-- Detect potential res judicata conflicts: same case_number across claims
SELECT
    c1.claim_type AS claim_1,
    c1.lane AS lane_1,
    c2.claim_type AS claim_2,
    c2.lane AS lane_2,
    c1.description
FROM claims c1
JOIN claims c2 ON c1.description LIKE '%' || c2.claim_type || '%'
    AND c1.id != c2.id
    AND c1.lane != c2.lane
WHERE c1.status = 'active' AND c2.status = 'active'
ORDER BY c1.lane, c2.lane;
```

```sql
-- Deadlines in multiple courts within 3 days of each other (scheduling conflicts)
SELECT
    d1.title AS filing_1,
    d1.court AS court_1,
    d1.due_date AS date_1,
    d2.title AS filing_2,
    d2.court AS court_2,
    d2.due_date AS date_2,
    ABS(julianday(d1.due_date) - julianday(d2.due_date)) AS days_apart
FROM deadlines d1
JOIN deadlines d2 ON d1.id < d2.id
WHERE d1.status = 'pending'
  AND d2.status = 'pending'
  AND ABS(julianday(d1.due_date) - julianday(d2.due_date)) <= 3
ORDER BY d1.due_date;
```

```sql
-- Evidence that spans multiple lanes (cross-court sharing opportunities)
SELECT
    eq.source_file,
    eq.category,
    GROUP_CONCAT(DISTINCT eq.lane) AS lanes_used,
    COUNT(DISTINCT eq.lane) AS lane_count,
    MAX(eq.relevance_score) AS max_relevance
FROM evidence_quotes eq
WHERE eq.is_duplicate = 0
GROUP BY eq.source_file
HAVING COUNT(DISTINCT eq.lane) > 1
ORDER BY lane_count DESC, max_relevance DESC
LIMIT 30;
```

---

## Appendix A: Lane-to-Court Quick Reference

| Lane | Court | Case Number | Type | Key Filing Rules |
|------|-------|-------------|------|-----------------|
| **A** | 14th Circuit Court, Family Division | 2024-001507-DC | Custody, parenting time, support | MCR 3.200 et seq.; MCL 722.21-722.31 (CCA) |
| **B** | 14th Circuit Court, Civil Division | 2025-002760-CZ | Housing, property, Shady Oaks | MCR 2.111 (complaints); MCR 2.116 (SJ) |
| **C** | Cross-lane convergence | Multiple | Multi-court coordination | This skill manages Lane C |
| **D** | 14th Circuit Court | 2023-5907-PP | PPO, protection orders | MCL 600.2950; MCR 3.700 et seq. |
| **E** | JTC / AGC | N/A | Judicial/attorney misconduct | MCR 9.200 (JTC); MCR 9.100 (AGC) |
| **F** | Michigan Court of Appeals / MSC | COA 366810 | Appeals, extraordinary writs | MCR 7.200 et seq. (COA); MCR 7.300 et seq. (MSC) |
| — | 60th District Court | 2025-25245676SM | Criminal (trial April 7, 2026) | MCR 6.000 et seq.; criminal procedure |
| — | USDC W.D. Michigan | TBD | §1983 civil rights | FRCP; 42 U.S.C. §1983; W.D. Mich. Local Rules |

## Appendix B: Emergency Protocol

```
IF CHILD SAFETY EMERGENCY:
  1. Call 911 if immediate physical danger
  2. File emergency ex parte motion in 14th Circuit Family (Lane A)
     → MCR 3.207 — emergency custody/parenting time
  3. Notify FOC (Pamela Rusco) immediately
  4. Document everything with dates, times, witnesses
  5. Preserve all evidence (photos, messages, recordings)
  6. File police report if applicable
  7. Consider emergency PPO (Lane D) if appropriate
  8. All other courts become secondary until child is safe

IF INCARCERATION RISK (Criminal Case):
  1. Criminal defense is PRIORITY — April 7, 2026 trial
  2. Do NOT make statements in other courts that could be used
     against you in criminal court (5th Amendment)
  3. Consider staying discovery in civil cases pending criminal resolution
  4. Coordinate all filings with criminal defense strategy
```

## Appendix C: Database Connection Protocol

All queries in this skill MUST use these PRAGMAs:

```sql
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

Primary database: `C:\Users\andre\LitigationOS\litigation_context.db`

Key tables referenced:
- `deadlines` (10 columns) — urgency-ranked filing deadlines
- `filing_readiness` (14 columns) — per-vehicle readiness scores
- `docket_events` (8 columns) — 683+ docket entries across courts
- `courts` (11 columns) — court registry with addresses and e-filing URLs
- `claims` (8 columns) — active claims per lane with strength scores
- `judicial_violations` (10 columns) — documented misconduct instances
- `exhibit_index` (9 columns) — Bates-stamped exhibit registry
- `exhibit_cross_references` (6 columns) — exhibits shared across filings
- `evidence_quotes` (12 columns) — sourced evidence with relevance scoring
- `documents` (12 columns) — document inventory with lane assignment

Always verify schema before querying: `PRAGMA table_info(table_name)`
