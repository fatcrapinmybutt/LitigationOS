---
name: litigation-federal-civil-rights
description: >-
  Use when drafting, analyzing, or strategizing a 42 USC § 1983 federal civil rights
  complaint, evaluating judicial or qualified immunity defenses, navigating
  Rooker-Feldman abstention barriers, or structuring Monell municipal liability claims.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: 1983, civil rights, federal, immunity, Rooker-Feldman, qualified immunity, Monell
---
# litigation-federal-civil-rights

> **Tier:** 2 — Discipline Specialist
> **Category:** discipline
> **Version:** 1.0.0
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
