"""
Skill Cross-Reference & Capability Index
=========================================
Scans all SKILL.md files across .agents/skills and .claude/skills,
extracts metadata from YAML frontmatter, and builds a SQLite FTS5
index for fast skill discovery by trigger keyword.

Usage:
    python skill_crossref_index.py              # full scan + summary
    python skill_crossref_index.py --query PPO  # search for skills
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SKILL_ROOTS: list[Path] = [
    Path(os.path.expanduser("~")) / ".agents" / "skills",
    Path(os.path.expanduser("~")) / ".claude" / "skills",
]

DB_PATH = Path(__file__).resolve().parent / "skill_index.db"

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SkillRecord:
    name: str
    path: str
    tier: str = "standard"
    category: str = "uncategorized"
    trigger_text: str = ""
    fuses_text: str = ""


# ---------------------------------------------------------------------------
# YAML-lite frontmatter parser (no pyyaml dependency)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"\A\s*---[ \t]*\r?\n(.*?\r?\n)---[ \t]*\r?\n",
    re.DOTALL,
)


def _extract_frontmatter(text: str) -> str:
    """Return raw YAML block between the first pair of --- delimiters."""
    m = _FRONTMATTER_RE.match(text)
    return m.group(1) if m else ""


def _scalar(raw: str) -> str:
    """Strip surrounding quotes and whitespace from a YAML scalar value."""
    raw = raw.strip()
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        raw = raw[1:-1]
    return raw.strip()


def _parse_yaml_flat(yaml_text: str) -> dict:
    """
    Parse *simple* YAML into a flat dict.  Handles:
      - top-level scalars            key: value
      - folded/literal blocks        key: >-  / key: |
      - nested one-level metadata    metadata:\\n  sub: val
      - inline JSON                  metadata: {"a": "b"}
    Does NOT handle arbitrary nesting — good enough for SKILL.md frontmatter.
    """
    result: dict = {}
    metadata: dict = {}
    lines = yaml_text.splitlines()
    i = 0
    in_metadata_block = False
    current_key: Optional[str] = None
    current_buf: list[str] = []

    def _flush():
        nonlocal current_key, current_buf
        if current_key and current_buf:
            result[current_key] = " ".join(current_buf).strip()
        current_key = None
        current_buf = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines / comments
        if not stripped or stripped.startswith("#"):
            if current_key and current_buf:
                # blank line may end a folded block
                pass
            i += 1
            continue

        indent = len(line) - len(line.lstrip())

        # Continuation of a folded/literal block
        if current_key and indent > 0 and not re.match(r"^[A-Za-z_][\w-]*\s*:", stripped):
            current_buf.append(stripped)
            i += 1
            continue
        else:
            _flush()

        # Detect a top-level key
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)", line)
        if m:
            in_metadata_block = False
            key = m.group(1).lower().replace("-", "_")
            val = m.group(2).strip()

            if key == "metadata":
                in_metadata_block = True
                # inline JSON?
                if val.startswith("{"):
                    try:
                        metadata = json.loads(val)
                    except (json.JSONDecodeError, ValueError):
                        pass
                    in_metadata_block = False
                i += 1
                continue

            # Folded / literal block scalar
            if val in (">-", ">", "|", "|-"):
                current_key = key
                current_buf = []
                i += 1
                continue

            result[key] = _scalar(val)
            i += 1
            continue

        # Inside metadata block — indented sub-keys
        if in_metadata_block and indent >= 2:
            m_sub = re.match(r"^\s+([A-Za-z_][\w-]*)\s*:\s*(.*)", line)
            if m_sub:
                sub_key = m_sub.group(1).lower().replace("-", "_")
                sub_val = m_sub.group(2).strip()
                # Handle multi-line folded inside metadata
                if sub_val in (">-", ">", "|", "|-"):
                    buf: list[str] = []
                    i += 1
                    while i < len(lines):
                        nxt = lines[i]
                        nxt_indent = len(nxt) - len(nxt.lstrip())
                        if nxt.strip() and nxt_indent >= 4:
                            buf.append(nxt.strip())
                            i += 1
                        else:
                            break
                    metadata[sub_key] = " ".join(buf).strip()
                    continue
                metadata[sub_key] = _scalar(sub_val)
            i += 1
            continue

        i += 1

    _flush()

    # Merge metadata sub-keys into result under "metadata." prefix
    for k, v in metadata.items():
        result[f"metadata.{k}"] = str(v)

    return result


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

def _extract_triggers_from_description(desc: str) -> str:
    """Pull trigger keywords that appear after 'Triggers:' in the description."""
    m = re.search(r"[Tt]riggers?:\s*(.+?)(?:\.|$)", desc, re.DOTALL)
    if m:
        return m.group(1).strip().rstrip(".")
    # Also look for "Use when:" pattern
    m2 = re.search(r"[Uu]se\s+when:\s*(.+?)(?:\.|$)", desc, re.DOTALL)
    if m2:
        return m2.group(1).strip().rstrip(".")
    return ""


def parse_skill_md(filepath: Path) -> Optional[SkillRecord]:
    """Parse a single SKILL.md and return a SkillRecord (or None on failure)."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fm = _extract_frontmatter(text)
    if not fm:
        return None

    try:
        data = _parse_yaml_flat(fm)
    except Exception:
        return None

    # --- name ---
    name = data.get("name", "")
    if not name:
        # Fallback: folder name
        name = filepath.parent.name
    name = name.strip()

    # --- tier ---
    tier = (
        data.get("metadata.tier")
        or data.get("tier")
        or "standard"
    )

    # --- category ---
    category = (
        data.get("metadata.category")
        or data.get("category")
        or "uncategorized"
    )

    # --- triggers ---
    triggers = data.get("metadata.triggers") or data.get("triggers") or ""
    desc = data.get("description", "")
    if not triggers and desc:
        triggers = _extract_triggers_from_description(desc)
    # If still empty, use description keywords as fallback
    if not triggers and desc:
        triggers = desc[:300]

    # --- fuses / fused_skills / forged_from ---
    fuses_parts: list[str] = []
    for key in ("metadata.fused_skills", "metadata.forged_from", "fused_skills", "forged_from"):
        val = data.get(key)
        if val:
            fuses_parts.append(f"{key.split('.')[-1]}={val}")
    fuses_text = "; ".join(fuses_parts)

    return SkillRecord(
        name=name,
        path=str(filepath),
        tier=str(tier),
        category=str(category),
        trigger_text=triggers,
        fuses_text=fuses_text,
    )


