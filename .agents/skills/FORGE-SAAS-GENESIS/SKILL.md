---
name: FORGE-SAAS-GENESIS
description: >-
  Unified SaaS product intelligence fusing multi-tenant architecture, subscription
  billing, payment processing, user onboarding, feature flags, usage analytics,
  pricing strategy, marketplace integration, white-labeling, and growth engineering
  into a complete product launch fabric. Triggers on SaaS, subscription, billing,
  multi-tenant, onboarding, feature flags, pricing, marketplace, white-label,
  growth. Creates emergent capability where entire SaaS products are architecturally
  designed, monetized, and growth-optimized as a unified system.
category: engineering
version: "1.0.0"
triggers:
  - "SaaS architecture"
  - "subscription billing"
  - "multi-tenant design"
  - "payment processing"
  - "user onboarding"
  - "feature flags"
  - "pricing strategy"
  - "usage analytics"
  - "marketplace integration"
  - "white-label platform"
  - "growth engineering"
  - "product launch"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: cross-domain-innovation
  emergent_capability: "Complete SaaS product genesis from architecture through monetization to growth optimization"
---

# 🚀 FORGE-SAAS-GENESIS
> **Complete Product Launch Intelligence (Ω-Δ99)**

## Overview

| Property | Value |
|---|---|
| **Tier** | FORGE |
| **Domain** | SaaS Architecture · Monetization · Growth |
| **Scope** | Tenant model → revenue engine → growth flywheel |
| **Emergent** | **Product Genesis** — design, launch, monetize, and scale as one system |
| **Key Principle** | Build tenancy, money, and growth boundaries together |

## Forged from 10 Skills

| # | Source Skill | Contribution |
|---|---|---|
| 1 | `multi-tenant-architect` | Tenant isolation, data partitioning |
| 2 | `subscription-billing-engine` | Stripe/Paddle, plan management |
| 3 | `payment-processing-specialist` | Payment flows, invoicing, taxes |
| 4 | `user-onboarding-designer` | Activation funnels, product tours |
| 5 | `feature-flag-strategist` | LaunchDarkly, A/B testing, gradual rollout |
| 6 | `usage-analytics-engine` | Mixpanel, PostHog, cohort analysis |
| 7 | `pricing-strategist` | Freemium, usage-based, tiered pricing models |
| 8 | `marketplace-builder` | App stores, plugins, partner ecosystems |
| 9 | `white-label-architect` | Theming, branding, tenant customization |
| 10 | `growth-engineering` | PLG loops, referral systems, retention |

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        FORGE-SAAS-GENESIS (Ω-Δ99)                          │
│                                                                            │
│  SG1 ──▶ SG2 ──▶ SG3                                                       │
│   │       │       │                                                        │
│   └──────▶ SG4 ──▶ SG5                                                     │
│            │       │                                                       │
│            └──────▶ SG6 ◀────▶ SG7                                         │
│                      │         │                                            │
│                      └────────▶ SG8                                         │
│                                                                            │
│  SG1 Multi-Tenant      SG5 Feature Mgmt     SG7 Pricing & Monetization     │
│  SG2 Billing           SG6 Analytics        SG8 Growth & Marketplace        │
│  SG3 Payments          SG4 Onboarding                                        │
└────────────────────────────────────────────────────────────────────────────┘
```

## SG1: Multi-Tenant Architecture

**Purpose:** Establish the trust boundary so every request resolves ownership, isolation, branding, region, and entitlements before business logic runs.

**Design Pattern:** Shared control plane + tenant-aware data plane + policy-enforced isolation.

SG1 defines how tenants are identified, where their data lives, and how platform capabilities inherit tenant context. It is the base layer for billing, analytics, flags, and white-label controls.

The module supports shared-schema, schema-per-tenant, and database-per-tenant models. Selection is economic and regulatory, not ideological.

The key sequence is domain → tenant → workspace → contract → entitlements → data policy. That sequence keeps product, finance, and ops aligned.

### Key Operations

- Resolve tenant from subdomain, custom domain, SSO assertion, or API credential.
- Enforce tenant scope on every read, write, queue message, and analytics event.
- Load plan, branding, region, and contract overrides into one context object.
- Support tenant lifecycle actions: create, migrate, suspend, archive, delete.
- Expose tenant-aware observability for spend, latency, errors, and adoption.

### TypeScript Example

```typescript
export type IsolationMode = 'shared' | 'schema' | 'database';

