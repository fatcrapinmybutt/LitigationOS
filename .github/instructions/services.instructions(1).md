---
applyTo: "services/**/*.py,services/**/*.md"
---

# Service instructions (Control Plane API)

- Endpoints must be safe by default (no path traversal; safe subtrees only).
- All endpoints must fail closed when not configured.
- Never expose verbatim court-form instruction text in API responses; serve only pointers/hashes.
- Any job trigger must enqueue into jobs table; worker executes.
