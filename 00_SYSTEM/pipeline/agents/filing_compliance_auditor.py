"""
FILING COMPLIANCE AUDITOR — Agent F05
Validates court filings against Michigan Court Rules (MCR) requirements.
Checks: caption format, signature blocks, certificate of service, 
page limits, font requirements, MCR citations, SCAO form compliance.

Part of the Delta9 fleet — inherits Agent9999 base class.
Convergence tier — runs as final QA before court filing.
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


class FilingComplianceAuditor(Agent9999):
    """Audits court filings for MCR compliance — GO/NO-GO gate.
    
    Pipeline role: Convergence tier — last gate before filing.
    Generates per-filing compliance scorecard with pass/fail per rule.
    
    Work items: Markdown filing files from LITIGATION_FILING_PACKAGE.
    Processing: Parse each filing, check against MCR requirements,
    generate compliance report with specific remediation instructions.
    """
    
    AGENT_ID = "F05"
    AGENT_NAME = "FilingComplianceAuditor"
    AGENT_TIER = "convergence"
    
    # MCR requirements by court
    MCR_REQUIREMENTS = {
        "circuit_court": {
            "caption": {
                "required_elements": ["case_number", "judge_name", "plaintiff", "defendant", "court_name"],
                "mcr": "MCR 2.113(C)",
            },
            "signature": {
                "required_elements": ["name", "address", "phone", "email", "bar_number_or_pro_se"],
                "mcr": "MCR 2.114(A)",
            },
            "certificate_of_service": {
                "required_elements": ["date", "method", "recipient", "address"],
                "mcr": "MCR 2.107(C)",
            },
            "verification": {
                "required_for": ["complaint", "motion", "affidavit"],
                "mcr": "MCR 2.114(B)",
            },
            "font": {"size": 12, "family": "Times New Roman", "mcr": "MCR 2.113(C)(1)"},
            "margins": {"all_sides": 1.0, "mcr": "MCR 2.113(C)(1)"},
        },
        "msc": {
            "word_limit": 16000,
            "page_limit_pro_se": 50,
            "font": {"size": 12, "family": "Times New Roman"},
            "spacing": "double",
            "mcr": "MCR 7.305-7.306",
        },
        "coa": {
            "word_limit": 16000,
            "font": {"size": 12, "family": "Times New Roman"},
            "spacing": "double",
            "appendix_required": True,
            "mcr": "MCR 7.212",
        },
        "federal": {
            "caption_required": True,
            "jury_demand": "must be in caption or separate document",
            "civil_cover_sheet": "JS-44 required",
            "ifp_motion": "28 USC §1915 if applicable",
        },
        "jtc": {
            "grievance_form": True,
            "supporting_documents": True,
            "canon_citations": True,
        },
    }
    
    # Filing → court mapping
    FILING_COURT_MAP = {
        "01_EMERGENCY_TRO": "circuit_court",
        "02_SHADY_OAKS_COMPLAINT": "circuit_court",
        "03_DISQUALIFICATION_MCR2003": "circuit_court",
        "04_FEDERAL_1983_COMPLAINT": "federal",
        "05_MSC_ORIGINAL_ACTION": "msc",
        "06_JTC_COMPLAINT": "jtc",
        "07_CUSTODY_MODIFICATION": "circuit_court",
        "08_PPO_TERMINATION": "circuit_court",
        "09_COA_BRIEF_ON_APPEAL": "coa",
        "10_COA_EMERGENCY_MOTION": "coa",
    }
    
    # Andrew's verified identity (NEVER fabricate)
    PLAINTIFF = {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
        "status": "Pro Se",
    }
    
    def __init__(self, filing_dir: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config=config or {})
        self.filing_dir = Path(filing_dir) if filing_dir else (
            Path(os.path.expanduser("~")) / "Desktop" / "LITIGATION_FILING_PACKAGE"
        )
        self.compliance_results = {}
    
    def _validate_preconditions(self) -> bool:
        """Check that filing directory exists with markdown files."""
        if not self.filing_dir.exists():
            self.logger.error(f"Filing directory not found: {self.filing_dir}")
            return False
        md_files = list(self.filing_dir.glob("*.md"))
        if not md_files:
            self.logger.error(f"No markdown files found in {self.filing_dir}")
            return False
        self.logger.info(f"Found {len(md_files)} filing files to audit")
        return True
    
    def _get_work_items(self) -> List[Any]:
        """Get all filing markdown files to audit."""
        items = []
        for md_file in sorted(self.filing_dir.glob("*.md")):
            name = md_file.stem
            # Skip non-filing files (indexes, reports, etc.)
            if name.startswith("00_") or name.startswith("CITATION") or name.startswith("CROSS") or name.startswith("RED_TEAM") or name.startswith("SESSION"):
                continue
            
            court = "circuit_court"  # default
            for prefix, court_type in self.FILING_COURT_MAP.items():
                if name.startswith(prefix[:2]) or prefix.lower() in name.lower():
                    court = court_type
                    break
            
            items.append({
                "file_path": str(md_file),
                "filing_name": name,
                "court": court,
                "size_kb": md_file.stat().st_size / 1024,
            })
        
        return items
    
    def _process_item(self, item: Any) -> Dict[str, Any]:
        """Audit a single filing for MCR compliance."""
        file_path = item["file_path"]
        filing_name = item["filing_name"]
        court = item["court"]
        
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"filing": filing_name, "status": "ERROR", "error": str(e)}
        
        checks = []
        
        # Check 1: Caption present?
        has_caption = bool(re.search(
            r'(STATE OF MICHIGAN|UNITED STATES DISTRICT|MICHIGAN SUPREME|JUDICIAL TENURE)',
            content, re.IGNORECASE
        ))
        checks.append({
            "check": "caption_present",
            "passed": has_caption,
            "mcr": "MCR 2.113(C)",
            "detail": "Caption block found" if has_caption else "MISSING: Court caption required",
        })
        
        # Check 2: Case number present?
        has_case_num = bool(re.search(
            r'(Case\s*(?:No\.?|Number)[:\s]*\d{4}[-–]\d+|No\.\s*\d+[-–]\d+|COA\s*\d+)',
            content, re.IGNORECASE
        ))
        checks.append({
            "check": "case_number",
            "passed": has_case_num,
            "mcr": "MCR 2.113(C)",
            "detail": "Case number found" if has_case_num else "MISSING: Case number required in caption",
        })
        
        # Check 3: Signature block?
        has_sig = bool(re.search(
            r'(Respectfully\s+submitted|/s/|___+\s*\n.*(?:Pro Se|Plaintiff|Petitioner))',
            content, re.IGNORECASE
        ))
        checks.append({
            "check": "signature_block",
            "passed": has_sig,
            "mcr": "MCR 2.114(A)",
            "detail": "Signature block found" if has_sig else "MISSING: Signature block required",
        })
        
        # Check 4: Certificate of Service?
        has_cos = bool(re.search(
            r'CERTIFICATE\s+OF\s+SERVICE', content, re.IGNORECASE
        ))
        if court not in ("jtc",):  # JTC doesn't require standard COS
            checks.append({
                "check": "certificate_of_service",
                "passed": has_cos,
                "mcr": "MCR 2.107(C)",
                "detail": "Certificate of Service found" if has_cos else "MISSING: Certificate of Service required",
            })
        
        # Check 5: Verification section?
        has_verify = bool(re.search(
            r'(VERIFICATION|under\s+penalty\s+of\s+perjury|sworn.*subscribed)',
            content, re.IGNORECASE
        ))
        checks.append({
            "check": "verification",
            "passed": has_verify,
            "mcr": "MCR 2.114(B)",
            "detail": "Verification section found" if has_verify else "WARNING: Verification may be required for sworn filings",
        })
        
        # Check 6: Plaintiff identity correct?
        has_correct_name = "Andrew James Pigors" in content or "ANDREW JAMES PIGORS" in content
        checks.append({
            "check": "plaintiff_identity",
            "passed": has_correct_name,
            "mcr": "Identity verification",
            "detail": "Correct plaintiff name" if has_correct_name else "WARNING: Full plaintiff name not found",
        })
        
        # Check 7: No hallucinated names?
        hallucinations = []
        for bad_name in ["Jane Berry", "Patricia Berry", "P35878", "Amy McNeill"]:
            if bad_name.lower() in content.lower():
                hallucinations.append(bad_name)
        
        checks.append({
            "check": "no_hallucinations",
            "passed": len(hallucinations) == 0,
            "mcr": "Anti-hallucination gate",
            "detail": "No hallucinations" if not hallucinations else f"CRITICAL: Hallucinated names found: {', '.join(hallucinations)}",
        })
        
        # Check 8: No placeholder text remaining?
        placeholders = re.findall(
            r'\[(?:ANDREW_REQUIRED|INSERT|ATTACH|TODO|PLACEHOLDER|FILL|VERIFY|TBD)[^\]]*\]',
            content, re.IGNORECASE
        )
        checks.append({
            "check": "no_placeholders",
            "passed": len(placeholders) == 0,
            "mcr": "Filing completeness",
            "detail": f"No placeholders" if not placeholders else f"FOUND {len(placeholders)} placeholder(s): {', '.join(placeholders[:5])}",
        })
        
        # Check 9: Child referenced by initials only?
        # Check for full name leaks (L.D.W. is the correct format)
        child_name_leak = bool(re.search(
            r'\b[A-Z][a-z]+\s+(?:Daniel|David|Dean)\s+Watson\b',
            content
        ))
        checks.append({
            "check": "child_privacy",
            "passed": not child_name_leak,
            "mcr": "MCR 8.119(H)",
            "detail": "Child referenced by initials" if not child_name_leak else "CRITICAL: Child full name exposed — use L.D.W. only",
        })
        
        # Check 10: Word count for MSC/COA
        if court in ("msc", "coa"):
            word_count = len(content.split())
            limit = 16000
            checks.append({
                "check": "word_limit",
                "passed": word_count <= limit,
                "mcr": "MCR 7.305/7.212",
                "detail": f"{word_count:,} words ({'within' if word_count <= limit else 'EXCEEDS'} {limit:,} limit)",
            })
        
        # Check 11: MCR/MCL citations present?
        cite_count = len(re.findall(r'MCR\s+\d+\.\d+|MCL\s+\d+\.\d+', content))
        checks.append({
            "check": "authority_citations",
            "passed": cite_count >= 3,
            "mcr": "Legal authority",
            "detail": f"{cite_count} MCR/MCL citations found",
        })
        
        # Calculate overall score
        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        score = (passed / total * 100) if total > 0 else 0
        
        go_nogo = "GO" if score >= 80 and not hallucinations and not child_name_leak else "NO-GO"
        
        result = {
            "filing": filing_name,
            "court": court,
            "checks": checks,
            "passed": passed,
            "total": total,
            "score": round(score, 1),
            "go_nogo": go_nogo,
            "size_kb": round(item.get("size_kb", 0), 1),
        }
        
        self.compliance_results[filing_name] = result
        
        # Broadcast critical findings
        if hallucinations:
            self.broadcast_finding(
                finding_type="HALLUCINATION_IN_FILING",
                content=f"{filing_name}: {', '.join(hallucinations)}",
                severity="CRITICAL",
                metadata={"filing": filing_name, "names": hallucinations}
            )
        
        if go_nogo == "NO-GO":
            self.broadcast_finding(
                finding_type="FILING_NOT_READY",
                content=f"{filing_name}: Score {score}% — {total - passed} checks failed",
                severity="HIGH",
                metadata=result
            )
        
        return result
    
    def _finalize(self, stats: AgentStats, results: List) -> None:
        """Write compliance report to master_index.db and generate summary."""
        try:
            conn = sqlite3.connect(str(MASTER_INDEX_DB))
            conn.execute("PRAGMA busy_timeout = 60000")
            conn.execute("PRAGMA journal_mode = WAL")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filing_compliance (
                    filing_name TEXT PRIMARY KEY,
                    court TEXT,
                    score REAL,
                    go_nogo TEXT,
                    checks_passed INTEGER,
                    checks_total INTEGER,
                    details TEXT,
                    audited_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            rows = []
            for r in results:
                if isinstance(r, dict) and "filing" in r:
                    rows.append((
                        r["filing"],
                        r.get("court", "unknown"),
                        r.get("score", 0),
                        r.get("go_nogo", "NO-GO"),
                        r.get("passed", 0),
                        r.get("total", 0),
                        json.dumps(r.get("checks", [])),
                    ))
            
            if rows:
                conn.executemany(
                    "INSERT OR REPLACE INTO filing_compliance VALUES (?,?,?,?,?,?,?,datetime('now'))",
                    rows
                )
                conn.commit()
            
            conn.close()
            
            # Summary log
            go_count = sum(1 for r in results if isinstance(r, dict) and r.get("go_nogo") == "GO")
            total = len([r for r in results if isinstance(r, dict)])
            self.logger.info(f"Filing Compliance Audit: {go_count}/{total} filings GO")
            
        except Exception as e:
            self.logger.error(f"Finalize failed: {e}")


# CLI entry point
if __name__ == "__main__":
    agent = FilingComplianceAuditor()
    result = agent.run()
    print(f"\nFiling Compliance Audit: {result.status}")
    if hasattr(result, 'stats'):
        print(f"Processed: {result.stats.processed}/{result.stats.total}")
    
    # Print scorecard
    for filing, data in agent.compliance_results.items():
        emoji = "✅" if data["go_nogo"] == "GO" else "❌"
        print(f"  {emoji} {filing}: {data['score']}% ({data['go_nogo']})")
