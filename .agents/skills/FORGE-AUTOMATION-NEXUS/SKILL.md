---
name: FORGE-AUTOMATION-NEXUS
description: >-
  Unified pipeline intelligence fusing CI/CD architecture, build optimization,
  deployment orchestration, infrastructure-as-code, release engineering, and
  workflow automation into a self-healing automation fabric. Triggers on pipeline,
  CI/CD, deploy, build, release, infrastructure, workflow, automation, DevOps pipeline,
  build system. Creates emergent capability where pipelines design, optimize, and
  heal themselves by understanding build graphs, deployment topology, and release
  cadence as one continuous flow.
category: operations
version: "1.0.0"
triggers:
  - "CI/CD pipeline"
  - "build optimization"
  - "deployment strategy"
  - "infrastructure as code"
  - "release automation"
  - "GitHub Actions"
  - "pipeline architecture"
  - "build caching"
  - "canary deployment"
  - "monorepo build"
  - "workflow automation"
  - "Terraform module"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: infrastructure
  emergent_capability: "Self-healing pipeline intelligence that auto-designs, optimizes, and repairs CI/CD systems"
---

# 🔄 FORGE-AUTOMATION-NEXUS
> **Unified Pipeline Intelligence (Ω-Δ99)**

## OVERVIEW

| Attribute | Value |
|---|---|
| Tier | FORGE |
| Domain | DevOps/Automation |
| Scope | CI/CD+IaC+Release+Deploy |
| Emergent | Self-healing pipelines |
| Key Principle | Pipelines as intelligent systems |

## FORGED SKILLS TABLE

| # | Source Skill | Absorbed Capability |
|---|---|---|
| 1 | ci-cd-pipeline-builder | Multi-stage pipeline design |
| 2 | github-actions-workflows | GitHub Actions mastery |
| 3 | workflow-automation | Event-driven task automation |
| 4 | infrastructure-as-code | Terraform/Pulumi/CloudFormation |
| 5 | pipeline-optimization | Build caching and parallelization |
| 6 | deployment-strategies | Blue-green/canary/rolling deploys |
| 7 | environment-management | Secrets, config, env parity |
| 8 | release-automation | Semver, changelog, release flows |
| 9 | build-system-architect | Monorepo builds (Nx/Turborepo/Bazel) |
| 10 | task-runner-orchestrator | Make/Just/Taskfile orchestration |

## ASCII ARCHITECTURE DIAGRAM

```text
                          ┌──────────────────────────────────────┐
                          │      FORGE-AUTOMATION-NEXUS         │
                          │    Unified Pipeline Intelligence     │
                          └──────────────────────────────────────┘
                                          │
         ┌───────────────┬────────────────┼────────────────┬───────────────┐
         │               │                │                │               │
   ┌─────▼─────┐   ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐   ┌─────▼─────┐
   │ AN1       │   │ AN2       │    │ AN3       │    │ AN4       │   │ AN5       │
   │ Pipeline  │◄──┤ Build     │◄──►│ Deploy    │◄──►│ IaC       │◄──►│ Release   │
   │ Arch      │   │ Optimize  │    │ Orchestr. │    │ Control   │   │ Eng       │
   └─────┬─────┘   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘   └─────┬─────┘
         │               │                │                │               │
         │               │                │                │               │
   ┌─────▼─────┐   ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐         │
   │ AN6       │◄──┤ AN7       │◄──►│ AN8       │────► Feedback  │─────────┘
   │ Env Mgmt  │   │ Workflow  │    │ Monorepo  │    │ Loop       │
   │ Secrets   │   │ Intel     │    │ Mastery   │    │ Signals    │
   └───────────┘   └───────────┘    └───────────┘    └────────────┘

Signal paths:
  AN1 defines stage graph and quality gates.
  AN2 compresses execution time and cost across the graph.
  AN3 turns validated artifacts into safe progressive delivery.
  AN4 provisions the substrate that AN3 deploys into.
  AN5 versions, tags, signs, and publishes what the graph produces.
  AN6 injects secure config and environment parity rules everywhere.
  AN7 reacts to repository, platform, and incident events.
  AN8 computes affected scope and feeds selective execution upstream.
```

## CORE OPERATING MODEL

FORGE-AUTOMATION-NEXUS treats the pipeline as a living graph rather than a linear shell script. Jobs, environments, release flows, and infrastructure modules are modeled as mutually aware control surfaces. The superskill reasons about build graph shape, deployment topology, release risk, and operator intent together so that one change can trigger the minimum safe amount of work.

The Ω-Δ99 stance is that every automation system should be observable, replayable, and repairable. That means each module exposes explicit inputs, outputs, confidence signals, rollback hooks, and policy constraints. Instead of merely running jobs, the superskill composes build intelligence, environment state, and release semantics into a closed-loop operating fabric.

This file is intentionally production-oriented. Examples assume GitHub Actions, Terraform, Docker, Python, shell orchestration, and monorepo tooling, but the patterns generalize to Jenkins, GitLab CI, Buildkite, Argo CD, Spacelift, Azure DevOps, and similar stacks.

## AN1: Pipeline Architecture

**Purpose:** Design multi-stage CI/CD from scratch with explicit gates, artifact contracts, and failure domains.

**Design Pattern:** Directed Delivery Graph

