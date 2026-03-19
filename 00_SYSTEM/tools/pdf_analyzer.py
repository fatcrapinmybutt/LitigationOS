"""
PDF Deep Analyzer for LitigationOS
===================================
Inventories, extracts, and analyzes PDFs across litigation directories.

Extracts:
- Full text content (page-by-page)
- Legal citations (MCR, MCL, MRE, case law, reporter cites)
- Evidence references (dates, dollar amounts, party names)
- Page counts and document metadata

Usage:
    python pdf_analyzer.py --inventory          Show all PDFs and DB status
    python pdf_analyzer.py --batch [limit]      Process unprocessed PDFs
    python pdf_analyzer.py --stats              Show processing statistics
    python pdf_analyzer.py <path.pdf>           Analyze a single PDF
"""

import os
import sys
import re
import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime

# PDF engine selection — prefer PyMuPDF for speed
try:
    import fitz  # PyMuPDF
    PDF_ENGINE = 'pymupdf'
except ImportError:
    try:
        import PyPDF2
        PDF_ENGINE = 'pypdf2'
    except ImportError:
        PDF_ENGINE = None

DB_PATH = r'C:\Users\andre\litigation_context.db'
SCAN_DIRS = [
    r'C:\Users\andre\Scans\discovery',
    r'C:\Users\andre\LitigationOS',
    r'I:\\',  # Drive FRED - litigation content
]


