---
name: FORGE-POLYGLOT-MCP
description: >-
  Universal MCP Server Genesis Engine. Fuses 10 language-specific MCP generators into 
  a polyglot code synthesis system. Define tools ONCE in a universal spec → generate
  production-ready MCP servers in ANY of 10 languages with native idioms, patterns,
  and best practices. The fusion creates CROSS-LANGUAGE INTELLIGENCE — understanding
  not just syntax but the soul of each language's design philosophy.
  Use for "MCP server", "tool generation", "polyglot", "cross-language", "code generation",
  "MCP in [any language]", or "universal tool spec".
category: engineering
version: "1.0.0"
triggers:
  - MCP server
  - tool generation
  - polyglot code
  - cross-language
  - code generation
  - universal spec
  - FastMCP
  - MCP in python
  - MCP in typescript
  - MCP in rust
  - MCP in go
  - multi-language
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-07-17
  forge_class: cross-domain-innovation
  emergent_capability: "Cross-language MCP synthesis — one spec, any language, native quality"
---

# 🌐 FORGE-POLYGLOT-MCP

## Universal MCP Genesis Engine (Ω-Δ99)

> **EMERGENT CAPABILITY**: No single MCP generator understands how concepts translate
> across language paradigms. FORGE-POLYGLOT-MCP creates a **META-UNDERSTANDING** of
> MCP tool design that transcends any one language. Describe your tools ONCE in a
> universal specification. The Genesis Engine routes through 10 language-specific
> generators — each producing code that isn't merely syntactically correct, but
> **idiomatically native**. Python code feels Pythonic. Rust code leverages ownership
> and traits. Go code uses interfaces and goroutines. This is CROSS-LANGUAGE
> INTELLIGENCE: the ability to express the same semantic intent through the unique
> design philosophy of each target language.
>
> _"One spec to define them. Ten generators to build them. Zero compromise on quality."_

---

## Forged Skills

| # | Source Skill | Language | Key Patterns | Contribution to Fusion |
|---|---|---|---|---|
| 1 | `python-mcp-server-generator` | Python 3.11+ | FastMCP, Pydantic models, `async`/`await`, type hints | Rapid prototyping baseline; Pydantic validation paradigm |
| 2 | `typescript-mcp-server-generator` | TypeScript 5.x | Zod schemas, MCP SDK, `Promise`-based concurrency | Type-safety reference model; Zod ↔ JSON Schema bridge |
| 3 | `java-mcp-server-generator` | Java 21+ | Spring Boot, Maven/Gradle, annotations, records | Enterprise patterns; annotation-driven tool registration |
| 4 | `go-mcp-server-generator` | Go 1.22+ | Go modules, interfaces, goroutines, channels | Concurrency-first design; interface-based tool contracts |
| 5 | `rust-mcp-server-generator` | Rust (2024 ed.) | Cargo, traits, `async-std`/`tokio`, `Result<T,E>` | Zero-cost abstraction patterns; trait-based tool dispatch |
| 6 | `kotlin-mcp-server-generator` | Kotlin 2.x | Coroutines, Ktor, sealed classes, DSL builders | Coroutine mapping; expressive DSL-style tool definitions |
| 7 | `csharp-mcp-server-generator` | C# 12 / .NET 9 | DI container, `async Task`, records, source generators | DI-first architecture; source-generator metaprogramming |
| 8 | `ruby-mcp-server-generator` | Ruby 3.3+ | Gems, Rack middleware, blocks, mixins | Convention-over-configuration; mixin-based tool composition |
| 9 | `swift-mcp-server-generator` | Swift 6.0+ | Swift concurrency, actors, Codable, Foundation | Actor-based isolation; protocol-oriented tool design |
| 10 | `php-mcp-server-generator` | PHP 8.3+ | Composer, Laravel-style, attributes, Fibers | Attribute-driven registration; Laravel service providers |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FORGE-POLYGLOT-MCP                        │
│               Universal MCP Genesis Engine                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────┐              │
│  │         UNIVERSAL TOOL SPEC (PM1)         │              │
│  │  ┌─────────┐ ┌──────────┐ ┌───────────┐  │              │
│  │  │  Tools  │ │Resources │ │  Prompts   │  │              │
│  │  │  Defns  │ │  Defns   │ │   Defns    │  │              │
│  │  └────┬────┘ └────┬─────┘ └─────┬─────┘  │              │
│  │       └───────────┼─────────────┘         │              │
│  └───────────────────┼───────────────────────┘              │
│                      ▼                                      │
│  ┌───────────────────────────────────────────┐              │
│  │       LANGUAGE IDIOM ENGINE (PM2)         │              │
│  │   ┌──────────┐  ┌────────────────────┐    │              │
│  │   │ Language  │  │  Idiom Knowledge   │    │              │
│  │   │ Detector  │  │  Base (10 langs)   │    │              │
│  │   └─────┬────┘  └────────┬───────────┘    │              │
│  │         └────────┬───────┘                 │              │
│  └──────────────────┼────────────────────────┘              │
│                     ▼                                       │
│  ┌──────────────────────────────────────────┐               │
│  │        TRANSLATION CORE (PM3+PM4+PM7)    │               │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────┐  │               │
│  │  │  Type    │ │  Async  │ │  Error   │  │               │
│  │  │  System  │ │Concurr. │ │ Handling │  │               │
│  │  │Translator│ │ Mapper  │ │Harmonizer│  │               │
│  │  └────┬─────┘ └────┬────┘ └────┬─────┘  │               │
│  │       └─────────────┼──────────┘         │               │
│  └─────────────────────┼────────────────────┘               │
│                        ▼                                    │
│  ┌──────── LANGUAGE ROUTER ─────────────────┐               │
│  │                                          │               │
│  │  ┌────┐┌────┐┌────┐┌────┐┌────┐         │               │
│  │  │ Py ││ TS ││Java││ Go ││Rust│         │               │
│  │  └──┬─┘└──┬─┘└──┬─┘└──┬─┘└──┬─┘         │               │
│  │  ┌──┴─┐┌──┴─┐┌──┴─┐┌──┴─┐┌──┴─┐         │               │
│  │  │ Kt ││ C# ││Ruby││Swft││PHP │         │               │
│  │  └──┬─┘└──┬─┘└──┬─┘└──┬─┘└──┬─┘         │               │
│  │     └─────┴─────┴──┬──┴─────┘            │               │
│  └────────────────────┼─────────────────────┘               │
│                       ▼                                     │
│  ┌──────────────────────────────────────────┐               │
│  │     BUILD + TEST + DEPLOY (PM5+PM6+PM8)  │               │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────┐  │               │
│  │  │ Package/ │ │ Testing │ │ Deploy   │  │               │
│  │  │  Build   │ │Scaffold │ │ Adapter  │  │               │
│  │  │Synthesize│ │Generator│ │          │  │               │
│  │  └──────────┘ └─────────┘ └──────────┘  │               │
│  └──────────────────────────────────────────┘               │
│                       ▼                                     │
│            PRODUCTION-READY MCP SERVER                      │
│        (in your chosen language, idiomatically)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Module PM1: Universal Tool Spec

