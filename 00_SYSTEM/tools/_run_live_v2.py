"""Direct live runner — all output to file, no stdout tricks."""
import sys, os, traceback

os.environ["PYTHONUTF8"] = "1"
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

RESULT = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt"

class TeeWriter:
    """Write to both console and file simultaneously."""
    def __init__(self, filepath):
        self.file = open(filepath, "w", encoding="utf-8", errors="replace")
        self.console = sys.__stdout__
    def write(self, s):
        try:
            self.console.write(s)
            self.console.flush()
        except Exception:
            pass
        self.file.write(s)
    def flush(self):
        try: self.console.flush()
        except Exception: pass
        self.file.flush()

try:
    tee = TeeWriter(RESULT)
    sys.stdout = tee
    sys.stderr = tee

    from organize_engine import run_organize
    moved, unclassified, errors = run_organize(dry_run=False)
    print(f"\nFINAL: moved={moved}, unclassified={unclassified}, errors={errors}")
    tee.file.close()

except Exception:
    tb = traceback.format_exc()
    sys.stdout = sys.__stdout__
    print(f"EXCEPTION:\n{tb}")
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write(f"EXCEPTION:\n{tb}\n")
