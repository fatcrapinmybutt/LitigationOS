---
name: FORGE-FULLSTACK-REACTOR
description: >-
  Nuclear Reactor for Full-Stack Product Creation. Fuses frontend (React/Next.js),
  backend (Node.js), database design, testing, deployment, and monitoring into a 
  unified product synthesis engine. Describe a feature → receive complete implementation
  spanning ALL layers with proper integration, type safety across boundaries, and
  production-ready deployment. The fusion creates END-TO-END PRODUCT SYNTHESIS —
  understanding how UI decisions affect DB schema, how API design impacts testing,
  how deployment constraints shape architecture.
  Use for "full-stack", "new feature", "product", "build app", "complete implementation",
  "frontend to backend", or "end-to-end".
category: engineering
version: "1.0.0"
triggers:
  - full-stack
  - new feature
  - build app
  - complete implementation
  - frontend to backend
  - end-to-end
  - product creation
  - feature implementation
  - React + API
  - full stack TypeScript
metadata:
  tier: FORGE
  fused_skills: 9
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-07-17
  forge_class: cross-domain-innovation
  emergent_capability: "End-to-end product synthesis — all layers as one coherent system"
---

# ⚛️ FORGE-FULLSTACK-REACTOR

## Nuclear Product Synthesis Engine (Ω-Δ99)

> **FORGE-class fusion of 9 domain skills into a single product creation reactor.**
> Individual skills know ONE layer. This reactor understands how ALL layers interact —
> that a many-to-many DB relationship implies a join table, a paginated API response,
> a list component with infinite scroll, integration tests across the join, a migration
> in the deployment pipeline, and observability on query performance. **No single skill
> sees the full chain. The reactor does.**
>
> Describe a product feature in plain language → receive a COMPLETE, production-ready
> implementation spanning UI → API → Database → Tests → Deployment → Monitoring.
> Every layer aware of every other layer. Zero gaps. Zero drift. One atomic operation.

---

## Forged Skills Matrix

| # | Source Skill | Domain | Contribution to Reactor | Fusion Role |
|---|---|---|---|---|
| 1 | `react-best-practices` | Frontend | Component architecture, hooks, state management | UI Reactor core |
| 2 | `nextjs-expert` | Full-Stack Framework | SSR/SSG, API routes, file-based routing | Framework spine |
| 3 | `nodejs-backend-patterns` | Backend | Express/Fastify, middleware, error handling | API Forge engine |
| 4 | `database-schema-design` | Data | Modeling, normalization, indexes, migrations | Data Layer Architect |
| 5 | `testing-strategies` | Quality | Test pyramid, coverage, TDD, E2E | Test Matrix Generator |
| 6 | `deployment-automation` | DevOps | CI/CD, pipelines, environment management | Deployment Capsule |
| 7 | `tailwind-patterns` | Styling | Responsive design, utility classes, theming | Visual synthesis |
| 8 | `docker-expert` | Containerization | Multi-stage builds, compose, orchestration | Container forge |
| 9 | `monitoring-observability` | Operations | Logging, metrics, tracing, alerting | Observability injection |

