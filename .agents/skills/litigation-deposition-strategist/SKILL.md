---
name: litigation-deposition-strategist
description: "Deposition preparation and execution specialist for Michigan family law. Use when: deposition prep, witness questioning, deposition notice, impeachment material, cross-examination plan, deposition summary."
---

# Litigation Deposition Strategist

**Role**: Expert deposition preparation and execution specialist for Michigan family law litigation (Pigors v. Watson). Handles witness profiling, question bank generation, deposition notice compliance, impeachment material organization, real-time objection guidance, and deposition-to-trial evidence mapping across all 6 case lanes.

## Capabilities

- Witness profiling with multi-factor credibility scoring (bias, consistency, corroboration, demeanor)
- Question bank generation for direct, cross, and impeachment examination
- Deposition notice preparation per MCR 2.306 (30-day notice requirement for parties)
- Impeachment material organization (prior inconsistent statements, records vs. testimony)
- Real-time objection guidance per Michigan Rules of Evidence (MRE)
- Deposition summary generation with key testimony extraction
- Deposition-to-trial evidence mapping per MCR 2.308
- Subpoena preparation for non-party witnesses per MCR 2.307
- Video deposition coordination per MCR 2.315

## Requirements

- Access to `litigation_context.db` for witness records and exhibit cross-references
- Lane assignment (A-F) for each deposition — never cross-contaminate lanes
- Prior filings and discovery responses loaded for impeachment material
- MANBEARPIG inference engine for credibility scoring
- Python 3.12+ with `legal_ai` package installed

## Patterns

### Pattern 1: Witness Credibility Profile Generation

**When to use**: Before scheduling any deposition, build a credibility profile to guide question strategy.

```python
from legal_ai.witnesses import CredibilityProfile

def build_witness_profile(witness_name: str, lane: str) -> dict:
    """Build a multi-factor credibility profile for a deposition witness."""
    profile = CredibilityProfile(
        witness_name=witness_name,
        lane=lane,
        factors={
            "bias_indicators": [],       # Relationship to parties, financial interest
            "internal_consistency": 0.0,  # 0-1 score from prior statement analysis
            "corroboration_rate": 0.0,    # % of claims backed by independent evidence
            "demeanor_markers": [],       # From prior hearing transcripts
            "impeachment_material": [],   # Prior inconsistent statements with exhibit refs
        }
    )
    # Score each factor against existing evidence
    profile.score_bias(db_path="litigation_context.db")
    profile.score_consistency(prior_statements=get_prior_statements(witness_name))
    profile.score_corroboration(evidence_pool=get_lane_evidence(lane))
    return profile.to_dict()
```

### Pattern 2: MCR 2.306 Compliant Deposition Notice

**When to use**: When scheduling a deposition — ensures compliance with Michigan 30-day notice rules.

```python
from legal_ai.discovery import DepositionNotice
from datetime import datetime, timedelta

def prepare_deposition_notice(
    deponent: str,
    is_party: bool,
    case_number: str,
    lane: str,
) -> dict:
    """Generate MCR 2.306 compliant deposition notice."""
    notice = DepositionNotice(
        case_number=case_number,
        plaintiff="Andrew James Pigors",
        deponent=deponent,
        is_party=is_party,
        # MCR 2.306(B): 30-day notice to parties (14 days if stipulated)
        notice_days=30 if is_party else 14,
        # MCR 2.306(D): reasonable time and place
        location="Muskegon County Courthouse or agreed location",
        # MCR 2.307: subpoena required for non-parties
        requires_subpoena=not is_party,
        lane=lane,
    )
    notice.validate_service_deadline()
    notice.generate_proof_of_service()
    return notice.render()
```

### Pattern 3: Impeachment Cross-Examination Builder

**When to use**: After gathering prior statements, build a cross-examination sequence that locks the witness into positions before revealing contradictions.

