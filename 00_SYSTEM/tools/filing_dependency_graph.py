#!/usr/bin/env python3
"""
Filing Dependency Graph — LitigationOS Novel Tool
===================================================
Generates a strategic filing dependency graph showing:
  1. Which filings must be filed BEFORE others
  2. Critical path to final filings
  3. Parallel filing opportunities
  4. Bottleneck identification
  5. Mermaid diagram for visualization

Dependencies based on legal strategy:
  F3 (Disqualification) → unblocks F5, F7, F9 (removes McNeill)
  F1 (TRO) → F2 (Complaint) — emergency first, full complaint follows
  F9 (COA Brief) → F10 (COA Emergency) — brief underpins emergency
  F3 → F9 → F10 (appeal chain)
  F4 (Federal) is independent — parallel path
  F6 (JTC) is independent — parallel path

Usage:
  python filing_dependency_graph.py --dashboard     # Dependency dashboard
  python filing_dependency_graph.py --mermaid       # Mermaid diagram
  python filing_dependency_graph.py --critical-path # Show critical path
  python filing_dependency_graph.py --order         # Recommended filing order
  python filing_dependency_graph.py --json          # JSON output
"""

import sys, os, json, argparse
from datetime import datetime, date, timedelta
from collections import defaultdict, deque

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

# ─── FILING METADATA ─────────────────────────────────────────────────

FILINGS = {
    'F1':  {'name': 'Emergency TRO (Housing)', 'court': '14th Circuit', 'deadline': '2026-04-15', 'urgency': 85, 'ready': True, 'score': 90},
    'F2':  {'name': 'Amended Complaint (Housing)', 'court': '14th Circuit', 'deadline': '2026-05-01', 'urgency': 70, 'ready': True, 'score': 85},
    'F3':  {'name': 'Disqualification Motion', 'court': '14th Circuit', 'deadline': '2026-04-01', 'urgency': 94, 'ready': True, 'score': 95},
    'F4':  {'name': 'Federal §1983 Complaint', 'court': 'USDC WDMI', 'deadline': '2026-06-01', 'urgency': 60, 'ready': False, 'score': 70},
    'F5':  {'name': 'MSC Original Action', 'court': 'MSC', 'deadline': '2026-05-15', 'urgency': 75, 'ready': False, 'score': 75},
    'F6':  {'name': 'JTC Complaint', 'court': 'JTC', 'deadline': '2026-06-30', 'urgency': 50, 'ready': False, 'score': 65},
    'F7':  {'name': 'Custody Modification', 'court': '14th Circuit', 'deadline': '2026-05-01', 'urgency': 70, 'ready': False, 'score': 67.5},
    'F8':  {'name': 'PPO Termination', 'court': '14th Circuit', 'deadline': '2026-05-15', 'urgency': 65, 'ready': False, 'score': 72.5},
    'F9':  {'name': 'COA Brief on Appeal', 'court': 'COA', 'deadline': '2026-04-15', 'urgency': 90, 'ready': False, 'score': 85},
    'F10': {'name': 'COA Emergency Motion', 'court': 'COA', 'deadline': '2026-04-01', 'urgency': 94, 'ready': False, 'score': 58.3},
}

# ─── DEPENDENCY GRAPH ─────────────────────────────────────────────────
# Edge: (A, B) means A must be filed BEFORE B

DEPENDENCIES = [
    ('F3', 'F5',  'Disqualification strengthens MSC petition'),
    ('F3', 'F7',  'Disqualification before custody motion to same judge'),
    ('F3', 'F9',  'Disqualification is key argument in COA brief'),
    ('F3', 'F10', 'Disqualification underpins emergency motion'),
    ('F1', 'F2',  'TRO emergency first, then full complaint'),
    ('F9', 'F10', 'Brief filed before emergency motion relies on it'),
    ('F3', 'F8',  'Disqualification before PPO modification'),
]

# Independent filings (no prerequisites)
INDEPENDENT = ['F3', 'F1', 'F4', 'F6']

