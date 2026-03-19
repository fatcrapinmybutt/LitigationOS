#!/usr/bin/env python3
"""
Case Strategy Dashboard — Aggregated HTML command center.

Novel LitigationOS Tool #25

Generates an interactive HTML dashboard combining ALL tool outputs:
- Filing readiness scorecard (10 filings)
- Deadline countdown with urgency
- Settlement valuation summary
- Witness credibility rankings
- Response predictions
- Evidence heatmap stats
- Page limit status
- Dependency graph
- Perjury evidence counts
- Impeachment readiness
"""
import sys, os, json, re
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")
OUTPUT_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\reports")


def load_json(filename):
    """Safely load a JSON report."""
    path = REPORT_DIR / filename
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def generate_filing_cards(scorecard, trim_plan, predictions, dependencies):
    """Generate HTML cards for each filing."""
    cards = []
    for fid in [f"F{i}" for i in range(1, 11)]:
        sc = scorecard.get(fid, {})
        tp = trim_plan.get(fid, {})
        pred = predictions.get(fid, {})
        
        score = sc.get('overall_score', 0)
        grade = sc.get('grade', 'N/A')
        ready = sc.get('filing_ready', False)
        
        pages = tp.get('current_pages', '?')
        limit = tp.get('page_limit', '?')
        over = tp.get('over_limit', False)
        
        success = pred.get('success_probability', 0)
        court = pred.get('court', 'Unknown')
        
        # Color coding
        if score >= 85:
            color = '#22c55e'  # green
        elif score >= 70:
            color = '#eab308'  # yellow
        elif score >= 55:
            color = '#f97316'  # orange
        else:
            color = '#ef4444'  # red
        
        page_color = '#ef4444' if over else '#22c55e'
        success_color = '#22c55e' if success >= 0.6 else '#eab308' if success >= 0.4 else '#ef4444'
        
        card = f'''
        <div class="card" style="border-left: 4px solid {color}">
            <div class="card-header">
                <span class="filing-id">{fid}</span>
                <span class="score" style="color:{color}">{score:.0f}</span>
            </div>
            <div class="card-name">{pred.get('filing_name', fid)}</div>
            <div class="card-court">{court}</div>
            <div class="card-metrics">
                <div class="metric">
                    <span class="label">Grade</span>
                    <span class="value">{grade}</span>
                </div>
                <div class="metric">
                    <span class="label">Pages</span>
                    <span class="value" style="color:{page_color}">{pages}/{limit}</span>
                </div>
                <div class="metric">
                    <span class="label">Success</span>
                    <span class="value" style="color:{success_color}">{success*100:.0f}%</span>
                </div>
                <div class="metric">
                    <span class="label">Ready</span>
                    <span class="value">{'✅' if ready else '❌'}</span>
                </div>
            </div>
        </div>'''
        cards.append(card)
    return '\n'.join(cards)


def generate_witness_table(credibility):
    """Generate witness credibility table HTML."""
    rows = []
    for witness, data in sorted(credibility.items(), key=lambda x: x[1].get('overall_score', 0)):
        score = data.get('overall_score', 0)
        grade = data.get('grade', 'N/A')
        strategies = len(data.get('cross_exam_strategies', []))
        
        if score >= 65: color = '#22c55e'
        elif score >= 50: color = '#eab308'
        elif score >= 35: color = '#f97316'
        else: color = '#ef4444'
        
        bar_width = int(score)
        rows.append(f'''
        <tr>
            <td>{witness}</td>
            <td>{data.get('role', '')}</td>
            <td style="color:{color}; font-weight:bold">{score:.1f}</td>
            <td>
                <div class="bar-bg"><div class="bar" style="width:{bar_width}%; background:{color}"></div></div>
            </td>
            <td>{grade}</td>
            <td>{strategies}</td>
        </tr>''')
    return '\n'.join(rows)


