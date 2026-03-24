---
name: OMEGA-RESEARCH
description: >-
  Use when performing legal research, citation verification, authority chain validation,
  case law analysis, statutory interpretation, gap analysis, or IRAC-structured legal
  reasoning. Covers Michigan state courts (14th Circuit, COA, MSC), federal courts
  (USDC WDMI, 6th Circuit), and specialty proceedings (JTC). Hybrid retrieval via
  TF-IDF + BM25 + FTS5 + semantic search. All citations must be verifiable — no
  fabricated case law, no invented statutes, no hallucinated authority chains.
  Bluebook citation format required for all references.
category: discipline
version: "2.0.0"
triggers:
  - research
  - citation
  - case law
  - authority
  - RAG
  - legal research
  - MCR
  - MCL
  - MRE
  - FRCP
  - statute
  - precedent
  - gap analysis
  - Shepardize
  - IRAC
  - Bluebook
  - cause of action
  - standard of review
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies: []
metadata:
  tier: 1
  fused_skills: 12
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# 📚 OMEGA-RESEARCH 📚

> **TIER 1 — Core Litigation Legal Research**
> **Pipeline:** Query → Retrieve → Validate → Chain → Score → Cite → Verify
> **Case:** Pigors v Watson · 5 courts · 10 jurisdiction databases · Bluebook format
> **Zero Tolerance:** No fabricated citations. No invented case law. Every authority verifiable.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        OMEGA-RESEARCH v2.0                               ║
║               12 Skills → 8 Modules → 1 Research System                  ║
║                                                                          ║
║  R1  Authority Chain ──────┐                                             ║
║  R2  Case Law Research ────┤→ R4 IRAC Analysis ──→ R5 Gap Analysis       ║
║  R3  Statutory Research ───┘        ↓                     ↓              ║
║  R6  Citation Verification ←── R7 RAG Pipeline            │              ║
║  R8  Jurisdiction Rules ──────────────────────────────→ ALL              ║
║                                                                          ║
║  DBs: litigation_context.db + 10 jurisdiction databases                  ║
║  Methods: TF-IDF + BM25 + FTS5 + semantic + reciprocal rank fusion       ║
║  Output: Verified authority chains with Bluebook citations               ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 12 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `deep-research` | Multi-source research orchestration, iterative refinement |
| 2 | `litigation-claim-researcher` | Claim viability analysis, cause of action research |
| 3 | `litigation-authority-validator` | 5-element authority chain scoring, broken chain detection |
| 4 | `litigation-case-evaluation-specialist` | Case strength assessment, risk analysis |
| 5 | `litigation-cause-of-action-library` | 14+ cause-of-action templates with elements |
| 6 | `local-legal-search` | Local-first legal search across litigation_context.db |
| 7 | `exa-search` | Advanced search query construction and result ranking |
| 8 | `ai-rag-pipeline` | Hybrid retrieval: TF-IDF + BM25 + semantic + rank fusion |
| 9 | `litigation-analysis-engine` | Legal reasoning engine, pattern analysis, scoring |
| 10 | `litigation-appellate-strategist` | Standard of review, appellate issue framing |
| 11 | `litigation-federal-civil-rights` | 42 USC §1983, qualified immunity, Monell |
| 12 | `litigation-judicial-analyst` | Judicial profile analysis, ruling pattern detection |

---

## When to Apply

- **Authority validation** — Verifying a chain of legal authority supports a claim
- **Case law research** — Finding Michigan or federal precedent on a legal issue
- **Statutory interpretation** — Analyzing MCR, MCL, MRE, FRCP, or federal statutes
- **IRAC analysis** — Structuring legal arguments with Issue-Rule-Application-Conclusion
- **Gap analysis** — Identifying weak spots in legal authority for a filing
- **Citation verification** — Cross-referencing all citations for accuracy and currency
- **Cause of action research** — Evaluating viability of specific legal claims
- **Appellate research** — Standard of review, preserved error, appellate procedure
- **Federal civil rights** — §1983 elements, qualified immunity, Monell liability
- **Judicial bias research** — Patterns in judicial rulings for recusal motions

---

