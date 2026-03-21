"""LitigationOS Installer Build Orchestrator.

Automates the full build pipeline:
  1. Check prerequisites (Python, pip, PyInstaller, Inno Setup)
  2. Build frozen executable via PyInstaller
  3. Copy runtime assets (icons, databases, configs) into dist
  4. Compile Windows installer via Inno Setup (ISCC.exe)

Usage:
    python build_installer.py              # full build
    python build_installer.py --status     # show build status
    python build_installer.py --exe-only   # build exe without installer

IMPORTANT: Never set CWD to the repo root — shadow modules will break imports.
"""

from __future__ import annotations

import argparse
import datetime
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — all relative to THIS file so CWD never matters
# ---------------------------------------------------------------------------
INSTALLER_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = INSTALLER_DIR.parent                       # 11_CODE/litigationos
SRC_DIR = PACKAGE_DIR / "src"                            # 11_CODE/litigationos/src
ASSETS_DIR = PACKAGE_DIR / "assets"                      # 11_CODE/litigationos/assets
DIST_DIR = INSTALLER_DIR / "dist"                        # installer/dist
BUILD_DIR = INSTALLER_DIR / "build"                      # installer/build (PyInstaller work)
OUTPUT_DIR = INSTALLER_DIR / "output"                    # installer/output (final .exe)
LICENSE_FILE = PACKAGE_DIR / "LICENSE"
REPO_ROOT = PACKAGE_DIR.parent.parent                    # C:\Users\andre\LitigationOS

# Database locations (runtime data — copied into dist for frozen builds)
LITIGATION_DB = REPO_ROOT / "litigation_context.db"
COURT_FORMS_DB = REPO_ROOT / "court_forms.db"
DATABASES_DIR = REPO_ROOT / "databases"

# PyInstaller entry point
ENTRY_POINT = SRC_DIR / "litigationos" / "app.py"

# Inno Setup compiler — common install locations
ISCC_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
]

