---
name: litigation-brief-writer
description: >-
  Use when drafting, structuring, or refining any legal brief, motion, response, or
  memorandum of law for Michigan state or federal court — providing argument architecture
  frameworks, persuasion techniques, and court-grade legal prose patterns.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: brief, argument, persuasion, writing, legal writing
---
# LITIGATION-BRIEF-WRITER

## Metadata

- **name**: litigation-brief-writer
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-claims-analyzer, litigation-harm-quantifier

## Description

Use when drafting, structuring, or refining any legal brief, motion, response, or memorandum of law for Michigan state or federal court. This skill provides argument architecture frameworks (IRAC/CREAC/TEC), persuasion techniques validated by appellate practice, Michigan-specific formatting and style requirements, and court-grade legal prose patterns. It transforms raw legal analysis into compelling, properly structured court filings that meet Michigan Court Rules and local practice standards. Specifically tuned for pro se filings where clarity and professionalism are critical to overcoming judicial skepticism.

## Triggers

- User needs to draft a motion, brief, response, or memorandum of law
- User asks how to structure legal arguments or organize a filing
- User wants to improve the persuasiveness or clarity of a legal document
- User needs Michigan-specific formatting, caption, or style guidance
- User is writing argument sections, statement of facts, or relief prayers
- User asks about IRAC, CREAC, or legal writing structure
- User needs to weave authority (cases, statutes, rules) into argument prose

## Argument Architecture Framework

### The Three Structures

Every legal argument in this case should use one of three validated structures, selected by context:

#### 1. IRAC (Issue-Rule-Application-Conclusion)
**Best for**: Simple motions, single-issue arguments, procedural matters

```
I — Issue:       Frame the specific legal question the court must answer
R — Rule:        State the governing legal standard with authority
A — Application: Apply the rule to the specific facts of Pigors v Watson
C — Conclusion:  State the result the court should reach
```

#### 2. CREAC (Conclusion-Rule-Explanation-Application-Conclusion)
**Best for**: Complex motions, multi-factor tests, dispositive motions

```
C — Conclusion:    State your position upfront (thesis sentence)
R — Rule:          Articulate the legal standard with full authority chain
E — Explanation:   Show how courts have applied this rule in analogous cases
A — Application:   Apply to Pigors v Watson facts with record citations
C — Conclusion:    Restate conclusion with specific relief requested
```

#### 3. TEC (Theme-Evidence-Conclusion)
**Best for**: Statement of facts, narrative sections, equity arguments

```
T — Theme:      Establish the narrative frame (what this case is really about)
E — Evidence:   Marshal facts in thematic order with record citations
C — Conclusion: Draw the factual inference that supports your legal theory
```

### Structure Selection Matrix

| Filing Type | Primary Structure | Secondary | Notes |
|---|---|---|---|
| Motion to Dismiss | CREAC | IRAC per element | Lead with strongest argument |
| Motion for Summary Judgment | CREAC | TEC for facts | Facts section is critical |
| Response to Motion | IRAC per point | CREAC for main defense | Mirror opponent's structure |
| Emergency Motion | IRAC (concise) | — | Brevity is persuasion |
| Trial Brief | TEC + CREAC | — | Narrative + law interleaved |
| Appellate Brief | CREAC | TEC for fact statement | Standard of review is key |
| § 1983 Complaint | TEC (story) | IRAC per count | Tell the constitutional story |

## Heading Hierarchy

Michigan briefs should use a clear hierarchical heading structure:

```
I.   ROMAN NUMERAL — Major Argument Sections
     A.  Capital Letter — Sub-Arguments
         1.  Arabic Numeral — Supporting Points
             a.  Lowercase Letter — Sub-Points (rarely needed)
```

**Heading Style Rules:**
- Major headings: ALL CAPS, BOLD, CENTERED
- Sub-headings: Title Case, Bold, Left-Aligned
- Point headings: Sentence case, bold or italic, left-aligned
- Every heading should be a complete persuasive sentence (not just a topic label)

**Bad heading**: "Standard of Review"
**Good heading**: "This Court Reviews the Trial Court's Custody Determination for an Abuse of Discretion"

## Argument Flow Principles

### 1. Front-Load Strength
Place your strongest argument first. Michigan appellate courts consistently note they give greatest attention to the first argument presented. Reserve your second-strongest argument for last (recency effect).

### 2. One Argument Per Section
Each Roman numeral section should advance exactly one legal argument. If you're making three arguments for why a motion should be granted, use three sections (I, II, III), not one section with three subsections.

### 3. Fact Integration
Never present facts without legal significance. Every factual assertion in the argument section should connect to a legal element:

**Weak**: "On March 15, 2025, Defendant failed to return the children at 6:00 PM."
**Strong**: "Defendant's failure to return the children at the court-ordered 6:00 PM exchange time on March 15, 2025, constitutes willful contempt of the January 10, 2025 custody order. (Ex. A, Custody Order ¶ 4; Ex. B, Text Messages.)"

### 4. Authority Weaving
Integrate authority into the prose flow rather than dropping block quotes:

