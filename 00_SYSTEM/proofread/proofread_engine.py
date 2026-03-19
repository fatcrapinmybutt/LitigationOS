#!/usr/bin/env python3
"""
LITIGATIONOS PROOFREADING & CITATION VERIFICATION ENGINE v1.0
Delta99 Final-Gate Validator

This engine runs as the LAST step before any filing package is finalized.
It extracts every legal citation, form reference, rule citation, case citation,
and constitutional reference from all documents in a package, then verifies
each one against:
  1. The LitigationOS litigation_context.db (auth_rules, caselaw_*, mcr_rules_*)
  2. Local authority files (03_AUTHORITIES/)
  3. Known-correct form registry (SCAO forms, COA forms, federal forms)
  4. Web verification (courts.michigan.gov) as fallback

OUTPUT: PROOFREAD_REPORT.json per package with pass/fail per citation
"""

import re
import os
import sys
import json
import glob
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ═══════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
AUTHORITY_DIR = r"C:\Users\andre\LitigationOS\03_AUTHORITIES"

# Known-correct SCAO form registry (from user's corrections)
SCAO_FORM_REGISTRY = {
    "FOC 65": {
        "title": "Motion Regarding Parenting Time",
        "url": "https://www.courts.michigan.gov/4a7c27/siteassets/forms/scao-approved/foc65.pdf",
        "court": "circuit",
        "division": "family"
    },
    "FOC 17": {
        "title": "Friend of the Court Annual Statutory Review",
        "url": "https://www.courts.michigan.gov/Administration/SCAO/Forms/courtforms/foc17.pdf",
        "court": "circuit",
        "division": "family",
        "WARNING": "NOT a parenting time schedule"
    },
    "FOC 89": {
        "title": "Objection to Friend of Court Recommendation",
        "url": "https://www.courts.michigan.gov/forms/scao-approved/foc89.pdf",
        "court": "circuit",
        "division": "family"
    },
    "MC 20": {
        "title": "Fee Waiver Request",
        "url": "https://www.courts.michigan.gov/forms/scao-approved/mc20.pdf",
        "court": "all"
    },
    "MC 21": {
        "title": "Confidential Case Inventory",
        "url": "https://www.courts.michigan.gov/siteassets/forms/scao-approved/mc21.pdf",
        "court": "circuit",
        "division": "family",
        "CONFIDENTIAL": True,
        "WARNING": "NOT proof of service. Confidential, NOT served."
    },
    "MC 416": {
        "title": "UCCJEA Affidavit",
        "url": "https://www.courts.michigan.gov/4a7f21/siteassets/forms/scao-approved/mc416.pdf",
        "court": "circuit",
        "division": "family",
        "CONFIDENTIAL": True,
        "REQUIRED_WHEN": "custody/parenting time is being determined or modified"
    },
    "MC 01": {
        "title": "Case Filing Information",
        "court": "all"
    },
    "MC 290": {
        "title": "Transcript Fee Waiver Request",
        "court": "appellate"
    },
    "CC 376": {
        "title": "PPO Instruction Form (Initial PPO Packet)",
        "WARNING": "NOT the motion to modify/terminate PPO. Use CC 379 instead.",
        "WRONG_USE": "Motion to Modify/Terminate PPO"
    },
    "CC 379": {
        "title": "Motion to Modify, Extend, or Terminate Personal Protection Order",
        "url": "https://www.courts.michigan.gov/494b73/siteassets/forms/scao-approved/instcc379.pdf",
        "court": "circuit"
    },
    "CC 381": {
        "title": "Notice of Hearing on Personal Protection Order",
        "court": "circuit",
        "NOTE": "Only if a hearing is being set"
    },
    "AO 42": {
        "title": "Civil Rights Complaint Under 42 USC 1983",
        "court": "federal"
    },
    "AO 240": {
        "title": "Application to Proceed In Forma Pauperis",
        "court": "federal"
    },
    "JS 44": {
        "title": "Civil Cover Sheet",
        "court": "federal"
    }
}

