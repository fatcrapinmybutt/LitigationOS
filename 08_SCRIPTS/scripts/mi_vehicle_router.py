from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class VehicleDecision:
    forum: str
    lane: str
    candidate_vehicle: str
    rationale: str
    authority_compass: List[str]
    service_compass: List[str]

def choose_vehicle(lane: str, purpose: str, case_id: Optional[str] = None) -> VehicleDecision:
    lane = (lane or "UNKNOWN").upper()
    purpose_l = (purpose or "").lower()

    common_auth = ["MCR", "MCL", "MRE", "MJI Benchbooks", "SCAO/FOC/MC forms", "Verified local orders"]
    service = ["Proof of service", "ROA/docket entry date", "Signed vs entered vs served date triad"]

    if lane == "MEEK4":
        if any(x in purpose_l for x in ["jtc", "canon", "bias"]):
            return VehicleDecision("JTC", lane, "JTC judicial conduct complaint packet", "Oversight lane for judicial conduct", common_auth + ["Michigan Code of Judicial Conduct", "MCR 9.200 et seq (verify current)"], service)
        if any(x in purpose_l for x in ["coa", "appeal", "superintending"]):
            return VehicleDecision("COA", lane, "COA supervisory/appellate support packet", "Oversight-appellate crossover", common_auth + ["MCR 7.205 / 7.206 / 7.216 (verify lane)"], service)

    if lane in {"MEEK2", "MEEK3"}:
        if "msc" in purpose_l:
            return VehicleDecision("MSC", lane, "MSC application/support packet", "Supreme Court rail requested", common_auth + ["MCR 7.305+ (verify exact vehicle)"], service)
        if any(x in purpose_l for x in ["coa", "appeal", "superintending"]):
            return VehicleDecision("COA", lane, "COA appeal/original action support packet", "Appellate rail requested", common_auth + ["MCR 7.203 / 7.205 / 7.206 (verify)"], service)
        return VehicleDecision("TRIAL", lane, "Record-preservation / modification / enforcement packet", "Trial lane default", common_auth + ["MCR 2.119", "MCR 3.x family/PPO rules (verify exact)"], service)

    if lane == "MEEK1":
        if any(x in purpose_l for x in ["coa", "appeal"]):
            return VehicleDecision("COA", lane, "Civil appeal support packet", "Housing lane appellate route", common_auth + ["MCR 7.104 / 7.204 / 7.205 (verify)"], service)
        return VehicleDecision("TRIAL", lane, "Civil claim/post-judgment packet", "Housing lane default route", common_auth + ["MCR 2.119", "MCR 2.612 (if relief from order)"], service)

    return VehicleDecision("TRIAL", lane, "General litigation packet", "Fallback route", common_auth, service)
