import os
import datetime

log_dir = "F:/FRED-PRIME/AppClose_Logs"
output_dir = "F:/FRED-PRIME/Violations_Reports"
os.makedirs(output_dir, exist_ok=True)

keywords = [
    "refused", "denied", "withheld", "canceled", "blocked", "ignored",
    "no show", "missed exchange", "PPO", "police", "alienation", "custody",
    "dad", "father", "court order", "judge", "emergency", "threat", "Ron Berry"
]

results = []

print("📖 Scanning AppClose logs for potential violations...")

for file in os.listdir(log_dir):
    if file.lower().endswith(".txt"):
        path = os.path.join(log_dir, file)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                for kw in keywords:
                    if kw.lower() in line.lower():
                        results.append(f"{file} | Line {i+1}: {line.strip()}")

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = os.path.join(output_dir, f"ViolationScan_{timestamp}.txt")
with open(out_path, "w", encoding="utf-8") as out:
    if results:
        out.write("\n".join(results))
    else:
        out.write("✅ No violations or keywords detected.")

print(f"🔎 Scan complete. Results saved to: {out_path}")
