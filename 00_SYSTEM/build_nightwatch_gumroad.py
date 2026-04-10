"""Build NIGHTWATCH Gumroad ZIP package."""
import zipfile
import os
from pathlib import Path

OUT_DIR = Path(r"J:\CORTEX\gumroad_packages")
OUT_DIR.mkdir(parents=True, exist_ok=True)

NW_SCRIPT = Path(r"C:\Users\andre\LitigationOS\scripts\cortex\nightwatch.py")

README_CONTENT = """# NIGHTWATCH - File Change Intelligence Monitor

> Real-time file monitoring, tamper detection, and forensic audit trails.

## What is NIGHTWATCH?

NIGHTWATCH is a standalone Python tool that monitors directories for file changes,
detects tampering via SHA-256 hashing, classifies events by severity, and generates
professional HTML dashboards and searchable audit trails.

**Perfect for:**
- Evidence preservation & chain of custody monitoring
- Compliance auditing (SOX, HIPAA, PCI-DSS file integrity)
- Insider threat detection (suspicious file modifications)
- IT asset change tracking and drift detection
- Legal hold monitoring and spoliation prevention
- DevOps config drift detection

## Features

- **Real-time monitoring** with configurable polling intervals
- **SHA-256 tamper detection** on every file change
- **Severity classification** (CRITICAL / HIGH / MEDIUM / INFO)
- **Suspicious file detection** (.exe, .dll, .bat, .ps1 in unexpected locations)
- **Sensitive data pattern matching** (passwords, API keys, credentials)
- **Full-text search** across all events (SQLite FTS5)
- **HTML dashboard** with interactive charts and event tables
- **CSV/JSON export** for integration with SIEM tools
- **SQLite audit trail** - tamper-evident, queryable, portable

## Quick Start

```bash
# First scan - baseline your directory
python nightwatch.py scan /path/to/monitor

# Re-scan to detect changes
python nightwatch.py scan /path/to/monitor

# Real-time monitoring
python nightwatch.py watch /path/to/monitor --interval 30

# Search events
python nightwatch.py search "deleted OR modified"

# Generate dashboard
python nightwatch.py dashboard -o report.html

# Export to CSV
python nightwatch.py export -o changes.csv --format csv

# View statistics
python nightwatch.py stats
```

## Commands

| Command | Description |
|---------|-------------|
| `scan` | Scan directory and detect changes from last baseline |
| `watch` | Real-time continuous monitoring with alerts |
| `search` | Full-text search across all recorded events |
| `dashboard` | Generate interactive HTML dashboard |
| `export` | Export events to CSV or JSON |
| `stats` | Show summary statistics |

## Options

- `--db PATH` - Custom database location (default: nightwatch.db)
- `--ext .py .json` - Filter by file extensions
- `--no-hash` - Skip SHA-256 hashing (faster scans)
- `--interval N` - Polling interval in seconds (watch mode)
- `--severity LEVEL` - Filter by minimum severity
- `--format csv|json` - Export format
- `-o PATH` - Output file path

## Requirements

- Python 3.10+
- No external dependencies (stdlib only!)

## License

MIT License - Use freely in any project.

---
*Part of the CORTEX Intelligence Platform - https://fatcrapinmybutt.github.io/cortex-site/*
"""

SAMPLE_CONFIG = """{
    "watch_paths": [
        "/path/to/evidence",
        "/path/to/legal/filings"
    ],
    "extensions": [".pdf", ".docx", ".xlsx", ".json", ".xml"],
    "ignore_patterns": ["*.tmp", "*.log", "~$*", ".git/*"],
    "poll_interval_seconds": 30,
    "alert_on_severity": "HIGH",
    "hash_algorithm": "sha256",
    "max_file_size_mb": 500,
    "dashboard_auto_refresh": true
}
"""

zip_path = OUT_DIR / "CORTEX_NIGHTWATCH.zip"

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(NW_SCRIPT, "NIGHTWATCH/nightwatch.py")
    zf.writestr("NIGHTWATCH/README.md", README_CONTENT)
    zf.writestr("NIGHTWATCH/sample_config.json", SAMPLE_CONFIG)

size_kb = zip_path.stat().st_size / 1024
print(f"NIGHTWATCH ZIP: {zip_path} ({size_kb:.1f} KB)")
print("Contents:")
with zipfile.ZipFile(zip_path, "r") as zf:
    for info in zf.infolist():
        print(f"  {info.filename} ({info.file_size:,} bytes)")
