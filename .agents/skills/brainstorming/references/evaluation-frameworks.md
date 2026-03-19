# Evaluation Frameworks for Litigation Strategy

## Overview

Brainstorming produces ideas. Evaluation converts ideas into decisions.
Without structured evaluation, the loudest idea wins — not the best one.
These frameworks are adapted for litigation strategy where "best" means
legally sound, evidentially supported, procedurally compliant, and strategically optimal.

---

## Framework 1: Feasibility-Impact Matrix

Plot every brainstormed idea on a 2×2 matrix.

```
          HIGH IMPACT
              │
    Quick     │    Strategic
    Wins      │    Priorities
              │
  ────────────┼────────────── HIGH FEASIBILITY
              │
    Fill-ins  │    Major
    (Maybe)   │    Projects
              │
          LOW IMPACT
```

### Scoring Criteria (Litigation-Adapted)

**Impact Score (1-5)**:
| Score | Meaning | Example |
|-------|---------|---------|
| 5 | Case-dispositive | Disqualification granted, case reassigned |
| 4 | Significant advantage | Key evidence admitted, opposing motion denied |
| 3 | Moderate advantage | Favorable ruling on procedural issue |
| 2 | Minor advantage | Extended deadline, additional discovery |
| 1 | Negligible | Cosmetic improvement to filing |

**Feasibility Score (1-5)**:
| Score | Meaning | Example |
|-------|---------|---------|
| 5 | Ready now | Evidence in DB, authority verified, forms available |
| 4 | Minor gaps | Need 1-2 more evidence items, otherwise ready |
| 3 | Moderate effort | Need research, partial evidence, some forms |
| 2 | Significant effort | Major gaps in evidence or authority |
| 1 | Blocked | Missing critical prerequisites, deadline passed |

### Decision Rules
- **Score ≥ 4 Impact AND ≥ 4 Feasibility** → Execute immediately
- **Score ≥ 4 Impact AND < 4 Feasibility** → Plan and resource
- **Score < 4 Impact AND ≥ 4 Feasibility** → Execute if low cost
- **Score < 4 Impact AND < 4 Feasibility** → Deprioritize or discard

---

## Framework 2: Litigation Decision Matrix

A weighted multi-criteria evaluation for comparing filing strategies.

### Criteria (Weighted)
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Legal merit | 30% | Strength of legal authority (MCR, case law) |
| Evidence support | 25% | Quantity and quality of supporting evidence in DB |
| Strategic timing | 15% | How well this fits the current procedural posture |
| Risk exposure | 15% | Downside if the motion fails or backfires |
| Resource cost | 10% | Time, complexity, and effort to prepare |
| Precedent value | 5% | Whether success creates leverage for future filings |

### Scoring Template
```
| Strategy | Legal (30%) | Evidence (25%) | Timing (15%) | Risk (15%) | Cost (10%) | Precedent (5%) | TOTAL |
|----------|------------|----------------|-------------|-----------|-----------|---------------|-------|
| Option A |    4 (1.2) |       5 (1.25) |    3 (0.45) |  4 (0.60) |  3 (0.30) |      2 (0.10) |  3.90 |
| Option B |    5 (1.5) |       3 (0.75) |    4 (0.60) |  3 (0.45) |  4 (0.40) |      4 (0.20) |  3.90 |
| Option C |    3 (0.9) |       4 (1.00) |    5 (0.75) |  2 (0.30) |  5 (0.50) |      3 (0.15) |  3.60 |
```

### Tie-Breaking Rules
When scores are equal:
1. Higher Legal Merit wins (legal soundness is non-negotiable)
2. Higher Evidence Support wins (you can't file what you can't prove)
3. Lower Risk Exposure wins (minimize downside)

---

## Framework 3: Pre-Mortem Analysis

Before committing to a strategy, assume it has ALREADY FAILED. Then diagnose why.

### Process
1. State the strategy: "We will file a motion to disqualify under MCR 2.003"
2. Assume it's 30 days from now and the motion was DENIED
3. Each participant writes: "The motion failed because..."
4. Collect all failure reasons
5. Categorize: Preventable vs. Unpreventable
6. For each preventable failure: Add a mitigation step to the plan

### Common Failure Categories (Litigation)
| Category | Example Failures |
|----------|-----------------|
| **Procedural** | Wrong form, missed deadline, improper service |
| **Evidential** | Insufficient evidence, inadmissible evidence, evidence gaps |
| **Legal** | Wrong legal standard, superseded authority, inapplicable rule |
| **Strategic** | Bad timing, telegraphed strategy, judge's known preferences |
| **Tactical** | Opposing counsel's likely response not anticipated |

---

## Framework 4: OODA Loop (Observe-Orient-Decide-Act)

Fast-cycle evaluation for time-sensitive litigation decisions.

### Observe
- What just happened? (New ruling, filing, discovery)
- Query litigation_context.db for current state
- Check deadline_dashboard for urgency

### Orient
- How does this change our position?
- Map new information against existing strategy
- Identify which lane(s) are affected

### Decide
- Apply Feasibility-Impact Matrix (quick scoring)
- Select action with highest impact within deadline
- Document decision rationale

### Act
- Execute the chosen strategy
- Monitor for opponent's response
- Return to Observe

### When to Use OODA vs. Full Decision Matrix
- **OODA**: Emergency motions, short deadlines (< 7 days), reactive filings
- **Full Matrix**: Strategic planning, brief writing, appeal strategy

---

## Framework 5: Evidence Sufficiency Gate

Before any strategy passes evaluation, it MUST clear this gate.

### Gate Criteria
```
For each claim in the proposed strategy:
  □ Supporting evidence exists in litigation_context.db
    → Query: SELECT COUNT(*) FROM evidence_quotes WHERE claim_id = ?
    → Minimum: 3 independent evidence items per claim
  
  □ Evidence is admissible (not hearsay, properly authenticated)
    → Check: evidence_quotes.authentication_status
  
  □ Legal authority is verified
    → Query: SELECT * FROM authority_chains WHERE claim_id = ? AND chain_complete = 1
    → At least 1 complete authority chain per claim
  
  □ No contradicting evidence exists (or it's addressed)
    → Query: SELECT * FROM contradictions WHERE claim_id = ?
    → All contradictions must have rebuttals planned
```

### Disposition
- **All checks PASS** → Strategy approved for filing preparation
- **1-2 checks FAIL** → Strategy approved with acquisition tasks for gaps
- **3+ checks FAIL** → Strategy rejected, return to brainstorming

---

## Integration with Brainstorming Skill

The evaluation frameworks above slot into the brainstorming process at Step 5
(Explore Design Approaches):

1. Generate ideas using structured ideation methods
2. **Apply Feasibility-Impact Matrix** for initial triage (eliminate low/low)
3. **Apply Decision Matrix** for detailed comparison of top 3 options
4. **Run Pre-Mortem** on the leading candidate
5. **Clear Evidence Sufficiency Gate** before proceeding to design
6. Document all evaluation results in the Decision Log

---

## Anti-Patterns

- **Evaluation without data**: Scoring "Evidence Support" without actually querying the DB is guessing, not evaluating.
- **Equal weighting fallacy**: Not all criteria matter equally. Legal merit outweighs resource cost in litigation.
- **Score inflation**: If every option scores 4+ on everything, your scoring is too generous. Recalibrate.
- **Single-framework reliance**: Use at least 2 frameworks for high-stakes decisions. They catch different blind spots.
