"""
Skill Registry for LitigationOS Daemon.
Scans, parses, versions, and tracks all litigation skills.

Skill sources:
- .agents/skills/*/SKILL.md — Custom agents skills
- .copilot/skills/*/SKILL.md — Copilot custom skills
- C:\\Users\\andre\\.copilot\\skills\\*\\SKILL.md — User-level skills
"""
import hashlib
import os
import re
import sqlite3
from datetime import datetime
from typing import Optional

from .models import SkillInfo, SkillRun, SkillTier

SKILL_DIRS = [
    r"C:\Users\andre\LitigationOS\.agents\skills",
    r"C:\Users\andre\LitigationOS\.copilot\skills",
    r"C:\Users\andre\.copilot\skills",
]

REGISTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    tier TEXT NOT NULL DEFAULT 'core',
    path TEXT NOT NULL,
    description TEXT DEFAULT '',
    dependencies TEXT DEFAULT '[]',
    status TEXT DEFAULT 'active',
    loaded_at TEXT,
    content_hash TEXT,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 1.0,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS skill_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    duration_sec REAL,
    success INTEGER,
    error TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);

CREATE INDEX IF NOT EXISTS idx_sr_skill_ts ON skill_runs(skill_id, timestamp);
"""


def _parse_skill_file(path: str) -> dict:
    """Parse a SKILL.md file for metadata."""
    metadata = {
        "name": "",
        "description": "",
        "version": "1.0.0",
        "tier": "core",
        "dependencies": [],
    }

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return metadata

    # Parse YAML front matter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key == "name":
                    metadata["name"] = val
                elif key == "description":
                    metadata["description"] = val[:500]
                elif key == "version":
                    metadata["version"] = val

    # Fallback: use directory name as skill name
    if not metadata["name"]:
        metadata["name"] = os.path.basename(os.path.dirname(path))

    # Determine tier from path
    if ".agents" in path:
        metadata["tier"] = "core"
    elif ".copilot" in path:
        metadata["tier"] = "enhancement"
    else:
        metadata["tier"] = "infrastructure"

    return metadata


def _hash_file(path: str) -> str:
    """SHA-256 hash of file content."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except Exception:
        return ""
    return h.hexdigest()[:16]