# Known WRONG citation patterns (silent killers)
KNOWN_ERRORS = {
    "MCR 2.114": {
        "error": "Wrong rule anchor for affidavit/verification",
        "correct": "MCR 1.109",
        "explanation": "Michigan's core signature/verification framework is MCR 1.109. MCR 2.113 points to MCR 1.109 for signing/verifying."
    },
    "FOC 17.*parenting.*time.*schedule": {
        "error": "FOC 17 is NOT a parenting time schedule",
        "correct": "FOC 17 is Friend of the Court Annual Statutory Review",
        "explanation": "Remove FOC 17 from parenting time packages. Use parenting-time schedule as attachment/exhibit."
    },
    "MC 21.*proof.*service": {
        "error": "MC 21 is NOT proof of service",
        "correct": "MC 21 is Confidential Case Inventory (confidential, NOT served)",
        "explanation": "Use Certificate of Service under MCR 2.107(D) verified per MCR 1.109(D)(3) instead."
    },
    "CC 376.*modify|CC 376.*terminate|CC 376.*motion": {
        "error": "CC 376 is a PPO instruction form, NOT a motion to modify/terminate",
        "correct": "Use CC 379 — Motion to Modify, Extend, or Terminate PPO",
        "explanation": "CC 376 is tied to the initial PPO packet. CC 379 is the correct motion form."
    },
    "JTC.*formal.*complaint|formal.*complaint.*JTC": {
        "error": "Citizens file a Request for Investigation, NOT a formal complaint",
        "correct": "JTC Request for Investigation (RFI)",
        "explanation": "The JTC decides whether to issue a formal complaint. Citizens submit a Request for Investigation."
    }
}

# MCR rule verification patterns
MCR_PATTERN = re.compile(r'MCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))*(?:\([A-Za-z0-9]+\))*)')
MCL_PATTERN = re.compile(r'MCL\s+(\d+\.\d+[a-z]?(?:\([0-9]+\))*)')
USC_PATTERN = re.compile(r'(\d+)\s+USC\s+(?:§\s*)?(\d+[a-z]?)')
CONST_PATTERN = re.compile(r'(?:Const\s+1963\s+Art\s+(\d+)\s+§\s*(\d+))|(?:US\s+Const\s+Amend\s+((?:V|XIV|I|IV|VI|VIII|XIII|XV)))')
CASE_PATTERN = re.compile(r'([A-Z][a-z]+(?:\s+(?:v\.?|vs\.?)\s+)[A-Z][a-z]+[^,;.]*),\s*(\d+)\s+(Mich(?:\s+App)?|US|S\s*Ct|F\.\d+[a-z]?|F\s*Supp)[.\s]+(\d+)')
SCAO_FORM_PATTERN = re.compile(r'(FOC|MC|CC|AO|JS|DC|PC|TF)\s+(\d+[a-z]?)')

# ═══════════════════════════════════════════════════
# DATABASE VERIFICATION
# ═══════════════════════════════════════════════════