## Decision Tree

```
Research task received
  │
  ├─ "Authority chain" / "validate citation" / "is this good law"
  │   └─→ R1: Authority Chain Validation
  │
  ├─ "Case law" / "find cases" / "precedent" / "what court held"
  │   └─→ R2: Case Law Research
  │
  ├─ "Statute" / "MCR" / "MCL" / "MRE" / "FRCP" / "USC"
  │   └─→ R3: Statutory Research
  │
  ├─ "IRAC" / "legal argument" / "analyze issue" / "reasoning"
  │   └─→ R4: IRAC Analysis
  │
  ├─ "Gap" / "weakness" / "what's missing" / "filing threshold"
  │   └─→ R5: Gap Analysis (EGCP)
  │
  ├─ "Verify" / "Shepardize" / "still good law" / "overruled"
  │   └─→ R6: Citation Verification
  │
  ├─ "Search" / "find in database" / "retrieve" / "lookup"
  │   └─→ R7: RAG Pipeline
  │
  ├─ "Local rules" / "14th Circuit" / "COA rules" / "USDC WDMI"
  │   └─→ R8: Jurisdiction-Specific Rules
  │
  └─ Complex / multi-step legal research
      └─→ R7 (retrieve) → R3/R2 (authorities) → R1 (validate) → R4 (analyze) → R5 (gaps)
```

---

## ██ MODULE R1: Authority Chain Validation ██

### Purpose
Validate that every legal argument has a complete, unbroken chain of authority
from statute to case law to constitutional provision.

### 5-Element Authority Chain

```
Level 1: CONSTITUTIONAL PROVISION
  │  Example: US Const. amend. XIV, §1 (Due Process)
  │  Example: Mich. Const. 1963, art. 1, §17
  ▼
Level 2: STATUTE
  │  Example: MCL 722.23 (Best Interest Factors)
  │  Example: 42 USC §1983 (Civil Rights)
  ▼
Level 3: COURT RULE
  │  Example: MCR 2.003 (Disqualification of Judge)
  │  Example: MCR 3.210 (Child Custody)
  ▼
Level 4: CASE LAW (binding precedent)
  │  Example: Ireland v Smith, 451 Mich 457 (1996)
  │  Example: Vodvarka v Grasmeyer, 259 Mich App 499 (2003)
  ▼
Level 5: SECONDARY AUTHORITY (persuasive only)
     Example: Restatement (Third) of Torts
     Example: Law review articles, treatises
```

### Chain Scoring (0-5 per link)

| Score | Meaning | Action |
|-------|---------|--------|
| 5 | All 5 elements present, current, directly on point | Ready to cite |
| 4 | 4 elements present, minor gap in secondary authority | Acceptable |
| 3 | Core 3 elements (statute + rule + case), missing constitutional/secondary | Workable but strengthen |
| 2 | Only statute + case, missing court rule connection | Needs more research |
| 1 | Single authority (case only or statute only) | Insufficient — research more |
| 0 | No verifiable authority found | Do NOT cite — find authority first |

### Broken Chain Detection
```sql
-- Find claims with incomplete authority chains
SELECT ac.vehicle_name, ac.claim_type, ac.chain_score,
       ac.has_statute, ac.has_court_rule, ac.has_case_law,
       ac.has_constitutional, ac.has_secondary
FROM authority_chains ac
WHERE ac.chain_complete = 0 OR ac.chain_score < 3
ORDER BY ac.chain_score ASC;
```

### Key Rule
**NEVER cite an authority you cannot verify exists.** If the DB doesn't have it
and you can't confirm it through the jurisdiction databases, insert
`[AUTHORITY NEEDED — research required for [specific legal issue]]` instead of inventing a citation.

---

## ██ MODULE R2: Case Law Research ██

### Purpose
Find binding and persuasive case law relevant to each legal issue in the case.

### Court Hierarchy (binding authority, top-down)

```
MICHIGAN STATE:
  Michigan Supreme Court (Mich)     ← binding on all MI courts
  Michigan Court of Appeals (Mich App) ← binding on trial courts
  14th Circuit Court (trial)         ← bound by both above

FEDERAL:
  US Supreme Court                   ← binding on all
  6th Circuit Court of Appeals       ← binding on WDMI
  US District Court, WDMI            ← trial level
```

