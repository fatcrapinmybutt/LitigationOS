"""SelfDocumenter — Automatic documentation generator for LitigationOS.

Introspects the codebase and database to generate:
    - TABLE_REFERENCE.md  — All tables with column schemas
    - ENGINE_REFERENCE.md — All engines with classes, functions, versions
    - SKILL_REFERENCE.md  — All SINGULARITY skills with summaries

Uses ast.parse for Python inspection (no imports = no side effects),
PRAGMA table_info for DB schemas, and os.walk for directory scanning.
"""

import sys
import os
import re
import ast
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

_ROOT = r"C:\Users\andre\LitigationOS"


class SelfDocumenter:
    """Generates reference documentation from live codebase and database.

    All generation is read-only — no modifications to source code or DB.
    Output is written as markdown to the specified directory.
    """

    def __init__(self, db_path: Optional[str] = None, root_dir: Optional[str] = None):
        self._db_path = db_path
        self._root = root_dir or _ROOT
        self._conn: Optional[sqlite3.Connection] = None

    # ── Lazy Connection ───────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
        return self._conn

    def _connect(self) -> sqlite3.Connection:
        if self._db_path:
            path = self._db_path
        else:
            try:
                from shared import get_db_path
                path = str(get_db_path("litigation_context"))
            except ImportError:
                path = os.path.join(self._root, "litigation_context.db")
        conn = sqlite3.connect(path, timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        return conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── Generate All ──────────────────────────────────────────────────

    def generate_all(self, output_dir: str) -> Dict[str, str]:
        """Generate all reference documents.

        Args:
            output_dir: Directory to write markdown files to.

        Returns:
            Dict mapping filename → full path of generated file.
        """
        os.makedirs(output_dir, exist_ok=True)
        generated = {}

        table_path = self.generate_table_reference(output_dir)
        generated["TABLE_REFERENCE.md"] = table_path

        engine_path = self.generate_engine_reference(output_dir)
        generated["ENGINE_REFERENCE.md"] = engine_path

        skill_path = self.generate_skill_reference(output_dir)
        generated["SKILL_REFERENCE.md"] = skill_path

        logger.info("Generated %d reference documents in %s", len(generated), output_dir)
        return generated

    # ── Table Reference ───────────────────────────────────────────────

    def generate_table_reference(self, output_dir: str) -> str:
        """Generate TABLE_REFERENCE.md from sqlite_master + PRAGMA table_info.

        Lists every table with column schemas, types, and row counts.
        """
        lines = [
            "# LitigationOS Table Reference",
            "",
            f"> Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"> Database: litigation_context.db",
            "",
        ]

        # Get all tables
        tables = self.conn.execute(
            """SELECT name FROM sqlite_master
               WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
               ORDER BY name"""
        ).fetchall()

        lines.append(f"**Total tables: {len(tables)}**\n")
        lines.append("## Table of Contents\n")
        for t in tables:
            name = t[0]
            lines.append(f"- [{name}](#{name.lower().replace(' ', '-')})")
        lines.append("")

        # Detail each table
        for t in tables:
            name = t[0]
            lines.append(f"## {name}\n")

            # Row count
            try:
                row = self.conn.execute(
                    f'SELECT COUNT(*) FROM "{name}"'
                ).fetchone()
                count = row[0] if row else 0
                lines.append(f"**Rows: {count:,}**\n")
            except sqlite3.OperationalError:
                lines.append("**Rows: (error reading)**\n")

            # Column schema
            try:
                cols = self.conn.execute(
                    f'PRAGMA table_info("{name}")'
                ).fetchall()
            except sqlite3.OperationalError:
                cols = []

            if cols:
                lines.append("| # | Column | Type | Nullable | Default | PK |")
                lines.append("|---|--------|------|----------|---------|-----|")
                for c in cols:
                    cid, col_name, col_type, notnull, dflt, pk = (
                        c[0], c[1], c[2] or "ANY", c[3], c[4] or "", c[5]
                    )
                    nullable = "NO" if notnull else "YES"
                    pk_mark = "✓" if pk else ""
                    lines.append(
                        f"| {cid} | `{col_name}` | {col_type} | {nullable} | {dflt} | {pk_mark} |"
                    )
            lines.append("")

        output_path = os.path.join(output_dir, "TABLE_REFERENCE.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Generated TABLE_REFERENCE.md (%d tables)", len(tables))
        return output_path

    # ── Engine Reference ──────────────────────────────────────────────

    def generate_engine_reference(self, output_dir: str) -> str:
        """Generate ENGINE_REFERENCE.md by scanning engine directories.

        For each engine dir, uses ast.parse to extract classes, functions,
        and docstrings without importing the code.
        """
        engines_dir = os.path.join(self._root, "00_SYSTEM", "engines")

        lines = [
            "# LitigationOS Engine Reference",
            "",
            f"> Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"> Source: {engines_dir}",
            "",
        ]

        if not os.path.isdir(engines_dir):
            lines.append("*Engine directory not found*\n")
            output_path = os.path.join(output_dir, "ENGINE_REFERENCE.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return output_path

        engine_dirs = sorted([
            d for d in os.listdir(engines_dir)
            if os.path.isdir(os.path.join(engines_dir, d))
            and not d.startswith("__")
        ])

        lines.append(f"**Total engine directories: {len(engine_dirs)}**\n")

        for eng_name in engine_dirs:
            eng_path = os.path.join(engines_dir, eng_name)
            lines.append(f"## {eng_name}\n")

            # Read version from __init__.py
            init_path = os.path.join(eng_path, "__init__.py")
            version = self._extract_version(init_path)
            if version:
                lines.append(f"**Version:** {version}\n")

            # Scan all .py files
            py_files = sorted([
                f for f in os.listdir(eng_path)
                if f.endswith(".py") and f != "__init__.py"
            ])

            if not py_files:
                lines.append("*No Python modules found*\n")
                continue

            for py_file in py_files:
                py_path = os.path.join(eng_path, py_file)
                module_info = self._parse_python_file(py_path)

                lines.append(f"### {py_file}\n")

                if module_info.get("docstring"):
                    doc = module_info["docstring"].split("\n")[0]
                    lines.append(f"*{doc}*\n")

                # Classes
                for cls in module_info.get("classes", []):
                    lines.append(f"#### `class {cls['name']}`\n")
                    if cls.get("docstring"):
                        doc = cls["docstring"].split("\n")[0]
                        lines.append(f"*{doc}*\n")
                    if cls.get("methods"):
                        lines.append("| Method | Args |")
                        lines.append("|--------|------|")
                        for m in cls["methods"]:
                            args_str = ", ".join(m["args"][:5])
                            if len(m["args"]) > 5:
                                args_str += ", ..."
                            lines.append(f"| `{m['name']}` | `{args_str}` |")
                        lines.append("")

                # Module-level functions
                funcs = module_info.get("functions", [])
                if funcs:
                    lines.append("**Functions:**\n")
                    for fn in funcs:
                        args_str = ", ".join(fn["args"][:5])
                        lines.append(f"- `{fn['name']}({args_str})`")
                    lines.append("")

        output_path = os.path.join(output_dir, "ENGINE_REFERENCE.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Generated ENGINE_REFERENCE.md (%d engines)", len(engine_dirs))
        return output_path

    def _extract_version(self, init_path: str) -> Optional[str]:
        """Extract __version__ string from an __init__.py file."""
        if not os.path.isfile(init_path):
            return None
        try:
            with open(init_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(4096)
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            return match.group(1) if match else None
        except (OSError, IOError):
            return None

    def _parse_python_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a Python file with ast to extract classes and functions.

        No imports executed — purely static analysis.
        """
        result: Dict[str, Any] = {
            "docstring": None,
            "classes": [],
            "functions": [],
        }

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except (OSError, IOError) as e:
            logger.warning("Cannot read %s: %s", file_path, e)
            return result

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            return result

        # Module docstring
        result["docstring"] = ast.get_docstring(tree)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                cls_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": [],
                }
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [
                            a.arg for a in item.args.args
                            if a.arg != "self"
                        ]
                        cls_info["methods"].append({
                            "name": item.name,
                            "args": args,
                            "docstring": ast.get_docstring(item),
                        })
                result["classes"].append(cls_info)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                result["functions"].append({
                    "name": node.name,
                    "args": args,
                    "docstring": ast.get_docstring(node),
                })

        return result

    # ── Skill Reference ───────────────────────────────────────────────

    def generate_skill_reference(self, output_dir: str) -> str:
        """Generate SKILL_REFERENCE.md from .agents/skills/SINGULARITY-*/SKILL.md files."""
        skills_dir = os.path.join(self._root, ".agents", "skills")

        lines = [
            "# LitigationOS SINGULARITY Skill Reference",
            "",
            f"> Auto-generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"> Source: {skills_dir}",
            "",
        ]

        if not os.path.isdir(skills_dir):
            lines.append("*Skills directory not found*\n")
            output_path = os.path.join(output_dir, "SKILL_REFERENCE.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return output_path

        skill_dirs = sorted([
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))
            and d.startswith("SINGULARITY-")
        ])

        lines.append(f"**Total SINGULARITY skills: {len(skill_dirs)}**\n")

        # Summary table
        lines.append("## Summary\n")
        lines.append("| Skill | Lines | Size |")
        lines.append("|-------|-------|------|")

        skill_details = []
        for skill_name in skill_dirs:
            skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
            if not os.path.isfile(skill_path):
                continue

            try:
                stat = os.stat(skill_path)
                size_kb = stat.st_size / 1024
                with open(skill_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                line_count = content.count("\n") + 1
                # Extract first heading after the title
                first_heading = ""
                for line in content.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("# ") and not first_heading:
                        first_heading = stripped[2:].strip()
                        break

                lines.append(
                    f"| [{skill_name}](#{skill_name.lower()}) | {line_count:,} | {size_kb:.1f} KB |"
                )
                skill_details.append({
                    "name": skill_name,
                    "heading": first_heading,
                    "lines": line_count,
                    "size_kb": size_kb,
                    "content_preview": content[:2000],
                })
            except (OSError, IOError):
                lines.append(f"| {skill_name} | — | — |")

        lines.append("")

        # Detail each skill
        for detail in skill_details:
            lines.append(f"## {detail['name']}\n")
            if detail["heading"]:
                lines.append(f"**{detail['heading']}**\n")
            lines.append(f"- Lines: {detail['lines']:,}")
            lines.append(f"- Size: {detail['size_kb']:.1f} KB")
            lines.append("")

            # Extract section headings from preview
            headings = re.findall(r'^#{2,3}\s+(.+)$', detail["content_preview"], re.MULTILINE)
            if headings:
                lines.append("**Sections:**\n")
                for h in headings[:15]:
                    lines.append(f"- {h}")
                if len(headings) > 15:
                    lines.append(f"- *(+{len(headings) - 15} more)*")
                lines.append("")

        output_path = os.path.join(output_dir, "SKILL_REFERENCE.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("Generated SKILL_REFERENCE.md (%d skills)", len(skill_details))
        return output_path

    # ── Statistics ────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return statistics about what's available to document."""
        # Count tables
        tables = self.conn.execute(
            """SELECT COUNT(*) FROM sqlite_master
               WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"""
        ).fetchone()

        # Count engine dirs
        engines_dir = os.path.join(self._root, "00_SYSTEM", "engines")
        engine_count = 0
        if os.path.isdir(engines_dir):
            engine_count = len([
                d for d in os.listdir(engines_dir)
                if os.path.isdir(os.path.join(engines_dir, d))
                and not d.startswith("__")
            ])

        # Count skill dirs
        skills_dir = os.path.join(self._root, ".agents", "skills")
        skill_count = 0
        if os.path.isdir(skills_dir):
            skill_count = len([
                d for d in os.listdir(skills_dir)
                if os.path.isdir(os.path.join(skills_dir, d))
                and d.startswith("SINGULARITY-")
            ])

        return {
            "tables": tables[0] if tables else 0,
            "engines": engine_count,
            "skills": skill_count,
        }
