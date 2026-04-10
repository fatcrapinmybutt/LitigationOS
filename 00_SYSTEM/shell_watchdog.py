"""
Shell Session Watchdog Daemon — LitigationOS
=============================================
Detached background daemon that:
  1. Monitors active Python/PowerShell child processes
  2. Kills orphaned processes older than MAX_AGE
  3. Protects whitelisted long-running jobs (Phase C, etc.)
  4. Logs all actions to watchdog log
  5. Provides live progress display for active consolidation

Run detached:  python shell_watchdog.py --daemon
Run once:      python shell_watchdog.py --check
Live progress: python shell_watchdog.py --progress
"""
import os, sys, time, sqlite3, signal, argparse, json
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────
MAX_PROCESS_AGE_MINUTES = 30       # Kill processes older than this
CHECK_INTERVAL_SECONDS  = 60       # How often daemon checks
WHITELIST_KEYWORDS      = [        # Never kill processes matching these
    "run_phase_c", "run_phase_d", "run_phase_e",
    "shell_watchdog", "copilot", "mcp_server",
    "code", "node", "typst", "go", "rust",
]
STATE_DB   = Path(r"D:\LitigationOS_tmp\consolidation_state.db")
LOG_FILE   = Path(r"D:\LitigationOS_tmp\shell_watchdog.log")
PID_FILE   = Path(r"D:\LitigationOS_tmp\shell_watchdog.pid")

# ── Logging ──────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ── Process Management ───────────────────────────────────────────────
def get_python_processes() -> list[dict]:
    """Get all running Python processes with their command lines."""
    import subprocess
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name LIKE '%python%'\" | "
             "Select-Object ProcessId, CreationDate, CommandLine | "
             "ConvertTo-Json -Depth 2"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        procs = []
        for p in data:
            pid = p.get("ProcessId", 0)
            cmdline = p.get("CommandLine", "") or ""
            creation = p.get("CreationDate", "")
            # Parse WMI datetime: /Date(1234567890000)/
            start_time = None
            if creation and "/Date(" in str(creation):
                try:
                    ms = int(str(creation).split("(")[1].split(")")[0])
                    start_time = datetime.fromtimestamp(ms / 1000)
                except Exception:
                    pass
            procs.append({
                "pid": pid,
                "cmdline": cmdline,
                "start_time": start_time,
                "age_minutes": (datetime.now() - start_time).total_seconds() / 60 if start_time else 0,
            })
        return procs
    except Exception as e:
        log(f"Error getting processes: {e}", "ERROR")
        return []


def is_whitelisted(cmdline: str) -> bool:
    """Check if process matches whitelist."""
    cl = cmdline.lower()
    return any(kw.lower() in cl for kw in WHITELIST_KEYWORDS)


def kill_stale_processes(dry_run: bool = False) -> int:
    """Find and kill stale Python processes. Returns count killed."""
    procs = get_python_processes()
    my_pid = os.getpid()
    killed = 0

    for p in procs:
        pid = p["pid"]
        if pid == my_pid:
            continue
        if p["age_minutes"] < MAX_PROCESS_AGE_MINUTES:
            continue
        if is_whitelisted(p["cmdline"]):
            log(f"  PROTECTED PID {pid} (age {p['age_minutes']:.0f}m): {p['cmdline'][:80]}")
            continue

        age_str = f"{p['age_minutes']:.0f}m"
        cmd_short = p["cmdline"][:100] if p["cmdline"] else "(unknown)"

        if dry_run:
            log(f"  WOULD KILL PID {pid} (age {age_str}): {cmd_short}")
        else:
            try:
                os.kill(pid, signal.SIGTERM)
                log(f"  KILLED PID {pid} (age {age_str}): {cmd_short}")
                killed += 1
            except (ProcessLookupError, PermissionError) as e:
                log(f"  FAILED to kill PID {pid}: {e}", "WARN")

    return killed