### Citation Format (Bluebook)

| Court | Format | Example |
|-------|--------|---------|
| Michigan Supreme Court | *Case*, Vol Mich Page (Year) | *Ireland v Smith*, 451 Mich 457 (1996) |
| Michigan Court of Appeals | *Case*, Vol Mich App Page (Year) | *Vodvarka v Grasmeyer*, 259 Mich App 499 (2003) |
| 6th Circuit | *Case*, Vol F.3d/F.4th Page (6th Cir. Year) | *Doe v Univ of Mich*, 42 F.4th 519 (6th Cir. 2022) |
| USDC WDMI | *Case*, Vol F. Supp. 3d Page (W.D. Mich. Year) | *Smith v Jones*, 123 F. Supp. 3d 456 (W.D. Mich. 2023) |

### Research Strategy

1. **Start with binding authority** — Michigan Supreme Court first, then COA
2. **Check recent decisions** — Newer cases may modify or distinguish older ones
3. **Verify currency** — Has the case been overruled, modified, or distinguished?
4. **Match facts** — Prioritize cases with factually similar scenarios
5. **Document negative authority** — Cases that go against your position (for pre-emption)

### Database Queries
```sql
-- Search case law in authority database
SELECT case_name, citation, court, year, holding, relevance
FROM case_law
WHERE topic LIKE ? OR holding LIKE ?
ORDER BY court_rank ASC, year DESC;

-- Search evidence_quotes for case citations already in evidence
SELECT quote_text, source_document, claim_id
FROM evidence_quotes
WHERE quote_text LIKE '%Mich App%' OR quote_text LIKE '%Mich %'
ORDER BY relevance_score DESC;
```

---

## ██ MODULE R3: Statutory Research ██

### Purpose
Research and interpret statutes, court rules, and rules of evidence applicable
to each case lane.

### Key Statutory Sources by Lane

| Lane | Primary Statutes | Primary Rules |
|------|-----------------|---------------|
| A (Custody) | MCL 722.21-722.31 (Child Custody Act) | MCR 3.210-3.219 |
| B (Housing) | MCL 600.5714-5744 (Summary Proceedings) | MCR 4.201 |
| C (§1983) | 42 USC §1983, 28 USC §1331/1343 | FRCP, FRE |
| D (PPO) | MCL 600.2950/2950a | MCR 3.705-3.708 |
| E (Misconduct) | MCR 2.003, Mich Const art 6 §30 | JTC Rules |
| F (Appellate) | MCR 7.201-7.219 (COA), MCR 7.301-7.319 (MSC) | MCR 7.212 (briefs) |

### Critical Statutes for Pigors v Watson

```
CUSTODY (Lane A):
  MCL 722.23    — Best Interest of the Child factors (a)-(l)
  MCL 722.25    — Parenting time
  MCL 722.27    — Modification of custody/support orders
  MCL 722.27a   — Change of domicile
  MCL 552.602-602d — Child support

DISQUALIFICATION (Lane E):
  MCR 2.003(C)  — Grounds for disqualification of a judge
  MCR 2.003(D)  — Procedure for disqualification
  Canon 2, MRPC — Impartiality and appearance of impartiality

APPELLATE (Lane F):
  MCR 7.203(A)  — Jurisdiction of Court of Appeals
  MCR 7.205     — Application for leave to appeal
  MCR 7.212     — Briefs (formatting, content requirements)

FEDERAL CIVIL RIGHTS (Lane C):
  42 USC §1983  — Civil action for deprivation of rights
  28 USC §1331  — Federal question jurisdiction
  28 USC §1343  — Civil rights jurisdiction
  42 USC §1988  — Attorney fees in civil rights cases
```

### Interpretation Framework
1. **Plain meaning** — Start with the statutory text
2. **Legislative intent** — If ambiguous, look to legislative history
3. **Court interpretation** — How have courts applied this statute?
4. **Harmonize** — Read related statutes together (in pari materia)
5. **Strict/liberal construction** — Remedial statutes construed liberally

