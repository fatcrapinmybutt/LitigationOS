#!/usr/bin/env python3
"""Placeholder Resolver v2.0 - Auto-fill from master DB with smart inference."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

# Known values that can be auto-filled
KNOWN_VALUES = {
    # Case information
    "case_number": "2024-001507-DC",
    "case_no": "2024-001507-DC",
    "coa_case": "366810",
    "coa_case_number": "366810",
    "court_name": "14th Circuit Court",
    "court": "14th Circuit Court, Muskegon County, Michigan",
    "county": "Muskegon County",
    "state": "Michigan",
    "judge": "Hon. Jenny L. McNeill",
    "judge_name": "Hon. Jenny L. McNeill",
    
    # Parties
    "petitioner": "Andrew Pigors",
    "petitioner_name": "Andrew Pigors",
    "plaintiff": "Andrew Pigors",
    "appellant": "Andrew Pigors",
    "respondent": "Emily Watson",
    "respondent_name": "Emily Watson",
    "defendant": "Emily Watson",
    "appellee": "Emily Watson",
    "child": "L.D.W.",
    "child_name": "L.D.W.",
    "child_initials": "L.D.W.",
    "child_dob": "November 9, 2022",
    "child_dob_year": "2022",
    
    # Addresses
    "petitioner_address": "1977 Whitehall Rd, Lot 17, Laketon Twp, MI 49445",
    "address": "1977 Whitehall Rd, Lot 17, Laketon Twp, MI 49445",
    
    # Attorneys
    "opposing_counsel": "Jennifer L. Barnes (P55406)",
    "opposing_attorney": "Jennifer L. Barnes",
    "attorney_bar": "P55406",
    "barnes": "Jennifer L. Barnes (P55406)",
    "foc": "Pamela Rusco",
    "foc_name": "Pamela Rusco",
    
    # Court addresses
    "court_address": "990 Terrace Street, Muskegon, MI 49442",
    "coa_address": "Cadillac Place, 3020 W. Grand Blvd, Suite 14-300, Detroit, MI 48202",
    "msc_address": "P.O. Box 30052, Lansing, MI 48909",
    
    # Shady Oaks defendants
    "shady_oaks_1": "Shady Oaks Park MHP LLC",
    "shady_oaks_2": "Shady Oaks MHP LLC (dissolved)",
    "homes_of_america": "Homes of America LLC",
    "alden_global": "Alden Global Capital LLC",
    "partridge_equity": "Partridge Equity Group",
    "jeremy_brown": "Jeremy Brown",
    "aaron_cox": "Aaron D. Cox (P69346)",
    "henry_brandel": "Henry Brandel",
    
    # Filing info
    "pro_se": "Pro Se",
    "pro_se_status": "Appearing Pro Se",
    "year": "2026",
}

# Patterns that CANNOT be auto-filled (need Andrew's input)
ANDREW_REQUIRED = [
    "email", "phone", "signature", "notari",
    "bar_number", "hearing_date", "transcript_page",
    "financial", "income", "bank", "account",
    "barnes_address", "watson_address",
    "docket_count", "motion_count",
]


class PlaceholderResolverV2:
    def __init__(self, db_path=DB_PATH):
        """Initialize placeholder resolver with known values.
        
        Args:
            db_path: Path to the litigation context database.
        """
        if db_path and not isinstance(db_path, str):
            raise TypeError("db_path must be a string path")
        self.db_path = db_path or DB_PATH
        self.known = dict(KNOWN_VALUES)
        self.resolved = 0
        self.unresolved = 0
        self.andrew_needed = []
        self.changes = []
    
    def load_db_values(self):
        """Load additional known values from master DB.
        
        Gracefully degrades if DB is unavailable.
        """
        if not os.path.exists(self.db_path):
            logger.warning("Database not found: %s -- using hardcoded values only", self.db_path)
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=120)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            
            # Try to find party info, dates, etc.
            for table in ['parties', 'case_info', 'case_metadata', 'contacts']:
                try:
                    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 50").fetchall()
                    for row in rows:
                        for i, col in enumerate(cols):
                            if row[i] and str(row[i]).strip():
                                key = col.lower().replace(' ', '_')
                                if key not in self.known:
                                    self.known[key] = str(row[i]).strip()
                except Exception as e:
                    logger.debug("Error loading values from table %s: %s", table, e)
                    continue
            
            conn.close()
        except Exception as e:
            logger.warning("DB value load failed: %s", e)
    
    def _match_placeholder(self, placeholder_text):
        """Try to match a placeholder to a known value.
        
        Args:
            placeholder_text: The text inside the placeholder brackets.
            
        Returns:
            tuple: (resolved_value_or_None, andrew_input_needed_bool).
        """
        # Clean the placeholder text
        clean = placeholder_text.lower().strip('[]').strip()
        clean = re.sub(r'^(placeholder|insert|fill|add|enter|provide)[\s:_-]*', '', clean)
        clean = clean.strip()
        
        # Check if this needs Andrew's input
        for pattern in ANDREW_REQUIRED:
            if pattern in clean:
                return None, True  # None = can't resolve, True = Andrew needed
        
        # Direct match
        if clean in self.known:
            return self.known[clean], False
        
        # Fuzzy match: check if any known key is contained in the placeholder
        for key, value in self.known.items():
            if key in clean or clean in key:
                return value, False
        
        # Partial word match
        words = clean.split()
        for word in words:
            if len(word) >= 4:  # Skip short words
                for key, value in self.known.items():
                    if word in key:
                        return value, False
        
        return None, False  # Can't resolve, but not Andrew-specific
    
    def process_file(self, filepath):
        """Process a single file, resolving placeholders where possible.
        
        Args:
            filepath: Path to the file to process.
            
        Returns:
            tuple: (resolved_count, unresolved_count).
        """
        if not filepath or not os.path.isfile(filepath):
            logger.debug("Skipping invalid file path: %s", filepath)
            return 0, 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (IOError, OSError) as e:
            logger.error("Failed to read file %s: %s", filepath, e)
            return 0, 0
        
        original = content
        file_resolved = 0
        file_unresolved = 0
        
        # Find all placeholder patterns
        patterns = [
            (r'\[PLACEHOLDER[:\s]*([^\]]*)\]', 'PLACEHOLDER'),
            (r'\[INSERT[:\s]*([^\]]*)\]', 'INSERT'),
            (r'\[FILL[:\s]*([^\]]*)\]', 'FILL'),
            (r'\[TBD[:\s]*([^\]]*)\]', 'TBD'),
        ]
        
        for pattern, ptype in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                full_match = match.group(0)
                inner = match.group(1) if match.lastindex else ''
                
                value, andrew_needed = self._match_placeholder(inner)
                
                if andrew_needed:
                    self.andrew_needed.append({
                        "file": str(filepath),
                        "placeholder": full_match,
                        "context": inner,
                    })
                    file_unresolved += 1
                elif value:
                    content = content.replace(full_match, value, 1)
                    file_resolved += 1
                    self.changes.append({
                        "file": str(filepath),
                        "old": full_match,
                        "new": value,
                    })
                else:
                    file_unresolved += 1
        
        # Write back if changed
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.resolved += file_resolved
        self.unresolved += file_unresolved
        
        return file_resolved, file_unresolved
    
    def scan_and_resolve(self):
        """Scan all filing stacks and resolve placeholders.
        
        Iterates through all markdown files in filing stacks and attempts
        to auto-fill placeholders from known values.
        """
        stacks = [
            "01_COA_366810",
            "02_TRIAL_14TH",
            "03_FEDERAL_1983",
            "04_MSC_ORIGINAL_ACTION",
            "06_EMERGENCY",
        ]
        
        for stack in stacks:
            stack_path = LITOS_ROOT / stack
            if not stack_path.exists():
                continue
            
            for f in stack_path.rglob("*.md"):
                resolved, unresolved = self.process_file(f)
                if resolved > 0 or unresolved > 0:
                    print(f"  {f.name}: {resolved} resolved, {unresolved} remaining")
    
    def generate_report(self):
        """Generate resolution report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  PLACEHOLDER RESOLUTION REPORT v2")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"  Auto-Resolved: {self.resolved}")
        lines.append(f"  Unresolved: {self.unresolved}")
        lines.append(f"  Andrew Input Needed: {len(self.andrew_needed)}")
        lines.append("")
        
        if self.andrew_needed:
            lines.append("  ANDREW INPUT REQUIRED:")
            seen = set()
            for item in self.andrew_needed:
                key = item['placeholder']
                if key not in seen:
                    seen.add(key)
                    lines.append(f"    --> {item['placeholder']}")
                    lines.append(f"        File: {Path(item['file']).name}")
            lines.append("")
        
        if self.changes:
            lines.append(f"  AUTO-FILLED ({len(self.changes)} replacements):")
            for c in self.changes[:20]:
                lines.append(f"    {Path(c['file']).name}: {c['old']} --> {c['new']}")
        
        lines.append("")
        lines.append("=" * 60)
        
        report = "\n".join(lines)
        
        # Save
        output = LITOS_ROOT / "00_SYSTEM" / "PLACEHOLDER_RESOLUTION_V2.txt"
        with open(output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save JSON
        with open(LITOS_ROOT / "00_SYSTEM" / "placeholder_resolution_v2.json", 'w', encoding='utf-8') as f:
            json.dump({
                "resolved": self.resolved,
                "unresolved": self.unresolved,
                "andrew_needed": self.andrew_needed[:50],
                "changes": self.changes[:100],
            }, f, indent=2, default=str)
        
        return report
    
    def run(self):
        """Execute full placeholder resolution cycle.
        
        Returns:
            str: Resolution report text, or error message on failure.
        """
        try:
            print("Loading known values from DB...")
            self.load_db_values()
            print(f"Known values: {len(self.known)}")
            
            print("Scanning and resolving placeholders...")
            self.scan_and_resolve()
            
            report = self.generate_report()
            print(report)
            
            return report
        except Exception as e:
            logger.error("Placeholder resolver failed: %s", e)
            return f"[ERROR] Placeholder resolver failed: {e}"


if __name__ == "__main__":
    try:
        engine = PlaceholderResolverV2()
        engine.run()
    except Exception as e:
        logger.error("Placeholder resolver crashed: %s", e)
        print(f"[ERROR] Placeholder resolver crashed: {e}")