AN1 establishes the canonical pipeline topology: source validation, dependency restoration, unit verification, integration qualification, packaging, security analysis, and deployment promotion. It treats stages as graph nodes with clear entry conditions and outputs rather than as an ad hoc list of shell commands. This reduces hidden coupling and makes it obvious where to parallelize, where to cache, and where to stop propagation when risk increases.

The module also defines artifact contracts. Each stage emits structured outputs such as test reports, SBOMs, container digests, Terraform plans, changelog fragments, and provenance attestations. Those outputs become the shared language between AN2, AN3, AN4, and AN5, allowing the overall automation fabric to reason about what is safe to reuse and what must be regenerated.

A FORGE-grade pipeline architecture includes policy gates, not just technical tasks. Required reviews, branch protection, environment approvals, release freeze windows, and deployment concurrency are all part of the architecture. AN1 therefore spans workflow YAML, repository conventions, branch strategy, and environment protection rules as one integrated system.

### Key Operations

- Model stages and dependencies before writing workflow YAML.
- Define artifact boundaries and retention policy per stage.
- Attach quality gates with explicit pass/fail semantics.
- Design concurrency groups to prevent deployment races.
- Emit traceable metadata for every pipeline hop.
- Separate fast feedback paths from release paths.
- Codify manual approvals only where risk justifies them.
- Expose promotion contracts between build and deploy systems.

### Code Example (YAML)

```yaml
name: platform-ci
on:
  pull_request:
  push:
    branches: [main]
concurrency:
  group: platform-${{ github.ref }}
  cancel-in-progress: true
jobs:
  validate:
    runs-on: ubuntu-latest
    outputs:
      app_version: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - id: meta
        run: echo "version=1.4.${GITHUB_RUN_NUMBER}" >> "$GITHUB_OUTPUT"
      - run: npm ci
      - run: npm run lint && npm run test:unit
      - uses: actions/upload-artifact@v4
        with:
          name: validation-reports
          path: reports/
  package:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ghcr.io/acme/app:${{ needs.validate.outputs.app_version }} .
      - run: docker save ghcr.io/acme/app:${{ needs.validate.outputs.app_version }} -o image.tar
      - uses: actions/upload-artifact@v4
        with:
          name: image
          path: image.tar
  deploy-staging:
    needs: package
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: image
      - run: ./scripts/deploy.sh staging image.tar
```

### Implementation Guidance

Start AN1 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN1: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN1 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN1 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN1 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN1 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN1 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Feeds AN2 with stage boundaries for cache placement and fan-out decisions.
- Hands AN3 artifact digests and promotion metadata for progressive delivery.
- Supplies AN5 version outputs and release gate signals.
- Consumes AN8 affected-scope intelligence to skip untouched stages.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN1 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN1 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN1 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN1? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN1 risk? | Automation stays fast without becoming reckless. |

## AN2: Build Optimization

**Purpose:** Reduce build latency and cost through caching, parallelization, and incremental execution.

**Design Pattern:** Feedback-Weighted Execution Mesh

AN2 focuses on shrinking the critical path without compromising determinism. It examines dependency graphs, cache hit ratios, test distribution, compiler behavior, and artifact sizes to place caches where they materially reduce time-to-signal. The goal is not maximum parallelism at all costs, but maximum trustworthy throughput with repeatable results.

A core principle is stratified caching. Dependency caches, build output caches, container layer caches, and test selection caches each have different invalidation rules. AN2 explicitly models those layers so stale outputs do not silently poison later stages. It also emphasizes remote caching and content-addressable storage for large monorepo workloads.

FORGE-grade optimization links performance telemetry back into design. Slowest jobs, cache misses, flakiest tests, oversized images, and redundant setup steps become measurable bottlenecks. AN2 therefore closes the loop by using workflow summaries, metrics exporters, and build timing baselines to guide iterative pipeline tuning.

### Key Operations

- Introduce dependency, compiler, and container layer caches with clear keys.
- Split independent quality tasks to parallel jobs or matrix strategies.
- Use affected-target detection to avoid whole-repo rebuilds.
- Persist remote cache across runners where supported.
- Profile build hot spots with timing and cache-hit metrics.
- Short-circuit expensive jobs when earlier guardrails fail.
- Pin toolchain versions to preserve cache usefulness.
- Compress or prune artifacts to reduce transfer overhead.

### Code Example (YAML)

```yaml
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [0, 1, 2, 3]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm
      - uses: actions/cache@v4
        with:
          path: .nx/cache
          key: nx-${{ runner.os }}-${{ hashFiles('package-lock.json', 'nx.json') }}
          restore-keys: |
            nx-${{ runner.os }}-
      - run: npx nx affected -t build,test --parallel=4 --base=origin/main~1 --head=HEAD --exclude=e2e
      - run: pytest -n auto --dist=loadscope tests --shard-id ${{ matrix.shard }} --num-shards 4
      - run: docker buildx build --cache-from type=gha --cache-to type=gha,mode=max -t app:${{ github.sha }} .
      - run: echo "cache-miss-threshold=0.25" >> optimization-metrics.txt
```

### Implementation Guidance

Start AN2 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN2: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN2 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN2 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN2 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN2 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN2 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Consumes AN1 stage graph to place cache boundaries on stable interfaces.
- Shares timing and cache telemetry with AN7 for reactive workflow tuning.
- Depends on AN8 to identify affected targets in large repositories.
- Improves AN5 release velocity by shortening artifact production time.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN2 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN2 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN2 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN2? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN2 risk? | Automation stays fast without becoming reckless. |