### Purpose
Define MCP tools, resources, and prompts in a **language-agnostic specification** that
serves as the single source of truth for all downstream generators.

### Design Philosophy
The Universal Tool Spec (UTS) is **not** YAML templates or string interpolation. It is a
structured schema that captures the **semantic intent** of each tool: what it does, what
it accepts, what it returns, and what side effects it has. The generators then express
that intent through the idioms of each target language.

### Spec Structure

```json
{
  "$schema": "https://litigationos.dev/schemas/uts/v1.json",
  "server": {
    "name": "my-mcp-server",
    "version": "1.0.0",
    "description": "A litigation document analyzer",
    "capabilities": ["tools", "resources", "prompts"]
  },
  "tools": [
    {
      "name": "analyze_document",
      "description": "Analyze a legal document for key entities and dates",
      "parameters": {
        "document_path": { "type": "string", "required": true, "description": "Path to the document" },
        "analysis_depth": { "type": "enum", "values": ["shallow", "deep", "exhaustive"], "default": "deep" },
        "max_entities": { "type": "integer", "min": 1, "max": 1000, "default": 100 },
        "include_metadata": { "type": "boolean", "default": true }
      },
      "returns": {
        "type": "object",
        "fields": {
          "entities": { "type": "array", "items": "Entity" },
          "dates": { "type": "array", "items": "DateReference" },
          "summary": { "type": "string" }
        }
      },
      "errors": ["FileNotFound", "ParseError", "AnalysisTimeout"],
      "side_effects": ["filesystem_read"],
      "async": true,
      "timeout_ms": 30000
    }
  ],
  "types": {
    "Entity": {
      "name": { "type": "string" },
      "kind": { "type": "enum", "values": ["person", "organization", "location", "statute"] },
      "confidence": { "type": "float", "min": 0.0, "max": 1.0 }
    },
    "DateReference": {
      "date": { "type": "string", "format": "iso8601" },
      "context": { "type": "string" },
      "significance": { "type": "enum", "values": ["critical", "important", "minor"] }
    }
  },
  "resources": [
    {
      "uri_template": "legal://documents/{case_id}/{doc_type}",
      "name": "Case Document",
      "description": "Access documents by case ID and type",
      "mime_type": "application/pdf"
    }
  ],
  "prompts": [
    {
      "name": "summarize_filing",
      "description": "Generate a concise summary of a court filing",
      "arguments": {
        "filing_text": { "type": "string", "required": true },
        "audience": { "type": "enum", "values": ["attorney", "client", "judge"], "default": "attorney" }
      }
    }
  ]
}
```

### Validation Rules
- All tool names must be `snake_case` (generators convert to target naming conventions)
- Type references must resolve within the `types` block
- Enum values are preserved as-is; generators produce language-native enum constructs
- `async: true` tools trigger concurrency-aware generation in all target languages
- `errors` array maps to language-specific error handling (see PM7)

