"""
Judicial Rebuttal Engine — LitigationOS
Combats every false/biased judicial finding with truth + evidence + authority.
"""
from .models import JudicialRebuttal, RebuttalSeverity, StatementCategory
from .engine import RebuttalEngine
from .formatter import RebuttalFormatter

__all__ = [
    "JudicialRebuttal",
    "RebuttalSeverity",
    "StatementCategory",
    "RebuttalEngine",
    "RebuttalFormatter",
]
__version__ = "1.0.0"
