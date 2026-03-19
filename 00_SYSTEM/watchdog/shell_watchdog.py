#!/usr/bin/env python3
"""
MANBEARPIG Shell Watchdog & Process Manager v1.0

Monitors and manages:
- PowerShell shell sessions (track, recover, prevent orphans)
- Background agent tasks (timeout enforcement, status logging)
- System health (DB locks, memory, disk space)

CLI Usage:
  python shell_watchdog.py check      # Run one health check
  python shell_watchdog.py status     # Full status report
  python shell_watchdog.py shells     # List active shells
  python shell_watchdog.py agents     # List running agents
  python shell_watchdog.py events     # Recent events
  python shell_watchdog.py health     # Health history
  python shell_watchdog.py guard      # Run continuous monitoring loop
"""

import os, sys, json, time, sqlite3, subprocess, logging, threading
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ── Config ──
WATCHDOG_DIR = Path(r'C:\Users\andre\LitigationOS\00_SYSTEM\watchdog')
WATCHDOG_DB = WATCHDOG_DIR / 'watchdog.db'
HEARTBEAT_FILE = WATCHDOG_DIR / 'heartbeat.json'
LOG_FILE = WATCHDOG_DIR / 'watchdog.log'

SHELL_TIMEOUT_SECONDS = 600
AGENT_TIMEOUT_SECONDS = 1800
HEALTH_CHECK_INTERVAL = 30
MAX_CONCURRENT_SHELLS = 8
DISK_WARNING_GB = 5
MEMORY_WARNING_PCT = 90

WATCHDOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger('watchdog')