---

## Module PM2: Language Idiom Engine

### Purpose
Encode the **design philosophy** of each language so generated code reads as if a senior
developer in that language wrote it by hand.

### Idiom Profiles

#### Python — "Explicit is better than implicit"
- Use `snake_case` everywhere; dataclasses or Pydantic models for types
- Type hints via `typing` module; `Optional[T]` over nullable
- Context managers for resource cleanup; generators for lazy sequences
- FastMCP decorators: `@mcp.tool()`, `@mcp.resource()`
- Docstrings in Google style; `logging` module for diagnostics

#### TypeScript — "Types as documentation"
- `camelCase` functions, `PascalCase` types, `UPPER_SNAKE` constants
- Zod schemas for runtime validation alongside TypeScript types
- `async/await` with explicit `Promise<T>` return types
- MCP SDK classes: `McpServer`, `StdioServerTransport`
- JSDoc + inline types; barrel exports via `index.ts`

#### Java — "Ceremony with purpose"
- Annotations for metadata: `@Tool`, `@Description`, `@Parameter`
- Records for immutable data; sealed interfaces for enums
- `CompletableFuture<T>` for async; `Optional<T>` for nullable returns
- Spring Boot auto-configuration; Maven POM with dependency management
- Javadoc on all public members; package-by-feature layout

#### Go — "Less is more"
- Exported (`PascalCase`) vs unexported (`camelCase`); no classes, only structs + methods
- Interfaces defined by consumer, not producer; implicit satisfaction
- Goroutines + channels for concurrency; `context.Context` everywhere
- `error` return values, never exceptions; `fmt.Errorf` wrapping
- `go.mod` with minimal dependencies; table-driven tests

#### Rust — "Fearless concurrency"
- `snake_case` functions, `PascalCase` types, `SCREAMING_SNAKE` constants
- Traits for tool dispatch; `#[derive(...)]` for boilerplate elimination
- `Result<T, E>` for all fallible operations; `?` operator for propagation
- `tokio` runtime with `#[tokio::main]`; `Arc<Mutex<T>>` for shared state
- `Cargo.toml` workspace; `#[cfg(test)]` inline test modules

#### Kotlin — "Concise but expressive"
- Coroutines with `suspend fun`; `Flow<T>` for streaming results
- Sealed classes for error hierarchies; data classes for DTOs
- DSL builders for server configuration; extension functions for utility
- Ktor for HTTP transport; `kotlinx.serialization` for JSON
- `build.gradle.kts` with Kotlin DSL; JUnit 5 + Kotest assertions

#### C# — "Enterprise-grade, DI-first"
- `PascalCase` everywhere; interfaces prefixed with `I`
- Dependency injection via `IServiceCollection`; `async Task<T>` returns
- Records for immutable models; `required` keyword for mandatory props
- Source generators for compile-time tool registration
- `.csproj` with `<PackageReference>`; xUnit + Moq for testing

#### Ruby — "Convention over configuration"
- `snake_case` methods, `PascalCase` classes, `UPPER_SNAKE` constants
- Blocks and `yield` for callback patterns; mixins via `include`/`extend`
- `Gemfile` + Bundler; Rack middleware for HTTP transport
- Minitest or RSpec; `rubocop` for style enforcement
- Dynamic method definition for tool registration

#### Swift — "Protocol-oriented design"
- Protocols for tool contracts; `actor` for thread-safe state
- `async/await` with structured concurrency; `Task` groups for parallelism
- `Codable` for JSON serialization; `Result<Success, Failure>` for errors
- Swift Package Manager (`Package.swift`); XCTest for testing
- Property wrappers for parameter validation

#### PHP — "Pragmatic web heritage"
- `camelCase` methods, `PascalCase` classes; PSR-12 style
- Attributes (`#[Tool]`, `#[Parameter]`) for metadata; Fibers for async
- Composer for dependencies; Laravel service providers for DI
- PHPUnit for testing; PHPStan for static analysis
- Enums (PHP 8.1+) for finite value sets

---

## Module PM3: Type System Translator

### Purpose
Map types across languages faithfully, preserving semantics while respecting each
language's type system capabilities and constraints.

### Core Type Mapping Matrix

