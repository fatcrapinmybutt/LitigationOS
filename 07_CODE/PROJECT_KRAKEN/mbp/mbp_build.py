#!/usr/bin/env python3
"""THEMANBEARPIG v7 — Unified Build Pipeline
═══════════════════════════════════════════════
Usage:
  python mbp_build.py data        # Rebuild graph data from DB
  python mbp_build.py html        # Rebuild HTML + data
  python mbp_build.py exe         # Full pipeline: data → HTML → .exe
  python mbp_build.py stats       # Show current data stats
  python mbp_build.py open        # Open HTML in browser
  python mbp_build.py launch      # Launch via pywebview
  python mbp_build.py judicial    # Rebuild judicial universe data only
  python mbp_build.py all         # Everything: data + HTML + judicial + exe

Build chain:
  litigation_context.db → build_manbearpig_v7.py → HTML + JSON → PyInstaller → .exe
"""
import subprocess, sys, os, json, sqlite3, shutil
from pathlib import Path
from datetime import date

# ═══════════════ PATHS ═══════════════
REPO = Path(r"C:\Users\andre\LitigationOS")
DB = REPO / "litigation_context.db"
BUILDER = Path(r"D:\LitigationOS_tmp\build_manbearpig_v7.py")
WORKSPACE = REPO / "12_WORKSPACE" / "THEMANBEARPIG_v7"
HTML = WORKSPACE / "THEMANBEARPIG_v7.html"
JSON_DATA = WORKSPACE / "graph_data_v7.json"
BLUEPRINT_DIR = Path(r"D:\LitigationOS_tmp\blueprint_build")
SPEC = BLUEPRINT_DIR / "THEMANBEARPIG.spec"
LAUNCHER = BLUEPRINT_DIR / "adversary_blueprint.py"
DESKTOP_EXE = Path(r"C:\Users\andre\Desktop\THEMANBEARPIG.exe")
SEP_DATE = date(2025, 7, 29)

def sep_days():
    return (date.today() - SEP_DATE).days

def banner(msg):
    w = max(len(msg) + 4, 50)
    print(f"\n{'═'*w}")
    print(f"  {msg}")
    print(f"{'═'*w}\n")

def run(cmd, cwd=None):
    print(f"  → {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    if r.returncode != 0:
        print(f"  ✗ FAILED (exit {r.returncode})")
        sys.exit(r.returncode)
    print(f"  ✓ OK")
    return r

def stats():
    """Show current data stats from DB + graph file."""
    banner(f"MANBEARPIG Stats — Separation Day {sep_days()}")
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA busy_timeout=30000")
    tables = {
        "evidence_quotes": "Core evidence",
        "authority_chains_v2": "Citation chains",
        "timeline_events": "Timeline",
        "impeachment_matrix": "Impeachment",
        "contradiction_map": "Contradictions",
        "judicial_violations": "Judicial violations",
        "berry_mcneill_intelligence": "Cartel intel",
        "police_reports": "Police reports",
        "weapon_chains": "Weapon chains",
    }
    total = 0
    for tbl, desc in tables.items():
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
            total += cnt
            print(f"  {desc:30s} {cnt:>10,}")
        except Exception:
            print(f"  {desc:30s} {'N/A':>10}")
    print(f"  {'─'*42}")
    print(f"  {'TOTAL':30s} {total:>10,}")
    conn.close()

    if JSON_DATA.exists():
        with open(JSON_DATA) as f:
            d = json.load(f)
        print(f"\n  Graph: {d.get('nodes',0)} nodes × {d.get('links',0)} links × {len(d.get('layers',[]))} layers")
        print(f"  Renderer: {d.get('renderer','unknown')}")
        print(f"  Version: {d.get('version','unknown')}")
    if HTML.exists():
        sz = HTML.stat().st_size / 1024 / 1024
        print(f"  HTML: {sz:.2f} MB")
    if DESKTOP_EXE.exists():
        sz = DESKTOP_EXE.stat().st_size / 1024 / 1024
        mod = date.fromtimestamp(DESKTOP_EXE.stat().st_mtime)
        print(f"  EXE: {sz:.1f} MB (built {mod})")

def build_data():
    """Rebuild graph data + HTML from litigation_context.db."""
    banner("Phase 1: Build Graph Data + HTML from DB")
    run(f'python -I "{BUILDER}"')
    if JSON_DATA.exists():
        with open(JSON_DATA) as f:
            d = json.load(f)
        print(f"  Generated: {d.get('nodes',0)} nodes × {d.get('links',0)} links")

def build_exe():
    """Package HTML into standalone .exe via PyInstaller."""
    banner("Phase 2: PyInstaller → THEMANBEARPIG.exe")
    if not HTML.exists():
        print("  ✗ HTML not found — run 'data' first")
        sys.exit(1)
    run(f'pyinstaller "{SPEC}" --clean --distpath "{BLUEPRINT_DIR}\\dist" --workpath "{BLUEPRINT_DIR}\\build"',
        cwd=str(BLUEPRINT_DIR))
    built = BLUEPRINT_DIR / "dist" / "THEMANBEARPIG.exe"
    if built.exists():
        shutil.copy2(str(built), str(DESKTOP_EXE))
        sz = DESKTOP_EXE.stat().st_size / 1024 / 1024
        print(f"  ✓ Deployed to Desktop: {sz:.1f} MB")

def build_judicial():
    """Rebuild judicial universe data summary."""
    banner("Phase 3: Judicial Universe Data Refresh")
    conn = sqlite3.connect(str(DB))
    conn.execute("PRAGMA busy_timeout=30000")

    # Violation breakdown
    rows = conn.execute("""
        SELECT violation_type, COUNT(*) cnt, ROUND(AVG(severity),1) avg_s
        FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC
    """).fetchall()
    print("  Judicial Violations by Type:")
    for vt, cnt, sev in rows[:10]:
        print(f"    {vt:30s} {cnt:>5} (avg sev {sev})")

    # Cartel connections
    rows = conn.execute("""
        SELECT connection_type, COUNT(*) cnt
        FROM berry_mcneill_intelligence GROUP BY connection_type ORDER BY cnt DESC
    """).fetchall()
    print(f"\n  Berry-McNeill Cartel Intel ({sum(c for _,c in rows)} total):")
    for ct, cnt in rows:
        print(f"    {ct:30s} {cnt:>5}")

    conn.close()

def open_html():
    """Open the visualization in default browser."""
    if HTML.exists():
        os.startfile(str(HTML))
        print(f"  Opened {HTML}")
    else:
        print("  ✗ HTML not found — run 'data' first")

def launch_pywebview():
    """Launch via pywebview (native window)."""
    banner("Launching THEMANBEARPIG via pywebview")
    if not HTML.exists():
        print("  ✗ HTML not found — run 'data' first")
        sys.exit(1)
    run(f'python -I "{LAUNCHER}"', cwd=str(BLUEPRINT_DIR))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    cmds = {
        'data': build_data,
        'html': build_data,
        'exe': lambda: (build_data(), build_exe()),
        'stats': stats,
        'open': open_html,
        'launch': launch_pywebview,
        'judicial': build_judicial,
        'all': lambda: (build_data(), build_judicial(), build_exe()),
    }
    if cmd == 'help' or cmd not in cmds:
        print(__doc__)
        sys.exit(0)
    cmds[cmd]() if callable(cmds[cmd]) else cmds[cmd]
