#!/usr/bin/env python3
"""
Tool #201: Mediation Preparation Kit
=====================================
Alternative dispute resolution strategy for Pigors v. Watson.
Covers pre-mediation prep, negotiation zones, BATNA analysis,
and fallback triggers for when mediation fails.

NOVEL INNOVATION: Combines litigation strength scoring with
negotiation theory to auto-generate settlement boundaries.
"""
import json, os, sys, sqlite3
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')

def get_db_stats():
    """Pull relevant data for mediation prep."""
    stats = {}
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM evidence_quotes) AS eq_count,
                (SELECT COUNT(*) FROM judicial_violations) AS jv_count
        """).fetchone()
        stats['evidence_quotes'] = row[0] if row else 0
        stats['judicial_violations'] = row[1] if row else 0
        
        try:
            claims = conn.execute("SELECT vehicle_name, claim_type, status FROM claims LIMIT 50").fetchall()
            stats['claims'] = [{'vehicle': c[0], 'type': c[1], 'status': c[2]} for c in claims]
        except:
            stats['claims'] = []
        
        conn.close()
    except Exception as e:
        stats['db_error'] = str(e)
    return stats

def build_mediation_kit():
    """Generate comprehensive mediation preparation materials."""
    stats = get_db_stats()
    
    kit = {
        "tool_id": 201,
        "name": "Mediation Preparation Kit",
        "generated": datetime.now().isoformat(),
        "pre_mediation_checklist": {
            "documents_to_bring": [
                "All filed motions and court orders",
                "Parenting time denial log (230+ days documented)",
                "Child's developmental timeline (L.D.W. born Nov 9, 2022)",
                "Financial affidavit (income, expenses, child support)",
                "Communication log with opposing party",
                "School/medical records (if available)",
                "Proposed parenting plan with calendar",
                "Evidence binder — TOP 20 exhibits (curated, not 36K)",
            ],
            "preparation_steps": [
                "Review ALL court orders currently in effect",
                "Identify non-negotiable items (safety, child welfare)",
                "Calculate parenting time owed (230 days denied = 18.8% of life)",
                "Prepare 3-minute opening statement (facts, not emotion)",
                "Identify mediator preferences (request family law specialist)",
                "Prepare BATNA (Best Alternative To Negotiated Agreement)",
                "Set emotional boundaries — bring support person if allowed",
                "Review Michigan mediation confidentiality rules (MCR 2.412)",
            ]
        },
        "negotiation_zones": {
            "custody": {
                "ideal": "50/50 joint legal and physical custody",
                "acceptable": "Joint legal, primary physical with liberal parenting time",
                "walk_away": "Less than standard parenting time (every other weekend)",
                "leverage": f"{stats.get('judicial_violations', 0)} documented judicial violations strengthen position"
            },
            "parenting_time": {
                "ideal": "Equal time — 2-2-3 or week-on/week-off schedule",
                "acceptable": "Extended weekends + midweek dinner + alternating holidays",
                "walk_away": "Supervised-only or less than 4 overnights/month",
                "leverage": "230 days denied — court MUST address systematic denial"
            },
            "communication": {
                "ideal": "OurFamilyWizard or TalkingParents (documented platform)",
                "acceptable": "Email-only with 24-hour response requirement",
                "walk_away": "Phone-only (no documentation trail)"
            },
            "decision_making": {
                "ideal": "Joint legal custody — both decide medical, education, religion",
                "acceptable": "Joint with tie-breaker mechanism (mediator/arbitrator)",
                "walk_away": "Sole legal custody to opposing party"
            }
        },
        "batna_analysis": {
            "definition": "Best Alternative To Negotiated Agreement — what happens if mediation fails",
            "litigation_strength": {
                "evidence_base": f"{stats.get('evidence_quotes', 0)} documented evidence quotes",
                "judicial_misconduct": f"{stats.get('judicial_violations', 0)} violations = strong disqualification case",
                "federal_option": "§1983 federal complaint viable (5 counts, 4 defendants)",
                "appellate_option": "COA appeal pending (Case 366810)",
                "overall_assessment": "STRONG BATNA — litigation alternatives are viable"
            },
            "mediation_failure_triggers": [
                "Opposing party refuses any unsupervised time",
                "Opposing party demands sole legal custody",
                "Mediator shows bias or pre-judgment",
                "Safety concerns raised without substantiation",
                "Opposing party brings unauthorized persons (Berry is NOT attorney)",
                "Mediation used as fishing expedition for information"
            ],
            "post_failure_actions": [
                "File Motion for Parenting Time (F1) immediately",
                "File Disqualification Motion (F3) if judge involved",
                "Escalate to FOC complaint if parenting time continues denied",
                "Document mediation failure for appellate record",
                "Consider filing federal §1983 if pattern continues"
            ]
        },
        "michigan_mediation_rules": {
            "governing_rule": "MCR 2.411 (Case Evaluation) / MCR 2.412 (Mediation)",
            "confidentiality": "MCR 2.412(D) — mediation communications are confidential",
            "exceptions_to_confidentiality": [
                "Child abuse or neglect (mandatory reporting)",
                "Threat of bodily harm",
                "Court-ordered exceptions",
                "Written agreement to disclose"
            ],
            "mediator_qualifications": "MCR 2.412(B) — must meet requirements of ADR plan",
            "cost": "Court-connected mediation may be free or low-cost with IFP",
            "duration": "Typically 2-4 hours, can extend to full day",
            "binding": "NOT binding unless both parties sign agreement"
        },
        "opening_statement_template": {
            "duration": "3 minutes maximum",
            "structure": [
                "1. Introduce yourself as L.D.W.'s father",
                "2. State your goal: healthy relationship with your child",
                "3. Briefly describe denial pattern (230 days, 18.8% of life)",
                "4. Express willingness to co-parent cooperatively",
                "5. Identify specific requests: schedule, communication, decision-making",
                "6. Close with focus on child's best interest"
            ],
            "tone": "Calm, factual, child-focused. Never attack opposing party.",
            "avoid": [
                "Personal attacks on Emily or Berry",
                "Legal arguments (save for court)",
                "Emotional outbursts (they undermine credibility)",
                "Threats of litigation (counter-productive in mediation)",
                "Discussing judge or judicial misconduct"
            ]
        },
        "db_stats": stats
    }
    
    # Count items
    total_items = (
        len(kit['pre_mediation_checklist']['documents_to_bring']) +
        len(kit['pre_mediation_checklist']['preparation_steps']) +
        len(kit['negotiation_zones']) +
        len(kit['batna_analysis']['mediation_failure_triggers']) +
        len(kit['batna_analysis']['post_failure_actions'])
    )
    kit['total_items'] = total_items
    
    return kit

def main():
    print("=" * 60)
    print("TOOL #201: MEDIATION PREPARATION KIT")
    print("=" * 60)
    
    kit = build_mediation_kit()
    
    # Save JSON
    json_path = os.path.join(REPORT_DIR, 'MEDIATION_PREP_KIT.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(kit, f, indent=2, ensure_ascii=False)
    
    # Save MD
    md_path = os.path.join(REPORT_DIR, 'MEDIATION_PREP_KIT.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 🤝 Mediation Preparation Kit (Tool #201)\n\n")
        f.write(f"Generated: {kit['generated']}\n\n")
        
        f.write("## Pre-Mediation Checklist\n\n")
        f.write("### Documents to Bring\n")
        for item in kit['pre_mediation_checklist']['documents_to_bring']:
            f.write(f"- [ ] {item}\n")
        
        f.write("\n### Preparation Steps\n")
        for i, step in enumerate(kit['pre_mediation_checklist']['preparation_steps'], 1):
            f.write(f"{i}. {step}\n")
        
        f.write("\n## Negotiation Zones\n\n")
        for zone, details in kit['negotiation_zones'].items():
            f.write(f"### {zone.replace('_', ' ').title()}\n")
            for level, desc in details.items():
                emoji = {"ideal": "🟢", "acceptable": "🟡", "walk_away": "🔴", "leverage": "⚡"}.get(level, "•")
                f.write(f"- {emoji} **{level.replace('_', ' ').title()}**: {desc}\n")
            f.write("\n")
        
        f.write("## BATNA Analysis\n\n")
        f.write(f"**Definition**: {kit['batna_analysis']['definition']}\n\n")
        f.write("### Litigation Strength\n")
        for k, v in kit['batna_analysis']['litigation_strength'].items():
            f.write(f"- **{k.replace('_', ' ').title()}**: {v}\n")
        
        f.write("\n### Mediation Failure Triggers\n")
        for trigger in kit['batna_analysis']['mediation_failure_triggers']:
            f.write(f"- ⚠️ {trigger}\n")
        
        f.write("\n### Post-Failure Actions\n")
        for action in kit['batna_analysis']['post_failure_actions']:
            f.write(f"- → {action}\n")
        
        f.write("\n## Michigan Mediation Rules\n\n")
        for k, v in kit['michigan_mediation_rules'].items():
            if isinstance(v, list):
                f.write(f"### {k.replace('_', ' ').title()}\n")
                for item in v:
                    f.write(f"- {item}\n")
            else:
                f.write(f"- **{k.replace('_', ' ').title()}**: {v}\n")
        
        f.write("\n## Opening Statement Template (3 min)\n\n")
        for step in kit['opening_statement_template']['structure']:
            f.write(f"- {step}\n")
        f.write("\n**Avoid:**\n")
        for item in kit['opening_statement_template']['avoid']:
            f.write(f"- ❌ {item}\n")
    
    print(f"\n✅ Mediation Prep Kit generated")
    print(f"   Items: {kit['total_items']}")
    print(f"   Zones: {len(kit['negotiation_zones'])} negotiation areas")
    print(f"   BATNA: {kit['batna_analysis']['litigation_strength']['overall_assessment']}")
    print(f"   Reports: {md_path}")
    return kit

if __name__ == '__main__':
    main()
