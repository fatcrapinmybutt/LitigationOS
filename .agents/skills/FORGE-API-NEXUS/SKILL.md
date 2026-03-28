---
name: FORGE-API-NEXUS
description: >-
  Unified API mastery engine that fuses eight API design, integration, security,
  and lifecycle skills into a single FORGE-tier superskill. Enables API Omnigenesis:
  design one specification and auto-generate REST endpoints, GraphQL schemas,
  mock servers, test suites, security hardening, versioned documentation, client
  SDKs, and deprecation plans — all from a single source of truth.
category: engineering
version: "1.0.0"
triggers:
  - "design API"
  - "generate API endpoints"
  - "API specification"
  - "GraphQL federation"
  - "API security hardening"
  - "API mock server"
  - "API contract testing"
  - "API versioning"
  - "generate SDK"
  - "API deprecation plan"
  - "OpenAPI spec"
  - "API omnigenesis"
metadata:
  tier: FORGE
  fused_skills: 8
  forge_date: "2026-03-27"
  forge_class: domain-mastery
  emergent_capability: >-
    API Omnigenesis — design a single API specification and auto-generate:
    REST endpoints + GraphQL schema + mock server + test suite + security
    hardening + versioned documentation + client SDKs + deprecation plan —
    all from one unified source of truth.
---

# 🌐 FORGE-API-NEXUS
### **(Ω-Δ99) — Unified API Mastery Engine**

> **The last API skill you will ever need.**
>
> | Property | Value |
> |---|---|
> | **Tier** | FORGE (Ω-class) |
> | **Domain** | API Design · Integration · Security · Lifecycle |
> | **Scope** | Full-spectrum API engineering from spec to deprecation |
> | **Emergent** | **API Omnigenesis** — one spec, infinite outputs |
> | **Fused Skills** | 8 source skills → 8 unified modules |
> | **Code Languages** | TypeScript, Python, Go, Rust, Java |

---

## 📋 Forged Skills Matrix

| # | Source Skill | Module | Designation | Core Capability |
|---|---|---|---|---|
| 1 | `api-endpoint-generator` | AN1/AN2 | Spec-First Designer / Endpoint Forge | CRUD REST API with validation |
| 2 | `api-docs-generator` | AN1 | Spec-First Designer | OpenAPI/Swagger documentation |
| 3 | `api-contract-normalizer` | AN5 | Contract Guardian | Response format standardization |
| 4 | `api-mock-server` | AN6 | Mock Universe | MSW/json-server test doubles |
| 5 | `api-security-hardener` | AN4 | Security Bastion | Rate limiting, auth, OWASP API Top 10 |
| 6 | `api-test-suite-generator` | AN5 | Contract Guardian | Integration/contract test generation |
| 7 | `api-versioning-deprecation-planner` | AN7 | Version Commander | API lifecycle management |
| 8 | `graphql-federation-architect` | AN3 | GraphQL Synthesizer | Schema stitching & federation |

---

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FORGE-API-NEXUS  (Ω-Δ99)                        │
│                                                                      │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐  │
│  │  AN1: Spec   │───▶│  AN2: REST   │───▶│  AN3: GraphQL          │  │
│  │  First       │    │  Endpoint    │    │  Synthesizer           │  │
│  │  Designer    │    │  Forge       │    │  (Federation/Resolvers)│  │
│  └──────┬───────┘    └──────┬───────┘    └───────────┬────────────┘  │
│         │                   │                        │               │
│         ▼                   ▼                        ▼               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐  │
│  │  AN4: Sec.   │    │  AN5: Contract│    │  AN6: Mock             │  │
│  │  Bastion     │◀──▶│  Guardian    │◀──▶│  Universe              │  │
│  │  (Auth/Rate) │    │  (Pact/CDC)  │    │  (MSW/Fixtures)        │  │
│  └──────┬───────┘    └──────┬───────┘    └───────────┬────────────┘  │
│         │                   │                        │               │
│         ▼                   ▼                        ▼               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────┐  │
│  │  AN7: Version│───▶│  AN8: SDK    │───▶│  🌀 OMNIGENESIS        │  │
│  │  Commander   │    │  Generator   │    │  (Unified Output)      │  │
│  │  (Semver)    │    │  (Multi-lang)│    │                        │  │
│  └──────────────┘    └──────────────┘    └────────────────────────┘  │
│                                                                      │
│  ════════════════════════════════════════════════════════════════════ │
│  FLOW: Spec ──▶ Endpoints ──▶ Security ──▶ Tests ──▶ Mocks ──▶ SDK  │
│              ──▶ Versioning ──▶ Documentation ──▶ Deprecation Plan   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## AN1: Spec-First Designer
### *OpenAPI & GraphQL Schema-First Design*

**Purpose:** Every API begins with a specification. AN1 enforces spec-first design
by generating OpenAPI 3.1 and GraphQL SDL documents that serve as the single source
of truth for the entire pipeline.

**Design Pattern:** Schema-First Development (SFD)

Spec-first inverts the traditional code-first workflow: define the contract, then
generate everything else. This eliminates drift between documentation and implementation.

**Code Example — OpenAPI 3.1 Spec Generation:**