# ---------------------------------------------------------------------------
# Directory scanner
# ---------------------------------------------------------------------------

def discover_skill_files(roots: list[Path] | None = None) -> list[Path]:
    """Walk each root and collect every SKILL.md found one level deep."""
    roots = roots or SKILL_ROOTS
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for entry in sorted(root.iterdir()):
                if entry.is_dir():
                    skill_file = entry / "SKILL.md"
                    if skill_file.is_file():
                        found.append(skill_file)
        except OSError as exc:
            print(f"  [WARN] Cannot read {root}: {exc}", file=sys.stderr)
    return found


# ---------------------------------------------------------------------------
# SQLite database builder
# ---------------------------------------------------------------------------

_SCHEMA_DDL = textwrap.dedent("""\
    CREATE TABLE IF NOT EXISTS skills (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        path        TEXT    NOT NULL UNIQUE,
        tier        TEXT    NOT NULL DEFAULT 'standard',
        category    TEXT    NOT NULL DEFAULT 'uncategorized',
        trigger_text TEXT   NOT NULL DEFAULT '',
        fuses_text  TEXT    NOT NULL DEFAULT '',
        created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
    );

    -- FTS5 virtual table for fast keyword search
    CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
        name,
        trigger_text,
        category,
        content='skills',
        content_rowid='id',
        tokenize='porter unicode61'
    );

    -- Triggers to keep FTS in sync
    CREATE TRIGGER IF NOT EXISTS skills_ai AFTER INSERT ON skills BEGIN
        INSERT INTO skills_fts(rowid, name, trigger_text, category)
        VALUES (new.id, new.name, new.trigger_text, new.category);
    END;

    CREATE TRIGGER IF NOT EXISTS skills_ad AFTER DELETE ON skills BEGIN
        INSERT INTO skills_fts(skills_fts, rowid, name, trigger_text, category)
        VALUES ('delete', old.id, old.name, old.trigger_text, old.category);
    END;

    CREATE TRIGGER IF NOT EXISTS skills_au AFTER UPDATE ON skills BEGIN
        INSERT INTO skills_fts(skills_fts, rowid, name, trigger_text, category)
        VALUES ('delete', old.id, old.name, old.trigger_text, old.category);
        INSERT INTO skills_fts(rowid, name, trigger_text, category)
        VALUES (new.id, new.name, new.trigger_text, new.category);
    END;
""")


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create (or open) the skill index database and ensure schema exists."""
    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA_DDL)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def index_skills(
    conn: sqlite3.Connection,
    records: list[SkillRecord],
    *,
    replace: bool = True,
) -> Tuple[int, int]:
    """
    Upsert skill records into the database.
    Returns (inserted, updated) counts.
    """
    inserted = updated = 0
    for rec in records:
        existing = conn.execute(
            "SELECT id FROM skills WHERE path = ?", (rec.path,)
        ).fetchone()

        if existing:
            if replace:
                conn.execute(
                    """UPDATE skills
                       SET name=?, tier=?, category=?, trigger_text=?, fuses_text=?,
                           created_at=datetime('now')
                     WHERE path=?""",
                    (rec.name, rec.tier, rec.category, rec.trigger_text,
                     rec.fuses_text, rec.path),
                )
                updated += 1
        else:
            conn.execute(
                """INSERT INTO skills (name, path, tier, category, trigger_text, fuses_text)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (rec.name, rec.path, rec.tier, rec.category, rec.trigger_text,
                 rec.fuses_text),
            )
            inserted += 1

    conn.commit()
    return inserted, updated


