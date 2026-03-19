#!/usr/bin/env python3
"""
Tool #112 — Mediation Preparation Kit
==========================================
🆕 NOVEL TOOL — If court orders mediation, be ready

Michigan courts frequently order mediation in custody cases.
Being prepared gives Andrew a massive advantage:
- Opening statement template
- Negotiation positions (BATNA analysis)
- Non-negotiable items vs. tradeable items
- Proposed parenting plans for negotiation
- Red flags to watch for in mediation
"""
import sys, json
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

POSITIONS = {
    'non_negotiable': [
        'Regular, meaningful parenting time with L.D.W.',
        'Joint legal custody preserved',
        'Phone/video contact on non-parenting days',
        'Access to all medical, educational, and welfare information about L.D.W.',
        'Right to participate in major decisions (education, healthcare, religion)',
        'Removal of false/misleading PPO allegations from record',
    ],
    'tradeable': [
        'Specific schedule days (flexible on which days, not whether days exist)',
        'Gradual vs. immediate transition back to full parenting time',
        'Neutral exchange location preferences',
        'Holiday schedule specifics (can alternate years)',
        'Summer vacation week distribution',
        'Right of first refusal threshold (flexible on hours)',
    ],
    'would_accept': [
        'Supervised parenting time as initial step (with defined graduation plan)',
        'Parenting coordinator/facilitator for transition period',
        'Parenting class completion (if both parties required equally)',
        'Family counseling or co-parenting counseling',
        'Structured communication method (e.g., OurFamilyWizard app)',
    ],
    'would_reject': [
        'Continued zero parenting time',
        'Indefinite supervised visitation with no graduation criteria',
        'Any agreement premised on admitted wrongdoing by Andrew',
        'Restrictions based on unsubstantiated allegations',
        'Berry having decision-making authority over L.D.W.',
    ],
}

def main():
    print("=" * 70)
    print("MEDIATION PREPARATION KIT — Tool #112")
    print("=" * 70)
    
    lines = [
        "# 🤝 MEDIATION PREPARATION KIT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #112*",
        "*WORK PRODUCT — Privileged Strategy Document*\n",
        "---\n",
        
        "## 📋 OPENING STATEMENT TEMPLATE\n",
        "> *\"Thank you. My name is Andrew Pigors, and I'm L.D.W.'s father.",
        "> I'm here because I want to be an active, involved parent.",
        "> For [X] months, I've been completely separated from my child.",
        "> I believe this separation is harmful to L.D.W., and I'm willing",
        "> to work with Emily to find a parenting arrangement that serves",
        "> our child's best interests. I'm not here to assign blame —",
        "> I'm here to find a path forward that gives L.D.W. both parents.\"*\n",
        "**Key principles:**",
        "- Focus on the CHILD, not the conflict",
        "- Show willingness to cooperate",
        "- Avoid blaming language",
        "- Be specific about what you want\n",
        
        "---\n",
        "## 🎯 BATNA ANALYSIS (Best Alternative to Negotiated Agreement)\n",
        "**If mediation fails, Andrew's alternatives are:**",
        "1. File F3 (disqualification) → new judge → refile custody motion",
        "2. File F4 (federal §1983) → damages pressure",
        "3. File F6 (JTC) + F10 (AGC) → institutional pressure",
        "4. Proceed to trial on custody modification\n",
        "**Andrew's BATNA is STRONG** — he has multiple legal avenues.",
        "This means he can negotiate from strength, not desperation.\n",
        
        "---\n",
        "## 🚫 NON-NEGOTIABLE ITEMS\n",
    ]
    
    for item in POSITIONS['non_negotiable']:
        lines.append(f"- ❌ **{item}**")
    
    lines.append("\n## 🔄 TRADEABLE ITEMS\n")
    for item in POSITIONS['tradeable']:
        lines.append(f"- 🔄 {item}")
    
    lines.append("\n## ✅ WOULD ACCEPT (Compromise Positions)\n")
    for item in POSITIONS['would_accept']:
        lines.append(f"- ✅ {item}")
    
    lines.append("\n## 🛑 WOULD REJECT\n")
    for item in POSITIONS['would_reject']:
        lines.append(f"- 🛑 {item}")
    
    lines.extend([
        "\n---",
        "## 📅 PROPOSED PARENTING PLANS\n",
        
        "### Option A: Standard Schedule (Goal)",
        "- Every other weekend (Friday 6pm to Sunday 6pm)",
        "- One midweek evening (Wednesday 4pm to 8pm)",
        "- Alternating holidays",
        "- 2 weeks summer vacation",
        "- Phone/video daily at 7pm\n",
        
        "### Option B: Graduated Schedule (Compromise)",
        "**Phase 1 (Weeks 1-4):** Supervised, 2x/week, 2 hours",
        "**Phase 2 (Weeks 5-8):** Unsupervised, 2x/week, 4 hours",
        "**Phase 3 (Weeks 9-12):** Unsupervised + one overnight per week",
        "**Phase 4 (Week 13+):** Standard schedule (Option A)\n",
        
        "### Option C: Minimum Acceptable",
        "- Supervised parenting time 3x/week, 3 hours each",
        "- Professional supervisor (not Emily's choice of person)",
        "- Written graduation criteria tied to specific, measurable benchmarks",
        "- Review hearing in 90 days\n",
        
        "---",
        "## ⚠️ RED FLAGS IN MEDIATION\n",
        "Watch for these tactics:",
        "1. **Stalling** — Emily/counsel may use mediation to delay, not resolve",
        "2. **New allegations** — Watch for surprise claims raised for the first time",
        "3. **Vague agreements** — Insist on SPECIFIC dates, times, and consequences",
        "4. **Unequal terms** — Reject any agreement that treats parents unequally without evidence",
        "5. **Pressure to admit** — Never admit wrongdoing as a condition of agreement\n",
        
        "## 📝 MEDIATION CHECKLIST\n",
        "- [ ] Bring 3 copies of proposed parenting plan",
        "- [ ] Bring evidence binder (organized exhibits)",
        "- [ ] Bring calendar for scheduling",
        "- [ ] Dress professionally (business casual minimum)",
        "- [ ] Arrive 15 minutes early",
        "- [ ] Bring notepad and pen (take notes of everything)",
        "- [ ] Do NOT bring Ronald Berry or other non-parties",
        "- [ ] Do NOT agree to anything on the spot — ask for time to review",
        "",
        f"*Mediation Prep Kit — Tool #112 — {sum(len(v) for v in POSITIONS.values())} negotiation positions mapped*",
    ])
    
    md_path = REPORTS_DIR / "MEDIATION_PREP.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "mediation_prep.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Mediation Preparation Kit (#112)',
        'positions': {k: len(v) for k, v in POSITIONS.items()},
        'total_positions': sum(len(v) for v in POSITIONS.values()),
        'parenting_plan_options': 3,
    }, indent=2), encoding='utf-8')
    
    total_pos = sum(len(v) for v in POSITIONS.values())
    print(f"\n✅ Mediation kit with {total_pos} negotiation positions")
    print(f"   3 parenting plan options (standard, graduated, minimum)")
    print(f"   Reports: MEDIATION_PREP.md + mediation_prep.json")

if __name__ == '__main__':
    main()