## AN3: Deployment Orchestration

**Purpose:** Safely move validated artifacts into runtime environments using progressive delivery and rollback-aware control loops.

**Design Pattern:** Progressive Delivery State Machine

AN3 owns the runtime transition from candidate artifact to live service. It models blue-green, canary, rolling, and feature-flag-assisted deployments as explicit state machines with health checks, abort paths, and rollback checkpoints. Instead of a single deploy step, the module sequences provisioning checks, preflight validations, traffic movement, post-deploy verification, and recovery actions.

The module is especially valuable when multiple environments, regions, or tenant rings exist. It can progressively roll out changes by geography, customer segment, or exposure percentage while measuring SLOs and business KPIs between steps. Health signals are first-class citizens; deployment success is determined by telemetry, not merely by command completion.

AN3 also normalizes deployment metadata. Rollout ID, container digest, config version, database migration status, and approval chain are captured together so incident response can rapidly answer what changed, where, and when. This provides the operational backbone for self-healing and human-led rollback alike.

### Key Operations

- Model deployment states, health checks, and rollback checkpoints.
- Use canary analysis or blue-green switching for high-risk services.
- Record rollout metadata and attach it to release artifacts.
- Gate traffic promotion on SLO-based evidence, not intuition.
- Coordinate schema changes with backward-compatible app releases.
- Define automatic rollback triggers and manual override controls.
- Limit concurrency for shared infrastructure or regional rollout.
- Keep preflight and postflight checks symmetrical and auditable.

### Code Example (PYTHON)

```python
import time
import requests

CANARY_URL = "https://metrics.internal.example/api/rollout"
THRESHOLDS = {"error_rate": 0.02, "p95_ms": 450}
STEPS = [5, 25, 50, 100]

def current_health(release_id: str) -> dict:
    response = requests.get(f"{CANARY_URL}/{release_id}", timeout=10)
    response.raise_for_status()
    return response.json()

def healthy(metrics: dict) -> bool:
    return metrics["error_rate"] <= THRESHOLDS["error_rate"] and metrics["p95_ms"] <= THRESHOLDS["p95_ms"]

def promote(release_id: str, percent: int) -> None:
    print(f"Promoting {release_id} to {percent}% traffic")
    requests.post(f"{CANARY_URL}/{release_id}/promote", json={"percent": percent}, timeout=10).raise_for_status()

def rollback(release_id: str) -> None:
    print(f"Rolling back {release_id}")
    requests.post(f"{CANARY_URL}/{release_id}/rollback", timeout=10).raise_for_status()

def orchestrate(release_id: str) -> None:
    for step in STEPS:
        promote(release_id, step)
        time.sleep(120)
        metrics = current_health(release_id)
        if not healthy(metrics):
            rollback(release_id)
            raise SystemExit(f"Rollback triggered for {release_id}: {metrics}")
    print(f"Release {release_id} fully promoted")
```

### Implementation Guidance

Start AN3 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN3: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN3 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN3 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN3 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN3 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN3 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Requires AN4-managed infrastructure surfaces and load balancer topology.
- Consumes AN5 release identifiers, semantic version labels, and signed artifacts.
- Uses AN6 secrets and environment-specific config bundles.
- Emits status events that AN7 can route to incident or approval workflows.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN3 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN3 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN3 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN3? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN3 risk? | Automation stays fast without becoming reckless. |

## AN4: Infrastructure as Code

**Purpose:** Provision and govern infrastructure with reusable modules, state discipline, and promotion-safe change controls.

**Design Pattern:** Declarative Substrate Mesh

AN4 transforms infrastructure from an opaque runtime dependency into versioned, reviewable, reproducible code. It emphasizes modular Terraform, Pulumi, or CloudFormation stacks with clear inputs, outputs, tagging standards, and policy enforcement. The module separates shared foundations from service-specific overlays so teams can move quickly without copy-paste drift.

State management is a first-class concern. Remote state backends, locking, drift detection, and plan/apply separation are not afterthoughts; they are the control mechanisms that keep infrastructure automation trustworthy. AN4 also considers secret injection, ephemeral preview environments, and lifecycle protections such as prevent_destroy or policy checks before high-risk changes execute.

In a FORGE configuration, infrastructure plans become pipeline artifacts. That means changes to networking, compute, IAM, DNS, storage, and deploy controllers flow through the same audit trail and approval semantics as application changes. This unifies platform operations with delivery operations and enables powerful change impact reasoning across layers.

### Key Operations

- Author reusable modules with stable interfaces and strong defaults.
- Store state remotely with locking and role-based access controls.
- Publish plan files for review before apply in protected environments.
- Detect and remediate drift through scheduled validation workflows.
- Separate foundational platform stacks from service overlays.
- Encode tagging, encryption, and network policy requirements.
- Use workspaces or environment directories carefully and consistently.
- Coordinate infrastructure rollouts with application deployment windows.

### Code Example (HCL)

```hcl
terraform {
  required_version = ">= 1.7.0"
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "platform/prod/app/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "acme-terraform-locks"
    encrypt        = true
  }
}

module "service_cluster" {
  source              = "../../modules/ecs-service"
  name                = "orders-api"
  environment         = var.environment
  desired_count       = 3
  container_image     = var.container_image
  alb_listener_arn    = module.network.public_listener_arn
  private_subnet_ids  = module.network.private_subnet_ids
  alarm_topic_arn     = module.observability.alarm_topic_arn
  tags = {
    system      = "commerce"
    managed_by  = "terraform"
    release_ref = var.release_ref
  }
}

resource "aws_ssm_parameter" "runtime_config" {
  name  = "/orders/${var.environment}/runtime"
  type  = "SecureString"
  value = jsonencode(var.runtime_config)
}
```

