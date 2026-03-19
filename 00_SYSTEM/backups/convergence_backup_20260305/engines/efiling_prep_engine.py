#!/usr/bin/env python3
"""E-Filing Prep Engine v1.0 - TrueFiling/MiFILE packet preparation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

# E-filing systems
EFILING_SYSTEMS = {
    "truefiling": {
        "name": "TrueFiling",
        "url": "https://www.truefiling.com",
        "courts": ["Michigan Court of Appeals", "Michigan Supreme Court"],
        "max_file_size_mb": 25,
        "accepted_formats": [".pdf"],
        "notes": "Requires account registration. PDF/A recommended.",
    },
    "mifile": {
        "name": "MiFILE",
        "url": "https://mifile.courts.michigan.gov",
        "courts": ["14th Circuit Court", "Circuit Courts"],
        "max_file_size_mb": 35,
        "accepted_formats": [".pdf", ".docx"],
        "notes": "Michigan Integrated Filing and E-service system.",
    },
    "pacer": {
        "name": "PACER/CM/ECF",
        "url": "https://ecf.miwd.uscourts.gov",
        "courts": ["WDMI Federal Court"],
        "max_file_size_mb": 35,
        "accepted_formats": [".pdf"],
        "notes": "Federal court e-filing. Requires PACER account.",
    },
}

FILING_CONFIGS = {
    "COA Brief 366810": {
        "system": "truefiling",
        "stack_path": "01_COA_366810",
        "documents": [
            {"type": "brief", "name": "Appellant's Brief", "pattern": "*brief*"},
            {"type": "appendix", "name": "Appendix", "pattern": "*appendix*"},
            {"type": "service", "name": "Proof of Service", "pattern": "*service*"},
        ],
        "fee": 0,  # IFP
    },
    "McNeill Disqualification": {
        "system": "mifile",
        "stack_path": "02_TRIAL_14TH/FULL_14TH_STACK/DISQUALIFY_PACKAGE",
        "documents": [
            {"type": "motion", "name": "Motion to Disqualify", "pattern": "*motion*disqualif*"},
            {"type": "brief", "name": "Brief in Support", "pattern": "*brief*"},
            {"type": "exhibits", "name": "Exhibits", "pattern": "*exhibit*"},
            {"type": "order", "name": "Proposed Order", "pattern": "*order*"},
            {"type": "service", "name": "Certificate of Service", "pattern": "*service*"},
        ],
        "fee": 0,
    },
    "MSC Original Action": {
        "system": "truefiling",
        "stack_path": "04_MSC_ORIGINAL_ACTION",
        "documents": [
            {"type": "complaint", "name": "Complaint for Superintending Control", "pattern": "*complaint*"},
            {"type": "brief", "name": "Brief in Support", "pattern": "*brief*"},
            {"type": "appendix", "name": "Appendix", "pattern": "*appendix*"},
            {"type": "service", "name": "Proof of Service", "pattern": "*service*"},
            {"type": "verification", "name": "Verification", "pattern": "*verif*"},
            {"type": "fee_waiver", "name": "Fee Waiver", "pattern": "*fee*waiv*"},
        ],
        "fee": 0,
    },
}


class EFilingPrepEngine:
    def __init__(self):
        self.output_dir = LITOS_ROOT / "00_SYSTEM" / "efiling_packets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_packet(self, filing_name, config):
        """Prepare an e-filing packet."""
        system = EFILING_SYSTEMS[config["system"]]
        stack_path = LITOS_ROOT / config["stack_path"]
        packet_dir = self.output_dir / filing_name.replace(" ", "_")
        packet_dir.mkdir(parents=True, exist_ok=True)
        
        result = {
            "filing": filing_name,
            "system": system["name"],
            "url": system["url"],
            "packet_dir": str(packet_dir),
            "documents": [],
            "issues": [],
            "ready": True,
        }
        
        if not stack_path.exists():
            result["issues"].append(f"Stack path not found: {stack_path}")
            result["ready"] = False
            return result
        
        # Find and validate each required document
        for doc in config["documents"]:
            found = None
            # Search for PDF first, then MD
            for ext in ['.pdf', '.md', '.docx', '.txt']:
                for f in stack_path.rglob(f"*{ext}"):
                    # Check if filename matches pattern loosely
                    import fnmatch
                    if any(word in f.name.lower() for word in doc["pattern"].replace("*", "").split("*") if word):
                        found = f
                        break
                if found:
                    break
            
            if found:
                # Copy to packet
                dest = packet_dir / f"{doc['type']}_{found.name}"
                shutil.copy2(found, dest)
                
                size_mb = found.stat().st_size / (1024 * 1024)
                
                doc_info = {
                    "type": doc["type"],
                    "name": doc["name"],
                    "source": str(found),
                    "size_mb": round(size_mb, 2),
                    "format": found.suffix,
                }
                
                # Check size limit
                if size_mb > system["max_file_size_mb"]:
                    result["issues"].append(f"{doc['name']}: {size_mb:.1f}MB exceeds {system['max_file_size_mb']}MB limit")
                    doc_info["over_size"] = True
                    result["ready"] = False
                
                # Check format
                if found.suffix not in system["accepted_formats"]:
                    result["issues"].append(f"{doc['name']}: {found.suffix} format -- needs conversion to {system['accepted_formats']}")
                    doc_info["needs_conversion"] = True
                
                result["documents"].append(doc_info)
            else:
                result["documents"].append({
                    "type": doc["type"],
                    "name": doc["name"],
                    "source": None,
                    "missing": True,
                })
                result["issues"].append(f"MISSING: {doc['name']}")
                result["ready"] = False
        
        # Generate filing checklist
        checklist_path = packet_dir / "EFILING_CHECKLIST.md"
        with open(checklist_path, 'w', encoding='utf-8') as f:
            f.write(f"# E-Filing Checklist: {filing_name}\n\n")
            f.write(f"**System:** {system['name']} ({system['url']})\n")
            f.write(f"**Max File Size:** {system['max_file_size_mb']}MB\n")
            f.write(f"**Accepted Formats:** {', '.join(system['accepted_formats'])}\n\n")
            f.write("## Documents\n\n")
            for doc in result["documents"]:
                status = "READY" if not doc.get("missing") else "MISSING"
                f.write(f"- [{('x' if status == 'READY' else ' ')}] {doc['name']} ({status})\n")
            f.write(f"\n## Filing Steps\n\n")
            f.write(f"1. Go to {system['url']}\n")
            f.write(f"2. Log in (create account if needed)\n")
            f.write(f"3. Select court and case\n")
            f.write(f"4. Upload documents in order listed above\n")
            f.write(f"5. Pay filing fee (${config['fee']}) or attach fee waiver\n")
            f.write(f"6. Submit and save confirmation number\n")
            f.write(f"7. Serve all parties per proof of service\n")
            f.write(f"\n## Notes\n{system['notes']}\n")
        
        return result
    
    def prepare_all(self):
        """Prepare all filing packets."""
        results = []
        for name, config in FILING_CONFIGS.items():
            print(f"\nPreparing: {name}")
            result = self.prepare_packet(name, config)
            results.append(result)
            
            status = "READY" if result["ready"] else "NOT READY"
            print(f"  Status: {status} | {len(result['documents'])} docs | {len(result['issues'])} issues")
            for issue in result["issues"]:
                print(f"    ! {issue}")
        
        # Summary
        ready = sum(1 for r in results if r["ready"])
        print(f"\n{'=' * 60}")
        print(f"  E-FILING PREP SUMMARY: {ready}/{len(results)} packets ready")
        print(f"{'=' * 60}")
        
        # Save results
        with open(self.output_dir / "efiling_prep_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def run(self):
        return self.prepare_all()


if __name__ == "__main__":
    engine = EFilingPrepEngine()
    engine.run()
