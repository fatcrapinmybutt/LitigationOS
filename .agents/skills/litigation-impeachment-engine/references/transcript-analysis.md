# Transcript Analysis — litigation-impeachment-engine

## Transcript Analysis Protocol for Michigan Court Proceedings

This reference provides a structured methodology for analyzing hearing and
deposition transcripts to identify impeachment opportunities, admissions,
evasions, and credibility indicators in 14th Judicial Circuit proceedings.

---

## Transcript Source Types

| Source | Format | Authority | Use |
|--------|--------|-----------|-----|
| Hearing transcript | Court reporter certified | MCR 8.108 | Substantive + Impeachment |
| Deposition transcript | Reporter certified | MCR 2.306 | Substantive (party) + Impeachment |
| FOC hearing transcript | FOC recorder | MCR 3.224 | Limited — check admissibility |
| Video recording | Court AV system | Local rule | Supplement to written transcript |

---

## Phase 1: Initial Transcript Scan

### Quick Pass Indicators
When first reviewing a transcript, flag the following on initial read:

| Indicator | Flag | Page/Line |
|-----------|------|-----------|
| "I don't recall" / "I don't remember" | EVASION | |
| "That's not exactly what I said" | POSSIBLE CONTRADICTION | |
| "I may have" / "I might have" | ADMISSION HEDGE | |
| "Yes" to leading question | POSSIBLE ADMISSION | |
| Long non-responsive answer | EVASION | |
| "I never said that" (denials) | IMPEACHMENT TARGET | |
| "Everyone knows" / "Obviously" | CONCLUSORY — no foundation | |
| Correction by counsel ("Let me rephrase") | COUNSEL RESCUE | |
| "Off the record" requests | RECORD GAP | |
| Objections (substance of question revealed) | SENSITIVE TOPIC | |

---

## Phase 2: Deep Analysis Categories

### Category A: Admissions Against Interest

**Definition**: Statements by a party that are adverse to their position.

**MRE 801(d)(2)**: Admissions by a party-opponent are NOT hearsay.

**Extraction Protocol**:
1. Identify the declarant (must be a party or party's agent)
2. Identify the statement that hurts their position
3. Record exact language, page, and line
4. Classify admissibility:
   - Party's own statement → 801(d)(2)(A) (always admissible)
   - Adoptive admission → 801(d)(2)(B)
   - Authorized admission → 801(d)(2)(C)
   - Agent/employee admission → 801(d)(2)(D)

**Lane A Examples**:
- Watson admitting awareness of conditions affecting child
- Watson admitting failure to comply with court orders
- Watson admitting facts supporting custody modification

**Lane B Examples**:
- Shady Oaks representative admitting knowledge of conditions
- Shady Oaks admitting failure to repair after notice
- Shady Oaks admitting corporate control by Alden Global

---

### Category B: Evasive Answers

**Definition**: Answers that avoid directly responding to the question.

**Types of Evasion**:

| Evasion Type | Example | Impeachment Value |
|-------------|---------|-------------------|
| Memory claim | "I don't recall" | Moderate — may be genuine |
| Redirect | "What I can tell you is..." | High — deliberate avoidance |
| Over-explanation | [Long narrative avoiding yes/no] | High — suggests discomfort |
| Qualification | "It depends on what you mean by..." | Moderate — may be legitimate |
| Non-responsive | [Answer to different question] | High — deliberate avoidance |
| Counsel objection shield | [Objection + instruction not to answer] | Note for record |

**Tracking Template**:
```
Evasion ID: EV-[XXX]
Page/Line: [P], [L]
Question: "[Exact question]"
Answer: "[Exact answer]"
Evasion Type: [Memory | Redirect | Over-explain | Qualify | Non-responsive]
Topic: [What question was trying to establish]
Follow-up needed: [Yes/No — what question to ask next time]
```

---

### Category C: Internal Contradictions

**Definition**: Statements within the SAME transcript that conflict.

**This is often the most powerful impeachment** because the witness cannot
claim changed memory or different context — both statements were made on
the same day, in the same proceeding, under the same oath.

**Detection Method**:
1. Index all factual claims by topic
2. For each topic, compare all statements
3. Flag any differences in fact, degree, timing, or characterization
4. Score using standard materiality/clarity/provability framework

---

### Category D: Witness Credibility Assessment

**Scoring Framework**:

| Factor | Score (0–10) | Notes |
|--------|-------------|-------|
| Consistency (internal) | | Same testimony contradicts itself? |
| Consistency (external) | | Testimony contradicts other evidence? |
| Responsiveness | | Does witness answer questions directly? |
| Memory pattern | | Selective memory (remembers helpful, forgets harmful)? |
| Demeanor indicators | | Confidence, hesitation patterns |
| Bias indicators | | Relationship to parties, financial interest |
| Detail calibration | | Appropriate detail level (too vague or too specific)? |

**Credibility Score** = average of all factors / 10

**Interpretation**:
| Score | Assessment |
|-------|-----------|
| 0.8–1.0 | Highly credible witness |
| 0.6–0.79 | Generally credible with some concerns |
| 0.4–0.59 | Significant credibility issues |
| 0.2–0.39 | Major credibility problems |
| 0.0–0.19 | Not credible |

---

## Phase 3: Cross-Reference Protocol

### Cross-Reference Against Other Sources
For each significant transcript claim, cross-reference against:

| Source | Available? | Contradiction Found? |
|--------|-----------|---------------------|
| Prior transcripts (same witness) | ☐ | ☐ |
| Depositions (same witness) | ☐ | ☐ |
| Affidavits (same witness) | ☐ | ☐ |
| Written communications (same witness) | ☐ | ☐ |
| Other witnesses on same topic | ☐ | ☐ |
| Documentary evidence | ☐ | ☐ |
| Physical evidence | ☐ | ☐ |
| Public records | ☐ | ☐ |

---

## Phase 4: Transcript Attack Preparation

### For Each Identified Impeachment Target

```
Target ID: TA-[XXX]
Witness: [Name]
Transcript: [Source, date]
Page/Line: [P, L]

Current testimony (to impeach):
  "[Exact quote]"

Prior inconsistent source:
  "[Exact quote from prior source]"
  Source: [Document]
  Page/Line: [P, L]

MRE Foundation:
  Rule: [613 / 801(d)(1)(A) / 801(d)(2)]
  Sworn prior statement: [Yes / No]
  Substantive use available: [Yes / No]

Examination script: [Reference contradiction template C-XXX]
Exhibits needed: [List]
Priority: [1-5, with 1 = highest]
```

---

## Michigan Transcript-Specific Rules

### Ordering Transcripts — MCR 8.108
- Court reporter must provide transcript within specified timeframe
- Expedited transcripts available for additional cost
- Daily copy available during trial (additional cost)
- Review and correction period: 21 days after receipt (MCR 2.308(B))

### Deposition Transcript Corrections — MCR 2.308(B)
- Witness may review and make changes within 21 days
- Changes must be signed by witness
- Original answers remain in the record — changes are noted
- **Impeachment note**: If witness makes changes to deposition, the original
  answer AND the change are both usable for impeachment

### Court Reporter Certification
- Michigan court reporters must be certified under MCR 8.108
- Certified transcript is self-authenticating under MRE 902
- No need for additional authentication foundation in court
