"""
Storage path resolver for LitigationOS Daemon.
Implements drive strategy: I: = heavy, D/F/G/H = lite, C: = primary.
"""
import os
import shutil
from typing import Optional

from .models import DaemonConfig, DriveConfig, DriveHealth, DriveRole

# File types → drive role mapping
HEAVY_EXTENSIONS = {
    ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".bak", ".dump", ".sql",
}

LITE_EXTENSIONS = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".csv",
    ".html", ".htm", ".xml",
}

# Size threshold: files above this go to heavy storage
HEAVY_SIZE_THRESHOLD_MB = 50


class StorageResolver:
    """Resolves file storage paths based on drive strategy."""

    def __init__(self, config: DaemonConfig):
        self.config = config
        self._drive_map: dict[DriveRole, list[DriveConfig]] = {}
        for drive in config.drives:
            self._drive_map.setdefault(drive.role, []).append(drive)

    def resolve_path(self, file_path: str, target_subdir: str = "") -> str:
        """Determine the correct storage location for a file.

        Args:
            file_path: Path to the file being stored
            target_subdir: Subdirectory within the drive (e.g., "DEDUP_GLOBAL")

        Returns:
            Full target path on the appropriate drive
        """
        ext = os.path.splitext(file_path)[1].lower()
        size_mb = 0
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Determine drive role
        if ext in HEAVY_EXTENSIONS or size_mb >= HEAVY_SIZE_THRESHOLD_MB:
            role = DriveRole.HEAVY
        elif ext in LITE_EXTENSIONS and size_mb < 10:
            role = DriveRole.LITE
        else:
            role = DriveRole.HEAVY  # Default to heavy for safety

        # Find best drive with enough space
        target_drive = self._find_drive(role, size_mb)
        if target_drive is None:
            # Fallback: try any drive with space
            target_drive = self._find_any_drive(size_mb)
        if target_drive is None:
            # Last resort: primary drive
            return os.path.join("C:", target_subdir, os.path.basename(file_path))

        base = target_drive.path
        if target_subdir:
            return os.path.join(base, target_subdir, os.path.basename(file_path))
        return os.path.join(base, os.path.basename(file_path))

    def _find_drive(self, role: DriveRole, size_mb: float) -> Optional[DriveConfig]:
        """Find a drive with the given role that has enough space."""
        for drive in self._drive_map.get(role, []):
            health = self.get_drive_health(drive)
            if health and health.free_gb > drive.pause_ingest_free_gb:
                if size_mb <= drive.max_file_size_mb:
                    return drive
        return None

    def _find_any_drive(self, size_mb: float) -> Optional[DriveConfig]:
        """Find any drive with space."""
        for drives in self._drive_map.values():
            for drive in drives:
                health = self.get_drive_health(drive)
                if health and health.free_gb > drive.pause_ingest_free_gb:
                    return drive
        return None

    def get_drive_health(self, drive: DriveConfig) -> Optional[DriveHealth]:
        """Get health status of a drive."""
        drive_path = drive.path + "\\"
        if not os.path.exists(drive_path):
            return None
        try:
            usage = shutil.disk_usage(drive_path)
            total_gb = usage.total / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            percent = (used_gb / total_gb * 100) if total_gb > 0 else 0

            status = "healthy"
            if free_gb < drive.pause_ingest_free_gb:
                status = "critical"
            elif free_gb < drive.alert_free_gb:
                status = "warning"

            return DriveHealth(
                path=drive.path,
                role=drive.role,
                total_gb=round(total_gb, 2),
                used_gb=round(used_gb, 2),
                free_gb=round(free_gb, 2),
                percent_used=round(percent, 1),
                status=status,
            )
        except OSError:
            return None

    def get_all_drive_health(self) -> list[DriveHealth]:
        """Get health for all configured drives."""
        results = []
        for drive in self.config.drives:
            health = self.get_drive_health(drive)
            if health:
                results.append(health)
        return results

    def get_storage_metrics(self) -> dict:
        """Get comprehensive storage metrics dashboard data."""
        metrics = {
            "drives": [],
            "total_capacity_gb": 0.0,
            "total_used_gb": 0.0,
            "total_free_gb": 0.0,
            "heavy_drive_free_gb": 0.0,
            "lite_drives_free_gb": 0.0,
            "primary_free_gb": 0.0,
            "health_summary": "healthy",
            "warnings": [],
        }

        warning_count = 0
        critical_count = 0

        for drive in self.config.drives:
            health = self.get_drive_health(drive)
            if health is None:
                metrics["drives"].append({
                    "path": drive.path, "role": drive.role.value,
                    "status": "offline",
                })
                metrics["warnings"].append(f"Drive {drive.path} is offline")
                warning_count += 1
                continue

            drive_info = {
                "path": health.path,
                "role": health.role.value,
                "total_gb": health.total_gb,
                "used_gb": health.used_gb,
                "free_gb": health.free_gb,
                "percent_used": health.percent_used,
                "status": health.status,
            }
            metrics["drives"].append(drive_info)

            metrics["total_capacity_gb"] += health.total_gb
            metrics["total_used_gb"] += health.used_gb
            metrics["total_free_gb"] += health.free_gb

            if drive.role == DriveRole.HEAVY:
                metrics["heavy_drive_free_gb"] += health.free_gb
            elif drive.role == DriveRole.LITE:
                metrics["lite_drives_free_gb"] += health.free_gb
            elif drive.role == DriveRole.PRIMARY:
                metrics["primary_free_gb"] += health.free_gb

            if health.status == "critical":
                critical_count += 1
                metrics["warnings"].append(f"Drive {drive.path} critically low on space ({health.free_gb:.1f} GB)")
            elif health.status == "warning":
                warning_count += 1
                metrics["warnings"].append(f"Drive {drive.path} low on space ({health.free_gb:.1f} GB)")

        # Round values
        for key in ["total_capacity_gb", "total_used_gb", "total_free_gb",
                     "heavy_drive_free_gb", "lite_drives_free_gb", "primary_free_gb"]:
            metrics[key] = round(metrics[key], 2)

        if critical_count > 0:
            metrics["health_summary"] = "critical"
        elif warning_count > 0:
            metrics["health_summary"] = "warning"

        return metrics

    def find_heavy_files_on_flash(self, min_size_mb: float = 50) -> list[dict]:
        """Find files on flash drives that should be on heavy storage."""
        heavy_files = []
        for drive in self._drive_map.get(DriveRole.LITE, []):
            drive_root = drive.path + "\\"
            if not os.path.exists(drive_root):
                continue
            try:
                for root, dirs, files in os.walk(drive_root):
                    for f in files:
                        full = os.path.join(root, f)
                        try:
                            size = os.path.getsize(full) / (1024 * 1024)
                            if size >= min_size_mb:
                                heavy_files.append({
                                    "path": full,
                                    "size_mb": round(size, 2),
                                    "drive": drive.path,
                                    "ext": os.path.splitext(f)[1].lower(),
                                })
                        except OSError:
                            continue
            except OSError:
                continue
        return heavy_files
