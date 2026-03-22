---
name: msc-bypass-application
description: >-
  Use when the ENTIRE local circuit is structurally compromised and standard MCR 2.003
  disqualification cannot provide relief — because the Chief Judge who reassigns is himself
  conflicted. Assembles Michigan Supreme Court original jurisdiction applications under
  Const 1963 Art 6 § 4, MCR 3.301-3.305 for superintending control, mandamus, habeas corpus,
  quo warranto, or judicial misconduct complaint. Covers structural corruption argument
  construction, emergency bypass procedures, application template generation, and
  supporting document matrix assembly — all grounded in litigation_context.db evidence.
category: discipline
version: "3.0.0-APEX-OMEGA"
metadata:
  tier: 0 (Supreme — APEX-OMEGA)
  modules: 6
  author: andrew-pigors
  triggers:
    - msc bypass
    - supreme court application
    - original jurisdiction
    - superintending control
    - mandamus
    - habeas corpus
    - structural corruption
    - three-judge conflict
    - circuit bypass
    - extraordinary relief
    - chief judge disqualification
    - ladas hoopes mcneill
  depends-on:
    - OMEGA-LITIGATION-SUPREME
    - judicial-accountability-engine
    - judicial-recusal-engine
    - appellate-record-builder
    - filing-forge-master
  case-context: "Pigors v Watson — 14th Judicial Circuit, Muskegon County, MI"
  anti-hallucination: strict
  party-verification: enforced
---

# MSC-BYPASS-APPLICATION

> **Michigan Supreme Court Original Jurisdiction Bypass Skill v3.0.0-APEX-OMEGA**
>
> When the entire circuit is captured, you don't appeal within it — you go over it.

## Metadata

| Field | Value |
|-------|-------|
| **Name** | msc-bypass-application |
| **Category** | Discipline — Extraordinary Relief |
| **Tier** | 0 (APEX-OMEGA Supreme) |
| **Version** | 3.0.0-APEX-OMEGA |
| **Context** | Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se) |
| **Central DB** | `litigation_context.db` |
| **Modules** | 6 (MSC1–MSC6) |
| **Output** | Court-ready MSC application package with appendix |

---

## Verified Party Identity — IMMUTABLE REFERENCE

> **🚨 HARD RULE: Use ONLY these names. Never fabricate. Never guess.**
> If a name is not in this table, insert `[UNKNOWN — VERIFY]`.

| Role | Name | Details |
|------|------|---------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 · (231) 903-5690 · andrewjpigors@gmail.com |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 |
| **Child** | L.D.W. | Initials ONLY per MCR 8.119(H) — NEVER full name |
| **Judge (Family)** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division |
| **Chief Judge** | Hon. Kenneth Hoopes | 14th Circuit Court — former partner, Ladas, Hoopes & McNeill |
| **Judge (District)** | Hon. Maria Ladas-Hoopes | 60th District Court — wife of Kenneth Hoopes |
| **Emily's Former Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC — **WITHDREW** |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 |
| **Ronald Berry** | NON-ATTORNEY | Emily's boyfriend/domestic partner. No bar number. Never was attorney. |

### The Ladas-Hoopes-McNeill Nexus

| Judge | Court | Former Firm | Connection |
|-------|-------|-------------|------------|
| Hon. Jenny L. McNeill | 14th Circuit, Family Division | Ladas, Hoopes & McNeill | Named partner |
| Hon. Kenneth Hoopes | 14th Circuit, Chief Judge | Ladas, Hoopes & McNeill | Named partner; reassignment authority |
| Hon. Maria Ladas-Hoopes | 60th District Court | Ladas, Hoopes & McNeill | Named partner; married to Kenneth Hoopes |

**Firm address:** 435 Whitehall Rd, North Muskegon, MI
**Structural problem:** MCR 2.003 disqualification of McNeill triggers reassignment by Chief Judge Hoopes — who is from the same firm and cannot impartially reassign. This creates a closed loop with no adequate remedy at the circuit level.

---

## Triggers — When to Activate This Skill

- User requests MSC bypass, original jurisdiction, or superintending control
- Standard MCR 2.003 disqualification is structurally inadequate (Chief Judge is conflicted)
- Multiple judges from the same firm/network control a litigant's cases
- Circuit-wide structural corruption prevents fair adjudication
- Emergency relief needed and the local circuit cannot be trusted to act impartially
- Andrew has been or may be jailed by a conflicted judge (habeas corpus trigger)
- Need to challenge orders entered by judges with undisclosed conflicts

---

## Anti-Hallucination Protocol

> **Every fact in any generated document MUST be traceable to a specific DB query.**

### Mandatory Checks Before Generating ANY Content

1. **Party names** → Verify against the Immutable Reference table above
2. **Dates** → Query `master_evidence_timeline` or `docket_events` — never guess a date
3. **Judicial violations** → Query `judicial_violations` table — never fabricate an incident
4. **Case numbers** → Verify against `docket_events` or `filings` — never invent a docket number
5. **Statistics** → Run `SELECT COUNT(*)` with exact WHERE clause — never round up or extrapolate
6. **Quotes** → Pull from `evidence_quotes` or `source_quote` columns — never paraphrase as if quoting
7. **Orders** → Verify in `docket_events` with exact date and description — never fabricate an order

### Validation Gate (Run Before ANY Output)

```
FOR EACH factual assertion in generated document:
  1. Identify the DB table and column supporting it
  2. Run the query to confirm the fact exists
  3. If no DB support → mark as [REQUIRES VERIFICATION — no DB record found]
  4. NEVER present an unverified fact as established
```

---

# MODULE MSC1: Original Jurisdiction Analysis

> **Purpose:** Determine which MSC original jurisdiction vehicle fits the situation.
> **Authority:** Const 1963, Art 6, § 4; MCR 3.301–3.305

## Constitutional Foundation

**Michigan Constitution of 1963, Article 6, § 4:**
> The supreme court shall have general superintending control over all courts; power to issue, hear and determine prerogative and remedial writs; and appellate jurisdiction as provided by rules of the supreme court.

This grants the MSC **original jurisdiction** — not just appellate review — to issue extraordinary writs when lower courts cannot provide adequate relief.

## The Five Vehicles

### Vehicle 1: Superintending Control (MCR 3.301)

