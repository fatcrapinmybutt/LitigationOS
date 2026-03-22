---
name: litigation-federal-civil-rights
description: >-
  Use when drafting, analyzing, or strategizing a 42 USC § 1983 federal civil rights
  complaint, evaluating judicial or qualified immunity defenses, navigating
  Rooker-Feldman abstention barriers, or structuring Monell municipal liability claims.
metadata:
  category: discipline
  author: andrew-pigors
  version: "3.0.0-APEX-OMEGA"
  tier: APEX-OMEGA
  triggers: 1983, civil rights, federal, immunity, Rooker-Feldman, qualified immunity, Monell, FRCP, TRO, IFP, WDMI, constitutional violation, defendant matrix
---
# litigation-federal-civil-rights

> **Tier:** APEX-OMEGA — Supreme Discipline Specialist
> **Category:** discipline
> **Version:** 3.0.0-APEX-OMEGA
> **Lane:** C (Convergence/County) + Federal Overlay

## Description

Use when the user needs to draft, analyze, or strategize a 42 USC § 1983 federal civil rights complaint, evaluate judicial or qualified immunity defenses, navigate Rooker-Feldman abstention barriers, structure Monell municipal liability claims, or prepare § 1985/§ 1986 conspiracy allegations—particularly in the context of Pigors v Watson (14th Judicial Circuit, Muskegon County, MI) where state-court judicial misconduct must be challenged in W.D. Michigan federal court.

## Triggers

- User asks about filing a § 1983 action against a state judge, court officer, or municipality
- User needs to pierce judicial immunity or analyze qualified immunity for non-judicial actors
- User asks how to avoid Rooker-Feldman dismissal when challenging state-court proceedings
- User references Monell liability against Muskegon County or 14th Judicial Circuit
- User needs to structure a § 1985(3) conspiracy claim among multiple state actors
- User asks about 6th Circuit standards for civil rights pleading or summary judgment

## Context: Pigors v Watson

- **Lane A actors with federal exposure:** Judge McNeill (judicial immunity analysis), Gerald Rusco (GAL—qualified immunity), Amy Watson (private actor—state action doctrine)
- **Lane B actors with federal exposure:** Judge Hoopes (if due process violated in housing), Muskegon County (Monell—policies/customs)
- **Lane C convergence:** Pattern of constitutional violations across lanes establishes § 1985 conspiracy and Monell "custom" evidence
- **Federal venue:** W.D. Michigan, Southern Division (Grand Rapids)
- **Key cases:** 2024-001507-DC, 2023-5907-PP, 2025-002760-CZ

## Decision Tree: Federal Civil Rights Claim Selection

```
START: Constitutional violation identified
│
├─ WHO violated rights?
│   ├─ State judge → JUDICIAL IMMUNITY ANALYSIS (go to § A)
│   ├─ Court-appointed officer (GAL, referee) → QUALIFIED IMMUNITY (go to § B)
│   ├─ Private party acting WITH state → STATE ACTION DOCTRINE (go to § C)
│   └─ Municipality/county → MONELL LIABILITY (go to § D)
│
├─ WHAT was violated?
│   ├─ Due process (14th Amendment)
│   │   ├─ Procedural → notice + opportunity to be heard
│   │   └─ Substantive → parental rights (fundamental right, strict scrutiny)
│   ├─ Equal protection (14th Amendment)
│   │   ├─ Gender discrimination in custody → intermediate scrutiny
│   │   └─ Class-of-one → no rational basis
│   ├─ First Amendment → retaliation for filing motions/complaints
│   ├─ Fourth Amendment → unreasonable seizure of children
│   └─ Conspiracy → § 1985(3) + § 1986 failure to prevent
│
└─ ROOKER-FELDMAN CHECK (go to § E)
    ├─ Challenging state judgment itself → BARRED
    └─ Challenging conduct/process independent of judgment → PERMITTED
```

## § A — Judicial Immunity Piercing

Judicial immunity is absolute BUT has two recognized exceptions:

1. **Non-judicial acts:** Actions not taken in judicial capacity
   - Administrative acts (scheduling manipulation, ex parte communications)
   - Enforcement acts (directing marshal without order)
   - Test: Mireles v. Waco (1991)—"whether the act is a function normally performed by a judge"

2. **Absence of jurisdiction:** Judge acted in clear absence of all jurisdiction
   - Not merely erroneous jurisdiction—complete absence
   - Stump v. Sparkman (1978)—broad reading of jurisdiction
   - BUT: Acting on a case type the court has no authority over = no jurisdiction

**Application to Judge McNeill:**
- Ex parte communications with GAL → non-judicial act
- Custody decisions without proper hearing → still judicial (but procedural due process claim survives for injunctive relief under Pulliam v. Allen)
- PPO modifications without statutory basis → arguable absence of jurisdiction

**Pulliam v. Allen pathway:** Prospective injunctive relief against judges is NOT barred by judicial immunity. 42 USC § 1983 explicitly authorizes declaratory and injunctive relief against judicial officers.

## § B — Qualified Immunity (Two-Step Sequoia)

Saucier v. Katz (2001), refined by Pearson v. Callahan (2009):

1. **Step 1:** Did the official violate a constitutional right?
2. **Step 2:** Was the right "clearly established" at the time?

Courts may address either step first (Pearson flexibility).

**6th Circuit "clearly established" standard:**
- Need not find case with identical facts
- Must show "existing precedent placed the constitutional question beyond debate"
- Ashcroft v. al-Kidd (2011)
- Specific to 6th Circuit: look at Supreme Court, 6th Circuit, and consensus of other circuits

**Application to Gerald Rusco (GAL):**
- GALs have qualified immunity, not absolute (Kurzawa v. Mueller, 6th Cir.)
- Violations: Biased investigation, failure to interview father, predetermined recommendation
- Clearly established: Parent's right to custody is fundamental (Troxel v. Granville, 2000)

