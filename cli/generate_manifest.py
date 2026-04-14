#!/usr/bin/env python
"""CLI entrypoint for generating a manifest."""
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import and run the main function from scripts.generate_manifest
from scripts.generate_manifest import main


if __name__ == "__main__":
    main()
