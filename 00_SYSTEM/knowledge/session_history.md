# LitigationOS — Session History & Learnings

## Overview

This document tracks the build sessions for LitigationOS, capturing what was built,
key decisions made, and lessons learned across the 13-phase development process.

---

## Phase 1-2: Foundation & Data Layer

**What was built:**
- Core directory structure with numeric prefix organization (00-13)
- SQLite database schema for litigation context
- Initial data models: cases, evidence, documents, entities
- Database connection layer with `better-sqlite3`

**Key learnings:**
- WAL mode is essential for concurrent dashboard reads during evidence ingestion
- Case-isolated databases simplify backup and portability
- Numeric prefixes keep directory listing predictable across all platforms

---

## Phase 3-4: OMEGA Engine & Evidence Management

**What was built:**
- OMEGA multi-dimensional scoring algorithm
- Evidence intake pipeline with categorization
- Chain of custody tracking
- Automated evidence strength assessment

**Key learnings:**
- Composite scores need decomposable dimensions for legal analysis
- Automated scoring must always be reviewable by humans
- Evidence chain of custody is non-negotiable for admissibility

---

## Phase 5-6: Knowledge Graph & Timeline

**What was built:**
- Neo4j integration for entity relationship mapping
- Timeline engine for chronological event visualization
- Cross-case pattern detection
- Authority ingestion for legal citations

**Key learnings:**
- Graph queries dramatically outperform SQL for relationship traversal
- Timeline visualization requires careful date normalization
- Legal authority relationships form natural graph structures

---

## Phase 7-8: Document Processing & Generation

**What was built:**
- Document Forge v18 and v19 engines
- PDF and text extraction pipeline
- Template-based legal document generation
- Filing automation with format compliance

**Key learnings:**
- Multiple DocForge versions must coexist for reproducibility
- PDF extraction quality varies wildly — fallback strategies essential
- Legal document formatting has zero tolerance for errors

---

## Phase 9-10: AI Integration & Analysis

**What was built:**
- LLM-powered evidence analysis (GPT-4o)
- Natural language search across evidence
- Automated categorization and tagging
- Summary generation for document sets

**Key learnings:**
- AI analysis must be clearly marked as AI-generated
- Prompt engineering for legal analysis requires domain expertise
- Token limits require chunking strategies for large documents
- AI confidence scores should feed into OMEGA, not replace it

---

## Phase 11-13: Deployment, CLI & Open Source

**What was built:**
- Vercel deployment configuration
- Docker containerization (multi-stage build)
- Docker Compose full-stack orchestration
- CLI tool (`litigos`) for command-line access
- Open source preparation (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT)
- Knowledge preservation documentation
- Resilience and backup architecture

**Key learnings:**
- Multi-stage Docker builds reduce image size significantly
- CLI tools should read directly from SQLite for simplicity
- Open source prep requires clear contribution guidelines
- Backup strategies must account for both SQLite and Neo4j data
- Knowledge preservation prevents institutional knowledge loss

---

## Cross-Cutting Learnings

1. **Modularity pays off** — The numeric prefix system makes it trivial to add new phases
2. **SQLite is underrated** — For single-team applications, it eliminates entire categories of ops work
3. **Graph + Relational** — Using both Neo4j and SQLite gives best of both worlds
4. **Agent architecture** — Autonomous agents must have comprehensive audit logging
5. **Legal domain specificity** — Every feature must be validated against legal standards
6. **Data sensitivity** — Self-hosted first approach respects data sovereignty requirements
