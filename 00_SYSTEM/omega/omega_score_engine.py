"""
OMEGA Score Engine v2 — 10-Axis Judicial Action Scoring System
LitigationOS Core Module

Scores every potential legal action on 10 axes (max 100 total).
Tiers: CRITICAL (85-100) | FILE IMMEDIATELY (70-84) | HIGH (55-69) | STANDARD (40-54) | HOLD (<40)
"""
import sqlite3
import json
from datetime import datetime, date

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

AXES = [
    "evidence_strength",      # Volume + quality + admissibility
    "legal_authority",        # Statutory/case law/constitutional basis
    "strategic_impact",       # Advances overall case objectives
    "urgency",               # Deadlines, separation days, SOL
    "feasibility",           # Pro se executability, resources needed
    "adversary_vulnerability", # Exploits known weakness
    "compound_effect",       # Strengthens other actions
    "reversibility_risk",    # Survives appeal/opposition (inverted: high = survives)
    "precedent_value",       # Creates useful precedent
    "public_interest",       # Serves broader justice
]

TIERS = [
    (85, 100, "CRITICAL", "FILE NOW"),
    (70, 84, "HIGH", "FILE IMMEDIATELY"),
    (55, 69, "MEDIUM", "HIGH PRIORITY"),
    (40, 54, "STANDARD", "STANDARD"),
    (0, 39, "HOLD", "HOLD"),
]

# Forum definitions
FORUMS = {
    "MSC": {"lane": "A", "label": "Michigan Supreme Court"},
    "COA": {"lane": "B", "label": "Court of Appeals"},
    "14TH": {"lane": "C", "label": "14th Circuit Court"},
    "JTC": {"lane": "D", "label": "Judicial Tenure Commission"},
    "USDC": {"lane": "E", "label": "US District Court (§1983)"},
    "BAR": {"lane": "F", "label": "State Bar of Michigan"},
}


def get_tier(score):
    for low, high, tier, action in TIERS:
        if low <= score <= high:
            return {"tier": tier, "action": action, "min": low, "max": high}
    return {"tier": "HOLD", "action": "HOLD", "min": 0, "max": 39}


def separation_days():
    start = date(2025, 8, 8)
    return (date.today() - start).days


def score_action(action_id, name, forum, scores_dict, notes=""):
    """Score a legal action on all 10 axes.
    
    Args:
        action_id: Unique identifier (e.g., 'msc-emergency-app')
        name: Human-readable name
        forum: Forum code (MSC, COA, 14TH, JTC, USDC, BAR)
        scores_dict: Dict of axis_name -> score (0-10)
        notes: Optional notes
    
    Returns:
        Complete scoring result dict
    """
    total = 0
    axis_scores = {}
    for axis in AXES:
        val = min(10, max(0, scores_dict.get(axis, 0)))
        axis_scores[axis] = val
        total += val
    
    tier_info = get_tier(total)
    forum_info = FORUMS.get(forum, {"lane": "?", "label": forum})
    
    return {
        "action_id": action_id,
        "name": name,
        "forum": forum,
        "lane": forum_info["lane"],
        "forum_label": forum_info["label"],
        "total_score": total,
        "tier": tier_info["tier"],
        "tier_action": tier_info["action"],
        "axes": axis_scores,
        "separation_days": separation_days(),
        "notes": notes,
        "scored_at": datetime.now().isoformat(),
    }