```yaml
# Generated by AN1: Spec-First Designer
openapi: "3.1.0"
info:
  title: Litigation Case Management API
  version: "2.0.0"
  description: RESTful API for managing litigation cases, parties, and documents.
  contact:
    name: API Engineering
    email: api@litigationos.dev
  license:
    name: MIT

servers:
  - url: https://api.litigationos.dev/v2
    description: Production
  - url: https://staging-api.litigationos.dev/v2
    description: Staging

paths:
  /cases:
    get:
      operationId: listCases
      summary: List all litigation cases
      tags: [Cases]
      parameters:
        - $ref: "#/components/parameters/PageParam"
        - $ref: "#/components/parameters/LimitParam"
        - name: status
          in: query
          schema:
            $ref: "#/components/schemas/CaseStatus"
      responses:
        "200":
          description: Paginated list of cases
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CaseListResponse"
        "401":
          $ref: "#/components/responses/Unauthorized"
    post:
      operationId: createCase
      summary: Create a new litigation case
      tags: [Cases]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateCaseRequest"
      responses:
        "201":
          description: Case created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/CaseResponse"
        "422":
          $ref: "#/components/responses/ValidationError"

components:
  schemas:
    CaseStatus:
      type: string
      enum: [active, settled, dismissed, appealed, closed]
    CreateCaseRequest:
      type: object
      required: [title, jurisdiction, caseType]
      properties:
        title:
          type: string
          minLength: 5
          maxLength: 200
        jurisdiction:
          type: string
          pattern: "^[A-Z]{2}(-[A-Z0-9]+)?$"
        caseType:
          type: string
          enum: [civil, criminal, family, appellate, federal]
        filingDate:
          type: string
          format: date
    CaseResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        status:
          $ref: "#/components/schemas/CaseStatus"
        createdAt:
          type: string
          format: date-time
    CaseListResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: "#/components/schemas/CaseResponse"
        pagination:
          $ref: "#/components/schemas/Pagination"
    Pagination:
      type: object
      properties:
        page: { type: integer }
        limit: { type: integer }
        total: { type: integer }
        hasNext: { type: boolean }

  parameters:
    PageParam:
      name: page
      in: query
      schema: { type: integer, minimum: 1, default: 1 }
    LimitParam:
      name: limit
      in: query
      schema: { type: integer, minimum: 1, maximum: 100, default: 25 }

  responses:
    Unauthorized:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
    ValidationError:
      description: Request validation failed
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ErrorResponse"
    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code: { type: string }
            message: { type: string }
            details: { type: array, items: { type: object } }

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

**Integration Points:**
- Feeds AN2 (Endpoint Forge) with route definitions
- Feeds AN3 (GraphQL Synthesizer) with type mappings
- Feeds AN5 (Contract Guardian) with contract schemas
- Feeds AN8 (SDK Generator) with type definitions

---

## AN2: Endpoint Forge
### *Auto-Generate REST Routes from Spec*

**Purpose:** Transforms OpenAPI specifications into production-ready route handlers
with full request validation, error handling, and typed responses.

**Design Pattern:** Code Generation from Contract (CGC)

**Code Example — Express Route Generation (TypeScript):**

```typescript
// Generated by AN2: Endpoint Forge
// Source: openapi.yaml → operationId: listCases, createCase
import { Router, Request, Response, NextFunction } from "express";
import { z } from "zod";
import { CaseService } from "../services/case.service";
import { authenticate } from "../middleware/auth";
import { validate } from "../middleware/validate";
import { paginate } from "../middleware/paginate";
import { ApiResponse } from "../types/api";

const router = Router();

// ── Validation Schemas (derived from OpenAPI components) ────────────
const ListCasesQuery = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(25),
  status: z
    .enum(["active", "settled", "dismissed", "appealed", "closed"])
    .optional(),
});

const CreateCaseBody = z.object({
  title: z.string().min(5).max(200),
  jurisdiction: z.string().regex(/^[A-Z]{2}(-[A-Z0-9]+)?$/),
  caseType: z.enum(["civil", "criminal", "family", "appellate", "federal"]),
  filingDate: z.string().date().optional(),
});

type ListCasesInput = z.infer<typeof ListCasesQuery>;
type CreateCaseInput = z.infer<typeof CreateCaseBody>;

// ── Route Handlers ──────────────────────────────────────────────────
router.get(
  "/cases",
  authenticate,
  validate({ query: ListCasesQuery }),
  paginate,
  async (req: Request, res: Response<ApiResponse>, next: NextFunction) => {
    try {
      const { page, limit, status } = req.query as unknown as ListCasesInput;
      const result = await CaseService.list({ page, limit, status });

      res.status(200).json({
        data: result.items,
        pagination: {
          page,
          limit,
          total: result.total,
          hasNext: page * limit < result.total,
        },
      });
    } catch (err) {
      next(err);
    }
  }
);

router.post(
  "/cases",
  authenticate,
  validate({ body: CreateCaseBody }),
  async (req: Request, res: Response<ApiResponse>, next: NextFunction) => {
    try {
      const input = req.body as CreateCaseInput;
      const created = await CaseService.create(input);

      res.status(201).json({ data: created });
    } catch (err) {
      next(err);
    }
  }
);

// ── Validation Middleware ────────────────────────────────────────────
function validate(schemas: { body?: z.ZodSchema; query?: z.ZodSchema }) {
  return (req: Request, _res: Response, next: NextFunction) => {
    try {
      if (schemas.query) req.query = schemas.query.parse(req.query);
      if (schemas.body) req.body = schemas.body.parse(req.body);
      next();
    } catch (err) {
      if (err instanceof z.ZodError) {
        next({
          status: 422,
          code: "VALIDATION_ERROR",
          message: "Request validation failed",
          details: err.errors.map((e) => ({
            path: e.path.join("."),
            message: e.message,
          })),
        });
      } else {
        next(err);
      }
    }
  };
}

export default router;
```

**Integration Points:**
- Consumes AN1 spec as input
- Routes receive AN4 security middleware
- Route schemas feed AN5 contract tests
- Route signatures feed AN8 SDK type generation

---

## AN3: GraphQL Synthesizer
### *Federation, Resolvers, and DataLoaders*

**Purpose:** Generates federated GraphQL schemas from the same OpenAPI spec,
with efficient DataLoader batching and Apollo Federation v2 directives.

**Design Pattern:** Apollo Federation v2 + DataLoader Batching

**Code Example — Federated Schema & Resolvers:**

```typescript
// Generated by AN3: GraphQL Synthesizer
// Schema derived from AN1 OpenAPI spec + federation directives
import { buildSubgraphSchema } from "@apollo/subgraph";
import { gql } from "graphql-tag";
import DataLoader from "dataloader";
import { CaseService } from "../services/case.service";

