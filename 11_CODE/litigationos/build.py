"""Build LitigationOS Windows executable using PyInstaller."""

import sys
from pathlib import Path

import PyInstaller.__main__


def build():
    """Create a standalone Windows executable."""
    root = Path(__file__).parent

    # Resolve paths
    entry = root / "src" / "litigationos" / "app.py"
    schema = root / "src" / "litigationos" / "db" / "schema.sql"
    plugins = root / "src" / "litigationos" / "plugins"
    data_dir = root / "data"
    icon = root / "assets" / "icon.ico"

    args = [
        str(entry),
        "--name=LitigationOS",
        "--onedir",
        "--windowed",
        f"--add-data={schema};litigationos/db/",
        f"--distpath={root / 'dist'}",
        f"--workpath={root / 'build'}",
        "--clean",
        "--noconfirm",
        # Hidden imports that PyInstaller may miss
        "--hidden-import=customtkinter",
        "--hidden-import=pydantic",
        "--hidden-import=jinja2",
        "--hidden-import=jinja2.ext",
        "--hidden-import=docx",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=rich",
        "--hidden-import=typer",
        "--hidden-import=pypdf",
        # All engine modules
        "--hidden-import=litigationos.engines.ai",
        "--hidden-import=litigationos.engines.court_rules",
        "--hidden-import=litigationos.engines.deadline",
        "--hidden-import=litigationos.engines.document",
        "--hidden-import=litigationos.engines.evidence",
        "--hidden-import=litigationos.engines.filing",
        "--hidden-import=litigationos.engines.rag",
        "--hidden-import=litigationos.engines.settings",
        # GUI modules
        "--hidden-import=litigationos.gui.app",
        "--hidden-import=litigationos.gui.dashboard",
        "--hidden-import=litigationos.gui.case_manager",
        "--hidden-import=litigationos.gui.filing_manager",
        "--hidden-import=litigationos.gui.filing_wizard",
        "--hidden-import=litigationos.gui.evidence_browser",
        "--hidden-import=litigationos.gui.evidence_map",
        "--hidden-import=litigationos.gui.document_editor",
        "--hidden-import=litigationos.gui.deadline_dashboard",
        "--hidden-import=litigationos.gui.calendar_view",
        "--hidden-import=litigationos.gui.timeline_view",
        "--hidden-import=litigationos.gui.settings_screen",
        # DB and models
        "--hidden-import=litigationos.db.connection",
        "--hidden-import=litigationos.db.seed",
        "--hidden-import=litigationos.config",
        # Plugins
        "--hidden-import=litigationos.plugins",
        "--hidden-import=litigationos.plugins.michigan",
        # Exclude heavy packages not needed at runtime
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=numpy",
        "--exclude-module=matplotlib",
        "--exclude-module=pytest",
        "--exclude-module=chromadb",
        "--exclude-module=ollama",
        "--exclude-module=IPython",
        "--exclude-module=notebook",
        "--exclude-module=numba",
        "--exclude-module=llvmlite",
        "--exclude-module=pyarrow",
        "--exclude-module=sqlalchemy",
    ]

    if icon.exists():
        args.append(f"--icon={icon}")

    # Include plugins data
    if plugins.exists():
        args.append(f"--add-data={plugins};litigationos/plugins/")

    # Include data directory
    if data_dir.exists():
        args.append(f"--add-data={data_dir};data/")

    # Collect customtkinter data files (themes, etc.)
    try:
        import customtkinter

        ctk_path = Path(customtkinter.__file__).parent
        args.append(f"--add-data={ctk_path};customtkinter/")
    except ImportError:
        print("WARNING: customtkinter not found -- install it first.", file=sys.stderr)

    PyInstaller.__main__.run(args)
    print(f"\nBuild complete! Output: {root / 'dist' / 'LitigationOS'}")


if __name__ == "__main__":
    build()
