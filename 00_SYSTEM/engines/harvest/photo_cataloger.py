"""Harvest Engine — Photo cataloging with EXIF metadata extraction.

Extracts EXIF data from images (JPEG, PNG, TIFF, HEIC) using Pillow,
classifies photos as potentially evidentiary based on date range and
GPS proximity to Muskegon, MI. Returns structured metadata for each image.

NO module-level side effects. NO stdout clobbering. NO database connections.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Supported image extensions ───────────────────────────────────────────────
IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic",
})

# ── Evidentiary classification parameters ────────────────────────────────────
# Case-relevant date range: 2023-01-01 through 2026-12-31
EVIDENCE_DATE_START = datetime(2023, 1, 1)
EVIDENCE_DATE_END = datetime(2026, 12, 31)

# Muskegon, MI approximate center: 43.2342° N, 86.2484° W
MUSKEGON_LAT = 43.2342
MUSKEGON_LON = -86.2484
# Radius in km — covers Muskegon, Norton Shores, North Muskegon, Whitehall
MUSKEGON_RADIUS_KM = 30.0

# EXIF tag IDs (Pillow uses integer keys from the EXIF spec)
_EXIF_TAG_DATETIME = 0x9003         # DateTimeOriginal
_EXIF_TAG_DATETIME_FALLBACK = 0x0132  # DateTime (modify date)
_EXIF_TAG_MAKE = 0x010F             # Camera Make
_EXIF_TAG_MODEL = 0x0110            # Camera Model
_EXIF_TAG_ORIENTATION = 0x0112      # Orientation
_EXIF_TAG_GPS_INFO = 0x8825         # GPSInfo sub-IFD pointer
_EXIF_TAG_IMAGE_WIDTH = 0xA002      # PixelXDimension (EXIF)
_EXIF_TAG_IMAGE_HEIGHT = 0xA003     # PixelYDimension (EXIF)

# GPS sub-tags within GPSInfo
_GPS_LAT_REF = 1       # 'N' or 'S'
_GPS_LAT = 2            # ((deg_num, deg_den), (min_num, min_den), (sec_num, sec_den))
_GPS_LON_REF = 3        # 'E' or 'W'
_GPS_LON = 4            # same format as latitude

# ── Lazy import for Pillow ───────────────────────────────────────────────────
_PIL_Image = None
_PIL_ExifTags = None


def _get_pil():
    """Lazy-load PIL.Image and PIL.ExifTags. Returns (Image, ExifTags) or (None, None)."""
    global _PIL_Image, _PIL_ExifTags
    if _PIL_Image is None:
        try:
            from PIL import Image as _img
            from PIL import ExifTags as _tags
            _PIL_Image = _img
            _PIL_ExifTags = _tags
        except ImportError:
            logger.warning("Pillow not available — photo cataloging disabled")
            _PIL_Image = False
            _PIL_ExifTags = False
    img = _PIL_Image if _PIL_Image is not False else None
    tags = _PIL_ExifTags if _PIL_ExifTags is not False else None
    return img, tags


# ── Data class ───────────────────────────────────────────────────────────────


@dataclass
class PhotoResult:
    """Metadata extracted from a single image file."""
    file_path: str
    date_taken: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    camera: Optional[str] = None
    dimensions: Optional[Tuple[int, int]] = None
    file_size: int = 0
    is_evidentiary: bool = False
    classification_reason: str = ""


# ── Internal helpers ─────────────────────────────────────────────────────────


def _parse_exif_datetime(raw: str) -> Optional[datetime]:
    """Parse EXIF datetime string (``YYYY:MM:DD HH:MM:SS``) to datetime."""
    if not raw or not isinstance(raw, str):
        return None
    # EXIF uses colons in the date portion
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _dms_to_decimal(dms_tuple, ref: str) -> Optional[float]:
    """Convert EXIF GPS DMS (degrees/minutes/seconds) to decimal degrees.

    ``dms_tuple`` may be a sequence of IFDRational or plain tuples.
    ``ref`` is 'N'/'S'/'E'/'W'.
    """
    try:
        # Handle IFDRational objects (Pillow >= 8) and plain tuples
        parts = []
        for component in dms_tuple:
            if hasattr(component, "numerator") and hasattr(component, "denominator"):
                # IFDRational
                val = float(component.numerator) / float(component.denominator) if component.denominator else 0.0
            elif isinstance(component, tuple) and len(component) == 2:
                val = float(component[0]) / float(component[1]) if component[1] else 0.0
            else:
                val = float(component)
            parts.append(val)

        if len(parts) < 3:
            return None

        decimal = parts[0] + parts[1] / 60.0 + parts[2] / 3600.0
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except (TypeError, ValueError, ZeroDivisionError, IndexError) as exc:
        logger.debug("GPS DMS conversion failed: %s", exc)
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance between two GPS coordinates in kilometres."""
    r = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def _extract_gps(exif_data: dict) -> Tuple[Optional[float], Optional[float]]:
    """Extract GPS latitude and longitude from EXIF GPS sub-IFD."""
    gps_info = exif_data.get(_EXIF_TAG_GPS_INFO)
    if not gps_info or not isinstance(gps_info, dict):
        return None, None

    lat_ref = gps_info.get(_GPS_LAT_REF, "")
    lat_dms = gps_info.get(_GPS_LAT)
    lon_ref = gps_info.get(_GPS_LON_REF, "")
    lon_dms = gps_info.get(_GPS_LON)

    lat = _dms_to_decimal(lat_dms, lat_ref) if lat_dms else None
    lon = _dms_to_decimal(lon_dms, lon_ref) if lon_dms else None
    return lat, lon


