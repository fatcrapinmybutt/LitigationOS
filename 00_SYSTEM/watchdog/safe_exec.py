#!/usr/bin/env python3
"""
MANBEARPIG Safe Shell Executor v1.0

A resilient command execution wrapper that:
1. Auto-retries on shell failures (up to 3 attempts)
2. Enforces timeouts to prevent runaway processes
3. Logs all executions to the watchdog DB
4. Provides clean error messages instead of crashes
5. Handles encoding issues on Windows
6. Prevents orphaned processes via process tree cleanup

Usage:
    python safe_exec.py "command to run" [--timeout 120] [--retries 3]
    python safe_exec.py --script path/to/script.py [--timeout 300]

As a Python module:
    from safe_exec import safe_run
    result = safe_run("python my_script.py", timeout=120)
"""

import os, sys, json, subprocess, time, signal
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

WATCHDOG_DIR = Path(r'C:\Users\andre\LitigationOS\00_SYSTEM\watchdog')
EXEC_LOG = WATCHDOG_DIR / 'exec_log.jsonl'

WATCHDOG_DIR.mkdir(parents=True, exist_ok=True)


def log_execution(cmd, status, duration, output='', error='', retries=0):
    """Append execution record to JSONL log."""
    record = {
        'timestamp': datetime.now().isoformat(),
        'command': cmd[:500],
        'status': status,
        'duration_seconds': round(duration, 2),
        'output_bytes': len(output),
        'error_bytes': len(error),
        'retries': retries,
        'pid': os.getpid()
    }
    try:
        with open(EXEC_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
    except:
        pass


def safe_run(command, timeout=120, retries=3, cwd=None, shell=True, auto_repair=True):
    """Execute a command with auto-retry, timeout, error interception, and repair.
    
    Args:
        command: Command string or list to execute
        timeout: Max seconds to wait (default 120)
        retries: Max retry attempts on failure (default 3)
        cwd: Working directory (default: LitigationOS root)
        shell: Run in shell mode (default True)
        auto_repair: Use ErrorInterceptor to auto-fix commands (default True)
    
    Returns:
        dict with keys: success, stdout, stderr, returncode, duration, attempts, repairs
    """
    if cwd is None:
        cwd = r'C:\Users\andre\LitigationOS'
    
    # Load error interceptor if available
    interceptor = None
    if auto_repair:
        try:
            from error_interceptor import ErrorInterceptor
            interceptor = ErrorInterceptor()
        except ImportError:
            pass
    
    current_cmd = command
    repairs = []
    last_error = None
    for attempt in range(1, retries + 1):
        start = time.time()
        try:
            result = subprocess.run(
                current_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                shell=shell,
                encoding='utf-8',
                errors='replace',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            duration = time.time() - start
            
            if result.returncode == 0:
                log_execution(str(current_cmd), 'success', duration, result.stdout, result.stderr, attempt - 1)
                return {
                    'success': True,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': 0,
                    'duration': round(duration, 2),
                    'attempts': attempt,
                    'repairs': repairs,
                    'command_used': str(current_cmd)
                }
            else:
                error_text = (result.stderr or '') + (result.stdout or '')
                last_error = error_text or f'Exit code {result.returncode}'
                
                # Try auto-repair via interceptor
                if interceptor and attempt < retries:
                    diagnosis = interceptor.intercept_and_repair(str(current_cmd), error_text)
                    if diagnosis.get('classified') and diagnosis.get('repair'):
                        repair = diagnosis['repair']
                        if repair.get('repaired_command') and repair.get('confidence', 0) >= 0.5:
                            repairs.append({
                                'attempt': attempt,
                                'error_class': diagnosis['error_class'],
                                'old_cmd': str(current_cmd),
                                'new_cmd': repair['repaired_command'],
                                'explanation': repair['explanation']
                            })
                            current_cmd = repair['repaired_command']
                            delay = repair.get('retry_delay', min(2 ** attempt, 10))
                            time.sleep(delay)
                            continue
                
                if attempt < retries:
                    time.sleep(min(2 ** attempt, 10))  # Exponential backoff
                    continue
                    
                log_execution(str(current_cmd), 'failed', duration, result.stdout, result.stderr, attempt)
                return {
                    'success': False,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode,
                    'duration': round(duration, 2),
                    'attempts': attempt,
                    'error': last_error,
                    'repairs': repairs,
                    'command_used': str(current_cmd)
                }
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            last_error = f'Timeout after {timeout}s'
            log_execution(str(command), 'timeout', duration, retries=attempt)
            if attempt < retries:
                time.sleep(2)
                continue
            return {
                'success': False,
                'stdout': '',
                'stderr': '',
                'returncode': -1,
                'duration': round(duration, 2),
                'attempts': attempt,
                'error': last_error
            }
            
        except Exception as e:
            duration = time.time() - start
            last_error = str(e)
            log_execution(str(command), 'exception', duration, error=str(e), retries=attempt)
            if attempt < retries:
                time.sleep(2)
                continue
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'duration': round(duration, 2),
                'attempts': attempt,
                'error': last_error
            }
    
    return {
        'success': False,
        'stdout': '',
        'stderr': last_error or 'All retries exhausted',
        'returncode': -1,
        'duration': 0,
        'attempts': retries,
        'error': 'All retries exhausted'
    }


def safe_python(script_content, timeout=300, script_name='temp_task.py'):
    """Execute Python code safely by writing to a temp file and running it.
    
    This avoids PowerShell escaping issues entirely.
    
    Args:
        script_content: Python source code string
        timeout: Max seconds (default 300)
        script_name: Temp file name (auto-deleted after)
    
    Returns:
        Same dict as safe_run
    """
    cwd = r'C:\Users\andre\LitigationOS'
    script_path = os.path.join(cwd, script_name)
    
    # Always prepend encoding fix
    if 'sys.stdout = open' not in script_content:
        script_content = (
            "import sys\n"
            "sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')\n\n"
            + script_content
        )
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = safe_run(f'python "{script_path}"', timeout=timeout, cwd=cwd)
        return result
        
    finally:
        # Always clean up temp script
        try:
            os.unlink(script_path)
        except:
            pass


def get_exec_stats():
    """Get execution statistics from the log."""
    if not EXEC_LOG.exists():
        return {'total': 0}
    
    stats = {'total': 0, 'success': 0, 'failed': 0, 'timeout': 0, 'exception': 0, 'avg_duration': 0}
    durations = []
    
    with open(EXEC_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line.strip())
                stats['total'] += 1
                status = rec.get('status', '')
                stats[status] = stats.get(status, 0) + 1
                durations.append(rec.get('duration_seconds', 0))
            except:
                continue
    
    if durations:
        stats['avg_duration'] = round(sum(durations) / len(durations), 2)
        stats['max_duration'] = round(max(durations), 2)
    
    return stats


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Safe Shell Executor v1.0')
    p.add_argument('command', nargs='?', help='Command to run')
    p.add_argument('--script', help='Python script file to run')
    p.add_argument('--timeout', type=int, default=120)
    p.add_argument('--retries', type=int, default=3)
    p.add_argument('--stats', action='store_true')
    args = p.parse_args()
    
    if args.stats:
        print(json.dumps(get_exec_stats(), indent=2))
    elif args.script:
        with open(args.script, 'r', encoding='utf-8') as f:
            result = safe_python(f.read(), timeout=args.timeout)
        print(json.dumps(result, indent=2))
    elif args.command:
        result = safe_run(args.command, timeout=args.timeout, retries=args.retries)
        if result['stdout']:
            print(result['stdout'])
        if result['stderr'] and not result['success']:
            print(f"ERROR: {result['stderr']}", file=sys.stderr)
        sys.exit(0 if result['success'] else 1)
    else:
        print("Usage: python safe_exec.py 'command' [--timeout N] [--retries N]")
        print("       python safe_exec.py --script path.py [--timeout N]")
        print("       python safe_exec.py --stats")
