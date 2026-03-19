# Skill Selection Matrix — ELITE_SKILLSET

## When to Use Which OMEGA Skill

The OMEGA ecosystem has 12 skills plus ELITE_SKILLSET (meta-skill) and OMEGA-LITIGATION-SUPREME (litigation super-skill). Selecting the wrong skill wastes tokens and produces shallow output. This matrix resolves overlaps.

## Primary Routing Decision

```
STEP 1: Is the task litigation/legal/evidence/filing?
  YES → OMEGA-LITIGATION-SUPREME (always, no exceptions)
  NO  → Continue to Step 2

STEP 2: Does the task span 3+ domains?
  YES → ELITE_SKILLSET (meta-skill for cross-domain work)
  NO  → Continue to Step 3

STEP 3: Match to single-domain OMEGA skill:
  Python code        → OMEGA-CODE (python-omega-engine)
  Agent design       → ai-agent-architect-omega
  SQL/database       → OMEGA-DATA
  Document gen       → document-forge-supreme
  MCP server         → OMEGA-MCP
  Security audit     → OMEGA-SECURITY
  Git/CI/CD          → OMEGA-DEVOPS
  Documentation      → OMEGA-WRITING
  Memory systems     → OMEGA-MEMORY
  Research           → OMEGA-RESEARCH
  Orchestration      → OMEGA-ORCHESTRATOR
```

## Overlap Resolution Table

| Scenario | Wrong Choice | Right Choice | Why |
|----------|-------------|--------------|-----|
| Draft a motion | ELITE_SKILLSET | OMEGA-LITIGATION-SUPREME | SUPREME has M4 Filing Factory with MCR templates |
| Optimize a SQLite query | ELITE_SKILLSET | OMEGA-DATA | OMEGA-DATA has specific index strategies, FTS5 patterns |
| Build a new pipeline agent | OMEGA-CODE | ai-agent-architect-omega | Agent design needs Agent9999 patterns, not general Python |
| Write a README | document-forge-supreme | OMEGA-WRITING | WRITING has project-doc-specific patterns |
| Analyze evidence + draft motion | OMEGA-LITIGATION-SUPREME | OMEGA-LITIGATION-SUPREME | Single skill covers both via M1+M4 modules |
| Refactor Python + update tests + optimize DB | OMEGA-CODE | ELITE_SKILLSET | Cross-domain (3+ domains) = ELITE territory |
| Generate PDF report (non-court) | OMEGA-LITIGATION-SUPREME | document-forge-supreme | Non-court documents don't need litigation skill |
| Design multi-agent workflow + implement in Python | ai-agent-architect-omega | ELITE_SKILLSET | Spans agent design + Python = cross-domain |

## Skill Depth vs Breadth Spectrum

```
DEPTH (single domain, maximum detail)
  ↑
  │  OMEGA-DATA (SQL-only, 13 skills deep)
  │  OMEGA-CODE (Python-only, 41 skills deep)
  │  OMEGA-SECURITY (Security-only, 29 skills deep)
  │  ai-agent-architect-omega (agents-only, 20 skills deep)
  │  document-forge-supreme (docs-only, 14 skills deep)
  │  OMEGA-LITIGATION-SUPREME (litigation-only, 67 skills, 12 modules)
  │
  │  ELITE_SKILLSET (27 skills across 9 domains)
  ↓
BREADTH (multi-domain, synthesized coverage)
```

## Anti-Stacking Rule

**Never activate more than ONE skill for a task.** If two skills seem necessary:
1. Check if ELITE_SKILLSET covers both domains (it likely does for 9 domains)
2. Check if one skill has a sub-module covering the other domain
3. If truly separate tasks, decompose and route each to its own skill sequentially

## Session Lifecycle

Skills are loaded at invocation time, not session start. Each skill invocation:
1. Loads the SKILL.md content into context
2. Applies for the duration of the current task/prompt
3. Does NOT persist across separate user messages unless re-invoked
4. Gotchas and references are available but not auto-loaded (reference explicitly)
