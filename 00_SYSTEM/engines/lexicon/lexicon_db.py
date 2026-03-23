"""
LEXICON Database — Michigan Legal Authority Knowledge Base
Schema + seed/query utilities for all Michigan legal rules.

Tables:
  legal_rules        — MCR, MCL, MRE, Canons, FOC, SCAO rules
  rule_cross_refs    — Relationships between rules
  filing_requirements — What's needed for each filing type per court
  deadline_rules     — Deadline computation formulas
  evidence_rules     — MRE admissibility decision trees
  canon_violations   — JTC complaint elements per canon
  legal_rules_fts    — FTS5 full-text search across all rules

Usage:
  from lexicon.lexicon_db import LexiconDB
  db = LexiconDB()
  db.seed_all()  # Populate from data modules
  results = db.search("disqualification bias")
  rule = db.get_rule("MCR-2.003")
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime


# ─── Data Classes ─────────────────────────────────────────────

@dataclass
class LegalRule:
    rule_id: str            # e.g., 'MCR-2.003', 'MCL-722.23', 'MRE-801'
    source: str             # 'MCR', 'MCL', 'MRE', 'CANON', 'FOC', 'SCAO', 'LOCAL'
    chapter: str = ""       # e.g., '2', '722', '8'
    section: str = ""       # e.g., '2.003', '722.23'
    subsection: str = ""    # e.g., '(C)(1)'
    title: str = ""
    summary: str = ""
    full_text: str = ""
    effective_date: str = ""
    amended_date: str = ""
    confidence: str = "verified"  # 'verified', 'high', 'medium', 'needs_verification'
    lanes: List[str] = field(default_factory=list)  # ["A","D","E"]
    tags: List[str] = field(default_factory=list)
    url: str = ""           # Official source URL

@dataclass
class RuleCrossRef:
    from_rule: str
    to_rule: str
    relationship: str = ""   # 'requires', 'supersedes', 'supplements', 'conflicts', 'see_also'
    description: str = ""

@dataclass
class FilingRequirement:
    requirement_id: str
    filing_type: str         # e.g., 'motion_to_modify_custody'
    court: str               # e.g., '14th_circuit_family', 'coa', 'msc'
    rule_id: str = ""        # FK to legal_rules
    requirement: str = ""
    category: str = ""       # 'notice', 'form', 'service', 'deadline', 'content', 'fee', 'format'
    is_mandatory: bool = True
    deadline_formula: str = ""  # e.g., '9_days_before_hearing'
    forms_required: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class DeadlineRule:
    rule_id: str
    source_rule: str = ""    # FK to legal_rules
    trigger_event: str = ""  # e.g., 'motion_filing', 'order_entry', 'hearing_date'
    deadline_type: str = ""  # 'before', 'after', 'within'
    days: int = 0
    business_days: bool = False
    description: str = ""
    court: str = ""
    lane: str = ""

@dataclass
class EvidenceRule:
    rule_id: str
    mre_number: str = ""
    rule_name: str = ""
    category: str = ""       # 'hearsay_exception', 'authentication', 'privilege', 'relevance'
    prerequisites: List[str] = field(default_factory=list)
    applies_when: str = ""
    excludes_when: str = ""
    decision_tree: Dict = field(default_factory=dict)
    lane_relevance: List[str] = field(default_factory=list)

@dataclass
class CanonViolation:
    violation_id: str
    canon_number: int = 0
    canon_title: str = ""
    violation_type: str = ""
    elements: List[str] = field(default_factory=list)
    evidence_needed: List[str] = field(default_factory=list)
    complaint_language: str = ""
    lane: str = "E"


# ─── Database Engine ──────────────────────────────────────────

class LexiconDB:
    """Michigan Legal Authority Knowledge Base."""

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base = Path(__file__).resolve().parent.parent.parent
            db_path = str(base / "databases" / "lexicon.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            -- Core rules table
            CREATE TABLE IF NOT EXISTS legal_rules (
                rule_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                chapter TEXT DEFAULT '',
                section TEXT DEFAULT '',
                subsection TEXT DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                summary TEXT DEFAULT '',
                full_text TEXT DEFAULT '',
                effective_date TEXT DEFAULT '',
                amended_date TEXT DEFAULT '',
                confidence TEXT DEFAULT 'verified',
                lanes TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                url TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- Cross-references between rules
            CREATE TABLE IF NOT EXISTS rule_cross_refs (
                from_rule TEXT NOT NULL,
                to_rule TEXT NOT NULL,
                relationship TEXT DEFAULT '',
                description TEXT DEFAULT '',
                PRIMARY KEY (from_rule, to_rule)
            );

            -- Filing requirements per filing type per court
            CREATE TABLE IF NOT EXISTS filing_requirements (
                requirement_id TEXT PRIMARY KEY,
                filing_type TEXT NOT NULL,
                court TEXT NOT NULL,
                rule_id TEXT DEFAULT '',
                requirement TEXT NOT NULL DEFAULT '',
                category TEXT DEFAULT '',
                is_mandatory INTEGER DEFAULT 1,
                deadline_formula TEXT DEFAULT '',
                forms_required TEXT DEFAULT '[]',
                notes TEXT DEFAULT ''
            );

            -- Deadline computation rules
            CREATE TABLE IF NOT EXISTS deadline_rules (
                rule_id TEXT PRIMARY KEY,
                source_rule TEXT DEFAULT '',
                trigger_event TEXT DEFAULT '',
                deadline_type TEXT DEFAULT '',
                days INTEGER DEFAULT 0,
                business_days INTEGER DEFAULT 0,
                description TEXT DEFAULT '',
                court TEXT DEFAULT '',
                lane TEXT DEFAULT ''
            );

            -- Evidence admissibility rules (MRE)
            CREATE TABLE IF NOT EXISTS evidence_rules (
                rule_id TEXT PRIMARY KEY,
                mre_number TEXT DEFAULT '',
                rule_name TEXT DEFAULT '',
                category TEXT DEFAULT '',
                prerequisites TEXT DEFAULT '[]',
                applies_when TEXT DEFAULT '',
                excludes_when TEXT DEFAULT '',
                decision_tree TEXT DEFAULT '{}',
                lane_relevance TEXT DEFAULT '[]'
            );

            -- Judicial canon violation elements (JTC)
            CREATE TABLE IF NOT EXISTS canon_violations (
                violation_id TEXT PRIMARY KEY,
                canon_number INTEGER DEFAULT 0,
                canon_title TEXT DEFAULT '',
                violation_type TEXT DEFAULT '',
                elements TEXT DEFAULT '[]',
                evidence_needed TEXT DEFAULT '[]',
                complaint_language TEXT DEFAULT '',
                lane TEXT DEFAULT 'E'
            );

            -- Schema metadata
            CREATE TABLE IF NOT EXISTS lexicon_meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            -- Indexes for fast lookups
            CREATE INDEX IF NOT EXISTS idx_rules_source ON legal_rules(source);
            CREATE INDEX IF NOT EXISTS idx_rules_chapter ON legal_rules(chapter);
            CREATE INDEX IF NOT EXISTS idx_rules_confidence ON legal_rules(confidence);
            CREATE INDEX IF NOT EXISTS idx_filing_req_type ON filing_requirements(filing_type);
            CREATE INDEX IF NOT EXISTS idx_filing_req_court ON filing_requirements(court);
            CREATE INDEX IF NOT EXISTS idx_deadline_trigger ON deadline_rules(trigger_event);
            CREATE INDEX IF NOT EXISTS idx_evidence_category ON evidence_rules(category);
            CREATE INDEX IF NOT EXISTS idx_canon_number ON canon_violations(canon_number);
        """)

        # FTS5 virtual table for full-text search across all rules
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS legal_rules_fts USING fts5(
                    rule_id, source, title, summary, full_text, tags,
                    content='legal_rules',
                    content_rowid='rowid'
                )
            """)
            # Sync triggers
            conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS legal_rules_ai AFTER INSERT ON legal_rules BEGIN
                    INSERT INTO legal_rules_fts(rowid, rule_id, source, title, summary, full_text, tags)
                    VALUES (new.rowid, new.rule_id, new.source, new.title, new.summary, new.full_text, new.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS legal_rules_ad AFTER DELETE ON legal_rules BEGIN
                    INSERT INTO legal_rules_fts(legal_rules_fts, rowid, rule_id, source, title, summary, full_text, tags)
                    VALUES ('delete', old.rowid, old.rule_id, old.source, old.title, old.summary, old.full_text, old.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS legal_rules_au AFTER UPDATE ON legal_rules BEGIN
                    INSERT INTO legal_rules_fts(legal_rules_fts, rowid, rule_id, source, title, summary, full_text, tags)
                    VALUES ('delete', old.rowid, old.rule_id, old.source, old.title, old.summary, old.full_text, old.tags);
                    INSERT INTO legal_rules_fts(rowid, rule_id, source, title, summary, full_text, tags)
                    VALUES (new.rowid, new.rule_id, new.source, new.title, new.summary, new.full_text, new.tags);
                END;
            """)
        except Exception:
            pass  # FTS5 triggers may already exist

        conn.execute(
            "INSERT OR REPLACE INTO lexicon_meta (key, value) VALUES (?, ?)",
            ("schema_version", self.SCHEMA_VERSION)
        )
        conn.commit()
        conn.close()

    # ─── CRUD Operations ──────────────────────────────────────

    def insert_rule(self, rule: LegalRule) -> bool:
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO legal_rules
                (rule_id, source, chapter, section, subsection, title, summary,
                 full_text, effective_date, amended_date, confidence, lanes, tags, url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                rule.rule_id, rule.source, rule.chapter, rule.section, rule.subsection,
                rule.title, rule.summary, rule.full_text, rule.effective_date,
                rule.amended_date, rule.confidence,
                json.dumps(rule.lanes), json.dumps(rule.tags), rule.url
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting rule {rule.rule_id}: {e}")
            return False
        finally:
            conn.close()

    def insert_rules_batch(self, rules: List[LegalRule]) -> int:
        conn = self._get_conn()
        rows = [(
            r.rule_id, r.source, r.chapter, r.section, r.subsection,
            r.title, r.summary, r.full_text, r.effective_date,
            r.amended_date, r.confidence,
            json.dumps(r.lanes), json.dumps(r.tags), r.url
        ) for r in rules]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO legal_rules
                (rule_id, source, chapter, section, subsection, title, summary,
                 full_text, effective_date, amended_date, confidence, lanes, tags, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting rules: {e}")
            return 0
        finally:
            conn.close()

    def insert_cross_refs_batch(self, refs: List[RuleCrossRef]) -> int:
        conn = self._get_conn()
        rows = [(r.from_rule, r.to_rule, r.relationship, r.description) for r in refs]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO rule_cross_refs
                (from_rule, to_rule, relationship, description)
                VALUES (?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting cross refs: {e}")
            return 0
        finally:
            conn.close()

    def insert_filing_requirements_batch(self, reqs: List[FilingRequirement]) -> int:
        conn = self._get_conn()
        rows = [(
            r.requirement_id, r.filing_type, r.court, r.rule_id,
            r.requirement, r.category, 1 if r.is_mandatory else 0,
            r.deadline_formula, json.dumps(r.forms_required), r.notes
        ) for r in reqs]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO filing_requirements
                (requirement_id, filing_type, court, rule_id, requirement,
                 category, is_mandatory, deadline_formula, forms_required, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting filing requirements: {e}")
            return 0
        finally:
            conn.close()

    def insert_deadline_rules_batch(self, rules: List[DeadlineRule]) -> int:
        conn = self._get_conn()
        rows = [(
            r.rule_id, r.source_rule, r.trigger_event, r.deadline_type,
            r.days, 1 if r.business_days else 0, r.description, r.court, r.lane
        ) for r in rules]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO deadline_rules
                (rule_id, source_rule, trigger_event, deadline_type,
                 days, business_days, description, court, lane)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting deadline rules: {e}")
            return 0
        finally:
            conn.close()

    def insert_evidence_rules_batch(self, rules: List[EvidenceRule]) -> int:
        conn = self._get_conn()
        rows = [(
            r.rule_id, r.mre_number, r.rule_name, r.category,
            json.dumps(r.prerequisites), r.applies_when, r.excludes_when,
            json.dumps(r.decision_tree), json.dumps(r.lane_relevance)
        ) for r in rules]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO evidence_rules
                (rule_id, mre_number, rule_name, category,
                 prerequisites, applies_when, excludes_when,
                 decision_tree, lane_relevance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting evidence rules: {e}")
            return 0
        finally:
            conn.close()

    def insert_canon_violations_batch(self, violations: List[CanonViolation]) -> int:
        conn = self._get_conn()
        rows = [(
            v.violation_id, v.canon_number, v.canon_title, v.violation_type,
            json.dumps(v.elements), json.dumps(v.evidence_needed),
            v.complaint_language, v.lane
        ) for v in violations]
        try:
            conn.executemany("""
                INSERT OR REPLACE INTO canon_violations
                (violation_id, canon_number, canon_title, violation_type,
                 elements, evidence_needed, complaint_language, lane)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            return len(rows)
        except Exception as e:
            print(f"Error batch inserting canon violations: {e}")
            return 0
        finally:
            conn.close()

    # ─── Query Operations ─────────────────────────────────────

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM legal_rules WHERE rule_id = ?", (rule_id,)
        ).fetchone()
        conn.close()
        if row:
            d = dict(row)
            d['lanes'] = json.loads(d.get('lanes', '[]'))
            d['tags'] = json.loads(d.get('tags', '[]'))
            return d
        return None

    def search(self, query: str, source: str = None, limit: int = 20) -> List[Dict]:
        conn = self._get_conn()
        try:
            if source:
                rows = conn.execute("""
                    SELECT lr.* FROM legal_rules_fts fts
                    JOIN legal_rules lr ON lr.rowid = fts.rowid
                    WHERE legal_rules_fts MATCH ? AND lr.source = ?
                    ORDER BY rank LIMIT ?
                """, (query, source, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT lr.* FROM legal_rules_fts fts
                    JOIN legal_rules lr ON lr.rowid = fts.rowid
                    WHERE legal_rules_fts MATCH ?
                    ORDER BY rank LIMIT ?
                """, (query, limit)).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d['lanes'] = json.loads(d.get('lanes', '[]'))
                d['tags'] = json.loads(d.get('tags', '[]'))
                results.append(d)
            return results
        except Exception:
            return []
        finally:
            conn.close()

    def get_rules_by_source(self, source: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM legal_rules WHERE source = ? ORDER BY section",
            (source,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_rules_for_lane(self, lane: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM legal_rules WHERE lanes LIKE ? ORDER BY source, section",
            (f'%"{lane}"%',)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_cross_refs(self, rule_id: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM rule_cross_refs
            WHERE from_rule = ? OR to_rule = ?
            ORDER BY relationship
        """, (rule_id, rule_id)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_filing_requirements(self, filing_type: str, court: str = None) -> List[Dict]:
        conn = self._get_conn()
        if court:
            rows = conn.execute("""
                SELECT fr.*, lr.title as rule_title, lr.summary as rule_summary
                FROM filing_requirements fr
                LEFT JOIN legal_rules lr ON fr.rule_id = lr.rule_id
                WHERE fr.filing_type = ? AND fr.court = ?
                ORDER BY fr.category, fr.is_mandatory DESC
            """, (filing_type, court)).fetchall()
        else:
            rows = conn.execute("""
                SELECT fr.*, lr.title as rule_title, lr.summary as rule_summary
                FROM filing_requirements fr
                LEFT JOIN legal_rules lr ON fr.rule_id = lr.rule_id
                WHERE fr.filing_type = ?
                ORDER BY fr.court, fr.category, fr.is_mandatory DESC
            """, (filing_type,)).fetchall()
        conn.close()
        results = []
        for row in rows:
            d = dict(row)
            d['forms_required'] = json.loads(d.get('forms_required', '[]'))
            results.append(d)
        return results

    def get_deadlines(self, trigger_event: str = None, court: str = None) -> List[Dict]:
        conn = self._get_conn()
        clauses, params = [], []
        if trigger_event:
            clauses.append("trigger_event = ?")
            params.append(trigger_event)
        if court:
            clauses.append("court = ?")
            params.append(court)
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = conn.execute(
            f"SELECT * FROM deadline_rules WHERE {where} ORDER BY days", params
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_evidence_rules_by_category(self, category: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM evidence_rules WHERE category = ? ORDER BY mre_number",
            (category,)
        ).fetchall()
        conn.close()
        results = []
        for row in rows:
            d = dict(row)
            d['prerequisites'] = json.loads(d.get('prerequisites', '[]'))
            d['decision_tree'] = json.loads(d.get('decision_tree', '{}'))
            d['lane_relevance'] = json.loads(d.get('lane_relevance', '[]'))
            results.append(d)
        return results

    def get_canon_violations(self, canon_number: int = None) -> List[Dict]:
        conn = self._get_conn()
        if canon_number:
            rows = conn.execute(
                "SELECT * FROM canon_violations WHERE canon_number = ?",
                (canon_number,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM canon_violations").fetchall()
        conn.close()
        results = []
        for row in rows:
            d = dict(row)
            d['elements'] = json.loads(d.get('elements', '[]'))
            d['evidence_needed'] = json.loads(d.get('evidence_needed', '[]'))
            results.append(d)
        return results

    # ─── Statistics ────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        row = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM legal_rules) as total_rules,
                (SELECT COUNT(*) FROM legal_rules WHERE source='MCR') as mcr_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='MCL') as mcl_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='MRE') as mre_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='CANON') as canon_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='FOC') as foc_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='SCAO') as scao_count,
                (SELECT COUNT(*) FROM legal_rules WHERE source='LOCAL') as local_count,
                (SELECT COUNT(*) FROM rule_cross_refs) as cross_refs,
                (SELECT COUNT(*) FROM filing_requirements) as filing_reqs,
                (SELECT COUNT(*) FROM deadline_rules) as deadline_rules,
                (SELECT COUNT(*) FROM evidence_rules) as evidence_rules,
                (SELECT COUNT(*) FROM canon_violations) as canon_violations,
                (SELECT COUNT(*) FROM legal_rules WHERE confidence='verified') as verified,
                (SELECT COUNT(*) FROM legal_rules WHERE confidence='needs_verification') as needs_verify
        """).fetchone()
        conn.close()
        return dict(row)

    # ─── Seed from Data Modules ────────────────────────────────

    def seed_all(self) -> Dict[str, int]:
        """Seed all data from companion data modules."""
        counts = {}

        # Import data modules (they live alongside this file)
        data_dir = Path(__file__).parent
        sys.path.insert(0, str(data_dir))

        try:
            from mcr_data import get_mcr_rules, get_mcr_cross_refs, get_mcr_filing_requirements, get_mcr_deadlines
            counts['mcr_rules'] = self.insert_rules_batch(get_mcr_rules())
            counts['mcr_cross_refs'] = self.insert_cross_refs_batch(get_mcr_cross_refs())
            counts['mcr_filing_reqs'] = self.insert_filing_requirements_batch(get_mcr_filing_requirements())
            counts['mcr_deadlines'] = self.insert_deadline_rules_batch(get_mcr_deadlines())
        except ImportError as e:
            print(f"MCR data not found: {e}")

        try:
            from mcl_data import get_mcl_rules, get_mcl_cross_refs
            counts['mcl_rules'] = self.insert_rules_batch(get_mcl_rules())
            counts['mcl_cross_refs'] = self.insert_cross_refs_batch(get_mcl_cross_refs())
        except ImportError as e:
            print(f"MCL data not found: {e}")

        try:
            from mre_data import get_mre_rules, get_mre_evidence_rules
            counts['mre_rules'] = self.insert_rules_batch(get_mre_rules())
            counts['mre_evidence_rules'] = self.insert_evidence_rules_batch(get_mre_evidence_rules())
        except ImportError as e:
            print(f"MRE data not found: {e}")

        try:
            from canons_data import get_canon_rules, get_canon_violations
            counts['canon_rules'] = self.insert_rules_batch(get_canon_rules())
            counts['canon_violations'] = self.insert_canon_violations_batch(get_canon_violations())
        except ImportError as e:
            print(f"Canons data not found: {e}")

        try:
            from foc_data import get_foc_rules, get_foc_deadlines
            counts['foc_rules'] = self.insert_rules_batch(get_foc_rules())
            counts['foc_deadlines'] = self.insert_deadline_rules_batch(get_foc_deadlines())
        except ImportError as e:
            print(f"FOC data not found: {e}")

        # Store seed timestamp
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO lexicon_meta (key, value) VALUES (?, ?)",
            ("last_seeded", datetime.now().isoformat())
        )
        conn.execute(
            "INSERT OR REPLACE INTO lexicon_meta (key, value) VALUES (?, ?)",
            ("seed_counts", json.dumps(counts))
        )
        conn.commit()
        conn.close()

        return counts


# ─── CLI ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="LEXICON — Michigan Legal Authority Database")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("seed", help="Seed database from data modules")
    sub.add_parser("stats", help="Show database statistics")

    sp = sub.add_parser("search", help="Full-text search across all rules")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--source", help="Filter by source (MCR, MCL, MRE, etc.)")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("rule", help="Get a specific rule by ID")
    sp.add_argument("rule_id", help="Rule ID (e.g., MCR-2.003)")

    sp = sub.add_parser("filing", help="Get filing requirements")
    sp.add_argument("filing_type", help="Filing type (e.g., motion_to_modify_custody)")
    sp.add_argument("--court", help="Court (e.g., 14th_circuit_family)")

    sp = sub.add_parser("deadlines", help="Get deadline rules")
    sp.add_argument("--trigger", help="Trigger event")
    sp.add_argument("--court", help="Court")

    sp = sub.add_parser("evidence", help="Get evidence rules by category")
    sp.add_argument("category", help="Category (hearsay_exception, authentication, etc.)")

    sp = sub.add_parser("canons", help="Get canon violations")
    sp.add_argument("--canon", type=int, help="Canon number (1-7)")

    sp = sub.add_parser("lane", help="Get all rules for a case lane")
    sp.add_argument("lane", help="Lane letter (A-F)")

    sp = sub.add_parser("crossrefs", help="Get cross-references for a rule")
    sp.add_argument("rule_id", help="Rule ID")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Force UTF-8
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

    db = LexiconDB()

    if args.command == "seed":
        print("Seeding LEXICON database...")
        counts = db.seed_all()
        total = sum(counts.values())
        print(f"\n✅ Seeded {total} items:")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
        stats = db.get_stats()
        print(f"\nDatabase totals:")
        print(f"  Rules: {stats['total_rules']} (MCR:{stats['mcr_count']} MCL:{stats['mcl_count']} "
              f"MRE:{stats['mre_count']} Canon:{stats['canon_count']} FOC:{stats['foc_count']})")
        print(f"  Cross-refs: {stats['cross_refs']}")
        print(f"  Filing reqs: {stats['filing_reqs']}")
        print(f"  Deadline rules: {stats['deadline_rules']}")
        print(f"  Evidence rules: {stats['evidence_rules']}")
        print(f"  Canon violations: {stats['canon_violations']}")

    elif args.command == "stats":
        stats = db.get_stats()
        print("LEXICON Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.command == "search":
        results = db.search(args.query, source=args.source, limit=args.limit)
        print(f"Found {len(results)} results for '{args.query}':")
        for r in results:
            print(f"\n  [{r['source']}] {r['rule_id']} — {r['title']}")
            if r['summary']:
                print(f"    {r['summary'][:120]}")

    elif args.command == "rule":
        rule = db.get_rule(args.rule_id)
        if rule:
            print(f"Rule: {rule['rule_id']} — {rule['title']}")
            print(f"Source: {rule['source']} | Chapter: {rule['chapter']} | Section: {rule['section']}")
            print(f"Confidence: {rule['confidence']} | Lanes: {rule['lanes']}")
            if rule['summary']:
                print(f"\nSummary: {rule['summary']}")
            if rule['full_text']:
                print(f"\nFull text:\n{rule['full_text'][:500]}")
            refs = db.get_cross_refs(args.rule_id)
            if refs:
                print(f"\nCross-references ({len(refs)}):")
                for ref in refs:
                    other = ref['to_rule'] if ref['from_rule'] == args.rule_id else ref['from_rule']
                    print(f"  → {other} ({ref['relationship']}): {ref['description']}")
        else:
            print(f"Rule '{args.rule_id}' not found")

    elif args.command == "filing":
        reqs = db.get_filing_requirements(args.filing_type, court=args.court)
        print(f"Filing requirements for '{args.filing_type}'" +
              (f" in {args.court}" if args.court else "") + f" ({len(reqs)}):")
        for r in reqs:
            mandatory = "REQUIRED" if r['is_mandatory'] else "optional"
            print(f"\n  [{r['category']}] {mandatory}: {r['requirement']}")
            if r['rule_id']:
                print(f"    Rule: {r['rule_id']} — {r.get('rule_title', '')}")
            if r['forms_required']:
                forms = json.loads(r['forms_required']) if isinstance(r['forms_required'], str) else r['forms_required']
                if forms:
                    print(f"    Forms: {', '.join(forms)}")
            if r['deadline_formula']:
                print(f"    Deadline: {r['deadline_formula']}")

    elif args.command == "deadlines":
        rules = db.get_deadlines(trigger_event=args.trigger, court=args.court)
        print(f"Deadline rules ({len(rules)}):")
        for r in rules:
            bdays = " (business days)" if r['business_days'] else ""
            print(f"  {r['rule_id']}: {r['days']} days {r['deadline_type']} {r['trigger_event']}{bdays}")
            print(f"    {r['description']}")

    elif args.command == "evidence":
        rules = db.get_evidence_rules_by_category(args.category)
        print(f"Evidence rules for '{args.category}' ({len(rules)}):")
        for r in rules:
            print(f"\n  MRE {r['mre_number']} — {r['rule_name']}")
            print(f"    Applies when: {r['applies_when']}")
            if r['prerequisites']:
                prereqs = json.loads(r['prerequisites']) if isinstance(r['prerequisites'], str) else r['prerequisites']
                if prereqs:
                    print(f"    Prerequisites: {', '.join(prereqs)}")

    elif args.command == "canons":
        violations = db.get_canon_violations(canon_number=args.canon)
        print(f"Canon violations ({len(violations)}):")
        for v in violations:
            print(f"\n  Canon {v['canon_number']}: {v['canon_title']}")
            print(f"  Violation: {v['violation_type']}")
            elements = json.loads(v['elements']) if isinstance(v['elements'], str) else v['elements']
            if elements:
                print(f"  Elements to prove:")
                for e in elements:
                    print(f"    • {e}")

    elif args.command == "lane":
        rules = db.get_rules_for_lane(args.lane)
        print(f"Rules for Lane {args.lane} ({len(rules)}):")
        for r in rules:
            print(f"  [{r['source']}] {r['rule_id']} — {r['title']}")

    elif args.command == "crossrefs":
        refs = db.get_cross_refs(args.rule_id)
        print(f"Cross-references for {args.rule_id} ({len(refs)}):")
        for ref in refs:
            other = ref['to_rule'] if ref['from_rule'] == args.rule_id else ref['from_rule']
            print(f"  → {other} ({ref['relationship']}): {ref['description']}")


if __name__ == "__main__":
    main()
