# LEXICON — Michigan Legal Authority Database
"""Comprehensive Michigan legal knowledge base: MCR, MCL, MRE, Canons, FOC, SCAO."""

try:
    from .lexicon_engine import LexiconEngine
except ImportError as e:
    LexiconEngine = None
    _import_error = str(e)

try:
    from .lexicon_db import LexiconDB
except ImportError as e:
    LexiconDB = None

__all__ = ["LexiconEngine", "LexiconDB"]
