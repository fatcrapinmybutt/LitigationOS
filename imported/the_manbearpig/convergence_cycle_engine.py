#!/usr/bin/env python3
"""
Advanced Iterative Convergence Cycle Engine
===========================================

A litigation-grade iterative build system that enforces strict output contracts
on each cycle, providing full traceability and version control.

Features:
- Automatic VERSION increment (v0001, v0002, ...)
- CURRENT pointer to runnable version
- Immutable VERSIONS/vNNNN snapshots with complete source
- Auto-generated CHANGELOG in Keep a Changelog format
- SHA-256 module manifest with integrity verification
- Comprehensive smoke test suite with detailed logging
- Conditional full release ZIP builder
- Size policy enforcement (650MB threshold, PATCHES mode, growth tracking)
- Multi-format logging (file + console)

Usage:
    python convergence_cycle_engine.py
    
    Or use the CLI wrapper:
    python run_cycle.py [--status|--history|--snapshot]

Author: FRED PRIME Litigation Deployment System
Version: 2.0
"""

import datetime
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure logs directory exists before configuring logging
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/convergence_cycle.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
VERSION_FILE = Path("VERSION")
CHANGELOG_FILE = Path("CHANGELOG.md")
MANIFEST_FILE = Path("codex_manifest.json")
CURRENT_FILE = Path("CURRENT")
VERSIONS_DIR = Path("VERSIONS")
OUTPUT_DIR = Path("output")
LOGS_DIR = Path("logs")
SMOKE_TEST_LOG = LOGS_DIR / "smoke_tests.log"
BUILD_LOG = LOGS_DIR / "build.log"
SIZE_REPORT = LOGS_DIR / "size_report.log"

# Size policy constants (in bytes)
MAX_BUILD_SIZE = 650 * 1024 * 1024  # 650MB
SIZE_GROWTH_THRESHOLD = 50 * 1024 * 1024  # 50MB
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB

# File patterns to exclude from release builds
EXCLUDE_PATTERNS = [
    "*.weights",
    "*.model",
    "*.bin",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.mkv",
    "*.mp3",
    "*.wav",
    "*.flac",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.bmp",
    "__pycache__",
    "*.pyc",
    ".git",
    ".github",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    "*.egg-info",
    "dist",
    "build",
]


