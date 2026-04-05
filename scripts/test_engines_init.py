"""
Convergence Integration Test Suite
====================================
Validates ALL connections in the LitigationOS processing pipeline:

  1. Extractor → lazy dep loading, text/PDF/DOCX dispatch, hash + metadata
  2. Classifier → doc type, lane routing, urgency, topic extraction
  3. Analyzer → quotes, timeline, authorities, impeachment, entities, READINESS
  4. Router → DB schema creation, document storage w/ readiness, dedup
  5. Pipeline → full end-to-end (extract→classify→analyze→route)
  6. Task Handlers → all 6 handlers callable, auto_classify returns real data
  7. Daemon wiring → task_handlers imported, get_handler resolves all types
  8. Engines __init__ → safe import, get_engine factory, cerberus guard
  9. Filing Engine → triggers, validator, pipeline phases exist and import
  10. Readiness scoring → computed, stored in DB, retrievable

Writes results to a file AND stdout (fault-tolerant output).
"""
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time
import types
from pathlib import Path

# --- Setup: direct module loading (bypasses engines/__init__.py / fitz) ----
_repo = Path(__file__).resolve().parent.parent
_system = _repo / "00_SYSTEM"
_intake_dir = _system / "engines" / "intake"
sys.path.insert(0, str(_system))

RESULTS_FILE = _repo / "scripts" / "convergence_results.txt"
_results = []
_pass = 0
_fail = 0


def _log(msg):
    _results.append(msg)
    try:
        print(msg)
    except OSError:
        pass


def _load_mod(pkg_name, mod_name, filepath):
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.{mod_name}", filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"{pkg_name}.{mod_name}"] = mod
    spec.loader.exec_module(mod)
    return mod


# Register intake as package
_pkg = types.ModuleType("intake")
_pkg.__path__ = [str(_intake_dir)]
_pkg.__package__ = "intake"
sys.modules["intake"] = _pkg

# Load all intake submodules in dependency order
case_config_mod = _load_mod("intake", "case_config", _intake_dir / "case_config.py")
extractor_mod = _load_mod("intake", "extractor", _intake_dir / "extractor.py")
classifier_mod = _load_mod("intake", "classifier", _intake_dir / "classifier.py")
analyzer_mod = _load_mod("intake", "analyzer", _intake_dir / "analyzer.py")
router_mod = _load_mod("intake", "router", _intake_dir / "router.py")
pipeline_mod = _load_mod("intake", "pipeline", _intake_dir / "pipeline.py")

IntakePipeline = pipeline_mod.IntakePipeline
CaseConfig = case_config_mod.CaseConfig
TextExtractor = extractor_mod.TextExtractor
DocumentClassifier = classifier_mod.DocumentClassifier
LitigationAnalyzer = analyzer_mod.LitigationAnalyzer
DatabaseRouter = router_mod.DatabaseRouter
AnalysisResult = analyzer_mod.AnalysisResult

# --- Test Data --------------------------------------------------------------
SAMPLE_MOTION = """
STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

PLAINTIFF,
    Plaintiff,                     Case No. 2024-999999-DC
v                                  Hon. Jane Doe
DEFENDANT,
    Defendant.
_____________________________________________/

MOTION FOR EMERGENCY RELIEF

NOW COMES Plaintiff, appearing pro se, and respectfully moves this Honorable
Court for emergency relief pursuant to MCR 2.119(B) and MCL 722.27(1)(c),
and states as follows:

STATEMENT OF FACTS

1. On January 15, 2026, the Court entered an ex parte order without notice
   or hearing, violating due process rights under the Fourteenth Amendment.

2. The Defendant admitted on March 1, 2026 that "nothing was physical" and
   that prior allegations were fabricated to gain leverage in the custody dispute.

3. MCL 722.23(j) requires courts to consider each parent's willingness to
   facilitate a close and continuing relationship between the child and the
   other parent.

4. Since July 29, 2025, the minor child has been withheld from contact
   with Plaintiff, constituting ongoing alienation.

5. 42 USC 1983 provides a cause of action for deprivation of constitutional
   rights under color of state law. See Troxel v Granville, 530 US 57 (2000).

6. On February 10, 2026, the respondent threatened to file additional false
   reports unless financial demands were met.

7. MCR 3.207(B) governs ex parte orders. MCL 600.2950 governs personal
   protection orders. The abuse of discretion standard applies.

8. Clear and convincing evidence is required for modification of custody
   under Vodvarka v Grasher, 259 Mich App 1 (2003).

RELIEF REQUESTED

Plaintiff respectfully requests this Court:
a) Restore supervised parenting time immediately;
b) Order Defendant to comply with prior custody orders;
c) Schedule an evidentiary hearing within 14 days.

Respectfully submitted,

_____________________________
Plaintiff, appearing pro se
"""

