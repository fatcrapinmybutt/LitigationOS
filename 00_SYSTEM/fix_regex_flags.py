"""Fix regex patterns in 5 domain packs - move (?i) flag to start of pattern."""
import json, pathlib, re

BROKEN = [
    "casino-gaming.json",
    "debt-collection.json",
    "patent-trolls.json",
    "sanctions-evasion.json",
    "tenant-rights.json",
]

domains_dir = pathlib.Path(r"J:\CORTEX\domains")

def fix_regex(pattern):
    """Move (?i) to the very start of the pattern."""
    # Remove (?i) wherever it appears
    cleaned = pattern.replace("(?i)", "")
    # Put it at the very beginning
    return "(?i)" + cleaned

for name in BROKEN:
    p = domains_dir / name
    data = json.loads(p.read_text(encoding="utf-8"))
    
    # Fix categories
    cats = data.get("categories", {})
    if isinstance(cats, dict):
        for cat_name, cat_val in cats.items():
            if isinstance(cat_val, dict) and "patterns" in cat_val:
                cat_val["patterns"] = [fix_regex(pat) for pat in cat_val["patterns"]]
    
    # Fix entities too (same issue might exist)
    ents = data.get("entities", {})
    if isinstance(ents, dict):
        for ent_name, ent_val in ents.items():
            if isinstance(ent_val, dict) and "patterns" in ent_val:
                ent_val["patterns"] = [fix_regex(pat) if "(?i)" in pat else pat for pat in ent_val["patterns"]]
    
    # Also fix flat-format entity_patterns and evidence_categories
    for key in ["entity_patterns", "evidence_categories"]:
        section = data.get(key, {})
        if isinstance(section, dict):
            for k, v in section.items():
                if isinstance(v, str) and "(?i)" in v:
                    section[k] = fix_regex(v)
    
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"FIXED: {name}")

print("\nDone. Re-run verification.")
