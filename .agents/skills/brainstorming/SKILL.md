---
name: brainstorming
description: "Use when transforming vague ideas into validated designs through structured ideation, constraint analysis, and incremental reasoning before any implementation begins. Covers features, architecture, filing strategy, and behavior changes."
version: "2.0.0"
category: discipline
triggers:
  - brainstorm
  - ideation
  - design exploration
  - strategy planning
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: "Pigors v Watson"
dependencies: []
---

# Brainstorming Ideas Into Designs

## Purpose

Turn raw ideas into **clear, validated designs and specifications**
through structured dialogue **before any implementation begins**.

This skill exists to prevent:
- premature implementation
- hidden assumptions
- misaligned solutions
- fragile systems

You are **not allowed** to implement, code, or modify behavior while this skill is active.

---

## Operating Mode

You are operating as a **design facilitator and senior reviewer**, not a builder.

- No creative implementation  
- No speculative features  
- No silent assumptions  
- No skipping ahead  

Your job is to **slow the process down just enough to get it right**.

---

## The Process

### 1️⃣ Understand the Current Context (Mandatory First Step)

Before asking any questions:

- Review the current project state (if available):
  - files
  - documentation
  - plans
  - prior decisions
- Identify what already exists vs. what is proposed
- Note constraints that appear implicit but unconfirmed

**Do not design yet.**

---

### 2️⃣ Understanding the Idea (One Question at a Time)

Your goal here is **shared clarity**, not speed.

**Rules:**

- Ask **one question per message**
- Prefer **multiple-choice questions** when possible
- Use open-ended questions only when necessary
- If a topic needs depth, split it into multiple questions

Focus on understanding:

- purpose  
- target users  
- constraints  
- success criteria  
- explicit non-goals  

---

### 3️⃣ Non-Functional Requirements (Mandatory)

You MUST explicitly clarify or propose assumptions for:

- Performance expectations  
- Scale (users, data, traffic)  
- Security or privacy constraints  
- Reliability / availability needs  
- Maintenance and ownership expectations  

If the user is unsure:

- Propose reasonable defaults  
- Clearly mark them as **assumptions**

---

### 4️⃣ Understanding Lock (Hard Gate)

Before proposing **any design**, you MUST pause and do the following:

#### Understanding Summary
Provide a concise summary (5–7 bullets) covering:
- What is being built  
- Why it exists  
- Who it is for  
- Key constraints  
- Explicit non-goals  

#### Assumptions
List all assumptions explicitly.

#### Open Questions
List unresolved questions, if any.

Then ask:

> “Does this accurately reflect your intent?  
> Please confirm or correct anything before we move to design.”

**Do NOT proceed until explicit confirmation is given.**

---

### 5️⃣ Explore Design Approaches

Once understanding is confirmed:

- Propose **2–3 viable approaches**
- Lead with your **recommended option**
- Explain trade-offs clearly:
  - complexity
  - extensibility
  - risk
  - maintenance
- Avoid premature optimization (**YAGNI ruthlessly**)

This is still **not** final design.

---

### 6️⃣ Present the Design (Incrementally)

When presenting the design:

- Break it into sections of **200–300 words max**
- After each section, ask:

  > “Does this look right so far?”

Cover, as relevant:

- Architecture  
- Components  
- Data flow  
- Error handling  
- Edge cases  
- Testing strategy  

---

### 7️⃣ Decision Log (Mandatory)

Maintain a running **Decision Log** throughout the design discussion.

For each decision:
- What was decided  
- Alternatives considered  
- Why this option was chosen  

This log should be preserved for documentation.

---

## After the Design

### 📄 Documentation

Once the design is validated:

- Write the final design to a durable, shared format (e.g. Markdown)
- Include:
  - Understanding summary
  - Assumptions
  - Decision log
  - Final design

Persist the document according to the project’s standard workflow.

---

### 🛠️ Implementation Handoff (Optional)

Only after documentation is complete, ask:

> “Ready to set up for implementation?”

If yes:
- Create an explicit implementation plan
- Isolate work if the workflow supports it
- Proceed incrementally

---

## Exit Criteria (Hard Stop Conditions)

You may exit brainstorming mode **only when all of the following are true**:

- Understanding Lock has been confirmed  
- At least one design approach is explicitly accepted  
- Major assumptions are documented  
- Key risks are acknowledged  
- Decision Log is complete  

If any criterion is unmet:
- Continue refinement  
- **Do NOT proceed to implementation**

---

## Key Principles (Non-Negotiable)

- One question at a time  
- Assumptions must be explicit  
- Explore alternatives  
- Validate incrementally  
- Prefer clarity over cleverness  
- Be willing to go back and clarify  
- **YAGNI ruthlessly**

---
If the design is high-impact, high-risk, or requires elevated confidence, you MUST hand off the finalized design and Decision Log to the `multi-agent-brainstorming` skill before implementation.

---

## Decision Tree

```
ENTRY: Brainstorming request received
│
├─ Q1: What is being brainstormed?
│   ├─ FILING STRATEGY → BRANCH A (Litigation Strategy)
│   ├─ SYSTEM DESIGN → BRANCH B (Architecture/Code)
│   └─ PROCESS IMPROVEMENT → BRANCH C (Workflow/Operations)
│
├─ BRANCH A: Litigation Strategy
│   ├─ Step 1: Identify case lane (A-F) — NEVER cross-contaminate
│   ├─ Step 2: Query litigation_context.db for current evidence/claims
│   ├─ Step 3: Check MCR rules and deadlines for procedural constraints
│   ├─ Step 4: Apply structured ideation (SCAMPER, Six Hats, or Reverse)
│   ├─ Step 5: Evaluate with Feasibility-Impact Matrix + Evidence Sufficiency Gate
│   ├─ Step 6: Understanding Lock → user confirms before design proceeds
│   └─ OUTPUT: Validated strategy with Decision Log, evidence citations, MCR compliance
│
├─ BRANCH B: Architecture/Code Design
│   ├─ Step 1: Review current project state (files, docs, prior decisions)
│   ├─ Step 2: Clarify purpose, constraints, non-functional requirements
│   ├─ Step 3: Propose 2-3 approaches with trade-off analysis
│   ├─ Step 4: Understanding Lock → user confirms
│   ├─ Step 5: Present design incrementally (200-300 word sections)
│   └─ OUTPUT: Design document with assumptions, Decision Log, implementation plan
│
└─ BRANCH C: Workflow/Operations
    ├─ Step 1: Document current state and pain points
    ├─ Step 2: Identify constraints (EAGAIN limits, DB connections, session budget)
    ├─ Step 3: Generate improvement options with Constraint-First method
    ├─ Step 4: Evaluate feasibility against LitigationOS architecture
    └─ OUTPUT: Improvement proposal with risk assessment and rollback plan
│
├─ GATE: Is this high-impact or high-risk?
│   ├─ YES → Hand off to multi-agent-brainstorming skill
│   └─ NO → Proceed to implementation handoff
```

---

## Output Contract

```yaml
output:
  type: enum [strategy, design, process_improvement]
  format: markdown
  required_fields:
    - understanding_summary: string
    - assumptions: list[string]
    - decision_log: list[{decision, alternatives, rationale}]
    - recommended_approach: string
    - non_goals: list[string]
  quality_gates:
    - understanding_lock_confirmed: boolean
    - constraints_validated: boolean
    - feasibility_checked: boolean
    - alternatives_explored: boolean
    - decision_log_complete: boolean
```