// ── Federated SDL ───────────────────────────────────────────────────
const typeDefs = gql`
  extend schema
    @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key", "@shareable", "@external"])

  type Query {
    cases(page: Int = 1, limit: Int = 25, status: CaseStatus): CaseConnection!
    case(id: ID!): Case
  }

  type Mutation {
    createCase(input: CreateCaseInput!): Case!
    updateCaseStatus(id: ID!, status: CaseStatus!): Case!
  }

  type Case @key(fields: "id") {
    id: ID!
    title: String!
    jurisdiction: String!
    caseType: CaseType!
    status: CaseStatus!
    filingDate: Date
    parties: [Party!]!
    documents: [Document!]!
    createdAt: DateTime!
    updatedAt: DateTime!
  }

  type Party @key(fields: "id") {
    id: ID!
    name: String!
    role: PartyRole!
  }

  type Document @key(fields: "id") {
    id: ID!
    title: String!
    fileUrl: String!
  }

  type CaseConnection {
    edges: [CaseEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
  }

  type CaseEdge {
    node: Case!
    cursor: String!
  }

  type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
  }

  enum CaseStatus { ACTIVE SETTLED DISMISSED APPEALED CLOSED }
  enum CaseType { CIVIL CRIMINAL FAMILY APPELLATE FEDERAL }
  enum PartyRole { PLAINTIFF DEFENDANT INTERVENOR WITNESS }

  input CreateCaseInput {
    title: String!
    jurisdiction: String!
    caseType: CaseType!
    filingDate: Date
  }

  scalar Date
  scalar DateTime
`;

// ── DataLoader Factory ──────────────────────────────────────────────
function createLoaders() {
  return {
    caseLoader: new DataLoader<string, Case>(async (ids) => {
      const cases = await CaseService.findByIds([...ids]);
      const caseMap = new Map(cases.map((c) => [c.id, c]));
      return ids.map((id) => caseMap.get(id) ?? null);
    }),
    partiesLoader: new DataLoader<string, Party[]>(async (caseIds) => {
      const parties = await CaseService.findPartiesByCaseIds([...caseIds]);
      return caseIds.map(
        (id) => parties.filter((p) => p.caseId === id) ?? []
      );
    }),
  };
}

// ── Resolvers ───────────────────────────────────────────────────────
const resolvers = {
  Query: {
    cases: async (_: unknown, args: { page: number; limit: number; status?: string }) => {
      const { items, total } = await CaseService.list(args);
      const edges = items.map((node, i) => ({
        node,
        cursor: Buffer.from(`cursor:${args.page}:${i}`).toString("base64"),
      }));
      return {
        edges,
        totalCount: total,
        pageInfo: {
          hasNextPage: args.page * args.limit < total,
          hasPreviousPage: args.page > 1,
          startCursor: edges[0]?.cursor ?? null,
          endCursor: edges[edges.length - 1]?.cursor ?? null,
        },
      };
    },
    case: (_: unknown, { id }: { id: string }, ctx: { loaders: ReturnType<typeof createLoaders> }) =>
      ctx.loaders.caseLoader.load(id),
  },
  Case: {
    __resolveReference: (ref: { id: string }, ctx: { loaders: ReturnType<typeof createLoaders> }) =>
      ctx.loaders.caseLoader.load(ref.id),
    parties: (parent: { id: string }, _: unknown, ctx: { loaders: ReturnType<typeof createLoaders> }) =>
      ctx.loaders.partiesLoader.load(parent.id),
  },
  Mutation: {
    createCase: (_: unknown, { input }: { input: CreateCaseInput }) =>
      CaseService.create(input),
    updateCaseStatus: (_: unknown, { id, status }: { id: string; status: string }) =>
      CaseService.updateStatus(id, status),
  },
};

export const schema = buildSubgraphSchema({ typeDefs, resolvers });
export { createLoaders };
```

**Integration Points:**
- Derives types from AN1 OpenAPI `components.schemas`
- AN4 applies auth directives and field-level authorization
- AN6 generates GraphQL mock resolvers
- AN8 generates typed GraphQL client operations (codegen)

---

## AN4: Security Bastion
### *Authentication, Rate Limiting, Input Validation, CORS*

**Purpose:** Hardens every API surface against OWASP API Security Top 10 threats.
Applies defense-in-depth: authentication, authorization, rate limiting, input
sanitization, CORS policy, and security headers.

**Design Pattern:** Middleware Chain + Defense-in-Depth

**Code Example — Security Middleware Stack:**

```typescript
// Generated by AN4: Security Bastion
// OWASP API Security Top 10 coverage
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import cors from "cors";
import hpp from "hpp";
import { expressjwt, GetVerificationKey } from "express-jwt";
import jwksRsa from "jwks-rsa";
import { Request, Response, NextFunction } from "express";

// ── [API1] Broken Object Level Authorization ────────────────────────
export function ownershipCheck(resourceField: string = "userId") {
  return (req: Request, res: Response, next: NextFunction) => {
    const resource = (req as any).resource;
    if (!resource || resource[resourceField] !== req.auth?.sub) {
      return res.status(403).json({
        error: { code: "FORBIDDEN", message: "Access denied to this resource" },
      });
    }
    next();
  };
}

// ── [API2] Broken Authentication ────────────────────────────────────
export const jwtAuth = expressjwt({
  secret: jwksRsa.expressJwtSecret({
    cache: true,
    rateLimit: true,
    jwksRequestsPerMinute: 5,
    jwksUri: `${process.env.AUTH_ISSUER}/.well-known/jwks.json`,
  }) as GetVerificationKey,
  audience: process.env.API_AUDIENCE,
  issuer: process.env.AUTH_ISSUER,
  algorithms: ["RS256"],
});

