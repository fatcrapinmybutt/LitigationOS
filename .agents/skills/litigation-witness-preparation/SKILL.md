---
name: litigation-witness-preparation
description: "Witness credibility assessment and examination preparation for Michigan family law trials. Use when: prepare witness, credibility scoring, direct examination, cross-examination, expert witness, impeachment index, witness sequestration, character evidence."
---

# Litigation Witness Preparation

**Role**: Witness credibility assessment and examination preparation specialist for Michigan family law and civil rights trials (Pigors v. Watson). Builds comprehensive witness profiles with credibility scoring, generates examination outlines for direct, cross, and impeachment, manages expert witness qualification under Daubert/MRE 702, and applies Michigan-specific evidence rules (MRE 404-406, 601-615, 701-807).

## Capabilities

- Witness credibility scoring: bias indicators, internal consistency, corroboration rate, demeanor markers
- Direct examination outline generation with story arc structure (primacy-recency)
- Cross-examination question development with trap-setting methodology
- Impeachment material indexing: prior inconsistent statements cross-referenced to exhibits
- Expert witness qualification assessment per Daubert standard / MRE 702
- Witness sequestration planning per MRE 615
- Character evidence rules application per MRE 404/405
- Habit evidence application per MRE 406
- Rehabilitation techniques for impeached witnesses
- Witness preparation checklists and mock examination outlines
- Hearsay exception identification for witness testimony per MRE 801-807

## Requirements

- Access to `litigation_context.db` for prior testimony, deposition transcripts, and exhibit records
- Lane assignment (A-F) for witness routing — custody witnesses differ from housing witnesses
- Prior inconsistent statements indexed by exhibit number
- MANBEARPIG inference engine for credibility scoring and consistency analysis
- Python 3.12+

## Patterns

### Pattern 1: Multi-Factor Credibility Scoring

**When to use**: Before any examination — assess each witness to prioritize preparation time and anticipate weaknesses.

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class WitnessProfile:
    name: str
    role: str  # party, fact_witness, expert, character
    lane: str
    called_by: str  # plaintiff or defendant

    # Credibility factors (each scored 0.0 to 1.0)
    bias_score: float = 0.0          # 0 = no bias, 1 = extreme bias
    consistency_score: float = 0.0    # 0 = highly inconsistent, 1 = perfectly consistent
    corroboration_score: float = 0.0  # 0 = no corroboration, 1 = fully corroborated
    demeanor_score: float = 0.0       # 0 = poor demeanor, 1 = excellent demeanor
    impeachment_risk: float = 0.0     # 0 = no material, 1 = devastating material exists

    prior_statements: List[dict] = field(default_factory=list)
    exhibits_referenced: List[str] = field(default_factory=list)

    @property
    def overall_credibility(self) -> float:
        """Weighted credibility score (higher = more credible)."""
        weights = {
            "consistency": 0.30,
            "corroboration": 0.25,
            "bias_inverse": 0.20,  # Inverse — lower bias = higher credibility
            "demeanor": 0.15,
            "impeachment_inverse": 0.10,
        }
        return (
            self.consistency_score * weights["consistency"]
            + self.corroboration_score * weights["corroboration"]
            + (1.0 - self.bias_score) * weights["bias_inverse"]
            + self.demeanor_score * weights["demeanor"]
            + (1.0 - self.impeachment_risk) * weights["impeachment_inverse"]
        )

    def assessment_summary(self) -> str:
        score = self.overall_credibility
        if score >= 0.8:
            return "HIGH credibility — strong witness, minimal impeachment exposure"
        elif score >= 0.5:
            return "MODERATE credibility — prepare for cross, address weak points proactively"
        else:
            return "LOW credibility — high impeachment risk, consider limiting testimony scope"


def build_witness_profile(
    name: str,
    role: str,
    lane: str,
    called_by: str,
    db_path: str = "litigation_context.db",
) -> WitnessProfile:
    """Build a complete witness profile from database records."""
    profile = WitnessProfile(name=name, role=role, lane=lane, called_by=called_by)

    # Score bias from relationship data
    profile.bias_score = score_witness_bias(name, db_path)
    # Score consistency from prior statements
    profile.consistency_score = score_statement_consistency(name, db_path)
    # Score corroboration from independent evidence
    profile.corroboration_score = score_corroboration(name, lane, db_path)
    # Assess impeachment exposure
    profile.impeachment_risk = assess_impeachment_risk(name, db_path)
    # Load prior statements for cross-reference
    profile.prior_statements = load_prior_statements(name, db_path)

    return profile
