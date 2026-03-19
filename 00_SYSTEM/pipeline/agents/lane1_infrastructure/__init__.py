"""
DELTA9 Lane 1 — Infrastructure Agents (I/O bound)
Tier 2: Dedup cluster (A05–A08)
"""
from .a05_legal_dedup import LegalDedup
from .a06_data_dedup import DataDedup
from .a07_code_dedup import CodeDedup
from .a08_archive_cracker import ArchiveCracker

__all__ = ['LegalDedup', 'DataDedup', 'CodeDedup', 'ArchiveCracker']
