"""
Zip Clustering Engine — Phase 2.1 DISTILL
Clusters similar zips by filename, content fingerprint, size, and date proximity.
Prioritizes by litigation relevance x duplication factor.
"""
import sqlite3
import sys
import os
import re
import math
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"


def normalize_name(name):
    """Normalize zip filename for clustering."""
    name = os.path.splitext(os.path.basename(name))[0].lower()
    name = re.sub(r'[\(\)\[\]\{\}]', '', name)
    name = re.sub(r'[-_\s]+', ' ', name)
    name = re.sub(r'\s*\d+\s*$', '', name)  # remove trailing numbers
    name = re.sub(r'\s*copy\s*\d*\s*$', '', name)
    return name.strip()


def cluster_zips(conn):
    """Multi-dimensional clustering of zip archives."""
    print("Loading zip intelligence data...")
    
    zips = conn.execute("""
        SELECT zip_path, drive, compressed_bytes/1048576.0 as compressed_size_mb, file_count,
               content_fingerprint, litigation_relevance, is_corrupted,
               has_nested_zips
        FROM omega_zip_intelligence
        WHERE is_corrupted = 0
        ORDER BY litigation_relevance DESC
    """).fetchall()
    
    print(f"  {len(zips)} non-corrupted zips loaded")
    
    # Phase 1: Group by content fingerprint (exact dupes)
    fp_groups = defaultdict(list)
    for z in zips:
        fp = z[4]
        if fp and fp not in ('EMPTY', 'ERROR', ''):
            fp_groups[fp].append(z)
    
    exact_dupes = {fp: g for fp, g in fp_groups.items() if len(g) > 1}
    print(f"  {len(exact_dupes)} exact-dupe groups ({sum(len(g) for g in exact_dupes.values())} zips)")
    
    # Phase 2: Name-based clustering
    name_groups = defaultdict(list)
    for z in zips:
        norm = normalize_name(z[0])
        tokens = set(norm.split()) - {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'zip', 'archive'}
        key = ' '.join(sorted(tokens)) if tokens else norm
        name_groups[key].append(z)
    
    name_clusters = {k: v for k, v in name_groups.items() if len(v) > 1}
    print(f"  {len(name_clusters)} name-based clusters ({sum(len(g) for g in name_clusters.values())} zips)")
    
    # Phase 3: Union-find merge
    zip_to_cluster = {}
    cluster_counter = [0]
    clusters = {}
    
    def merge_group(group):
        paths = [z[0] for z in group]
        existing = set(zip_to_cluster[p] for p in paths if p in zip_to_cluster)
        
        if existing:
            target = min(existing)
            for eid in existing:
                if eid != target:
                    for p in clusters.get(eid, set()):
                        zip_to_cluster[p] = target
                        clusters.setdefault(target, set()).add(p)
                    clusters.pop(eid, None)
            for p in paths:
                zip_to_cluster[p] = target
                clusters.setdefault(target, set()).add(p)
        else:
            cid = cluster_counter[0]
            cluster_counter[0] += 1
            clusters[cid] = set(paths)
            for p in paths:
                zip_to_cluster[p] = cid
    
    for group in exact_dupes.values():
        merge_group(group)
    for group in name_clusters.values():
        merge_group(group)
    
    # Singletons
    for z in zips:
        if z[0] not in zip_to_cluster:
            cid = cluster_counter[0]
            cluster_counter[0] += 1
            clusters[cid] = {z[0]}
            zip_to_cluster[z[0]] = cid
    
    zip_data = {z[0]: z for z in zips}
    
    # Score clusters
    scored = []
    for cid, paths in clusters.items():
        members = [zip_data[p] for p in paths if p in zip_data]
        if not members:
            continue
        avg_rel = sum(m[5] or 0 for m in members) / len(members)
        total_mb = sum(m[2] or 0 for m in members)
        total_files = sum(m[3] or 0 for m in members)
        priority = (avg_rel * len(members)) / math.log2(len(members) + 1)
        
        scored.append({
            'cluster_id': cid,
            'member_count': len(members),
            'total_size_mb': round(total_mb, 2),
            'total_files': total_files,
            'avg_relevance': round(avg_rel, 2),
            'priority': round(priority, 2),
            'paths': list(paths),
            'drives': list(set(m[1] for m in members)),
        })
    
    scored.sort(key=lambda x: x['priority'], reverse=True)
    
    multi = [c for c in scored if c['member_count'] > 1]
    print(f"\n  RESULTS: {len(scored)} clusters ({len(multi)} multi-member, {len(scored)-len(multi)} singletons)")
    return scored


