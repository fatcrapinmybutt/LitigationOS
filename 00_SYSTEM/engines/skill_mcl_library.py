#!/usr/bin/env python3
"""
skill_mcl_library.py — MCL Authority Library Skill
====================================================
Query, search, and analyze Michigan Compiled Laws entries
in the mcl_authority_library table of litigation_context.db.

Usage:
    from skill_mcl_library import MCLLibrary
    lib = MCLLibrary()
    
    # Search by statute number
    result = lib.lookup("722.23")
    
    # Full-text search
    results = lib.search("best interest factors")
    
    # Get all statutes for a filing stack
    results = lib.by_filing_stack("01_COA_FINAL_BRIEF")
    
    # Get cross-referenced statutes
    results = lib.cross_refs("722.23")
    
    # Get application notes for a statute
    notes = lib.application_notes("722.23")
    
    # List all statutes
    all_statutes = lib.list_all()
    
    # Get stats
    stats = lib.stats()
"""
import sys
import sqlite3
import os
import json

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.environ.get(
    'LITIGATION_DB',
    r'C:\Users\andre\LitigationOS\litigation_context.db'
)


class MCLLibrary:
    """Query interface for the MCL Authority Library."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._conn = None

    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=120)
            self._conn.execute('PRAGMA busy_timeout=60000')
            self._conn.execute('PRAGMA journal_mode=WAL')
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def lookup(self, statute_number):
        """Look up a specific MCL statute by number (e.g., '722.23')."""
        db = self._get_conn()
        row = db.execute(
            "SELECT * FROM mcl_authority_library WHERE statute_number = ?",
            (statute_number,)
        ).fetchone()
        if row:
            return dict(row)
        # Try partial match
        rows = db.execute(
            "SELECT * FROM mcl_authority_library WHERE statute_number LIKE ?",
            (f"%{statute_number}%",)
        ).fetchall()
        return [dict(r) for r in rows]

    def search(self, query, limit=20):
        """Full-text search across MCL authority library."""
        db = self._get_conn()
        try:
            rows = db.execute("""
                SELECT m.*, rank
                FROM mcl_authority_fts f
                JOIN mcl_authority_library m ON f.rowid = m.rowid
                WHERE mcl_authority_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            # Fallback to LIKE search
            rows = db.execute("""
                SELECT * FROM mcl_authority_library
                WHERE title LIKE ? OR summary LIKE ? OR full_text LIKE ?
                   OR application_notes LIKE ? OR full_citation LIKE ?
                LIMIT ?
            """, (f"%{query}%",) * 5 + (limit,)).fetchall()
            return [dict(r) for r in rows]

    def by_filing_stack(self, stack_name):
        """Get all MCL statutes cited in a specific filing stack."""
        db = self._get_conn()
        rows = db.execute(
            "SELECT * FROM mcl_authority_library WHERE filing_stacks LIKE ? ORDER BY statute_number",
            (f"%{stack_name}%",)
        ).fetchall()
        return [dict(r) for r in rows]

    def cross_refs(self, statute_number):
        """Get cross-referenced statutes for a given MCL."""
        db = self._get_conn()
        row = db.execute(
            "SELECT cross_refs FROM mcl_authority_library WHERE statute_number = ?",
            (statute_number,)
        ).fetchone()
        if not row or not row['cross_refs']:
            return []
        refs = [r.strip() for r in row['cross_refs'].split(',')]
        results = []
        for ref in refs:
            num = ref.replace('MCL ', '').replace('MCR ', '').strip()
            match = db.execute(
                "SELECT * FROM mcl_authority_library WHERE statute_number = ?",
                (num,)
            ).fetchone()
            if match:
                results.append(dict(match))
            else:
                results.append({'full_citation': ref, 'status': 'not in library'})
        return results

    def application_notes(self, statute_number):
        """Get application notes for a specific statute."""
        db = self._get_conn()
        row = db.execute(
            "SELECT application_notes, full_citation, title FROM mcl_authority_library WHERE statute_number = ?",
            (statute_number,)
        ).fetchone()
        if row:
            return dict(row)
        return None

    def list_all(self):
        """List all MCL statutes in the library."""
        db = self._get_conn()
        rows = db.execute("""
            SELECT mcl_id, statute_number, full_citation, title, chapter,
                   LENGTH(COALESCE(full_text,'')) as text_len,
                   CASE WHEN application_notes IS NOT NULL THEN 1 ELSE 0 END as has_notes,
                   filing_stacks
            FROM mcl_authority_library
            ORDER BY statute_number
        """).fetchall()
        return [dict(r) for r in rows]

    def stats(self):
        """Get library statistics."""
        db = self._get_conn()
        total = db.execute("SELECT COUNT(*) as c FROM mcl_authority_library").fetchone()['c']
        with_text = db.execute(
            "SELECT COUNT(*) as c FROM mcl_authority_library WHERE full_text IS NOT NULL AND LENGTH(full_text) > 100"
        ).fetchone()['c']
        with_notes = db.execute(
            "SELECT COUNT(*) as c FROM mcl_authority_library WHERE application_notes IS NOT NULL"
        ).fetchone()['c']
        chapters = db.execute(
            "SELECT DISTINCT chapter FROM mcl_authority_library WHERE chapter IS NOT NULL ORDER BY chapter"
        ).fetchall()
        stacks = db.execute(
            "SELECT DISTINCT filing_stacks FROM mcl_authority_library WHERE filing_stacks IS NOT NULL AND filing_stacks != ''"
        ).fetchall()
        return {
            'total_statutes': total,
            'with_full_text': with_text,
            'with_application_notes': with_notes,
            'chapters': [r['chapter'] for r in chapters],
            'filing_stacks_referenced': len(stacks),
        }

    def for_brief(self, filing_stack=None, with_text=False):
        """Get statutes formatted for brief writing.
        
        Args:
            filing_stack: Optional stack name to filter by
            with_text: Include full statute text
        """
        db = self._get_conn()
        if filing_stack:
            rows = db.execute("""
                SELECT * FROM mcl_authority_library
                WHERE filing_stacks LIKE ?
                ORDER BY statute_number
            """, (f"%{filing_stack}%",)).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM mcl_authority_library ORDER BY statute_number"
            ).fetchall()
        
        entries = []
        for r in rows:
            entry = {
                'citation': r['full_citation'],
                'title': r['title'],
                'summary': r['summary'],
                'application': r['application_notes'],
            }
            if with_text and r['full_text']:
                entry['full_text'] = r['full_text']
            entries.append(entry)
        return entries

    def citation_frequency(self, statute_number):
        """Get citation frequency data for a statute from citation_frequency_map."""
        db = self._get_conn()
        rows = db.execute("""
            SELECT citation_normalized, filing_name, occurrence_count
            FROM citation_frequency_map
            WHERE citation_normalized = ?
            ORDER BY occurrence_count DESC
        """, (f"MCL {statute_number}",)).fetchall()
        return [dict(r) for r in rows]

    def evidence_quotes(self, statute_number, limit=20):
        """Get evidence quotes citing this statute."""
        db = self._get_conn()
        rows = db.execute("""
            SELECT eq.quote_text, eq.date_ref, eq.legal_significance, eq.source_type
            FROM evidence_quotes eq
            JOIN extracted_citations ec ON ec.source_id = CAST(eq.id AS TEXT)
            WHERE ec.citation_type = 'MCL'
              AND ec.normalized LIKE ?
            LIMIT ?
        """, (f"MCL {statute_number}%", limit)).fetchall()
        return [dict(r) for r in rows]