---

## ██ MODULE R4: IRAC Analysis ██

### Purpose
Structure every legal argument using the Issue-Rule-Application-Conclusion framework.
This is the standard for Michigan court filings.

### IRAC Template

```
═══════════════════════════════════════════
ISSUE: [Precise legal question]
═══════════════════════════════════════════

RULE: [Statement of controlling law]
  Statute: [MCL/USC citation]
  Court Rule: [MCR/FRCP citation]
  Case Law: [Binding precedent with citation]
  Standard: [Standard of review if appellate]

APPLICATION:
  [Apply the rule to the specific facts of this case]
  [Reference specific evidence by Bates number or exhibit]
  [Address counter-arguments]
  [Distinguish unfavorable authority]

CONCLUSION:
  [Clear statement of the result the law requires]
  [Specific relief requested]
═══════════════════════════════════════════
```

### 14 Claim Types (Pigors v Watson)

| # | Claim | Lane | Key Statute |
|---|-------|------|-------------|
| 1 | Custody modification | A | MCL 722.27 |
| 2 | Parenting time enforcement | A | MCL 722.25 |
| 3 | Best interest violation | A | MCL 722.23 |
| 4 | Parental alienation | A | MCL 722.23(j) |
| 5 | Child support modification | A | MCL 552.602 |
| 6 | PPO violation | D | MCL 600.2950 |
| 7 | Housing code violation | B | MCL 600.5714 |
| 8 | Judicial disqualification | E | MCR 2.003(C) |
| 9 | Due process violation | C/E | US Const. amend. XIV |
| 10 | Equal protection violation | C | US Const. amend. XIV |
| 11 | §1983 (state action) | C | 42 USC §1983 |
| 12 | Contempt of court | A/D | MCL 600.1701 |
| 13 | FOC misconduct | A | MCL 552.505 |
| 14 | Appellate error | F | MCR 7.216 |

### Quality Gate
Every IRAC section MUST have:
- [ ] At least one binding authority cited (statute + case law minimum)
- [ ] At least one specific evidence reference (Bates number or exhibit)
- [ ] Counter-argument addressed (what will the other side say?)
- [ ] Conclusion tied to specific relief

---

## ██ MODULE R5: Gap Analysis ██

### Purpose
Identify weaknesses in legal authority and evidence support for each claim.
Uses EGCP scoring to assess filing readiness.

### EGCP Scoring (per claim)

| Component | Question | Score 0-5 |
|-----------|----------|-----------|
| **E** — Evidence | How strong is the existing evidence? | 0=none, 5=overwhelming |
| **G** — Gaps | How severe are the gaps? | 0=no gaps, 5=critical gaps |
| **C** — Claims | How legally viable is the claim? | 0=frivolous, 5=slam dunk |
| **P** — Proof | Does the evidence meet the burden? | 0=not close, 5=exceeds standard |

### Filing Readiness Matrix

| E | G | C | P | Status | Action |
|---|---|---|---|--------|--------|
| ≥4 | ≤1 | ≥4 | ≥4 | 🟢 READY | File immediately |
| ≥3 | ≤2 | ≥3 | ≥3 | 🟡 NEAR READY | Minor gap-filling then file |
| ≥2 | ≤3 | ≥3 | ≥2 | 🟠 NEEDS WORK | Targeted evidence acquisition |
| <2 | >3 | any | <2 | 🔴 NOT READY | Major research/evidence needed |
| any | any | <2 | any | ⚫ RECONSIDER | Claim may not be viable |

### Gap Detection Query
```sql
-- Comprehensive gap analysis per claim
SELECT
    c.claim_id, c.claim_type, c.vehicle_name,
    c.evidence_score AS E,
    c.gap_score AS G,
    c.viability_score AS C,
    c.proof_score AS P,
    CASE
        WHEN c.evidence_score >= 4 AND c.gap_score <= 1 THEN 'READY'
        WHEN c.evidence_score >= 3 AND c.gap_score <= 2 THEN 'NEAR_READY'
        WHEN c.evidence_score >= 2 AND c.gap_score <= 3 THEN 'NEEDS_WORK'
        ELSE 'NOT_READY'
    END AS filing_status
FROM claims c
WHERE c.status = 'active'
ORDER BY c.gap_score DESC, c.evidence_score ASC;
```

