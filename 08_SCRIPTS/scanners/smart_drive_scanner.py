"""
LitigationOS Smart Drive Scanner v2.0
- Fingerprints directories by content (not just name)
- Detects: Python projects, legal docs, databases, config files, evidence, court filings
- Classifies: litigation code, evidence, court docs, databases, media, archives, trash
- Outputs structured JSON manifest per drive
"""
import os, sys, json, hashlib, sqlite3, time
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# Content fingerprinting rules
FINGERPRINTS = {
    'litigation_code': {
        'files': ['agent_base.py', 'local_ai_engine.py', 'llm_client.py', 'config.py', 'pipeline.py',
                  'court_document_generator.py', 'master_orchestrator.py', 'lexos_server.py'],
        'patterns': ['litigation', 'litigationos', 'pipeline', 'agent', 'lexos'],
        'extensions': {'.py'},
    },
    'legal_documents': {
        'files': ['motion.pdf', 'brief.pdf', 'complaint.pdf', 'order.pdf', 'affidavit.pdf'],
        'patterns': ['motion', 'brief', 'complaint', 'petition', 'affidavit', 'order', 'custody',
                     'parenting', 'filing', 'court', 'judicial', 'mcr', 'mcl', 'foc'],
        'extensions': {'.pdf', '.docx', '.doc', '.rtf'},
    },
    'evidence': {
        'files': [],
        'patterns': ['evidence', 'exhibit', 'deposition', 'testimony', 'discovery', 'subpoena',
                     'shadyoaks', 'shady_oaks', 'watson', 'hoopes', 'mcneill', 'pigors'],
        'extensions': {'.pdf', '.jpg', '.jpeg', '.png', '.mp3', '.mp4', '.wav', '.eml', '.msg'},
    },
    'databases': {
        'files': ['master_index.db', 'litigation_master.db', 'housing_shadyoaks.db', 'autogrow_state.db'],
        'patterns': ['master', 'index', 'litigation'],
        'extensions': {'.db', '.sqlite', '.sqlite3'},
    },
    'web_app': {
        'files': ['package.json', 'index.html', 'app.js', 'server.js', 'next.config.js'],
        'patterns': ['node_modules', 'dist', 'build', '.next'],
        'extensions': {'.js', '.jsx', '.ts', '.tsx', '.html', '.css'},
    },
    'config_infra': {
        'files': ['Dockerfile', 'docker-compose.yml', '.env', 'requirements.txt', 'setup.py'],
        'patterns': ['config', 'deploy', 'infra'],
        'extensions': {'.yml', '.yaml', '.toml', '.ini', '.cfg', '.json'},
    },
    'archives': {
        'files': [],
        'patterns': ['backup', 'archive', 'old', 'copy', 'deprecated'],
        'extensions': {'.zip', '.tar', '.gz', '.7z', '.rar', '.bak'},
    },
    'media_photos': {
        'files': [],
        'patterns': ['photo', 'picture', 'camera', 'screenshot', 'capture'],
        'extensions': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic', '.mp4', '.mov', '.avi'},
    },
}

def classify_directory(dirpath, files_in_dir):
    """Classify a directory by fingerprinting its contents."""
    scores = Counter()
    dir_lower = dirpath.lower()
    
    file_names = [f.lower() for f in files_in_dir]
    file_exts = Counter(os.path.splitext(f)[1].lower() for f in files_in_dir)
    
    for category, fp in FINGERPRINTS.items():
        # Check known filenames
        for known in fp['files']:
            if known.lower() in file_names:
                scores[category] += 10
        # Check directory name patterns
        for pat in fp['patterns']:
            if pat in dir_lower:
                scores[category] += 5
        # Check extension distribution
        for ext in fp['extensions']:
            scores[category] += file_exts.get(ext, 0)
    
    if not scores:
        return 'uncategorized'
    return scores.most_common(1)[0][0]