# ---------------------------------------------------------------------------
# Query API
# ---------------------------------------------------------------------------

def find_skills(
    query: str,
    *,
    db_path: Path | None = None,
    limit: int = 20,
) -> list[dict]:
    """
    FTS5 search for skills matching *query*.
    Returns list of dicts with id, name, tier, category, trigger_text, rank.
    """
    db_path = db_path or DB_PATH
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row

    # Sanitise query for FTS5 — wrap each token in quotes to avoid syntax errors
    tokens = re.findall(r"[\w][\w.-]*", query)
    if not tokens:
        return []
    fts_query = " OR ".join(f'"{t}"' for t in tokens)

    try:
        rows = conn.execute(
            """SELECT s.id, s.name, s.tier, s.category, s.trigger_text,
                      s.fuses_text, s.path, rank
                 FROM skills_fts f
                 JOIN skills s ON s.id = f.rowid
                WHERE skills_fts MATCH ?
                ORDER BY rank
                LIMIT ?""",
            (fts_query, limit),
        ).fetchall()
    except Exception:
        # FTS5 fallback: use LIKE query (Rule 15)
        like_terms = [f"%{t}%" for t in tokens]
        where_clauses = " OR ".join(
            f"(s.name LIKE ? OR s.trigger_text LIKE ? OR s.fuses_text LIKE ?)"
            for _ in tokens
        )
        params = []
        for t in like_terms:
            params.extend([t, t, t])
        params.append(limit)
        rows = conn.execute(
            f"""SELECT s.id, s.name, s.tier, s.category, s.trigger_text,
                       s.fuses_text, s.path, 0 as rank
                  FROM skills s
                 WHERE {where_clauses}
                 LIMIT ?""",
            params,
        ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_stats(conn: sqlite3.Connection) -> dict:
    """Return summary statistics from the skills table."""
    total = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]

    tier_rows = conn.execute(
        "SELECT tier, COUNT(*) as cnt FROM skills GROUP BY tier ORDER BY cnt DESC"
    ).fetchall()

    cat_rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM skills GROUP BY category ORDER BY cnt DESC"
    ).fetchall()

    return {
        "total": total,
        "per_tier": {r[0]: r[1] for r in tier_rows},
        "per_category": {r[0]: r[1] for r in cat_rows},
    }


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------

