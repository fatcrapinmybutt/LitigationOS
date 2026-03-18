---
name: litigation-default-judgment-engine
description: >-
  Use when pursuing or defending against default judgment under MCR 2.603,
  calculating entry of default timelines, preparing default judgment
  applications, filing motions to set aside default under MCR 2.603(D),
  analyzing good cause for setting aside, or assessing default judgment
  risks in multi-lane litigation.
metadata:
  category: procedure
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    default judgment, MCR 2.603, entry of default, set aside default,
    good cause, default, failure to plead, failure to answer,
    MCL 600.2531, default application, clerk's default,
    motion to set aside, meritorious defense, excusable neglect,
    judgment by default
---

# litigation-default-judgment-engine

> **Tier:** 2 — Procedure Specialist
> **Category:** procedure
> **Version:** 1.0.0
> **Lane:** ALL (A through F)

## Description

Default judgment pursuit and defense specialist for Michigan litigation.
Handles entry of default per MCR 2.603(A), default judgment applications
per MCR 2.603(B), motions to set aside default per MCR 2.603(D), good
cause analysis, and strategic assessment of when default judgment is
available and advisable across all six case lanes.

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

- Opposing party fails to answer complaint within 21 days
- User needs to request entry of default from clerk
- User applying for default judgment
- User needs to set aside a default entered against Plaintiff
- User analyzing good cause factors for setting aside default
- User assessing default judgment risk in any lane

## Michigan Rules — Default Judgment

### MCR 2.603 — Default and Default Judgment

#### (A) Entry of Default

**(1)** When a party against whom a judgment for affirmative relief is
sought has failed to plead or otherwise defend as provided by these
rules, and that fact is made to appear by affidavit or otherwise, the
clerk must enter the default of that party.

**(2)** Notice of request for entry of default must be sent to the
party in default at the party's last known address at least 7 days
before the default is entered.

**Timeline:**
- Complaint served → 21 days to answer (MCR 2.108)
- Day 22: eligible to request entry of default
- 7-day notice to defaulting party required
- Day 29+: clerk enters default

#### (B) Default Judgment

**(1) By Clerk:** When the claim is for a sum certain (specific dollar
amount) and the defendant has not appeared, the clerk may enter
judgment.

**(2) By Court:** In all other cases, the party must apply to the court
for default judgment. The court may:
- Conduct hearings or order references to determine damages
- Establish the truth of any allegation by evidence
- Investigate other matters to enter judgment

**(3) Amount:** Default judgment cannot exceed the amount demanded in
the complaint (or in a notice served on the defendant).

#### (C) Setting Aside Default (Before Judgment)

The court may set aside an entry of default for **good cause** and on
conditions the court considers proper.

#### (D) Setting Aside Default Judgment (After Judgment)

**(1)** A motion to set aside default judgment may be granted if:
- Filed within a **reasonable time** (and not more than 1 year)
- The moving party shows **good cause**
- An affidavit of facts showing a **meritorious defense**

**(2) Good cause factors** (from *Shawl v Spence*, 236 Mich App 120 (1999)):
1. Whether the default was the result of substantial defect or
   irregularity in the proceedings
2. Whether a meritorious defense has been shown
3. Whether the default was the result of excusable neglect
4. The prejudice to the non-defaulting party

### MCL 600.2531 — Judgment by Default

Provides statutory authority for default judgments in Michigan circuit
courts. Works in conjunction with MCR 2.603.

## Default Judgment Workflow

### Phase 1: Eligibility Check

```
Is the claim for affirmative relief?        → YES → Continue
Has defendant been properly served?          → YES → Continue
Has the answer deadline passed (21 days)?    → YES → Continue
Has defendant filed any responsive pleading? → NO  → Eligible
```

### Phase 2: Entry of Default (MCR 2.603(A))

| Step | Action | Timeline |
|------|--------|----------|
| 1 | Verify service was proper (MCR 2.105) | Before filing |
| 2 | Prepare affidavit of non-answer | Day 22+ |
| 3 | Send 7-day notice to defaulting party | Day 22+ |
| 4 | File request for entry of default with clerk | Day 29+ |
| 5 | Clerk enters default | Same day or next |

### Phase 3: Default Judgment (MCR 2.603(B))

| Step | Action | Timeline |
|------|--------|----------|
| 1 | If sum certain: request clerk's judgment | After default |
| 2 | If not sum certain: file motion for judgment | After default |
| 3 | Serve notice of hearing on defaulting party | Per MCR 2.119 |
| 4 | Prepare evidence of damages | Before hearing |
| 5 | Attend hearing; present evidence | Hearing date |
| 6 | Court enters judgment | After hearing |

## Patterns

### Pattern 1: Pursuing Default Judgment

**Context:** Defendant failed to answer the complaint.

**Steps:**
1. Confirm proper service (proof of service on file)
2. Calculate answer deadline (21 days from service)
3. Verify no responsive pleading was filed
4. Prepare affidavit of non-answer
5. Send 7-day notice to defendant's last known address
6. File request for entry of default with clerk
7. After default entered, apply for default judgment
8. For non-sum-certain claims, prepare evidence for damages hearing