| UTS Type | Python | TypeScript | Java | Go | Rust | Kotlin | C# | Ruby | Swift | PHP |
|---|---|---|---|---|---|---|---|---|---|---|
| `string` | `str` | `string` | `String` | `string` | `String` | `String` | `string` | `String` | `String` | `string` |
| `integer` | `int` | `number` | `int` / `long` | `int` / `int64` | `i32` / `i64` | `Int` / `Long` | `int` / `long` | `Integer` | `Int` | `int` |
| `float` | `float` | `number` | `double` | `float64` | `f64` | `Double` | `double` | `Float` | `Double` | `float` |
| `boolean` | `bool` | `boolean` | `boolean` | `bool` | `bool` | `Boolean` | `bool` | `TrueClass` | `Bool` | `bool` |
| `array<T>` | `list[T]` | `T[]` | `List<T>` | `[]T` | `Vec<T>` | `List<T>` | `List<T>` | `Array` | `[T]` | `array` |
| `map<K,V>` | `dict[K,V]` | `Record<K,V>` | `Map<K,V>` | `map[K]V` | `HashMap<K,V>` | `Map<K,V>` | `Dictionary<K,V>` | `Hash` | `[K:V]` | `array` |
| `optional<T>` | `T \| None` | `T \| undefined` | `Optional<T>` | `*T` | `Option<T>` | `T?` | `T?` | `T \| nil` | `T?` | `?T` |
| `enum` | `Enum` | `union type` | `sealed interface` | `const iota` | `enum` | `sealed class` | `enum` | `module constants` | `enum` | `enum` |
| `object` | `@dataclass` | `interface` | `record` | `struct` | `struct` | `data class` | `record` | `Struct/Class` | `struct` | `class` |
| `datetime` | `datetime` | `Date` | `Instant` | `time.Time` | `chrono::DateTime` | `Instant` | `DateTimeOffset` | `Time` | `Date` | `DateTimeImmutable` |

### Nullable Strategy per Language
- **Python**: `Optional[T]` with explicit `None` checks; Pydantic `Field(default=None)`
- **TypeScript**: `T | undefined` in params; strict null checks enabled
- **Java**: `Optional<T>` return types; `@Nullable` annotations on parameters
- **Go**: Pointer types `*T`; zero values for non-pointer types; `nil` checks
- **Rust**: `Option<T>` with pattern matching; `.unwrap_or_default()` for defaults
- **Kotlin**: `T?` nullable types; safe calls `?.` and Elvis `?:` operator
- **C#**: Nullable reference types `T?`; null-coalescing `??` operator
- **Ruby**: `nil` checks; safe navigation `&.` operator
- **Swift**: Optionals `T?`; `guard let` / `if let` unwrapping
- **PHP**: `?T` nullable type hints; null coalescing `??` operator

### Composite Type Translation
When the UTS defines a custom type (e.g., `Entity`), each generator produces:
- **Python**: A Pydantic `BaseModel` subclass with `Field()` validators
- **TypeScript**: A Zod schema + inferred TypeScript type via `z.infer<>`
- **Java**: A `record` with `@JsonProperty` annotations
- **Go**: A `struct` with `json:""` tags
- **Rust**: A `struct` with `#[derive(Serialize, Deserialize)]`
- **Kotlin**: A `data class` with `@Serializable` annotation
- **C#**: A `record` with `System.Text.Json` attributes
- **Ruby**: A `Struct` or plain class with `attr_accessor`
- **Swift**: A `struct` conforming to `Codable`
- **PHP**: A `readonly class` with constructor promotion

---

## Module PM4: Async/Concurrency Mapper

### Purpose
Tools marked `async: true` in the UTS must leverage each language's **native concurrency
model** — not bolted-on threading, but the idiomatic concurrency primitives.

### Concurrency Model Matrix

| Concept | Python | TypeScript | Java | Go | Rust | Kotlin | C# | Ruby | Swift | PHP |
|---|---|---|---|---|---|---|---|---|---|---|
| **Async function** | `async def` | `async function` | `CompletableFuture` | goroutine | `async fn` | `suspend fun` | `async Task` | `Fiber` | `async` | `Fiber` |
| **Await** | `await` | `await` | `.join()` | `<-chan` | `.await` | implicit | `await` | `Fiber.resume` | `await` | `Fiber::suspend` |
| **Parallelism** | `asyncio.gather` | `Promise.all` | `ForkJoinPool` | `go func()` | `tokio::join!` | `async {}` | `Task.WhenAll` | `Thread` | `TaskGroup` | `Fiber` pool |
| **Cancellation** | `Task.cancel()` | `AbortController` | `Future.cancel()` | `context.Cancel` | `tokio::select!` | `Job.cancel()` | `CancellationToken` | N/A | `Task.cancel()` | N/A |
| **Streaming** | `async for` | `AsyncIterator` | `Flow<T>` (Reactor) | `chan T` | `Stream` trait | `Flow<T>` | `IAsyncEnumerable` | `Enumerator` | `AsyncSequence` | Generator |
| **Timeout** | `asyncio.timeout` | `AbortSignal.timeout` | `.orTimeout()` | `context.WithTimeout` | `tokio::time::timeout` | `withTimeout` | `Task.WhenAny` | `Timeout.timeout` | `Task.sleep` | `set_time_limit` |

### Generation Rules
1. If `async: true` and language has native async → use it directly
2. If `async: true` and language lacks native async (older Ruby/PHP) → use fiber/thread wrapper
3. If `timeout_ms` specified → wrap in language-native timeout mechanism
4. If tool has `side_effects: ["filesystem_read"]` → add resource cleanup patterns
5. Streaming results → use language-native async iteration where available

### Example: Same Async Tool in Three Languages

