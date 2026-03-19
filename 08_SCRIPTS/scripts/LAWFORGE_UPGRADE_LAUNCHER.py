#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
LAWFORGE_UPGRADE_LAUNCHER.py
Purpose:
1) Upgrade an existing FREDPRIME/LAWFORGE repo in-place with a plugin/core system.
2) Append missing "cores" as modular plugins.
3) Provide a single CLI to run common litigation tasks.
4) Optionally build a one-file .exe via PyInstaller.

This script is self-contained. It does NOT alter legal text or case data.
It creates a lightweight plugin architecture and a registry for extensibility.

Tested on Python 3.10+.
'''
import os, sys, json, subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent / 'fredprime-legal-system-main'
PLUGINS_DIR  = PROJECT_ROOT / 'plugins'
REGISTRY     = PROJECT_ROOT / 'plugins' / 'registry.json'
VENV_DIR     = PROJECT_ROOT / '.venv'

ADDON_PACKAGES = [
    'typer>=0.12.3', 'rich>=13.7.1', 'python-dotenv>=1.0.1',
    'pydantic>=2.8.2', 'watchdog>=4.0.2', 'fastapi>=0.112.2',
    'uvicorn>=0.30.5', 'pyinstaller>=6.9.0',
]

def sh(cmd, cwd=None):
    print(f'[RUN] {cmd}')
    return subprocess.run(cmd, cwd=cwd, shell=True, check=False)

def is_windows():
    return os.name == 'nt'

def venv_python():
    return VENV_DIR / ('Scripts/python.exe' if is_windows() else 'bin/python')
def venv_pip():
    return VENV_DIR / ('Scripts/pip.exe' if is_windows() else 'bin/pip')

def load_requirements():
    req = PROJECT_ROOT / 'requirements.txt'
    if not req.exists():
        return []
    return [l.strip() for l in req.read_text(encoding='utf-8', errors='ignore').splitlines() if l.strip() and not l.strip().startswith('#')]

def cmd_bootstrap():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    if not VENV_DIR.exists():
        sh(f"{sys.executable} -m venv '{VENV_DIR}'")
    py = str(venv_python()); pip = str(venv_pip())
    sh(f"'{py}' -m pip install --upgrade pip")
    reqs = load_requirements()
    if reqs:
        (PROJECT_ROOT / '_temp_requirements.txt').write_text('\n'.join(reqs), encoding='utf-8')
        sh(f"'{pip}' install -r '{PROJECT_ROOT / '_temp_requirements.txt'}'")
    sh(f"'{pip}' install " + ' '.join(ADDON_PACKAGES))
    print('[*] Bootstrap complete')

TEMPLATE_PLUGIN = '''# -*- coding: utf-8 -*-
from typing import Dict, Any
def run(**kwargs) -> Dict[str, Any]:
    return {'ok': True, 'message': 'Template plugin executed', 'kwargs': kwargs}
'''
DEFAULT_PLUGINS = {
 'core_scan': '''from typing import Dict, Any
from pathlib import Path

def run(**kwargs) -> Dict[str, Any]:
    root = Path(kwargs.get('scan_root', '.'))
    exts = kwargs.get('exts', ['.pdf','.png','.jpg','.jpeg','.tif','.tiff','.docx','.txt'])
    found = []
    for p in root.rglob('*'):
        if p.is_file() and (p.suffix.lower() in exts or '*' in exts):
            found.append(p.as_posix())
    return {'ok': True, 'count': len(found), 'sample': found[:15]}
''',
 'core_zip_bundler': '''from typing import Dict, Any
from pathlib import Path
import subprocess, sys

def run(**kwargs) -> Dict[str, Any]:
    project_root = Path(kwargs.get('project_root', '.')).resolve()
    target = project_root / 'Build_And_Upload_Master_Litigation_Pack_Z.py'
    if not target.exists():
        return {'ok': False, 'error': f'Missing {target.name}'}
    args = kwargs.get('args', [])
    cmd = f"{sys.executable} '{target}' " + ' '.join(args)
    rc = subprocess.run(cmd, shell=True).returncode
    return {'ok': rc == 0, 'returncode': rc, 'cmd': cmd}
''',
 'core_zip_validate': '''from typing import Dict, Any
from pathlib import Path
import subprocess, sys

def run(**kwargs) -> Dict[str, Any]:
    project_root = Path(kwargs.get('project_root', '.')).resolve()
    target = project_root / 'ZIP_VALIDATOR.py'
    if not target.exists():
        return {'ok': False, 'error': f'Missing {target.name}'}
    cmd = f"{sys.executable} '{target}'"
    rc = subprocess.run(cmd, shell=True).returncode
    return {'ok': rc == 0, 'returncode': rc, 'cmd': cmd}
''',
 'core_gdrive_sync': '''from typing import Dict, Any
from pathlib import Path
import subprocess, sys

def run(**kwargs) -> Dict[str, Any]:
    project_root = Path(kwargs.get('project_root', '.')).resolve()
    target = project_root / 'gdrive_sync.py'
    if not target.exists():
        return {'ok': False, 'error': f'Missing {target.name}'}
    args = kwargs.get('args', [])
    cmd = f"{sys.executable} '{target}' " + ' '.join(args)
    rc = subprocess.run(cmd, shell=True).returncode
    return {'ok': rc == 0, 'returncode': rc, 'cmd': cmd}
''',
 'core_organize_drive': '''from typing import Dict, Any
from pathlib import Path
import subprocess, sys

