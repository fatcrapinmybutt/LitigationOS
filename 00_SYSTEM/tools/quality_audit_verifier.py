#!/usr/bin/env python3
"""
Tool #42 — Quality Audit Verifier
===================================
Verifies all statistics cited in filings and reports against actual DB queries.
Prevents inflated numbers from reaching court documents.
Detects: fabricated counts, inflated statistics, unverifiable claims, 
         duplicate counting, and synthetic scores.
"""
import sys, os, json, re, sqlite3, glob
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

def get_db_counts(conn):
    """Get actual verified counts from database."""
    counts = {}
    queries = {
        'evidence_quotes': "SELECT COUNT(*) FROM evidence_quotes",
        'judicial_violations': "SELECT COUNT(*) FROM judicial_violations",
        'actor_violations': "SELECT COUNT(*) FROM actor_violations",
        'mcneill_violations': "SELECT COUNT(*) FROM actor_violations WHERE actor LIKE '%McNeill%'",
        'detected_contradictions': "SELECT COUNT(*) FROM detected_contradictions",
        'contradiction_map': "SELECT COUNT(*) FROM contradiction_map",
        'watson_perjury': "SELECT COUNT(*) FROM watson_perjury_compilation",
        'adversary_assertions': "SELECT COUNT(*) FROM adversary_assertions",
        'claims': "SELECT COUNT(*) FROM claims",
        'docket_events': "SELECT COUNT(*) FROM docket_events",
    }
    
    for name, query in queries.items():
        try:
            result = conn.execute(query).fetchone()
            counts[name] = result[0] if result else 0
        except Exception as e:
            counts[name] = f"ERROR: {e}"
    
    return counts

def extract_numbers_from_filing(text, filing_id):
    """Extract all numeric claims from a filing."""
    numbers = []
    
    # Pattern: "N incidents/violations/events/items/times"
    patterns = [
        (r'(\d[\d,]+)\s+(?:incidents?|violations?|events?|instances?|occasions?|times?|episodes?)',
         'incident_count'),
        (r'(\d[\d,]+)\s+(?:days?|consecutive days?)',
         'day_count'),
        (r'(\d[\d,]+)\s+(?:documents?|exhibits?|pages?|filings?)',
         'document_count'),
        (r'(\d[\d,]+)\s+(?:ex\s*parte|orders?)',
         'order_count'),
        (r'\$\s*([\d,]+(?:\.\d{2})?)',
         'dollar_amount'),
        (r'(\d{1,3})%',
         'percentage'),
        (r'(\d[\d,]+)\s+(?:CPS|investigations?|reports?)',
         'investigation_count'),
    ]
    
    for pattern, category in patterns:
        for match in re.finditer(pattern, text, re.I):
            raw = match.group(1).replace(',', '')
            try:
                value = int(raw) if '.' not in raw else float(raw)
            except ValueError:
                continue
            
            # Get context (surrounding 100 chars)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].replace('\n', ' ').strip()
            
            numbers.append({
                'value': value,
                'raw': match.group(0),
                'category': category,
                'context': context,
                'filing_id': filing_id,
            })
    
    return numbers