**Python (FastMCP)**:
```python
from mcp.server.fastmcp import FastMCP
import asyncio

mcp = FastMCP("document-analyzer")

@mcp.tool()
async def analyze_document(
    document_path: str,
    analysis_depth: str = "deep",
    max_entities: int = 100,
    include_metadata: bool = True,
) -> dict:
    """Analyze a legal document for key entities and dates."""
    async with asyncio.timeout(30):
        content = await read_document(document_path)
        entities = await extract_entities(content, max_entities)
        dates = await extract_dates(content)
        return {
            "entities": [e.model_dump() for e in entities],
            "dates": [d.model_dump() for d in dates],
            "summary": await summarize(content, analysis_depth),
        }
```

**Go**:
```go
package main

import (
    "context"
    "time"
)

type AnalyzeDocumentParams struct {
    DocumentPath    string `json:"document_path"`
    AnalysisDepth   string `json:"analysis_depth"`
    MaxEntities     int    `json:"max_entities"`
    IncludeMetadata bool   `json:"include_metadata"`
}

type AnalyzeDocumentResult struct {
    Entities []Entity        `json:"entities"`
    Dates    []DateReference `json:"dates"`
    Summary  string          `json:"summary"`
}

func (s *Server) AnalyzeDocument(ctx context.Context, params AnalyzeDocumentParams) (*AnalyzeDocumentResult, error) {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    content, err := readDocument(ctx, params.DocumentPath)
    if err != nil {
        return nil, fmt.Errorf("reading document: %w", err)
    }

    entitiesCh := make(chan []Entity, 1)
    datesCh := make(chan []DateReference, 1)
    errCh := make(chan error, 2)

    go func() {
        entities, err := extractEntities(ctx, content, params.MaxEntities)
        if err != nil {
            errCh <- err
            return
        }
        entitiesCh <- entities
    }()

    go func() {
        dates, err := extractDates(ctx, content)
        if err != nil {
            errCh <- err
            return
        }
        datesCh <- dates
    }()

    // Collect results
    var entities []Entity
    var dates []DateReference
    for i := 0; i < 2; i++ {
        select {
        case e := <-entitiesCh:
            entities = e
        case d := <-datesCh:
            dates = d
        case err := <-errCh:
            return nil, err
        case <-ctx.Done():
            return nil, ctx.Err()
        }
    }

    summary, err := summarize(ctx, content, params.AnalysisDepth)
    if err != nil {
        return nil, fmt.Errorf("summarizing: %w", err)
    }

    return &AnalyzeDocumentResult{
        Entities: entities,
        Dates:    dates,
        Summary:  summary,
    }, nil
}
```

**Rust (tokio)**:
```rust
use serde::{Deserialize, Serialize};
use tokio::time::{timeout, Duration};
use anyhow::Result;

#[derive(Deserialize)]
struct AnalyzeDocumentParams {
    document_path: String,
    #[serde(default = "default_depth")]
    analysis_depth: AnalysisDepth,
    #[serde(default = "default_max_entities")]
    max_entities: u32,
    #[serde(default = "default_true")]
    include_metadata: bool,
}

#[derive(Serialize)]
struct AnalyzeDocumentResult {
    entities: Vec<Entity>,
    dates: Vec<DateReference>,
    summary: String,
}

async fn analyze_document(params: AnalyzeDocumentParams) -> Result<AnalyzeDocumentResult> {
    timeout(Duration::from_secs(30), async {
        let content = read_document(&params.document_path).await?;

        let (entities, dates) = tokio::join!(
            extract_entities(&content, params.max_entities),
            extract_dates(&content),
        );

        let summary = summarize(&content, &params.analysis_depth).await?;

        Ok(AnalyzeDocumentResult {
            entities: entities?,
            dates: dates?,
            summary,
        })
    }).await?
}
```

---

## Module PM5: Package/Build Synthesizer

### Purpose
Generate complete, ready-to-build project scaffolds with correct dependency management,
build scripts, and development tooling for each target language.

### Build Config Matrix

| Language | Build File | Package Manager | Lock File | Dev Script | Lint |
|---|---|---|---|---|---|
| Python | `pyproject.toml` | `uv` / `pip` | `uv.lock` | `uv run server.py` | `ruff` |
| TypeScript | `package.json` | `npm` / `pnpm` | `package-lock.json` | `npm run dev` | `eslint` |
| Java | `pom.xml` | Maven | — | `mvn spring-boot:run` | `checkstyle` |
| Go | `go.mod` | Go modules | `go.sum` | `go run .` | `golangci-lint` |
| Rust | `Cargo.toml` | Cargo | `Cargo.lock` | `cargo run` | `clippy` |
| Kotlin | `build.gradle.kts` | Gradle | `gradle.lockfile` | `./gradlew run` | `detekt` |
| C# | `*.csproj` | NuGet | `packages.lock.json` | `dotnet run` | `dotnet format` |
| Ruby | `Gemfile` | Bundler | `Gemfile.lock` | `bundle exec ruby server.rb` | `rubocop` |
| Swift | `Package.swift` | SwiftPM | `Package.resolved` | `swift run` | `swiftlint` |
| PHP | `composer.json` | Composer | `composer.lock` | `php server.php` | `phpstan` |