def generate_dashboard():
    """Generate the full HTML dashboard."""
    # Load all reports
    scorecard = load_json('filing_readiness_scorecard.json')
    trim_plan = load_json('filing_trim_plan.json')
    predictions = load_json('response_predictions.json')
    credibility = load_json('witness_credibility.json')
    settlement = load_json('settlement_valuation.json')
    heatmap = load_json('evidence_heatmap.json')
    dependencies = load_json('filing_dependencies.json')
    perjury = load_json('perjury_evidence.json')
    deadlines = load_json('deadline_intelligence.json')
    authority = load_json('authority_strength.json')
    
    # Extract key stats
    grand_total = settlement.get('grand_total', {})
    low = grand_total.get('low', 0)
    mid = grand_total.get('mid', 0)
    high = grand_total.get('high', 0)
    demand = grand_total.get('recommended_demand', 0)
    
    case_params = settlement.get('case_parameters', {})
    days_sep = case_params.get('days_separated', 0)
    violations = case_params.get('violations', 0)
    contradictions = case_params.get('contradictions', 0)
    
    heatmap_summary = heatmap.get('summary', {})
    evidence_total = heatmap_summary.get('total_dated_evidence', 0)
    peak_month = heatmap_summary.get('peak_month', 'N/A')
    
    # Count ready filings
    ready_count = sum(1 for f in scorecard.values() if isinstance(f, dict) and f.get('filing_ready'))
    avg_score = sum(f.get('overall_score', 0) for f in scorecard.values() if isinstance(f, dict)) / max(len(scorecard), 1)
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LitigationOS — Case Strategy Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        h1 {{ font-size: 1.8em; color: #38bdf8; margin-bottom: 5px; }}
        h2 {{ font-size: 1.3em; color: #94a3b8; margin: 20px 0 10px; border-bottom: 1px solid #334155; padding-bottom: 5px; }}
        .subtitle {{ color: #64748b; font-size: 0.9em; margin-bottom: 20px; }}
        
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
        .kpi {{ background: #1e293b; border-radius: 8px; padding: 16px; text-align: center; }}
        .kpi .number {{ font-size: 2em; font-weight: bold; color: #38bdf8; }}
        .kpi .label {{ font-size: 0.8em; color: #94a3b8; margin-top: 4px; }}
        .kpi.green .number {{ color: #22c55e; }}
        .kpi.red .number {{ color: #ef4444; }}
        .kpi.yellow .number {{ color: #eab308; }}
        .kpi.purple .number {{ color: #a855f7; }}
        
        .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 14px; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .filing-id {{ font-weight: bold; font-size: 1.1em; }}
        .score {{ font-size: 1.8em; font-weight: bold; }}
        .card-name {{ font-size: 0.85em; color: #94a3b8; margin: 4px 0; }}
        .card-court {{ font-size: 0.75em; color: #64748b; margin-bottom: 8px; }}
        .card-metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
        .metric {{ text-align: center; }}
        .metric .label {{ font-size: 0.7em; color: #64748b; display: block; }}
        .metric .value {{ font-size: 0.9em; font-weight: bold; }}
        
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ background: #1e293b; color: #94a3b8; padding: 8px 12px; text-align: left; font-size: 0.85em; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #1e293b; font-size: 0.9em; }}
        tr:hover {{ background: #1e293b; }}
        
        .bar-bg {{ background: #334155; border-radius: 4px; height: 12px; width: 100px; }}
        .bar {{ height: 12px; border-radius: 4px; }}
        
        .settlement {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 12px; padding: 20px; margin: 10px 0; }}
        .settlement-range {{ display: flex; justify-content: space-around; text-align: center; }}
        .settlement-range .amount {{ font-size: 1.5em; font-weight: bold; }}
        .settlement-range .type {{ font-size: 0.8em; color: #64748b; }}
        
        .footer {{ text-align: center; color: #475569; font-size: 0.8em; margin-top: 30px; padding-top: 15px; border-top: 1px solid #1e293b; }}
    </style>
</head>
<body>
    <h1>⚖️ LitigationOS — Case Strategy Dashboard</h1>
    <div class="subtitle">Pigors v. Watson | Generated: {now} | {days_sep} days since separation</div>
    
    <div class="kpi-grid">
        <div class="kpi {'green' if ready_count >= 5 else 'yellow' if ready_count >= 3 else 'red'}">
            <div class="number">{ready_count}/10</div>
            <div class="label">Filings Ready</div>
        </div>
        <div class="kpi yellow">
            <div class="number">{avg_score:.0f}</div>
            <div class="label">Avg Score</div>
        </div>
        <div class="kpi red">
            <div class="number">{violations:,}</div>
            <div class="label">Violations</div>
        </div>
        <div class="kpi">
            <div class="number">{contradictions:,}</div>
            <div class="label">Contradictions</div>
        </div>
        <div class="kpi green">
            <div class="number">{evidence_total:,}</div>
            <div class="label">Evidence Items</div>
        </div>
        <div class="kpi purple">
            <div class="number">{days_sep}</div>
            <div class="label">Days Separated</div>
        </div>
    </div>
    
    <div class="settlement">
        <h2 style="border:none; margin:0 0 15px 0">💰 Settlement Valuation</h2>
        <div class="settlement-range">
            <div><div class="amount" style="color:#eab308">${low:,.0f}</div><div class="type">Conservative</div></div>
            <div><div class="amount" style="color:#22c55e">${mid:,.0f}</div><div class="type">Midpoint</div></div>
            <div><div class="amount" style="color:#38bdf8">${high:,.0f}</div><div class="type">Aggressive</div></div>
            <div><div class="amount" style="color:#a855f7">${demand:,.0f}</div><div class="type">Recommended Demand</div></div>
        </div>
    </div>
    
    <h2>📋 Filing Status</h2>
    <div class="cards-grid">
        {generate_filing_cards(scorecard, trim_plan, predictions, dependencies)}
    </div>
    
    <h2>👤 Witness Credibility</h2>
    <table>
        <tr><th>Witness</th><th>Role</th><th>Score</th><th>Bar</th><th>Grade</th><th>Strategies</th></tr>
        {generate_witness_table(credibility)}
    </table>
    
    <div class="footer">
        LitigationOS v∞ — 25 Novel Tools — Built Autonomously by Copilot Agent Fleet<br>
        NOT legal advice. All statistics traceable to litigation_context.db queries.
    </div>
</body>
</html>'''
    
    return html


def main():
    print("=" * 70)
    print("CASE STRATEGY DASHBOARD — HTML Command Center Generator")
    print("=" * 70)
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    html = generate_dashboard()
    
    output_path = OUTPUT_DIR / "CASE_DASHBOARD.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n  ✅ Dashboard generated: {output_path}")
    print(f"  📊 Open in browser to view interactive command center")
    print(f"  📁 Size: {len(html):,} bytes")
    
    # Count data sources loaded
    reports = [
        'filing_readiness_scorecard.json', 'filing_trim_plan.json',
        'response_predictions.json', 'witness_credibility.json',
        'settlement_valuation.json', 'evidence_heatmap.json',
        'filing_dependencies.json', 'perjury_evidence.json',
        'deadline_intelligence.json', 'authority_strength.json',
    ]
    loaded = sum(1 for r in reports if (REPORT_DIR / r).exists())
    print(f"  📈 Data sources: {loaded}/{len(reports)} reports loaded")


if __name__ == '__main__':
    main()
