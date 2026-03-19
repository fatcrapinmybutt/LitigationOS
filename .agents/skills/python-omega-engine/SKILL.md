---
name: python-omega-engine
description: "Use when writing, reviewing, or refactoring any Python code in LitigationOS — covers Python 3.12+, async/await, performance optimization, testing, error handling, design patterns, type safety, resilience, Pydantic v2, FastAPI, packaging, observability, background jobs, resource management, configuration, and anti-patterns."
category: discipline
version: "2.0.0"
triggers:
  - python
  - script
  - pip
  - pytest
  - fastapi
  - pydantic
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: "Pigors v Watson"
dependencies: []
metadata:
  model: opus
  forged_from: 20
  forge_date: 2026-03-12
---

# PYTHON-OMEGA-ENGINE — The Ultimate Python Mastery Skill

> Forged from 20 individual Python skills into one supreme composite.
> Sources: python-pro, python-testing-patterns, python-performance-optimization, python-error-handling, python-design-patterns, python-background-jobs, python-resilience, python-type-safety, python-patterns, python-anti-patterns, python-code-style, python-resource-management, python-project-structure, python-packaging, python-observability, pydantic-models-py, fastapi-pro, async-python-patterns, python-configuration, python-executor.

## When to Apply

Activate this skill for ANY Python work:
- Writing, reviewing, or refactoring Python 3.12+ code
- Designing APIs, services, CLI tools, or data pipelines
- Implementing async workflows, background jobs, or concurrent systems
- Adding tests, error handling, logging, or monitoring
- Configuring projects, packaging for distribution, or setting up CI/CD
- Performance profiling, memory optimization, or algorithmic tuning
- Working with FastAPI, Pydantic, SQLAlchemy, Celery, or the modern Python ecosystem

---

## Decision Tree

```
ENTRY: Python task received
│
├─ Q1: What type of Python work?
│   ├─ New code / feature → BRANCH A
│   ├─ Bug fix / debug → BRANCH B
│   ├─ Performance optimization → BRANCH C
│   ├─ Testing → BRANCH D
│   └─ Packaging / CI/CD → BRANCH E
│
├─ BRANCH A: New Code
│   ├─ Step 1: Verify CWD is NOT repo root (shadow modules!)
│   ├─ Step 2: Set UTF-8 encoding (sys.stdout + file I/O)
│   ├─ Step 3: Use Python 3.12+ features (match, type, union syntax)
│   ├─ Step 4: Add type hints (pyright/mypy compatible)
│   ├─ Step 5: Implement error handling (7-layer protocol if agent code)
│   ├─ Step 6: Write tests (pytest, fixtures, parametrize)
│   └─ OUTPUT: Type-safe, tested Python module
│
├─ BRANCH B: Bug Fix
│   ├─ Step 1: Check for shadow module interference first
│   ├─ Step 2: Verify encoding (cp1252 vs UTF-8 on Windows)
│   ├─ Step 3: Check DB connection PRAGMAs (busy_timeout, WAL)
│   ├─ Step 4: Reproduce, fix, add regression test
│   └─ OUTPUT: Fix with regression test
│
├─ BRANCH C: Performance
│   ├─ Step 1: Profile with cProfile or line_profiler
│   ├─ Step 2: Check DB queries (SELECT *, missing indexes, LIKE vs FTS5)
│   ├─ Step 3: Check for executemany vs execute-in-loop
│   ├─ Step 4: Optimize and benchmark
│   └─ OUTPUT: Optimized code with before/after metrics
│
├─ BRANCH D: Testing
│   ├─ Step 1: Use pytest (not unittest)
│   ├─ Step 2: Fixtures for DB setup/teardown
│   ├─ Step 3: Parametrize for edge cases
│   ├─ Step 4: Coverage target: 80%+
│   └─ OUTPUT: Test suite with coverage report
│
└─ BRANCH E: Packaging
    ├─ Step 1: pyproject.toml (not setup.py)
    ├─ Step 2: Use uv for dependency management
    ├─ Step 3: Ruff for lint + format
    └─ OUTPUT: Pip-installable package
```

## Output Contract

