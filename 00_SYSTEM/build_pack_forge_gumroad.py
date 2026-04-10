"""Build Pack Forge Gumroad ZIP package."""
import zipfile, shutil, os, json
from pathlib import Path
from datetime import datetime

OUT = Path(r"J:\CORTEX\gumroad_packages")
OUT.mkdir(parents=True, exist_ok=True)

FORGE = Path(r"C:\Users\andre\LitigationOS\scripts\cortex\pack_forge.py")
SCHEMA = Path(r"C:\Users\andre\LitigationOS\scripts\cortex\cortex_schema.py")

# Create Pack Forge README
readme = """# CORTEX Pack Forge - Domain Pack Creator & Editor

> Create custom intelligence domain packs for the CORTEX Graph Intelligence Platform

## What You Get

- **pack_forge.py** - Full CLI tool for creating, validating, and managing domain packs
- **cortex_schema.py** - Core schema engine (required dependency)
- **8 built-in templates** - OSINT, Cyber, Legal, Finance, Healthcare, Journalism, Supply Chain, Real Estate
- **Interactive wizard** - Step-by-step pack creation with prompts
- **Schema validator** - Verify packs before loading into CORTEX

## Quick Start

```bash
# Generate a pack from built-in template
python pack_forge.py template corporate -o my_corporate_pack.json

# Create a custom pack interactively
python pack_forge.py create -o my_custom_pack.json

# Validate an existing pack
python pack_forge.py validate my_pack.json

# List all available templates
python pack_forge.py catalog
```

## Built-in Templates

| Template | Entities | Categories | Focus Modes |
|----------|----------|------------|-------------|
| OSINT | 25 | 15 | 8 |
| Cyber | 22 | 12 | 8 |
| Legal | 20 | 14 | 8 |
| Finance | 24 | 15 | 8 |
| Healthcare | 22 | 14 | 8 |
| Journalism | 20 | 12 | 8 |
| Supply Chain | 25 | 15 | 8 |
| Real Estate | 22 | 14 | 8 |

## Creating Custom Packs

1. Start with a template: `python pack_forge.py template osint -o base.json`
2. Edit the JSON to customize entities, categories, authorities, and focus modes
3. Validate: `python pack_forge.py validate base.json`
4. Load into CORTEX and hunt!

## Pack Format (RICH)

```json
{
  "name": "My Domain",
  "version": "1.0.0",
  "description": "Custom intelligence domain",
  "entities": {
    "Person": {
      "patterns": ["\\\\b[A-Z][a-z]+ [A-Z][a-z]+\\\\b"],
      "color": "#ff6b6b",
      "shape": "circle"
    }
  },
  "categories": {
    "Category Name": {
      "keywords": ["keyword1", "keyword2"],
      "color": "#4ecdc4",
      "priority": "high"
    }
  }
}
```

## Requirements

- Python 3.10+
- No external dependencies (stdlib only)

## Support

- Landing Page: https://fatcrapinmybutt.github.io/cortex-site/
- Full Platform: https://andrewpioneer6.gumroad.com/

---
*Pack Forge is part of the CORTEX Graph Intelligence Platform*
"""

# Build ZIP
zip_path = OUT / "CORTEX_Pack_Forge.zip"
with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
    # Core files
    zf.write(str(FORGE), "pack_forge.py")
    zf.write(str(SCHEMA), "cortex_schema.py")
    zf.writestr("README.md", readme)
    zf.writestr("LICENSE", "MIT License\n\nCopyright (c) 2026 Andrew Pioneer\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software...")
    
    # Generate a sample pack
    sample = {
        "name": "Sample Corporate Intelligence",
        "version": "1.0.0",
        "description": "Example corporate investigation pack - customize for your needs",
        "author": "Pack Forge",
        "license": "MIT",
        "tags": ["corporate", "investigation", "due-diligence"],
        "entities": {
            "Person": {"patterns": ["\\b[A-Z][a-z]+ [A-Z][a-z]+\\b"], "color": "#ff6b6b", "shape": "circle"},
            "Company": {"patterns": ["\\b[A-Z][A-Za-z]+ (?:Inc|LLC|Corp|Ltd|Co)\\b"], "color": "#4ecdc4", "shape": "diamond"},
            "Amount": {"patterns": ["\\$[\\d,]+(?:\\.\\d{2})?"], "color": "#ffd93d", "shape": "triangle"}
        },
        "categories": {
            "Financial Activity": {"keywords": ["revenue", "profit", "loss", "transaction", "payment"], "color": "#4ecdc4", "priority": "high"},
            "Legal Action": {"keywords": ["lawsuit", "complaint", "settlement", "litigation"], "color": "#ff6b6b", "priority": "high"},
            "Risk Indicator": {"keywords": ["fraud", "suspicious", "irregular", "violation"], "color": "#e74c3c", "priority": "critical"}
        },
        "authorities": {
            "SEC Filing": {"patterns": ["\\bSEC\\b.*\\b(?:10-K|10-Q|8-K|S-1)\\b"], "type": "regulatory"},
            "Court Case": {"patterns": ["\\b\\d+:\\d+-cv-\\d+\\b"], "type": "judicial"}
        },
        "focus_modes": {
            "fraud": {"boost_categories": ["Risk Indicator", "Financial Activity"], "boost_entities": ["Amount", "Company"]},
            "compliance": {"boost_categories": ["Legal Action"], "boost_entities": ["Company"]}
        },
        "scoring": {"entity_weight": 3, "category_weight": 2, "authority_weight": 4, "focus_multiplier": 1.5},
        "ui": {"primary_color": "#2c3e50", "graph_bg": "#1a1a2e", "title": "Corporate Intelligence"}
    }
    zf.writestr("examples/sample_corporate.json", json.dumps(sample, indent=2))

size_kb = zip_path.stat().st_size / 1024
print(f"Pack Forge ZIP: {zip_path}")
print(f"Size: {size_kb:.1f} KB")
print("DONE")
