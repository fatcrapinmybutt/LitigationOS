# LitigationOS DIAMOND+++ Master Plan — 100+ High-Signal Delta Tasks
## Separation: 211+ days since July 29, 2025 | Mission: Reunite father and son
## Status: EXECUTING — Cycle Method + Legal Skills + Shady Oaks Chess Mode
## See SQL `todos` table for live status tracking

---

## 🔴 PRIORITY ZERO — CYCLE METHOD ENGINE (EAGAIN Killer)

**Problem:** Large writes to stdout/stdin/pipes overflow kernel buffers → EAGAIN error → data loss.
**Solution:** The **Cycle Method** — NEVER write a large payload in one shot. Break EVERY output into measured chunks, write them back-to-back in a cycle, respecting backpressure between each chunk.

### Architecture

```
┌─────────────────────────────────────────────┐
│           CYCLE METHOD ENGINE               │
│                                             │
│  Input: any data (string, JSON, bytes)      │
│                                             │
│  1. Measure payload size                    │
│  2. If > CHUNK_LIMIT (4KB): split into      │
│     chunks of CHUNK_SIZE (4096 bytes)       │
│  3. For each chunk:                         │
│     a. Write chunk                          │
│     b. Check backpressure (drain/flush)     │
│     c. If blocked → wait with exp backoff   │
│     d. Continue to next chunk               │
│  4. Flush final buffer                      │
│  5. Return success                          │
│                                             │
│  Applies to: Python stdout, Node.js pipes,  │
│  Electron IPC, file streams, DB writes      │
└─────────────────────────────────────────────┘
```

### Files to Create/Modify
- **`00_SYSTEM/cycle_method.py`** — Python Cycle Method module (import everywhere)
- **`08_APPS/desktop/main/cycleMethod.js`** — Node.js Cycle Method module
- **`00_SYSTEM/local_model/safe_io.py`** — Add CycleWriter class
- **`00_SYSTEM/local_model/document_qa.py`** — Replace `_safe_write` with CycleMethod
- **`08_APPS/desktop/main/electron-main.js`** — Replace mllmWrite with CycleMethod
- **30+ Python scripts** — Add `from cycle_method import cycle_write` to replace raw print/stdout

### Cycle Method Rules
1. **NEVER write > 4KB in one call** — always chunk
2. **ALWAYS wait for drain/flush between chunks** — respect backpressure  
3. **Exponential backoff on BlockingIOError** — 10ms → 20ms → 40ms → ... → 640ms max
4. **10 retries per chunk max** — then log error and skip (never crash)
5. **Atomic completion** — either all chunks written or error reported
6. **Zero EAGAIN guarantee** — by design, buffer never overflows

---

## 🔴 PRIORITY ONE — LEGAL SKILLS CREATION

### New Skills to Build (saved to 00_SYSTEM/skills/)

| Skill | File | Covers |
|-------|------|--------|
| **michigan-landlord-tenant** | `skill_landlord_tenant.py` | MCL 554.139 (habitability), MCL 600.5714-5744 (summary proceedings), MCL 554.601-614 (security deposits), MCL 125.2301-2349 (Mobile Home Commission Act), retaliation (MCL 600.5720), illegal entry, constructive eviction |
| **michigan-business-corporate** | `skill_business_corporate.py` | MCL 450.1101+ (Business Corporation Act), veil piercing, successor liability, parent-subsidiary, officer/director liability, corporate negligence, LLC liability (MCL 450.4101+) |
| **michigan-torts-claims** | `skill_torts_claims.py` | Conversion (MCL 600.2919a), trespass, negligence per se, IIED/NIED, fraud, MCPA (MCL 445.901+), warranty of habitability, nuisance, premises liability |
| **michigan-defenses-setoffs** | `skill_defenses_setoffs.py` | Statute of limitations, laches, estoppel, waiver, comparative fault, mitigation of damages, setoff/recoupment, governmental immunity, failure to exhaust admin remedies |
| **chess-mode-anticipator** | `skill_chess_mode.py` | For EVERY claim: predict opposing defenses → pre-rebut them in the filing. Maps attack→defense→counter-defense chains. Uses adversary_models table. |

### Chess Mode: Shady Oaks Defense Anticipation

| Our Claim | Their Likely Defense | Our Counter (Pre-Built) |
|-----------|---------------------|------------------------|
| Illegal entry (MCL 125.2303) | "Emergency maintenance exception" | Require 24hr written notice (MCL 125.2303(1)); no emergency existed; pattern of repeated entries |
| Habitability (MCL 554.139) | "Tenant failed to report/gave access" | Written maintenance requests on file; photos timestamped; MCL 554.139 is non-waivable |
| Retaliatory eviction (MCL 600.5720) | "Eviction was for non-payment" | Timeline shows eviction within 90 days of complaints; MCL 600.5720(1) presumption applies |
| Conversion of property (MCL 600.2919a) | "Abandoned property per lease" | MCL 554.612 requires 30-day written notice; no notice given; items had value > $500 |
| Corporate veil piercing | "LLC is separate entity" | Commingled funds, inadequate capitalization, single-entity operation, alter ego doctrine per *Foodland v Al-Naimi* |
| MCPA violations (MCL 445.903) | "Not a consumer transaction" | Lease IS a consumer transaction; deceptive practices in lease terms; treble damages available |
| Custody nexus (MCL 722.23(d)) | "Housing is irrelevant to custody" | Factor (d) = home environment; homelessness caused by illegal eviction → lost custody → 211+ days separation |

