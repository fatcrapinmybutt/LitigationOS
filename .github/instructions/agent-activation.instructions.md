---
description: Agent activation matrix for LitigationOS. Maps custom agents and skills to litigation workflows. Apply to all interactions.
applyTo: "**/*"
---

# Agent Activation Matrix — LitigationOS

## MCP Servers (auto-start, persistent, unlimited executions)

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| **command-runner** | Shell replacement — zero session pool consumption | `exec_command`, `exec_python`, `exec_git`, `exec_pipeline_phase`, `system_status` |
| **litigation-context** | 45 legal tools — DB queries, filings, evidence, deadlines | `search`, `filing_readiness`, `evidence_chain`, `deadline_dashboard`, `prefiling_qa` |
| **agent-memory** | Persistent cross-session memory | `store`, `retrieve`, `search` |

### Command Runner Priority Rule
**ALWAYS prefer command-runner MCP tools over the `powershell` tool.**
The powershell tool creates OS sessions that exhaust after ~120 uses per session.
The command-runner MCP executes unlimited commands via a single persistent process.

```
GOOD:  exec_python("00_SYSTEM/scripts/noreply_pdf_processor.py", "--limit 50")
BAD:   powershell("python 00_SYSTEM/scripts/noreply_pdf_processor.py --limit 50")

GOOD:  exec_git("status")
BAD:   powershell("git --no-pager status")

GOOD:  exec_command("Get-ChildItem *.pdf | Measure-Object")
BAD:   powershell("Get-ChildItem *.pdf | Measure-Object")
```

## ⚡ SUPREME TIER: OMEGA-LITIGATION-SUPREME (Route ALL Litigation Here)

> **OMEGA-LITIGATION-SUPREME absorbs ALL 67 litigation skills into one unified combat system.**
> This is the FIRST routing target for ANY litigation, evidence, filing, or legal task.
> It replaces the need to select between individual litigation skills or OMEGA-LITIGATOR.
> **Skill file:** `.agents/skills/OMEGA-LITIGATION-SUPREME/SKILL.md`

| Skill | Skills Fused | 12 Modules | Use When |
|-------|-------------|------------|----------|
| **OMEGA-LITIGATION-SUPREME** | **ALL 67** litigation skills | M1 Evidence Pipeline · M2 Contradiction Engine · M3 Authority Validator · M4 Filing Factory · M5 Strategic Command · M6 Domain Specialists · M7 DB Intelligence · M8 QA/Anti-Hallucination · M9 Execution Protocol · M10 Adversary Intel · M11 Smart Router · M12 Self-Evolution | **ANY litigation task whatsoever** — evidence analysis, filing generation, impeachment, discovery, appeals, MSC, COA, JTC, PPO, custody, housing, §1983, strategy, convergence |

### SUPREME Routing (replaces OMEGA routing for litigation)
```
Task received →
  Is it litigation/legal/evidence/filing? → OMEGA-LITIGATION-SUPREME (ALWAYS)
  Is it system design/agent work? → OMEGA-ARCHITECT
  Is it coding/data/security? → OMEGA-ENGINEER
  Is it maintenance/health/docs? → OMEGA-SENTINEL
  Is it specialized (transcripts, forms, redaction)? → Legacy agent below
```

### SUPREME Module Router (auto-detection from natural language)
```
"Analyze files/evidence"              → M1 + M7
"Find contradictions/impeachment"     → M2
"Validate citations"                  → M3
"Draft motion/brief/petition"         → M4
"What should I file next?"            → M5
"Custody/PPO/appeal question"         → M6
"Run QA check"                        → M8
"Full pipeline from files to filing"  → M1→M2→M3→M5→M6→M4→M8
"What's Emily's pattern?"             → M10
"Check McNeill bias"                  → M6.D4
```

---

## OMEGA Agents (Tier 2 — Non-Litigation Domains)

> **For NON-litigation tasks only.** All litigation routes through OMEGA-LITIGATION-SUPREME above.
> **Full index:** `skills/litigation/OMEGA-INDEX.md`

| Agent | Skills Fused | Triggers | Use When |
|-------|-------------|----------|----------|
| **OMEGA-ARCHITECT** | AGENT-ARCHITECT + ORCHESTRATOR + MCP | Agent design, system evolution, MCP tools, fleet optimization, orchestration | ANY system design or agent improvement task |
| **OMEGA-ENGINEER** | CODE + DATA + SECURITY | Write code, fix bugs, optimize queries, refactor, code review, security audit | ANY coding, database, or security task |
| **OMEGA-SENTINEL** | MEMORY + DEVOPS + WRITING | System health, monitoring, backup, memory management, documentation | ANY maintenance, monitoring, or documentation task |

