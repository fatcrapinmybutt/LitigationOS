#!/usr/bin/env python3
"""Tool #183 — Child Welfare & Developmental Psychology Brief.
Research-based arguments for custody hearings: attachment theory,
developmental milestones, impact of parental separation on toddlers."""

import json, os, sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_welfare_brief():
    brief = {
        "tool_id": 183,
        "title": "CHILD WELFARE & DEVELOPMENTAL PSYCHOLOGY BRIEF",
        "subtitle": "Research-Based Arguments for L.D.W.'s Best Interests",
        "categories": []
    }

    brief["categories"].append({
        "category": "Attachment Theory",
        "relevance": "L.D.W. age 2-3 is in CRITICAL attachment formation window",
        "points": [
            {"point": "Bowlby Attachment Theory: Secure attachment to BOTH parents is essential for healthy development", "source": "Bowlby (1969) Attachment and Loss"},
            {"point": "Ainsworth Strange Situation: Children who lose access to attachment figure show protest → despair → detachment", "source": "Ainsworth et al. (1978)"},
            {"point": "Ages 1-3 are the primary attachment window — disruption during this period causes lasting harm", "source": "APA Developmental Psychology Guidelines"},
            {"point": "Overnight stays with non-custodial parent strengthen secure attachment", "source": "Warshak (2014) Social Science and Parenting Plans"},
            {"point": "Complete severance of parent-child contact is the MOST harmful outcome — worse than conflict exposure", "source": "Kelly & Lamb (2000) Child Development"},
        ]
    })

    brief["categories"].append({
        "category": "Developmental Milestones (Age 2-3)",
        "relevance": "L.D.W. born Nov 9, 2022 — currently in critical development period",
        "points": [
            {"point": "Language explosion (ages 2-3): Children learn 200+ new words — needs BOTH parents' verbal input", "source": "Hart & Risley (1995) Meaningful Differences"},
            {"point": "Social-emotional development: Learns trust, empathy, self-regulation through parent interactions", "source": "Erikson's Stages — Trust vs. Mistrust"},
            {"point": "Gender identity formation begins: Father-child relationship is critical for healthy identity development", "source": "Lamb (2010) The Role of the Father"},
            {"point": "Cognitive development: Object permanence → understanding that absent parent still exists and loves them", "source": "Piaget's Preoperational Stage"},
            {"point": "Play-based learning: Different parent styles (rough-and-tumble with fathers) serve distinct developmental functions", "source": "Paquette (2004) Father-Child Activation"},
        ]
    })

    brief["categories"].append({
        "category": "Impact of Parental Alienation on Toddlers",
        "relevance": "Emily's pattern of excluding Andrew from L.D.W.'s life",
        "points": [
            {"point": "Children who lose contact with a parent show increased anxiety, depression, and behavioral problems", "source": "Bernet (2010) Parental Alienation — Science and Law"},
            {"point": "Toddlers cannot articulate their distress — manifests as sleep disruption, regression, aggression", "source": "APA Task Force on Children & Divorce"},
            {"point": "Long-term effects: Children alienated from a parent have higher rates of substance abuse and relationship failure", "source": "Baker (2007) Adult Children of Parental Alienation"},
            {"point": "The alienating parent's behavior — not the rejected parent's — is the primary risk factor", "source": "Fidler & Bala (2010) Children Resisting Contact"},
            {"point": "Courts increasingly recognize alienation as a form of child abuse", "source": "Harman et al. (2018) International Consensus"},
        ]
    })

    brief["categories"].append({
        "category": "Father-Child Relationship Research",
        "relevance": "Andrew's role as engaged father documented by 26 strengths (tool #157)",
        "points": [
            {"point": "Father involvement predicts better academic performance, social competence, and psychological well-being", "source": "Amato & Rivera (1999) Paternal Involvement"},
            {"point": "Children with involved fathers have 33% fewer behavioral problems", "source": "Carlson (2006) Family Structure"},
            {"point": "Father absence is linked to 5x higher poverty rate, 2x higher dropout rate", "source": "US Census Bureau (2022)"},
            {"point": "Michigan law creates PRESUMPTION of parenting time — MCL 722.27a(1)", "source": "Michigan Child Custody Act"},
            {"point": "Best Interest Factor (j): Willingness to facilitate close relationship — Emily's behavior is dispositive", "source": "MCL 722.23(j)"},
        ]
    })

    brief["categories"].append({
        "category": "Court-Ready Arguments",
        "relevance": "Specific arguments to present to new judge after McNeill removal",
        "points": [
            {"point": "ARGUMENT 1: Complete parenting time suspension violates L.D.W.'s fundamental right to both parents", "authority": "Troxel v Granville 530 US 57 (2000)"},
            {"point": "ARGUMENT 2: No evidence that Andrew poses any risk — suspension based solely on Emily's unverified allegations", "authority": "MCL 722.27a(7) — burden of proof on party seeking restriction"},
            {"point": "ARGUMENT 3: L.D.W. is in critical developmental window — every day of separation causes measurable harm", "authority": "Expert consensus on attachment theory"},
            {"point": "ARGUMENT 4: Emily's alienating behavior is itself grounds for custody modification", "authority": "MCL 722.23(j) + Bernet (2010)"},
            {"point": "ARGUMENT 5: Gradual reunification protocol should begin IMMEDIATELY — delay compounds harm", "authority": "Warshak (2015) Ten Parenting Plan Mistakes"},
            {"point": "ARGUMENT 6: GAL appointment will confirm Andrew's fitness and Emily's alienation", "authority": "MCL 722.24"},
        ]
    })

    brief["total_points"] = sum(len(c["points"]) for c in brief["categories"])
    brief["total_categories"] = len(brief["categories"])

    return brief

def main():
    brief = build_welfare_brief()
    
    md_path = os.path.join(REPORT_DIR, 'CHILD_WELFARE_BRIEF.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {brief['title']}\n\n")
        f.write(f"*{brief['subtitle']}*\n\n")
        f.write(f"**{brief['total_categories']} categories | {brief['total_points']} research-based points**\n\n")
        for cat in brief["categories"]:
            f.write(f"## {cat['category']}\n")
            f.write(f"*Relevance: {cat['relevance']}*\n\n")
            for p in cat["points"]:
                source = p.get("source") or p.get("authority", "")
                f.write(f"- {p['point']}\n  *— {source}*\n\n")
        f.write(f"---\n*Tool #183 | {brief['total_points']} points across {brief['total_categories']} categories*\n")
    
    json_path = os.path.join(REPORT_DIR, 'child_welfare_brief.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, indent=2)
    
    print(f"Tool #183 — CHILD WELFARE & DEVELOPMENTAL PSYCHOLOGY BRIEF")
    print(f"  {brief['total_categories']} categories | {brief['total_points']} research points")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