def scan_drive(drive_letter, max_depth=4):
    """Deep scan a drive, classify every directory."""
    root = f"{drive_letter}:\\"
    if not os.path.exists(root):
        return None
    
    results = {
        'drive': drive_letter,
        'scan_time': datetime.now().isoformat(),
        'total_files': 0,
        'total_dirs': 0,
        'total_size_bytes': 0,
        'categories': defaultdict(lambda: {'dirs': [], 'file_count': 0, 'size_bytes': 0}),
        'databases_found': [],
        'large_files': [],  # > 100MB
        'empty_dirs': [],
        'duplicate_names': defaultdict(list),  # dirs with same name
        'litigationos_roots': [],  # directories that ARE litigationos project roots
    }
    
    SKIP = {'node_modules', '.git', '__pycache__', '.next', 'venv', '.venv', 'dist',
            '$Recycle.Bin', 'System Volume Information', 'Windows', 'Program Files',
            'Program Files (x86)', 'ProgramData', 'Recovery', 'pagefile.sys'}
    
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.replace(root, '').count(os.sep)
        if depth > max_depth:
            dirnames.clear()
            continue
        
        # Skip system/vendor dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith('.')]
        
        results['total_dirs'] += 1
        
        if not filenames:
            if depth <= 2:
                results['empty_dirs'].append(dirpath)
            continue
        
        results['total_files'] += len(filenames)
        
        # Calculate size
        dir_size = 0
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                sz = os.path.getsize(fp)
                dir_size += sz
                if sz > 100_000_000:  # >100MB
                    results['large_files'].append({'path': fp, 'size_mb': round(sz/1048576, 1)})
                # Track databases
                if f.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                    results['databases_found'].append({'path': fp, 'size_mb': round(sz/1048576, 1)})
            except OSError:
                pass
        
        results['total_size_bytes'] += dir_size
        
        # Classify
        category = classify_directory(dirpath, filenames)
        cat = results['categories'][category]
        cat['dirs'].append({'path': dirpath, 'files': len(filenames), 'size_mb': round(dir_size/1048576, 1)})
        cat['file_count'] += len(filenames)
        cat['size_bytes'] += dir_size
        
        # Detect LitigationOS project roots
        fset = set(f.lower() for f in filenames)
        if any(marker in fset for marker in ['agent_base.py', 'local_ai_engine.py', 'config.py', 'lexos_server.py', 'pipeline.py']):
            results['litigationos_roots'].append(dirpath)
        
        # Track duplicate directory names
        dirname = os.path.basename(dirpath).lower()
        if dirname and depth <= 2:
            results['duplicate_names'][dirname].append(dirpath)
    
    # Clean up duplicate_names — only keep actual dupes
    results['duplicate_names'] = {k: v for k, v in results['duplicate_names'].items() if len(v) > 1}
    
    # Convert defaultdict for JSON
    cats = {}
    for k, v in results['categories'].items():
        cats[k] = {
            'dir_count': len(v['dirs']),
            'file_count': v['file_count'],
            'size_mb': round(v['size_bytes'] / 1048576, 1),
            'top_dirs': sorted(v['dirs'], key=lambda x: x['files'], reverse=True)[:10]
        }
    results['categories'] = cats
    results['total_size_gb'] = round(results['total_size_bytes'] / (1024**3), 2)
    del results['total_size_bytes']
    
    return results

