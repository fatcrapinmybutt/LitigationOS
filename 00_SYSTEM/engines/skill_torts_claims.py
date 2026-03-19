#!/usr/bin/env python3
"""
skill_torts_claims.py — Torts & Claims Evidence Skill
Wired to: extracted_harms (26K all adversaries), evidence_quotes (308K), tort_claims (10), claim_evidence_links (5910)
"""
import sys, os, sqlite3, json
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'litigation_context.db')

def _conn():
    c = sqlite3.connect(DB, timeout=120)
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA journal_mode=WAL')
    c.row_factory = sqlite3.Row
    return c

# ── Core Functions ──────────────────────────────────────────────────

def search_evidence(tort_type):
    """Search evidence_quotes by tort type using FTS5."""
    conn = _conn()
    try:
        fts_results = conn.execute(
            "SELECT id, document_id, page_number, evidence_category, quote_text, speaker, date_ref, legal_significance "
            "FROM evidence_quotes WHERE id IN "
            "(SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) LIMIT 100",
            (tort_type,)
        ).fetchall()
    except Exception:
        fts_results = conn.execute(
            "SELECT id, document_id, page_number, evidence_category, quote_text, speaker, date_ref, legal_significance "
            "FROM evidence_quotes WHERE quote_text LIKE ? OR evidence_category LIKE ? OR legal_significance LIKE ? "
            "ORDER BY id DESC LIMIT 100",
            (f'%{tort_type}%', f'%{tort_type}%', f'%{tort_type}%')
        ).fetchall()

    harms = conn.execute(
        "SELECT id, category, subcategory, adversary, description, severity, constitutional_violation "
        "FROM extracted_harms WHERE category LIKE ? OR subcategory LIKE ? OR description LIKE ? "
        "ORDER BY severity DESC LIMIT 100",
        (f'%{tort_type}%', f'%{tort_type}%', f'%{tort_type}%')
    ).fetchall()

    conn.close()
    return {
        'evidence_quotes': [dict(r) for r in fts_results],
        'related_harms': [dict(r) for r in harms]
    }


def build_tort_claim(adversary, tort_type):
    """Build a structured tort claim for adversary + tort type with evidence."""
    conn = _conn()
    harms = conn.execute(
        "SELECT * FROM extracted_harms WHERE adversary LIKE ? AND (category LIKE ? OR subcategory LIKE ? OR description LIKE ?) "
        "ORDER BY severity DESC LIMIT 50",
        (f'%{adversary}%', f'%{tort_type}%', f'%{tort_type}%', f'%{tort_type}%')
    ).fetchall()

    existing = conn.execute(
        "SELECT * FROM tort_claims WHERE (defendant LIKE ? OR defendant='ALL_DEFENDANTS') AND tort_type LIKE ?",
        (f'%{adversary}%', f'%{tort_type}%')
    ).fetchall()

    evidence_links = conn.execute(
        "SELECT * FROM claim_evidence_links WHERE claim_id IN "
        "(SELECT claim_id FROM claims WHERE proposition LIKE ? OR actor LIKE ?) LIMIT 50",
        (f'%{tort_type}%', f'%{adversary}%')
    ).fetchall()

    adv_summary = conn.execute(
        "SELECT * FROM adversary_harm_summary WHERE adversary LIKE ?",
        (f'%{adversary}%',)
    ).fetchone()

    conn.close()
    return {
        'adversary': adversary,
        'tort_type': tort_type,
        'harm_evidence': [dict(r) for r in harms],
        'existing_claims': [dict(r) for r in existing],
        'evidence_links': [dict(r) for r in evidence_links],
        'adversary_profile': dict(adv_summary) if adv_summary else None,
        'harm_count': len(harms)
    }


def get_all_tort_types():
    """Get distinct categories and tort types from the DB."""
    conn = _conn()
    categories = conn.execute(
        "SELECT DISTINCT category, COUNT(*) as cnt FROM extracted_harms GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    tort_types = conn.execute("SELECT DISTINCT tort_type FROM tort_claims").fetchall()
    conn.close()
    return {
        'harm_categories': [dict(r) for r in categories],
        'formal_tort_types': [dict(r) for r in tort_types]
    }


# ── Main ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("TORTS & CLAIMS EVIDENCE SKILL — DB-WIRED")
    print("=" * 70)

    types = get_all_tort_types()
    print(f"\n[TORT TYPES] {len(types['formal_tort_types'])} formal types, {len(types['harm_categories'])} harm categories")
    for t in types['formal_tort_types']:
        print(f"  • {t['tort_type']}")
    print("\n  Top harm categories:")
    for c in types['harm_categories'][:10]:
        print(f"  • {c['category']}: {c['cnt']} entries")

    ev = search_evidence('fraud')
    print(f"\n[EVIDENCE SEARCH: 'fraud'] {len(ev['evidence_quotes'])} quotes, {len(ev['related_harms'])} harms")

    claim = build_tort_claim('Emily Watson', 'IIED')
    print(f"\n[BUILD CLAIM] Emily Watson / IIED: {claim['harm_count']} harms found")

    print("\n✅ Torts & Claims Skill operational")
