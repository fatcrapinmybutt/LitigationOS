# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\andre\\LitigationOS\\11_CODE\\litigationos\\src\\litigationos\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\andre\\LitigationOS\\11_CODE\\litigationos\\src\\litigationos\\db\\schema.sql', 'litigationos/db/'), ('C:\\Users\\andre\\LitigationOS\\11_CODE\\litigationos\\src\\litigationos\\plugins', 'litigationos/plugins/'), ('C:\\Users\\andre\\LitigationOS\\11_CODE\\litigationos\\data', 'data/'), ('C:\\Users\\andre\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\customtkinter', 'customtkinter/')],
    hiddenimports=['customtkinter', 'pydantic', 'jinja2', 'jinja2.ext', 'docx', 'reportlab', 'reportlab.lib.pagesizes', 'reportlab.platypus', 'rich', 'typer', 'pypdf', 'litigationos.engines.ai', 'litigationos.engines.court_rules', 'litigationos.engines.deadline', 'litigationos.engines.document', 'litigationos.engines.evidence', 'litigationos.engines.filing', 'litigationos.engines.rag', 'litigationos.engines.settings', 'litigationos.gui.app', 'litigationos.gui.dashboard', 'litigationos.gui.case_manager', 'litigationos.gui.filing_manager', 'litigationos.gui.filing_wizard', 'litigationos.gui.evidence_browser', 'litigationos.gui.evidence_map', 'litigationos.gui.document_editor', 'litigationos.gui.deadline_dashboard', 'litigationos.gui.calendar_view', 'litigationos.gui.timeline_view', 'litigationos.gui.settings_screen', 'litigationos.db.connection', 'litigationos.db.seed', 'litigationos.config', 'litigationos.plugins', 'litigationos.plugins.michigan'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'scipy', 'pandas', 'numpy', 'matplotlib', 'pytest', 'chromadb', 'ollama', 'IPython', 'notebook', 'numba', 'llvmlite', 'pyarrow', 'sqlalchemy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LitigationOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LitigationOS',
)