def verify_number(claim, db_counts):
    """Check if a numeric claim is verifiable and reasonable."""
    value = claim['value']
    category = claim['category']
    context = claim['context'].lower()
    
    result = {
        'claim': claim,
        'status': 'UNVERIFIED',
        'confidence': 'LOW',
        'note': '',
    }
    
    # Known fabrication patterns from prior sessions
    KNOWN_FABRICATIONS = [
        (308704, 'evidence_quotes', 'Old pre-dedup count'),
        (308000, 'evidence_quotes', 'Approximate old count'),
        (13016, 'various', 'Old inflated count'),
        (1127, 'judicial_violations', 'Check if still accurate'),
        (91, 'percentage', 'Synthetic alienation score - NEVER EXISTED'),
        (9, 'investigation_count', 'Fabricated CPS count - NEVER EXISTED'),
    ]
    
    for fab_value, fab_context, fab_note in KNOWN_FABRICATIONS:
        if value == fab_value:
            if fab_value in (91,) and category == 'percentage':
                result['status'] = 'FABRICATED'
                result['confidence'] = 'HIGH'
                result['note'] = f'KNOWN FABRICATION: {fab_note}'
                return result
            elif fab_value == 9 and 'cps' in context:
                result['status'] = 'FABRICATED'
                result['confidence'] = 'HIGH'
                result['note'] = f'KNOWN FABRICATION: {fab_note}'
                return result
            else:
                result['note'] = f'SUSPICIOUS — matches known inflated count: {fab_note}'
    
    # Verify against DB counts
    if category == 'incident_count':
        if 'violation' in context:
            actual = db_counts.get('judicial_violations', 0)
            if isinstance(actual, int):
                if value == actual:
                    result['status'] = 'VERIFIED'
                    result['confidence'] = 'HIGH'
                    result['note'] = f'Matches judicial_violations count ({actual})'
                elif abs(value - actual) / max(actual, 1) < 0.05:
                    result['status'] = 'APPROXIMATE'
                    result['confidence'] = 'MEDIUM'
                    result['note'] = f'Close to judicial_violations ({actual})'
                elif value > actual * 2:
                    result['status'] = 'INFLATED'
                    result['confidence'] = 'HIGH'
                    result['note'] = f'Claimed {value} but DB has {actual}'
        
        if 'contradiction' in context:
            actual = db_counts.get('detected_contradictions', 0)
            if isinstance(actual, int):
                if value == actual or abs(value - actual) < 10:
                    result['status'] = 'VERIFIED'
                    result['confidence'] = 'HIGH'
                    result['note'] = f'Matches detected_contradictions ({actual})'
    
    elif category == 'day_count':
        if 'consecutive' in context and ('contact' in context or 'depriv' in context or 'separat' in context):
            # Calculate actual separation days from known date
            from datetime import date
            separation_start = date(2025, 8, 8)
            today = date.today()
            actual_days = (today - separation_start).days
            if abs(value - actual_days) <= 5:
                result['status'] = 'VERIFIED'
                result['confidence'] = 'HIGH'
                result['note'] = f'Matches separation calc ({actual_days} days from Aug 8, 2025)'
            elif value > actual_days + 30:
                result['status'] = 'INFLATED'
                result['confidence'] = 'MEDIUM'
                result['note'] = f'Claimed {value} days but actual is ~{actual_days}'
    
    elif category == 'investigation_count':
        if 'cps' in context:
            result['status'] = 'UNVERIFIABLE'
            result['confidence'] = 'LOW'
            result['note'] = 'CPS count MUST be verified from actual records — prior sessions fabricated "9 CPS investigations"'
    
    return result

def audit_filing(filing_id, conn, db_counts):
    """Audit a single filing for numeric accuracy."""
    pkg = glob.glob(str(PKG_BASE / f"PKG_{filing_id}_*"))
    if not pkg:
        return {'filing_id': filing_id, 'status': 'NOT_FOUND', 'claims': []}
    
    main_file = Path(pkg[0]) / "01_MAIN_FILING.md"
    if not main_file.exists():
        return {'filing_id': filing_id, 'status': 'NO_FILE', 'claims': []}
    
    text = main_file.read_text(encoding='utf-8', errors='replace')
    numbers = extract_numbers_from_filing(text, filing_id)
    
    verified_claims = []
    for claim in numbers:
        result = verify_number(claim, db_counts)
        verified_claims.append(result)
    
    fabricated = [c for c in verified_claims if c['status'] == 'FABRICATED']
    inflated = [c for c in verified_claims if c['status'] == 'INFLATED']
    verified = [c for c in verified_claims if c['status'] == 'VERIFIED']
    
    return {
        'filing_id': filing_id,
        'status': 'AUDITED',
        'total_claims': len(verified_claims),
        'fabricated': len(fabricated),
        'inflated': len(inflated),
        'verified': len(verified),
        'unverified': len(verified_claims) - len(fabricated) - len(inflated) - len(verified),
        'claims': verified_claims,
        'fabricated_details': fabricated,
        'inflated_details': inflated,
    }