## § C — State Action Doctrine for Private Parties

Private defendants (Amy Watson, Shady Oaks) can be § 1983 defendants if:

1. **Joint action test:** Private party is a "willful participant in joint activity with the State"
   - Dennis v. Sparks (1980)—private parties who corrupt judicial process
   - Application: Amy Watson + GAL Rusco coordinating testimony/evidence

2. **Nexus test:** State "so far insinuated itself" into private action
   - Application: FOC/court enabling custody interference

3. **Public function test:** Private party performs traditional state function
   - Limited applicability here

## § D — Monell Municipal Liability

Monell v. Dept. of Social Services (1978)—no respondeat superior. Must show:

1. **Official policy:** Written rule or formal decision
2. **Custom:** Persistent, widespread practice so common it has force of law
3. **Failure to train:** Deliberate indifference to known constitutional violations
4. **Ratification:** Final policymaker approves subordinate's unconstitutional act

**Application to Muskegon County / 14th Circuit:**
- Custom: Pattern of denying pro se litigants due process (document across Lane A, B, C)
- Failure to train: No training on pro se accommodation requirements
- Ratification: Chief Judge aware of complaints, no corrective action

**Policymaker identification (6th Circuit):**
- Chief Judge of 14th Circuit for court administration
- County Board of Commissioners for county operations
- Pembaur v. City of Cincinnati (1986)

## § E — Rooker-Feldman Navigation

Rooker-Feldman bars federal claims that are:
1. Brought by state-court losers
2. Complaining of injuries caused by state-court judgments
3. Rendered before federal proceedings commenced
4. Inviting federal review and rejection of those judgments

**AVOIDANCE STRATEGIES:**

| Strategy | Application | Authority |
|----------|-------------|-----------|
| Challenge conduct, not judgment | "McNeill violated due process BY denying hearing" not "custody order was wrong" | Exxon Mobil v. Saudi Basic (2005) |
| Independent federal claim | Constitutional violation exists regardless of state outcome | Skinner v. Switzer (2011) |
| Ongoing state proceedings | File federal action WHILE state case is pending (no final judgment yet) | Timing matters—file before final order |
| Prospective relief only | Seek injunction against future unconstitutional conduct | Does not "review" past judgment |
| Conspiracy claim | § 1985 conspiracy is independent federal wrong | Not reviewing state judgment |

## § 1985(3) Conspiracy Elements

1. Two or more persons conspired
2. Purpose: depriving person of equal protection or equal privileges/immunities
3. Act in furtherance of conspiracy
4. Injury or deprivation of rights

**Cross-lane conspiracy theory (Pigors):**
- Lane A: McNeill + Rusco + Amy Watson → deprive father of custody rights
- Lane B: Hoopes + Shady Oaks → deprive tenant of housing rights
- Lane C: County pattern → systemic deprivation across multiple cases
- Class-based animus: Pro se litigant / father in custody / low-income tenant

## § 1986 — Failure to Prevent

Every person who has knowledge of § 1985 wrongs and has power to prevent them but neglects to do so is liable. Application: County officials aware of pattern who fail to act.

## Pleading Standards (6th Circuit)

- Ashcroft v. Iqbal (2009): Plausibility standard
- Must plead specific facts, not conclusory allegations
- Immunity defenses should be anticipated and rebutted in complaint
- 6th Circuit requires particularity for conspiracy claims
- File in W.D. Michigan; venue proper under 28 USC § 1391(b)

## Filing Checklist — W.D. Michigan

1. [ ] Civil cover sheet (JS-44)
2. [ ] Complaint with numbered paragraphs
3. [ ] IFP application (28 USC § 1915) if applicable
4. [ ] Summons for each defendant
5. [ ] Service plan (state officials: certified mail + Secretary of State)
6. [ ] Preliminary injunction motion if emergency relief needed
7. [ ] Rooker-Feldman preemptive analysis in complaint

## Output Format

When generating federal civil rights analysis:
1. Identify each defendant and their immunity status
2. Map each constitutional violation to specific amendment/clause
3. Run Rooker-Feldman check on each claim
4. Draft elements with factual support for each surviving claim
5. Recommend filing sequence and protective strategies

## Related Skills

