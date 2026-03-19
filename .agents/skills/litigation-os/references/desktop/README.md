# LitigationOS-Desktop Architecture

## Stack

- **Frontend**: Electron 28 + React 18 + Redux + Tailwind CSS + Vite 5
- **Backend**: Node.js Express + SQLite + Better-SQLite3 + optional Neo4j
- **AI Agents**: 7 Python agents via child_process
- **Real-time**: Socket.io for live updates
- **Queues**: Bull job queues for background processing
- **API**: GraphQL + REST endpoints

## 7 AI Agents (Python)

| Agent | Role |
|-------|------|
| `evidence_analyst.py` | Evidence analysis + scoring |
| `judicial_misconduct.py` | Judge bias/misconduct pattern detection |
| `procedural_compliance.py` | MCR/MCL compliance checking |
| `appellate_specialist.py` | Appellate strategy + brief drafting |
| `citation_verifier.py` | Citation accuracy verification |
| `harm_quantifier.py` | Damages calculation |
| `quality_validator.py` | Filing quality assurance |

## Key Services

- `agentBuilderService.js` — No-code agent template builder
- `omegaPipelineService.js` — OMEGA pipeline orchestration (Phase 16)
- Bull job queues for long-running tasks
- Multi-LLM orchestration (Claude, GPT, Gemini)

## Product Tiers

| Tier | Price | Features |
|------|-------|----------|
| Lite | $29/mo | Basic filing assistant |
| Pro | $99/mo | Full AI analysis + drafting |
| Enterprise | $299/mo | Multi-case + team + API |

## Location

`C:\Users\andre\LITIGATIONOS_MASTER\LitigationOS-Desktop\`

See [pipeline-integration.md](pipeline-integration.md) for OMEGA pipeline UI blueprint.