```yaml
output:
  type: enum [code, config, analysis]
  format: python_code_or_markdown
  required_fields:
    - summary: string           # What was implemented/fixed
    - files_changed: list[str]  # All files created or modified
    - quality_score: float      # 0.0-1.0 self-assessment
  quality_gates:
    - syntax_valid: boolean          # AST parses without error
    - no_shadow_imports: boolean     # CWD not repo root, no shadow conflicts
    - type_hints_present: boolean    # All public functions have type annotations
    - encoding_safe: boolean         # UTF-8 explicit on all file I/O
    - tests_pass: boolean            # pytest returns 0 exit code
    - db_pragmas_set: boolean        # WAL + busy_timeout on all DB connections
```

---

## §1. Modern Python 3.12+ Features

### Structural Pattern Matching

```python
def handle_response(response: dict) -> str:
    match response:
        case {"status": 200, "data": data}:
            return f"Success: {data}"
        case {"status": 404}:
            return "Not found"
        case {"status": status} if 400 <= status < 500:
            return f"Client error: {status}"
        case {"status": status} if status >= 500:
            return f"Server error: {status}"
        case _:
            return "Unknown response"
```

### Modern Union Syntax (3.10+)

```python
# Preferred
def find_user(user_id: str) -> User | None: ...
def parse_value(v: str) -> int | float | str: ...

# Older style (for 3.9 compat)
from typing import Optional, Union
def find_user(user_id: str) -> Optional[User]: ...
```

### Type Statement (3.12+)

```python
type UserId = str
type Handler[T] = Callable[[Request], T]
type AsyncHandler[T] = Callable[[Request], Awaitable[T]]
```

### Modern Tooling Ecosystem

| Tool | Purpose | Replaces |
|------|---------|----------|
| **uv** | Package management (fastest) | pip, pipenv |
| **ruff** | Lint + format (single tool) | black, isort, flake8 |
| **pyright/mypy** | Static type checking | — |
| **pyproject.toml** | Project configuration | setup.py, setup.cfg |

---

## §2. Async & Concurrency Mastery

### Decision Guide

```
I/O-bound (network, DB, file) → async/await
CPU-bound (computation)       → multiprocessing / process pool
Mixed                         → asyncio.to_thread() for CPU in async context
Simple scripts, few connections → sync (simpler, easier to debug)
```

**Key Rule:** Stay fully sync or fully async within a call path. Mixing creates hidden blocking.

### Concurrent Execution with gather()

```python
import asyncio

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.5)
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_all_users(user_ids: list[int]) -> list[dict]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

### Task Groups (3.11+ Structured Concurrency)

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_user(1))
        task2 = tg.create_task(fetch_user(2))
    # Both complete or both cancelled on error
    print(task1.result(), task2.result())
```

### Rate Limiting with Semaphore

```python
async def api_call(url: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

async def rate_limited_requests(urls: list[str], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = [api_call(url, semaphore) for url in urls]
    return await asyncio.gather(*tasks)
```

### Producer-Consumer Pattern

```python
async def producer(queue: asyncio.Queue, items: list[str]):
    for item in items:
        await queue.put(item)
    await queue.put(None)  # Sentinel

async def consumer(queue: asyncio.Queue, worker_id: int):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        await process(item)
        queue.task_done()
```

### Wrapping Blocking Code

```python
# Python 3.9+ — offload sync code to thread pool
async def read_file_async(path: str) -> str:
    return await asyncio.to_thread(Path(path).read_text)

# Lower-level approach
async def run_blocking(data):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, blocking_function, data)
```

### Async Library Selection

| Need | Library |
|------|---------|
| HTTP client | `httpx` (async + sync) |
| PostgreSQL | `asyncpg` |
| Redis | `redis-py` (async mode) |
| File I/O | `aiofiles` |
| ORM | SQLAlchemy 2.0 async |

### ❌ DON'T: Block the Event Loop

```python
# BAD — blocks everything
async def bad():
    time.sleep(1)           # Blocks!
    requests.get(url)       # Also blocks!

# GOOD — async-native
async def good():
    await asyncio.sleep(1)
    async with httpx.AsyncClient() as client:
        await client.get(url)
```

---

