"""HYDRA Governor — Session lifecycle management + MCP watchdog."""

try:
    from .governor_engine import (
        classify_output,
        check_mcp_health,
        restart_mcp_server,
        generate_report,
        sweep_protocol,
    )
except ImportError as e:
    classify_output = check_mcp_health = restart_mcp_server = None
    generate_report = sweep_protocol = None
    _import_error = str(e)

try:
    from .mcp_launcher import ServerProcess, launch_all, check_status
except ImportError as e:
    ServerProcess = launch_all = check_status = None

__all__ = [
    "classify_output",
    "check_mcp_health",
    "restart_mcp_server",
    "generate_report",
    "sweep_protocol",
    "ServerProcess",
    "launch_all",
    "check_status",
]
