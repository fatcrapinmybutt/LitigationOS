"""List Desktop files with sizes, identify what needs reading."""
import os
desktop = r"C:\Users\andre\Desktop"

already_read = {
    "listofgoodfiles.txt",           # partial (100/10524 lines)
    "CHAT_WEAPONS_SUMMARY.txt",      # full
    "emiklys fulings.txt",           # full (462 lines)
    "KAL_SESSION_RESULTS.txt",       # full (316 lines)
    "2025-0000002760-CZ.md",         # full (416 lines)
    "KAL_RAW_PPO_OUTPUT.txt",        # partial (100 lines)
    "COPILOTCHATv7.txt",             # partial (80/3506 lines)
}

files = []
for f in os.listdir(desktop):
    fp = os.path.join(desktop, f)
    if os.path.isfile(fp):
        sz = os.path.getsize(fp)
        status = "✅ READ" if f in already_read else "📋 UNREAD"
        if f in already_read and f in ("listofgoodfiles.txt", "KAL_RAW_PPO_OUTPUT.txt", "COPILOTCHATv7.txt"):
            status = "⚠️ PARTIAL"
        files.append((f, sz, status))

files.sort(key=lambda x: x[1], reverse=True)

print(f"{'File':<55} {'Size':>10} {'Status'}")
print("=" * 85)
for f, sz, st in files:
    if sz > 1_000_000:
        szstr = f"{sz/1_000_000:.1f} MB"
    elif sz > 1_000:
        szstr = f"{sz/1_000:.1f} KB"
    else:
        szstr = f"{sz} B"
    print(f"{f:<55} {szstr:>10} {st}")

unread = [f for f, _, st in files if st == "📋 UNREAD"]
partial = [f for f, _, st in files if st == "⚠️ PARTIAL"]
print(f"\nSummary: {len(files)} total, {len(unread)} unread, {len(partial)} partial")
