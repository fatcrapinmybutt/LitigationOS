# LitigationOS — SINGULARITY Task Runner (Rust `just` v1.48.1)
# Usage: just <recipe>    |    just --list

set windows-shell := ["python", "-c"]
set dotenv-load := false

# Default: show all recipes
default:
    @import sys; sys.stdout.write('\n'.join([' just verify        — 5-gate verification (<15s)', ' just test           — run all pytest suites', ' just lint           — ruff + boundary check', ' just status         — DB stats + separation counter + deadlines', ' just engines        — list all 16 engines with status', ' just search QUERY   — hybrid FTS5 search across evidence', ' just ingest PATH    — Go ingest engine (8-worker)', ' just filing LANE    — filing readiness for lane', ' just hooks-install  — install Python git hooks', ' just clean          — purge __pycache__ + .pyc', ' just build-go       — compile Go ingest engine', ' just startup        — full session startup report', '']) + '\n')

# ══════════════════════════════════════════════════════════════
# VERIFICATION & TESTING
# ══════════════════════════════════════════════════════════════

# 5-gate verification pipeline (<15s)
verify:
    @import subprocess, sys, time; t0=time.time(); gates=[('Syntax', ['python', '-I', 'scripts/verify_syntax.py']), ('Contracts', ['python', '-I', '-m', 'pytest', '00_SYSTEM/shared/tests/', '-q', '--tb=line', '--no-header']), ('Boundaries', ['python', '-I', 'scripts/check_boundaries.py']), ('Schema', ['python', '-I', 'scripts/litctl.py', 'schema-check']), ('FTS5', ['python', '-I', 'scripts/litctl.py', 'fts5-health'])]; passed=0; \
    [sys.stdout.write(f'  Gate {i+1}/5: {n}... ') or (lambda r: (sys.stdout.write('PASS\n') if r.returncode==0 else sys.stdout.write(f'FAIL\n{r.stderr[:200]}\n')) or (passed:=passed+(1 if r.returncode==0 else 0)))(subprocess.run(c, capture_output=True, text=True, cwd=r'C:\Users\andre\LitigationOS')) for i,(n,c) in enumerate(gates)]; \
    sys.stdout.write(f'\n  {passed}/5 gates passed in {time.time()-t0:.1f}s\n')

# Run all pytest suites
test:
    @import subprocess; subprocess.run(['python', '-I', '-m', 'pytest', '00_SYSTEM/shared/tests/', '00_SYSTEM/engines/tests/', '00_SYSTEM/brains/tests/', '.github/extensions/tests/', '-q', '--tb=short'], cwd=r'C:\Users\andre\LitigationOS')

# Ruff lint check
lint:
    @import subprocess; subprocess.run(['python', '-I', '-m', 'ruff', 'check', '00_SYSTEM/', 'scripts/', '--select', 'E,F,W,I,N,UP,B,SIM,C4', '--line-length', '100'], cwd=r'C:\Users\andre\LitigationOS')

# ══════════════════════════════════════════════════════════════
# STATUS & INTELLIGENCE
# ══════════════════════════════════════════════════════════════

# Full system status dashboard
status:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'status'], cwd=r'C:\Users\andre\LitigationOS')

# List all 16 engines
engines:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'engines'], cwd=r'C:\Users\andre\LitigationOS')

# Session startup report
startup:
    @import subprocess; subprocess.run(['python', '-I', '00_SYSTEM/local_model/copilot_startup_hook.py', '--file'], cwd=r'C:\Users\andre\LitigationOS'); \
    subprocess.run(['python', '-I', '00_SYSTEM/local_model/session_recall.py', 'recent'], cwd=r'C:\Users\andre\LitigationOS')

# ══════════════════════════════════════════════════════════════
# SEARCH & EVIDENCE
# ══════════════════════════════════════════════════════════════

# Hybrid search across evidence (FTS5 + LIKE fallback)
search QUERY:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'search', '{{QUERY}}'], cwd=r'C:\Users\andre\LitigationOS')

# Filing readiness for a specific lane
filing LANE:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'filing', '{{LANE}}'], cwd=r'C:\Users\andre\LitigationOS')

# ══════════════════════════════════════════════════════════════
# BUILD & INGEST
# ══════════════════════════════════════════════════════════════

# Compile Go ingest engine
build-go:
    @import subprocess, os; os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\engines\ingest'); subprocess.run(['go', 'build', '-o', 'ingest.exe', '.'])

# Run Go ingest on a path
ingest PATH:
    @import subprocess; subprocess.run([r'00_SYSTEM\engines\ingest\ingest.exe', '{{PATH}}'], cwd=r'C:\Users\andre\LitigationOS')

# ══════════════════════════════════════════════════════════════
# MAINTENANCE
# ══════════════════════════════════════════════════════════════

# Install Python pre-commit hooks (replaces PS1 hooks)
hooks-install:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'hooks-install'], cwd=r'C:\Users\andre\LitigationOS')

# Purge __pycache__ and .pyc files
clean:
    @import subprocess; subprocess.run(['fd', '-t', 'd', '__pycache__', '.', '--exec', 'rd', '/s', '/q', '{}'], cwd=r'C:\Users\andre\LitigationOS'); print('Cleaned __pycache__ dirs')

# FTS5 rebuild (run after bulk inserts)
fts5-rebuild:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'fts5-rebuild'], cwd=r'C:\Users\andre\LitigationOS')

# Deadline check with urgency
deadlines:
    @import subprocess; subprocess.run(['python', '-I', 'scripts/litctl.py', 'deadlines'], cwd=r'C:\Users\andre\LitigationOS')

# Separation day counter
separation:
    @import datetime; d=(datetime.date.today()-datetime.date(2025,7,29)).days; print(f'\n  ⚠️  SEPARATION: {d} days since last contact with L.D.W. (Jul 29, 2025)\n')
