import os, json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from .engine.ingest import IngestEngine
from .engine.ruleswatch import RuleWatcher
from .engine.graph import GraphEngine
from .engine.actions import ActionabilityEngine
from .engine.forms_gate import FormsGate
from .engine.binder import Binderizer
from .engine.canon import CanonDetector
from .engine.entities import VeilPiercer
from .engine.rules_intel import RulesIntelligenceCore
from .engine.odb import ODB
from .engine.autodraft import AutoDraftEngine
from .engine.validate import ValidationEngine
from .engine.calendar import CalendarEngine
from .engine.graph_analytics import GraphAnalytics
from .engine.evidence import EvidenceManifest
from .engine.template_patcher import TemplatePatcher
from .engine.strike_seed import GraphStrikeSeeder
from .engine.mifile_packager import MiFilePackager, CaseProfileStore
from .engine.scao_fill import ScaoFiller
from .engine.pdf_normalize import PdfNormalizer
from .engine.venue_rules import VenueRules

from .engine.graph_importer import GraphImporter
from .engine.graph_schema_importer import GraphSchemaImporter
from .engine.drivepuller_bulk import DrivePullerBulk
from .engine.drivepuller import DrivePuller

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "..", "..", "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="Litigation OS — SUPREME Integrator")

class StartIngest(BaseModel):
    paths: List[str]
    exts: Optional[List[str]] = None

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.now().isoformat()}

@app.post("/api/ingest/start")
def api_ingest_start(payload: StartIngest):
    eng = IngestEngine()
    result = eng.run(paths=payload.paths, exts=payload.exts or [".pdf", ".docx", ".txt", ".csv", ".json"])
    return result

@app.get("/api/ingest/status")
def api_ingest_status():
    index_path = os.path.join(DATA_DIR, "evidence_index.json")
    if not os.path.exists(index_path):
        return {"indexed": 0}
    data = json.load(open(index_path, "r", encoding="utf-8"))
    return {"indexed": len(data.get("files", []))}

@app.post("/api/ruleswatch/run")
def api_ruleswatch_run():
    rw = RuleWatcher()
    return rw.run_once()

@app.post("/api/graph/ingest")
async def api_graph_ingest(run_id: Optional[str] = Form(None), nodes: UploadFile = File(...), edges: UploadFile = File(...)):
    ge = GraphEngine()
    rid = ge.save_run(nodes, edges, run_id=run_id)
    return {"run_id": rid}

@app.get("/api/graph/runs")
def api_graph_runs():
    base = os.path.join(DATA_DIR, "graph_runs")
    if not os.path.exists(base):
        return {"runs": []}
    runs = sorted(os.listdir(base))
    return {"runs": runs}

@app.post("/api/actions/best")
def api_actions_best(context: Optional[Dict[str, Any]] = None):
    ae = ActionabilityEngine()
    return ae.best_action(context=context or {})

@app.post("/api/forms/map")
def api_forms_map(action: str):
    fg = FormsGate()
    return fg.map_action_to_forms(action)

@app.post("/api/binder/build")
def api_binder_build(action: str):
    bz = Binderizer()
    path = bz.build(action=action)
    return {"zip_path": path}

@app.post("/api/canon/scan")
def api_canon_scan(timeline: Optional[List[Dict[str, Any]]] = None):
    cd = CanonDetector()
    return cd.scan(timeline or [])

@app.post("/api/entities/map")
def api_entities_map(records: Optional[List[Dict[str, Any]]] = None):
    vp = VeilPiercer()
    return vp.map_entities(records or [])

@app.post("/api/rulesintel/analyze")
def api_rulesintel_analyze(results: dict):
    ric = RulesIntelligenceCore()
    return ric.analyze_and_patch(results)

@app.post("/api/odb/run")
def api_odb_run(context: dict | None = None):
    odb = ODB()
    return odb.run(context or {})

@app.post("/api/draft/build")
def api_draft_build(action: str):
    ad = AutoDraftEngine()
    out = ad.build(action=action, context={})
    ve = ValidationEngine()
    val = ve.scan_text_files(out["files"])
    ce = CalendarEngine()
    cal = ce.build_deadlines(action)
    out["validation"] = val
    out["calendar"] = cal
    return out


@app.post("/api/graph/import/generate")
def api_graph_import_generate(run_id: str | None = None):
    gi = GraphImporter()
    schema = gi.generate_import_pack(run_id)
    return schema

@app.post("/api/drive/ingest")
def api_drive_ingest(path: str):
    dp = DrivePuller()
    return dp.ingest_path(path)


@app.post("/api/graph/import/generate_schema")
def api_graph_import_generate_schema(run_id: str | None = None):
    gsi = GraphSchemaImporter()
    return gsi.generate_schema_pack(run_id)

@app.post("/api/drive/ingest/bulk")
def api_drive_ingest_bulk(paths: list[str] | None = None):
    dpb = DrivePullerBulk()
    return dpb.run(paths or [])


