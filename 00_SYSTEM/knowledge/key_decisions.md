# LitigationOS — Key Technical Decisions

## Decision Log

This document records important technical decisions, the alternatives considered,
and the reasoning behind each choice. Decisions are numbered for reference.

---

### KD-001: SQLite over PostgreSQL

**Date:** Project inception
**Status:** Accepted

**Decision:** Use SQLite as the primary relational database.

**Alternatives considered:**
| Option | Pros | Cons |
|--------|------|------|
| PostgreSQL | Mature, concurrent writes, replication | Requires server, complex setup |
| MySQL | Widely supported, good tooling | Server dependency, licensing |
| SQLite | Zero-config, portable, single-file | Limited concurrency, no server features |

**Why SQLite:**
- Litigation teams are typically 1-5 people — concurrency is not a bottleneck
- Single-file database means case data is trivially portable
- No database server reduces attack surface and maintenance burden
- `better-sqlite3` provides synchronous, high-performance access
- WAL mode provides sufficient concurrent read performance

---

### KD-002: Neo4j over Graph Extensions

**Date:** Phase 5
**Status:** Accepted

**Decision:** Use standalone Neo4j rather than PostgreSQL graph extensions (AGE) or in-memory graphs.

**Alternatives considered:**
| Option | Pros | Cons |
|--------|------|------|
| Apache AGE (PG extension) | Single database | Immature, limited ecosystem |
| NetworkX (in-memory) | No server needed | Not persistent, memory-limited |
| Neo4j Community | Best graph DB, Cypher, APOC | Additional service to manage |

**Why Neo4j:**
- Cypher is significantly more readable than graph SQL extensions
- APOC library provides algorithms litigation analysis needs
- Community Edition is free and sufficient
- Graph visualization tools integrate natively
- Docker makes deployment trivial

---

### KD-003: OMEGA Composite Scoring

**Date:** Phase 3
**Status:** Accepted

**Decision:** Create a unified multi-dimensional scoring system rather than separate scores.

**Why composite:**
- Legal teams need a single "glance score" for triage
- Decomposable dimensions allow deep-dive analysis
- Weighted scoring lets teams customize priorities per case
- Automated recalculation keeps scores current without manual effort
- Score history enables trend analysis

---

### KD-004: Next.js App Router

**Date:** Phase 7
**Status:** Accepted

**Alternatives considered:**
| Option | Pros | Cons |
|--------|------|------|
| Next.js App Router | RSC, streaming, Vercel-native | Newer, evolving API |
| Next.js Pages Router | Stable, well-documented | No RSC, older patterns |
| Remix | Nested routes, progressive | Smaller ecosystem |
| Express + React SPA | Full control | No SSR without effort |

**Why App Router:**
- Server Components can query SQLite directly — no API layer needed for reads
- Streaming allows progressive rendering of large evidence tables
- Layouts enable consistent navigation without re-renders
- Vercel deployment is zero-config

---

### KD-005: Chalk 4.x (CommonJS) for CLI

**Date:** Phase 11
**Status:** Accepted

**Decision:** Pin CLI to Chalk 4.x (CommonJS) rather than Chalk 5+ (ESM-only).

**Why:**
- CLI uses `#!/usr/bin/env node` with CommonJS `require()`
- Chalk 5+ is ESM-only, requiring import/module changes throughout
- Chalk 4.x is stable, fully featured, and widely compatible
- Avoids forcing ESM migration on the CLI tool

---

### KD-006: Docker Multi-Stage Build

**Date:** Phase 11
**Status:** Accepted

**Decision:** Use three-stage Docker build (deps → build → runtime).

**Why:**
- Stage 1 (deps): Installs native dependencies with build tools
- Stage 2 (build): Compiles Next.js with full node_modules
- Stage 3 (runtime): Minimal Alpine image with only production artifacts
- Final image is ~150MB instead of ~1.5GB
- `better-sqlite3` native bindings compiled in deps stage

---

### KD-007: Backup Strategy — Incremental + Full

**Date:** Phase 12
**Status:** Accepted

**Decision:** Daily incremental backups with weekly full backups.

**Retention:** 14 days daily, 90 days weekly.

**Why:**
- SQLite `.backup` command provides atomic point-in-time copies
- Daily incremental catches all changes without excessive storage
- Weekly full backup provides clean restore points
- 14/90 day retention balances storage cost with legal hold requirements
- Evidence data retention is set to "forever" — never auto-deleted

---

### KD-008: MIT License for Open Source Core

**Date:** Phase 13
**Status:** Accepted

**Alternatives considered:**
| License | Pros | Cons |
|---------|------|------|
| MIT | Maximum adoption, simple | No copyleft protection |
| Apache 2.0 | Patent grant, corporate-friendly | More complex |
| AGPL | Strong copyleft, SaaS protection | Deters corporate adoption |
| BSL | Source-available, delayed open source | Non-standard |

**Why MIT:**
- Maximizes community adoption and contribution
- Legal teams are already cautious — simplest license reduces friction
- No patent concerns for a litigation tool
- Commercial extensions can use proprietary licensing separately

---

### KD-009: Agent-Based Architecture with Audit Logging

**Date:** Phase 5-6
**Status:** Accepted

**Decision:** All autonomous agents must produce comprehensive audit logs.

**Why:**
- Legal proceedings require demonstrable chain of custody
- Automated actions must be attributable and reviewable
- Audit logs serve as evidence of system behavior
- Regulatory compliance may require action history
- Debugging autonomous agents requires detailed execution traces

---

### KD-010: Self-Hosted Default with Cloud Option

**Date:** Phase 11
**Status:** Accepted

**Decision:** Design for self-hosted deployment first; cloud deployment is optional.

**Why:**
- Litigation data is among the most sensitive data categories
- Many law firms have strict data residency requirements
- Self-hosted eliminates third-party data access concerns
- Docker Compose provides one-command deployment
- Vercel config exists for teams that choose managed hosting
- No vendor lock-in on any specific cloud provider
