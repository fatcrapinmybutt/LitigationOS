import os
from pathlib import Path

try:
    from PyInstaller.utils.hooks import collect_submodules
    from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
except ModuleNotFoundError as e:
    print("ERROR: PyInstaller is not installed or not available in this environment.")
    print(str(e))
    print("Please run this script in a local Python environment with PyInstaller installed.")
    raise SystemExit(1)

block_cipher = None

source_file = 'FRED_Processor_GUI.py'
source_path = Path(__file__).parent.resolve()
full_source_path = source_path / source_file

if not full_source_path.exists():
    raise FileNotFoundError(f"Missing {source_file} in expected directory: {source_path}")

# Dynamically collect all submodules for docx
hiddenimports = collect_submodules('docx')

print("[✔] Starting analysis...")
a = Analysis(
    [str(full_source_path)],
    pathex=[str(source_path)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

print("[✔] Building PYZ stage...")
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

print("[✔] Building EXE...")
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    exclude_binaries=False,
    name='FRED_Master_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='FRED_Master_GUI.ico',
    onefile=True
)

print("[✔] Collecting final build...")
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FRED_Master_GUI'
)

with open("build_complete.log", "w") as log:
    log.write("FRED_Master_GUI.exe successfully built.")
    print("[✔] Build log written to build_complete.log")
