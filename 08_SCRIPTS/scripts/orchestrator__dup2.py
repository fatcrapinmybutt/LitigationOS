from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core import db
from core.logging_mw import RequestIDMiddleware
from core.jobs_worker import run_worker
from modules.authority_harvester.router import router as rules_router
from modules.form_governor.router import router as forms_router
from modules.procedure_completer.router import router as procedure_router
from modules.evidence_engine.router import router as evidence_router
from modules.nexus_graph.router import router as nexus_router
from modules.client_packager.router import router as package_router
from modules.system.router import router as system_router

app = FastAPI(title="Litigation OS — Orchestrator v4")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestIDMiddleware)

@app.on_event("startup")
def startup():
    db.init_db()
    run_worker()

@app.get("/health")
def health():
    return {"status":"ok"}

app.include_router(rules_router, prefix="/rules", tags=["Rules Watch"])
app.include_router(forms_router, prefix="/forms", tags=["Form Bank"])
app.include_router(procedure_router, prefix="/procedure", tags=["Procedural Map"])
app.include_router(evidence_router, prefix="/evidence", tags=["Evidence Audit"])
app.include_router(nexus_router, prefix="/nexus", tags=["Nexus Graph"])
app.include_router(package_router, prefix="/package", tags=["Client Packager"])
app.include_router(system_router, prefix="/system", tags=["System"])