---

## 🟠 PRIORITY TWO — SHADY OAKS DOCUMENT OVERHAUL

Current filing: `SHADY_OAKS_FILING_PACKAGE.md` (12.4KB, 4 counts)
Target: **Expanded to 8+ counts with chess-mode defense anticipation, corporate veil piercing, MCPA, and custody nexus**

### New Counts to Add
5. **Count V: MCPA Violations** (MCL 445.903) — deceptive lease practices, treble damages
6. **Count VI: Breach of Quiet Enjoyment** (common law + MCL 554.139) — repeated intrusions
7. **Count VII: Corporate Veil Piercing** — South Haven Park MHC LLC → Our Homes of America → parent entities
8. **Count VIII: Negligence Per Se** — statutory violations = negligence per se under Michigan law
9. **Count IX: Custody Harm Nexus** (MCL 722.23(d)) — connect housing loss → custody loss → 211+ days

### Desktop Offloading
- All analysis scripts run locally on desktop via Electron IPC
- Results saved to `litigation_context.db` tables
- Desktop app shows real-time analysis progress

---

## Platform Overview (4 Products + Core + Context Engine)

| Product | Tech Stack | Status | Location |
|---------|-----------|--------|----------|
| **Core System** | Python MLLM (TF-IDF/NB), 16-phase pipeline, SQLite 1.44GB | ✅ Mature | `00_SYSTEM/` |
| **Desktop App** | Electron + React 18/Vite + Express (disabled) | 🟡 Broken | `08_APPS/desktop/` |
| **Website** | Next.js 14 + TypeScript + Tailwind + Three.js | 🟢 Mostly done | `08_APPS/web/` |
| **Mobile App** | Expo + React Native 0.73 + TypeScript | 🟢 Built, needs audit | `08_APPS/mobile/` |
| **Context Continuer** | New — session persistence engine | 🔴 Not started | `00_SYSTEM/context_continuer/` |

---

## WORKSTREAM A — CONTEXT CONTINUER (New System)

A self-updating context persistence engine that creates structured "handoff documents" before context condensation, enabling near-infinite context continuity across sessions.

### Architecture
- **`context_continuer.py`** — Main engine: reads session state, generates handoff
- **`context_continuer.md`** — Living handoff document (auto-updated)
- **`context_snapshots/`** — Versioned snapshots with timestamps
- **DB table `context_snapshots`** — Indexed searchable history

### Handoff Document Structure
1. **IDENTITY** — Case, parties, judge, lane status, separation day count
2. **PLATFORM STATE** — Per-product build status, last error, last fix
3. **ACTIVE WORK** — Current todos, blockers, in-progress items
4. **DECISIONS LOG** — Key architectural/legal decisions with rationale
5. **FILE CHANGE LOG** — Files modified this session with diff summaries
6. **KNOWLEDGE GAINED** — Facts discovered about codebase/case this session
7. **NEXT ACTIONS** — Prioritized queue of what to do next
8. **CRITICAL WARNINGS** — Deadlines, risks, gotchas for next session

### Implementation Todos
- **ctx-engine** — Build context_continuer.py with snapshot/restore/update methods
- **ctx-handoff-template** — Create the structured markdown template
- **ctx-db-table** — Add context_snapshots table to litigation_context.db
- **ctx-auto-trigger** — Hook into session lifecycle for auto-snapshot
- **ctx-restore** — Build restore logic that loads latest handoff on session start

---

## WORKSTREAM B — DESKTOP APP (Electron + React + Express)

### 🔴 TIER 1 — CRITICAL (Runtime Breaking)
- **dt-fix-analytics-api** — Analytics.jsx: replace `systemAPI` with valid service export
- **dt-fix-cases-icon** — Cases.jsx: add `Scale` to lucide-react imports
- **dt-fix-service-mismatch** — Rewrite citationService, motionService, analysisService to use IPC-based domain APIs instead of fake axios calls
- **dt-fix-auth-response** — authService.js: fix response shape handling for apiHelper
- **dt-fix-electron-entry** — electron-app/package.json: fix `"main"` path
- **dt-fix-electron-sqlite** — Add better-sqlite3 to electron-app package.json
- **dt-fix-module-system** — Standardize backend to CommonJS (remove `"type": "module"`)

