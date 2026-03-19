#!/usr/bin/env python3
"""Tool #194 — Reunification Protocol.
Step-by-step reunification plan for Andrew and L.D.W. after
parenting time is restored. Graduated schedule based on
attachment theory and Michigan guidelines."""

import json, os, sys
from datetime import datetime
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_reunification_protocol():
    protocol = {
        "tool_id": 194,
        "title": "REUNIFICATION PROTOCOL — ANDREW & L.D.W.",
        "subtitle": "Graduated Reintroduction Based on Attachment Theory + Michigan Guidelines",
        "phases": []
    }

    protocol["phases"].append({
        "phase": 1,
        "name": "REINTRODUCTION (Week 1-2)",
        "goal": "Reestablish father-child bond in safe, structured setting",
        "schedule": [
            {"day": "Day 1-3", "activity": "2-hour supervised visits at neutral location (library, park)", "frequency": "Every other day"},
            {"day": "Day 4-7", "activity": "3-hour visits, child-led play, no pressure", "frequency": "Every other day"},
            {"day": "Week 2", "activity": "4-hour visits including meal together", "frequency": "3x per week"},
        ],
        "guidelines": [
            "Let L.D.W. set the pace — no forcing physical contact",
            "Bring familiar toys/items from before separation",
            "Keep routine predictable — same time, same location",
            "No negative talk about Emily — EVER (MCL 722.23(j))",
            "Document each visit: duration, child's mood, activities",
        ]
    })

    protocol["phases"].append({
        "phase": 2,
        "name": "BUILDING COMFORT (Week 3-4)",
        "goal": "Transition to unsupervised visits at Andrew's home",
        "schedule": [
            {"day": "Week 3", "activity": "Full-day visits (8 hours) at Andrew's home", "frequency": "2x per week"},
            {"day": "Week 3", "activity": "Include one meal preparation together", "frequency": "Each visit"},
            {"day": "Week 4", "activity": "First overnight stay (Friday to Saturday)", "frequency": "1x this week"},
            {"day": "Week 4", "activity": "Continue daytime visits", "frequency": "2x additional"},
        ],
        "guidelines": [
            "Set up L.D.W.'s room with familiar items",
            "Establish bedtime routine immediately",
            "FaceTime/video calls on non-visit days",
            "Share photos of visits with court/evaluator if required",
        ]
    })

    protocol["phases"].append({
        "phase": 3,
        "name": "STANDARD PARENTING TIME (Week 5-8)",
        "goal": "Achieve Michigan standard parenting time schedule",
        "schedule": [
            {"day": "Every other weekend", "activity": "Friday 6pm to Sunday 6pm", "frequency": "Bi-weekly"},
            {"day": "Wednesday", "activity": "After school/daycare to 8pm", "frequency": "Weekly"},
            {"day": "Holidays", "activity": "Per Michigan FOC holiday schedule", "frequency": "As applicable"},
        ],
        "guidelines": [
            "This is the MINIMUM standard per Michigan FOC guidelines",
            "Exchange locations should be neutral (police station, school)",
            "Maintain communication log for all exchanges",
            "Begin make-up time calculation — MCL 722.27a(8)",
        ]
    })

    protocol["phases"].append({
        "phase": 4,
        "name": "EXPANDED TIME + MAKE-UP (Month 3-6)",
        "goal": "Recover lost parenting time + establish 50/50 schedule",
        "schedule": [
            {"day": "Alternating weeks", "activity": "Move toward week-on/week-off", "frequency": "Bi-weekly"},
            {"day": "Make-up time", "activity": "Additional overnights per MCL 722.27a(8)", "frequency": "As ordered"},
            {"day": "Extended holidays", "activity": "1-2 week blocks during school breaks", "frequency": "Per schedule"},
        ],
        "guidelines": [
            "Make-up time is MANDATORY — court SHALL grant it",
            "Document all denied or shortened visits for make-up calculation",
            "Request modification to joint physical custody if going well",
            "File motion for equal parenting time if Emily resists",
        ]
    })

    protocol["phases"].append({
        "phase": 5,
        "name": "LONG-TERM STABILITY (Month 6+)",
        "goal": "Established co-parenting relationship with equal time",
        "schedule": [
            {"day": "Equal time", "activity": "50/50 or per agreed schedule", "frequency": "Ongoing"},
            {"day": "Communication", "activity": "Use OurFamilyWizard or similar co-parenting app", "frequency": "Daily as needed"},
        ],
        "guidelines": [
            "Maintain detailed records of all exchanges and communications",
            "If alienation continues, file for primary custody",
            "Continue therapy for L.D.W. if recommended",
            "Annual review of parenting plan per court order",
        ]
    })

    protocol["professional_support"] = [
        {"role": "Family therapist", "purpose": "Facilitate reunification, assess attachment recovery"},
        {"role": "Guardian ad litem (GAL)", "purpose": "Independent assessment of L.D.W.'s best interests — MCL 722.24"},
        {"role": "Parenting coordinator", "purpose": "Resolve day-to-day co-parenting disputes without court"},
        {"role": "Child psychologist", "purpose": "Assess developmental impact of separation and recovery trajectory"},
    ]

    protocol["total_phases"] = len(protocol["phases"])
    protocol["total_steps"] = sum(len(p["schedule"]) + len(p["guidelines"]) for p in protocol["phases"])

    return protocol

def main():
    p = build_reunification_protocol()
    md_path = os.path.join(REPORT_DIR, 'REUNIFICATION_PROTOCOL.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {p['title']}\n\n*{p['subtitle']}*\n\n")
        f.write(f"**{p['total_phases']} phases | {p['total_steps']} steps | Graduated over 6+ months**\n\n")
        for phase in p["phases"]:
            f.write(f"## Phase {phase['phase']}: {phase['name']}\n")
            f.write(f"**Goal:** {phase['goal']}\n\n")
            f.write("### Schedule\n")
            for s in phase["schedule"]:
                f.write(f"- **{s['day']}:** {s['activity']} ({s['frequency']})\n")
            f.write("\n### Guidelines\n")
            for g in phase["guidelines"]:
                f.write(f"- {g}\n")
            f.write("\n")
        f.write("## Professional Support Team\n\n")
        for ps in p["professional_support"]:
            f.write(f"- **{ps['role']}:** {ps['purpose']}\n")
        f.write(f"\n---\n*Tool #194 | {p['total_phases']} phases, {p['total_steps']} steps*\n")
    json_path = os.path.join(REPORT_DIR, 'reunification_protocol.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(p, f, indent=2)
    print(f"Tool #194 — REUNIFICATION PROTOCOL")
    print(f"  {p['total_phases']} phases | {p['total_steps']} steps | 6+ month graduated plan")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
