import sys, os, traceback
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')
os.environ["PYTHONUTF8"] = "1"
os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")
outpath = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt"
try:
    from organize_engine import run_organize
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    moved, unclassified, errors = run_organize(dry_run=False)
    sys.stdout = old
    output = buf.getvalue()
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(output)
        f.write(f"\nFINAL: moved={moved}, unclassified={unclassified}, errors={errors}\n")
    print(f"SUCCESS: moved={moved}, unclassified={unclassified}, errors={errors}")
    print(f"Full output at: {outpath}")
except Exception:
    tb = traceback.format_exc()
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(f"ERROR:\n{tb}\n")
    print(f"ERROR: {tb}")