- [litigation-harm-quantifier](skill://litigation-harm-quantifier) — Quantifies damages and harm amounts
- [litigation-sanctions-engine](skill://litigation-sanctions-engine) — Pursues sanctions and contempt proceedings


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

### Governing Authority (Verified)
**USC:** 42 USC § 1983, 42 USC § 1985, 42 USC § 1988, 28 USC § 1343, 28 USC § 1367
**Binding Cases:**
- *Monroe v Pape, 365 US 167*
- *Monell v NYC, 436 US 658*
- *Harlow v Fitzgerald, 457 US 800*
- *Ashcroft v Iqbal, 556 US 662*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

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
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-harm-quantifier` | Integration | Complementary analysis |
| `litigation-damages-calculator` | Integration | Complementary analysis |
| `litigation-jury-instruction-engine` | Integration | Bidirectional data exchange |
| `litigation-summary-judgment-engine` | Integration | Bidirectional data exchange |

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
| Custody Modification | 65/100 | A,B,C,D,E | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E | Verified |
| Contempt | 70/100 | A,B,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E | Verified |
| Default Judgment | 60/100 | A,B,C,D,E | Verified |
| TRO Application | 60/100 | A,B,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E | Verified |

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

## 🔥 APEX-OMEGA v3.0 — Advanced Federal Modules (F1–F6)

*Added: v3.0.0-APEX-OMEGA | These modules extend the base skill with automated decision engines, template factories, and constitutional pattern detection.*

---

### Module F1: Qualified Immunity Decision Engine

> Automated 2-step Saucier/Pearson analysis with 6th Circuit case matching and Mireles exception detection.

#### F1.1 — Automated Saucier/Pearson Analysis

For each defendant, the engine runs two sequential steps:

**Step 1 — Constitutional Violation Detection:**
```
INPUT:  defendant_name, alleged_conduct, constitutional_right
PROCESS:
  1. Query litigation_context.db → judicial_violations WHERE defendant LIKE '%{name}%'
  2. Query litigation_context.db → evidence_quotes WHERE legal_significance LIKE '%{right}%'
  3. Map conduct to constitutional provision:
     - No notice before deprivation → 14th Amend. procedural due process
     - Interference with parent-child bond → 14th Amend. substantive due process (Troxel)
     - Punishment for filing motions/complaints → 1st Amend. retaliation
     - Unequal treatment of pro se vs. represented → 14th Amend. equal protection
     - Removal of child without court order → 4th Amend. seizure
  4. Score violation strength: STRONG (direct evidence) / MODERATE (pattern) / WEAK (inference)
OUTPUT: violation_finding {right, evidence_count, strength, key_quotes[]}
```

**Step 2 — "Clearly Established" Test (6th Circuit Particularized):**
```
INPUT:  violation_finding from Step 1
PROCESS:
  1. Search authority_chains for binding precedent matching the specific right + context
  2. Apply 6th Circuit hierarchy:
     a. U.S. Supreme Court decisions (strongest)
     b. 6th Circuit published opinions (binding)
     c. Consensus of sister circuits (persuasive if 6th Cir. silent)
     d. Michigan Supreme Court federal-right interpretations (limited)
  3. Particularized fact matching — find cases with analogous facts:
     - Family court due process: Doe v. Claiborne County (6th Cir.)
     - GAL bias: Kurzawa v. Mueller (6th Cir.)
     - Parental rights: Troxel v. Granville (SCOTUS)
     - Retaliation: Thaddeus-X v. Blatter (6th Cir.)
  4. "Obviousness" fallback: Even without case on point, was the violation
     so egregious that any reasonable official would know it was wrong?
     Hope v. Pelzer, 536 U.S. 730 (2002)
OUTPUT: clearly_established_finding {precedent[], strength, particularization_score}
```

**Combined Result:**
```
IMMUNITY STATUS:
  □ IMMUNITY DEFEATED — both steps satisfied (proceed with damages claim)
  □ IMMUNITY UNCERTAIN — Step 1 strong but Step 2 weak (proceed but prepare for MTD)
  □ IMMUNITY LIKELY — one or both steps unsatisfied (seek injunctive relief instead)
```

#### F1.2 — Mireles Exception Analysis (Judicial Acts vs. Non-Judicial Acts)

Judicial immunity is absolute for judicial acts. The Mireles test determines what qualifies:

**Function test:** "Whether the act is a function normally performed by a judge"
**Expectation test:** "Whether the parties dealt with the judge in the judge's judicial capacity"

| Conduct | Classification | Immunity Status | Authority |
|---------|---------------|-----------------|-----------|
| Ruling on motion after hearing | Judicial act | IMMUNE (even if wrong) | Stump v. Sparkman |
| Entering order with findings | Judicial act | IMMUNE | Stump |
| Ex parte communication with GAL | **NON-JUDICIAL** | **NOT IMMUNE** | Mireles — not a normal judicial function |
| Ex parte communication with one party | **NON-JUDICIAL** | **NOT IMMUNE** | Mireles — factfinding outside adversarial process |
| Scheduling manipulation to deny hearing | **NON-JUDICIAL** (administrative) | **NOT IMMUNE** | Mireles — administrative, not adjudicative |
| Directing enforcement without order | **NON-JUDICIAL** (enforcement) | **NOT IMMUNE** | Mireles — enforcement is executive, not judicial |
| Retaliating for filing JTC complaint | **NON-JUDICIAL** | **NOT IMMUNE** | Retaliation is never a judicial function |
| Refusing to rule on pending motion | **Arguable** — case management vs. denial of access | Analyze under both theories | Circuit split — argue non-judicial |
| Muting party during hearing | **Judicial act** (courtroom management) | Likely IMMUNE — but due process claim survives for injunctive relief | Pulliam pathway |

**Auto-Detection Rules for Pigors v Watson:**
```sql
-- Detect ex parte communications (= non-judicial acts, immunity pierced)
SELECT * FROM judicial_violations
WHERE violation_type LIKE '%ex parte%'
   OR violation_type LIKE '%communication%'
   OR description LIKE '%without notice%'
ORDER BY violation_date;

-- Detect scheduling manipulation (= administrative acts, immunity pierced)
SELECT * FROM judicial_violations
WHERE violation_type LIKE '%schedul%'
   OR violation_type LIKE '%delay%'
   OR violation_type LIKE '%hearing denied%'
ORDER BY violation_date;

-- Detect retaliation (= non-judicial, immunity pierced)
SELECT * FROM judicial_violations
WHERE violation_type LIKE '%retaliat%'
   OR description LIKE '%after filing%'
   OR description LIKE '%complaint%'
ORDER BY violation_date;
```

#### F1.3 — Template Output: Immunity Analysis Brief Section

```
IMMUNITY ANALYSIS — DEFENDANT [NAME]

I. [Name]'s Actions Were Not Protected by [Judicial/Qualified] Immunity

    A. [For judicial immunity — Mireles exception]

    Judicial immunity does not protect Defendant [Name] because
[his/her] actions were not judicial in nature. Under Mireles v. Waco,
502 U.S. 9, 11-12 (1991), immunity attaches only to acts that are
"functions normally performed by a judge" where "the parties dealt
with the judge in the judge's judicial capacity."

    [Name]'s ex parte communications with [party] on [dates] are not
functions normally performed by a judge. Ex parte factfinding outside
the adversarial process is an administrative or investigative act, not
a judicial one. See [6th Circuit authority].

    Specifically, on [DATE], Defendant [Name] [specific conduct from
litigation_context.db → judicial_violations]. This conduct is not
protected because [analysis].

    [For each non-judicial act, cite specific DB evidence with dates]

    B. [For qualified immunity — Saucier/Pearson]

    Even if Defendant [Name] claims qualified immunity, the defense
fails at both steps of the Saucier/Pearson analysis.

    Step 1 — Constitutional Violation: Defendant [Name] violated
Plaintiff's [specific right] by [specific conduct]. [Cite evidence
from litigation_context.db → evidence_quotes, judicial_violations]

    Step 2 — Clearly Established: The right to [specific right] was
clearly established at the time of Defendant's conduct. [Cite
specific 6th Circuit or SCOTUS precedent]. No reasonable [official]
could have believed that [specific conduct] was lawful.

    C. Alternatively, Injunctive Relief Is Available Regardless

    Even where immunity bars damages, Pulliam v. Allen, 466 U.S. 522
