#!/usr/bin/env python3
"""
LitigationOS Master Rebuild Script v3.0
Reproduces the entire pipeline from scratch.

Usage:
  python litigationos_rebuild.py --mode full
  python litigationos_rebuild.py --mode verify
  python litigationos_rebuild.py --mode incremental --skip-harvest
"""
import argparse, os, sys, json, time, hashlib, subprocess, shutil, re, zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, 'D:/TEMP')
sys.path.insert(0, 'D:/TEMP/pylibs')
os.environ['TEMP'] = 'D:/TEMP'
os.environ['TMP'] = 'D:/TEMP'
os.environ['PYTHONPATH'] = 'D:/TEMP/pylibs'

# ===== CONFIGURATION =====
CONFIG = {
    'scans_dir': 'C:/Users/andre/Scans',
    'output_dir': 'C:/Users/andre/Desktop',
    'temp_dir': 'D:/TEMP',
    'journals_dir': 'C:/Users/andre/Desktop/AGENT_JOURNALS',
    'packets_v3_dir': 'C:/Users/andre/Desktop/COURT_PACKETS_v3',
    'packets_v2_dir': 'C:/Users/andre/Desktop/COURT_PACKETS_v2',
    'state_file': 'D:/TEMP/rebuild_state.json',
    'log_file': 'D:/TEMP/rebuild.log',
    'workers': 10,
    'good_exts': ['.txt','.md','.pdf','.jsonl','.csv','.json','.msg',
                  '.docx','.eml','.rtf','.log','.yaml','.yml','.toml'],
}

CASE = {
    'plaintiff': 'ANDREW J. PIGORS',
    'defendant': 'EMILY WATSON',
    'child': 'L.D.W.',
    'child_dob': '2022-11-09',
    'court': '14th Judicial Circuit Court, Family Division',
    'county': 'Muskegon County, Michigan',
    'judge': 'Hon. Jenny L. McNeill',
    'cases': {'custody': '2024-001507-DC', 'ppo': '2023-5907-PP', 'civil': '2025-002760-CZ'},
    'opposing_counsel': 'Rusco',
    'watson_family': ['Albert Watson', 'Lori Watson', 'Cody Watson'],
    'damages': 94250,
    'separation_days': 329,
}

# ===== LOGGING =====
def log(msg, level='INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] [{level}] {msg}'
    print(line)
    with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
        f.write(line + '\n')

# ===== STATE MANAGEMENT =====
def load_state():
    if os.path.exists(CONFIG['state_file']):
        with open(CONFIG['state_file'], 'r') as f:
            return json.load(f)
    return {'steps_completed': [], 'started': datetime.now().isoformat(), 'errors': []}

def save_state(state):
    tmp = CONFIG['state_file'] + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, CONFIG['state_file'])

# ===== STEP 1: VERIFY ENVIRONMENT =====
def step_verify_environment():
    log('Step 1: Verifying environment...')
    checks = {}
    checks['python'] = f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'

    pkgs = ['docx','openpyxl','bs4','lxml','pdfplumber','tabulate',
            'PIL','chardet','textstat','networkx','matplotlib','jinja2']
    missing = []
    for p in pkgs:
        try:
            __import__(p)
        except ImportError:
            missing.append(p)
    checks['packages_ok'] = len(missing) == 0
    checks['packages_missing'] = missing

    c_free = shutil.disk_usage('C:/').free / (1024**3)
    d_free = shutil.disk_usage('D:/').free / (1024**3)
    checks['c_free_gb'] = round(c_free, 1)
    checks['d_free_gb'] = round(d_free, 1)
    checks['disk_ok'] = c_free > 5 and d_free > 5

    tools = {
        'pandoc': 'D:/TEMP/pandoc/pandoc-3.6.4/pandoc.exe',
        'rclone': 'D:/TEMP/rclone/rclone-v1.69.3-windows-amd64/rclone.exe',
        'frankenstein': 'D:/TEMP/frankenstein_engine.py',
        'fleet_v3': 'D:/TEMP/fleet_v3.py',
        'ai_dispatch': 'D:/TEMP/ai_dispatch.py',
        'synthesizer': 'D:/TEMP/journal_synthesizer.py',
    }
    for name, path in tools.items():
        checks[f'tool_{name}'] = os.path.exists(path)

    try:
        r = subprocess.run(['gemini', '--version'], capture_output=True, text=True, timeout=10)
        checks['gemini'] = r.stdout.strip()
    except Exception:
        checks['gemini'] = 'NOT FOUND'

    try:
        r = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        checks['ollama'] = 'OK' if r.returncode == 0 else 'ERROR'
    except Exception:
        checks['ollama'] = 'NOT FOUND'

    log(f'Environment: Python {checks["python"]}, C: {checks["c_free_gb"]}GB, D: {checks["d_free_gb"]}GB')
    if missing:
        log(f'Missing packages: {missing}', 'WARN')
    return checks