class WatchdogDB:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(self.db_path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=5000")
        return c

    def _init_db(self):
        c = self._conn()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS shell_sessions (
                shell_id TEXT PRIMARY KEY, pid INTEGER, command TEXT,
                started_at TEXT DEFAULT (datetime('now')),
                last_activity TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'active', exit_code INTEGER,
                output_bytes INTEGER DEFAULT 0, error_count INTEGER DEFAULT 0, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS agent_tasks (
                agent_id TEXT PRIMARY KEY, agent_type TEXT, description TEXT,
                started_at TEXT DEFAULT (datetime('now')), completed_at TEXT,
                status TEXT DEFAULT 'running', elapsed_seconds REAL,
                result_summary TEXT, error TEXT
            );
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TEXT DEFAULT (datetime('now')),
                active_shells INTEGER, active_agents INTEGER,
                python_processes INTEGER, disk_free_gb REAL,
                memory_used_pct REAL, db_size_gb REAL,
                db_locked INTEGER DEFAULT 0, warnings TEXT, errors TEXT
            );
            CREATE TABLE IF NOT EXISTS process_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT DEFAULT (datetime('now')),
                event_type TEXT, process_type TEXT, process_id TEXT,
                pid INTEGER, details TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_shell_status ON shell_sessions(status);
            CREATE INDEX IF NOT EXISTS idx_agent_status ON agent_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_health_time ON health_checks(check_time);
        """)
        c.commit(); c.close()

    def log_event(self, etype, ptype, pid_str, pid=None, details=None):
        c = self._conn()
        c.execute("INSERT INTO process_events (event_type,process_type,process_id,pid,details) VALUES (?,?,?,?,?)",
                  (etype, ptype, pid_str, pid, details))
        c.commit(); c.close()

    def register_shell(self, sid, pid, cmd):
        c = self._conn()
        c.execute("INSERT OR REPLACE INTO shell_sessions (shell_id,pid,command,status) VALUES (?,?,?,'active')", (sid, pid, cmd))
        c.commit(); c.close()
        self.log_event('created', 'shell', sid, pid, cmd[:200])

    def update_shell(self, sid):
        c = self._conn()
        c.execute("UPDATE shell_sessions SET last_activity=datetime('now') WHERE shell_id=?", (sid,))
        c.commit(); c.close()

    def mark_shell_dead(self, sid, exit_code=None, reason='unknown'):
        c = self._conn()
        c.execute("UPDATE shell_sessions SET status='dead', exit_code=?, notes=? WHERE shell_id=?", (exit_code, reason, sid))
        c.commit(); c.close()
        self.log_event('died', 'shell', sid, details=reason)

    def register_agent(self, aid, atype, desc):
        c = self._conn()
        c.execute("INSERT OR REPLACE INTO agent_tasks (agent_id,agent_type,description,status) VALUES (?,?,?,'running')", (aid, atype, desc))
        c.commit(); c.close()
        self.log_event('started', 'agent', aid, details=desc[:200])

    def complete_agent(self, aid, status='completed', result=None, error=None):
        c = self._conn()
        c.execute("""UPDATE agent_tasks SET status=?, completed_at=datetime('now'),
            elapsed_seconds=(julianday('now')-julianday(started_at))*86400,
            result_summary=?, error=? WHERE agent_id=?""",
            (status, result[:500] if result else None, error, aid))
        c.commit(); c.close()

    def get_active_shells(self):
        c = self._conn()
        r = [dict(x) for x in c.execute("SELECT * FROM shell_sessions WHERE status='active'").fetchall()]
        c.close(); return r

    def get_active_agents(self):
        c = self._conn()
        r = [dict(x) for x in c.execute("SELECT * FROM agent_tasks WHERE status='running'").fetchall()]
        c.close(); return r

    def record_health(self, **kw):
        c = self._conn()
        c.execute("""INSERT INTO health_checks (active_shells,active_agents,python_processes,
            disk_free_gb,memory_used_pct,db_size_gb,db_locked,warnings,errors)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (kw.get('active_shells',0), kw.get('active_agents',0), kw.get('python_processes',0),
             kw.get('disk_free_gb',0), kw.get('memory_used_pct',0), kw.get('db_size_gb',0),
             kw.get('db_locked',0), kw.get('warnings',''), kw.get('errors','')))
        c.commit(); c.close()

    def get_recent_health(self, n=10):
        c = self._conn()
        r = [dict(x) for x in c.execute("SELECT * FROM health_checks ORDER BY check_time DESC LIMIT ?", (n,)).fetchall()]
        c.close(); return r

    def get_stats(self):
        c = self._conn()
        s = {}
        s['total_shells'] = c.execute("SELECT COUNT(*) FROM shell_sessions").fetchone()[0]
        s['active_shells'] = c.execute("SELECT COUNT(*) FROM shell_sessions WHERE status='active'").fetchone()[0]
        s['dead_shells'] = c.execute("SELECT COUNT(*) FROM shell_sessions WHERE status='dead'").fetchone()[0]
        s['total_agents'] = c.execute("SELECT COUNT(*) FROM agent_tasks").fetchone()[0]
        s['running_agents'] = c.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='running'").fetchone()[0]
        s['completed_agents'] = c.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='completed'").fetchone()[0]
        s['failed_agents'] = c.execute("SELECT COUNT(*) FROM agent_tasks WHERE status='failed'").fetchone()[0]
        s['total_events'] = c.execute("SELECT COUNT(*) FROM process_events").fetchone()[0]
        avg = c.execute("SELECT AVG(elapsed_seconds) FROM agent_tasks WHERE status='completed'").fetchone()[0]
        s['avg_agent_seconds'] = round(avg, 1) if avg else 0
        c.close()
        return s


