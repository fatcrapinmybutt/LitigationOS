---
name: litigation-parental-alienation-detector
description: >-
  Use when detecting parental alienation patterns, cataloging alienation behaviors
  with evidence links, analyzing MCL 722.23(j) willingness-to-facilitate factor,
  building temporal behavior patterns for court presentation, or preparing
  counter-narratives against false alienation claims in Michigan custody cases.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    alienation, parental alienation, Gardner, best interest factor j,
    willingness to facilitate, gatekeeping, parent-child relationship,
    MCL 722.23(j), Vodvarka
---

# litigation-parental-alienation-detector

> **Tier:** 2 — Discipline Specialist
> **Category:** discipline
> **Version:** 1.0.0
> **Lane:** A (Custody — 2024-001507-DC)

## Description

Parental Alienation Pattern Detection and Documentation Specialist for the
Pigors v. Watson custody litigation. Detects, catalogs, and documents
alienation behaviors using the Gardner 8-manifestation framework, links
each behavior to supporting evidence, and produces court-ready reports
tied to Michigan's best-interest factors — particularly MCL 722.23(j)
(willingness to facilitate a close and continuing parent-child relationship).

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case No. | 2024-001507-DC |
| Lane | A (Custody) |

## Triggers

- User mentions parental alienation, gatekeeping, or estrangement
- User asks about MCL 722.23 factor (j) analysis
- User references Gardner alienation criteria or 8 manifestations
- User needs evidence linking for alienation behavior patterns
- User preparing for custody modification based on alienation
- User needs counter-narrative against false alienation allegations

## Gardner Eight Manifestations Framework

The eight behavioral manifestations of Parental Alienation Syndrome (PAS)
as identified by Dr. Richard Gardner (1985, 1998). Each manifestation
is independently scored on a 3-point severity scale (mild / moderate / severe).

| # | Manifestation | Description | Evidence Types |
|---|---------------|-------------|----------------|
| 1 | Campaign of denigration | Child participates in denigrating the targeted parent | Texts, emails, recordings of child's statements |
| 2 | Weak or frivolous rationalizations | Child gives absurd or trivial reasons for hostility | Deposition testimony, FOC interview notes |
| 3 | Lack of ambivalence | Child expresses only negative feelings toward targeted parent | Therapist notes, GAL reports |
| 4 | Independent-thinker phenomenon | Child claims alienation is entirely their own idea | Interview transcripts, child's statements |
| 5 | Reflexive support of alienating parent | Child automatically sides with alienating parent in all disputes | Communication records, witness statements |
| 6 | Absence of guilt | Child shows no guilt for exploitation or cruelty toward targeted parent | Behavioral observations, therapist records |
| 7 | Borrowed scenarios | Child uses phrases or describes events clearly coached by alienating parent | Comparison of parent's language to child's statements |
| 8 | Spread to extended family | Hostility extends to targeted parent's entire family and social circle | Communication records, party invitations, family event exclusions |

### Severity Scoring

```
Mild:     Isolated incidents, child shows some ambivalence
          Score: 1 per manifestation
Moderate: Pattern of behavior, child increasingly rigid
          Score: 2 per manifestation
Severe:   Entrenched behavior, child refuses all contact
          Score: 3 per manifestation

Total Score Range: 0-24
  0-4:   No significant alienation
  5-10:  Mild alienation indicators
  11-16: Moderate alienation — court intervention warranted
  17-24: Severe alienation — emergency intervention required
```

## Michigan Legal Framework

### MCL 722.23 — Best Interest Factors

Factor (j) is the primary statutory basis for alienation claims:

> **(j)** The willingness and ability of each of the parties to facilitate
> and encourage a close and continuing parent-child relationship between
> the child and the other parent or the child and the parents. A court
> may not consider negatively for the purposes of this factor any
> reasonable action taken by a parent to protect a child or that parent
> from sexual assault or domestic violence by the child's other parent.

**Scoring Factor (j):**

| Behavior | Score Impact | Evidence Required |
|----------|-------------|-------------------|
| Encouraging contact with other parent | +2 Favors parent | Communication records showing facilitation |
| Neutral compliance with court orders | 0 Neutral | Parenting time logs |
| Passive interference (scheduling conflicts) | -1 Against parent | Calendar records, missed exchanges |
| Active obstruction (withholding child) | -2 Against parent | Police reports, contempt filings |
| Campaign of alienation | -3 Strongly against | Pattern evidence across multiple manifestations |

### Related Statutes and Rules

| Authority | Subject | Application |
|-----------|---------|-------------|
| MCL 722.23(j) | Willingness to facilitate parent-child relationship | Primary alienation factor |
| MCL 722.27(1)(c) | Change of custody upon proper cause or change of circumstances | Basis for custody modification |
| MCL 722.27a | Parenting time — best interest standard | Parenting time interference |
| MCL 722.25 | Custody to third party | When both parents engage in alienation |
| MCR 3.210 | Custody proceedings generally | Procedural requirements |
| MCR 3.218 | Friend of Court — recommendations and objections | FOC investigation of alienation |

### Key Michigan Case Law

| Case | Holding | Application |
|------|---------|-------------|
| Vodvarka v Grasmeyer, 259 Mich App 499 (2003) | Change of circumstances must be significant and of a lasting nature | Standard for custody modification based on alienation |
| Shade v Wright, 291 Mich App 17 (2010) | Factor (j) is one of many; courts must consider all 12 factors | Prevents over-reliance on alienation alone |
| Pierron v Pierron, 486 Mich 81 (2010) | Clear and convincing evidence required to change established custodial environment | Burden of proof when alienation disrupts custody |
| Brown v Loveman, 260 Mich App 576 (2004) | Court may order therapy to address alienation | Remedy for moderate alienation |
| Berger v Berger, 277 Mich App 700 (2008) | Custody change warranted when alienation harms child | Severe alienation justifying custody transfer |

