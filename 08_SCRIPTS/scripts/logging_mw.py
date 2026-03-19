import time, json, uuid, os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

AUDIT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "audit", "audit.jsonl"))
os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        response.headers["X-Request-ID"] = rid
        log = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "rid": rid,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms
        }
        with open(AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log) + "\n")
        return response
