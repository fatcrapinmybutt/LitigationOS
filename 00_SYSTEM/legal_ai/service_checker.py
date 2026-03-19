# -*- coding: utf-8 -*-
"""
service_checker.py — Proof of Service Requirements Checker
============================================================
For every defendant × case combination, verifies:
  - Service method (personal, mail, substituted, publication)
  - Service date computation per MCR 2.105/2.107
  - Proof of Service template generation
  - Service completeness tracking

Michigan Court Rules:
  - MCR 2.105: Service of process methods
  - MCR 2.107: Service and filing of pleadings
  - MCR 2.108: Time for service; default

Zero external dependencies. Local-only.
"""

import re
import json
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


# ─── Data Classes ───

@dataclass
class Defendant:
    """A named defendant requiring service."""
    name: str
    case_number: str
    address: Optional[str] = None
    service_method: Optional[str] = None  # personal, mail, substituted, publication
    served: bool = False
    served_date: Optional[str] = None
    served_by: Optional[str] = None
    proof_of_service_filed: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ServiceDeadline:
    """Computed service deadline for a defendant."""
    defendant_name: str
    case_number: str
    filing_date: str
    service_method: str
    service_deadline: str
    days_remaining: int
    expired: bool
    authority: str
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ServiceReport:
    """Complete service status report."""
    total_defendants: int = 0
    served: int = 0
    unserved: int = 0
    pos_filed: int = 0
    pos_missing: int = 0
    expired_service: int = 0
    defendants: list = field(default_factory=list)
    deadlines: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    ready_for_filing: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "total_defendants": self.total_defendants,
            "served": self.served,
            "unserved": self.unserved,
            "pos_filed": self.pos_filed,
            "pos_missing": self.pos_missing,
            "expired_service": self.expired_service,
            "issues": self.issues,
            "ready_for_filing": self.ready_for_filing,
            "generated_at": self.generated_at,
            "defendants": [d.to_dict() if hasattr(d, 'to_dict') else d for d in self.defendants],
        }


# ─── Michigan Service Rules ───

SERVICE_RULES = {
    "personal": {
        "description": "Personal service on individual",
        "authority": "MCR 2.105(A)(1)",
        "days_to_serve": 91,  # Must serve within 91 days of filing
        "response_days": 21,  # 21 days to answer after service
        "notes": "Deliver summons and complaint to defendant personally",
    },
    "mail": {
        "description": "Service by registered or certified mail",
        "authority": "MCR 2.105(A)(2)",
        "days_to_serve": 91,
        "response_days": 28,  # 21 days + 7 days for mail
        "notes": "Registered mail, return receipt requested, restricted delivery",
    },
    "substituted": {
        "description": "Substituted service at usual abode",
        "authority": "MCR 2.105(A)(3)",
        "days_to_serve": 91,
        "response_days": 21,
        "notes": "Deliver to person of suitable age at defendant's usual abode",
    },
    "publication": {
        "description": "Service by publication (last resort)",
        "authority": "MCR 2.106",
        "days_to_serve": 182,  # Extended for publication
        "response_days": 42,  # 42 days after last publication
        "notes": "Only when other methods failed; requires court order",
    },
    "agent": {
        "description": "Service on registered agent (businesses)",
        "authority": "MCR 2.105(D)",
        "days_to_serve": 91,
        "response_days": 21,
        "notes": "For corporations, LLCs — serve registered agent",
    },
}