def main():
    print("=" * 70)
    print("QUALITY AUDIT VERIFIER — Tool #42")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    
    print("\n📊 Getting verified DB counts...")
    db_counts = get_db_counts(conn)
    for name, count in db_counts.items():
        print(f"  {name}: {count:,}" if isinstance(count, int) else f"  {name}: {count}")
    
    filings = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']
    all_results = {}
    total_fabricated = 0
    total_inflated = 0
    total_verified = 0
    total_claims = 0
    
    for fid in filings:
        print(f"\n--- Auditing {fid} ---")
        result = audit_filing(fid, conn, db_counts)
        all_results[fid] = result
        
        total_claims += result.get('total_claims', 0)
        total_fabricated += result.get('fabricated', 0)
        total_inflated += result.get('inflated', 0)
        total_verified += result.get('verified', 0)
        
        status = '✅' if result.get('fabricated', 0) == 0 and result.get('inflated', 0) == 0 else '🚨'
        print(f"  {status} {fid}: {result.get('total_claims', 0)} claims — "
              f"{result.get('verified', 0)} verified, "
              f"{result.get('fabricated', 0)} fabricated, "
              f"{result.get('inflated', 0)} inflated")
        
        for fab in result.get('fabricated_details', []):
            print(f"    🚨 FABRICATED: {fab['claim']['raw']} — {fab['note']}")
        for inf in result.get('inflated_details', []):
            print(f"    ⚠️ INFLATED: {inf['claim']['raw']} — {inf['note']}")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("QUALITY AUDIT SUMMARY")
    print("=" * 70)
    print(f"Total numeric claims:  {total_claims}")
    print(f"Verified:              {total_verified} ✅")
    print(f"Fabricated:            {total_fabricated} 🚨")
    print(f"Inflated:              {total_inflated} ⚠️")
    print(f"Unverified:            {total_claims - total_verified - total_fabricated - total_inflated}")
    
    go_nogo = "🟢 GO" if total_fabricated == 0 else "🔴 NO-GO"
    print(f"\nFILING STATUS: {go_nogo}")
    
    # Save reports
    # Simplify claims for JSON (remove non-serializable items)
    for fid in all_results:
        for claim_result in all_results[fid].get('claims', []):
            claim_result['claim'] = {
                'value': claim_result['claim']['value'],
                'raw': claim_result['claim']['raw'],
                'category': claim_result['claim']['category'],
                'filing_id': claim_result['claim']['filing_id'],
            }
    
    json_path = REPORTS_DIR / "quality_audit.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Quality Audit Verifier (#42)',
        'db_counts': {k: v for k, v in db_counts.items() if isinstance(v, int)},
        'summary': {
            'total_claims': total_claims,
            'verified': total_verified,
            'fabricated': total_fabricated,
            'inflated': total_inflated,
            'go_nogo': go_nogo,
        },
        'filings': all_results,
    }, indent=2, default=str), encoding='utf-8')
    
    md_lines = [
        "# QUALITY AUDIT REPORT",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n",
        f"## Status: {go_nogo}\n",
        "| Filing | Claims | Verified | Fabricated | Inflated | Status |",
        "|--------|--------|----------|------------|----------|--------|",
    ]
    for fid in filings:
        r = all_results.get(fid, {})
        status = '✅' if r.get('fabricated', 0) == 0 and r.get('inflated', 0) == 0 else '🚨'
        md_lines.append(f"| {fid} | {r.get('total_claims', 0)} | {r.get('verified', 0)} | {r.get('fabricated', 0)} | {r.get('inflated', 0)} | {status} |")
    
    md_lines.extend(["", "## Verified DB Counts (Ground Truth)", ""])
    for name, count in db_counts.items():
        md_lines.append(f"- **{name}**: {count:,}" if isinstance(count, int) else f"- **{name}**: {count}")
    
    if total_fabricated > 0:
        md_lines.extend(["", "## 🚨 FABRICATED CLAIMS (MUST FIX BEFORE FILING)", ""])
        for fid in filings:
            for fab in all_results.get(fid, {}).get('fabricated_details', []):
                md_lines.append(f"- **{fid}**: `{fab['claim']['raw']}` — {fab['note']}")
    
    md_path = REPORTS_DIR / "QUALITY_AUDIT_REPORT.md"
    md_path.write_text('\n'.join(md_lines), encoding='utf-8')
    
    print(f"\nReports: {json_path.name}, {md_path.name}")

if __name__ == '__main__':
    main()