# ─── STRATEGIC LANES ─────────────────────────────────────────────────

LANES = {
    'Bypass Muskegon': ['F3', 'F5', 'F9', 'F10'],
    'Housing Emergency': ['F1', 'F2'],
    'Federal Offensive': ['F4'],
    'Judicial Accountability': ['F6'],
    'Family Court Reform': ['F7', 'F8'],
}


def build_adjacency():
    """Build adjacency list and reverse graph."""
    adj = defaultdict(list)       # forward: who depends on me
    rev = defaultdict(list)       # reverse: who do I depend on
    for src, dst, reason in DEPENDENCIES:
        adj[src].append((dst, reason))
        rev[dst].append((src, reason))
    return adj, rev


def topological_sort():
    """Return filing order via topological sort."""
    adj, rev = build_adjacency()
    in_degree = defaultdict(int)
    for fid in FILINGS:
        in_degree[fid] = 0
    for src, dst, _ in DEPENDENCIES:
        in_degree[dst] += 1
    
    queue = deque()
    for fid in FILINGS:
        if in_degree[fid] == 0:
            queue.append(fid)
    
    order = []
    while queue:
        # Pick highest urgency first among ready items
        candidates = sorted(queue, key=lambda f: (-FILINGS[f]['urgency'], f))
        node = candidates[0]
        queue.remove(node)
        order.append(node)
        
        for dst, _ in adj[node]:
            in_degree[dst] -= 1
            if in_degree[dst] == 0:
                queue.append(dst)
    
    return order


def find_critical_path():
    """Find the longest path through the dependency graph (critical path)."""
    adj, rev = build_adjacency()
    order = topological_sort()
    
    # Longest path using urgency as weight
    dist = {fid: 0 for fid in FILINGS}
    parent = {fid: None for fid in FILINGS}
    
    for node in order:
        for dst, reason in adj[node]:
            new_dist = dist[node] + FILINGS[node]['urgency']
            if new_dist > dist[dst]:
                dist[dst] = new_dist
                parent[dst] = node
    
    # Find endpoint with max distance
    end = max(dist, key=dist.get)
    path = []
    current = end
    while current:
        path.append(current)
        current = parent[current]
    path.reverse()
    
    return path, dist[end]


def generate_mermaid():
    """Generate a Mermaid flowchart diagram."""
    lines = ['```mermaid', 'flowchart LR']
    
    # Style nodes by readiness
    for fid, info in FILINGS.items():
        label = f"{fid}: {info['name'][:25]}"
        dl = info['deadline']
        if info['ready']:
            lines.append(f'    {fid}["{label}<br/>{dl} ✅"]')
        else:
            lines.append(f'    {fid}("{label}<br/>{dl}")')
    
    # Add edges
    for src, dst, reason in DEPENDENCIES:
        lines.append(f'    {src} --> {dst}')
    
    # Style ready nodes green
    ready = [fid for fid, info in FILINGS.items() if info['ready']]
    if ready:
        lines.append(f'    style {" ".join(ready)} fill:#90EE90')
    
    # Style urgent nodes red
    urgent = [fid for fid, info in FILINGS.items() if info['urgency'] >= 90]
    if urgent:
        lines.append(f'    style {" ".join(urgent)} stroke:#FF0000,stroke-width:3px')
    
    lines.append('```')
    return '\n'.join(lines)