```python
def build_impeachment_sequence(witness: str, prior_statements: list) -> list:
    """
    Build a 3-step impeachment sequence per MRE 613:
    1. Commit — lock witness into current testimony
    2. Credit — establish reliability of prior statement source
    3. Confront — present the prior inconsistent statement
    """
    sequences = []
    for stmt in prior_statements:
        sequences.append({
            "step_1_commit": f"You testified today that {stmt['current_position']}, correct?",
            "step_2_credit": f"You previously {stmt['context']} on {stmt['date']}, correct?",
            "step_3_confront": f"Isn't it true you stated: '{stmt['prior_text']}'?",
            "exhibit_ref": stmt["exhibit_id"],
            "mre_basis": "MRE 613(b) — extrinsic evidence of prior inconsistent statement",
            "impeachment_value": stmt["contradiction_severity"],  # 1-10 scale
        })
    # Sort by impeachment value — save strongest for last
    return sorted(sequences, key=lambda x: x["impeachment_value"])
```

### Pattern 4: Deposition Summary with Key Testimony Extraction

**When to use**: After completing a deposition — generate a structured summary for trial preparation and motion support.

```python
def generate_deposition_summary(
    deponent: str,
    transcript_pages: list,
    lane: str,
) -> dict:
    """
    Extract key testimony from deposition transcript for trial use.
    Organize by: admissions, impeachment material, favorable testimony,
    harmful testimony, and exhibits referenced.
    """
    summary = {
        "deponent": deponent,
        "lane": lane,
        "date": None,  # Populated from transcript header
        "total_pages": len(transcript_pages),
        "key_admissions": [],        # Statements favorable to Andrew
        "impeachment_material": [],  # Prior inconsistent statements
        "favorable_testimony": [],   # Testimony supporting Andrew's claims
        "harmful_testimony": [],     # Testimony that hurts Andrew's case
        "exhibits_referenced": [],   # Exhibits marked during deposition
        "objections_lodged": [],     # Objections on record (preserved for trial)
        "follow_up_needed": [],      # Areas requiring additional discovery
        "trial_use_classification": {
            "mcr_2_308_a1": [],  # Impeachment of live witness
            "mcr_2_308_a2": [],  # Admission of party-opponent
            "mcr_2_308_a3": [],  # Unavailable witness
        },
    }
    for page in transcript_pages:
        classify_testimony_segment(page, summary)
    return summary


def classify_testimony_segment(page: dict, summary: dict) -> None:
    """Classify each page/segment into the appropriate summary bucket."""
    if page.get("is_admission"):
        summary["key_admissions"].append({
            "page_line": f"{page['page']}:{page['line']}",
            "text": page["text"],
            "topic": page["topic"],
        })
    if page.get("contradicts_prior"):
        summary["impeachment_material"].append({
            "page_line": f"{page['page']}:{page['line']}",
            "current_statement": page["text"],
            "prior_statement": page["prior_text"],
            "prior_source": page["prior_source"],
            "mre_basis": "MRE 613(b)",
        })
```

### Pattern 5: Objection Quick-Reference for Depositions

**When to use**: During deposition preparation — build a quick-reference card of common objections and their MRE basis.

```python
DEPOSITION_OBJECTIONS = {
    "form": {
        "mre_basis": "MRE 611(a)",
        "grounds": [
            "Compound question — asks two things at once",
            "Assumes facts not in evidence",
            "Argumentative — argues rather than asks",
            "Vague and ambiguous — unclear what is being asked",
            "Leading on direct (only if examining own witness)",
            "Calls for narrative — overly broad",
            "Mischaracterizes prior testimony",
        ],
        "note": "Form objections MUST be made at deposition or they are WAIVED (MCR 2.306(D)(3))",
    },
    "substantive": {
        "mre_basis": "Various MRE",
        "grounds": [
            "Relevance — MRE 401/402",
            "Hearsay — MRE 801/802 (state exception if applicable)",
            "Privilege — attorney-client, spousal, therapist-patient",
            "Work product — MCR 2.302(B)(3)",
            "Beyond scope of discovery — MCR 2.302(B)(1)",
        ],
        "note": "Substantive objections are PRESERVED without stating at deposition (MCR 2.306(D)(3))",
    },
    "instruction_not_to_answer": {
        "mre_basis": "MCR 2.306(D)(4)",
        "grounds": [
            "Privilege (attorney-client, etc.)",
            "Court-ordered limitation on discovery",
            "To present motion to terminate/limit under MCR 2.306(D)(4)",
        ],
        "note": "Instruction not to answer is LIMITED to these three grounds only",
    },
}
```

