#!/usr/bin/env python3
import os
import sys
import time

os.environ["PYTHONUTF8"] = "1"

output_file = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_import_debug.txt"

def log(msg):
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"{time.time()}: {msg}\n")
        f.flush()

# Clear previous
with open(output_file, "w", encoding="utf-8") as f:
    f.write("")

log("Starting import debug script")
log(f"CWD: {os.getcwd()}")
log("About to change directory...")

try:
    os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")
    log(f"Changed CWD to: {os.getcwd()}")
except Exception as e:
    log(f"ERROR changing CWD: {e}")

log("About to import safe_shell...")

try:
    import safe_shell
    log("SUCCESS: safe_shell imported")
except Exception as e:
    log(f"ERROR importing safe_shell: {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())
    sys.exit(1)

log("Script completed successfully")
