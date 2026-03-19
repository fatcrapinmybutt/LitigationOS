# Structured Ideation Methods for Litigation Strategy

## Overview

Unstructured brainstorming produces anchored, biased, and incomplete idea sets.
These structured methods force diverse thinking, especially when applied to
litigation strategy where missing an angle can mean losing a motion.

---

## Method 1: SCAMPER (Adapted for Litigation)

SCAMPER generates ideas by systematically applying transformations to an existing
strategy or filing approach.

| Letter | Transformation | Litigation Application |
|--------|---------------|----------------------|
| **S** — Substitute | Replace one element | What if we substitute MCR 2.003 (disqualification) for MCR 2.003(D) (reassignment)? |
| **C** — Combine | Merge two approaches | Combine the PPO enforcement (Lane D) with custody modification (Lane A) in one hearing |
| **A** — Adapt | Borrow from another context | Adapt the COA brief structure for a circuit court motion |
| **M** — Modify | Change scale, scope, timing | File an emergency motion instead of a standard motion (faster timeline) |
| **P** — Put to other use | Repurpose existing work | Use the JTC complaint evidence (Lane E) to support the disqualification motion (Lane A) |
| **E** — Eliminate | Remove unnecessary elements | Drop the weakest 3 claims to strengthen the remaining 5 |
| **R** — Reverse | Invert the approach | Instead of attacking the ruling, argue the ruling supports our position on appeal |

### When to Use
- You have an existing strategy that feels incomplete
- You want to stress-test a filing approach before committing
- You need creative alternatives to a conventional motion

---

## Method 2: Six Thinking Hats (De Bono)

Forces the brainstorm through six distinct perspectives sequentially.
Prevents the dominant perspective from drowning out others.

| Hat | Perspective | Litigation Prompt |
|-----|-----------|-------------------|
| 🟡 **Yellow** | Optimistic / Benefits | "What's the best-case outcome if this motion succeeds?" |
| ⚫ **Black** | Critical / Risks | "How will opposing counsel (Barnes, P55406) attack this?" |
| 🔴 **Red** | Emotional / Intuitive | "How will Judge McNeill likely react to this argument?" |
| ⟠ **White** | Facts / Data | "What does litigation_context.db actually show? Run the query." |
| 🟢 **Green** | Creative / Alternatives | "What unconventional approaches haven't we considered?" |
| 🔵 **Blue** | Process / Meta | "Are we brainstorming the right question? Should we reframe?" |

### Enforcement Rule
Complete ALL six hats before evaluating any idea. The temptation to skip
Black Hat (risks) or Red Hat (intuition) is the #1 failure mode.

### Litigation-Specific Adaptation
- **White Hat is mandatory first**: Query the DB before generating ideas.
  No strategy should be proposed without evidence grounding.
- **Black Hat must simulate opposing counsel**: Don't just identify risks —
  write the actual counterargument Barnes would file.

---

## Method 3: Mind Mapping (Evidence-Centered)

Start from the central legal claim and branch outward to supporting evidence,
counterarguments, procedural requirements, and strategic options.

### Structure
```
                    [Central Claim]
                    /      |       \
            [Evidence]  [Authority]  [Procedure]
            /    \       /    \        /      \
      [Doc1] [Doc2]  [MCR]  [Case]  [Form]  [Deadline]
```

### Litigation Application
1. Center: "Judicial Disqualification under MCR 2.003"
2. Branch 1 — Evidence: Query evidence_quotes WHERE claim relates to bias
3. Branch 2 — Authority: Query authority_chains for MCR 2.003 citations
4. Branch 3 — Procedure: Check deadlines, required forms, service rules
5. Branch 4 — Opposition: Anticipated counterarguments
6. Branch 5 — Alternatives: What if disqualification is denied?

### Key Rule
Every branch must be DB-grounded. If a branch has no supporting data in
litigation_context.db, it's either a gap (create acquisition task) or
a hallucination (delete the branch).

---

## Method 4: Reverse Brainstorming

Instead of "How do we win this motion?", ask "How do we guarantee we LOSE?"
Then invert every answer.

### Process
1. Define the goal: "Win motion to disqualify Judge McNeill"
2. Reverse it: "How do we guarantee the disqualification motion fails?"
3. Generate failure causes:
   - File after the deadline
   - Cite no specific instances of bias
   - Use generic legal authority, not Michigan-specific
   - Fail to serve opposing counsel
   - Ignore MCR 2.003(D) procedural requirements
4. Invert each: These become your checklist of must-do items

### Why It Works
- Easier to identify failure modes than success factors
- Naturally produces a constraint checklist
- Exposes assumptions ("we assumed service was handled")

---

## Method 5: Constraint-First Ideation

Start with immovable constraints, then generate ideas within them.

### LitigationOS Constraints (Always Apply)
| Constraint | Source | Impact |
|-----------|--------|--------|
| Filing deadlines | MCR, court orders | Hard stop — miss it and the motion is barred |
| Court rules (MCR) | Michigan Court Rules DB | Procedural requirements are non-negotiable |
| Evidence availability | litigation_context.db | Can't cite evidence that doesn't exist |
| Lane isolation | MEEK classification | Don't mix Lane A custody with Lane D PPO |
| Page limits | MCR 7.212 (briefs), local rules | Exceeding limits = rejection |
| Service requirements | MCR 2.107 | No service = no hearing |

### Process
1. List ALL applicable constraints for the current filing
2. Eliminate any idea that violates a hard constraint
3. For ideas that partially conflict, identify modifications to make them compliant
4. Rank remaining ideas by impact within constraint boundaries

---

## Choosing a Method

| Situation | Best Method |
|-----------|-------------|
| Improving an existing strategy | SCAMPER |
| Need comprehensive perspective coverage | Six Thinking Hats |
| Mapping evidence to claims | Mind Mapping |
| Identifying what could go wrong | Reverse Brainstorming |
| Working within tight rules/deadlines | Constraint-First |
| Complex multi-lane strategy | Combine Mind Mapping + Six Hats |

---

## Anti-Patterns to Avoid

- **Method shopping**: Don't try all 5 methods on every brainstorm. Pick 1-2 based on the situation.
- **Skipping the data check**: Every method above requires DB validation. No ideas without evidence.
- **Solo hat wearing**: In Six Thinking Hats, don't combine hats. One perspective at a time.
- **Constraint relaxation**: "What if we could ignore the deadline?" is not a useful brainstorm — the deadline exists.
