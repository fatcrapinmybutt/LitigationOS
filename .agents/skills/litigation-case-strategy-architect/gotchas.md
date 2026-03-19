# Gotchas — litigation-case-strategy-architect

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We should file everything at once for maximum impact — show the court our full case." | Litigation is sequential chess, not simultaneous bombardment. Filing everything at once overwhelms the court, dilutes strong arguments with weak ones, and reveals your entire strategy to opposing counsel. Strategic sequencing — filing the strongest claims first — creates momentum and preserves surprise for later phases. | Judge McNeill (14th Circuit) and the COA manage heavy dockets. An overwhelming simultaneous filing gets triaged, not carefully considered. Opposing counsel sees your full hand and prepares comprehensive defenses. Phased filing forces opponents to react serially, consuming their resources. |
| 2 | "Lane C convergence means we should merge everything into one super-filing." | The six-lane architecture exists because each lane has DIFFERENT legal standards, judges, courts, and procedural requirements. Lane C convergence identifies CONNECTIONS between lanes — it does NOT merge them. A custody motion (Lane A, MCR 3.210) has completely different requirements than a housing complaint (Lane B, MCL 554.139). | Cross-contaminated filings get rejected: a custody motion citing housing code violations confuses the court. Each filing must be lane-pure. Convergence creates the STRATEGY that coordinates timing and leverage across lanes, not monolithic filings. |
| 3 | "The case is strong enough that we don't need to think about opposing party's strategy." | Litigation is adversarial. Emily A. Watson has counsel who will file counter-motions, raise defenses, and exploit weaknesses. Every strategic plan must include anticipated opposing moves and prepared responses. Game theory isn't optional — it's how you avoid being blindsided. | Filing a custody modification without anticipating Watson's likely response (e.g., counter-motion for increased support, allegations of instability, request for psychological evaluation) means scrambling to respond instead of having the response ready. Reactive litigation is losing litigation. |
| 4 | "Pro se limitations don't affect strategy — we just can't have an attorney sign things." | Pro se status affects EVERYTHING: no attorney-client privilege for communications with helpers, no recovery of attorney fees (no attorney), asymmetric MCR 2.403(O) sanctions exposure, potential for court to appoint GAL at party's expense, and judicial skepticism about complex motions. Strategy must account for these structural disadvantages. | Strategies designed for represented parties fail for pro se litigants. Filing fee petitions (no attorney = no fees), requesting continuances (courts less sympathetic to pro se scheduling issues), and complex discovery battles (pro se parties struggle with discovery mechanics) all require pro-se-specific strategic adjustments. |
| 5 | "We can adjust strategy on the fly — detailed planning is bureaucratic overhead." | Courtroom deadlines don't wait for strategic pivots. MCR 2.119(C)(1) requires 9-day motion notice. MCR 7.204(A) has a 21-day appeal deadline. MCR 2.403(K) gives 28 days to accept/reject evaluation. Missing any deadline because you were "adjusting on the fly" is catastrophic. Strategic planning IS the deadline management system. | Missed deadlines cannot be recovered. A missed 21-day appeal deadline is jurisdictional — no appeal. A missed 28-day evaluation response is deemed rejection with sanctions exposure. Strategy documents with built-in deadline tracking prevent these catastrophic failures. |
| 6 | "Focus on Lane A custody — the other lanes are distractions." | Lanes B-F create leverage for Lane A. A housing code victory (Lane B) demonstrates opposing party's pattern of negligence. A judicial misconduct finding (Lane E) provides grounds for recusal. An appellate reversal (Lane F) resets unfavorable trial court rulings. Ignoring non-custody lanes abandons strategic leverage. | Single-lane strategy means fighting custody on custody terms alone, where the opposing party may have advantages. Multi-lane strategy creates pressure points: housing liability affects financial calculations, judicial misconduct affects judicial credibility, federal claims create removal threats. Each lane amplifies the others. |

---

## Common Failure Modes

### 1. Lane Cross-Contamination in Strategy
- **What happens**: Strategic plan blends arguments from different lanes into single filings, creating legal confusion
- **How to prevent**: Each filing maps to ONE lane; convergence strategy document tracks cross-lane timing but never cross-lane content
- **Lane risk**: CRITICAL — a custody motion citing housing code violations gets rejected or ignored

### 2. Deadline Cascade Failure
- **What happens**: Filing in Lane A triggers response deadlines in Lanes D and F that weren't anticipated, causing missed deadlines
- **How to prevent**: Maintain unified deadline calendar across all lanes; before any filing, map downstream deadline impacts; use `litigation-filing-countdown` for monitoring
- **Lane risk**: HIGH — missed deadlines in ANY lane can be fatal

### 3. Resource Overcommitment
- **What happens**: Strategy calls for simultaneous actions in 4+ lanes, exceeding pro se litigant's capacity
- **How to prevent**: Maximum 2 active lanes at any time for a pro se litigant; sequence the remaining lanes; build slack into timelines
- **Lane risk**: HIGH — trying to do everything at once means doing nothing well

### 4. Opponent Response Blindness
- **What happens**: Strategy assumes opponent will be passive; opponent files aggressive counter-motions that derail the plan
- **How to prevent**: For every planned filing, document 2-3 likely opponent responses and pre-draft responses to each; war-game critical motions before filing
- **Lane risk**: HIGH for Lane A — custody cases invite aggressive counter-motions

### 5. Convergence Timing Misalignment
- **What happens**: Lane A filing goes out before Lane B evidence is ready, losing the leverage that Lane B victory would have created
- **How to prevent**: Convergence timeline must track readiness across all lanes; don't file Lane A motion until Lane B evidence package is ready to deploy as supporting evidence
- **Lane risk**: MEDIUM — suboptimal timing reduces strategic impact but doesn't prevent filing

---

## Integration Gotchas

- **litigation-analysis-engine** provides evidence strength scores that drive lane prioritization decisions
- **litigation-filing-countdown** tracks ALL deadlines across all lanes — strategy must respect these constraints
- **litigation-convergence-orchestrator** implements cross-lane coordination — strategy architect DESIGNS, orchestrator EXECUTES
- **litigation-court-order-tracker** provides the compliance baseline — strategy must account for existing obligations
- **litigation-damages-calculator** quantifies the financial stakes that drive accept/reject and settlement decisions
- Game theory analysis is only as good as the input assumptions — regularly update opponent modeling with new information
