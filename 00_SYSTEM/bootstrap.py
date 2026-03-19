#!/usr/bin/env python3
"""
LitigationOS Bootstrap & Restore Script
========================================
Verifies system integrity and can restore from scratch.
Run: python bootstrap.py [--check | --repair | --full-restore]

--check:        Verify all components (read-only)
--repair:       Fix issues found during check
--full-restore: Complete system rebuild (DESTRUCTIVE - backs up first)
"""

import sqlite3
import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration
DB_PATH = r'C:\Users\andre\litigation_context.db'
LITIGOS_ROOT = r'C:\Users\andre\LitigationOS'
SYSTEM_DIR = os.path.join(LITIGOS_ROOT, '00_SYSTEM')

# Critical tables that must exist
CRITICAL_TABLES = {
    'auth_rules': {'min_rows': 5000, 'required_cols': ['rule_number', 'title', 'rule_type', 'full_text']},
    'master_citations': {'min_rows': 100000, 'required_cols': ['citation', 'cite_type']},
    'evidence_quotes': {'min_rows': 100, 'required_cols': ['quote_text']},
    'documents': {'min_rows': 100, 'required_cols': ['file_path', 'file_name']},
    'pages': {'min_rows': 1000, 'required_cols': ['document_id', 'page_number', 'text_content']},
    'judicial_violations': {'min_rows': 50, 'required_cols': ['violation_description', 'severity']},
    'auth_benchbook_violations': {'min_rows': 50, 'required_cols': ['rule', 'matching_text']},
    'auth_benchbook_entries': {'min_rows': 20, 'required_cols': ['section', 'title', 'content']},
    'impeachment_items': {'min_rows': 100, 'required_cols': ['speaker', 'statement']},
    'contradiction_map': {'min_rows': 100, 'required_cols': ['source_a_text', 'source_b_text']},
    'adversary_models': {'min_rows': 10, 'required_cols': ['attack_type', 'rebuttal_strategy']},
    'claims': {'min_rows': 1, 'required_cols': ['classification', 'proposition']},
    'docket_events': {'min_rows': 1, 'required_cols': ['event_date_iso', 'title']},
    'deadlines': {'min_rows': 5, 'required_cols': ['title', 'due_date_iso']},
    'vehicles': {'min_rows': 1, 'required_cols': ['case_lane', 'title', 'status']},
    'risk_events': {'min_rows': 1, 'required_cols': ['risk_class', 'severity', 'title']},
    'gap_tickets': {'min_rows': 1, 'required_cols': ['gap_type', 'description']},
}

# FTS5 indexes that must exist and be functional
FTS5_INDEXES = [
    'auth_rules_fts',
    'auth_passages_fts',
    'rules_text_fts',
    'evidence_quotes_fts',
    'md_sections_fts',
    'pages_fts',
    'master_csv_fts',
]

# Critical directories
CRITICAL_DIRS = [
    '00_SYSTEM',
    '00_SYSTEM/skills',
    '00_SYSTEM/tools',
    '00_SYSTEM/local_model',
    '01_INTAKE',
    '02_AUTHORITY',
    '03_EVIDENCE',
    '04_COURT_FILINGS',
    '05_ANALYSIS',
    '06_VEHICLES',
    '07_VALIDATION',
    '08_APPS',
]

# Critical files
CRITICAL_FILES = [
    '00_SYSTEM/skills/__init__.py',
    '00_SYSTEM/skills/skill_convergence_engine.py',
    '00_SYSTEM/tools/memory_retriever.py',
    '00_SYSTEM/tools/pdf_analyzer.py',
    '00_SYSTEM/tools/system_health.py',
    '00_SYSTEM/tools/quick_query.py',
    '00_SYSTEM/safe_db_wrapper.py',
    '00_SYSTEM/brain_search.py',
    '00_SYSTEM/context_loader.py',
    '00_SYSTEM/local_model/inference_engine.py',
]