# Scan C: and H:
for drive in ['C', 'H']:
    print(f"\n{'='*60}")
    print(f"  SCANNING {drive}: DRIVE")
    print(f"{'='*60}")
    t0 = time.time()
    
    if drive == 'C':
        # For C:, focus on user dirs (skip Windows/Program Files)
        result = {'drive': 'C', 'scan_time': datetime.now().isoformat(),
                  'total_files': 0, 'total_dirs': 0, 'total_size_bytes': 0,
                  'categories': defaultdict(lambda: {'dirs': [], 'file_count': 0, 'size_bytes': 0}),
                  'databases_found': [], 'large_files': [], 'empty_dirs': [],
                  'duplicate_names': defaultdict(list), 'litigationos_roots': []}
        
        # Scan key C: locations
        scan_paths = [
            r'C:\Users\andre\LitigationOS',
            r'C:\Users\andre\LITIGATIONOS_MASTER',
            r'C:\Users\andre\Desktop',
            r'C:\Users\andre\Documents',
            r'C:\Users\andre\Downloads',
            r'C:\Users\andre\scans',
        ]
        for sp in scan_paths:
            if os.path.exists(sp):
                for dirpath, dirnames, filenames in os.walk(sp):
                    depth = dirpath.replace(sp, '').count(os.sep)
                    if depth > 5:
                        dirnames.clear()
                        continue
                    dirnames[:] = [d for d in dirnames if d not in 
                                   {'node_modules', '.git', '__pycache__', '.next', 'venv', '.venv'}]
                    result['total_dirs'] += 1
                    result['total_files'] += len(filenames)
                    dir_size = 0
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            sz = os.path.getsize(fp)
                            dir_size += sz
                            if sz > 100_000_000:
                                result['large_files'].append({'path': fp, 'size_mb': round(sz/1048576, 1)})
                            if f.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                                result['databases_found'].append({'path': fp, 'size_mb': round(sz/1048576, 1)})
                        except OSError:
                            pass
                    category = classify_directory(dirpath, filenames)
                    cat = result['categories'][category]
                    cat['dirs'].append({'path': dirpath, 'files': len(filenames), 'size_mb': round(dir_size/1048576, 1)})
                    cat['file_count'] += len(filenames)
                    cat['size_bytes'] += dir_size
                    fset = set(f.lower() for f in filenames)
                    if any(m in fset for m in ['agent_base.py', 'local_ai_engine.py', 'config.py', 'lexos_server.py']):
                        result['litigationos_roots'].append(dirpath)
        
        cats = {}
        for k, v in result['categories'].items():
            cats[k] = {
                'dir_count': len(v['dirs']),
                'file_count': v['file_count'],
                'size_mb': round(v['size_bytes'] / 1048576, 1),
                'top_dirs': sorted(v['dirs'], key=lambda x: x['files'], reverse=True)[:10]
            }
        result['categories'] = cats
        result['total_size_gb'] = round(result['total_size_bytes'] / (1024**3), 2)
        del result['total_size_bytes']
    else:
        result = scan_drive(drive, max_depth=3)
    
    elapsed = time.time() - t0
    
    print(f"\n  Scan time: {elapsed:.1f}s")
    print(f"  Total: {result['total_files']:,} files in {result['total_dirs']:,} dirs ({result['total_size_gb']} GB)")
    print(f"\n  📊 CONTENT CLASSIFICATION:")
    for cat, info in sorted(result['categories'].items(), key=lambda x: x[1]['file_count'], reverse=True):
        print(f"    {cat:25s} — {info['file_count']:>7,} files, {info['size_mb']:>8.1f} MB, {info['dir_count']} dirs")
        for d in info['top_dirs'][:3]:
            print(f"      └─ {d['path']} ({d['files']} files, {d['size_mb']}MB)")
    
    if result.get('litigationos_roots'):
        print(f"\n  🔧 LITIGATIONOS PROJECT ROOTS:")
        for r in result['litigationos_roots']:
            print(f"    ★ {r}")
    
    if result.get('databases_found'):
        print(f"\n  💾 DATABASES:")
        for db in sorted(result['databases_found'], key=lambda x: x['size_mb'], reverse=True)[:10]:
            print(f"    {db['size_mb']:>8.1f} MB — {db['path']}")
    
    if result.get('large_files'):
        print(f"\n  📦 LARGE FILES (>100MB):")
        for lf in sorted(result['large_files'], key=lambda x: x['size_mb'], reverse=True)[:10]:
            print(f"    {lf['size_mb']:>8.1f} MB — {lf['path']}")
    
    if result.get('duplicate_names'):
        print(f"\n  ⚠️  DUPLICATE DIR NAMES ({len(result['duplicate_names'])} sets):")
        for name, paths in list(result['duplicate_names'].items())[:5]:
            print(f"    '{name}' appears in:")
            for p in paths:
                print(f"      - {p}")
    
    # Save manifest
    out_path = os.path.join(r'C:\Users\andre\LitigationOS\00_SYSTEM', f'drive_{drive}_manifest.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  💾 Manifest saved: {out_path}")

print("\n✅ SCAN COMPLETE")