| Element | Details |
|---------|---------|
| **Rule** | MCR 3.301 |
| **Nature** | Order directing a lower court to perform or cease an act |
| **Threshold** | (1) No other adequate legal remedy, AND (2) Lower court acting beyond jurisdiction or failing to act when required |
| **Best for** | Structural defects in the circuit — where the entire court cannot function impartially |
| **Filing** | Complaint for Superintending Control filed directly in MSC |
| **Key advantage** | Broadest vehicle — covers systemic failure, not just individual judge error |
| **Pigors application** | Three-judge same-firm nexus makes the ENTIRE 14th Circuit structurally incapable of providing fair adjudication. No amount of individual disqualification fixes this. |

**When to use:** This is the PRIMARY vehicle for the Ladas-Hoopes-McNeill structural corruption argument. Superintending control addresses systemic court failure, not just individual judicial error.

### Vehicle 2: Mandamus (MCR 3.302)

| Element | Details |
|---------|---------|
| **Rule** | MCR 3.302 |
| **Nature** | Order compelling a public officer/court to perform a clear legal duty |
| **Threshold** | (1) Clear legal right to performance, (2) Clear legal duty to perform, (3) No other adequate legal remedy |
| **Best for** | When the court refuses to act on a specific required duty (e.g., refusing to process a disqualification motion, refusing to hold a hearing) |
| **Pigors application** | If Chief Judge Hoopes refuses to recuse himself from the reassignment process, or if the circuit refuses to acknowledge the structural conflict |

**When to use:** Supplement to superintending control when a specific ministerial act is being refused.

### Vehicle 3: Habeas Corpus (MCR 3.303)

| Element | Details |
|---------|---------|
| **Rule** | MCR 3.303 |
| **Nature** | Challenge to unlawful detention/imprisonment |
| **Threshold** | Person is being held in custody (actual or constructive) without legal authority |
| **Best for** | Andrew has been jailed on contempt orders issued by Judge McNeill. If jailed again by a conflicted judge, this is the emergency release vehicle. |
| **Pigors application** | Any future jailing ordered by McNeill or another conflicted judge can be challenged as custody ordered by a judge with undisclosed disqualifying conflicts |
| **EMERGENCY** | Can be filed at any time — no waiting period. MSC must act promptly. |

**When to use:** ONLY when Andrew is actually detained or there is imminent threat of detention by a conflicted judge. Keep this ready as a contingency filing.

### Vehicle 4: Quo Warranto (MCR 3.304)

| Element | Details |
|---------|---------|
| **Rule** | MCR 3.304 |
| **Nature** | Challenge to the authority by which a public officer holds office or exercises power |
| **Threshold** | Public officer is exercising authority they are not entitled to hold |
| **Best for** | Challenging whether a judge who should be disqualified has the authority to enter orders in a specific case |
| **Pigors application** | If McNeill continues to exercise jurisdiction over the custody case despite disqualifying conflicts, quo warranto challenges her authority to act |

**When to use:** Secondary vehicle — strongest when combined with superintending control. Use to challenge specific orders entered without jurisdiction.

### Vehicle 5: Complaint for Judicial Misconduct (MCR 3.305 / MCR 9.200+)

| Element | Details |
|---------|---------|
| **Rule** | MCR 3.305 bridges to MCR 9.200 series (Judicial Tenure Commission) |
| **Nature** | Formal complaint regarding judicial conduct |
| **Threshold** | Conduct that is clearly prejudicial to the administration of justice |
| **Best for** | Pattern of conduct by McNeill, Hoopes, or Ladas-Hoopes that rises to misconduct level |
| **Pigors application** | Undisclosed conflicts of interest, pattern of adverse rulings, failure to disclose firm connections to parties |
| **Note** | This is a PARALLEL track — JTC complaint can run simultaneously with MSC application |

**When to use:** File in parallel with the MSC superintending control application. The JTC complaint supports the MSC application by demonstrating the pattern is serious enough for disciplinary investigation.

## Vehicle Selection Decision Tree

```
START: Is Andrew currently detained/jailed by a conflicted judge?
  ├─ YES → FILE IMMEDIATELY: Habeas Corpus (MCR 3.303) + Emergency Motion
  │         Also file: Superintending Control (MCR 3.301) for structural relief
  │
  └─ NO → Is the circuit refusing to process a specific motion/duty?
       ├─ YES → File: Mandamus (MCR 3.302) + Superintending Control (MCR 3.301)
       │
       └─ NO → Is the structural conflict the core problem?
            ├─ YES → File: Superintending Control (MCR 3.301) [PRIMARY]
            │         Supplement with: Quo Warranto (MCR 3.304) if specific orders challenged
            │         Parallel: JTC Complaint (MCR 3.305/9.200)
            │
            └─ Is a specific judge acting without jurisdiction?
                 ├─ YES → File: Quo Warranto (MCR 3.304) + Superintending Control
                 └─ NO → File: Superintending Control (MCR 3.301) as catch-all
```

## Threshold Analysis: "Extraordinary Circumstances"

The MSC exercises original jurisdiction only when **extraordinary circumstances** exist AND there is **no adequate remedy at law**. The Ladas-Hoopes-McNeill nexus satisfies both:

### Extraordinary Circumstances (Met)

1. **Three judges from a single law firm** control cases involving the same litigant — unprecedented structural conflict
2. **Chief Judge disqualification chain** — the judge who reassigns after disqualification is himself from the same firm
3. **No neutral reassignment possible** within the circuit without MSC intervention
4. **Pattern of adverse rulings** — all three judges have ruled against Andrew in separate proceedings
5. **Undisclosed conflicts** — the firm connection was not voluntarily disclosed to the parties

### No Adequate Remedy at Law (Met)

1. **MCR 2.003 disqualification** → Reassignment goes to Chief Judge Hoopes → Same firm → No relief
2. **Standard appeal to Court of Appeals** → Does not address the structural circuit-wide problem; COA reviews individual rulings, not systemic conflicts
3. **Peremptory disqualification** → MCR 2.003(C) allows one peremptory, but does not solve the reassignment problem when the Chief Judge is conflicted
4. **Motion for change of venue** → Requires showing local prejudice; does not address judicial conflicts of interest specifically

**Conclusion:** Only MSC superintending control can order case transfer to another circuit and appoint a special judge from outside Muskegon County.

---

