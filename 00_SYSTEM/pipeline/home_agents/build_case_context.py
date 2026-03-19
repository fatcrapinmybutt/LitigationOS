import os, re, json

# Read top evidence files for case context
files = [
    r"C:\Users\andre\Scans\discovery\encyclopediaUNIVERSE.txt",
    r"C:\Users\andre\Scans\JTC_MSC_BINDER_EXTRACTED.md",
    r"C:\Users\andre\Scans\discovery\WMDI1.txt",
]

keywords = ["parental alienation", "best interest", "custody", "parenting time",
            "mcl 722.23", "mcl 722.27", "mcr 3.207", "ppo", "contempt",
            "disqualif", "judicial misconduct", "ex parte", "due process",
            "child separation", "denied", "without hearing", "no notice",
            "canon", "recuse", "bias", "prejudice", "emergency", "father",
            "overnight", "supervised", "unsupervised", "bonding", "attachment",
            "harm to child", "emotional abuse", "neglect", "welfare", "safety",
            "violation of rights", "constitutional", "14th amendment", "first amendment",
            "abuse of discretion", "clear error", "de novo", "appeal"]

all_segments = []

for fpath in files:
    if not os.path.exists(fpath):
        continue
    fname = os.path.basename(fpath)
    print(f"Reading {fname}...", flush=True)
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    lines = text.split("\n")
    for i, line in enumerate(lines):
        lower = line.lower()
        if any(k in lower for k in keywords):
            start = max(0, i-1)
            end = min(len(lines), i+4)
            chunk = " ".join(l.strip() for l in lines[start:end] if l.strip())
            if len(chunk) > 60:
                all_segments.append({"source": fname, "line": i+1, "text": chunk[:600]})

# Deduplicate by first 100 chars
seen = set()
unique = []
for s in all_segments:
    key = s["text"][:100]
    if key not in seen:
        seen.add(key)
        unique.append(s)

print(f"\nTotal unique case segments: {len(unique)}", flush=True)

# Save for document generation
with open(r"D:\TEMP\case_context.json", "w", encoding="utf-8") as f:
    json.dump(unique, f, indent=2)

# Print samples by category
categories = {
    "PARENTAL_ALIENATION": ["parental alienation", "alienat"],
    "CUSTODY_PT": ["custody", "parenting time", "overnight", "supervised", "unsupervised"],
    "JUDICIAL_MISCONDUCT": ["judicial misconduct", "canon", "recuse", "disqualif", "bias", "prejudice"],
    "DUE_PROCESS": ["due process", "without hearing", "no notice", "ex parte", "denied"],
    "BEST_INTEREST": ["best interest", "mcl 722.23", "bonding", "attachment", "welfare"],
    "PPO_CONTEMPT": ["ppo", "contempt", "mcl 600.2950"],
    "CONSTITUTIONAL": ["constitutional", "14th amendment", "first amendment", "violation of rights"],
    "APPELLATE": ["appeal", "clear error", "de novo", "abuse of discretion"],
}

for cat, kws in categories.items():
    matches = [s for s in unique if any(k in s["text"].lower() for k in kws)]
    print(f"\n=== {cat} ({len(matches)} segments) ===", flush=True)
    for s in matches[:5]:
        print(f"  [{s['source']}:{s['line']}] {s['text'][:200]}", flush=True)
        print(flush=True)

print("DONE", flush=True)