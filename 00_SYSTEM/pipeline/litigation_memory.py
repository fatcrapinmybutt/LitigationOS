# -*- coding: utf-8 -*-
"""
LITIGATION MEMORY ENGINE v1.0 — Persistent Cross-Session Intelligence
═══════════════════════════════════════════════════════════════════════

Deep memory system that ensures no knowledge is lost between sessions:
  - Filing history: what was filed, when, outcome, court response
  - Evidence usage: which evidence used in which filing, strength score
  - Citation tracking: every authority cited, where, validation status
  - Session continuity: key decisions, findings, corrections per session
  - System evolution: what was upgraded, what broke, what improved

All stored in litigation_context.db for cross-session persistence.
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(r"C:\Users\andre\LitigationOS")
LITIGATION_DB = BASE_DIR / "litigation_context.db"

PRAGMAS = """
PRAGMA busy_timeout=60000;
PRAGMA journal_mode=WAL;
PRAGMA cache_size=-32000;
PRAGMA temp_store=MEMORY;
PRAGMA synchronous=NORMAL;
"""


class LitigationMemory:
    """Persistent litigation intelligence — survives across all sessions."""
    
    def __init__(self, db_path: Path = LITIGATION_DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(PRAGMAS)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create memory tables if they don't exist."""
        self.conn.executescript("""
        -- Filing history — what was generated, edited, filed
        CREATE TABLE IF NOT EXISTS filing_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_id TEXT NOT NULL,
            filing_name TEXT,
            lane TEXT,
            version INTEGER DEFAULT 1,
            action TEXT,
            details TEXT,
            file_path TEXT,
            word_count INTEGER,
            citation_count INTEGER,
            authority_count INTEGER,
            qa_status TEXT,
            blockers INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            session_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_filing_memory_id ON filing_memory(filing_id);
        
        -- Evidence usage — tracks which evidence is used where
        CREATE TABLE IF NOT EXISTS evidence_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT,
            evidence_description TEXT,
            source_file TEXT,
            source_line INTEGER,
            used_in_filing TEXT,
            used_in_section TEXT,
            strength_score REAL,
            admissibility TEXT,
            relevance TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_evidence_usage_filing ON evidence_usage(used_in_filing);
        
        -- Citation tracker — every authority across all filings
        CREATE TABLE IF NOT EXISTS citation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citation_text TEXT NOT NULL,
            citation_type TEXT,
            used_in_filings TEXT,
            validated INTEGER DEFAULT 0,
            validation_status TEXT,
            propositions TEXT,
            pinpoint TEXT,
            first_used TEXT,
            last_verified TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_citation_text ON citation_memory(citation_text);
        
        -- Session continuity — key decisions and findings per session
        CREATE TABLE IF NOT EXISTS session_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            category TEXT,
            key_finding TEXT NOT NULL,
            details TEXT,
            impact TEXT,
            files_affected TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        -- Corrections log — what was wrong and how it was fixed
        CREATE TABLE IF NOT EXISTS correction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            error_description TEXT NOT NULL,
            correction_applied TEXT,
            files_affected TEXT,
            root_cause TEXT,
            prevention_rule TEXT,
            session_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        -- System evolution — upgrades, improvements, new capabilities
        CREATE TABLE IF NOT EXISTS evolution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT NOT NULL,
            change_type TEXT,
            description TEXT,
            before_state TEXT,
            after_state TEXT,
            metrics_before TEXT,
            metrics_after TEXT,
            session_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        -- Filing dependency graph — how filings reinforce each other
        CREATE TABLE IF NOT EXISTS filing_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_filing TEXT NOT NULL,
            target_filing TEXT NOT NULL,
            relationship TEXT,
            strength TEXT,
            description TEXT
        );
        
        -- Opponent intelligence — predictions, patterns, responses
        CREATE TABLE IF NOT EXISTS opponent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            behavior_type TEXT,
            description TEXT,
            evidence_refs TEXT,
            predicted_response TEXT,
            counter_strategy TEXT,
            confidence TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        self.conn.commit()
    
    # ─── FILING MEMORY ────────────────────────────────────────
    
    def record_filing_action(self, filing_id: str, action: str, details: str = "",
                              file_path: str = "", session_id: str = "", **kwargs):
        """Record a filing action (created, edited, audited, filed, etc.)."""
        filing_name = kwargs.get("filing_name", "")
        self.conn.execute("""
            INSERT INTO filing_memory 
            (filing_id, filing_name, lane, action, details, file_path, 
             word_count, citation_count, authority_count, qa_status,
             blockers, warnings, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (filing_id, filing_name, kwargs.get("lane", ""),
              action, details, file_path,
              kwargs.get("word_count", 0), kwargs.get("citation_count", 0),
              kwargs.get("authority_count", 0), kwargs.get("qa_status", ""),
              kwargs.get("blockers", 0), kwargs.get("warnings", 0),
              session_id))
        self.conn.commit()
    
    def get_filing_history(self, filing_id: str) -> List[dict]:
        """Get complete history of a filing across all sessions."""
        rows = self.conn.execute(
            "SELECT * FROM filing_memory WHERE filing_id = ? ORDER BY created_at",
            (filing_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    # ─── EVIDENCE USAGE ───────────────────────────────────────
    
    def record_evidence_use(self, evidence_id: str, description: str,
                            source_file: str, used_in_filing: str,
                            section: str = "", strength: float = 0.0):
        """Record that evidence was used in a filing."""
        self.conn.execute("""
            INSERT INTO evidence_usage 
            (evidence_id, evidence_description, source_file, used_in_filing,
             used_in_section, strength_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (evidence_id, description, source_file, used_in_filing,
              section, strength))
        self.conn.commit()
    
    def get_evidence_for_filing(self, filing_id: str) -> List[dict]:
        """Get all evidence used in a specific filing."""
        rows = self.conn.execute(
            "SELECT * FROM evidence_usage WHERE used_in_filing = ? ORDER BY strength_score DESC",
            (filing_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    
    def get_unused_evidence(self) -> List[dict]:
        """Find strong evidence not yet used in any filing."""
        # This requires cross-referencing evidence_atoms with evidence_usage
        try:
            rows = self.conn.execute("""
                SELECT ea.* FROM evidence_atoms ea
                WHERE ea.id NOT IN (SELECT evidence_id FROM evidence_usage WHERE evidence_id IS NOT NULL)
                ORDER BY ea.strength DESC
                LIMIT 50
            """).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
    
    # ─── CITATION MEMORY ─────────────────────────────────────
    
    def record_citation(self, citation_text: str, citation_type: str,
                        filing_id: str, validated: bool = False,
                        propositions: str = ""):
        """Record a citation used in a filing."""
        existing = self.conn.execute(
            "SELECT id, used_in_filings FROM citation_memory WHERE citation_text = ?",
            (citation_text,)
        ).fetchone()
        
        if existing:
            filings = existing["used_in_filings"] or ""
            if filing_id not in filings:
                filings = f"{filings},{filing_id}" if filings else filing_id
            self.conn.execute(
                "UPDATE citation_memory SET used_in_filings = ?, last_verified = datetime('now') WHERE id = ?",
                (filings, existing["id"])
            )
        else:
            self.conn.execute("""
                INSERT INTO citation_memory 
                (citation_text, citation_type, used_in_filings, validated, 
                 validation_status, propositions, first_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (citation_text, citation_type, filing_id, int(validated),
                  "verified" if validated else "unverified", propositions,
                  datetime.now().isoformat()))
        self.conn.commit()
    
    # ─── SESSION CONTINUITY ───────────────────────────────────
    
    def record_finding(self, category: str, finding: str, details: str = "",
                       impact: str = "", files: str = "", session_id: str = ""):
        """Record a key finding from this session."""
        self.conn.execute("""
            INSERT INTO session_memory (session_id, category, key_finding, details, impact, files_affected)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, category, finding, details, impact, files))
        self.conn.commit()
    
    def record_correction(self, error_type: str, description: str,
                          correction: str, files: str = "",
                          root_cause: str = "", prevention: str = "",
                          session_id: str = ""):
        """Record a correction that was made."""
        self.conn.execute("""
            INSERT INTO correction_log 
            (error_type, error_description, correction_applied, files_affected,
             root_cause, prevention_rule, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (error_type, description, correction, files, root_cause, prevention, session_id))
        self.conn.commit()
    
    def record_evolution(self, component: str, change_type: str,
                         description: str, session_id: str = "", **kwargs):
        """Record a system evolution/upgrade."""
        self.conn.execute("""
            INSERT INTO evolution_log 
            (component, change_type, description, before_state, after_state,
             metrics_before, metrics_after, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (component, change_type, description,
              kwargs.get("before", ""), kwargs.get("after", ""),
              kwargs.get("metrics_before", ""), kwargs.get("metrics_after", ""),
              session_id))
        self.conn.commit()
    
    # ─── FILING DEPENDENCY GRAPH ──────────────────────────────
    
    def add_filing_dependency(self, source: str, target: str,
                               relationship: str, strength: str = "strong",
                               description: str = ""):
        """Record how one filing reinforces another."""
        self.conn.execute("""
            INSERT OR REPLACE INTO filing_dependencies 
            (source_filing, target_filing, relationship, strength, description)
            VALUES (?, ?, ?, ?, ?)
        """, (source, target, relationship, strength, description))
        self.conn.commit()
    
    # ─── OPPONENT INTELLIGENCE ────────────────────────────────
    
    def record_opponent_behavior(self, actor: str, behavior_type: str,
                                  description: str, evidence: str = "",
                                  predicted_response: str = "",
                                  counter: str = ""):
        """Record opponent behavior pattern."""
        self.conn.execute("""
            INSERT INTO opponent_memory 
            (actor, behavior_type, description, evidence_refs,
             predicted_response, counter_strategy)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (actor, behavior_type, description, evidence, predicted_response, counter))
        self.conn.commit()
    
    # ─── REPORTS ──────────────────────────────────────────────
    
    def generate_memory_report(self) -> str:
        """Generate a comprehensive memory status report."""
        counts = self.conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM filing_memory) as filing_actions,
                (SELECT COUNT(DISTINCT filing_id) FROM filing_memory) as unique_filings,
                (SELECT COUNT(*) FROM evidence_usage) as evidence_uses,
                (SELECT COUNT(*) FROM citation_memory) as citations,
                (SELECT COUNT(*) FROM citation_memory WHERE validated = 1) as verified_citations,
                (SELECT COUNT(*) FROM session_memory) as findings,
                (SELECT COUNT(*) FROM correction_log) as corrections,
                (SELECT COUNT(*) FROM evolution_log) as evolutions,
                (SELECT COUNT(*) FROM filing_dependencies) as dependencies,
                (SELECT COUNT(*) FROM opponent_memory) as opponent_intel
        """).fetchone()
        
        lines = ["# LITIGATION MEMORY STATUS", ""]
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Filing Actions | {counts['filing_actions']} |")
        lines.append(f"| Unique Filings Tracked | {counts['unique_filings']} |")
        lines.append(f"| Evidence Usage Records | {counts['evidence_uses']} |")
        lines.append(f"| Citations Tracked | {counts['citations']} ({counts['verified_citations']} verified) |")
        lines.append(f"| Session Findings | {counts['findings']} |")
        lines.append(f"| Corrections Logged | {counts['corrections']} |")
        lines.append(f"| System Evolutions | {counts['evolutions']} |")
        lines.append(f"| Filing Dependencies | {counts['dependencies']} |")
        lines.append(f"| Opponent Intel | {counts['opponent_intel']} |")
        
        return "\n".join(lines)
    
    def close(self):
        self.conn.close()


# ═══════════════════════════════════════════════════════════════
# SEED INITIAL MEMORY DATA
# ═══════════════════════════════════════════════════════════════

def seed_memory():
    """Seed the memory system with known filing dependencies and opponent intel."""
    mem = LitigationMemory()
    
    # Filing dependency graph — how filings reinforce each other
    dependencies = [
        ("F3", "F5", "enables", "critical", "Disqualification denial enables MSC superintending control"),
        ("F3", "F6", "supports", "strong", "Bias evidence in F3 feeds JTC complaint"),
        ("F3", "F9", "preserves", "critical", "Disqualification denial = primary COA appeal issue"),
        ("F4", "F5", "parallel_track", "strong", "Federal §1983 and MSC run simultaneously for pressure"),
        ("F4", "F7", "supports", "medium", "Federal discovery exposes evidence useful in custody"),
        ("F5", "F3", "escalates", "critical", "MSC can order disqualification if circuit court won't"),
        ("F6", "F3", "supports", "strong", "JTC investigation supports judicial bias claims"),
        ("F6", "F5", "supports", "strong", "JTC findings support MSC superintending control"),
        ("F7", "F8", "linked", "strong", "Custody modification and PPO termination share evidence"),
        ("F7", "F4", "feeds", "medium", "Custody denial generates more §1983 evidence"),
        ("F8", "F7", "enables", "strong", "PPO termination removes barrier to custody modification"),
        ("F9", "F3", "appeals", "critical", "COA reviews disqualification denial"),
        ("F9", "F10", "paired", "critical", "Brief and emergency motion filed together"),
        ("F1", "F2", "precedes", "critical", "TRO preserves status quo before complaint"),
        ("F2", "F4", "feeds", "medium", "Housing violations feed federal due process claims"),
    ]
    for src, tgt, rel, str_, desc in dependencies:
        mem.add_filing_dependency(src, tgt, rel, str_, desc)
    
    # Opponent intelligence
    opponents = [
        ("Emily Watson", "withholding", "Withholds parenting time as leverage — 2 major episodes (40 days + 270+ days)", "timeline evidence", "Will claim Andrew is dangerous", "Counter with HealthWest eval #1 (all zeros), Officer Randall report"),
        ("Emily Watson", "false_allegations", "Pattern of false police reports, false poisoning claim, false suicide welfare check", "police reports, medical records", "Will claim self-defense or safety concern", "Counter with dispatch callback, medical results, timeline showing retaliation"),
        ("Emily Watson", "financial_fraud", "Conceals Cody's rent, Kent insurance, Austin support", "financial declarations, trial testimony", "Will claim poverty", "Subpoena Cody's bank records, Kent County employment records"),
        ("Ronald Berry", "unauthorized_practice", "Drafts Emily's legal filings without a bar number", "filing analysis showing Berry's language patterns", "Will claim he just helped fill out forms", "Compare his language across filings — professional legal drafting by non-attorney"),
        ("Albert Watson", "assault", "Threw PPO papers through car window, forcibly removed child from Andrew's arms Oct 20 2024", "police report, witness statements", "Will claim Andrew was hostile", "Counter with timeline showing Andrew was compliant during exchange"),
        ("Cody Watson", "threats_intimidation", "MCSD-2024-02101 threatening texts, pays Emily's rent (undisclosed)", "text screenshots, bank records", "Will deny or minimize", "Present MCSD case number, text evidence, bank transfer records"),
        ("Lori Watson", "withholding_participation", "Issued ultimatum, participated in Mar 26 2024 withholding, Kent County employee ID 1190", "chatgpt statements, Kent records", "Will claim family was trying to help", "Counter with timeline showing coordinated action"),
        ("Judge McNeill", "ex_parte_pattern", "44% ex parte rate vs 12% average, 24+ ex parte orders", "SCAO data, docket analysis", "Will claim emergency circumstances justified each order", "Counter with pattern analysis — 44% cannot ALL be emergencies"),
        ("Pamela Rusco", "exceeded_authority", "Emailed prosecutor Hooker requesting warrant against Andrew — judicial secretary directing prosecution", "Rusco email to Hooker", "Will claim judge directed her", "That's WORSE — judge using staff as proxy for ex parte prosecution"),
    ]
    for actor, btype, desc, evidence, predicted, counter in opponents:
        mem.record_opponent_behavior(actor, btype, desc, evidence, predicted, counter)
    
    # Record this session's major evolutions
    evolutions = [
        ("databases", "creation", "Built 10 specialty databases (6 jurisdiction + 4 knowledge)", "0 DBs", "10 DBs, 72 tables, 492 rows"),
        ("filing_factory", "creation", "Built Filing Factory engine with 6 sub-engines", "No filing automation", "Full caption/forms/affidavit/citation/QA pipeline"),
        ("memory_system", "creation", "Built persistent LitigationMemory engine", "Session-only memory", "Cross-session persistent memory with 8 tables"),
        ("court_forms", "creation", "Built court_forms.db + F06 agent + Copilot agent", "No form awareness", "39 forms, 31 mappings, auto-fill capability"),
        ("agent_fleet", "upgrade", "Upgraded agent_base.py, agent_models.py, agent_orchestrator.py to v2.0 OMEGA", "v1.0 basic agents", "v2.0: message bus, plan-and-execute, quality scoring, adaptive retry"),
        ("omega_skills", "condensation", "Condensed 1200+ skills into 12 OMEGA skills + OMEGA-LITIGATION-SUPREME", "1200+ scattered skills", "12 OMEGA skills, 1 SUPREME (67 fused, 12 modules)"),
        ("startup_protocol", "enforcement", "Made MANBEARPIG startup mandatory 5-step protocol", "Optional startup", "Mandatory: hook → report → recall → DBs → readiness"),
    ]
    for comp, ctype, desc, before, after in evolutions:
        mem.record_evolution(comp, ctype, desc, session_id="marathon-2026-03-16", before=before, after=after)
    
    print(mem.generate_memory_report())
    mem.close()


if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    seed_memory()
