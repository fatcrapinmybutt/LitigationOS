# LitigationOS — Architecture Decisions & Rationale

## System Overview

LitigationOS is a 13-phase modular litigation management platform built for AI-powered
legal analysis, evidence management, and case strategy optimization.

```
┌─────────────────────────────────────────────────────┐
│                    LitigationOS                      │
├──────────┬──────────┬──────────┬────────────────────┤
│ Dashboard│ Evidence │ Timeline │ Document Forge     │
├──────────┴──────────┴──────────┴────────────────────┤
│              OMEGA Scoring Engine                    │
├─────────────────────┬───────────────────────────────┤
│    SQLite (Primary)  │   Neo4j (Knowledge Graph)    │
├─────────────────────┴───────────────────────────────┤
│         Pipeline / Watchdog / Agents                 │
└─────────────────────────────────────────────────────┘
```

## Key Architecture Decisions

### ADR-001: SQLite as Primary Database

**Decision:** Use SQLite instead of PostgreSQL/MySQL for the primary data store.

**Context:** Litigation data is document-heavy with moderate write concurrency. The system
needs to be portable, self-contained, and deployable without external database servers.

**Rationale:**
- Zero configuration — no database server to install or manage
- Single-file database — trivially portable and backupable
- WAL mode enables concurrent reads during writes
- `better-sqlite3` provides synchronous, fast access from Node.js
- Evidence integrity benefits from file-level atomicity
- Databases can be case-isolated (one DB per case if needed)

**Trade-offs:**
- Limited write concurrency (WAL helps but doesn't eliminate)
- No built-in replication (handled by backup service)
- Not suitable for high-traffic multi-user scenarios (acceptable for litigation teams)

### ADR-002: Neo4j for Knowledge Graph

**Decision:** Use Neo4j Community Edition for entity relationship mapping.

**Context:** Legal cases involve complex many-to-many relationships between people,
organizations, events, documents, and legal authorities. Relational queries become
unwieldy for graph traversal.

**Rationale:**
- Native graph traversal is orders of magnitude faster than SQL JOINs for relationship queries
- Cypher query language is intuitive for legal relationship patterns
- APOC library provides advanced graph algorithms (centrality, community detection)
- Pattern matching across cases reveals connections SQL would miss
- Visual graph exploration aids legal strategy

### ADR-003: Numeric Prefix Directory Structure

**Decision:** Organize the project using `NN_NAME` directory prefixes (00-13).

**Rationale:**
- Deterministic sort order in all file managers and CLIs
- Clear phase/module boundaries
- Case directories are physically isolated
- Easy to navigate: `00` = system, `01-06` = cases, `07-08` = processing, `09` = data, etc.
- New phases append without disrupting existing structure

### ADR-004: OMEGA Scoring as Central Metric

**Decision:** Build a unified scoring engine (OMEGA) that evaluates evidence across
multiple dimensions simultaneously.

**Dimensions:**
- **O**rigin — Source reliability and authentication
- **M**ateriality — Relevance to case elements
- **E**videntiary weight — Legal admissibility strength
- **G**raph connectivity — Relationship density in knowledge graph
- **A**ttention — Temporal urgency and deadline proximity

**Rationale:**
- Single composite score enables rapid triage
- Multi-dimensional decomposition supports detailed analysis
- Automated recalculation keeps scores current
- Threshold-based alerts prevent missed critical evidence

### ADR-005: Agent-Based Architecture

**Decision:** Use autonomous agents for repetitive litigation workflows.

**Components:**
- **Watchdog** — Monitors file system for new evidence intake
- **Autopilot Suite** — Task-specific autonomous agents
- **Pipeline** — Sequential processing stages for document ingestion

**Rationale:**
- Litigation involves repetitive, time-sensitive tasks
- Agents can work 24/7 on categorization, scoring, and alerting
- Human review is reserved for high-stakes decisions
- Agent logs provide audit trail for all automated actions

### ADR-006: Document Forge Versioning

**Decision:** Maintain multiple DocForge engine versions (v18, v19) simultaneously.

**Rationale:**
- Legal documents have strict formatting requirements
- Older filings must be reproducible exactly as generated
- Version coexistence allows gradual migration
- Template evolution doesn't break existing document references

### ADR-007: Next.js with App Router

**Decision:** Use Next.js (App Router) as the web framework.

**Rationale:**
- Server Components reduce client-side JavaScript
- Built-in API routes eliminate separate backend server
- Static generation for documentation pages
- Vercel deployment is zero-config
- React Server Components can query SQLite directly

### ADR-008: Self-Hosted First, Cloud Optional

**Decision:** Design for self-hosted deployment with cloud as an option.

**Rationale:**
- Litigation data is highly sensitive — many firms require on-premises
- Docker Compose provides full stack in one command
- SQLite portability means the entire database is one file
- Vercel config exists for teams that prefer managed hosting
- No vendor lock-in on any cloud provider

## Data Flow

```
Evidence Intake → Watchdog → Pipeline → Categorization → OMEGA Scoring
                                                              ↓
                                              Knowledge Graph Update
                                                              ↓
                                              Dashboard / Timeline / Alerts
```

## Security Model

- All API endpoints require authentication (NextAuth.js)
- Security headers enforced at deployment layer (Vercel/Docker)
- Rate limiting prevents abuse
- SQLite databases are file-permission controlled
- Neo4j requires authentication for all connections
- Backup encryption recommended for cloud storage
