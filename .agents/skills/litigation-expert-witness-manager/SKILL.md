---
name: litigation-expert-witness-manager
description: >-
  Use when identifying, qualifying, and managing expert witnesses,
  performing Daubert/MRE 702 qualification analysis, reviewing expert
  reports, coordinating expert depositions, drafting retention agreements,
  preparing Daubert challenges, or managing expert discovery under
  MCR 2.302(B)(4).
metadata:
  category: evidence
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    expert witness, Daubert, MRE 702, MRE 703, MRE 704, MRE 705,
    MRE 706, expert report, expert deposition, qualification,
    MCR 2.302(B)(4), expert discovery, retention agreement,
    Daubert challenge, expert testimony, scientific evidence,
    expert opinion, expert qualification
---

# litigation-expert-witness-manager

> **Tier:** 2 — Evidence Specialist
> **Category:** evidence
> **Version:** 1.0.0
> **Lane:** ALL (A through F)

## Description

Expert witness identification, qualification, and lifecycle management
specialist for Michigan litigation. Performs Daubert/MRE 702
qualification analysis, reviews expert reports for admissibility,
coordinates expert depositions, drafts retention agreements, prepares
and defends Daubert challenges, and manages expert discovery obligations
under MCR 2.302(B)(4).

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case Nos. | 2024-001507-DC, 2025-002760-CZ, 2023-5907-PP |
| Lanes | ALL |

## Triggers

- User needs to identify potential expert witnesses
- User evaluating whether a witness qualifies as an expert
- User preparing to challenge opposing expert (Daubert motion)
- User reviewing or drafting an expert report
- User managing expert discovery disclosures
- User coordinating expert depositions
- User drafting expert retention agreement

## Michigan Rules — Expert Witnesses

### MRE 702 — Expert Testimony

A witness qualified as an expert by knowledge, skill, experience,
training, or education may testify in the form of an opinion or
otherwise if:

1. The testimony is based on sufficient facts or data
2. The testimony is the product of reliable principles and methods
3. The witness has applied the principles and methods reliably to the
   facts of the case

**Michigan follows the Daubert standard** since *Gilbert v DaimlerChrysler
Corp*, 470 Mich 749 (2004).

### MRE 703 — Bases of Expert Opinion

An expert may base opinions on facts or data perceived by or made known
to the expert at or before the hearing. If of a type reasonably relied
upon by experts in the particular field, the facts need not be
admissible in evidence.

### MRE 704 — Opinion on Ultimate Issue

Expert testimony is not objectionable merely because it embraces an
ultimate issue to be decided by the trier of fact.

### MRE 705 — Disclosure of Underlying Facts

The expert may testify in terms of opinion without first testifying to
the underlying facts, but may be required to disclose them on
cross-examination.

### MRE 706 — Court-Appointed Experts

The court may appoint its own expert witnesses. Compensation is paid by
the parties as the court directs.

### MCR 2.302(B)(4) — Expert Discovery

**(a) Discovery of retained experts:**
- Party may require opponent to identify each expert expected to testify
- Must provide: subject matter, substance of facts and opinions,
  summary of grounds for each opinion

**(b) Discovery of non-retained experts:**
- Party may discover facts known and opinions held by non-retained experts
  acquired in anticipation of litigation only on showing exceptional
  circumstances

## Daubert Analysis Framework

### The Five Daubert Factors (Gilbert v DaimlerChrysler)

| Factor | Question | Weight |
|--------|----------|--------|
| 1. Testability | Can the theory or technique be tested? | High |
| 2. Peer Review | Has it been subjected to peer review and publication? | Medium |
| 3. Error Rate | What is the known or potential rate of error? | Medium |
| 4. Standards | Are there standards controlling the technique's operation? | Medium |
| 5. General Acceptance | Is the methodology generally accepted? | High |

### Qualification Checklist

- [ ] Relevant educational credentials (degree, certifications)
- [ ] Years of experience in the specific field
- [ ] Prior qualification as expert in Michigan courts
- [ ] Published work in the relevant field
- [ ] Methodology reliability (Daubert factors)
- [ ] Methodology applied correctly to case facts
- [ ] No disqualifying conflicts of interest
- [ ] Reasonable and customary fees

## Patterns

### Pattern 1: Expert Identification and Vetting

**Context:** Need an expert in a specific field for trial.

**Steps:**
1. Define the specific issue requiring expert testimony
2. Identify the field of expertise needed
3. Search for qualified experts (professional associations, publications)
4. Vet credentials against MRE 702 requirements
5. Assess potential Daubert challenges
6. Conduct preliminary interview
7. Draft retention agreement

**Michigan basis:** MRE 702, MCR 2.302(B)(4)

