"""
Agent Contract Tests — Verify all DELTA9 agents conform to Agent9999 contract.

Auto-discovers agent .py files, AST-parses them, and verifies:
  - Required abstract methods exist: _get_work_items, _process_item, _validate_preconditions
  - run() return type hint is AgentResult
  - agent_id follows naming convention (letter + 2 digits, e.g. A01, J05, F03)
  - Class inherits from Agent9999
  - __init__ calls super().__init__ with agent_id
"""
import ast
import os
import re
import sys
import unittest
from pathlib import Path

# UTF-8 stdout for Windows — only when running directly (not via pytest)
if __name__ == '__main__':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
else:
    os.environ['PYTHONUTF8'] = '1'

# Resolve paths relative to this file
AGENTS_DIR = Path(__file__).resolve().parent.parent
LANE1_DIR = AGENTS_DIR / "lane1_infrastructure"
LANE2_DIR = AGENTS_DIR / "lane2_intelligence"
CONVERGENCE_DIR = AGENTS_DIR / "convergence"

# Agent ID pattern: 1-2 uppercase letters + 2 digits, optionally followed by
# hyphen-separated descriptor (e.g., A01, A01-INDEX-SCOUT-C, K05-PERSONS)
AGENT_ID_PATTERN = re.compile(r'^[A-Z]{1,2}\d{2}(-[A-Z0-9]+)*$')

# Discover all agent .py files (skip __init__.py)
AGENT_FILES: list[tuple[str, Path]] = []
for subdir in [LANE1_DIR, LANE2_DIR, CONVERGENCE_DIR]:
    if subdir.is_dir():
        for f in sorted(subdir.glob("*.py")):
            if f.name.startswith("__"):
                continue
            AGENT_FILES.append((f.stem, f))


def _parse_agent_file(filepath: Path) -> tuple[ast.Module | None, str | None]:
    """Parse a Python file and return (AST module, error string)."""
    try:
        source = filepath.read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(source, filename=str(filepath))
        return tree, None
    except SyntaxError as e:
        return None, f"SyntaxError: {e}"


def _find_agent_classes(tree: ast.Module) -> list[ast.ClassDef]:
    """Find all classes that inherit from Agent9999 (directly or via string match)."""
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr
                if base_name == 'Agent9999':
                    classes.append(node)
                    break
    return classes