### Implementation Guidance

Start AN4 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN4: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN4 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN4 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN4 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN4 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN4 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Supplies AN3 with target topology, endpoints, and traffic-switch resources.
- Relies on AN6 for secret and configuration mapping into IaC.
- Exports plan artifacts that AN1 can place behind protected approval gates.
- Aligns AN5 releases with immutable infrastructure references and release tags.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN4 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN4 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN4 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN4? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN4 risk? | Automation stays fast without becoming reckless. |

## AN5: Release Engineering

**Purpose:** Turn validated change sets into trustworthy releases with semantic versioning, provenance, and automated publication.

**Design Pattern:** Versioned Evidence Conveyor

AN5 manages the passage from merged code to consumable release. It computes semantic versions, assembles changelog narratives, signs artifacts, publishes packages or images, and records release provenance so downstream operators can verify exactly what was shipped. The module treats release metadata as operational evidence, not cosmetic documentation.

A well-designed release system balances automation with intention. Feature work can cut prereleases automatically, while production channels may require approvals, freeze-window checks, or business sign-off. AN5 therefore supports multiple tracks: nightly, candidate, stable, hotfix, and rollback release lines, each with its own gating and publication logic.

Release engineering also bridges developers and operators. Clear changelog fragments, migration notes, deprecation flags, and artifact manifests reduce cognitive load during deployment and incident response. AN5 ensures releases are both machine-actionable and human-readable.

### Key Operations

- Generate semver bumps from conventional commits or labels.
- Assemble changelog fragments into release notes automatically.
- Sign, attest, and publish artifacts to registries or package indexes.
- Create prerelease and stable channels with explicit promotion rules.
- Gate release creation on test, security, and compliance evidence.
- Attach SBOMs, checksums, and migration notes to releases.
- Support hotfix lanes without corrupting the main cadence.
- Feed release metadata into deployment and observability systems.

### Code Example (YAML)

```yaml
name: release
on:
  push:
    branches: [main]
jobs:
  cut-release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
      - run: cosign sign --yes ghcr.io/acme/app:${{ github.sha }}
      - run: syft ghcr.io/acme/app:${{ github.sha }} -o spdx-json > sbom.json
      - uses: softprops/action-gh-release@v2
        if: startsWith(github.ref, 'refs/tags/')
        with:
          files: |
            sbom.json
            dist/checksums.txt
```

### Implementation Guidance

Start AN5 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN5: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN5 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN5 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN5 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN5 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN5 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Consumes AN1 validation outputs and AN2-produced build artifacts.
- Provides AN3 with immutable release IDs, digests, and notes for rollout.
- Tags infrastructure updates from AN4 with the same release_ref used in deploys.
- Triggers AN7 notifications, approvals, and post-release automations.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN5 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN5 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN5 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN5? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN5 risk? | Automation stays fast without becoming reckless. |

## AN6: Environment Management

**Purpose:** Maintain secure, consistent, and auditable configuration across dev, staging, and production environments.

**Design Pattern:** Parity Envelope

AN6 manages the often chaotic boundary between code and runtime reality. It organizes secrets, config maps, feature flags, service endpoints, and environment policies so applications experience predictable behavior as they move from local development to production. The objective is parity of structure, not necessarily parity of scale: each environment should look alike in shape even when it differs in volume or cost.

Secrets handling is central. AN6 encourages short-lived credentials, OIDC federation, managed secret stores, and strict scoping of access by workflow and environment. Rather than sprinkling secrets across repository variables, shell profiles, and ad hoc runtime overrides, it establishes a single authoritative mapping layer with traceable consumers.

This module also manages config validation and drift detection. Schema-checked environment bundles, startup assertions, and deployment-time config diffs reduce the class of failures where a deployment technically succeeds but the service is functionally broken because a key value is missing or inconsistent.

### Key Operations

- Centralize secrets in managed stores and inject them just-in-time.
- Use schema-validated environment bundles for every stage.
- Separate secret values from non-secret configuration references.
- Enforce environment parity through generated manifests and diff checks.
- Adopt OIDC and short-lived cloud credentials where possible.
- Version config contracts alongside application code.
- Block deployment when required config keys are absent or malformed.
- Emit environment provenance to deployment and release records.

### Code Example (PYTHON)

```python
from pathlib import Path
import json
from pydantic import AnyHttpUrl, BaseModel, ValidationError

class RuntimeConfig(BaseModel):
    environment: str
    api_base_url: AnyHttpUrl
    redis_url: str
    sentry_dsn: str
    feature_checkout_v2: bool

def load_config(path: str) -> RuntimeConfig:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return RuntimeConfig.model_validate(payload)

if __name__ == '__main__':
    try:
        cfg = load_config('config/runtime.staging.json')
        print(cfg.model_dump_json(indent=2))
    except ValidationError as exc:
        raise SystemExit(f"Invalid runtime config: {exc}")
```

### Implementation Guidance