export interface TenantContext {
  tenantId: string;
  workspaceId: string;
  planCode: string;
  region: 'us' | 'eu' | 'apac';
  isolationMode: IsolationMode;
  entitlements: Record<string, boolean>;
}

export async function resolveTenant(host: string): Promise<TenantContext> {
  const tenant = await tenantRepo.findByHost(host);
  if (!tenant) throw new Error(`Unknown tenant: ${host}`);
  const contract = await contractRepo.load(tenant.id);
  return {
    tenantId: tenant.id,
    workspaceId: tenant.workspaceId,
    planCode: contract.planCode,
    region: tenant.region,
    isolationMode: tenant.isolationMode,
    entitlements: await entitlementRepo.forPlan(contract.planCode),
  };
}
```

### Python Example

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    workspace_id: str
    plan_code: str
    region: str

class TenantRepository:
    def projects(self, db, ctx: TenantContext):
        return db.execute(
            'select id, name from projects where tenant_id = :tenant_id',
            {'tenant_id': ctx.tenant_id},
        ).mappings().all()
```

### SQL Example

```sql
create table tenants (
    id uuid primary key,
    slug text not null unique,
    isolation_mode text not null,
    region text not null,
    status text not null,
    created_at timestamptz not null default now()
);

create table workspaces (
    id uuid primary key,
    tenant_id uuid not null references tenants(id),
    name text not null,
    created_at timestamptz not null default now()
);

create index idx_workspaces_tenant on workspaces (tenant_id);
```

### Integration Points

- Feeds SG2 with the billable owner and contract scope.
- Feeds SG5 with tenant, region, and plan context for flag evaluation.
- Feeds SG6 with tenant-level metrics and identity stitching.
- Feeds SG8 with white-label and marketplace ownership boundaries.

### Operational Checks

- Test cross-tenant denial paths, not only happy paths.
- Carry tenant context through background jobs and webhooks.
- Centralize tenant resolution instead of duplicating it per service.
- Document the isolation upgrade path before enterprise sales begin.

### Success Signals

- Zero confirmed cross-tenant leaks.
- Tenant lookup fits inside request latency budget.
- Support can explain ownership of any object in one query chain.
- Premium isolation upgrades do not require application forks.

---

## SG2: Billing & Subscriptions

**Purpose:** Model recurring revenue through trials, plan catalogs, amendments, renewals, grace periods, and entitlement synchronization.

**Design Pattern:** Event-driven subscription ledger with payment-provider reconciliation.

SG2 treats revenue as a long-running customer state machine, not a one-time charge. Trial, active, past_due, grace, canceled, and enterprise contract states all matter.

The internal ledger is authoritative for product behavior while Stripe or Paddle remains authoritative for settlement and invoices.

Plans stay separate from entitlements so enterprise overrides can change product behavior without mutating the global catalog.

### Key Operations

- Define plans, intervals, seat rules, add-ons, and override policies.
- Start and expire trials with predictable conversion handling.
- Handle upgrades, downgrades, pauses, proration, and seat true-ups.
- Reconcile provider webhooks into a canonical ledger.
- Sync entitlements to auth, UI, flags, and usage metering.

### TypeScript Example

