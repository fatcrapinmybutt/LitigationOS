#!/usr/bin/env python3
"""
Phase A: Dedup Marking Script
Marks files as CANONICAL, DUPLICATE_SKIP, or EMPTY_SKIP in the consolidation state database.
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
    print("PHASE A: DEDUP MARKING")
    print("=" * 80)
    print(f"Database: {db_path}")
    print()
    
    # Open database with busy timeout
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=60000")
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
            AND copy_status IS NULL
        """)
        empty_count = cursor.rowcount
        print(f"  Marked {empty_count} empty files as EMPTY_SKIP")
        print()
        
        # 3. Mark canonical/duplicate files for each drive
        print("MARKING CANONICAL/DUPLICATE FILES BY DRIVE:")
        print("-" * 80)
        
        drives = ['D:', 'F:', 'G:', 'I:']
        drive_stats = {}
        
        for drive in drives:
            print(f"\n  Processing drive: {drive}")
            
            # Get all valid hash groups for this drive (pending or null copy_status)
            cursor.execute("""
                SELECT xxhash, COUNT(*) as cnt, COUNT(DISTINCT source_path) as unique_paths
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
            canonical_count = 0
            duplicate_count = 0
            canonical_bytes = 0
            duplicate_bytes = 0
            
            for xxhash, cnt, unique_paths in hash_groups:
                # Get files in this hash group, sorted by modified_date DESC (newest first)
                cursor.execute("""
                    SELECT id, source_path, file_size, modified_date
                    FROM file_inventory
                    WHERE source_drive = ?
                    AND (copy_status IS NULL OR copy_status = 'pending')
                    AND xxhash = ?
                    ORDER BY modified_date DESC, source_path ASC
                """, (drive, xxhash))
                
                files_in_group = cursor.fetchall()
                
                if not files_in_group:
                    continue
                
                # First file is canonical
                first_file = files_in_group[0]
                first_file_id = first_file[0]
                cursor.execute("""
                    UPDATE file_inventory
                    SET copy_status='CANONICAL'
                    WHERE id = ?
                """, (first_file_id,))
                canonical_count += 1
                if first_file[2]:
                    canonical_bytes += first_file[2]
                
                # Rest are duplicates
                for file_info in files_in_group[1:]:
                    file_id = file_info[0]
                    cursor.execute("""
                        UPDATE file_inventory
                        SET copy_status='DUPLICATE_SKIP'
                        WHERE id = ?
                    """, (file_id,))
                    duplicate_count += 1
                    if file_info[2]:
                        duplicate_bytes += file_info[2]
            
            conn.commit()
            
            drive_stats[drive] = {
                'canonical': canonical_count,
                'duplicate': duplicate_count,
                'canonical_bytes': canonical_bytes,
                'duplicate_bytes': duplicate_bytes,
                'hash_groups': len(hash_groups)
            }
            
            print(f"    Hash groups found: {len(hash_groups)}")
            print(f"    CANONICAL files: {canonical_count} ({format_size(canonical_bytes)})")
            print(f"    DUPLICATE files: {duplicate_count} ({format_size(duplicate_bytes)})")
        
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
        
        print()
        print("=" * 80)
        print("PHASE A COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