### 🟠 TIER 2 — HIGH (Functionality)
- **dt-fix-dynamic-tailwind** — Replace dynamic Tailwind classes with static color maps in AnalysisResults.jsx, UpgradePrompt.jsx
- **dt-fix-streaming** — Replace EventSource in analysisService with IPC-based streaming
- **dt-fix-hardcoded-paths** — Use env vars / app.getPath() instead of `C:\Users\andre\...`
- **dt-create-case-model** — Create missing Case.js model for exportController
- **dt-unify-db-layer** — Standardize on better-sqlite3 only; remove Sequelize/MongoDB patterns
- **dt-create-migration-runner** — Build src/utils/migrate.js and seed.js

### 🟡 TIER 3 — MEDIUM (Quality)
- **dt-add-error-handling** — Add try/catch to citationService (8 methods), motionService (10 methods)
- **dt-fix-settings-buttons** — Wire up Settings.jsx button handlers
- **dt-fix-evidence-mocks** — Replace hardcoded mock IDs with route params
- **dt-fix-state-mgmt** — Standardize: Redux for global state, React Query for server state
- **dt-create-env-docs** — Complete .env.example with all required variables

### 🔵 TIER 4 — SECURITY
- **dt-fix-sql-exposure** — Add query allowlist/parameterization in preload.js
- **dt-add-path-validation** — Sandbox file:read/save to project directories
- **dt-enable-sandbox** — Set `sandbox: true` in Electron webPreferences
- **dt-add-csp** — Add Content Security Policy headers

---

## WORKSTREAM C — WEBSITE (Next.js 14)

### 🟠 HIGH
- **web-verify-build** — Run `npm run build` and fix any TypeScript/build errors
- **web-wire-contact-form** — Connect contact form to backend (API route or serverless function)
- **web-wire-demo-signup** — Connect demo signup form to email service or DB
- **web-add-analytics** — Configure Google Analytics + Hotjar with real measurement IDs
- **web-stripe-integration** — Wire up Stripe checkout for pricing page

### 🟡 MEDIUM
- **web-add-real-content** — Replace placeholder images/videos with real content
- **web-add-blog-cms** — Implement MDX-based blog for legal resources
- **web-add-live-chat** — Integrate live chat widget
- **web-seo-audit** — Run Lighthouse, fix any performance/SEO/a11y gaps
- **web-add-sentry** — Set up Sentry error monitoring

### 🔵 POLISH
- **web-optimize-3d** — Ensure Three.js 3D animations don't tank mobile performance
- **web-add-testimonials** — Add real testimonial content
- **web-legal-pages** — Verify ToS and Privacy Policy content is complete

---

## WORKSTREAM D — MOBILE APP (Expo/React Native)

### 🟠 HIGH
- **mob-audit-deps** — Check node_modules integrity, run `npx expo doctor`
- **mob-audit-imports** — Verify all imports resolve
- **mob-verify-build** — Run `eas build --platform android --profile preview`
- **mob-test-auth-flow** — Verify authentication works end-to-end
- **mob-test-db-connection** — Verify app connects to backend API or local DB

### 🟡 MEDIUM
- **mob-audit-screens** — Review all screens for broken imports, missing components
- **mob-test-camera** — Verify camera/document scanning works
- **mob-test-offline** — Verify offline mode syncs properly
- **mob-push-notifications** — Configure push notification credentials
- **mob-biometric-auth** — Test biometric auth on actual device

### 🔵 POLISH
- **mob-app-icon** — Verify adaptive icons render correctly
- **mob-splash-screen** — Configure splash screen properly
- **mob-deep-linking** — Set up deep link handling

---

## WORKSTREAM E — CORE SYSTEM (MLLM + Pipeline)

### 🟡 MEDIUM
- **core-retrain-model** — Run fresh MLLM training cycle
- **core-run-evolution** — Run self-evolution cycle
- **core-implement-quality-validator** — Fill in empty quality_validator.py agent
- **core-verify-pipeline** — Run omega pipeline phases 1-5 and verify output
- **core-fill-empty-tables** — Populate deadlines, docket_events, vehicles from DB data

### 🔵 POLISH
- **core-create-skills-dir** — Create 00_SYSTEM/skills/ directory
- **core-update-manifest** — Verify model manifest.json
- **core-consolidate-archives** — Clean up 99_ARCHIVE and _QUARANTINE

---

## Parallelization Strategy

**Wave 1** (all parallel — no deps):
ctx-engine, dt-fix-analytics-api, dt-fix-cases-icon, dt-fix-electron-entry, dt-fix-electron-sqlite, web-verify-build, mob-audit-deps

**Wave 2** (after Wave 1):
ctx-handoff-template, ctx-db-table, dt-fix-service-mismatch, dt-fix-auth-response, dt-fix-module-system, web-wire-contact-form, mob-audit-imports

**Wave 3** (after Wave 2):
ctx-auto-trigger, dt-fix-dynamic-tailwind, dt-fix-streaming, dt-fix-hardcoded-paths, dt-unify-db-layer, web-stripe-integration, mob-verify-build

**Wave 4** (after Wave 3):
ctx-restore, dt-add-error-handling, dt-fix-state-mgmt, dt-security-fixes, web-seo-audit, mob-test-*, core-retrain-model

**Wave 5** (polish):
All remaining items across all workstreams