def run(**kwargs) -> Dict[str, Any]:
    project_root = Path(kwargs.get('project_root', '.')).resolve()
    target = project_root / 'organize_drive.py'
    if not target.exists():
        return {'ok': False, 'error': f'Missing {target.name}'}
    args = kwargs.get('args', [])
    cmd = f"{sys.executable} '{target}' " + ' '.join(args)
    rc = subprocess.run(cmd, shell=True).returncode
    return {'ok': rc == 0, 'returncode': rc, 'cmd': cmd}
''',
}

def cmd_install_plugins():
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY.exists():
        REGISTRY.write_text(json.dumps({'plugins': {}}, indent=2))
    for name, body in DEFAULT_PLUGINS.items():
        p = PLUGINS_DIR / f'{name}.py'
        if not p.exists():
            p.write_text(body, encoding='utf-8')
        reg = json.loads(REGISTRY.read_text(encoding='utf-8'))
        reg['plugins'][name] = {'module': f'plugins.{name}', 'enabled': True}
        REGISTRY.write_text(json.dumps(reg, indent=2))
    t = PLUGINS_DIR / '_template.py'
    if not t.exists():
        t.write_text(TEMPLATE_PLUGIN, encoding='utf-8')
    print('[*] Plugin system ready')

def import_plugin(mod_path: str):
    import importlib
    return importlib.import_module(mod_path)

def run_plugin(name: str, **kwargs):
    if not REGISTRY.exists():
        raise SystemExit('Registry missing; run install-plugins first.')
    reg = json.loads(REGISTRY.read_text(encoding='utf-8'))
    if name not in reg.get('plugins', {}):
        raise SystemExit(f"Plugin '{name}' not registered.")
    meta = reg['plugins'][name]
    if not meta.get('enabled', True):
        raise SystemExit(f"Plugin '{name}' is disabled.")
    mod = import_plugin(meta['module'])
    if not hasattr(mod, 'run'):
        raise SystemExit(f"Plugin '{name}' missing run()")
    return mod.run(**kwargs)

def cmd_list():
    if not REGISTRY.exists():
        print('No registry found. Run: python LAWFORGE_UPGRADE_LAUNCHER.py install-plugins')
        return
    reg = json.loads(REGISTRY.read_text(encoding='utf-8'))
    print(json.dumps(reg, indent=2))

def cmd_build_exe():
    py = str(venv_python()); pip = str(venv_pip())
    sh(f"'{pip}' install pyinstaller")
    spec_name = 'LAWFORGE_UPGRADE_LAUNCHER'
    cmd = f"'{py}' -m PyInstaller --noconsole --onefile --name {spec_name} '{Path(__file__).resolve()}'"
    rc = sh(cmd).returncode
    if rc == 0:
        dist = Path.cwd() / 'dist' / (spec_name + ('.exe' if is_windows() else ''))
        print(f'[*] Built: {dist}')
    else:
        print('[!] Build failed')

def cmd_menu():
    options = [
        ('Bootstrap env (venv + deps)', 'bootstrap'),
        ('Install/refresh plugin system', 'install-plugins'),
        ('List plugins', 'list'),
        ('Scan files (core_scan)', 'run core_scan'),
        ('Build Master Litigation ZIP (core_zip_bundler)', 'run core_zip_bundler'),
        ('Validate ZIP bundle (core_zip_validate)', 'run core_zip_validate'),
        ('Sync Google Drive (core_gdrive_sync)', 'run core_gdrive_sync'),
        ('Organize Drive (core_organize_drive)', 'run core_organize_drive'),
        ('Build EXE (pyinstaller)', 'build-exe'),
        ('Quit', 'quit'),
    ]
    while True:
        print('\n=== LAWFORGE Launcher ===')
        for i, (label, _) in enumerate(options, 1):
            print(f'{i}. {label}')
        choice = input('Select: ').strip()
        try:
            idx = int(choice) - 1
        except:
            continue
        if idx < 0 or idx >= len(options):
            continue
        label, cmd = options[idx]
        if cmd == 'quit':
            break
        elif cmd == 'bootstrap':
            cmd_bootstrap()
        elif cmd == 'install-plugins':
            cmd_install_plugins()
        elif cmd == 'list':
            cmd_list()
        elif cmd.startswith('run '):
            name = cmd.split(' ',1)[1]
            if name == 'core_scan':
                scan_root = input('Scan root path [.]: ').strip() or '.'
                print(json.dumps(run_plugin('core_scan', scan_root=Path(scan_root).resolve(), exts='*'), indent=2))
            else:
                print(json.dumps(run_plugin(name, project_root=str(PROJECT_ROOT)), indent=2))
        elif cmd == 'build-exe':
            cmd_build_exe()
        else:
            print('Unknown selection.')

def main():
    import argparse
    ap = argparse.ArgumentParser(description='LAWFORGE Upgrade + Launcher')
    ap.add_argument('command', nargs='?', default='menu', help='bootstrap | install-plugins | list | run | build-exe | menu')
    ap.add_argument('plugin', nargs='?', help="plugin name for 'run'")
    ap.add_argument('--scan-root', default='.')
    args, rest = ap.parse_known_args()
    if args.command == 'bootstrap':
        cmd_bootstrap()
    elif args.command == 'install-plugins':
        cmd_install_plugins()
    elif args.command == 'list':
        cmd_list()
    elif args.command == 'run':
        if not args.plugin:
            raise SystemExit("Specify plugin name after 'run'")
        if args.plugin == 'core_scan':
            out = run_plugin('core_scan', scan_root=Path(args.scan_root).resolve(), exts='*')
        else:
            out = run_plugin(args.plugin, project_root=str(PROJECT_ROOT), args=rest)
        print(json.dumps(out, indent=2))
    elif args.command == 'build-exe':
        cmd_build_exe()
    else:
        cmd_menu()

if __name__ == '__main__':
    main()
