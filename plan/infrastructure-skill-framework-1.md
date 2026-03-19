---
goal: "Build skill registry, versioning, chaining, and auto-evolution framework"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [infrastructure, skills, framework]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Build a structured skill framework replacing the ad-hoc skill loading mechanism with a tiered registry, semantic versioning, dependency resolution, skill chaining, and auto-evolution for 100+ litigation skills.

## 1. Requirements & Constraints

- **REQ-001**: Registry supporting ≥200 skills with O(1) lookup
- **REQ-002**: Auto-discovery from 3 locations (skills/, engines/skill_*.py, .agents/skills/)
- **REQ-003**: Semantic versioning with breaking change detection
- **REQ-004**: Skill chaining with typed data flow between stages
- **CON-001**: Must not break existing skill_loader.py → skill_router.py chain
- **CON-002**: Pure Python — no external binary dependencies per skill
- **CON-003**: Each skill must complete within 5 seconds
- **GUD-001**: Every skill implements `SkillContract` base class

## 2. Implementation Steps

### Implementation Phase 1 — Skill Contract & Registry

- GOAL-001: Define the base contract and build the registry

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create `00_SYSTEM/local_model/skill_contract.py` — `SkillContract` ABC with `execute()`, `validate_input()`, `health_check()` | | |
| TASK-002 | Create `skill_registry` table in `litigation_context.db` (see spec for schema) | | |
| TASK-003 | Create `00_SYSTEM/local_model/skill_registry.py` — `SkillRegistry` class with register/lookup/search | | |
| TASK-004 | Implement `@register_skill()` decorator for declarative registration | | |
| TASK-005 | Implement `SkillMetadata` dataclass with version, tier, intents, dependencies | | |

### Implementation Phase 2 — Auto-Discovery & Scanner

- GOAL-002: Build scanner that auto-discovers skills from filesystem

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-006 | Create `00_SYSTEM/local_model/skill_scanner.py` — filesystem scanner | | |
| TASK-007 | Scan `00_SYSTEM/local_model/skills/` — 55 Python skill modules | | |
| TASK-008 | Scan `00_SYSTEM/engines/skill_*.py` — 14 engine-level skills | | |
| TASK-009 | Scan `.agents/skills/` — 90+ Copilot skill definitions (parse YAML/MD frontmatter) | | |
| TASK-010 | Auto-register discovered skills into `skill_registry` table | | |
| TASK-011 | Implement version comparison and upgrade detection | | |

### Implementation Phase 3 — Skill Chaining

- GOAL-003: Build skill chaining framework with typed data flow

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-012 | Create `00_SYSTEM/local_model/skill_chain_executor.py` — chain execution engine | | |
| TASK-013 | Define chain config format (YAML) with input/output mapping | | |
| TASK-014 | Implement data flow: skill_a.output → skill_b.input with type validation | | |
| TASK-015 | Create 3 default chains: evidence_to_filing, query_to_answer, document_to_claims | | |
| TASK-016 | Handle chain failures: skip failed skill, pass partial data to next | | |

### Implementation Phase 4 — Auto-Evolution & Dashboard

- GOAL-004: Build skill auto-evolution and performance tracking

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-017 | Track per-skill metrics: invocation_count, error_count, avg_latency, accuracy_score | | |
| TASK-018 | Build evolution analyzer: flag skills with >5% error rate for review | | |
| TASK-019 | Implement skill upgrade triggers: when new version detected, validate and swap | | |
| TASK-020 | Build skill performance dashboard query (SQL views on registry table) | | |
| TASK-021 | Integrate with MANBEARPIG v10 self-evolution cycle | | |

### Implementation Phase 5 — Migration & Testing

- GOAL-005: Migrate existing skills and comprehensive testing

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-022 | Migrate top 20 existing skills to use `SkillContract` base class | | |
| TASK-023 | Create `tests/test_skill_framework.py` — registry, chain, evolution tests | | |
| TASK-024 | Verify all 55+ existing skills register successfully | | |
| TASK-025 | Benchmark: registry lookup <1ms for 200 skills | | |
| TASK-026 | Upgrade remaining 27 agent skills (blocked todo OE-SK-06) | | |

## 3. Alternatives

- **ALT-001**: Use stevedore plugin framework — rejected: heavy dependency, overkill for local use
- **ALT-002**: Keep ad-hoc importlib loading — rejected: no versioning, no chaining, no evolution
- **ALT-003**: Use entry_points (pkg_resources) — rejected: requires pip packaging per skill

## 4. Dependencies

- **DEP-001**: SQLite 3 — registry persistence
- **DEP-002**: PyYAML — chain configuration files
- **DEP-003**: Existing `skill_loader.py`, `skill_router.py`, `skill_chaining.py` (reference)

## 5. Files

- **FILE-001**: `00_SYSTEM/local_model/skill_contract.py` — base contract (NEW)
- **FILE-002**: `00_SYSTEM/local_model/skill_registry.py` — registry (NEW)
- **FILE-003**: `00_SYSTEM/local_model/skill_scanner.py` — auto-discovery (NEW)
- **FILE-004**: `00_SYSTEM/local_model/skill_chain_executor.py` — chaining (NEW)
- **FILE-005**: `00_SYSTEM/local_model/skill_loader.py` — adapter to new registry (MODIFY)
- **FILE-006**: `00_SYSTEM/local_model/skill_router.py` — adapter to new registry (MODIFY)
- **FILE-007**: `tests/test_skill_framework.py` — tests (NEW)

## 6. Testing

- **TEST-001**: All 55+ existing skills register without error
- **TEST-002**: Skill chain executes 4 skills with correct data flow
- **TEST-003**: Version comparison detects breaking changes correctly
- **TEST-004**: Auto-discovery finds skills in all 3 scan locations
- **TEST-005**: Registry lookup <1ms for 200 registered skills

## 7. Risks & Assumptions

- **RISK-001**: Some existing skills may not conform to SkillContract — mitigate with adapter pattern
- **RISK-002**: Circular dependencies between skills — mitigate with detection at registration time
- **ASSUMPTION-001**: Existing skills have consistent enough interfaces to adapt
- **ASSUMPTION-002**: PyYAML is already available in the environment

## 8. Related Specifications / Further Reading

- [spec/spec-infrastructure-skill-framework.md](/spec/spec-infrastructure-skill-framework.md)
- [spec/spec-architecture-manbearpig-v10.md](/spec/spec-architecture-manbearpig-v10.md)