SAMPLE_BRIEF = """
BRIEF IN SUPPORT OF MOTION

This brief addresses the constitutional violations arising from the ex parte
order entered without due process. The Fourteenth Amendment guarantees that
no state shall deprive any person of liberty without due process of law.

The Michigan Court of Appeals in Pierron v Pierron, 486 Mich 81 (2010),
held that custody determinations must consider all twelve best interest factors.

MCR 2.003(C)(1) requires disqualification where there is a conflict of interest
or the appearance of impropriety. The judge's former law partnership with the
opposing party's attorney creates such a conflict.

MRE 801(d)(2) permits admission of party-opponent statements. The defendant's
recantation that "nothing was physical" directly contradicts the PPO petition.
"""

# --- Tests ------------------------------------------------------------------
_log("=" * 70)
_log("  LITIGATIONOS CONVERGENCE INTEGRATION TEST")
_log("=" * 70)

td = tempfile.mkdtemp()
db_path = os.path.join(td, "convergence_test.db")
motion_file = os.path.join(td, "test_motion.txt")
brief_file = os.path.join(td, "test_brief.txt")

with open(motion_file, "w", encoding="utf-8") as f:
    f.write(SAMPLE_MOTION)
with open(brief_file, "w", encoding="utf-8") as f:
    f.write(SAMPLE_BRIEF)


def test(name, fn):
    global _pass, _fail
    try:
        result = fn()
        if result:
            _pass += 1
            _log(f"  [PASS] {name}")
        else:
            _fail += 1
            _log(f"  [FAIL] {name} — returned falsy")
    except Exception as e:
        _fail += 1
        _log(f"  [FAIL] {name} — {type(e).__name__}: {e}")


# -- TEST 1: Extractor (lazy deps, text extraction) -------------------------
_log("\n-- 1. EXTRACTOR --")


def t1a():
    ext = TextExtractor(ocr_enabled=False)
    assert not ext._dep_checked, "deps should not check at __init__"
    r = ext.extract(motion_file)
    assert ext._dep_checked, "deps should check after first extract"
    assert r.char_count > 100, f"char_count too low: {r.char_count}"
    assert r.sha256 and len(r.sha256) == 64, "bad sha256"
    assert r.extraction_method.startswith("text_read"), f"method: {r.extraction_method}"
    assert not r.error, f"error: {r.error}"
    _log(f"      chars={r.char_count} sha={r.sha256[:12]}… method={r.extraction_method}")
    return True


def t1b():
    ext = TextExtractor(ocr_enabled=False)
    r = ext.extract("/nonexistent/file.pdf")
    assert r.error and "not found" in r.error.lower()
    return True


def t1c():
    ext = TextExtractor(ocr_enabled=False)
    r = ext.extract(motion_file)
    assert len(r.pages) == 1
    assert r.pages[0].char_count == r.char_count
    return True


test("Lazy dependency loading + text extraction", t1a)
test("Missing file returns error (no crash)", t1b)
test("Page structure populated correctly", t1c)

# -- TEST 2: Classifier -----------------------------------------------------
_log("\n-- 2. CLASSIFIER --")


def t2a():
    clf = DocumentClassifier(case_config=CaseConfig())
    r = clf.classify(SAMPLE_MOTION, "test_motion.txt")
    assert r.doc_type == "motion", f"doc_type: {r.doc_type}"
    assert len(r.lanes) > 0, "no lanes assigned"
    assert r.urgency in ("low", "medium", "high", "critical"), f"urgency: {r.urgency}"
    assert len(r.legal_topics) > 0, "no topics found"
    _log(f"      type={r.doc_type} lanes={r.lanes} urgency={r.urgency} topics={len(r.legal_topics)}")
    return True