```typescript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function upsertSubscription(input: {
  tenantId: string;
  customerId: string;
  priceId: string;
  quantity: number;
}) {
  const current = await subscriptionRepo.findActive(input.tenantId);
  if (!current) {
    return stripe.subscriptions.create({
      customer: input.customerId,
      items: [{ price: input.priceId, quantity: input.quantity }],
      trial_period_days: 14,
      metadata: { tenantId: input.tenantId },
    });
  }
  return stripe.subscriptions.update(current.providerId, {
    items: [{ id: current.itemId, price: input.priceId, quantity: input.quantity }],
    proration_behavior: 'always_invoice',
  });
}
```

### Python Example

```python
class BillingLedger:
    def invoice_paid(self, repo, tenant_id: str, invoice_id: str):
        repo.append_event(tenant_id, 'invoice.paid', {'invoice_id': invoice_id})
        repo.update_status(tenant_id, 'active')

    def start_grace(self, repo, tenant_id: str, until_iso: str):
        repo.append_event(tenant_id, 'billing.grace_started', {'until': until_iso})
        repo.set_contract_field(tenant_id, 'grace_until', until_iso)

    def cancel_at_period_end(self, repo, tenant_id: str):
        repo.append_event(tenant_id, 'subscription.cancel_requested', {})
        repo.set_contract_field(tenant_id, 'cancel_at_period_end', True)
```

### SQL Example

```sql
create table billing_plans (
    code text primary key,
    interval text not null,
    base_amount_cents integer not null,
    trial_days integer not null default 14,
    active boolean not null default true
);

create table subscriptions (
    id uuid primary key,
    tenant_id uuid not null references tenants(id),
    provider_subscription_id text not null unique,
    plan_code text not null references billing_plans(code),
    status text not null,
    seat_count integer not null default 1,
    current_period_end timestamptz
);
```

### Integration Points

- Consumes tenant ownership from SG1.
- Consumes invoice outcomes from SG3.
- Implements packages defined by SG7.
- Triggers trial and upgrade messaging in SG4.

### Operational Checks

- Store every state transition as a durable ledger event.
- Never derive entitlements directly from display-plan names.
- Simulate proration and downgrade paths before launch.
- Separate voluntary churn from failed-payment churn.

### Success Signals

- Billing state and entitlement state remain synchronized.
- Finance can explain MRR changes from ledger events.
- Webhook replay does not duplicate business actions.
- Trial conversion flow stays stable during catalog changes.

---

## SG3: Payment Processing

**Purpose:** Collect money safely with checkout, invoicing, taxation, receipts, retries, and settlement-aware recovery workflows.

**Design Pattern:** Payment intent orchestration with idempotent webhook handling.

SG3 turns a pricing decision into collected cash. It handles self-serve checkout, finance-grade invoicing, regional taxes, and failure recovery.

The module separates quote creation, payment authorization, invoice settlement, and entitlement confirmation so business logic is resilient to provider timing.

It supports both card-first SMB motion and invoice-first enterprise motion without splitting the product into two architectures.

### Key Operations

- Create checkout sessions and one-time purchase flows.
- Generate invoices for subscriptions, overages, and manual line items.
- Apply tax rules by region and business status.
- Record idempotent webhook outcomes and recovery attempts.
- Export finance-ready payment records and receipts.

### TypeScript Example

```typescript
import Stripe from 'stripe';
const stripeClient = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function createCheckout(tenantId: string, customerId: string, priceId: string) {
  const session = await stripeClient.checkout.sessions.create({
    mode: 'subscription',
    customer: customerId,
    line_items: [{ price: priceId, quantity: 1 }],
    automatic_tax: { enabled: true },
    metadata: { tenantId },
    success_url: 'https://app.example.com/billing/success',
    cancel_url: 'https://app.example.com/billing/cancel',
  });
  await paymentRepo.recordSession({ tenantId, providerSessionId: session.id });
  return session.url;
}
```

### Python Example

