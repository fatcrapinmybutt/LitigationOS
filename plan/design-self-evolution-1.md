---
goal: "Build auto-evolver daemon, 24/7 improvement loop, and self-healing monitor"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [design, ai, evolution, autonomous]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Build an autonomous self-evolution system that runs as a background daemon, continuously improving MANBEARPIG models, discovering new skills, and healing itself from failures — with no human intervention required.

## 1. Requirements & Constraints

- **REQ-001**: Background daemon with configurable cycle intervals (default: 6 hours)
- **REQ-002**: Quality-triggered retraining when accuracy drops below 0.85
- **REQ-003**: Skill auto-discovery from query pattern analysis
- **REQ-004**: Self-healing: detect and recover from DB locks, disk issues, model corruption
- **CON-001**: <2 GB RAM, <25% CPU during evolution cycles
- **CON-002**: Retraining <10 minutes per model
- **CON-003**: Must not interfere with active pipeline operations
- **CON-004**: Checkpoint every 5 minutes (GOAWAY 503 protection)
- **SEC-001**: No network access during any evolution operation

## 2. Implementation Steps

### Implementation Phase 1 — Daemon Framework

- GOAL-001: Build the background daemon with scheduling and lifecycle management

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Install `APScheduler`: `pip install apscheduler` | | |
| TASK-002 | Create `00_SYSTEM/local_model/evolution_daemon.py` — `EvolutionDaemon` class | | |
| TASK-003 | Implement daemon start/stop with file-based locking (prevent multiple instances) | | |
| TASK-004 | Implement configurable scheduling (interval, cron, one-shot modes) | | |
| TASK-005 | Implement checkpoint/resume: persist cycle state to `evolution_state` table | | |
| TASK-006 | Implement Windows service wrapper (optional: `pywin32` or `nssm`) | | |

### Implementation Phase 2 — Quality Feedback & Retraining

- GOAL-002: Build quality monitoring and automated retraining pipeline

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-007 | Create `quality_feedback` table: log query-answer-rating triples | | |
| TASK-008 | Build accuracy tracker: rolling 100-query window with trend detection | | |
| TASK-009 | Build error pattern analyzer: cluster common failure modes | | |
| TASK-010 | Build incremental retraining: update TF-IDF/NB models from new data | | |
| TASK-011 | Build shadow validation: test new model on held-out set before swapping | | |
| TASK-012 | Implement quality gate: reject models that score lower than current production | | |

### Implementation Phase 3 — Self-Healing Monitor

- GOAL-003: Build automated health monitoring and recovery

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-013 | Create `00_SYSTEM/local_model/self_heal_v2.py` — enhanced monitor | | |
| TASK-014 | Implement DB health check: WAL size, lock contention, connection count | | |
| TASK-015 | Implement disk space check: all 6 drives, alert at <5% free | | |
| TASK-016 | Implement model integrity check: SHA-256 verification of model files | | |
| TASK-017 | Implement auto-recovery actions: WAL checkpoint, temp cleanup, model reload | | |
| TASK-018 | Implement circuit breaker: 3 consecutive failures → pause + alert | | |

### Implementation Phase 4 — Skill Discovery & Metrics

- GOAL-004: Build skill auto-discovery and evolution metrics dashboard

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-019 | Analyze query logs for unhandled intents (queries with <0.5 confidence) | | |
| TASK-020 | Propose new skill definitions: intent name, example queries, suggested implementation | | |
| TASK-021 | Build evolution metrics: accuracy trend, latency trend, error rate, skill coverage | | |
| TASK-022 | Write metrics to `evolution_state` table and `00_SYSTEM/PROGRESS_LOG.md` | | |

### Implementation Phase 5 — Testing & Deployment

- GOAL-005: Testing, validation, and initial deployment

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-023 | Create `tests/test_evolution_daemon.py` — unit + integration tests | | |
| TASK-024 | Test: daemon runs 24 hours without crashes (simulated accelerated time) | | |
| TASK-025 | Test: retraining never degrades accuracy (inject synthetic degradation) | | |
| TASK-026 | Test: self-healing resolves ≥80% of injected health issues | | |
| TASK-027 | Test: checkpoint/resume works after simulated crash | | |
| TASK-028 | Deploy: start daemon on system boot via Task Scheduler | | |

## 3. Alternatives

- **ALT-001**: Manual retraining on schedule — rejected: requires human intervention
- **ALT-002**: Use MLflow for experiment tracking — rejected: heavy dependency, cloud-oriented
- **ALT-003**: Use celery for task scheduling — rejected: requires message broker, overkill
- **ALT-004**: Windows Task Scheduler only — considered: simpler but less control over lifecycle

## 4. Dependencies

- **DEP-001**: `APScheduler` ≥3.10 — job scheduling
- **DEP-002**: `psutil` ≥5.9 — system resource monitoring
- **DEP-003**: Existing `self_evolve_v2.py`, `self_evolve_v3.py` (reference/wrap)
- **DEP-004**: Existing `self_heal_monitor.py` (reference/extend)

## 5. Files

- **FILE-001**: `00_SYSTEM/local_model/evolution_daemon.py` (NEW)
- **FILE-002**: `00_SYSTEM/local_model/self_heal_v2.py` (NEW)
- **FILE-003**: `00_SYSTEM/local_model/quality_tracker.py` (NEW)
- **FILE-004**: `00_SYSTEM/local_model/self_evolve_v3.py` (MODIFY — integrate with daemon)
- **FILE-005**: `tests/test_evolution_daemon.py` (NEW)

## 6. Testing

- **TEST-001**: Daemon runs 24h without crashes
- **TEST-002**: Retraining never degrades accuracy (5 cycles tested)
- **TEST-003**: Self-healing resolves ≥80% of injected issues
- **TEST-004**: Checkpoint/resume works after crash
- **TEST-005**: Resource usage: <2 GB RAM, <25% CPU

## 7. Risks & Assumptions

- **RISK-001**: Daemon may interfere with pipeline operations — mitigate with process-level locking
- **RISK-002**: Windows sleep/hibernate may interrupt daemon — mitigate with resume-on-wake
- **RISK-003**: Retraining on biased recent data — mitigate with stratified sampling
- **ASSUMPTION-001**: `APScheduler` works reliably on Windows for days-long runs
- **ASSUMPTION-002**: Sufficient disk space for model checkpoints (~500 MB per checkpoint)

## 8. Related Specifications / Further Reading

- [spec/spec-design-self-evolution.md](/spec/spec-design-self-evolution.md)
- [spec/spec-architecture-manbearpig-v10.md](/spec/spec-architecture-manbearpig-v10.md)
- [plan/upgrade-manbearpig-v10-1.md](/plan/upgrade-manbearpig-v10-1.md)
