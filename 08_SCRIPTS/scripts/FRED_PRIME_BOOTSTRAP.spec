# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['FRED_PRIME_SELF_BOOTSTRAP_SYSTEM.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FRED-PRIME-BOOTSTRAP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False to hide the console window
    version='FRED_PRIME_VERSION_FILE.txt',
    icon='FRED_ICON.ico'  # Optional: provide your own FRED_ICON.ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FRED-PRIME-BOOTSTRAP'
)