class SkillRegistry:
    """Manages skill discovery, versioning, and usage tracking."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        conn.executescript(REGISTRY_SCHEMA)
        conn.commit()
        conn.close()

    def scan(self, dirs: list[str] = None) -> list[SkillInfo]:
        """Scan directories for skills. Returns list of discovered skills."""
        dirs = dirs or SKILL_DIRS
        skills = []

        for skill_dir in dirs:
            if not os.path.isdir(skill_dir):
                continue
            for entry in os.scandir(skill_dir):
                if not entry.is_dir():
                    continue
                skill_file = os.path.join(entry.path, "SKILL.md")
                if not os.path.isfile(skill_file):
                    continue

                meta = _parse_skill_file(skill_file)
                content_hash = _hash_file(skill_file)

                skill = SkillInfo(
                    id=meta["name"],
                    name=meta["name"],
                    version=meta["version"],
                    tier=SkillTier(meta["tier"]),
                    path=skill_file,
                    description=meta["description"],
                    dependencies=meta["dependencies"],
                    content_hash=content_hash,
                    loaded_at=datetime.utcnow(),
                )
                skills.append(skill)

        # Upsert into DB
        conn = self._conn()
        for s in skills:
            conn.execute(
                "INSERT OR REPLACE INTO skills "
                "(id, name, version, tier, path, description, dependencies, "
                "content_hash, loaded_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (s.id, s.name, s.version, s.tier.value, s.path,
                 s.description, str(s.dependencies), s.content_hash,
                 s.loaded_at.isoformat() if s.loaded_at else None)
            )
        conn.commit()
        conn.close()

        return skills

    def get(self, skill_id: str) -> Optional[SkillInfo]:
        """Get a skill by ID."""
        conn = self._conn()
        row = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return SkillInfo(
            id=row["id"], name=row["name"], version=row["version"],
            tier=SkillTier(row["tier"]), path=row["path"],
            description=row["description"],
            content_hash=row["content_hash"] or "",
            usage_count=row["usage_count"] or 0,
            success_rate=row["success_rate"] or 1.0,
        )

    def list_all(self, tier: str = None) -> list[SkillInfo]:
        """List all registered skills, optionally filtered by tier."""
        conn = self._conn()
        if tier:
            rows = conn.execute(
                "SELECT * FROM skills WHERE tier = ? ORDER BY name", (tier,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM skills ORDER BY name").fetchall()
        conn.close()
        return [
            SkillInfo(
                id=r["id"], name=r["name"], version=r["version"],
                tier=SkillTier(r["tier"]), path=r["path"],
                description=r["description"],
                content_hash=r["content_hash"] or "",
                usage_count=r["usage_count"] or 0,
                success_rate=r["success_rate"] or 1.0,
            )
            for r in rows
        ]

    def record_run(self, run: SkillRun):
        """Record a skill execution for tracking."""
        conn = self._conn()
        conn.execute(
            "INSERT INTO skill_runs (skill_id, input_summary, output_summary, "
            "duration_sec, success, error) VALUES (?, ?, ?, ?, ?, ?)",
            (run.skill_id, run.input_summary, run.output_summary,
             run.duration_sec, 1 if run.success else 0, run.error)
        )
        # Update skill stats
        conn.execute(
            "UPDATE skills SET usage_count = usage_count + 1, "
            "success_rate = (SELECT CAST(SUM(success) AS REAL) / COUNT(*) "
            "FROM skill_runs WHERE skill_id = ?) WHERE id = ?",
            (run.skill_id, run.skill_id)
        )
        conn.commit()
        conn.close()

    def detect_changes(self) -> list[str]:
        """Detect skills whose content has changed since last scan."""
        changed = []
        conn = self._conn()
        rows = conn.execute("SELECT id, path, content_hash FROM skills").fetchall()
        conn.close()
        for row in rows:
            if os.path.isfile(row["path"]):
                current_hash = _hash_file(row["path"])
                if current_hash != row["content_hash"]:
                    changed.append(row["id"])
        return changed

    def resolve_dependencies(self, skill_id: str) -> list[str]:
        """Resolve skill dependencies in topological order.

        Returns list of skill IDs that must be loaded before this skill.
        Raises ValueError on circular dependencies.
        """
        conn = self._conn()
        all_skills = {
            r["id"]: r["dependencies"]
            for r in conn.execute("SELECT id, dependencies FROM skills").fetchall()
        }
        conn.close()

        resolved = []
        visited = set()
        in_stack = set()

        def _visit(sid: str):
            if sid in in_stack:
                raise ValueError(f"Circular dependency detected: {sid}")
            if sid in visited:
                return
            in_stack.add(sid)
            deps_raw = all_skills.get(sid, "[]")
            try:
                deps = eval(deps_raw) if isinstance(deps_raw, str) else deps_raw
            except Exception:
                deps = []
            for dep in deps:
                if dep in all_skills:
                    _visit(dep)
            in_stack.discard(sid)
            visited.add(sid)
            resolved.append(sid)

        _visit(skill_id)
        # Remove the skill itself from the dependency chain
        return [s for s in resolved if s != skill_id]

    def activate(self, skill_id: str) -> dict:
        """Activate a skill — verify dependencies, mark as active, return skill info.

        Returns dict with success status and skill details.
        """
        skill = self.get(skill_id)
        if not skill:
            return {"success": False, "error": f"Skill not found: {skill_id}"}

        # Resolve dependencies
        try:
            deps = self.resolve_dependencies(skill_id)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Verify all dependencies are active
        conn = self._conn()
        missing = []
        for dep_id in deps:
            row = conn.execute(
                "SELECT status FROM skills WHERE id = ?", (dep_id,)
            ).fetchone()
            if not row or row["status"] != "active":
                missing.append(dep_id)

        if missing:
            conn.close()
            return {
                "success": False,
                "error": f"Missing/inactive dependencies: {missing}",
                "missing_deps": missing,
            }

        # Mark as active
        conn.execute(
            "UPDATE skills SET status = 'active', updated_at = datetime('now') WHERE id = ?",
            (skill_id,)
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "skill_id": skill_id,
            "dependencies_resolved": deps,
            "status": "active",
        }

    def deactivate(self, skill_id: str) -> dict:
        """Deactivate a skill."""
        conn = self._conn()
        conn.execute(
            "UPDATE skills SET status = 'inactive', updated_at = datetime('now') WHERE id = ?",
            (skill_id,)
        )
        conn.commit()
        conn.close()
        return {"success": True, "skill_id": skill_id, "status": "inactive"}
