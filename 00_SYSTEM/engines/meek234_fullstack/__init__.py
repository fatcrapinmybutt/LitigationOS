"""
MEEK234 Fullstack — End-to-end filing stack builder.

Assembles complete filing packages (motion + brief + exhibits +
certificate of service) from catalog-driven specifications.
Tracks runs via RUN_LEDGER.jsonl and validates against MANIFEST.json.

Key resources:
    catalogs/       — Filing catalog definitions
    schema/         — Validation schemas for filing stacks
    parsed/         — Pre-parsed filing components
    tests/          — Smoke tests and integration tests
    MANIFEST.json   — Package manifest with file inventory
"""

__all__ = []