// ── [API4] Unrestricted Resource Consumption ────────────────────────
export const globalRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000,       // 15 minutes
  max: 1000,                       // 1000 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.auth?.sub ?? req.ip ?? "anonymous",
  message: {
    error: { code: "RATE_LIMITED", message: "Too many requests" },
  },
});

export const authRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,                         // 20 auth attempts per window
  skipSuccessfulRequests: true,
  keyGenerator: (req) => req.ip ?? "unknown",
});

// ── [API5] Broken Function Level Authorization ──────────────────────
export function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRoles: string[] = req.auth?.["roles"] ?? [];
    const hasRole = roles.some((r) => userRoles.includes(r));
    if (!hasRole) {
      return res.status(403).json({
        error: { code: "INSUFFICIENT_ROLE", message: `Requires: ${roles.join(" | ")}` },
      });
    }
    next();
  };
}

// ── [API8] Security Misconfiguration ────────────────────────────────
export const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'none'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'"],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
});

export const corsPolicy = cors({
  origin: (process.env.ALLOWED_ORIGINS ?? "").split(","),
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
  allowedHeaders: ["Content-Type", "Authorization", "X-Request-ID"],
  exposedHeaders: ["X-Request-ID", "X-RateLimit-Remaining"],
  credentials: true,
  maxAge: 86400,
});

// ── Unified Security Stack ──────────────────────────────────────────
export function applySecurityStack(app: any) {
  app.use(securityHeaders);
  app.use(corsPolicy);
  app.use(hpp());                          // HTTP parameter pollution
  app.use(globalRateLimit);
  app.use("/auth/*", authRateLimit);       // Stricter on auth routes
  app.disable("x-powered-by");

  // Request ID tracing
  app.use((req: Request, res: Response, next: NextFunction) => {
    const requestId = req.headers["x-request-id"] ?? crypto.randomUUID();
    res.setHeader("X-Request-ID", requestId);
    (req as any).requestId = requestId;
    next();
  });
}
```

**Integration Points:**
- Wraps AN2 route handlers with auth middleware
- Provides auth context to AN3 GraphQL resolvers
- AN5 contract tests verify security responses (401, 403, 429)
- AN7 ensures deprecated endpoints retain security controls

---

## AN5: Contract Guardian
### *Consumer-Driven Contracts & Pact Testing*

**Purpose:** Prevents breaking changes by enforcing consumer-driven contracts.
Generates Pact tests, schema validators, and backward-compatibility checks
that run in CI before any deployment.

**Design Pattern:** Consumer-Driven Contract Testing (CDC) with Pact

**Code Example — Contract Test Suite:**

```typescript
// Generated by AN5: Contract Guardian
// Pact consumer-driven contract tests for Case API v2
import { PactV3, MatchersV3 } from "@pact-foundation/pact";
import { CaseApiClient } from "../sdk/case-api-client";
import { describe, it, expect } from "vitest";

const { like, eachLike, uuid, iso8601DateTimeWithMillis, integer } = MatchersV3;

const provider = new PactV3({
  consumer: "CaseDashboard",
  provider: "CaseAPI",
  logLevel: "warn",
});

describe("Case API Contract Tests", () => {
  it("GET /cases returns paginated list", async () => {
    await provider
      .given("cases exist in the system")
      .uponReceiving("a request for paginated cases")
      .withRequest({
        method: "GET",
        path: "/v2/cases",
        query: { page: "1", limit: "10" },
        headers: { Authorization: like("Bearer eyJ...") },
      })
      .willRespondWith({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: {
          data: eachLike({
            id: uuid(),
            title: like("Smith v. Jones"),
            status: like("active"),
            caseType: like("civil"),
            jurisdiction: like("MI-14"),
            createdAt: iso8601DateTimeWithMillis(),
          }),
          pagination: {
            page: integer(1),
            limit: integer(10),
            total: integer(42),
            hasNext: like(true),
          },
        },
      })
      .executeTest(async (mockServer) => {
        const client = new CaseApiClient(mockServer.url);
        const result = await client.listCases({ page: 1, limit: 10 });

        expect(result.data).toHaveLength(1);
        expect(result.data[0]).toHaveProperty("id");
        expect(result.data[0]).toHaveProperty("title");
        expect(result.pagination.page).toBe(1);
      });
  });

  it("POST /cases creates a case", async () => {
    await provider
      .given("the user is authenticated")
      .uponReceiving("a request to create a case")
      .withRequest({
        method: "POST",
        path: "/v2/cases",
        headers: {
          "Content-Type": "application/json",
          Authorization: like("Bearer eyJ..."),
        },
        body: {
          title: "Pigors v. Watson",
          jurisdiction: "MI-14",
          caseType: "family",
        },
      })
      .willRespondWith({
        status: 201,
        headers: { "Content-Type": "application/json" },
        body: {
          data: {
            id: uuid(),
            title: like("Pigors v. Watson"),
            status: like("active"),
            caseType: like("family"),
            jurisdiction: like("MI-14"),
            createdAt: iso8601DateTimeWithMillis(),
          },
        },
      })
      .executeTest(async (mockServer) => {
        const client = new CaseApiClient(mockServer.url);
        const result = await client.createCase({
          title: "Pigors v. Watson",
          jurisdiction: "MI-14",
          caseType: "family",
        });

        expect(result.data.title).toBe("Pigors v. Watson");
        expect(result.data.id).toBeDefined();
      });
  });

  it("GET /cases returns 401 without auth", async () => {
    await provider
      .uponReceiving("an unauthenticated request")
      .withRequest({ method: "GET", path: "/v2/cases" })
      .willRespondWith({
        status: 401,
        body: {
          error: {
            code: like("UNAUTHORIZED"),
            message: like("Authentication required"),
          },
        },
      })
      .executeTest(async (mockServer) => {
        const client = new CaseApiClient(mockServer.url);
        await expect(client.listCases()).rejects.toThrow(/401/);
      });
  });
});