# CLI interface
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='MCL Authority Library')
    parser.add_argument('command', choices=['lookup', 'search', 'stack', 'xrefs', 'notes', 'list', 'stats', 'brief'],
                       help='Command to execute')
    parser.add_argument('query', nargs='?', default=None, help='Statute number or search query')
    parser.add_argument('--limit', type=int, default=20, help='Max results')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    lib = MCLLibrary()

    if args.command == 'lookup':
        result = lib.lookup(args.query)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        elif isinstance(result, dict):
            for k, v in result.items():
                if k == 'full_text' and v and len(str(v)) > 500:
                    print(f"  {k}: [{len(str(v))} chars]")
                else:
                    print(f"  {k}: {v}")
        elif isinstance(result, list):
            for r in result:
                print(f"  {r.get('full_citation', '?')} — {r.get('title', '?')}")
        else:
            print("Not found")

    elif args.command == 'search':
        results = lib.search(args.query, limit=args.limit)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            for r in results:
                print(f"  {r.get('full_citation', '?')} — {r.get('title', '?')}")

    elif args.command == 'stack':
        results = lib.by_filing_stack(args.query)
        for r in results:
            print(f"  {r.get('full_citation', '?')} — {r.get('title', '?')}")

    elif args.command == 'xrefs':
        results = lib.cross_refs(args.query)
        for r in results:
            print(f"  {r.get('full_citation', '?')} — {r.get('title', r.get('status', '?'))}")

    elif args.command == 'notes':
        result = lib.application_notes(args.query)
        if result:
            print(f"  {result['full_citation']} — {result['title']}")
            print(f"  Notes: {result['application_notes']}")
        else:
            print("Not found")

    elif args.command == 'list':
        results = lib.list_all()
        for r in results:
            notes = "✅" if r['has_notes'] else "❌"
            print(f"  {r['full_citation']:<20} {r['title'] or 'N/A':<50} text={r['text_len']:>6} notes={notes}")

    elif args.command == 'stats':
        s = lib.stats()
        if args.json:
            print(json.dumps(s, indent=2))
        else:
            for k, v in s.items():
                print(f"  {k}: {v}")

    elif args.command == 'brief':
        results = lib.for_brief(filing_stack=args.query)
        for r in results:
            print(f"\n  {r['citation']} — {r['title']}")
            if r['summary']:
                print(f"    Summary: {r['summary'][:200]}")
            if r['application']:
                print(f"    Application: {r['application'][:200]}")

    lib.close()
