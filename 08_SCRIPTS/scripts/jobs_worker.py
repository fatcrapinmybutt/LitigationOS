import threading, time, json, os, hashlib
from . import db

TASKS = {}
def task(name):
    def wrap(fn):
        TASKS[name] = fn
        return fn
    return wrap

def run_worker(poll_seconds=1):
    def loop():
        while True:
            job = db.next_job()
            if not job:
                time.sleep(poll_seconds); continue
            job_id = job["id"]; kind = job["kind"]; payload = json.loads(job["payload_json"] or "{}")
            db.set_job_status(job_id, "running")
            db.log_job(job_id, "INFO", f"Starting {kind}")
            try:
                fn = TASKS.get(kind)
                if not fn:
                    raise RuntimeError(f"No handler for job kind={kind}")
                fn(job_id, payload)
                db.set_job_status(job_id, "done")
                db.log_job(job_id, "INFO", "Completed")
            except Exception as e:
                db.set_job_status(job_id, "error")
                db.log_job(job_id, "ERROR", str(e))
    t = threading.Thread(target=loop, daemon=True)
    t.start()
