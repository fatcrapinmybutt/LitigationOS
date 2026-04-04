---
description: "Engine and brain development safety rules. Stdout contamination prevention, import safety, module-level side effects. Apply when writing or modifying engine/brain Python files."
applyTo: "00_SYSTEM/engines/**/*.py,00_SYSTEM/brains/**/*.py"
---

# Engine & Brain Development Rules

Safety rules learned from debugging 35 engine files with stdout contamination, import crashes, and module-level side effects.

## No Stdout Clobbering (CRITICAL — 35 files fixed in cf1f4fad8)

**NEVER** use `sys.stdout = open(...)` or `sys.stdout.reconfigure()` at module level.

These patterns corrupt stdout for ALL importers — including MCP servers, test harnesses, and the Copilot CLI runtime. When an engine module is imported (not executed), module-level stdout changes propagate to the importing process, causing silent data corruption or encoding crashes.

### Banned Patterns

```python
# BANNED — module-level stdout replacement
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# BANNED — module-level reconfigure
sys.stdout.reconfigure(encoding='utf-8')
```

### Safe Patterns

```python
# SAFE — inside __main__ guard with try/except
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass  # Not a real terminal (MCP, pipe, etc.)

# SAFE — explicit output encoding where needed
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(result)

# SAFE — PYTHONUTF8=1 environment variable (set externally)
```

### Why This Matters

The MCP server imports engine modules to register tools. When an engine clobbers stdout at import time, the MCP JSON-RPC protocol breaks because its stdout is no longer the expected pipe. This caused cascading failures across 8+ engine modules until the fix in commit cf1f4fad8.

## No Module-Level Side Effects

Engine modules must be safe to import without triggering:
- Database connections (use lazy initialization)
- File I/O (use factory functions)
- Network requests (use dependency injection)
- Process spawning (use explicit init methods)

```python
# WRONG — connects on import
class Engine:
    conn = sqlite3.connect("litigation_context.db")  # fires at import

# RIGHT — lazy connection
class Engine:
    def __init__(self):
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = get_db("litigation_context")
        return self._conn
```

## Import from shared Module

All engines MUST import database access, FTS5 sanitization, and configuration from the shared module:

```python
from shared import get_db, sanitize_fts5, config, get_db_path
```

Never import `sqlite3` directly for database connections — `get_db()` handles PRAGMAs, WAL mode, busy_timeout, and filesystem-aware journal mode selection automatically.

## Engine Registration

Every engine directory should have an `__init__.py` that:
1. Exports the primary class/function
2. Declares `__version__`
3. Does NOT perform any initialization at import time

```python
# 00_SYSTEM/engines/myengine/__init__.py
"""MyEngine — brief description."""
__version__ = "1.0.0"
from .engine import MyEngine  # lazy, no side effects
```

## Error Handling

Engine functions must never crash silently. Use structured error reporting:
```python
import logging
logger = logging.getLogger(__name__)

def process(data):
    try:
        result = _do_work(data)
    except sqlite3.OperationalError as e:
        logger.error("DB error in %s: %s", __name__, e)
        raise
    except Exception as e:
        logger.error("Unexpected error in %s: %s", __name__, e)
        raise
```
