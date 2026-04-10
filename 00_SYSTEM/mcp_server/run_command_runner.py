#!/usr/bin/env python3
"""Launcher for the command_runner MCP server.

Ensures the script directory is on sys.path before importing,
validates the environment, then starts the JSON-RPC stdio server.
"""
import sys
import os
import logging
from pathlib import Path

# Configure logging
log_dir = Path(r"C:\Users\andre\LitigationOS\logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(log_dir / "mcp_command_runner.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("command_runner_mcp")

# Add this directory to sys.path
server_dir = str(Path(__file__).resolve().parent)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

def validate_environment():
    """Pre-flight checks before starting the server."""
    runner_path = Path(server_dir) / "command_runner.py"
    if not runner_path.exists():
        logger.error(f"command_runner.py not found: {runner_path}")
        raise FileNotFoundError(f"command_runner.py not found: {runner_path}")
    
    logger.info(f"Python: {sys.version}")
    logger.info(f"Server dir: {server_dir}")
    logger.info(f"CWD: {os.getcwd()}")

if __name__ == "__main__":
    try:
        validate_environment()
        logger.info("Starting command_runner MCP server...")
        from command_runner import main
        main()
    except Exception as e:
        logger.exception(f"Server failed to start: {e}")
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
