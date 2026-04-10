"""Fix domain packs where 'categories' is a list instead of a dict."""
import json, pathlib, re

BROKEN = [
    "casino-gaming.json",
    "debt-collection.json",
    "patent-trolls.json",
    "sanctions-evasion.json",
    "tenant-rights.json",
]

domains_dir = pathlib.Path(r"J:\CORTEX\domains")

for name in BROKEN:
    p = domains_dir / name
    data = json.loads(p.read_text(encoding="utf-8"))
    cats = data.get("categories", [])
    if isinstance(cats, list):
        # Convert list items to dict: {"Item Name": {"patterns": ["regex"], "color": "#hex"}}
        new_cats = {}
        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
                  "#1abc9c", "#e67e22", "#c0392b", "#2980b9", "#27ae60"]
        for i, item in enumerate(cats):
            # Build a regex from the category name (case-insensitive words)
            words = item.split()
            if len(words) <= 3:
                pattern = r"(?i)\b" + r"\s+".join(re.escape(w) for w in words) + r"\b"
            else:
                # Use first 3 significant words
                pattern = r"(?i)\b" + r"\s+".join(re.escape(w) for w in words[:3]) + r"\b"
            new_cats[item] = {
                "patterns": [pattern],
                "color": colors[i % len(colors)]
            }
        data["categories"] = new_cats
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"FIXED: {name} -- {len(new_cats)} categories converted")
    else:
        print(f"SKIP:  {name} -- already a dict")
