import os, sqlite3, json, datetime
DB_PATH = os.getenv("LITOS_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "litigation_os.db")))
SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql"))

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = get_conn()
    with conn:
        conn.executescript(sql)
    # Jobs tables
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );""")
        conn.execute("""CREATE TABLE IF NOT EXISTS job_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            time TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );""")
    conn.close()

def put_event(kind, payload):
    conn = get_conn()
    with conn:
        conn.execute("INSERT INTO events(kind, when, payload_json) VALUES (?,?,?)",
                     (kind, datetime.datetime.now().isoformat(), json.dumps(payload)))
    conn.close()

def create_job(kind, payload):
    conn = get_conn()
    with conn:
        cur = conn.execute("INSERT INTO jobs(kind, created_at, status, payload_json) VALUES (?,?,?,?)",
                      (kind, datetime.datetime.now().isoformat(), "queued", json.dumps(payload)))
        job_id = cur.lastrowid
    conn.close()
    return job_id

def next_job(kind=None):
    conn = get_conn()
    if kind:
        row = conn.execute("SELECT * FROM jobs WHERE status='queued' AND kind=? ORDER BY id LIMIT 1", (kind,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def set_job_status(job_id, status):
    conn = get_conn()
    with conn:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.close()

def log_job(job_id, level, message):
    conn = get_conn()
    with conn:
        conn.execute("INSERT INTO job_logs(job_id, time, level, message) VALUES (?,?,?,?)",
                     (job_id, datetime.datetime.now().isoformat(), level, message))
    conn.close()

def get_job(job_id:int):
    conn = get_conn()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    logs = conn.execute("SELECT * FROM job_logs WHERE job_id=? ORDER BY id", (job_id,)).fetchall()
    conn.close()
    return (dict(job) if job else None, [dict(r) for r in logs])