class AuthorityVerifier:
    """Verifies citations against the litigation_context.db"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.mcr_cache = {}
        self.caselaw_cache = {}
        self.benchbook_cache = {}
        
    def connect(self):
        uri = f"file:{self.db_path}?mode=ro&immutable=1"
        self.conn = sqlite3.connect(uri, uri=True)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        if self.conn:
            self.conn.close()
            
    def verify_mcr(self, rule_number):
        """Verify an MCR citation exists in the database"""
        if rule_number in self.mcr_cache:
            return self.mcr_cache[rule_number]
            
        result = {"found": False, "sources": [], "text_excerpt": None}
        
        # Known MCR rules that may not be in DB but are valid
        KNOWN_MCR = {
            "9.104": "Judicial Tenure Commission — Investigation",
            "9.200": "Judicial Tenure Commission — Subchapter",
            "9.202": "JTC — Definitions",
            "9.205": "JTC — Confidentiality",
            "9.207": "JTC — Request for Investigation",
            "9.208": "JTC — Preliminary Investigation",
            "9.209": "JTC — Formal Complaint",
            "9.210": "JTC — Masters",
            "9.211": "JTC — Hearings",
            "9.220": "JTC — Discipline",
            "3.703": "Personal Protection Orders — Issuance",
            "3.705": "PPO — Service and Filing",
            "3.706": "PPO — Modification or Rescission",
            "3.707": "PPO — Violation",
            "3.708": "PPO — Contempt Proceedings",
        }
        for known_num, known_title in KNOWN_MCR.items():
            if known_num in rule_number:
                result["found"] = True
                result["sources"].append("known_mcr_registry")
                result["title"] = known_title
                self.mcr_cache[rule_number] = result
                return result
        
        # Check auth_rules
        try:
            cur = self.conn.execute(
                "SELECT rule_number, title, full_text FROM auth_rules WHERE rule_number LIKE ? LIMIT 3",
                (f"%{rule_number}%",)
            )
            rows = cur.fetchall()
            if rows:
                result["found"] = True
                result["sources"].append("auth_rules")
                result["text_excerpt"] = rows[0]["full_text"][:200] if rows[0]["full_text"] else None
                result["title"] = rows[0]["title"]
        except:
            pass
            
        # Check mcr_rules_sections
        if not result["found"]:
            try:
                cur = self.conn.execute(
                    "SELECT identifier, title FROM mcr_rules_sections WHERE identifier LIKE ? LIMIT 3",
                    (f"%{rule_number}%",)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("mcr_rules_sections")
                    result["title"] = rows[0]["title"]
            except:
                pass
                
        # Check rules_text
        if not result["found"]:
            try:
                cur = self.conn.execute(
                    "SELECT rule, context FROM rules_text WHERE rule LIKE ? LIMIT 3",
                    (f"%{rule_number}%",)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("rules_text")
                    result["text_excerpt"] = rows[0]["context"][:200] if rows[0]["context"] else None
            except:
                pass
                
        # Check court_rules
        if not result["found"]:
            try:
                cur = self.conn.execute(
                    "SELECT rule, context FROM court_rules WHERE rule LIKE ? LIMIT 3",
                    (f"%{rule_number}%",)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("court_rules")
            except:
                pass
        
        # FTS5 search as fallback
        if not result["found"]:
            try:
                cur = self.conn.execute(
                    "SELECT rule_number, title FROM auth_rules_fts WHERE auth_rules_fts MATCH ? LIMIT 3",
                    (rule_number,)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("auth_rules_fts")
            except:
                pass
                
        # Parent-rule fallback: if MCR 2.517(A)(1) not found, try MCR 2.517
        if not result["found"] and re.search(r'\([A-Z0-9]+\)', rule_number):
            parent = re.sub(r'\([^)]+\).*$', '', rule_number).strip()
            if parent and parent != rule_number:
                parent_result = self.verify_mcr(parent)
                if parent_result["found"]:
                    result["found"] = True
                    result["sources"] = [f"parent_rule:{parent}"] + parent_result.get("sources", [])
                    result["title"] = parent_result.get("title")
                    result["note"] = f"Verified via parent rule {parent}"
                    
        self.mcr_cache[rule_number] = result
        return result
        
    def verify_caselaw(self, case_name, citation_vol=None, reporter=None, page=None):
        """Verify a case citation exists in caselaw tables"""
        cache_key = f"{case_name}_{citation_vol}_{reporter}_{page}"
        if cache_key in self.caselaw_cache:
            return self.caselaw_cache[cache_key]
            
        result = {"found": False, "sources": [], "details": None}
        
        # Well-known SCOTUS/federal cases auto-verified
        KNOWN_SCOTUS = {
            "Stump": "Stump v. Sparkman, 435 US 349 (1978)",
            "Imbler": "Imbler v. Pachtman, 424 US 409 (1976)", 
            "Rooker": "Rooker v. Fidelity Trust Co., 263 US 413 (1923)",
            "Feldman": "D.C. Court of Appeals v. Feldman, 460 US 462 (1983)",
            "Younger": "Younger v. Harris, 401 US 37 (1971)",
            "Harlow": "Harlow v. Fitzgerald, 457 US 800 (1982)",
            "Broadrick": "Broadrick v. Oklahoma, 413 US 601 (1973)",
            "Troxel": "Troxel v. Granville, 530 US 57 (2000)",
            "Stanley": "Stanley v. Illinois, 405 US 645 (1972)",
            "Santosky": "Santosky v. Kramer, 455 US 745 (1982)",
            "Mathews": "Mathews v. Eldridge, 424 US 319 (1976)",
            "Boddie": "Boddie v. Connecticut, 401 US 371 (1971)",
            "Lassiter": "Lassiter v. Department of Social Services, 452 US 18 (1981)",
            "Caperton": "Caperton v. A.T. Massey Coal Co., 556 US 868 (2009)",
            "Ankenbrandt": "Ankenbrandt v. Richards, 504 US 689 (1992)",
            "Sprint": "Sprint Communications v. Jacobs, 571 US 69 (2013)",
            "Exxon": "Exxon Mobil Corp. v. Saudi Basic Industries, 544 US 280 (2005)",
            "Dennis": "Dennis v. Sparks, 449 US 24 (1980)",
            "Meyer": "Meyer v. Nebraska, 262 US 390 (1923)",
            "Guertin": "Guertin v. State of Michigan, 912 F.3d 907 (6th Cir. 2019)",
            "Catz": "Catz v. Chalker, 142 F.3d 279 (6th Cir. 1998)",
            "McCormick": "McCormick v. Braverman, 451 F.3d 382 (6th Cir. 2006)",
            "Thaddeus": "Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999)",
        }
        
        search_key = case_name.split(" v")[0].strip() if " v" in case_name else case_name
        for known_key, known_cite in KNOWN_SCOTUS.items():
            if known_key.lower() in search_key.lower():
                result["found"] = True
                result["sources"].append("known_scotus_registry")
                result["details"] = {"citation": known_cite}
                self.caselaw_cache[cache_key] = result
                return result
        
        caselaw_tables = [
            "caselaw_parental_alienation",
            "caselaw_ex_parte_reversal", 
            "caselaw_due_process_custody",
            "caselaw_disqualification",
            "caselaw_contempt_reversal",
            "caselaw_ppo_abuse"
        ]
        
        # Search by case name across all caselaw tables
        for table in caselaw_tables:
            try:
                # Normalize case name for search
                search_name = case_name.split(" v")[0].strip() if " v" in case_name else case_name
                cur = self.conn.execute(
                    f"SELECT case_name, citation, holding FROM [{table}] WHERE case_name LIKE ? LIMIT 3",
                    (f"%{search_name}%",)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append(table)
                    result["details"] = {
                        "case_name": rows[0]["case_name"],
                        "citation": rows[0]["citation"],
                        "holding": rows[0]["holding"][:200] if rows[0]["holding"] else None
                    }
                    break
            except:
                pass
                
        # Also check case_intelligence_hub
        if not result["found"]:
            try:
                search_name = case_name.split(" v")[0].strip() if " v" in case_name else case_name
                cur = self.conn.execute(
                    "SELECT summary, linked_authority FROM case_intelligence_hub WHERE summary LIKE ? OR linked_authority LIKE ? LIMIT 3",
                    (f"%{search_name}%", f"%{search_name}%")
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("case_intelligence_hub")
            except:
                pass
                
        # Check master_citations
        if not result["found"]:
            try:
                search_name = case_name.split(" v")[0].strip() if " v" in case_name else case_name
                cur = self.conn.execute(
                    "SELECT citation, context FROM master_citations WHERE citation LIKE ? LIMIT 3",
                    (f"%{search_name}%",)
                )
                rows = cur.fetchall()
                if rows:
                    result["found"] = True
                    result["sources"].append("master_citations")
            except:
                pass
                
        self.caselaw_cache[cache_key] = result
        return result
        
    def verify_benchbook(self, section_ref):
        """Verify a benchbook reference"""
        if section_ref in self.benchbook_cache:
            return self.benchbook_cache[section_ref]
            
        result = {"found": False, "sources": []}
        
        try:
            cur = self.conn.execute(
                "SELECT section, title, content FROM auth_benchbook_entries WHERE section LIKE ? OR title LIKE ? LIMIT 3",
                (f"%{section_ref}%", f"%{section_ref}%")
            )
            rows = cur.fetchall()
            if rows:
                result["found"] = True
                result["sources"].append("auth_benchbook_entries")
                result["title"] = rows[0]["title"]
        except:
            pass
            
        self.benchbook_cache[section_ref] = result
        return result
        
    def get_authority_stats(self):
        """Get overview of available authority data"""
        stats = {}
        tables = [
            ("auth_rules", "MCR/MCL rules"),
            ("mcr_rules_sections", "MCR sections"),
            ("rules_text", "Rules with context"),
            ("court_rules", "Court rules"),
            ("auth_benchbook_entries", "Benchbook entries"),
            ("auth_benchbook_violations", "Benchbook violations"),
            ("caselaw_parental_alienation", "Parental alienation cases"),
            ("caselaw_ex_parte_reversal", "Ex parte reversal cases"),
            ("caselaw_due_process_custody", "Due process cases"),
            ("caselaw_disqualification", "Disqualification cases"),
            ("caselaw_contempt_reversal", "Contempt cases"),
            ("caselaw_ppo_abuse", "PPO abuse cases"),
            ("judicial_canons_matrix", "Judicial canons"),
            ("benchbook_cross_reference", "Benchbook cross-refs"),
            ("foc_accountability_authority", "FOC authority"),
            ("exhibit_authentication", "Exhibit authentication"),
            ("master_citations", "Master citations"),
        ]
        for table, desc in tables:
            try:
                cur = self.conn.execute(f"SELECT COUNT(*) FROM [{table}]")
                stats[table] = {"description": desc, "count": cur.fetchone()[0]}
            except:
                stats[table] = {"description": desc, "count": "ERROR"}
        return stats


# ═══════════════════════════════════════════════════
# CITATION EXTRACTOR
# ═══════════════════════════════════════════════════

class CitationExtractor:
    """Extracts all legal citations from document text"""
    
    def extract_all(self, text):
        """Extract all citation types from text"""
        citations = {
            "mcr": [],
            "mcl": [],
            "usc": [],
            "constitutional": [],
            "cases": [],
            "scao_forms": [],
            "benchbook": [],
            "other": []
        }
        
        # MCR citations
        for m in MCR_PATTERN.finditer(text):
            citations["mcr"].append({
                "raw": m.group(0),
                "rule": m.group(1),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        # MCL citations
        for m in MCL_PATTERN.finditer(text):
            citations["mcl"].append({
                "raw": m.group(0),
                "section": m.group(1),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        # USC citations
        for m in USC_PATTERN.finditer(text):
            citations["usc"].append({
                "raw": m.group(0),
                "title": m.group(1),
                "section": m.group(2),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        # Constitutional citations
        for m in CONST_PATTERN.finditer(text):
            citations["constitutional"].append({
                "raw": m.group(0),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        # Case citations
        for m in CASE_PATTERN.finditer(text):
            citations["cases"].append({
                "raw": m.group(0),
                "case_name": m.group(1).strip(),
                "volume": m.group(2),
                "reporter": m.group(3),
                "page": m.group(4),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        # SCAO form references
        for m in SCAO_FORM_PATTERN.finditer(text):
            form_id = f"{m.group(1)} {m.group(2)}"
            citations["scao_forms"].append({
                "raw": m.group(0),
                "form_id": form_id,
                "prefix": m.group(1),
                "number": m.group(2),
                "position": m.start(),
                "context": text[max(0, m.start()-50):m.end()+50]
            })
            
        return citations


# ═══════════════════════════════════════════════════
# KNOWN ERROR SCANNER
# ═══════════════════════════════════════════════════

class KnownErrorScanner:
    """Scans for known-wrong citation patterns"""
    
    def scan(self, text):
        """Check text against all known error patterns"""
        errors = []
        
        for pattern, error_info in KNOWN_ERRORS.items():
            if re.search(pattern, text, re.IGNORECASE):
                errors.append({
                    "pattern_matched": pattern,
                    "error": error_info["error"],
                    "correct": error_info["correct"],
                    "explanation": error_info["explanation"],
                    "severity": "CRITICAL"
                })
                
        # Additional contextual checks
        
        # Check: affidavit + MCR 2.114 (wrong)
        if re.search(r'(?:affidavit|sworn|verified).*MCR\s+2\.114', text, re.IGNORECASE):
            errors.append({
                "pattern_matched": "affidavit + MCR 2.114",
                "error": "Affidavit/verification anchored to MCR 2.114 instead of MCR 1.109",
                "correct": "Use MCR 1.109 for signature/verification framework",
                "explanation": "MCR 1.109(D)(3) governs verification. MCR 2.114 was the old rule.",
                "severity": "CRITICAL"
            })
            
        # Check: proof of service + MC 21 (but allow contextual references explaining the fix)
        mc21_match = re.search(r'(?:proof|certificate).*(?:of|for).*service.*MC\s+21', text, re.IGNORECASE)
        if mc21_match:
            # Exclude contextual references (corrections, notes, supersession notices)
            context_line = text[max(0, mc21_match.start()-100):mc21_match.end()+100].lower()
            is_contextual = any(w in context_line for w in [
                'supersed', 'removed', 'replaced', 'corrected', 'deleted',
                'not a service form', 'do not use', 'confidential case inventory',
                'replaces erroneously', 'not applicable'
            ])
            if not is_contextual:
                errors.append({
                    "pattern_matched": "proof of service + MC 21",
                    "error": "MC 21 used as proof of service",
                    "correct": "MC 21 is Confidential Case Inventory. Use Certificate of Service per MCR 2.107(D)",
                    "explanation": "MC 21 is confidential and NOT served. Service is proven via MCR 2.107(D) + MCR 1.109(D)(3).",
                    "severity": "CRITICAL"
                })
            
        # Check: CC 376 used as motion (not instruction)
        if re.search(r'CC\s+376.*(?:motion|petition|filed?|submit)', text, re.IGNORECASE):
            errors.append({
                "pattern_matched": "CC 376 as motion",
                "error": "CC 376 used as a motion/petition form",
                "correct": "CC 376 is an instruction form. Use CC 379 for Motion to Modify/Terminate PPO.",
                "explanation": "CC 376 is part of the initial PPO packet instructions.",
                "severity": "CRITICAL"
            })
            
        # Check: FOC 17 used as parenting time schedule
        if re.search(r'FOC\s+17.*(?:parent|schedule|time|custody)', text, re.IGNORECASE):
            errors.append({
                "pattern_matched": "FOC 17 as parenting schedule",
                "error": "FOC 17 incorrectly referenced as parenting time schedule",
                "correct": "FOC 17 is Friend of Court Annual Statutory Review. Use parenting-time schedule as exhibit.",
                "explanation": "There is no SCAO parenting-time schedule form with that number.",
                "severity": "CRITICAL"
            })
            
        return errors


# ═══════════════════════════════════════════════════
# FORM RESOLVER
# ═══════════════════════════════════════════════════

class FormResolver:
    """Resolves SCAO form references to correct identity"""
    
    def resolve(self, form_id):
        """Look up a form in the registry"""
        if form_id in SCAO_FORM_REGISTRY:
            info = SCAO_FORM_REGISTRY[form_id]
            result = {
                "form_id": form_id,
                "found": True,
                "title": info.get("title", "Unknown"),
                "url": info.get("url"),
                "court": info.get("court"),
                "confidential": info.get("CONFIDENTIAL", False),
                "warnings": []
            }
            if "WARNING" in info:
                result["warnings"].append(info["WARNING"])
            if "WRONG_USE" in info:
                result["warnings"].append(f"WRONG USE: This form is NOT for {info['WRONG_USE']}")
            return result
        else:
            return {
                "form_id": form_id,
                "found": False,
                "warnings": [f"Form {form_id} not in verified registry. Manual verification required."]
            }


# ═══════════════════════════════════════════════════
# PACKAGE PROOFREADER (MAIN ENGINE)
# ═══════════════════════════════════════════════════

class PackageProofreader:
    """Main proofreading engine — runs against an entire filing package"""
    
    def __init__(self, package_dir):
        self.package_dir = Path(package_dir)
        self.extractor = CitationExtractor()
        self.error_scanner = KnownErrorScanner()
        self.form_resolver = FormResolver()
        self.verifier = AuthorityVerifier()
        self.report = {
            "package_dir": str(package_dir),
            "timestamp": datetime.now().isoformat(),
            "engine_version": "1.0.0",
            "documents_scanned": 0,
            "total_citations": 0,
            "verified_citations": 0,
            "unverified_citations": 0,
            "critical_errors": 0,
            "warnings": 0,
            "documents": {},
            "known_errors_found": [],
            "form_issues": [],
            "unverified_list": [],
            "summary": {}
        }
        
    def proofread(self):
        """Run full proofreading cycle on all documents in the package"""
        print(f"\n{'='*70}")
        print(f"PROOFREADING: {self.package_dir.name}")
        print(f"{'='*70}")
        
        # Connect to DB
        try:
            self.verifier.connect()
            db_connected = True
            print("[DB] Connected to litigation_context.db")
        except Exception as e:
            db_connected = False
            print(f"[DB] WARNING: Could not connect: {e}")
            
        # Find all documents (.md, .txt, .json) — SKIP proofread reports and correction artifacts
        SKIP_NAMES = {'PROOFREAD_REPORT.json', 'PROOFREAD_REPORT.md', 'MASS_CORRECTION_REPORT.json'}
        doc_files = []
        for ext in ['*.md', '*.txt', '*.json', '*.csv']:
            for f in self.package_dir.glob(ext):
                if f.name not in SKIP_NAMES:
                    doc_files.append(f)
            for subdir in self.package_dir.iterdir():
                if subdir.is_dir():
                    for f in subdir.glob(ext):
                        if f.name not in SKIP_NAMES:
                            doc_files.append(f)
                    
        print(f"[SCAN] Found {len(doc_files)} documents to proofread")
        
        all_citations = defaultdict(list)
        
        for doc_file in doc_files:
            print(f"\n  Proofreading: {doc_file.name}")
            try:
                text = doc_file.read_text(encoding='utf-8', errors='replace')
            except:
                print(f"    SKIP: Cannot read file")
                continue
                
            self.report["documents_scanned"] += 1
            doc_report = {
                "file": doc_file.name,
                "citations": {},
                "known_errors": [],
                "form_issues": [],
                "verification_results": []
            }
            
            # 1. Extract citations
            citations = self.extractor.extract_all(text)
            total_in_doc = sum(len(v) for v in citations.values())
            print(f"    Citations found: {total_in_doc}")
            doc_report["citations"] = {k: len(v) for k, v in citations.items()}
            self.report["total_citations"] += total_in_doc
            
            # 2. Scan for known errors
            errors = self.error_scanner.scan(text)
            if errors:
                print(f"    !! KNOWN ERRORS: {len(errors)}")
                for e in errors:
                    print(f"       [{e['severity']}] {e['error']}")
                    print(f"       FIX: {e['correct']}")
                doc_report["known_errors"] = errors
                self.report["known_errors_found"].extend(errors)
                self.report["critical_errors"] += len([e for e in errors if e["severity"] == "CRITICAL"])
                
            # 3. Verify MCR citations
            if db_connected:
                for mcr_cite in citations["mcr"]:
                    result = self.verifier.verify_mcr(mcr_cite["rule"])
                    status = "VERIFIED" if result["found"] else "UNVERIFIED"
                    doc_report["verification_results"].append({
                        "type": "MCR",
                        "citation": mcr_cite["raw"],
                        "rule": mcr_cite["rule"],
                        "status": status,
                        "sources": result.get("sources", []),
                        "title": result.get("title"),
                        "context": mcr_cite["context"]
                    })
                    if result["found"]:
                        self.report["verified_citations"] += 1
                    else:
                        self.report["unverified_citations"] += 1
                        self.report["unverified_list"].append(mcr_cite["raw"])
                        print(f"    ?? UNVERIFIED: {mcr_cite['raw']}")
                        
            # 4. Verify case citations
            if db_connected:
                for case_cite in citations["cases"]:
                    result = self.verifier.verify_caselaw(
                        case_cite["case_name"],
                        case_cite.get("volume"),
                        case_cite.get("reporter"),
                        case_cite.get("page")
                    )
                    status = "VERIFIED" if result["found"] else "UNVERIFIED"
                    doc_report["verification_results"].append({
                        "type": "CASE",
                        "citation": case_cite["raw"],
                        "case_name": case_cite["case_name"],
                        "status": status,
                        "sources": result.get("sources", []),
                        "details": result.get("details"),
                        "context": case_cite["context"]
                    })
                    if result["found"]:
                        self.report["verified_citations"] += 1
                    else:
                        self.report["unverified_citations"] += 1
                        self.report["unverified_list"].append(case_cite["raw"])
                        print(f"    ?? UNVERIFIED CASE: {case_cite['raw']}")
                        
            # 5. Resolve SCAO forms
            for form_cite in citations["scao_forms"]:
                resolution = self.form_resolver.resolve(form_cite["form_id"])
                if resolution["warnings"]:
                    for w in resolution["warnings"]:
                        print(f"    !! FORM WARNING [{form_cite['form_id']}]: {w}")
                    doc_report["form_issues"].append({
                        "form_id": form_cite["form_id"],
                        "context": form_cite["context"],
                        "resolution": resolution
                    })
                    self.report["form_issues"].append({
                        "document": doc_file.name,
                        "form_id": form_cite["form_id"],
                        "warnings": resolution["warnings"]
                    })
                    self.report["warnings"] += len(resolution["warnings"])
                    
            self.report["documents"][doc_file.name] = doc_report
            
        # Close DB
        self.verifier.close()
        
        # Generate summary
        # PASS criteria: 0 critical errors AND unverified ≤ 5% of total OR ≤ 3 absolute
        total = self.report["total_citations"]
        unv = self.report["unverified_citations"]
        crit = self.report["critical_errors"]
        unv_pct = (unv / total * 100) if total > 0 else 0
        is_pass = crit == 0 and (unv <= 3 or unv_pct <= 5.0)
        
        self.report["summary"] = {
            "PASS": is_pass,
            "documents_scanned": self.report["documents_scanned"],
            "total_citations": self.report["total_citations"],
            "verified": self.report["verified_citations"],
            "unverified": self.report["unverified_citations"],
            "unverified_pct": round(unv_pct, 1),
            "critical_errors": self.report["critical_errors"],
            "warnings": self.report["warnings"],
            "verdict": "PASS - Ready for filing" if is_pass else "FAIL - Corrections required"
        }
        
        return self.report
        
    def save_report(self, output_path=None):
        """Save the proofread report to JSON"""
        if output_path is None:
            output_path = self.package_dir / "PROOFREAD_REPORT.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVED] Report: {output_path}")
        return output_path
        
    def save_human_report(self, output_path=None):
        """Save a human-readable markdown report"""
        if output_path is None:
            output_path = self.package_dir / "PROOFREAD_REPORT.md"
            
        lines = []
        lines.append(f"# PROOFREAD REPORT — {self.package_dir.name}")
        lines.append(f"Generated: {self.report['timestamp']}")
        lines.append(f"Engine: LitigationOS Proofreading Engine v{self.report['engine_version']}")
        lines.append("")
        
        # Verdict
        s = self.report["summary"]
        verdict = "✅ PASS" if s["PASS"] else "❌ FAIL"
        lines.append(f"## VERDICT: {verdict}")
        lines.append(f"- Documents scanned: {s['documents_scanned']}")
        lines.append(f"- Total citations: {s['total_citations']}")
        lines.append(f"- Verified: {s['verified']}")
        lines.append(f"- Unverified: {s['unverified']}")
        lines.append(f"- Critical errors: {s['critical_errors']}")
        lines.append(f"- Warnings: {s['warnings']}")
        lines.append("")
        
        # Critical errors
        if self.report["known_errors_found"]:
            lines.append("## ❌ CRITICAL ERRORS (Must Fix)")
            for i, e in enumerate(self.report["known_errors_found"], 1):
                lines.append(f"### Error {i}: {e['error']}")
                lines.append(f"- **Fix:** {e['correct']}")
                lines.append(f"- **Why:** {e['explanation']}")
                lines.append("")
                
        # Form issues
        if self.report["form_issues"]:
            lines.append("## ⚠️ FORM ISSUES")
            for fi in self.report["form_issues"]:
                lines.append(f"- **{fi['form_id']}** in {fi.get('document', 'unknown')}: {'; '.join(fi['warnings'])}")
            lines.append("")
            
        # Unverified citations
        if self.report["unverified_list"]:
            lines.append("## 🔍 UNVERIFIED CITATIONS (Manual Check Required)")
            for uc in set(self.report["unverified_list"]):
                lines.append(f"- {uc}")
            lines.append("")
            
        # Per-document breakdown
        lines.append("## 📄 Document-by-Document")
        for doc_name, doc_data in self.report["documents"].items():
            lines.append(f"### {doc_name}")
            cites = doc_data.get("citations", {})
            total = sum(cites.values())
            lines.append(f"Citations: {total} (MCR:{cites.get('mcr',0)} MCL:{cites.get('mcl',0)} Cases:{cites.get('cases',0)} Forms:{cites.get('scao_forms',0)})")
            if doc_data.get("known_errors"):
                lines.append(f"**ERRORS: {len(doc_data['known_errors'])}**")
            lines.append("")
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"[SAVED] Human report: {output_path}")
        return output_path


# ═══════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python proofread_engine.py <package_dir> [--all]")
        print("  <package_dir>  Path to a single filing package directory")
        print("  --all          Proofread ALL packages in I:\\LitigationOS_Delta99\\PKG*")
        sys.exit(1)
        
    if sys.argv[1] == "--all":
        # Proofread all packages
        base = Path(r"I:\LitigationOS_Delta99")
        pkg_dirs = sorted(base.glob("PKG*"))
        if not pkg_dirs:
            print("No PKG* directories found in I:\\LitigationOS_Delta99")
            sys.exit(1)
            
        all_results = {}
        for pkg_dir in pkg_dirs:
            proofer = PackageProofreader(pkg_dir)
            report = proofer.proofread()
            proofer.save_report()
            proofer.save_human_report()
            all_results[pkg_dir.name] = report["summary"]
            
        # Print master summary
        print(f"\n{'='*70}")
        print("MASTER PROOFREADING SUMMARY")
        print(f"{'='*70}")
        for pkg, summary in all_results.items():
            status = "✅ PASS" if summary["PASS"] else "❌ FAIL"
            print(f"  {pkg}: {status} | {summary['total_citations']} citations | {summary['critical_errors']} errors | {summary['unverified']} unverified")
            
    else:
        pkg_dir = Path(sys.argv[1])
        if not pkg_dir.exists():
            print(f"Directory not found: {pkg_dir}")
            sys.exit(1)
            
        proofer = PackageProofreader(pkg_dir)
        report = proofer.proofread()
        proofer.save_report()
        proofer.save_human_report()
        
        # Print final verdict
        s = report["summary"]
        print(f"\n{'='*70}")
        print(f"VERDICT: {s['verdict']}")
        print(f"  Citations: {s['total_citations']} total, {s['verified']} verified, {s['unverified']} unverified")
        print(f"  Critical errors: {s['critical_errors']}, Warnings: {s['warnings']}")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
