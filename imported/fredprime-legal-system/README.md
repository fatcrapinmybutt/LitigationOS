# FRED PRIME Litigation System

A Python-based legal automation toolkit for managing Michigan court cases — exhibits, motions, forms, timelines, and more.

## Features

- **Auto-label exhibits** in a folder (`Exhibit_A`, `Exhibit_B`, ...)
- **Link motions to exhibits** by scanning motion text files
- **Validate signature blocks** (Michigan Court Rule 1.109(D)(3))
- **Timeline builder** for fact chronology
- **Warboard engine** for case visualization
- **FOIA request builder**
- **Form database** with SQLite backend
- **Drive organizer** with multi-platform support
- **Codex manifest** for module integrity verification

## Setup

Python 3.10+ is required. Clone the repo and install:

```bash
pip install -e ".[dev]"
```

Or for a minimal install:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 fredprime.py label-exhibits path/to/exhibits
python3 fredprime.py link-motions path/to/motions
python3 fredprime.py validate-signature path/to/document.txt
python3 fredprime.py --help
```

Run the full assembler:

```bash
python3 litigation_os_assembler.py --help
```

## Repository Structure

```
fredprime-legal-system/
├── fredprime.py               # Main CLI entry point
├── firstimport.py             # System-definition bootstrap
├── litigation_os_assembler.py # Full assembly pipeline
├── build_system.py            # Build configuration generator
│
├── src/                       # Core source modules
│   ├── exhibit_labeler.py
│   ├── motion_exhibit_linker.py
│   ├── signature_validator.py
│   ├── form_db.py
│   ├── knowledge_store.py
│   ├── config.py
│   ├── neo4j_sanitizer.py
│   ├── neo4j_import_hygiene.py
│   └── utils/
│
├── modules/                   # Pluggable analysis modules
│   ├── codex_guardian.py
│   ├── codex_manifest.py
│   ├── codex_supreme.py
│   ├── benchbook_loader.py
│   └── ...
│
├── core/                      # Codex orchestration & forensic engine
│   ├── codex_brain.py
│   ├── codex_absorption_engine.py
│   ├── codex_patch_manager.py
│   └── forensic_compliance_validator.py
│
├── cli/                       # Command-line tools
│   ├── generate_manifest.py
│   ├── organize_drive.py
│   └── fts_cli.py
│
├── scripts/                   # Utility & maintenance scripts
│   ├── generate_manifest.py
│   ├── graph_preview.py
│   ├── zip_validator.py
│   └── ...
│
├── litigationos/              # Drive configuration package
│   └── config/
│       ├── drives.py
│       └── __init__.py
│
├── CONFIG/                    # Configuration templates
│   └── drives.toml.example
│
├── warboard/                  # Case visualization engine
├── timeline/                  # Timeline builder
├── binder/                    # Document binder utilities
├── foia/                      # FOIA request tools
├── motions/                   # Motion generators
├── notices/                   # Legal notices
├── violations/                # Misconduct documentation
├── federal/                   # Federal complaint generators
├── entity_trace/              # Corporate entity mapping
├── scheduling/                # Court date calculator
├── scanner/                   # Evidence scanner / OCR intake
├── contradictions/            # Contradiction matrix
├── mifile/                    # Michigan e-filing stack
├── press/                     # Press release drafts
│
├── forms/                     # Michigan court form templates
├── data/                      # JSON data files
├── docs/                      # Extended documentation
├── notebooks/                 # Jupyter notebooks
├── pyinstaller/               # PyInstaller spec files
├── archive/                   # Legacy / historical scripts
│
└── tests/                     # Full test suite
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

## Documentation

Extended docs live in [`docs/`](docs/):

- [Quick Reference](docs/QUICK_REFERENCE.md)
- [Advanced Development](docs/ADVANCED_DEVELOPMENT.md)
- [Bootstrap Prerequisites](docs/bootstrap_prerequisites.md)
- [Windows Drive Organizer Runbook](docs/windows_drive_organizer_runbook.md)
