# Changelog

All notable changes to LitigationOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] — 2026-03-12

### 🏆 Golden Master Release

LitigationOS v0.9.0 — stabilized Golden Master with verified filing packages, 539 passing tests, and full chronicle upgrade.

### Added
- **SUBMIT_THIS/ folder** — Court-ready COA 366810 filing package (brief + appendix + PoS + cover)
- **docs/REFERENCE_CATALOG.md** — Canonical reference for all engines, agents, modules, and directory structure
- **Pre-filing QA system** — GO/CONDITIONAL/NO-GO verdicts with MCR 7.212 compliance checking
- **PII protection** — .gitignore entries for sensitive litigation data patterns

### Fixed
- **CRITICAL: Party name correction** — Changed "Tiffany A. Watson" to "Emily A. Watson" in COA brief (8 instances)
- **config/paths.yaml** — Corrected canonical_root from Desktop path to C:\Users\andre\LitigationOS
- **Copilot instructions v19.1** — Removed 496 lines of duplicate reference catalogs, de-hardcoded all statistics, promoted zero-shell EAGAIN prevention

### Changed
- Product app version bumped from 0.2.0 → 0.9.0
- Instructions file reduced from 909 → 413 lines (behavioral rules preserved, bloat removed)
- All hardcoded DB statistics replaced with runtime query commands

### Verified
- 539 product app tests passing
- DB integrity: 772 tables, 11.46 GB, 18.5M rows
- DB backup: I:\litigation_context_v0.9.0_backup.db (verified size match)
- .env properly gitignored and untracked
- MCP server paths verified (two implementations: litigation_context.db + formos_v2.db noted)

## [1.0.0] — 2025-01-01

### 🎉 Initial Release

LitigationOS v1.0.0 — AI-powered litigation management platform.

### Added

#### Core Platform
- **Dashboard** — Central command view with case overview, recent activity, and system health
- **Evidence Management** — Full evidence lifecycle: intake, categorization, chain of custody tracking
- **Timeline Engine** — Chronological event mapping with multi-case correlation
- **Document Forge** — Automated legal document generation (v18/v19 engines)

#### OMEGA Scoring Engine
- **Multi-dimensional scoring** — Evidence strength, relevance, credibility, and impact analysis
- **Automated recalculation** — Periodic score updates based on new evidence and connections
- **Confidence thresholds** — Configurable minimum confidence for automated assessments
- **Visual score indicators** — Color-coded scoring with trend visualization

#### Knowledge Graph (Neo4j)
- **Entity relationship mapping** — People, organizations, events, documents connected
- **Authority ingestion** — Automated legal authority import and citation linking
- **Pattern detection** — Cross-case pattern recognition and anomaly flagging

#### AI Integration
- **LLM-powered analysis** — GPT-4o integration for evidence analysis and summarization
- **Natural language search** — Query evidence and documents in plain English
- **Automated categorization** — AI-driven evidence classification and tagging

#### Infrastructure
- **SQLite primary database** — Zero-configuration, portable, WAL-mode enabled
- **Neo4j graph database** — Relationship-centric data for entity networks
- **Docker deployment** — Full containerized stack (web + Neo4j + backup)
- **Vercel deployment** — Serverless deployment configuration
- **Automated backups** — Daily incremental, weekly full, configurable retention
- **CLI tool (`litigos`)** — Command-line access to system status, OMEGA scores, search, and deadlines

#### Pipeline & Automation
- **Watchdog service** — File system monitoring for new evidence intake
- **CyclePacks** — Inventory management and batch processing
- **Autopilot suite** — Autonomous litigation workflow agents

#### Security
- **Security headers** — HSTS, CSP, XSS protection, frame denial
- **Rate limiting** — Configurable request throttling
- **Session management** — Secure session handling with NextAuth.js

### Architecture
- 13-phase modular build (00_SYSTEM through 13_TOOLS)
- Numeric prefix directory organization for case isolation
- Agent-based architecture for autonomous operations
- Knowledge preservation system for institutional memory