# ── Progress Display ─────────────────────────────────────────────────
def get_consolidation_progress() -> dict:
    """Query state DB for current consolidation progress."""
    if not STATE_DB.exists():
        return {"error": "State DB not found"}

    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=60000")

    result = {}

    # Status breakdown
    rows = conn.execute(
        "SELECT copy_status, COUNT(*), COALESCE(SUM(file_size),0) "
        "FROM file_inventory GROUP BY copy_status"
    ).fetchall()
    result["statuses"] = {r[0]: {"count": r[1], "bytes": r[2]} for r in rows}

    # Per-drive for COPIED and CANONICAL
    for status in ("COPIED", "CANONICAL"):
        drives = conn.execute(
            "SELECT source_drive, COUNT(*), COALESCE(SUM(file_size),0) "
            "FROM file_inventory WHERE copy_status=? GROUP BY source_drive",
            (status,)
        ).fetchall()
        result[f"{status.lower()}_by_drive"] = {
            r[0]: {"count": r[1], "bytes": r[2]} for r in drives
        }

    # Error details
    errors = conn.execute(
        "SELECT source_drive, copy_status, COUNT(*) FROM file_inventory "
        "WHERE copy_status IN ('COPY_ERROR','SOURCE_MISSING') "
        "GROUP BY source_drive, copy_status"
    ).fetchall()
    result["errors"] = [{"drive": r[0], "status": r[1], "count": r[2]} for r in errors]

    # Timing
    first_copy = conn.execute(
        "SELECT MIN(copied_at) FROM file_inventory WHERE copied_at IS NOT NULL"
    ).fetchone()[0]
    last_copy = conn.execute(
        "SELECT MAX(copied_at) FROM file_inventory WHERE copied_at IS NOT NULL"
    ).fetchone()[0]
    result["first_copy"] = first_copy
    result["last_copy"] = last_copy

    conn.close()
    return result


def render_progress_bar(pct: float, width: int = 50) -> str:
    """Render an ASCII progress bar."""
    filled = int(width * pct / 100)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    return f"[{bar}] {pct:.1f}%"


def format_bytes(b: float) -> str:
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.2f} {unit}"
        b /= 1024
    return f"{b:.2f} PB"