## §3. Performance Engineering

### Profile BEFORE Optimizing

```python
# cProfile — CPU profiling
import cProfile, pstats
profiler = cProfile.Profile()
profiler.enable()
main()
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(10)

# line_profiler — line-by-line
# kernprof -l -v script.py

# memory_profiler — memory usage
# python -m memory_profiler script.py

# py-spy — production profiling (no code changes)
# py-spy record -o profile.svg -- python script.py
```

### Critical Optimizations

**List comprehensions > loops:**
```python
# 2-3x faster than append loop
squares = [i**2 for i in range(n)]
```

**Generators for memory efficiency:**
```python
# Constant memory regardless of size
total = sum(i**2 for i in range(10_000_000))
```

**String join > concatenation:**
```python
# O(n) vs O(n²)
result = "".join(str(item) for item in items)
```

**Dict/Set for lookups:**
```python
# O(1) vs O(n) for lists
lookup = {item.id: item for item in items}
found = item_id in lookup
```

**`lru_cache` for expensive computations:**
```python
from functools import lru_cache

@lru_cache(maxsize=256)
def expensive_calculation(n: int) -> int:
    return sum(i**2 for i in range(n))
```

**`__slots__` for memory-heavy classes:**
```python
class Point:
    __slots__ = ['x', 'y', 'z']
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
```

**NumPy for numerical operations:**
```python
import numpy as np
# 10-100x faster than pure Python loops
result = np.arange(1_000_000).sum()
```

**Batch database operations:**
```python
# 10-100x faster than row-by-row
rows = [(item.name, item.value) for item in items]
cursor.executemany("INSERT INTO t (name, value) VALUES (?, ?)", rows)
conn.commit()
```

**Multiprocessing for CPU-bound:**
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(cpu_intensive_fn, data_chunks))
```

### Memory Leak Detection

```python
import tracemalloc
tracemalloc.start()
snapshot1 = tracemalloc.take_snapshot()
# ... run code ...
snapshot2 = tracemalloc.take_snapshot()
for stat in snapshot2.compare_to(snapshot1, 'lineno')[:10]:
    print(stat)
```

---

## §4. Type System & Validation

### Annotate All Public Signatures

```python
def process_batch(
    items: list[Item],
    max_workers: int = 4,
) -> BatchResult[ProcessedItem]:
    ...

class UserRepository:
    async def find_by_id(self, user_id: str) -> User | None: ...
    async def save(self, user: User) -> User: ...
```

### Generics

```python
from typing import TypeVar, Generic

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

class Result(Generic[T, E]):
    def __init__(self, value: T | None = None, error: E | None = None) -> None:
        self._value = value
        self._error = error

    def unwrap(self) -> T:
        if self._error is not None:
            raise self._error
        return self._value  # type: ignore
```

### Protocols (Structural Typing)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, data: dict) -> "Serializable": ...

# Any class with to_dict/from_dict satisfies this — no inheritance needed
def serialize(obj: Serializable) -> str:
    return json.dumps(obj.to_dict())
```

### TypeVar with Bounds

```python
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)

def validate_and_create(model_cls: type[ModelT], data: dict) -> ModelT:
    return model_cls.model_validate(data)
```

### Pydantic v2 Models

```python
from pydantic import BaseModel, Field, field_validator

class CreateUserInput(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()
```

### Multi-Model Pattern (API Contracts)

| Model | Purpose |
|-------|---------|
| `Base` | Common fields shared across models |
| `Create` | Request body for creation (required fields) |
| `Update` | Request body for updates (all optional) |
| `Response` | API response with all fields |
| `InDB` | Database document with `doc_type` |

### Strict Type Checking Config

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

---

## §5. Testing Excellence

### AAA Pattern

```python
def test_create_user_assigns_id():
    # Arrange
    data = {"email": "test@example.com", "name": "Test"}
    # Act
    user = service.create_user(data)
    # Assert
    assert user.id is not None
```

### Fixtures for Setup/Teardown

```python
@pytest.fixture
def db() -> Generator[Database, None, None]:
    database = Database("sqlite:///:memory:")
    database.connect()
    yield database
    database.disconnect()

@pytest.fixture(scope="session")
def app_config():
    return {"database_url": "sqlite:///:memory:", "debug": True}
```

