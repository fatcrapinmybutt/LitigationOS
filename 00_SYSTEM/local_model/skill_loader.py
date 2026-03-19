"""
APEX Skill Loader — Discovers, loads, and manages litigation skills.

Reads from skills/ directory within local_model/ and from .agents/skills/.
Provides skill metadata for routing, matching, and chaining.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("apex.skill_loader")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_PROJECT_ROOT = _MODULE_DIR.parent.parent
_INTERNAL_SKILL_DIR = _MODULE_DIR / "skills"
_AGENT_SKILL_DIR = _PROJECT_ROOT / ".agents" / "skills"
_COPILOT_SKILL_DIR = _PROJECT_ROOT / ".copilot" / "skills"

# Well-known skill directories to probe
_SKILL_DIRS: List[Path] = [
    _INTERNAL_SKILL_DIR,
    _AGENT_SKILL_DIR,
    _COPILOT_SKILL_DIR,
    _PROJECT_ROOT / "skills",
    _PROJECT_ROOT / "Agent-Skills-for-Context-Engineering",
]

# ---------------------------------------------------------------------------
# Skill metadata extraction
# ---------------------------------------------------------------------------

_TRIGGER_PATTERN = re.compile(
    r"(?:trigger|keyword|match|pattern)[s]?\s*[:=]\s*['\"]?([^'\";\n]+)",
    re.IGNORECASE,
)

_DESCRIPTION_PATTERN = re.compile(
    r'(?:description|desc|summary)\s*[:=]\s*["\'](.+?)["\']',
    re.IGNORECASE,
)


def _extract_skill_meta(path: Path) -> Dict[str, Any]:
    """Extract metadata from a skill file (Python or Markdown)."""
    meta: Dict[str, Any] = {
        "name": path.stem,
        "path": str(path),
        "description": "",
        "triggers": [],
        "type": path.suffix.lstrip("."),
    }

    try:
        content = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except Exception:
        return meta

    # Extract from docstrings / comments
    lines = content.split("\n")

    # First docstring or comment block as description
    in_doc = False
    doc_lines: List[str] = []
    for line in lines[:30]:
        stripped = line.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if in_doc:
                break
            in_doc = True
            text = stripped.strip("\"'").strip()
            if text:
                doc_lines.append(text)
            continue
        if in_doc:
            doc_lines.append(stripped.strip("\"'").strip())
        elif stripped.startswith("#") and not doc_lines:
            doc_lines.append(stripped.lstrip("#").strip())
            break

    if doc_lines:
        meta["description"] = " ".join(doc_lines).strip()[:300]

    # Extract triggers
    for m in _TRIGGER_PATTERN.finditer(content):
        triggers = [t.strip() for t in m.group(1).split(",")]
        meta["triggers"].extend(triggers)

    # Extract description from structured fields
    dm = _DESCRIPTION_PATTERN.search(content)
    if dm and not meta["description"]:
        meta["description"] = dm.group(1).strip()[:300]

    # Extract from YAML/Markdown frontmatter (skills may use this)
    if content.startswith("---"):
        fm_end = content.find("---", 3)
        if fm_end > 3:
            fm = content[3:fm_end]
            for line in fm.split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip().lower()
                    val = val.strip().strip("\"'")
                    if key == "description" and val:
                        meta["description"] = val[:300]
                    elif key == "name" and val:
                        meta["name"] = val
                    elif key in ("triggers", "keywords") and val:
                        meta["triggers"].extend(t.strip() for t in val.split(","))

    meta["triggers"] = list(dict.fromkeys(meta["triggers"]))  # deduplicate
    return meta


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SkillLoader:
    """Discovers, loads, and manages litigation skills."""

    SKILL_DIR = _AGENT_SKILL_DIR  # primary skill directory

    def __init__(self, extra_dirs: Optional[List[str | Path]] = None) -> None:
        self._lock = threading.Lock()
        self._skills_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self._extra_dirs: List[Path] = [Path(d) for d in (extra_dirs or [])]

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_skill_files(self) -> List[Path]:
        """Find all skill files across known directories."""
        files: List[Path] = []
        search_dirs = _SKILL_DIRS + self._extra_dirs
        seen: set[str] = set()

        for d in search_dirs:
            try:
                if not d.exists() or not d.is_dir():
                    continue
                for ext in ("*.py", "*.md", "*.yaml", "*.yml", "*.json"):
                    for f in d.rglob(ext):
                        if f.name.startswith("_") or f.name.startswith("."):
                            continue
                        canon = str(f.resolve())
                        if canon not in seen:
                            seen.add(canon)
                            files.append(f)
            except Exception as exc:
                logger.debug("Skill discovery error in %s: %s", d, exc)
        return files

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load all available skills.

        Returns ``{name: {description, path, triggers, type}}``.
        """
        if self._skills_cache is not None:
            return self._skills_cache

        with self._lock:
            if self._skills_cache is not None:
                return self._skills_cache
            skills: Dict[str, Dict[str, Any]] = {}
            try:
                files = self._discover_skill_files()
                for f in files:
                    try:
                        meta = _extract_skill_meta(f)
                        name = meta["name"]
                        # Avoid overwriting with lower-priority duplicates
                        if name not in skills:
                            skills[name] = meta
                    except Exception as exc:
                        logger.debug("Skill load error for %s: %s", f, exc)
                logger.info("Loaded %d skills from %d files", len(skills), len(files))
            except Exception as exc:
                logger.error("Skill loader failed: %s", exc)
            self._skills_cache = skills
            return skills

    def get_skill(self, name: str) -> dict:
        """Get a specific skill's metadata.

        Returns skill dict or ``{error: "not found"}``.
        """
        try:
            skills = self.load_all()
            if name in skills:
                return skills[name]
            # Fuzzy match
            lower = name.lower().replace("-", "_").replace(" ", "_")
            for sn, sm in skills.items():
                if sn.lower().replace("-", "_").replace(" ", "_") == lower:
                    return sm
            return {"name": name, "error": "not found"}
        except Exception as exc:
            logger.error("get_skill failed: %s", exc)
            return {"name": name, "error": str(exc)}

    def match_skills(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find skills matching a query. Returns ranked list."""
        try:
            skills = self.load_all()
            query_lower = query.lower()
            query_words = set(query_lower.split())
            scored: List[tuple[float, str, dict]] = []

            for name, meta in skills.items():
                score = 0.0
                name_lower = name.lower().replace("-", " ").replace("_", " ")
                desc_lower = meta.get("description", "").lower()
                triggers = [t.lower() for t in meta.get("triggers", [])]

                # Exact name match
                if query_lower in name_lower or name_lower in query_lower:
                    score += 10.0

                # Trigger match
                for trigger in triggers:
                    if trigger in query_lower or query_lower in trigger:
                        score += 8.0

                # Word overlap with name
                name_words = set(name_lower.split())
                name_overlap = query_words & name_words
                score += len(name_overlap) * 3.0

                # Word overlap with description
                desc_words = set(desc_lower.split())
                desc_overlap = query_words & desc_words
                score += len(desc_overlap) * 1.0

                if score > 0:
                    scored.append((score, name, meta))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                {**meta, "match_score": round(score, 2)}
                for score, name, meta in scored[:top_k]
            ]
        except Exception as exc:
            logger.error("match_skills failed: %s", exc)
            return []

    def get_chain(self, task_type: str) -> list:
        """Get recommended skill chain for a task type.

        Returns ordered list of skill names.
        """
        # Well-known chains
        chains: Dict[str, List[str]] = {
            "brief": ["litigation-claim-researcher", "litigation-brief-writer", "litigation-red-team"],
            "complaint": ["litigation-claim-researcher", "litigation-complaint-drafter"],
            "motion": ["litigation-claim-researcher", "litigation-brief-writer"],
            "appeal": ["litigation-appellate-strategist", "litigation-record-builder"],
            "discovery": ["litigation-evidence-harvester", "litigation-discovery-warfare"],
            "impeachment": ["litigation-impeachment-engine", "litigation-evidence-harvester"],
            "filing": ["litigation-filing-architect", "litigation-pro-se-guardian"],
        }
        try:
            tt = task_type.lower().strip()
            if tt in chains:
                return chains[tt]
            # Partial match
            for key, chain in chains.items():
                if key in tt or tt in key:
                    return chain
            # Fallback: match skills
            matches = self.match_skills(task_type, top_k=3)
            return [m["name"] for m in matches if "name" in m]
        except Exception as exc:
            logger.error("get_chain failed: %s", exc)
            return []

    def reload(self) -> int:
        """Force reload all skills. Returns count loaded."""
        with self._lock:
            self._skills_cache = None
        skills = self.load_all()
        return len(skills)

    def summary(self) -> Dict[str, Any]:
        """Return summary statistics about loaded skills."""
        skills = self.load_all()
        by_type: Dict[str, int] = {}
        for s in skills.values():
            t = s.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total": len(skills),
            "by_type": by_type,
            "directories_searched": len(_SKILL_DIRS) + len(self._extra_dirs),
        }


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_loader: Optional[SkillLoader] = None
_loader_lock = threading.Lock()


def get_loader() -> SkillLoader:
    """Return the default SkillLoader instance."""
    global _default_loader
    if _default_loader is None:
        with _loader_lock:
            if _default_loader is None:
                _default_loader = SkillLoader()
    return _default_loader
