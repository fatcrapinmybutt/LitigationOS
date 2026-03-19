import sys, os, traceback

outpath = r"C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt"

try:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')
    os.environ["PYTHONUTF8"] = "1"

    # Redirect all output to a file to avoid stdout deadlock
    import io
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    # Change to script directory and import
    os.chdir(r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")
    sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM\tools")

    from organize_engine import run_organize
    moved, unclassified, errors = run_organize(dry_run=False)

    sys.stdout = old_stdout
    output = buf.getvalue()

    with open(outpath, "w", encoding="utf-8", errors="replace") as f:
        f.write(output)
        f.write(f"\n\nFINAL: moved={moved}, unclassified={unclassified}, errors={errors}\n")

    print(f"Done. Results at {outpath}")

except Exception:
    # Restore stdout if possible
    try:
        sys.stdout = sys.__stdout__
    except Exception:
        pass
    tb = traceback.format_exc()
    with open(outpath, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"EXCEPTION:\n{tb}\n")
    print(f"ERROR — see {outpath}")
    print(tb)
