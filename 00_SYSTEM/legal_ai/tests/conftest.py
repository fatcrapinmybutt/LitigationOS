"""
conftest.py — Protect test collection from heavy imports.

Mocks brains and sentence_transformers BEFORE any test module imports them,
preventing multi-minute hangs from model downloads / GPU detection.
"""

import os
import sys
from unittest.mock import MagicMock

# Prevent Hugging Face / transformers from downloading models during tests
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Mock heavy optional dependencies that are never exercised in unit tests
for mod_name in (
    "brains",
    "brains.brain_manager",
    "sentence_transformers",
    "torch",
):
    sys.modules.setdefault(mod_name, MagicMock())
