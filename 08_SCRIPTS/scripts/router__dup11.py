from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os

router = APIRouter()
DELIV_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../deliverables"))

@router.post("/build")
async def build():
    viewer = os.path.join(DELIV_DIR, "graph.html")
    open(viewer,"w",encoding="utf-8").write("<html><body><h1>Nexus Graph</h1></body></html>")
    return JSONResponse({"viewer": viewer})
