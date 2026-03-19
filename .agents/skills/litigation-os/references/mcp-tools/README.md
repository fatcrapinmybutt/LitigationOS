# MCP Tools — 31-Tool Catalog

## Tool Categories

| Category | Count | Reference |
|----------|-------|-----------|
| PDF Knowledge Base | 8 | [pdf-knowledge.md](pdf-knowledge.md) |
| Knowledge Graph | 4 | [knowledge-graph.md](knowledge-graph.md) |
| Self-Awareness | 3 | Below |
| SUPERPIN | 2 | Below |
| Evolution Pipeline | 5 | [evolution.md](evolution.md) |
| Health | 1 | Below |
| GOD-Level | 8 | [god-level.md](god-level.md) |

## Self-Awareness (3)

| Tool | Purpose |
|------|---------|
| `litigation_self_test` | Validate entire stack (DB, FTS5, graphs, PDFs) |
| `litigation_self_audit` | Data quality analysis (score 0-100) |
| `litigation_convergence_status` | DNEW / BLOCKERS / NEXT_PATCH report |

## SUPERPIN (2)

| Tool | Purpose |
|------|---------|
| `litigation_get_vehicle_map` | Relief → Vehicle → Authority → Elements → Deadlines |
| `litigation_get_subagent_spec` | Agent role, inputs, outputs from 50+ swarm |

## Health (1)

| Tool | Purpose |
|------|---------|
| `litigation_health` | Circuit breaker status, 24h error telemetry, reset |

## Workflow Patterns

**Searching for information:**
- Court rules → `litigation_lookup_rule` or `litigation_lookup_authority`
- Evidence → `litigation_search` (PDF) or `litigation_search_evolved` (all)
- Knowledge graph → `litigation_query_graph`
- Cross-references → `litigation_cross_refs`

**Building a filing:**
1. `litigation_get_vehicle_map` → identify relief + vehicle
2. `litigation_lookup_authority` → pin cites
3. `litigation_assess_risk` → risk events + cure steps
4. `litigation_deadlines` → temporal reasoning
5. `litigation_red_team` → structural validation
6. `litigation_evidence_chain` → exhibit linking

**Ingesting content:**
- PDFs → `litigation_ingest_pdf` or `litigation_bulk_ingest`
- TXT/MD → `litigation_evolve_files`
- CSV → `litigation_ingest_csv`
- Already-ingested → `litigation_evolve_pdfs`

**System health:**
- Quick → `litigation_self_test`
- Quality → `litigation_self_audit`
- Convergence → `litigation_convergence_status`
- Errors → `litigation_health`
- Stats → `litigation_evolution_stats` or `litigation_get_stats`