```python
class InvoiceService:
    def issue(self, repo, tenant_id: str, subtotal_cents: int, tax_cents: int):
        total = subtotal_cents + tax_cents
        return repo.create_invoice(tenant_id, subtotal_cents, tax_cents, total)

    def queue_dunning(self, repo, tenant_id: str, invoice_id: str):
        repo.add_recovery_step(tenant_id, invoice_id, 'email_reminder_1')
        repo.add_recovery_step(tenant_id, invoice_id, 'email_reminder_2')
        repo.add_recovery_step(tenant_id, invoice_id, 'restrict_service')
```

### SQL Example

```sql
create table invoices (
    id uuid primary key,
    tenant_id uuid not null references tenants(id),
    invoice_number text not null unique,
    subtotal_cents integer not null,
    tax_cents integer not null,
    total_cents integer not null,
    status text not null,
    due_at timestamptz,
    paid_at timestamptz
);

create table payment_events (
    provider_event_id text primary key,
    event_type text not null,
    payload jsonb not null,
    processed_at timestamptz not null default now()
);
```

### Integration Points

- Updates SG2 subscription state from invoice outcomes.
- Uses SG7 pricing results to build quotes and overage lines.
- Sends checkout and recovery events to SG6 analytics.
- Shares partner and marketplace settlements with SG8.

### Operational Checks

- Use provider event IDs for idempotency.
- Store tax snapshots on invoices, not only in provider logs.
- Test card failure and retry sequences in staging.
- Do not unlock service until business settlement rules are satisfied.

### Success Signals

- Checkout completion stays healthy across regions.
- Duplicate webhooks never create duplicate invoices or upgrades.
- Tax and invoice records reconcile cleanly.
- Recovery workflows reduce involuntary churn.

---

## SG4: Onboarding Engine

**Purpose:** Move users from sign-up to first value through persona-specific checklists, tours, nudges, and milestone scoring.

**Design Pattern:** Activation state machine driven by product events.

SG4 measures onboarding by value milestones, not by whether a tooltip was shown. It is the bridge between acquisition and monetization.

The flow changes by role, plan, use case, and channel. A solo founder, team admin, and enterprise champion do not need the same path.

The module also detects stall states and triggers reminders, support assists, or alternate playbooks before trial value collapses.

### Key Operations

- Define milestone maps by persona and plan.
- Render contextual tours and checklists from live product state.
- Detect stalled users and route lifecycle interventions.
- Score activation at user and tenant level.
- Hand proven-value users into upgrade prompts and referrals.

### TypeScript Example

```typescript
export type Step = { key: string; label: string; done: boolean; href: string };

export function buildChecklist(input: {
  createdProject: boolean;
  importedData: boolean;
  invitedTeammate: boolean;
  connectedIntegration: boolean;
  planCode: string;
}): Step[] {
  const steps: Step[] = [
    { key: 'project', label: 'Create first project', done: input.createdProject, href: '/projects/new' },
    { key: 'import', label: 'Import data', done: input.importedData, href: '/imports' },
    { key: 'invite', label: 'Invite a teammate', done: input.invitedTeammate, href: '/settings/team' },
  ];
  if (input.planCode !== 'free') steps.push({ key: 'integration', label: 'Connect integration', done: input.connectedIntegration, href: '/settings/integrations' });
  return steps;
}
```

### Python Example

```python
class OnboardingOrchestrator:
    def apply_event(self, repo, tenant_id: str, user_id: str, event_name: str):
        transitions = {
            'project.created': 'created_first_project',
            'data.imported': 'imported_data',
            'team.invited': 'invited_teammate',
            'integration.connected': 'connected_integration',
        }
        if event_name in transitions:
            repo.complete_step(tenant_id, user_id, transitions[event_name])
        return repo.activation_score(tenant_id, user_id)
```

### SQL Example