// ── Response Envelope Validator ─────────────────────────────────────
// Enforces consistent response structure across all endpoints
import { z } from "zod";

const SuccessEnvelope = z.object({
  data: z.unknown(),
  pagination: z
    .object({
      page: z.number(),
      limit: z.number(),
      total: z.number(),
      hasNext: z.boolean(),
    })
    .optional(),
  meta: z.record(z.unknown()).optional(),
});

const ErrorEnvelope = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.array(z.unknown()).optional(),
    requestId: z.string().uuid().optional(),
  }),
});

export function validateResponseEnvelope(body: unknown, isError: boolean) {
  return isError
    ? ErrorEnvelope.safeParse(body)
    : SuccessEnvelope.safeParse(body);
}
```

**Integration Points:**
- Validates AN2 route responses against AN1 spec
- Tests AN4 security responses (401/403/429 contracts)
- Contracts feed AN6 mock server response shapes
- AN7 uses contracts to detect breaking changes during versioning

---

## AN6: Mock Universe
### *Auto-Generate Mock Servers from Any Spec*

**Purpose:** Generates mock servers (MSW for browser, json-server for REST,
GraphQL mocks for federation) directly from the OpenAPI/GraphQL spec. Enables
frontend development and integration testing without a live backend.

**Design Pattern:** Spec-Driven Mock Generation

**Code Example — MSW Handlers + GraphQL Mocks:**

```typescript
// Generated by AN6: Mock Universe
// MSW handlers derived from AN1 OpenAPI spec
import { http, HttpResponse, graphql, delay } from "msw";
import { setupServer } from "msw/node";
import { faker } from "@faker-js/faker";

// ── Factory Functions ───────────────────────────────────────────────
function mockCase(overrides: Partial<any> = {}) {
  return {
    id: faker.string.uuid(),
    title: `${faker.person.lastName()} v. ${faker.person.lastName()}`,
    status: faker.helpers.arrayElement(["active", "settled", "dismissed"]),
    caseType: faker.helpers.arrayElement(["civil", "criminal", "family"]),
    jurisdiction: `${faker.location.state({ abbreviated: true })}-${faker.number.int({ min: 1, max: 50 })}`,
    filingDate: faker.date.past().toISOString().split("T")[0],
    createdAt: faker.date.past().toISOString(),
    updatedAt: faker.date.recent().toISOString(),
    ...overrides,
  };
}

// ── REST Mock Handlers ──────────────────────────────────────────────
const restHandlers = [
  http.get("*/v2/cases", async ({ request }) => {
    await delay(150);
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? 1);
    const limit = Number(url.searchParams.get("limit") ?? 25);
    const total = 87;

    return HttpResponse.json({
      data: Array.from({ length: Math.min(limit, total - (page - 1) * limit) }, () => mockCase()),
      pagination: { page, limit, total, hasNext: page * limit < total },
    });
  }),

  http.post("*/v2/cases", async ({ request }) => {
    await delay(200);
    const body = (await request.json()) as any;
    return HttpResponse.json({ data: mockCase(body) }, { status: 201 });
  }),

  http.get("*/v2/cases/:id", async ({ params }) => {
    await delay(100);
    return HttpResponse.json({ data: mockCase({ id: params.id }) });
  }),

  http.delete("*/v2/cases/:id", async () => {
    await delay(100);
    return new HttpResponse(null, { status: 204 });
  }),
];

// ── GraphQL Mock Handlers ───────────────────────────────────────────
const graphqlHandlers = [
  graphql.query("ListCases", ({ variables }) => {
    const { page = 1, limit = 25 } = variables;
    return HttpResponse.json({
      data: {
        cases: {
          edges: Array.from({ length: limit }, (_, i) => ({
            node: mockCase(),
            cursor: Buffer.from(`cursor:${page}:${i}`).toString("base64"),
          })),
          totalCount: 87,
          pageInfo: {
            hasNextPage: true,
            hasPreviousPage: page > 1,
            startCursor: "c3RhcnQ=",
            endCursor: "ZW5k",
          },
        },
      },
    });
  }),

  graphql.mutation("CreateCase", ({ variables }) => {
    return HttpResponse.json({
      data: { createCase: mockCase(variables.input) },
    });
  }),
];

// ── Server Setup ────────────────────────────────────────────────────
export const mockServer = setupServer(...restHandlers, ...graphqlHandlers);

export function enableMocks() {
  mockServer.listen({ onUnhandledRequest: "warn" });
}

export function disableMocks() {
  mockServer.close();
}

export function resetMocks() {
  mockServer.resetHandlers();
}

// ── Scenario Overrides (for edge-case testing) ──────────────────────
export const scenarios = {
  empty: () =>
    mockServer.use(
      http.get("*/v2/cases", () =>
        HttpResponse.json({ data: [], pagination: { page: 1, limit: 25, total: 0, hasNext: false } })
      )
    ),

  serverError: () =>
    mockServer.use(
      http.get("*/v2/cases", () =>
        HttpResponse.json(
          { error: { code: "INTERNAL_ERROR", message: "Database unavailable" } },
          { status: 500 }
        )
      )
    ),

  rateLimited: () =>
    mockServer.use(
      http.get("*/v2/cases", () =>
        HttpResponse.json(
          { error: { code: "RATE_LIMITED", message: "Too many requests" } },
          { status: 429, headers: { "Retry-After": "60" } }
        )
      )
    ),

  slowResponse: () =>
    mockServer.use(
      http.get("*/v2/cases", async () => {
        await delay(5000);
        return HttpResponse.json({ data: [mockCase()], pagination: { page: 1, limit: 25, total: 1, hasNext: false } });
      })
    ),
};
```

**Integration Points:**
- Consumes AN1 spec for response shapes
- Validates mocks against AN5 contract definitions
- AN8 SDK tests run against AN6 mock server
- AN4 security scenarios (401/403/429) available as mock overrides

---

## AN7: Version Commander
### *Semantic Versioning, Deprecation & Migration Guides*

**Purpose:** Manages API lifecycle from v1 to sunset. Enforces semantic versioning,
generates deprecation headers, builds migration guides, and maintains backward
compatibility windows.

**Design Pattern:** API Lifecycle Management (ALM) with Sunset Headers

**Code Example — Version Router & Deprecation Engine:**

```typescript
// Generated by AN7: Version Commander
// API versioning with deprecation enforcement
import { Router, Request, Response, NextFunction } from "express";