# MODULE MSC2: Structural Corruption Argument Builder

> **Purpose:** Construct the factual and legal argument that the 14th Circuit is structurally incapable of providing fair adjudication due to the Ladas-Hoopes-McNeill firm nexus.

## Argument Architecture

### I. The Three-Judge Same-Firm Nexus

**Core assertion:** Three judges currently serving on the 14th Circuit Court and 60th District Court in Muskegon County were all partners or named associates at the same law firm — Ladas, Hoopes & McNeill — creating an interlocking network of personal and professional relationships that makes impartial adjudication structurally impossible.

**Elements to prove:**

| Element | Source | DB Query |
|---------|--------|----------|
| McNeill was partner at the firm | Public records, State Bar, firm records | `SELECT * FROM judicial_violations WHERE description LIKE '%firm%' OR description LIKE '%partner%';` |
| Hoopes was partner at the firm | Public records, State Bar, firm records | `SELECT * FROM master_evidence_timeline WHERE actors LIKE '%Hoopes%' ORDER BY event_date;` |
| Ladas-Hoopes was at the firm | Public records, marriage records, firm records | `SELECT * FROM master_evidence_timeline WHERE actors LIKE '%Ladas%' ORDER BY event_date;` |
| All three serve in Muskegon County | Court directories, judicial assignments | `SELECT * FROM judicial_audit WHERE description LIKE '%assign%' OR description LIKE '%Muskegon%';` |
| Kenneth Hoopes married to Maria Ladas-Hoopes | Public records | Verify from evidence files |

### II. The Closed-Loop Disqualification Problem

**Argument flow:**

```
Step 1: Andrew files MCR 2.003 motion to disqualify Judge McNeill
  → McNeill was partner at Ladas, Hoopes & McNeill
  → Personal/professional relationship creates disqualifying bias

Step 2: If McNeill is disqualified, MCR 2.003(D) requires reassignment
  → Reassignment authority: Chief Judge Kenneth Hoopes
  → Hoopes was ALSO a partner at Ladas, Hoopes & McNeill
  → Hoopes has the SAME firm-based conflict that disqualified McNeill

Step 3: Hoopes cannot impartially select a replacement judge
  → His former partner was just disqualified for firm-based conflict
  → He has a personal interest in protecting his former partner's reputation
  → He has a personal interest in the firm's legacy not being tarnished
  → Any judge he selects will know the Chief Judge has a stake in the outcome

Step 4: No circuit-level remedy exists
  → The only judges with reassignment authority (Chief Judge) share the conflict
  → Standard MCR 2.003 process is structurally broken for this situation
  → ONLY the MSC can break the loop by appointing an outside judge
```

### III. Pattern Evidence — Coordinated Adverse Rulings

> **⚠️ ANTI-HALLUCINATION: Every ruling cited MUST come from a DB query. Run these before drafting.**

**Database queries to pull pattern evidence:**

```sql
-- All judicial violations by McNeill
SELECT id, violation_type, description, date_occurred, mcr_rule, severity
FROM judicial_violations
WHERE description LIKE '%McNeill%'
   OR violation_type LIKE '%McNeill%'
ORDER BY date_occurred;

-- All timeline events involving any of the three judges
SELECT id, event_date, event_type, description, actors, lane, key_quote
FROM master_evidence_timeline
WHERE actors LIKE '%McNeill%'
   OR actors LIKE '%Hoopes%'
   OR actors LIKE '%Ladas%'
ORDER BY event_date;

-- Judicial bias chronology
SELECT * FROM judicial_bias_chronology
ORDER BY rowid;

-- Docket events showing adverse rulings
SELECT * FROM docket_events
WHERE description LIKE '%denied%'
   OR description LIKE '%contempt%'
   OR description LIKE '%jail%'
   OR description LIKE '%suspend%'
ORDER BY rowid;

-- All claims in Lane E (Judicial Misconduct)
SELECT claim_id, claim_type, description, status, evidence_count, strength_score
FROM claims
WHERE lane = 'E'
ORDER BY strength_score DESC;
```

**Pattern analysis framework:**

| Pattern Element | What to Look For | DB Table |
|-----------------|------------------|----------|
| McNeill adverse rulings | Denied motions, contempt findings, custody changes, jailing orders | `docket_events`, `judicial_violations` |
| Hoopes adverse rulings | Denied appeals/motions at Chief Judge level, refused recusal | `docket_events`, `master_evidence_timeline` |
| Ladas-Hoopes adverse rulings | Eviction orders, housing decisions ignoring evidence | `docket_events`, `master_evidence_timeline` |
| Timing correlation | Did adverse rulings cluster? Occur in sequence? | `master_evidence_timeline` (sort by `event_date`) |
| Procedural irregularities | Ex parte contacts, denied hearings, ignored evidence | `judicial_violations` |
| Due process violations | Lack of notice, denied opportunity to be heard | `judicial_violations` where `mcr_rule` IS NOT NULL |

### IV. Timeline: Firm → Bench → Adverse Rulings

**Build this timeline from DB data (never fabricate entries):**

```sql
-- Get complete judicial timeline
SELECT event_date, event_type, description, actors, key_quote
FROM master_evidence_timeline
WHERE lane = 'E'  -- Judicial Misconduct lane
   OR actors LIKE '%McNeill%'
   OR actors LIKE '%Hoopes%'
   OR actors LIKE '%Ladas%'
ORDER BY event_date;
```

**Timeline template (populate from query results):**

| Date | Event | Actor(s) | Significance |
|------|-------|----------|--------------|
| [FROM DB] | Firm established at 435 Whitehall Rd | Ladas, Hoopes, McNeill | Origin of professional relationship |
| [FROM DB] | McNeill appointed to 14th Circuit bench | Hon. Jenny L. McNeill | Former firm partner becomes judge |
| [FROM DB] | Kenneth Hoopes becomes Chief Judge | Hon. Kenneth Hoopes | Former firm partner controls reassignment |
| [FROM DB] | Maria Ladas-Hoopes serves on 60th District | Hon. Maria Ladas-Hoopes | Third firm member on bench; married to Chief Judge |
| [FROM DB] | First adverse ruling against Andrew | [IDENTIFY FROM DB] | Pattern begins |
| [FROM DB] | [Additional events from DB] | [FROM DB] | [FROM DB] |