def _get_method_names(cls: ast.ClassDef) -> set[str]:
    """Return all method names defined in a class."""
    return {
        node.name for node in cls.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _get_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef | None:
    """Get a specific method from a class definition."""
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _get_return_annotation_str(func: ast.FunctionDef) -> str | None:
    """Get the return annotation as a string, if present."""
    if func.returns is None:
        return None
    if isinstance(func.returns, ast.Name):
        return func.returns.id
    if isinstance(func.returns, ast.Attribute):
        return func.returns.attr
    if isinstance(func.returns, ast.Constant):
        return str(func.returns.value)
    return ast.dump(func.returns)


def _find_super_init_call(cls: ast.ClassDef) -> bool:
    """Check if __init__ contains a super().__init__() call."""
    init_method = _get_method(cls, '__init__')
    if init_method is None:
        # No __init__ means relying on parent — acceptable
        return True
    for node in ast.walk(init_method):
        if isinstance(node, ast.Call):
            func = node.func
            # super().__init__(...)
            if (isinstance(func, ast.Attribute)
                    and func.attr == '__init__'
                    and isinstance(func.value, ast.Call)
                    and isinstance(func.value.func, ast.Name)
                    and func.value.func.id == 'super'):
                return True
            # Agent9999.__init__(self, ...)
            if (isinstance(func, ast.Attribute)
                    and func.attr == '__init__'
                    and isinstance(func.value, ast.Name)
                    and func.value.id == 'Agent9999'):
                return True
    return False


def _extract_agent_id_from_init(cls: ast.ClassDef, source_path: Path) -> str | None:
    """Try to extract the agent_id string from the super().__init__ call."""
    init_method = _get_method(cls, '__init__')
    if init_method is None:
        return None
    source = source_path.read_text(encoding='utf-8', errors='replace')
    for node in ast.walk(init_method):
        if isinstance(node, ast.Call):
            func = node.func
            is_super_init = (
                isinstance(func, ast.Attribute)
                and func.attr == '__init__'
                and isinstance(func.value, ast.Call)
                and isinstance(func.value.func, ast.Name)
                and func.value.func.id == 'super'
            )
            is_direct_init = (
                isinstance(func, ast.Attribute)
                and func.attr == '__init__'
                and isinstance(func.value, ast.Name)
                and func.value.id == 'Agent9999'
            )
            if is_super_init or is_direct_init:
                # Look for string literal in args
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        return arg.value
                for kw in node.keywords:
                    if kw.arg == 'agent_id' and isinstance(kw.value, ast.Constant):
                        return kw.value.value
    return None


class TestAgentDiscovery(unittest.TestCase):
    """Verify we can discover agent files."""

    def test_agent_files_discovered(self):
        """At least 40 agent files should be discovered across all lanes."""
        self.assertGreaterEqual(
            len(AGENT_FILES), 40,
            f"Expected >= 40 agents, found {len(AGENT_FILES)}: "
            f"{[name for name, _ in AGENT_FILES]}"
        )

    def test_lane1_agents_exist(self):
        """Lane 1 (infrastructure) should have A01-A12."""
        lane1 = [name for name, path in AGENT_FILES if path.parent == LANE1_DIR]
        self.assertGreaterEqual(len(lane1), 10, f"Lane 1 has {len(lane1)} agents")

    def test_lane2_agents_exist(self):
        """Lane 2 (intelligence) should have J/K/L tier agents."""
        lane2 = [name for name, path in AGENT_FILES if path.parent == LANE2_DIR]
        self.assertGreaterEqual(len(lane2), 20, f"Lane 2 has {len(lane2)} agents")

    def test_convergence_agents_exist(self):
        """Convergence should have F01-F06."""
        conv = [name for name, path in AGENT_FILES if path.parent == CONVERGENCE_DIR]
        self.assertGreaterEqual(len(conv), 5, f"Convergence has {len(conv)} agents")


class TestAgentContract(unittest.TestCase):
    """Verify every agent implements the Agent9999 contract."""

    @classmethod
    def setUpClass(cls):
        """Parse all agent files once."""
        cls.parsed: dict[str, dict] = {}
        for name, filepath in AGENT_FILES:
            tree, error = _parse_agent_file(filepath)
            agent_classes = _find_agent_classes(tree) if tree else []
            cls.parsed[name] = {
                'path': filepath,
                'tree': tree,
                'error': error,
                'classes': agent_classes,
            }

    def test_all_files_parse(self):
        """Every agent file must be valid Python (no syntax errors)."""
        failures = []
        for name, info in self.parsed.items():
            if info['error']:
                failures.append(f"{name}: {info['error']}")
        self.assertEqual(failures, [], f"Parse failures:\n" + "\n".join(failures))

    def test_all_agents_have_agent9999_subclass(self):
        """Every agent file must define at least one Agent9999 subclass."""
        missing = []
        for name, info in self.parsed.items():
            if not info['classes']:
                missing.append(name)
        self.assertEqual(
            missing, [],
            f"Files without Agent9999 subclass:\n" + "\n".join(missing)
        )

    def test_get_work_items_exists(self):
        """Every agent class must implement _get_work_items."""
        missing = []
        for name, info in self.parsed.items():
            for cls in info['classes']:
                methods = _get_method_names(cls)
                if '_get_work_items' not in methods:
                    missing.append(f"{name}::{cls.name}")
        self.assertEqual(
            missing, [],
            f"Missing _get_work_items:\n" + "\n".join(missing)
        )

    def test_process_item_exists(self):
        """Every agent class must implement _process_item."""
        missing = []
        for name, info in self.parsed.items():
            for cls in info['classes']:
                methods = _get_method_names(cls)
                if '_process_item' not in methods:
                    missing.append(f"{name}::{cls.name}")
        self.assertEqual(
            missing, [],
            f"Missing _process_item:\n" + "\n".join(missing)
        )

    def test_validate_preconditions_exists(self):
        """Every agent class must implement _validate_preconditions."""
        missing = []
        for name, info in self.parsed.items():
            for cls in info['classes']:
                methods = _get_method_names(cls)
                if '_validate_preconditions' not in methods:
                    missing.append(f"{name}::{cls.name}")
        self.assertEqual(
            missing, [],
            f"Missing _validate_preconditions:\n" + "\n".join(missing)
        )

    def test_run_returns_agent_result(self):
        """If run() is overridden, it must have AgentResult return type hint."""
        bad = []
        for name, info in self.parsed.items():
            for cls in info['classes']:
                run_method = _get_method(cls, 'run')
                if run_method is not None:
                    ret = _get_return_annotation_str(run_method)
                    if ret is None or 'AgentResult' not in ret:
                        bad.append(f"{name}::{cls.name} -> {ret}")
        self.assertEqual(
            bad, [],
            f"run() without AgentResult return hint:\n" + "\n".join(bad)
        )

    def test_super_init_called(self):
        """Every agent __init__ must call super().__init__() or Agent9999.__init__()."""
        missing = []
        for name, info in self.parsed.items():
            for cls in info['classes']:
                if not _find_super_init_call(cls):
                    missing.append(f"{name}::{cls.name}")
        self.assertEqual(
            missing, [],
            f"Missing super().__init__() call:\n" + "\n".join(missing)
        )


class TestAgentNamingConvention(unittest.TestCase):
    """Verify agent IDs follow the naming convention."""

    @classmethod
    def setUpClass(cls):
        cls.agent_ids: list[tuple[str, str, str | None]] = []  # (filename, classname, agent_id)
        for name, filepath in AGENT_FILES:
            tree, _ = _parse_agent_file(filepath)
            if tree:
                for agent_cls in _find_agent_classes(tree):
                    aid = _extract_agent_id_from_init(agent_cls, filepath)
                    cls.agent_ids.append((name, agent_cls.name, aid))

    def test_agent_ids_follow_convention(self):
        """Agent IDs must match pattern: prefix (letter+2 digits) + optional descriptor (e.g., A01-INDEX-SCOUT-C)."""
        bad = []
        for filename, classname, agent_id in self.agent_ids:
            if agent_id is None:
                # Can't extract — skip (might use variable)
                continue
            if not AGENT_ID_PATTERN.match(agent_id):
                bad.append(f"{filename}::{classname} has id='{agent_id}'")
        self.assertEqual(
            bad, [],
            f"Non-conforming agent IDs:\n" + "\n".join(bad)
        )

    def test_filename_matches_agent_id(self):
        """Filename prefix should match agent_id prefix (e.g., a01_*.py → A01-*)."""
        mismatches = []
        for filename, classname, agent_id in self.agent_ids:
            if agent_id is None:
                continue
            # Extract expected prefix from filename: a01_index_scout_c → A01
            prefix_match = re.match(r'^([a-z]{1,2})(\d{2})_', filename)
            if prefix_match:
                expected_prefix = (prefix_match.group(1) + prefix_match.group(2)).upper()
                # agent_id should start with the same prefix
                actual_prefix = agent_id.split('-')[0] if '-' in agent_id else agent_id
                if expected_prefix != actual_prefix:
                    mismatches.append(
                        f"{filename}: file suggests '{expected_prefix}' but agent_id='{agent_id}'"
                    )
        self.assertEqual(
            mismatches, [],
            f"Filename/agent_id mismatches:\n" + "\n".join(mismatches)
        )

    def test_no_duplicate_agent_ids(self):
        """No two agents should share the same agent_id."""
        seen: dict[str, str] = {}
        dupes = []
        for filename, classname, agent_id in self.agent_ids:
            if agent_id is None:
                continue
            if agent_id in seen:
                dupes.append(f"'{agent_id}' in both {seen[agent_id]} and {filename}::{classname}")
            else:
                seen[agent_id] = f"{filename}::{classname}"
        self.assertEqual(dupes, [], f"Duplicate agent IDs:\n" + "\n".join(dupes))


class TestAgentCompleteness(unittest.TestCase):
    """Verify the full agent fleet is present."""

    def test_expected_lane1_agents(self):
        """Lane 1 should have A01-A12."""
        expected = {f"a{i:02d}" for i in range(1, 13)}
        actual = {
            name[:3] for name, path in AGENT_FILES
            if path.parent == LANE1_DIR and name[0] == 'a'
        }
        missing = expected - actual
        self.assertEqual(missing, set(), f"Missing lane1 agents: {missing}")

    def test_expected_convergence_agents(self):
        """Convergence should have F01-F06."""
        expected = {f"f{i:02d}" for i in range(1, 7)}
        actual = {
            name[:3] for name, path in AGENT_FILES
            if path.parent == CONVERGENCE_DIR and name[0] == 'f'
        }
        missing = expected - actual
        self.assertEqual(missing, set(), f"Missing convergence agents: {missing}")

    def test_expected_j_tier_agents(self):
        """Lane 2 should have J01-J08."""
        expected = {f"j{i:02d}" for i in range(1, 9)}
        actual = {
            name[:3] for name, path in AGENT_FILES
            if path.parent == LANE2_DIR and name[0] == 'j'
        }
        missing = expected - actual
        self.assertEqual(missing, set(), f"Missing J-tier agents: {missing}")

    def test_expected_k_tier_agents(self):
        """Lane 2 should have K01-K11."""
        expected = {f"k{i:02d}" for i in range(1, 12)}
        actual = {
            name[:3] for name, path in AGENT_FILES
            if path.parent == LANE2_DIR and name[0] == 'k'
        }
        missing = expected - actual
        self.assertEqual(missing, set(), f"Missing K-tier agents: {missing}")

    def test_expected_l_tier_agents(self):
        """Lane 2 should have L01-L11."""
        expected = {f"l{i:02d}" for i in range(1, 12)}
        actual = {
            name[:3] for name, path in AGENT_FILES
            if path.parent == LANE2_DIR and name[0] == 'l'
        }
        missing = expected - actual
        self.assertEqual(missing, set(), f"Missing L-tier agents: {missing}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