**Weak**: The court stated: "[long block quote]." This applies here because...
**Strong**: Michigan courts require a showing of "proper cause or change of circumstances" before modifying custody. MCL 722.27(1)(c); Vodvarka v Grasmeyer, 259 Mich App 499, 508 (2003). Here, Defendant's documented pattern of [specific conduct] constitutes precisely the type of changed circumstance that...

### 5. Transition Logic
Every paragraph must logically connect to the next. Use these transition patterns:

| Pattern | Example Opener |
|---|---|
| Building | "Moreover, ..." / "Additionally, ..." |
| Contrasting | "Despite this, ..." / "Notwithstanding ..." |
| Causation | "As a result, ..." / "Consequently, ..." |
| Concession | "Although Defendant may argue ..., this fails because ..." |
| Temporal | "Following the court's order, ..." / "Subsequently, ..." |
| Emphasis | "Critically, ..." / "Most significantly, ..." |

## Persuasion Techniques

This skill integrates 15 validated legal persuasion techniques. See `references/persuasion-techniques.md` for the complete catalog. Key techniques for Pigors v Watson:

### Primacy and Recency
- First and last impressions dominate judicial memory
- Open every brief with your strongest theme; close with your ask

### Rule of Three
- Group arguments, examples, and facts in threes
- "Defendant interfered with parenting time, alienated the children, and defied court orders"

### Anchoring
- Set the damages number high early; every subsequent number feels reasonable by comparison
- In damages sections, lead with total aggregate before breaking down

### Framing
- Frame issues in terms that favor your position before the legal analysis begins
- "The question is not whether Defendant had reasons, but whether the court's order was followed"

### Narrative
- Courts remember stories, not syllogisms
- Statement of Facts should read like a compelling narrative, not a chronology

### Concession-and-Refute
- Acknowledge the opponent's strongest point, then demonstrate why it fails
- Builds credibility and eliminates the court's concern in advance

## Brief Components Checklist

Every Michigan brief/motion should include these components in order:

```
□  Caption (MCR 2.113 compliant)
□  Table of Contents (if > 10 pages)
□  Table of Authorities (if > 10 pages)
□  Introduction / Summary of Argument (1 page max)
□  Statement of Facts (with record citations)
□  Statement of Issues Presented (appellate briefs)
□  Standard of Review (if applicable)
□  Argument (CREAC/IRAC structured)
□  Relief Requested (specific, itemized)
□  Signature Block (pro se format)
□  Certificate of Service
□  Verification (if required — MCR 2.114)
□  Proposed Order (attached as exhibit)
□  Index of Exhibits
```

## Pro Se Writing Considerations

### Credibility Through Professionalism
As a pro se litigant, the quality of your writing is your first impression. Courts extend leniency on substance (Haines v Kerner) but professional presentation earns respect and attention.

### Tone Calibration
- **Never**: Angry, accusatory, personal attacks on opposing counsel/judge
- **Always**: Measured, factual, respectful, focused on legal standards
- **Pro se advantage**: Direct, authentic voice without lawyer obfuscation; judges respond to genuine, well-organized presentations

### Length Discipline
- Emergency motions: 5–10 pages
- Standard motions: 10–20 pages
- Trial briefs: 20–35 pages
- Appellate briefs: MCR 7.212(B) — 50 pages or 16,000 words (COA)
- **Shorter is almost always better**. A 12-page motion that hits every point beats a 30-page motion that buries the lead.

### Self-Editing Checklist
```
□  Does every paragraph advance the argument? (Cut if not)
□  Is every factual claim supported by a citation to the record?
□  Is every legal claim supported by authority?
□  Have I addressed the opponent's best counterargument?
□  Does the relief section tell the court exactly what to do?
□  Would a non-lawyer understand the core argument?
□  Is the tone respectful throughout?
```

## Output Format

When drafting brief sections, always produce:

1. **Structural Outline**: Heading hierarchy with thesis sentences
2. **Draft Prose**: Court-ready text with citations
3. **Authority List**: All cases/statutes/rules cited with pinpoint cites
4. **Strength Assessment**: Rate each argument (Strong/Moderate/Weak) with reasoning

## Files

- `gotchas.md` — Anti-rationalization table for legal writing pitfalls
- `references/argument-architecture.md` — Complete IRAC/CREAC/TEC framework
- `references/persuasion-techniques.md` — 15 legal persuasion patterns
- `references/style-guide.md` — Michigan formatting and style requirements

## Related Skills

- [litigation-filing-architect](skill://litigation-filing-architect) — Architects court-ready filing packages
- [litigation-authority-validator](skill://litigation-authority-validator) — Validates citations and authority chains


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
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `michigan-litigation-writer` | Integration | Complementary analysis |
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
| Custody Modification | 65/100 | A,D,E,F | Verified |
| Emergency Custody | 55/100 | A,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,E,F | Verified |
| Contempt | 70/100 | A,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,D,E,F | Verified |
| Appeal Brief | 70/100 | A,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,D,E,F | Verified |

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

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

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