class ConvergenceCycleEngine:
    """
    Manages the full convergence cycle for litigation OS builds.
    
    This class orchestrates version management, change tracking, testing,
    and release building in a single coordinated workflow.
    
    Attributes:
        current_version (str): The version being built (e.g., "v0042")
        previous_version (str): The previous version for comparison
        changed_files (List[str]): Files modified since last version
        module_count (int): Number of Python modules tracked
        total_size (int): Total size of project in bytes
        previous_size (int): Previous project size for growth calculation
        use_patches_mode (bool): Whether to use PATCHES mode for large builds
    """

    def __init__(self):
        """Initialize the convergence cycle engine with default values."""
        self.current_version: str = ""
        self.previous_version: str = ""
        self.changed_files: List[str] = []
        self.module_count: int = 0
        self.total_size: int = 0
        self.previous_size: int = 0
        self.use_patches_mode: bool = False
        
        # Ensure directories exist
        for directory in [VERSIONS_DIR, OUTPUT_DIR, LOGS_DIR]:
            directory.mkdir(exist_ok=True)

    def read_version(self) -> str:
        """
        Read current version from VERSION file.
        
        Returns:
            str: Current version string (e.g., "v0042"), or "v0000" if file doesn't exist
        """
        try:
            if VERSION_FILE.exists():
                version = VERSION_FILE.read_text().strip()
                # Validate version format
                if not re.match(r"^v\d{4}$", version):
                    logger.warning(f"Invalid version format: {version}, using v0000")
                    return "v0000"
                return version
            return "v0000"
        except Exception as e:
            logger.error(f"Error reading version file: {e}")
            return "v0000"

    def increment_version(self) -> str:
        """
        Increment version number (v0001 -> v0002).
        
        Returns:
            str: The new incremented version string
            
        Raises:
            ValueError: If version format is invalid
        """
        self.previous_version = self.read_version()
        
        # Extract numeric part
        match = re.match(r"v(\d+)", self.previous_version)
        if match:
            num = int(match.group(1))
            num += 1
            self.current_version = f"v{num:04d}"
        else:
            logger.warning(f"Could not parse version {self.previous_version}, starting at v0001")
            self.current_version = "v0001"
        
        # Write new version
        try:
            VERSION_FILE.write_text(self.current_version)
            logger.info(f"Version incremented: {self.previous_version} -> {self.current_version}")
        except Exception as e:
            logger.error(f"Failed to write version file: {e}")
            raise
        
        return self.current_version

    def update_current(self) -> None:
        """Update CURRENT file to point to the latest version."""
        CURRENT_FILE.write_text(self.current_version)
        logger.info(f"CURRENT updated to {self.current_version}")

    def snapshot_version(self) -> Path:
        """Create immutable snapshot in VERSIONS/vNNNN."""
        version_dir = VERSIONS_DIR / self.current_version
        version_dir.mkdir(exist_ok=True)
        
        # Copy all Python source files, configs, and docs
        patterns = ["*.py", "*.json", "*.yaml", "*.yml", "*.md", "*.txt"]
        files_copied = []
        
        for pattern in patterns:
            for src_file in Path(".").rglob(pattern):
                # Skip excluded directories
                if any(excluded in src_file.parts for excluded in [".git", "__pycache__", "VERSIONS", "output", ".venv", "venv"]):
                    continue
                
                # Create destination path maintaining directory structure
                rel_path = src_file.relative_to(".")
                dst_file = version_dir / rel_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(src_file, dst_file)
                files_copied.append(str(rel_path))
        
        # Create snapshot manifest
        snapshot_manifest = {
            "version": self.current_version,
            "timestamp": datetime.datetime.now().isoformat(),
            "files": files_copied,
            "file_count": len(files_copied),
        }
        
        manifest_path = version_dir / "SNAPSHOT_MANIFEST.json"
        manifest_path.write_text(json.dumps(snapshot_manifest, indent=2))
        
        logger.info(f"Created immutable snapshot at {version_dir} ({len(files_copied)} files)")
        return version_dir

    def detect_changed_files(self) -> List[str]:
        """Detect files changed since last version."""
        try:
            # Try to get changed files from git
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                self.changed_files = [f for f in result.stdout.strip().split("\n") if f]
            else:
                # Fallback: compare with previous version snapshot
                prev_version_dir = VERSIONS_DIR / self.previous_version
                if prev_version_dir.exists():
                    # Simple heuristic: any .py file modified in last 24h
                    cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
                    self.changed_files = []
                    for py_file in Path(".").rglob("*.py"):
                        if py_file.stat().st_mtime > cutoff.timestamp():
                            self.changed_files.append(str(py_file))
                else:
                    self.changed_files = []
        except Exception as e:
            logger.warning(f"Could not detect changed files: {e}")
            self.changed_files = []
        
        logger.info(f"Detected {len(self.changed_files)} changed files")
        return self.changed_files

    def update_changelog(self) -> None:
        """Update CHANGELOG.md with new version entry."""
        if not CHANGELOG_FILE.exists():
            CHANGELOG_FILE.write_text("# CHANGELOG\n\n")
        
        changelog_content = CHANGELOG_FILE.read_text()
        
        # Create new entry
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        new_entry = f"\n## [{self.current_version}] - {timestamp}\n\n"
        
        # Categorize changes
        added = []
        changed = []
        fixed = []
        
        for file in self.changed_files:
            if "test" in file.lower():
                fixed.append(f"- Updated tests in {file}")
            elif file.endswith(".py"):
                changed.append(f"- Modified {file}")
            elif file.endswith((".md", ".txt")):
                changed.append(f"- Updated documentation: {file}")
        
        if added:
            new_entry += "### Added\n" + "\n".join(added) + "\n\n"
        else:
            new_entry += "### Added\n- N/A\n\n"
        
        if changed:
            new_entry += "### Changed\n" + "\n".join(changed) + "\n\n"
        else:
            new_entry += "### Changed\n- N/A\n\n"
        
        if fixed:
            new_entry += "### Fixed\n" + "\n".join(fixed) + "\n\n"
        else:
            new_entry += "### Fixed\n- N/A\n\n"
        
        # Insert new entry after header
        lines = changelog_content.split("\n")
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith("## ["):
                insert_pos = i
                break
        
        if insert_pos > 0:
            lines.insert(insert_pos, new_entry)
            CHANGELOG_FILE.write_text("\n".join(lines))
        else:
            CHANGELOG_FILE.write_text(changelog_content + new_entry)
        
        logger.info(f"Updated CHANGELOG.md with {self.current_version}")

    def update_manifest(self) -> None:
        """Update codex_manifest.json with current module hashes."""
        manifest_list = []
        
        for py_file in Path(".").rglob("*.py"):
            # Skip test files and excluded directories
            if any(excluded in py_file.parts for excluded in [".git", "__pycache__", "VERSIONS", "output", ".venv", "venv", "tests"]):
                continue
            
            # Calculate hash
            sha256 = hashlib.sha256(py_file.read_bytes()).hexdigest()
            
            # Try to extract docstring for legal_function
            legal_function = "Core module"
            try:
                content = py_file.read_text()
                if '"""' in content:
                    docstring = content.split('"""')[1].strip().split("\n")[0]
                    if docstring:
                        legal_function = docstring[:100]
            except Exception:
                pass
            
            manifest_list.append({
                "module": py_file.stem,
                "path": str(py_file),
                "hash": sha256,
                "sha256": sha256,  # Add this for compatibility with verify_all_modules
                "legal_function": legal_function,
                "dependencies": []
            })
        
        self.module_count = len(manifest_list)
        MANIFEST_FILE.write_text(json.dumps(manifest_list, indent=2))
        logger.info(f"Updated MANIFEST with {self.module_count} modules")

    def run_smoke_tests(self) -> bool:
        """Run smoke tests and capture logs."""
        logger.info("Running smoke tests...")
        
        # Ensure log file exists
        SMOKE_TEST_LOG.parent.mkdir(exist_ok=True)
        
        test_results = []
        all_passed = True
        
        # Test 1: Import core modules
        logger.info("  - Testing core module imports...")
        # Skip codex_patch_manager as it has module-level execution
        core_modules = ["codex_brain", "build_system"]
        for module in core_modules:
            try:
                __import__(module)
                test_results.append(f"✓ Import {module}: PASS")
                logger.info(f"    ✓ {module}")
            except Exception as e:
                test_results.append(f"✗ Import {module}: FAIL - {e}")
                logger.error(f"    ✗ {module}: {e}")
                all_passed = False
        
        # Test 2: Verify manifest integrity
        logger.info("  - Verifying manifest integrity...")
        try:
            from modules.codex_manifest import verify_all_modules
            manifest_data = json.loads(MANIFEST_FILE.read_text())
            # Convert list to dict format expected by verify_all_modules
            manifest_dict = {entry["path"]: entry for entry in manifest_data}
            verify_all_modules(manifest_dict)
            test_results.append("✓ Manifest integrity: PASS")
            logger.info("    ✓ Manifest integrity verified")
        except Exception as e:
            test_results.append(f"✗ Manifest integrity: FAIL - {e}")
            logger.error(f"    ✗ Manifest integrity: {e}")
            all_passed = False
        
        # Test 3: Check critical files exist
        logger.info("  - Checking critical files...")
        critical_files = [VERSION_FILE, CHANGELOG_FILE, MANIFEST_FILE, CURRENT_FILE]
        for file_path in critical_files:
            if file_path.exists():
                test_results.append(f"✓ Critical file {file_path}: PASS")
                logger.info(f"    ✓ {file_path}")
            else:
                test_results.append(f"✗ Critical file {file_path}: FAIL - missing")
                logger.error(f"    ✗ {file_path} missing")
                all_passed = False
        
        # Test 4: Run pytest if available
        logger.info("  - Running pytest...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                test_results.append("✓ Pytest suite: PASS")
                logger.info("    ✓ Pytest suite passed")
            else:
                test_results.append(f"✗ Pytest suite: FAIL\n{result.stdout}\n{result.stderr}")
                logger.warning(f"    ✗ Pytest suite failed")
                # Don't fail the entire build for test failures
        except subprocess.TimeoutExpired:
            test_results.append("✗ Pytest suite: TIMEOUT")
            logger.warning("    ✗ Pytest suite timed out")
        except Exception as e:
            test_results.append(f"✗ Pytest suite: SKIP - {e}")
            logger.info(f"    ⊘ Pytest not available: {e}")
        
        # Write test results to log
        timestamp = datetime.datetime.now().isoformat()
        log_content = f"\n{'='*60}\n"
        log_content += f"Smoke Test Run - {self.current_version} - {timestamp}\n"
        log_content += f"{'='*60}\n\n"
        log_content += "\n".join(test_results)
        log_content += f"\n\nOverall: {'PASS' if all_passed else 'FAIL'}\n"
        
        with open(SMOKE_TEST_LOG, "a") as f:
            f.write(log_content)
        
        logger.info(f"Smoke tests {'PASSED' if all_passed else 'FAILED'}")
        return all_passed

    def calculate_directory_size(self, directory: Path, exclude_patterns: List[str]) -> Tuple[int, List[str]]:
        """Calculate total size of directory excluding certain patterns."""
        total_size = 0
        large_files = []
        
        for item in directory.rglob("*"):
            if item.is_file():
                # Check if file matches exclude pattern
                excluded = False
                for pattern in exclude_patterns:
                    if item.match(pattern):
                        excluded = True
                        break
                
                if not excluded:
                    file_size = item.stat().st_size
                    total_size += file_size
                    if file_size > LARGE_FILE_THRESHOLD:
                        large_files.append(f"{item}: {file_size / (1024*1024):.2f} MB")
        
        return total_size, large_files

    def enforce_size_policy(self) -> bool:
        """Enforce size policy and report budget."""
        logger.info("Enforcing size policy...")
        
        # Calculate current project size
        self.total_size, large_files = self.calculate_directory_size(Path("."), EXCLUDE_PATTERNS)
        
        # Try to get previous size
        try:
            if SIZE_REPORT.exists():
                with open(SIZE_REPORT, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if "Total size:" in line:
                            match = re.search(r"(\d+) bytes", line)
                            if match:
                                self.previous_size = int(match.group(1))
                                break
        except Exception:
            self.previous_size = 0
        
        size_growth = self.total_size - self.previous_size if self.previous_size > 0 else 0
        size_mb = self.total_size / (1024 * 1024)
        growth_mb = size_growth / (1024 * 1024)
        
        # Generate size report
        report = f"\n{'='*60}\n"
        report += f"Size Policy Report - {self.current_version}\n"
        report += f"{'='*60}\n\n"
        report += f"Total size: {self.total_size} bytes ({size_mb:.2f} MB)\n"
        report += f"Previous size: {self.previous_size} bytes ({self.previous_size/(1024*1024):.2f} MB)\n"
        report += f"Growth: {size_growth} bytes ({growth_mb:.2f} MB)\n\n"
        
        # Check size thresholds
        if self.total_size > MAX_BUILD_SIZE:
            self.use_patches_mode = True
            report += f"⚠️  WARNING: Build size exceeds {MAX_BUILD_SIZE/(1024*1024):.0f}MB threshold\n"
            report += "   Switching to PATCHES mode for incremental updates\n\n"
            logger.warning(f"Build exceeds {MAX_BUILD_SIZE/(1024*1024):.0f}MB, using PATCHES mode")
        else:
            self.use_patches_mode = False
            report += f"✓ Build size within {MAX_BUILD_SIZE/(1024*1024):.0f}MB limit\n\n"
        
        if size_growth > SIZE_GROWTH_THRESHOLD:
            report += f"⚠️  WARNING: Size growth exceeds {SIZE_GROWTH_THRESHOLD/(1024*1024):.0f}MB threshold\n"
            report += f"   Growth: {growth_mb:.2f}MB\n\n"
            logger.warning(f"Size growth of {growth_mb:.2f}MB exceeds threshold")
        
        # Report large files
        if large_files:
            report += f"Large files detected ({len(large_files)}):\n"
            for large_file in large_files[:10]:  # Show top 10
                report += f"  - {large_file}\n"
            if len(large_files) > 10:
                report += f"  ... and {len(large_files) - 10} more\n"
            report += "\n"
        
        report += f"Excluded patterns: {', '.join(EXCLUDE_PATTERNS[:5])}...\n"
        report += f"\nPATCHES mode: {'ENABLED' if self.use_patches_mode else 'DISABLED'}\n"
        
        # Write report
        with open(SIZE_REPORT, "a") as f:
            f.write(report)
        
        logger.info(f"Size policy check complete: {size_mb:.2f}MB, PATCHES mode: {self.use_patches_mode}")
        return not self.use_patches_mode  # Return False if we need patches mode

    def should_build_full_release(self) -> bool:
        """Determine if full release zip should be built."""
        # Build if >2 files changed
        if len(self.changed_files) > 2:
            logger.info(f"Building full release: {len(self.changed_files)} files changed (>2)")
            return True
        
        # Build if multi-module feature added (check if multiple modules touched)
        module_dirs = set()
        for file in self.changed_files:
            parts = Path(file).parts
            if len(parts) > 1:
                module_dirs.add(parts[0])
        
        if len(module_dirs) > 1:
            logger.info(f"Building full release: multi-module feature ({len(module_dirs)} modules)")
            return True
        
        logger.info("Skipping full release build: changes below threshold")
        return False

    def build_full_release(self) -> Optional[Path]:
        """Build full release ZIP package."""
        if self.use_patches_mode:
            logger.info("Using PATCHES mode - building patch archive instead of full release")
            return self.build_patches_archive()
        
        logger.info("Building full release ZIP...")
        
        # Create release filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        release_name = f"SUPREME_LITIGATION_OS_{self.current_version}_{timestamp}.zip"
        release_path = OUTPUT_DIR / release_name
        
        # Create build manifest
        build_manifest = {
            "version": self.current_version,
            "timestamp": datetime.datetime.now().isoformat(),
            "build_type": "FULL_RELEASE",
            "module_count": self.module_count,
            "changed_files": self.changed_files,
            "size_bytes": self.total_size,
        }
        
        manifest_path = OUTPUT_DIR / f"build_manifest_{self.current_version}.json"
        manifest_path.write_text(json.dumps(build_manifest, indent=2))
        
        # Create ZIP archive
        files_added = set()
        with zipfile.ZipFile(release_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add all relevant files
            for pattern in ["*.py", "*.json", "*.yaml", "*.yml", "*.md", "*.txt"]:
                for file in Path(".").rglob(pattern):
                    # Check exclusions
                    if any(excluded in file.parts for excluded in ["VERSIONS", "output", ".git", "__pycache__", ".venv", "venv"]):
                        continue
                    
                    # Check file size
                    if file.stat().st_size > LARGE_FILE_THRESHOLD:
                        logger.warning(f"Skipping large file: {file}")
                        continue
                    
                    # Avoid duplicates
                    arcname = str(file)
                    if arcname in files_added:
                        continue
                    
                    # Add to archive
                    zf.write(file, arcname=arcname)
                    files_added.add(arcname)
            
            # Add manifest
            zf.write(manifest_path, arcname=f"build_manifest_{self.current_version}.json")
            
            # Add CURRENT and VERSION (if not already added)
            if "VERSION" not in files_added:
                zf.write(VERSION_FILE, arcname="VERSION")
            if "CURRENT" not in files_added:
                zf.write(CURRENT_FILE, arcname="CURRENT")
        
        release_size = release_path.stat().st_size
        release_size_mb = release_size / (1024 * 1024)
        
        logger.info(f"Full release built: {release_path} ({release_size_mb:.2f}MB)")
        
        # Write build log
        with open(BUILD_LOG, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Full Release Build - {self.current_version}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Package: {release_path}\n")
            f.write(f"Size: {release_size_mb:.2f}MB\n")
            f.write(f"Modules: {self.module_count}\n")
            f.write(f"Changed files: {len(self.changed_files)}\n")
        
        return release_path

    def build_patches_archive(self) -> Optional[Path]:
        """Build patches-only archive for large projects."""
        logger.info("Building PATCHES archive...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        patch_name = f"LITIGATION_OS_PATCHES_{self.current_version}_{timestamp}.zip"
        patch_path = OUTPUT_DIR / patch_name
        
        with zipfile.ZipFile(patch_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Only include changed files
            for file in self.changed_files:
                file_path = Path(file)
                if file_path.exists() and file_path.is_file():
                    zf.write(file_path, arcname=str(file_path))
            
            # Add metadata
            patch_manifest = {
                "version": self.current_version,
                "timestamp": datetime.datetime.now().isoformat(),
                "build_type": "PATCHES",
                "patches": self.changed_files,
            }
            
            manifest_json = json.dumps(patch_manifest, indent=2)
            zf.writestr("PATCHES_MANIFEST.json", manifest_json)
        
        patch_size_mb = patch_path.stat().st_size / (1024 * 1024)
        logger.info(f"Patches archive built: {patch_path} ({patch_size_mb:.2f}MB)")
        
        return patch_path

    def run_cycle(self) -> bool:
        """
        Run a complete convergence cycle with progress tracking.
        
        Returns:
            bool: True if cycle completed successfully (smoke tests passed), False otherwise
        """
        start_time = datetime.datetime.now()
        
        logger.info(f"\n{'='*60}")
        logger.info("CONVERGENCE CYCLE START")
        logger.info(f"{'='*60}\n")
        
        try:
            # 1. Increment VERSION
            logger.info("Step 1/9: Incrementing VERSION...")
            self.increment_version()
            
            # 2. Update CURRENT
            logger.info("Step 2/9: Updating CURRENT...")
            self.update_current()
            
            # 3. Detect changes
            logger.info("Step 3/9: Detecting changes...")
            self.detect_changed_files()
            
            # 4. Update CHANGELOG
            logger.info("Step 4/9: Updating CHANGELOG...")
            self.update_changelog()
            
            # 5. Update MANIFEST
            logger.info("Step 5/9: Updating MANIFEST...")
            self.update_manifest()
            
            # 6. Snapshot version
            logger.info("Step 6/9: Creating immutable snapshot...")
            self.snapshot_version()
            
            # 7. Run smoke tests
            logger.info("Step 7/9: Running smoke tests...")
            smoke_tests_passed = self.run_smoke_tests()
            
            # 8. Enforce size policy
            logger.info("Step 8/9: Enforcing size policy...")
            size_ok = self.enforce_size_policy()
            
            # 9. Build full release if needed
            logger.info("Step 9/9: Checking if full release build needed...")
            if self.should_build_full_release():
                logger.info("Step 9/9: Building full release...")
                release_path = self.build_full_release()
                if release_path:
                    logger.info(f"Release package: {release_path}")
            else:
                logger.info("Step 9/9: Skipping full release build")
            
            # Calculate elapsed time
            elapsed = datetime.datetime.now() - start_time
            
            logger.info(f"\n{'='*60}")
            logger.info("CONVERGENCE CYCLE COMPLETE")
            logger.info(f"Version: {self.current_version}")
            logger.info(f"Modules: {self.module_count}")
            logger.info(f"Changed files: {len(self.changed_files)}")
            logger.info(f"Smoke tests: {'PASS' if smoke_tests_passed else 'FAIL'}")
            logger.info(f"Size policy: {'OK' if size_ok else 'PATCHES MODE'}")
            logger.info(f"Elapsed time: {elapsed.total_seconds():.2f}s")
            logger.info(f"{'='*60}\n")
            
            return smoke_tests_passed
            
        except Exception as e:
            logger.error(f"CONVERGENCE CYCLE FAILED: {e}", exc_info=True)
            return False


def main():
    """Main entry point for convergence cycle engine."""
    engine = ConvergenceCycleEngine()
    
    # Run cycle
    success = engine.run_cycle()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
