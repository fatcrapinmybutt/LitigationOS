import os, re

eu_path = r"C:\Users\andre\Music\encyclopediaUNIVERSE.txt"
with open(eu_path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

lines = text.split("\n")
sections = []
keywords = ["parental alienation", "best interest", "custody", "parenting time",
            "mcl 722.23", "mcl 722.27", "mcr 3.207", "ppo", "contempt",
            "disqualif", "judicial misconduct", "ex parte", "due process",
            "separation", "child separation", "mcneill", "watson", "pigors",
            "emergency motion", "deny", "denied", "without hearing", "no notice",
            "canon", "recuse", "bias", "prejudice", "alienat"]

for i, line in enumerate(lines):
    lower = line.lower()
    if any(k in lower for k in keywords):
        start = max(0, i-1)
        end = min(len(lines), i+3)
        chunk = " ".join(lines[start:end]).strip()
        if len(chunk) > 50:
            sections.append(chunk[:500])

seen = set()
unique = []
for s in sections:
    key = s[:80]
    if key not in seen:
        seen.add(key)
        unique.append(s)

print(f"Found {len(unique)} key case narrative segments", flush=True)
for s in unique[:50]:
    print(f"  > {s[:250]}", flush=True)
    print(flush=True)