class ProcessMonitor:
    @staticmethod
    def get_python_processes():
        try:
            r = subprocess.run(['powershell', '-Command',
                "Get-Process python*,pwsh* -ErrorAction SilentlyContinue | Select Id,ProcessName,CPU,@{N='MB';E={[math]::Round($_.WorkingSet64/1MB)}} | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10)
            if r.stdout.strip():
                d = json.loads(r.stdout)
                return [d] if isinstance(d, dict) else d
        except: pass
        return []

    @staticmethod
    def get_disk_free_gb():
        try:
            r = subprocess.run(['powershell', '-Command', "(Get-PSDrive C).Free / 1GB"],
                capture_output=True, text=True, timeout=5)
            return round(float(r.stdout.strip()), 2)
        except: return -1

    @staticmethod
    def get_memory_pct():
        try:
            r = subprocess.run(['powershell', '-Command',
                "$os = Get-CimInstance Win32_OperatingSystem; [math]::Round((1-$os.FreePhysicalMemory/$os.TotalVisibleMemorySize)*100,1)"],
                capture_output=True, text=True, timeout=10)
            return float(r.stdout.strip())
        except: return -1

    @staticmethod
    def is_alive(pid):
        try:
            r = subprocess.run(['powershell', '-Command', f"Get-Process -Id {pid} -ErrorAction SilentlyContinue"],
                capture_output=True, text=True, timeout=5)
            return str(pid) in r.stdout
        except: return False

    @staticmethod
    def db_size_gb():
        p = Path(r'C:\Users\andre\LitigationOS\litigation_context.db')
        return round(p.stat().st_size / (1024**3), 2) if p.exists() else 0

    @staticmethod
    def db_locked():
        try:
            c = sqlite3.connect(r'C:\Users\andre\LitigationOS\litigation_context.db', timeout=2)
            c.execute("SELECT 1 FROM sqlite_master LIMIT 1"); c.close()
            return False
        except: return True


class ShellWatchdog:
    def __init__(self):
        self.db = WatchdogDB(WATCHDOG_DB)
        self.mon = ProcessMonitor()
        self.running = False
        self._checks = 0
        self._warns = []
        self._errs = []

    def heartbeat(self):
        hb = {
            'pid': os.getpid(), 'timestamp': datetime.now().isoformat(),
            'check_count': self._checks, 'status': 'running' if self.running else 'idle',
            'shells': len(self.db.get_active_shells()),
            'agents': len(self.db.get_active_agents()),
            'warnings': self._warns[-5:], 'errors': self._errs[-5:]
        }
        with open(HEARTBEAT_FILE, 'w') as f: json.dump(hb, f, indent=2)

    def check_shells(self):
        active = self.db.get_active_shells()
        dead = 0
        for sh in active:
            pid = sh.get('pid')
            sid = sh['shell_id']
            if pid and not self.mon.is_alive(pid):
                self.db.mark_shell_dead(sid, reason='process_gone')
                dead += 1; log.warning(f"Shell {sid} (PID {pid}) gone")
                continue
            if sh.get('last_activity'):
                try:
                    idle = (datetime.now() - datetime.fromisoformat(sh['last_activity'])).total_seconds()
                    if idle > SHELL_TIMEOUT_SECONDS:
                        self.db.mark_shell_dead(sid, reason=f'idle_{int(idle)}s')
                        dead += 1; log.warning(f"Shell {sid} idle {int(idle)}s")
                except: pass
        if dead: self._warns.append(f"{dead} shells died {datetime.now():%H:%M:%S}")
        return len(active) - dead

    def check_agents(self):
        active = self.db.get_active_agents()
        warn = 0
        for a in active:
            if a.get('started_at'):
                try:
                    elapsed = (datetime.now() - datetime.fromisoformat(a['started_at'])).total_seconds()
                    if elapsed > AGENT_TIMEOUT_SECONDS:
                        warn += 1
                        log.warning(f"Agent {a['agent_id']} running {int(elapsed)}s")
                except: pass
        if warn: self._warns.append(f"{warn} agents slow {datetime.now():%H:%M:%S}")
        return len(active)

    def check_system(self):
        w, e = [], []
        disk = self.mon.get_disk_free_gb()
        if 0 < disk < DISK_WARNING_GB: w.append(f"Low disk: {disk:.1f}GB")
        mem = self.mon.get_memory_pct()
        if mem > MEMORY_WARNING_PCT: w.append(f"High mem: {mem:.0f}%")
        locked = self.mon.db_locked()
        if locked: e.append("DB LOCKED")
        dbsz = self.mon.db_size_gb()
        self._warns.extend(w); self._errs.extend(e)
        return {'disk_free_gb': disk, 'memory_pct': mem, 'db_size_gb': dbsz, 'db_locked': locked, 'warnings': w, 'errors': e}

    def run_check(self):
        self._checks += 1
        shells = self.check_shells()
        agents = self.check_agents()
        sys_h = self.check_system()
        procs = self.mon.get_python_processes()
        self.db.record_health(
            active_shells=shells, active_agents=agents, python_processes=len(procs),
            disk_free_gb=sys_h['disk_free_gb'], memory_used_pct=sys_h['memory_pct'],
            db_size_gb=sys_h['db_size_gb'], db_locked=1 if sys_h['db_locked'] else 0,
            warnings='; '.join(sys_h['warnings']), errors='; '.join(sys_h['errors']))
        self.heartbeat()
        self._warns = self._warns[-20:]; self._errs = self._errs[-20:]
        return {'check': self._checks, 'shells': shells, 'agents': agents,
                'processes': len(procs), **sys_h}

    def guard_loop(self, interval=HEALTH_CHECK_INTERVAL):
        """Run continuous monitoring."""
        self.running = True
        log.info(f"Watchdog guard started (PID {os.getpid()}, interval {interval}s)")
        try:
            while self.running:
                result = self.run_check()
                log.info(f"Check #{result['check']}: shells={result['shells']} agents={result['agents']} disk={result['disk_free_gb']:.1f}GB mem={result['memory_pct']:.0f}%")
                time.sleep(interval)
        except KeyboardInterrupt:
            log.info("Watchdog stopped by user")
        self.running = False
        self.heartbeat()


def main():
    import argparse
    p = argparse.ArgumentParser(description='MANBEARPIG Shell Watchdog v1.0')
    p.add_argument('command', choices=['check','status','stats','shells','agents','events','health','guard'])
    p.add_argument('--json', action='store_true')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--interval', type=int, default=30)
    args = p.parse_args()

    wd = ShellWatchdog()

    if args.command == 'check':
        r = wd.run_check()
        if args.json: print(json.dumps(r, indent=2, default=str))
        else:
            print(f"  Health Check #{r['check']}")
            print(f"   Shells: {r['shells']} | Agents: {r['agents']} | Procs: {r['processes']}")
            print(f"   Disk: {r['disk_free_gb']:.1f}GB | Mem: {r['memory_pct']:.0f}% | DB: {r['db_size_gb']:.1f}GB {'LOCKED' if r['db_locked'] else 'ok'}")
            for w in r.get('warnings',[]): print(f"   >> {w}")
            for e in r.get('errors',[]): print(f"   !! {e}")

    elif args.command == 'status':
        r = wd.run_check()
        s = wd.db.get_stats()
        print(f"MANBEARPIG Watchdog v1.0 (PID {os.getpid()})")
        print(f"  Shells: {s['active_shells']}/{s['total_shells']} | Dead: {s['dead_shells']}")
        print(f"  Agents: {s['running_agents']}/{s['total_agents']} | Done: {s['completed_agents']} | Fail: {s['failed_agents']}")
        print(f"  Avg agent time: {s['avg_agent_seconds']}s | Events logged: {s['total_events']}")
        print(f"  Disk: {r['disk_free_gb']:.1f}GB | Mem: {r['memory_pct']:.0f}% | DB: {r['db_size_gb']:.1f}GB")

    elif args.command == 'stats':
        print(json.dumps(wd.db.get_stats(), indent=2, default=str))

    elif args.command == 'shells':
        for s in wd.db.get_active_shells():
            print(f"  [{s['shell_id']}] PID={s.get('pid')} cmd={s.get('command','')[:60]} last={s.get('last_activity','?')}")
        if not wd.db.get_active_shells(): print("  No active shells")

    elif args.command == 'agents':
        for a in wd.db.get_active_agents():
            print(f"  [{a['agent_id']}] {a.get('agent_type','?')} - {a.get('description','')[:60]}")
        if not wd.db.get_active_agents(): print("  No running agents")

    elif args.command == 'events':
        c = wd.db._conn()
        for r in c.execute("SELECT * FROM process_events ORDER BY event_time DESC LIMIT ?", (args.limit,)).fetchall():
            print(f"  {r['event_time']} [{r['event_type']}] {r['process_type']}:{r['process_id']} - {(r.get('details') or '')[:80]}")
        c.close()

    elif args.command == 'health':
        for h in wd.db.get_recent_health(args.limit):
            flag = ' !!' if h.get('errors') else (' >>' if h.get('warnings') else ' ok')
            print(f"  {h['check_time']}{flag} sh={h['active_shells']} ag={h['active_agents']} disk={h.get('disk_free_gb',0):.1f}GB mem={h.get('memory_used_pct',0):.0f}%")

    elif args.command == 'guard':
        wd.guard_loop(args.interval)

if __name__ == '__main__':
    main()