def _print_table(headers: list[str], rows: list[list[str]], widths: list[int]):
    """Minimal ASCII table printer."""
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        truncated = [
            col[:w] if len(col) > w else col for col, w in zip(row, widths)
        ]
        print(fmt.format(*truncated))


def main():
    t0 = time.perf_counter()
    print("=" * 70)
    print("  Skill Cross-Reference & Capability Index")
    print("=" * 70)

    # --- Query mode ---
    if "--query" in sys.argv:
        idx = sys.argv.index("--query")
        q = " ".join(sys.argv[idx + 1:]) if idx + 1 < len(sys.argv) else ""
        if not q:
            print("Usage: --query <search terms>")
            sys.exit(1)
        results = find_skills(q)
        if not results:
            print(f"No skills found for: {q}")
            sys.exit(0)
        print(f"\n  Results for '{q}' ({len(results)} matches):\n")
        _print_table(
            ["#", "Name", "Tier", "Category"],
            [
                [str(i + 1), r["name"], r["tier"], r["category"]]
                for i, r in enumerate(results)
            ],
            [4, 40, 22, 22],
        )
        sys.exit(0)

    # --- Full scan + index ---
    print(f"\n  Scanning skill directories...")
    for root in SKILL_ROOTS:
        status = "OK" if root.is_dir() else "NOT FOUND"
        print(f"    {root}  [{status}]")

    files = discover_skill_files()
    print(f"  Discovered {len(files)} SKILL.md files\n")

    if not files:
        print("  [WARN] No SKILL.md files found. Nothing to index.")
        sys.exit(0)

    # Parse
    records: list[SkillRecord] = []
    errors = 0
    for f in files:
        rec = parse_skill_md(f)
        if rec:
            records.append(rec)
        else:
            errors += 1

    print(f"  Parsed: {len(records)} OK, {errors} errors")

    # Index
    conn = init_db()
    inserted, updated = index_skills(conn, records)
    print(f"  Indexed: {inserted} new, {updated} updated")

    # Stats
    stats = get_stats(conn)
    elapsed = time.perf_counter() - t0

    print(f"\n{'─' * 70}")
    print(f"  SUMMARY")
    print(f"{'─' * 70}")
    print(f"  Total skills indexed : {stats['total']}")
    print(f"  Database             : {DB_PATH}")
    print(f"  Elapsed              : {elapsed:.2f}s\n")

    # Per-tier
    print("  Per-Tier Breakdown:")
    _print_table(
        ["Tier", "Count"],
        [[t, str(c)] for t, c in stats["per_tier"].items()],
        [35, 8],
    )

    # Per-category (top 20)
    cat_items = list(stats["per_category"].items())[:20]
    print(f"\n  Per-Category Breakdown (top {len(cat_items)}):")
    _print_table(
        ["Category", "Count"],
        [[cat, str(cnt)] for cat, cnt in cat_items],
        [35, 8],
    )

    # Demo query
    demo_queries = ["litigation", "agent", "security"]
    print(f"\n{'─' * 70}")
    print("  SAMPLE QUERIES")
    print(f"{'─' * 70}")
    for q in demo_queries:
        results = find_skills(q, limit=5)
        print(f"\n  find_skills('{q}') → {len(results)} results:")
        for r in results:
            print(f"    • {r['name']:<40s}  tier={r['tier']:<20s}  cat={r['category']}")

    conn.close()
    print(f"\n{'=' * 70}")
    print("  Done.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