Start AN6 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN6: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN6 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN6 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN6 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN6 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN6 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Provides AN3 deployment steps with environment-scoped secrets and flags.
- Pairs with AN4 to map secret stores and parameter resources into IaC.
- Gives AN1 policy gates a way to block promotion on config drift.
- Enables AN7 event handlers to route based on environment severity or policy.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN6 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN6 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN6 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN6? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN6 risk? | Automation stays fast without becoming reckless. |

## AN7: Workflow Intelligence

**Purpose:** Coordinate event-driven automation so repositories, platforms, incidents, and releases trigger the right actions automatically.

**Design Pattern:** Reactive Control Lattice

AN7 is the nervous system of the superskill. It listens for repository events, cron triggers, dependency updates, vulnerability disclosures, deployment failures, issue labels, and external webhooks, then maps them to automations with the correct urgency and blast radius. It is concerned with routing, filtering, fan-out, and idempotency.

The intelligence layer does more than trigger workflows. It enriches events with context such as changed paths, ownership metadata, environment risk, business calendar constraints, and incident state. That context determines whether a workflow should run, what scope it should run against, and who should be notified or asked to approve the result.

FORGE maturity means automations are designed to heal or at least stabilize systems automatically where safe. AN7 can open rollback workflows on deployment regressions, schedule drift checks, launch cache warm-ups before peak windows, or create actionable issues when repeated failures point to systemic bottlenecks.

### Key Operations

- Translate repository and platform events into targeted automation runs.
- Enrich events with ownership, risk, and environment metadata.
- Debounce noisy triggers and enforce idempotent handlers.
- Route failures to rollback, ticketing, or escalation automations.
- Schedule maintenance workflows such as drift checks and cache warm-ups.
- Apply branching or path filters to limit unnecessary execution.
- Capture workflow outcomes as signals for future tuning.
- Integrate chatops, issue trackers, and incident platforms.

### Code Example (YAML)

```yaml
name: automation-router
on:
  workflow_run:
    workflows: [platform-ci, release]
    types: [completed]
  schedule:
    - cron: '0 5 * * *'
  repository_dispatch:
    types: [incident_detected]
jobs:
  route:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const event = context.eventName;
            if (event === 'schedule') {
              core.notice('Running drift and cache-warm workflow');
            } else if (event === 'repository_dispatch') {
              core.warning('Incident detected: starting rollback assessment');
            } else {
              core.info(`Workflow ${context.payload.workflow_run.name} completed with ${context.payload.workflow_run.conclusion}`);
            }
      - run: python automation/router.py
```

### Implementation Guidance

Start AN7 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN7: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN7 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN7 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN7 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN7 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN7 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Consumes signals from every other module and turns them into actions or escalations.
- Uses AN8 path and target intelligence to choose the minimum necessary automation scope.
- Coordinates AN3 rollback or approval flows when health signals degrade.
- Schedules AN4 drift detection and AN2 performance maintenance routines.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN7 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN7 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN7 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN7? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN7 risk? | Automation stays fast without becoming reckless. |

## AN8: Monorepo Mastery

**Purpose:** Operate large multi-project repositories with affected detection, task graph awareness, and shared build governance.

**Design Pattern:** Selective Execution Graph

AN8 handles the realities of scale in monorepos: many applications, many libraries, shared tooling, and a constant risk of overbuilding. It leverages Nx, Turborepo, Bazel, or equivalent graph engines to compute which targets are affected by a given change, then supplies that scope to the pipeline so only necessary tasks run. The result is faster feedback and more predictable infrastructure consumption.

The module also enforces build governance. Shared linting, code generation, dependency constraints, ownership rules, and project tagging help preserve order as the repository grows. AN8 is not only about performance; it is also about keeping system boundaries understandable so the automation graph remains operable by humans.

At FORGE tier, monorepo intelligence becomes a control plane for the entire pipeline. Release candidates can be cut per package, deployments can be scoped to impacted services, and environment updates can be correlated to only the projects they actually affect. This converts the monorepo from a liability into a high-leverage orchestration substrate.

### Key Operations

- Compute affected projects and tasks from git diff boundaries.
- Use remote execution or cache backends for large task graphs.
- Enforce dependency rules and ownership boundaries between packages.
- Scope release notes and deployment decisions to changed services.
- Partition e2e or integration suites based on impacted surfaces.
- Run graph visualizations to understand hot spots and bottlenecks.
- Keep shared generators and toolchain versions centralized.
- Expose monorepo metadata to pipeline and workflow logic.

### Code Example (SHELL)

```shell
git fetch origin main --depth=1
npx nx graph --file=dist/project-graph.json
npx nx print-affected --base=origin/main --head=HEAD --select=projects
npx nx affected -t lint,test,build --parallel=6 --base=origin/main --head=HEAD
turbo run build test --filter=...[origin/main]
bazel query 'kind("py_binary", rdeps(//..., set(//services/payments/...)))'
just affected-deploy base=origin/main head=HEAD
```

### Implementation Guidance

Start AN8 with one measurable control objective: speed, safety, repeatability, or traceability. Designing for all four simultaneously is the end state, but a successful rollout begins by making one control loop explicit and observable.

Document the contract surface for AN8: required inputs, emitted outputs, ownership expectations, retry behavior, and failure escalation. This is what allows the module to compose cleanly with neighboring modules rather than becoming a fragile bespoke script collection.