def save_clusters(conn, clusters):
    """Save to DB."""
    conn.execute("DROP TABLE IF EXISTS omega_zip_cluster_members")
    conn.execute("DROP TABLE IF EXISTS omega_zip_clusters")
    
    conn.execute("""
        CREATE TABLE omega_zip_clusters (
            cluster_id INTEGER PRIMARY KEY,
            member_count INTEGER,
            total_size_mb REAL,
            total_files INTEGER,
            avg_relevance REAL,
            priority REAL,
            drives TEXT,
            status TEXT DEFAULT 'pending',
            processed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE omega_zip_cluster_members (
            cluster_id INTEGER,
            zip_path TEXT,
            FOREIGN KEY (cluster_id) REFERENCES omega_zip_clusters(cluster_id)
        )
    """)
    
    for c in clusters:
        conn.execute(
            "INSERT INTO omega_zip_clusters (cluster_id, member_count, total_size_mb, total_files, avg_relevance, priority, drives) VALUES (?,?,?,?,?,?,?)",
            (c['cluster_id'], c['member_count'], c['total_size_mb'], c['total_files'], c['avg_relevance'], c['priority'], ','.join(c['drives']))
        )
        for p in c['paths']:
            conn.execute("INSERT INTO omega_zip_cluster_members (cluster_id, zip_path) VALUES (?,?)", (c['cluster_id'], p))
    
    conn.commit()
    print(f"  Saved {len(clusters)} clusters to DB")


def print_dashboard(clusters):
    """Print cluster dashboard."""
    multi = [c for c in clusters if c['member_count'] > 1]
    total_dupe_mb = sum(c['total_size_mb'] for c in multi)
    
    print(f"\n  TOP 20 PRIORITY CLUSTERS:")
    print(f"  {'#':>3} {'Pri':>7} {'Zips':>5} {'MB':>9} {'Files':>7} {'Rel':>5} {'Drives':>8} Sample")
    print(f"  {'='*80}")
    
    for i, c in enumerate(clusters[:20]):
        sample = os.path.basename(c['paths'][0])[:35]
        print(f"  {i+1:>3} {c['priority']:>7.1f} {c['member_count']:>5} {c['total_size_mb']:>9.1f} {c['total_files']:>7} {c['avg_relevance']:>5.1f} {','.join(c['drives']):>8} {sample}")
    
    print(f"\n  DEDUP POTENTIAL:")
    print(f"  Multi-member clusters: {len(multi)}")
    print(f"  Total size in dupes: {total_dupe_mb:,.0f} MB ({total_dupe_mb/1024:.1f} GB)")
    print(f"  Est. reclaimable: ~{total_dupe_mb * 0.4:,.0f} MB (~{total_dupe_mb * 0.4 / 1024:.1f} GB)")
    
    # Per-drive breakdown
    drive_stats = defaultdict(lambda: {'clusters': 0, 'zips': 0, 'mb': 0})
    for c in clusters:
        for d in c['drives']:
            drive_stats[d]['clusters'] += 1
            drive_stats[d]['zips'] += c['member_count']
            drive_stats[d]['mb'] += c['total_size_mb']
    
    print(f"\n  PER-DRIVE BREAKDOWN:")
    for d in sorted(drive_stats.keys()):
        s = drive_stats[d]
        print(f"  {d}: {s['clusters']} clusters, {s['zips']} zips, {s['mb']:,.0f} MB")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    clusters = cluster_zips(conn)
    save_clusters(conn, clusters)
    print_dashboard(clusters)
    conn.close()
    print("\n[DONE] Zip clustering complete")
