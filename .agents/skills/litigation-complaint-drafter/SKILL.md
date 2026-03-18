---
name: litigation-complaint-drafter
description: >-
  Use when drafting a verified complaint, amending an existing complaint, or structuring
  individual counts for filing in Michigan circuit court under MCR 2.111, MCR 2.113, and
  related court rules.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: complaint, verified complaint, count, prayer, amended
---
# litigation-complaint-drafter

> **Category:** discipline
> **Tier:** 2
> **Jurisdiction:** Michigan — 14th Judicial Circuit, Muskegon County
> **Context:** Pigors v Watson, pro se litigation

## Description

Use when drafting a verified complaint, amending an existing complaint, or structuring individual counts for filing in Michigan circuit court under MCR 2.111, MCR 2.113, and related court rules.

## Triggers

- User needs to draft a new verified complaint from scratch
- User needs to add counts to an existing complaint
- User needs to structure factual allegations into numbered paragraphs
- User asks about complaint formatting, caption requirements, or verification language
- User needs to amend a previously filed complaint under MCR 2.118
- User needs cross-claim, counterclaim, or third-party complaint structure

## Complaint Generation Protocol

### Phase 1 — Pre-Drafting Checklist
Before writing a single word, verify:

- [ ] All defendants properly identified with full legal names
- [ ] Defendant capacity confirmed (individual, corporate, LLC, government)
- [ ] Jurisdiction basis identified (subject matter + personal)
- [ ] Venue confirmed under MCR 2.221-2.226
- [ ] All viable causes of action identified (cross-reference Skill 22)
- [ ] Elements for each count mapped to specific facts
- [ ] Evidence for each element identified
- [ ] SOL verified for each count
- [ ] Remedies identified per count (cross-reference remedies-matrix.md)

### Phase 2 — Section-by-Section Drafting

Draft each section in order. Do NOT proceed to the next section until the current section passes its quality gate.

#### Section 1: Caption (MCR 2.113)
```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
14TH JUDICIAL CIRCUIT

[PLAINTIFF NAME],
        Plaintiff,                    Case No. ____________

v.                                    Hon. _______________

[DEFENDANT NAME(S)],
        Defendant(s).
________________________________________/
```

**Quality Gate:** Caption includes court name, county, circuit number, all party names, case number line, judge line, separator.

#### Section 2: Introduction / Parties
Numbered paragraphs identifying:
- Each plaintiff (name, address, capacity)
- Each defendant (name, address, capacity, registered agent if entity)
- Relationships between parties relevant to claims

**Quality Gate:** Every party identified. Entity defendants include state of incorporation/organization. Pro se plaintiff includes address.

#### Section 3: Jurisdiction and Venue
- Subject matter jurisdiction: MCL 600.605 (circuit court general jurisdiction)
- Personal jurisdiction: MCR 2.105 (manner of service establishing jurisdiction)
- Venue: MCR 2.221 (county where cause of action arose or defendant resides)
- Amount in controversy exceeds $25,000 (circuit court minimum)

**Quality Gate:** Jurisdiction and venue each have specific statutory/rule citations. Amount in controversy stated.

#### Section 4: General Allegations / Factual Background
Chronological factual narrative in numbered paragraphs. Rules:
- One fact per paragraph (MCR 2.111(A)(1) — "short and plain statement")
- Date-stamp every event
- Name every actor
- Attach or reference documentary evidence
- Incorporate by reference into all subsequent counts

**Quality Gate:** Every material fact has a date. No legal conclusions in fact section. No argument. Exhibits referenced.

#### Section 5: Individual Counts
Each count is a separate section:
```
COUNT [N] — [CAUSE OF ACTION]
(Against Defendant [Name])

[Incorporation paragraph]
[Element-by-element allegations]
[Damage allegations specific to this count]
[Prayer specific to this count]
```

**Quality Gate per count:**
- [ ] Incorporation by reference paragraph
- [ ] Each element of the cause of action is alleged in a separate paragraph
- [ ] Each element paragraph connects to specific fact paragraphs
- [ ] Damages specific to this count are alleged
- [ ] Individual prayer for relief

#### Section 6: Prayer for Relief
Two parts:
1. **Per-count prayer** (at the end of each count)
2. **General prayer** (after all counts):
   - Compensatory damages in excess of $25,000
   - All statutory enhancements (treble, double)
   - Attorney fees where authorized by statute
   - Pre-judgment and post-judgment interest
   - Costs and disbursements
   - Injunctive/declaratory relief (if applicable)
   - "Such other and further relief as this Court deems just and equitable"

**Quality Gate:** Prayer covers every remedy available for every count. No remedy claimed without statutory/legal basis.

#### Section 7: Verification
```
VERIFICATION

I, [Plaintiff Name], declare under the penalty of perjury
that the statements in the foregoing Verified Complaint are
true to the best of my knowledge, information, and belief.

Date: ________________     ____________________________
                           [Plaintiff Name], Pro Se
                           [Address]
                           [Phone]
                           [Email]
```

**Quality Gate:** Verification is under penalty of perjury. Plaintiff's name, address, phone, email included. Date line present.

#### Section 8: Exhibit List
```
EXHIBIT LIST

Exhibit A — [Description]
Exhibit B — [Description]
...
```

**Quality Gate:** Every document referenced in the complaint appears in the exhibit list. Exhibits are in order of first reference.

### Phase 3 — Final Review Checklist

- [ ] All paragraphs consecutively numbered throughout entire complaint
- [ ] Each count incorporates prior paragraphs by reference
- [ ] No element of any cause of action is missing
- [ ] Fraud counts pled with particularity (MCR 2.112(B)(1))
- [ ] Special damages specifically pled (MCR 2.112(A))
- [ ] Caption matches all named parties
- [ ] Verification signed and dated
- [ ] Exhibit list matches body references

## Formatting Rules (MCR 2.113)

- Paper size: 8½ × 11 inches
- Margins: 1 inch minimum
- Font: legible, 12-point minimum (Times New Roman or similar)
- Line spacing: double-spaced body text
- Paragraph numbering: consecutive Arabic numerals
- Page numbering: bottom center

## Cross-References

- **Skill 22** (litigation-cause-of-action-library): Elements and remedies for each count
- **Skill 24** (litigation-claim-researcher): Fact-to-claim mapping before drafting
- **Skill 25** (litigation-service-engine): Service after filing

## Related Skills

- [litigation-cause-of-action-library](skill://litigation-cause-of-action-library) — References causes of action elements
- [litigation-service-engine](skill://litigation-service-engine) — Executes process service requirements


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
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
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
| Judicial Disqualification | 75/100 | E | Verified |
| JTC Formal Complaint | 75/100 | E | Verified |

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