```sql
create table onboarding_playbooks (
    id uuid primary key,
    persona text not null,
    plan_code text not null,
    acquisition_source text not null
);

create table user_onboarding_state (
    tenant_id uuid not null references tenants(id),
    user_id uuid not null,
    step_key text not null,
    completed_at timestamptz,
    primary key (tenant_id, user_id, step_key)
);
```

### Integration Points

- Reads trial and contract state from SG2.
- Sends milestone events into SG6.
- Uses SG5 to test alternate sequences and prompts.
- Hands activated users into SG8 invitation and referral loops.

### Operational Checks

- Tie every step to a measurable event.
- Distinguish tour completion from value completion.
- Suppress upsell prompts before first value appears.
- Review onboarding performance after every major UX change.

### Success Signals

- Median time-to-first-value declines.
- Activation correlates strongly with conversion.
- New-user support burden drops as playbooks improve.
- Enterprise admins can self-provision without manual rescue.

---

## SG5: Feature Management

**Purpose:** Unify operational kill switches, premium access, and experimentation under one controlled access layer.

**Design Pattern:** Policy-evaluated flags with experiment overlays and cleanup discipline.

SG5 handles three forms of controlled access: rollout safety, plan gating, and product experimentation. Treating them as one policy system reduces duplication.

The evaluation context includes tenant, user, role, plan, region, cohort, and experiment assignment. That makes progressive delivery commercially aware.

Cleanup is part of the module. Flags without owners and sunset criteria become platform debt.

### Key Operations

- Evaluate operational, entitlement, and experimental flags from one context object.
- Roll out features by region, plan, tenant, or percentage bucket.
- Capture exposure events for experimentation integrity.
- Provide emergency kill switches for risky capabilities.
- Retire stale flags on a defined cleanup cadence.

### TypeScript Example

```typescript
export type FlagRule = {
  key: string;
  allowedPlans?: string[];
  allowedRegions?: string[];
  percentage?: number;
};

export function evaluateFlag(rule: FlagRule, ctx: { planCode: string; region: string; subject: string }) {
  if (rule.allowedPlans && !rule.allowedPlans.includes(ctx.planCode)) return false;
  if (rule.allowedRegions && !rule.allowedRegions.includes(ctx.region)) return false;
  if (rule.percentage == null) return true;
  const hash = [...`${rule.key}:${ctx.subject}`].reduce((n, c) => (n * 31 + c.charCodeAt(0)) >>> 0, 0);
  return (hash % 100) < rule.percentage;
}
```

### Python Example

```python
class ExperimentReporter:
    def summarize(self, rows):
        totals = {}
        for row in rows:
            bucket = totals.setdefault(row['variant'], {'exposures': 0, 'activations': 0, 'upgrades': 0})
            bucket['exposures'] += row['exposures']
            bucket['activations'] += row['activations']
            bucket['upgrades'] += row['upgrades']
        return totals
```

### SQL Example

```sql
create table feature_flags (
    key text primary key,
    kind text not null,
    owner text not null,
    status text not null,
    sunset_at timestamptz
);

create table feature_exposures (
    id bigserial primary key,
    tenant_id uuid not null references tenants(id),
    user_id uuid not null,
    flag_key text not null references feature_flags(key),
    variant text,
    exposed_at timestamptz not null default now()
);
```

### Integration Points

- Implements premium fences defined by SG7 and SG2.
- Supports onboarding experiments for SG4.
- Emits exposure data to SG6.
- Protects risky marketplace or partner launches in SG8.

### Operational Checks

- Require owner, hypothesis, and sunset date for non-permanent flags.
- Log exposure when experiments are evaluated.
- Do not rely on frontend-only checks for premium access.
- Review stale flags in each release cycle.

### Success Signals

- Rollouts can pause instantly without redeploys.
- Experiment readouts remain exposure-aware.
- Premium gating matches commercial contracts.
- Flag debt stays bounded over time.

---

## SG6: Analytics Intelligence

**Purpose:** Turn product behavior into decisions about activation, retention, monetization, support, and roadmap direction.

