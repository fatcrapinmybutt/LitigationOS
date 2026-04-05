"""
EVENT HORIZON Δ∞ — GENESIS: The Deep Scanner
=============================================
Scans a zone (directory) and produces a complete FileManifest for every file.
Content sampling, protection detection, and junk identification included.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from .models import FileManifest, REPO_ROOT, PROTECTED_DIRS, ALLOWED_ROOT_FILES
from .monad import is_junk, is_protected_dir, sample_content

log = logging.getLogger("event_horizon.genesis")


class Genesis:
    """🌅 GENESIS — Deep scanning subsystem.
    
    Scans a zone and produces FileManifest objects for every file found.
    Handles protected zone detection, junk filtering, and content sampling.
    """

    def __init__(self, root: Path = REPO_ROOT, sample_size: int = 2048):
        self.root = root
        self.sample_size = sample_size

    def scan(self, zone: str) -> list[FileManifest]:
        """
        Scan a zone and return all file manifests.
        
        zone: "ROOT" for root-level files, or a canonical folder name like "06_DATA"
        """
        log.info(f"GENESIS: Scanning zone={zone}")

        if zone == "ROOT":
            manifests = list(self._scan_root())
        else:
            zone_path = self.root / zone
            if not zone_path.exists():
                log.warning(f"GENESIS: Zone {zone} does not exist at {zone_path}")
                return []
            manifests = list(self._scan_directory(zone_path))

        log.info(f"GENESIS: Scanned {len(manifests)} files in zone={zone}")
        return manifests

    def _scan_root(self) -> Iterator[FileManifest]:
        """Scan root-level files only (not recursive into subdirectories)."""
        for item in self.root.iterdir():
            if item.is_file():
                yield self._profile_file(item)

    def _scan_directory(self, path: Path) -> Iterator[FileManifest]:
        """Recursively scan a directory for all files."""
        try:
            for item in path.rglob("*"):
                if not item.is_file():
                    continue
                # Skip protected subdirectories
                if is_protected_dir(item):
                    continue
                # Skip embedded git repos
                if ".git" in item.parts:
                    continue
                yield self._profile_file(item)
        except PermissionError as e:
            log.warning(f"GENESIS: Permission denied: {e}")
        except Exception as e:
            log.error(f"GENESIS: Error scanning {path}: {e}")

    def _profile_file(self, path: Path) -> FileManifest:
        """Create a FileManifest for a single file."""
        try:
            manifest = FileManifest.from_path(path, self.sample_size)
        except Exception as e:
            log.warning(f"GENESIS: Error profiling {path}: {e}")
            manifest = FileManifest(
                path=path,
                name=path.name,
                extension=path.suffix.lower(),
                size_bytes=0,
                modified=None,
            )

        # Mark protected files
        if is_protected_dir(path):
            manifest.is_protected = True
        elif path.parent == self.root and path.name in ALLOWED_ROOT_FILES:
            manifest.is_protected = True

        # Mark junk
        # (junk detection happens in Oracle, but we note it here in content_sample)
        if is_junk(manifest.name, manifest.extension):
            if manifest.content_sample is None:
                manifest.content_sample = "__JUNK__"

        return manifest

    def scan_zones(self, zones: list[str]) -> dict[str, list[FileManifest]]:
        """Scan multiple zones, returning manifests keyed by zone name."""
        results = {}
        for zone in zones:
            results[zone] = self.scan(zone)
        return results

    def quick_census(self) -> dict[str, int]:
        """Quick file count per zone without full profiling."""
        census = {"ROOT": 0}
        # Root files
        for item in self.root.iterdir():
            if item.is_file():
                census["ROOT"] += 1
        # Canonical folders
        for folder in self.root.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                try:
                    count = sum(1 for _ in folder.rglob("*") if _.is_file())
                    census[folder.name] = count
                except Exception:
                    census[folder.name] = -1
        return census
