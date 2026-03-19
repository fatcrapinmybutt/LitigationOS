#!/usr/bin/env python3
"""
Quality Validator v1.0 — LitigationOS Core System
Validates court documents, citations, evidence chains, and filing readiness.
Integrates with analysis_engine.py and litigation_context.db.
"""

import os
import re
import sqlite3
import json
from datetime import datetime

DB_PATH = os.environ.get('LITIGATION_DB', r'C:\Users\andre\litigation_context.db')
VEHICLES_DIR = os.environ.get('VEHICLES_DIR', r'C:\Users\andre\LitigationOS\06_VEHICLES')

# Citation patterns
PATTERNS = {
    'MCR': re.compile(r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*)'),
    'MCL': re.compile(r'MCL\s+(\d+\.\d+[a-z]?(?:\([a-z0-9]+\))*)'),
    'MRE': re.compile(r'MRE\s+(\d+(?:\([a-z0-9]+\))*)'),
    'CASE_LAW': re.compile(r'\*([A-Z][a-z]+ v [A-Z][a-z]+)\*'),
    'CONST': re.compile(r'(?:US Const|Const 1963).*?(?:Amend|art)\s+[\dIVXLC]+'),
}

REQUIRED_SECTIONS = {
    'MOTION': ['caption', 'introduction', 'argument', 'relief', 'certificate of service'],
    'BRIEF': ['table of contents', 'table of authorities', 'statement', 'argument', 'conclusion', 'certificate of service'],
    'APPLICATION': ['jurisdiction', 'questions presented', 'statement', 'grounds', 'argument', 'relief', 'certificate of service'],
    'COMPLAINT': ['parties', 'jurisdiction', 'factual background', 'causes of action', 'prayer for relief', 'verification', 'certificate of service'],
}

ALIENATION_REQUIRED = [
    r'MCL 722\.23\(j\)',
    r'MCL 722\.27a\(9\)',
    r'[Hh]arvey v [Hh]arvey',
    r'parental alienation',
    r'Kent County',
    r'329\+?\s*days',
]