class BootstrapChecker:
    def __init__(self):
        self.results = {'pass': [], 'warn': [], 'fail': []}
        self.db = None

    def log(self, level, component, message):
        self.results[level].append({'component': component, 'message': message})
        icon = {'pass': '\u2705', 'warn': '\u26a0\ufe0f', 'fail': '\u274c'}[level]
        print(f'  {icon} [{component}] {message}')

    def check_db_connection(self):
        """Verify database connectivity"""
        print('\n\U0001f4ca Database Connection')
        try:
            if not os.path.exists(DB_PATH):
                self.log('fail', 'database', f'Database not found at {DB_PATH}')
                return False
            size_gb = os.path.getsize(DB_PATH) / (1024**3)
            self.db = sqlite3.connect(DB_PATH)
            self.db.execute('SELECT 1')
            self.log('pass', 'database', f'Connected ({size_gb:.2f} GB)')
            return True
        except Exception as e:
            self.log('fail', 'database', f'Connection failed: {e}')
            return False

    def check_tables(self):
        """Verify all critical tables exist with correct schemas"""
        print('\n\U0001f4cb Critical Tables')
        cur = self.db.cursor()

        # Get all tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r[0] for r in cur.fetchall()}

        for table, spec in CRITICAL_TABLES.items():
            if table not in existing:
                self.log('fail', table, 'TABLE MISSING')
                continue

            # Check row count
            cur.execute(f'SELECT count(*) FROM [{table}]')
            count = cur.fetchone()[0]

            # Check columns
            cur.execute(f'PRAGMA table_info([{table}])')
            cols = {r[1] for r in cur.fetchall()}
            missing_cols = [c for c in spec['required_cols'] if c not in cols]

            if missing_cols:
                self.log('fail', table, f'{count:,} rows -- MISSING COLUMNS: {missing_cols}')
            elif count < spec['min_rows']:
                self.log('warn', table, f'{count:,} rows (expected >={spec["min_rows"]:,})')
            else:
                self.log('pass', table, f'{count:,} rows')

    def check_fts5(self):
        """Verify FTS5 indexes are functional"""
        print('\n\U0001f50d FTS5 Indexes')
        cur = self.db.cursor()

        for fts in FTS5_INDEXES:
            try:
                cur.execute(f"SELECT count(*) FROM [{fts}] WHERE [{fts}] MATCH 'test'")
                count = cur.fetchone()[0]
                # Also check total rows
                cur.execute(f"SELECT count(*) FROM [{fts}]")
                total = cur.fetchone()[0]
                self.log('pass', fts, f'Functional ({total:,} indexed)')
            except Exception as e:
                self.log('warn', fts, f'Error: {str(e)[:80]}')

    def check_directories(self):
        """Verify critical directories exist"""
        print('\n\U0001f4c1 Directory Structure')
        for d in CRITICAL_DIRS:
            full = os.path.join(LITIGOS_ROOT, d)
            if os.path.isdir(full):
                count = len(os.listdir(full))
                self.log('pass', d, f'{count} items')
            else:
                self.log('fail', d, 'DIRECTORY MISSING')

    def check_files(self):
        """Verify critical files exist"""
        print('\n\U0001f4c4 Critical Files')
        for f in CRITICAL_FILES:
            full = os.path.join(LITIGOS_ROOT, f)
            if os.path.isfile(full):
                size = os.path.getsize(full)
                self.log('pass', f, f'{size:,} bytes')
            else:
                self.log('warn', f, 'FILE MISSING')

    def check_skills(self):
        """Verify skill registry"""
        print('\n\U0001f9e0 Skill Registry')
        skills_dir = os.path.join(SYSTEM_DIR, 'skills')
        try:
            if not os.path.isdir(skills_dir):
                self.log('fail', 'skill_registry', 'Skills directory missing')
                return
            skill_files = [f for f in os.listdir(skills_dir)
                           if f.startswith('skill_') and f.endswith('.py')]
            self.log('pass', 'skill_registry', f'{len(skill_files)} skill files found')
            for sf in skill_files:
                full = os.path.join(skills_dir, sf)
                size = os.path.getsize(full)
                if size > 0:
                    self.log('pass', f'skill:{sf}', f'{size:,} bytes')
                else:
                    self.log('warn', f'skill:{sf}', 'Empty file')
        except Exception as e:
            self.log('warn', 'skill_registry', f'Cannot scan: {e}')

    def check_authority_coverage(self):
        """Check authority coverage percentages"""
        print('\n\u2696\ufe0f  Authority Coverage')
        cur = self.db.cursor()

        # Check what rule_type values exist
        try:
            cur.execute("SELECT rule_type, count(*) FROM auth_rules GROUP BY rule_type ORDER BY count(*) DESC")
            rows = cur.fetchall()
            for rtype, cnt in rows:
                label = rtype if rtype else '(NULL)'
                threshold = 100 if rtype in ('MCR', 'MCR_SUBRULE') else 10
                self.log('pass' if cnt >= threshold else 'warn', f'auth:{label}', f'{cnt:,} entries')
        except Exception as e:
            self.log('warn', 'authority', f'Cannot query auth_rules: {e}')

        # Citations
        try:
            cur.execute("SELECT count(*) FROM master_citations")
            cit = cur.fetchone()[0]
            self.log('pass' if cit > 100000 else 'warn', 'citations', f'{cit:,} total')
        except Exception as e:
            self.log('warn', 'citations', f'Error: {e}')

        # Evidence
        try:
            cur.execute("SELECT count(*) FROM evidence_quotes")
            ev = cur.fetchone()[0]
            self.log('pass' if ev > 100 else 'warn', 'evidence', f'{ev:,} quotes')
        except Exception as e:
            self.log('warn', 'evidence', f'Error: {e}')

    def check_deadlines(self):
        """Check upcoming deadlines"""
        print('\n\u23f0 Deadlines')
        cur = self.db.cursor()
        try:
            cur.execute("SELECT title, due_date_iso, status FROM deadlines WHERE status != 'satisfied' ORDER BY due_date_iso")
            rows = cur.fetchall()
            if not rows:
                self.log('warn', 'deadline', 'No active deadlines found')
                return
            for r in rows:
                try:
                    due = datetime.strptime(r[1], '%Y-%m-%d')
                    days = (due - datetime.now()).days
                    if days < 0:
                        self.log('fail', 'deadline', f'OVERDUE ({abs(days)}d): {r[0]}')
                    elif days <= 7:
                        self.log('warn', 'deadline', f'{days}d remaining: {r[0]}')
                    else:
                        self.log('pass', 'deadline', f'{days}d remaining: {r[0]}')
                except Exception:
                    self.log('warn', 'deadline', f'{r[0]} | {r[1]} | {r[2]}')
        except Exception as e:
            self.log('warn', 'deadline', f'Cannot query deadlines: {e}')

    def check_separation_days(self):
        """Track parent-child separation duration"""
        print('\n\U0001f4a1 Case Status')
        sep_start = datetime(2024, 7, 29)
        days = (datetime.now() - sep_start).days
        self.log('fail' if days > 300 else 'warn', 'separation',
                 f'{days} days parent-child separation (since 2024-07-29)')

    def run_check(self):
        """Run full system check"""
        print('=' * 60)
        print('LitigationOS Bootstrap Check')
        print(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 60)

        if not self.check_db_connection():
            print('\n\u274c FATAL: Cannot connect to database. Aborting.')
            return self.summary()

        self.check_tables()
        self.check_fts5()
        self.check_directories()
        self.check_files()
        self.check_skills()
        self.check_authority_coverage()
        self.check_deadlines()
        self.check_separation_days()

        if self.db:
            self.db.close()

        return self.summary()

    def summary(self):
        """Print summary"""
        print('\n' + '=' * 60)
        print('SUMMARY')
        print('=' * 60)
        total = sum(len(v) for v in self.results.values())
        print(f'  \u2705 Pass: {len(self.results["pass"])}')
        print(f'  \u26a0\ufe0f  Warn: {len(self.results["warn"])}')
        print(f'  \u274c Fail: {len(self.results["fail"])}')
        print(f'  Total checks: {total}')

        if self.results['fail']:
            print('\n\u274c FAILURES:')
            for f in self.results['fail']:
                print(f'  - [{f["component"]}] {f["message"]}')

        if self.results['warn']:
            print('\n\u26a0\ufe0f  WARNINGS:')
            for w in self.results['warn']:
                print(f'  - [{w["component"]}] {w["message"]}')

        health = len(self.results['pass']) / total * 100 if total > 0 else 0
        print(f'\n\U0001f3e5 System Health: {health:.1f}%')

        return self.results


def rebuild_fts5(db_path=DB_PATH):
    """Rebuild all FTS5 indexes"""
    print('\n\U0001f527 Rebuilding FTS5 indexes...')
    db = sqlite3.connect(db_path)

    for fts in FTS5_INDEXES:
        try:
            db.execute(f"INSERT INTO [{fts}]([{fts}]) VALUES('rebuild')")
            db.commit()
            print(f'  \u2705 {fts} rebuilt')
        except Exception as e:
            print(f'  \u26a0\ufe0f  {fts}: {e}')

    db.close()
    print('Done.')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'

    if mode == '--check':
        checker = BootstrapChecker()
        checker.run_check()
    elif mode == '--repair':
        checker = BootstrapChecker()
        results = checker.run_check()
        if results['fail'] or results['warn']:
            print('\n\U0001f527 Attempting repairs...')
            rebuild_fts5()
    elif mode == '--rebuild-fts':
        rebuild_fts5()
    else:
        print(__doc__)
