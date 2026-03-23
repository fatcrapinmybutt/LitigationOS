"""Multi-jurisdiction plugin architecture for LitigationOS.

Provides an abstract base for jurisdiction-specific plugins that supply
court rules, filing requirements, and validation logic.  Michigan is the
default (and currently only) implementation.
"""

from litigationos.jurisdiction.base import (
    JurisdictionInfo,
    JurisdictionPlugin,
    JurisdictionRegistry,
)
from litigationos.jurisdiction.michigan import MichiganJurisdiction

__all__ = [
    "JurisdictionInfo",
    "JurisdictionPlugin",
    "JurisdictionRegistry",
    "MichiganJurisdiction",
]