(1984), authorizes prospective injunctive and declaratory relief
against judicial officers acting unconstitutionally.
```

---

### Module F2: Rooker-Feldman Navigator

> Automated Exxon Mobil 4-requirement check with complaint framing engine.

#### F2.1 — Automated Rooker-Feldman Check

For each federal claim, run the 4-requirement test from Exxon Mobil Corp. v. Saudi Basic Industries Corp., 544 U.S. 280 (2005):

```
CLAIM: [description]

REQUIREMENT 1 — State-court loser?
  □ YES — Plaintiff lost on this issue in state court
  □ NO  — No final adverse ruling on this issue → NOT BARRED
  □ PENDING — State case still open → NOT BARRED (Exxon Mobil, 544 U.S. at 291)

REQUIREMENT 2 — Injuries caused BY state-court judgment?
  □ YES — Injury flows from the judgment itself → POTENTIALLY BARRED
  □ NO  — Injury flows from conduct DURING proceedings → NOT BARRED
  Analysis: [distinguish conduct from judgment]

REQUIREMENT 3 — State judgment rendered BEFORE federal filing?
  □ YES — Final judgment preceded federal filing
  □ NO  — Federal filed while state pending → NOT BARRED
  □ N/A — No final judgment on this specific issue

REQUIREMENT 4 — Federal suit invites review/rejection of state judgment?
  □ YES — Federal relief would effectively reverse state court → BARRED
  □ NO  — Federal relief addresses independent wrong → NOT BARRED
  Analysis: [explain how federal relief is independent]

RESULT:
  □ ALL FOUR MET → BARRED — reframe claim or abandon
  □ ANY ONE NOT MET → NOT BARRED — proceed
```

#### F2.2 — Strategy Engine: Frame PROCESS Not JUDGMENT

The critical distinction that saves claims from Rooker-Feldman:

| BARRED Framing (challenges judgment) | PERMITTED Framing (challenges process) |
|--------------------------------------|----------------------------------------|
| "The custody order was wrong" | "Due process was denied in the custody proceeding" |
| "The PPO should not have been issued" | "The PPO was issued via ex parte proceeding without constitutionally adequate notice" |
| "The court erred in applying best-interest factors" | "The court conducted a biased investigation and denied father opportunity to present evidence on best-interest factors" |
| "Visitation should not have been suspended" | "Visitation was suspended without hearing, notice, or findings, in violation of procedural due process" |
| "The contempt finding was wrong" | "Criminal contempt sanctions were imposed without criminal procedure protections" |
| "The GAL's recommendation was incorrect" | "The GAL conducted a predetermined, biased investigation that deprived father of fair process" |

#### F2.3 — Pre-Built "Independent Federal Claim" Language

Include in every count of the federal complaint:

```
    [N]. The constitutional violations alleged in this Count exist
independently of any state court judgment. Even if every state court order
at issue were affirmed on direct appeal, the deprivation of Plaintiff's
[specific right] through [specific unconstitutional process] would remain
an actionable federal wrong. This Count does not seek review, reversal,
or modification of any state court judgment but instead challenges the
unconstitutional conduct of Defendant [Name] that occurred during the
course of state proceedings. See Exxon Mobil Corp. v. Saudi Basic
Industries Corp., 544 U.S. 280 (2005); Skinner v. Switzer, 562 U.S.
521 (2011).
```

#### F2.4 — Andrew-Specific Fact Application

| Federal Claim | Independent Injury (not tied to judgment) | Evidence Source |
|---------------|------------------------------------------|----------------|
| Ex parte orders without notice | Due process violation exists regardless of order content | `judicial_violations` WHERE violation_type LIKE '%ex parte%' |
| Hearings without opportunity to present evidence | Right to be heard violated regardless of outcome | `evidence_quotes` WHERE legal_significance LIKE '%hearing%' |
| GAL bias and predetermined conclusions | Biased investigation is independent wrong | `evidence_quotes` WHERE claim_id relates to GAL |
| Retaliation for filing JTC complaint | 1st Amendment violation independent of any ruling | `judicial_violations` WHERE description LIKE '%retaliat%' |
| FOC conducting biased investigation | Biased state actor conduct is independent § 1983 claim | `evidence_quotes` WHERE legal_significance LIKE '%FOC%' |
| Pattern of denying pro se due process | Monell claim is structural, not tied to any single judgment | Cross-lane pattern from all lanes |

#### F2.5 — Pre-Built MTD Response (Rooker-Feldman)

When defendants raise Rooker-Feldman in a Motion to Dismiss, respond with:

```
III. ROOKER-FELDMAN DOES NOT BAR PLAINTIFF'S CLAIMS

    A. Post-Exxon Mobil, Rooker-Feldman Is Narrow

    After Exxon Mobil Corp. v. Saudi Basic Industries Corp., 544 U.S.
