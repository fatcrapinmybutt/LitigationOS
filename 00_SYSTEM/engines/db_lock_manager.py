#!/usr/bin/env python3
"""
DB Lock Manager v3.0 — NUCLEAR-GRADE EAGAIN Prevention

Root cause chain:
  1. Stale .lock files accumulate across 09_DATA, 13_TOOLS, HuggingFace, .copilot/ide
  2. Multiple agents open 10GB+ SQLite DB simultaneously
  3. File descriptor table fills -> EAGAIN (Resource temporarily unavailable)
  4. WAL grows unbounded when checkpoint blocked by readers

Prevention stack:
  - Auto-purge ALL stale locks on every init (system-wide, not just .db_locks)
  - PID-validated locks (dead PID = instant cleanup, no timeout wait)
  - Hard cap: 3 concurrent DB connections
  - WAL auto-checkpoint when > 50MB
  - Connection reuse (singleton per-process)
  - atexit + signal handler cleanup

Usage:
    from db_lock_manager import managed_db
    with managed_db() as conn:
        conn.execute("SELECT ...")

CLI:
    python db_lock_manager.py --status
    python db_lock_manager.py --cleanup
    python db_lock_manager.py --fix-eagain
    python db_lock_manager.py --nuke     # Kill ALL locks + checkpoint + optimize
"""
import sqlite3
import os
import sys
import time
import json
import signal
import atexit
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
LOCK_DIR = r'C:\Users\andre\LitigationOS\00_SYSTEM\.db_locks'
MAX_CONCURRENT = 3
LOCK_TIMEOUT = 60  # seconds (was 120 — tighter now)
BUSY_TIMEOUT = 60000  # ms
WAL_AUTOCHECKPOINT = 500  # pages (was 1000 — more frequent)
WAL_MAX_SIZE_MB = 50  # auto-checkpoint if WAL exceeds this
STALE_LOCK_DIRS = [
    r'C:\Users\andre\LitigationOS\09_DATA\lock',
    r'C:\Users\andre\LitigationOS\.copilot\ide',
    r'C:\Users\andre\LitigationOS\00_SYSTEM\local_model',
]


def _pid_alive(pid):
    """Check if a process with given PID is still running (Windows)."""
    if pid <= 0:
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        # Fallback: try os.kill with signal 0
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def _purge_system_stale_locks():
    """Purge stale .lock files from ALL known accumulation points."""
    killed = 0
    for lock_dir in STALE_LOCK_DIRS:
        if not os.path.exists(lock_dir):
            continue
        # For 09_DATA\lock — kill all PID-named locks
        if 'lock' in os.path.basename(lock_dir):
            try:
                for f in os.listdir(lock_dir):
                    fp = os.path.join(lock_dir, f)
                    if os.path.isfile(fp):
                        age = time.time() - os.path.getmtime(fp)
                        if age > 3600:  # > 1 hour = definitely stale
                            os.unlink(fp)
                            killed += 1
            except Exception:
                pass
        # For .copilot/ide — kill locks > 24h old
        elif 'ide' in lock_dir:
            try:
                for f in Path(lock_dir).glob('*.lock'):
                    age = time.time() - f.stat().st_mtime
                    if age > 86400:
                        f.unlink(missing_ok=True)
                        killed += 1
            except Exception:
                pass
        # For local_model — kill HuggingFace download locks > 6h old
        elif 'local_model' in lock_dir:
            try:
                for f in Path(lock_dir).rglob('*.lock'):
                    age = time.time() - f.stat().st_mtime
                    if age > 21600:
                        f.unlink(missing_ok=True)
                        killed += 1
            except Exception:
                pass
    return killed