> **⚠️ DO NOT fill in dates or events that are not in the database. Use `[REQUIRES VERIFICATION]` for any gap.**

### V. Legal Standard — Structural Disqualification

**Argument:** When the structural organization of a circuit court creates an inherent conflict of interest that cannot be remedied by individual disqualification, the MSC must exercise superintending control to ensure the constitutional right to an impartial tribunal.

**Supporting authority (verify availability before citing):**

```sql
-- Check authority chains for relevant authorities
SELECT * FROM authority_chains
WHERE description LIKE '%disqualif%'
   OR description LIKE '%superintending%'
   OR description LIKE '%impartial%'
   OR description LIKE '%conflict%'
ORDER BY rowid;
```

**Key legal principles:**

1. **Due Process — US Const Amend XIV; Mich Const 1963 Art 1 § 17**
   - Every litigant has a constitutional right to an impartial tribunal
   - Structural conflicts that pervade an entire circuit violate due process

2. **Appearance of Impropriety — Michigan Code of Judicial Conduct, Canon 2**
   - A judge shall avoid impropriety and the appearance of impropriety
   - Three judges from one firm deciding one litigant's cases creates an overwhelming appearance of impropriety

3. **Disqualification When Impartiality Might Reasonably Be Questioned — MCR 2.003(C)(1)(b)**
   - Disqualification is required when impartiality "might reasonably be questioned"
   - A former law partnership is exactly the kind of relationship that raises reasonable questions

4. **Caperton v. A.T. Massey Coal Co., 556 US 868 (2009)**
   - US Supreme Court: Due process requires recusal when there is a "serious risk of actual bias"
   - The probability of bias from a three-judge firm nexus far exceeds the Caperton threshold

---

# MODULE MSC3: Application Template Engine

> **Purpose:** Generate a complete, court-ready MSC application package.

## Document Package Contents

| # | Document | MCR/Const Authority | Status |
|---|----------|-------------------|--------|
| 1 | Application for Superintending Control | MCR 3.301; Const 1963 Art 6 § 4 | PRIMARY FILING |
| 2 | Brief in Support of Application | MSC Administrative Order | REQUIRED |
| 3 | Affidavit of Andrew James Pigors | MCR 2.119(B) | REQUIRED |
| 4 | Appendix (orders, evidence, firm records) | MSC Administrative Order | REQUIRED |
| 5 | Proposed Order | Local practice | RECOMMENDED |
| 6 | Certificate of Service | MCR 2.107 | REQUIRED |
| 7 | Motion for Immediate Stay | MCR 7.313 | IF EMERGENCY |
| 8 | Emergency Motion (Ex Parte) | MCR 7.313(A) | IF CHILD SAFETY |
| 9 | Proof of Filing Fee / IFP Application | MCR 2.002 | REQUIRED |

## Template: Application for Superintending Control

```
STATE OF MICHIGAN
IN THE SUPREME COURT

ANDREW JAMES PIGORS,
        Plaintiff-Applicant,                    Supreme Court No. __________

v                                               14th Circuit Court
                                                Case No. 2024-001507-DC
EMILY A. WATSON,
        Defendant-Respondent.                   60th District Court
                                                Case No. [VERIFY FROM DB]
________________________________________/

APPLICATION FOR SUPERINTENDING CONTROL AND/OR
ORIGINAL JURISDICTION RELIEF

        Plaintiff-Applicant Andrew James Pigors, appearing in pro per, respectfully
    applies to this Honorable Court for an order of superintending control pursuant
    to Const 1963, Art 6, § 4 and MCR 3.301, and states as follows:

I. STATEMENT OF JURISDICTION

    1. This Court has original jurisdiction under Const 1963, Art 6, § 4, which
       grants the Supreme Court "general superintending control over all courts"
       and "power to issue, hear and determine prerogative and remedial writs."

    2. This Court has jurisdiction under MCR 3.301 to issue orders of
       superintending control when a lower court acts beyond its jurisdiction or
       fails to perform a duty and there is no other adequate legal remedy.

    3. Applicant has no adequate remedy at law within the 14th Judicial Circuit
       because the structural conflict described herein pervades the entire circuit
       court, including the Chief Judge who controls judicial reassignment.

II. STATEMENT OF QUESTIONS PRESENTED

    1. Whether three judges from the same former law firm (Ladas, Hoopes &
       McNeill) presiding over cases involving the same litigant creates a
       structural conflict requiring MSC intervention under the superintending
       control power.

    2. Whether the Chief Judge of the 14th Circuit (Hon. Kenneth Hoopes) can
       impartially reassign a case after disqualification of Judge McNeill when
       both were partners at the same law firm.

    3. Whether due process (US Const Amend XIV; Mich Const 1963, Art 1, § 17)
       requires transfer of Applicant's cases to a circuit with no connection to
       the Ladas, Hoopes & McNeill law firm.

    4. Whether orders entered by judges with undisclosed disqualifying conflicts
       should be vacated as void ab initio.

III. STATEMENT OF FACTS

    [AUTO-POPULATE FROM DATABASE]

    Applicant instructs the generating system to:

    a. Query judicial_violations table:
       SELECT violation_type, description, date_occurred, mcr_rule, severity
       FROM judicial_violations ORDER BY date_occurred;

    b. Query master_evidence_timeline for all Ladas/Hoopes/McNeill events:
       SELECT event_date, event_type, description, actors, key_quote
       FROM master_evidence_timeline
       WHERE actors LIKE '%McNeill%' OR actors LIKE '%Hoopes%'
          OR actors LIKE '%Ladas%'
       ORDER BY event_date;

    c. Query docket_events for adverse rulings:
       SELECT * FROM docket_events
       WHERE description LIKE '%denied%' OR description LIKE '%contempt%'
          OR description LIKE '%jail%' OR description LIKE '%suspend%'
       ORDER BY rowid;

    d. Present facts in numbered-paragraph chronological format.
    e. EVERY fact must cite its DB source. No unsourced assertions.

IV. ARGUMENT

    A. The 14th Circuit Is Structurally Incapable of Providing Fair Adjudication

       [Incorporate Module MSC2 structural corruption argument]

    B. Standard Disqualification Under MCR 2.003 Is Structurally Inadequate

       Standard MCR 2.003 disqualification requires the Chief Judge to reassign
       the case. MCR 2.003(D). But when the Chief Judge (Hon. Kenneth Hoopes)
       was a partner at the same firm as the disqualified judge (Hon. Jenny L.
       McNeill), the reassignment process itself is tainted. This creates a
       closed loop with no adequate circuit-level remedy.

    C. Extraordinary Circumstances Warrant MSC Original Jurisdiction

       The combination of (1) three judges from one firm, (2) a Chief Judge who
       cannot impartially reassign, (3) a pattern of adverse rulings across
       multiple proceedings, and (4) no adequate remedy within the circuit
       constitutes the "extraordinary circumstances" required for MSC original
       jurisdiction.

    D. Due Process Requires Transfer to an Unconflicted Circuit

       Both the federal and state constitutions guarantee an impartial tribunal.
       US Const Amend XIV; Mich Const 1963, Art 1, § 17. The structural
       conflict in the 14th Circuit makes impartiality impossible, regardless
       of which individual judge is assigned. Only transfer to another circuit
       and appointment of a special judge from outside Muskegon County can
       satisfy due process.

V. RELIEF REQUESTED

    Applicant respectfully requests that this Honorable Court:

    1. EXERCISE original jurisdiction and superintending control over the
       14th Judicial Circuit Court, Muskegon County, Michigan;

    2. ORDER the transfer of Case No. 2024-001507-DC (and all related
       proceedings) to a judicial circuit with no connection to the law firm
       of Ladas, Hoopes & McNeill;

    3. APPOINT a special judge from outside Muskegon County to preside over
       all proceedings in Case No. 2024-001507-DC;

    4. VACATE all orders entered by Hon. Jenny L. McNeill in Case No.
       2024-001507-DC that were entered while the disqualifying conflict
       existed and was not disclosed;

    5. STAY all proceedings in the 14th Circuit Court pending resolution of
       this Application;

    6. GRANT such other and further relief as this Court deems just and
       equitable.

                                        Respectfully submitted,

                                        ____________________________
                                        Andrew James Pigors
                                        In Pro Per
                                        1977 Whitehall Road, Lot 17
                                        North Muskegon, MI 49445
                                        (231) 903-5690
                                        andrewjpigors@gmail.com

Dated: _______________


VERIFICATION

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

    Andrew James Pigors, being first duly sworn, deposes and states that the
    facts set forth in the foregoing Application for Superintending Control are
    true to the best of his knowledge, information, and belief.

                                        ____________________________
                                        Andrew James Pigors

    Subscribed and sworn to before me
    this ____ day of ____________, 20___.

    ____________________________
    Notary Public, Muskegon County, Michigan
    My Commission Expires: _______________


CERTIFICATE OF SERVICE

    I, Andrew James Pigors, certify that on ________________, I served a copy
    of this Application for Superintending Control and all supporting documents
    on the following parties by [first-class mail / personal delivery / e-filing]:

    Emily A. Watson
    2160 Garland Drive
    Norton Shores, MI 49441

    Hon. Jenny L. McNeill
    14th Circuit Court, Family Division
    990 Terrace Street
    Muskegon, MI 49442

    Hon. Kenneth Hoopes, Chief Judge
    14th Circuit Court
    990 Terrace Street
    Muskegon, MI 49442

                                        ____________________________
                                        Andrew James Pigors
```