### IQ Boost Patterns (Apply to ALL OMEGA interactions)
1. **Chain-of-Thought** — Reason step-by-step before acting
2. **Self-Reflection** — Verify outputs against quality gates before delivering
3. **Anti-Hallucination** — Every fact DB-grounded, every citation verified, every stat traceable
4. **Cross-Skill Fusion** — OMEGA skills automatically invoke each other when needed
5. **Adaptive Depth** — Scale detail based on task complexity (simple → concise, complex → exhaustive)

## 12 OMEGA Skills (Direct Invocation)

### Tier 1 — Litigation Core
| Skill | Triggers | Fuses |
|-------|----------|-------|
| `OMEGA-LITIGATION` | Court documents, IRAC, motions, scoring, legal strategy | 8 skills |
| `OMEGA-EVIDENCE` | Evidence processing, dedup, exhibits, Bates stamps, chain of custody | 10 skills |
| `OMEGA-RESEARCH` | Legal research, RAG, citation verification, case law, gap analysis | 12 skills |

### Tier 2 — Agent Intelligence
| Skill | Triggers | Fuses |
|-------|----------|-------|
| `OMEGA-AGENT-ARCHITECT` | Agent design, multi-agent patterns, evaluation, tool building | 21 skills |
| `OMEGA-ORCHESTRATOR` | Workflow execution, task decomposition, checkpoint/resume, context management | 17 skills |
| `OMEGA-MEMORY` | Memory systems, embeddings, cross-session recall, context optimization | 13 skills |

### Tier 3 — Engineering
| Skill | Triggers | Fuses |
|-------|----------|-------|
| `OMEGA-CODE` | Python, TypeScript, clean code, refactoring, TDD, debugging | 41 skills |
| `OMEGA-DATA` | SQLite, queries, optimization, schema management, FTS5 | 13 skills |
| `OMEGA-MCP` | MCP servers, tool design, FastMCP, multi-language generators | 13 skills |

### Tier 4 — Operations
| Skill | Triggers | Fuses |
|-------|----------|-------|
| `OMEGA-SECURITY` | Security audit, OWASP, PII protection, incident response | 29 skills |
| `OMEGA-DEVOPS` | Git, CI/CD, deployment, observability, backup, system health | 23 skills |
| `OMEGA-WRITING` | Documentation, README, specs, reports, case summaries, wiki | 17 skills |

---

## Legacy Agent Activation Map (Specialized — Use When OMEGA Doesn't Cover)

### Filing & Court Operations
| Agent | Trigger | Use When |
|-------|---------|----------|
| **michigan-litigation-orchestrator** | Filing packages, COA dockets, record organization | Multi-step filing workflows requiring compliance proofs |
| **court-form-finder** | Form identification | Need Michigan court form numbers (MC, DC, CC, COA forms) |
| **pre-filing-qa** | Quality assurance | Before any court filing — generates GO/NO-GO report |
| **filing-countdown** | Deadline monitoring | Display urgency levels for all active deadlines |
| **exhibit-formatter** | Bates stamps, tabs, indexes | Formatting exhibits for court submission |
| **service-tracker** | Proof of service | Track service status across all cases/courts |

### Legal Research & Analysis
| Agent | Trigger | Use When |
|-------|---------|----------|
| **legal-research-deep** | Authority research, case law | Multi-source legal research with relevance ranking |
| **transcript-analyzer** | Hearing transcripts | Extract testimony, rulings, objections from transcripts |
| **order-compliance-monitor** | Court order compliance | Track compliance with existing orders by all parties |
| **cost-tracker** | Litigation costs | Filing fees, service costs, copies, mileage |

### Code & Architecture
| Agent | Trigger | Use When |
|-------|---------|----------|
| **context-architect** | Multi-file changes | Planning changes that span multiple files |
| **debug** | Bug investigation | Finding and fixing application bugs |
| **janitor** | Cleanup, tech debt | Code cleanup, simplification, dead code removal |
| **principal-software-engineer** | Architecture decisions | Engineering excellence, system design |
| **planner** | Implementation plans | Feature planning, refactoring strategies |
| **critical-thinking** | Challenge assumptions | Stress-test ideas, find flaws and edge cases |
| **devils-advocate** | Risk assessment | Counter-arguments, worst-case analysis |

### Document Processing
| Agent | Trigger | Use When |
|-------|---------|----------|
| **redaction-agent** | PII removal | Auto-redact sensitive information before e-filing |
| **legal-phase-indexer** | Complex workflows | Structure, parse, organize litigation phases |

