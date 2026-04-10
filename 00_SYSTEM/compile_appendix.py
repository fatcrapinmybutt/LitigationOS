"""Compile all F09 appendix markdown files to PDF via Typst pipeline."""
import subprocess
import sys
from pathlib import Path

appendix_dir = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\GOLDEN_SET\F09_COA_BRIEF\APPENDIX")
pipeline_dir = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines\typst")
pdf_dir = appendix_dir / "PDF"
pdf_dir.mkdir(exist_ok=True)

md_files = sorted(appendix_dir.glob("*.md"))
print(f"Found {len(md_files)} appendix markdown files")

success = 0
failed = 0
for md in md_files:
    print(f"\n  Compiling: {md.name}")
    result = subprocess.run(
        [sys.executable, "-u", "pipeline.py", "--doc", "F09", str(md)],
        cwd=str(pipeline_dir),
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        # Move PDF from F09/PDF/ to APPENDIX/PDF/ 
        default_pdf = appendix_dir.parent / "PDF" / md.with_suffix(".pdf").name
        if default_pdf.exists():
            target = pdf_dir / md.with_suffix(".pdf").name
            import shutil
            shutil.move(str(default_pdf), str(target))
            size_kb = target.stat().st_size / 1024
            print(f"    ✓ {target.name} ({size_kb:.1f} KB)")
            success += 1
        else:
            print(f"    ✓ Compiled (PDF at default location)")
            success += 1
    else:
        failed += 1
        err_lines = result.stderr.strip().split('\n')[-5:]
        print(f"    ✗ FAILED: {' | '.join(err_lines)}")

print(f"\n{'='*50}")
print(f"Results: {success} compiled, {failed} failed out of {len(md_files)}")
