"""
System Tray Icon for LitigationOS Daemon.
Provides quick-access status, controls, and notifications via Windows tray.

Requires: pystray, Pillow
Falls back gracefully when not installed.
"""
import io
import logging
import os
import sys
import threading
import webbrowser
from typing import Callable, Optional

logger = logging.getLogger("daemon.tray")

# Color constants for status indicator
COLOR_GREEN = (76, 175, 80)     # Running + healthy
COLOR_YELLOW = (255, 193, 7)    # Running + warnings
COLOR_RED = (244, 67, 54)       # Stopped or errors
COLOR_GRAY = (158, 158, 158)    # Unknown


def _create_icon_image(color: tuple = COLOR_GREEN, size: int = 64):
    """Create a simple colored circle icon."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle (border)
    draw.ellipse([2, 2, size - 3, size - 3], fill=color, outline=(30, 30, 30), width=2)

    # Inner "L" for LitigationOS
    cx, cy = size // 2, size // 2
    white = (255, 255, 255)
    # Vertical bar of L
    draw.rectangle([cx - 8, cy - 12, cx - 3, cy + 8], fill=white)
    # Horizontal bar of L
    draw.rectangle([cx - 8, cy + 3, cx + 8, cy + 8], fill=white)

    return img


class TrayIcon:
    """System tray icon with status indicator and context menu."""

    def __init__(self, on_start: Callable = None, on_stop: Callable = None,
                 on_status: Callable = None, on_quit: Callable = None):
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_status = on_status
        self._on_quit = on_quit
        self._icon = None
        self._thread: Optional[threading.Thread] = None
        self._current_color = COLOR_GRAY

    def start(self):
        """Start the tray icon in a background thread."""
        try:
            import pystray
        except ImportError:
            logger.warning("pystray not installed — tray icon disabled. Install: pip install pystray Pillow")
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("System tray icon started")

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        logger.info("System tray icon stopped")

    def update_status(self, status: str, tooltip: str = None):
        """Update icon color based on daemon status."""
        color_map = {
            "running": COLOR_GREEN,
            "healthy": COLOR_GREEN,
            "warning": COLOR_YELLOW,
            "degraded": COLOR_YELLOW,
            "stopped": COLOR_RED,
            "error": COLOR_RED,
            "critical": COLOR_RED,
        }
        new_color = color_map.get(status, COLOR_GRAY)

        if new_color != self._current_color and self._icon:
            self._current_color = new_color
            new_image = _create_icon_image(new_color)
            if new_image:
                self._icon.icon = new_image
            if tooltip:
                self._icon.title = f"LitigationOS — {tooltip}"

    def notify(self, title: str, message: str):
        """Show a Windows notification balloon."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception as e:
                logger.debug(f"Notification failed: {e}")

    def _run(self):
        """Main tray icon loop."""
        import pystray

        image = _create_icon_image(COLOR_GRAY)
        if image is None:
            logger.error("Failed to create tray icon image (Pillow not installed?)")
            return

        menu = pystray.Menu(
            pystray.MenuItem("LitigationOS Daemon", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("▶ Start Daemon", self._menu_start),
            pystray.MenuItem("⏹ Stop Daemon", self._menu_stop),
            pystray.MenuItem("📊 Status", self._menu_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📂 Open Project", self._menu_open_project),
            pystray.MenuItem("📋 View Logs", self._menu_open_logs),
            pystray.MenuItem("⚙ Settings", self._menu_open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._menu_quit),
        )

        self._icon = pystray.Icon(
            "litigationos",
            image,
            "LitigationOS Daemon",
            menu,
        )

        self._icon.run()

    def _menu_start(self, icon, item):
        if self._on_start:
            try:
                self._on_start()
                self.notify("LitigationOS", "Daemon started")
            except Exception as e:
                self.notify("LitigationOS Error", str(e))

    def _menu_stop(self, icon, item):
        if self._on_stop:
            try:
                self._on_stop()
                self.notify("LitigationOS", "Daemon stopped")
            except Exception as e:
                self.notify("LitigationOS Error", str(e))

    def _menu_status(self, icon, item):
        if self._on_status:
            try:
                status = self._on_status()
                if isinstance(status, dict):
                    msg = (
                        f"Status: {status.get('status', 'unknown')}\n"
                        f"Uptime: {status.get('uptime_sec', 0):.0f}s\n"
                        f"Queue: {status.get('task_queue_depth', 0)} tasks\n"
                        f"Running: {status.get('running_tasks', 0)} tasks"
                    )
                else:
                    msg = str(status)
                self.notify("LitigationOS Status", msg)
            except Exception as e:
                self.notify("LitigationOS Error", str(e))

    def _menu_open_project(self, icon, item):
        project_dir = r"C:\Users\andre\LitigationOS"
        if os.path.isdir(project_dir):
            os.startfile(project_dir)

    def _menu_open_logs(self, icon, item):
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        if os.path.isdir(log_dir):
            os.startfile(log_dir)

    def _menu_open_config(self, icon, item):
        config_path = os.path.join(os.path.dirname(__file__), "daemon_config.yaml")
        if os.path.isfile(config_path):
            os.startfile(config_path)

    def _menu_quit(self, icon, item):
        if self._on_quit:
            self._on_quit()
        icon.stop()
