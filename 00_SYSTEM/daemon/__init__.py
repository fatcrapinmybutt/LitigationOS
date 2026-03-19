"""
LitigationOS Daemon — 24/7 Windows Service
============================================
Core daemon for autonomous litigation intelligence.

Architecture: Hybrid Core + Satellites
- Core (in-process, <100ms): File Watchdog, Scheduler, Task Queue, Skill Registry
- Satellites (isolated processes): Legal AI, MANBEARPIG v10, Smart Search

Modules:
- core.py           — Main daemon asyncio loop
- models.py         — 20+ Pydantic models
- task_queue.py     — SQLite WAL task queue with priority + dead letter
- config.py         — YAML config manager with hot-reload
- logging_config.py — Structured JSON logging + SQLite handler
- storage.py        — Drive strategy resolver (I:=heavy, flash=lite)
- satellite.py      — Satellite process launcher/monitor/recovery + IPC
- skill_registry.py — Skill scanner/parser/versioner/tracker + dependency resolver
- ipc.py            — Named pipe JSON-RPC 2.0 IPC (server + client)
- cli.py            — Typer CLI (start/stop/status/config/skills/tasks)
- watchdog_engine.py — File watchdog with MEEK lane detection
- auto_ingest.py    — Watchdog → task queue bridge for automatic processing
- scheduler.py      — Scheduled job framework
- resource_monitor.py — CPU/RAM/disk monitoring + satellite caps
- service_wrapper.py — Windows service via NSSM or pywin32
- tray_icon.py      — System tray icon with status + controls
- shell_integration.py — Right-click context menu + toast notifications
- file_migrator.py  — Safe heavy-file migration with verification

Storage Strategy:
- I: = heavy storage (DBs, archives, dedup, indexes, brains)
- D:/F:/G:/H: = flash drives (lite: refs, templates, quick-access)

Author: LitigationOS / Andrew J. Pigors
"""

__version__ = "1.0.0"
__app_name__ = "litigationos-daemon"
