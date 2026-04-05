"""
CHRONOS — Chronological History Reconstruction and Ordered Narrative Operating System
=====================================================================================
Unified timeline engine for LitigationOS. Ingests date-tagged events from documents,
tags them to case lanes A–F, builds master + per-lane chronologies, detects evidence
gaps, and overlays accusation/withholding/retaliation/judicial patterns.

All data stored in litigation_context.db (chronos_events, chronos_links,
chronos_gaps, chronos_patterns tables).
"""
from .chronos_engine import ChronosEngine

__all__ = ["ChronosEngine"]
__version__ = "1.0.0"
