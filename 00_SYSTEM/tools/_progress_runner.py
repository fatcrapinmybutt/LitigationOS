#!/usr/bin/env python3
import os
import sys
import time

os.environ["PYTHONUTF8"] = "1"
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

output_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_progress_output.txt"

def write_log(msg):
    """Write to file with flush."""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()

# Clear previous output
with open(output_file, "w", encoding="utf-8") as f:
    f.write("")

write_log("=" * 70)
write_log("STARTING COMMAND EXECUTION")
write_log(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
write_log("=" * 70)

write_log("\n[1/3] Importing safe_shell...")
try:
    import safe_shell
    write_log("✅ safe_shell imported successfully")
except Exception as e:
    write_log(f"❌ Failed to import safe_shell: {e}")
    sys.exit(1)

write_log("\n" + "=" * 70)
write_log("COMMAND 1: env-check")
write_log("=" * 70)

try:
    write_log("[Running] env_check()...")
    result = safe_shell.env_check()
    write_log(f"✅ env_check completed")
    if result:
        write_log(f"Result: {result}")
except Exception as e:
    write_log(f"❌ env_check failed: {type(e).__name__}: {e}")

write_log("\n" + "=" * 70)
write_log("COMMAND 2: shadow-audit")
write_log("=" * 70)

try:
    write_log("[Running] shadow_audit()...")
    result = safe_shell.shadow_audit()
    write_log(f"✅ shadow_audit completed")
    if result:
        write_log(f"Result count: {len(result)}")
except Exception as e:
    write_log(f"❌ shadow_audit failed: {type(e).__name__}: {e}")

write_log("\n" + "=" * 70)
write_log("COMMAND 3: check org_agents/__init__.py")
write_log("=" * 70)

try:
    fpath = r"C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py"
    write_log(f"[Running] check_syntax(['{fpath}'])...")
    result = safe_shell.check_syntax([fpath])
    write_log(f"✅ check_syntax completed")
    if result:
        write_log(f"Result: {result}")
except Exception as e:
    write_log(f"❌ check_syntax failed: {type(e).__name__}: {e}")

write_log("\n" + "=" * 70)
write_log("ALL COMMANDS COMPLETED")
write_log(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
write_log("=" * 70)

print(f"Output written to {output_file}")
