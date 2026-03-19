#!/usr/bin/env python3
"""Pre-Filing QA Engine v1.0 - GO/NO-GO compliance checking."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
from pathlib import Path
from datetime import datetime

LITOS_ROOT = r"C:\Users\andre\LitigationOS"

FILING_STACKS = {
    "McNeill Disqualification": {
        "path": "02_TRIAL_14TH/FULL_14TH_STACK/DISQUALIFY_PACKAGE",
        "deadline": "2026-03-15",
        "court": "14th Circuit Court",
        "required_docs": ["motion", "brief", "proposed_order", "certificate_of_service", "verification"],
    },
    "COA Brief 366810": {
        "path": "01_COA_366810",
        "deadline": "2026-04-15",
        "court": "Michigan Court of Appeals",
        "required_docs": ["brief", "appendix", "proof_of_service", "table_of_contents"],
    },
    "Watson Tort": {
        "path": "02_TRIAL_14TH/WATSON_TORT",
        "deadline": "2026-04-30",
        "court": "14th Circuit Court",
        "required_docs": ["complaint", "summons", "verification", "fee_waiver", "proof_of_service"],
    },
    "Shady Oaks": {
        "path": "02_TRIAL_14TH/SHADY_OAKS",
        "deadline": "2026-04-30",
        "court": "14th Circuit Court",
        "required_docs": ["complaint", "summons", "verification", "fee_waiver", "proof_of_service", "corporate_disclosure"],
    },
    "MSC Original Action": {
        "path": "04_MSC_ORIGINAL_ACTION",
        "deadline": "2026-04-01",
        "court": "Michigan Supreme Court",
        "required_docs": ["complaint", "brief", "appendix", "verification", "fee_waiver", "proof_of_service"],
    },
    "Federal 1983": {
        "path": "03_FEDERAL_1983/WDMI_FULL_STACK",
        "deadline": "2029-12-31",
        "court": "WDMI Federal Court",
        "required_docs": ["complaint", "js44", "summons", "ifp_application"],
    },
}

class PreFilingQAEngine:
    def __init__(self, stack_name, stack_config):
        self.name = stack_name
        self.config = stack_config
        self.path = Path(LITOS_ROOT) / stack_config["path"]
        self.issues = []
        self.warnings = []
        self.checks = {}
        self.verdict = "UNKNOWN"
    
    def check_documents_exist(self):
        """Check all required documents are present."""
        if not self.path.exists():
            self.issues.append(f"STACK DIRECTORY MISSING: {self.path}")
            self.checks["document_completeness"] = False
            return False
        
        all_files = []
        for f in self.path.rglob("*"):
            if f.is_file():
                all_files.append(f.name.lower())
        
        found = []
        missing = []
        for doc in self.config["required_docs"]:
            if any(doc.lower() in fn for fn in all_files):
                found.append(doc)
            else:
                missing.append(doc)
        
        self.checks["document_completeness"] = len(missing) == 0
        if missing:
            self.issues.append(f"MISSING DOCUMENTS: {', '.join(missing)}")
        
        return len(missing) == 0
    
    def check_placeholders(self):
        """Check for unresolved placeholders."""
        placeholder_count = 0
        placeholder_files = []
        
        if not self.path.exists():
            return False
        
        for f in self.path.rglob("*.md"):
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
                patterns = [r'\[PLACEHOLDER[^\]]*\]', r'\[TODO[^\]]*\]', r'\[INSERT[^\]]*\]', r'\[ANDREW[^\]]*\]', r'\[TBD[^\]]*\]', r'XXX+']
                count = 0
                for p in patterns:
                    count += len(re.findall(p, content, re.IGNORECASE))
                if count > 0:
                    placeholder_count += count
                    placeholder_files.append((f.name, count))
            except:
                continue
        
        self.checks["no_placeholders"] = placeholder_count == 0
        if placeholder_count > 0:
            self.warnings.append(f"UNRESOLVED PLACEHOLDERS: {placeholder_count} in {len(placeholder_files)} files")
            for fn, cnt in placeholder_files[:5]:
                self.warnings.append(f"  {fn}: {cnt} placeholders")
        
        return placeholder_count == 0
    
    def check_signatures(self):
        """Check for signature blocks."""
        has_sig = False
        if not self.path.exists():
            return False
            
        for f in self.path.rglob("*.md"):
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
                if re.search(r'(?i)(respectfully\s+submitted|/s/|signature|andrew\s+pigors)', content):
                    has_sig = True
                    break
            except:
                continue
        
        self.checks["signature_present"] = has_sig
        if not has_sig:
            self.warnings.append("NO SIGNATURE BLOCK FOUND: Ensure at least one document has proper signature")
        
        return has_sig
    
    def check_service(self):
        """Check for proof/certificate of service."""
        has_service = False
        if not self.path.exists():
            return False
            
        for f in self.path.rglob("*"):
            if 'service' in f.name.lower() or 'certificate' in f.name.lower():
                has_service = True
                break
        
        self.checks["service_packet"] = has_service
        if not has_service:
            self.issues.append("NO PROOF OF SERVICE: Required for all court filings")
        
        return has_service
    
    def check_deadline(self):
        """Check deadline urgency."""
        today = datetime.now().date()
        deadline = datetime.strptime(self.config["deadline"], "%Y-%m-%d").date()
        days = (deadline - today).days
        
        self.checks["deadline_days"] = days
        
        if days < 0:
            self.issues.append(f"OVERDUE by {abs(days)} days!")
        elif days <= 3:
            self.issues.append(f"EMERGENCY: {days} days to deadline!")
        elif days <= 7:
            self.warnings.append(f"CRITICAL: {days} days to deadline")
        
        return days
    
    def run(self):
        """Execute all QA checks."""
        self.check_documents_exist()
        self.check_placeholders()
        self.check_signatures()
        self.check_service()
        days = self.check_deadline()
        
        # Determine verdict
        critical_checks = ["document_completeness", "service_packet"]
        critical_pass = all(self.checks.get(c, False) for c in critical_checks)
        
        if len(self.issues) == 0:
            self.verdict = "GO"
        elif critical_pass and len(self.issues) <= 2:
            self.verdict = "CONDITIONAL"
        else:
            self.verdict = "NO-GO"
        
        return self.verdict
    
    def report(self):
        """Generate QA report."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  PRE-FILING QA REPORT")
        lines.append(f"  {self.name} | {self.config['court']}")
        lines.append(f"  Deadline: {self.config['deadline']} | {self.checks.get('deadline_days', '?')} days")
        lines.append("=" * 60)
        lines.append(f"")
        lines.append(f"  VERDICT: {self.verdict}")
        lines.append("")
        
        if self.issues:
            lines.append("  CRITICAL ISSUES:")
            for i in self.issues:
                lines.append(f"    ! {i}")
            lines.append("")
        
        if self.warnings:
            lines.append("  WARNINGS:")
            for w in self.warnings:
                lines.append(f"    ~ {w}")
            lines.append("")
        
        lines.append("  CHECKLIST:")
        for check, passed in self.checks.items():
            if check == "deadline_days":
                continue
            icon = "[x]" if passed else "[ ]"
            lines.append(f"    {icon} {check.replace('_', ' ').title()}")
        
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


def run_all_qa():
    """Run QA on all filing stacks."""
    print("=" * 60)
    print("  LITIGATIONOS PRE-FILING QA SWEEP")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()
    
    all_results = []
    
    for name, config in sorted(FILING_STACKS.items(), key=lambda x: x[1]["deadline"]):
        engine = PreFilingQAEngine(name, config)
        verdict = engine.run()
        report = engine.report()
        print(report)
        print()
        all_results.append({
            "name": name,
            "verdict": verdict,
            "issues": engine.issues,
            "warnings": engine.warnings,
            "checks": engine.checks,
        })
    
    # Summary
    go = sum(1 for r in all_results if r["verdict"] == "GO")
    cond = sum(1 for r in all_results if r["verdict"] == "CONDITIONAL")
    nogo = sum(1 for r in all_results if r["verdict"] == "NO-GO")
    
    print("=" * 60)
    print(f"  SUMMARY: {go} GO | {cond} CONDITIONAL | {nogo} NO-GO")
    print("=" * 60)
    
    # Save results
    output = Path(LITOS_ROOT) / "00_SYSTEM" / "PREFILING_QA_REPORT.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Report saved: {output}")
    
    return all_results


if __name__ == "__main__":
    run_all_qa()