### Parametrized Tests

```python
@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("invalid.email", False),
    ("@example.com", False),
    ("", False),
])
def test_email_validation(email, expected):
    assert is_valid_email(email) == expected
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_get_user_success():
    mock_response = Mock()
    mock_response.json.return_value = {"id": 1, "name": "John"}
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get:
        user = client.get_user(1)
        assert user["name"] == "John"
        mock_get.assert_called_once()
```

### Testing Exceptions

```python
def test_division_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(5, 0)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_fetch_data():
    result = await fetch_data("https://api.example.com")
    assert result is not None
```

### Property-Based Testing (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_reverse_twice_is_original(s):
    assert reverse_string(reverse_string(s)) == s

@given(st.lists(st.integers()))
def test_sorted_list_is_ordered(lst):
    sorted_lst = sorted(lst)
    for i in range(len(sorted_lst) - 1):
        assert sorted_lst[i] <= sorted_lst[i + 1]
```

### Testing Retry Behavior

```python
def test_retries_on_transient_error():
    client = Mock()
    client.request.side_effect = [
        ConnectionError("Failed"),
        ConnectionError("Failed"),
        {"status": "ok"},
    ]
    service = ServiceWithRetry(client, max_retries=3)
    result = service.fetch()
    assert result == {"status": "ok"}
    assert client.request.call_count == 3
```

### Time-Dependent Tests (freezegun)

```python
from freezegun import freeze_time

@freeze_time("2026-01-15 10:00:00")
def test_token_expiry():
    token = create_token(expires_in_seconds=3600)
    assert token.expires_at == datetime(2026, 1, 15, 11, 0, 0)
```

### Test Markers & Coverage

```python
@pytest.mark.slow
def test_slow_operation(): ...

@pytest.mark.integration
def test_database_integration(): ...

# Run: pytest --cov=myapp --cov-fail-under=80 tests/
```

### One Behavior Per Test

```python
# GOOD — focused, easy to diagnose
def test_create_user_assigns_id(): ...
def test_create_user_stores_email(): ...

# BAD — multiple behaviors, unclear failures
def test_user_service():
    user = create_user(data)
    assert user.id is not None
    assert user.email == data["email"]
    updated = update_user(user.id, {"name": "New"})
    assert updated.name == "New"
```

---

## §6. Error Handling & Resilience

### Fail Fast — Validate Early

```python
def process_order(order_id: str, quantity: int, discount: float) -> OrderResult:
    if not order_id:
        raise ValueError("'order_id' is required")
    if quantity <= 0:
        raise ValueError(f"'quantity' must be positive, got {quantity}")
    if not 0 <= discount <= 100:
        raise ValueError(f"'discount' must be 0-100, got {discount}")
    return _process_validated_order(order_id, quantity, discount)
```

### Exception Hierarchy

```python
class ApiError(Exception):
    def __init__(self, message: str, status_code: int, body: str | None = None):
        self.status_code = status_code
        self.response_body = body
        super().__init__(message)