**Fusion Class**: Cross-Domain Innovation
**Emergent Capability**: End-to-end product synthesis — all layers as one coherent system

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ⚛️  FORGE-FULLSTACK-REACTOR                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  FEATURE REQUEST (Plain Language)                │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ FR1: Feature    │                                  │
│                    │ Decomposition   │                                  │
│                    │ Engine          │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ FR2: Type-Safe  │                                  │
│                    │ Boundary        │◄─── Shared types flow through    │
│                    │ Synthesizer     │     ALL layers below             │
│                    └────────┬────────┘                                  │
│                             │                                           │
│          ┌──────────────────┼──────────────────┐                       │
│          │                  │                  │                        │
│  ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐               │
│  │ FR3: UI       │ │ FR4: API      │ │ FR5: Data     │               │
│  │ Reactor       │ │ Forge         │ │ Layer         │               │
│  │               │ │               │ │ Architect     │               │
│  │ React/Next.js │ │ REST/GraphQL  │ │ Schema +      │               │
│  │ + Tailwind    │ │ + Validation  │ │ Migrations    │               │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘               │
│          │                  │                  │                        │
│          └──────────────────┼──────────────────┘                       │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ FR6: Test       │                                  │
│                    │ Matrix          │◄─── Tests span ALL boundaries   │
│                    │ Generator       │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ FR7: Deployment │                                  │
│                    │ Capsule         │◄─── Docker + CI/CD + Env        │
│                    └────────┬────────┘                                  │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ FR8:            │                                  │
│                    │ Observability   │◄─── Wired into EVERY layer      │
│                    │ Injection       │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│                    ┌────────▼────────┐                                  │
│                    │ COMPLETE        │                                  │
│                    │ PRODUCTION-READY│                                  │
│                    │ FEATURE         │                                  │
│                    └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module FR1: Feature Decomposition Engine

**Purpose**: Transform any plain-language feature request into a structured decomposition
spanning all implementation layers — simultaneously, not sequentially.

### Decomposition Protocol

When receiving a feature request, immediately decompose into:

1. **UI Surface**: What does the user see and interact with?
   - Pages / routes required
   - Components (atomic → composite hierarchy)
   - User interactions and state transitions
   - Responsive breakpoints and accessibility requirements

2. **API Contract**: What data flows between client and server?
   - Endpoints (method, path, request/response shape)
   - Authentication / authorization requirements
   - Rate limiting and caching strategy
   - Error response taxonomy

3. **Data Model**: What persists and how is it structured?
   - Entities and their relationships (1:1, 1:N, M:N)
   - Required indexes for query patterns
   - Migration steps from current schema
   - Seed data for development

4. **Test Surface**: What must be verified?
   - Unit test targets per layer
   - Integration test boundaries (API ↔ DB, UI ↔ API)
   - E2E user journey scenarios
   - Edge cases and error paths

5. **Deployment Delta**: What changes in infrastructure?
   - New environment variables
   - Database migration ordering
   - Container image changes
   - CI/CD pipeline modifications

6. **Observability Hooks**: What do we need to monitor?
   - New metrics to emit
   - Log events to capture
   - Traces to instrument
   - Alerts to configure

### Example Decomposition

**Input**: "Add a team invitation system where admins can invite users by email"

**Output**:
```yaml
feature: team-invitations
ui:
  pages: [/team/invitations, /invite/[token]]
  components: [InviteForm, InvitationList, InviteStatus, AcceptInvitePage]
  state: [invitations list, form state, invitation status polling]
api:
  endpoints:
    - POST /api/teams/:id/invitations   # create invitation
    - GET  /api/teams/:id/invitations   # list pending
    - POST /api/invitations/:token/accept  # accept invite
    - DELETE /api/invitations/:id       # revoke
  auth: [team-admin for create/list/revoke, public+token for accept]
data:
  tables: [invitations]
  columns: [id, team_id, email, token, status, invited_by, expires_at, accepted_at]
  indexes: [token (unique), team_id+status, email+team_id (unique)]
  relations: [invitations.team_id → teams.id, invitations.invited_by → users.id]
tests:
  unit: [invitation model validation, token generation, expiry logic]
  integration: [create+accept flow, duplicate email guard, expired token rejection]
  e2e: [admin invites user → user receives link → user accepts → user appears in team]
deploy:
  env_vars: [INVITATION_EXPIRY_HOURS, SMTP_* for email sending]
  migrations: [001_create_invitations_table]
  services: [email worker queue]
observability:
  metrics: [invitations.created, invitations.accepted, invitations.expired]
  logs: [invitation_sent, invitation_accepted, invitation_expired]
  alerts: [invitation accept rate < 10% over 7 days]
```

---

## Module FR2: Type-Safe Boundary Synthesizer