```

### Pattern 2: Direct Examination Outline with Story Arc

**When to use**: When preparing a witness for direct examination — structures testimony for maximum jury impact using primacy-recency ordering.

```python
def generate_direct_outline(
    witness: WitnessProfile,
    testimony_themes: list,
    key_exhibits: list,
) -> dict:
    """
    Generate a direct examination outline using primacy-recency structure:
    1. ANCHOR — strongest point first (primacy effect)
    2. CONTEXT — background and foundation
    3. NARRATIVE — chronological story with exhibit integration
    4. KEY POINT — most important evidence (recency effect)
    5. CLOSE — tie back to theme

    Rules for direct examination questions:
    - Open-ended (who, what, when, where, why, how)
    - No leading questions (MRE 611(c) prohibits leading on direct)
    - Let the witness tell the story
    """
    outline = {
        "witness": witness.name,
        "role": witness.role,
        "estimated_duration": "30-45 minutes",
        "sections": [
            {
                "section": "1. ANCHOR — Strongest Point First",
                "purpose": "Primacy effect — jury remembers what they hear first",
                "questions": [
                    f"Can you tell the court about {testimony_themes[0]['anchor_event']}?",
                ],
                "exhibit": testimony_themes[0].get("exhibit"),
                "note": "Open with your most powerful fact. Not chronological — impactful.",
            },
            {
                "section": "2. CONTEXT — Foundation",
                "purpose": "Establish witness credibility and relationship to case",
                "questions": [
                    "Please state your full name for the record.",
                    "How do you know the parties in this case?",
                    "How long have you been involved in these events?",
                ],
            },
            {
                "section": "3. NARRATIVE — Chronological Story",
                "purpose": "Walk through events with exhibit integration",
                "question_blocks": [
                    {
                        "theme": theme["description"],
                        "questions": theme["questions"],
                        "exhibits_to_introduce": theme.get("exhibits", []),
                    }
                    for theme in testimony_themes
                ],
            },
            {
                "section": "4. KEY POINT — Most Critical Evidence",
                "purpose": "Recency effect — jury remembers what they hear last",
                "questions": testimony_themes[-1].get("closing_questions", []),
                "exhibit": key_exhibits[-1] if key_exhibits else None,
            },
            {
                "section": "5. CLOSE",
                "purpose": "Tie testimony to case theme",
                "questions": ["Is there anything else you'd like the court to know?"],
            },
        ],
        "mre_notes": [
            "MRE 611(a) — court controls mode and order of witness examination",
            "MRE 611(c) — no leading questions on direct (except hostile witness)",
            "MRE 612 — if witness uses writing to refresh memory, opposing party may inspect it",
        ],
    }
    return outline
```

### Pattern 3: Cross-Examination Trap Sequence

**When to use**: When preparing to cross-examine an adverse witness — build controlled sequences that lock the witness before confronting with contradictions.

```python
def build_cross_examination_plan(
    witness: WitnessProfile,
    impeachment_targets: list,
) -> list:
    """
    Cross-examination structure:
    - Only leading questions (MRE 611(b)(c) — leading permitted on cross)
    - One fact per question
    - Never ask a question you don't know the answer to
    - Build toward impeachment in a 3-step sequence: Commit → Credit → Confront

    Target the weakest credibility factors first.
    """
    plan = []
    for target in impeachment_targets:
        sequence = {
            "topic": target["topic"],
            "impeachment_type": target["type"],  # prior_inconsistent, bias, character
            "steps": [],
        }

        if target["type"] == "prior_inconsistent":
            # MRE 613 impeachment sequence
            sequence["steps"] = [
                {
                    "phase": "COMMIT",
                    "question": f"You testified on direct that {target['current_claim']}, correct?",
                    "purpose": "Lock witness into current position under oath",
                },
                {
                    "phase": "CREDIT",
                    "question": f"You {target['prior_context']}, isn't that right?",
                    "purpose": "Establish the prior statement was reliable/serious",
                },
                {
                    "phase": "CONFRONT",
                    "question": f"Isn't it true that you stated: '{target['prior_statement']}'?",
                    "exhibit": target["exhibit_ref"],
                    "purpose": "Present the contradiction — let the jury see it",
                    "mre_basis": "MRE 613(b) — extrinsic evidence of prior inconsistent statement",
                },
            ]
        elif target["type"] == "bias":
            # Bias impeachment
            sequence["steps"] = [
                {
                    "phase": "ESTABLISH",
                    "question": f"You have a {target['relationship']} with the defendant, correct?",
                    "purpose": "Establish relationship that creates bias",
                },
                {
                    "phase": "MOTIVE",
                    "question": f"And {target['motive_fact']}, isn't that true?",
                    "purpose": "Show motive to shade testimony",
                },
            ]

        plan.append(sequence)

    return plan