### Generated Project Structure (Python example)

```
my-mcp-server/
├── pyproject.toml          # Dependencies, metadata, tool configs
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── server.py       # MCP server entry point
│       ├── tools/
│       │   ├── __init__.py
│       │   └── analyze_document.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── entity.py
│       │   └── date_reference.py
│       └── resources/
│           ├── __init__.py
│           └── case_document.py
├── tests/
│   ├── conftest.py
│   ├── test_analyze_document.py
│   └── test_models.py
├── Dockerfile
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

### Generated `pyproject.toml`

```toml
[project]
name = "my-mcp-server"
version = "1.0.0"
description = "A litigation document analyzer"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23", "ruff>=0.5"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## Module PM6: Testing Scaffold Generator

### Purpose
Every generated MCP server ships with a **complete test suite** using each language's
native testing framework. Tests cover tool execution, input validation, error handling,
and MCP protocol compliance.

### Testing Framework Matrix

| Language | Framework | Assertion Style | Mocking | Async Testing |
|---|---|---|---|---|
| Python | `pytest` + `pytest-asyncio` | `assert x == y` | `unittest.mock` | `@pytest.mark.asyncio` |
| TypeScript | `vitest` / `jest` | `expect(x).toBe(y)` | `vi.mock()` | `async/await` in tests |
| Java | JUnit 5 | `assertEquals(x, y)` | Mockito | `@Test` + `CompletableFuture` |
| Go | `testing` stdlib | `if got != want { t.Errorf }` | interfaces | goroutine tests |
| Rust | `#[cfg(test)]` | `assert_eq!(x, y)` | trait objects | `#[tokio::test]` |
| Kotlin | JUnit 5 + Kotest | `shouldBe` matchers | MockK | `runTest { }` |
| C# | xUnit | `Assert.Equal(x, y)` | Moq / NSubstitute | `async Task` test methods |
| Ruby | RSpec / Minitest | `expect(x).to eq(y)` | `double` / `allow` | fiber-aware tests |
| Swift | XCTest | `XCTAssertEqual(x, y)` | protocols | `async` test methods |
| PHP | PHPUnit | `$this->assertEquals()` | Prophecy / Mockery | Fiber-aware assertions |

### Generated Test Categories
1. **Unit tests** — Each tool function in isolation with mocked dependencies
2. **Validation tests** — Verify parameter constraints (min/max, required, enums)
3. **Error path tests** — Each declared error type triggers correctly
4. **Integration tests** — Full MCP protocol round-trip via stdio transport
5. **Snapshot tests** — Tool responses match expected JSON structure

### Example Test (Python)

```python
import pytest
from my_mcp_server.tools.analyze_document import analyze_document

@pytest.mark.asyncio
async def test_analyze_document_returns_entities():
    result = await analyze_document(
        document_path="fixtures/sample_filing.pdf",
        analysis_depth="shallow",
        max_entities=10,
    )
    assert "entities" in result
    assert len(result["entities"]) <= 10
    assert all("name" in e and "kind" in e for e in result["entities"])

@pytest.mark.asyncio
async def test_analyze_document_file_not_found():
    with pytest.raises(FileNotFoundError):
        await analyze_document(document_path="/nonexistent/path.pdf")

@pytest.mark.asyncio
async def test_analyze_document_respects_timeout():
    with pytest.raises(TimeoutError):
        await analyze_document(
            document_path="fixtures/enormous_document.pdf",
            analysis_depth="exhaustive",
        )
```

---

## Module PM7: Error Handling Harmonizer

### Purpose
Map the UTS `errors` array to each language's native error handling paradigm. The goal:
errors feel natural in every language, not like a foreign concept forced into the syntax.

### Error Philosophy per Language

| Language | Paradigm | Mechanism | Idiom |
|---|---|---|---|
| Python | Exceptions | `raise CustomError("msg")` | Custom exception classes inheriting `Exception` |
| TypeScript | Exceptions | `throw new CustomError("msg")` | Custom error classes extending `Error` |
| Java | Checked exceptions | `throws AnalysisException` | Exception hierarchy with semantic subtypes |
| Go | Return values | `return nil, &FileNotFoundError{}` | Error types implementing `error` interface |
| Rust | `Result` type | `Err(AnalysisError::FileNotFound)` | Enum variants in `thiserror` derive |
| Kotlin | Exceptions + sealed | `throw AnalysisException.FileNotFound` | Sealed class hierarchies |
| C# | Exceptions | `throw new FileNotFoundException()` | Custom exception classes with inner exceptions |
| Ruby | Exceptions | `raise FileNotFoundError` | Custom classes inheriting `StandardError` |
| Swift | Typed throws | `throw AnalysisError.fileNotFound` | Enums conforming to `Error` protocol |
| PHP | Exceptions | `throw new FileNotFoundException()` | SPL exception subclasses |

### Error Mapping Example

Given UTS errors: `["FileNotFound", "ParseError", "AnalysisTimeout"]`

