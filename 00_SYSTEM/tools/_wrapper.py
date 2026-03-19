import subprocess, sys, os
os.environ["PYTHONUTF8"] = "1"
r = subprocess.run([sys.executable, "organize_engine.py", "--dry-run"], 
    cwd=r"C:\Users\andre\LitigationOS\00_SYSTEM\tools",
    capture_output=True, text=True, timeout=300)
with open(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_dryrun_out.txt", "w") as f:
    f.write(r.stdout + "\n" + r.stderr)
print("Output written to _dryrun_out.txt")