def print_dashboard(verbose=False):
    """Print the full dependency dashboard."""
    print(f"\n{'═' * 78}")
    print(f"  FILING DEPENDENCY GRAPH — LitigationOS")
    print(f"  {date.today().isoformat()}")
    print(f"{'═' * 78}\n")
    
    # Recommended filing order
    order = topological_sort()
    print(f"  📋 RECOMMENDED FILING ORDER:")
    print(f"  {'─' * 60}")
    
    adj, rev = build_adjacency()
    
    for i, fid in enumerate(order, 1):
        info = FILINGS[fid]
        ready_icon = '✅' if info['ready'] else '⬜'
        deps = [src for src, _ in rev[fid]]
        dep_str = f" (after {', '.join(deps)})" if deps else " (INDEPENDENT)"
        days_left = (date.fromisoformat(info['deadline']) - date.today()).days
        urgency = '🔴' if days_left <= 14 else '🟡' if days_left <= 30 else '🟢'
        
        print(f"  {i:>2}. {ready_icon} {fid} — {info['name']:<30} {urgency} {days_left}d{dep_str}")
    
    # Critical path
    path, weight = find_critical_path()
    print(f"\n  🔥 CRITICAL PATH: {' → '.join(path)} (weight: {weight})")
    
    # Parallel opportunities
    print(f"\n  ⚡ PARALLEL FILING OPPORTUNITIES:")
    for fid in INDEPENDENT:
        info = FILINGS[fid]
        print(f"    {fid} ({info['name']}) — can file immediately, no prerequisites")
    
    # Strategic lanes
    print(f"\n  🎯 STRATEGIC LANES:")
    for lane, filings in LANES.items():
        statuses = [('✅' if FILINGS[f]['ready'] else '⬜') + f for f in filings]
        print(f"    {lane}: {' → '.join(statuses)}")
    
    # Bottleneck analysis
    print(f"\n  🚧 BOTTLENECK ANALYSIS:")
    for fid in FILINGS:
        blocked = [(dst, reason) for dst, reason in adj.get(fid, [])]
        if len(blocked) >= 3:
            print(f"    {fid} BLOCKS {len(blocked)} filings: {', '.join(d for d,_ in blocked)}")
            if not FILINGS[fid]['ready']:
                print(f"      ⚠ NOT READY — this is the #1 bottleneck!")
    
    if verbose:
        print(f"\n  📊 FILING SCORES:")
        for fid in sorted(FILINGS.keys()):
            info = FILINGS[fid]
            print(f"    {fid}: {info['score']}/100 ({info['court']}) — {'READY' if info['ready'] else 'NOT READY'}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description='Filing Dependency Graph')
    parser.add_argument('--dashboard', '-d', action='store_true', help='Full dashboard')
    parser.add_argument('--mermaid', '-m', action='store_true', help='Mermaid diagram')
    parser.add_argument('--critical-path', '-c', action='store_true', help='Critical path')
    parser.add_argument('--order', '-o', action='store_true', help='Filing order')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    args = parser.parse_args()
    
    if not any([args.dashboard, args.mermaid, args.critical_path, args.order]):
        args.dashboard = True
        args.verbose = True
    
    if args.dashboard:
        print_dashboard(args.verbose)
    
    if args.mermaid:
        diagram = generate_mermaid()
        print(diagram)
        mpath = os.path.join(REPORTS_DIR, 'filing_dependency_graph.md')
        os.makedirs(REPORTS_DIR, exist_ok=True)
        with open(mpath, 'w', encoding='utf-8') as f:
            f.write(f"# Filing Dependency Graph\n\n{diagram}\n")
        print(f"\n  📊 Mermaid: {mpath}")
    
    if args.critical_path:
        path, weight = find_critical_path()
        print(f"\n  Critical Path: {' → '.join(path)}")
        print(f"  Weight: {weight}")
    
    if args.order:
        order = topological_sort()
        for i, fid in enumerate(order, 1):
            print(f"  {i}. {fid} — {FILINGS[fid]['name']}")
    
    if args.json:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        jpath = os.path.join(REPORTS_DIR, 'filing_dependencies.json')
        with open(jpath, 'w', encoding='utf-8') as f:
            json.dump({
                'filings': FILINGS,
                'dependencies': [{'from': s, 'to': d, 'reason': r} for s, d, r in DEPENDENCIES],
                'recommended_order': topological_sort(),
                'critical_path': find_critical_path()[0],
                'independent': INDEPENDENT,
                'lanes': LANES,
                'generated': datetime.now().isoformat(),
            }, f, indent=2, default=str)
        print(f"  📊 JSON: {jpath}")


if __name__ == '__main__':
    main()
