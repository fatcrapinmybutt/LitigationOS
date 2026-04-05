# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['adversary_blueprint.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\andre\\LitigationOS\\12_WORKSPACE\\THEMANBEARPIG_v7\\THEMANBEARPIG_v7.html', '.'), ('C:\\Users\\andre\\LitigationOS\\12_WORKSPACE\\THEMANBEARPIG_v7\\graph_data_v7.json', '.')],
    hiddenimports=['clr'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='THEMANBEARPIG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
