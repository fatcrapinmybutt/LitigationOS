# Fleet Architecture — 25 Agent Skills

## Overview

The litigation-os fleet consists of 1 core skill (this one) + 25 specialized agent skills organized in 3 tiers. Each skill is independently invocable and follows the writing-skills standard.

## Tier Summary

| Tier | Purpose | Skills | Files |
|------|---------|--------|-------|
| **I: Operational Warfare** | Core litigation operations | 10 | 50 |
| **II: Supreme Domination** | Higher courts + specialized domains | 10 | 57 |
| **III: The Lawsuit Forge** | New lawsuit creation lifecycle | 5 | 37 |

## Fleet Manifest

### Tier I: Operational Warfare
| # | Skill | Trigger Keywords |
|---|-------|-----------------|
| 1 | `litigation-filing-architect` | filing, VehicleMap, court document |
| 2 | `litigation-red-team` | stress test, adversarial, weakness |
| 3 | `litigation-judicial-analyst` | judge, bias, misconduct, Canon |
| 4 | `litigation-impeachment-engine` | impeachment, contradiction, transcript |
| 5 | `litigation-evidence-harvester` | scan, classify, extract, OCR |
| 6 | `litigation-authority-validator` | citation, MCR, MCL, verify |
| 7 | `litigation-convergence-orchestrator` | converge, quality, emergence |
| 8 | `litigation-pipeline-commander` | OMEGA, pipeline, phase |
| 9 | `litigation-appellate-strategist` | appeal, COA, brief, record |
| 10 | `litigation-skill-auditor` | audit, compliance, fleet health |

### Tier II: Supreme Domination
| # | Skill | Trigger Keywords |
|---|-------|-----------------|
| ★11 | `litigation-supreme-court-architect` | MSC, Supreme Court, MCR 7.3xx, bypass, leave |
| 12 | `litigation-federal-civil-rights` | 1983, civil rights, immunity, Rooker-Feldman |
| 13 | `litigation-discovery-warfare` | interrogatory, RFP, RFA, subpoena, compel |
| 14 | `litigation-sanctions-engine` | sanctions, fees, contempt, MCR 2.114 |
| 15 | `litigation-custody-specialist` | custody, parenting time, best interest, FOC |
| 16 | `litigation-ppo-specialist` | PPO, bond, protection order |
| 17 | `litigation-harm-quantifier` | damages, harm, emotional distress, per diem |
| 18 | `litigation-brief-writer` | brief, argument, persuasion, writing |
| 19 | `litigation-record-builder` | record, transcript, exhibit, appeal |
| 20 | `litigation-pro-se-guardian` | pro se, self-represented, fee waiver |

### Tier III: The Lawsuit Forge
| # | Skill | Trigger Keywords |
|---|-------|-----------------|
| ★21 | `litigation-lawsuit-forge` | new lawsuit, complaint, new claim, sue |
| 22 | `litigation-cause-of-action-library` | cause of action, elements, tort, statutory |
| 23 | `litigation-complaint-drafter` | complaint, verified complaint, count, prayer |
| 24 | `litigation-claim-researcher` | research, viable claims, fact mapping |
| 25 | `litigation-service-engine` | service, serve, proof of service, MC 12 |

## Dispatching

See [dispatch-matrix.md](dispatch-matrix.md) for routing rules.
See [coordination-protocol.md](coordination-protocol.md) for handoff patterns.
