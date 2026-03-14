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

## Custom Agent Activation Map

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

## Skill Activation Triggers

### Litigation-Relevant Skills (from 900+ available)
| Skill | Trigger Keywords | Use When |
|-------|-----------------|----------|
| `mcp-builder` | Build MCP server, create tools | Adding new MCP tools or servers |
| `executing-plans` | Execute plan, implement | Running an approved plan with checkpoints |
| `agent-orchestration-multi-agent-optimize` | Optimize agents, improve fleet | Improving multi-agent performance |
| `agent-orchestration-improve-agent` | Improve agent, fix agent | Optimizing a specific agent's performance |
| `accessibility-compliance` | ADA, WCAG, accessible | Making filings accessible |

## Six Case Lanes — Agent Routing

When processing evidence or filings, route to the correct lane:

| Lane | Case | Agents to Engage |
|------|------|-----------------|
| **A** (Custody) | 2024-001507-DC | michigan-litigation-orchestrator, filing-countdown |
| **B** (Housing) | 2025-002760-CZ | michigan-litigation-orchestrator, cost-tracker |
| **D** (PPO) | 2023-5907-PP | michigan-litigation-orchestrator, service-tracker |
| **E** (Misconduct) | Judge McNeill | legal-research-deep, transcript-analyzer |
| **F** (Appellate) | COA 366810 | legal-research-deep, exhibit-formatter |
| **C** (Convergence) | Multi-lane | context-architect, legal-phase-indexer |

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