// ── Version Registry ────────────────────────────────────────────────
interface VersionEntry {
  version: string;
  status: "current" | "deprecated" | "sunset";
  router: Router;
  deprecatedAt?: string;       // ISO date
  sunsetAt?: string;           // ISO date
  successor?: string;          // Version that replaces this
  changelog: string;
}

const versionRegistry: Map<string, VersionEntry> = new Map();

export function registerVersion(entry: VersionEntry) {
  versionRegistry.set(entry.version, entry);
}

// ── Deprecation Middleware ───────────────────────────────────────────
export function deprecationHeaders(version: string) {
  return (_req: Request, res: Response, next: NextFunction) => {
    const entry = versionRegistry.get(version);
    if (!entry) return next();

    if (entry.status === "deprecated") {
      res.setHeader("Deprecation", `date="${entry.deprecatedAt}"`);
      res.setHeader("Sunset", entry.sunsetAt ?? "");
      res.setHeader(
        "Link",
        `</v${entry.successor}/docs>; rel="successor-version"`
      );
      res.setHeader(
        "X-Deprecation-Notice",
        `API v${version} is deprecated. Migrate to v${entry.successor} before ${entry.sunsetAt}.`
      );
    }

    if (entry.status === "sunset") {
      return res.status(410).json({
        error: {
          code: "API_SUNSET",
          message: `API v${version} has been retired as of ${entry.sunsetAt}.`,
          migration: `/v${entry.successor}/docs/migration`,
        },
      });
    }

    next();
  };
}

// ── Version Router Factory ──────────────────────────────────────────
export function createVersionedApp(app: any) {
  for (const [version, entry] of versionRegistry) {
    app.use(
      `/v${version}`,
      deprecationHeaders(version),
      entry.router
    );
  }

  // Version discovery endpoint
  app.get("/api/versions", (_req: Request, res: Response) => {
    const versions = Array.from(versionRegistry.entries()).map(([v, e]) => ({
      version: v,
      status: e.status,
      deprecatedAt: e.deprecatedAt ?? null,
      sunsetAt: e.sunsetAt ?? null,
      successor: e.successor ?? null,
      changelog: `/v${v}/changelog`,
    }));
    res.json({ versions });
  });
}

// ── Breaking Change Detector ────────────────────────────────────────
interface BreakingChange {
  type: "removed_endpoint" | "removed_field" | "type_change" | "required_added";
  path: string;
  description: string;
  severity: "breaking" | "deprecation" | "addition";
}

export function detectBreakingChanges(
  oldSpec: Record<string, any>,
  newSpec: Record<string, any>
): BreakingChange[] {
  const changes: BreakingChange[] = [];

  // Detect removed endpoints
  for (const path of Object.keys(oldSpec.paths ?? {})) {
    if (!newSpec.paths?.[path]) {
      changes.push({
        type: "removed_endpoint",
        path,
        description: `Endpoint ${path} was removed`,
        severity: "breaking",
      });
    } else {
      for (const method of Object.keys(oldSpec.paths[path])) {
        if (!newSpec.paths[path][method]) {
          changes.push({
            type: "removed_endpoint",
            path: `${method.toUpperCase()} ${path}`,
            description: `Method ${method.toUpperCase()} removed from ${path}`,
            severity: "breaking",
          });
        }
      }
    }
  }

  // Detect removed response fields
  for (const [name, oldSchema] of Object.entries(oldSpec.components?.schemas ?? {})) {
    const newSchema = newSpec.components?.schemas?.[name] as any;
    if (!newSchema) continue;

    for (const prop of Object.keys((oldSchema as any).properties ?? {})) {
      if (!newSchema.properties?.[prop]) {
        changes.push({
          type: "removed_field",
          path: `${name}.${prop}`,
          description: `Field ${prop} removed from ${name}`,
          severity: "breaking",
        });
      }
    }
  }

  return changes;
}

// ── Migration Guide Generator ───────────────────────────────────────
export function generateMigrationGuide(
  from: string,
  to: string,
  changes: BreakingChange[]
): string {
  const breaking = changes.filter((c) => c.severity === "breaking");
  const deprecations = changes.filter((c) => c.severity === "deprecation");

  return `# Migration Guide: v${from} → v${to}

## Breaking Changes (${breaking.length})
${breaking.map((c) => `- **${c.path}**: ${c.description}`).join("\n")}

## Deprecations (${deprecations.length})
${deprecations.map((c) => `- **${c.path}**: ${c.description}`).join("\n")}

## Steps
1. Update base URL from \`/v${from}\` to \`/v${to}\`
2. Review breaking changes above and update client code
3. Test against v${to} staging environment
4. Update SDK: \`npm install @api/client@^${to}.0.0\`
5. Remove deprecated field usage before sunset date
`;
}
```

**Integration Points:**
- AN1 specs for both old and new versions feed the breaking change detector
- AN5 contract tests validate backward compatibility during transitions
- AN8 SDK generator produces version-pinned client libraries
- AN2 routes are wrapped with deprecation middleware

---

## AN8: SDK Generator
### *Type-Safe Client SDKs in Multiple Languages*

**Purpose:** Generates fully-typed client SDKs from the OpenAPI spec, with
built-in retry logic, error handling, authentication, and pagination helpers.

**Design Pattern:** Code Generation + Builder Pattern

**Code Example — TypeScript SDK Generation:**

```typescript
// Generated by AN8: SDK Generator
// Derived from AN1 OpenAPI spec: Case Management API v2
// Includes: auth, retry, pagination, error handling

