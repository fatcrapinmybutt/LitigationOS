---
name: litigation-claim-researcher
description: >-
  Use when you have raw facts and need to systematically identify every viable cause of
  action, map evidence to elements, score claim viability, and rank claims by filing
  priority.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: research, viable claims, fact mapping, legal theory
---
# litigation-claim-researcher

> **Category:** discipline
> **Tier:** 2
> **Jurisdiction:** Michigan — 14th Judicial Circuit, Muskegon County
> **Context:** Pigors v Watson, pro se litigation

## Description

Use when you have raw facts from a case and need to systematically identify every viable cause of action, map evidence to elements, score claim viability, and rank claims by filing priority — especially when you suspect claims are being missed or under-explored.

## Triggers

- User provides case facts and asks "what can I sue for" or "what claims do I have"
- User wants to ensure no viable claims are being overlooked
- User needs fact-to-element mapping for known claims
- User needs to prioritize which claims to file first
- User wants a cost-benefit analysis of potential claims
- User asks to evaluate the strength of a particular legal theory

## Research Protocol

### Phase 1 — Exhaustive Fact Extraction

Before analyzing ANY legal theories, extract every fact:

1. **Temporal facts**: Every dated event — create a chronological master list
2. **Actor facts**: Every person/entity involved and their role
3. **Document facts**: Every document, communication, contract, notice
4. **Harm facts**: Every harm suffered — physical, emotional, financial, property
5. **Relationship facts**: Every legal relationship (landlord-tenant, contractual, fiduciary)
6. **Regulatory facts**: Every applicable code, statute, regulation, ordinance
7. **Omission facts**: Every duty that was NOT performed

**Quality Gate:** The fact list should be comprehensive. If the user provides 10 facts, the analysis should identify at least 5 additional implied facts (e.g., if there was a lease, there was a habitability covenant — MCL 554.139).

### Phase 2 — Rights Mapping

For each fact, identify what legal rights it implicates:

| Fact Category | Rights Implicated | Source of Right |
|--------------|------------------|----------------|
| False statement by defendant | Right to truthful dealing | Common law fraud, MCPA |
| Unsafe premises | Right to habitable housing | MCL 554.139, building code |
| Unauthorized entry | Right to quiet enjoyment | Lease covenant, trespass |
| Deposit not returned | Right to deposit return | MCL 554.601 et seq. |
| Retaliation for complaint | Right to exercise legal rights | MCL 600.5720 |
| Discriminatory treatment | Right to equal treatment | Elliott-Larsen, FHA |

### Phase 3 — Cause of Action Identification

For each implicated right, identify ALL possible causes of action:

**Systematic Checklist:**

#### A. Tort Claims (cross-reference Skill 22, tort-elements.md):
- [ ] Fraud (6 elements)
- [ ] Silent fraud / concealment
- [ ] Negligence
- [ ] Negligence per se
- [ ] IIED
- [ ] NIED
- [ ] Conversion
- [ ] Trespass
- [ ] Defamation (per se / per quod)
- [ ] Invasion of privacy (4 types)
- [ ] Civil conspiracy
- [ ] Abuse of process
- [ ] Malicious prosecution
- [ ] Wrongful eviction

#### B. Contract Claims:
- [ ] Breach of express contract
- [ ] Breach of implied contract
- [ ] Breach of implied warranty of habitability (MCL 554.139)
- [ ] Breach of covenant of quiet enjoyment
- [ ] Unjust enrichment / quantum meruit

#### C. Statutory Claims (cross-reference Skill 22, statutory-elements.md):
- [ ] MCPA (MCL 445.903) — check ALL 29 subsections
- [ ] Truth in Renting (MCL 554.631)
- [ ] Security Deposit Act (MCL 554.601)
- [ ] Retaliatory Action (MCL 600.5720)
- [ ] Elliott-Larsen Civil Rights Act
- [ ] Manufactured Housing Act (MCL 125.2301)
- [ ] Building code violations

