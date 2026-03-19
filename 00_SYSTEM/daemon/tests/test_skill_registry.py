"""
Unit tests for skill registry.
Tests skill discovery, parsing, dependency resolution, and activation.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from daemon.skill_registry import SkillRegistry, _parse_skill_file, _hash_file


class TestSkillFileParsing(unittest.TestCase):
    """Test SKILL.md parsing."""

    def test_parse_yaml_front_matter(self):
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("---\nname: test-skill\ndescription: A test skill\nversion: 2.0.0\n---\n# Test\nContent here.\n")
            path = f.name

        try:
            meta = _parse_skill_file(path)
            self.assertEqual(meta["name"], "test-skill")
            self.assertEqual(meta["description"], "A test skill")
            self.assertEqual(meta["version"], "2.0.0")
        finally:
            os.unlink(path)

    def test_parse_no_front_matter(self):
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write("# My Skill\nJust a plain file.\n")
            path = f.name

        try:
            meta = _parse_skill_file(path)
            # Should use directory name as fallback
            self.assertEqual(meta["version"], "1.0.0")
        finally:
            os.unlink(path)

    def test_parse_missing_file(self):
        meta = _parse_skill_file(r"C:\nonexistent\SKILL.md")
        self.assertEqual(meta["name"], "")
        self.assertEqual(meta["version"], "1.0.0")


class TestHashFile(unittest.TestCase):
    """Test file hashing."""

    def test_hash_produces_consistent_result(self):
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w"
        ) as f:
            f.write("consistent content")
            path = f.name

        try:
            h1 = _hash_file(path)
            h2 = _hash_file(path)
            self.assertEqual(h1, h2)
            self.assertEqual(len(h1), 16)  # Truncated to 16 chars
        finally:
            os.unlink(path)

    def test_hash_missing_file(self):
        result = _hash_file(r"C:\nonexistent_file.md")
        self.assertEqual(result, "")


class TestSkillRegistry(unittest.TestCase):
    """Test SkillRegistry with a fresh temp database."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.registry = SkillRegistry(self.db_path)
        self.skill_dir = tempfile.mkdtemp()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        for ext in ["-wal", "-shm"]:
            p = self.db_path + ext
            if os.path.exists(p):
                os.unlink(p)
        import shutil
        shutil.rmtree(self.skill_dir, ignore_errors=True)

    def _create_skill(self, name: str, version: str = "1.0.0", deps: str = ""):
        """Helper to create a skill directory with SKILL.md."""
        skill_path = os.path.join(self.skill_dir, name)
        os.makedirs(skill_path, exist_ok=True)
        content = f"---\nname: {name}\nversion: {version}\ndescription: Test skill {name}\n---\n# {name}\n"
        with open(os.path.join(skill_path, "SKILL.md"), "w") as f:
            f.write(content)
        return skill_path

    def test_scan_finds_skills(self):
        self._create_skill("skill-alpha")
        self._create_skill("skill-beta")

        skills = self.registry.scan(dirs=[self.skill_dir])
        self.assertEqual(len(skills), 2)
        names = {s.name for s in skills}
        self.assertIn("skill-alpha", names)
        self.assertIn("skill-beta", names)

    def test_get_skill(self):
        self._create_skill("my-skill", version="3.0.0")
        self.registry.scan(dirs=[self.skill_dir])

        skill = self.registry.get("my-skill")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.version, "3.0.0")

    def test_get_missing_skill(self):
        skill = self.registry.get("nonexistent")
        self.assertIsNone(skill)

    def test_list_all(self):
        self._create_skill("s1")
        self._create_skill("s2")
        self._create_skill("s3")
        self.registry.scan(dirs=[self.skill_dir])

        all_skills = self.registry.list_all()
        self.assertEqual(len(all_skills), 3)

    def test_record_run(self):
        from daemon.models import SkillRun
        self._create_skill("test-skill")
        self.registry.scan(dirs=[self.skill_dir])

        run = SkillRun(
            skill_id="test-skill",
            input_summary="test input",
            output_summary="test output",
            duration_sec=1.5,
            success=True,
        )
        self.registry.record_run(run)

        skill = self.registry.get("test-skill")
        self.assertEqual(skill.usage_count, 1)
        self.assertEqual(skill.success_rate, 1.0)

    def test_detect_changes(self):
        path = self._create_skill("change-skill")
        self.registry.scan(dirs=[self.skill_dir])

        # Modify the skill file
        with open(os.path.join(path, "SKILL.md"), "a") as f:
            f.write("\n## New section\n")

        changed = self.registry.detect_changes()
        self.assertIn("change-skill", changed)

    def test_activate_skill(self):
        self._create_skill("act-skill")
        self.registry.scan(dirs=[self.skill_dir])

        result = self.registry.activate("act-skill")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "active")

    def test_activate_missing_skill(self):
        result = self.registry.activate("nonexistent")
        self.assertFalse(result["success"])

    def test_deactivate_skill(self):
        self._create_skill("deact-skill")
        self.registry.scan(dirs=[self.skill_dir])

        result = self.registry.deactivate("deact-skill")
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