def _classify_evidentiary(result: PhotoResult) -> None:
    """Determine if the photo is potentially evidentiary. Mutates *result* in-place."""
    reasons: List[str] = []

    # Date within case-relevant range
    if result.date_taken is not None:
        if EVIDENCE_DATE_START <= result.date_taken <= EVIDENCE_DATE_END:
            reasons.append(f"date in case range ({result.date_taken.strftime('%Y-%m-%d')})")

    # GPS within Muskegon area
    if result.gps_lat is not None and result.gps_lon is not None:
        dist = _haversine_km(result.gps_lat, result.gps_lon, MUSKEGON_LAT, MUSKEGON_LON)
        if dist <= MUSKEGON_RADIUS_KM:
            reasons.append(f"GPS within {dist:.1f} km of Muskegon")

    if reasons:
        result.is_evidentiary = True
        result.classification_reason = "; ".join(reasons)
    else:
        result.classification_reason = "no evidentiary indicators"


# ── Public API ───────────────────────────────────────────────────────────────


def catalog_single(file_path: str | Path) -> PhotoResult:
    """Extract EXIF metadata from a single image and classify it.

    Args:
        file_path: Path to an image file.

    Returns:
        PhotoResult with extracted metadata. Fields are None when EXIF data
        is missing or Pillow is unavailable.
    """
    fpath = Path(file_path)
    result = PhotoResult(file_path=str(fpath))

    # File size
    try:
        result.file_size = fpath.stat().st_size
    except OSError:
        result.file_size = 0

    if not fpath.is_file():
        logger.warning("Image file not found: %s", fpath)
        result.classification_reason = "file not found"
        return result

    Image, _ExifTags = _get_pil()
    if Image is None:
        result.classification_reason = "Pillow unavailable"
        return result

    try:
        with Image.open(fpath) as img:
            # Dimensions from the image itself (always available)
            result.dimensions = (img.width, img.height)

            # Attempt EXIF extraction
            exif_data: dict = {}
            try:
                raw_exif = img.getexif()
                if raw_exif:
                    exif_data = dict(raw_exif)
                    # Pillow nests GPS in a sub-IFD accessed via get_ifd()
                    try:
                        gps_ifd = raw_exif.get_ifd(_EXIF_TAG_GPS_INFO)
                        if gps_ifd:
                            exif_data[_EXIF_TAG_GPS_INFO] = dict(gps_ifd)
                    except (AttributeError, KeyError):
                        # Older Pillow or no GPS — try plain dict lookup
                        if _EXIF_TAG_GPS_INFO in exif_data and isinstance(exif_data[_EXIF_TAG_GPS_INFO], int):
                            # Tag is just a pointer, not a dict — skip
                            exif_data.pop(_EXIF_TAG_GPS_INFO, None)
            except Exception as exc:
                logger.debug("EXIF read failed for %s: %s", fpath.name, exc)

            if not exif_data:
                _classify_evidentiary(result)
                return result

            # ── Date taken ────────────────────────────────────────────
            date_raw = exif_data.get(_EXIF_TAG_DATETIME)
            if date_raw is None:
                date_raw = exif_data.get(_EXIF_TAG_DATETIME_FALLBACK)
            result.date_taken = _parse_exif_datetime(str(date_raw) if date_raw else "")

            # ── Camera ────────────────────────────────────────────────
            make = exif_data.get(_EXIF_TAG_MAKE, "")
            model = exif_data.get(_EXIF_TAG_MODEL, "")
            camera_parts = [str(p).strip() for p in (make, model) if p]
            result.camera = " ".join(camera_parts) if camera_parts else None

            # ── EXIF dimensions (override if present) ─────────────────
            exif_w = exif_data.get(_EXIF_TAG_IMAGE_WIDTH)
            exif_h = exif_data.get(_EXIF_TAG_IMAGE_HEIGHT)
            if exif_w and exif_h:
                try:
                    result.dimensions = (int(exif_w), int(exif_h))
                except (ValueError, TypeError):
                    pass  # keep PIL dimensions

            # ── GPS ───────────────────────────────────────────────────
            result.gps_lat, result.gps_lon = _extract_gps(exif_data)

    except Exception as exc:
        logger.error("Failed to process image %s: %s", fpath.name, exc)
        result.classification_reason = f"processing error: {exc}"
        return result

    _classify_evidentiary(result)
    return result