## OMEGA Skill Activation Triggers (Replaces Legacy Skill Map)

> **200+ source skills condensed into 12 OMEGA skills.** Invoke OMEGA skills for any task
> matching their triggers. Individual source skills remain in `skills/agents/` for edge cases.

| OMEGA Skill | Replaces | Trigger Keywords |
|-------------|----------|-----------------|
| `OMEGA-LITIGATION` | michigan-litigation-writer, legal-advisor, omega-scoring | Court doc, motion, brief, IRAC, filing, scoring |
| `OMEGA-EVIDENCE` | drive-forensic-scanner, file-organizer, pdf, docx | Evidence, dedup, exhibit, scan, classify |
| `OMEGA-RESEARCH` | deep-research, rag-engineer, exa-search | Research, citation, case law, authority, RAG |
| `OMEGA-AGENT-ARCHITECT` | ai-agents-architect, agent-orchestration-*, crewai, langgraph | Agent design, orchestration, evaluation, tool building |
| `OMEGA-ORCHESTRATOR` | executing-plans, workflow-*, conductor-*, context-* | Plan, execute, workflow, checkpoint, context |
| `OMEGA-MEMORY` | agent-memory-*, remember, memory-merger | Memory, recall, embedding, context save |
| `OMEGA-CODE` | python-pro, typescript-pro, clean-code, refactor-*, tdd-* | Code, debug, test, refactor, review |
| `OMEGA-DATA` | sql-pro, database-*, postgresql-* | SQL, database, query, schema, optimize |
| `OMEGA-MCP` | mcp-builder, *-mcp-server-generator | MCP, tool, server, FastMCP |
| `OMEGA-SECURITY` | security-*, pentest-*, incident-response-* | Security, audit, vulnerability, PII |
| `OMEGA-DEVOPS` | github-*, git-*, docker-*, deployment-*, observability-* | Git, CI/CD, deploy, monitor, backup |
| `OMEGA-WRITING` | documentation-*, create-readme, wiki-* | Docs, README, spec, report, wiki |

## Six Case Lanes — Agent Routing (OMEGA-Enhanced)

When processing evidence or filings, route to the correct lane:

| Lane | Case | OMEGA Agent | Legacy Specialists |
|------|------|-------------|-------------------|
| **A** (Custody) | 2024-001507-DC | OMEGA-LITIGATOR | filing-countdown |
| **B** (Housing) | 2025-002760-CZ | OMEGA-LITIGATOR | cost-tracker |
| **D** (PPO) | 2023-5907-PP | OMEGA-LITIGATOR | service-tracker |
| **E** (Misconduct) | Judge McNeill | OMEGA-LITIGATOR + OMEGA-RESEARCH | transcript-analyzer |
| **F** (Appellate) | COA 366810 | OMEGA-LITIGATOR + OMEGA-RESEARCH | exhibit-formatter |
| **C** (Convergence) | Multi-lane | OMEGA-ARCHITECT | legal-phase-indexer |

## Session Budget Rules (v2.0 — EXPANDED, aligned with eagain-prevention.instructions.md v2.0)

> **v2.0 KEY INSIGHT:** Shells and agents have SEPARATE pipe budgets.
> Shells = SHARED pipes (EAGAIN risk). Agents = ISOLATED pipes (safe to expand).
> See eagain-prevention.instructions.md v2.0 for engineering proof.

### Shell Budget (SHARED pipes — conservative)
- **Max 2 async shells** concurrent (unchanged — these are the ONLY EAGAIN vector)
- **2-second cooldown** between shell spawns
- **Output cap**: All shell commands must limit output to ~100 lines max
- **Large output**: Redirect to temp file → read with view tool (bypasses pipes entirely)
- **Limit to 50 powershell sessions per session** (reserve for interactive/async needs)

### Agent Budget (ISOLATED pipes — expanded)
- **Max 3 parallel sub-agents** (expanded from 2 — isolated pipes are safe)
- **1-second cooldown** between agent spawns (reduced from 2s)
- **Can spawn 2 agents in parallel** in one tool call (they don't interfere with each other)
- **Can spawn 1 shell + 1 agent** in same tool call (different pipe pools)

### Combined Limits
- **Max 5 total concurrent** (2 shells + 3 agents)
- **Checkpoint every 3 agent completions** to SQL todos table
- **Prefer MCP tools** over powershell for ALL command execution
- **Dynamic throttle**: If EAGAIN symptoms appear, auto-reduce to shells:1 agents:2 (see EAGAIN protocol)