**Rust** generates:
```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AnalyzeDocumentError {
    #[error("File not found: {path}")]
    FileNotFound { path: String },

    #[error("Failed to parse document: {reason}")]
    ParseError { reason: String },

    #[error("Analysis timed out after {elapsed_ms}ms")]
    AnalysisTimeout { elapsed_ms: u64 },
}
```

**Go** generates:
```go
type FileNotFoundError struct {
    Path string
}

func (e *FileNotFoundError) Error() string {
    return fmt.Sprintf("file not found: %s", e.Path)
}

type ParseError struct {
    Reason string
}

func (e *ParseError) Error() string {
    return fmt.Sprintf("failed to parse document: %s", e.Reason)
}

type AnalysisTimeoutError struct {
    ElapsedMs int64
}

func (e *AnalysisTimeoutError) Error() string {
    return fmt.Sprintf("analysis timed out after %dms", e.ElapsedMs)
}
```

**Kotlin** generates:
```kotlin
sealed class AnalyzeDocumentError(message: String) : Exception(message) {
    data class FileNotFound(val path: String) :
        AnalyzeDocumentError("File not found: $path")

    data class ParseError(val reason: String) :
        AnalyzeDocumentError("Failed to parse document: $reason")

    data class AnalysisTimeout(val elapsedMs: Long) :
        AnalyzeDocumentError("Analysis timed out after ${elapsedMs}ms")
}
```

---

## Module PM8: Deployment Adapter

### Purpose
Generate deployment configurations so the MCP server can run anywhere — local stdio,
Docker container, serverless function, or platform-specific hosting.

### Deployment Target Matrix

| Target | Transport | Config File | Languages Supported |
|---|---|---|---|
| **Local stdio** | stdin/stdout | MCP client config | All 10 |
| **Docker** | stdio or SSE | `Dockerfile` | All 10 |
| **AWS Lambda** | HTTP/SSE | `serverless.yml` | Python, TS, Java, Go, Rust, C# |
| **Cloud Run** | HTTP/SSE | `cloudbuild.yaml` | All 10 |
| **Fly.io** | HTTP/SSE | `fly.toml` | All 10 |
| **Systemd** | stdio | `*.service` file | Python, Go, Rust, C# |

### Generated Dockerfile (multi-stage, language-aware)

**Python**:
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ ./src/
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["python", "-m", "my_mcp_server.server"]
```

**Rust**:
```dockerfile
FROM rust:1.80-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/my-mcp-server /usr/local/bin/
ENTRYPOINT ["my-mcp-server"]
```

**Go**:
```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /server .

FROM scratch
COPY --from=builder /server /server
ENTRYPOINT ["/server"]
```

### MCP Client Configuration (auto-generated)

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "my-mcp-server:latest"],
      "transportType": "stdio"
    }
  }
}
```

---

## Language Comparison Matrix

How core MCP concepts express across all 10 languages at a glance:

| MCP Concept | Python | TypeScript | Java | Go | Rust |
|---|---|---|---|---|---|
| **Tool registration** | `@mcp.tool()` | `server.tool()` | `@Tool` annotation | `AddTool()` method | `#[tool]` macro |
| **Parameter validation** | Pydantic `Field()` | Zod `.string()` | Bean Validation | struct tags | `serde` attributes |
| **Server init** | `FastMCP("name")` | `new McpServer()` | `@SpringBootApp` | `mcp.NewServer()` | `Server::builder()` |
| **Transport** | `mcp.run()` | `StdioTransport` | Auto-configured | `stdio.Serve()` | `StdioTransport` |
| **JSON handling** | `json` / Pydantic | native / Zod | Jackson | `encoding/json` | `serde_json` |

| MCP Concept | Kotlin | C# | Ruby | Swift | PHP |
|---|---|---|---|---|---|
| **Tool registration** | DSL builder | `[McpTool]` | `register_tool` | `@Tool` macro | `#[Tool]` attribute |
| **Parameter validation** | `require()` | Data annotations | custom validators | property wrappers | attributes |
| **Server init** | `mcpServer { }` | `builder.AddMcp()` | `MCP::Server.new` | `MCPServer()` | `new McpServer()` |
| **Transport** | Ktor plugin | middleware | Rack handler | `AsyncStream` | stream wrapper |
| **JSON handling** | `kotlinx.serialization` | `System.Text.Json` | `json` gem | `Codable` | `json_encode` |

---

