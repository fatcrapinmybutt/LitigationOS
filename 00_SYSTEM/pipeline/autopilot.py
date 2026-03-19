"""
Auto-pilot: Monitors A07, then runs K → L → F tiers sequentially.
Launch this and walk away — everything queues up behind A07.
"""
import sys, os, time, json
sys.path.insert(0, '.')
os.chdir(r'C:\Users\andre\LitigationOS\00_SYSTEM\pipeline')

from agents.agent_orchestrator import run_tier

TIERS = [
    ("tierK", "K-TIER ANALYSIS", 4),
    ("tierL", "L-TIER SCORING", 4),
    ("convergence", "CONVERGENCE F01-F06", 2),
]

def wait_for_a07():
    """Poll A07 checkpoint until done."""
    cp_path = 'agents/checkpoints/A07-CODE-DEDUP.checkpoint.json'
    while True:
        try:
            d = json.load(open(cp_path))
            p = d.get('processed', 0)
            t = d.get('total', 857028)
            pct = 100 * p / max(t, 1)
            print(f'[AUTOPILOT] A07: {p:,}/{t:,} ({pct:.1f}%)', flush=True)
            if p >= t - 10:  # within 10 of done
                print('[AUTOPILOT] A07 appears complete!', flush=True)
                return
        except Exception as e:
            print(f'[AUTOPILOT] A07 check error: {e}', flush=True)
        time.sleep(60)  # check every 60s

def run_tier_safe(tier_name, label, workers):
    """Run a tier with full error handling."""
    print(f'\n{"="*60}', flush=True)
    print(f'[AUTOPILOT] === {label} ===', flush=True)
    print(f'{"="*60}', flush=True)
    try:
        results = run_tier(tier_name, max_workers=workers)
        for r in results:
            s = r.stats
            status_icon = "✓" if r.status == "SUCCESS" else "✗"
            print(f'  {status_icon} {r.agent_id}: {r.status} '
                  f'[{s.processed}/{s.total} done, {s.skipped} skip, {s.errored} err]',
                  flush=True)
            if r.error:
                print(f'    ERR: {str(r.error)[:200]}', flush=True)
        return results
    except Exception as e:
        print(f'[AUTOPILOT] {label} FAILED: {e}', flush=True)
        return []

if __name__ == '__main__':
    print('[AUTOPILOT] Waiting for A07 to complete before launching K → L → F...', flush=True)
    wait_for_a07()

    # Small delay to let A07 finalize and release DB
    time.sleep(5)

    for tier_name, label, workers in TIERS:
        run_tier_safe(tier_name, label, workers)

    # Final DB stats
    import sqlite3
    db = sqlite3.connect('agents/master_index.db', timeout=30)
    db.execute('PRAGMA busy_timeout=30000')
    print('\n' + '='*60, flush=True)
    print('[AUTOPILOT] === FINAL STATUS ===', flush=True)
    for label, q in [
        ('Files', 'SELECT COUNT(*) FROM files'),
        ('Canonical', 'SELECT COUNT(*) FROM files WHERE is_canonical=1'),
        ('fact_atoms', 'SELECT COUNT(*) FROM fact_atoms'),
        ('citation_atoms', 'SELECT COUNT(*) FROM citation_atoms'),
        ('atoms', 'SELECT COUNT(*) FROM atoms'),
        ('judicial', 'SELECT COUNT(*) FROM judicial_findings'),
        ('action_scores', 'SELECT COUNT(*) FROM action_scores'),
        ('Ready to file', "SELECT COUNT(*) FROM action_scores WHERE readiness_score >= 0.7"),
    ]:
        try:
            val = db.execute(q).fetchone()[0]
            print(f'  {label}: {val:,}', flush=True)
        except:
            pass
    db.close()
    print('\n[AUTOPILOT] ALL TIERS COMPLETE', flush=True)