Treat generated artifacts, plans, metrics, and summaries from AN8 as durable operational evidence. Store them long enough for debugging, auditing, and rollback, and reference them in later stages instead of recomputing state invisibly.

### Failure Modes to Guard Against

- Invisible coupling: AN8 depends on undocumented files, variables, or side effects outside its declared interface.
- False confidence: AN8 marks success based on command exit status while ignoring runtime or policy signals that should block progression.
- Unbounded blast radius: AN8 can affect more services, environments, or repositories than the triggering change actually requires.
- Telemetry gaps: AN8 cannot explain what happened after the fact because outputs, logs, timings, or metadata were not preserved.

### Integration Points

- Supplies AN1 and AN2 with affected scope to avoid full-graph execution.
- Allows AN5 to cut package- or service-specific releases from one repository.
- Helps AN7 trigger only the automations relevant to changed ownership domains.
- Supports AN3 by narrowing deployment surfaces to impacted services or regions.

### Operational Checklist

| Control | Question | Desired Outcome |
|---|---|---|
| Inputs | Are AN8 inputs explicit and validated? | Runs are reproducible and debuggable. |
| Outputs | Does AN8 emit durable metadata and artifacts? | Later stages consume evidence instead of assumptions. |
| Risk | Is the blast radius of AN8 bounded by environment or scope? | Failure stays local and recoverable. |
| Observability | Can operators see timing, status, and rollback context for AN8? | Incidents are diagnosable within minutes. |
| Policy | Are approvals and protection rules aligned with AN8 risk? | Automation stays fast without becoming reckless. |

## DECISION TREE

```text
                          START: What automation problem are you solving?
                                               │
                 ┌─────────────────────────────┼─────────────────────────────┐
                 │                             │                             │
        Need a new pipeline?           Need faster feedback?          Need safer releases?
                 │                             │                             │
               Use AN1                     Use AN2                     Use AN3 + AN5
                 │                             │                             │
                 ├───────────────┐             │                     ┌───────┴────────┐
                 │               │             │                     │                │
         Need infra changes?  Need env rules? │              Need infra changes?  Need config parity?
                 │               │             │                     │                │
               AN4             AN6            │                    AN4              AN6
                 │               │             │                     │                │
                 └───────┬───────┘             │                     └────────┬───────┘
                         │                     │                              │
                    Need event routing, scheduled healing, or cross-system reactions?
                                                 │
                                               AN7
                                                 │
                        Large monorepo or many interdependent packages/services?
                                                 │
                                               AN8
                                                 │
                                      Compose outputs back into AN1-AN5
```

## CROSS-MODULE INTEGRATION

### Cascade 1: Pull Request to Selective Validation

A pull request lands in a monorepo. AN8 computes the affected graph and tells AN1 which stages truly need to run for the changed projects. AN2 then applies cache and parallel execution to just that narrowed scope, producing fast and trustworthy feedback for reviewers without burning compute on untouched services.

### Cascade 2: Release Candidate to Progressive Deploy

AN5 cuts a release candidate with semver metadata, SBOM, and signed artifact digest. AN3 consumes that release package and performs staged rollout, while AN6 injects environment-scoped configuration bundles. If health signals degrade, AN7 routes the failure into rollback automation and notification flows, preserving the release evidence chain.

### Cascade 3: Infrastructure Change with Policy Protection

AN4 produces a Terraform plan artifact and drift summary. AN1 places that plan behind an approval gate for protected environments. Once approved, AN3 coordinates deployment timing so application rollout only begins after infrastructure convergence. AN6 verifies secret and parameter readiness before traffic shifts.

### Cascade 4: Incident-Driven Self-Healing

An observability system emits a degradation event. AN7 enriches the event with ownership, environment, and current release metadata, then triggers AN3 rollback assessment. AN5 identifies the offending release, AN6 verifies config lineage, and AN2 optionally warms the cache path needed for a rapid rebuild or hotfix lane if rollback is insufficient.

## DOMAIN APPLICATIONS

### 1. SaaS Platform with Multiple Services

Use AN8 to scope changes across services, AN2 to distribute builds, AN5 to publish versioned images, and AN3 to canary only the affected workloads. The result is fast feedback on pull requests and low-risk production promotion across a service fleet.

### 2. Enterprise Infrastructure Platform

Use AN4 to manage shared VPC, cluster, and IAM modules; AN6 for secret and environment discipline; and AN1 to create plan/apply approval paths. This is ideal where compliance requires auditable infrastructure promotion and separation of duties.

### 3. Consumer Application with High Release Cadence

Use AN5 for automated semantic releases, AN3 for canary rollouts, and AN7 for instant rollback and chatops notification. This pattern supports daily or hourly release cadence without surrendering operational control.

### 4. Polyglot Monorepo with Shared Tooling

Use AN8 to compute affected projects across JavaScript, Python, and Go packages, AN2 to exploit remote cache and matrix sharding, and AN1 to expose language-specific validation stages behind a single orchestrated graph. This keeps a large repository governable as team count increases.

