---
name: litigation-harm-quantifier
description: >-
  Use when calculating, quantifying, or structuring damages for any claim — converting
  documented harms into dollar amounts through compensatory, punitive, nominal,
  statutory treble, and equitable remedy frameworks.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: damages, harm, emotional distress, per diem, economic
---
# LITIGATION-HARM-QUANTIFIER

## Metadata

- **name**: litigation-harm-quantifier
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-evidence-mapper, litigation-claims-analyzer

## Description

Use when calculating, quantifying, or structuring damages for any claim in the Pigors v Watson litigation. This skill converts documented harms into dollar amounts through a rigorous five-link chain: Harm → Causation → Evidence → Relief Theory → Damages Calculation. It covers compensatory damages (economic and non-economic), punitive damages, nominal damages, statutory treble damages under Michigan consumer protection law, and equitable remedies. Specifically calibrated for the overlapping custody, housing, and federal civil rights claims in this case.

## Triggers

- User needs to calculate or estimate damages for a motion, complaint, or brief
- User asks "how much can I claim" or "what are my damages" for any claim type
- User is drafting a damages section for a filing or demand letter
- User needs to map specific harms to dollar amounts with supporting evidence
- User asks about emotional distress valuation, lost wages, or housing damages
- User needs to structure a damages prayer or relief section
- User is preparing for mediation or settlement and needs damages framework

## Harm Chain Framework

Every damages argument must trace through all five links. A break in any link defeats that damages category.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   1. HARM   │───▶│ 2. CAUSATION│───▶│ 3. EVIDENCE │───▶│  4. RELIEF  │───▶│ 5. DAMAGES  │
│  (What hurt)│    │ (Who caused)│    │ (Proof of)  │    │  (Theory)   │    │(Dollar amt) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Link 1: Harm Identification

Catalog every harm across all claim categories:

| Harm Category | Specific Harms (Pigors Case) |
|---|---|
| Custody/Parental | Loss of parenting time, parent-child bond disruption, alienation effects, schedule interference |
| Housing/Consumer | Defective conditions, habitability failures, deposit theft, fraudulent representations |
| Emotional/Psychological | Anxiety, depression, PTSD symptoms, sleep disruption, loss of enjoyment of life |
| Economic/Financial | Lost wages (court appearances), repair costs, alternative housing costs, moving expenses |
| Civil Rights | Due process deprivation, equal protection violation, judicial bias harm |
| Children's Harms | Derivative claims, therapy costs, educational disruption, emotional harm to minors |

### Link 2: Causation Analysis

Michigan uses **but-for** causation (proximate cause) under Skinner v Square D Co, 445 Mich 153 (1994):

- **But-for test**: But for defendant's conduct, would the harm have occurred?
- **Proximate cause**: Was the harm a foreseeable result of defendant's conduct?
- **Substantial factor**: For multiple causes, was defendant's conduct a substantial factor?
- **Intervening cause defense**: Was there a superseding cause that broke the causal chain?

For each harm, document:
1. The specific defendant conduct causing the harm
2. The temporal connection (when conduct occurred → when harm manifested)
3. The absence of alternative explanations
4. Foreseeability of the harm type

### Link 3: Evidence Mapping

Each harm requires specific evidence types. See `references/evidence-requirements.md` for the complete matrix. Minimum evidence per harm:

- **Documentary**: At least one document per claimed harm (receipt, record, report)
- **Testimonial**: Plaintiff declaration + corroboration where available
- **Expert**: Required for future damages, complex causation, and non-obvious harms
- **Demonstrative**: Photos, timelines, charts for jury/judge comprehension

### Link 4: Relief Theory Selection

Match each harm to the appropriate relief mechanism:

| Relief Type | When Available | Michigan Authority |
|---|---|---|
| Compensatory (Economic) | Quantifiable out-of-pocket losses | Standard tort measure |
| Compensatory (Non-Economic) | Pain, suffering, emotional distress | MCL 600.1483 (caps in medical malpractice only; no cap in intentional torts) |
| Punitive/Exemplary | Malicious, willful, or wanton conduct | Veselenak v Smith, 414 Mich 567 (1982); MCL 600.6304 |
| Nominal | Right violated but damages unquantifiable | Constitutional tort actions |
| Statutory (Treble) | Michigan Consumer Protection Act | MCL 445.911(2) — minimum $250 |
| Equitable | Injunctive relief, specific performance | Court's inherent equity powers |

### Link 5: Damages Calculation

Apply the appropriate calculation method from `references/calculation-methods.md`:

**Economic Damages Formula:**
```
Total Economic = (Past Out-of-Pocket) + (Future Out-of-Pocket × Present Value Factor)
                + (Lost Wages Past) + (Lost Earning Capacity Future)
                + (Cost of Remediation/Repair)
```

**Non-Economic Damages Framework:**
```
Per Diem Method:  Daily suffering value × Number of affected days
Multiplier Method: Economic damages × Severity multiplier (1.5–5x)
Comparable Verdict: Similar Michigan cases with similar harm profiles
Hybrid Approach:   Average of all three methods (recommended)
```

## Damages Categories for Pigors v Watson