### Gap Remediation Protocol
For each identified gap:
1. **Specify exactly what's missing** — "Need text messages from March 2024 showing [X]"
2. **Identify potential sources** — "Check F:\Correspondence\, G:\Screenshots\"
3. **Assign acquisition priority** — Critical (blocks filing) / Important / Nice-to-have
4. **Track in database** — Insert into acquisition_tasks table
5. **Set deadline** — When must this evidence be acquired by?

---

## ██ MODULE R6: Citation Verification ██

### Purpose
Verify every citation in a filing is accurate, current, and properly formatted.
No fabricated citations may appear in any court document.

### Verification Checklist (per citation)

- [ ] **Exists** — Citation refers to a real case/statute/rule
- [ ] **Format** — Bluebook-compliant citation format
- [ ] **Current** — Not overruled, modified, or superseded
- [ ] **Relevant** — Actually supports the proposition cited for
- [ ] **Binding** — Correctly identifies whether binding or persuasive
- [ ] **Pin cite** — Specific page/section reference (not just case name)

### Red Flags (auto-detect)

| Pattern | Risk | Action |
|---------|------|--------|
| Case name not in DB | May be fabricated | Flag `[VERIFY — citation not found in database]` |
| Volume/page mismatch | Typo or fabrication | Cross-reference with known citations |
| "Id." without antecedent | Format error | Trace back to find the referenced citation |
| Overruled case | Bad law | Check subsequent history |
| Wrong court identified | Attribution error | Verify court from citation format |
| Statute repealed/amended | Outdated law | Check current MCL/USC version |

### Anti-Hallucination Protocol
```
BEFORE citing any authority:
  1. Query litigation_context.db → authority_chains, case_law tables
  2. Query jurisdiction databases → databases/*.db
  3. If found → cite with confidence
  4. If NOT found → insert [CITATION NEEDED — verify: case/statute description]
  5. NEVER invent a citation to fill a gap
```

### Database Cross-Reference
```sql
-- Verify a case citation exists
SELECT case_name, citation, court, year, status
FROM case_law WHERE citation LIKE ? OR case_name LIKE ?;

-- Check authority chain completeness
SELECT vehicle_name, claim_type, chain_score, chain_complete
FROM authority_chains WHERE vehicle_name = ?;
```

---

## ██ MODULE R7: RAG Pipeline ██

### Purpose
Hybrid retrieval-augmented generation pipeline for searching the 12 GB
litigation database and 10 jurisdiction databases.

### Retrieval Stack

```
Query → Preprocessing (tokenize, expand, normalize)
  ├─ TF-IDF retrieval (fast, keyword-based)
  ├─ BM25 retrieval (tuned for legal text, k1=1.5, b=0.75)
  ├─ FTS5 full-text search (SQLite native, boolean queries)
  └─ Semantic search (embedding-based similarity)
      ↓
  Reciprocal Rank Fusion (combine all result sets)
      ↓
  Re-ranking (relevance scoring per legal context)
      ↓
  Top-K results with provenance tracking
```

### FTS5 Query Patterns
```sql
-- Boolean search with ranking
SELECT document_id, rank, snippet(fts_documents, 0, '<b>', '</b>', '...', 64)
FROM fts_documents
WHERE fts_documents MATCH 'custody AND "best interest" NOT housing'
ORDER BY rank LIMIT 20;

-- Proximity search
SELECT * FROM fts_documents
WHERE fts_documents MATCH 'NEAR(parenting time, modification, 10)'
ORDER BY rank;

-- Column-specific search
SELECT * FROM fts_evidence
WHERE fts_evidence MATCH 'quote_text:alienation OR quote_text:"parental interference"'
ORDER BY rank;
```

### Adaptive Query Rewriting
The `adaptive_query_rewriter.py` module automatically optimizes queries:
- `LIKE '%term%'` → FTS5 `MATCH 'term'` (100x faster on large tables)
- Cached `COUNT(*)` results for frequently queried tables
- Safety `LIMIT` added to unbounded queries
- Always route through the rewriter for hot-path queries