**Design Pattern:** Canonical event taxonomy backed by warehouse-grade lifecycle models.

SG6 is product memory. Without consistent event names and identity dimensions, pricing and growth decisions become opinion-driven.

It uses both product analytics tools for fast iteration and SQL models for durable financial and retention analysis.

The module produces triggers as well as dashboards so stalled trials, churn signals, and successful expansion patterns feed action systems.

### Key Operations

- Define tenant-aware event taxonomy and identity rules.
- Track funnels for signup, activation, conversion, expansion, and referral.
- Compute cohort retention and monetization curves.
- Surface drop-off segments and churn-risk alerts.
- Supply experiment-aware readouts for SG5 and pricing readouts for SG7.

### TypeScript Example

```typescript
export async function trackEvent(client: any, input: {
  event: string;
  tenantId: string;
  userId: string;
  workspaceId: string;
  planCode: string;
  properties?: Record<string, unknown>;
}) {
  return client.capture({
    distinctId: input.userId,
    event: input.event,
    properties: {
      tenant_id: input.tenantId,
      workspace_id: input.workspaceId,
      plan_code: input.planCode,
      ...input.properties,
    },
  });
}
```

### Python Example

```python
class CohortAnalyzer:
    def retention_sql(self) -> str:
        return '''
        with cohort as (
            select tenant_id, min(date_trunc('month', occurred_at)) as cohort_month
            from analytics_events
            group by tenant_id
        )
        select * from cohort
        '''
```

### SQL Example

```sql
create table analytics_events (
    id bigserial primary key,
    tenant_id uuid not null references tenants(id),
    user_id uuid not null,
    workspace_id uuid not null references workspaces(id),
    event_name text not null,
    plan_code text not null,
    properties jsonb not null default '{}'::jsonb,
    occurred_at timestamptz not null default now()
);

create index idx_analytics_events_tenant_time on analytics_events (tenant_id, occurred_at desc);
```

### Integration Points

- Measures SG4 activation milestones.
- Interprets SG5 experiment outcomes with exposure context.
- Validates SG7 pricing and expansion decisions.
- Attributes SG8 referrals, installs, and partner-driven revenue.

### Operational Checks

- Version the event taxonomy like an API.
- Require tenant and plan context on lifecycle events.
- Keep semantic definitions of activation, retained, and churned documented.
- Mirror critical events into the warehouse.

### Success Signals

- Metrics are consistent across product, BI, and finance reviews.
- Retention analysis no longer depends on ad hoc one-off SQL.
- Experiment outcomes can be explained by segment and cohort.
- Growth decisions become evidence-driven.

---

## SG7: Pricing & Monetization

**Purpose:** Align revenue with customer value through packaging, value metrics, meters, overages, and expansion paths.

**Design Pattern:** Value-metric pricing with configurable plan fences and metered overlays.

SG7 defines what is free, what is paid, what expands, and what feels fair. It is not only a finance function; it is product design expressed commercially.

The module supports freemium acquisition, seat-based collaboration, usage-based intensity pricing, and enterprise add-ons inside one coherent packaging model.

It treats pricing as a living control system and expects experimentation, visibility, and contract overrides.

### Key Operations

- Define packages, add-ons, value metrics, and usage meters.
- Set hard limits, soft warnings, and overage behaviors.
- Simulate price changes and churn risk before rollout.
- Map plans to entitlements and upgrade prompts.
- Feed billable usage into invoices and account health models.

### TypeScript Example

```typescript
export function quote(snapshot: { planCode: string; seats: number; apiCalls: number; storageGb: number }) {
  const base = { free: 0, starter: 4900, growth: 14900, scale: 49900 }[snapshot.planCode] ?? 0;
  const seatOverage = Math.max(snapshot.seats - 5, 0) * 1200;
  const apiIncluded = snapshot.planCode === 'growth' ? 250000 : 50000;
  const apiOverage = Math.max(snapshot.apiCalls - apiIncluded, 0) * 0.02;
  const storageIncluded = snapshot.planCode === 'growth' ? 250 : 50;
  const storageOverage = Math.max(snapshot.storageGb - storageIncluded, 0) * 30;
  return Math.round(base + seatOverage + apiOverage + storageOverage);
}
```