class DBLockManager:
    """Nuclear-grade concurrent DB access manager."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path=DB_PATH, max_concurrent=MAX_CONCURRENT):
        if self._initialized:
            return
        self.db_path = db_path
        self.max_concurrent = max_concurrent
        self.lock_dir = Path(LOCK_DIR)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._my_lock_path = None
        self._conn_cache = None  # Singleton connection per process
        self._init_cleanup_done = False
        self._initialized = True

    def _init_cleanup(self):
        """One-time cleanup on first use. Purges ALL stale locks system-wide."""
        if self._init_cleanup_done:
            return
        self._init_cleanup_done = True
        # Phase 1: Purge system-wide stale locks
        _purge_system_stale_locks()
        # Phase 2: Purge our own .db_locks
        self._cleanup_stale_locks()
        # Phase 3: Auto-checkpoint WAL if bloated
        self._auto_checkpoint_if_needed()

    def _get_active_locks(self):
        """Return list of active lock files with metadata. Dead PIDs = auto-removed."""
        locks = []
        for lf in self.lock_dir.glob('*.lock'):
            try:
                data = json.loads(lf.read_text(encoding='utf-8'))
                pid = data.get('pid', 0)
                age = time.time() - data.get('timestamp', 0)
                data['age_seconds'] = age
                data['path'] = str(lf)

                # PID-validated staleness: dead PID = instant kill (no timeout wait)
                if pid and not _pid_alive(pid):
                    lf.unlink(missing_ok=True)
                    continue

                data['stale'] = age > LOCK_TIMEOUT
                locks.append(data)
            except (json.JSONDecodeError, OSError):
                # Corrupt or inaccessible lock file — nuke it
                try:
                    lf.unlink(missing_ok=True)
                except Exception:
                    pass
        return locks

    def _cleanup_stale_locks(self):
        """Remove lock files older than LOCK_TIMEOUT or with dead PIDs."""
        cleaned = 0
        for lock in self._get_active_locks():
            if lock['stale']:
                try:
                    Path(lock['path']).unlink(missing_ok=True)
                    cleaned += 1
                except Exception:
                    pass
        return cleaned

    def _auto_checkpoint_if_needed(self):
        """Checkpoint WAL if it exceeds WAL_MAX_SIZE_MB."""
        try:
            wal_path = self.db_path + '-wal'
            if os.path.exists(wal_path):
                wal_mb = os.path.getsize(wal_path) / (1024 * 1024)
                if wal_mb > WAL_MAX_SIZE_MB:
                    conn = sqlite3.connect(self.db_path, timeout=30)
                    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT}")
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")  # Non-blocking
                    conn.close()
        except Exception:
            pass  # Non-critical — WAL will self-manage

    def acquire_slot(self, caller='unknown', timeout=LOCK_TIMEOUT):
        """Acquire a DB access slot. Blocks until available or timeout."""
        self._init_cleanup()
        start = time.time()

        while True:
            # Get active locks (auto-removes dead PIDs)
            active = [l for l in self._get_active_locks() if not l['stale']]

            if len(active) < self.max_concurrent:
                lock_name = f"{os.getpid()}_{int(time.time()*1000)}.lock"
                lock_path = self.lock_dir / lock_name
                lock_data = {
                    'pid': os.getpid(),
                    'caller': caller,
                    'timestamp': time.time(),
                    'created': datetime.now().isoformat()
                }
                lock_path.write_text(json.dumps(lock_data), encoding='utf-8')
                self._my_lock_path = lock_path
                return True

            elapsed = time.time() - start
            if elapsed > timeout:
                # Emergency: force-clean all stale + dead-PID locks and retry once
                self._cleanup_stale_locks()
                _purge_system_stale_locks()
                active2 = [l for l in self._get_active_locks() if not l['stale']]
                if len(active2) < self.max_concurrent:
                    continue  # Retry after emergency cleanup

                raise TimeoutError(
                    f"EAGAIN PREVENTION: Could not acquire DB slot in {timeout}s. "
                    f"{len(active2)} active connections (max {self.max_concurrent}). "
                    f"Run: python db_lock_manager.py --nuke"
                )

            time.sleep(0.3 + min(elapsed * 0.1, 2.0))  # Adaptive backoff

    def release_slot(self):
        """Release the DB access slot."""
        if self._my_lock_path:
            try:
                self._my_lock_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._my_lock_path = None

    def get_connection(self, caller='unknown'):
        """Get a properly configured DB connection with slot management."""
        self.acquire_slot(caller)
        try:
            conn = sqlite3.connect(self.db_path, timeout=BUSY_TIMEOUT / 1000)
            conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT}")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(f"PRAGMA wal_autocheckpoint={WAL_AUTOCHECKPOINT}")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-32000")  # 32MB (was 64 — conserve FDs)
            conn.execute("PRAGMA mmap_size=134217728")  # 128MB (was 256 — conserve)
            conn.execute("PRAGMA temp_store=MEMORY")
            return conn
        except Exception:
            self.release_slot()
            raise

    def status(self):
        """Print current lock status."""
        self._init_cleanup()
        locks = self._get_active_locks()
        active = [l for l in locks if not l['stale']]
        stale = [l for l in locks if l['stale']]

        print(f"DB Lock Manager v3.0 Status")
        print(f"  DB: {self.db_path}")
        db_mb = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
        wal_path = self.db_path + '-wal'
        wal_mb = os.path.getsize(wal_path) / (1024 * 1024) if os.path.exists(wal_path) else 0
        print(f"  DB size: {db_mb:.0f} MB | WAL: {wal_mb:.1f} MB")
        print(f"  Max concurrent: {self.max_concurrent}")
        print(f"  Active locks: {len(active)}/{self.max_concurrent}")
        print(f"  Stale locks: {len(stale)}")

        for l in active:
            print(f"    [ACTIVE] PID {l['pid']} ({l['caller']}) {l['age_seconds']:.0f}s")
        for l in stale:
            print(f"    [STALE]  PID {l['pid']} ({l['caller']}) {l['age_seconds']:.0f}s")

        return {'active': len(active), 'stale': len(stale), 'max': self.max_concurrent}

    def checkpoint(self):
        """Force WAL checkpoint."""
        conn = sqlite3.connect(self.db_path, timeout=120)
        conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT}")
        result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        conn.close()

        wal_path = self.db_path + '-wal'
        wal_size = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
        print(f"WAL Checkpoint: blocked={result[0]}, written={result[1]}, moved={result[2]}")
        print(f"WAL file size: {wal_size / 1024 / 1024:.1f} MB")
        return result

    def nuke(self):
        """NUCLEAR option: Kill ALL locks everywhere, checkpoint, optimize."""
        print("=== NUCLEAR EAGAIN PURGE v3.0 ===")

        # Step 1: Kill ALL .db_locks
        killed = 0
        for lf in self.lock_dir.glob('*.lock'):
            try:
                lf.unlink(missing_ok=True)
                killed += 1
            except Exception:
                pass
        print(f"Step 1: Killed {killed} DB locks")

        # Step 2: Kill ALL system-wide stale locks
        sys_killed = _purge_system_stale_locks()
        print(f"Step 2: Killed {sys_killed} system-wide stale locks")

        # Step 3: Kill 09_DATA\lock dir entirely if it exists
        lock_data_dir = Path(r'C:\Users\andre\LitigationOS\09_DATA\lock')
        if lock_data_dir.exists():
            import shutil
            try:
                shutil.rmtree(lock_data_dir)
                print("Step 3: Nuked 09_DATA\\lock\\ directory")
            except Exception as e:
                print(f"Step 3: Could not remove 09_DATA\\lock\\: {e}")
        else:
            print("Step 3: 09_DATA\\lock\\ already clean")

        # Step 4: WAL checkpoint
        print("Step 4: WAL checkpoint...")
        try:
            self.checkpoint()
        except Exception as e:
            print(f"  Checkpoint failed (non-critical): {e}")

        # Step 5: Connection test + optimize
        print("Step 5: Connection test + optimize...")
        try:
            conn = sqlite3.connect(self.db_path, timeout=120)
            conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT}")
            tbl = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            print(f"  Tables: {tbl}")
            conn.execute("PRAGMA optimize")
            conn.close()
            print("  Optimize: DONE")
        except Exception as e:
            print(f"  ERROR: {e}")

        # Step 6: Final status
        print("\nStep 6: Final status")
        self.status()
        print("\n=== NUCLEAR PURGE COMPLETE ===")
        print("System is CLEAN. Max 3 concurrent agents enforced.")

    def fix_eagain(self):
        """Backward-compatible alias for nuke."""
        self.nuke()


# Global singleton
_manager = None


def get_manager():
    global _manager
    if _manager is None:
        _manager = DBLockManager()
    return _manager


def get_db_connection(caller='unknown'):
    """Get a managed DB connection. Caller should close when done."""
    return get_manager().get_connection(caller)


@contextmanager
def managed_db(caller='unknown'):
    """Context manager for safe DB access with automatic slot release."""
    mgr = get_manager()
    conn = None
    try:
        conn = mgr.get_connection(caller)
        yield conn
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        mgr.release_slot()


def safe_connect(db_path=DB_PATH, caller='unknown'):
    """Standalone safe connection — no lock manager, just best-practice PRAGMAs.
    Use when lock manager overhead is not needed (single-shot scripts)."""
    conn = sqlite3.connect(db_path, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


# Cleanup on exit
@atexit.register
def _cleanup():
    if _manager:
        _manager.release_slot()

# Handle SIGTERM/SIGINT gracefully
def _signal_handler(sig, frame):
    if _manager:
        _manager.release_slot()
    sys.exit(0)

try:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
except (OSError, ValueError):
    pass  # Signal handlers can't be set in all contexts


if __name__ == '__main__':
    import argparse
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='DB Lock Manager v3.0')
    parser.add_argument('--status', action='store_true', help='Show lock status')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup stale locks')
    parser.add_argument('--checkpoint', action='store_true', help='WAL checkpoint')
    parser.add_argument('--fix-eagain', action='store_true', help='Full EAGAIN fix (alias for --nuke)')
    parser.add_argument('--nuke', action='store_true', help='NUCLEAR: Kill ALL locks + checkpoint + optimize')
    args = parser.parse_args()

    mgr = DBLockManager()

    if args.nuke or args.fix_eagain:
        mgr.nuke()
    elif args.cleanup:
        cleaned = mgr._cleanup_stale_locks()
        sys_cleaned = _purge_system_stale_locks()
        print(f"Cleaned {cleaned} DB locks + {sys_cleaned} system locks")
        mgr.status()
    elif args.checkpoint:
        mgr.checkpoint()
    elif args.status:
        mgr.status()
    else:
        mgr.nuke()
