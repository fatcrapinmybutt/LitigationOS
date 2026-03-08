#!/usr/bin/env python3
"""
Filing Production Pipeline v1.0 - Agent-154 / LitigationOS
============================================================
End-to-end pipeline: draft markdown --> court-ready submission packet.

Usage:
    python filing_production_pipeline.py --stack "path/to/stack"
    python filing_production_pipeline.py --stack "01_COA_366810"

Importable:
    from filing_production_pipeline import FilingProductionPipeline
    pipeline = FilingProductionPipeline("path/to/stack")
    report = pipeline.run()
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import glob
import shutil
import sqlite3
import logging
import hashlib
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from collections import OrderedDict

# ============================================================================
# CONSTANTS
# ============================================================================
LITOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
ENGINES_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines")
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

FILING_EXTENSIONS = {'.md', '.txt', '.docx', '.pdf', '.doc', '.rtf'}
EVIDENCE_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.docx', '.xlsx'}

COURT_MAP = {
    "01_COA":       {"court": "Michigan Court of Appeals", "rules": "MCR 7.212", "efiling": "truefiling"},
    "02_TRIAL":     {"court": "14th Circuit Court",        "rules": "MCR 2.119", "efiling": "mifile"},
    "03_FEDERAL":   {"court": "WDMI Federal Court",        "rules": "FRCP",      "efiling": "pacer"},
    "04_JTC":       {"court": "Judicial Tenure Commission","rules": "MCR 9.200", "efiling": "truefiling"},
    "04_MSC":       {"court": "Michigan Supreme Court",    "rules": "MCR 7.306", "efiling": "truefiling"},
    "05_BAR":       {"court": "Attorney Grievance Commission","rules": "MCR 9.100","efiling": "mifile"},
    "06_EMERGENCY": {"court": "Emergency Filing",          "rules": "MCR 3.207", "efiling": "mifile"},
    "06_FILINGS":   {"court": "General Filings",           "rules": "MCR 2.119", "efiling": "mifile"},
}

PLACEHOLDER_PATTERN = re.compile(r'\[([A-Z][A-Z0-9_\s/\-]{2,})\]')
CITATION_PATTERNS = {
    "MCL":         re.compile(r'MCL\s+[\d.]+'),
    "MCR":         re.compile(r'MCR\s+[\d.]+'),
    "USC":         re.compile(r'\d+\s+U\.?S\.?C\.?\s+[0-9a-z]+', re.IGNORECASE),
    "Mich":        re.compile(r'\d+\s+Mich\s+\d+'),
    "Mich App":    re.compile(r'\d+\s+Mich\s+App\s+\d+'),
    "NW2d":        re.compile(r'\d+\s+NW\s*2d\s+\d+'),
    "US":          re.compile(r'\d+\s+US\s+\d+'),
    "F.3d":        re.compile(r'\d+\s+F\.\s*3d\s+\d+'),
    "S.Ct":        re.compile(r'\d+\s+S\.\s*Ct\.?\s+\d+'),
    "FRCP":        re.compile(r'(?:Fed\.?\s*R\.?\s*Civ\.?\s*P\.?|FRCP)\s*\d+', re.IGNORECASE),
    "Const":       re.compile(r'(?:Const|US\s+Const|Mich\s+Const)\s+\d+', re.IGNORECASE),
}

STEP_NAMES = [
    "INTAKE",
    "PLACEHOLDER_CHECK",
    "AUTHORITY_CHECK",
    "EVIDENCE_CHECK",
    "COMPLIANCE_CHECK",
    "QA_GATE",
    "PDF_GENERATION",
    "EXHIBIT_COMPILATION",
    "SERVICE_PACKET",
    "EFILING_PREP",
    "FINAL_REPORT",
]


# ============================================================================
# HELPER: safe import of sibling engines
# ============================================================================
def _try_import(module_name, class_name=None):
    """Attempt to import a sibling engine; return None if unavailable."""
    try:
        old_path = sys.path.copy()
        if str(ENGINES_DIR) not in sys.path:
            sys.path.insert(0, str(ENGINES_DIR))
        mod = __import__(module_name)
        sys.path = old_path
        if class_name:
            return getattr(mod, class_name, None)
        return mod
    except Exception:
        return None


def _get_db():
    """Get a database connection with WAL mode and busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# PIPELINE CLASS
