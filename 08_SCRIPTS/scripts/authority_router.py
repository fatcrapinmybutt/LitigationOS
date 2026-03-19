from __future__ import annotations
from typing import List, Dict

def authority_triples_for_lane(lane: str, forum: str) -> List[Dict[str, str]]:
    lane = (lane or "UNKNOWN").upper()
    forum = (forum or "TRIAL").upper()
    triples: List[Dict[str, str]] = []

    # Generic Michigan authority compass (placeholder pinpoints are acquisition targets)
    triples.extend([
        {"issue": "vehicle_and_form", "authority": "MCR (vehicle rule)", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"},
        {"issue": "evidence_admissibility", "authority": "MRE", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"},
        {"issue": "service_notice", "authority": "MCR service/proof", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"},
    ])

    if lane == "MEEK4":
        triples.append({"issue": "judicial_conduct", "authority": "Michigan Code of Judicial Conduct / JTC procedure", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"})
    if forum == "COA":
        triples.append({"issue": "appellate_jurisdiction", "authority": "MCR 7.203/7.205/7.206 (verify exact)", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"})
    if forum == "MSC":
        triples.append({"issue": "supreme_court_application", "authority": "MCR 7.305+ (verify exact)", "pinpoint": "VERIFY_PINPOINT", "status": "ACQUIRE"})
    return triples