interface SDKConfig {
  baseUrl: string;
  apiKey?: string;
  accessToken?: string;
  timeout?: number;
  retries?: number;
  onError?: (error: ApiError) => void;
}

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown[],
    public requestId?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Core HTTP Client with Retry ─────────────────────────────────────
class HttpClient {
  private config: Required<SDKConfig>;

  constructor(config: SDKConfig) {
    this.config = {
      baseUrl: config.baseUrl.replace(/\/$/, ""),
      apiKey: config.apiKey ?? "",
      accessToken: config.accessToken ?? "",
      timeout: config.timeout ?? 30_000,
      retries: config.retries ?? 3,
      onError: config.onError ?? (() => {}),
    };
  }

  async request<T>(method: string, path: string, options?: {
    body?: unknown;
    query?: Record<string, string | number | boolean | undefined>;
    headers?: Record<string, string>;
  }): Promise<T> {
    const url = new URL(path, this.config.baseUrl);
    if (options?.query) {
      for (const [k, v] of Object.entries(options.query)) {
        if (v !== undefined) url.searchParams.set(k, String(v));
      }
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options?.headers,
    };

    if (this.config.accessToken) {
      headers.Authorization = `Bearer ${this.config.accessToken}`;
    } else if (this.config.apiKey) {
      headers["X-API-Key"] = this.config.apiKey;
    }

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.config.timeout);

        const response = await fetch(url.toString(), {
          method,
          headers,
          body: options?.body ? JSON.stringify(options.body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timer);

        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({}));
          const apiError = new ApiError(
            response.status,
            errorBody.error?.code ?? "UNKNOWN",
            errorBody.error?.message ?? response.statusText,
            errorBody.error?.details,
            response.headers.get("X-Request-ID") ?? undefined
          );
          if (response.status === 429 || response.status >= 500) {
            lastError = apiError;
            const backoff = Math.min(1000 * 2 ** attempt, 30_000);
            await new Promise((r) => setTimeout(r, backoff));
            continue;
          }
          throw apiError;
        }

        if (response.status === 204) return undefined as T;
        return (await response.json()) as T;
      } catch (err) {
        if (err instanceof ApiError) throw err;
        lastError = err as Error;
      }
    }

    throw lastError ?? new Error("Request failed after retries");
  }
}

// ── Generated SDK Client ────────────────────────────────────────────
interface Case {
  id: string;
  title: string;
  status: "active" | "settled" | "dismissed" | "appealed" | "closed";
  caseType: "civil" | "criminal" | "family" | "appellate" | "federal";
  jurisdiction: string;
  filingDate?: string;
  createdAt: string;
  updatedAt: string;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: { page: number; limit: number; total: number; hasNext: boolean };
}

interface SingleResponse<T> {
  data: T;
}

export class CaseApiClient {
  private http: HttpClient;

  constructor(config: SDKConfig | string) {
    this.http = new HttpClient(
      typeof config === "string" ? { baseUrl: config } : config
    );
  }

  // ── Cases ───────────────────────────────────────────────────────
  async listCases(params?: {
    page?: number;
    limit?: number;
    status?: Case["status"];
  }): Promise<PaginatedResponse<Case>> {
    return this.http.request("GET", "/v2/cases", { query: params as any });
  }

  async getCase(id: string): Promise<SingleResponse<Case>> {
    return this.http.request("GET", `/v2/cases/${id}`);
  }

  async createCase(input: {
    title: string;
    jurisdiction: string;
    caseType: Case["caseType"];
    filingDate?: string;
  }): Promise<SingleResponse<Case>> {
    return this.http.request("POST", "/v2/cases", { body: input });
  }

  async deleteCase(id: string): Promise<void> {
    return this.http.request("DELETE", `/v2/cases/${id}`);
  }

  // ── Pagination Helper ─────────────────────────────────────────
  async *listAllCases(
    params?: { status?: Case["status"]; limit?: number }
  ): AsyncGenerator<Case> {
    let page = 1;
    const limit = params?.limit ?? 100;
    let hasNext = true;

    while (hasNext) {
      const result = await this.listCases({ page, limit, status: params?.status });
      for (const item of result.data) yield item;
      hasNext = result.pagination.hasNext;
      page++;
    }
  }
}
```

**Integration Points:**
- Types derived from AN1 OpenAPI spec schemas
- Auth patterns match AN4 security configuration
- Tests run against AN6 mock servers
- Version-pinned to AN7 API version lifecycle
- Contract compatibility validated by AN5

---

## 🌳 Decision Tree

```
START: What do you need?
│
├─▶ "Design a new API"
│   ├─▶ AN1: Spec-First Designer (OpenAPI + GraphQL SDL)
│   └─▶ Then: AN2 (REST) + AN3 (GraphQL) in parallel
│
├─▶ "Secure my API"
│   └─▶ AN4: Security Bastion
│       ├─▶ Auth? → JWT/JWKS middleware
│       ├─▶ Rate limiting? → Window + key config
│       └─▶ CORS? → Origin whitelist
│
├─▶ "Prevent breaking changes"
│   ├─▶ AN5: Contract Guardian (Pact CDC tests)
│   └─▶ AN7: Version Commander (breaking change detector)
│
├─▶ "Mock for frontend dev"
│   └─▶ AN6: Mock Universe (MSW + GraphQL mocks)
│
├─▶ "Generate client SDK"
│   └─▶ AN8: SDK Generator (TypeScript / Python / Go)
│
├─▶ "Deprecate old version"
│   └─▶ AN7: Version Commander
│       ├─▶ Sunset headers + migration guide
│       └─▶ AN5 validates backward compat
│
└─▶ "Full API Omnigenesis" (all-in-one)
    └─▶ AN1 → AN2 + AN3 → AN4 → AN5 + AN6 → AN7 → AN8
        (Complete pipeline from spec to SDK)