## QUICK REFERENCE CARD

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FORGE-AUTOMATION-NEXUS                                                      │
│ Unified Pipeline Intelligence (Ω-Δ99)                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│ Modules                                                                     │
│  AN1 Pipeline Architecture   -> Stage graph, gates, artifact contracts      │
│  AN2 Build Optimization      -> Cache, parallel, incremental execution      │
│  AN3 Deployment Orchestration-> Blue-green, canary, rollback                │
│  AN4 Infrastructure as Code  -> Terraform/Pulumi modules, state, drift      │
│  AN5 Release Engineering     -> Semver, changelog, signing, publish         │
│  AN6 Environment Management  -> Secrets, config, parity, validation         │
│  AN7 Workflow Intelligence   -> Event routing, healing, automation          │
│  AN8 Monorepo Mastery        -> Affected scope, task graph, governance      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Primary Triggers                                                            │
│  pipeline • build optimization • deployment strategy • IaC • release flow   │
│  GitHub Actions • build caching • canary deployment • monorepo build        │
│  workflow automation • Terraform module                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Emergent Capability                                                         │
│  Self-healing pipeline intelligence that designs, optimizes, and repairs    │
│  CI/CD systems by understanding build graphs, deployment topology, release  │
│  cadence, and environment state as one continuous operational fabric.       │
└──────────────────────────────────────────────────────────────────────────────┘

## FORGE OPERATING HEURISTICS

1. Prefer graph-aware execution over whole-repo execution.
2. Prefer artifact contracts over implicit filesystem coupling.
3. Prefer progressive delivery over binary all-at-once release moves.
4. Prefer short-lived credentials over long-lived static secrets.
5. Prefer versioned evidence over undocumented operator memory.
6. Prefer scheduled drift detection over surprise infrastructure drift.
7. Prefer event routing with context over blanket automation triggers.
8. Prefer bounded blast radius over maximum nominal speed.
9. Prefer consistent environment shape over hand-tuned exceptions.
10. Prefer self-healing with auditability over opaque magic.

## MODULE-TO-TRIGGER MAP

| Trigger Phrase | Primary Module | Secondary Module | Typical Outcome |
|---|---|---|---|
| CI/CD pipeline | AN1 | AN2 | Multi-stage workflow graph with gates |
| build optimization | AN2 | AN8 | Faster feedback through cache and scope control |
| deployment strategy | AN3 | AN6 | Controlled rollout with safe config injection |
| infrastructure as code | AN4 | AN1 | Managed plan/apply flow and drift discipline |
| release automation | AN5 | AN7 | Automated cut, sign, publish, and notify |
| GitHub Actions | AN1 | AN7 | Workflow topology plus event orchestration |
| build caching | AN2 | AN8 | Remote/local cache and affected execution |
| canary deployment | AN3 | AN5 | Evidence-based progressive rollout |
| monorepo build | AN8 | AN2 | Affected-only validation and graph governance |
| workflow automation | AN7 | AN6 | Reactive, context-aware task routing |
| Terraform module | AN4 | AN6 | Reusable infrastructure module with secrets mapping |

## PRODUCTION READINESS RUBRIC

| Capability | Bronze | Silver | Gold | FORGE |
|---|---|---|---|---|
| Pipeline topology | Linear jobs | Stage separation | Reusable workflows | Graph-aware design with policy and artifact contracts |
| Build speed | Basic cache | Parallel jobs | Incremental builds | Telemetry-driven selective execution with remote cache |
| Deploy safety | Manual deploy | Scripted deploy | Health checks | Progressive delivery with rollback state machine |
| IaC maturity | Single stack | Module reuse | Remote state | Policy-governed platform mesh with drift workflows |
| Release rigor | Manual tags | Automated tags | Changelog + publish | Signed, attested, multi-channel release evidence chain |
| Env management | .env files | Secret store | Schema validation | Parity envelope with provenance and blocking diffs |
| Workflow intelligence | Cron jobs | Event triggers | Chatops | Context-enriched healing and escalation lattice |
| Monorepo scale | Full builds | Package scripts | Affected runs | Graph governance and scope-aware release/deploy |

## IMPLEMENTATION PLAYBOOK

### Phase 1: Stabilize
- Create the AN1 stage graph and define artifact contracts.
- Add AN6 config validation so environments cannot silently diverge.
- Introduce AN4 plan/apply separation for infrastructure changes.

### Phase 2: Accelerate
- Add AN2 cache layers, matrix fan-out, and critical-path profiling.
- Add AN8 affected detection if repository scale justifies it.
- Feed performance metrics into workflow summaries for weekly review.

### Phase 3: Safeguard
- Roll out AN3 progressive deployment states and rollback hooks.
- Add AN5 signed release artifacts, SBOMs, and automated notes.
- Put environment approvals and freeze-window logic behind AN7 routing.

### Phase 4: Self-Heal
- Route failures and incidents through AN7 enriched workflows.
- Schedule drift checks, cache warming, and dependency hygiene jobs.
- Use release and deployment metadata to automate reversible actions safely.

## REFERENCE COMMANDS

```bash
# Generate affected targets
npx nx print-affected --base=origin/main --head=HEAD --select=tasks.target.project

# Warm Docker buildx cache in GitHub Actions-compatible mode
docker buildx build --cache-to type=gha,mode=max --cache-from type=gha -t ghcr.io/acme/app:cache .

# Create and review Terraform plan
terraform init -upgrade
terraform fmt -check -recursive
terraform plan -out=tfplan -var="release_ref=v2.8.0"
terraform show -json tfplan > tfplan.json

# Cut a semantic release
npx semantic-release

# Validate runtime config
python scripts/validate_runtime_config.py config/runtime.prod.json

# Trigger rollback automation
gh workflow run rollback.yml -f environment=prod -f release_id=v2.8.0
```

## CLOSING DIRECTIVE

