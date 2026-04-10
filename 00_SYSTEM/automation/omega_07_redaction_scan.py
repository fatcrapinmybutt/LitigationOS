#!/usr/bin/env python3
"""
Ω7: PII REDACTION SCANNER — OMEGA-ELITE-MASTER
Right-click any folder → scan for SSNs, DOBs, phone numbers, financial info,
addresses, minor names. Critical for court filing preparation.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime
from collections import Counter

PII_PATTERNS = {
    "SSN": (r'\b\d{3}-\d{2}-\d{4}\b', "CRITICAL"),
    "SSN_NO_DASH": (r'\b\d{9}\b', "LOW"),
    "PHONE": (r'\b\d{3}[-.)]\s*\d{3}[-.)]\s*\d{4}\b', "MEDIUM"),
    "EMAIL": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "MEDIUM"),
    "DOB": (r'\b(?:DOB|[Dd]ate\s+of\s+[Bb]irth|[Bb]orn)\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', "HIGH"),
    "DRIVER_LICENSE": (r'\b[A-Z]\s*\d{3}\s*\d{3}\s*\d{3}\s*\d{3}\b', "CRITICAL"),
    "BANK_ACCOUNT": (r'\b(?:account|acct)\.?\s*#?\s*:?\s*\d{8,17}\b', "CRITICAL"),
    "ROUTING": (r'\b(?:routing|ABA)\s*#?\s*:?\s*\d{9}\b', "CRITICAL"),
    "CREDIT_CARD": (r'\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))\s*[-]?\s*\d{4}\s*[-]?\s*\d{4}\s*[-]?\s*\d{4}\b', "CRITICAL"),
    "MINOR_NAME": (r'\bLincoln\s+(?:Daniel\s+)?(?:Watson|Pigors)\b', "CRITICAL"),
    "MINOR_FIRST": (r'\bLincoln\b', "HIGH"),
    "IP_ADDRESS": (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "LOW"),
    "STREET_ADDRESS": (r'\b\d{1,5}\s+\w+\s+(?:St|Ave|Rd|Dr|Blvd|Ct|Ln|Way|Pl|Cir)\b', "MEDIUM"),
}

def scan_file(fp, target):
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return []

    findings = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for pii_type, (pattern, severity) in PII_PATTERNS.items():
            for match in re.finditer(pattern, line, re.IGNORECASE):
                val = match.group(0)
                # Mask sensitive value
                if severity == "CRITICAL":
                    masked = val[:2] + "***" + val[-2:] if len(val) > 4 else "***"
                else:
                    masked = val
                findings.append({
                    "type": pii_type, "severity": severity,
                    "value_masked": masked,
                    "file": str(fp.relative_to(target)),
                    "line": i + 1,
                    "context": line.strip()[:120]
                })
    return findings

def scan_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω7: PII REDACTION SCANNER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    all_findings = []
    severity_count = Counter()
    type_count = Counter()

    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.docx', '.csv', '.json') and fp.is_file():
            findings = scan_file(fp, target)
            all_findings.extend(findings)
            for f in findings:
                severity_count[f["severity"]] += 1
                type_count[f["type"]] += 1

    print(f"📊 PII SCAN RESULTS")
    print(f"  Total PII items found: {len(all_findings):,}")
    print(f"\n⚠️ BY SEVERITY:")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = severity_count.get(sev, 0)
        icon = "🔴" if sev == "CRITICAL" else "🟠" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
        print(f"  {icon} {sev:10s}: {count:,}")
    print(f"\n📋 BY TYPE:")
    for ptype, count in type_count.most_common():
        print(f"  {ptype:20s}: {count:,}")

    if severity_count.get("CRITICAL", 0) > 0:
        print(f"\n🔴 CRITICAL FINDINGS (redact before filing!):")
        for f in all_findings:
            if f["severity"] == "CRITICAL":
                print(f"  {f['type']:20s} in {f['file']}:{f['line']}")
                print(f"    Value: {f['value_masked']}")

    verdict = "🔴 REDACTION REQUIRED" if severity_count.get("CRITICAL", 0) > 0 else \
              "🟡 REVIEW RECOMMENDED" if severity_count.get("HIGH", 0) > 0 else "✅ CLEAN"
    print(f"\n{'='*60}")
    print(f"  {verdict}")
    print(f"{'='*60}")

    report_path = target / f"_pii_scan_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({"scan_time": datetime.now().isoformat(),
                    "total_findings": len(all_findings),
                    "severity_summary": dict(severity_count),
                    "type_summary": dict(type_count),
                    "findings": all_findings}, f, indent=2)
    print(f"\n📄 Report: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_07_redaction_scan.py <folder_path>")
        sys.exit(1)
    scan_folder(sys.argv[1])
    input("\nPress Enter to close...")