### Key Databases

| Database | Tables | Purpose |
|----------|--------|---------|
| `litigation_context.db` | 790+ | Central evidence, claims, authorities, filings |
| `court_forms.db` | 5+ | Michigan SCAO form definitions and requirements |
| `databases/14th_circuit_family.db` | — | 14th Circuit Family Division local rules |
| `databases/michigan_coa.db` | — | COA procedures, briefing rules, deadlines |
| `databases/michigan_msc.db` | — | MSC rules, application procedures |
| `databases/usdc_wdmi.db` | — | USDC WDMI local rules, CM/ECF procedures |
| `databases/jtc.db` | — | Judicial Tenure Commission procedures |

---

## ██ MODULE R8: Jurisdiction-Specific Rules ██

### Purpose
Apply the correct procedural rules for each court and case lane.
Michigan courts have layered rule systems that must be navigated precisely.

### Rule Hierarchy (Michigan State)

```
Level 1: Michigan Court Rules (MCR) — statewide
Level 2: Local Administrative Orders — per circuit
Level 3: Standing Orders — per judge
Level 4: Practice Customs — per court
```

### 14th Circuit Court (Muskegon County) — Lanes A, D, E

| Rule Area | Applicable Rules | Key Requirements |
|-----------|-----------------|------------------|
| Filing | MCR 2.107, Local Rule 1.02 | E-filing via MiFILE preferred |
| Service | MCR 2.105, MCR 2.107 | Service by mail + proof of service |
| Motions | MCR 2.119 | 9-day notice, 7-day brief filing deadline |
| Discovery | MCR 2.301-2.316 | 28-day response time for interrogatories |
| Scheduling | MCR 2.401 | Scheduling conference within 91 days |
| Custody | MCR 3.210-3.219 | Friend of the court involvement mandatory |

### Michigan Court of Appeals — Lane F

| Rule Area | Applicable Rules | Key Requirements |
|-----------|-----------------|------------------|
| Jurisdiction | MCR 7.203 | Claim of appeal or leave application |
| Filing | MCR 7.204 | 21 days for claim of appeal (right) |
| Briefs | MCR 7.212 | 56-day deadline, 50-page limit, double-spaced |
| Record | MCR 7.210 | Register of actions, transcript, exhibits |
| Oral argument | MCR 7.214 | 30 minutes per side default |
| Stay | MCR 7.209 | Motion to stay in trial court first |

### USDC Western District of Michigan — Lane C

| Rule Area | Applicable Rules | Key Requirements |
|-----------|-----------------|------------------|
| Jurisdiction | 28 USC §1331, 1343 | Federal question, civil rights |
| Filing | FRCP 3, LCivR 5.7 | CM/ECF electronic filing |
| Service | FRCP 4 | 90 days for service |
| Pleading | FRCP 8, Twombly/Iqbal | Plausibility standard |
| Discovery | FRCP 26-37 | Initial disclosures within 14 days of 26(f) |
| Summary judgment | FRCP 56, LCivR 7.2 | Statement of undisputed facts required |

### JTC Procedures — Lane E

| Stage | Procedure | Key Requirements |
|-------|-----------|------------------|
| Complaint | MCR 9.220-9.223 | 28-day investigation period |
| Investigation | MCR 9.224 | Confidential during pendency |
| Formal complaint | MCR 9.229 | Public proceeding after formal charges |
| Hearing | MCR 9.231 | Master/panel hearing |
| Discipline | Mich Const art 6 §30 | Censure, suspension, or removal |

---

## ██ GLOBAL RULES (Apply to ALL Modules) ██

### Anti-Hallucination (CRITICAL)
- **NEVER fabricate a case name, citation, or holding** — verify in DB first
- **NEVER invent a statute number** — confirm in MCL/MCR/USC indexes
- **NEVER claim a case says something it doesn't** — quote the actual holding
- If authority cannot be verified: `[CITATION NEEDED — research: [description of issue]]`
- Every citation must be traceable to a DB record or verified source