```python
from legal_ai.expert_witness_manager import ExpertWitnessManager

ewm = ExpertWitnessManager()
candidates = ewm.identify_experts(
    field="child psychology",
    issue="best interest of child",
    jurisdiction="Michigan",
)
assessment = ewm.assess_qualification(candidates[0])
```

### Pattern 2: Daubert Challenge Preparation

**Context:** Opposing party's expert has questionable qualifications or methodology.

**Steps:**
1. Obtain expert's report and CV
2. Analyze against all five Daubert factors
3. Research expert's prior testimony and publications
4. Identify specific methodology flaws
5. Draft Daubert motion with supporting brief
6. Request evidentiary hearing per *Gilbert v DaimlerChrysler*
7. Prepare cross-examination questions targeting methodology

**Michigan basis:** MRE 702, *Gilbert v DaimlerChrysler Corp*, 470 Mich 749 (2004)

### Pattern 3: Expert Report Review

**Context:** Received opposing party's expert report; need to evaluate.

**Steps:**
1. Verify expert's qualifications match the opinion rendered
2. Check that opinions are based on sufficient facts (MRE 702(1))
3. Verify methodology is reliable (MRE 702(2))
4. Confirm methodology was correctly applied (MRE 702(3))
5. Identify unsupported conclusions or logical gaps
6. Flag opinions that go beyond the expert's area of expertise
7. Prepare rebuttal points for each opinion

**Michigan basis:** MRE 702, MRE 703

### Pattern 4: Expert Discovery Management

**Context:** Managing expert disclosure obligations and deadlines.

**Steps:**
1. Track expert disclosure deadlines per scheduling order
2. Prepare expert disclosure: identity, subject matter, opinions, bases
3. Supplement disclosures if expert opinions change
4. Serve discovery requests on opposing expert
5. Schedule and prepare for expert deposition

**Michigan basis:** MCR 2.302(B)(4), MCR 2.301

## Anti-Patterns

### Anti-Pattern 1: Late Expert Disclosure

❌ Disclosing expert witnesses after the court-ordered deadline.
**Why it fails:** Court may exclude the expert entirely. MCR 2.302(B)(4)
requires timely disclosure. Undisclosed experts = excluded testimony.
**Fix:** Calendar the disclosure deadline immediately. Prepare disclosures
well in advance. Supplement promptly if opinions change.

### Anti-Pattern 2: Hiring Without Daubert Pre-Screening

❌ Retaining an expert without evaluating Daubert factors first.
**Why it fails:** If the expert's methodology is unreliable, the
testimony will be excluded at trial and you've wasted fees.
**Fix:** Run a full Daubert analysis before retention. Only retain
experts whose methodology will survive a challenge.

### Anti-Pattern 3: Over-Reliance on Expert Credentials

❌ Assuming impressive credentials guarantee admissibility.
**Why it fails:** Daubert focuses on methodology, not credentials.
A Nobel laureate using unreliable methods will be excluded.
**Fix:** Analyze the expert's specific methodology for this case,
not just their CV.

## Expert Witness Types for Family Law

| Type | Use Case | Common in Lane |
|------|----------|---------------|
| Child Psychologist | Best interest evaluation | A (Custody) |
| Forensic Accountant | Hidden assets, income | A (Custody) |
| Real Estate Appraiser | Property valuation | B (Housing) |
| Domestic Violence Expert | DV dynamics, safety | D (PPO) |
| Mental Health Professional | Parental fitness | A (Custody) |
| Guardian ad Litem | Child's best interest | A (Custody) |
| Vocational Evaluator | Earning capacity | A (Custody) |
| Medical Expert | Physical/mental health | A, D |

## Integration Points

### Upstream Skills
- `litigation-case-strategy-architect` — Strategic need for expert testimony
- `litigation-evidence-harvester` — Evidence base for expert opinions
- `litigation-discovery-warfare` — Expert discovery requests/responses

### Downstream Skills
- `litigation-deposition-strategist` — Expert deposition preparation
- `litigation-brief-writer` — Daubert brief drafting
- `litigation-witness-preparation` — Expert trial testimony preparation
- `litigation-appellate-strategist` — Preservation of Daubert rulings


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
| D | 6,462 | 2023-5907-PP | 14th Circuit |
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
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,D,F | Verified |
| Emergency Custody | 55/100 | A,B,D,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,D,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D,F | Verified |
| Contempt | 70/100 | A,B,D,F | Verified |
| Appeal Brief | 70/100 | A,B,D,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,D,F | Verified |
| Default Judgment | 60/100 | A,B,D,F | Verified |
| TRO Application | 60/100 | A,B,D,F | Verified |

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

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

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
