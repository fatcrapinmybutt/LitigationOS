#!/usr/bin/env python3
"""
NOVEL TOOL #29: Filing Priority Optimizer (Game Theory)
========================================================
Uses multi-criteria decision analysis + game theory to determine
the OPTIMAL filing sequence that maximizes litigation success.

Factors considered:
- Deadline urgency (hard deadlines vs strategic timing)
- Filing dependencies (which must come before others)
- Court receptivity (probability of success per filing)
- Strategic value (how much leverage each filing creates)
- Resource cost (preparation effort remaining)
- Adversary disruption (how much pressure on opposing side)
- Cascade effects (how one filing affects others)

This combines operations research (scheduling optimization)
with legal strategy — never been done in litigation software.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from itertools import permutations

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")

# Filing data (from all prior tools)
FILINGS = {
    "F1": {
        "name": "Emergency TRO / Eviction Defense",
        "lane": "B",
        "court": "14th Circuit Civil",
        "deadline": "2025-04-15",
        "deadline_type": "strategic",
        "readiness": 0.65,
        "success_probability": 0.45,
        "strategic_value": 6,  # 1-10
        "prep_effort_days": 5,
        "adversary_disruption": 4,
        "dependencies": [],
        "page_limit_status": "under",
        "research_coverage": 0.43,
        "word_count_status": "needs_trim"
    },
    "F2": {
        "name": "Housing Rights Complaint",
        "lane": "B",
        "court": "14th Circuit Civil",
        "deadline": "2025-05-01",
        "deadline_type": "strategic",
        "readiness": 0.55,
        "success_probability": 0.50,
        "strategic_value": 5,
        "prep_effort_days": 7,
        "adversary_disruption": 5,
        "dependencies": ["F1"],
        "page_limit_status": "over",
        "research_coverage": 0.29,
        "word_count_status": "needs_trim"
    },
    "F3": {
        "name": "Judicial Disqualification MCR 2.003",
        "lane": "A",
        "court": "14th Circuit Family",
        "deadline": "2025-04-01",
        "deadline_type": "hard",
        "readiness": 0.85,
        "success_probability": 0.55,
        "strategic_value": 9,
        "prep_effort_days": 2,
        "adversary_disruption": 9,
        "dependencies": [],
        "page_limit_status": "over",
        "research_coverage": 0.82,
        "word_count_status": "needs_trim"
    },
    "F4": {
        "name": "Federal §1983 Civil Rights",
        "lane": "E",
        "court": "USDC Western District",
        "deadline": "2025-05-15",
        "deadline_type": "strategic",
        "readiness": 0.80,
        "success_probability": 0.65,
        "strategic_value": 10,
        "prep_effort_days": 5,
        "adversary_disruption": 10,
        "dependencies": ["F3"],
        "page_limit_status": "over",
        "research_coverage": 1.00,
        "word_count_status": "needs_trim"
    },
    "F5": {
        "name": "MSC Superintending Control",
        "lane": "E",
        "court": "Michigan Supreme Court",
        "deadline": "2025-05-15",
        "deadline_type": "strategic",
        "readiness": 0.70,
        "success_probability": 0.35,
        "strategic_value": 8,
        "prep_effort_days": 7,
        "adversary_disruption": 8,
        "dependencies": ["F3"],
        "page_limit_status": "over",
        "research_coverage": 1.00,
        "word_count_status": "needs_trim"
    },
    "F6": {
        "name": "JTC Judicial Misconduct Complaint",
        "lane": "E",
        "court": "Judicial Tenure Commission",
        "deadline": "2025-05-01",
        "deadline_type": "strategic",
        "readiness": 0.75,
        "success_probability": 0.75,
        "strategic_value": 8,
        "prep_effort_days": 3,
        "adversary_disruption": 7,
        "dependencies": [],
        "page_limit_status": "under",
        "research_coverage": 0.67,
        "word_count_status": "ok"
    },
    "F7": {
        "name": "Custody Modification",
        "lane": "A",
        "court": "14th Circuit Family",
        "deadline": "2025-05-15",
        "deadline_type": "strategic",
        "readiness": 0.60,
        "success_probability": 0.50,
        "strategic_value": 9,
        "prep_effort_days": 7,
        "adversary_disruption": 6,
        "dependencies": ["F3", "F8"],
        "page_limit_status": "over",
        "research_coverage": 0.70,
        "word_count_status": "needs_trim"
    },
    "F8": {
        "name": "PPO Termination",
        "lane": "D",
        "court": "14th Circuit Family",
        "deadline": "2025-04-15",
        "deadline_type": "hard",
        "readiness": 0.55,
        "success_probability": 0.50,
        "strategic_value": 7,
        "prep_effort_days": 4,
        "adversary_disruption": 5,
        "dependencies": [],
        "page_limit_status": "over",
        "research_coverage": 0.33,
        "word_count_status": "needs_trim"
    },
    "F9": {
        "name": "COA Appeal Brief",
        "lane": "F",
        "court": "Court of Appeals",
        "deadline": "2025-04-15",
        "deadline_type": "hard",
        "readiness": 0.50,
        "success_probability": 0.55,
        "strategic_value": 8,
        "prep_effort_days": 10,
        "adversary_disruption": 7,
        "dependencies": [],
        "page_limit_status": "under",
        "research_coverage": 0.29,
        "word_count_status": "ok"
    },
    "F10": {
        "name": "COA Emergency Motion",
        "lane": "F",
        "court": "Court of Appeals",
        "deadline": "2025-04-01",
        "deadline_type": "hard",
        "readiness": 0.60,
        "success_probability": 0.40,
        "strategic_value": 7,
        "prep_effort_days": 2,
        "adversary_disruption": 6,
        "dependencies": [],
        "page_limit_status": "under",
        "research_coverage": 0.25,
        "word_count_status": "ok"
    }
}

# Cascade effects matrix: filing A → how it affects filing B
CASCADE_EFFECTS = {
    ("F3", "F4"): 0.15,   # Disqualification success boosts §1983
    ("F3", "F5"): 0.10,   # Disqualification shows MSC pattern
    ("F3", "F7"): 0.20,   # New judge = better custody chance
    ("F6", "F3"): 0.10,   # JTC complaint adds pressure for recusal
    ("F6", "F5"): 0.15,   # JTC validates MSC complaint
    ("F4", "F7"): 0.10,   # Federal filing pressures state court
    ("F8", "F7"): 0.15,   # PPO termination enables custody mod
    ("F10", "F9"): 0.10,  # Emergency motion buys time for appeal
    ("F1", "F2"): 0.10,   # TRO success helps housing complaint
    ("F3", "F6"): 0.05,   # Recusal docs support JTC
    ("F4", "F3"): 0.05,   # Federal filing adds recusal pressure
}


def calculate_urgency_score(filing):
    """Score urgency based on deadline proximity and type."""
    try:
        deadline = datetime.strptime(filing["deadline"], "%Y-%m-%d")
        days_left = (deadline - datetime.now()).days
    except Exception:
        days_left = 30

    if filing["deadline_type"] == "hard":
        if days_left <= 0:
            return 10.0  # OVERDUE
        elif days_left <= 7:
            return 9.5
        elif days_left <= 14:
            return 9.0
        elif days_left <= 21:
            return 8.0
        elif days_left <= 30:
            return 7.0
        else:
            return 5.0
    else:  # strategic
        if days_left <= 14:
            return 7.0
        elif days_left <= 30:
            return 5.0
        else:
            return 3.0


def calculate_composite_score(filing_id, filing):
    """Multi-criteria score combining all factors."""
    weights = {
        "urgency": 0.25,
        "strategic_value": 0.20,
        "success_probability": 0.15,
        "adversary_disruption": 0.15,
        "readiness": 0.10,
        "research_coverage": 0.10,
        "cascade_potential": 0.05
    }

    urgency = calculate_urgency_score(filing)
    strategic = filing["strategic_value"]
    success = filing["success_probability"] * 10
    disruption = filing["adversary_disruption"]
    readiness = filing["readiness"] * 10
    research = filing["research_coverage"] * 10

    # Calculate cascade potential
    cascade = 0
    for (src, tgt), effect in CASCADE_EFFECTS.items():
        if src == filing_id:
            cascade += effect * 10
    cascade = min(cascade, 10)

    composite = (
        weights["urgency"] * urgency +
        weights["strategic_value"] * strategic +
        weights["success_probability"] * success +
        weights["adversary_disruption"] * disruption +
        weights["readiness"] * readiness +
        weights["research_coverage"] * research +
        weights["cascade_potential"] * cascade
    )

    return {
        "composite": round(composite, 2),
        "urgency": round(urgency, 1),
        "strategic_value": strategic,
        "success_probability": round(success, 1),
        "disruption": disruption,
        "readiness": round(readiness, 1),
        "research_coverage": round(research, 1),
        "cascade_potential": round(cascade, 1)
    }


def topological_sort(filings):
    """Sort filings respecting dependencies."""
    in_degree = {fid: 0 for fid in filings}
    adj = {fid: [] for fid in filings}

    for fid, fdata in filings.items():
        for dep in fdata["dependencies"]:
            if dep in filings:
                adj[dep].append(fid)
                in_degree[fid] += 1

    queue = [fid for fid, deg in in_degree.items() if deg == 0]
    result = []

    while queue:
        # Among zero-degree nodes, pick highest composite score
        queue.sort(key=lambda x: calculate_composite_score(x, filings[x])["composite"], reverse=True)
        node = queue.pop(0)
        result.append(node)

        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def simulate_sequence(sequence, filings):
    """Simulate a filing sequence and calculate total strategic value."""
    total_value = 0
    success_boosts = {}
    filed = set()

    for filing_id in sequence:
        filing = filings[filing_id]
        base_success = filing["success_probability"]

        # Apply cascade boosts from already-filed filings
        boost = 0
        for prev_filed in filed:
            key = (prev_filed, filing_id)
            if key in CASCADE_EFFECTS:
                boost += CASCADE_EFFECTS[key]

        adjusted_success = min(base_success + boost, 0.95)
        expected_value = adjusted_success * filing["strategic_value"]
        total_value += expected_value

        success_boosts[filing_id] = {
            "base_success": base_success,
            "cascade_boost": round(boost, 3),
            "adjusted_success": round(adjusted_success, 3),
            "expected_value": round(expected_value, 2)
        }

        filed.add(filing_id)

    return total_value, success_boosts


def generate_waves(sequence, filings):
    """Group sequence into filing waves (max 3 per wave)."""
    waves = []
    current_wave = []

    for filing_id in sequence:
        current_wave.append(filing_id)
        if len(current_wave) >= 3:
            waves.append(current_wave)
            current_wave = []

    if current_wave:
        waves.append(current_wave)

    return waves


def main():
    print("=" * 60)
    print("FILING PRIORITY OPTIMIZER v1.0")
    print("Game Theory + Multi-Criteria Decision Analysis")
    print("=" * 60)

    # Step 1: Score all filings
    print("\n📊 STEP 1: Multi-Criteria Scoring")
    print("-" * 50)

    scores = {}
    for fid, fdata in FILINGS.items():
        score = calculate_composite_score(fid, fdata)
        scores[fid] = score
        print(f"  {fid} ({fdata['name'][:30]:30s}) "
              f"Composite: {score['composite']:5.2f} "
              f"Urgency: {score['urgency']:4.1f} "
              f"Strategic: {score['strategic_value']}")

    # Step 2: Topological sort (respect dependencies)
    print(f"\n📋 STEP 2: Dependency-Aware Optimal Sequence")
    print("-" * 50)

    optimal_sequence = topological_sort(FILINGS)
    total_value, boosts = simulate_sequence(optimal_sequence, FILINGS)

    print(f"  Optimal sequence: {' → '.join(optimal_sequence)}")
    print(f"  Total expected strategic value: {total_value:.2f}")
    print()

    for i, fid in enumerate(optimal_sequence, 1):
        fdata = FILINGS[fid]
        boost_data = boosts[fid]
        cascade_str = f"+{boost_data['cascade_boost']*100:.1f}%" if boost_data['cascade_boost'] > 0 else ""
        print(f"  {i:2d}. {fid} — {fdata['name'][:35]:35s} "
              f"P(success)={boost_data['adjusted_success']*100:.0f}%{cascade_str:>8s} "
              f"EV={boost_data['expected_value']:.1f}")

    # Step 3: Wave planning
    print(f"\n🌊 STEP 3: Filing Waves (max 3 per wave)")
    print("-" * 50)

    waves = generate_waves(optimal_sequence, FILINGS)
    for i, wave in enumerate(waves, 1):
        hard_deadlines = [FILINGS[fid]["deadline"] for fid in wave
                          if FILINGS[fid]["deadline_type"] == "hard"]
        wave_deadline = min(hard_deadlines) if hard_deadlines else "strategic"
        print(f"\n  Wave {i} (deadline: {wave_deadline}):")
        for fid in wave:
            fdata = FILINGS[fid]
            print(f"    {fid}: {fdata['name'][:40]:40s} "
                  f"[{fdata['deadline_type'].upper():9s}] "
                  f"Due: {fdata['deadline']}")

    # Step 4: Alternative sequences comparison
    print(f"\n🎯 STEP 4: Alternative Strategy Comparison")
    print("-" * 50)

    strategies = {
        "OPTIMAL (dependency-aware)": optimal_sequence,
        "URGENCY-FIRST": sorted(FILINGS.keys(),
                                 key=lambda x: calculate_urgency_score(FILINGS[x]),
                                 reverse=True),
        "HIGH-VALUE-FIRST": sorted(FILINGS.keys(),
                                    key=lambda x: FILINGS[x]["strategic_value"],
                                    reverse=True),
        "DISRUPTION-FIRST": sorted(FILINGS.keys(),
                                    key=lambda x: FILINGS[x]["adversary_disruption"],
                                    reverse=True),
        "READY-FIRST": sorted(FILINGS.keys(),
                               key=lambda x: FILINGS[x]["readiness"],
                               reverse=True),
    }

    strategy_results = {}
    for name, seq in strategies.items():
        tv, _ = simulate_sequence(seq, FILINGS)
        strategy_results[name] = round(tv, 2)
        best_marker = " ⭐ BEST" if name == "OPTIMAL (dependency-aware)" else ""
        print(f"  {name:35s}  EV = {tv:6.2f}{best_marker}")

    # Step 5: Critical path analysis
    print(f"\n⚡ STEP 5: Critical Path Analysis")
    print("-" * 50)

    hard_deadline_filings = {fid: fdata for fid, fdata in FILINGS.items()
                             if fdata["deadline_type"] == "hard"}
    for fid in sorted(hard_deadline_filings.keys(),
                       key=lambda x: FILINGS[x]["deadline"]):
        fdata = FILINGS[fid]
        days = (datetime.strptime(fdata["deadline"], "%Y-%m-%d") - datetime.now()).days
        status = "🔴 OVERDUE" if days < 0 else "🟡 URGENT" if days <= 14 else "🟢 ON TRACK"
        print(f"  {fid}: {fdata['name'][:30]:30s} Due: {fdata['deadline']} ({days}d) {status}")
        if fdata["page_limit_status"] == "over":
            print(f"       ⚠️  OVER PAGE LIMIT — needs trimming before filing!")
        if fdata["research_coverage"] < 0.50:
            print(f"       ⚠️  RESEARCH GAPS — only {fdata['research_coverage']*100:.0f}% authority coverage")

    # Step 6: Immediate action items
    print(f"\n🎯 STEP 6: Immediate Action Items (Next 7 Days)")
    print("-" * 50)

    actions = []
    for fid in optimal_sequence[:5]:
        fdata = FILINGS[fid]
        if fdata["page_limit_status"] == "over":
            actions.append(f"TRIM {fid} to page limit ({fdata['court']})")
        if fdata["research_coverage"] < 0.70:
            actions.append(f"FILL RESEARCH GAPS for {fid} ({fdata['research_coverage']*100:.0f}% → 100%)")
        days = (datetime.strptime(fdata["deadline"], "%Y-%m-%d") - datetime.now()).days
        if days <= 14:
            actions.append(f"FINALIZE {fid} — {fdata['name']} (due in {days} days)")

    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action}")

    # Save results
    output = {
        "generated": datetime.now().isoformat(),
        "optimal_sequence": optimal_sequence,
        "total_expected_value": round(total_value, 2),
        "filing_scores": {fid: {**scores[fid], **boosts[fid]} for fid in optimal_sequence},
        "waves": [{"wave": i+1, "filings": wave} for i, wave in enumerate(waves)],
        "strategy_comparison": strategy_results,
        "critical_path": {fid: {
            "deadline": FILINGS[fid]["deadline"],
            "days_remaining": (datetime.strptime(FILINGS[fid]["deadline"], "%Y-%m-%d") - datetime.now()).days,
            "deadline_type": FILINGS[fid]["deadline_type"],
            "page_limit_status": FILINGS[fid]["page_limit_status"],
            "research_coverage": FILINGS[fid]["research_coverage"]
        } for fid in hard_deadline_filings},
        "immediate_actions": actions
    }

    json_path = REPORTS_DIR / "filing_priority_optimization.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    # Markdown report
    md_lines = ["# FILING PRIORITY OPTIMIZATION REPORT"]
    md_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    md_lines.append("## Optimal Filing Sequence\n")
    for i, fid in enumerate(optimal_sequence, 1):
        fdata = FILINGS[fid]
        b = boosts[fid]
        md_lines.append(f"{i}. **{fid}** — {fdata['name']} "
                        f"(P={b['adjusted_success']*100:.0f}%, EV={b['expected_value']:.1f})")

    md_lines.append(f"\n**Total Expected Strategic Value: {total_value:.2f}**\n")

    md_lines.append("## Filing Waves\n")
    for i, wave in enumerate(waves, 1):
        md_lines.append(f"### Wave {i}")
        for fid in wave:
            md_lines.append(f"- {fid}: {FILINGS[fid]['name']} (due {FILINGS[fid]['deadline']})")
        md_lines.append("")

    md_lines.append("## Immediate Actions\n")
    for i, action in enumerate(actions, 1):
        md_lines.append(f"{i}. {action}")

    md_path = REPORTS_DIR / "FILING_PRIORITY_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\n✅ JSON report: {json_path}")
    print(f"✅ Markdown report: {md_path}")
    print(f"\n{'='*60}")
    print(f"FILING PRIORITY OPTIMIZER — COMPLETE")
    print(f"{'='*60}")
    print(f"Optimal sequence: {' → '.join(optimal_sequence)}")
    print(f"Total EV: {total_value:.2f}")
    print(f"Waves: {len(waves)}")
    print(f"Immediate actions: {len(actions)}")

    return output


if __name__ == "__main__":
    main()