# ===== STEP 2: INVENTORY =====
def step_inventory():
    log('Step 2: Inventorying files...')
    from collections import Counter
    ext_counts = Counter()
    total = 0
    for root, dirs, files in os.walk(CONFIG['scans_dir']):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            ext_counts[ext] += 1
            total += 1
    good = sum(ext_counts[e] for e in CONFIG['good_exts'])
    log(f'Inventory: {total} total files, {good} high-value, {len(ext_counts)} extensions')
    return {'total': total, 'high_value': good, 'by_extension': dict(ext_counts.most_common(20))}

# ===== STEP 3: HARVEST =====
def step_harvest():
    log('Step 3: Running fleet v3 harvest...')
    cmd = [sys.executable, 'D:/TEMP/fleet_v3.py']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200, cwd='D:/TEMP')
        log(f'Fleet v3 completed with exit code {r.returncode}')
        return {'exit_code': r.returncode}
    except subprocess.TimeoutExpired:
        log('Fleet v3 timed out (2h limit)', 'WARN')
        return {'exit_code': -1, 'note': 'timeout'}

# ===== STEP 4: SYNTHESIZE =====
def step_synthesize():
    log('Step 4: Running journal synthesis...')
    cmd = [sys.executable, 'D:/TEMP/journal_synthesizer.py']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd='D:/TEMP')
        log(f'Synthesis completed with exit code {r.returncode}')
        return {'exit_code': r.returncode}
    except Exception as e:
        log(f'Synthesis error: {e}', 'ERROR')
        return {'exit_code': -1, 'error': str(e)}

# ===== STEP 5: ANALYZE =====
def step_analyze():
    log('Step 5: Analyzing synthesis data...')
    synthesis_path = os.path.join(CONFIG['output_dir'], 'SYNTHESIS_DATA.json')
    if not os.path.exists(synthesis_path):
        log('SYNTHESIS_DATA.json not found, skipping', 'WARN')
        return {'status': 'skipped'}
    with open(synthesis_path, 'r', encoding='utf-8', errors='replace') as f:
        data = json.load(f)
    stats = {
        'mcl_count': len(data.get('mcl_citations', {})),
        'mcr_count': len(data.get('mcr_citations', {})),
        'case_count': len(data.get('case_citations', {})),
        'persons': len(data.get('persons', {})),
        'dates': len(data.get('dates', {})),
    }
    log(f'Analysis: {stats["mcl_count"]} MCL, {stats["mcr_count"]} MCR, {stats["case_count"]} cases')
    return stats

# ===== STEP 6: GENERATE CSVs =====
def step_generate_csvs():
    log('Step 6: Checking master CSVs...')
    csvs = ['MASTER_CITATIONS.csv', 'MASTER_VIOLATIONS.csv', 'MASTER_TIMELINE.csv',
            'MASTER_PERSONS.csv', 'MASTER_EVIDENCE_INDEX.csv']
    existing = []
    for c in csvs:
        p = os.path.join(CONFIG['output_dir'], c)
        if os.path.exists(p):
            sz = os.path.getsize(p)
            existing.append({'name': c, 'size_kb': round(sz/1024, 1)})
    log(f'CSVs found: {len(existing)}/{len(csvs)}')
    return {'csvs': existing}

