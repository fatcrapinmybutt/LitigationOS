#!/usr/bin/env python3
"""Evidence Chain Engine v1.0 - Chain of custody tracking and gap analysis."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
LITOS_ROOT = r"C:\Users\andre\LitigationOS"

class EvidenceChainEngine:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.evidence_items = []
        self.claims = []
        self.gaps = []
        self.chain_records = []
    
    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row
        return conn
    
    def load_evidence(self):
        """Load evidence items from master DB."""
        conn = self.connect()
        try:
            # Find evidence tables
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%evidence%'").fetchall()]
            
            for table in tables:
                try:
                    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 1000").fetchall()
                    for row in rows:
                        item = dict(zip(cols, row))
                        item['_source_table'] = table
                        self.evidence_items.append(item)
                except Exception as e:
                    continue
            
            # Find claim tables
            claim_tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%claim%'").fetchall()]
            for table in claim_tables:
                try:
                    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 500").fetchall()
                    for row in rows:
                        item = dict(zip(cols, row))
                        item['_source_table'] = table
                        self.claims.append(item)
                except:
                    continue
        finally:
            conn.close()
        
        return len(self.evidence_items), len(self.claims)
    
    def analyze_gaps(self):
        """Find claims lacking supporting evidence."""
        evidence_by_claim = defaultdict(list)
        
        for ev in self.evidence_items:
            # Try to link evidence to claims via common fields
            claim_id = ev.get('claim_id') or ev.get('claim') or ev.get('related_claim')
            if claim_id:
                evidence_by_claim[str(claim_id)].append(ev)
        
        for claim in self.claims:
            claim_id = str(claim.get('id') or claim.get('claim_id') or '')
            claim_name = claim.get('name') or claim.get('title') or claim.get('description') or claim_id
            evidence_count = len(evidence_by_claim.get(claim_id, []))
            
            if evidence_count == 0:
                self.gaps.append({
                    "claim_id": claim_id,
                    "claim_name": str(claim_name)[:100],
                    "evidence_count": 0,
                    "severity": "HIGH",
                    "recommendation": "Find or create supporting evidence for this claim",
                })
            elif evidence_count < 3:
                self.gaps.append({
                    "claim_id": claim_id,
                    "claim_name": str(claim_name)[:100],
                    "evidence_count": evidence_count,
                    "severity": "MEDIUM",
                    "recommendation": "Consider additional corroborating evidence",
                })
        
        return self.gaps
    
    def scan_evidence_files(self):
        """Scan physical evidence files on disk."""
        evidence_dirs = ["05_EVIDENCE"]
        file_inventory = []
        
        for edir in evidence_dirs:
            full_path = Path(LITOS_ROOT) / edir
            if full_path.exists():
                for f in full_path.rglob("*"):
                    if f.is_file():
                        file_inventory.append({
                            "path": str(f.relative_to(LITOS_ROOT)),
                            "name": f.name,
                            "size_kb": f.stat().st_size / 1024,
                            "extension": f.suffix,
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        })
        
        return file_inventory
    
    def generate_report(self):
        """Generate evidence chain report."""
        file_inventory = self.scan_evidence_files()
        
        lines = []
        lines.append("=" * 70)
        lines.append("  EVIDENCE CHAIN REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"  Evidence Items (DB): {len(self.evidence_items):,}")
        lines.append(f"  Claims (DB): {len(self.claims):,}")
        lines.append(f"  Evidence Files (Disk): {len(file_inventory):,}")
        lines.append(f"  Evidence Gaps: {len(self.gaps)}")
        lines.append("")
        
        if self.gaps:
            high = [g for g in self.gaps if g['severity'] == 'HIGH']
            med = [g for g in self.gaps if g['severity'] == 'MEDIUM']
            
            lines.append(f"  GAPS: {len(high)} HIGH | {len(med)} MEDIUM")
            lines.append("")
            
            if high:
                lines.append("  HIGH PRIORITY GAPS (no evidence):")
                for g in high[:20]:
                    lines.append(f"    ! {g['claim_name']}")
                lines.append("")
            
            if med:
                lines.append("  MEDIUM GAPS (weak evidence):")
                for g in med[:20]:
                    lines.append(f"    ~ {g['claim_name']} ({g['evidence_count']} items)")
                lines.append("")
        
        # File type breakdown
        ext_counts = defaultdict(int)
        for f in file_inventory:
            ext_counts[f['extension']] += 1
        
        lines.append("  EVIDENCE FILE TYPES:")
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"    {ext or '(none)'}: {count}")
        
        lines.append("")
        lines.append("=" * 70)
        
        report = "\n".join(lines)
        
        # Save
        output_dir = Path(LITOS_ROOT) / "00_SYSTEM"
        with open(output_dir / "EVIDENCE_CHAIN_REPORT.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        with open(output_dir / "evidence_chain_data.json", 'w', encoding='utf-8') as f:
            json.dump({
                "evidence_count": len(self.evidence_items),
                "claims_count": len(self.claims),
                "file_count": len(file_inventory),
                "gaps": self.gaps[:50],
                "file_types": dict(ext_counts),
            }, f, indent=2, default=str)
        
        return report
    
    def run(self):
        ev_count, claim_count = self.load_evidence()
        print(f"Loaded {ev_count} evidence items, {claim_count} claims")
        
        gaps = self.analyze_gaps()
        print(f"Found {len(gaps)} evidence gaps")
        
        report = self.generate_report()
        print(report)
        
        return report


if __name__ == "__main__":
    engine = EvidenceChainEngine()
    engine.run()