**Purpose**: Generate shared TypeScript types that flow from database schema through
API responses into React component props. ZERO type drift between layers.

### The Type Flow Chain

```
Database Schema → Prisma/Drizzle Types → API Response Types → React Props
     ▲                                                            │
     └────────────── Single Source of Truth ───────────────────────┘
```

### Implementation Pattern

```typescript
// ═══════════════════════════════════════════════════════
// SHARED TYPES — packages/shared/src/types/invitation.ts
// Single source of truth for ALL layers
// ═══════════════════════════════════════════════════════

export const InvitationStatus = {
  PENDING: "pending",
  ACCEPTED: "accepted",
  EXPIRED: "expired",
  REVOKED: "revoked",
} as const;

export type InvitationStatus = (typeof InvitationStatus)[keyof typeof InvitationStatus];

// Base entity — mirrors DB columns exactly
export interface Invitation {
  id: string;
  teamId: string;
  email: string;
  token: string;
  status: InvitationStatus;
  invitedBy: string;
  expiresAt: Date;
  acceptedAt: Date | null;
  createdAt: Date;
}

// API request shapes — what the client sends
export interface CreateInvitationRequest {
  email: string;
  role?: "member" | "admin";
}

// API response shapes — what the server returns
export interface InvitationResponse {
  id: string;
  email: string;
  status: InvitationStatus;
  invitedBy: { id: string; name: string };
  expiresAt: string; // ISO string over the wire
  createdAt: string;
}

export interface InvitationListResponse {
  invitations: InvitationResponse[];
  total: number;
  hasMore: boolean;
}

// Zod validation schemas derived from the same types
import { z } from "zod";

export const CreateInvitationSchema = z.object({
  email: z.string().email("Invalid email address"),
  role: z.enum(["member", "admin"]).default("member"),
});

export const InvitationParamsSchema = z.object({
  teamId: z.string().uuid(),
});
```

### Cross-Boundary Guarantees

- **DB → API**: Prisma/Drizzle model maps 1:1 to base entity type
- **API → Client**: Response types are serialization-safe (Date → string)
- **Client → API**: Request types have Zod validators server-side
- **Props → Component**: React component props derive from response types
- **Test → All**: Test factories use the same shared types

---

## Module FR3: UI Reactor

**Purpose**: Generate React/Next.js components with Tailwind styling, accessibility,
responsive design, and proper state management — all derived from the feature spec.

### Component Generation Protocol

For each UI surface identified in FR1, generate:

```typescript
// ═══════════════════════════════════════════════
// COMPONENT — app/team/[teamId]/invitations/page.tsx
// ═══════════════════════════════════════════════

import { Suspense } from "react";
import { InvitationList } from "./components/InvitationList";
import { InviteForm } from "./components/InviteForm";
import { InvitationListSkeleton } from "./components/skeletons";

interface InvitationsPageProps {
  params: Promise<{ teamId: string }>;
}

export default async function InvitationsPage({ params }: InvitationsPageProps) {
  const { teamId } = await params;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Team Invitations
        </h1>
      </div>

      <InviteForm teamId={teamId} />

      <Suspense fallback={<InvitationListSkeleton />}>
        <InvitationList teamId={teamId} />
      </Suspense>
    </div>
  );
}
```

### State Management Strategy

| Complexity | Solution | When |
|---|---|---|
| Server data | React Server Components + `fetch` | Read-heavy, cacheable |
| Server mutations | Server Actions or `useMutation` | Form submissions |
| Client interactivity | `useState` + `useReducer` | Toggles, forms, modals |
| Shared client state | Zustand / Context | Theme, auth, sidebar |
| Real-time data | `useSWR` / React Query | Polling, optimistic updates |

### Accessibility Checklist (Auto-applied)

- [ ] All interactive elements have visible focus indicators
- [ ] Form inputs have associated `<label>` elements
- [ ] Error messages use `aria-live="polite"` for screen readers
- [ ] Color is never the sole indicator of state
- [ ] Keyboard navigation works for all interactions
- [ ] Loading states announced via `aria-busy`