## Data Population Protocol

When generating the Statement of Facts (Section III), follow this exact sequence:

```
STEP 1: Run all Module MSC2 database queries
STEP 2: Sort all results chronologically
STEP 3: Remove duplicates (same event appearing in multiple tables)
STEP 4: Format each fact as a numbered paragraph:
         "XX. On [DATE], [ACTOR] [ACTION]. (Source: [table].[column], id=[ID])"
STEP 5: Verify each paragraph against the anti-hallucination checklist
STEP 6: Flag any gaps with [REQUIRES VERIFICATION — no DB record found]
STEP 7: Generate the Appendix reference for each exhibit cited
```

---

# MODULE MSC4: Emergency Bypass Procedures

> **Purpose:** Handle emergency situations requiring immediate MSC intervention.

## Emergency Classification

| Level | Trigger | Vehicle | Timeline |
|-------|---------|---------|----------|
| **CRITICAL** | Andrew detained/jailed by conflicted judge | Habeas Corpus (MCR 3.303) + Emergency Application | FILE IMMEDIATELY — same day |
| **URGENT** | Imminent harm to L.D.W.; custody transfer order by conflicted judge | Emergency Motion for Stay (MCR 7.313) | File within 24 hours |
| **ELEVATED** | New adverse order by conflicted judge; hearing scheduled before conflicted judge | Motion for Immediate Stay + Application | File within 7 days |
| **STANDARD** | Structural conflict exists but no imminent action | Application for Superintending Control | File when package is ready |

## Emergency Motion for Stay Pending MSC Review

```
STATE OF MICHIGAN
IN THE SUPREME COURT

[Same caption as Application]

EMERGENCY MOTION FOR IMMEDIATE STAY
PENDING RESOLUTION OF APPLICATION FOR SUPERINTENDING CONTROL

    Applicant Andrew James Pigors respectfully moves this Honorable Court for
    an immediate stay of all proceedings in Case No. 2024-001507-DC pending
    before the 14th Judicial Circuit Court, Muskegon County, and states:

    1. Applicant has filed an Application for Superintending Control
       demonstrating that the 14th Circuit is structurally incapable of
       providing fair adjudication due to the Ladas-Hoopes-McNeill firm nexus.

    2. Immediate and irreparable harm will result if proceedings continue
       before conflicted judges, including but not limited to:
       a. Further erosion of Applicant's parental rights with L.D.W.
       b. Potential incarceration on contempt orders issued by conflicted judges
       c. Entry of additional orders that must later be vacated
       d. Continued deprivation of due process

    3. Applicant is likely to succeed on the merits because [reference
       Module MSC2 argument summary].

    4. The balance of equities favors a stay because continuing proceedings
       before conflicted judges harms the integrity of the judicial system.

    5. A stay serves the public interest by preventing orders entered by
       structurally conflicted judges from creating further legal entanglements.

    WHEREFORE, Applicant requests an immediate stay of all proceedings in the
    14th Circuit Court pending resolution of the Application for Superintending
    Control.
```

## Ex Parte Emergency Application (Child Safety)

