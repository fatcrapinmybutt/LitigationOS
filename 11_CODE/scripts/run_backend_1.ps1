python -m venv .venv
.\.venv\Scripts\pip install -r backend/requirements.txt
.\.venv\Scripts\python -m uvicorn backend.orchestrator:app --reload --host 127.0.0.1 --port 8000