### A. Custody-Related Damages

1. **Lost Parenting Time**: Value each missed day/hour; document with court orders vs. actual time received
2. **Parent-Child Bond Harm**: Non-economic; requires psychological testimony or detailed declaration
3. **Alienation Damages**: Emerging area; document behavioral changes in children, therapy costs
4. **Schedule Interference Costs**: Transportation, lost wages for rescheduling, childcare

### B. Housing/Consumer Damages

1. **Rent Differential**: Difference between rent paid and fair market value of defective unit
2. **Security Deposit**: Actual amount + statutory penalties under MCL 554.613 (double deposit)
3. **Repair Costs**: Out-of-pocket repairs tenant made; estimates for repairs landlord refused
4. **Moving/Relocation**: Actual costs forced by uninhabitable conditions
5. **MCPA Treble Damages**: MCL 445.911(2) — actual damages × 3 or $250 minimum

### C. Emotional Distress Damages

Michigan recognizes IIED and NIED as independent torts:

- **IIED**: Requires extreme and outrageous conduct; Roberts v Auto-Owners Ins Co, 422 Mich 594 (1985)
- **NIED**: Requires physical manifestation or zone of danger in negligence context
- **Parasitic**: Emotional distress attached to another tort (no independent showing needed)

Valuation factors:
- Severity and duration of distress
- Physical manifestations (insomnia, weight change, medical treatment)
- Impact on daily functioning and relationships
- Corroboration (therapist records, witness testimony, medication records)

### D. Federal Civil Rights Damages (42 USC § 1983)

- **Compensatory**: Full tort-style damages for constitutional violations
- **Nominal**: $1 where right violated but no actual damages proven; Carey v Piphus, 435 US 247 (1978)
- **Punitive**: Available against individuals (not municipalities); Smith v Wade, 461 US 30 (1983)
- **Attorney fees not applicable for pro se**: Kay v Ehrler, 499 US 432 (1991) — pro se litigants cannot recover attorney fees under § 1988

## Calculation Workflow

```
Step 1: List every specific harm experienced (use Harm Category table above)
Step 2: For each harm, identify the responsible defendant and causal link
Step 3: Match evidence to each harm (see evidence-requirements.md)
Step 4: Select relief theory for each harm (compensatory, punitive, statutory, equitable)
Step 5: Apply calculation method (see calculation-methods.md)
Step 6: Check for overlap/double-counting across claims
Step 7: Apply statutory caps or multipliers where applicable
Step 8: Draft damages summary table for filing
Step 9: Prepare prayer for relief with specific dollar amounts
```

## Anti-Double-Counting Rules

- The same out-of-pocket cost cannot appear under two different damage categories
- Non-economic damages for the same emotional harm can only be claimed once even if multiple torts caused it
- Statutory treble damages under MCPA are calculated on actual damages, not on damages already enhanced
- Punitive damages are calculated independently from compensatory but informed by their amount

## Michigan-Specific Caps and Limits

| Damages Type | Cap/Limit | Authority |
|---|---|---|
| Non-Economic (Med Mal) | $280,000–$500,000 (indexed) | MCL 600.1483 |
| Non-Economic (Other Torts) | **No cap** | |
| Punitive | No statutory cap; constitutional limit ~9:1 ratio | State Farm v Campbell, 538 US 408 (2003) |
| MCPA Statutory | Treble actual damages or $250 minimum | MCL 445.911(2) |
| Security Deposit | Double the deposit amount | MCL 554.613 |
| § 1983 Punitive | No cap against individuals | |

## Output Format

When quantifying damages, always produce:

1. **Damages Summary Table**: Harm | Category | Amount | Calculation Method | Key Evidence
2. **Total Damages Range**: Conservative (provable minimum) to Aggressive (maximum arguable)
3. **Prayer for Relief Language**: Court-ready text for the relief section
4. **Evidence Gap Analysis**: What's missing to prove each damages element

## Files

- `gotchas.md` — Anti-rationalization table for damages pitfalls
- `references/damages-taxonomy.md` — Complete damages type taxonomy with Michigan case law
- `references/calculation-methods.md` — Calculation frameworks for all damages types
- `references/evidence-requirements.md` — Evidence matrix for each damages category

## Related Skills

- [litigation-federal-civil-rights](skill://litigation-federal-civil-rights) — Drafts federal civil rights claims
- [litigation-custody-specialist](skill://litigation-custody-specialist) — Analyzes Michigan custody law factors


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
**MCR:** MCR 2.625
**MCL:** MCL 600.2911, MCL 600.2913, MCL 600.2918, MCL 600.6304, MCL 600.6306
**Binding Cases:**
- *Veselenak v Smith, 414 Mich 567*
- *Casey v Auto Owners Ins, 273 Mich App 388*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
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
| Custody Modification | 65/100 | A,B,D,E | Verified |
| Emergency Custody | 55/100 | A,B,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D,E | Verified |
| Contempt | 70/100 | A,B,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,D,E | Verified |
| Default Judgment | 60/100 | A,B,D,E | Verified |
| TRO Application | 60/100 | A,B,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,D,E | Verified |

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
