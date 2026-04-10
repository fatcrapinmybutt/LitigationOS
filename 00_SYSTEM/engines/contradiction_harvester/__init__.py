"""Contradiction Harvester — Autonomous contradiction detection engine.

Two-stage pipeline: fast keyword-opposition scan followed by precision
scoring. Discovers inconsistencies in adversary statements across the
evidence corpus and persists high-confidence contradictions for
impeachment use.

Usage:
    from engines.contradiction_harvester import ContradictionHarvester

    harvester = ContradictionHarvester()
    results = harvester.harvest(target="Emily Watson")
    harvester.persist_contradictions(results)
"""

__version__ = "1.0.0"

from .harvester import ContradictionHarvester

__all__ = ["ContradictionHarvester"]
