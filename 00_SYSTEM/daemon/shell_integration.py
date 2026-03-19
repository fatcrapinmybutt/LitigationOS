"""
Windows Shell Integration for LitigationOS Daemon.
Provides:
  - Right-click context menu actions (Classify, Add to Evidence, Check Filing Status)
  - Toast notifications via Windows 10+ notification center
  - Registry-based shell extension registration

Requires admin rights for registry modifications.
"""
import json
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("daemon.shell")

# Registry paths for context menu
_SHELL_KEY = r"Software\Classes\*\shell\LitigationOS"
_DIR_SHELL_KEY = r"Software\Classes\Directory\shell\LitigationOS"

# Menu item definitions
MENU_ITEMS = {
    "classify": {
        "label": "🏷 Classify (LitigationOS)",
        "description": "Auto-classify document by type and case lane",
        "task_type": "classify_file",
    },
    "add_evidence": {
        "label": "📎 Add to Evidence (LitigationOS)",
        "description": "Add file to evidence chain with SHA-256 hash",
        "task_type": "add_evidence",
    },
    "check_filing": {
        "label": "📋 Check Filing Status (LitigationOS)",
        "description": "Check which filing package this document belongs to",
        "task_type": "check_filing_status",
    },
}


class ShellIntegration:
    """Manages Windows shell context menu integration."""

    def __init__(self, daemon_exe: str = None):
        self._daemon_exe = daemon_exe or sys.executable
        self._daemon_script = os.path.join(os.path.dirname(__file__), "_shell_action.py")

    def register(self) -> tuple[bool, str]:
        """Register context menu items in Windows registry. Requires admin."""
        if sys.platform != "win32":
            return False, "Windows only"

        try:
            import winreg
        except ImportError:
            return False, "winreg not available"

        errors = []
        for action_id, item in MENU_ITEMS.items():
            try:
                self._register_menu_item(winreg, action_id, item)
            except PermissionError:
                errors.append(f"Permission denied for {action_id} — run as admin")
            except Exception as e:
                errors.append(f"Failed to register {action_id}: {e}")

        if errors:
            return False, "; ".join(errors)
        return True, f"Registered {len(MENU_ITEMS)} context menu items"

    def unregister(self) -> tuple[bool, str]:
        """Remove context menu items from registry."""
        if sys.platform != "win32":
            return False, "Windows only"

        try:
            import winreg
        except ImportError:
            return False, "winreg not available"

        errors = []
        for action_id in MENU_ITEMS:
            for base_key in [_SHELL_KEY, _DIR_SHELL_KEY]:
                key_path = f"{base_key}\\{action_id}"
                try:
                    self._delete_key_recursive(winreg, winreg.HKEY_CURRENT_USER, key_path)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    errors.append(f"Failed to remove {action_id}: {e}")

        # Remove parent keys if empty
        for base_key in [_SHELL_KEY, _DIR_SHELL_KEY]:
            try:
                self._delete_key_recursive(winreg, winreg.HKEY_CURRENT_USER, base_key)
            except Exception:
                pass

        if errors:
            return False, "; ".join(errors)
        return True, "Context menu items removed"

    def _register_menu_item(self, winreg, action_id: str, item: dict):
        """Register a single context menu item."""
        for base_key in [_SHELL_KEY, _DIR_SHELL_KEY]:
            key_path = f"{base_key}\\{action_id}"

            # Create menu key
            key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, key_path,
                access=winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, item["label"])
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ,
                              os.path.join(os.path.dirname(__file__), "icon.ico"))
            winreg.CloseKey(key)

            # Create command key
            cmd_key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, f"{key_path}\\command",
                access=winreg.KEY_SET_VALUE,
            )
            cmd = f'"{self._daemon_exe}" "{self._daemon_script}" {action_id} "%1"'
            winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(cmd_key)

    def _delete_key_recursive(self, winreg, root, path: str):
        """Delete a registry key and all subkeys."""
        try:
            key = winreg.OpenKeyEx(root, path, access=winreg.KEY_ALL_ACCESS)
            info = winreg.QueryInfoKey(key)
            for i in range(info[0] - 1, -1, -1):
                subkey_name = winreg.EnumKey(key, i)
                self._delete_key_recursive(winreg, root, f"{path}\\{subkey_name}")
            winreg.CloseKey(key)
            winreg.DeleteKey(root, path)
        except FileNotFoundError:
            pass

    def is_registered(self) -> bool:
        """Check if context menu is registered."""
        if sys.platform != "win32":
            return False
        try:
            import winreg
            winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, _SHELL_KEY)
            return True
        except (FileNotFoundError, ImportError):
            return False


class ShellAction:
    """Handles shell context menu actions by sending tasks to daemon."""

    def __init__(self):
        from .ipc import IPCClient
        self._client = IPCClient(timeout_ms=10000)

    def execute(self, action_id: str, file_path: str) -> dict:
        """Execute a shell action for the given file."""
        item = MENU_ITEMS.get(action_id)
        if not item:
            return {"success": False, "error": f"Unknown action: {action_id}"}

        # Verify daemon is running
        if not self._client.ping():
            return {"success": False, "error": "Daemon is not running"}

        # Enqueue task
        task_id = self._client.enqueue_task(
            task_type=item["task_type"],
            payload={"file_path": os.path.abspath(file_path)},
            priority="high",
        )

        if task_id:
            return {"success": True, "task_id": task_id, "action": action_id}
        return {"success": False, "error": "Failed to enqueue task"}


class ToastNotifier:
    """Windows 10+ toast notifications."""

    @staticmethod
    def notify(title: str, message: str, timeout_sec: int = 10) -> bool:
        """Show a Windows toast notification."""
        if sys.platform != "win32":
            return False

        # Method 1: win10toast
        try:
            from win10toast import ToastNotifier as _Win10Toast
            toaster = _Win10Toast()
            toaster.show_toast(title, message, duration=timeout_sec, threaded=True)
            return True
        except ImportError:
            pass

        # Method 2: plyer
        try:
            from plyer import notification
            notification.notify(
                title=title, message=message,
                timeout=timeout_sec,
                app_name="LitigationOS",
            )
            return True
        except ImportError:
            pass

        # Method 3: PowerShell fallback
        try:
            import subprocess
            ps_script = (
                f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
                f'ContentType = WindowsRuntime] > $null; '
                f'$xml = [Windows.UI.Notifications.ToastNotificationManager]::'
                f'GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); '
                f'$text = $xml.GetElementsByTagName("text"); '
                f'$text[0].AppendChild($xml.CreateTextNode("{title}")) > $null; '
                f'$text[1].AppendChild($xml.CreateTextNode("{message}")) > $null; '
                f'$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
                f'[Windows.UI.Notifications.ToastNotificationManager]::'
                f'CreateToastNotifier("LitigationOS").Show($toast)'
            )
            subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except Exception:
            pass

        logger.debug("No toast notification method available")
        return False