280 (2005), Rooker-Feldman is "confined to cases brought by state-court
losers complaining of injuries caused by state-court judgments rendered
before the district court proceedings commenced and inviting district
court review and rejection of those judgments." Id. at 284. It is a
"narrow doctrine." Id. at 291.

    B. Plaintiff's Claims Are Independent of State Judgments

    [For each challenged count:]

    Count [X]: Plaintiff does not challenge the [specific state court
order]. Rather, Plaintiff challenges [specific unconstitutional conduct]
that occurred [before/during/independent of] the state court proceeding.
The injury — deprivation of [specific right] through [specific process
violation] — exists independently of the state court judgment. See
Skinner v. Switzer, 562 U.S. 521, 532 (2011) (claims that do not
require review of state court judgment are not barred).

    [If state proceedings are still pending:]
    C. No Final State Judgment Exists

    Rooker-Feldman requires a state-court judgment "rendered before the
district court proceedings commenced." Exxon Mobil, 544 U.S. at 284.
The state proceedings in [case number] remain pending. Absent a final
judgment, Rooker-Feldman is inapplicable.

    D. Plaintiff Seeks Prospective Relief

    Even if Rooker-Feldman applied to some claims (it does not),
Plaintiff's claims for prospective injunctive and declaratory relief
survive because they do not require the Court to review past judgments
but instead regulate Defendants' future conduct.
```

---

### Module F3: USDC WDMI Filing Template Engine

> W.D. Michigan Southern Division (Grand Rapids) specific templates and procedures.

#### F3.1 — Complaint Structure (FRCP-Compliant, Numbered Paragraphs)

See **`frcp-templates.md`** (Template 1) for the complete multi-defendant complaint template.

Key WDMI-specific requirements:
- **All paragraphs numbered sequentially** across the entire complaint
- **Each defendant:** separate capacity allegations (individual + official)
- **Each count:** re-alleges prior paragraphs by reference, states specific constitutional provision, identifies specific defendant(s), alleges all elements
- **Rooker-Feldman preemptive paragraph** in introductory section
- **Immunity preemptive analysis** woven into fact section for each defendant
- **Certificate of service** at end per FRCP 5

#### F3.2 — Pro Se IFP Application (28 USC § 1915)

See **`frcp-templates.md`** (Template 3) for the complete IFP application and poverty affidavit.

WDMI-specific notes:
- File simultaneously with complaint
- Court will screen under § 1915(e)(2) — anticipate screening in complaint drafting
- If granted, request U.S. Marshal service under § 1915(d) to avoid service costs
- Filing fee: $405 if IFP denied

#### F3.3 — TRO/PI Emergency Motion (FRCP 65)

See **`frcp-templates.md`** (Template 2) for the complete emergency motion template.

WDMI-specific notes:
- Call Clerk's Office for emergency filing procedures: (616) 456-2381
- After-hours: duty judge available through Clerk's emergency line
- Must satisfy Winter v. NRDC, 555 U.S. 7 (2008) four-factor test
- Security bond under FRCP 65(c) — request waiver for IFP plaintiff

#### F3.4 — Discovery Templates (FRCP 26/33/34/36)

See **`frcp-templates.md`** (Template 6) for complete discovery request templates including:
- FRCP 26(a)(1) initial disclosures
- FRCP 33 interrogatories (max 25 per party)
- FRCP 34 requests for production
- FRCP 36 requests for admission

#### F3.5 — Summary Judgment Motion/Response (FRCP 56)

See **`frcp-templates.md`** (Template 5) for the summary judgment template.

Standards:
- **Celotex Corp. v. Catrett, 477 U.S. 317 (1986):** Movant must show absence of genuine dispute
- **Matsushita Elec. v. Zenith Radio, 475 U.S. 574 (1986):** View facts favorably to non-movant
- **Anderson v. Liberty Lobby, 477 U.S. 242 (1986):** "Genuine" dispute requires sufficient evidence for jury
- **Scott v. Harris, 550 U.S. 372 (2007):** Video evidence may override opposing party's version

#### F3.6 — Certificate of Service (FRCP 5)

Every filing must include:
```
CERTIFICATE OF SERVICE

I certify that on [DATE], I served a copy of the foregoing [DOCUMENT]
by [CM/ECF / first-class mail / certified mail] on:

[List all counsel/parties with addresses]