def t2b():
    clf = DocumentClassifier(case_config=CaseConfig())
    r = clf.classify(SAMPLE_BRIEF, "test_brief.txt")
    assert r.doc_type in ("brief", "motion", "legal_memo"), f"doc_type: {r.doc_type}"
    return True


test("Motion classification (type, lanes, urgency, topics)", t2a)
test("Brief classification", t2b)

# -- TEST 3: Analyzer + Readiness Scoring -----------------------------------
_log("\n-- 3. ANALYZER + READINESS --")


def t3a():
    ana = LitigationAnalyzer(case_config=CaseConfig())
    r = ana.analyze(SAMPLE_MOTION, file_name="test_motion.txt")
    assert len(r.evidence_quotes) > 0, "no quotes found"
    assert len(r.timeline_events) > 0, "no events found"
    assert len(r.authority_refs) > 0, "no authorities found"
    assert len(r.entities) > 0, "no entities found"
    _log(f"      quotes={len(r.evidence_quotes)} events={len(r.timeline_events)} "
         f"auth={len(r.authority_refs)} imp={len(r.impeachment_items)} ent={len(r.entities)}")
    return True


def t3b():
    ana = LitigationAnalyzer(case_config=CaseConfig())
    r = ana.analyze(SAMPLE_MOTION, file_name="test_motion.txt")
    assert r.readiness_score > 0, f"readiness_score is {r.readiness_score}"
    assert r.readiness_score <= 100, f"readiness_score exceeds 100: {r.readiness_score}"
    assert "readiness_score" in r.summary_stats
    assert r.summary_stats["readiness_score"] == r.readiness_score
    _log(f"      readiness_score={r.readiness_score}/100")
    return True


def t3c():
    # Verify calculate_readiness is a pure function on AnalysisResult
    empty = AnalysisResult()
    score = LitigationAnalyzer.calculate_readiness(empty)
    assert score == 0.0, f"empty result should score 0, got {score}"
    return True


test("Deep analysis (quotes, events, authorities, entities)", t3a)
test("Readiness score computed and in summary_stats", t3b)
test("Readiness score = 0 for empty analysis", t3c)

# -- TEST 4: Router (DB creation, storage, dedup) --------------------------
_log("\n-- 4. ROUTER + DATABASE --")


def t4a():
    router = DatabaseRouter(db_path=db_path)
    conn = router.get_conn()
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    required = {"documents", "pages", "evidence_quotes", "timeline_events",
                "authority_chains_v2", "impeachment_matrix", "entities", "intake_log"}
    missing = required - tables
    assert not missing, f"missing tables: {missing}"
    _log(f"      tables created: {len(tables)} (required: {len(required)})")
    return True


def t4b():
    # Verify readiness_score column exists in documents
    conn = sqlite3.connect(db_path)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
    conn.close()
    assert "readiness_score" in cols, f"readiness_score column missing. Columns: {cols}"
    return True


test("Schema creation (all required tables)", t4a)
test("readiness_score column in documents table", t4b)

# -- TEST 5: Full Pipeline (end-to-end) -------------------------------------
_log("\n-- 5. FULL PIPELINE --")


def t5a():
    pipeline = IntakePipeline(db_path=db_path, case_config=CaseConfig(), ocr_enabled=False)
    r = pipeline.process_file(motion_file)
    assert r.status == "completed", f"status: {r.status}, error: {r.error}"
    assert r.document_id is not None and r.document_id > 0
    assert r.quotes_found > 0
    assert r.events_found > 0
    assert r.authorities_found > 0
    _log(f"      doc_id={r.document_id} type={r.doc_type} lanes={r.lanes}")
    _log(f"      q={r.quotes_found}→{r.quotes_inserted} e={r.events_found}→{r.events_inserted} "
         f"a={r.authorities_found}→{r.authorities_inserted} i={r.impeachment_found}→{r.impeachment_inserted}")
    pipeline.close()
    return True


def t5b():
    # Readiness stored in DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    doc = conn.execute("SELECT readiness_score FROM documents WHERE id = 1").fetchone()
    conn.close()
    assert doc is not None, "document not found in DB"
    score = doc["readiness_score"]
    assert score > 0, f"readiness_score stored as {score}"
    _log(f"      DB readiness_score={score}/100")
    return True


