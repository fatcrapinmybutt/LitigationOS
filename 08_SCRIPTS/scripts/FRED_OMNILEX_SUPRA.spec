
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['FRED_OMNILEX_SUPRA_MAIN.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('DARS_GENERATOR.py', '.'),
        ('ZIP_OUTPUT_INJECTOR.py', '.'),
        ('FRED_OMNILEX_SUPRA_MAIN.py', '.')
    ],
    hiddenimports=[],
    hookspath=[],
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
    name='FRED_OMNILEX_SUPRA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FRED_OMNILEX_SUPRA'
)
