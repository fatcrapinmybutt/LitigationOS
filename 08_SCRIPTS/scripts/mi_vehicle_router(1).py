from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class VehicleDecision:
    forum: str
    lane: str
    candidate_vehicle: str
    rationale: str

def choose_vehicle(lane: str, purpose: str, case_id: Optional[str] = None) -> VehicleDecision:
    lane = (lane or "UNKNOWN").upper()
    purpose = (purpose or "").lower()

    if lane == "MEEK4":
        if any(x in purpose for x in ["bias", "canon", "jtc"]):
            return VehicleDecision("JTC", lane, "Judicial Conduct Complaint / JTC packet", "MEEK4 oversight lane")
        if any(x in purpose for x in ["appeal", "coa", "msc"]):
            return VehicleDecision("COA", lane, "Appellate oversight support packet", "MEEK4 appellate crossover")

    if lane in {"MEEK2", "MEEK3"}:
        if any(x in purpose for x in ["coa", "appeal"]):
            return VehicleDecision("COA", lane, "COA application/original action support packet", "Appellate lane requested")
        if "msc" in purpose:
            return VehicleDecision("MSC", lane, "MSC application/support packet", "Supreme Court lane requested")
        return VehicleDecision("TRIAL", lane, "Trial-court record-preservation packet", "Default preserve-and-build route")

    if lane == "MEEK1":
        if any(x in purpose for x in ["coa", "appeal"]):
            return VehicleDecision("COA", lane, "Civil appeal support packet", "Housing lane appellate support")
        return VehicleDecision("TRIAL", lane, "Civil claim/post-judgment packet", "Housing lane default")

    return VehicleDecision("TRIAL", lane, "General litigation packet", "Unknown lane fallback")