## Universal Spec Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-2020-12/schema",
  "$id": "https://litigationos.dev/schemas/uts/v1.json",
  "title": "Universal Tool Specification",
  "description": "Language-agnostic MCP server definition for FORGE-POLYGLOT-MCP",
  "type": "object",
  "required": ["server", "tools"],
  "properties": {
    "server": {
      "type": "object",
      "required": ["name", "version"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z][a-z0-9-]*$" },
        "version": { "type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$" },
        "description": { "type": "string" },
        "capabilities": {
          "type": "array",
          "items": { "enum": ["tools", "resources", "prompts", "sampling", "logging"] }
        }
      }
    },
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description", "parameters"],
        "properties": {
          "name": { "type": "string", "pattern": "^[a-z_][a-z0-9_]*$" },
          "description": { "type": "string" },
          "parameters": {
            "type": "object",
            "additionalProperties": { "$ref": "#/$defs/ParameterDef" }
          },
          "returns": { "$ref": "#/$defs/TypeRef" },
          "errors": { "type": "array", "items": { "type": "string" } },
          "side_effects": {
            "type": "array",
            "items": { "enum": ["filesystem_read", "filesystem_write", "network", "database", "subprocess"] }
          },
          "async": { "type": "boolean", "default": false },
          "timeout_ms": { "type": "integer", "minimum": 100 }
        }
      }
    },
    "types": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": { "$ref": "#/$defs/TypeRef" }
      }
    },
    "resources": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["uri_template", "name"],
        "properties": {
          "uri_template": { "type": "string" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "mime_type": { "type": "string" }
        }
      }
    },
    "prompts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" },
          "arguments": {
            "type": "object",
            "additionalProperties": { "$ref": "#/$defs/ParameterDef" }
          }
        }
      }
    }
  },
  "$defs": {
    "ParameterDef": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": { "enum": ["string", "integer", "float", "boolean", "enum", "array", "object", "datetime"] },
        "required": { "type": "boolean", "default": false },
        "description": { "type": "string" },
        "default": {},
        "values": { "type": "array", "items": { "type": "string" } },
        "min": { "type": "number" },
        "max": { "type": "number" },
        "items": { "type": "string" },
        "format": { "type": "string" }
      }
    },
    "TypeRef": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "fields": { "type": "object" },
        "items": { "type": "string" },
        "format": { "type": "string" }
      }
    }
  }
}
```

---

## Decision Tree: Which Language for Which Use Case

```
START: What is your MCP server's primary use case?
│
├─► Rapid prototyping / AI-heavy tooling
│   └─► Python (FastMCP) — fastest time-to-working-server
│
├─► Web ecosystem / frontend tooling / VS Code extension
│   └─► TypeScript — native MCP SDK, npm ecosystem
│
├─► Enterprise / existing Java infrastructure
│   ├─► Kotlin preferred? → Kotlin (coroutines + DSL)
│   └─► Java (Spring Boot — enterprise patterns, annotation-driven)
│
├─► Maximum performance / systems tooling
│   ├─► Memory safety required? → Rust (zero-cost abstractions)
│   └─► Go (simplicity + goroutines, fast compilation)
│
├─► .NET ecosystem / Windows-first
│   └─► C# (DI-first, async Task, source generators)
│
├─► Apple ecosystem / iOS/macOS tooling
│   └─► Swift (actors, structured concurrency)
│
├─► Scripting / DevOps automation
│   └─► Ruby (convention-over-configuration, expressive DSL)
│
├─► Web hosting / shared infrastructure
│   └─► PHP (Composer, Laravel patterns, wide hosting support)
│
└─► Multi-language monorepo / polyglot team
    └─► Use FORGE-POLYGLOT-MCP: define once, generate for each team's language
```

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════════╗
║                    FORGE-POLYGLOT-MCP                               ║
║               Universal MCP Genesis Engine                          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  WORKFLOW:                                                          ║
║    1. Write Universal Tool Spec (JSON)                              ║
║    2. Choose target language(s)                                     ║
║    3. Genesis Engine generates full project                         ║
║    4. Build, test, deploy                                           ║
║                                                                     ║
║  COMMANDS:                                                          ║
║    "Generate MCP server in Python for [spec]"                       ║
║    "Convert this TypeScript MCP server to Go"                       ║
║    "Create Universal Tool Spec from this description"               ║
║    "Generate MCP server in all 10 languages"                        ║
║    "What's the best language for [use case]?"                       ║
║                                                                     ║
║  MODULES:                                                           ║
║    PM1  Universal Tool Spec       — Define once                     ║
║    PM2  Language Idiom Engine     — Native feel                     ║
║    PM3  Type System Translator    — Faithful mapping                ║
║    PM4  Async/Concurrency Mapper  — Native concurrency              ║
║    PM5  Package/Build Synthesizer — Ready to build                  ║
║    PM6  Testing Scaffold          — Tests included                  ║
║    PM7  Error Handling Harmonizer — Idiomatic errors                ║
║    PM8  Deployment Adapter        — Run anywhere                    ║
║                                                                     ║
║  SUPPORTED LANGUAGES:                                               ║
║    Python │ TypeScript │ Java │ Go │ Rust                           ║
║    Kotlin │ C#         │ Ruby │ Swift │ PHP                         ║
║                                                                     ║
║  FORGE CLASS: cross-domain-innovation (Ω-Δ99)                      ║
║  FUSED SKILLS: 10                                                   ║
║  EMERGENT: Cross-language MCP synthesis                             ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

_Forged by FORGE-POLYGLOT-MCP • andrew-pigors + copilot-omega-delta-99 • 2026-07-17_
_One spec. Ten languages. Zero compromise._