**Michigan basis:** MCR 2.603(A), MCR 2.603(B)

```python
from legal_ai.default_judgment_engine import DefaultJudgmentEngine

dje = DefaultJudgmentEngine()
eligibility = dje.check_eligibility(
    service_date="2025-01-15",
    answer_deadline="2025-02-05",
    responsive_pleading_filed=False,
)
if eligibility["eligible"]:
    timeline = dje.generate_default_timeline(
        service_date="2025-01-15",
        case_number="2025-002760-CZ",
    )
```

### Pattern 2: Setting Aside Default (Defense)

**Context:** Default was entered against Plaintiff (e.g., on a counterclaim).

**Steps:**
1. Determine when default was entered
2. File motion to set aside within reasonable time (max 1 year)
3. Address all four good cause factors
4. Prepare affidavit showing meritorious defense
5. Explain the excusable neglect
6. Show no prejudice to opposing party from setting aside
7. Propose conditions (e.g., expedited answer, costs)

**Michigan basis:** MCR 2.603(D), *Shawl v Spence*, 236 Mich App 120 (1999)

### Pattern 3: Default Judgment Risk Assessment

**Context:** Evaluating whether opposing party may seek default.

**Steps:**
1. Review all pending complaints and counterclaims
2. Verify all answer deadlines are calendared
3. Confirm all responsive pleadings are filed and served
4. Check for any missed deadlines that could expose default risk
5. If risk identified, immediately file responsive pleading
6. If default already entered, move to set aside immediately

### Pattern 4: Strategic Default in Multi-Lane Litigation

**Context:** Defendant fails to respond in one lane while active in others.

**Steps:**
1. Identify the lane where defendant has defaulted
2. Assess whether default judgment advances overall strategy
3. If yes, pursue default in that lane while maintaining other lanes
4. Use default in one lane as leverage in others
5. Consider whether default judgment is enforceable and collectible

**Michigan basis:** MCR 2.603, strategic analysis

## Anti-Patterns

### Anti-Pattern 1: Seeking Default Without Proper Service

❌ Requesting entry of default when service was defective.
**Why it fails:** Default judgment on improper service is void and will be
set aside. MCR 2.603(A) requires proper service as a prerequisite.
Wastes time and credibility with the court.
**Fix:** Always verify proper service before requesting default.
Review the return of service for compliance with MCR 2.105.

### Anti-Pattern 2: Ignoring the 7-Day Notice Requirement

❌ Filing for entry of default without sending 7-day notice.
**Why it fails:** MCR 2.603(A)(2) requires 7-day notice to the
defaulting party at their last known address. Failure to provide
notice is grounds to set aside the default.
**Fix:** Always send 7-day notice by mail and keep proof. Calendar
the 7-day waiting period before filing.

### Anti-Pattern 3: Claiming Damages Not in the Complaint

❌ Seeking default judgment for an amount exceeding the complaint demand.
**Why it fails:** MCR 2.603(B)(3) — default judgment cannot exceed the
amount demanded in the complaint. If the complaint demands $10,000, the
default judgment is capped at $10,000.
**Fix:** Ensure the complaint contains a specific demand for the full
amount sought. If discovery reveals higher damages, amend the complaint
before seeking default.

## Good Cause Analysis Framework

When filing or opposing a motion to set aside default:

| Factor | Favors Setting Aside | Favors Maintaining Default |
|--------|---------------------|--------------------------|
| Procedural regularity | Service defective | Service was proper |
| Meritorious defense | Strong factual defense | No viable defense |
| Excusable neglect | Legitimate reason for delay | Willful disregard |
| Prejudice | No prejudice to plaintiff | Plaintiff prejudiced by delay |

### Burden of Proof
- **Before judgment:** "Good cause" — lower bar (MCR 2.603(C))
- **After judgment:** "Good cause" + meritorious defense affidavit — higher bar (MCR 2.603(D))

## Integration Points

### Upstream Skills
- `litigation-service-engine` — Proof of service verification
- `litigation-filing-architect` — Complaint/answer filing tracking
- `litigation-case-strategy-architect` — Strategic default assessment

### Downstream Skills
- `litigation-damages-calculator` — Damages for default hearing
- `litigation-brief-writer` — Brief supporting/opposing default
- `litigation-court-order-tracker` — Track default judgment entry
- `litigation-appellate-strategist` — Appeal of default ruling


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
**MCR:** MCR 2.603, MCR 2.603(A), MCR 2.603(D), MCR 2.108
**MCL:** MCL 600.8316, MCL 600.1915
**Binding Cases:**
- *Alken-Ziegler v Waterbury Headers Corp, 461 Mich 219*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D,F | Verified |
| Emergency Custody | 55/100 | A,D,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,F | Verified |
| Contempt | 70/100 | A,D,F | Verified |
| Appeal Brief | 70/100 | A,D,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,F | Verified |

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
