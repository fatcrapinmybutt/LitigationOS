# LitigationOS RAG Index Report

**Generated:** 2026-03-04 11:54:31
**ChromaDB Store:** `C:\Users\andre\LitigationOS\00_SYSTEM\chromadb_store`
**Embedding Model:** nomic-embed-text (via Ollama)
**Chunk Size:** 500 tokens / 50 token overlap

---

## Index Summary

| Collection | Vectors | Time |
|---|---|---|
| filing_stacks | 265 | 3873.4s |
| evidence_master | 1,753 | 7408.5s |
| **TOTAL** | **2,018** | **11281.9s** |

---

## Filing Stacks Indexed

| Stack | Files | Chunks | Status |
|---|---|---|---|
| COA_366810_BRIEF | 9 | 49 | OK |
| WATSON_TORT | 9 | 76 | OK |
| SHADY_OAKS_EXPANDED | 9 | 32 | OK |
| EMERGENCY_MOTIONS | 10 | 49 | OK |
| JTC_MCNEILL | 4 | 22 | OK |
| BAR_BARNES | 3 | 4 | OK |
| FEDERAL_1983 | 5 | 11 | OK |
| VEHICLE_DISCOVERY | 2 | 22 | OK |

**Total:** 51 files → 265 chunks

---

## Evidence Master Sections

| Section | Chunks |
|---|---|
| so_claims | 49 |
| so_harms | 300 |
| housing_violations | 100 |
| watson_harms | 300 |
| mcneill_harms | 300 |
| atty_harms | 200 |
| adv_summary | 4 |
| timeline | 500 |

**Total:** 1753 chunks

---

## Test Query Results

### Q1: What are the RICO allegations against Shady Oaks?

**Filing Stacks (top 5):**

| Score | Stack | Source File | Preview |
|---|---|---|---|
| 0.663 | BAR_BARNES | 01_BAR_COMPLAINT.md | # REQUEST FOR INVESTIGATION / GRIEVANCE ## Attorney Grievance Commission / Attor... |
| 0.662 | SHADY_OAKS_EXPANDED | 05_DAMAGES_CALCULATION.md | 2x) \| $410,000 \| $980,000 \| \| **GRAND TOTAL** \| **$1,230,000** \| **$2,940,000** ... |
| 0.654 | SHADY_OAKS_EXPANDED | 06_ADVERSARY_REBUTTAL_FRAMEWORK.md | # ADVERSARY REBUTTAL FRAMEWORK -- Shady Oaks  ---  ## DEFENSE 1: "Res Judicata /... |
| 0.654 | WATSON_TORT | 01_CIVIL_TORT_COMPLAINT_WATSON.md | n of a crime, harm a person in their profession or business, or tend to disgrace... |
| 0.642 | WATSON_TORT | 06_ADVERSARY_REBUTTAL_FRAMEWORK.md | # ADVERSARY REBUTTAL FRAMEWORK -- Watson Civil Tort  ---  ## ANTICIPATED DEFENSE... |

**Evidence Master (top 5):**

| Score | Section | Preview |
|---|---|---|
| 0.673 | so_harms | category: HOUSING_HARM adversary: Shady Oaks date_ref: July 17, 2024 description: HOUSING_HARM: incl... |
| 0.673 | watson_harms | category: PARENTAL_ALIENATION adversary: Emily Watson date_ref: July 17, 2024 description: PARENTAL_... |
| 0.673 | watson_harms | category: FINANCIAL_HARM adversary: Emily Watson date_ref: July 17, 2024 description: FINANCIAL_HARM... |
| 0.673 | watson_harms | category: PROCEDURAL_VIOLATIONS adversary: Emily Watson date_ref: July 17, 2024 description: PROCEDU... |
| 0.673 | watson_harms | category: CHILD_WELFARE adversary: Emily Watson date_ref: July 17, 2024 description: CHILD_WELFARE: ... |

### Q2: What evidence supports judicial bias by McNeill?

**Filing Stacks (top 5):**

| Score | Stack | Source File | Preview |
|---|---|---|---|
| 0.713 | JTC_MCNEILL | 01_JTC_COMPLAINT.md | ng party - Made findings unsupported by evidence in the record  ### VIOLATION 3:... |
| 0.686 | COA_366810_BRIEF | 01_APPELLANTS_BRIEF_ON_APPEAL.md | or (ii) has failed to adhere to the appearance of impropriety standard . . .  Th... |
| 0.681 | COA_366810_BRIEF | 01_APPELLANTS_BRIEF_ON_APPEAL.md | redetermined Outcome  The totality of the trial court's conduct is consistent wi... |
| 0.677 | COA_366810_BRIEF | 09_READINESS_SCORE.md | are powerful evidence of systemic bias.  **Gap to Close:** Complete the ex parte... |
| 0.674 | EMERGENCY_MOTIONS | 04_MOTION_DISQUALIFY_JUDGE.md | ders** entered in this matter    - **100% grant rate** on motions filed by Defen... |

**Evidence Master (top 5):**

| Score | Section | Preview |
|---|---|---|
| 0.726 | timeline | event_date: 2025-06-02 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |
| 0.723 | timeline | event_date: 2025-05-19 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |
| 0.723 | timeline | event_date: 2025-05-20 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |
| 0.712 | timeline | event_date: 2025-06-02 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |
| 0.703 | timeline | event_date: 2025-06-02 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |

### Q3: What damages are claimed in the Watson tort action?

**Filing Stacks (top 5):**

