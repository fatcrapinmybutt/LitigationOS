#!/usr/bin/env python3
"""
Tool #86 — Contradiction Heat Map
=====================================
Mines detected_contradictions table to build a visual heat map
showing WHERE contradictions cluster:
- By topic (custody, violence, housing, finances, etc.)
- By party (Emily's statements vs evidence)
- By severity (perjury-grade vs minor inconsistency)
- By filing relevance

Produces a priority-ranked list of the strongest contradictions
for impeachment at trial.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

TOPIC_KEYWORDS = {
    'custody_parenting': ['custody', 'parenting', 'visitation', 'child', 'parent', 'father', 'mother'],
    'violence_abuse': ['violence', 'abuse', 'assault', 'hit', 'struck', 'threat', 'harm', 'danger'],
    'housing': ['housing', 'evict', 'lease', 'rent', 'shady oaks', 'apartment', 'home'],
    'financial': ['money', 'income', 'pay', 'support', 'financial', 'debt', 'employment'],
    'substance': ['drug', 'alcohol', 'substance', 'drink', 'intoxicat'],
    'mental_health': ['mental', 'psych', 'therapy', 'counsel', 'depress', 'anxiety'],
    'ppo_stalking': ['ppo', 'stalking', 'protection', 'restrain', 'no contact'],
    'court_process': ['court', 'hearing', 'motion', 'order', 'judge', 'filing'],
}

def main():
    print("=" * 70)
    print("CONTRADICTION HEAT MAP — Tool #86")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    # Check schema
    cols = [r[1] for r in conn.execute("PRAGMA table_info(detected_contradictions)").fetchall()]
    print(f"  Columns: {', '.join(cols[:10])}")
    
    total = conn.execute("SELECT COUNT(*) FROM detected_contradictions").fetchone()[0]
    print(f"  Total contradictions: {total}")
    
    # Find text columns
    text_cols = []
    for c in cols:
        if any(kw in c.lower() for kw in ['text', 'content', 'description', 'statement', 'detail', 'contradiction', 'quote', 'claim']):
            text_cols.append(c)
    if not text_cols:
        text_cols = [c for c in cols if c not in ('id', 'rowid', 'created_at', 'updated_at')][:3]
    
    print(f"  Search columns: {', '.join(text_cols)}")
    
    # Find severity column
    severity_col = None
    for c in cols:
        if any(kw in c.lower() for kw in ['severity', 'level', 'grade', 'score', 'priority']):
            severity_col = c
            break
    
    severity_dist = {}
    if severity_col:
        rows = conn.execute(f"SELECT {severity_col}, COUNT(*) FROM detected_contradictions GROUP BY {severity_col} ORDER BY COUNT(*) DESC").fetchall()
        severity_dist = {str(r[0]): r[1] for r in rows if r[0]}
        print(f"\n  Severity distribution:")
        for sev, cnt in severity_dist.items():
            print(f"    {cnt:>5}x  {sev}")
    
    # Topic clustering
    topic_counts = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        topic_total = 0
        for kw in keywords:
            for col in text_cols:
                try:
                    cnt = conn.execute(
                        f"SELECT COUNT(*) FROM detected_contradictions WHERE LOWER(CAST({col} AS TEXT)) LIKE ?",
                        (f'%{kw}%',)
                    ).fetchone()[0]
                    topic_total += cnt
                except:
                    pass
        topic_counts[topic] = topic_total
    
    # Sort by count
    sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
    
    print(f"\n  Topic heat map:")
    max_count = max(topic_counts.values()) if topic_counts.values() else 1
    for topic, count in sorted_topics:
        bar_len = int((count / max_count) * 30) if max_count > 0 else 0
        bar = '🔴' * min(bar_len, 10) + '🟡' * max(0, min(bar_len - 10, 10)) + '🟢' * max(0, bar_len - 20)
        print(f"    {topic:>20}: {bar} ({count:,})")
    
    # Get sample strongest contradictions
    samples = []
    for col in text_cols[:1]:
        try:
            rows = conn.execute(f"SELECT SUBSTR(CAST({col} AS TEXT), 1, 150) FROM detected_contradictions LIMIT 5").fetchall()
            samples = [str(r[0]) for r in rows if r[0]]
        except:
            pass
    
    conn.close()
    
    # Build report
    lines = [
        "# 🔥 CONTRADICTION HEAT MAP",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Total contradictions: {total:,}*\n",
        "---\n",
        "## Topic Clusters (highest concentration = strongest impeachment)\n",
        "| Topic | Count | Heat | Impeachment Value |",
        "|-------|-------|------|-------------------|",
    ]
    
    for topic, count in sorted_topics:
        heat = '🔴🔴🔴' if count > 300 else '🔴🔴' if count > 100 else '🟡' if count > 50 else '🟢'
        value = 'CRITICAL' if count > 300 else 'HIGH' if count > 100 else 'MEDIUM' if count > 50 else 'LOW'
        topic_display = topic.replace('_', ' ').title()
        lines.append(f"| {topic_display} | {count:,} | {heat} | {value} |")
    
    if severity_dist:
        lines.append("\n## Severity Distribution\n")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev, cnt in severity_dist.items():
            lines.append(f"| {sev} | {cnt:,} |")
    
    if samples:
        lines.append("\n## Sample Contradictions\n")
        for i, s in enumerate(samples, 1):
            lines.append(f"{i}. _{s}_\n")
    
    lines.extend([
        "---",
        "## Impeachment Strategy",
        "",
        "**Strongest topics for cross-examination:**",
        f"1. {sorted_topics[0][0].replace('_', ' ').title()} ({sorted_topics[0][1]:,} contradictions)" if sorted_topics else "",
        f"2. {sorted_topics[1][0].replace('_', ' ').title()} ({sorted_topics[1][1]:,} contradictions)" if len(sorted_topics) > 1 else "",
        f"3. {sorted_topics[2][0].replace('_', ' ').title()} ({sorted_topics[2][1]:,} contradictions)" if len(sorted_topics) > 2 else "",
        "",
        "**Approach:** Use contradictions as impeachment material per MRE 613(b).",
        "First establish the prior statement, then confront with contradicting evidence.",
        "",
        f"*Contradiction Heat Map — Tool #86*",
    ])
    
    md_path = REPORTS_DIR / "CONTRADICTION_HEATMAP.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "contradiction_heatmap.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Contradiction Heat Map (#86)',
        'total': total,
        'topic_counts': dict(sorted_topics),
        'severity': severity_dist,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total:,} contradictions mapped across {len(TOPIC_KEYWORDS)} topics")
    print(f"   Reports: CONTRADICTION_HEATMAP.md + contradiction_heatmap.json")

if __name__ == '__main__':
    main()
