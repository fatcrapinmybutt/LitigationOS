"""
AuthorityAgent: MI-only authority node generation helpers.

This pack does not ship a full authority corpus; it ships:
- schema + Neo4j fulltext indexes
- an importer pattern for your authority shards (Benchbooks/MCR/MCL/MRE/SCAO forms)

You can ingest authority text shards as AuthorityTriple JSONL and load into Neo4j.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import datetime
import logging
import uuid

from agents.agent_base import uuid_str

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthorityTriple:
    authority_id: str
    source: str
    citation: str
    jurisdiction: str
    effective_date: str
    version: int
    text: str
    pinpoints: Optional[List[str]] = None

def make_authority(source: str, citation: str, text: str, effective_date: str, version: int = 0, pinpoints: Optional[List[str]] = None) -> AuthorityTriple:
    try:
        return AuthorityTriple(
            authority_id=uuid_str(),
            source=source,
            citation=citation,
            jurisdiction="MI",
            effective_date=effective_date,
            version=version,
            text=text,
            pinpoints=pinpoints,
        )
    except Exception as e:
        logger.error("AuthorityTriple creation failed for '%s': %s", citation, e)
        raise