| Score | Stack | Source File | Preview |
|---|---|---|---|
| 0.708 | WATSON_TORT | 01_CIVIL_TORT_COMPLAINT_WATSON.md | ious disregard for Plaintiff's rights    - Punitive damages are necessary to det... |
| 0.687 | WATSON_TORT | 06_ADVERSARY_REBUTTAL_FRAMEWORK.md | - 3-year statute for tort; conduct ongoing through present.  ## ANTICIPATED DEFE... |
| 0.662 | WATSON_TORT | 01_CIVIL_TORT_COMPLAINT_WATSON.md | onomic damages, non-economic damages, and exemplary/punitive damages as permitte... |
| 0.660 | WATSON_TORT | 01_CIVIL_TORT_COMPLAINT_WATSON.md | fered with Plaintiff's economic relations by:    - Actions that directly caused ... |
| 0.652 | WATSON_TORT | 03_LEGAL_THEORIES_AUTHORITY.md | ication to third party; (3) Fault; (4) Actionable irrespective of special damage... |

**Evidence Master (top 5):**

| Score | Section | Preview |
|---|---|---|
| 0.690 | so_claims | cl_id: CL-20260123-0029 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Award compensatory damages... |
| 0.683 | so_claims | cl_id: CL-20260123-0016 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Such conduct violates MCL ... |
| 0.680 | so_claims | cl_id: CL-20260123-0030 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Award treble damages under... |
| 0.672 | so_claims | cl_id: CL-20260123-0027 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Statutory/exemplary: trebl... |
| 0.653 | so_claims | cl_id: CL-20260123-0031 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Award exemplary damages, c... |

### Q4: What is the timeline of custody interference?

**Filing Stacks (top 5):**

| Score | Stack | Source File | Preview |
|---|---|---|---|
| 0.714 | COA_366810_BRIEF | 01_APPELLANTS_BRIEF_ON_APPEAL.md | ation of court-ordered parenting time. (LCR, Father's Motion, filed 05/13/2024.)... |
| 0.702 | EMERGENCY_MOTIONS | 01_EMERGENCY_MOTION_RESTORE_PARENTING_TIME.md | n    - **MCL 722.27a** — Parenting time presumption and enforcement    - **MCL 7... |
| 0.697 | EMERGENCY_MOTIONS | 03_MOTION_CONTEMPT_SHOW_CAUSE.md | to allow any contact between Plaintiff and the minor child.  ### B. Specific Vio... |
| 0.688 | COA_366810_BRIEF | 01_APPELLANTS_BRIEF_ON_APPEAL.md | r's parenting time. (Lower Court Record ["LCR"], Final Judgment, 08/23/2024.)  2... |
| 0.686 | COA_366810_BRIEF | 01_APPELLANTS_BRIEF_ON_APPEAL.md | f this required finding renders the denial of Father's parenting time reversible... |

**Evidence Master (top 5):**

| Score | Section | Preview |
|---|---|---|
| 0.724 | timeline | event_date: 2024-10-25 case_type: CUSTODY event_type: order actor: Emily Watson title: Lincoln durin... |
| 0.724 | timeline | event_date: 2024-10-20 case_type: CUSTODY event_type: order actor: Albert Watson title: rcing custod... |
| 0.702 | timeline | event_date: 2024-10-02 case_type: CUSTODY event_type: violation actor: Andrew Pigors title: [BIAS] P... |
| 0.691 | timeline | event_date: 2024-10-20 case_type: PPO event_type: violation actor: Albert Watson title: with LDW and... |
| 0.681 | timeline | event_date: 2025-06-02 case_type: CUSTODY event_type: incident actor: Andrew Pigors title: [EMILY_FA... |

### Q5: What emergency motions are pending?

**Filing Stacks (top 5):**

| Score | Stack | Source File | Preview |
|---|---|---|---|
| 0.679 | EMERGENCY_MOTIONS | 08_PROPOSED_ORDERS.md | ________________________ HON. _________________________ Chief Judge, 14th Judici... |
| 0.626 | COA_366810_BRIEF | 04_STATEMENT_OF_FACTS_EXPANDED.md | Father's proactive engagement \| \| 04/11/2024 \| Notice to Appear issued; Return o... |
| 0.624 | FEDERAL_1983 | 02_IMMUNITY_ANALYSIS.md | es, not outcome challenges \| \| Younger Abstention \| **HIGH** \| Wait until state ... |
| 0.614 | EMERGENCY_MOTIONS | 09_FILING_INSTRUCTIONS.md | 990 Terrace St, Muskegon, MI 49442 \|  ### C. Proof of Service  File **SCAO Form ... |
| 0.613 | COA_366810_BRIEF | 09_READINESS_SCORE.md | ite the actual text of the August 8, 2025 ex parte motion to show it lacks the r... |

**Evidence Master (top 5):**

| Score | Section | Preview |
|---|---|---|
| 0.653 | timeline | event_date: 2025-05-22 case_type: CUSTODY event_type: order actor: Judge McNeill title: Order Denyin... |
| 0.650 | timeline | event_date: 2025-05-31 case_type: CUSTODY event_type: incident actor: Andrew Pigors title: [CONSPIRA... |
| 0.644 | timeline | event_date: 2025-05-16 case_type: CUSTODY event_type: incident actor: Andrew Pigors title: [CONSPIRA... |
| 0.643 | timeline | event_date: 2025-06-01 case_type: HOUSING event_type: incident actor: Andrew Pigors title: [HOUSING]... |
| 0.642 | timeline | event_date: 2025-04-01 case_type: CUSTODY event_type: filing actor: Andrew Pigors title: Shady Oaks ... |

---

## RAG Engine Status

- ✅ ChromaDB persistent store initialized at `C:\Users\andre\LitigationOS\00_SYSTEM\chromadb_store`
- ✅ filing_stacks collection: 265 vectors
- ✅ evidence_master collection: 1,753 vectors
- ✅ nomic-embed-text embeddings operational
- ✅ 5 test queries executed successfully

**The RAG brain is now ACTIVE and ready for queries.**