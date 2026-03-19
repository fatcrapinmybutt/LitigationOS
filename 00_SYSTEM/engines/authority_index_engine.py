#!/usr/bin/env python3
"""Authority Index Engine v1.0 - Searchable case law, statute, and rule database."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
INDEX_DIR = LITOS_ROOT / "00_SYSTEM" / "authority_index"

class AuthorityIndexEngine:
    def __init__(self, db_path=DB_PATH):
        """Initialize authority index engine.
        
        Args:
            db_path: Path to the litigation context database.
        """
        if db_path and not isinstance(db_path, str):
            raise TypeError("db_path must be a string path")
        self.db_path = db_path or DB_PATH
        self.authorities = []
        self.citation_graph = defaultdict(list)  # authority --> [cited_by]
        try:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create index directory: %s", e)
    
    def connect(self):
        """Create a database connection with WAL mode and busy timeout.
        
        Returns:
            sqlite3.Connection or None: Database connection, or None if unavailable.
        """
        if not os.path.exists(self.db_path):
            logger.warning("Database not found: %s", self.db_path)
            return None
        try:
            conn = sqlite3.connect(self.db_path, timeout=120)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            return conn
        except sqlite3.Error as e:
            logger.error("Failed to connect to database: %s", e)
            return None
    
    def extract_authorities(self):
        """Extract all authorities from master DB tables.
        
        Returns:
            int: Number of authority records found, or 0 if DB unavailable.
        """
        conn = self.connect()
        if conn is None:
            logger.warning("DB unavailable -- skipping authority extraction")
            return 0
        
        # Find authority-related tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        authority_tables = [t[0] for t in tables if any(kw in t[0].lower() for kw in ['authority', 'case_law', 'citation', 'statute', 'rule', 'mcr', 'mcl', 'precedent', 'legal_auth'])]
        
        print(f"Found {len(authority_tables)} authority tables")
        
        for table in authority_tables:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                
                # Sample data
                rows = conn.execute(f"SELECT * FROM {table} LIMIT 500").fetchall()
                for row in rows:
                    auth = {"_table": table}
                    for i, col in enumerate(cols):
                        if row[i] is not None:
                            auth[col] = str(row[i])[:500]
                    self.authorities.append(auth)
                
                print(f"  {table}: {count} rows, {len(cols)} columns")
            except Exception as e:
                logger.error("Error extracting from %s: %s", table, e)
        
        conn.close()
        return len(self.authorities)
    
    def scan_filing_citations(self):
        """Scan filing documents for citation patterns.
        
        Returns:
            dict: Citation text --> {count, files} mapping.
        """
        citation_patterns = {
            "michigan_case": r'([A-Z][a-zA-Z]+\s+v\s+[A-Z][a-zA-Z]+),?\s+(\d+)\s+Mich(?:\s+App)?\s+(\d+)',
            "mcl": r'MCL\s+([\d.]+(?:\([a-z0-9]+\))?)',
            "mcr": r'MCR\s+([\d.]+(?:\([A-Z]\))?(?:\(\d+\))?)',
            "usc": r'(\d+)\s+USC\s+[Ss]?([\d]+)',
            "federal_case": r'([A-Z][a-zA-Z]+\s+v\s+[A-Z][a-zA-Z]+),?\s+(\d+)\s+F\.?\s*(?:2d|3d|4th)\s+(\d+)',
            "us_const": r'US\s+Const(?:itution)?,?\s+(Art|Amend)\.?\s+([IVXLCDM\d]+)',
            "mi_const": r'(?:Mich|MI)\s+Const(?:itution)?,?\s+(?:19\d{2},?\s+)?(?:Art|art)\.?\s+([IVXLCDM\d]+)',
        }
        
        all_citations = defaultdict(lambda: {"count": 0, "files": []})
        
        filing_dirs = ["01_COA_366810", "02_TRIAL_14TH", "03_FEDERAL_1983", "04_MSC_ORIGINAL_ACTION", "06_EMERGENCY"]
        
        for fdir in filing_dirs:
            fpath = LITOS_ROOT / fdir
            if not fpath.exists():
                continue
            
            for f in fpath.rglob("*.md"):
                try:
                    content = f.read_text(encoding='utf-8', errors='replace')
                    for ctype, pattern in citation_patterns.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            cite_text = match.group(0).strip()
                            all_citations[cite_text]["count"] += 1
                            if str(f.name) not in all_citations[cite_text]["files"]:
                                all_citations[cite_text]["files"].append(str(f.name))
                except Exception as e:
                    logger.debug("Error scanning file for citations: %s", e)
                    continue
        
        return dict(all_citations)
    
    def build_citation_graph(self, citations):
        """Build a citation relationship graph.
        
        Args:
            citations: Dict mapping citation text to usage info.
        """
        if not citations:
            logger.info("No citations to build graph from")
            return
        for cite, info in citations.items():
            for other_cite, other_info in citations.items():
                if cite != other_cite:
                    # If they appear in the same file, they're related
                    common_files = set(info["files"]) & set(other_info["files"])
                    if common_files:
                        self.citation_graph[cite].append({
                            "related_to": other_cite,
                            "shared_files": list(common_files),
                        })
    
    def generate_index(self, citations):
        """Generate the authority index report.
        
        Args:
            citations: Dict mapping citation text to usage info.
            
        Returns:
            str: Formatted authority index text.
        """
        # Sort by frequency
        sorted_cites = sorted(citations.items(), key=lambda x: -x[1]["count"])
        
        lines = []
        lines.append("=" * 70)
        lines.append("  AUTHORITY INDEX")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"  Total Authorities (DB): {len(self.authorities):,}")
        lines.append(f"  Total Citations (Filings): {len(citations):,}")
        lines.append("=" * 70)
        lines.append("")
        
        # Top cited
        lines.append("  MOST CITED AUTHORITIES:")
        for cite, info in sorted_cites[:30]:
            lines.append(f"    [{info['count']}x] {cite}")
            lines.append(f"         Files: {', '.join(info['files'][:3])}")
        
        # By type
        mcl_cites = {k: v for k, v in citations.items() if 'MCL' in k}
        mcr_cites = {k: v for k, v in citations.items() if 'MCR' in k}
        case_cites = {k: v for k, v in citations.items() if ' v ' in k}
        
        lines.append("")
        lines.append(f"  BY TYPE:")
        lines.append(f"    Case Law: {len(case_cites)}")
        lines.append(f"    MCL Statutes: {len(mcl_cites)}")
        lines.append(f"    MCR Rules: {len(mcr_cites)}")
        lines.append(f"    Other: {len(citations) - len(case_cites) - len(mcl_cites) - len(mcr_cites)}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def run(self):
        """Execute full authority index generation.
        
        Returns:
            dict: Summary with counts, or error dict on failure.
        """
        try:
            print("Extracting authorities from master DB...")
            auth_count = self.extract_authorities()
            print(f"Found {auth_count} authority records")
            
            print("Scanning filing citations...")
            citations = self.scan_filing_citations()
            print(f"Found {len(citations)} unique citations")
            
            print("Building citation graph...")
            self.build_citation_graph(citations)
            
            index = self.generate_index(citations)
            print(index)
            
            # Save everything
            for filename, data in [
                ("AUTHORITY_INDEX.txt", index),
                ("citations.json", json.dumps(citations, indent=2, default=str)),
                ("citation_graph.json", json.dumps(dict(self.citation_graph), indent=2, default=str)),
                ("authorities_db.json", json.dumps(self.authorities[:1000], indent=2, default=str)),
            ]:
                try:
                    with open(INDEX_DIR / filename, 'w', encoding='utf-8') as f:
                        f.write(data)
                except (IOError, OSError) as e:
                    logger.error("Failed to write %s: %s", filename, e)
            
            print(f"\nIndex saved to {INDEX_DIR}")
            return {
                "authorities_db": auth_count,
                "citations_filed": len(citations),
                "graph_edges": sum(len(v) for v in self.citation_graph.values()),
            }
        except Exception as e:
            logger.error("Authority index engine failed: %s", e)
            return {"error": str(e), "authorities_db": 0, "citations_filed": 0, "graph_edges": 0}


if __name__ == "__main__":
    try:
        engine = AuthorityIndexEngine()
        engine.run()
    except Exception as e:
        logger.error("Authority index engine crashed: %s", e)
        print(f"[ERROR] Authority index engine crashed: {e}")
