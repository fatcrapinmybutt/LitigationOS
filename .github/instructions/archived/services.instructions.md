---
applyTo: "00_SYSTEM/**/*.py,07_CODE/**/*.py,scripts/**/*.py"
excludeAgent: "code-review"
---

# Service & Script Instructions (LitigationOS Python Code)

- Import from `00_SYSTEM/shared/` for DB access, FTS5 sanitization, and config.
- All scripts must support `--help` and return non-zero on failure.
- Never expose verbatim court-form instruction text in API responses; serve only pointers/hashes.
- Any job trigger must enqueue into jobs table; worker executes.
- Always set PRAGMA journal_mode=WAL, cache_size=-50000, mmap_size=268435456 at connection time.
- Never delete source evidence files; append-only new versions.
- FTS5 queries: `re.sub(r'[^\w\s*"]', ' ', query)` before MATCH. Fallback: LIKE.
