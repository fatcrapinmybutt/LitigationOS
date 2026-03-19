# Skill Activation Protocol — ELITE_SKILLSET

## How Skills Are Loaded

ELITE_SKILLSET and all OMEGA skills follow a consistent activation lifecycle. Understanding this model prevents wasted invocations and context overflow.

## Activation Lifecycle

```
1. USER MESSAGE arrives
   │
2. SKILL ROUTING — Agent determines which skill(s) apply
   │  Priority: OMEGA-LITIGATION-SUPREME > ELITE_SKILLSET > domain OMEGA > legacy agent
   │
3. SKILL LOADING — SKILL.md content injected into context window
   │  • Metadata block parsed for triggers, lanes, dependencies
   │  • Full skill body becomes available for reasoning
   │  • gotchas.md and references/ are NOT auto-loaded (reference on demand)
   │
4. TASK EXECUTION — Agent works with skill context active
   │  • Skill guides decision-making, patterns, and output format
   │  • Output Contract defines expected deliverables
   │  • Decision Tree guides branching logic
   │
5. TASK COMPLETION — Skill context ends
   │  • Skill does NOT persist to next user message
   │  • Results persist (in agent output, files, SQL)
   │  • Re-invoke skill explicitly for follow-up work
```

## Persistence Model

| Aspect | Persists Across Messages? | Notes |
|--------|--------------------------|-------|
| Skill instructions | NO | Must re-invoke per task |
| Generated files | YES | Written to filesystem |
| SQL todo updates | YES | Session database persists |
| Agent results | MAYBE | Must `read_agent` immediately; compaction may clear |
| Memory store facts | YES | Cross-session via `store_memory` |

## Pre-Activation Checklist (ELITE_SKILLSET)

Before activating ELITE_SKILLSET, verify:

1. **MANBEARPIG startup protocol completed** — STARTUP_REPORT.md is current
2. **litigation_context.db accessible** — the 12GB central database must be reachable
3. **EAGAIN state is L0 or L1** — if at L2+, reduce concurrency before starting complex work
4. **No stale shells** — run `list_powershell` and stop any dangling sessions
5. **Agent budget available** — run `list_agents` and confirm < 3 running

## Multi-Skill Invocation (Anti-Pattern)

```
❌ WRONG: Invoke ELITE_SKILLSET + OMEGA-LITIGATION + OMEGA-CODE simultaneously
   Result: Conflicting formatting rules, duplicated context, wasted tokens

✅ RIGHT: Invoke ELITE_SKILLSET alone (it contains fused versions of both domains)
   Result: Unified guidance from synthesized 27-skill knowledge base

✅ RIGHT: Decompose into sub-tasks, invoke one skill per sub-task
   Sub-task 1 (filing): OMEGA-LITIGATION-SUPREME
   Sub-task 2 (code fix): OMEGA-CODE
```

## Trigger Keywords → Skill Routing

| Keywords in User Message | Route To |
|-------------------------|----------|
| "motion", "brief", "filing", "court", "MCR" | OMEGA-LITIGATION-SUPREME |
| "evidence", "exhibit", "Bates", "dedup" | OMEGA-LITIGATION-SUPREME (M1) |
| "Python", "script", "function", "class", "test" | OMEGA-CODE / python-omega-engine |
| "agent", "orchestrate", "spawn", "fleet" | ai-agent-architect-omega |
| "document", "PDF", "DOCX", "template", "report" | document-forge-supreme |
| "SQL", "query", "database", "index", "schema" | OMEGA-DATA |
| "security", "vulnerability", "PII", "audit" | OMEGA-SECURITY |
| Complex multi-domain task | ELITE_SKILLSET |

## ELITE_SKILLSET Domain Coverage Map

```
Domain 1: Agent Architecture (7 skills)  — Design, orchestrate, evaluate agents
Domain 2: AI Engineering (2 skills)      — LLM integration, RAG, product AI
Domain 3: Prompt Engineering (2 skills)  — Prompt optimization, templates
Domain 4: Performance (2 skills)         — SQL optimization, app performance
Domain 5: Evidence Engineering (3 skills)— Harvesting, analysis, timeline
Domain 6: Legal Writing (2 skills)       — Affidavits, Michigan litigation
Domain 7: Legal Intelligence (2 skills)  — Case analysis, strategy
Domain 8: Data Engineering (1 skill)     — Pipeline design
Domain 9: Execution (5 skills)           — Planning, execution, research, QA, improvement
```

## Error Recovery

If a skill invocation produces poor results:
1. Check if the wrong skill was selected (see selection matrix)
2. Check if skill prerequisites were met (startup protocol, DB access)
3. Try a more specific OMEGA skill instead of ELITE_SKILLSET
4. For litigation tasks, ALWAYS escalate to OMEGA-LITIGATION-SUPREME
5. Report the failure pattern in gotchas.md for future reference