class PDFAnalyzer:
    """Core PDF analysis engine for LitigationOS."""

    def __init__(self, db_path=DB_PATH):
        if PDF_ENGINE is None:
            print("ERROR: No PDF library available. Install PyMuPDF: pip install PyMuPDF")
            sys.exit(1)
        self.db = sqlite3.connect(db_path, timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.row_factory = sqlite3.Row
        self._stats = {
            'processed': 0, 'errors': 0,
            'total_pages': 0, 'total_citations': 0, 'total_evidence': 0
        }

    def close(self):
        self.db.close()

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------
    def inventory(self):
        """Find all PDFs on disk and compare against DB."""
        all_pdfs = []
        for scan_dir in SCAN_DIRS:
            if not os.path.isdir(scan_dir):
                print(f"  WARN: directory not found: {scan_dir}")
                continue
            for root, _dirs, files in os.walk(scan_dir):
                for fname in files:
                    if fname.lower().endswith('.pdf'):
                        full_path = os.path.join(root, fname)
                        try:
                            size = os.path.getsize(full_path)
                        except OSError:
                            size = 0
                        all_pdfs.append({
                            'path': full_path,
                            'name': fname,
                            'size': size,
                            'dir': os.path.basename(root),
                        })

        # Check which are already in the DB
        cur = self.db.cursor()
        cur.execute("SELECT file_path FROM documents")
        existing = {row[0] for row in cur.fetchall()}

        # Also normalize paths for comparison (some DB entries may differ)
        existing_norm = {os.path.normpath(p).lower() for p in existing}

        new_pdfs = [
            p for p in all_pdfs
            if os.path.normpath(p['path']).lower() not in existing_norm
        ]
        return all_pdfs, new_pdfs

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------
    def extract_text(self, pdf_path):
        """Extract text page-by-page using the best available engine."""
        if PDF_ENGINE == 'pymupdf':
            return self._extract_pymupdf(pdf_path)
        elif PDF_ENGINE == 'pypdf2':
            return self._extract_pypdf2(pdf_path)
        return None

    def _extract_pymupdf(self, pdf_path):
        doc = fitz.open(pdf_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            pages.append({'page': i + 1, 'text': text})
        doc.close()
        return pages

    def _extract_pypdf2(self, pdf_path):
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ''
                pages.append({'page': i + 1, 'text': text})
        return pages

    # ------------------------------------------------------------------
    # Citation extraction
    # ------------------------------------------------------------------
    _CITATION_PATTERNS = [
        # Michigan Court Rules  — MCR 2.003(C)(1)(b)
        ('MCR', re.compile(r'MCR\s*(\d+\.\d+(?:\([A-Za-z0-9]+\))*)')),
        # Michigan Compiled Laws — MCL 722.23(a)
        ('MCL', re.compile(r'MCL\s*(\d+\.\d+[a-z]?(?:\([A-Za-z0-9]+\))*)')),
        # Michigan Rules of Evidence — MRE 801(d)(2)
        ('MRE', re.compile(r'MRE\s*(\d+(?:\([A-Za-z0-9]+\))*)')),
        # Case law — Party v Party
        ('CASE_LAW', re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        )),
        # Reporter citations — 123 Mich App 456, 789 NW2d 101
        ('REPORTER', re.compile(
            r'(\d+)\s+(Mich(?:\s+App)?|NW2d|NW\.?2d|US|F\.\d+d|S\.?\s*Ct\.?)\s+(\d+)'
        )),
    ]

    def extract_citations(self, text):
        """Extract all legal citations from text."""
        citations = []
        for cite_type, pattern in self._CITATION_PATTERNS:
            for m in pattern.finditer(text):
                citations.append({
                    'type': cite_type,
                    'text': m.group(0).strip(),
                    'pos': m.start(),
                })
        return citations

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------
    _DATE_PATTERN = re.compile(
        r'(?:January|February|March|April|May|June|July|August|'
        r'September|October|November|December)\s+\d{1,2},?\s+\d{4}'
    )
    _AMOUNT_PATTERN = re.compile(r'\$[\d,]+(?:\.\d{2})?')
    _PARTY_NAMES = ['Pigors', 'Watson', 'McNeill', 'Tiffany', 'Andrew']

    def extract_evidence(self, text):
        """Extract potential evidence items from text."""
        evidence = []
        for m in self._DATE_PATTERN.finditer(text):
            evidence.append({'type': 'DATE', 'text': m.group(0), 'pos': m.start()})
        for m in self._AMOUNT_PATTERN.finditer(text):
            evidence.append({'type': 'AMOUNT', 'text': m.group(0), 'pos': m.start()})
        for name in self._PARTY_NAMES:
            for m in re.finditer(name, text, re.IGNORECASE):
                evidence.append({'type': 'PARTY', 'text': m.group(0), 'pos': m.start()})
        return evidence

    # ------------------------------------------------------------------
    # Single PDF analysis
    # ------------------------------------------------------------------
    def analyze_pdf(self, pdf_path, insert_to_db=True):
        """Full analysis of a single PDF — extract, parse, store."""
        pages = self.extract_text(pdf_path)
        if not pages:
            return None

        result = {
            'path': pdf_path,
            'name': os.path.basename(pdf_path),
            'page_count': len(pages),
            'total_chars': sum(len(p['text']) for p in pages),
            'citations': [],
            'evidence': [],
            'pages': pages,
        }

        for page in pages:
            txt = page['text']
            for cit in self.extract_citations(txt):
                cit['page'] = page['page']
                result['citations'].append(cit)
            for ev in self.extract_evidence(txt):
                ev['page'] = page['page']
                result['evidence'].append(ev)

        if insert_to_db:
            self._insert_to_db(result, pdf_path)

        return result

    # ------------------------------------------------------------------
    # Database insertion  (matches actual schema)
    # ------------------------------------------------------------------
    def _file_hash(self, path):
        """SHA-256 hash of file contents."""
        h = hashlib.sha256()
        try:
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
        except OSError:
            return None
        return h.hexdigest()

    def _insert_to_db(self, result, pdf_path):
        """Insert analysis results into the litigation DB."""
        cur = self.db.cursor()
        now = datetime.now().isoformat()

        file_size = 0
        try:
            file_size = os.path.getsize(pdf_path)
        except OSError:
            pass

        sha = self._file_hash(pdf_path)

        # Determine evidence_category from path
        ev_cat = self._categorize_path(pdf_path)

        # --- documents table ---
        cur.execute("""
            INSERT OR IGNORE INTO documents
                (file_path, file_name, file_size_bytes, page_count,
                 sha256_hash, ingested_at, evidence_category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pdf_path, result['name'], file_size,
            result['page_count'], sha, now, ev_cat,
        ))

        # Retrieve the document id
        cur.execute("SELECT id FROM documents WHERE file_path = ?", (pdf_path,))
        row = cur.fetchone()
        if row is None:
            self.db.commit()
            return
        doc_id = row[0]

        # --- pages table ---
        for page in result['pages']:
            text = page['text'].strip()
            if text:
                cur.execute("""
                    INSERT OR IGNORE INTO pages (document_id, page_number, text_content)
                    VALUES (?, ?, ?)
                """, (doc_id, page['page'], text))

        # --- master_citations table ---
        directory = os.path.dirname(pdf_path)
        for cit in result['citations']:
            context_snippet = cit['text']
            cur.execute("""
                INSERT INTO master_citations
                    (source_file, directory, cite_type, citation, line_number, context)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pdf_path, directory, cit['type'],
                cit['text'], str(cit['page']), context_snippet,
            ))

        # --- evidence_quotes table (high-value items only) ---
        for ev in result['evidence']:
            if ev['type'] in ('DATE', 'AMOUNT'):
                # Get surrounding context (100 chars around the match)
                page_text = result['pages'][ev['page'] - 1]['text']
                start = max(0, ev['pos'] - 50)
                end = min(len(page_text), ev['pos'] + len(ev['text']) + 50)
                context = page_text[start:end].strip()

                quote_hash = hashlib.md5(
                    (context + str(ev['page'])).encode()
                ).hexdigest()

                cur.execute("""
                    INSERT OR IGNORE INTO evidence_quotes
                        (document_id, page_number, evidence_category,
                         quote_text, quote_hash, quote_type, date_ref,
                         legal_significance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, ev['page'], ev_cat,
                    context, quote_hash, ev['type'],
                    ev['text'] if ev['type'] == 'DATE' else None,
                    f"Extracted {ev['type']}: {ev['text']}",
                    now,
                ))

        self.db.commit()

    @staticmethod
    def _categorize_path(pdf_path):
        """Infer evidence category from file path."""
        lower = pdf_path.lower()
        if 'discovery' in lower:
            return 'discovery'
        if 'court_filing' in lower or 'filing' in lower:
            return 'court_filing'
        if 'evidence' in lower:
            return 'evidence'
        if 'order' in lower:
            return 'court_order'
        if 'motion' in lower:
            return 'motion'
        if 'brief' in lower:
            return 'brief'
        if 'transcript' in lower:
            return 'transcript'
        return 'unclassified'

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------
    def run_batch(self, limit=None):
        """Process all unprocessed PDFs."""
        all_pdfs, new_pdfs = self.inventory()
        already = len(all_pdfs) - len(new_pdfs)

        print("=" * 60)
        print("  LitigationOS PDF Analyzer — Batch Run")
        print("=" * 60)
        print(f"  PDF engine    : {PDF_ENGINE}")
        print(f"  Total on disk : {len(all_pdfs):,}")
        print(f"  Already in DB : {already:,}")
        print(f"  New to process: {len(new_pdfs):,}")
        if limit:
            print(f"  Batch limit   : {limit}")
        print("=" * 60)

        if limit:
            new_pdfs = new_pdfs[:limit]

        results = []
        for i, pdf in enumerate(new_pdfs, 1):
            short = f"{pdf['dir']}/{pdf['name']}"
            if len(short) > 55:
                short = "..." + short[-52:]
            print(f"  [{i:>4}/{len(new_pdfs)}] {short}", end="", flush=True)
            try:
                result = self.analyze_pdf(pdf['path'])
                if result:
                    self._stats['processed'] += 1
                    self._stats['total_pages'] += result['page_count']
                    self._stats['total_citations'] += len(result['citations'])
                    self._stats['total_evidence'] += len(result['evidence'])
                    results.append({
                        'name': result['name'],
                        'pages': result['page_count'],
                        'citations': len(result['citations']),
                        'evidence': len(result['evidence']),
                        'chars': result['total_chars'],
                    })
                    print(f"  OK  {result['page_count']}pp  {len(result['citations'])}cit  {len(result['evidence'])}ev")
                else:
                    self._stats['errors'] += 1
                    print("  SKIP (no text)")
            except Exception as e:
                self._stats['errors'] += 1
                print(f"  ERR: {e}")

        self._print_summary(results, already, len(all_pdfs))
        return results

    def _print_summary(self, results, already_in_db, total_on_disk):
        """Print final batch summary."""
        print()
        print("=" * 60)
        print("  BATCH COMPLETE — Summary")
        print("=" * 60)
        print(f"  PDFs processed this run : {self._stats['processed']:,}")
        print(f"  Errors/skipped          : {self._stats['errors']:,}")
        print(f"  Total pages extracted   : {self._stats['total_pages']:,}")
        print(f"  Total citations found   : {self._stats['total_citations']:,}")
        print(f"  Total evidence items    : {self._stats['total_evidence']:,}")
        print(f"  Now in DB (approx)      : {already_in_db + self._stats['processed']:,}")
        print(f"  Remaining unprocessed   : {total_on_disk - already_in_db - self._stats['processed']:,}")
        print("=" * 60)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def show_stats(self):
        """Show current DB statistics."""
        cur = self.db.cursor()
        cur.execute("SELECT count(*) FROM documents")
        doc_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM documents WHERE file_name LIKE '%.pdf'")
        pdf_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM pages")
        page_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM master_citations")
        cite_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM evidence_quotes")
        ev_count = cur.fetchone()[0]

        print("=" * 60)
        print("  LitigationOS Database Statistics")
        print("=" * 60)
        print(f"  Total documents : {doc_count:,}")
        print(f"  PDF documents   : {pdf_count:,}")
        print(f"  Total pages     : {page_count:,}")
        print(f"  Citations       : {cite_count:,}")
        print(f"  Evidence quotes : {ev_count:,}")

        # Top citation types
        cur.execute("""
            SELECT cite_type, count(*) as cnt
            FROM master_citations
            GROUP BY cite_type ORDER BY cnt DESC LIMIT 10
        """)
        print("\n  Citation breakdown:")
        for row in cur.fetchall():
            print(f"    {row[0]:15s} : {row[1]:,}")

        # Evidence categories
        cur.execute("""
            SELECT evidence_category, count(*) as cnt
            FROM documents WHERE evidence_category IS NOT NULL
            GROUP BY evidence_category ORDER BY cnt DESC
        """)
        print("\n  Document categories:")
        for row in cur.fetchall():
            print(f"    {row[0]:15s} : {row[1]:,}")
        print("=" * 60)


# ======================================================================
# CLI entry point
# ======================================================================
def main():
    analyzer = PDFAnalyzer()
    try:
        if len(sys.argv) < 2:
            print(__doc__)
            return

        cmd = sys.argv[1]

        if cmd == '--inventory':
            all_pdfs, new_pdfs = analyzer.inventory()
            print(f"Total PDFs on disk : {len(all_pdfs):,}")
            print(f"Already in DB      : {len(all_pdfs) - len(new_pdfs):,}")
            print(f"New (unprocessed)  : {len(new_pdfs):,}")
            print()

            # Show size breakdown by directory
            from collections import Counter
            dir_counts = Counter(p['dir'] for p in new_pdfs)
            print("Unprocessed by directory (top 20):")
            for d, c in dir_counts.most_common(20):
                print(f"  {d:40s} {c:>5,} PDFs")

            # Show a sample
            print(f"\nSample unprocessed (first 20):")
            for pdf in new_pdfs[:20]:
                sz = pdf['size']
                sz_str = f"{sz / 1024:.0f}KB" if sz < 1048576 else f"{sz / 1048576:.1f}MB"
                print(f"  {pdf['dir']}/{pdf['name']}  ({sz_str})")

        elif cmd == '--batch':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            analyzer.run_batch(limit=limit)

        elif cmd == '--stats':
            analyzer.show_stats()

        elif os.path.isfile(cmd):
            result = analyzer.analyze_pdf(cmd, insert_to_db=False)
            if result:
                # Print without full page text for readability
                summary = {
                    'name': result['name'],
                    'pages': result['page_count'],
                    'chars': result['total_chars'],
                    'citations': result['citations'],
                    'evidence_count': len(result['evidence']),
                    'evidence_sample': result['evidence'][:20],
                }
                print(json.dumps(summary, indent=2, default=str))
            else:
                print("ERROR: Could not extract text from PDF.")

        else:
            print(f"Unknown command or file not found: {cmd}")
            print(__doc__)

    finally:
        analyzer.close()


if __name__ == '__main__':
    main()