______________________________
Andrew James Pigors, Pro Se
```

---

### Module F4: 19-Defendant Pleading Matrix

> Per-defendant analysis: elements + immunity + evidence from DB + recommended claims.

#### F4.1 — Defendant Category 1: Judge McNeill (Judicial Immunity Analysis)

| Field | Analysis |
|-------|----------|
| **Full Name** | Hon. Jenny L. McNeill |
| **Role** | Judge, 14th Judicial Circuit Court, Family Division |
| **Immunity Type** | Absolute judicial immunity (with exceptions) |
| **Capacity Sued** | Individual (non-judicial acts for damages) + Official (injunctive/declaratory per Pulliam) |
| **Mireles Exception — Non-Judicial Acts** | Ex parte communications with GAL/parties; scheduling manipulation; retaliatory conduct after JTC filing |
| **Pulliam Pathway** | Injunctive relief requiring constitutional hearing procedures; declaratory judgment that procedures violated due process |
| **DB Evidence** | `judicial_violations` (1,127 records); `evidence_quotes` WHERE legal_significance LIKE '%McNeill%' |
| **Recommended Claims** | Count I: Procedural due process (14th Amend.) — non-judicial acts; Count IV: 1st Amend. retaliation; Count V: § 1985(3) conspiracy; Official capacity: injunctive + declaratory relief |

**SQL Evidence Query:**
```sql
SELECT violation_type, COUNT(*) as count
FROM judicial_violations
GROUP BY violation_type
ORDER BY count DESC;
```

#### F4.2 — Defendant Category 2: Emily A. Watson (Private Party — State Action)

| Field | Analysis |
|-------|----------|
| **Full Name** | Emily A. Watson |
| **Role** | Defendant mother, private party |
| **Immunity Type** | NONE (if state action established) |
| **State Action Theory** | Dennis v. Sparks joint action — willful participant in corrupting judicial process; conspiracy with GAL/court to deprive father of custody rights |
| **Key Evidence** | Coordinated ex parte communications with court/GAL; false allegations pattern; withholding parenting time in concert with court orders |
| **DB Evidence** | `evidence_quotes` WHERE claim_type LIKE '%Watson%'; `contradiction_map` for inconsistent statements |
| **Recommended Claims** | Count I: Procedural due process (via state action); Count II: Substantive due process (interfering with fundamental parental right); Count V: § 1985(3) conspiracy; Full damages + punitive |

#### F4.3 — Defendant Category 3: Ronald Berry (Private Party — Conspiracy)

| Field | Analysis |
|-------|----------|
| **Full Name** | Ronald Berry |
| **Role** | Emily Watson's domestic partner — NON-ATTORNEY, no bar number |
| **Immunity Type** | NONE |
| **State Action Theory** | § 1985(3) conspiracy — participated in scheme to deprive father of parental rights; aided interference with court-ordered parenting time |
| **Key Evidence** | Involvement in custody interference; presence during denied parenting time; communications relevant to conspiracy |
| **DB Evidence** | `evidence_quotes` WHERE description LIKE '%Berry%' OR '%Ronald%' |
| **Recommended Claims** | Count V: § 1985(3) conspiracy; Count VI: § 1986 neglect to prevent (if he had knowledge + power); Compensatory + punitive damages |

#### F4.4 — Defendant Category 4: Albert & Lori Watson (Private Parties)

| Field | Analysis |
|-------|----------|
| **Names** | Albert Watson, Lori Watson |
| **Role** | Emily's parents — involvement in custody interference |
| **Immunity Type** | NONE |
| **State Action Theory** | § 1985(3) conspiracy — active participants; potential false reporting; witness tampering |
| **Key Evidence** | False reports to authorities; interference with parenting time; coordinated conduct |
| **DB Evidence** | `evidence_quotes` WHERE description LIKE '%Albert%' OR '%Lori%' |
| **Recommended Claims** | Count V: § 1985(3) conspiracy; compensatory + punitive damages |

#### F4.5 — Defendant Category 5: FOC Pamela Rusco (Qualified Immunity)

| Field | Analysis |
|-------|----------|
| **Full Name** | Pamela Rusco |
| **Role** | Friend of the Court, Muskegon County |
| **Immunity Type** | Qualified immunity (investigative functions) |
| **Saucier Step 1** | Biased investigation; failure to investigate father's evidence; predetermined conclusions; denial of due process in FOC proceedings |
| **Saucier Step 2** | Right to unbiased investigation clearly established: Mathews v. Eldridge (1976); Cleveland Bd. of Ed. v. Loudermill (1985) |
| **Capacity Sued** | Individual (damages if QI defeated) + Official (injunctive relief) |
| **DB Evidence** | `evidence_quotes` WHERE legal_significance LIKE '%FOC%' OR '%Rusco%' |
| **Recommended Claims** | Count I: Procedural due process; Count III: Equal protection (treating father differently); Count V: § 1985(3) conspiracy |

#### F4.6 — Defendant Category 6: GAL (Qualified Immunity — Not Absolute)

| Field | Analysis |
|-------|----------|
| **Role** | Guardian Ad Litem (court-appointed) |
| **Immunity Type** | Qualified (NOT absolute per 6th Circuit — Kurzawa v. Mueller) |
| **Saucier Step 1** | Biased investigation; failure to interview father; predetermined recommendation; ex parte communications with judge |
| **Saucier Step 2** | Parent's right to custody = fundamental liberty interest (Troxel); right to fair investigation = clearly established (Loudermill) |
| **Key Vulnerability** | GALs have only qualified immunity — if investigation was demonstrably biased, immunity is defeated |
| **DB Evidence** | `evidence_quotes` WHERE claim_type LIKE '%GAL%' |
| **Recommended Claims** | Count I: Procedural due process; Count II: Substantive due process; Count V: § 1985(3) conspiracy; Full damages + punitive |

#### F4.7 — Defendant Category 7: Jennifer Barnes P55406 (Attorney Conduct)

| Field | Analysis |
|-------|----------|
| **Full Name** | Jennifer Barnes (P55406) |
| **Role** | Emily Watson's attorney (WITHDRAWN) — Barnes Law Firm PLLC |
| **Immunity Type** | Generally NONE for private attorneys, but state action must be shown |
| **State Action Theory** | If Barnes colluded with court/GAL in ex parte proceedings → joint action under Dennis v. Sparks; if Barnes knowingly participated in unconstitutional deprivation → color of law |
| **Key Evidence** | Ex parte communications with court; participation in proceedings where father was denied due process; communications with GAL outside adversarial process |
| **DB Evidence** | `evidence_quotes` WHERE description LIKE '%Barnes%' |
| **Recommended Claims** | Count V: § 1985(3) conspiracy (if evidence supports agreement); state-law claims as supplemental |
| **Caution** | Attorney conduct claims require strong evidence of collusion beyond normal zealous advocacy |

#### F4.8 — Defendant Category 8: Muskegon County (Monell Liability)

| Field | Analysis |
|-------|----------|
| **Entity** | County of Muskegon |
| **Immunity Type** | NONE (municipalities have no sovereign immunity under Monell) |
| **Monell Theory 1 — Custom** | Pattern of denying pro se litigants due process in family court; systemic failure to provide constitutional hearing procedures |
| **Monell Theory 2 — Failure to Train** | No training on pro se litigant accommodation; no training on constitutional hearing requirements; deliberate indifference to known pattern |
| **Monell Theory 3 — Ratification** | Chief Judge and county administrators aware of complaints about family court procedures; no corrective action taken |
| **Policymaker** | Chief Judge of 14th Circuit (court administration); County Board of Commissioners (county operations) — per Pembaur v. City of Cincinnati |
| **DB Evidence** | Cross-lane pattern evidence from all lanes; `claims` WHERE vehicle_name = 'Federal §1983' |
| **Recommended Claims** | Count VII: Monell liability for custom + failure to train + ratification; compensatory damages only (no punitive against municipalities per City of Newport) |
| **Caution** | Monell requires specific factual allegations — conclusory "policy" claims will be dismissed |

#### F4.9 — Additional Defendants (As Applicable)

| Potential Defendant | Theory | Strength | Notes |
|--------------------|---------|---------:|-------|
| 14th Judicial Circuit (as entity) | Analyze: arm of state (11th Amend.) vs. local entity (Monell) | Medium | Michigan courts may be state entities — research required |
| Chief Judge of 14th Circuit | Supervisory liability for failure to address pattern | Medium | Must show personal involvement or deliberate indifference |
| SCAO | State-level failure to enforce judicial conduct standards | Low | Likely arm of state — 11th Amendment bar |
| Additional FOC staff | Qualified immunity — specific acts of individual staff | Variable | Must identify specific individuals and specific conduct |
| Process servers / clerks | Qualified immunity — failure to serve, improper service | Low-Medium | Ministerial acts — qualified immunity may be weak |

---

### Module F5: Constitutional Violation Pattern Detector

> Automated scan of master_evidence_timeline and judicial_violations for constitutional violation patterns.

#### F5.1 — 14th Amendment Due Process Violations

**Procedural Due Process (no notice, no hearing, ex parte):**

```sql
-- Detect no-notice deprivations
SELECT COUNT(*) as no_notice_count,
       MIN(violation_date) as earliest,
       MAX(violation_date) as latest
