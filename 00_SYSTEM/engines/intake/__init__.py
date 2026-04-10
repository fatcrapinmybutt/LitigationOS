"""
Intake Engine — The Central Nervous System of LitigationOS
==========================================================

Unified pipeline: Intake → Extract → Classify → Analyze → Route → Store

This engine connects ALL other engines into one cohesive flow:

    ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐    ┌───────┐
    │  WATCH  │───▶│ EXTRACT  │───▶│ CLASSIFY │───▶│ ANALYZE │───▶│ STORE │
    │(folder) │    │(OCR/text)│    │(type/lane)│   │(deep NLP)│   │  (DB) │
    └─────────┘    └──────────┘    └──────────┘    └─────────┘    └───────┘
         │                                               │              │
         │              ┌─────────────────┐              │              │
         └─────────────▶│ READINESS CHECK │◀─────────────┘              │
                        │ (EGCP scoring)  │                             │
                        └────────┬────────┘                             │
                                 │ score >= threshold                   │
                                 ▼                                      │
                        ┌─────────────────┐                             │
                        │  FILING ENGINE  │◀────────────────────────────┘
                        │ (auto-trigger)  │
                        └─────────────────┘

100% case-agnostic. Case specificity comes from:
  1. The intake folder path
  2. A case_config.yaml in the intake folder OR in the case DB
  3. The evidence content itself (analyzed, not hardcoded)
"""

import sys
from pathlib import Path

_ENGINE_DIR = Path(__file__).resolve().parent
_SYSTEM_DIR = _ENGINE_DIR.parent.parent
if str(_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(_SYSTEM_DIR))

from .extractor import TextExtractor
from .classifier import DocumentClassifier
from .analyzer import LitigationAnalyzer
from .router import DatabaseRouter
from .pipeline import IntakePipeline
from .case_config import CaseConfig

__all__ = [
    "TextExtractor",
    "DocumentClassifier",
    "LitigationAnalyzer",
    "DatabaseRouter",
    "IntakePipeline",
    "CaseConfig",
]

__version__ = "1.0.0"