def format_duration(seconds: float) -> str:
    """Human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}m {seconds%60:.0f}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def display_live_progress():
    """Continuous live progress display with refresh."""
    print("\033[2J\033[H", end="")  # Clear screen
    
    while True:
        data = get_consolidation_progress()
        if "error" in data:
            print(f"Error: {data['error']}")
            return

        statuses = data["statuses"]
        copied_count = statuses.get("COPIED", {}).get("count", 0)
        copied_bytes = statuses.get("COPIED", {}).get("bytes", 0)
        verified_count = statuses.get("VERIFIED", {}).get("count", 0)
        verified_bytes = statuses.get("VERIFIED", {}).get("bytes", 0)
        canonical_count = statuses.get("CANONICAL", {}).get("count", 0)
        canonical_bytes = statuses.get("CANONICAL", {}).get("bytes", 0)
        dup_count = statuses.get("DUPLICATE_SKIP", {}).get("count", 0)
        empty_count = statuses.get("EMPTY_SKIP", {}).get("count", 0)
        error_count = sum(
            statuses.get(s, {}).get("count", 0)
            for s in ("COPY_ERROR", "SOURCE_MISSING")
        )

        done = copied_count + verified_count
        target = done + canonical_count
        done_bytes = copied_bytes + verified_bytes
        target_bytes = done_bytes + canonical_bytes
        pct = (done / target * 100) if target > 0 else 0
        pct_bytes = (done_bytes / target_bytes * 100) if target_bytes > 0 else 0

        # Calculate speed from timing
        speed_str = "calculating..."
        eta_str = "calculating..."
        if data.get("first_copy") and data.get("last_copy") and done > 10:
            try:
                t0 = datetime.fromisoformat(data["first_copy"])
                t1 = datetime.fromisoformat(data["last_copy"])
                elapsed = (t1 - t0).total_seconds()
                if elapsed > 0:
                    speed = done_bytes / elapsed
                    speed_str = f"{format_bytes(speed)}/s"
                    remaining_bytes = canonical_bytes
                    if speed > 0:
                        eta_sec = remaining_bytes / speed
                        eta_str = format_duration(eta_sec)
            except Exception:
                pass

        # Current drive
        canonical_by_drive = data.get("canonical_by_drive", {})
        copied_by_drive = data.get("copied_by_drive", {})
        
        current_drive = "DONE"
        for drv in ["D:", "F:", "G:", "I:"]:
            if drv in canonical_by_drive and canonical_by_drive[drv]["count"] > 0:
                current_drive = drv
                break

        now = datetime.now().strftime("%H:%M:%S")

        # ── RENDER ──
        print("\033[H", end="")  # Move cursor home
        print("\033[2J", end="")  # Clear
        
        print("=" * 62)
        print(f"  \U0001F680 LITIGATIONOS CONSOLIDATION — LIVE MONITOR  [{now}]")
        print("=" * 62)
        print()

        # Main progress bar
        bar_w = 50
        filled = int(bar_w * pct / 100)
        bar = "\u2588" * filled + "\u2591" * (bar_w - filled)
        print(f"  FILES:  [{bar}] {pct:.1f}%")
        print(f"          {done:,} / {target:,} files")
        print()

        filled_b = int(bar_w * pct_bytes / 100)
        bar_b = "\u2588" * filled_b + "\u2591" * (bar_w - filled_b)
        print(f"  BYTES:  [{bar_b}] {pct_bytes:.1f}%")
        print(f"          {format_bytes(done_bytes)} / {format_bytes(target_bytes)}")
        print()

        print(f"  \u26A1 Speed: {speed_str}    \u23F1  ETA: {eta_str}")
        print(f"  \U0001F4C0 Current Drive: {current_drive}")
        print()

        # Drive breakdown
        print("  \u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u252C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
        print("  \u2502 Drive  \u2502   Copied    \u2502  Remaining  \u2502   Status   \u2502")
        print("  \u251C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2524")

        for drv in ["D:", "F:", "G:", "I:"]:
            cop = copied_by_drive.get(drv, {}).get("count", 0)
            rem = canonical_by_drive.get(drv, {}).get("count", 0)
            total_drv = cop + rem
            if total_drv == 0 and cop == 0:
                status = "\u2705 skip"
            elif rem == 0:
                status = "\u2705 done"
            elif cop > 0:
                status = "\U0001F525 active"
            else:
                status = "\u23F3 queued"
            print(f"  \u2502 {drv:<6s} \u2502 {cop:>9,}   \u2502 {rem:>9,}   \u2502 {status:<10s} \u2502")

        print("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
        print()

        # Status summary
        print(f"  \u2713 Copied:    {copied_count:>8,}    \u2713 Verified:  {verified_count:>8,}")
        print(f"  \u2717 Errors:    {error_count:>8,}    \u25CB Remaining: {canonical_count:>8,}")
        print(f"  ~ Dup Skip:  {dup_count:>8,}    ~ Empty:    {empty_count:>8,}")
        
        if error_count > 0:
            print(f"\n  \u26A0\uFE0F  Error Details:")
            for e in data.get("errors", []):
                print(f"     {e['drive']} [{e['status']}]: {e['count']}")

        # Process check
        procs = get_python_processes()
        phase_c_alive = any("run_phase_c" in (p["cmdline"] or "") for p in procs)
        print(f"\n  \U0001F9E0 Phase C Process: {'ALIVE \u2705' if phase_c_alive else 'NOT RUNNING \u274C'}")

        if not phase_c_alive and canonical_count == 0:
            print("\n  \U0001F389 PHASE C COMPLETE — Ready for Phase D!")
            break
        elif not phase_c_alive and canonical_count > 0:
            print(f"\n  \u26A0\uFE0F  Phase C process DEAD but {canonical_count:,} files remain!")
            print("     Restart with: python D:\\LitigationOS_tmp\\run_phase_c.py")
            break

        # Stale process check
        stale = [p for p in procs 
                 if p["age_minutes"] > MAX_PROCESS_AGE_MINUTES 
                 and not is_whitelisted(p.get("cmdline", ""))
                 and p["pid"] != os.getpid()]
        if stale:
            print(f"\n  \u26A0\uFE0F  {len(stale)} stale process(es) detected (>{MAX_PROCESS_AGE_MINUTES}m old)")
            for s in stale[:3]:
                print(f"     PID {s['pid']} ({s['age_minutes']:.0f}m): {(s['cmdline'] or '')[:60]}")

        print(f"\n  Refreshing in 10s... (Ctrl+C to exit)")
        
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n  Monitor stopped.")
            break


# ── Daemon Mode ──────────────────────────────────────────────────────
def run_daemon():
    """Background daemon: periodic process cleanup + progress logging."""
    log("Shell Watchdog Daemon STARTED")
    log(f"  Check interval: {CHECK_INTERVAL_SECONDS}s")
    log(f"  Max process age: {MAX_PROCESS_AGE_MINUTES}m")
    log(f"  Whitelist: {WHITELIST_KEYWORDS}")

    # Write PID file
    PID_FILE.write_text(str(os.getpid()))

    cycle = 0
    try:
        while True:
            cycle += 1
            log(f"--- Watchdog cycle {cycle} ---")

            # 1. Kill stale processes
            killed = kill_stale_processes(dry_run=False)
            if killed:
                log(f"  Killed {killed} stale process(es)")

            # 2. Log consolidation progress
            data = get_consolidation_progress()
            if "error" not in data:
                statuses = data.get("statuses", {})
                copied = statuses.get("COPIED", {}).get("count", 0)
                verified = statuses.get("VERIFIED", {}).get("count", 0)
                canonical = statuses.get("CANONICAL", {}).get("count", 0)
                done = copied + verified
                target = done + canonical
                pct = (done / target * 100) if target > 0 else 0
                log(f"  Consolidation: {done:,}/{target:,} ({pct:.1f}%)")

            # 3. Check if Phase C is still alive
            procs = get_python_processes()
            phase_c_alive = any("run_phase_c" in (p.get("cmdline", "") or "") for p in procs)
            if not phase_c_alive and canonical > 0:
                log(f"  WARNING: Phase C not running, {canonical:,} files remain!", "WARN")

            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log("Daemon stopped by user")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()
        log("Shell Watchdog Daemon STOPPED")


# ── One-Shot Check ───────────────────────────────────────────────────
def run_check():
    """One-time check: list processes, identify stale, show progress."""
    print("=" * 60)
    print("  SHELL WATCHDOG — ONE-TIME CHECK")
    print("=" * 60)

    procs = get_python_processes()
    print(f"\n  Python processes: {len(procs)}")
    for p in procs:
        wl = " [PROTECTED]" if is_whitelisted(p.get("cmdline", "")) else ""
        stale = " [STALE]" if p["age_minutes"] > MAX_PROCESS_AGE_MINUTES else ""
        cmd = (p.get("cmdline", "") or "")[:80]
        print(f"    PID {p['pid']:>6}  age {p['age_minutes']:>6.0f}m{wl}{stale}  {cmd}")

    stale = [p for p in procs
             if p["age_minutes"] > MAX_PROCESS_AGE_MINUTES
             and not is_whitelisted(p.get("cmdline", ""))
             and p["pid"] != os.getpid()]

    if stale:
        print(f"\n  {len(stale)} stale process(es) would be killed.")
        for s in stale:
            print(f"    PID {s['pid']} ({s['age_minutes']:.0f}m)")
    else:
        print(f"\n  No stale processes found. All clean.")

    # Quick consolidation status
    data = get_consolidation_progress()
    if "error" not in data:
        statuses = data.get("statuses", {})
        copied = statuses.get("COPIED", {}).get("count", 0)
        verified = statuses.get("VERIFIED", {}).get("count", 0)
        canonical = statuses.get("CANONICAL", {}).get("count", 0)
        done = copied + verified
        target = done + canonical
        pct = (done / target * 100) if target > 0 else 0
        print(f"\n  Consolidation: {done:,}/{target:,} ({pct:.1f}%)")


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shell Session Watchdog")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--daemon", action="store_true", help="Run as background daemon")
    group.add_argument("--check", action="store_true", help="One-time process check")
    group.add_argument("--progress", action="store_true", help="Live progress display")
    group.add_argument("--kill-stale", action="store_true", help="Kill stale processes now")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be killed")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.check:
        run_check()
    elif args.progress:
        display_live_progress()
    elif args.kill_stale:
        killed = kill_stale_processes(dry_run=args.dry_run)
        print(f"{'Would kill' if args.dry_run else 'Killed'} {killed} process(es)")