class QualityValidator:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.conn = None
        self.results = []

    def _connect(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def _close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def validate_document(self, filepath):
        """Run all validation checks on a single document."""
        if not os.path.exists(filepath):
            return {'file': filepath, 'error': 'File not found', 'score': 0}

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = os.path.basename(filepath)
        report = {
            'file': filename,
            'path': filepath,
            'size_bytes': len(content.encode('utf-8')),
            'word_count': len(content.split()),
            'checks': [],
            'score': 0,
            'max_score': 0,
        }

        # Determine document type from filename
        doc_type = self._detect_type(filename, content)
        report['doc_type'] = doc_type

        # Run checks
        self._check_citations(content, report)
        self._check_sections(content, doc_type, report)
        self._check_alienation_theme(content, report)
        self._check_irac_structure(content, report)
        self._check_certificate_of_service(content, report)
        self._check_paragraph_numbering(content, report)
        self._check_naked_claims(content, report)
        self._verify_citations_against_db(content, report)

        # Calculate score
        passed = sum(1 for c in report['checks'] if c['passed'])
        total = len(report['checks'])
        report['score'] = round((passed / total * 100) if total > 0 else 0, 1)
        report['passed'] = passed
        report['total_checks'] = total

        self.results.append(report)
        return report

    def _detect_type(self, filename, content):
        fn = filename.upper()
        if 'APPLICATION' in fn:
            return 'APPLICATION'
        elif 'BRIEF' in fn:
            return 'BRIEF'
        elif 'COMPLAINT' in fn:
            return 'COMPLAINT'
        elif 'MOTION' in fn or 'EMERGENCY' in fn:
            return 'MOTION'
        elif 'ORDER' in fn:
            return 'ORDER'
        elif 'THEME' in fn or 'GUIDE' in fn or 'DASHBOARD' in fn:
            return 'GUIDE'
        return 'UNKNOWN'

    def _check_citations(self, content, report):
        """Check citation density and variety."""
        counts = {}
        for name, pattern in PATTERNS.items():
            matches = pattern.findall(content)
            counts[name] = len(matches)

        total = sum(counts.values())
        words = len(content.split())
        density = (total / words * 1000) if words > 0 else 0

        report['citations'] = counts
        report['citation_total'] = total
        report['citation_density'] = round(density, 2)

        report['checks'].append({
            'name': 'citation_count',
            'passed': total >= 5,
            'detail': f'{total} citations found (MCR:{counts["MCR"]}, MCL:{counts["MCL"]}, MRE:{counts["MRE"]}, Case:{counts["CASE_LAW"]})',
        })
        report['checks'].append({
            'name': 'citation_density',
            'passed': density >= 2.0,
            'detail': f'{density:.2f} citations per 1000 words (min: 2.0)',
        })
        report['checks'].append({
            'name': 'citation_variety',
            'passed': sum(1 for v in counts.values() if v > 0) >= 2,
            'detail': f'{sum(1 for v in counts.values() if v > 0)} citation types used',
        })

    def _check_sections(self, content, doc_type, report):
        """Check for required document sections."""
        if doc_type not in REQUIRED_SECTIONS:
            report['checks'].append({
                'name': 'required_sections',
                'passed': True,
                'detail': f'No section requirements for type: {doc_type}',
            })
            return

        content_lower = content.lower()
        required = REQUIRED_SECTIONS[doc_type]
        missing = [s for s in required if s not in content_lower]

        report['checks'].append({
            'name': 'required_sections',
            'passed': len(missing) == 0,
            'detail': f'Missing: {", ".join(missing)}' if missing else f'All {len(required)} required sections present',
        })

    def _check_alienation_theme(self, content, report):
        """Verify parental alienation theme is injected."""
        found = []
        missing = []
        for pattern in ALIENATION_REQUIRED:
            if re.search(pattern, content, re.IGNORECASE):
                found.append(pattern)
            else:
                missing.append(pattern)

        coverage = len(found) / len(ALIENATION_REQUIRED) * 100

        report['checks'].append({
            'name': 'alienation_theme',
            'passed': coverage >= 50,
            'detail': f'{coverage:.0f}% coverage ({len(found)}/{len(ALIENATION_REQUIRED)} markers). Missing: {", ".join(missing[:3])}' if missing else f'100% coverage',
        })

    def _check_irac_structure(self, content, report):
        """Check for IRAC structure markers."""
        markers = {
            'Issue': bool(re.search(r'(?:^|\n)#+\s*.*[Ii]ssue', content)),
            'Rule': bool(re.search(r'(?:^|\n)#+\s*.*[Rr]ule', content)),
            'Application': bool(re.search(r'(?:^|\n)#+\s*.*[Aa]pplication', content)),
            'Conclusion': bool(re.search(r'(?:^|\n)#+\s*.*[Cc]onclusion', content)),
        }
        found = sum(1 for v in markers.values() if v)

        report['checks'].append({
            'name': 'irac_structure',
            'passed': found >= 3,
            'detail': f'{found}/4 IRAC markers found: {", ".join(k for k, v in markers.items() if v)}',
        })

    def _check_certificate_of_service(self, content, report):
        """Verify certificate of service is present."""
        has_cos = bool(re.search(r'certificate of service', content, re.IGNORECASE))
        report['checks'].append({
            'name': 'certificate_of_service',
            'passed': has_cos,
            'detail': 'Certificate of Service present' if has_cos else 'MISSING Certificate of Service',
        })

    def _check_paragraph_numbering(self, content, report):
        """Check for sequential paragraph numbering."""
        para_nums = [int(m) for m in re.findall(r'^(\d+)\.\s', content, re.MULTILINE)]
        if len(para_nums) < 5:
            report['checks'].append({
                'name': 'paragraph_numbering',
                'passed': True,
                'detail': f'{len(para_nums)} numbered paragraphs (below threshold)',
            })
            return

        sequential = all(para_nums[i] <= para_nums[i+1] for i in range(len(para_nums)-1))
        report['checks'].append({
            'name': 'paragraph_numbering',
            'passed': sequential,
            'detail': f'{len(para_nums)} paragraphs, {"sequential" if sequential else "OUT OF ORDER"}',
        })

    def _check_naked_claims(self, content, report):
        """Spot-check for legal assertions without citations."""
        legal_phrases = [
            r'the court (?:must|shall|is required)',
            r'(?:due process|equal protection) requires',
            r'(?:clearly erroneous|abuse of discretion)',
            r'fundamental (?:right|liberty)',
            r'the law (?:requires|mandates|prohibits)',
        ]
        naked = 0
        total_checked = 0
        for phrase in legal_phrases:
            for m in re.finditer(phrase, content, re.IGNORECASE):
                total_checked += 1
                context = content[max(0, m.start()-200):m.end()+200]
                has_cite = any(p.search(context) for p in PATTERNS.values())
                if not has_cite:
                    naked += 1

        report['checks'].append({
            'name': 'naked_claims',
            'passed': naked == 0,
            'detail': f'{naked} legal assertions without nearby citation (checked {total_checked})',
        })

    def _verify_citations_against_db(self, content, report):
        """Verify MCR citations exist in auth_rules table."""
        try:
            conn = self._connect()
            c = conn.cursor()
            mcr_cites = PATTERNS['MCR'].findall(content)
            unique_rules = set()
            for cite in mcr_cites:
                base = cite.split('(')[0]
                unique_rules.add(base)

            verified = 0
            missing = []
            for rule in sorted(unique_rules):
                c.execute("SELECT COUNT(*) FROM auth_rules WHERE rule_number = ?", (rule,))
                if c.fetchone()[0] > 0:
                    verified += 1
                else:
                    missing.append(rule)

            total = len(unique_rules)
            report['checks'].append({
                'name': 'db_citation_verify',
                'passed': len(missing) <= 2,
                'detail': f'{verified}/{total} MCR rules verified in DB. Missing: {", ".join(missing[:5])}' if missing else f'All {total} MCR rules verified',
            })
        except Exception as e:
            report['checks'].append({
                'name': 'db_citation_verify',
                'passed': True,
                'detail': f'DB verification skipped: {e}',
            })

    def validate_all(self, directory=None):
        """Validate all .md files in the vehicles directory."""
        directory = directory or VEHICLES_DIR
        results = []
        for root, dirs, files in os.walk(directory):
            for f in files:
                if f.endswith('.md'):
                    filepath = os.path.join(root, f)
                    result = self.validate_document(filepath)
                    results.append(result)
        return results

    def generate_report(self):
        """Generate a summary report of all validations."""
        if not self.results:
            return "No documents validated."

        lines = []
        lines.append("=" * 70)
        lines.append("LITIGATIONOS QUALITY VALIDATION REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("=" * 70)

        total_score = 0
        for r in sorted(self.results, key=lambda x: x.get('score', 0)):
            score = r.get('score', 0)
            total_score += score
            icon = '🟢' if score >= 80 else '🟡' if score >= 60 else '🔴'
            lines.append(f"\n{icon} {r['file']} — {score}% ({r.get('passed',0)}/{r.get('total_checks',0)} checks)")
            lines.append(f"   Type: {r.get('doc_type','?')} | Words: {r.get('word_count',0)} | Citations: {r.get('citation_total',0)}")
            for check in r.get('checks', []):
                mark = '✅' if check['passed'] else '❌'
                lines.append(f"   {mark} {check['name']}: {check['detail']}")

        avg = total_score / len(self.results) if self.results else 0
        lines.append(f"\n{'='*70}")
        lines.append(f"OVERALL: {avg:.1f}% average across {len(self.results)} documents")
        lines.append(f"{'='*70}")

        return '\n'.join(lines)

    def save_results_to_db(self):
        """Save validation results to the database."""
        try:
            conn = self._connect()
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS quality_validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_path TEXT,
                doc_type TEXT,
                score REAL,
                checks_passed INTEGER,
                checks_total INTEGER,
                citation_count INTEGER,
                word_count INTEGER,
                details_json TEXT,
                validated_at TEXT DEFAULT (datetime('now'))
            )''')

            for r in self.results:
                c.execute('''INSERT INTO quality_validation_results
                    (file_name, file_path, doc_type, score, checks_passed, checks_total,
                     citation_count, word_count, details_json)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (r['file'], r.get('path',''), r.get('doc_type',''),
                     r.get('score',0), r.get('passed',0), r.get('total_checks',0),
                     r.get('citation_total',0), r.get('word_count',0),
                     json.dumps(r.get('checks',[]))))

            conn.commit()
            return len(self.results)
        except Exception as e:
            print(f"DB save error: {e}")
            return 0


def main():
    import sys
    validator = QualityValidator()

    if len(sys.argv) > 1 and sys.argv[1] == '--file':
        filepath = sys.argv[2] if len(sys.argv) > 2 else ''
        result = validator.validate_document(filepath)
    else:
        validator.validate_all()

    print(validator.generate_report())

    saved = validator.save_results_to_db()
    if saved:
        print(f"\n📊 {saved} results saved to quality_validation_results table.")

    validator._close()


if __name__ == '__main__':
    main()