---

## Module FR4: API Forge

**Purpose**: Generate RESTful (or GraphQL) endpoints with Zod validation, structured
error handling, middleware chains, rate limiting, and auto-generated OpenAPI docs.

### Endpoint Generation Pattern

```typescript
// ═══════════════════════════════════════════════
// API ROUTE — app/api/teams/[teamId]/invitations/route.ts
// ═══════════════════════════════════════════════

import { NextRequest, NextResponse } from "next/server";
import { withAuth } from "@/lib/middleware/auth";
import { withRateLimit } from "@/lib/middleware/rate-limit";
import { withValidation } from "@/lib/middleware/validation";
import { CreateInvitationSchema, InvitationParamsSchema } from "@shared/types";
import { invitationService } from "@/services/invitation";
import { logger } from "@/lib/observability/logger";
import { metrics } from "@/lib/observability/metrics";

// POST /api/teams/:teamId/invitations
export const POST = withAuth(
  withRateLimit({ window: "1m", max: 10 })(
    withValidation({ params: InvitationParamsSchema, body: CreateInvitationSchema })(
      async (req: NextRequest, { params, body, user }) => {
        const startTime = performance.now();

        try {
          const invitation = await invitationService.create({
            teamId: params.teamId,
            email: body.email,
            role: body.role,
            invitedBy: user.id,
          });

          metrics.increment("invitations.created", {
            team: params.teamId,
          });

          logger.info("invitation_created", {
            invitationId: invitation.id,
            teamId: params.teamId,
            invitedEmail: body.email,
          });

          return NextResponse.json(invitation, { status: 201 });
        } catch (error) {
          if (error.code === "DUPLICATE_INVITATION") {
            return NextResponse.json(
              { error: "User already invited", code: "DUPLICATE_INVITATION" },
              { status: 409 }
            );
          }
          throw error; // Global error handler catches this
        } finally {
          metrics.histogram("api.latency", performance.now() - startTime, {
            route: "POST /api/teams/:teamId/invitations",
          });
        }
      }
    )
  )
);

// GET /api/teams/:teamId/invitations
export const GET = withAuth(
  withValidation({ params: InvitationParamsSchema })(
    async (req: NextRequest, { params, user }) => {
      const url = new URL(req.url);
      const page = parseInt(url.searchParams.get("page") ?? "1");
      const limit = Math.min(parseInt(url.searchParams.get("limit") ?? "20"), 100);

      const result = await invitationService.listByTeam(params.teamId, {
        page,
        limit,
      });

      return NextResponse.json(result);
    }
  )
);
```

### Error Response Contract

All API errors follow a consistent structure:

```typescript
interface ApiError {
  error: string;        // Human-readable message
  code: string;         // Machine-readable error code
  details?: unknown;    // Validation errors, field-level info
  requestId: string;    // Correlation ID for tracing
}
```

### Middleware Chain Order

```
Request → Rate Limit → Auth → Validation → Handler → Error Handler → Response
                                                          │
                                                    Logging + Metrics
```

---

## Module FR5: Data Layer Architect

**Purpose**: Design schema, write migrations, optimize queries, and create seed data —
all derived from the access patterns the feature actually requires.

### Schema Design Protocol

```sql
-- ═══════════════════════════════════════════════
-- MIGRATION — migrations/001_create_invitations.sql
-- ═══════════════════════════════════════════════

CREATE TABLE invitations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id     UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email       VARCHAR(255) NOT NULL,
    token       VARCHAR(64) NOT NULL UNIQUE,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
    role        VARCHAR(20) NOT NULL DEFAULT 'member'
                CHECK (role IN ('member', 'admin')),
    invited_by  UUID NOT NULL REFERENCES users(id),
    expires_at  TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate active invitations
    UNIQUE (team_id, email) WHERE status = 'pending'
);

-- Indexes derived from query patterns
CREATE INDEX idx_invitations_team_status ON invitations(team_id, status);
CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_expires ON invitations(expires_at)
    WHERE status = 'pending';
```

