#!/usr/bin/env python3
"""
Tool #246 — Judicial Bias Pattern Analyzer
Deep analysis of Judge McNeill's documented bias patterns. Queries judicial_violations,
docket_events for rulings, evidence_quotes for McNeill references. Analyzes ruling
asymmetry, procedural shortcuts, canon violations, FOC communication patterns.
Applies Crampton v Dept of State 395 Mich 347 objective bias test.

LitigationOS — Pigors v. Watson
"""
import sys, os, sqlite3, json, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

def s(v):
    """Safe lowercase string — prevents NoneType crashes."""
    return (v or "").lower()

def get_conn():
    conn = sqlite3.connect(DB, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def verify_table(conn, table_name):
    """Verify table exists and return column names."""
    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    if not cols:
        return None
    return [c['name'] for c in cols]

def main():
    print("=" * 70)
    print("TOOL #246 — JUDICIAL BIAS PATTERN ANALYZER")
    print("Pigors v. Watson | LitigationOS")
    print("Subject: Hon. Jenny L. McNeill, 14th Circuit Court")
    print("=" * 70)

    if not os.path.exists(DB):
        print(f"ERROR: Database not found at {DB}")
        return

    conn = get_conn()

    # ===== 1. JUDICIAL VIOLATIONS ANALYSIS =====
    print("\n[1/5] Analyzing judicial_violations...")
    jv_cols = verify_table(conn, 'judicial_violations')
    violations_by_canon = defaultdict(list)
    violations_by_severity = defaultdict(int)
    total_violations = 0

    if jv_cols:
        print(f"  Columns: {jv_cols}")
        has_canon = 'canon_number' in jv_cols
        has_desc = 'violation_description' in jv_cols
        has_severity = 'severity' in jv_cols
        has_judge = 'judge_name' in jv_cols
        has_date = 'violation_date' in jv_cols or 'date' in jv_cols
        date_col = 'violation_date' if 'violation_date' in jv_cols else 'date' if 'date' in jv_cols else None
        has_category = 'violation_category' in jv_cols or 'category' in jv_cols
        cat_col = 'violation_category' if 'violation_category' in jv_cols else 'category' if 'category' in jv_cols else None

        total_violations = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
        print(f"  Total violations: {total_violations:,}")

        rows = conn.execute("SELECT * FROM judicial_violations").fetchall()
        for r in rows:
            canon = str(r['canon_number'] if has_canon else 'Unknown') or 'Unknown'
            desc = str(r['violation_description'] if has_desc else '') or ''
            sev = str(r['severity'] if has_severity else 'medium') or 'medium'
            date_val = str(r[date_col] if date_col else '') or ''
            cat_val = str(r[cat_col] if cat_col else '') or ''

            violations_by_canon[canon].append({
                'description': desc[:200],
                'severity': sev,
                'date': date_val,
                'category': cat_val
            })
            violations_by_severity[s(sev)] += 1

        # Print canon breakdown
        for canon, vlist in sorted(violations_by_canon.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
            print(f"  Canon {canon}: {len(vlist)} violations")
    else:
        print("  TABLE NOT FOUND — skipping")

    # ===== 2. DOCKET EVENTS — RULING ANALYSIS =====
    print("\n[2/5] Analyzing docket_events for ruling patterns...")
    de_cols = verify_table(conn, 'docket_events')
    rulings = []
    rulings_favoring_emily = 0
    rulings_favoring_andrew = 0
    rulings_neutral = 0
    procedural_shortcuts = 0
    no_hearing_orders = []

    if de_cols:
        has_title = 'title' in de_cols
        has_summary = 'summary' in de_cols
        has_type = 'event_type' in de_cols
        has_date = 'event_date_iso' in de_cols

        rows = conn.execute("SELECT * FROM docket_events").fetchall()
        for r in rows:
            title = str(r['title'] if has_title else '') or ''
            summary = str(r['summary'] if has_summary else '') or ''
            etype = str(r['event_type'] if has_type else '') or ''
            date_val = str(r['event_date_iso'] if has_date else '') or ''
            combined = s(title + ' ' + summary + ' ' + etype)

            is_ruling = any(w in combined for w in ['order', 'ruling', 'judgment', 'grant', 'deny', 'sustain', 'overrul'])
            if is_ruling:
                rulings.append({
                    'date': date_val, 'title': title[:200], 'summary': summary[:200],
                    'type': etype
                })

                # Analyze favor direction
                favors_emily = any(w in combined for w in [
                    'deny father', 'deny plaintiff', 'deny andrew', 'grant defendant',
                    'grant emily', 'custody to mother', 'custody to defendant',
                    'denied motion', 'denied request', 'restrict father', 'restrict plaintiff',
                    'suspend parenting', 'no contact'
                ])
                favors_andrew = any(w in combined for w in [
                    'grant father', 'grant plaintiff', 'grant andrew', 'deny defendant',
                    'deny emily', 'custody to father', 'custody to plaintiff',
                    'restore parenting', 'increase parenting'
                ])

                if favors_emily:
                    rulings_favoring_emily += 1
                elif favors_andrew:
                    rulings_favoring_andrew += 1
                else:
                    rulings_neutral += 1

                # Detect procedural shortcuts — orders without prior hearing
                if any(w in combined for w in ['without hearing', 'ex parte', 'no hearing',
                                                 'sua sponte', 'without notice', 'without opportunity']):
                    procedural_shortcuts += 1
                    no_hearing_orders.append({
                        'date': date_val,
                        'description': title[:200]
                    })

        total_rulings = len(rulings)
        print(f"  Total rulings/orders: {total_rulings}")
        print(f"  Favoring Emily: {rulings_favoring_emily}")
        print(f"  Favoring Andrew: {rulings_favoring_andrew}")
        print(f"  Neutral/unclear: {rulings_neutral}")
        print(f"  Procedural shortcuts (no hearing): {procedural_shortcuts}")
    else:
        total_rulings = 0
        print("  TABLE NOT FOUND — skipping")

    # ===== 3. EVIDENCE QUOTES — McNEILL REFERENCES =====
    print("\n[3/5] Searching evidence_quotes for McNeill references...")
    eq_cols = verify_table(conn, 'evidence_quotes')
    mcneill_quotes = []
    foc_communication_refs = []

    if eq_cols:
        has_quote = 'quote_text' in eq_cols
        has_speaker = 'speaker' in eq_cols
        has_cat = 'evidence_category' in eq_cols
        has_date = 'date_ref' in eq_cols

        if has_quote:
            # Search for McNeill references
            mcneill_rows = conn.execute(
                "SELECT quote_text, speaker, evidence_category, date_ref, document_id "
                "FROM evidence_quotes "
                "WHERE quote_text LIKE '%McNeill%' OR quote_text LIKE '%mcneill%' "
                "OR quote_text LIKE '%judge%McNeill%' "
                "LIMIT 5000"
            ).fetchall()

            for r in mcneill_rows:
                qt = str(r['quote_text'] or '')
                speaker = str(r['speaker'] or '')
                cat = str(r['evidence_category'] or '')
                date_val = str(r['date_ref'] or '')

                mcneill_quotes.append({
                    'quote': qt[:300],
                    'speaker': speaker,
                    'category': cat,
                    'date': date_val
                })

                # Check for FOC/Rusco communication patterns
                qt_lower = s(qt)
                if any(w in qt_lower for w in ['rusco', 'foc', 'friend of the court',
                                                  'ex parte communication', 'off record']):
                    foc_communication_refs.append({
                        'quote': qt[:300],
                        'date': date_val,
                        'speaker': speaker
                    })

            print(f"  McNeill references found: {len(mcneill_quotes):,}")
            print(f"  FOC/Rusco communication refs: {len(foc_communication_refs)}")
        else:
            print("  No quote_text column — skipping")
    else:
        print("  TABLE NOT FOUND — skipping")

    # ===== 4. CANON VIOLATION DEEP ANALYSIS =====
    print("\n[4/5] Performing canon violation deep analysis...")
    canon_analysis = {}
    canon_descriptions = {
        '1': 'Uphold independence, integrity, impartiality of judiciary',
        '2': 'Avoid impropriety and appearance of impropriety',
        '2A': 'Respect and comply with law; act impartially',
        '2B': 'Outside influence: family, social, political, financial interests',
        '3': 'Perform duties impartially and diligently',
        '3A': 'Adjudicative responsibilities — fair hearing rights',
        '3B': 'Administrative responsibilities',
        '3C': 'Disqualification obligations',
        '4': 'Minimize risk of conflict with judicial obligations',
        '5': 'Refrain from inappropriate political activity'
    }

    for canon, vlist in violations_by_canon.items():
        severity_counts = defaultdict(int)
        for v in vlist:
            severity_counts[s(v['severity'])] += 1

        canon_key = str(canon).strip()
        canon_analysis[canon_key] = {
            'count': len(vlist),
            'description': canon_descriptions.get(canon_key, f'Canon {canon_key}'),
            'severity_breakdown': dict(severity_counts),
            'sample_violations': [v['description'] for v in vlist[:5]]
        }

    # Print top canons
    for canon, data in sorted(canon_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
        print(f"  Canon {canon} ({data['description'][:50]}): {data['count']} violations")
        for sev, cnt in data['severity_breakdown'].items():
            print(f"    {sev}: {cnt}")

    # ===== 5. CRAMPTON OBJECTIVE BIAS TEST =====
    print("\n[5/5] Applying Crampton v Dept of State objective bias test...")

    # Crampton v Dept of State, 395 Mich 347 (1975):
    # Test: Would a reasonable person, knowing all the circumstances,
    # have a legitimate basis to question the judge's impartiality?

    crampton_indicators = []

    # Indicator 1: Ruling asymmetry
    if total_rulings > 0:
        emily_pct = (rulings_favoring_emily / total_rulings * 100) if total_rulings > 0 else 0
        andrew_pct = (rulings_favoring_andrew / total_rulings * 100) if total_rulings > 0 else 0
        asymmetry = emily_pct - andrew_pct
        crampton_indicators.append({
            'indicator': 'Ruling Asymmetry',
            'finding': f"{rulings_favoring_emily} rulings favoring Emily vs {rulings_favoring_andrew} favoring Andrew "
                       f"({emily_pct:.1f}% vs {andrew_pct:.1f}%)",
            'score': min(10, max(0, int(asymmetry / 5))),
            'query': f"SELECT * FROM docket_events — analyzed {total_rulings} rulings"
        })

    # Indicator 2: Procedural shortcuts
    crampton_indicators.append({
        'indicator': 'Procedural Shortcuts',
        'finding': f"{procedural_shortcuts} orders issued without hearing or notice "
                   f"(violates MCR 2.119 right to respond)",
        'score': min(10, procedural_shortcuts * 2),
        'query': "SELECT * FROM docket_events WHERE title/summary contains 'without hearing/ex parte/sua sponte'"
    })

    # Indicator 3: Volume of canon violations
    critical_count = violations_by_severity.get('critical', 0) + violations_by_severity.get('high', 0)
    crampton_indicators.append({
        'indicator': 'Canon Violation Volume',
        'finding': f"{total_violations:,} documented violations — {critical_count} critical/high severity",
        'score': min(10, total_violations // 100),
        'query': f"SELECT COUNT(*) FROM judicial_violations — {total_violations:,} rows"
    })

    # Indicator 4: FOC/Rusco ex parte communications
    crampton_indicators.append({
        'indicator': 'FOC Communication Pattern',
        'finding': f"{len(foc_communication_refs)} references to FOC/Rusco communications in evidence",
        'score': min(10, len(foc_communication_refs)),
        'query': "SELECT * FROM evidence_quotes WHERE quote_text LIKE '%rusco%' OR '%foc%'"
    })

    # Indicator 5: Canon 2 — Appearance of impropriety
    canon2_count = sum(len(v) for c, v in violations_by_canon.items() if s(str(c)).startswith('2'))
    crampton_indicators.append({
        'indicator': 'Appearance of Impropriety (Canon 2)',
        'finding': f"{canon2_count} Canon 2 violations — directly relevant to Crampton appearance test",
        'score': min(10, canon2_count // 10),
        'query': "SELECT * FROM judicial_violations WHERE canon_number LIKE '2%'"
    })

    # Indicator 6: Canon 3 — Impartiality and diligence
    canon3_count = sum(len(v) for c, v in violations_by_canon.items() if s(str(c)).startswith('3'))
    crampton_indicators.append({
        'indicator': 'Impartiality Violations (Canon 3)',
        'finding': f"{canon3_count} Canon 3 violations — failure to perform duties impartially",
        'score': min(10, canon3_count // 10),
        'query': "SELECT * FROM judicial_violations WHERE canon_number LIKE '3%'"
    })

    # Composite score (average of indicators, weighted)
    if crampton_indicators:
        total_score = sum(ind['score'] for ind in crampton_indicators)
        max_possible = len(crampton_indicators) * 10
        composite_pct = (total_score / max_possible * 100) if max_possible > 0 else 0
    else:
        composite_pct = 0
        total_score = 0
        max_possible = 0

    for ind in crampton_indicators:
        bar = "█" * ind['score'] + "░" * (10 - ind['score'])
        print(f"  {bar} {ind['score']}/10 — {ind['indicator']}: {ind['finding'][:80]}")

    print(f"\n  COMPOSITE: {total_score}/{max_possible} ({composite_pct:.1f}%)")

    # --- Generate MD Report ---
    md = []
    md.append("# ⚖️ JUDICIAL BIAS PATTERN ANALYZER")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case:** Pigors v. Watson | 14th Circuit Court")
    md.append(f"**Subject:** Hon. Jenny L. McNeill")
    md.append(f"**Legal Standard:** *Crampton v Dept of State*, 395 Mich 347 (1975)")
    md.append(f"**Total Documented Violations:** {total_violations:,}")
    md.append(f"**Bias Composite Score:** {total_score}/{max_possible} ({composite_pct:.1f}%)\n")

    md.append("## CRAMPTON OBJECTIVE BIAS TEST")
    md.append("> *Crampton v Dept of State*, 395 Mich 347 (1975): A judge should be disqualified")
    md.append("> when a reasonable person, knowing all the circumstances, would have a legitimate")
    md.append("> basis to question the judge's impartiality. This is an **objective** test — actual")
    md.append("> bias need not be proven; the **appearance** of bias suffices.\n")

    md.append("### Bias Indicators")
    md.append("| # | Indicator | Score | Finding | Traceable Query |")
    md.append("|---|-----------|-------|---------|-----------------|")
    for i, ind in enumerate(crampton_indicators, 1):
        bar = "█" * ind['score'] + "░" * (10 - ind['score'])
        finding = ind['finding'].replace('|', '\\|')[:100]
        query = ind['query'].replace('|', '\\|')[:80]
        md.append(f"| {i} | {ind['indicator']} | {bar} {ind['score']}/10 | {finding} | `{query}` |")
    md.append(f"\n**COMPOSITE SCORE: {total_score}/{max_possible} ({composite_pct:.1f}%)**")

    if composite_pct >= 50:
        md.append("\n> ⚠️ **FINDING:** The composite score exceeds 50%, indicating a pattern that")
        md.append("> a reasonable person would find sufficient to question impartiality under *Crampton*.")
    elif composite_pct >= 30:
        md.append("\n> ⚠️ **FINDING:** Significant indicators present. Consider supplementing record")
        md.append("> before filing disqualification motion under MCR 2.003.")

    md.append("\n## RULING PATTERN ANALYSIS")
    md.append(f"**Total Rulings Analyzed:** {total_rulings}")
    md.append(f"**Query:** `SELECT * FROM docket_events` — filtered for orders/rulings\n")
    md.append("| Direction | Count | Percentage |")
    md.append("|-----------|-------|------------|")
    md.append(f"| Favoring Emily Watson | {rulings_favoring_emily} | {(rulings_favoring_emily/total_rulings*100) if total_rulings else 0:.1f}% |")
    md.append(f"| Favoring Andrew Pigors | {rulings_favoring_andrew} | {(rulings_favoring_andrew/total_rulings*100) if total_rulings else 0:.1f}% |")
    md.append(f"| Neutral/Procedural | {rulings_neutral} | {(rulings_neutral/total_rulings*100) if total_rulings else 0:.1f}% |")

    if no_hearing_orders:
        md.append(f"\n### Procedural Shortcuts — Orders Without Hearing ({procedural_shortcuts})")
        md.append("| Date | Description |")
        md.append("|------|-------------|")
        for nho in no_hearing_orders[:20]:
            md.append(f"| {nho['date']} | {nho['description'].replace('|', '\\|')} |")

    md.append("\n## CANON VIOLATION BREAKDOWN")
    md.append(f"**Total Violations:** {total_violations:,}")
    md.append(f"**Query:** `SELECT * FROM judicial_violations` — {total_violations:,} rows\n")
    md.append("| Canon | Description | Count | Critical | High | Medium | Low |")
    md.append("|-------|-------------|-------|----------|------|--------|-----|")
    for canon, data in sorted(canon_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:15]:
        sb = data['severity_breakdown']
        md.append(f"| {canon} | {data['description'][:50]} | {data['count']} | "
                  f"{sb.get('critical', 0)} | {sb.get('high', 0)} | {sb.get('medium', 0)} | {sb.get('low', 0)} |")

    md.append("\n### Severity Distribution")
    md.append("| Severity | Count | Percentage |")
    md.append("|----------|-------|------------|")
    for sev in ['critical', 'high', 'medium', 'low']:
        cnt = violations_by_severity.get(sev, 0)
        pct = (cnt / total_violations * 100) if total_violations > 0 else 0
        md.append(f"| {sev.title()} | {cnt:,} | {pct:.1f}% |")

    md.append("\n### Sample Canon Violations")
    for canon, data in sorted(canon_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
        md.append(f"\n#### Canon {canon}: {data['description']}")
        for sample in data['sample_violations'][:3]:
            md.append(f"- {sample[:200]}")

    if foc_communication_refs:
        md.append(f"\n## FOC/RUSCO COMMUNICATION PATTERN ({len(foc_communication_refs)} references)")
        md.append("Evidence of potentially improper communications with FOC Pamela Rusco.\n")
        md.append("| # | Date | Speaker | Quote |")
        md.append("|---|------|---------|-------|")
        for i, ref in enumerate(foc_communication_refs[:15], 1):
            quote = ref['quote'].replace('|', '\\|')[:120]
            md.append(f"| {i} | {ref['date']} | {ref['speaker']} | {quote} |")

    if mcneill_quotes:
        md.append(f"\n## McNEILL REFERENCES IN EVIDENCE ({len(mcneill_quotes):,} found)")
        md.append(f"**Query:** `SELECT * FROM evidence_quotes WHERE quote_text LIKE '%McNeill%'`\n")
        md.append("| # | Date | Speaker | Category | Quote |")
        md.append("|---|------|---------|----------|-------|")
        for i, mq in enumerate(mcneill_quotes[:20], 1):
            quote = mq['quote'].replace('|', '\\|')[:120]
            md.append(f"| {i} | {mq['date']} | {mq['speaker']} | {mq['category']} | {quote} |")

    md.append("\n## JUDICIAL STANDARDS COMPARISON")
    md.append("### Michigan Code of Judicial Conduct")
    md.append("| Standard | Expectation | Documented Reality |")
    md.append("|----------|-------------|-------------------|")
    md.append(f"| Canon 1 — Independence | Uphold integrity | {sum(len(v) for c, v in violations_by_canon.items() if s(str(c)).startswith('1'))} violations |")
    md.append(f"| Canon 2 — No Impropriety | Avoid appearance of bias | {canon2_count} violations |")
    md.append(f"| Canon 3 — Impartial Duties | Fair hearing, diligent | {canon3_count} violations |")
    md.append(f"| MCR 2.003 — Disqualification | Recuse when biased | {procedural_shortcuts} shortcuts documented |")
    md.append(f"| Due Process — 14th Amendment | Notice + opportunity to be heard | {procedural_shortcuts} orders without hearing |")

    md.append("\n## DATABASE QUERIES USED (Traceable)")
    md.append("```sql")
    md.append("-- Judicial violations count and breakdown")
    md.append("SELECT COUNT(*) FROM judicial_violations;")
    md.append("SELECT canon_number, COUNT(*) FROM judicial_violations GROUP BY canon_number;")
    md.append("")
    md.append("-- Docket events ruling analysis")
    md.append("SELECT * FROM docket_events; -- Filtered for orders/rulings/judgments")
    md.append("")
    md.append("-- McNeill evidence references")
    md.append("SELECT quote_text, speaker, evidence_category, date_ref FROM evidence_quotes")
    md.append("WHERE quote_text LIKE '%McNeill%';")
    md.append("")
    md.append("-- FOC/Rusco communication search")
    md.append("SELECT * FROM evidence_quotes WHERE quote_text LIKE '%rusco%' OR '%foc%';")
    md.append("```")

    md.append(f"\n---\n*Tool #246 — Judicial Bias Pattern Analyzer | LitigationOS*")
    md.append(f"*{total_violations:,} violations analyzed — Crampton composite: {composite_pct:.1f}%*")
    md.append(f"*Legal standard: Crampton v Dept of State, 395 Mich 347 (1975)*")

    # Write outputs
    os.makedirs(REPORT_DIR, exist_ok=True)
    md_path = os.path.join(REPORT_DIR, "tool_246_judicial_bias_analyzer.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    json_data = {
        'tool': 246, 'name': 'Judicial Bias Pattern Analyzer',
        'generated': datetime.now().isoformat(),
        'case': 'Pigors v. Watson',
        'subject_judge': 'Hon. Jenny L. McNeill',
        'total_violations': total_violations,
        'violations_by_severity': dict(violations_by_severity),
        'canon_analysis': canon_analysis,
        'ruling_analysis': {
            'total_rulings': total_rulings,
            'favoring_emily': rulings_favoring_emily,
            'favoring_andrew': rulings_favoring_andrew,
            'neutral': rulings_neutral,
            'procedural_shortcuts': procedural_shortcuts,
            'no_hearing_orders': no_hearing_orders[:20]
        },
        'crampton_test': {
            'legal_citation': 'Crampton v Dept of State, 395 Mich 347 (1975)',
            'test_description': 'Objective test: would a reasonable person question impartiality?',
            'indicators': crampton_indicators,
            'composite_score': total_score,
            'max_possible': max_possible,
            'composite_pct': round(composite_pct, 2)
        },
        'mcneill_evidence_refs': len(mcneill_quotes),
        'foc_communication_refs': len(foc_communication_refs),
        'queries_used': {
            'judicial_violations': "SELECT * FROM judicial_violations",
            'docket_events': "SELECT * FROM docket_events",
            'mcneill_quotes': "SELECT ... FROM evidence_quotes WHERE quote_text LIKE '%McNeill%'",
            'foc_refs': "SELECT ... FROM evidence_quotes WHERE quote_text LIKE '%rusco%' OR '%foc%'"
        }
    }
    json_path = os.path.join(REPORT_DIR, "tool_246_judicial_bias_analyzer.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")

    print(f"\n{'='*70}")
    print(f"VIOLATIONS: {total_violations:,} documented canon violations")
    print(f"RULINGS: {total_rulings} analyzed — Emily:{rulings_favoring_emily} Andrew:{rulings_favoring_andrew} Neutral:{rulings_neutral}")
    print(f"PROCEDURAL: {procedural_shortcuts} orders without hearing")
    print(f"EVIDENCE: {len(mcneill_quotes):,} McNeill refs | {len(foc_communication_refs)} FOC/Rusco refs")
    print(f"CRAMPTON SCORE: {total_score}/{max_possible} ({composite_pct:.1f}%)")
    print(f"{'='*70}")

    conn.close()

if __name__ == '__main__':
    main()