class ServiceChecker:
    """
    Checks proof of service requirements for all defendants.
    Computes deadlines and generates PoS templates.
    """

    KNOWN_DEFENDANTS = {
        "Pigors v. Watson": [
            Defendant("Emily A. Watson", "2024-001507-DC"),
            Defendant("Emily A. Watson", "2023-005907-PP"),
        ],
        "Pigors v. Shady Oaks": [
            Defendant("Shady Oaks MHP LLC", "2025-002760-CZ"),
            Defendant("Shady Oaks Management", "2025-002760-CZ"),
            Defendant("Lifestyle Homes LLC", "2025-002760-CZ"),
            Defendant("Lifestyle Property Management", "2025-002760-CZ"),
            Defendant("Kevin Buckner", "2025-002760-CZ"),
            Defendant("Paul Zarkowski", "2025-002760-CZ"),
            Defendant("Michael Soto", "2025-002760-CZ"),
            Defendant("Margaret Williams", "2025-002760-CZ"),
            Defendant("Anthony Jackson", "2025-002760-CZ"),
            Defendant("Gabriel Schulte", "2025-002760-CZ"),
            Defendant("Kelli Thompson", "2025-002760-CZ"),
            Defendant("Manistee Investments LLC", "2025-002760-CZ"),
            Defendant("Frank Markel", "2025-002760-CZ"),
            Defendant("Kim Schuitema", "2025-002760-CZ"),
        ],
    }

    def __init__(self, defendants: Optional[list] = None):
        """
        Args:
            defendants: Optional list of Defendant objects. If None, uses known defendants.
        """
        if defendants is not None:
            self.defendants = defendants
        else:
            self.defendants = []
            for case_defs in self.KNOWN_DEFENDANTS.values():
                self.defendants.extend(case_defs)
        self._stats = {"checks_run": 0, "pos_generated": 0}

    def check_all(self) -> ServiceReport:
        """Check service status for all defendants."""
        report = ServiceReport()
        report.total_defendants = len(self.defendants)
        report.defendants = self.defendants

        for d in self.defendants:
            if d.served:
                report.served += 1
                if d.proof_of_service_filed:
                    report.pos_filed += 1
                else:
                    report.pos_missing += 1
                    report.issues.append(
                        f"MISSING PoS: {d.name} ({d.case_number}) — served but no PoS filed"
                    )
            else:
                report.unserved += 1
                report.issues.append(
                    f"UNSERVED: {d.name} ({d.case_number}) — needs service"
                )

        report.ready_for_filing = (
            report.unserved == 0
            and report.pos_missing == 0
            and report.total_defendants > 0
        )

        self._stats["checks_run"] += 1
        return report

    def compute_deadlines(
        self, filing_date: str, service_method: str = "personal"
    ) -> list[ServiceDeadline]:
        """
        Compute service deadlines for all unserved defendants.

        Args:
            filing_date: Date complaint was filed (YYYY-MM-DD)
            service_method: Default service method
        """
        today = date.today()
        try:
            filed = datetime.strptime(filing_date, "%Y-%m-%d").date()
        except ValueError:
            return []

        rule = SERVICE_RULES.get(service_method, SERVICE_RULES["personal"])
        deadline_date = filed + timedelta(days=rule["days_to_serve"])

        deadlines = []
        for d in self.defendants:
            if d.served:
                continue
            method = d.service_method or service_method
            r = SERVICE_RULES.get(method, SERVICE_RULES["personal"])
            dl = filed + timedelta(days=r["days_to_serve"])
            days_left = (dl - today).days

            deadlines.append(ServiceDeadline(
                defendant_name=d.name,
                case_number=d.case_number,
                filing_date=filing_date,
                service_method=method,
                service_deadline=dl.isoformat(),
                days_remaining=days_left,
                expired=days_left < 0,
                authority=r["authority"],
                notes=r["notes"],
            ))

        return deadlines

    def generate_pos_template(
        self, defendant: Defendant, service_date: str = "", server_name: str = "Andrew James Pigors"
    ) -> str:
        """
        Generate a Proof of Service template for a defendant.

        Args:
            defendant: The Defendant to generate PoS for
            service_date: Date of service (YYYY-MM-DD), defaults to today
            server_name: Name of person who served
        """
        if not service_date:
            service_date = date.today().isoformat()

        method = defendant.service_method or "personal"
        rule = SERVICE_RULES.get(method, SERVICE_RULES["personal"])

        template = f"""PROOF OF SERVICE

STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

Case No.: {defendant.case_number}

I, {server_name}, certify that on {service_date}, I served a copy of
the foregoing document(s) upon:

    {defendant.name}
    {defendant.address or '[ADDRESS REQUIRED]'}

Method of Service: {rule['description']}
Authority: {rule['authority']}

{self._method_specific_language(method)}

    ___________________________
    {server_name}
    Date: {service_date}
"""
        self._stats["pos_generated"] += 1
        return template

    def check_defendant(self, name: str) -> Optional[Defendant]:
        """Find a specific defendant by name."""
        name_lower = name.lower()
        for d in self.defendants:
            if name_lower in d.name.lower():
                return d
        return None

    def mark_served(
        self, name: str, served_date: str, served_by: str = "process server"
    ) -> bool:
        """Mark a defendant as served."""
        d = self.check_defendant(name)
        if d:
            d.served = True
            d.served_date = served_date
            d.served_by = served_by
            return True
        return False

    def get_stats(self) -> dict:
        """Return checker statistics."""
        return {
            **self._stats,
            "total_defendants": len(self.defendants),
            "served": sum(1 for d in self.defendants if d.served),
            "unserved": sum(1 for d in self.defendants if not d.served),
        }

    # ─── Private Methods ───

    @staticmethod
    def _method_specific_language(method: str) -> str:
        """Return method-specific certification language."""
        if method == "personal":
            return "I personally delivered the documents to the above-named individual."
        elif method == "mail":
            return (
                "I sent the documents by registered/certified mail, return receipt\n"
                "requested, restricted delivery, to the address listed above.\n"
                "Tracking Number: [TRACKING_NUMBER_REQUIRED]"
            )
        elif method == "substituted":
            return (
                "I delivered the documents to [NAME_OF_PERSON], a person of suitable\n"
                "age and discretion residing at the defendant's usual place of abode."
            )
        elif method == "publication":
            return (
                "Service was made by publication in [NEWSPAPER_NAME], a newspaper\n"
                "published in the county where the defendant was last known to reside.\n"
                "Publication dates: [DATES_REQUIRED]"
            )
        elif method == "agent":
            return "I delivered the documents to the registered agent for the entity."
        return "I served the documents as described above."


# ─── Module-level convenience ───

def check_service(defendants: list = None) -> ServiceReport:
    """Quick service check."""
    return ServiceChecker(defendants).check_all()


if __name__ == "__main__":
    checker = ServiceChecker()
    report = checker.check_all()
    print(f"Total defendants: {report.total_defendants}")
    print(f"Served: {report.served} | Unserved: {report.unserved}")
    print(f"PoS Filed: {report.pos_filed} | PoS Missing: {report.pos_missing}")
    print(f"Ready for filing: {report.ready_for_filing}")
    if report.issues:
        print(f"\nIssues ({len(report.issues)}):")
        for issue in report.issues[:10]:
            print(f"  - {issue}")
