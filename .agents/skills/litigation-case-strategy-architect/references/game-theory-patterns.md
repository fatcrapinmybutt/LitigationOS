# Game Theory Patterns — Litigation Strategy Reference

## Adversarial Game Theory in Multi-Lane Litigation

### Core Principle: Litigation as Sequential Game

In Pigors v Watson, the six-lane architecture creates a multi-front sequential game where each filing is a "move" that affects the opponent's available responses across all lanes.

### Strategic Game Patterns

#### Pattern 1: Commitment Strategy
**Definition**: Making an irreversible move that constrains the opponent's options.

**Litigation Application**:
- Filing an appeal (Lane F) commits the case to appellate review — trial court cannot modify appealed orders
- Filing a JTC complaint (Lane E) creates a public record — withdrawal signals weakness
- Requesting a jury trial (MCR 2.508) changes the decision-maker calculus

**Example in Pigors v Watson**:
```
Move: File claim of appeal (COA 366810)
Effect: Trial court order is frozen during appeal
Opponent constraint: Cannot rely on appealed order as final
Strategic value: Forces settlement negotiation around uncertainty
```

#### Pattern 2: Information Asymmetry Exploitation
**Definition**: Using knowledge advantages to make better decisions.

**Litigation Application**:
- Andrew James Pigors knows his evidence better than opposing counsel
- LitigationOS analysis provides comprehensive evidence mapping
- Opposing counsel must discover through formal processes

**Tactical Implementation**:
```
Step 1: Complete internal evidence analysis (EGCP scoring)
Step 2: Identify evidence gaps in opponent's likely case
Step 3: Design discovery requests targeting those gaps
Step 4: File discovery requests (MCR 2.309, 2.310)
Step 5: Use responses to refine strategy before opponent knows your full case
```

#### Pattern 3: Sequential Pressure Escalation
**Definition**: Increasing pressure through progressive filings across lanes.

**Litigation Application**:
```
Phase 1: File custody modification (Lane A) — standard pressure
Phase 2: File housing complaint (Lane B) — financial pressure
Phase 3: File discovery (Lane A) — information pressure
Phase 4: Contempt motion (Lane A) — compliance pressure
Phase 5: JTC complaint (Lane E) — structural pressure
```

Each phase creates cumulative pressure. Opposing party must respond to each, consuming resources and creating potential for errors.

#### Pattern 4: Tit-for-Tat with Forgiveness
**Definition**: Cooperate initially, retaliate proportionally to defection, but return to cooperation.

**Litigation Application**:
- Begin with reasonable positions and cooperative communication
- If opponent acts in bad faith (discovery abuse, false allegations), respond proportionally
- After proportional response, signal willingness to return to cooperation
- Courts reward parties who demonstrate good faith (MCR 2.401(C))

**Example**:
```
Round 1: Propose reasonable parenting schedule → opponent counters
Round 2: Make reasonable concession → opponent makes unreasonable demand
Round 3: File motion documenting opponent's unreasonable position → court hearing
Round 4: After court ruling, return to reasonable negotiation posture
```

### Opponent Modeling — Emily A. Watson

#### Predicted Response Patterns
| Our Move | Likely Response | Preparation |
|----------|----------------|-------------|
| Custody modification motion | Counter-motion + support increase request | Pre-draft response to support motion |
| Discovery requests | Objections + delay | Motion to compel ready (MCR 2.313) |
| Contempt motion | Claims of compliance + counter-allegations | Document all violations with evidence |
| Emergency motion | Motion to dismiss + claims of exaggeration | Strong irreparable harm evidence |
| Appeal filing | Motion to dismiss appeal + cross-appeal | Jurisdictional statement airtight |

#### Decision Tree Analysis
```
Our filing: Custody modification (MCL 722.27)
├── Opponent responds → Counter-motion
│   ├── We reply → Court hearing
│   │   ├── Court grants → WIN this round
│   │   └── Court denies → Appeal evaluation (Lane F)
│   └── We don't reply → DEFAULT RISK
├── Opponent doesn't respond → Default possible (MCR 2.603)
│   └── File for default → Motion for default judgment
└── Opponent moves to dismiss → Opposition brief required
    ├── Court grants dismissal → Appeal (Lane F)
    └── Court denies dismissal → Proceed to hearing
```

### Nash Equilibrium in Settlement

#### Settlement Zone Calculation
```
Andrew's BATNA (Best Alternative to Negotiated Agreement):
  = Expected trial outcome - trial costs - time cost - risk discount
  = EGCP score × probability × damages - costs

Emily's BATNA:
  = Expected trial defense - trial costs - risk of adverse judgment
  = Defense probability × (damages avoided) - costs

Settlement Zone exists when:
  Andrew's minimum acceptable > Emily's maximum acceptable = NO ZONE
  Andrew's minimum acceptable < Emily's maximum acceptable = ZONE EXISTS

Zone size determines settlement likelihood.
Multi-lane leverage EXPANDS the zone by increasing Emily's risk across lanes.
```

### Resource Allocation (Minimax Strategy)

#### Pro Se Resource Constraints
- Time: ~20 hours/week available
- Money: Limited filing and service budget
- Energy: Emotional toll of self-representation

#### Minimax Principle
Allocate resources to MINIMIZE the MAXIMUM possible loss across all lanes:

| Resource | Lane A (50%) | Lane F (25%) | Others (25%) |
|----------|-------------|-------------|-------------|
| Time | 10 hrs/wk | 5 hrs/wk | 5 hrs/wk |
| Budget | 50% | 25% | 25% |
| Priority | PRIMARY | SECONDARY | TERTIARY |

**Justification**: Lane A (custody) has the highest stakes (L.D.W.'s welfare). Lane F (appeal) can reset unfavorable Lane A rulings. Other lanes provide leverage but are not primary objectives.

### Strategic Communication Principles

1. **Signal strength before filing** — let opposing counsel know you have strong evidence without revealing specifics
2. **File consistently and professionally** — establish pattern of competence to earn judicial respect
3. **Never bluff on evidence** — courts verify; exposed bluffs destroy credibility permanently
4. **Use silence strategically** — not every opposing filing requires an immediate response
5. **Document everything** — the party with better records wins credibility battles