FROM judicial_violations
WHERE violation_type LIKE '%notice%'
   OR description LIKE '%without notice%'
   OR description LIKE '%no notice%'
   OR description LIKE '%ex parte%';

-- Detect denied hearings
SELECT COUNT(*) as denied_hearing_count
FROM judicial_violations
WHERE violation_type LIKE '%hearing%'
   OR description LIKE '%no hearing%'
   OR description LIKE '%denied hearing%'
   OR description LIKE '%without hearing%';

-- Detect ex parte communications
SELECT COUNT(*) as ex_parte_count
FROM judicial_violations
WHERE violation_type LIKE '%ex parte%'
   OR description LIKE '%ex parte%';

-- Aggregate due process violation pattern
SELECT
  (SELECT COUNT(*) FROM judicial_violations
   WHERE description LIKE '%notice%' OR description LIKE '%ex parte%') as notice_violations,
  (SELECT COUNT(*) FROM judicial_violations
   WHERE description LIKE '%hearing%') as hearing_violations,
  (SELECT COUNT(*) FROM judicial_violations
   WHERE description LIKE '%ex parte%') as ex_parte_violations;
```

**Substantive Due Process (parental rights — fundamental liberty interest):**

```sql
-- Detect interference with parental rights
SELECT COUNT(*) as parental_rights_violations
FROM evidence_quotes
WHERE legal_significance LIKE '%parental%'
   OR legal_significance LIKE '%custody%'
   OR legal_significance LIKE '%parenting time%'
   OR legal_significance LIKE '%visitation%';

-- Detect deprivation without adequate justification
SELECT COUNT(*) as unjustified_deprivations
FROM judicial_violations
WHERE violation_type LIKE '%custody%'
   OR violation_type LIKE '%parenting%'
   OR description LIKE '%suspended%'
   OR description LIKE '%terminated%';
```

#### F5.2 — 14th Amendment Equal Protection Violations

```sql
-- Detect unequal treatment of pro se vs. represented
SELECT COUNT(*) as unequal_treatment_count
FROM judicial_violations
WHERE description LIKE '%pro se%'
   OR description LIKE '%self-represented%'
   OR description LIKE '%unequal%'
   OR violation_type LIKE '%equal%';

-- Detect gender-based discrimination in custody
SELECT COUNT(*) as gender_bias_indicators
FROM evidence_quotes
WHERE legal_significance LIKE '%father%'
   OR legal_significance LIKE '%gender%'
   OR legal_significance LIKE '%bias%'
   OR legal_significance LIKE '%discrimination%';
```

#### F5.3 — 1st Amendment Retaliation

Three elements: (1) protected activity → (2) adverse action → (3) causal connection

```sql
-- Detect retaliation pattern: filing complaints → adverse action
SELECT COUNT(*) as retaliation_incidents
FROM judicial_violations
WHERE violation_type LIKE '%retaliat%'
   OR description LIKE '%after filing%'
   OR description LIKE '%in response to%'
   OR description LIKE '%complaint%retaliat%';

-- Detect protected activities (filings, complaints)
SELECT COUNT(*) as protected_activities
FROM evidence_quotes
WHERE legal_significance LIKE '%filed%motion%'
   OR legal_significance LIKE '%JTC%'
   OR legal_significance LIKE '%complaint%'
   OR legal_significance LIKE '%grievance%';