FORGE-AUTOMATION-NEXUS is most powerful when treated as an operating doctrine rather than a single workflow file. Design the graph, measure the graph, constrain the graph, and teach the graph to react to evidence. That is the path from scripted automation to self-healing delivery intelligence.

## APPENDIX A: Pipeline Signals

This appendix provides an operational checklist for pipeline signals within FORGE-AUTOMATION-NEXUS. Use it to standardize implementation reviews, incident retrospectives, and platform maturity assessments.

| Item | Why It Matters | Recommended Treatment |
|---|---|---|
| Queue time | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Critical path duration | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Cache hit rate | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Artifact transfer size | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Flaky test rate | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Deployment error rate | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Rollback frequency | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Drift findings | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Config validation failures | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Release lead time | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |

- **Queue time:** Define owner, source of truth, escalation path, and review cadence.
- **Critical path duration:** Define owner, source of truth, escalation path, and review cadence.
- **Cache hit rate:** Define owner, source of truth, escalation path, and review cadence.
- **Artifact transfer size:** Define owner, source of truth, escalation path, and review cadence.
- **Flaky test rate:** Define owner, source of truth, escalation path, and review cadence.
- **Deployment error rate:** Define owner, source of truth, escalation path, and review cadence.
- **Rollback frequency:** Define owner, source of truth, escalation path, and review cadence.
- **Drift findings:** Define owner, source of truth, escalation path, and review cadence.
- **Config validation failures:** Define owner, source of truth, escalation path, and review cadence.
- **Release lead time:** Define owner, source of truth, escalation path, and review cadence.

## APPENDIX B: Approval Boundaries

This appendix provides an operational checklist for approval boundaries within FORGE-AUTOMATION-NEXUS. Use it to standardize implementation reviews, incident retrospectives, and platform maturity assessments.

| Item | Why It Matters | Recommended Treatment |
|---|---|---|
| Prod deploy approval | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Prod infra apply approval | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Database migration approval | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Freeze window override | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Incident rollback acknowledgement | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Third-party dependency risk review | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Secrets rotation sign-off | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Package publication authority | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Hotfix lane authorization | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Multi-region rollout go/no-go | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |

- **Prod deploy approval:** Define owner, source of truth, escalation path, and review cadence.
- **Prod infra apply approval:** Define owner, source of truth, escalation path, and review cadence.
- **Database migration approval:** Define owner, source of truth, escalation path, and review cadence.
- **Freeze window override:** Define owner, source of truth, escalation path, and review cadence.
- **Incident rollback acknowledgement:** Define owner, source of truth, escalation path, and review cadence.
- **Third-party dependency risk review:** Define owner, source of truth, escalation path, and review cadence.
- **Secrets rotation sign-off:** Define owner, source of truth, escalation path, and review cadence.
- **Package publication authority:** Define owner, source of truth, escalation path, and review cadence.
- **Hotfix lane authorization:** Define owner, source of truth, escalation path, and review cadence.
- **Multi-region rollout go/no-go:** Define owner, source of truth, escalation path, and review cadence.

## APPENDIX C: Rollback Triggers

This appendix provides an operational checklist for rollback triggers within FORGE-AUTOMATION-NEXUS. Use it to standardize implementation reviews, incident retrospectives, and platform maturity assessments.

| Item | Why It Matters | Recommended Treatment |
|---|---|---|
| 5xx spike | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Latency SLO breach | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Synthetic check failure | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Migration error | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Queue backlog saturation | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Memory regression | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| CPU saturation | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Error budget burn | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Feature flag anomaly | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |
| Security scanner block | Keeps automation trustworthy and auditable. | Measure it, set a threshold, and route exceptions through AN7. |

- **5xx spike:** Define owner, source of truth, escalation path, and review cadence.
- **Latency SLO breach:** Define owner, source of truth, escalation path, and review cadence.
- **Synthetic check failure:** Define owner, source of truth, escalation path, and review cadence.
- **Migration error:** Define owner, source of truth, escalation path, and review cadence.
- **Queue backlog saturation:** Define owner, source of truth, escalation path, and review cadence.
- **Memory regression:** Define owner, source of truth, escalation path, and review cadence.
- **CPU saturation:** Define owner, source of truth, escalation path, and review cadence.
- **Error budget burn:** Define owner, source of truth, escalation path, and review cadence.
- **Feature flag anomaly:** Define owner, source of truth, escalation path, and review cadence.
- **Security scanner block:** Define owner, source of truth, escalation path, and review cadence.

## MODULE SIGNAL MATRICES

### AN1 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN1 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN2 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN2 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN3 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN3 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN4 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN4 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN5 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN5 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN6 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN6 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN7 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN7 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

### AN8 Signal Matrix

| Signal | Source | Action | Notes |
|---|---|---|---|
| success | workflow/job | Promote or unblock downstream dependency | Persist summary artifact and metadata. |
| failure | workflow/job | Stop propagation and create actionable context | Prefer local containment to global cancellation. |
| warning | policy or metric | Escalate for review or degrade safely | Warnings become trend data for weekly tuning. |
| drift | infra/config | Open remediation workflow | Attach diff and ownership metadata. |
| latency | metrics | Optimize, shard, or cache | Correlate to repository changes and runner type. |

AN8 should emit machine-readable summaries and human-readable workflow annotations so that both automation and operators can understand what changed, why it mattered, and what should happen next.