APP_NAME = "litigationos"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_installer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, log the command, and return the result.

    Always uses the *installer* directory as CWD unless overridden — never
    the repo root (shadow modules would break Python imports).
    """
    effective_cwd = cwd or INSTALLER_DIR
    log.info("Running: %s  (cwd=%s)", " ".join(cmd), effective_cwd)
    result = subprocess.run(
        cmd,
        cwd=str(effective_cwd),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines()[-20:]:
            log.debug("  stdout: %s", line)
    if result.returncode != 0:
        log.error("Command failed (rc=%d):", result.returncode)
        for line in result.stderr.strip().splitlines()[-30:]:
            log.error("  stderr: %s", line)
        if check:
            raise RuntimeError(
                f"Command failed (rc={result.returncode}): {' '.join(cmd)}\n"
                f"{result.stderr[-500:]}"
            )
    return result


def _find_iscc() -> Path | None:
    """Locate the Inno Setup compiler (ISCC.exe)."""
    # Check PATH first
    iscc_on_path = shutil.which("ISCC") or shutil.which("ISCC.exe")
    if iscc_on_path:
        return Path(iscc_on_path)
    # Check common install locations
    for candidate in ISCC_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _file_info(path: Path) -> dict:
    """Return size and mtime for a file, or None values if missing."""
    if path.exists():
        stat = path.stat()
        return {
            "path": str(path),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        }
    return {"path": str(path), "size_mb": None, "modified": None}


# ---------------------------------------------------------------------------
# InstallerBuilder
# ---------------------------------------------------------------------------

class InstallerBuilder:
    """Orchestrates the complete LitigationOS installer build pipeline."""

    def __init__(self) -> None:
        self._iscc_path: Path | None = None
        self._pyinstaller_available: bool = False

    # ---- Step 1: Prerequisites -------------------------------------------

    def check_prerequisites(self) -> dict:
        """Verify that required build tools are available.

        Returns a dict with tool availability and version info.
        """
        log.info("=" * 60)
        log.info("Step 1 — Checking prerequisites")
        log.info("=" * 60)

        results: dict[str, dict] = {}

        # Python
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_ok = sys.version_info >= (3, 12)
        results["python"] = {"version": py_version, "ok": py_ok, "path": sys.executable}
        log.info("Python %s — %s", py_version, "OK" if py_ok else "NEED >=3.12")

        # pip
        pip_result = _run([sys.executable, "-m", "pip", "--version"], check=False)
        pip_ok = pip_result.returncode == 0
        results["pip"] = {"ok": pip_ok, "output": pip_result.stdout.strip()[:120]}
        log.info("pip — %s", "OK" if pip_ok else "MISSING")

        # PyInstaller
        pi_result = _run([sys.executable, "-m", "PyInstaller", "--version"], check=False)
        self._pyinstaller_available = pi_result.returncode == 0
        pi_version = pi_result.stdout.strip() if self._pyinstaller_available else None
        results["pyinstaller"] = {"version": pi_version, "ok": self._pyinstaller_available}
        if self._pyinstaller_available:
            log.info("PyInstaller %s — OK", pi_version)
        else:
            log.warning("PyInstaller — MISSING. Install: pip install 'pyinstaller>=6.0.0'")

        # Inno Setup
        self._iscc_path = _find_iscc()
        iscc_ok = self._iscc_path is not None
        results["inno_setup"] = {"ok": iscc_ok, "path": str(self._iscc_path) if iscc_ok else None}
        if iscc_ok:
            log.info("Inno Setup — OK (%s)", self._iscc_path)
        else:
            log.warning(
                "Inno Setup — NOT FOUND\n"
                "  Download from: https://jrsoftware.org/isdl.php\n"
                "  Install Inno Setup 6.x and ensure ISCC.exe is on PATH\n"
                "  or installed at: C:\\Program Files (x86)\\Inno Setup 6\\"
            )

        # Platform
        results["platform"] = {
            "os": platform.system(),
            "arch": platform.machine(),
            "ok": platform.system() == "Windows",
        }

        # Source files
        entry_ok = ENTRY_POINT.exists()
        results["entry_point"] = {"path": str(ENTRY_POINT), "ok": entry_ok}
        log.info("Entry point %s — %s", ENTRY_POINT.name, "OK" if entry_ok else "MISSING")

        all_ok = all(r.get("ok", False) for r in results.values())
        results["all_ok"] = all_ok
        if all_ok:
            log.info("All prerequisites satisfied ✓")
        else:
            log.warning("Some prerequisites are missing — see warnings above")

        return results

    # ---- Step 2: Build executable ----------------------------------------

    def build_executable(self) -> str:
        """Build the frozen executable with PyInstaller.

        Returns the path to the generated exe.
        """
        log.info("=" * 60)
        log.info("Step 2 — Building executable with PyInstaller")
        log.info("=" * 60)

        if not self._pyinstaller_available:
            raise RuntimeError(
                "PyInstaller is not installed. Run: pip install 'pyinstaller>=6.0.0'"
            )

        # Ensure clean build directories
        for d in (DIST_DIR, BUILD_DIR):
            if d.exists():
                log.info("Cleaning %s", d)
                shutil.rmtree(d)
            d.mkdir(parents=True, exist_ok=True)

        # Resolve icon path (may not exist yet — PyInstaller will warn)
        icon_path = ASSETS_DIR / "icon.ico"
        icon_arg = f"--icon={icon_path}" if icon_path.exists() else ""

        # Build the add-data args for bundled databases
        add_data: list[str] = []
        if LITIGATION_DB.exists():
            add_data.extend(["--add-data", f"{LITIGATION_DB}{os.pathsep}data"])
            log.info("Bundling litigation_context.db (%d MB)", LITIGATION_DB.stat().st_size // (1024 * 1024))
        if COURT_FORMS_DB.exists():
            add_data.extend(["--add-data", f"{COURT_FORMS_DB}{os.pathsep}data"])
            log.info("Bundling court_forms.db")
        if DATABASES_DIR.exists():
            db_files = list(DATABASES_DIR.glob("*.db"))
            if db_files:
                add_data.extend(["--add-data", f"{DATABASES_DIR}{os.pathsep}databases"])
                log.info("Bundling %d jurisdiction databases", len(db_files))

        # Bundle package assets (icons, templates)
        pkg_assets = SRC_DIR / "litigationos" / "assets"
        if pkg_assets.exists():
            add_data.extend(["--add-data", f"{pkg_assets}{os.pathsep}litigationos/assets"])

        # Hidden imports for dynamic dependencies
        hidden_imports = [
            "--hidden-import=customtkinter",
            "--hidden-import=pydantic",
            "--hidden-import=typer",
            "--hidden-import=rich",
            "--hidden-import=PIL",
            "--hidden-import=tkcalendar",
            "--hidden-import=sklearn",
            "--hidden-import=jinja2",
            "--hidden-import=docx",
            "--hidden-import=reportlab",
            "--hidden-import=pypdf",
        ]

        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", APP_NAME,
            "--noconsole",
            "--distpath", str(DIST_DIR),
            "--workpath", str(BUILD_DIR),
            "--specpath", str(INSTALLER_DIR),
            "--noconfirm",
            "--clean",
            *hidden_imports,
            *add_data,
        ]

        if icon_arg:
            cmd.append(icon_arg)

        # Paths to search for imports — use src dir, NOT repo root
        cmd.extend(["--paths", str(SRC_DIR)])
        cmd.append(str(ENTRY_POINT))

        _run(cmd, cwd=INSTALLER_DIR)

        exe_path = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            log.info("Executable built: %s (%.1f MB)", exe_path, size_mb)
            return str(exe_path)

        raise RuntimeError(f"PyInstaller completed but exe not found at {exe_path}")

    # ---- Step 3: Copy assets ---------------------------------------------

    def copy_assets(self) -> None:
        """Copy runtime assets into the dist directory alongside the exe."""
        log.info("=" * 60)
        log.info("Step 3 — Copying assets to dist")
        log.info("=" * 60)

        target = DIST_DIR / APP_NAME
        if not target.exists():
            raise RuntimeError(f"Dist directory does not exist: {target}. Run build_executable first.")

        # Icon
        icon_src = ASSETS_DIR / "icon.ico"
        if icon_src.exists():
            shutil.copy2(icon_src, target / "icon.ico")
            log.info("Copied icon.ico")
        else:
            log.warning("icon.ico not found at %s — installer may show default icon", icon_src)

        # LICENSE
        if LICENSE_FILE.exists():
            shutil.copy2(LICENSE_FILE, target / "LICENSE")
            log.info("Copied LICENSE")

        # Data directory (for runtime DB access)
        data_target = target / "data"
        data_target.mkdir(exist_ok=True)

        # Config templates
        config_src = PACKAGE_DIR / "data"
        if config_src.exists():
            for f in config_src.iterdir():
                if f.is_file():
                    shutil.copy2(f, data_target / f.name)
                    log.info("Copied data/%s", f.name)

        # README
        readme = PACKAGE_DIR / "README.md"
        if readme.exists():
            shutil.copy2(readme, target / "README.md")
            log.info("Copied README.md")

        log.info("Asset copy complete ✓")

    # ---- Step 4: Build installer -----------------------------------------

    def build_installer(self) -> str:
        """Compile the Inno Setup installer (.exe).

        Returns the path to the generated installer.
        """
        log.info("=" * 60)
        log.info("Step 4 — Building installer with Inno Setup")
        log.info("=" * 60)

        if self._iscc_path is None:
            self._iscc_path = _find_iscc()
        if self._iscc_path is None:
            raise RuntimeError(
                "Inno Setup compiler (ISCC.exe) not found.\n"
                "Download from: https://jrsoftware.org/isdl.php\n"
                "Install Inno Setup 6.x and add to PATH, or install to:\n"
                "  C:\\Program Files (x86)\\Inno Setup 6\\"
            )

        iss_file = INSTALLER_DIR / "setup.iss"
        if not iss_file.exists():
            raise RuntimeError(f"setup.iss not found at {iss_file}")

        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        cmd = [str(self._iscc_path), str(iss_file)]
        _run(cmd, cwd=INSTALLER_DIR)

        installer_path = OUTPUT_DIR / f"LitigationOS-Setup-{APP_VERSION}.exe"
        if installer_path.exists():
            size_mb = installer_path.stat().st_size / (1024 * 1024)
            log.info("Installer built: %s (%.1f MB)", installer_path, size_mb)
            return str(installer_path)

        # Inno Setup may have succeeded but output name differs — check output dir
        exes = list(OUTPUT_DIR.glob("*.exe"))
        if exes:
            log.warning("Expected filename not found; found: %s", exes[0].name)
            return str(exes[0])

        raise RuntimeError(f"ISCC completed but installer not found in {OUTPUT_DIR}")

    # ---- Step 5: Full pipeline -------------------------------------------

    def full_build(self) -> str:
        """Run the complete build pipeline: prerequisites → exe → assets → installer.

        Returns the path to the final installer executable.
        """
        log.info("#" * 60)
        log.info("# LitigationOS Installer Build — Full Pipeline")
        log.info("# Version: %s", APP_VERSION)
        log.info("# Timestamp: %s", datetime.datetime.now().isoformat(timespec="seconds"))
        log.info("#" * 60)

        prereqs = self.check_prerequisites()
        if not prereqs.get("all_ok"):
            missing = [k for k, v in prereqs.items() if isinstance(v, dict) and not v.get("ok", True)]
            raise RuntimeError(f"Missing prerequisites: {', '.join(missing)}")

        self.build_executable()
        self.copy_assets()
        installer_path = self.build_installer()

        log.info("#" * 60)
        log.info("# BUILD COMPLETE")
        log.info("# Installer: %s", installer_path)
        log.info("#" * 60)

        return installer_path

    # ---- Status check ----------------------------------------------------

    def get_build_status(self) -> dict:
        """Report what has been built so far, with sizes and timestamps."""
        log.info("Build Status Report")
        log.info("-" * 40)

        status: dict[str, object] = {
            "version": APP_VERSION,
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        }

        # Executable
        exe_path = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
        status["executable"] = _file_info(exe_path)
        exists_label = "EXISTS" if exe_path.exists() else "not built"
        log.info("Executable: %s", exists_label)

        # Dist directory size
        if (DIST_DIR / APP_NAME).exists():
            total_size = sum(
                f.stat().st_size for f in (DIST_DIR / APP_NAME).rglob("*") if f.is_file()
            )
            status["dist_size_mb"] = round(total_size / (1024 * 1024), 2)
            status["dist_file_count"] = sum(1 for _ in (DIST_DIR / APP_NAME).rglob("*") if _.is_file())
            log.info("Dist: %.1f MB, %d files", status["dist_size_mb"], status["dist_file_count"])
        else:
            status["dist_size_mb"] = 0
            status["dist_file_count"] = 0

        # Installer
        installer_path = OUTPUT_DIR / f"LitigationOS-Setup-{APP_VERSION}.exe"
        status["installer"] = _file_info(installer_path)
        exists_label = "EXISTS" if installer_path.exists() else "not built"
        log.info("Installer: %s", exists_label)

        # Prerequisites
        status["iscc_available"] = _find_iscc() is not None
        pi_result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        status["pyinstaller_available"] = pi_result.returncode == 0

        # Source databases available for bundling
        status["databases"] = {
            "litigation_context_db": LITIGATION_DB.exists(),
            "court_forms_db": COURT_FORMS_DB.exists(),
            "jurisdiction_dbs": len(list(DATABASES_DIR.glob("*.db"))) if DATABASES_DIR.exists() else 0,
        }

        log.info("-" * 40)
        return status


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments and run the appropriate build step."""
    parser = argparse.ArgumentParser(
        description="LitigationOS Installer Build Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python build_installer.py              # full build\n"
            "  python build_installer.py --status     # show build status\n"
            "  python build_installer.py --exe-only   # build exe only\n"
            "  python build_installer.py --check      # check prerequisites\n"
        ),
    )
    parser.add_argument("--status", action="store_true", help="Show current build status")
    parser.add_argument("--exe-only", action="store_true", help="Build executable without installer")
    parser.add_argument("--check", action="store_true", help="Check prerequisites only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    builder = InstallerBuilder()

    try:
        if args.status:
            import json
            status = builder.get_build_status()
            print(json.dumps(status, indent=2, default=str))
        elif args.check:
            builder.check_prerequisites()
        elif args.exe_only:
            builder.check_prerequisites()
            builder.build_executable()
            builder.copy_assets()
            log.info("Executable build complete (installer step skipped)")
        else:
            builder.full_build()
    except RuntimeError as exc:
        log.error("BUILD FAILED: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        log.warning("Build interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