### Index Strategy (Access-Pattern-Driven)

| Query Pattern | Index | Rationale |
|---|---|---|
| List invitations by team | `(team_id, status)` | Filtered list page |
| Accept by token | `(token) UNIQUE` | Single-row lookup |
| Expiry cron job | `(expires_at) WHERE pending` | Partial index, minimal size |
| Duplicate guard | `(team_id, email) WHERE pending` | Unique partial constraint |

### ORM Model (Prisma Example)

```prisma
model Invitation {
  id         String           @id @default(uuid())
  teamId     String           @map("team_id")
  email      String
  token      String           @unique
  status     InvitationStatus @default(PENDING)
  role       TeamRole         @default(MEMBER)
  invitedBy  String           @map("invited_by")
  expiresAt  DateTime         @map("expires_at")
  acceptedAt DateTime?        @map("accepted_at")
  createdAt  DateTime         @default(now()) @map("created_at")
  updatedAt  DateTime         @updatedAt @map("updated_at")

  team    Team @relation(fields: [teamId], references: [id], onDelete: Cascade)
  inviter User @relation(fields: [invitedBy], references: [id])

  @@unique([teamId, email], name: "unique_pending_invite")
  @@index([teamId, status])
  @@index([expiresAt])
  @@map("invitations")
}
```

---

## Module FR6: Test Matrix Generator

**Purpose**: Generate a complete test suite — unit tests per layer, integration tests
across layer boundaries, and E2E tests for the full user journey.

### Test Pyramid for Each Feature

```
         ╱╲
        ╱E2E╲         2-3 critical user journeys
       ╱──────╲
      ╱ Integr. ╲     5-10 cross-boundary tests
     ╱────────────╲
    ╱   Unit Tests  ╲  20-30 per-layer tests
   ╱────────────────────╲
```

### Generated Test Suite