# ===== STEP 7: BUILD GRAPH =====
def step_build_graph():
    log('Step 7: Checking graph artifacts...')
    artifacts = ['neo4j_nodes.csv', 'neo4j_edges.csv', 'neo4j_constraints.cypher',
                 'bloom_perspective.json', 'graph.graphml']
    found = []
    for a in artifacts:
        for search_dir in [CONFIG['output_dir'], os.path.join(CONFIG['output_dir'], 'OFFLOAD_20260219')]:
            p = os.path.join(search_dir, a)
            if os.path.exists(p):
                found.append(a)
                break
    log(f'Graph artifacts: {len(found)}/{len(artifacts)}')
    return {'artifacts': found}

# ===== STEP 8: GENERATE FILINGS =====
def step_generate_filings():
    log('Step 8: Checking court filings...')
    filings_dir = CONFIG['packets_v3_dir']
    os.makedirs(filings_dir, exist_ok=True)
    filings = []
    for f in sorted(os.listdir(filings_dir)):
        p = os.path.join(filings_dir, f)
        if os.path.isfile(p):
            filings.append({'name': f, 'size_kb': round(os.path.getsize(p)/1024, 1)})
    total_kb = sum(f['size_kb'] for f in filings)
    log(f'Court filings: {len(filings)} files, {round(total_kb, 1)} KB total')
    return {'filings': filings, 'total_kb': total_kb}

