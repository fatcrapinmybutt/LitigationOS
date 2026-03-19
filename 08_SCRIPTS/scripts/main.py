import os, json, hashlib, time, csv
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from .engine.ingest import IngestEngine
from .engine.ruleswatch import RuleWatcher
from .engine.graph import GraphEngine
from .engine.actions import ActionabilityEngine
from .engine.forms_gate import FormsGate
from .engine.binder import Binderizer
from .engine.canon import CanonDetector
from .engine.entities import VeilPiercer
from .engine.draft_engine import DraftEngine
from .engine.orchestrator import MultiFrontOrchestrator
from .engine.rules_intel import RulesIntelligenceCore

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_ROOT, "..", "..", "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="Litigation OS — v5 API")

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
    # simple status from ledger
    index_path = os.path.join(DATA_DIR, "evidence_index.json")
    if not os.path.exists(index_path):
        return {"indexed": 0}
    data = json.load(open(index_path, "r", encoding="utf-8"))
    return {"indexed": len(data.get("files", []))}

@app.post("/api/ruleswatch/run")
def api_ruleswatch_run():
    rw = RuleWatcher()
    result = rw.run_once()
    return result

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


@app.post("/api/autodraft/generate")
def api_autodraft_generate(action: str = "Injunction/TRO (Stay eviction, enforce parenting time, suspend PPO)"):
    de = DraftEngine(DATA_DIR)
    # naive route selection
    if "injunction" in action.lower():
        path = de.injunction_doc()
    elif "complaint" in action.lower() or "§1983" in action.lower() or "rico" in action.lower():
        path = de.complaint_doc()
    elif "disqualify" in action.lower():
        path = de.disqualification_doc()
    elif "relief from judgment" in action.lower():
        path = de.relief_from_judgment_doc()
    elif "appeal" in action.lower():
        path = de.appeal_packet()
    elif "show cause" in action.lower():
        path = de.show_cause_doc()
    elif "discovery" in action.lower():
        path = de.discovery_packet()
    elif "jtc" in action.lower():
        path = de.jtc_complaint()
    elif "egle" in action.lower():
        path = de.egle_letter()
    elif "hud" in action.lower():
        path = de.hud_letter()
    elif "foia" in action.lower():
        path = de.foia_request()
    else:
        path = de.discovery_packet()
    return {"docx_path": path}

@app.post("/api/orchestrate/strike")
def api_orchestrate_strike(topk: int = 3):
    # Use ODB ranking by calling /api/odb/run logic directly
    odb = ODB()
    plan = odb.run({})
    mfo = MultiFrontOrchestrator(DATA_DIR)
    result = mfo.orchestrate(plan["ranking"], topk=topk)
    return {"odb_plan": plan, "orchestrated": result}


@app.post("/api/forms/catalog/update")
def api_forms_catalog_update():
    fc = FormsCatalog(DATA_DIR)
    return fc.build()

@app.get("/api/forms/resolve")
def api_forms_resolve(action: str):
    ff = FormsForge(DATA_DIR)
    return ff.resolve_for_action(action)
