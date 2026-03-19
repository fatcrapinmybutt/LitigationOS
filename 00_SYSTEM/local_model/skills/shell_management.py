#!/usr/bin/env python3
"""
MANBEARPIG Shell Management Skill v1.0

Integrates shell_watchdog into the MANBEARPIG inference engine as a skill.
Provides JSON-RPC methods for shell/agent/health monitoring.

Methods:
- watchdog_check: Run single health check
- watchdog_status: Full watchdog status
- watchdog_register_shell: Register a new shell session
- watchdog_register_agent: Register a new agent task
- watchdog_complete_agent: Mark agent completed
- watchdog_shells: List active shells
- watchdog_agents: List running agents
- watchdog_events: Recent process events
- watchdog_guard_start: Start background monitoring
"""

import os, sys, json, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from sibling directory
WATCHDOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'watchdog')
sys.path.insert(0, WATCHDOG_DIR)

try:
    from shell_watchdog import ShellWatchdog, WatchdogDB, ProcessMonitor, WATCHDOG_DB
except ImportError:
    # Fallback: construct path manually
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "shell_watchdog",
        os.path.join(WATCHDOG_DIR, "shell_watchdog.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ShellWatchdog = mod.ShellWatchdog
    WatchdogDB = mod.WatchdogDB
    ProcessMonitor = mod.ProcessMonitor
    WATCHDOG_DB = mod.WATCHDOG_DB


# Singleton watchdog instance
_watchdog = None
_guard_thread = None

def _get_watchdog():
    global _watchdog
    if _watchdog is None:
        _watchdog = ShellWatchdog()
    return _watchdog


def watchdog_check(params=None):
    """Run a single health check and return results."""
    wd = _get_watchdog()
    return wd.run_check()


def watchdog_status(params=None):
    """Get full watchdog status with stats and active sessions."""
    wd = _get_watchdog()
    result = wd.run_check()
    stats = wd.db.get_stats()
    return {
        'check_result': result,
        'stats': stats,
        'active_shells': wd.db.get_active_shells(),
        'active_agents': wd.db.get_active_agents(),
        'recent_health': wd.db.get_recent_health(5)
    }


def watchdog_register_shell(params):
    """Register a new shell session for monitoring.
    
    Args:
        shell_id: Shell session identifier
        pid: Process ID (optional)
        command: Command being run (optional)
    """
    wd = _get_watchdog()
    wd.db.register_shell(
        params.get('shell_id', 'unknown'),
        params.get('pid'),
        params.get('command', '')
    )
    return {'registered': True, 'shell_id': params.get('shell_id')}


def watchdog_register_agent(params):
    """Register a new background agent for monitoring.
    
    Args:
        agent_id: Agent identifier
        agent_type: Type (general-purpose, explore, task, etc.)
        description: Task description
    """
    wd = _get_watchdog()
    wd.db.register_agent(
        params.get('agent_id', 'unknown'),
        params.get('agent_type', 'unknown'),
        params.get('description', '')
    )
    return {'registered': True, 'agent_id': params.get('agent_id')}


def watchdog_complete_agent(params):
    """Mark a background agent as completed.
    
    Args:
        agent_id: Agent identifier
        status: completed/failed/timeout
        result: Result summary (optional)
        error: Error message (optional)
    """
    wd = _get_watchdog()
    wd.db.complete_agent(
        params.get('agent_id'),
        params.get('status', 'completed'),
        params.get('result'),
        params.get('error')
    )
    return {'completed': True, 'agent_id': params.get('agent_id')}


def watchdog_shells(params=None):
    """List all active shell sessions."""
    wd = _get_watchdog()
    return {'shells': wd.db.get_active_shells()}


def watchdog_agents(params=None):
    """List all running agents."""
    wd = _get_watchdog()
    return {'agents': wd.db.get_active_agents()}


def watchdog_events(params=None):
    """Get recent process events.
    
    Args:
        limit: Number of events to return (default 20)
    """
    wd = _get_watchdog()
    limit = (params or {}).get('limit', 20)
    conn = wd.db._conn()
    rows = conn.execute(
        "SELECT * FROM process_events ORDER BY event_time DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {'events': [dict(r) for r in rows]}


def watchdog_guard_start(params=None):
    """Start background monitoring thread.
    
    Args:
        interval: Check interval in seconds (default 30)
    """
    global _guard_thread
    wd = _get_watchdog()
    
    if _guard_thread and _guard_thread.is_alive():
        return {'status': 'already_running', 'pid': os.getpid()}
    
    interval = (params or {}).get('interval', 30)
    
    def _run():
        wd.guard_loop(interval)
    
    _guard_thread = threading.Thread(target=_run, daemon=True, name='watchdog_guard')
    _guard_thread.start()
    
    return {'status': 'started', 'interval': interval, 'pid': os.getpid()}


# ── Skill Registry ──────────────────────────────────────────────────────────

SKILL_NAME = "shell_management"
SKILL_VERSION = "2.0.0"
SKILL_DESCRIPTION = "Shell watchdog, error interceptor, and process management for LitigationOS"

# Import error interceptor
try:
    from error_interceptor import ErrorInterceptor, safe_execute
    _interceptor = ErrorInterceptor()
except ImportError:
    _interceptor = None
    safe_execute = None


def error_diagnose(params=None):
    """Diagnose an error string — classify and suggest repair.
    
    Args:
        error_text: The error output to diagnose
    """
    if not _interceptor:
        return {'error': 'ErrorInterceptor not available'}
    text = (params or {}).get('error_text', '')
    if not text:
        return {'error': 'error_text required'}
    result = _interceptor.intercept_and_repair('unknown', text)
    return result


def error_execute(params=None):
    """Execute a command with automatic error interception and repair.
    
    Args:
        command: Shell command to execute
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default 120)
    """
    if not safe_execute:
        return {'error': 'safe_execute not available'}
    cmd = (params or {}).get('command', '')
    cwd = (params or {}).get('cwd')
    timeout = (params or {}).get('timeout', 120)
    if not cmd:
        return {'error': 'command required'}
    return safe_execute(cmd, cwd=cwd, timeout=timeout)


def error_stats(params=None):
    """Get error interception statistics."""
    if not _interceptor:
        return {'error': 'ErrorInterceptor not available'}
    return _interceptor.get_stats()


def error_rules(params=None):
    """Get active error prevention rules."""
    if not _interceptor:
        return {'error': 'ErrorInterceptor not available'}
    return {'rules': _interceptor.get_prevention_rules()}


METHODS = {
    'watchdog_check': watchdog_check,
    'watchdog_status': watchdog_status,
    'watchdog_register_shell': watchdog_register_shell,
    'watchdog_register_agent': watchdog_register_agent,
    'watchdog_complete_agent': watchdog_complete_agent,
    'watchdog_shells': watchdog_shells,
    'watchdog_agents': watchdog_agents,
    'watchdog_events': watchdog_events,
    'watchdog_guard_start': watchdog_guard_start,
    'error_diagnose': error_diagnose,
    'error_execute': error_execute,
    'error_stats': error_stats,
    'error_rules': error_rules,
}

def handle(method, params=None):
    """Handle a JSON-RPC call to this skill."""
    fn = METHODS.get(method)
    if fn:
        return fn(params)
    return {'error': f'Unknown method: {method}'}