```typescript
// ═══════════════════════════════════════════════
// UNIT — __tests__/services/invitation.test.ts
// ═══════════════════════════════════════════════

describe("InvitationService", () => {
  describe("create", () => {
    it("generates a unique token and sets expiry", async () => {
      const invitation = await service.create({
        teamId: "team-1",
        email: "new@example.com",
        invitedBy: "user-1",
      });

      expect(invitation.token).toHaveLength(64);
      expect(invitation.status).toBe("pending");
      expect(invitation.expiresAt.getTime()).toBeGreaterThan(Date.now());
    });

    it("rejects duplicate pending invitation for same email + team", async () => {
      await service.create({ teamId: "team-1", email: "dup@example.com", invitedBy: "user-1" });

      await expect(
        service.create({ teamId: "team-1", email: "dup@example.com", invitedBy: "user-1" })
      ).rejects.toThrow("DUPLICATE_INVITATION");
    });

    it("allows re-invitation after previous was revoked", async () => {
      const first = await service.create({ teamId: "t1", email: "a@b.com", invitedBy: "u1" });
      await service.revoke(first.id);

      const second = await service.create({ teamId: "t1", email: "a@b.com", invitedBy: "u1" });
      expect(second.id).not.toBe(first.id);
      expect(second.status).toBe("pending");
    });
  });

  describe("accept", () => {
    it("transitions status and records accepted_at", async () => {
      const inv = await service.create({ teamId: "t1", email: "a@b.com", invitedBy: "u1" });
      const accepted = await service.accept(inv.token, "new-user-id");

      expect(accepted.status).toBe("accepted");
      expect(accepted.acceptedAt).toBeInstanceOf(Date);
    });

    it("rejects expired tokens", async () => {
      const inv = await createExpiredInvitation();

      await expect(service.accept(inv.token, "user-2")).rejects.toThrow("INVITATION_EXPIRED");
    });
  });
});

// ═══════════════════════════════════════════════
// INTEGRATION — __tests__/api/invitations.integration.test.ts
// ═══════════════════════════════════════════════

describe("POST /api/teams/:teamId/invitations", () => {
  it("creates invitation and returns 201", async () => {
    const res = await request(app)
      .post("/api/teams/team-1/invitations")
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ email: "invite@example.com" });

    expect(res.status).toBe(201);
    expect(res.body.email).toBe("invite@example.com");
    expect(res.body.status).toBe("pending");

    // Verify DB state
    const dbRecord = await db.invitation.findUnique({ where: { id: res.body.id } });
    expect(dbRecord).toBeTruthy();
    expect(dbRecord!.token).toHaveLength(64);
  });

  it("returns 409 for duplicate invitation", async () => {
    await request(app)
      .post("/api/teams/team-1/invitations")
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ email: "dup@example.com" });

    const res = await request(app)
      .post("/api/teams/team-1/invitations")
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ email: "dup@example.com" });

    expect(res.status).toBe(409);
    expect(res.body.code).toBe("DUPLICATE_INVITATION");
  });

  it("returns 403 for non-admin users", async () => {
    const res = await request(app)
      .post("/api/teams/team-1/invitations")
      .set("Authorization", `Bearer ${memberToken}`)
      .send({ email: "someone@example.com" });

    expect(res.status).toBe(403);
  });
});

// ═══════════════════════════════════════════════
// E2E — e2e/invitation-flow.spec.ts
// ═══════════════════════════════════════════════

test("complete invitation flow: invite → accept → team membership", async ({ page }) => {
  await page.goto("/team/team-1/invitations");

  // Admin sends invitation
  await page.getByLabel("Email address").fill("newuser@example.com");
  await page.getByRole("button", { name: "Send Invitation" }).click();
  await expect(page.getByText("Invitation sent")).toBeVisible();

  // New user accepts via link
  const token = await getLatestInvitationToken("newuser@example.com");
  await page.goto(`/invite/${token}`);
  await page.getByRole("button", { name: "Accept Invitation" }).click();

  // Verify team membership
  await page.goto("/team/team-1/members");
  await expect(page.getByText("newuser@example.com")).toBeVisible();
});
```

---

## Module FR7: Deployment Capsule

**Purpose**: Generate the complete deployment story — Dockerfile, docker-compose,
CI/CD pipeline, environment configuration — for the new feature.

### Dockerfile (Multi-stage)

```dockerfile
# ═══════════════════════════════════════════════
# Dockerfile — Production-optimized multi-stage build
# ═══════════════════════════════════════════════

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

USER appuser
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

### Docker Compose (Development)

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: builder
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/app
      REDIS_URL: redis://redis:6379
      INVITATION_EXPIRY_HOURS: "72"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
      - /app/node_modules

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Build, Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - run: npm ci
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
      - run: npm run test:unit
      - run: npm run test:integration
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Module FR8: Observability Injection

**Purpose**: Wire logging, metrics, error tracking, and health checks into every
layer from day one — not as an afterthought.

### Structured Logging

```typescript
// ═══════════════════════════════════════════════
// lib/observability/logger.ts
// ═══════════════════════════════════════════════

import pino from "pino";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  serializers: {
    err: pino.stdSerializers.err,
    req: (req) => ({
      method: req.method,
      url: req.url,
      userAgent: req.headers["user-agent"],
    }),
  },
});

// Contextual child loggers per request
export function createRequestLogger(requestId: string) {
  return logger.child({ requestId });
}
```

### Metrics Collection

```typescript
// ═══════════════════════════════════════════════
// lib/observability/metrics.ts
// ═══════════════════════════════════════════════

interface MetricsClient {
  increment(name: string, tags?: Record<string, string>): void;
  histogram(name: string, value: number, tags?: Record<string, string>): void;
  gauge(name: string, value: number, tags?: Record<string, string>): void;
}

