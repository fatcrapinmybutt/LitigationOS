"""
Windows Service Wrapper for LitigationOS Daemon.
Supports two install methods:
  1. NSSM (recommended): nssm install LitigationOSDaemon <python> -m 00_SYSTEM.daemon.core
  2. win32serviceutil (requires pywin32): python service_wrapper.py install

Falls back gracefully when pywin32 is not available.
"""
import logging
import os
import subprocess
import sys
from typing import Optional

SERVICE_NAME = "LitigationOSDaemon"
SERVICE_DISPLAY = "LitigationOS Daemon"
SERVICE_DESC = "24/7 litigation intelligence engine — file monitoring, brain evolution, deadline tracking"
NSSM_URL = "https://nssm.cc/download"

logger = logging.getLogger("daemon.service")


class NSSMInstaller:
    """Install/manage Windows service via NSSM (Non-Sucking Service Manager)."""

    def __init__(self, nssm_path: str = "nssm"):
        self.nssm = nssm_path

    def _run(self, *args) -> tuple[int, str, str]:
        """Run NSSM command. Returns (returncode, stdout, stderr)."""
        cmd = [self.nssm] + list(args)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except FileNotFoundError:
            return -1, "", f"NSSM not found at '{self.nssm}'. Download from {NSSM_URL}"
        except subprocess.TimeoutExpired:
            return -2, "", "NSSM command timed out"
        except Exception as e:
            return -3, "", str(e)

    def is_available(self) -> bool:
        code, _, _ = self._run("version")
        return code == 0

    def install(self, python_exe: str = None, config_path: str = None) -> tuple[bool, str]:
        """Install as Windows service via NSSM."""
        exe = python_exe or sys.executable
        script = os.path.join(os.path.dirname(__file__), "core.py")

        args = [script]
        if config_path:
            args.extend(["--config", config_path])

        code, out, err = self._run("install", SERVICE_NAME, exe, *args)
        if code != 0:
            return False, err or f"NSSM install failed (code {code})"

        # Set display name and description
        self._run("set", SERVICE_NAME, "DisplayName", SERVICE_DISPLAY)
        self._run("set", SERVICE_NAME, "Description", SERVICE_DESC)
        self._run("set", SERVICE_NAME, "Start", "SERVICE_DELAYED_AUTO_START")
        self._run("set", SERVICE_NAME, "AppStdout",
                  os.path.join(os.path.dirname(__file__), "logs", "service_stdout.log"))
        self._run("set", SERVICE_NAME, "AppStderr",
                  os.path.join(os.path.dirname(__file__), "logs", "service_stderr.log"))
        self._run("set", SERVICE_NAME, "AppRotateFiles", "1")
        self._run("set", SERVICE_NAME, "AppRotateBytes", "10485760")

        return True, f"Service '{SERVICE_NAME}' installed successfully"

    def uninstall(self) -> tuple[bool, str]:
        code, out, err = self._run("remove", SERVICE_NAME, "confirm")
        if code != 0:
            return False, err or f"NSSM remove failed (code {code})"
        return True, f"Service '{SERVICE_NAME}' removed"

    def start(self) -> tuple[bool, str]:
        code, out, err = self._run("start", SERVICE_NAME)
        return code == 0, out or err

    def stop(self) -> tuple[bool, str]:
        code, out, err = self._run("stop", SERVICE_NAME)
        return code == 0, out or err

    def status(self) -> str:
        code, out, err = self._run("status", SERVICE_NAME)
        if code != 0:
            return "not_installed"
        return out.lower().strip()

    def restart(self) -> tuple[bool, str]:
        code, out, err = self._run("restart", SERVICE_NAME)
        return code == 0, out or err


class Win32ServiceWrapper:
    """Fallback: direct win32serviceutil integration (requires pywin32)."""

    @staticmethod
    def is_available() -> bool:
        try:
            import win32serviceutil  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def install(config_path: str = None):
        """Install as Windows service using pywin32."""
        try:
            import win32serviceutil
            import win32service
            import servicemanager

            class LitigationOSService:
                _svc_name_ = SERVICE_NAME
                _svc_display_name_ = SERVICE_DISPLAY
                _svc_description_ = SERVICE_DESC

            # Use HandleCommandLine for install
            win32serviceutil.HandleCommandLine(LitigationOSService)
        except ImportError:
            return False, "pywin32 not installed. Use: pip install pywin32"
        except Exception as e:
            return False, str(e)
        return True, "Service installed via pywin32"


class ServiceManager:
    """Unified service management — tries NSSM first, falls back to pywin32."""

    def __init__(self, nssm_path: str = "nssm"):
        self._nssm = NSSMInstaller(nssm_path)
        self._win32 = Win32ServiceWrapper()

    def install(self, config_path: str = None) -> tuple[bool, str]:
        if self._nssm.is_available():
            return self._nssm.install(config_path=config_path)
        if self._win32.is_available():
            return self._win32.install(config_path=config_path)
        return False, (
            f"No service manager found.\n"
            f"Option 1: Download NSSM from {NSSM_URL}\n"
            f"Option 2: pip install pywin32"
        )

    def uninstall(self) -> tuple[bool, str]:
        if self._nssm.is_available():
            return self._nssm.uninstall()
        return False, "NSSM required for uninstall"

    def start(self) -> tuple[bool, str]:
        if self._nssm.is_available():
            return self._nssm.start()
        return False, "NSSM required for service start"

    def stop(self) -> tuple[bool, str]:
        if self._nssm.is_available():
            return self._nssm.stop()
        return False, "NSSM required for service stop"

    def status(self) -> str:
        if self._nssm.is_available():
            return self._nssm.status()
        return "unknown"

    def restart(self) -> tuple[bool, str]:
        if self._nssm.is_available():
            return self._nssm.restart()
        return False, "NSSM required for restart"
