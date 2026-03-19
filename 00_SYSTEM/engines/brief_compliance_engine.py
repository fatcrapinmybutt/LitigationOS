#!/usr/bin/env python3
"""Brief Compliance Engine v1.0 - MCR 7.212 validation for appellate briefs."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
from pathlib import Path
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class BriefComplianceEngine:
    """Validates appellate briefs against MCR 7.212 requirements."""
    
    # MCR 7.212(B) word limit
    MAX_WORDS = 16000
    
    # Required sections per MCR 7.212(A)
    REQUIRED_SECTIONS = [
        ("Table of Contents", r"(?i)(table\s+of\s+contents|contents)"),
        ("Index of Authorities", r"(?i)(index\s+of\s+authorities|table\s+of\s+authorities|authorities\s+cited)"),
        ("Statement of Jurisdiction", r"(?i)(statement\s+of\s+jurisdiction|jurisdictional?\s+statement|basis\s+(of|for)\s+jurisdiction)"),
        ("Questions Presented", r"(?i)(questions?\s+presented|issues?\s+presented|statement\s+of\s+(the\s+)?questions?)"),
        ("Statement of Facts", r"(?i)(statement\s+of\s+(the\s+)?facts|factual\s+background|background\s+facts)"),
        ("Argument", r"(?i)(^#+\s*argument|^argument\b|## argument|### argument)"),
        ("Relief Requested", r"(?i)(relief\s+requested|prayer\s+for\s+relief|conclusion\s+and\s+relief|wherefore)"),
    ]
    
    # Michigan citation patterns
    CITATION_PATTERNS = {
        "michigan_supreme": r"\d+\s+Mich\s+\d+",
        "michigan_appeals": r"\d+\s+Mich\s+App\s+\d+",
        "northwest_reporter": r"\d+\s+NW2?d?\s+\d+",
        "us_supreme": r"\d+\s+US\s+\d+",
        "federal_reporter": r"\d+\s+F\s*(?:2d|3d|4th)?\s+\d+",
        "usc": r"\d+\s+USC\s+[0-9a-z]+",
        "mcl": r"MCL\s+[0-9.]+",
        "mcr": r"MCR\s+[0-9.]+",
    }
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "file": None,
            "checks": [],
            "score": 0,
            "max_score": 0,
            "pass": False,
            "word_count": 0,
            "sections_found": [],
            "sections_missing": [],
            "citations": {},
            "issues": [],
            "recommendations": [],
        }
    
    def load_brief(self, filepath):
        """Load brief content from file.
        
        Args:
            filepath: Path to the brief file.
            
        Returns:
            str: File content, or empty string on failure.
        """
        self.results["file"] = str(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except (IOError, OSError) as e:
            logger.error("Failed to load brief %s: %s", filepath, e)
            return ""
    
    def check_word_count(self, content):
        """Check word count against MCR 7.212(B) limit."""
        # Strip markdown formatting, headers, tables for count
        # Remove code blocks, tables, captions
        clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        clean = re.sub(r'\|.*?\|', '', clean)  # table rows
        clean = re.sub(r'^#+\s+.*$', '', clean, flags=re.MULTILINE)  # headers (counted separately)
        clean = re.sub(r'---+', '', clean)
        clean = re.sub(r'\*\*|__|~~|`', '', clean)  # formatting
        
        words = len(clean.split())
        self.results["word_count"] = words
        
        passed = words <= self.MAX_WORDS
        pct = (words / self.MAX_WORDS) * 100
        
        check = {
            "name": "Word Count (MCR 7.212(B))",
            "passed": passed,
            "details": f"{words:,} / {self.MAX_WORDS:,} words ({pct:.1f}%)",
            "weight": 20,
        }
        
        if not passed:
            self.results["issues"].append(f"OVER WORD LIMIT: {words:,} words (max {self.MAX_WORDS:,}). Reduce by {words - self.MAX_WORDS:,} words.")
        elif pct > 90:
            self.results["recommendations"].append(f"Word count at {pct:.1f}% of limit. Consider trimming for safety margin.")
        
        self.results["checks"].append(check)
        return passed
    
    def check_required_sections(self, content):
        """Check for all MCR 7.212(A) required sections."""
        found = []
        missing = []
        
        for section_name, pattern in self.REQUIRED_SECTIONS:
            if re.search(pattern, content, re.MULTILINE):
                found.append(section_name)
            else:
                missing.append(section_name)
        
        self.results["sections_found"] = found
        self.results["sections_missing"] = missing
        
        passed = len(missing) == 0
        check = {
            "name": "Required Sections (MCR 7.212(A))",
            "passed": passed,
            "details": f"{len(found)}/{len(self.REQUIRED_SECTIONS)} sections found" + (f". Missing: {', '.join(missing)}" if missing else ""),
            "weight": 25,
        }
        
        for m in missing:
            self.results["issues"].append(f"MISSING REQUIRED SECTION: {m}")
        
        self.results["checks"].append(check)
        return passed
    
    def check_citations(self, content):
        """Analyze citation usage and format."""
        citations = {}
        total = 0
        
        for name, pattern in self.CITATION_PATTERNS.items():
            matches = re.findall(pattern, content)
            citations[name] = len(matches)
            total += len(matches)
        
        self.results["citations"] = citations
        self.results["citation_count"] = total
        
        # Check for proper case citation format: Name v Name, xxx Mich xxx; xxx (year)
        case_citations = re.findall(r'[A-Z][a-z]+ v [A-Z][a-z]+', content)
        
        passed = total >= 5  # At least 5 citations expected in an appellate brief
        check = {
            "name": "Citation Analysis",
            "passed": passed,
            "details": f"{total} citations found ({len(case_citations)} case citations). Types: " + ", ".join(f"{k}={v}" for k, v in citations.items() if v > 0),
            "weight": 15,
        }
        
        if total < 5:
            self.results["issues"].append(f"LOW CITATION COUNT: Only {total} citations found. Appellate briefs typically need 15+.")
        if citations.get("mcr", 0) == 0:
            self.results["recommendations"].append("No MCR citations found. Consider citing applicable court rules.")
        
        self.results["checks"].append(check)
        return passed
    
    def check_appendix_reference(self, content):
        """Check for appendix references per MCR 7.212(C)."""
        has_appendix_ref = bool(re.search(r'(?i)(appendix|app[\s-]?\d+|see\s+appendix)', content))
        
        check = {
            "name": "Appendix Reference (MCR 7.212(C))",
            "passed": has_appendix_ref,
            "details": "Appendix referenced in brief" if has_appendix_ref else "No appendix references found",
            "weight": 10,
        }
        
        if not has_appendix_ref:
            self.results["issues"].append("NO APPENDIX REFERENCE: MCR 7.212(C) requires a separate appendix.")
        
        self.results["checks"].append(check)
        return has_appendix_ref
    
    def check_signature_block(self, content):
        """Check for proper signature block."""
        has_sig = bool(re.search(r'(?i)(respectfully\s+submitted|pro\s+se|/s/|signature|andrew\s+pigors)', content))
        
        check = {
            "name": "Signature Block",
            "passed": has_sig,
            "details": "Signature block found" if has_sig else "No signature block detected",
            "weight": 10,
        }
        
        if not has_sig:
            self.results["issues"].append("MISSING SIGNATURE BLOCK: Brief must include signature with name, address, phone.")
        
        self.results["checks"].append(check)
        return has_sig
    
    def check_caption(self, content):
        """Check for proper court caption."""
        has_caption = bool(re.search(r'(?i)(court\s+of\s+appeals|circuit\s+court|case\s+no|docket\s+no)', content))
        has_parties = bool(re.search(r'(?i)(appellant|appellee|petitioner|respondent|plaintiff|defendant)', content))
        
        passed = has_caption and has_parties
        check = {
            "name": "Court Caption",
            "passed": passed,
            "details": f"Caption: {'Yes' if has_caption else 'No'}, Parties: {'Yes' if has_parties else 'No'}",
            "weight": 10,
        }
        
        if not passed:
            self.results["issues"].append("INCOMPLETE CAPTION: Must include court name, case number, and party designations.")
        
        self.results["checks"].append(check)
        return passed
    
    def check_placeholder_contamination(self, content):
        """Check for unresolved placeholders that would invalidate the filing."""
        patterns = [r'\[PLACEHOLDER[^\]]*\]', r'\[TODO[^\]]*\]', r'\[INSERT[^\]]*\]', r'\[ANDREW[^\]]*\]', r'\[TBD[^\]]*\]', r'XXX+', r'\[FILL[^\]]*\]']
        
        found = []
        for p in patterns:
            matches = re.findall(p, content, re.IGNORECASE)
            found.extend(matches)
        
        passed = len(found) == 0
        check = {
            "name": "Placeholder Contamination",
            "passed": passed,
            "details": f"{'Clean - no placeholders' if passed else f'{len(found)} unresolved placeholders: ' + ', '.join(found[:5])}",
            "weight": 10,
        }
        
        if not passed:
            self.results["issues"].append(f"UNRESOLVED PLACEHOLDERS: {len(found)} found. Must resolve before filing.")
            for ph in found[:10]:
                self.results["issues"].append(f"  --> {ph}")
        
        self.results["checks"].append(check)
        return passed
    
    def calculate_score(self):
        """Calculate compliance score."""
        total_weight = sum(c["weight"] for c in self.results["checks"])
        earned = sum(c["weight"] for c in self.results["checks"] if c["passed"])
        
        self.results["max_score"] = total_weight
        self.results["score"] = earned
        self.results["pass"] = earned >= total_weight * 0.7  # 70% minimum
        
        return self.results["score"]
    
    def generate_report(self):
        """Generate compliance report."""
        lines = []
        lines.append("=" * 70)
        lines.append("  BRIEF COMPLIANCE REPORT (MCR 7.212)")
        lines.append(f"  Generated: {self.results['timestamp']}")
        lines.append(f"  File: {self.results['file']}")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"  SCORE: {self.results['score']}/{self.results['max_score']} ({'PASS' if self.results['pass'] else 'FAIL'})")
        lines.append(f"  Word Count: {self.results['word_count']:,} / {self.MAX_WORDS:,}")
        lines.append("")
        
        lines.append("  CHECKS:")
        for c in self.results["checks"]:
            icon = "[PASS]" if c["passed"] else "[FAIL]"
            lines.append(f"    {icon} {c['name']} ({c['weight']}pts)")
            lines.append(f"          {c['details']}")
        
        if self.results["issues"]:
            lines.append("")
            lines.append("  ISSUES:")
            for issue in self.results["issues"]:
                lines.append(f"    ! {issue}")
        
        if self.results["recommendations"]:
            lines.append("")
            lines.append("  RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                lines.append(f"    > {rec}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def validate(self, filepath):
        """Run full compliance validation on a brief.
        
        Args:
            filepath: Path to the brief file to validate.
            
        Returns:
            tuple: (report_text, results_dict) or (error_text, error_dict) on failure.
        """
        if not filepath:
            logger.error("No filepath provided to validate()")
            return "ERROR: No file specified", {"error": "No filepath provided"}
        if not os.path.isfile(filepath):
            logger.error("File not found: %s", filepath)
            return f"ERROR: File not found: {filepath}", {"error": f"File not found: {filepath}"}
        content = self.load_brief(filepath)
        
        self.check_word_count(content)
        self.check_required_sections(content)
        self.check_citations(content)
        self.check_appendix_reference(content)
        self.check_signature_block(content)
        self.check_caption(content)
        self.check_placeholder_contamination(content)
        
        self.calculate_score()
        report = self.generate_report()
        
        return report, self.results


def scan_all_briefs(base_dir):
    """Scan all brief files in the LitigationOS directory."""
    brief_patterns = ['*brief*', '*BRIEF*', '*motion*', '*MOTION*', '*complaint*', '*COMPLAINT*']
    results = []
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.md') and any(p.replace('*', '').lower() in f.lower() for p in ['brief', 'motion', 'complaint']):
                filepath = os.path.join(root, f)
                try:
                    engine = BriefComplianceEngine()
                    report, result = engine.validate(filepath)
                    results.append(result)
                    print(f"  {'PASS' if result['pass'] else 'FAIL'} ({result['score']}/{result['max_score']}) {f} [{result['word_count']:,} words]")
                except Exception as e:
                    logger.error("Failed to validate %s: %s", f, e)
    
    return results


if __name__ == "__main__":
    import sys
    
    try:
        if len(sys.argv) > 1:
            # Validate specific file
            filepath = sys.argv[1]
            engine = BriefComplianceEngine()
            report, results = engine.validate(filepath)
            print(report)
        else:
            # Scan all briefs
            base = r"C:\Users\andre\LitigationOS"
            print("=" * 70)
            print("  BRIEF COMPLIANCE SCAN")
            print("=" * 70)
            print()
            all_results = scan_all_briefs(base)
            
            passed = sum(1 for r in all_results if r['pass'])
            print(f"\n  TOTAL: {len(all_results)} briefs scanned, {passed} passed, {len(all_results)-passed} need attention")
            
            # Save results
            output = Path(base) / "00_SYSTEM" / "BRIEF_COMPLIANCE_REPORT.json"
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"  Report saved: {output}")
    except Exception as e:
        logger.error("Brief compliance engine failed: %s", e)
        print(f"[ERROR] Brief compliance engine failed: {e}")
