---
description: Agent activation matrix for LitigationOS. Maps custom agents to litigation workflows.
applyTo: "**/*"
---

# Agent Activation Matrix — LitigationOS

## ⚡ TOOL ROUTING (MANDATORY)

**Prefer NEXUS daemon tools over `litigation_context-*` MCP tools.** All 38 MCP capabilities have been ABSORBED into the local NEXUS v2 persistent daemon (51 total handlers, warm connections, 100× faster). MCP tools still work as fallback but are slow (spawn-per-call).
Use local SINGULARITY extension tools first: `query_litigation_db`, `search_evidence`, `search_impeachment`, `search_contradictions`, `search_authority_chains`, `nexus_fuse`, `nexus_argue`, `nexus_readiness`, `nexus_damages`, `lexos_narrative`, `lexos_adversary`, `lexos_filing_plan`, `lexos_rules_check`, `lexos_gap_analysis`, `lexos_cross_connect`, `judicial_intel`, `timeline_search`, `case_context`, `filing_status`, `check_deadlines`, plus 27 absorbed capabilities (list_documents, get_document, search_documents, lookup_rule, query_graph, lookup_authority, assess_risk, get_vehicle_map, case_health, adversary_threats, filing_pipeline, get_subagent_spec, evolution_stats, search_evolved, cross_refs, convergence_status, stats_extended, self_test, query_master, vector_search, self_audit, evidence_chain, compute_deadlines, red_team).

For execution: `exec_python` > `exec_git` > `exec_command` > `powershell` (last resort).

## Skills → SINGULARITY (see copilot-instructions.md for full taxonomy)

All litigation tasks route through **SINGULARITY** superskills (15 skills, 5 tiers).
See `.agents/skills/SINGULARITY-*/SKILL.md` for domain-specific guidance.

## Active Agent Fleet (28 Agents)

> **All legacy agents (54) were consolidated into 28 active agents in `.agents/agents/`.**
> Do NOT reference archived agents — they no longer exist as active definitions.

### Filing & Court Operations
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **filing-forge-master** | pre-filing-qa, filing-countdown, exhibit-formatter, service-tracker | Filing packages, QA, Bates stamps, service tracking | Any filing workflow — assembly, validation, service proof |
| **omega-litigation-commander** | michigan-litigation-orchestrator | COA dockets, record organization, multi-step filings | Complex multi-step filing workflows requiring compliance proofs |
| **court-form-finder** | (original — still active) | Form identification | Need Michigan court form numbers (MC, DC, CC, COA forms) |
| **appellate-record-builder** | (new) | COA/MSC record assembly | Building appendices, lower court record compilation |
| **contempt-prosecutor** | (new) | Contempt motions, show cause | Enforcing court order violations |
| **garnishment-specialist** | (new) | Garnishment, wage orders | Post-judgment enforcement via garnishment |
| **post-judgment-enforcer** | (new) | Post-judgment motions | Enforcing judgments, collections, compliance |

### Legal Research & Analysis
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **timeline-forensics** | transcript-analyzer, (new) | Hearing transcripts, chronology | Extract testimony, rulings, objections; build timelines |
| **court-order-tracker** | order-compliance-monitor | Court order compliance | Track compliance with existing orders by all parties |
| **damages-calculator** | cost-tracker | Damages, litigation costs | Calculate damages, filing fees, service costs, mileage |
| **case-strategy-architect** | (new) | Case strategy, war planning | High-level litigation strategy and prioritization |
| **settlement-analyzer** | (new) | Settlement evaluation | Analyze settlement offers, counter-proposals |
| **summary-judgment** | (new) | MSJ/SJ motions | Summary judgment analysis, no-genuine-issue arguments |