```

---

## 🔗 Cross-Module Integration Matrix

```
        AN1  AN2  AN3  AN4  AN5  AN6  AN7  AN8
  AN1    ─   ▶▶▶  ▶▶▶  ───  ▶▶   ▶▶   ▶▶   ▶▶▶
  AN2   ◀◀◀   ─   ───  ◀◀◀  ▶▶▶  ───  ◀◀   ▶▶
  AN3   ◀◀◀  ───   ─   ◀◀◀  ▶▶   ▶▶   ───  ▶▶▶
  AN4   ───  ▶▶▶  ▶▶▶   ─   ▶▶   ───  ───  ───
  AN5   ◀◀   ◀◀◀  ◀◀   ◀◀    ─   ▶▶▶  ◀◀◀  ───
  AN6   ◀◀   ───  ◀◀   ───  ◀◀◀   ─   ───  ◀◀
  AN7   ◀◀   ▶▶   ───  ───  ▶▶▶  ───   ─   ▶▶▶
  AN8   ◀◀◀  ◀◀   ◀◀◀  ───  ───  ▶▶   ◀◀◀   ─

Legend: ▶▶▶ = produces for │ ◀◀◀ = consumes from │ ─── = no direct link
```

---

## 🏢 Domain Applications

### Litigation API (LitigationOS)
```
AN1 → Define Case/Party/Document schemas in OpenAPI 3.1
AN2 → Generate /cases, /parties, /documents CRUD routes
AN3 → Build federated GraphQL gateway across case services
AN4 → Apply RBAC (attorney, paralegal, admin), rate limiting
AN5 → Contract tests between Case Dashboard ↔ Case API
AN6 → Mock server for frontend team during discovery sprint
AN7 → Plan v1→v2 migration when adding e-filing support
AN8 → Generate TypeScript SDK for the React dashboard
```

### E-Commerce API
```
AN1 → Products, Orders, Payments spec
AN2 → RESTful endpoints with Stripe webhook handlers
AN3 → Storefront GraphQL with inventory federation
AN4 → API key auth + per-merchant rate limits
AN5 → Contract tests: Checkout UI ↔ Payment API
AN6 → Mock payment gateway for load testing
AN7 → Deprecate v1 catalog API, sunset in 90 days
AN8 → Mobile SDK (Swift/Kotlin) for native apps
```

### Healthcare API (HIPAA)
```
AN1 → FHIR-aligned Patient/Encounter schemas
AN2 → RESTful endpoints with audit logging
AN3 → GraphQL for clinical dashboard aggregation
AN4 → OAuth2 + SMART on FHIR + field-level encryption
AN5 → Contract tests ensuring PHI field consistency
AN6 → De-identified mock patient data for dev/test
AN7 → Manage FHIR version transitions (R4 → R5)
AN8 → Python SDK for EHR integration partners
```

---

## ⚡ Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                 FORGE-API-NEXUS Quick Reference              │
├──────────────┬──────────────────────────────────────────────┤
│ COMMAND      │ DESCRIPTION                                  │
├──────────────┼──────────────────────────────────────────────┤
│ @nexus spec  │ Generate OpenAPI 3.1 + GraphQL SDL           │
│ @nexus rest  │ Generate REST route handlers from spec       │
│ @nexus gql   │ Generate federated GraphQL schema            │
│ @nexus secure│ Apply full OWASP API security stack          │
│ @nexus pact  │ Generate consumer-driven contract tests      │
│ @nexus mock  │ Spin up MSW + GraphQL mock server            │
│ @nexus ver   │ Manage versioning + deprecation schedule     │
│ @nexus sdk   │ Generate typed client SDK (TS/Py/Go)         │
│ @nexus omni  │ Full Omnigenesis: spec → everything          │
├──────────────┼──────────────────────────────────────────────┤
│ PIPES        │                                              │
│ spec | rest  │ Generate spec then routes                    │
│ spec | gql   │ Generate spec then GraphQL                   │
│ spec | omni  │ Full pipeline from spec                      │
│ rest | pact  │ Generate routes then contract tests          │
│ rest | mock  │ Generate routes then mock server             │
│ pact | ver   │ Contract tests inform version decisions      │
├──────────────┼──────────────────────────────────────────────┤
│ FLAGS        │                                              │
│ --lang=ts    │ Target language (ts, py, go, rust, java)     │
│ --version=2  │ Target API version                           │
│ --format=oas │ Spec format (oas, graphql, both)             │
│ --strict     │ Fail on any breaking change                  │
│ --dry-run    │ Preview output without writing files         │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 🔄 Omnigenesis Pipeline (End-to-End)

```
INPUT: Domain requirements + entity definitions
  │
  ▼
┌──────────────────────────────────┐
│  AN1: Spec-First Designer        │  → openapi.yaml + schema.graphql
└──────────────┬───────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│ AN2: REST    │ │ AN3: GraphQL │  → routes/ + resolvers/
│ Endpoint     │ │ Synthesizer  │
└──────┬───────┘ └──────┬───────┘
       │                │
       └───────┬────────┘
               ▼
┌──────────────────────────────────┐
│  AN4: Security Bastion           │  → middleware/ + auth config
└──────────────┬───────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│ AN5: Contract│ │ AN6: Mock    │  → tests/ + mocks/
│ Guardian     │ │ Universe     │
└──────┬───────┘ └──────┬───────┘
       │                │
       └───────┬────────┘
               ▼
┌──────────────────────────────────┐
│  AN7: Version Commander          │  → CHANGELOG + migration guide
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  AN8: SDK Generator              │  → sdk/{ts,py,go}/ + docs/
└──────────────┬───────────────────┘
               ▼
OUTPUT: Complete API ecosystem ready for deployment
```

---

> **FORGE-API-NEXUS (Ω-Δ99)** — *One specification. Infinite possibilities.*
> Eight skills forged into one. API Omnigenesis achieved.