```

#### F5.4 — Right to Parent (Troxel Fundamental Liberty Interest)

```sql
-- Detect parenting time denial pattern
SELECT COUNT(*) as pt_denial_count
FROM evidence_quotes
WHERE legal_significance LIKE '%parenting time%denied%'
   OR legal_significance LIKE '%visitation%denied%'
   OR legal_significance LIKE '%custody%denied%'
   OR legal_significance LIKE '%contact%denied%';

-- Calculate separation duration from evidence
SELECT
  MIN(CASE WHEN legal_significance LIKE '%separation%'
      THEN quote_date END) as first_separation,
  MAX(quote_date) as latest_evidence,
  COUNT(DISTINCT quote_date) as evidence_points
FROM evidence_quotes
WHERE legal_significance LIKE '%separation%'
   OR legal_significance LIKE '%parenting time%';
```

#### F5.5 — Pattern Scoring Output

```
CONSTITUTIONAL VIOLATION PATTERN REPORT
═══════════════════════════════════════

Defendant: [NAME]
Analysis Date: [DATE]
Data Source: litigation_context.db

14TH AMENDMENT — PROCEDURAL DUE PROCESS
  Notice violations:      [COUNT] incidents ([DATE RANGE])
  Hearing denials:        [COUNT] incidents ([DATE RANGE])
  Ex parte communications: [COUNT] incidents ([DATE RANGE])
  PATTERN SCORE: [STRONG/MODERATE/WEAK]

14TH AMENDMENT — SUBSTANTIVE DUE PROCESS
  Parental rights deprivations: [COUNT] incidents
  Unjustified restrictions:     [COUNT] incidents
  Separation duration:          [DAYS] days
  PATTERN SCORE: [STRONG/MODERATE/WEAK]

14TH AMENDMENT — EQUAL PROTECTION
  Unequal treatment incidents:  [COUNT]
  Gender bias indicators:       [COUNT]
  PATTERN SCORE: [STRONG/MODERATE/WEAK]

1ST AMENDMENT — RETALIATION
  Protected activities:         [COUNT]
  Adverse actions post-filing:  [COUNT]
  Temporal proximity matches:   [COUNT]
  PATTERN SCORE: [STRONG/MODERATE/WEAK]

PARENTAL RIGHTS (TROXEL)
  Days of separation:           [COUNT]
  Denied contact incidents:     [COUNT]
  PATTERN SCORE: [STRONG/MODERATE/WEAK]

OVERALL FEDERAL CLAIM STRENGTH: [STRONG/MODERATE/WEAK]
RECOMMENDED FILING PRIORITY:    [IMMEDIATE/STANDARD/HOLD]
```

---

### Module F6: 2025 FRCP Amendments Integration

> Awareness and compliance for current federal procedural rules.

#### F6.1 — Rule 16.1 (MDL Management)

- **New rule** for multidistrict litigation case management
- **Direct applicability to Pigors:** Limited — single-plaintiff case
- **Awareness value:** If Pigors case reveals pattern affecting multiple pro se litigants, potential for MDL-like consolidation or class action
- **Monitor:** Whether WDMI implements local rules implementing Rule 16.1

#### F6.2 — Rule 26(f) Discovery Planning Conference Updates

**Enhanced obligations for FRCP 26(f) conference:**
- Discuss privilege log format early in litigation
- Address ESI preservation obligations
- Plan for proportional discovery (cost-benefit analysis)
- Discuss protective order needs

**Pro se adaptations:**
- Request telephonic conference if travel is burdensome
- Prepare written discovery plan in advance
- State formats you can accept for document production (PDF preferred)
- Document preservation obligations apply equally to pro se parties

#### F6.3 — Updated Discovery Scope and Limits

**FRCP 26(b)(1) proportionality factors (reinforced):**
1. Importance of issues at stake
2. Amount in controversy
3. Parties' relative access to information
4. Parties' resources
5. Importance of discovery in resolving issues
6. Whether burden/expense outweighs likely benefit

**Pro se advantage:** Courts may consider resource asymmetry between pro se plaintiff and institutional defendants. Request discovery accommodation based on:
- Limited financial resources (IFP status)
- Defendants' superior access to their own records
- Importance of constitutional rights at stake

#### F6.4 — E-Filing Requirements for W.D. Michigan

See **`wdmi-local-rules.md`** for complete e-filing procedures.

Key points:
- Pro se parties may file in paper (exemption from mandatory e-filing)
- CM/ECF registration available for pro se parties who prefer electronic filing
- All paper filings: original + one copy to Clerk's Office
- PDF format preferred for any electronic submissions
- Proposed orders: separate document/attachment

#### F6.5 — Privilege Log Automation Requirements

Under updated Rule 26, privilege logs must:
- Identify each withheld document
- State the privilege claimed
- Provide sufficient description to assess the claim without revealing privileged content

**For Pigors (as plaintiff):**
- Limited privilege log obligation (plaintiff has fewer privilege claims)
- Attorney-client privilege: N/A for pro se (but work product may apply)
- Prepare demands for defendants' privilege logs early
- Challenge overbroad privilege claims — government defendants often over-designate

---

## 📎 APEX-OMEGA Supporting Files

| File | Purpose |
|------|---------|
| `frcp-templates.md` | Ready-to-use template structures for all federal filings |
| `wdmi-local-rules.md` | W.D. Michigan specific rules, procedures, courthouse info |
| `references/immunity-analysis.md` | Deep-dive immunity analysis for all defendant categories |
| `references/rooker-feldman.md` | Complete Rooker-Feldman doctrine analysis and avoidance strategies |
| `references/section-1983.md` | Full § 1983 elements, Monell, conspiracy, damages |
| `gotchas.md` | Anti-rationalization tables and critical failure modes |