## Evidence Collection Protocol

### Phase 1: Pattern Identification

1. **Communication Scan** — Review all text messages, emails, and social media
   for denigrating language, scheduling interference, or coaching indicators.
2. **Timeline Construction** — Build chronological timeline of alienation events
   with date, description, manifestation number, and evidence reference.
3. **Frequency Analysis** — Calculate alienation events per month to establish
   escalation or de-escalation patterns.
4. **Cross-Reference** — Link each event to Gardner manifestation(s) and
   MCL 722.23 factor(j) scoring criteria.

### Phase 2: Documentation

```sql
-- Query alienation indicators from litigation_context.db
SELECT
    ai.indicator_id,
    ai.event_date,
    ai.gardner_manifestation,
    ai.severity,
    ai.description,
    ai.evidence_refs,
    ai.lane
FROM alienation_indicators ai
WHERE ai.lane = 'A'
ORDER BY ai.event_date ASC;
```

### Phase 3: Court-Ready Report Generation

Output format for alienation analysis report:

1. **Executive Summary** — Overall alienation severity score and recommendation
2. **Gardner Manifestation Scores** — Table of all 8 manifestations with evidence
3. **Temporal Pattern Chart** — Monthly frequency of alienation events
4. **Factor (j) Impact Analysis** — How alienation affects each party's score
5. **Evidence Index** — All supporting documents with Bates numbers
6. **Recommended Interventions** — Therapy, custody modification, contempt

## Counter-Narrative Preparation

When the opposing party alleges alienation against the Plaintiff:

1. **Document facilitation efforts** — Every instance of encouraging contact,
   complying with parenting time, attending co-parenting therapy.
2. **Identify legitimate concerns** — Distinguish protective behavior from
   alienation (MCL 722.23(j) safe-harbor for protection from DV/SA).
3. **Challenge methodology** — Gardner's PAS is not in DSM-5; challenge
   admissibility of pure PAS testimony if opposing expert relies on it.
4. **Reframe behaviors** — Show that child's reluctance stems from the
   other parent's behavior, not alienation coaching.

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS alienation_indicators (
    indicator_id   TEXT PRIMARY KEY,
    event_date     TEXT NOT NULL,
    gardner_manifestation INTEGER CHECK(gardner_manifestation BETWEEN 1 AND 8),
    severity       TEXT CHECK(severity IN ('mild', 'moderate', 'severe')),
    description    TEXT NOT NULL,
    evidence_refs  TEXT,  -- JSON array of evidence IDs
    accused_party  TEXT DEFAULT 'Emily A. Watson',
    child_initials TEXT DEFAULT 'L.D.W.',
    lane           TEXT DEFAULT 'A',
    case_number    TEXT DEFAULT '2024-001507-DC',
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alienation_date
    ON alienation_indicators(event_date);
CREATE INDEX IF NOT EXISTS idx_alienation_manifestation
    ON alienation_indicators(gardner_manifestation, severity);
```

## Integration

### Companion Skills

- [litigation-custody-specialist](skill://litigation-custody-specialist) — Full 12-factor analysis
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Evidence collection
- [litigation-impeachment-engine](skill://litigation-impeachment-engine) — Contradiction detection
- [litigation-witness-preparation](skill://litigation-witness-preparation) — Testimony prep
- [litigation-harm-quantifier](skill://litigation-harm-quantifier) — Emotional harm from alienation

### Companion Agents

- `parental-alienation-detector` — Automated scan and report generation
- `evidence-authentication` — Authenticate alienation evidence exhibits

### Python Module

- `00_SYSTEM/legal_ai/parental_alienation_detector.py` — Computational engine

## Fabrication Warnings

- **DO NOT** fabricate alienation incidents or evidence references.
- **DO NOT** invent case citations — only use verified Michigan case law.
- **DO NOT** overstate severity scores without supporting evidence.
- **DO NOT** apply Gardner criteria mechanically — context matters.
- **DO NOT** use "Emily Ann" or "Emily M." — defendant's legal name is Emily A. Watson.
- **ALWAYS** use L.D.W. for the child per MCR 8.119(H).
- **ALWAYS** spell Judge McNeill with TWO L's: Jenny L. McNeill.

## Output Format

When presenting alienation analysis, structure as:

```markdown
## Parental Alienation Analysis — [Case Number]

### Overall Score: [X]/24 — [Severity Level]

| Manifestation | Score | Key Evidence |
|---------------|-------|-------------|
| 1. Campaign of denigration | [0-3] | [Evidence ref] |
| 2. Weak rationalizations | [0-3] | [Evidence ref] |
| ... | ... | ... |

### Factor (j) Assessment
[Narrative analysis of willingness to facilitate]

### Recommended Actions
1. [Action item with legal basis]
2. [Action item with legal basis]
```


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
**MCR:** MCR 3.210, MCR 3.215
**MCL:** MCL 722.23(j), MCL 722.27, MCL 722.27a
**Binding Cases:**
- *Demski v Petlick, 309 Mich App 404*
- *Brown v Loveman, 260 Mich App 576*
- *Shade v Wright, 291 Mich App 17*

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
