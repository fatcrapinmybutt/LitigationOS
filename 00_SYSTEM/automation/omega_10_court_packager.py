#!/usr/bin/env python3
"""
Ω10: COURT FILING PACKAGER — OMEGA-ELITE-MASTER
Right-click any folder → assemble a complete court filing package.
Auto-detects: main motion, exhibits, COS, proposed order, cover sheet.
Generates: filing checklist, exhibit index, page count, filing manifest.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime

FILING_COMPONENTS = {
    "motion": ["motion", "brief", "complaint", "petition", "application"],
    "exhibit": ["exhibit", "attachment", "appendix"],
    "cos": ["certificate of service", "cos", "proof of service"],
    "proposed_order": ["proposed order", "order to show cause"],
    "cover_sheet": ["cover sheet", "civil case cover"],
    "affidavit": ["affidavit", "declaration", "verification", "sworn"],
    "memorandum": ["memorandum", "memo of law", "brief in support"],
}

MCR_REQUIREMENTS = {
    "motion": "MCR 2.119(A)(1) — Written motions with supporting brief",
    "cos": "MCR 2.107 — Proof of service on all parties",
    "proposed_order": "MCR 2.602 — Proposed order submitted with motion",
    "caption": "MCR 1.109(D)(1) — Proper caption with case number",
}

def classify_file(fp):
    """Classify a file by its likely role in a filing package."""
    name = fp.stem.lower()
    try:
        text = fp.read_text(encoding='utf-8', errors='replace')[:2000].lower()
    except Exception:
        text = name

    for role, keywords in FILING_COMPONENTS.items():
        for kw in keywords:
            if kw in name or kw in text:
                return role
    return "supporting"

def package_folder(target):
    target = Path(target).resolve()
    print(f"{'='*60}")
    print(f"  Ω10: COURT FILING PACKAGER")
    print(f"  Target: {target}")
    print(f"{'='*60}\n")

    # Collect files
    package = {"motion": [], "exhibit": [], "cos": [], "proposed_order": [],
               "cover_sheet": [], "affidavit": [], "memorandum": [], "supporting": []}
    
    for fp in sorted(target.rglob("*")):
        if fp.suffix.lower() in ('.md', '.txt', '.pdf', '.docx') and fp.is_file():
            if fp.name.startswith("_"):
                continue
            role = classify_file(fp)
            sz = fp.stat().st_size
            package[role].append({
                "file": fp.name,
                "path": str(fp.relative_to(target)),
                "size": sz,
                "type": fp.suffix.lower(),
                "page_est": max(1, sz // 3000),
            })

    total_files = sum(len(v) for v in package.values())
    total_pages = sum(f["page_est"] for v in package.values() for f in v)

    print(f"📦 FILING PACKAGE ASSEMBLY")
    print(f"  Total files: {total_files}")
    print(f"  Est. pages:  {total_pages}")
    
    for role, files in package.items():
        if files:
            icon = "📄" if role == "motion" else "📎" if role == "exhibit" else "📜"
            print(f"\n  {icon} {role.upper()} ({len(files)} files):")
            for f in files:
                print(f"     {f['file']} ({f['page_est']} pg)")

    # Compliance checklist
    print(f"\n{'─'*60}")
    print(f"  MCR COMPLIANCE CHECKLIST")
    print(f"{'─'*60}")
    checklist = {}
    for req, rule in MCR_REQUIREMENTS.items():
        has = bool(package.get(req))
        checklist[req] = has
        icon = "✅" if has else "❌"
        print(f"  {icon} {rule}")
    
    # Additional checks
    if package["exhibit"]:
        print(f"  ✅ Exhibits present ({len(package['exhibit'])} files)")
    if package["affidavit"]:
        print(f"  ✅ Affidavit/Declaration present")

    ready = all(checklist.get(k, False) for k in ["motion", "cos"])
    verdict = "✅ FILING READY" if ready else "❌ INCOMPLETE — see missing items above"
    
    print(f"\n{'='*60}")
    print(f"  {verdict}")
    print(f"{'='*60}")

    # Generate manifest
    manifest = {
        "package_time": datetime.now().isoformat(),
        "target": str(target),
        "total_files": total_files,
        "total_pages_est": total_pages,
        "filing_ready": ready,
        "checklist": checklist,
        "components": {k: v for k, v in package.items() if v},
    }

    manifest_path = target / f"_FILING_MANIFEST_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Generate filing checklist markdown
    cl_path = target / "_FILING_CHECKLIST.md"
    with open(cl_path, "w", encoding="utf-8") as f:
        f.write(f"# FILING CHECKLIST\n\n")
        f.write(f"**Generated:** {datetime.now():%B %d, %Y at %I:%M %p}\n")
        f.write(f"**Status:** {'READY' if ready else 'INCOMPLETE'}\n\n")
        f.write(f"## Components\n\n")
        for role, files in package.items():
            if files:
                f.write(f"### {role.title()}\n")
                for fl in files:
                    f.write(f"- [x] {fl['file']} (~{fl['page_est']} pages)\n")
                f.write("\n")
        f.write(f"## MCR Compliance\n\n")
        for req, rule in MCR_REQUIREMENTS.items():
            check = "x" if checklist.get(req) else " "
            f.write(f"- [{check}] {rule}\n")
        f.write(f"\n**Total pages:** ~{total_pages}\n")

    print(f"\n📄 Manifest: {manifest_path}")
    print(f"📄 Checklist: {cl_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python omega_10_court_packager.py <folder_path>")
        sys.exit(1)
    package_folder(sys.argv[1])
    input("\nPress Enter to close...")
