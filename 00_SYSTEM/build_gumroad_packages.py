"""Build upload-ready Gumroad product ZIPs for CORTEX."""
import zipfile, os, json, sys
from pathlib import Path

CORTEX = Path(r"J:\CORTEX")
DIST = CORTEX / "dist" / "CORTEX"
DOMAINS = CORTEX / "domains"
OUT = CORTEX / "gumroad_packages"
INDIV = OUT / "individual_packs"

# Ensure output dirs
OUT.mkdir(exist_ok=True)
INDIV.mkdir(exist_ok=True)

FREE_PACKS = {"osint.json", "cyber.json", "legal.json"}

# Price tiers
TIER_14 = {
    "academic-integrity.json", "journalism.json", "missing-persons.json"
}
TIER_29 = {
    "antitrust.json", "aviation-safety.json", "banking-fraud.json",
    "corporate-compliance.json", "corporate-espionage.json", "cryptocurrency.json",
    "defense-contractor.json", "divorce-forensics.json", "due-diligence.json",
    "energy-sector.json", "environmental.json", "healthcare-fraud.json",
    "human-trafficking.json", "insurance-claims.json", "intellectual-property.json",
    "maritime.json", "media-disinformation.json", "pharmaceutical.json",
    "supply-chain.json", "tax-fraud.json", "telecom-fraud.json", "wildlife-trafficking.json"
}

def get_exe_files():
    """Get all files in the dist/CORTEX directory."""
    files = []
    for root, dirs, fnames in os.walk(DIST):
        for f in fnames:
            full = Path(root) / f
            arc = "CORTEX/" + str(full.relative_to(DIST)).replace("\\", "/")
            files.append((str(full), arc))
    return files

def build_pro_zip():
    """Product 1: CORTEX Pro ($49) — exe + 3 free packs."""
    out_path = OUT / "CORTEX_PRO_v1.0.0.zip"
    print(f"Building Pro ZIP...")
    exe_files = get_exe_files()
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full, arc in exe_files:
            # Skip premium domain packs from exe bundle
            if "domains" in arc:
                fname = os.path.basename(full)
                if fname not in FREE_PACKS:
                    continue
            zf.write(full, arc)
        # Add README
        readme = CORTEX / "README.md"
        if readme.exists():
            zf.write(str(readme), "CORTEX/README.md")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  -> {out_path.name}: {size_mb:.1f} MB")
    return out_path

def build_bundle_zip():
    """Product 2: Complete Bundle ($199) — exe + ALL 55 packs."""
    out_path = OUT / "CORTEX_COMPLETE_BUNDLE_v1.0.0.zip"
    print(f"Building Complete Bundle ZIP...")
    exe_files = get_exe_files()
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for full, arc in exe_files:
            zf.write(full, arc)
        # Ensure all 55 domain packs are included
        for pack_file in sorted(DOMAINS.glob("*.json")):
            arc_name = f"CORTEX/domains/{pack_file.name}"
            # Check if already in exe bundle
            already = any(a == arc_name for _, a in exe_files)
            if not already:
                zf.write(str(pack_file), arc_name)
        # Add README
        readme = CORTEX / "README.md"
        if readme.exists():
            zf.write(str(readme), "CORTEX/README.md")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  -> {out_path.name}: {size_mb:.1f} MB")
    return out_path

def build_individual_packs():
    """Product 3+: Individual domain pack ZIPs ($14-$29 each)."""
    print(f"Building individual pack ZIPs...")
    count = 0
    for pack_file in sorted(DOMAINS.glob("*.json")):
        if pack_file.name in FREE_PACKS:
            continue  # Free packs come with Pro
        # Determine price tier
        if pack_file.name in TIER_14:
            price = 14
        elif pack_file.name in TIER_29:
            price = 29
        else:
            price = 19
        # Load pack for name
        with open(pack_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        pack_name = data.get("name", pack_file.stem)
        # Build zip
        slug = pack_file.stem
        zip_name = f"cortex-pack-{slug}.zip"
        zip_path = INDIV / zip_name
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(pack_file), f"domains/{pack_file.name}")
            # Add a small README inside
            info = f"# CORTEX Domain Pack: {pack_name}\n\n"
            info += f"Price: ${price}\n\n"
            info += "## Installation\n\n"
            info += "1. Copy the .json file to your CORTEX/domains/ folder\n"
            info += "2. Run: CORTEX.exe list-domains (to verify)\n"
            info += "3. Run: CORTEX.exe build --domain {slug} --input YOUR_FOLDER\n\n"
            info += "Requires CORTEX Pro ($49) base application.\n"
            zf.writestr("README.txt", info)
        count += 1
    print(f"  -> {count} individual pack ZIPs created in {INDIV}")
    return count

# Main
if not DIST.exists():
    print(f"ERROR: {DIST} not found. Build exe first.")
    sys.exit(1)

pro = build_pro_zip()
bundle = build_bundle_zip()
n_packs = build_individual_packs()

# Summary
print(f"\n{'='*60}")
print(f"GUMROAD PACKAGES READY")
print(f"{'='*60}")
print(f"  Pro ($49):     {pro}")
print(f"  Bundle ($199): {bundle}")
print(f"  Individual:    {n_packs} packs in {INDIV}")
print(f"\nUpload guide:  J:\\CORTEX\\GUMROAD_UPLOAD_GUIDE.md")