### Python Example

```python
class PricingSimulator:
    def project(self, current_amount: int, proposed_amount: int) -> dict:
        increase_pct = (proposed_amount - current_amount) / max(current_amount, 1)
        churn_probability = min(max(increase_pct * 0.6, 0), 0.4)
        retained_value = int(proposed_amount * (1 - churn_probability))
        return {'retained_value': retained_value, 'churn_probability': churn_probability}
```

### SQL Example

```sql
create table usage_meters (
    key text primary key,
    unit text not null,
    reset_interval text not null
);

create table tenant_usage_daily (
    usage_date date not null,
    tenant_id uuid not null references tenants(id),
    meter_key text not null references usage_meters(key),
    quantity numeric(18,4) not null,
    primary key (usage_date, tenant_id, meter_key)
);
```

### Integration Points

- Supplies plan structure to SG2.
- Supplies overage and quote inputs to SG3.
- Uses SG5 for price-fence and packaging experiments.
- Uses SG6 to judge conversion, expansion, and churn outcomes.

### Operational Checks

- Choose meters customers can understand and monitor.
- Show warnings before overages become charges.
- Publish plan-to-entitlement mappings clearly.
- Model enterprise overrides without forking the catalog.

### Success Signals

- Users can explain why they fit a plan.
- Overage disputes remain rare.
- Expansion revenue rises without matching support pain.
- Price changes are measured by cohort, not opinion.

---

## SG8: Growth & Marketplace

**Purpose:** Build self-reinforcing acquisition and expansion loops through referrals, collaboration invites, partner APIs, marketplaces, and white-label channels.

**Design Pattern:** Product-led growth loop plus extensibility platform.

SG8 treats growth as a product property. The product should recruit more users, unlock more use cases, and widen distribution through ecosystems.

Marketplace and partner systems are included because platform distribution requires identity, billing, analytics, and permission models from day one.

White-labeling is part of the same fabric because reseller and agency growth often depends on controlled branding and tenant-scoped customization.

### Key Operations

- Create referral and invite loops tied to collaboration behavior.
- Offer marketplace listings, install flows, and app review states.
- Expose partner APIs, webhooks, and sandbox tenants.
- Enable white-label branding, custom domains, and partner packaging.
- Track attributed conversions, installs, and partner revenue.

### TypeScript Example

```typescript
export async function createReferral(repo: any, tenantId: string, userId: string, campaign: string) {
  const code = crypto.randomUUID().slice(0, 8);
  await repo.insert({ tenantId, userId, code, campaign });
  return `https://app.example.com/signup?ref=${code}`;
}

export async function requestInstall(repo: any, tenantId: string, appId: string, installedBy: string) {
  await repo.recordInstallRequest({ tenantId, appId, installedBy, status: 'pending_oauth' });
}
```

### Python Example

```python
class PartnerRevenueService:
    def payout(self, settled_amount_cents: int, share_percent: float) -> int:
        return int(settled_amount_cents * share_percent / 100)

    def activate_white_label(self, repo, tenant_id: str, brand_name: str, domain: str):
        repo.enable_white_label(tenant_id, brand_name, domain)
        repo.enqueue_brand_assets(tenant_id)
```

### SQL Example

```sql
create table referrals (
    code text primary key,
    tenant_id uuid not null references tenants(id),
    user_id uuid not null,
    campaign text not null,
    converted_tenant_id uuid
);

