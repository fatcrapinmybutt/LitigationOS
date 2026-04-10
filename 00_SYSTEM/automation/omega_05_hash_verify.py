#!/usr/bin/env python3
"""
Ω5: SHA-256 INTEGRITY VERIFY — OMEGA-ELITE-MASTER
Right-click any folder → verify file integrity via SHA-256 checksums.
Creates baseline manifest on first run, verifies against it on subsequent runs.
Detects: tampered files, missing files, new files, bit rot.
"""
import sys, os, hashlib, json
from pathlib import Path
from datetime import datetime

MANIFEST_NAME = "_integrity_manifest.json"

def sha256(fp):
    h = hashlib.sha256()
    try:
        with open(fp, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    except (OSError, PermissionError):
        return None
    return h.hexdigest()

def build_manifest(target):
    manifest = {}
    for fp in sorted(target.rglob("*")):
        if not fp.is_file() or fp.name == MANIFEST_NAME:
            continue
        rel = str(fp.relative_to(target))
        h = sha256(fp)
        if h:
            manifest[rel] = {"hash": h, "size": fp.stat().st_size, "modified": fp.stat().st_mtime}
    return manifest

def verify_folder(target):
    target = Path(target).resolve()
    manifest_path = target / MANIFEST_NAME

    print(f"{'='*60}")
    print(f"  Ω5: SHA-256 INTEGRITY VERIFY")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    if manifest_path.exists():
        # VERIFY mode
        print("📋 Existing manifest found — VERIFYING...")
        with open(manifest_path) as f:
            old = json.load(f)
        old_files = old.get("files", {})
        
        current = build_manifest(target)
        
        tampered = []
        missing = []
        new_files = []
        unchanged = 0

        for rel, info in old_files.items():
            if rel in current:
                if current[rel]["hash"] != info["hash"]:
                    tampered.append(rel)
                else:
                    unchanged += 1
            else:
                missing.append(rel)
        
        for rel in current:
            if rel not in old_files:
                new_files.append(rel)

        total = len(old_files)
        print(f"\n📊 INTEGRITY REPORT")
        print(f"  Baseline files:  {total:,}")
        print(f"  Unchanged:       {unchanged:,} ✅")
        print(f"  Tampered:        {len(tampered):,} {'🔴' if tampered else '✅'}")
        print(f"  Missing:         {len(missing):,} {'🔴' if missing else '✅'}")
        print(f"  New files:       {len(new_files):,}")

        if tampered:
            print(f"\n🔴 TAMPERED FILES:")
            for f in tampered[:30]:
                print(f"  ⚠️ {f}")
        if missing:
            print(f"\n🔴 MISSING FILES:")
            for f in missing[:30]:
                print(f"  ❌ {f}")
        if new_files:
            print(f"\n🆕 NEW FILES:")
            for f in new_files[:30]:
                print(f"  ➕ {f}")

        verdict = "✅ INTEGRITY VERIFIED" if not tampered and not missing else "🔴 INTEGRITY COMPROMISED"
        print(f"\n{'='*60}")
        print(f"  {verdict}")
        print(f"{'='*60}")

        # Update manifest
        new_manifest = {"created": old.get("created", datetime.now().isoformat()),
                        "last_verified": datetime.now().isoformat(),
                        "verification_count": old.get("verification_count", 0) + 1,
                        "files": current}
        with open(manifest_path, "w") as f:
            json.dump(new_manifest, f, indent=2)

    else:
        # CREATE BASELINE mode
        print("🆕 No manifest found — CREATING BASELINE...")
        current = build_manifest(target)
        manifest = {"created": datetime.now().isoformat(),
                     "last_verified": datetime.now().isoformat(),
                     "verification_count": 0,
                     "files": current}
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n✅ Baseline created: {len(current):,} files hashed")
        print(f"📄 Manifest: {manifest_path}")
        print(f"\n  Run again later to VERIFY integrity against this baseline.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_05_hash_verify.py <folder_path>")
        sys.exit(1)
    verify_folder(sys.argv[1])
    input("\nPress Enter to close...")