class AppMetrics implements MetricsClient {
  increment(name: string, tags?: Record<string, string>) {
    // Emit to StatsD / Prometheus / CloudWatch
    console.log(`METRIC counter ${name}`, tags);
  }

  histogram(name: string, value: number, tags?: Record<string, string>) {
    console.log(`METRIC histogram ${name}=${value}ms`, tags);
  }

  gauge(name: string, value: number, tags?: Record<string, string>) {
    console.log(`METRIC gauge ${name}=${value}`, tags);
  }
}

export const metrics = new AppMetrics();
```

### Health Check Endpoint

```typescript
// app/api/health/route.ts

export async function GET() {
  const checks = await Promise.allSettled([
    checkDatabase(),
    checkRedis(),
    checkExternalServices(),
  ]);

  const health = {
    status: checks.every((c) => c.status === "fulfilled") ? "healthy" : "degraded",
    timestamp: new Date().toISOString(),
    checks: {
      database: checks[0].status === "fulfilled" ? "up" : "down",
      redis: checks[1].status === "fulfilled" ? "up" : "down",
      external: checks[2].status === "fulfilled" ? "up" : "down",
    },
    uptime: process.uptime(),
  };

  return Response.json(health, {
    status: health.status === "healthy" ? 200 : 503,
  });
}
```

### Observability per Layer

| Layer | Logging | Metrics | Tracing |
|---|---|---|---|
| UI | Client error boundary reports | Core Web Vitals, user interactions | Browser performance API |
| API | Request/response, errors, auth events | Latency histograms, error rates, throughput | Request ID propagation |
| Database | Slow queries, connection pool stats | Query duration, pool utilization | Query-level spans |
| Background Jobs | Job start/complete/fail, retry attempts | Queue depth, processing time | Job correlation IDs |
| Infrastructure | Container health, resource usage | CPU, memory, disk, network | Distributed trace context |

---

## The Reactor Chain

When a feature request enters the reactor, modules execute in this sequence:

```
STEP 1: FR1 — Decompose feature into all-layer spec
         │
         ▼
STEP 2: FR2 — Generate shared types (DB → API → UI boundary contracts)
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
STEP 3: FR5 ────► FR4 ────► FR3     (Data → API → UI, parallel but ordered)
  Schema + Migration  Endpoints    Components
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
STEP 4: FR6 — Generate test matrix spanning all boundaries
                        │
                        ▼
STEP 5: FR7 — Emit deployment capsule (Docker + CI/CD + env config)
                        │
                        ▼
STEP 6: FR8 — Inject observability into every layer retroactively
                        │
                        ▼
              COMPLETE FEATURE — Ready for review
```

**Key insight**: Steps 3a/3b/3c (Data, API, UI) can proceed in parallel because
FR2's shared types ensure they will integrate cleanly. The types ARE the contract.

---

## Cross-Layer Intelligence

This is where the FORGE-class fusion creates genuinely emergent capability.
Individual skills cannot see across layer boundaries. The reactor can.

### Intelligence Propagation Rules

| When this happens in Layer A... | The reactor automatically propagates to Layer B... |
|---|---|
| M:N relationship added to schema | Join table created, API returns nested arrays, UI gets list component with pagination |
| Field marked `NOT NULL` in DB | Zod schema makes field required, form adds required indicator, tests cover missing-field case |
| Endpoint needs auth | Middleware added, UI adds auth check before rendering, tests include 401/403 cases |
| Component needs real-time data | API gets WebSocket/SSE endpoint, DB gets change notification trigger, tests cover reconnection |
| New env variable added | Dockerfile gets `ENV`, compose gets variable, CI/CD gets secret, health check validates presence |
| Rate limit set on endpoint | UI gets retry-with-backoff logic, tests cover 429 response, monitoring gets rate-limit-hit metric |
| Soft delete chosen over hard delete | DB gets `deleted_at` column, API filters deleted records, UI hides without removing, migration handles existing data |

### Example: The M:N Cascade

When the feature spec implies a many-to-many relationship (e.g., "users can belong to multiple teams"):

```
DB Layer:  Creates join table `team_members(user_id, team_id, role, joined_at)`
           with composite primary key and indexes on both foreign keys.