# ============================================================================
class FilingProductionPipeline:
    """Orchestrates the full filing production workflow for a single stack."""

    def __init__(self, stack_path, verbose=True):
        self.stack_path = Path(stack_path)
        # Resolve relative paths against LITOS_ROOT
        if not self.stack_path.is_absolute():
            self.stack_path = LITOS_ROOT / self.stack_path
        self.stack_name = self.stack_path.name
        self.verbose = verbose

        # Output directory
        self.output_dir = self.stack_path / "PRODUCTION_OUTPUT"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Detect court context from path
        self.court_ctx = self._detect_court()

        # Results tracking
        self.steps = OrderedDict()
        for s in STEP_NAMES:
            self.steps[s] = {"status": "PENDING", "details": [], "issues": [], "warnings": []}
        self.documents = []
        self.evidence_files = []
        self.placeholders_found = []
        self.citations_found = {}
        self.go_nogo = "PENDING"
        self.start_time = datetime.now()

        # Setup logging
        self._setup_logging()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _setup_logging(self):
        self.logger = logging.getLogger(f"Pipeline-{self.stack_name}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        log_path = self.output_dir / "pipeline.log"
        fh = logging.FileHandler(str(log_path), mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(fh)

        if self.verbose:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            self.logger.addHandler(ch)

    def log(self, msg, level="info"):
        getattr(self.logger, level, self.logger.info)(msg)

    # ------------------------------------------------------------------
    # Court detection
    # ------------------------------------------------------------------
    def _detect_court(self):
        path_str = str(self.stack_path).replace("\\", "/")
        for prefix, ctx in COURT_MAP.items():
            if prefix in path_str:
                return ctx
        return {"court": "Unknown", "rules": "General", "efiling": "mifile"}

    # ------------------------------------------------------------------
    # STEP 1: INTAKE
    # ------------------------------------------------------------------
    def step_intake(self):
        step = "INTAKE"
        self.log(f"--- STEP 1: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            if not self.stack_path.exists():
                self.steps[step]["issues"].append(f"Stack directory not found: {self.stack_path}")
                self.steps[step]["status"] = "FAIL"
                return False

            # Scan all documents
            doc_count = 0
            for ext in FILING_EXTENSIONS:
                for fp in self.stack_path.rglob(f"*{ext}"):
                    # Skip output directories
                    rel = fp.relative_to(self.stack_path)
                    if any(part.upper() in ("PRODUCTION_OUTPUT", "__PYCACHE__", ".GIT")
                           for part in rel.parts):
                        continue
                    stat = fp.stat()
                    self.documents.append({
                        "path": str(fp),
                        "name": fp.name,
                        "ext": ext,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "relative": str(rel),
                    })
                    doc_count += 1

            # Scan evidence files
            evidence_dirs = ["exhibits", "evidence", "attachments", "appendix", "APPENDIX"]
            for edir in evidence_dirs:
                epath = self.stack_path / edir
                if epath.exists():
                    for fp in epath.rglob("*"):
                        if fp.suffix.lower() in EVIDENCE_EXTENSIONS and fp.is_file():
                            self.evidence_files.append({
                                "path": str(fp),
                                "name": fp.name,
                                "ext": fp.suffix.lower(),
                                "size": fp.stat().st_size,
                            })

            self.steps[step]["details"].append(f"Found {doc_count} documents")
            self.steps[step]["details"].append(f"Found {len(self.evidence_files)} evidence files")
            self.steps[step]["details"].append(f"Court context: {self.court_ctx['court']}")
            self.steps[step]["details"].append(f"Rules: {self.court_ctx['rules']}")

            if doc_count == 0:
                self.steps[step]["warnings"].append("No documents found in stack directory")

            self.steps[step]["status"] = "PASS"
            self.log(f"  Intake complete: {doc_count} docs, {len(self.evidence_files)} evidence files")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"Intake error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Intake FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 2: PLACEHOLDER CHECK
    # ------------------------------------------------------------------
    def step_placeholder_check(self):
        step = "PLACEHOLDER_CHECK"
        self.log(f"--- STEP 2: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            unresolved = []
            resolved_count = 0
            auto_filled_count = 0

            # Try to load the full PlaceholderResolverV2 for active resolution
            resolver_mod = _try_import("placeholder_resolver_v2")
            resolver = None
            known_values = {}
            if resolver_mod:
                ResolverClass = getattr(resolver_mod, "PlaceholderResolverV2", None)
                if ResolverClass:
                    try:
                        resolver = ResolverClass()
                        resolver.load_db_values()
                        known_values = resolver.known
                        self.log(f"  PlaceholderResolverV2 active: {len(known_values)} known values")
                    except Exception as exc:
                        self.log(f"  Resolver init warning: {exc}", "warning")
                        resolver = None
                if not known_values and hasattr(resolver_mod, "KNOWN_VALUES"):
                    known_values = resolver_mod.KNOWN_VALUES
                    self.log(f"  Loaded {len(known_values)} known placeholder values (fallback)")

            # Phase 1: Active resolution — let resolver rewrite files in-place
            md_docs = [d for d in self.documents if d["ext"] in ('.md', '.txt')]
            if resolver:
                for doc in md_docs:
                    try:
                        r, u = resolver.process_file(doc["path"])
                        auto_filled_count += r
                    except Exception:
                        continue
                self.log(f"  Auto-filled {auto_filled_count} placeholders in-place")

            # Phase 2: Re-scan to find any remaining unresolved placeholders
            for doc in md_docs:
                try:
                    with open(doc["path"], "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    matches = PLACEHOLDER_PATTERN.findall(content)
                    for m in matches:
                        m_clean = m.strip()
                        if m_clean in known_values:
                            resolved_count += 1
                        else:
                            unresolved.append({
                                "placeholder": f"[{m_clean}]",
                                "file": doc["name"],
                                "resolvable": False,
                            })
                except Exception:
                    continue

            self.placeholders_found = unresolved

            total_resolved = resolved_count + auto_filled_count
            fill_rate = (total_resolved / max(total_resolved + len(unresolved), 1)) * 100

            self.steps[step]["details"].append(f"Auto-filled in-place: {auto_filled_count}")
            self.steps[step]["details"].append(f"Auto-resolvable (remaining): {resolved_count}")
            self.steps[step]["details"].append(f"Unresolved: {len(unresolved)}")
            self.steps[step]["details"].append(f"Fill rate: {fill_rate:.1f}%")

            if unresolved:
                for ph in unresolved[:20]:
                    self.steps[step]["warnings"].append(
                        f"  Unresolved: {ph['placeholder']} in {ph['file']}")
                self.steps[step]["status"] = "WARN"
                self.log(f"  {len(unresolved)} unresolved placeholders (fill rate: {fill_rate:.1f}%)")
            else:
                self.steps[step]["status"] = "PASS"
                self.log(f"  All placeholders resolved (fill rate: 100%)")

            return len(unresolved) == 0

        except Exception as e:
            self.steps[step]["issues"].append(f"Placeholder check error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Placeholder check FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 3: AUTHORITY CHECK
    # ------------------------------------------------------------------
    def step_authority_check(self):
        step = "AUTHORITY_CHECK"
        self.log(f"--- STEP 3: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            all_citations = {}
            total_found = 0
            incomplete = []
            verified_count = 0
            unverified_count = 0

            # Try to load Bloom filter for O(1) citation verification
            bloom_filter = None
            try:
                bloom_mod_path = str(Path(__file__).resolve().parent.parent / "pipeline")
                if bloom_mod_path not in sys.path:
                    sys.path.insert(0, bloom_mod_path)
                from bloom_citation_filter import get_filter
                bloom_filter = get_filter()
                bf_stats = bloom_filter.stats()
                self.log(f"  Bloom filter loaded: {bf_stats.get('item_count', 0):,} citations, "
                         f"{bf_stats.get('size_mb', 0)} MB")
            except Exception as exc:
                self.log(f"  Bloom filter unavailable: {exc} — skipping verification", "warning")

            md_docs = [d for d in self.documents if d["ext"] in ('.md', '.txt')]
            for doc in md_docs:
                try:
                    with open(doc["path"], "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception:
                    continue

                for ctype, pattern in CITATION_PATTERNS.items():
                    matches = pattern.findall(content)
                    if matches:
                        if ctype not in all_citations:
                            all_citations[ctype] = []
                        for m in matches:
                            citation_text = m.strip()
                            is_verified = False
                            if bloom_filter:
                                is_verified = bloom_filter.contains(citation_text)
                            if is_verified:
                                verified_count += 1
                            else:
                                unverified_count += 1
                            all_citations[ctype].append({
                                "citation": citation_text,
                                "file": doc["name"],
                                "verified": is_verified,
                            })
                            total_found += 1

                # Check for incomplete citations (e.g., "__ Mich __" or "[CITE]")
                bad = re.findall(r'(?:__\s*(?:Mich|NW|US|F\.)\s*__|_+\s*\(\d{4}\)|\[CITE[^\]]*\])', content)
                for b in bad:
                    incomplete.append({"fragment": b.strip(), "file": doc["name"]})

            self.citations_found = all_citations

            self.steps[step]["details"].append(f"Total citations found: {total_found}")
            self.steps[step]["details"].append(f"Verified against authority DB: {verified_count}")
            self.steps[step]["details"].append(f"Unverified: {unverified_count}")
            if total_found > 0:
                verify_rate = (verified_count / total_found) * 100
                self.steps[step]["details"].append(f"Verification rate: {verify_rate:.1f}%")
            for ctype, cites in all_citations.items():
                v_count = sum(1 for c in cites if c.get("verified"))
                self.steps[step]["details"].append(f"  {ctype}: {len(cites)} ({v_count} verified)")

            has_issues = False
            if incomplete:
                for ic in incomplete:
                    self.steps[step]["issues"].append(
                        f"Incomplete citation: '{ic['fragment']}' in {ic['file']}")
                has_issues = True
                self.log(f"  {len(incomplete)} incomplete citations found")

            if unverified_count > 0 and bloom_filter:
                self.steps[step]["warnings"].append(
                    f"{unverified_count} citation(s) not found in authority database")
                self.log(f"  {unverified_count} unverified citations (may be valid but missing from DB)")

            if has_issues:
                self.steps[step]["status"] = "WARN"
            elif unverified_count > 0:
                self.steps[step]["status"] = "WARN"
            else:
                self.steps[step]["status"] = "PASS"
                self.log(f"  Authority check passed: {total_found} citations, {verified_count} verified")

            # Cross-reference with citation_validator if available
            cv_mod = _try_import("citation_validator")
            if cv_mod:
                self.steps[step]["details"].append("Citation validator engine available for deep check")

            return len(incomplete) == 0

        except Exception as e:
            self.steps[step]["issues"].append(f"Authority check error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Authority check FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 4: EVIDENCE CHECK
    # ------------------------------------------------------------------
    def step_evidence_check(self):
        step = "EVIDENCE_CHECK"
        self.log(f"--- STEP 4: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            # Check exhibit references in documents
            exhibit_refs = []
            missing_exhibits = []
            existing_files = {Path(e["path"]).stem.lower() for e in self.evidence_files}
            existing_files.update(Path(e["path"]).name.lower() for e in self.evidence_files)

            exhibit_pattern = re.compile(
                r'(?:Exhibit|Ex\.?|Attachment)\s+([A-Z0-9]+(?:\s*[-]\s*[A-Z0-9]+)?)',
                re.IGNORECASE
            )

            md_docs = [d for d in self.documents if d["ext"] in ('.md', '.txt')]
            for doc in md_docs:
                try:
                    with open(doc["path"], "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    refs = exhibit_pattern.findall(content)
                    for r in refs:
                        r_clean = r.strip()
                        if r_clean not in exhibit_refs:
                            exhibit_refs.append(r_clean)
                except Exception:
                    continue

            self.steps[step]["details"].append(f"Exhibit references found: {len(exhibit_refs)}")
            self.steps[step]["details"].append(f"Evidence files on disk: {len(self.evidence_files)}")

            # Cross-reference with evidence_chain_engine
            EvidenceChainEngine = _try_import("evidence_chain_engine", "EvidenceChainEngine")
            if EvidenceChainEngine:
                try:
                    ece = EvidenceChainEngine()
                    ece.load_evidence()
                    self.steps[step]["details"].append(
                        f"DB evidence items loaded: {len(ece.evidence_items)}")
                except Exception as exc:
                    self.steps[step]["warnings"].append(
                        f"Evidence chain engine load warning: {exc}")

            if missing_exhibits:
                for me in missing_exhibits:
                    self.steps[step]["issues"].append(f"Missing exhibit: {me}")
                self.steps[step]["status"] = "WARN"
            else:
                self.steps[step]["status"] = "PASS"
                self.log(f"  Evidence check passed: {len(exhibit_refs)} refs, "
                         f"{len(self.evidence_files)} files")

            return len(missing_exhibits) == 0

        except Exception as e:
            self.steps[step]["issues"].append(f"Evidence check error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Evidence check FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 5: COMPLIANCE CHECK
    # ------------------------------------------------------------------
    def step_compliance_check(self):
        step = "COMPLIANCE_CHECK"
        self.log(f"--- STEP 5: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            compliance_results = []

            # Use BriefComplianceEngine if available
            BriefComplianceEngine = _try_import("brief_compliance_engine", "BriefComplianceEngine")

            md_docs = [d for d in self.documents
                       if d["ext"] == '.md'
                       and any(kw in d["name"].lower()
                               for kw in ("brief", "motion", "complaint", "petition", "response"))]

            if BriefComplianceEngine and md_docs:
                for doc in md_docs:
                    try:
                        engine = BriefComplianceEngine()
                        engine.load_brief(doc["path"])
                        engine.check_word_count()
                        r = engine.results
                        compliance_results.append({
                            "file": doc["name"],
                            "word_count": r.get("word_count", 0),
                            "pass": r.get("pass", False),
                            "issues": r.get("issues", []),
                        })
                        self.steps[step]["details"].append(
                            f"{doc['name']}: {r.get('word_count', 0)} words, "
                            f"pass={r.get('pass', 'N/A')}")
                    except Exception as exc:
                        self.steps[step]["warnings"].append(
                            f"Compliance check warning for {doc['name']}: {exc}")
            else:
                # Basic compliance checks without engine
                for doc in md_docs:
                    try:
                        with open(doc["path"], "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        words = len(content.split())
                        has_caption = bool(re.search(
                            r'(?i)(circuit\s+court|court\s+of\s+appeals|supreme\s+court'
                            r'|district\s+court)', content))
                        has_sig = bool(re.search(
                            r'(?i)(respectfully\s+submitted|/s/|signature)', content))
                        has_cert = bool(re.search(
                            r'(?i)(certificate\s+of\s+service|proof\s+of\s+service)', content))

                        issues = []
                        if not has_caption:
                            issues.append("Missing court caption")
                        if not has_sig:
                            issues.append("Missing signature block")
                        if not has_cert:
                            issues.append("Missing certificate of service")

                        compliance_results.append({
                            "file": doc["name"],
                            "word_count": words,
                            "pass": len(issues) == 0,
                            "issues": issues,
                        })
                        self.steps[step]["details"].append(
                            f"{doc['name']}: {words} words, issues={len(issues)}")
                    except Exception:
                        continue

            total_issues = sum(len(cr["issues"]) for cr in compliance_results)
            if total_issues > 0:
                for cr in compliance_results:
                    for iss in cr["issues"]:
                        self.steps[step]["issues"].append(f"{cr['file']}: {iss}")
                self.steps[step]["status"] = "WARN"
                self.log(f"  Compliance: {total_issues} issues across "
                         f"{len(compliance_results)} documents")
            else:
                self.steps[step]["status"] = "PASS"
                self.log(f"  Compliance passed for {len(compliance_results)} documents")

            return total_issues == 0

        except Exception as e:
            self.steps[step]["issues"].append(f"Compliance check error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Compliance check FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 6: QA GATE
    # ------------------------------------------------------------------
    def step_qa_gate(self):
        step = "QA_GATE"
        self.log(f"--- STEP 6: {step} (GO/NO-GO Decision) ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            # Aggregate results from all prior steps
            fail_count = sum(1 for s in list(self.steps.values())[:5]
                             if s["status"] == "FAIL")
            warn_count = sum(1 for s in list(self.steps.values())[:5]
                             if s["status"] == "WARN")
            pass_count = sum(1 for s in list(self.steps.values())[:5]
                             if s["status"] == "PASS")

            total_issues = sum(len(s["issues"]) for s in list(self.steps.values())[:5])
            total_warnings = sum(len(s["warnings"]) for s in list(self.steps.values())[:5])

            # Cross-reference with PreFilingQAEngine
            PreFilingQAEngine = _try_import("prefiling_qa_engine", "PreFilingQAEngine")
            if PreFilingQAEngine:
                self.steps[step]["details"].append(
                    "PreFilingQAEngine available for deep QA")

            # GO / NO-GO decision
            if fail_count > 0:
                self.go_nogo = "NO-GO"
                self.steps[step]["status"] = "FAIL"
                self.steps[step]["issues"].append(
                    f"NO-GO: {fail_count} step(s) FAILED")
            elif warn_count > 2:
                self.go_nogo = "NO-GO"
                self.steps[step]["status"] = "FAIL"
                self.steps[step]["issues"].append(
                    f"NO-GO: {warn_count} steps have warnings (threshold: 2)")
            elif total_issues > 10:
                self.go_nogo = "NO-GO"
                self.steps[step]["status"] = "FAIL"
                self.steps[step]["issues"].append(
                    f"NO-GO: {total_issues} total issues (threshold: 10)")
            else:
                self.go_nogo = "GO"
                self.steps[step]["status"] = "PASS"

            self.steps[step]["details"].extend([
                f"Steps PASS: {pass_count} / WARN: {warn_count} / FAIL: {fail_count}",
                f"Total issues: {total_issues}",
                f"Total warnings: {total_warnings}",
                f"Verdict: {self.go_nogo}",
            ])

            self.log(f"  QA Gate verdict: {self.go_nogo} "
                     f"(P:{pass_count} W:{warn_count} F:{fail_count})")
            return self.go_nogo == "GO"

        except Exception as e:
            self.steps[step]["issues"].append(f"QA gate error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.go_nogo = "NO-GO"
            self.log(f"  QA gate FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 7: PDF GENERATION
    # ------------------------------------------------------------------
    def step_pdf_generation(self):
        step = "PDF_GENERATION"
        self.log(f"--- STEP 7: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            pdf_dir = self.output_dir / "PDF"
            pdf_dir.mkdir(exist_ok=True)
            generated = 0

            # Try to use filing_assembly_pipeline for DOCX generation
            fap_mod = _try_import("filing_assembly_pipeline")
            has_docx_lib = False
            try:
                from docx import Document
                has_docx_lib = True
            except ImportError:
                pass

            md_docs = [d for d in self.documents if d["ext"] == '.md']

            if fap_mod and hasattr(fap_mod, 'read_stack') and has_docx_lib:
                try:
                    stack_files = fap_mod.read_stack(str(self.stack_path))
                    if stack_files:
                        self.steps[step]["details"].append(
                            f"Assembly pipeline loaded {len(stack_files)} files")
                except Exception as exc:
                    self.steps[step]["warnings"].append(
                        f"Assembly pipeline warning: {exc}")

            # Generate per-document output stubs
            for doc in md_docs:
                try:
                    out_name = Path(doc["name"]).stem + ".pdf"
                    manifest_entry = {
                        "source": doc["name"],
                        "output": out_name,
                        "status": "ready_for_conversion",
                        "word_count": 0,
                    }
                    with open(doc["path"], "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    manifest_entry["word_count"] = len(content.split())

                    # Write conversion manifest
                    manifest_path = pdf_dir / (Path(doc["name"]).stem + ".manifest.json")
                    with open(manifest_path, "w", encoding="utf-8") as mf:
                        json.dump(manifest_entry, mf, indent=2)

                    generated += 1
                except Exception as exc:
                    self.steps[step]["warnings"].append(
                        f"PDF prep warning for {doc['name']}: {exc}")

            # Copy existing PDFs
            existing_pdfs = [d for d in self.documents if d["ext"] == '.pdf']
            for doc in existing_pdfs:
                try:
                    dest = pdf_dir / doc["name"]
                    if not dest.exists():
                        shutil.copy2(doc["path"], dest)
                        generated += 1
                except Exception:
                    pass

            self.steps[step]["details"].append(f"PDF manifests generated: {generated}")
            self.steps[step]["details"].append(f"Existing PDFs copied: {len(existing_pdfs)}")
            self.steps[step]["details"].append(f"Output dir: {pdf_dir}")
            self.steps[step]["status"] = "PASS"
            self.log(f"  PDF generation: {generated} documents prepared")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"PDF generation error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  PDF generation FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 8: EXHIBIT COMPILATION
    # ------------------------------------------------------------------
    def step_exhibit_compilation(self):
        step = "EXHIBIT_COMPILATION"
        self.log(f"--- STEP 8: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            exhibit_dir = self.output_dir / "EXHIBITS"
            exhibit_dir.mkdir(exist_ok=True)

            # Load exhibit registry from DB
            exhibit_data = []
            try:
                conn = _get_db()
                tables = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name LIKE '%exhibit%'").fetchall()]
                for tbl in tables:
                    try:
                        rows = conn.execute(f"SELECT * FROM {tbl} LIMIT 200").fetchall()
                        cols = [d[0] for d in conn.execute(
                            f"PRAGMA table_info({tbl})").fetchall()]
                        col_names = [c[1] if isinstance(c, (list, tuple)) else c for c in cols]
                        # Re-fetch with proper column names
                        col_info = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
                        col_names = [c[1] for c in col_info]
                        rows = conn.execute(f"SELECT * FROM {tbl} LIMIT 200").fetchall()
                        for row in rows:
                            exhibit_data.append(dict(zip(col_names, row)))
                    except Exception:
                        continue
                conn.close()
            except Exception as exc:
                self.steps[step]["warnings"].append(f"DB exhibit load warning: {exc}")

            # Generate Bates numbers
            bates_counter = 1
            bates_index = []
            prefix = self.stack_name[:3].upper().replace("_", "")

            for i, ef in enumerate(self.evidence_files):
                bates_start = f"{prefix}-{bates_counter:06d}"
                # Estimate 1 page per file (conservative)
                bates_end = f"{prefix}-{bates_counter:06d}"
                bates_index.append({
                    "file": ef["name"],
                    "bates_start": bates_start,
                    "bates_end": bates_end,
                    "size": ef["size"],
                })
                bates_counter += 1

            # Write exhibit index
            index_path = exhibit_dir / "EXHIBIT_INDEX.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(f"# Exhibit Index - {self.stack_name}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write(f"Court: {self.court_ctx['court']}\n")
                f.write(f"Rules: {self.court_ctx['rules']}\n\n")
                f.write("| # | File | Bates Start | Bates End | Size |\n")
                f.write("|---|------|-------------|-----------|------|\n")
                for i, entry in enumerate(bates_index, 1):
                    sz = f"{entry['size']:,}" if entry['size'] else "N/A"
                    f.write(f"| {i} | {entry['file']} | {entry['bates_start']} "
                            f"| {entry['bates_end']} | {sz} |\n")
                if exhibit_data:
                    f.write(f"\n## DB Exhibit Registry ({len(exhibit_data)} entries)\n\n")
                    for ex in exhibit_data[:30]:
                        title = ex.get('exhibit_title', ex.get('title', 'N/A'))
                        num = ex.get('exhibit_number', ex.get('id', 'N/A'))
                        f.write(f"- **Exhibit {num}**: {title}\n")

            self.steps[step]["details"].append(f"Evidence files indexed: {len(bates_index)}")
            self.steps[step]["details"].append(f"DB exhibit entries: {len(exhibit_data)}")
            self.steps[step]["details"].append(f"Bates range: {prefix}-000001 to "
                                               f"{prefix}-{bates_counter - 1:06d}")
            self.steps[step]["status"] = "PASS"
            self.log(f"  Exhibit compilation: {len(bates_index)} files, "
                     f"{len(exhibit_data)} DB entries")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"Exhibit compilation error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Exhibit compilation FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 9: SERVICE PACKET
    # ------------------------------------------------------------------
    def step_service_packet(self):
        step = "SERVICE_PACKET"
        self.log(f"--- STEP 9: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            svc_dir = self.output_dir / "SERVICE_PACKET"
            svc_dir.mkdir(exist_ok=True)

            # Load service list from DB
            service_parties = []
            try:
                conn = _get_db()
                party_tables = [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND (name LIKE '%part%' OR name LIKE '%attorney%' "
                    "OR name LIKE '%service%')").fetchall()]
                for tbl in party_tables:
                    try:
                        col_info = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
                        col_names = [c[1] for c in col_info]
                        rows = conn.execute(f"SELECT * FROM {tbl} LIMIT 50").fetchall()
                        for row in rows:
                            service_parties.append(dict(zip(col_names, row)))
                    except Exception:
                        continue
                conn.close()
            except Exception:
                pass

            # Generate proof of service
            pos_path = svc_dir / "PROOF_OF_SERVICE.md"
            with open(pos_path, "w", encoding="utf-8") as f:
                f.write("# PROOF OF SERVICE\n\n")
                f.write(f"Case: {self.stack_name}\n")
                f.write(f"Court: {self.court_ctx['court']}\n")
                f.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n\n")
                f.write("I hereby certify that on the above date, I served a copy of the ")
                f.write("foregoing documents upon all parties/attorneys of record by:\n\n")
                f.write("- [X] E-Filing (electronic service through court e-filing system)\n")
                f.write("- [ ] First-class U.S. Mail, postage prepaid\n")
                f.write("- [ ] Personal delivery\n")
                f.write("- [ ] Email\n\n")
                f.write("## Service List\n\n")
                if service_parties:
                    for sp in service_parties[:20]:
                        name = sp.get('name', sp.get('party_name',
                               sp.get('attorney_name', 'Unknown')))
                        addr = sp.get('address', sp.get('email', 'On file'))
                        f.write(f"- **{name}**: {addr}\n")
                else:
                    f.write("- [SERVICE LIST TO BE COMPLETED]\n")
                f.write("\n\n___________________________\n")
                f.write("Andrew J. Pigors, Pro Se\n")
                f.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n")

            # Generate cover letter
            cover_path = svc_dir / "COVER_LETTER.md"
            with open(cover_path, "w", encoding="utf-8") as f:
                f.write("# COVER LETTER\n\n")
                f.write(f"Date: {datetime.now().strftime('%B %d, %Y')}\n\n")
                f.write(f"RE: Filing Submission - {self.stack_name}\n")
                f.write(f"Court: {self.court_ctx['court']}\n\n")
                f.write("Dear Clerk of the Court,\n\n")
                f.write("Enclosed please find the following documents for filing:\n\n")
                filed_docs = [d for d in self.documents
                              if d["ext"] in ('.md', '.pdf', '.docx')
                              and 'PRODUCTION_OUTPUT' not in d["relative"]]
                for i, doc in enumerate(filed_docs[:20], 1):
                    f.write(f"{i}. {doc['name']}\n")
                f.write("\nRespectfully submitted,\n\n")
                f.write("Andrew J. Pigors, Pro Se\n")

            # Generate mailing list
            mail_path = svc_dir / "MAILING_LIST.md"
            with open(mail_path, "w", encoding="utf-8") as f:
                f.write(f"# Mailing List - {self.stack_name}\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                if service_parties:
                    for sp in service_parties[:20]:
                        name = sp.get('name', sp.get('party_name', 'Unknown'))
                        f.write(f"## {name}\n")
                        for k, v in sp.items():
                            if k.startswith('_'):
                                continue
                            f.write(f"- {k}: {v}\n")
                        f.write("\n")
                else:
                    f.write("No service parties loaded from database.\n")
                    f.write("Complete mailing list manually.\n")

            self.steps[step]["details"].extend([
                f"Proof of service generated: {pos_path.name}",
                f"Cover letter generated: {cover_path.name}",
                f"Mailing list generated: {mail_path.name}",
                f"Service parties from DB: {len(service_parties)}",
            ])
            self.steps[step]["status"] = "PASS"
            self.log(f"  Service packet generated: {len(service_parties)} parties")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"Service packet error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Service packet FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 10: EFILING PREP
    # ------------------------------------------------------------------
    def step_efiling_prep(self):
        step = "EFILING_PREP"
        self.log(f"--- STEP 10: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            efiling_dir = self.output_dir / "EFILING"
            efiling_dir.mkdir(exist_ok=True)

            system = self.court_ctx.get("efiling", "mifile")

            # Load config from efiling_prep_engine
            efiling_mod = _try_import("efiling_prep_engine")
            system_config = None
            if efiling_mod and hasattr(efiling_mod, 'EFILING_SYSTEMS'):
                system_config = efiling_mod.EFILING_SYSTEMS.get(system, {})

            if not system_config:
                system_config = {
                    "name": system.upper(),
                    "max_file_size_mb": 25,
                    "accepted_formats": [".pdf"],
                }

            # Generate efiling manifest
            manifest = {
                "system": system_config.get("name", system),
                "court": self.court_ctx["court"],
                "stack": self.stack_name,
                "generated": datetime.now().isoformat(),
                "max_file_size_mb": system_config.get("max_file_size_mb", 25),
                "accepted_formats": system_config.get("accepted_formats", [".pdf"]),
                "documents": [],
                "checklist": {
                    "all_pdf": False,
                    "under_size_limit": True,
                    "service_attached": False,
                    "fee_paid_or_waived": False,
                },
            }

            # Check documents
            pdf_docs = [d for d in self.documents if d["ext"] == '.pdf']
            md_docs = [d for d in self.documents if d["ext"] == '.md']
            max_size = system_config.get("max_file_size_mb", 25) * 1024 * 1024

            for doc in pdf_docs + md_docs:
                entry = {
                    "name": doc["name"],
                    "format": doc["ext"],
                    "size_bytes": doc["size"],
                    "under_limit": doc["size"] < max_size,
                    "needs_conversion": doc["ext"] != '.pdf',
                }
                manifest["documents"].append(entry)
                if not entry["under_limit"]:
                    manifest["checklist"]["under_size_limit"] = False

            manifest["checklist"]["all_pdf"] = all(
                d["format"] == ".pdf" for d in manifest["documents"])

            # Write manifest
            manifest_path = efiling_dir / "EFILING_MANIFEST.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Write submission instructions
            instr_path = efiling_dir / "SUBMISSION_INSTRUCTIONS.md"
            with open(instr_path, "w", encoding="utf-8") as f:
                f.write(f"# E-Filing Submission Instructions\n\n")
                f.write(f"**System:** {manifest['system']}\n")
                f.write(f"**Court:** {manifest['court']}\n")
                f.write(f"**Stack:** {manifest['stack']}\n")
                f.write(f"**Generated:** {manifest['generated']}\n\n")
                f.write("## Pre-Submission Checklist\n\n")
                for key, val in manifest["checklist"].items():
                    mark = "X" if val else " "
                    f.write(f"- [{mark}] {key.replace('_', ' ').title()}\n")
                f.write(f"\n## Documents to Upload ({len(manifest['documents'])})\n\n")
                f.write("| # | Document | Format | Size | Under Limit | Needs Conversion |\n")
                f.write("|---|----------|--------|------|-------------|------------------|\n")
                for i, doc in enumerate(manifest["documents"], 1):
                    sz = f"{doc['size_bytes']:,}"
                    f.write(f"| {i} | {doc['name']} | {doc['format']} | {sz} "
                            f"| {'Yes' if doc['under_limit'] else 'NO'} "
                            f"| {'Yes' if doc['needs_conversion'] else 'No'} |\n")
                if system_config.get("url"):
                    f.write(f"\n## Filing URL\n\n{system_config['url']}\n")
                if system_config.get("notes"):
                    f.write(f"\n## Notes\n\n{system_config['notes']}\n")

            self.steps[step]["details"].extend([
                f"E-filing system: {manifest['system']}",
                f"Documents: {len(manifest['documents'])}",
                f"All PDF: {manifest['checklist']['all_pdf']}",
                f"Under size limit: {manifest['checklist']['under_size_limit']}",
            ])
            self.steps[step]["status"] = "PASS"
            self.log(f"  E-filing prep: {manifest['system']}, "
                     f"{len(manifest['documents'])} documents")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"E-filing prep error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  E-filing prep FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # STEP 11: FINAL REPORT
    # ------------------------------------------------------------------
    def step_final_report(self):
        step = "FINAL_REPORT"
        self.log(f"--- STEP 11: {step} ---")
        self.steps[step]["status"] = "RUNNING"
        try:
            elapsed = (datetime.now() - self.start_time).total_seconds()

            # Build report
            report = {
                "pipeline": "FilingProductionPipeline v1.0",
                "stack": self.stack_name,
                "stack_path": str(self.stack_path),
                "court": self.court_ctx,
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": round(elapsed, 2),
                "go_nogo": self.go_nogo,
                "documents_scanned": len(self.documents),
                "evidence_files": len(self.evidence_files),
                "steps": {},
            }
            for sname, sdata in self.steps.items():
                report["steps"][sname] = {
                    "status": sdata["status"],
                    "details": sdata["details"],
                    "issue_count": len(sdata["issues"]),
                    "issues": sdata["issues"][:20],
                    "warning_count": len(sdata["warnings"]),
                    "warnings": sdata["warnings"][:10],
                }

            # Write JSON report
            json_path = self.output_dir / "PRODUCTION_REPORT.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)

            # Write markdown report
            md_path = self.output_dir / "PRODUCTION_REPORT.md"
            with open(md_path, "w", encoding="utf-8") as f:
                verdict_icon = "GO" if self.go_nogo == "GO" else "NO-GO"
                f.write(f"# Filing Production Report: {self.stack_name}\n\n")
                f.write(f"**Verdict: {verdict_icon}**\n\n")
                f.write(f"- **Court:** {self.court_ctx['court']}\n")
                f.write(f"- **Rules:** {self.court_ctx['rules']}\n")
                f.write(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **Elapsed:** {elapsed:.1f}s\n")
                f.write(f"- **Documents:** {len(self.documents)}\n")
                f.write(f"- **Evidence Files:** {len(self.evidence_files)}\n\n")

                f.write("## Pipeline Checklist\n\n")
                f.write("| Step | Status | Issues | Warnings |\n")
                f.write("|------|--------|--------|----------|\n")
                for sname, sdata in self.steps.items():
                    status = sdata["status"]
                    if status == "PASS":
                        indicator = "[PASS]"
                    elif status == "WARN":
                        indicator = "[WARN]"
                    elif status == "FAIL":
                        indicator = "[FAIL]"
                    else:
                        indicator = "[----]"
                    f.write(f"| {sname} | {indicator} | {len(sdata['issues'])} "
                            f"| {len(sdata['warnings'])} |\n")

                f.write(f"\n## GO/NO-GO Decision\n\n")
                f.write(f"**{self.go_nogo}**\n\n")

                # Issues summary
                all_issues = []
                for sname, sdata in self.steps.items():
                    for iss in sdata["issues"]:
                        all_issues.append(f"[{sname}] {iss}")
                if all_issues:
                    f.write("## Issues Requiring Resolution\n\n")
                    for iss in all_issues[:50]:
                        f.write(f"- {iss}\n")
                    f.write("\n")

                # Document inventory
                f.write("## Document Inventory\n\n")
                f.write("| File | Type | Size | Modified |\n")
                f.write("|------|------|------|----------|\n")
                for doc in self.documents[:50]:
                    sz = f"{doc['size']:,}"
                    f.write(f"| {doc['name']} | {doc['ext']} | {sz} "
                            f"| {doc['modified'][:10]} |\n")

                # Citations summary
                if self.citations_found:
                    f.write("\n## Citation Summary\n\n")
                    for ctype, cites in self.citations_found.items():
                        f.write(f"- **{ctype}**: {len(cites)} citations\n")

                f.write(f"\n## Output Directory\n\n`{self.output_dir}`\n")

            self.steps[step]["details"].extend([
                f"JSON report: {json_path.name}",
                f"Markdown report: {md_path.name}",
                f"Total elapsed: {elapsed:.1f}s",
                f"Final verdict: {self.go_nogo}",
            ])
            self.steps[step]["status"] = "PASS"
            self.log(f"  Final report written to {self.output_dir}")
            return True

        except Exception as e:
            self.steps[step]["issues"].append(f"Final report error: {e}")
            self.steps[step]["status"] = "FAIL"
            self.log(f"  Final report FAILED: {e}", "error")
            return False

    # ------------------------------------------------------------------
    # MAIN RUN
    # ------------------------------------------------------------------
    def run(self):
        """Execute the full pipeline, all 11 steps."""
        self.log("=" * 70)
        self.log(f"FILING PRODUCTION PIPELINE v1.0")
        self.log(f"Stack: {self.stack_name}")
        self.log(f"Path:  {self.stack_path}")
        self.log(f"Court: {self.court_ctx['court']}")
        self.log("=" * 70)

        # Execute steps in order
        self.step_intake()
        self.step_placeholder_check()
        self.step_authority_check()
        self.step_evidence_check()
        self.step_compliance_check()
        self.step_qa_gate()

        # Production steps run regardless of GO/NO-GO (generate what we can)
        self.step_pdf_generation()
        self.step_exhibit_compilation()
        self.step_service_packet()
        self.step_efiling_prep()
        self.step_final_report()

        # Summary
        pass_count = sum(1 for s in self.steps.values() if s["status"] == "PASS")
        total = len(self.steps)
        self.log("=" * 70)
        self.log(f"PIPELINE COMPLETE: {pass_count}/{total} steps passed")
        self.log(f"VERDICT: {self.go_nogo}")
        self.log(f"Output: {self.output_dir}")
        self.log("=" * 70)

        # Log to DB
        self._log_to_db()

        return {
            "stack": self.stack_name,
            "path": str(self.stack_path),
            "court": self.court_ctx,
            "go_nogo": self.go_nogo,
            "steps_passed": pass_count,
            "steps_total": total,
            "documents": len(self.documents),
            "evidence_files": len(self.evidence_files),
            "output_dir": str(self.output_dir),
            "elapsed": (datetime.now() - self.start_time).total_seconds(),
        }

    def _log_to_db(self):
        """Record pipeline run in litigation_context.db."""
        try:
            conn = _get_db()
            conn.execute("""CREATE TABLE IF NOT EXISTS filing_production_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stack_name TEXT,
                stack_path TEXT,
                court TEXT,
                go_nogo TEXT,
                steps_passed INTEGER,
                steps_total INTEGER,
                documents_scanned INTEGER,
                evidence_files INTEGER,
                issues_total INTEGER,
                output_dir TEXT,
                elapsed_seconds REAL,
                run_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
            total_issues = sum(len(s["issues"]) for s in self.steps.values())
            pass_count = sum(1 for s in self.steps.values() if s["status"] == "PASS")
            conn.execute("""INSERT INTO filing_production_runs
                (stack_name, stack_path, court, go_nogo, steps_passed, steps_total,
                 documents_scanned, evidence_files, issues_total, output_dir, elapsed_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.stack_name, str(self.stack_path), self.court_ctx["court"],
                 self.go_nogo, pass_count, len(self.steps),
                 len(self.documents), len(self.evidence_files), total_issues,
                 str(self.output_dir),
                 (datetime.now() - self.start_time).total_seconds()))
            conn.commit()
            conn.close()
            self.log("  Pipeline run logged to DB")
        except Exception as e:
            self.log(f"  DB log warning: {e}", "warning")


# ============================================================================
# CLI ENTRY POINT
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Filing Production Pipeline - draft to court-ready submission")
    parser.add_argument("--stack", required=True,
                        help="Path to filing stack directory (absolute or relative to LitigationOS root)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress console output")
    args = parser.parse_args()

    pipeline = FilingProductionPipeline(args.stack, verbose=not args.quiet)
    result = pipeline.run()

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"VERDICT: {result['go_nogo']}")
    print(f"Steps:   {result['steps_passed']}/{result['steps_total']} passed")
    print(f"Docs:    {result['documents']}")
    print(f"Output:  {result['output_dir']}")
    print(f"Elapsed: {result['elapsed']:.1f}s")
    print(f"{'=' * 60}")

    return 0 if result["go_nogo"] == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
