# Gotchas — litigation-convergence-orchestrator

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The quality score is 72 — that's passing, so we can file." | 72 means significant gaps remain. 'Passing' is a school mentality, not a courtroom standard. A filing with a 72 quality score has ~28% unaddressed risk surface. In Pigors v Watson, every gap is an opportunity for opposing counsel. | Filing with known gaps = malpractice exposure. Judge McNeill (Lane A) and Judge Hoopes (Lane B) will not forgive avoidable errors. One unfixed gap can unravel an entire motion. |
| 2 | "We'll fix the DNEW items next cycle — they're not blockers." | DNEW items become blockers when ignored. Today's minor gap is tomorrow's critical failure. The convergence cycle exists precisely because gaps compound over time. Deferring everything to NEXT_PATCH creates a debt spiral. | DNEW items deferred without analysis become invisible. By the time they surface as blockers, the filing deadline has passed. In Lane B (Shady Oaks), deferred evidence gaps meant missing the statute of limitations window. |
| 3 | "Emergence detection is optional — it's just nice-to-have pattern matching." | Emergence detection found the cross-lane connection between Watson's housing situation and custody fitness. Without it, Lane A and Lane B stayed siloed. The whole point of Lane C (Convergence) is emergence-driven strategy. | Skipping emergence = missing the strongest arguments. The Pigors litigation depends on cross-lane synthesis. Without emergence detection, you're litigating two separate cases instead of one unified strategy. |
| 4 | "The convergence cycle takes too long — we'll do a quick manual check instead." | Manual checks miss what automated convergence catches: cross-reference integrity, authority currency drift, timeline inconsistencies, entity overlap patterns. Humans are terrible at systematic completeness checking. | Manual spot-checks create false confidence. You think you checked everything; you checked 30%. The remaining 70% contains the gap that loses the case. Every major litigation failure starts with "I checked it manually." |
| 5 | "Regression is fine — we just added new data, so the score naturally dropped." | New data should IMPROVE quality (more evidence = stronger case). If the score drops when you add data, something is wrong: contradictions introduced, authority chains broken, or classifications incorrect. Regression requires root cause analysis, not rationalization. | Accepting regression normalizes quality decay. Each accepted regression lowers the baseline. After three accepted regressions, your 85 has become a 60, and you've convinced yourself it's fine because each individual drop was "expected." |
| 6 | "Cross-lane contradictions aren't real contradictions — the contexts are different." | If Lane A says Pigors is an exemplary parent and Lane B implies financial irresponsibility, opposing counsel WILL connect them. "Different context" is YOUR framing; the court sees one plaintiff. Every cross-lane statement must be consistent. | Opposing counsel in Watson/Custody (Lane A) will subpoena housing records (Lane B). If your filings contain inconsistent characterizations of Pigors across lanes, your credibility is destroyed in both cases simultaneously. |
| 7 | "We don't need to run litigation_self_test() — the filings look fine." | "Looks fine" is the most dangerous phrase in litigation. Self-test catches formatting errors, missing signatures, incorrect case numbers, stale dates, and broken cross-references that visual review misses. Every pipeline phase can introduce subtle errors. | The 14th Circuit clerk's office will reject improperly formatted filings. If rejection happens on the deadline day, you've missed your filing window. Self-test catches the errors that "look fine" to tired eyes at midnight. |

---

## Common Failure Modes

### 1. Score Inflation
- **What happens**: Scoring weights manually adjusted to produce higher scores
- **How to prevent**: Scoring formula is fixed in skill spec — no runtime modification
- **Lane risk**: HIGH — temptation increases as deadlines approach

### 2. Emergence False Positives
- **What happens**: Pattern matching finds connections that don't actually exist
- **How to prevent**: All emergence events require evidence links; novelty score ≥ 7 triggers human review
- **Lane risk**: MEDIUM for Lane C — convergence creates many weak signals

### 3. Cycle Skipping
- **What happens**: Phases within the convergence cycle are skipped "to save time"
- **How to prevent**: Cycle protocol enforces sequential phase completion; no phase can be bypassed
- **Lane risk**: HIGH under deadline pressure for all lanes

### 4. Gap Misclassification
- **What happens**: BLOCKER items classified as NEXT_PATCH to avoid dealing with them
- **How to prevent**: Blockers are defined by objective criteria (blocks filing progress); classification is auditable
- **Lane risk**: CRITICAL — misclassified blockers cause filing failures

### 5. Stale Convergence Status
- **What happens**: litigation_convergence_status() not called, decisions based on old data
- **How to prevent**: Status must be refreshed at the start of every convergence cycle
- **Lane risk**: HIGH — litigation context changes rapidly during active proceedings

---

## Integration Gotchas

- **litigation-pipeline-commander** feeds data INTO convergence — ensure pipeline phase data is current
- **litigation-authority-validator** reports feed the authority_completeness score — stale authority reports = stale quality scores
- **litigation-brain-spec** knowledge graph changes can cause quality score fluctuations — expected after brain updates
- **litigation-skill-auditor** audits THIS skill — ensure convergence protocol changes are reflected in both places