API Layer: GET /teams/:id/members returns paginated list with cursor.
           POST /teams/:id/members adds with role.
           Includes count in team list response.

UI Layer:  MemberList component with virtualized scrolling for large teams.
           AddMemberDialog with role selector.
           Member count badge on team cards.

Test Layer: Unit tests for join table constraints.
            Integration tests for bidirectional queries (user's teams, team's users).
            E2E test for add-member → appears-in-list → remove-member flow.

Deploy:    Migration ordered AFTER both users and teams tables exist.
           Seed data creates realistic team memberships.

Monitor:   Query performance metric on the join (most expensive query pattern).
           Alert if avg join query exceeds 100ms.
```

**No single skill produces this cascade. The reactor does.**

---

## Decision Tree: Feature Complexity Router

```
Feature Request Received
│
├── Is it a CRUD resource?
│   ├── YES → Full reactor chain (FR1-FR8), standard templates
│   └── NO ↓
│
├── Does it involve real-time data?
│   ├── YES → Add WebSocket/SSE to FR4, subscription hooks to FR3
│   └── NO ↓
│
├── Does it involve file uploads?
│   ├── YES → Add multipart handling to FR4, S3/blob storage to FR5,
│   │         progress UI to FR3, large-file tests to FR6
│   └── NO ↓
│
├── Does it involve background processing?
│   ├── YES → Add job queue to FR4, worker to FR7 (Docker service),
│   │         job monitoring to FR8, retry tests to FR6
│   └── NO ↓
│
├── Does it involve third-party integration?
│   ├── YES → Add adapter pattern to FR4, mock service to FR6,
│   │         circuit breaker to FR8, API key to FR7
│   └── NO ↓
│
├── Does it involve search/filtering?
│   ├── YES → Add search indexes to FR5, debounced input to FR3,
│   │         query parameter handling to FR4, relevance tests to FR6
│   └── NO ↓
│
└── Simple UI-only change?
    └── FR3 only (with FR6 for component tests)
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│           ⚛️  FORGE-FULLSTACK-REACTOR                │
│           Quick Reference Card                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  TRIGGER: "Build [feature] with full-stack"          │
│           "Implement [feature] end-to-end"           │
│           "Create complete [feature]"                │
│                                                      │
│  MODULES:                                            │
│  FR1  Feature Decomposition    → All-layer spec      │
│  FR2  Type-Safe Boundaries     → Shared contracts    │
│  FR3  UI Reactor               → React + Tailwind    │
│  FR4  API Forge                → Endpoints + Auth    │
│  FR5  Data Layer Architect     → Schema + Migrations │
│  FR6  Test Matrix Generator    → Unit/Integ/E2E      │
│  FR7  Deployment Capsule       → Docker + CI/CD      │
│  FR8  Observability Injection  → Logs + Metrics      │
│                                                      │
│  CHAIN: FR1 → FR2 → [FR3|FR4|FR5] → FR6 → FR7 → FR8│
│                                                      │
│  KEY PRINCIPLE:                                      │
│  Every decision propagates across ALL layers.        │
│  Types are the contract. Tests verify the contract.  │
│  Deployment ships the contract. Monitoring guards it.│
│                                                      │
│  FUSED SKILLS: 9 | TIER: FORGE | CLASS: Ω-Δ99       │
│  EMERGENT: End-to-end product synthesis              │
└─────────────────────────────────────────────────────┘
```

---

*Forged by andrew-pigors + copilot-omega-delta-99 — 2026-07-17*
*FORGE-class cross-domain innovation: 9 skills → 1 reactor → ∞ features*
