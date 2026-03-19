"""
DELTA9 Agent Fleet — 50 agents across dual-lane parallel architecture.
MAX LEVEL 9999++ — Michigan Judicial Domination System.

Lane 1 (Infrastructure): Index, Dedup, Flatten, Extract — I/O bound
Lane 2 (Intelligence): Judicial, Case Intel, Legal Warfare — CPU/AI bound
Convergence: Filing, Brains, Graph, MSC, Test, Certify
"""
from .agent_models import (
    AgentResult, AgentStats, SkipItemError, FatalAgentError,
    LaneCrossContaminationError, MASTER_INDEX_DB, CHECKPOINT_DIR,
    LANE_A_SIGNALS, LANE_B_SIGNALS, LANE_C_SIGNALS,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS, CODE_EXTENSIONS,
    ARCHIVE_EXTENSIONS, IMAGE_EXTENSIONS,
    SKIP_DIRS, SKIP_EXTENSIONS, CANONICAL_PRIORITY
)
from .agent_base import Agent9999

__all__ = [
    'Agent9999', 'AgentResult', 'AgentStats',
    'SkipItemError', 'FatalAgentError', 'LaneCrossContaminationError',
    'MASTER_INDEX_DB', 'CHECKPOINT_DIR',
    'LANE_A_SIGNALS', 'LANE_B_SIGNALS', 'LANE_C_SIGNALS',
    'LEGAL_EXTENSIONS', 'DATA_EXTENSIONS', 'CODE_EXTENSIONS',
    'ARCHIVE_EXTENSIONS', 'IMAGE_EXTENSIONS',
    'SKIP_DIRS', 'SKIP_EXTENSIONS', 'CANONICAL_PRIORITY'
]