#### D. Federal Claims:
- [ ] 42 USC § 1983 (if state action present)
- [ ] Fair Housing Act (42 USC § 3601)

#### E. Derivative / Combination Claims:
- [ ] Civil conspiracy (requires underlying tort)
- [ ] Aiding and abetting
- [ ] Respondeat superior (employer liability)
- [ ] Piercing the corporate veil
- [ ] Joint venture liability

### Phase 4 — Element-by-Element Analysis

For each candidate cause of action, map facts to elements:

```
CLAIM: [Cause of Action]
Element 1: [Statement] → Fact(s): [Reference] → Evidence: [Document/Testimony] → Strength: [STRONG/ARGUABLE/WEAK]
Element 2: [Statement] → Fact(s): [Reference] → Evidence: [Document/Testimony] → Strength: [STRONG/ARGUABLE/WEAK]
...
Element N: [Statement] → Fact(s): [Reference] → Evidence: [Document/Testimony] → Strength: [STRONG/ARGUABLE/WEAK]
Coverage: [X/N elements] = [XX%]
```

### Phase 5 — Viability Scoring

Score each claim using the framework in `references/viability-scoring.md`:

| Factor | Weight | Score Range |
|--------|--------|-------------|
| Element coverage | 30% | 0-100 |
| Evidence strength | 25% | 0-100 |
| SOL compliance | 15% | 0 or 100 |
| Defense vulnerability | 15% | 0-100 |
| Remedy value | 15% | 0-100 |

**Composite Score = Weighted average of all factors**

### Phase 6 — Priority Ranking

Rank all viable claims by filing priority:

| Priority | Criteria |
|----------|----------|
| **CRITICAL** | Score ≥ 80, high damages, time-sensitive (SOL expiring) |
| **HIGH** | Score ≥ 65, strong elements, meaningful remedies |
| **MEDIUM** | Score ≥ 50, arguable elements, modest remedies |
| **LOW** | Score ≥ 35, weak elements or limited remedies |
| **DEFER** | Score < 35, but preserve for later development |
| **REJECT** | Score < 20, elements not supportable |

## Bias Correction Protocols

### Against Confirmation Bias:
For each claim you WANT to include, ask: "What is the strongest argument AGAINST this claim?" If you cannot articulate a strong counterargument, you may be rationalizing.

### Against Overlooked Claims:
After completing the checklist, force yourself through EVERY cause of action in Skill 22's reference files, even ones that seem inapplicable. Spend at least one sentence explaining why each rejected claim doesn't fit.

### Against Premature Dismissal:
Before rejecting any claim, score it. A claim with 3/4 elements met and only 1 weak element may still be viable with additional investigation. Mark it "INVESTIGATE FURTHER" rather than "REJECT."

### Against Tunnel Vision:
If all identified claims fall in one category (e.g., all torts), force yourself to analyze statutory, contractual, and federal theories. Multi-theory complaints are stronger.

## Cross-References

- **Skill 22** (litigation-cause-of-action-library): Element lists and SOL for each claim
- **Skill 23** (litigation-complaint-drafter): Draft the complaint once claims are identified
- **Skill 25** (litigation-service-engine): Service after filing

## Related Skills

- [litigation-cause-of-action-library](skill://litigation-cause-of-action-library) — References causes of action elements
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Extracts and classifies case evidence


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
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
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
| PPO Modification/Termination | 60/100 | B,D,E | Verified |
| Summary Disposition (C10) | 75/100 | B,D,E | Verified |
| Summary Disposition (C8) | 70/100 | B,D,E | Verified |
| Judicial Disqualification | 75/100 | B,D,E | Verified |
| Default Judgment | 60/100 | B,D,E | Verified |
| TRO Application | 60/100 | B,D,E | Verified |
| JTC Formal Complaint | 75/100 | B,D,E | Verified |

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