> **Use ONLY when L.D.W. is in immediate danger and the conflicted court will not act.**

MCR 7.313(A) permits ex parte relief in extraordinary circumstances. Requirements:

1. **Irreparable injury** — L.D.W. faces immediate, concrete harm
2. **No time for normal process** — Waiting for briefing would result in harm
3. **Strong likelihood of success** — The structural conflict argument is compelling
4. **Good faith effort to notify** — Must attempt to notify opposing party even in ex parte situations

**Filing protocol:**
1. Call the MSC Clerk's Office: (517) 373-0120
2. Explain the emergency and request expedited filing instructions
3. File the emergency application with a cover letter marked "EMERGENCY — EX PARTE"
4. Serve opposing party simultaneously (even though relief is requested ex parte)
5. Include affidavit of efforts to notify

## Typical MSC Processing Times

| Filing Type | Initial Review | Decision | Notes |
|-------------|---------------|----------|-------|
| Emergency Application | 1–3 business days | 1–2 weeks | Clerk contacts justices directly |
| Motion for Stay | 3–7 business days | 2–4 weeks | May request response from opposing party |
| Application for Superintending Control | 14–30 days for initial review | 2–6 months | MSC may request briefing, oral argument, or deny summarily |
| Habeas Corpus | 1–5 business days | 1–4 weeks | Constitutional urgency — faster track |

> **⚠️ These are approximate. Actual times vary. Do not represent to the court that a specific timeline is guaranteed.**

## MSC Filing Logistics