def catalog_directory(
    dir_path: str | Path,
    recursive: bool = True,
    extensions: Optional[frozenset] = None,
) -> List[PhotoResult]:
    """Recursively scan a directory and catalog all images.

    Args:
        dir_path: Root directory to scan.
        recursive: If True (default), scan subdirectories.
        extensions: Image suffixes to include. Defaults to
            ``IMAGE_EXTENSIONS`` (.jpg, .jpeg, .png, .tiff, .tif, .heic).

    Returns:
        List of PhotoResult, one per image found (sorted by file path).
    """
    root = Path(dir_path)
    if not root.is_dir():
        logger.warning("Photo scan directory not found: %s", root)
        return []

    exts = extensions if extensions is not None else IMAGE_EXTENSIONS
    results: List[PhotoResult] = []

    try:
        iterator = root.rglob("*") if recursive else root.iterdir()
        for entry in iterator:
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in exts:
                continue
            result = catalog_single(entry)
            results.append(result)
    except OSError as exc:
        logger.error("Error scanning directory %s: %s", root, exc)

    results.sort(key=lambda r: r.file_path)
    logger.info(
        "Cataloged %d images in %s (%d evidentiary)",
        len(results), root,
        sum(1 for r in results if r.is_evidentiary),
    )
    return results


def filter_evidentiary(photos: List[PhotoResult]) -> List[PhotoResult]:
    """Return only photos classified as evidentiary.

    Args:
        photos: List of PhotoResult from ``catalog_directory`` or individual calls.

    Returns:
        Filtered list (new list — does not mutate input).
    """
    return [p for p in photos if p.is_evidentiary]


def summarize_catalog(photos: List[PhotoResult]) -> dict:
    """Produce a summary dict for a batch of cataloged photos.

    Returns:
        Dict with keys: total, evidentiary, with_gps, with_date, cameras,
        date_range, total_size_bytes.
    """
    cameras: set = set()
    dates: List[datetime] = []
    total_size = 0

    for p in photos:
        total_size += p.file_size
        if p.camera:
            cameras.add(p.camera)
        if p.date_taken:
            dates.append(p.date_taken)

    return {
        "total": len(photos),
        "evidentiary": sum(1 for p in photos if p.is_evidentiary),
        "with_gps": sum(1 for p in photos if p.gps_lat is not None),
        "with_date": sum(1 for p in photos if p.date_taken is not None),
        "cameras": sorted(cameras),
        "date_range": (min(dates).isoformat(), max(dates).isoformat()) if dates else None,
        "total_size_bytes": total_size,
    }