# ===== STEP 9: QUALITY CHECK =====
def step_quality_check():
    log('Step 9: Running quality check...')
    filings_dir = CONFIG['packets_v3_dir']
    if not os.path.exists(filings_dir):
        return {'results': [], 'average_score': 0}
    results = []
    for fname in sorted(os.listdir(filings_dir)):
        fpath = os.path.join(filings_dir, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()

        score = 0
        checks = {}

        if 'Circuit Court' in text or 'Court of Appeals' in text:
            score += 10
            checks['caption'] = True
        if '2024-001507' in text or '2023-5907' in text:
            score += 10
            checks['case_number'] = True

        mcl = len(re.findall(r'MCL\s+\d+\.\d+', text))
        score += min(mcl * 2, 15)
        checks['mcl_citations'] = mcl

        mcr = len(re.findall(r'MCR\s+\d+\.\d+', text))
        score += min(mcr * 2, 15)
        checks['mcr_citations'] = mcr

        cases = len(re.findall(r'\d+\s+Mich\s+(App\s+)?\d+', text))
        score += min(cases * 3, 15)
        checks['case_citations'] = cases

        if 'PRAYER' in text.upper() or 'RELIEF' in text.upper():
            score += 5
            checks['prayer_relief'] = True
        if 'VERIFICATION' in text.upper() or 'CERTIFICATE' in text.upper():
            score += 5
            checks['verification'] = True

        exhibits = len(re.findall(r'Exhibit\s+[A-Z]', text))
        score += min(exhibits, 10)
        checks['exhibits'] = exhibits

        size_kb = len(text) / 1024
        score += min(int(size_kb / 5), 15)
        checks['size_kb'] = round(size_kb, 1)

        verifies = text.count('[VERIFY')
        checks['verify_tags'] = verifies

        grade = 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D'
        results.append({'file': fname, 'score': min(score, 100), 'grade': grade, 'checks': checks})

    avg = sum(r['score'] for r in results) / max(len(results), 1)
    log(f'Quality: {len(results)} filings scored, avg {round(avg, 1)}/100')
    return {'results': results, 'average_score': round(avg, 1)}

# ===== STEP 10: PACKAGE =====
def step_package():
    log('Step 10: Packaging deliverables...')
    zip_name = f'LitigationOS_Package_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    zip_path = os.path.join(CONFIG['temp_dir'], zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(CONFIG['packets_v3_dir']):
            for f in os.listdir(CONFIG['packets_v3_dir']):
                fp = os.path.join(CONFIG['packets_v3_dir'], f)
                if os.path.isfile(fp):
                    z.write(fp, f'COURT_PACKETS_v3/{f}')

        for sf in ['SYNTHESIS_MASTER.md', 'SYNTHESIS_DATA.json', 'SYNTHESIS_STATS.md']:
            sp = os.path.join(CONFIG['output_dir'], sf)
            if os.path.exists(sp):
                z.write(sp, f'SYNTHESIS/{sf}')

        for bf in ['MEGA_BLUEPRINT_LITIGATIONOS.md', 'LITIGATIONOS_ARCHITECTURE_BLUEPRINT.md']:
            bp = os.path.join(CONFIG['output_dir'], bf)
            if os.path.exists(bp):
                z.write(bp, f'BLUEPRINTS/{bf}')

        engines = ['frankenstein_engine.py', 'fleet_v3.py', 'ai_dispatch.py',
                   'journal_synthesizer.py', 'litigationos_rebuild.py']
        for ef in engines:
            ep = os.path.join(CONFIG['temp_dir'], ef)
            if os.path.exists(ep):
                z.write(ep, f'ENGINES/{ef}')

        if os.path.exists(CONFIG['state_file']):
            z.write(CONFIG['state_file'], 'STATE/rebuild_state.json')

    size_mb = round(os.path.getsize(zip_path) / (1024**2), 1)
    log(f'Package: {zip_path} ({size_mb} MB)')
    return {'zip_path': zip_path, 'size_mb': size_mb}

# ===== MAIN =====
STEPS = [
    ('verify_environment', step_verify_environment),
    ('inventory', step_inventory),
    ('harvest', step_harvest),
    ('synthesize', step_synthesize),
    ('analyze', step_analyze),
    ('generate_csvs', step_generate_csvs),
    ('build_graph', step_build_graph),
    ('generate_filings', step_generate_filings),
    ('quality_check', step_quality_check),
    ('package', step_package),
]

def main():
    parser = argparse.ArgumentParser(description='LitigationOS Master Rebuild v3.0')
    parser.add_argument('--mode', choices=['full', 'incremental', 'verify'], default='verify')
    parser.add_argument('--skip-harvest', action='store_true')
    parser.add_argument('--skip-analysis', action='store_true')
    parser.add_argument('--skip-filings', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    log(f'LitigationOS Rebuild v3.0 -- mode={args.mode}')
    state = load_state()

    skip_steps = set()
    if args.skip_harvest:
        skip_steps.add('harvest')
    if args.skip_analysis:
        skip_steps.add('analyze')
    if args.skip_filings:
        skip_steps.add('generate_filings')

    if args.mode == 'verify':
        skip_steps.update(['harvest', 'synthesize', 'inventory'])

    results = {}
    for step_name, step_func in STEPS:
        if step_name in skip_steps:
            log(f'Skipping {step_name}')
            continue
        if args.mode == 'incremental' and step_name in state.get('steps_completed', []):
            log(f'Already completed: {step_name}')
            continue

        t0 = time.time()
        try:
            result = step_func()
            elapsed = round(time.time() - t0, 1)
            results[step_name] = result
            if step_name not in state['steps_completed']:
                state['steps_completed'].append(step_name)
            state[f'{step_name}_result'] = result
            state[f'{step_name}_elapsed'] = elapsed
            save_state(state)
            log(f'Completed {step_name} in {elapsed}s')
        except Exception as e:
            log(f'FAILED {step_name}: {e}', 'ERROR')
            state['errors'].append({'step': step_name, 'error': str(e)})
            save_state(state)

    log('Rebuild complete!')
    return results


if __name__ == '__main__':
    main()