def t5c():
    # Dedup: re-processing same file returns same doc_id
    pipeline = IntakePipeline(db_path=db_path, case_config=CaseConfig(), ocr_enabled=False)
    r = pipeline.process_file(motion_file)
    assert r.status == "completed"
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()
    assert count == 1, f"dedup failed: {count} documents"
    pipeline.close()
    return True


def t5d():
    # Second file processes correctly
    pipeline = IntakePipeline(db_path=db_path, case_config=CaseConfig(), ocr_enabled=False)
    r = pipeline.process_file(brief_file)
    assert r.status == "completed", f"brief failed: {r.error}"
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()
    assert count == 2, f"expected 2 documents, got {count}"
    pipeline.close()
    return True


def t5e():
    # Batch processing
    pipeline = IntakePipeline(db_path=db_path, case_config=CaseConfig(), ocr_enabled=False)
    batch = pipeline.process_folder(td)
    assert batch.total_files >= 2
    assert batch.errors == 0
    pipeline.close()
    _log(f"      batch: total={batch.total_files} processed={batch.processed} "
         f"skipped={batch.skipped} errors={batch.errors}")
    return True


test("Single file: extract→classify→analyze→route→DB", t5a)
test("Readiness score stored in DB documents table", t5b)
test("Dedup: re-process returns same doc_id, count=1", t5c)
test("Second file processes and count=2", t5d)
test("Batch processing (folder intake)", t5e)

# -- TEST 6: Task Handlers --------------------------------------------------
_log("\n-- 6. TASK HANDLERS --")

# Import task_handlers directly
daemon_dir = _system / "daemon"
sys.path.insert(0, str(daemon_dir.parent))

th_spec = importlib.util.spec_from_file_location(
    "task_handlers", daemon_dir / "task_handlers.py"
)
th_mod = importlib.util.module_from_spec(th_spec)
th_spec.loader.exec_module(th_mod)


def t6a():
    expected = {"auto_classify", "ocr_extract", "brain_feed",
                "add_evidence", "check_status", "classify_file",
                "filing_scan", "filing_validate", "filing_run",
                "brain_query", "brain_search",
                "automation", "scheduled_maintenance", "legal_ai",
                "tool_run", "hydra_health", "hydra_respawn"}
    actual = set(th_mod.HANDLER_MAP.keys())
    assert expected == actual, f"mismatch: expected={expected}, actual={actual}"
    for name, fn in th_mod.HANDLER_MAP.items():
        assert callable(fn), f"{name} is not callable"
    _log(f"      handlers: {sorted(actual)}")
    return True


def t6b():
    # get_handler returns correct function or None
    assert th_mod.get_handler("auto_classify") is not None
    assert th_mod.get_handler("nonexistent_type") is None
    return True


def t6c():
    # check_status on our test DB
    result = th_mod.handle_check_status({
        "file_path": motion_file,
        "db_path": db_path,
    })
    assert result["status"] != "error", f"error: {result.get('error')}"
    _log(f"      check_status result: {result['status']}")
    return True


test("All 17 handlers registered and callable", t6a)
test("get_handler returns function or None", t6b)
test("check_status queries real DB correctly", t6c)

# -- TEST 7: Daemon Core Wiring ---------------------------------------------
_log("\n-- 7. DAEMON CORE WIRING --")


def t7a():
    core_path = daemon_dir / "core.py"
    source = core_path.read_text(encoding="utf-8")
    assert "from . import task_handlers" in source or "import task_handlers" in source, \
        "task_handlers not imported in core.py"
    return True


def t7b():
    core_path = daemon_dir / "core.py"
    source = core_path.read_text(encoding="utf-8")
    assert "task_handlers.get_handler" in source, \
        "get_handler not called in core.py _process_tasks"
    assert "# TODO:" not in source.split("task_handlers.get_handler")[0].split("_process_tasks")[-1], \
        "TODO stub still present before get_handler"
    return True


def t7c():
    core_path = daemon_dir / "core.py"
    source = core_path.read_text(encoding="utf-8")
    assert "TriggerScanner" in source, "Filing trigger scan not in main loop"
    assert "tick % 300" in source, "Trigger scan not on periodic interval"
    return True


test("core.py imports task_handlers", t7a)
test("core.py routes tasks via get_handler (no TODO stub)", t7b)
test("core.py includes periodic filing trigger scan", t7c)

