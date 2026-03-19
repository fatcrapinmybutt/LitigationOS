from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI(title="FRED Query Engine")

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
def query_project_files(request: QueryRequest):
    # This should search your local Benchbooks, MCR, MCL files (use LangChain, OCR, etc)
    # Stubbed response — replace with actual doc search logic
    allowed_files = ["benchbook.txt", "mcr_rules.txt", "mcl_statutes.txt"]
    hits = [f for f in allowed_files if os.path.exists(f)]

    if not hits:
        raise HTTPException(status_code=403, detail="This information is not available within the project files provided.")

    return {
        "answer": "This response came from Michigan Benchbook paragraph 4.2 on page 18.",
        "source_metadata": {
            "matched_file": "benchbook.txt",
            "matched_section": "4.2",
            "paragraph_id": "BB_0042"
        }
    }