## Anti-Patterns

### ❌ Asking Compound Questions During Cross-Examination

**Why bad**: Compound questions let the witness choose which part to answer, escaping impeachment traps. Michigan courts sustain objections to compound questions, wasting precious deposition time.

**Instead**: One fact per question. Each question should be answerable with "yes" or "no." Build the impeachment incrementally — commit, credit, confront — one step at a time.

### ❌ Failing to Serve Deposition Notice on All Parties

**Why bad**: MCR 2.306(B) requires reasonable notice to **every party**, not just the deponent. Missing service on co-defendants invalidates the deposition for trial use per MCR 2.308.

**Instead**: Generate a service list from all active parties across all lanes. Use `litigation-service-engine` to track service completion for every party before the deposition date.

### ❌ Using Deposition Testimony at Trial Without Foundation

**Why bad**: MCR 2.308(A) limits trial use of depositions. You must establish the deponent is unavailable, or use it only for impeachment of a live witness. Reading deposition testimony without proper foundation draws a sustained objection and jury instruction to disregard.

**Instead**: Always classify deposition excerpts by trial-use category: (1) impeachment of live witness per MCR 2.308(A)(1), (2) admission of party-opponent per MRE 801(d)(2), (3) unavailable witness per MCR 2.308(A)(3) with proof of unavailability.

### ❌ Waiving Form Objections by Silence

**Why bad**: MCR 2.306(D)(3) distinguishes between form objections (waived if not raised at deposition) and substantive objections (preserved automatically). Failing to object to a compound or leading question at the deposition means you cannot object at trial when the transcript is read. Many pro se litigants lose admissible impeachment material because they stayed silent during deposition.

**Instead**: Prepare an objection quick-reference card (Pattern 5) before every deposition. Object to form defects immediately and concisely: "Objection — compound" or "Objection — leading." Do not argue the objection — state the basis and move on. Substantive objections (relevance, hearsay, privilege) are preserved without stating them at deposition.

## Michigan-Specific Rules

- **MCR 2.306**: Deposition upon oral examination — 30-day notice to parties, reasonable time/place, scope per MCR 2.302(B)
- **MCR 2.306(D)(4)**: Deposition limited to 7 hours per day unless court orders otherwise
- **MCR 2.307**: Subpoena for non-party deponents — must be served per MCR 2.105
- **MCR 2.308**: Use of depositions at trial — impeachment, party-opponent, unavailable witness
- **MCR 2.309**: Depositions before action or pending appeal
- **MCR 2.310**: Written depositions (interrogatories on written questions)
- **MCR 2.315**: Video depositions — notice must specify video, copy provided to all parties
- **MRE 613**: Prior inconsistent statements — (a) examining witness, (b) extrinsic evidence
- **MRE 801(d)(1)**: Prior statement by witness — not hearsay if inconsistent under oath
- **MRE 801(d)(2)**: Admission by party-opponent — always admissible, no hearsay objection
- **MRE 611(b)**: Scope of cross-examination — limited to subject matter of direct + credibility
- **MCR 8.119(H)**: Minor children referenced by initials only (L.D.W.)

## Integration Points

- **litigation-impeachment-engine**: Receives impeachment material packages; feeds contradiction data back to deposition strategy
- **litigation-witness-preparation**: Shares witness profiles; coordinates direct examination outlines with deposition testimony
- **litigation-evidence-harvester**: Pulls exhibits, records, and prior statements used in deposition question banks
- **litigation-service-engine**: Tracks service of deposition notices to all parties
- **litigation-timeline-forensics**: Provides chronological event data for time-based deposition questions
- **litigation-custody-specialist**: Supplies best-interest-factor analysis for custody-related depositions (Lane A/D)
- **MANBEARPIG inference engine**: Powers credibility scoring and contradiction detection


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
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

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