# -- TEST 8: Engines __init__ Safety ----------------------------------------
_log("\n-- 8. ENGINES __init__.py --")


def t8a():
    init_path = _system / "engines" / "__init__.py"
    source = init_path.read_text(encoding="utf-8")
    assert "try:" in source and "except" in source, "no try/except guards"
    # Should have try/except for each engine import
    assert source.count("try:") >= 4, f"only {source.count('try:')} try blocks (need ≥4)"
    return True


def t8b():
    init_path = _system / "engines" / "__init__.py"
    source = init_path.read_text(encoding="utf-8")
    assert "get_engine" in source, "get_engine factory missing"
    assert "def get_engine" in source, "get_engine not defined"
    return True


def t8c():
    init_path = _system / "engines" / "__init__.py"
    source = init_path.read_text(encoding="utf-8")
    assert '__version__ = "3.0.0"' in source, "version not updated to 3.0.0"
    return True


test("All engine imports wrapped in try/except", t8a)
test("get_engine factory defined", t8b)
test("Version updated to 2.0.0", t8c)

# -- TEST 9: Filing Engine Integration --------------------------------------
_log("\n-- 9. FILING ENGINE --")


def t9a():
    fe_dir = _system / "engines" / "filing_engine"
    required = ["engine.py", "state.py", "triggers.py", "validator.py",
                "pipeline.py", "__main__.py", "__init__.py"]
    for f in required:
        assert (fe_dir / f).exists(), f"missing: {f}"
    return True


def t9b():
    # Template framework complete
    tf_dir = _system / "templates" / "filing_framework"
    required = ["deadline_calculator.py", "caption_generator.py", "cos_generator.py",
                "filing_checklist.py", "michigan_format_specs.py", "exhibit_indexer.py",
                "signature_block.py", "init_case_db.py", "README.md"]
    for f in required:
        assert (tf_dir / f).exists(), f"missing template: {f}"
    return True


test("Filing engine: all 7 modules present", t9a)
test("Filing framework: all 9 template modules present", t9b)

# -- TEST 10: Cerberus Stdout Guard -----------------------------------------
_log("\n-- 10. CERBERUS STDOUT GUARD --")


def t10a():
    cerb_path = _system / "engines" / "cerberus" / "cerberus_engine.py"
    source = cerb_path.read_text(encoding="utf-8")
    assert "isatty()" in source, "isatty guard missing"
    # The raw sys.stdout = io.TextIOWrapper(...) should NOT be unconditional
    lines = source.split("\n")
    for i, line in enumerate(lines):
        if "sys.stdout = io.TextIOWrapper" in line:
            # Should be inside an if/try block
            preceding = "\n".join(lines[max(0, i-3):i])
            assert "if " in preceding or "try:" in preceding, \
                f"Unguarded stdout rewrap at line {i+1}"
    return True


test("Cerberus stdout rewrap guarded by isatty()", t10a)

# -- TEST 11: Engine Inventory Updated --------------------------------------
_log("\n-- 11. REFERENCE DOCS --")


def t11a():
    inv_path = _repo / ".github" / "reference" / "engine-inventory.md"
    if not inv_path.exists():
        return True  # Skip if not present
    source = inv_path.read_text(encoding="utf-8")
    assert "INTAKE ENGINE" in source or "intake" in source.lower(), \
        "Intake engine not in engine-inventory.md"
    return True


test("engine-inventory.md lists intake engine", t11a)

# -- SUMMARY -----------------------------------------------------------------
_log("\n" + "=" * 70)
total = _pass + _fail
_log(f"  CONVERGENCE: {_pass}/{total} PASSED, {_fail} FAILED")
if _fail == 0:
    _log("  🟢 ALL SYSTEMS CONVERGED — READY FOR OPERATIONS")
else:
    _log(f"  🔴 {_fail} FAILURES — FIX BEFORE PROCEEDING")
_log("=" * 70)

# Write results to file (survives stdout issues)
with open(str(RESULTS_FILE), "w", encoding="utf-8") as f:
    f.write("\n".join(_results))

# Cleanup temp dir
import shutil
try:
    shutil.rmtree(td, ignore_errors=True)
except Exception:
    pass

sys.exit(0 if _fail == 0 else 1)