```

## Anti-Patterns

### ❌ Asking Questions on Cross You Don't Know the Answer To

**Why bad**: Cross-examination is controlled presentation of YOUR facts through the opposing witness's mouth. Asking an open-ended question on cross invites the witness to explain, justify, and rehabilitate themselves. Every unexpected answer on cross hurts your case and helps theirs. This is the single most common trial mistake.

**Instead**: Every cross-examination question must be a leading question (statement ending with "correct?" or "isn't that true?") where you already know the answer from deposition testimony, exhibits, or prior statements. If you don't have impeachment material for a topic, skip it entirely on cross.

### ❌ Failing to Request Witness Sequestration

**Why bad**: MRE 615 gives parties the right to exclude witnesses from the courtroom during other witnesses' testimony. Failing to invoke this rule lets witnesses coordinate their stories in real-time. In family law cases with multiple witnesses from the same household, this is catastrophic.

**Instead**: File a motion in limine or make an oral request at trial start to invoke MRE 615 witness sequestration. Exceptions: (1) a party who is a natural person, (2) an officer/employee designated by a party, (3) a person whose presence is essential. Track which witnesses are subject to sequestration and which are exempt.

### ❌ Introducing Character Evidence Without Proper Foundation

**Why bad**: MRE 404(a) prohibits character evidence to prove action in conformity. Attempting to introduce "Emily is a bad person" evidence without fitting an exception results in a sustained objection and potential jury instruction to disregard. Repeated violations may draw sanctions.

**Instead**: Character evidence is admissible only through specific exceptions: MRE 404(a)(1) — pertinent character trait offered by accused; MRE 404(a)(2) — character of victim; MRE 404(b) — other acts for purpose other than propensity (motive, plan, identity, absence of mistake). In custody cases, MCL 722.23 best interest factors may open the door to character-like evidence through factor (f) moral fitness.

## Michigan-Specific Rules

- **MRE 601**: General competency of witnesses — every person is competent
- **MRE 602**: Personal knowledge requirement — witness must have firsthand knowledge
- **MRE 607**: Who may impeach — any party, including the party that called the witness
- **MRE 608**: Evidence of character for truthfulness — opinion/reputation only, not specific acts (except on cross)
- **MRE 611**: Mode and order of examination — (a) court control, (b) cross scope, (c) leading questions
- **MRE 612**: Writing used to refresh memory — opposing party may inspect
- **MRE 613**: Prior inconsistent statements — (a) examine witness, (b) extrinsic evidence
- **MRE 614**: Calling and interrogation by court — judge may call witnesses
- **MRE 615**: Exclusion of witnesses (sequestration) — on motion, court shall exclude
- **MRE 701**: Lay opinion testimony — rationally based on perception, helpful
- **MRE 702**: Expert testimony — Daubert standard (reliable principles, sufficient facts, reliable application)
- **MRE 703**: Bases of expert opinion — facts or data of a type reasonably relied upon
- **MRE 801-807**: Hearsay rules and exceptions — critical for testimony planning
- **MRE 404**: Character evidence — general prohibition with exceptions
- **MRE 405**: Methods of proving character — reputation or opinion; specific acts on cross
- **MRE 406**: Habit evidence — admissible to prove conduct on a particular occasion
- **MCL 722.23**: Best interest factors — witness testimony mapped to specific factors
- **MCR 8.119(H)**: Minor child referenced as L.D.W. only in all examination outlines

## Integration Points

- **litigation-deposition-strategist**: Shares witness profiles and question banks; deposition testimony feeds impeachment material
- **litigation-impeachment-engine**: Receives organized impeachment packages; returns contradiction severity scores
- **litigation-custody-specialist**: Provides best-interest-factor mapping for custody witness testimony
- **litigation-timeline-forensics**: Supplies chronological event data for witness statement verification
- **litigation-evidence-harvester**: Pulls exhibits and records referenced in examination outlines
- **litigation-motion-practice**: Motions in limine for witness sequestration and evidence exclusion
- **litigation-damages-calculator**: Witness testimony supporting damages elements
- **MANBEARPIG inference engine**: Powers credibility scoring, consistency analysis, and contradiction detection


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
| Custody Modification | 65/100 | A,B,D | Verified |
| Emergency Custody | 55/100 | A,B,D | Verified |
| PPO Modification/Termination | 60/100 | A,B,D | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D | Verified |
| Contempt | 70/100 | A,B,D | Verified |
| Default Judgment | 60/100 | A,B,D | Verified |
| TRO Application | 60/100 | A,B,D | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
