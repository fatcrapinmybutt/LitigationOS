"""
CHIMERA — Cross-referencing Hostile Inconsistencies via
Multi-source Evidence Reconciliation and Analysis.

Detects contradictions in witness/party statements across police reports,
PPO petitions, court testimony, affidavits, and other litigation documents.
Builds impeachment matrices for trial preparation.
"""
from .chimera_engine import ChimeraEngine

__all__ = ["ChimeraEngine"]
