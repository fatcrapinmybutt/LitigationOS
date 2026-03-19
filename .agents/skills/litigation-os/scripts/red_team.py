#!/usr/bin/env python3
"""Red Team — Automated adversarial analysis of court filings."""

import json
import sys
from dataclasses import dataclass, field

ATTACK_VECTORS = {
    "procedural": [
        {"id": "P1", "name": "Jurisdiction defect", "severity": "critical", "check": "Subject matter + personal jurisdiction verified?"},
        {"id": "P2", "name": "Venue improper", "severity": "critical", "check": "Correct county/division per MCR 2.221-2.226?"},
        {"id": "P3", "name": "Service defect", "severity": "critical", "check": "Proper method per MCR 2.103-2.107? Proof filed?"},
        {"id": "P4", "name": "Statute of limitations", "severity": "critical", "check": "Filed within SOL per MCL 600.5805-5856?"},
        {"id": "P5", "name": "Standing defect", "severity": "major", "check": "Injury-in-fact + causation + redressability?"},
        {"id": "P6", "name": "Capacity defect", "severity": "major", "check": "Correct legal name and capacity?"},
        {"id": "P7", "name": "Exhaustion failure", "severity": "major", "check": "Administrative remedies exhausted?"},
        {"id": "P8", "name": "Res judicata / Collateral estoppel", "severity": "critical", "check": "No prior adjudication bars?"},
    ],
    "substantive": [
        {"id": "S1", "name": "Element failure", "severity": "critical", "check": "Every element supported by evidence?"},
        {"id": "S2", "name": "Authority weakness", "severity": "major", "check": "Citations current, on-point, not distinguishable?"},
        {"id": "S3", "name": "Evidence gap", "severity": "major", "check": "Key facts have record support?"},
        {"id": "S4", "name": "Contradicted fact", "severity": "critical", "check": "No assertion contradicted by record evidence?"},
        {"id": "S5", "name": "Hearsay exposure", "severity": "major", "check": "Hearsay evidence has exception identified?"},
        {"id": "S6", "name": "Privilege claim", "severity": "minor", "check": "No privileged material improperly used?"},
        {"id": "S7", "name": "Weight vs admissibility", "severity": "minor", "check": "Evidence weight assessed realistically?"},
    ],
    "strategic": [
        {"id": "T1", "name": "Remedy mismatch", "severity": "major", "check": "Relief available for the claim asserted?"},
        {"id": "T2", "name": "Proportionality", "severity": "minor", "check": "Relief proportionate to harm shown?"},
        {"id": "T3", "name": "Credibility attack", "severity": "major", "check": "Key witnesses impeachment-resistant?"},
        {"id": "T4", "name": "Alternative explanation", "severity": "major", "check": "Facts don't support opposing narrative better?"},
        {"id": "T5", "name": "Equitable defense", "severity": "minor", "check": "No unclean hands, laches, estoppel?"},
    ],
    "compliance": [
        {"id": "F1", "name": "Page limit", "severity": "minor", "check": "Within MCR page limits?"},
        {"id": "F2", "name": "Required sections", "severity": "major", "check": "TOC, TOA, certificate of service present?"},
        {"id": "F3", "name": "Citation format", "severity": "minor", "check": "Michigan citation format standard?"},
        {"id": "F4", "name": "Caption errors", "severity": "major", "check": "Case number, parties, court correct per MCR 2.113?"},
    ],
}


@dataclass
class Finding:
    vector_id: str
    vector_name: str
    severity: str
    finding: str
    mitigation: str = ""
    resolved: bool = False


@dataclass
class RedTeamReport:
    filing_name: str
    lane: str
    score: int = 100
    findings: list = field(default_factory=list)

    def add_finding(self, f: Finding):
        self.findings.append(f)
        penalty = {"critical": 20, "major": 10, "minor": 3}.get(f.severity, 5)
        self.score = max(0, self.score - penalty)

    def status(self) -> str:
        if self.score >= 90: return "BATTLE-READY"
        if self.score >= 75: return "STRONG"
        if self.score >= 50: return "VULNERABLE"
        return "EXPOSED"

    def to_vr_block(self) -> str:
        critical = sum(1 for f in self.findings if f.severity == "critical")
        major = sum(1 for f in self.findings if f.severity == "major")
        minor = sum(1 for f in self.findings if f.severity == "minor")
        resolved = sum(1 for f in self.findings if f.resolved)
        lines = [
            f"[VR] RED_TEAM_REPORT",
            f"  Filing: {self.filing_name}",
            f"  Lane: {self.lane}",
            f"  Score: {self.score}/100 ({self.status()})",
            f"  Attack Vectors Found: {len(self.findings)}",
            f"  Critical: {critical}",
            f"  Major: {major}",
            f"  Minor: {minor}",
            f"  Mitigations Applied: {resolved}",
        ]
        for f in self.findings:
            prefix = "✅" if f.resolved else "❌"
            lines.append(f"  {prefix} [{f.severity.upper()}] {f.vector_id}: {f.finding}")
            if f.mitigation:
                lines.append(f"      → {f.mitigation}")
        return "\n".join(lines)


def get_checklist() -> list[dict]:
    """Return flat checklist of all attack vectors."""
    checks = []
    for category, vectors in ATTACK_VECTORS.items():
        for v in vectors:
            checks.append({**v, "category": category})
    return checks


if __name__ == "__main__":
    checklist = get_checklist()
    print(f"Red Team Attack Vectors: {len(checklist)}")
    for c in checklist:
        print(f"  [{c['severity'].upper():8s}] {c['id']}: {c['name']}")
        print(f"           Check: {c['check']}")
