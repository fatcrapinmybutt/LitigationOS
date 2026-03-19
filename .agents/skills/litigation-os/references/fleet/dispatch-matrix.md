# Fleet Dispatch Matrix

## Routing Rules

When the core litigation-os skill identifies a task, it dispatches to the most specific fleet agent.

### By Task Type

| Task | Primary Agent | Secondary |
|------|--------------|-----------|
| **Build a filing** | litigation-filing-architect | litigation-brief-writer |
| **New lawsuit/complaint** | litigation-lawsuit-forge | litigation-complaint-drafter |
| **Identify viable claims** | litigation-claim-researcher | litigation-cause-of-action-library |
| **Verify citations** | litigation-authority-validator | — |
| **Analyze a judge** | litigation-judicial-analyst | — |
| **Find contradictions** | litigation-impeachment-engine | — |
| **Scan new evidence** | litigation-evidence-harvester | litigation-pipeline-commander |
| **Stress-test a filing** | litigation-red-team | — |
| **Run convergence** | litigation-convergence-orchestrator | — |
| **Execute pipeline** | litigation-pipeline-commander | — |
| **Prepare appeal** | litigation-appellate-strategist | litigation-record-builder |
| **File in MSC** | litigation-supreme-court-architect | — |
| **42 USC 1983 action** | litigation-federal-civil-rights | litigation-lawsuit-forge |
| **Draft discovery** | litigation-discovery-warfare | — |
| **Seek sanctions** | litigation-sanctions-engine | — |
| **Custody matters** | litigation-custody-specialist | — |
| **PPO matters** | litigation-ppo-specialist | — |
| **Calculate damages** | litigation-harm-quantifier | — |
| **Write brief/motion** | litigation-brief-writer | — |
| **Build record** | litigation-record-builder | — |
| **Pro se guidance** | litigation-pro-se-guardian | — |
| **Serve process** | litigation-service-engine | — |
| **Audit fleet health** | litigation-skill-auditor | — |

### By Court Level

| Court | Primary Agents |
|-------|---------------|
| **Circuit Court (Trial)** | filing-architect, brief-writer, discovery-warfare |
| **Court of Appeals (COA)** | appellate-strategist, record-builder, brief-writer |
| **Supreme Court (MSC)** | supreme-court-architect, appellate-strategist |
| **Judicial Tenure (JTC)** | judicial-analyst, filing-architect |
| **Federal (W.D. Mich.)** | federal-civil-rights, lawsuit-forge |

### By Case Lane

| Lane | Primary Agents |
|------|---------------|
| **A: Custody** | custody-specialist, ppo-specialist, harm-quantifier |
| **B: Housing** | lawsuit-forge, cause-of-action-library, harm-quantifier |
| **C: Convergence** | judicial-analyst, federal-civil-rights, sanctions-engine |

## Multi-Agent Chains

Complex tasks dispatch to multiple agents in sequence:

```
New Lawsuit:
  claim-researcher → cause-of-action-library → lawsuit-forge → complaint-drafter → red-team → service-engine

Appeal:
  record-builder → appellate-strategist → brief-writer → red-team

MSC Application:
  supreme-court-architect → brief-writer → red-team → service-engine

Convergence Cycle:
  convergence-orchestrator → evidence-harvester → authority-validator → pipeline-commander
```
