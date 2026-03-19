---
goal: "Transform LitigationOS into multi-tenant SaaS with jurisdiction plugins and tiered pricing"
version: 1.0
date_created: 2026-03-12
last_updated: 2026-03-12
owner: Andrew Pigors
status: 'Planned'
tags: [architecture, product, saas, monetization]
---

# Introduction

![Status: Planned](https://img.shields.io/badge/status-Planned-blue)

Transform LitigationOS from a single-case personal tool into a multi-tenant product with jurisdiction plugins, customer onboarding, and tiered monetization (Free / Pro $29/mo / Enterprise $99/mo). Desktop-first, local-first architecture preserved.

## 1. Requirements & Constraints

- **REQ-001**: Multi-tenant data isolation — separate SQLite database per tenant
- **REQ-002**: Jurisdiction plugin system with standardized interface
- **REQ-003**: Michigan plugin extracted from current codebase as reference
- **REQ-004**: Case onboarding wizard: 8-step guided setup
- **REQ-005**: Tiered monetization with feature flags
- **CON-001**: Must not break existing Pigors v Watson deployment
- **CON-002**: Desktop-first (Windows) — web is future scope
- **CON-003**: SQLite per-tenant (local-first, no cloud DB in v1)
- **SEC-001**: Zero cross-tenant data access
- **SEC-002**: Encryption at rest for sensitive fields

## 2. Implementation Steps

### Implementation Phase 1 — Multi-Tenant Architecture

- GOAL-001: Build tenant isolation and data management layer

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create `11_CODE/litigationos/src/litigationos/tenant/` package | | |
| TASK-002 | Implement `TenantManager`: create, list, switch, delete tenants | | |
| TASK-003 | Implement per-tenant SQLite database creation from schema template | | |
| TASK-004 | Implement `TenantContext`: thread-local tenant binding for all DB access | | |
| TASK-005 | Implement tenant data directory: `data/tenants/{tenant_id}/` | | |
| TASK-006 | Migrate existing `DatabaseManager` to be tenant-aware | | |
| TASK-007 | Add tenant isolation tests: verify zero cross-tenant data leakage | | |

### Implementation Phase 2 — Jurisdiction Plugin System

- GOAL-002: Build plugin interface and extract Michigan as reference implementation

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-008 | Create `JurisdictionPlugin` ABC in `plugins/base.py` | | |
| TASK-009 | Define plugin interface: get_rules, get_forms, calculate_deadline, validate_filing | | |
| TASK-010 | Extract Michigan court rules into `plugins/jurisdictions/MI/` plugin | | |
| TASK-011 | Extract Michigan forms catalog into plugin (SCAO forms mapping) | | |
| TASK-012 | Extract Michigan deadline rules into plugin (MCR-based calculations) | | |
| TASK-013 | Build plugin loader: discover and load jurisdiction plugins at runtime | | |
| TASK-014 | Create generic/template jurisdiction for states without full plugins | | |

### Implementation Phase 3 — Case Onboarding Wizard

- GOAL-003: Build guided case setup flow in the desktop app

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-015 | Design 8-step wizard UI in CustomTkinter (see spec for step definitions) | | |
| TASK-016 | Implement Step 1-3: Case type → Jurisdiction → Parties | | |
| TASK-017 | Implement Step 4-6: Case numbers → Judge/Attorney → Key dates | | |
| TASK-018 | Implement Step 7-8: Evidence import → Review & Create | | |
| TASK-019 | Create case templates: custody, housing, tort, civil rights, generic | | |
| TASK-020 | Wire wizard to TenantManager: create tenant + case on completion | | |

### Implementation Phase 4 — Monetization & Feature Flags

- GOAL-004: Implement tiered pricing with feature gating

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-021 | Create `FeatureFlagManager` with tier-based gates | | |
| TASK-022 | Implement Free tier: 1 case, 500 MB, basic engines only | | |
| TASK-023 | Implement Pro tier: 5 cases, 5 GB, all engines, export, custom templates | | |
| TASK-024 | Implement Enterprise tier: unlimited cases, unlimited storage, all features | | |
| TASK-025 | Build upgrade flow: Free → Pro upsell prompts at tier limits | | |
| TASK-026 | Implement license key validation (offline-capable) | | |

### Implementation Phase 5 — Export, Import & Documentation

- GOAL-005: Portability, documentation, and market readiness

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-027 | Build case export: ZIP with filings, evidence refs, timeline, DB | | |
| TASK-028 | Build case import: restore from ZIP on another machine | | |
| TASK-029 | Document the process blueprint (what worked for Pigors v Watson) | | |
| TASK-030 | Create product landing page content and screenshots | | |
| TASK-031 | Build product installer (PyInstaller + NSIS or MSI) | | |
| TASK-032 | Create user documentation: getting started, case setup, filing workflow | | |

## 3. Alternatives

- **ALT-001**: PostgreSQL multi-tenant — rejected: violates local-first, requires server
- **ALT-002**: Web-first (Django/FastAPI) — rejected: Andrew wants desktop-first
- **ALT-003**: Single DB with row-level isolation — rejected: harder to enforce, backup complexity
- **ALT-004**: Subscription via Stripe — future scope: v1 uses offline license keys

## 4. Dependencies

- **DEP-001**: CustomTkinter — existing GUI framework
- **DEP-002**: Pydantic v2 — data models (existing)
- **DEP-003**: PyInstaller — executable packaging (existing)
- **DEP-004**: All companion specs/plans (PDF, filing, skills, MANBEARPIG)

## 5. Files

- **FILE-001**: `11_CODE/litigationos/src/litigationos/tenant/` package (NEW)
- **FILE-002**: `11_CODE/litigationos/src/litigationos/plugins/base.py` (NEW — plugin ABC)
- **FILE-003**: `11_CODE/litigationos/src/litigationos/plugins/jurisdictions/MI/` (NEW)
- **FILE-004**: `11_CODE/litigationos/src/litigationos/gui/onboarding_wizard.py` (NEW)
- **FILE-005**: `11_CODE/litigationos/src/litigationos/features.py` (NEW — feature flags)
- **FILE-006**: `11_CODE/litigationos/src/litigationos/db/connection.py` (MODIFY — tenant-aware)
- **FILE-007**: `tests/test_multi_tenant.py` (NEW)
- **FILE-008**: `tests/test_jurisdiction_plugin.py` (NEW)

## 6. Testing

- **TEST-001**: Tenant isolation: zero cross-tenant data leakage (pen test)
- **TEST-002**: Michigan plugin passes all existing filing validation tests
- **TEST-003**: Onboarding wizard creates functional case in <5 minutes
- **TEST-004**: Tier limits correctly enforced for all 3 tiers
- **TEST-005**: Export/import round-trip preserves all data
- **TEST-006**: Existing Pigors v Watson deployment unaffected by changes

## 7. Risks & Assumptions

- **RISK-001**: Multi-tenant refactor may break existing code paths — mitigate with backward-compat mode
- **RISK-002**: Jurisdiction plugins require deep legal knowledge per state — mitigate with template/generic plugin
- **RISK-003**: Monetization may deter open-source contributors — mitigate with generous Free tier
- **ASSUMPTION-001**: CustomTkinter supports wizard-style multi-step flows
- **ASSUMPTION-002**: Market exists for pro se litigation software ($29/mo is reasonable)

## 8. Related Specifications / Further Reading

- [spec/spec-architecture-productization.md](/spec/spec-architecture-productization.md)
- [11_CODE/litigationos/](/11_CODE/litigationos/) — existing product app
- [PROCESS_BLUEPRINT.md](/PROCESS_BLUEPRINT.md) — existing process documentation