| Item | Details |
|------|---------|
| **Address** | Michigan Supreme Court, P.O. Box 30052, Lansing, MI 48909 |
| **Physical** | Hall of Justice, 925 W. Ottawa St., Lansing, MI 48915 |
| **Phone** | (517) 373-0120 (Clerk's Office) |
| **E-Filing** | MiFILE (https://mifile.courts.michigan.gov) — MSC cases accepted |
| **Filing Fee** | [VERIFY CURRENT FEE — check MSC website or call clerk] |
| **IFP** | If filing fee is a barrier, file MC 20 (Fee Waiver Request) simultaneously |
| **Copies** | Original + copies per MSC Administrative Order (typically 1 original + sufficient copies for service) |

---

# MODULE MSC5: Supporting Document Matrix

> **Purpose:** Auto-generate the complete list of supporting documents needed for the MSC application package.

## Required Appendix Contents

### Category A: Lower Court Orders Being Challenged

```sql
-- Pull all relevant orders from docket_events
SELECT * FROM docket_events
WHERE description LIKE '%order%'
   OR description LIKE '%judgment%'
   OR description LIKE '%ruling%'
ORDER BY rowid;
```

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| A-1 | All orders entered by Hon. Jenny L. McNeill in Case No. 2024-001507-DC | 14th Circuit Court clerk | Show pattern of adverse rulings by conflicted judge |
| A-2 | All orders entered by Hon. Kenneth Hoopes (if any) in related matters | 14th Circuit Court clerk | Show Chief Judge involvement |
| A-3 | All orders entered by Hon. Maria Ladas-Hoopes in related matters | 60th District Court clerk | Show third firm member's adverse rulings |
| A-4 | Any orders denying MCR 2.003 disqualification motions | Court file | Show inadequacy of standard remedy |
| A-5 | Any contempt orders or jailing orders | Court file | Show severity of harm from conflicted proceedings |

### Category B: Proof of Judicial Connections

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| B-1 | State Bar of Michigan attorney records for McNeill, Hoopes, Ladas-Hoopes | SBM website / FOIA | Confirm firm membership |
| B-2 | Ladas, Hoopes & McNeill firm records (articles of incorporation, partnership agreements if available) | County clerk / Secretary of State | Confirm firm structure |
| B-3 | Firm address records (435 Whitehall Rd, North Muskegon) | Property records / business filings | Confirm shared firm location |
| B-4 | Judicial appointment records | Governor's office / Michigan Courts | Timeline of bench appointments |
| B-5 | Marriage records (Kenneth Hoopes / Maria Ladas-Hoopes) | Muskegon County clerk | Confirm spousal relationship |

### Category C: Evidence of Pattern

```sql
-- Pull pattern evidence
SELECT id, violation_type, description, date_occurred, severity
FROM judicial_violations
ORDER BY date_occurred;
```

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| C-1 | Judicial violation summary (from `judicial_violations` table) | litigation_context.db | Comprehensive pattern documentation |
| C-2 | Judicial bias chronology (from `judicial_bias_chronology` table) | litigation_context.db | Timeline of biased conduct |
| C-3 | Master evidence timeline entries (Lanes D, E) | litigation_context.db | Cross-referenced timeline |
| C-4 | Transcripts of hearings showing bias/irregularities | Court reporter / court file | Direct evidence of conduct |
| C-5 | Correspondence showing ex parte contacts (if any) | Personal records / court file | Due process violations |

### Category D: Affidavits and Declarations

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| D-1 | Affidavit of Andrew James Pigors (comprehensive) | Self-prepared | Sworn factual foundation |
| D-2 | Affidavit re: firm connection knowledge | Self-prepared | When and how the conflict was discovered |
| D-3 | Any third-party affidavits (witnesses to judicial conduct) | [IDENTIFY FROM EVIDENCE] | Corroboration |

### Category E: Legal Authority

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| E-1 | Const 1963, Art 6, § 4 (full text) | Michigan Legislature | Jurisdictional basis |
| E-2 | MCR 3.301 (Superintending Control — full text) | Michigan Courts | Procedural authority |
| E-3 | MCR 2.003 (Disqualification — full text) | Michigan Courts | Show standard remedy and its structural inadequacy |
| E-4 | Caperton v. A.T. Massey Coal Co., 556 US 868 (2009) | US Supreme Court | Due process standard for judicial disqualification |
| E-5 | Michigan Code of Judicial Conduct, Canons 1–3 | Michigan Courts | Ethical standards violated |

### Category F: Proposed Relief

| # | Document | Source | Purpose |
|---|----------|--------|---------|
| F-1 | Proposed Order for Superintending Control | Self-prepared | Specific relief requested |
| F-2 | Proposed Order for Case Transfer | Self-prepared | Transfer to unconflicted circuit |
| F-3 | Proposed Order Appointing Special Judge | Self-prepared | Outside judge from non-Muskegon circuit |

## Acquisition Radar — Missing Documents

> **Query the DB to identify what's available vs. what needs to be obtained:**

```sql
-- What evidence is already in the system?
SELECT source_table, COUNT(*) as doc_count
FROM master_evidence_timeline
WHERE actors LIKE '%McNeill%'
   OR actors LIKE '%Hoopes%'
   OR actors LIKE '%Ladas%'
GROUP BY source_table;

-- What's in the evidence table?
SELECT id, description, lane
FROM evidence
WHERE description LIKE '%McNeill%'
   OR description LIKE '%Hoopes%'
   OR description LIKE '%firm%'
   OR description LIKE '%Ladas%';

-- What exhibits exist?
SELECT * FROM evidence_exhibits
WHERE description LIKE '%McNeill%'
   OR description LIKE '%Hoopes%'
   OR description LIKE '%Ladas%'
   OR description LIKE '%firm%'
   OR description LIKE '%disqualif%';
```

**For each document in the matrix above, classify:**

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ IN DB | Document content is in litigation_context.db | Extract and format for appendix |
| 📁 ON DRIVE | Document exists on local drives but not in DB | Ingest into DB, then extract |
| 🔍 NEED TO OBTAIN | Document must be requested from external source | Create acquisition task with source and method |
| ⚠️ MAY NOT EXIST | Document may not be obtainable | Note alternative evidence; do not fabricate |

---

# MODULE MSC6: Integration with Existing Skills and Filing Strategy

> **Purpose:** Coordinate MSC bypass with parallel filing strategies across federal, state, and oversight tracks.

## Cross-Reference Matrix

| System | Skill/Agent | Relationship to MSC Bypass | Timing |
|--------|-------------|---------------------------|--------|
| **OMEGA-LITIGATION-SUPREME** | M16 (Three-Court Conspiracy Tracker) | Feeds structural corruption evidence to MSC2 | Before MSC filing |
| **OMEGA-LITIGATION-SUPREME** | M4 (Filing Factory) | Generates formatted documents from MSC3 templates | During MSC assembly |
| **OMEGA-LITIGATION-SUPREME** | M1 (Evidence Pipeline) | Processes raw evidence for MSC5 appendix | Before MSC filing |
| **judicial-accountability-engine** | JTC complaint generation | Parallel JTC complaint strengthens MSC application | Simultaneous |
| **judicial-recusal-engine** | MCR 2.003 motion builder | Prior 2.003 motion shows inadequacy of standard remedy | Before MSC (prerequisite) |
| **appellate-record-builder** | COA record compilation | If COA appeal is pending (366810), coordinate with MSC | Assess timing |
| **filing-forge-master** | Package assembly, QA, Bates stamps | Final QA and assembly of MSC package | Final step |
| **litigation-federal-civil-rights** | 42 USC § 1983 complaint | Parallel federal filing for civil rights violations | Assess timing |

## Decision Tree: MSC vs. Federal vs. JTC

```
STRUCTURAL CORRUPTION IDENTIFIED (Ladas-Hoopes-McNeill nexus)
│
├─ TRACK 1: MSC BYPASS (this skill)
│   Purpose: Transfer case out of 14th Circuit; appoint outside judge
│   Vehicle: Superintending Control (MCR 3.301)
│   Timeline: File as soon as package is ready
│   Priority: ★★★★★ HIGHEST — this addresses the STRUCTURAL problem
│
├─ TRACK 2: JTC COMPLAINT (judicial-accountability-engine)
│   Purpose: Discipline judges for undisclosed conflicts; deter future misconduct
│   Vehicle: MCR 9.200 series (Judicial Tenure Commission)
│   Timeline: File SIMULTANEOUSLY with MSC application
│   Priority: ★★★★ HIGH — supports MSC application; creates independent pressure
│   Note: JTC complaint is confidential; does not directly change case assignment
│
├─ TRACK 3: FEDERAL § 1983 (litigation-federal-civil-rights)
│   Purpose: Monetary damages for constitutional violations under color of law
│   Vehicle: 42 USC § 1983 in US District Court, Western District of Michigan
│   Timeline: FILE AFTER MSC application (or simultaneously)
│   Priority: ★★★ MEDIUM — judges have absolute judicial immunity for judicial acts
│   Limitation: Judicial immunity blocks most § 1983 claims against judges
│   Exception: Administrative/non-judicial acts (e.g., failing to disclose conflicts)
│   Strategy: § 1983 against non-judicial actors (FOC, prosecutors) may be stronger
│
├─ TRACK 4: COA APPEAL (appellate-record-builder)
│   Purpose: Appeal specific orders on the merits
│   Vehicle: Standard appeal to Michigan Court of Appeals (if COA 366810 pending)
│   Timeline: Governed by existing appellate deadlines
│   Priority: ★★★ MEDIUM — addresses individual orders, not structural problem
│   Note: COA cannot reassign judges or transfer circuits
│   Strategy: COA appeal runs parallel; MSC bypass addresses what COA cannot
│
└─ TRACK 5: ATTORNEY GENERAL COMPLAINT
    Purpose: Request AG investigation of systemic judicial conflicts
    Vehicle: Letter/complaint to Michigan Attorney General
    Timeline: File after MSC and JTC filings
    Priority: ★★ LOW — AG has discretion; may decline
    Value: Creates public record; may prompt legislative or executive action
```

## Recommended Filing Sequence

```
PHASE 1 — FOUNDATION (do these first)
  ☐ File MCR 2.003 disqualification motion against McNeill (if not already filed)
     → This establishes that the standard remedy was attempted
     → Even if denied, the filing and denial become MSC appendix evidence
     → Agent: judicial-recusal-engine

  ☐ Obtain firm records (SBM, Secretary of State, property records)
     → Critical evidence for MSC5 Category B
     → Cannot file MSC without proof of firm connection
     → Agent: evidence-warfare-commander

PHASE 2 — SIMULTANEOUS FILING (file these together)
  ☐ MSC Application for Superintending Control (this skill — MSC3 template)
  ☐ JTC Complaint against McNeill (judicial-accountability-engine)
  ☐ JTC Complaint against Hoopes (judicial-accountability-engine)
  ☐ JTC Complaint against Ladas-Hoopes (judicial-accountability-engine)

PHASE 3 — FOLLOW-UP (file after MSC is pending)
  ☐ Emergency Motion for Stay (MSC4) if adverse proceedings continue
  ☐ Federal § 1983 if applicable (litigation-federal-civil-rights)
  ☐ AG complaint (supplementary pressure)

PHASE 4 — CONTINGENCY (keep ready)
  ☐ Habeas Corpus petition (MSC4) — pre-drafted, ready to file if Andrew is jailed
  ☐ Updated affidavit — keep current with any new developments
  ☐ Supplemental brief — if MSC requests additional briefing
```

## Filing Deadline Tracker

```sql
-- Check existing deadlines
SELECT * FROM deadlines
WHERE description LIKE '%MSC%'
   OR description LIKE '%Supreme%'
   OR description LIKE '%appeal%'
   OR description LIKE '%disqualif%'
ORDER BY rowid;

-- Check COA 366810 status
SELECT * FROM docket_events
WHERE description LIKE '%366810%'
   OR description LIKE '%COA%'
ORDER BY rowid;
```

> **⚠️ Always verify current deadlines from the database. Do not assume deadlines from this template.**

## Output Contract

When this skill is invoked, the system MUST produce:

| Output | Format | Quality Gate |
|--------|--------|-------------|
| Complete MSC Application | Formatted pleading text | All facts DB-sourced; all parties verified |
| Brief in Support | Formatted legal argument | All authorities verified; no fabricated citations |
| Affidavit | Sworn statement format | Every assertion grounded in personal knowledge or documents |
| Appendix Index | Numbered exhibit list | Every exhibit linked to source file or acquisition task |
| Proposed Orders | Court order format | Specific relief requested; legally achievable |
| Certificate of Service | Service proof format | All parties listed with correct addresses |
| Document Acquisition List | Table format | Missing docs identified with source and method to obtain |
| Filing Checklist | Checkbox format | Every document accounted for; nothing missing |

## Quality Gates (Pre-Filing)

```
GATE 1: PARTY VERIFICATION
  ☐ All party names match Immutable Reference table
  ☐ L.D.W. used for child (never full name)
  ☐ No fabricated names anywhere in package

GATE 2: FACT VERIFICATION
  ☐ Every factual assertion has a DB source citation
  ☐ All dates verified against master_evidence_timeline or docket_events
  ☐ All case numbers verified
  ☐ No statistics without traceable COUNT(*) queries

GATE 3: LEGAL AUTHORITY VERIFICATION
  ☐ All constitutional citations are accurate
  ☐ All MCR citations reference correct rule numbers
  ☐ All case citations are real cases (not hallucinated)
  ☐ Caperton cite verified: 556 US 868 (2009)

GATE 4: COMPLETENESS
  ☐ All 9 documents in the package are present or accounted for
  ☐ Certificate of service lists all required parties
  ☐ Appendix index matches actual appendix contents
  ☐ No placeholder text remains (or each placeholder has acquisition task)

GATE 5: FORMATTING
  ☐ Caption is correct for MSC filing
  ☐ Page numbering is continuous
  ☐ Exhibits are Bates-stamped (if applicable)
  ☐ Filing fee or IFP application included
```

---

## Appendix: Key Database Queries Reference

> **All queries use litigation_context.db. Always set PRAGMAs first:**
> ```sql
> PRAGMA busy_timeout = 60000;
> PRAGMA journal_mode = WAL;
> PRAGMA cache_size = -32000;
> ```

### Query Bank — MSC Bypass Application

```sql
-- Q1: All judicial violations (McNeill focus)
SELECT id, violation_type, description, date_occurred, mcr_rule, canon, severity
FROM judicial_violations
ORDER BY date_occurred;

-- Q2: Master timeline — judicial actors
SELECT id, event_date, event_type, description, actors, lane, key_quote
FROM master_evidence_timeline
WHERE actors LIKE '%McNeill%'
   OR actors LIKE '%Hoopes%'
   OR actors LIKE '%Ladas%'
ORDER BY event_date;

-- Q3: Judicial bias chronology
SELECT * FROM judicial_bias_chronology
ORDER BY rowid;

-- Q4: All Lane E claims (judicial misconduct)
SELECT claim_id, claim_type, description, status, evidence_count, strength_score
FROM claims
WHERE lane = 'E'
ORDER BY strength_score DESC;

-- Q5: Docket events — adverse rulings
SELECT * FROM docket_events
WHERE description LIKE '%denied%'
   OR description LIKE '%contempt%'
   OR description LIKE '%jail%'
   OR description LIKE '%suspend%'
   OR description LIKE '%custody%'
ORDER BY rowid;

-- Q6: Filing readiness for Lane E
SELECT * FROM filing_readiness
WHERE vehicle_name LIKE '%misconduct%'
   OR vehicle_name LIKE '%disqualif%'
   OR vehicle_name LIKE '%superintending%';

-- Q7: Evidence authentication status
SELECT * FROM evidence_authentication
WHERE description LIKE '%McNeill%'
   OR description LIKE '%Hoopes%'
   OR description LIKE '%firm%';

-- Q8: Authority chains for disqualification/superintending
SELECT * FROM authority_chains
WHERE description LIKE '%disqualif%'
   OR description LIKE '%superintending%'
   OR description LIKE '%impartial%'
   OR description LIKE '%Caperton%';

-- Q9: Michigan Judicial Canons cited
SELECT * FROM michigan_judicial_canons;

-- Q10: Aggregate counts for application (anti-hallucination)
SELECT
  (SELECT COUNT(*) FROM judicial_violations) AS total_violations,
  (SELECT COUNT(*) FROM judicial_violations
   WHERE description LIKE '%McNeill%') AS mcneill_violations,
  (SELECT COUNT(*) FROM master_evidence_timeline
   WHERE actors LIKE '%McNeill%' OR actors LIKE '%Hoopes%'
      OR actors LIKE '%Ladas%') AS nexus_timeline_events,
  (SELECT COUNT(*) FROM claims WHERE lane = 'E') AS lane_e_claims,
  (SELECT COUNT(*) FROM judicial_bias_chronology) AS bias_entries;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0-APEX-OMEGA | 2025-07-14 | Initial creation — 6 modules, full MSC bypass coverage |

---

*MSC-BYPASS-APPLICATION v3.0.0-APEX-OMEGA — When the circuit is captured, go over it.*