### Database-First Research
```python
# ALWAYS query the DB before claiming anything
from db_lock_manager import managed_db

with managed_db() as conn:
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    
    # Check authority chains
    result = conn.execute("""
        SELECT chain_score, chain_complete, has_statute, has_case_law
        FROM authority_chains WHERE vehicle_name = ? AND claim_type = ?
    """, (vehicle, claim)).fetchone()
```

### Traceable Statistics
- Every count cited MUST come from a `SELECT COUNT(*)` query
- Every percentage MUST show numerator and denominator
- NEVER round up to inflate numbers
- NEVER extrapolate from partial data

### Bluebook Citation Rules
- Case names in italics: *Ireland v Smith*
- Statutes not italicized: MCL 722.23
- Court rules not italicized: MCR 2.003(C)(1)
- Pin cites required: *Ireland*, 451 Mich at 461
- Subsequent history required: *Smith v Jones*, 100 Mich App 200 (2020), rev'd, 510 Mich 50 (2022)

---

## ═══════════════════════════════════════════════════════════════
## UPGRADE v2.1: MICHIGAN AUTHORITY SYSTEM
## ═══════════════════════════════════════════════════════════════

### Authority Master Index (728 authorities indexed)
```sql
-- litigation_context.db
SELECT * FROM authority_master_index WHERE type = 'MCR' AND lanes LIKE '%A%';
SELECT * FROM authority_fts WHERE authority_fts MATCH 'disqualification OR recusal';
```

### Michigan Rule Systems
| System | Scope | Key Rules for Pigors v Watson |
|--------|-------|------------------------------|
| **MCR** | Court Rules | 2.003 (disqualification), 2.119 (motions), 3.206 (custody), 7.212 (COA briefs) |
| **MCL** | Compiled Laws | 722.23 (best interest), 552.605 (child support), 600.2950 (PPO), 780.972 (self-defense) |
| **MRE** | Evidence Rules | 401/402 (relevance), 404(b) (prior acts), 702 (experts), 801-807 (hearsay), 901 (authentication) |
| **SCAO** | Admin Orders | Court forms, e-filing, case assignment |
| **FOC** | Friend of Court | MCL 552.505+, FOC handbook, support calculations |
| **JTC** | Judicial Tenure | MCR 9.200+, complaint procedures, grounds for discipline |
| **Canon** | Judicial Canons | Canons 1-7, esp. Canon 2 (impartiality), Canon 3 (recusal) |

### LEXICON Integration (148 procedural rules)
```sql
-- 00_SYSTEM/databases/lexicon.db
SELECT r.*, cr.target_rule FROM rules r
LEFT JOIN cross_references cr ON r.rule_id = cr.source_rule
WHERE r.rule_id = 'MCR 2.003';
-- Returns: rule text + all cross-referenced rules
```

### Shepardizing Workflow (Local-Only)
```
1. Extract citation from filing → parse components (reporter, volume, page)
2. Query authority_master_index for the citation
3. Check authority_chains for treatment history
4. Cross-reference with LEXICON rules_fts for procedural context
5. Flag: overruled? distinguished? affirmed? modified?
6. If not in DB → insert [VERIFY — Shepardize citation] placeholder
```

### COA/MSC Brief Requirements
| Court | Rule | Page Limit | Font | Margins | Appendix |
|-------|------|-----------|------|---------|----------|
| **COA** | MCR 7.212 | 50 pp (or 16K words) | 12pt proportional or 12pt mono | 1" all sides | Required per MCR 7.212(H) |
| **MSC** | MCR 7.312 | 50 pp (or 16K words) | Same as COA | Same | Required per MCR 7.312 |
| **14th Circuit** | MCR 2.119 | No fixed limit (15pp guideline) | 12pt | 1" | Not required |

### Opposition Research Patterns
```
For any opposing motion/brief:
  1. Extract ALL citations
  2. Verify each against authority_master_index
  3. Check subsequent history — are any overruled/distinguished?
  4. Identify distinguishing facts (our case vs. cited case)
  5. Find counter-authorities supporting our position
  6. Check for misquotes/selective quoting via evidence_quotes
```
