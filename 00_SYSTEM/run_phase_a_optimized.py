#!/usr/bin/env python3
"""
Phase A: Dedup Marking Script - Optimized Batch Version
Marks files as CANONICAL, DUPLICATE_SKIP, or EMPTY_SKIP in the consolidation state database.
Uses batch operations for performance.
"""
import sqlite3
import time

def format_size(size):
    """Format bytes to human-readable size."""
    if size is None:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def main():
    db_path = r'D:\LitigationOS_tmp\consolidation_state.db'
    
    print("=" * 80)
    print("PHASE A: DEDUP MARKING (OPTIMIZED)")
    print("=" * 80)
    print(f"Database: {db_path}")
    print()
    
    # Open database with busy timeout
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    
    try:
        # 1. Report initial status
        print("INITIAL STATUS:")
        print("-" * 80)
        cursor.execute("""
            SELECT copy_status, COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_bytes
            FROM file_inventory
            GROUP BY copy_status
            ORDER BY copy_status
        """)
        initial_results = cursor.fetchall()
        total_files = 0
        total_bytes = 0
        for status, count, total_bytes_status in initial_results:
            status_label = status if status else "NULL"
            print(f"  {status_label:20s}: {count:8d} files, {format_size(total_bytes_status)}")
            total_files += count
            total_bytes += total_bytes_status if total_bytes_status else 0
        print(f"  {'TOTAL':20s}: {total_files:8d} files, {format_size(total_bytes)}")
        print()
        
        # 2. Mark empty files
        print("MARKING EMPTY FILES:")
        print("-" * 80)
        cursor.execute("""
            UPDATE file_inventory 
            SET copy_status='EMPTY_SKIP'
            WHERE (file_size=0 OR file_size IS NULL) 
            AND (copy_status IS NULL OR copy_status = 'pending')
        """)
        empty_count = cursor.rowcount
        print(f"  Marked {empty_count} empty files as EMPTY_SKIP")
        conn.commit()
        print()
        
        # 3. Mark canonical/duplicate files for each drive
        print("MARKING CANONICAL/DUPLICATE FILES BY DRIVE:")
        print("-" * 80)
        
        drives = ['D:', 'F:', 'G:', 'I:']
        drive_stats = {}
        
        for drive in drives:
            print(f"\n  Processing drive: {drive}")
            start_time = time.time()
            
            # Get all valid hash groups for this drive
            cursor.execute("""
                SELECT xxhash, COUNT(*) as cnt
                FROM file_inventory
                WHERE source_drive = ? 
                AND (copy_status IS NULL OR copy_status = 'pending')
                AND xxhash IS NOT NULL
                AND xxhash != ''
                AND NOT xxhash LIKE 'ERROR%'
                AND xxhash != 'EMPTY_FILE'
                GROUP BY xxhash
            """, (drive,))
            
            hash_groups = cursor.fetchall()
            print(f"    Total hash groups found: {len(hash_groups)}")
            
            if not hash_groups:
                drive_stats[drive] = {
                    'canonical': 0,
                    'duplicate': 0,
                    'canonical_bytes': 0,
                    'duplicate_bytes': 0,
                    'time': 0
                }
                continue
            
            # Process in batches
            canonical_ids = []
            duplicate_ids = []
            
            for i, (xxhash, cnt) in enumerate(hash_groups):
                if (i + 1) % 100 == 0:
                    print(f"      Processing hash groups {i+1}/{len(hash_groups)}...")
                
                # Get files in this hash group, sorted by modified_date DESC
                cursor.execute("""
                    SELECT id, file_size
                    FROM file_inventory
                    WHERE source_drive = ?
                    AND (copy_status IS NULL OR copy_status = 'pending')
                    AND xxhash = ?
                    ORDER BY modified_date DESC, source_path ASC
                """, (drive, xxhash))
                
                files_in_group = cursor.fetchall()
                
                if not files_in_group:
                    continue
                
                # First file is canonical, rest are duplicates
                canonical_ids.append(files_in_group[0][0])
                for file_info in files_in_group[1:]:
                    duplicate_ids.append(file_info[0])
            
            # Batch update canonical files
            if canonical_ids:
                print(f"    Marking {len(canonical_ids)} files as CANONICAL...")
                for i in range(0, len(canonical_ids), 1000):
                    batch = canonical_ids[i:i+1000]
                    placeholders = ','.join(['?' for _ in batch])
                    cursor.execute(f"""
                        UPDATE file_inventory
                        SET copy_status='CANONICAL'
                        WHERE id IN ({placeholders})
                    """, batch)
                    conn.commit()
            
            # Batch update duplicate files
            if duplicate_ids:
                print(f"    Marking {len(duplicate_ids)} files as DUPLICATE_SKIP...")
                for i in range(0, len(duplicate_ids), 1000):
                    batch = duplicate_ids[i:i+1000]
                    placeholders = ','.join(['?' for _ in batch])
                    cursor.execute(f"""
                        UPDATE file_inventory
                        SET copy_status='DUPLICATE_SKIP'
                        WHERE id IN ({placeholders})
                    """, batch)
                    conn.commit()
            
            # Get stats
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN copy_status='CANONICAL' THEN 1 ELSE 0 END) as canonical_count,
                    SUM(CASE WHEN copy_status='DUPLICATE_SKIP' THEN 1 ELSE 0 END) as duplicate_count,
                    SUM(CASE WHEN copy_status='CANONICAL' THEN file_size ELSE 0 END) as canonical_bytes,
                    SUM(CASE WHEN copy_status='DUPLICATE_SKIP' THEN file_size ELSE 0 END) as duplicate_bytes
                FROM file_inventory
                WHERE source_drive = ?
                AND (copy_status='CANONICAL' OR copy_status='DUPLICATE_SKIP')
            """, (drive,))
            
            stats = cursor.fetchone()
            canonical_count = stats[0] or 0
            duplicate_count = stats[1] or 0
            canonical_bytes = stats[2] or 0
            duplicate_bytes = stats[3] or 0
            
            elapsed = time.time() - start_time
            drive_stats[drive] = {
                'canonical': canonical_count,
                'duplicate': duplicate_count,
                'canonical_bytes': canonical_bytes,
                'duplicate_bytes': duplicate_bytes,
                'time': elapsed
            }
            
            print(f"    CANONICAL files: {canonical_count} ({format_size(canonical_bytes)})")
            print(f"    DUPLICATE files: {duplicate_count} ({format_size(duplicate_bytes)})")
            print(f"    Time: {elapsed:.1f}s")
        
        print()
        
        # 4. Report final status
        print("FINAL STATUS:")
        print("-" * 80)
        cursor.execute("""
            SELECT copy_status, COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_bytes
            FROM file_inventory
            GROUP BY copy_status
            ORDER BY copy_status
        """)
        final_results = cursor.fetchall()
        total_files_final = 0
        total_bytes_final = 0
        for status, count, total_bytes_status in final_results:
            status_label = status if status else "NULL"
            print(f"  {status_label:20s}: {count:8d} files, {format_size(total_bytes_status)}")
            total_files_final += count
            total_bytes_final += total_bytes_status if total_bytes_status else 0
        print(f"  {'TOTAL':20s}: {total_files_final:8d} files, {format_size(total_bytes_final)}")
        print()
        
        # 5. Summary by drive
        print("SUMMARY BY DRIVE:")
        print("-" * 80)
        for drive in drives:
            if drive in drive_stats:
                stats = drive_stats[drive]
                print(f"  {drive}:")
                print(f"    CANONICAL:      {stats['canonical']:6d} files ({format_size(stats['canonical_bytes'])})")
                print(f"    DUPLICATE_SKIP: {stats['duplicate']:6d} files ({format_size(stats['duplicate_bytes'])})")
                if stats['time'] > 0:
                    print(f"    Time: {stats['time']:.1f}s")
        
        print()
        print("=" * 80)
        print("PHASE A COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
