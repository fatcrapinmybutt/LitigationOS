#!/usr/bin/env python
from __future__ import annotations
import shutil, subprocess, sys
from pathlib import Path
import csv

HERE = Path(__file__).resolve().parent

def run(cmd, cwd=None):
    print(">>", " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    print(p.stdout)
    if p.returncode != 0:
        print(p.stderr)
        raise SystemExit(p.returncode)

def main():
    import py_compile
    py_compile.compile(str(HERE / "ai_organizer_stack.py"), doraise=True)
    py_compile.compile(str(HERE / "download_models.py"), doraise=True)
    py_compile.compile(str(HERE / "plan_validator.py"), doraise=True)
    py_compile.compile(str(HERE / "undo_last.py"), doraise=True)
    py_compile.compile(str(HERE / "mbp_worldfirst_builder.py"), doraise=True)
    print("[OK] py_compile passed")

    work = HERE / "_SELFTEST_WORK"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    nested = work / "A" / "B" / "C"
    nested.mkdir(parents=True, exist_ok=True)

    (nested / "doc1.txt").write_text("hello world", encoding="utf-8")
    (nested / "note.md").write_text("# title", encoding="utf-8")
    (work / "root.pdf").write_bytes(b"%PDF-1.4\n%FAKEPDF\n")

    run_root = work / "RUNS"
    run_root.mkdir(parents=True, exist_ok=True)

    cfg_path = work / "config.yaml"
    cfg_text = (HERE / "config.yaml").read_text(encoding="utf-8")

    # Use POSIX paths for sandbox self-test
    run_root_s = str(run_root)
    work_s = str(work)

    cfg_text = cfg_text.replace("run_root: 'F:\\LitigationOS\\_OrganizeAI'", f"run_root: '{run_root_s}'")
    cfg_text = cfg_text.replace("  - 'F:\\LitigationOS\\INBOX'", f"  - '{work_s}'")
    cfg_text = cfg_text.replace("move_mode: 'move'", "move_mode: 'copy'")
    cfg_path.write_text(cfg_text, encoding="utf-8")

    # PLAN
    run([sys.executable, str(HERE / "ai_organizer_stack.py"), "--config", str(cfg_path), "--mode", "plan"])
    last_run = run_root / "LAST_RUN.txt"
    if not last_run.exists():
        raise SystemExit("[FAIL] LAST_RUN.txt not created")
    run_dir = Path(last_run.read_text(encoding="utf-8").strip())
    plan_csv = run_dir / "plan.csv"
    if not plan_csv.exists():
        raise SystemExit("[FAIL] plan.csv not created")

    rows = list(csv.DictReader(plan_csv.open("r", encoding="utf-8")))
    if len(rows) < 2:
        raise SystemExit("[FAIL] plan.csv too small")
    print("[OK] plan.csv generated:", len(rows), "rows")

    # VALIDATE
    run([sys.executable, str(HERE / "plan_validator.py"), "--plan", str(plan_csv)])

    # APPLY (COPY)
    run([sys.executable, str(HERE / "ai_organizer_stack.py"), "--config", str(cfg_path), "--mode", "apply", "--run_dir", str(run_dir)])

    target = run_dir / "_TARGET"
    if not target.exists():
        raise SystemExit("[FAIL] _TARGET missing after apply")
    print("[OK] apply created target")

    print("\nSELF TEST PASSED")

if __name__ == "__main__":
    main()