create table marketplace_apps (
    id uuid primary key,
    slug text not null unique,
    name text not null,
    share_percent numeric(5,2) not null default 0,
    status text not null
);
```

### Integration Points

- Uses SG4 activation to decide when invite loops should fire.
- Uses SG6 to attribute referrals, installs, and partner revenue.
- Uses SG7 to monetize apps, rev-share, and white-label add-ons.
- Uses SG1 to keep apps and brand assets tenant-scoped.

### Operational Checks

- Review app scopes before install.
- Attribute settled revenue before partner payout.
- Keep brand customization in config, never code forks.
- Offer sandbox tenants for partners and agencies.

### Success Signals

- Referral traffic produces activated tenants, not empty signups.
- Marketplace installs correlate with retention or expansion lift.
- White-label customers launch without bespoke engineering.
- Partner payouts reconcile with settled revenue.

---

## Decision Tree for Module Routing

```
START
  │
  ├─ Isolation, ownership, workspace boundaries?        → SG1
  ├─ Plans, trials, renewals, contracts?                → SG2
  ├─ Checkout, invoices, tax, payment recovery?         → SG3
  ├─ Activation, tours, checklists, time-to-value?      → SG4
  ├─ Progressive rollout, gating, experiments?          → SG5
  ├─ Funnels, cohorts, retention, attribution?          → SG6
  ├─ Packaging, limits, meters, expansion?              → SG7
  ├─ Referrals, marketplace, partner motion?            → SG8
  └─ Multiple of the above at once?                     → Whole FORGE system
```

## Cross-Module Integration

### Cascade 1: Trial to Paid
- SG2 creates the trial and sets commercial state.
- SG4 guides the user to first value before expiration.
- SG5 experiments with upgrade timing and messaging.
- SG6 measures conversion, drop-off, and activation quality.
- SG3 collects payment and confirms invoice settlement.

### Cascade 2: Enterprise White-Label Expansion
- SG1 provisions tenant boundaries and custom domains.
- SG7 packages enterprise controls and white-label add-ons.
- SG2 records annual terms and seat minimums.
- SG8 activates branded notifications, partner attribution, and resale paths.

### Cascade 3: Usage-Based Expansion
- SG6 finds healthy tenants approaching usage thresholds.
- SG7 computes best-fit package and overage math.
- SG5 reveals contextual upgrade prompts and premium features.
- SG3 and SG2 convert that commercial change into billable state.

### Cascade 4: Marketplace Growth Loop
- SG8 launches an app, template, or integration listing.
- SG4 onboards new tenants through ecosystem-specific playbooks.
- SG6 attributes activation and revenue back to the source.
- SG7 monetizes installs, add-ons, or revenue share where applicable.

## Domain Applications

### 1. B2B Workflow SaaS
Seat-based collaboration, tenant-scoped projects, connector marketplaces, and automation overages all fit this operating model.

### 2. AI SaaS
Credit or token metering, premium model access, high-variance usage, and trial activation can be modeled coherently.

### 3. Agency / White-Label SaaS
Custom domains, branded emails, reseller channels, client sub-workspaces, and partner onboarding become first-class rather than exceptions.

### 4. Platform + Ecosystem SaaS
Once the core app expands into apps, templates, APIs, and partner revenue share, the same fabric governs identity, billing, and growth.

## Quick Reference Card

```text
╔════════════════════════════════════════════════════════════════════════════╗
║                     FORGE-SAAS-GENESIS QUICK REFERENCE                    ║
╠════════════════════════════════════════════════════════════════════════════╣
║ SG1 tenant boundary     │ SG5 flags & rollout │ SG7 pricing & meters     ║
║ SG2 subscriptions       │ SG6 funnels & cohorts │ SG8 growth & ecosystem ║
║ SG3 checkout & invoices │ SG4 activation engine │ whole-system launch    ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Use the full superskill whenever architecture, monetization, and growth   ║
║ decisions are interacting and must be designed as one product system.     ║
╚════════════════════════════════════════════════════════════════════════════╝
```