@app.post("/api/graph/analyze")
def api_graph_analyze(run_id: str | None = None):
    ga = GraphAnalytics()
    return ga.analyze(run_id)

@app.post("/api/odb/run_with_graph")
def api_odb_run_with_graph(run_id: str | None = None):
    ga = GraphAnalytics()
    analysis = ga.analyze(run_id)
    pressure = analysis.get("pressure", {}) if analysis.get("ok") else {}
    odb = ODB()
    plan = odb.run({"pressure": pressure})
    return {"analysis": analysis, "plan": plan}


@app.post("/api/evidence/manifest")
def api_evidence_manifest(prefix: str = "AJB", start: int = 1):
    em = EvidenceManifest()
    return em.build(prefix=prefix, start=start)

@app.post("/api/templates/patch")
def api_templates_patch():
    tp = TemplatePatcher()
    return tp.patch()

@app.post("/api/strike/oneclick")
def api_strike_oneclick(run_id: str | None = None, action: str | None = None):
    # 1) Analyze graph
    ga = GraphAnalytics()
    analysis = ga.analyze(run_id)
    pressure = analysis.get("pressure", {}) if analysis.get("ok") else {}

    # 2) Patch templates (optional hot update)
    tp = TemplatePatcher()
    _ = tp.patch()

    # 3) Run ODB with pressure to pick best action
    odb = ODB()
    plan = odb.run({"pressure": pressure})
    chosen = action or plan["chosen_action"]

    # 4) Seed allegations/exhibits
    gs = GraphStrikeSeeder()
    seed = gs.seed_from_run(analysis.get("run_id") if analysis.get("ok") else None)

    # 5) Load clauses from templates
    templates_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates")
    def readp(name):
        path = os.path.join(templates_root, name)
        return open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
    clauses = {
        "service": readp("service_clause.txt"),
        "parenting_time": readp("parenting_time_clause.txt"),
        "motion_standard": readp("motion_standard.txt")
    }

    # 6) Build draft bundle
    ad = AutoDraftEngine()
    context = {
        "allegations": seed.get("allegations", []) if seed.get("ok") else [],
        "exhibits": seed.get("exhibits", []) if seed.get("ok") else [],
        "clauses": clauses
    }
    bundle = ad.build(action=chosen, context=context)
    return {"analysis": analysis, "plan": plan, "seed": seed, "bundle": bundle}


@app.post("/api/case/profile/save")
def api_case_profile_save(profile: dict):
    store = CaseProfileStore()
    return store.save(profile)

@app.get("/api/case/profile/load")
def api_case_profile_load(case_id: str):
    store = CaseProfileStore()
    return store.load(case_id)

@app.post("/api/mifile/build")
def api_mifile_build(case_id: str, action: str, prefix: str = "AJB"):
    mp = MiFilePackager()
    return mp.build(case_id=case_id, action=action, prefix=prefix)


@app.post("/api/scao/fill")
def api_scao_fill(case_id: str, form_id: str, action: str, out_dir: str | None = None):
    store = CaseProfileStore()
    case = store.load(case_id)
    if not case.get("ok"):
        return case
    filler = ScaoFiller()
    od = out_dir or os.path.join(os.path.dirname(store.path_for(case_id)), "forms_out")
    os.makedirs(od, exist_ok=True)
    return filler.fill(form_id=form_id, profile=case["profile"], action=action, out_dir=od)

@app.post("/api/pdf/normalize")
def api_pdf_normalize(src: str, out: str):
    pn = PdfNormalizer()
    return pn.normalize(src, out)

@app.get("/api/venue/rules/load")
def api_rules_load(county: str):
    vr = VenueRules(os.path.join(os.path.dirname(__file__), "..", "rules", "mi"))
    return vr.load(county)

@app.post("/api/odb/run_compliant")
def api_odb_run_compliant(county: str, completed: list[str] | None = None):
    # Run ODB with graph pressure then check venue dependencies for the chosen action
    ga = GraphAnalytics()
    analysis = ga.analyze(None)
    pressure = analysis.get("pressure", {}) if analysis.get("ok") else {}
    odb = ODB()
    plan = odb.run({"pressure": pressure})

    vr = VenueRules(os.path.join(os.path.dirname(__file__), "..", "rules", "mi"))
    loaded = vr.load(county)
    if not loaded.get("ok"):
        return {"ok": False, "error": loaded.get("error"), "plan": plan}
    check = vr.check_plan(loaded["rules"], plan["chosen_action"], completed or [])
    plan["venue_check"] = check
    if not check["compliant"]:
        # Naive: if missing deps, try drop to next action in ranking
        for alt, score in plan.get("ranking", [])[1:]:
            alt_check = vr.check_plan(loaded["rules"], alt, completed or [])
            if alt_check["compliant"]:
                plan["chosen_action_alt"] = alt
                plan["venue_check_alt"] = alt_check
                break
    return {"ok": True, "analysis": analysis, "plan": plan, "rules": loaded}
