#!/usr/bin/env python3
"""Build GRAPHFORGE Gumroad ZIP package."""
import zipfile, shutil
from pathlib import Path
from datetime import datetime

SRC = Path(r"C:\Users\andre\LitigationOS\scripts\cortex\graphforge.py")
OUT_DIR = Path(r"J:\CORTEX\gumroad_packages")
OUT_DIR.mkdir(parents=True, exist_ok=True)
ZIP_PATH = OUT_DIR / "CORTEX_GRAPHFORGE.zip"

README = """# GRAPHFORGE - Universal Database Visualizer
## Part of the CORTEX Intelligence Platform

Turn ANY SQLite database or CSV file into an interactive force-directed graph visualization.

## Quick Start
```
python graphforge.py scan your_database.db
python graphforge.py graph your_database.db --output graph.html
python graphforge.py serve your_database.db
```

## Commands
- **scan** - Discover tables, columns, row counts, and relationships
- **graph** - Generate interactive HTML graph from any SQLite database
- **csv** - Generate graph from CSV/JSON files
- **merge** - Merge multiple databases into one visualization
- **export** - Export graph data as JSON or CSV
- **serve** - Launch local browser viewer with live reload

## Features
- Zero dependencies (Python 3.8+ stdlib only)
- Automatic relationship detection (foreign keys + naming conventions)
- 6 color palettes (neon, ocean, fire, forest, cyber, grayscale)
- Canvas 2D rendering with force-directed physics
- HUD with real-time stats
- Search, filter, zoom, pan
- Configurable node limits (default 500)
- Works with ANY SQLite database or CSV file

## Pricing
$29 one-time purchase | Part of CORTEX Bundle ($79)

(c) 2025 CORTEX Intelligence Platform
"""

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(SRC, "graphforge.py")
    zf.writestr("README.md", README)
    zf.writestr("LICENSE", "MIT License\n\nCopyright (c) 2025 CORTEX Intelligence\n\n"
                "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
                "of this software and associated documentation files (the \"Software\"), to deal\n"
                "in the Software without restriction, including without limitation the rights\n"
                "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
                "copies of the Software, and to permit persons to whom the Software is\n"
                "furnished to do so, subject to the following conditions:\n\n"
                "The above copyright notice and this permission notice shall be included in all\n"
                "copies or substantial portions of the Software.\n\n"
                "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND.\n")

size = ZIP_PATH.stat().st_size
print(f"  Built: {ZIP_PATH}")
print(f"  Size: {size:,} bytes")
print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
