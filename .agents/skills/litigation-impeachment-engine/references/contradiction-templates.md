# Contradiction Templates — litigation-impeachment-engine

## Contradiction Documentation Templates

These templates provide standardized formats for documenting, scoring, and
packaging contradictions for impeachment in Pigors v Watson litigation.

---

## Template 1: Direct Contradiction Record

```yaml
contradiction_id: C-[XXX]
type: DIRECT
witness: [Full Name]
topic: [Subject matter of contradiction]
lane: [A | B | C]

statement_a:
  text: "[Exact quote from first statement]"
  source: "[Document name / title]"
  date: "[YYYY-MM-DD]"
  location: "Page [X], Line [Y]"
  sworn: [true | false]
  context: "[Proceeding type: deposition, hearing, affidavit, email, etc.]"

statement_b:
  text: "[Exact quote from second statement]"
  source: "[Document name / title]"
  date: "[YYYY-MM-DD]"
  location: "Page [X], Line [Y]"
  sworn: [true | false]
  context: "[Proceeding type]"

analysis:
  nature: "[How exactly do these statements conflict?]"
  materiality: [0-10]    # How important to case outcome
  clarity: [0-10]        # How clear/obvious is the contradiction
  provability: [0-10]    # How easily shown in court
  composite: [0-30]      # Sum of three scores

mre_foundation:
  applicable_rule: "[MRE 613 / MRE 801(d)(1)(A) / MRE 801(d)(1)(B)]"
  substantive_use: [true | false]
  foundation_steps: "[List required foundation elements]"

examination_script:
  commit:
    - "Q: [Question to lock witness into current position]"
    - "Q: [Follow-up commitment question]"
  credit:
    - "Q: [Question establishing reliability of prior statement]"
    - "Q: [Follow-up credit question]"
  confront:
    - "Q: [Question presenting the prior statement]"
    - "Q: [Direction to read specific language]"
  contrast:
    - "[Statement highlighting the inconsistency — not a question]"

anticipated_explanation: "[What the witness will likely say to explain]"
rebuttal: "[How to counter the explanation]"
exhibits_needed: "[List exhibit numbers and descriptions]"
```

---

## Template 2: Material Omission Record

```yaml
contradiction_id: C-[XXX]
type: MATERIAL_OMISSION
witness: [Full Name]
topic: [Subject matter]
lane: [A | B | C]

original_statement:
  text: "[Full text of original statement — note what is present]"
  source: "[Document name]"
  date: "[YYYY-MM-DD]"
  location: "Page [X], Line [Y]"
  pages_total: [number]
  critical_fact_absent: "[The fact that should have been included but wasn't]"

later_statement:
  text: "[Text where the critical fact first appears]"
  source: "[Document name]"
  date: "[YYYY-MM-DD]"
  location: "Page [X], Line [Y]"

analysis:
  nature: "Witness omitted [fact] from [original statement] but raised it
           for first time in [later statement], [X days/months] later."
  materiality: [0-10]
  clarity: [0-10]
  provability: [0-10]
  composite: [0-30]
  reason_omission_matters: "[Why this fact should have been in original]"

examination_script:
  establish_completeness:
    - "Q: You gave a statement on [date] about [topic], correct?"
    - "Q: You tried to be thorough and accurate?"
    - "Q: You included everything you thought was important?"
  establish_omission:
    - "Q: Nowhere in that [X]-page statement did you mention [fact]?"
    - "Q: That's because [fact] didn't happen / wasn't important then?"
  confront:
    - "Q: But now, [X months later], you're telling us [fact]?"
```

---

## Template 3: Temporal Contradiction Record

```yaml
contradiction_id: C-[XXX]
type: TEMPORAL
witness: [Full Name]
topic: [Timeline event]
lane: [A | B | C]

timeline_claim_a:
  event: "[What allegedly happened]"
  date_claimed: "[Date given in statement A]"
  source: "[Document]"
  date_of_statement: "[When this statement was made]"

timeline_claim_b:
  event: "[Same event]"
  date_claimed: "[Different date given in statement B]"
  source: "[Document]"
  date_of_statement: "[When this statement was made]"

corroborating_evidence:
  actual_date: "[If known from independent evidence]"
  source: "[Independent evidence source]"

analysis:
  discrepancy: "[X days/weeks/months between claimed dates]"
  significance: "[Why the timing matters to the case]"
  materiality: [0-10]
  clarity: [0-10]
  provability: [0-10]
  composite: [0-30]
```

---

## Template 4: Degree Contradiction Record

```yaml
contradiction_id: C-[XXX]
type: DEGREE
witness: [Full Name]
topic: [Subject]
lane: [A | B | C]

statement_a:
  text: "[Statement with one degree of severity/frequency/amount]"
  degree: "[e.g., 'occasionally', '$500', 'minor damage']"
  source: "[Document]"
  date: "[Date]"

statement_b:
  text: "[Same topic with different degree]"
  degree: "[e.g., 'constantly', '$5,000', 'severe damage']"
  source: "[Document]"
  date: "[Date]"

analysis:
  shift_direction: "[Escalation or minimization?]"
  magnitude: "[How large is the degree shift?]"
  motive: "[Why would witness change the degree?]"
  materiality: [0-10]
  clarity: [0-10]
  provability: [0-10]
  composite: [0-30]
```

---

## Template 5: Cross-Witness Contradiction Matrix

```yaml
contradiction_id: CW-[XXX]
type: CROSS_WITNESS
topic: [Shared event/fact]
lane: [A | B | C]

witness_a:
  name: "[Name]"
  text: "[Statement about event]"
  source: "[Document]"
  date: "[Date]"
  relationship: "[Relationship to parties]"
  credibility_factors: "[Sworn? Motive? Bias?]"

witness_b:
  name: "[Name]"
  text: "[Contradicting statement about same event]"
  source: "[Document]"
  date: "[Date]"
  relationship: "[Relationship to parties]"
  credibility_factors: "[Sworn? Motive? Bias?]"

analysis:
  nature: "[How do these witnesses' accounts conflict?]"
  who_is_likely_correct: "[Based on corroborating evidence]"
  corroboration: "[Independent evidence supporting one version]"
  materiality: [0-10]
  clarity: [0-10]
  provability: [0-10]
  composite: [0-30]

strategic_use: "[How to use this contradiction in proceedings]"
```

---

## Contradiction Scoring Quick Reference

| Materiality (0–10) | Description |
|--------------------|-------------|
| 0–2 | Trivial — no case impact |
| 3–4 | Minor — peripheral to key issues |
| 5–6 | Moderate — affects secondary arguments |
| 7–8 | Significant — affects primary arguments |
| 9–10 | Critical — affects case outcome directly |

| Clarity (0–10) | Description |
|----------------|-------------|
| 0–2 | Ambiguous — reasonable explanations exist |
| 3–4 | Unclear — some ambiguity |
| 5–6 | Moderate — contradiction visible but nuanced |
| 7–8 | Clear — obvious contradiction |
| 9–10 | Unambiguous — flat contradiction, no reasonable explanation |

| Provability (0–10) | Description |
|--------------------|-------------|
| 0–2 | Difficult — oral statement, no record |
| 3–4 | Challenging — informal written record only |
| 5–6 | Moderate — written record, some authentication needed |
| 7–8 | Strong — sworn statement, authenticated document |
| 9–10 | Irrefutable — multiple sworn sources confirm |
