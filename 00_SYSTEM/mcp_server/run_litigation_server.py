#!/usr/bin/env python3
"""Launcher for the litigation_context MCP server.

Ensures the package directory is on sys.path before importing,
validates the environment, then starts the FastMCP stdio server.
"""
import sys
import os
import logging
from pathlib import Path

# Configure logging
log_dir = Path(r"C:\Users\andre\LitigationOS\logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(log_dir / "mcp_litigation_server.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("litigation_mcp")

# Add this directory to sys.path so litigation_context_mcp is importable
server_dir = str(Path(__file__).resolve().parent)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

def validate_environment():
    """Pre-flight checks before starting the server."""
    db_path = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    pkg_dir = Path(server_dir) / "litigation_context_mcp"
    if not (pkg_dir / "server.py").exists():
        logger.error(f"Server module not found: {pkg_dir / 'server.py'}")
        raise FileNotFoundError(f"Server module not found: {pkg_dir / 'server.py'}")
    
    try:
        import mcp
        logger.info(f"MCP SDK version: {getattr(mcp, '__version__', 'unknown')}")
    except ImportError:
        logger.error("mcp package not installed. Run: pip install 'mcp[cli]'")
        raise
    
    logger.info(f"Database: {db_path} ({db_path.stat().st_size / 1024 / 1024:.0f} MB)")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Server dir: {server_dir}")

if __name__ == "__main__":
    try:
        validate_environment()
        logger.info("Starting litigation_context MCP server...")
        from litigation_context_mcp.server import main
        main()
    except Exception as e:
        logger.exception(f"Server failed to start: {e}")
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