### Evidence & Investigation
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **evidence-warfare-commander** | (3 old evidence agents) | Evidence strategy, gaps, impeachment | Evidence triage, gap analysis, impeachment prep |
| **evidence-vehicle-scanner** | (new) | PDF scanning, lane routing | Scan PDFs, match evidence to case lanes A-F via MEEK |
| **evidence-authentication** | (new) | Chain of custody, authentication | Proving evidence admissibility and authenticity |
| **parental-alienation-detector** | (new) | Alienation patterns | Detect and document parental alienation indicators |
| **expert-witness-manager** | (new) | Expert witnesses | Manage expert witness selection, reports, Daubert prep |
| **subpoena-engine** | (new) | Subpoenas | Draft and track subpoenas for witnesses/documents |

### Judicial Accountability
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **judicial-accountability-engine** | (new) | JTC complaints, misconduct | Document judicial misconduct, prepare JTC complaints |
| **judicial-recusal-engine** | (new) | Disqualification, recusal | MCR 2.003 disqualification motions, bias documentation |

### Family Law Specialized
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **family-law-guardian** | (new) | Custody, parenting time, GAL | Family-law-specific motions, custody analysis |
| **affidavit-chronology-builder** | (new) | Affidavits, chronology | Mine affidavits/exports, build master chronological narrative |
| **motion-practice** | (new) | General motions | Draft, review, and strengthen any motion type |
| **trial-preparation** | (new) | Trial prep | Witness lists, exhibit lists, trial briefs, voir dire |

### System & Fleet Management
| Agent | Replaces | Trigger | Use When |
|-------|----------|---------|----------|
| **omega-dedup** | (new) | Deduplication | Content-based dedup across drives (NO hashing — peek inside) |
| **self-evolving-fleet-manager** | (new) | Fleet optimization | Monitor, upgrade, and evolve the agent fleet |
| **compliance-auditor** | redaction-agent, (new) | PII, compliance, redaction | Redact PII, audit filing compliance, pre-submission checks |

### Code & Architecture (Built-in Copilot Agents — Always Available)
| Agent | Trigger | Use When |
|-------|---------|----------|
| **context-architect** | Multi-file changes | Planning changes that span multiple files |
| **debug** | Bug investigation | Finding and fixing application bugs |
| **janitor** | Cleanup, tech debt | Code cleanup, simplification, dead code removal |
| **principal-software-engineer** | Architecture decisions | Engineering excellence, system design |
| **planner** | Implementation plans | Feature planning, refactoring strategies |
| **critical-thinking** | Challenge assumptions | Stress-test ideas, find flaws and edge cases |
| **devils-advocate** | Risk assessment | Counter-arguments, worst-case analysis |

## Case Lane Routing

| Lane | Case | Specialist Agent |
|------|------|-----------------|
| **A** (Custody) | 2024-001507-DC | filing-forge-master |
| **B** (Housing) | 2025-002760-CZ | damages-calculator |
| **D** (PPO) | 2023-5907-PP | compliance-auditor |
| **E** (Misconduct) | Judge McNeill | judicial-accountability-engine |
| **F** (Appellate) | COA 366810 | appellate-record-builder |
| **CRIMINAL** | 2025-25245676SM | 100% SEPARATE — zero crossover |

## Evidence Pipeline (MEEK Lane Routing)

Drive scan order: **C:\LitigationOS** → I:\ → D:\ → F:\ → G:\ → J:\
Detection priority: **E → D → F → C → A → B**

| Lane | MEEK | Keywords |
|------|------|---------|
| E (Misconduct) | MEEK4 | McNeill, judicial, bias, JTC, canon, ex parte |
| D (PPO) | MEEK3 | PPO, protection order, 5907, contempt |
| F (Appellate) | MEEK5 | COA, 366810, appeal, appellant, brief |
| C (Federal) | — | Multi-lane, conspiracy, federal, §1983 |
| A (Custody) | MEEK2 | Custody, parenting, 001507, Watson, child |
| B (Housing) | MEEK1 | Shady Oaks, eviction, housing, 002760 |

OCR: pypdfium2 → atomize → lane-classify → dedup (content-based, NOT hash-only — peek inside per user mandate) → Bates stamp (`PIGORS-{LANE}-{NNNNNN}`).
Quality gates: OCR ≥85% confidence, exactly one primary lane, metadata complete (path/size/date/sha256/pages).