class RateLimitError(ApiError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s", 429)
```

### Exception Chaining

```python
try:
    response = httpx.post(url, files={"file": f})
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    raise ServiceError(f"Upload failed: {e.response.status_code}") from e
```

### Batch Processing with Partial Failures

```python
@dataclass
class BatchResult[T]:
    succeeded: dict[int, T]
    failed: dict[int, Exception]

    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0

def process_batch(items: list[Item]) -> BatchResult[ProcessedItem]:
    succeeded, failed = {}, {}
    for idx, item in enumerate(items):
        try:
            succeeded[idx] = process_single_item(item)
        except Exception as e:
            failed[idx] = e
    return BatchResult(succeeded=succeeded, failed=failed)
```

### Retry with Tenacity

```python
from tenacity import (
    retry, stop_after_attempt, stop_after_delay,
    wait_exponential_jitter, retry_if_exception_type,
)

TRANSIENT_ERRORS = (ConnectionError, TimeoutError, OSError)

@retry(
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
    stop=stop_after_attempt(5) | stop_after_delay(60),
    wait=wait_exponential_jitter(initial=1, max=30),
)
def fetch_data(url: str) -> dict:
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

### Never Retry Permanent Errors

- `ValueError`, `TypeError` — bugs, not transient
- `AuthenticationError` — invalid credentials won't become valid
- HTTP 4xx (except 429) — client errors are permanent

### Circuit Breaker (Fail-Safe Defaults)

```python
from functools import wraps

def fail_safe(default, log_failure: bool = True):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_failure:
                    logger.warning("Using default", fn=func.__name__, error=str(e))
                return default
        return wrapper
    return decorator

@fail_safe(default=[])
async def get_recommendations(user_id: str) -> list[str]: ...
```

### Dead Letter Queue

```python
@app.task(bind=True, max_retries=3)
def process_webhook(self, webhook_id: str, payload: dict):
    try:
        send_webhook(payload)
    except Exception as e:
        if self.request.retries >= self.max_retries:
            dead_letter_queue.send({
                "task": "process_webhook",
                "payload": payload,
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat(),
            })
            return
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
```

---

## §7. Design Patterns

### KISS — Keep It Simple

```python
# Over-engineered factory? Just use a dict.
FORMATTERS = {"json": JsonFormatter, "csv": CsvFormatter, "xml": XmlFormatter}

def get_formatter(name: str) -> Formatter:
    if name not in FORMATTERS:
        raise ValueError(f"Unknown format: {name}")
    return FORMATTERS[name]()
```

### Separation of Concerns (Layered Architecture)

```
API Layer (handlers) → parse requests, format responses
         ↓
Service Layer (logic) → domain rules, orchestration, pure functions
         ↓
Repository Layer (data) → SQL, external APIs, caches
```

```python
class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def create_user(self, data: CreateUserInput) -> User:
        user = User(email=data.email, name=data.name)
        return await self._repo.save(user)
```

### Composition Over Inheritance

```python
class NotificationService:
    def __init__(self, email: EmailSender, sms: SmsSender | None = None):
        self._email = email
        self._sms = sms

    async def notify(self, user: User, message: str, channels: set[str] | None = None):
        channels = channels or {"email"}
        if "email" in channels:
            await self._email.send(user.email, message)
        if "sms" in channels and self._sms and user.phone:
            await self._sms.send(user.phone, message)
```

### Dependency Injection

```python
from typing import Protocol

class Cache(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...

class UserService:
    def __init__(self, repository: UserRepository, cache: Cache, logger: Logger):
        self._repo = repository
        self._cache = cache
        self._logger = logger

# Production
service = UserService(PostgresUserRepo(db), RedisCache(redis), StructlogLogger())
# Testing
service = UserService(InMemoryRepo(), FakeCache(), NullLogger())
```

### Rule of Three

Wait until you have three instances of similar code before abstracting. Duplication is often better than the wrong abstraction.

### Function Size

Keep functions focused. Extract when:
- Exceeds 20-50 lines
- Handles multiple unrelated responsibilities
- Has 3+ levels of nesting

---

## §8. Anti-Patterns & Code Smells

### Quick Review Checklist

| Anti-Pattern | Fix |
|-------------|-----|
| Scattered retry logic | Centralized decorators |
| Double retry (app + client) | Retry at ONE layer only |
| Hard-coded config/secrets | `pydantic-settings` + env vars |
| Exposed ORM models in API | DTO/response schemas |
| Mixed I/O + business logic | Repository pattern |
| Bare `except Exception: pass` | Catch specific exceptions, log |
| Batch stops on first error | `BatchResult` with successes/failures |
| No input validation | Validate at boundaries with Pydantic |
| Unclosed resources | Context managers (`with` / `async with`) |
| Blocking calls in async code | Async-native libraries |
| Missing type hints | Annotate all public APIs |
| Untyped collections (`list`) | `list[User]` with type parameters |
| Only happy path tests | Test errors + edge cases |
| Over-mocking | Integration tests for critical paths |
| Mutable default arguments | Use `None` + set inside function |

### ❌ Mutable Default Arguments

```python
# BAD — shared list across calls
def add_item(item, items=[]):
    items.append(item)
    return items

# GOOD
def add_item(item, items: list | None = None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### ❌ Bare Exception Handling

```python
# BAD
try:
    process()
except Exception:
    pass  # Bugs hidden forever

# GOOD
try:
    process()
except ConnectionError as e:
    logger.warning("Connection failed", error=str(e))
    raise
except ValueError as e:
    raise BadRequestError(str(e))
```

### Code Style (PEP 8 + ruff)

```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Naming Conventions

```python
# Files: snake_case — user_repository.py
# Classes: PascalCase — UserRepository
# Functions/vars: snake_case — get_user_by_email
# Constants: SCREAMING_SNAKE — MAX_RETRY_ATTEMPTS
# Imports: absolute — from myproject.services import UserService
```

### Google-Style Docstrings

```python
def process_batch(
    items: list[Item],
    max_workers: int = 4,
) -> BatchResult:
    """Process items concurrently using a worker pool.

    Args:
        items: The items to process. Must not be empty.
        max_workers: Maximum concurrent workers. Defaults to 4.

    Returns:
        BatchResult containing succeeded items and failures.

    Raises:
        ValueError: If items is empty.
    """
    ...
```

---

## §9. Resource Management

### Context Managers (Always)

```python
# File I/O
with open(path) as f:
    return f.read()

# Database connection
with DatabaseConnection(dsn) as db:
    result = db.execute(query)

# Async resources
async with AsyncDatabasePool(dsn) as pool:
    users = await pool.execute("SELECT * FROM users")
```

### Custom Context Manager (Decorator)

```python
from contextlib import contextmanager, asynccontextmanager

@contextmanager
def timed_block(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"{name} completed", duration_s=round(elapsed, 3))

@asynccontextmanager
async def database_transaction(conn):
    await conn.execute("BEGIN")
    try:
        yield conn
        await conn.execute("COMMIT")
    except Exception:
        await conn.execute("ROLLBACK")
        raise
```

### ExitStack for Dynamic Resources

```python
from contextlib import ExitStack, AsyncExitStack

def process_files(paths: list[Path]) -> list[str]:
    with ExitStack() as stack:
        files = [stack.enter_context(open(p)) for p in paths]
        return [f.read() for f in files]

async def process_connections(hosts: list[str]) -> list[dict]:
    async with AsyncExitStack() as stack:
        conns = [await stack.enter_async_context(connect(h)) for h in hosts]
        return [await c.fetch_data() for c in conns]
```

### Efficient String Accumulation

```python
# BAD — O(n²)
content = ""
for chunk in stream:
    content += chunk

# GOOD — O(n)
chunks: list[str] = []
for chunk in stream:
    chunks.append(chunk)
content = "".join(chunks)
```

---

## §10. Project Structure & Packaging

### Recommended Layout (src/)

```
my-package/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── core.py
│       ├── py.typed
│       ├── api/
│       ├── services/
│       ├── models/
│       └── config/
├── tests/
│   ├── conftest.py
│   ├── test_unit/
│   └── test_integration/
└── docs/
```

### Explicit Public APIs

```python
# mypackage/__init__.py
from .core import MainClass
from .exceptions import PackageError
__all__ = ["MainClass", "PackageError"]
__version__ = "1.0.0"
```

### pyproject.toml (Complete)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-package"
version = "1.0.0"
description = "Description"
readme = "README.md"
requires-python = ">=3.12"
license = {text = "MIT"}
authors = [{name = "Name", email = "email@example.com"}]
dependencies = ["httpx>=0.25", "pydantic>=2.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0", "ruff>=0.1", "mypy>=1.0"]

[project.scripts]
my-cli = "my_package.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=my_package --cov-report=term-missing"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
```

### CLI with Click

```python
import click

@click.group()
@click.version_option()
def cli():
    """My CLI tool."""

@cli.command()
@click.argument("name")
@click.option("--greeting", default="Hello")
def greet(name: str, greeting: str):
    click.echo(f"{greeting}, {name}!")

def main():
    cli()
```

### Building & Publishing

```bash
pip install build twine
python -m build                    # Creates dist/*.whl + *.tar.gz
twine check dist/*                 # Validate
twine upload --repository testpypi dist/*  # Test
twine upload dist/*                # Publish
```

### Dynamic Versioning (setuptools-scm)

```toml
[project]
dynamic = ["version"]

[tool.setuptools_scm]
write_to = "src/my_package/_version.py"
```

---

## §11. Configuration Management

### Typed Settings with pydantic-settings

```python
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
import sys

class Settings(BaseSettings):
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_password: str = Field(alias="DB_PASSWORD")  # Required — no default
    api_secret_key: str = Field(alias="API_SECRET_KEY")
    debug: bool = Field(default=False, alias="DEBUG")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

try:
    settings = Settings()
except ValidationError as e:
    print(f"Configuration error:\n{e}")
    sys.exit(1)
```

### Environment-Specific Config

```python
from enum import Enum

class Environment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    environment: Environment = Field(default=Environment.LOCAL, alias="ENVIRONMENT")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
```

### Nested Configuration

```python
class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str
    password: str

class Settings(BaseSettings):
    database: DatabaseSettings
    model_config = {"env_nested_delimiter": "__"}

# Env: DATABASE__HOST=db.example.com DATABASE__PASSWORD=secret
```

### Secrets from Files (Docker)

```python
class Settings(BaseSettings):
    db_password: str = Field(alias="DB_PASSWORD")
    model_config = {"secrets_dir": "/run/secrets"}
```

### Rules

1. **Never hardcode** config in source
2. **Fail fast** — crash on missing required config at startup
3. **Provide dev defaults** — make local dev easy
4. **Never commit .env** — add to .gitignore
5. **Singleton pattern** — `from myapp.config import settings` everywhere

---

## §12. Observability & Monitoring

### Structured Logging with structlog

```python
import structlog

def configure_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), log_level.upper())
        ),
    )

logger = structlog.get_logger()
logger.info("Order created", order_id=order.id, total=order.total)
```

### Semantic Log Levels

| Level | Use For |
|-------|---------|
| `DEBUG` | Internal state, variable values |
| `INFO` | Request lifecycle, job completion |
| `WARNING` | Retry attempts, fallback used, rate limit approaching |
| `ERROR` | Exceptions needing investigation |

**Wrong password = `INFO`, not `ERROR`.** Don't cry wolf.

### Correlation ID Propagation

```python
from contextvars import ContextVar
import uuid

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

# FastAPI middleware
async def correlation_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id.set(cid)
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response
```

### Four Golden Signals (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "Latency",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)
REQUEST_COUNT = Counter("http_requests_total", "Traffic", ["method", "endpoint", "status"])
ERROR_COUNT = Counter("http_errors_total", "Errors", ["method", "endpoint", "error_type"])
DB_POOL_USAGE = Gauge("db_connection_pool_used", "Saturation")
```

**Bounded cardinality:** Never use user IDs as metric labels — they explode storage.

### OpenTelemetry Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        with tracer.start_as_current_span("validate_order"):
            validate_order(order_id)
        with tracer.start_as_current_span("charge_payment"):
            charge_payment(order_id)
```

### Timed Operation Context Manager

```python
@contextmanager
def timed_operation(name: str, **fields):
    start = time.perf_counter()
    try:
        yield
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("Operation failed", operation=name, duration_ms=round(elapsed_ms, 2), error=str(e), **fields)
        raise
    else:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("Operation completed", operation=name, duration_ms=round(elapsed_ms, 2), **fields)
```

---

## §13. FastAPI Production Patterns

### App Structure

```python
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(title="My API", lifespan=lifespan)
```

### Dependency Injection

```python
from fastapi import Depends
from typing import Annotated

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return decode_and_validate(token)

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/users/me")
async def read_me(user: CurrentUser, db: DB) -> UserResponse:
    return UserResponse.from_orm(user)
```

### Response Models & Error Handling

```python
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: CreateUserInput, db: DB) -> UserResponse:
    user = await user_service.create(data)
    return UserResponse.from_orm(user)

@app.exception_handler(ServiceError)
async def service_error_handler(request, exc: ServiceError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": str(exc)},
    )
```

### Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/reports")
async def generate_report(request: ReportRequest, bg: BackgroundTasks):
    job_id = str(uuid4())
    bg.add_task(run_report_generation, job_id, request)
    return {"job_id": job_id, "poll_url": f"/jobs/{job_id}"}
```

### Middleware

```python
@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(round(elapsed, 4))
    return response
```

### Key Principles

- **Async-first** by default; sync def runs in thread pool automatically
- **Pydantic v2** for all request/response validation
- **Annotated dependencies** for clean injection
- **Lifespan events** for startup/shutdown
- **Never expose ORM models** — use response schemas

---

## §14. Background Jobs & Task Queues

### When to Use

- Operations > a few seconds
- Sending emails, notifications, webhooks
- Report generation, data exports
- Integrating with unreliable external services

### Selection Guide

| Solution | Best For |
|----------|----------|
| `BackgroundTasks` (FastAPI) | Simple, in-process, fire-and-forget |
| **Celery** | Distributed, complex workflows, mature |
| **Dramatiq** | Modern Celery alternative, simpler |
| **RQ** | Simple Redis-based queue |
| **ARQ** | Async, Redis-based |

### Celery Task Configuration

```python
from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379")
app.conf.update(
    task_time_limit=3600,
    task_soft_time_limit=3000,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

@app.task(bind=True, max_retries=3, autoretry_for=(ConnectionError, TimeoutError))
def process_payment(self, payment_id: str) -> dict:
    try:
        return payment_gateway.charge(payment_id)
    except TransientError as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
```

### Idempotency

```python
@app.task(bind=True)
def process_order(self, order_id: str):
    order = orders_repo.get(order_id)
    if order.status == OrderStatus.COMPLETED:
        return  # Already done

    payment_provider.charge(
        amount=order.total,
        idempotency_key=f"order-{order_id}",  # Critical!
    )
    orders_repo.update(order_id, status=OrderStatus.COMPLETED)
```

### Task Chaining (Celery)

```python
from celery import chain, group, chord

# Sequential: A → B → C
workflow = chain(extract.s(src), transform.s(), load.s(dest))

# Parallel: A, B, C at once
parallel = group(send_email.s(email), send_sms.s(phone), log_analytics.s(data))

# Fan-out then callback
workflow = chord([process_item.s(id) for id in ids], notify_complete.s(batch_id))
```

---

## §15. Quick Reference Cards

### Error Mapping

| Failure Type | Exception | When |
|---|---|---|
| Invalid input | `ValueError` | Bad parameter values |
| Wrong type | `TypeError` | Expected str, got int |
| Missing item | `KeyError` | Dict key not found |
| Operational failure | `RuntimeError` | Service unavailable |
| Timeout | `TimeoutError` | Operation too slow |
| Not found | `FileNotFoundError` | Path doesn't exist |
| Permission | `PermissionError` | Access denied |

### Import Organization

```python
# 1. Standard library
import os
from collections.abc import Callable

# 2. Third-party
import httpx
from pydantic import BaseModel

# 3. Local
from myproject.models import User
```

### Testing Pyramid

```
           /  E2E  \        Few, slow, high confidence
          / Integration \    Moderate count
         /  Unit Tests   \   Many, fast, focused
```

### Performance Cheat Sheet

| Technique | Speedup | Use When |
|-----------|---------|----------|
| List comprehension | 2-3x | Replacing append loops |
| `dict` lookup | 100x+ | Replacing `in list` |
| `lru_cache` | ∞ | Repeated expensive calls |
| `__slots__` | 30-50% memory | Many instances |
| NumPy vectorize | 10-100x | Numerical loops |
| `executemany` | 10-100x | Batch DB inserts |
| Generator expr | ~0 memory | Large datasets |
| `asyncio.gather` | N× for I/O | Concurrent network calls |

### Pre-Submit Checklist

- [ ] All public functions have type annotations
- [ ] All public functions have docstrings
- [ ] No bare `except Exception: pass`
- [ ] No hardcoded secrets or config
- [ ] Resources use context managers
- [ ] No blocking calls in async code
- [ ] Tests cover error paths
- [ ] Batch operations handle partial failures
- [ ] ruff check + mypy pass
- [ ] Coverage ≥80% on changed code
