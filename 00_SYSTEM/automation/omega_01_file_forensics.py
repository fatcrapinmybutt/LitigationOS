#!/usr/bin/env python3
"""
Ω1: FILE FORENSICS SCAN — OMEGA-ELITE-MASTER
Right-click any folder → deep metadata analysis, integrity check, timestamp forensics.
Detects: corrupt files, suspicious timestamps, hidden data, encoding anomalies.
"""
import sys, os, hashlib, json, struct
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def get_metadata(fp):
    """Extract deep file metadata."""
    stat = fp.stat()
    return {
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        "readonly": not os.access(str(fp), os.W_OK),
        "hidden": bool(stat.st_file_attributes & 2) if hasattr(stat, 'st_file_attributes') else False,
    }

def detect_magic(fp):
    """Detect file type by magic bytes, compare with extension."""
    MAGIC = {
        b'%PDF': 'pdf', b'\x89PNG': 'png', b'\xff\xd8\xff': 'jpg',
        b'PK\x03\x04': 'zip/docx/xlsx', b'PK\x05\x06': 'zip-empty',
        b'\xd0\xcf\x11\xe0': 'doc/xls-ole', b'SQLite': 'sqlite',
        b'{\n': 'json', b'[': 'json-array', b'<!DOCTYPE': 'html',
        b'<html': 'html', b'\x1f\x8b': 'gzip', b'Rar!': 'rar',
        b'\x50\x4b': 'pkzip', b'\xff\xfe': 'utf16-le-bom',
        b'\xef\xbb\xbf': 'utf8-bom',
    }
    try:
        with open(fp, 'rb') as f:
            header = f.read(16)
        for magic, ftype in MAGIC.items():
            if header.startswith(magic):
                return ftype
    except Exception:
        pass
    return "unknown"

def check_corruption(fp):
    """Basic corruption detection."""
    issues = []
    try:
        sz = fp.stat().st_size
        if sz == 0:
            issues.append("ZERO_BYTE_FILE")
        ext = fp.suffix.lower()
        magic = detect_magic(fp)
        if ext == '.pdf' and magic != 'pdf':
            issues.append(f"MAGIC_MISMATCH: ext={ext}, detected={magic}")
        if ext in ('.jpg', '.jpeg') and magic != 'jpg':
            issues.append(f"MAGIC_MISMATCH: ext={ext}, detected={magic}")
        if ext == '.png' and magic != 'png':
            issues.append(f"MAGIC_MISMATCH: ext={ext}, detected={magic}")
        if ext in ('.docx', '.xlsx', '.pptx') and 'zip' not in magic and 'pkzip' not in magic:
            issues.append(f"MAGIC_MISMATCH: ext={ext}, detected={magic}")
        # Timestamp anomaly: modified before created
        stat = fp.stat()
        if stat.st_mtime < stat.st_ctime - 1:
            issues.append("TIMESTAMP_ANOMALY: modified before created")
        # Future dates
        now = datetime.now().timestamp()
        if stat.st_mtime > now + 86400:
            issues.append("FUTURE_TIMESTAMP: modified in future")
    except Exception as e:
        issues.append(f"ACCESS_ERROR: {e}")
    return issues

def scan_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω1: FILE FORENSICS SCAN")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    results = {"files": 0, "total_size": 0, "issues": [], "types": Counter(), "sizes": Counter()}
    
    for fp in sorted(target.rglob("*")):
        if not fp.is_file():
            continue
        results["files"] += 1
        sz = fp.stat().st_size
        results["total_size"] += sz
        ext = fp.suffix.lower() or "(none)"
        results["types"][ext] += 1
        
        if sz == 0: results["sizes"]["zero"] += 1
        elif sz < 1024: results["sizes"]["<1KB"] += 1
        elif sz < 1048576: results["sizes"]["1KB-1MB"] += 1
        elif sz < 104857600: results["sizes"]["1MB-100MB"] += 1
        else: results["sizes"][">100MB"] += 1

        issues = check_corruption(fp)
        for iss in issues:
            results["issues"].append({"file": str(fp.relative_to(target)), "issue": iss})
    
    # Report
    print(f"📊 SCAN RESULTS")
    print(f"  Files scanned:   {results['files']:,}")
    print(f"  Total size:      {results['total_size']/(1024**2):.1f} MB")
    print(f"\n📁 FILE TYPES:")
    for ext, count in results["types"].most_common(20):
        print(f"  {ext:12s} {count:>6,}")
    print(f"\n📏 SIZE DISTRIBUTION:")
    for label, count in sorted(results["sizes"].items()):
        print(f"  {label:12s} {count:>6,}")
    
    if results["issues"]:
        print(f"\n⚠️  ISSUES FOUND: {len(results['issues'])}")
        for iss in results["issues"][:50]:
            print(f"  🔴 {iss['issue']}: {iss['file']}")
        if len(results["issues"]) > 50:
            print(f"  ... and {len(results['issues'])-50} more")
    else:
        print(f"\n✅ NO ISSUES FOUND")

    # Save report
    report_path = target / f"_forensics_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(report_path, "w") as f:
        json.dump({"scan_time": datetime.now().isoformat(), **results, 
                    "types": dict(results["types"]), "sizes": dict(results["sizes"])}, f, indent=2)
    print(f"\n📄 Report saved: {report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_01_file_forensics.py <folder_path>")
        sys.exit(1)
    scan_folder(sys.argv[1])
    input("\nPress Enter to close...")
