#!/usr/bin/env python3
"""Fleet Dispatch — Routes litigation tasks to the correct agent skill."""

FLEET_MANIFEST = {
    # Tier I: Operational Warfare
    "litigation-filing-architect":         {"tier": 1, "triggers": ["filing", "vehiclemap", "court document", "motion", "brief"]},
    "litigation-red-team":                 {"tier": 1, "triggers": ["stress test", "adversarial", "weakness", "red team", "attack vector"]},
    "litigation-judicial-analyst":         {"tier": 1, "triggers": ["judge", "bias", "misconduct", "canon", "recusal", "disqualification"]},
    "litigation-impeachment-engine":       {"tier": 1, "triggers": ["impeachment", "contradiction", "transcript", "prior inconsistent"]},
    "litigation-evidence-harvester":       {"tier": 1, "triggers": ["scan", "classify", "extract", "ocr", "evidence", "harvest"]},
    "litigation-authority-validator":      {"tier": 1, "triggers": ["citation", "mcr", "mcl", "verify", "authority", "shepardize"]},
    "litigation-convergence-orchestrator": {"tier": 1, "triggers": ["converge", "quality", "emergence", "dnew", "blocker"]},
    "litigation-pipeline-commander":       {"tier": 1, "triggers": ["omega", "pipeline", "phase", "checkpoint", "inventory"]},
    "litigation-appellate-strategist":     {"tier": 1, "triggers": ["appeal", "coa", "appellate brief", "record", "standard of review"]},
    "litigation-skill-auditor":            {"tier": 1, "triggers": ["audit", "compliance", "fleet health", "skill check"]},
    # Tier II: Supreme Domination
    "litigation-supreme-court-architect":  {"tier": 2, "triggers": ["msc", "supreme court", "mcr 7.3", "bypass", "leave to appeal"]},
    "litigation-federal-civil-rights":     {"tier": 2, "triggers": ["1983", "civil rights", "immunity", "rooker-feldman", "section 1985"]},
    "litigation-discovery-warfare":        {"tier": 2, "triggers": ["interrogatory", "rfp", "rfa", "subpoena", "compel", "discovery"]},
    "litigation-sanctions-engine":         {"tier": 2, "triggers": ["sanctions", "fees", "contempt", "mcr 2.114", "rule 11"]},
    "litigation-custody-specialist":       {"tier": 2, "triggers": ["custody", "parenting time", "best interest", "foc", "mcl 722"]},
    "litigation-ppo-specialist":           {"tier": 2, "triggers": ["ppo", "protection order", "bond", "mcl 600.2950"]},
    "litigation-harm-quantifier":          {"tier": 2, "triggers": ["damages", "harm", "emotional distress", "per diem", "economic"]},
    "litigation-brief-writer":             {"tier": 2, "triggers": ["brief", "argument", "persuasion", "writing", "irac"]},
    "litigation-record-builder":           {"tier": 2, "triggers": ["record", "transcript", "exhibit compilation", "mcr 7.210"]},
    "litigation-pro-se-guardian":          {"tier": 2, "triggers": ["pro se", "self-represented", "fee waiver", "mc 20"]},
    # Tier III: The Lawsuit Forge
    "litigation-lawsuit-forge":            {"tier": 3, "triggers": ["new lawsuit", "complaint", "new claim", "sue", "initiate action"]},
    "litigation-cause-of-action-library":  {"tier": 3, "triggers": ["cause of action", "elements", "tort", "statutory claim"]},
    "litigation-complaint-drafter":        {"tier": 3, "triggers": ["verified complaint", "count", "prayer", "amended complaint"]},
    "litigation-claim-researcher":         {"tier": 3, "triggers": ["research", "viable claims", "fact mapping", "theory"]},
    "litigation-service-engine":           {"tier": 3, "triggers": ["service", "serve", "proof of service", "mc 12", "process server"]},
}


def dispatch(task_description: str, lane: str = None) -> list[str]:
    """Route a task to the best fleet agents."""
    task_lower = task_description.lower()
    scores = {}
    for skill, meta in FLEET_MANIFEST.items():
        score = sum(1 for t in meta["triggers"] if t in task_lower)
        if score > 0:
            scores[skill] = score
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return [skill for skill, _ in ranked[:3]]


def fleet_status() -> dict:
    """Return fleet manifest with tier counts."""
    tiers = {1: [], 2: [], 3: []}
    for skill, meta in FLEET_MANIFEST.items():
        tiers[meta["tier"]].append(skill)
    return {
        "total_skills": len(FLEET_MANIFEST),
        "tier_1_operational": len(tiers[1]),
        "tier_2_supreme": len(tiers[2]),
        "tier_3_forge": len(tiers[3]),
        "manifest": FLEET_MANIFEST,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        agents = dispatch(task)
        print(f"Task: {task}")
        print(f"Dispatch to: {', '.join(agents) if agents else 'No match — use core litigation-os'}")
    else:
        status = fleet_status()
        print(f"Fleet: {status['total_skills']} skills")
        print(f"  Tier I (Operational): {status['tier_1_operational']}")
        print(f"  Tier II (Supreme): {status['tier_2_supreme']}")
        print(f"  Tier III (Forge): {status['tier_3_forge']}")
