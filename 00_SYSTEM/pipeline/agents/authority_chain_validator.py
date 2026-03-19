"""
AUTHORITY CHAIN VALIDATOR — Agent A13
Validates legal citations: checks chain completeness, identifies fabricated cases,
cross-references authorities against filings, scores citation strength.

Part of the Delta9 fleet — inherits Agent9999 base class.
"""
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agent_models import (
    AgentResult, AgentStats, FatalAgentError, SkipItemError,
    RetryableError, QualityScore, MASTER_INDEX_DB
)
from .agent_base import Agent9999


class AuthorityChainValidator(Agent9999):
    """Validates legal citation chains and scores authority strength.
    
    Pipeline role: Tier L (Convergence) — runs after evidence extraction
    to verify all cited authorities are real, correctly cited, and properly chained.
    
    Work items: rows from authority_chains table in litigation_context.db
    Processing: For each citation, verify format, check chain completeness,
    cross-reference against known fabricated cases, score strength.
    """
    
    AGENT_ID = "A13"
    AGENT_NAME = "AuthorityChainValidator"
    AGENT_TIER = "L"
    BATCH_SIZE = 50
    
    # Known hallucinated cases — NEVER cite these
    KNOWN_FABRICATIONS = {
        "McCraney v Ford Motor Co",
        "Jane Berry",
        "Patricia Berry",
    }
    
    # Citation format patterns
    PATTERNS = {
        "us_supreme": re.compile(r'\d+\s+U\.?S\.?\s+\d+'),
        "fed_reporter": re.compile(r'\d+\s+F\.\d[dth]+\s+\d+'),
        "mich_supreme": re.compile(r'\d+\s+Mich\.?\s+\d+'),
        "mich_app": re.compile(r'\d+\s+Mich\.?\s*App\.?\s+\d+'),
        "mcr": re.compile(r'MCR\s+\d+\.\d+'),
        "mcl": re.compile(r'MCL\s+\d+\.\d+[a-z]?'),
        "usc": re.compile(r'\d+\s+U\.?S\.?C\.?\s+§?\s*\d+'),
    }
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config=config or {})
        self.db_path = db_path or str(
            Path(__file__).resolve().parent.parent.parent.parent / "litigation_context.db"
        )
        self.validated_count = 0
        self.fabricated_count = 0
        self.weak_chains = []
        self.strong_chains = []
    
    def _validate_preconditions(self) -> bool:
        """Check that litigation_context.db exists and has authority tables."""
        if not os.path.exists(self.db_path):
            self.logger.error(f"DB not found: {self.db_path}")
            return False
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            # Check for authority-related tables
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%authority%'"
            ).fetchall()]
            conn.close()
            if not tables:
                self.logger.warning("No authority tables found — will scan filings directly")
            return True
        except Exception as e:
            self.logger.error(f"DB connection failed: {e}")
            return False
    
    def _get_work_items(self) -> List[Any]:
        """Get citations to validate from DB or by scanning filing markdown files."""
        items = []
        
        # Strategy 1: Pull from authority_chains table if it exists
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -32000")
            
            # Check table existence and columns
            cursor = conn.execute("PRAGMA table_info(authority_chains)")
            cols = [row[1] for row in cursor.fetchall()]
            
            if cols:
                # Build query based on available columns
                query = "SELECT * FROM authority_chains"
                if "chain_complete" in cols:
                    query += " WHERE chain_complete = 0 OR chain_complete IS NULL"
                query += " LIMIT 500"
                
                rows = conn.execute(query).fetchall()
                col_names = [desc[0] for desc in conn.execute(query.replace(" LIMIT 500", " LIMIT 1")).description] if rows else cols
                for row in rows:
                    items.append(dict(zip(col_names, row)))
            conn.close()
        except Exception as e:
            self.logger.warning(f"authority_chains query failed: {e}")
        
        # Strategy 2: Scan filing markdown files for citations
        if not items:
            filing_dir = Path(os.path.expanduser("~")) / "Desktop" / "LITIGATION_FILING_PACKAGE"
            if filing_dir.exists():
                for md_file in filing_dir.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="replace")
                        citations = self._extract_citations(content)
                        for cite in citations:
                            items.append({
                                "citation": cite["text"],
                                "pattern_type": cite["type"],
                                "source_file": str(md_file),
                                "context": cite.get("context", ""),
                            })
                    except Exception as e:
                        self.logger.warning(f"Failed to scan {md_file}: {e}")
        
        self.logger.info(f"Found {len(items)} citations to validate")
        return items
    
    def _extract_citations(self, text: str) -> List[Dict]:
        """Extract legal citations from text using regex patterns."""
        citations = []
        seen = set()
        
        for pattern_type, pattern in self.PATTERNS.items():
            for match in pattern.finditer(text):
                cite_text = match.group()
                if cite_text not in seen:
                    seen.add(cite_text)
                    # Get surrounding context (100 chars each side)
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    citations.append({
                        "text": cite_text,
                        "type": pattern_type,
                        "context": text[start:end].replace("\n", " ").strip(),
                    })
        
        return citations
    
    def _process_item(self, item: Any) -> Dict[str, Any]:
        """Validate a single citation."""
        citation = item.get("citation", str(item))
        result = {
            "citation": citation,
            "status": "UNKNOWN",
            "issues": [],
            "strength_score": 0.0,
            "chain_complete": False,
        }
        
        # Check 1: Known fabrication?
        for fab in self.KNOWN_FABRICATIONS:
            if fab.lower() in citation.lower():
                result["status"] = "FABRICATED"
                result["issues"].append(f"Known hallucination: {fab}")
                self.fabricated_count += 1
                # Broadcast finding to fleet
                self.broadcast_finding(
                    finding_type="FABRICATED_CITATION",
                    content=f"HALLUCINATED: {citation}",
                    severity="CRITICAL",
                    metadata={"source": item.get("source_file", "unknown")}
                )
                return result
        
        # Check 2: Valid format?
        format_valid = False
        for ptype, pattern in self.PATTERNS.items():
            if pattern.search(citation):
                format_valid = True
                result["pattern_type"] = ptype
                break
        
        if not format_valid:
            result["status"] = "INVALID_FORMAT"
            result["issues"].append("Citation does not match any known format")
            result["strength_score"] = 0.1
            return result
        
        # Check 3: Score strength based on court level
        strength_map = {
            "us_supreme": 1.0,
            "fed_reporter": 0.85,
            "mich_supreme": 0.9,
            "mich_app": 0.75,
            "mcr": 0.8,
            "mcl": 0.85,
            "usc": 0.9,
        }
        result["strength_score"] = strength_map.get(
            result.get("pattern_type", ""), 0.5
        )
        
        # Check 4: Cross-reference against DB known_citations if available
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout = 60000")
            
            # Check if known_citations or similar table exists
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            
            if "known_citations" in tables:
                row = conn.execute(
                    "SELECT status FROM known_citations WHERE citation LIKE ?",
                    (f"%{citation}%",)
                ).fetchone()
                if row:
                    if row[0] == "verified":
                        result["status"] = "VERIFIED"
                        result["chain_complete"] = True
                    elif row[0] == "hallucinated":
                        result["status"] = "FABRICATED"
                        result["issues"].append("Flagged as hallucination in known_citations DB")
                        self.fabricated_count += 1
            
            conn.close()
        except Exception:
            pass  # Non-fatal — DB check is supplementary
        
        # Default: mark as UNVERIFIED if no definitive status
        if result["status"] == "UNKNOWN":
            result["status"] = "UNVERIFIED"
            result["chain_complete"] = False
        
        self.validated_count += 1
        return result
    
    def _finalize(self, stats: AgentStats, results: List) -> None:
        """Write validation report to master_index.db."""
        try:
            conn = sqlite3.connect(str(MASTER_INDEX_DB))
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS authority_validation (
                    citation TEXT PRIMARY KEY,
                    status TEXT,
                    strength_score REAL,
                    chain_complete INTEGER,
                    issues TEXT,
                    pattern_type TEXT,
                    source_file TEXT,
                    validated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            rows = []
            for r in results:
                if isinstance(r, dict) and "citation" in r:
                    rows.append((
                        r["citation"],
                        r.get("status", "UNKNOWN"),
                        r.get("strength_score", 0.0),
                        1 if r.get("chain_complete") else 0,
                        json.dumps(r.get("issues", [])),
                        r.get("pattern_type", ""),
                        r.get("source_file", ""),
                    ))
            
            if rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO authority_validation VALUES (?,?,?,?,?,?,?,datetime('now'))",
                    rows
                )
                conn.commit()
            
            conn.close()
            self.logger.info(
                f"Authority validation complete: {self.validated_count} validated, "
                f"{self.fabricated_count} fabricated"
            )
        except Exception as e:
            self.logger.error(f"Finalize failed: {e}")


# CLI entry point
if __name__ == "__main__":
    agent = AuthorityChainValidator()
    result = agent.run()
    print(f"Authority Chain Validator: {result.status} — "
          f"{result.stats.processed}/{result.stats.total} citations checked")