def save_scores(scores, db_path=DB_PATH):
    """Save scored actions to the database."""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS omega_scores")
    conn.execute("""CREATE TABLE omega_scores (
        action_id TEXT PRIMARY KEY,
        name TEXT, forum TEXT, lane TEXT,
        total_score INTEGER, tier TEXT, tier_action TEXT,
        evidence_strength INTEGER, legal_authority INTEGER,
        strategic_impact INTEGER, urgency INTEGER,
        feasibility INTEGER, adversary_vulnerability INTEGER,
        compound_effect INTEGER, reversibility_risk INTEGER,
        precedent_value INTEGER, public_interest INTEGER,
        notes TEXT, scored_at TEXT,
        separation_days INTEGER
    )""")
    
    for s in scores:
        conn.execute("""INSERT OR REPLACE INTO omega_scores 
            (action_id, name, forum, lane, total_score, tier, tier_action,
             evidence_strength, legal_authority, strategic_impact, urgency,
             feasibility, adversary_vulnerability, compound_effect, reversibility_risk,
             precedent_value, public_interest, notes, scored_at, separation_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (s["action_id"], s["name"], s["forum"], s["lane"],
             s["total_score"], s["tier"], s["tier_action"],
             s["axes"]["evidence_strength"], s["axes"]["legal_authority"],
             s["axes"]["strategic_impact"], s["axes"]["urgency"],
             s["axes"]["feasibility"], s["axes"]["adversary_vulnerability"],
             s["axes"]["compound_effect"], s["axes"]["reversibility_risk"],
             s["axes"]["precedent_value"], s["axes"]["public_interest"],
             s["notes"], s["scored_at"], s["separation_days"]))
    
    conn.commit()
    conn.close()


def score_all_actions():
    """Score all identified legal actions across all forums."""
    actions = []
    
    # ========== MSC (Lane A) ==========
    actions.append(score_action("msc-emergency-app", "MSC Emergency Application",
        "MSC", {
            "evidence_strength": 9, "legal_authority": 8, "strategic_impact": 10,
            "urgency": 10, "feasibility": 7, "adversary_vulnerability": 8,
            "compound_effect": 9, "reversibility_risk": 7, "precedent_value": 8,
            "public_interest": 8
        }, "MCR 7.306(B)(1) — immediate relief from ongoing harm. 574+ days separation."))
    
    actions.append(score_action("msc-superintending", "MSC Superintending Control",
        "MSC", {
            "evidence_strength": 8, "legal_authority": 9, "strategic_impact": 9,
            "urgency": 8, "feasibility": 7, "adversary_vulnerability": 8,
            "compound_effect": 8, "reversibility_risk": 8, "precedent_value": 9,
            "public_interest": 7
        }, "Const 1963 Art 6 §4. 377 violations documented. Systemic failure."))
    
    actions.append(score_action("msc-mandamus", "MSC Writ of Mandamus",
        "MSC", {
            "evidence_strength": 8, "legal_authority": 8, "strategic_impact": 8,
            "urgency": 8, "feasibility": 6, "adversary_vulnerability": 7,
            "compound_effect": 7, "reversibility_risk": 7, "precedent_value": 8,
            "public_interest": 7
        }, "Compel judge to perform ministerial duties. Clear legal duty violated."))
    
    actions.append(score_action("msc-habeas", "MSC Habeas Corpus",
        "MSC", {
            "evidence_strength": 9, "legal_authority": 9, "strategic_impact": 9,
            "urgency": 10, "feasibility": 6, "adversary_vulnerability": 7,
            "compound_effect": 7, "reversibility_risk": 6, "precedent_value": 9,
            "public_interest": 9
        }, "Child unlawfully restrained from parent. Fundamental liberty interest."))
    
    # ========== COA (Lane B) ==========
    actions.append(score_action("coa-appeal-366810", "COA Appeal 366810 Brief",
        "COA", {
            "evidence_strength": 8, "legal_authority": 8, "strategic_impact": 7,
            "urgency": 7, "feasibility": 8, "adversary_vulnerability": 7,
            "compound_effect": 7, "reversibility_risk": 7, "precedent_value": 7,
            "public_interest": 6
        }, "Pending appeal — brief quality critical. Standard of review per issue."))
    
    # ========== 14th Circuit (Lane C) ==========
    actions.append(score_action("14th-vacate-exparte", "Vacate Ex Parte Orders (24)",
        "14TH", {
            "evidence_strength": 9, "legal_authority": 8, "strategic_impact": 8,
            "urgency": 9, "feasibility": 8, "adversary_vulnerability": 9,
            "compound_effect": 8, "reversibility_risk": 6, "precedent_value": 7,
            "public_interest": 7
        }, "24 ex parte orders without notice/hearing. MCR 3.207, due process."))
    
    actions.append(score_action("14th-disqualification", "Disqualification (MCR 2.003)",
        "14TH", {
            "evidence_strength": 9, "legal_authority": 8, "strategic_impact": 8,
            "urgency": 7, "feasibility": 7, "adversary_vulnerability": 8,
            "compound_effect": 8, "reversibility_risk": 6, "precedent_value": 6,
            "public_interest": 6
        }, "1,127 violations. Bias well-documented. MCR 2.003(C)(1)(a-b)."))
    
    actions.append(score_action("14th-emergency-restore", "Emergency Restore Parenting Time",
        "14TH", {
            "evidence_strength": 8, "legal_authority": 7, "strategic_impact": 9,
            "urgency": 10, "feasibility": 8, "adversary_vulnerability": 7,
            "compound_effect": 7, "reversibility_risk": 5, "precedent_value": 5,
            "public_interest": 6
        }, "Immediate restoration of parent-child relationship. Child welfare."))
    
    # ========== JTC (Lane D) ==========
    actions.append(score_action("jtc-formal-complaint", "JTC Formal Complaint (9-Count)",
        "JTC", {
            "evidence_strength": 10, "legal_authority": 9, "strategic_impact": 10,
            "urgency": 9, "feasibility": 8, "adversary_vulnerability": 10,
            "compound_effect": 10, "reversibility_risk": 8, "precedent_value": 9,
            "public_interest": 10
        }, "1,127 violations. 377 critical. Systematic pattern. Maximum impact."))
    
    # ========== USDC (Lane E) ==========
    actions.append(score_action("usdc-1983-5count", "USDC §1983 (5 Counts)",
        "USDC", {
            "evidence_strength": 8, "legal_authority": 9, "strategic_impact": 9,
            "urgency": 8, "feasibility": 6, "adversary_vulnerability": 8,
            "compound_effect": 8, "reversibility_risk": 7, "precedent_value": 9,
            "public_interest": 9
        }, "Due process + equal protection. Qualified immunity analysis needed."))
    
    actions.append(score_action("usdc-1983-injunction", "USDC §1983 Injunctive Relief",
        "USDC", {
            "evidence_strength": 8, "legal_authority": 8, "strategic_impact": 8,
            "urgency": 9, "feasibility": 6, "adversary_vulnerability": 7,
            "compound_effect": 7, "reversibility_risk": 6, "precedent_value": 8,
            "public_interest": 8
        }, "Preliminary + permanent injunction. Ongoing constitutional violation."))
    
    # ========== State Bar (Lane F) ==========
    actions.append(score_action("bar-berry", "State Bar Complaint — Berry",
        "BAR", {
            "evidence_strength": 8, "legal_authority": 7, "strategic_impact": 7,
            "urgency": 6, "feasibility": 9, "adversary_vulnerability": 8,
            "compound_effect": 7, "reversibility_risk": 7, "precedent_value": 6,
            "public_interest": 7
        }, "MRPC violations documented. AGC referral ready."))
    
    actions.append(score_action("bar-barnes", "State Bar Complaint — Barnes",
        "BAR", {
            "evidence_strength": 8, "legal_authority": 7, "strategic_impact": 7,
            "urgency": 6, "feasibility": 9, "adversary_vulnerability": 8,
            "compound_effect": 7, "reversibility_risk": 7, "precedent_value": 6,
            "public_interest": 6
        }, "MRPC violations. Conflicts of interest. Misrepresentation."))
    
    actions.append(score_action("bar-martini", "State Bar Complaint — Martini",
        "BAR", {
            "evidence_strength": 7, "legal_authority": 7, "strategic_impact": 6,
            "urgency": 6, "feasibility": 9, "adversary_vulnerability": 7,
            "compound_effect": 6, "reversibility_risk": 7, "precedent_value": 5,
            "public_interest": 6
        }, "MRPC violations. Incompetent representation."))
    
    return actions


def print_dashboard(actions):
    """Print a text dashboard of all scored actions."""
    sorted_actions = sorted(actions, key=lambda a: a["total_score"], reverse=True)
    
    print(f"\n{'='*80}")
    print(f"  OMEGA SCORE DASHBOARD — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Separation Days: {separation_days()} | Actions Scored: {len(actions)}")
    print(f"{'='*80}\n")
    
    for tier_name in ["CRITICAL", "HIGH", "MEDIUM", "STANDARD", "HOLD"]:
        tier_actions = [a for a in sorted_actions if a["tier"] == tier_name]
        if not tier_actions:
            continue
        
        symbol = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "STANDARD": "🔵", "HOLD": "⚪"}.get(tier_name, "")
        print(f"  {symbol} {tier_name} ({len(tier_actions)} actions)")
        print(f"  {'─'*76}")
        
        for a in tier_actions:
            print(f"  Ω{a['total_score']:3d} | Lane {a['lane']} | {a['name']}")
            print(f"       | {a['forum_label']}")
            # Axis breakdown
            axes = a["axes"]
            bars = " ".join(f"{k[:3]}:{v:2d}" for k, v in axes.items())
            print(f"       | {bars}")
            print()
    
    # Summary by forum
    print(f"\n  {'─'*76}")
    print(f"  FORUM SUMMARY")
    for forum, info in FORUMS.items():
        forum_acts = [a for a in sorted_actions if a["forum"] == forum]
        if forum_acts:
            avg = sum(a["total_score"] for a in forum_acts) / len(forum_acts)
            top = max(a["total_score"] for a in forum_acts)
            print(f"  Lane {info['lane']} {info['label']:35s} | {len(forum_acts)} actions | Avg Ω{avg:.0f} | Top Ω{top}")


if __name__ == "__main__":
    actions = score_all_actions()
    save_scores(actions)
    print_dashboard(actions)
    print(f"\n  ✓ {len(actions)} actions scored and saved to omega_scores table")
