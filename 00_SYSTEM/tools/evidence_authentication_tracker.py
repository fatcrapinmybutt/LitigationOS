#!/usr/bin/env python3
"""
Tool #245 — Evidence Authentication Tracker
Track authentication status of all evidence. Query documents table for file inventory,
check SHA-256 hashes, categorize by evidence type, flag items needing affidavits,
business records certifications (MRE 803(6)), or chain of custody documentation.

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

def classify_evidence_type(file_name, file_path, category_hint=None):
    """Classify document into evidence type based on filename and path."""
    fn = s(file_name)
    fp = s(file_path)
    ch = s(category_hint)
    combined = f"{fn} {fp} {ch}"

    if any(w in combined for w in ['text_message', 'sms', 'imessage', 'chat', 'messenger', 'whatsapp']):
        return 'text_message'
    if any(w in combined for w in ['email', 'gmail', 'outlook', 'inbox', 'sent_mail', '.eml']):
        return 'email'
    if any(w in combined for w in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', 'photo', 'image', 'screenshot']):
        return 'photo'
    if any(w in combined for w in ['.mp4', '.avi', '.mov', '.mkv', 'video', 'recording', '.wmv']):
        return 'video'
    if any(w in combined for w in ['.mp3', '.wav', '.m4a', 'audio', 'voicemail', 'call_recording', '.ogg']):
        return 'audio'
    if any(w in combined for w in ['court', 'order', 'ruling', 'judgment', 'docket', 'motion', 'petition', 'brief']):
        return 'court_record'
    if any(w in combined for w in ['medical', 'health', 'hospital', 'diagnosis', 'therapy', 'prescription', 'doctor']):
        return 'medical_record'
    if any(w in combined for w in ['financial', 'bank', 'tax', 'income', 'pay_stub', 'w2', '1099']):
        return 'financial_record'
    if any(w in combined for w in ['police', 'incident', 'arrest', 'cps', 'dhhs', 'investigation']):
        return 'government_record'
    if any(w in combined for w in ['.pdf']):
        return 'pdf_document'
    if any(w in combined for w in ['.docx', '.doc']):
        return 'word_document'
    return 'other'

def get_authentication_requirements(evidence_type):
    """Determine authentication requirements per Michigan Rules of Evidence."""
    requirements = {
        'text_message': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(1) testimony of knowledge; screenshot + device identification needed'
        },
        'email': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(4) distinctive characteristics; header metadata + account ownership'
        },
        'photo': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(1) fair and accurate representation; EXIF metadata preservation'
        },
        'video': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(1) + (b)(9) process/system authentication; unedited original required'
        },
        'audio': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(5) voice identification; MI one-party consent applies (MCL 750.539c)'
        },
        'court_record': {
            'affidavit': False,
            'business_records_803_6': False,
            'chain_of_custody': False,
            'notes': 'MRE 902(4) certified copy of public record; self-authenticating if certified'
        },
        'medical_record': {
            'affidavit': False,
            'business_records_803_6': True,
            'chain_of_custody': True,
            'notes': 'MRE 803(6) business records exception; custodian affidavit or MRE 902(11) certification'
        },
        'financial_record': {
            'affidavit': False,
            'business_records_803_6': True,
            'chain_of_custody': True,
            'notes': 'MRE 803(6) business records; bank/employer certification needed'
        },
        'government_record': {
            'affidavit': False,
            'business_records_803_6': True,
            'chain_of_custody': False,
            'notes': 'MRE 803(8) public records exception; MRE 902(1)-(4) self-authenticating'
        },
        'pdf_document': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'Authentication depends on content type — identify source for correct rule'
        },
        'word_document': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'MRE 901(b)(1) testimony; metadata preservation important'
        },
        'other': {
            'affidavit': True,
            'business_records_803_6': False,
            'chain_of_custody': True,
            'notes': 'Default: sworn affidavit + chain of custody recommended'
        }
    }
    return requirements.get(evidence_type, requirements['other'])

def main():
    print("=" * 70)
    print("TOOL #245 — EVIDENCE AUTHENTICATION TRACKER")
    print("Pigors v. Watson | LitigationOS")
    print("=" * 70)

    if not os.path.exists(DB):
        print(f"ERROR: Database not found at {DB}")
        return

    conn = get_conn()

    # Verify documents table
    print("\n[1/4] Verifying documents table schema...")
    cols = verify_table(conn, 'documents')
    if not cols:
        print("  FATAL: documents table not found")
        conn.close()
        return
    print(f"  Columns: {cols}")

    has_hash = 'sha256_hash' in cols
    has_filename = 'file_name' in cols
    has_filepath = 'file_path' in cols
    has_size = 'file_size_bytes' in cols
    has_category = 'evidence_category' in cols or 'category' in cols
    cat_col = 'evidence_category' if 'evidence_category' in cols else 'category' if 'category' in cols else None

    # Get counts efficiently
    print("\n[2/4] Querying document inventory...")
    total_docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    print(f"  Total documents: {total_docs:,}")

    if has_hash:
        hash_stats = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM documents WHERE sha256_hash IS NOT NULL AND sha256_hash != '') AS has_hash,
                (SELECT COUNT(*) FROM documents WHERE sha256_hash IS NULL OR sha256_hash = '') AS no_hash
        """).fetchone()
        authenticated_count = hash_stats['has_hash']
        pending_count = hash_stats['no_hash']
    else:
        authenticated_count = 0
        pending_count = total_docs

    print(f"  With SHA-256 hash: {authenticated_count:,}")
    print(f"  Without hash (pending): {pending_count:,}")

    # Classify all documents by type
    print("\n[3/4] Classifying evidence by type...")
    select_cols = []
    if has_filename:
        select_cols.append('file_name')
    if has_filepath:
        select_cols.append('file_path')
    if has_hash:
        select_cols.append('sha256_hash')
    if has_size:
        select_cols.append('file_size_bytes')
    if cat_col:
        select_cols.append(cat_col)

    if not select_cols:
        print("  FATAL: No usable columns in documents table")
        conn.close()
        return

    query = f"SELECT {', '.join(select_cols)} FROM documents"
    rows = conn.execute(query).fetchall()

    type_stats = defaultdict(lambda: {'total': 0, 'authenticated': 0, 'pending': 0,
                                       'total_size_bytes': 0})
    needs_affidavit = []
    needs_803_6 = []
    needs_chain_custody = []

    for r in rows:
        fn = str(r['file_name'] if has_filename else '') or ''
        fp = str(r['file_path'] if has_filepath else '') or ''
        ch = str(r[cat_col] if cat_col else '') or ''
        has_h = bool(r['sha256_hash']) if has_hash else False
        size = r['file_size_bytes'] if has_size else 0

        etype = classify_evidence_type(fn, fp, ch)
        type_stats[etype]['total'] += 1
        type_stats[etype]['total_size_bytes'] += (size or 0)
        if has_h:
            type_stats[etype]['authenticated'] += 1
        else:
            type_stats[etype]['pending'] += 1

        # Check authentication requirements
        reqs = get_authentication_requirements(etype)
        doc_ref = fn[:80] or fp[:80] or 'unknown'
        if reqs['affidavit'] and not has_h:
            needs_affidavit.append(doc_ref)
        if reqs['business_records_803_6']:
            needs_803_6.append(doc_ref)
        if reqs['chain_of_custody'] and not has_h:
            needs_chain_custody.append(doc_ref)

    # Print type breakdown
    for etype, data in sorted(type_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        pct = (data['authenticated'] / data['total'] * 100) if data['total'] > 0 else 0
        size_mb = data['total_size_bytes'] / (1024 * 1024)
        print(f"  {etype:20s}: {data['total']:6,} total | {data['authenticated']:6,} auth ({pct:5.1f}%) | {data['pending']:6,} pending | {size_mb:8.1f} MB")

    # Cross-reference with evidence_quotes for linked evidence
    print("\n[4/4] Cross-referencing with evidence_quotes...")
    eq_cols = verify_table(conn, 'evidence_quotes')
    linked_evidence = 0
    if eq_cols and 'document_id' in eq_cols:
        linked_evidence = conn.execute(
            "SELECT COUNT(DISTINCT document_id) FROM evidence_quotes WHERE document_id IS NOT NULL"
        ).fetchone()[0]
        print(f"  Documents with extracted quotes: {linked_evidence:,}")

    # --- Generate MD Report ---
    md = []
    md.append("# 🔐 EVIDENCE AUTHENTICATION TRACKER")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case:** Pigors v. Watson | 14th Circuit Court")
    md.append(f"**Total Documents:** {total_docs:,}")
    md.append(f"**Authenticated (SHA-256):** {authenticated_count:,} ({(authenticated_count/total_docs*100) if total_docs else 0:.1f}%)")
    md.append(f"**Pending Authentication:** {pending_count:,}\n")

    md.append("## AUTHENTICATION READINESS MATRIX")
    md.append("| Evidence Type | Total | Authenticated | Pending | Auth Rate | Size (MB) | Needs Affidavit | Needs 803(6) | Needs CoC |")
    md.append("|---------------|-------|---------------|---------|-----------|-----------|-----------------|--------------|-----------|")
    overall_auth = 0
    overall_total = 0
    for etype in sorted(type_stats.keys(), key=lambda x: type_stats[x]['total'], reverse=True):
        data = type_stats[etype]
        reqs = get_authentication_requirements(etype)
        pct = (data['authenticated'] / data['total'] * 100) if data['total'] > 0 else 0
        size_mb = data['total_size_bytes'] / (1024 * 1024)
        aff = "✅ Required" if reqs['affidavit'] else "—"
        biz = "✅ Required" if reqs['business_records_803_6'] else "—"
        coc = "✅ Required" if reqs['chain_of_custody'] else "—"
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        md.append(f"| {etype} | {data['total']:,} | {data['authenticated']:,} | {data['pending']:,} | {bar} {pct:.1f}% | {size_mb:,.1f} | {aff} | {biz} | {coc} |")
        overall_auth += data['authenticated']
        overall_total += data['total']
    overall_pct = (overall_auth / overall_total * 100) if overall_total else 0
    md.append(f"| **TOTAL** | **{overall_total:,}** | **{overall_auth:,}** | **{overall_total - overall_auth:,}** | **{overall_pct:.1f}%** | | | | |")

    md.append("\n## AUTHENTICATION REQUIREMENTS BY TYPE")
    md.append("### Michigan Rules of Evidence (MRE) Reference")
    for etype in sorted(type_stats.keys()):
        reqs = get_authentication_requirements(etype)
        count = type_stats[etype]['total']
        md.append(f"\n#### {etype.replace('_', ' ').title()} ({count:,} documents)")
        md.append(f"- **Sworn Affidavit:** {'Required' if reqs['affidavit'] else 'Not required (self-authenticating)'}")
        md.append(f"- **Business Records — MRE 803(6):** {'Required' if reqs['business_records_803_6'] else 'Not applicable'}")
        md.append(f"- **Chain of Custody:** {'Required' if reqs['chain_of_custody'] else 'Not required'}")
        md.append(f"- **Notes:** {reqs['notes']}")

    md.append("\n## ⚠️ ACTION ITEMS — EVIDENCE NEEDING AUTHENTICATION")
    md.append(f"\n### 1. Sworn Affidavit of Authenticity Needed ({len(needs_affidavit):,} documents)")
    md.append("These documents require Andrew's sworn testimony confirming their authenticity.")
    md.append(f"*Showing top 20 of {len(needs_affidavit):,}:*")
    for item in needs_affidavit[:20]:
        md.append(f"- [ ] `{item}`")

    md.append(f"\n### 2. Business Records Certification — MRE 803(6) ({len(needs_803_6):,} documents)")
    md.append("These documents require certification from the records custodian or MRE 902(11) declaration.")
    md.append(f"*Showing top 20 of {len(needs_803_6):,}:*")
    for item in needs_803_6[:20]:
        md.append(f"- [ ] `{item}`")

    md.append(f"\n### 3. Chain of Custody Documentation ({len(needs_chain_custody):,} documents)")
    md.append("These documents need documented chain of custody from creation/receipt to court filing.")
    md.append(f"*Showing top 20 of {len(needs_chain_custody):,}:*")
    for item in needs_chain_custody[:20]:
        md.append(f"- [ ] `{item}`")

    md.append("\n## DATABASE QUERIES USED (Traceable)")
    md.append("```sql")
    md.append("-- Total document count")
    md.append("SELECT COUNT(*) FROM documents;")
    md.append("")
    md.append("-- Hash authentication status")
    md.append("SELECT")
    md.append("  (SELECT COUNT(*) FROM documents WHERE sha256_hash IS NOT NULL AND sha256_hash != '') AS has_hash,")
    md.append("  (SELECT COUNT(*) FROM documents WHERE sha256_hash IS NULL OR sha256_hash = '') AS no_hash;")
    md.append("")
    md.append("-- Full document inventory")
    md.append(f"-- {query}")
    md.append("")
    md.append("-- Cross-referenced evidence quotes")
    md.append("SELECT COUNT(DISTINCT document_id) FROM evidence_quotes WHERE document_id IS NOT NULL;")
    md.append("```")

    md.append(f"\n---\n*Tool #245 — Evidence Authentication Tracker | LitigationOS*")
    md.append(f"*{total_docs:,} documents audited — {authenticated_count:,} authenticated ({overall_pct:.1f}%)*")

    # Write outputs
    os.makedirs(REPORT_DIR, exist_ok=True)
    md_path = os.path.join(REPORT_DIR, "tool_245_evidence_authentication_tracker.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    json_data = {
        'tool': 245, 'name': 'Evidence Authentication Tracker',
        'generated': datetime.now().isoformat(),
        'case': 'Pigors v. Watson',
        'total_documents': total_docs,
        'authenticated_count': authenticated_count,
        'pending_count': pending_count,
        'auth_rate_pct': round(overall_pct, 2),
        'linked_evidence_quotes': linked_evidence,
        'type_breakdown': {k: dict(v) for k, v in type_stats.items()},
        'action_items': {
            'needs_affidavit_count': len(needs_affidavit),
            'needs_803_6_count': len(needs_803_6),
            'needs_chain_custody_count': len(needs_chain_custody)
        },
        'authentication_requirements': {
            etype: get_authentication_requirements(etype) for etype in type_stats.keys()
        },
        'queries_used': {
            'total_count': 'SELECT COUNT(*) FROM documents',
            'hash_status': "SELECT ... WHERE sha256_hash IS NOT NULL / IS NULL",
            'full_inventory': query,
            'evidence_crossref': "SELECT COUNT(DISTINCT document_id) FROM evidence_quotes WHERE document_id IS NOT NULL"
        }
    }
    json_path = os.path.join(REPORT_DIR, "tool_245_evidence_authentication_tracker.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")

    print(f"\n{'='*70}")
    print(f"DOCUMENTS: {total_docs:,} total | {authenticated_count:,} authenticated ({overall_pct:.1f}%)")
    print(f"TYPES: {len(type_stats)} evidence categories detected")
    print(f"ACTION ITEMS: {len(needs_affidavit):,} need affidavit | {len(needs_803_6):,} need 803(6) | {len(needs_chain_custody):,} need CoC")
    print(f"LINKED QUOTES: {linked_evidence:,} documents have extracted evidence quotes")
    print(f"{'='*70}")

    conn.close()

if __name__ == '__main__':
    main()
