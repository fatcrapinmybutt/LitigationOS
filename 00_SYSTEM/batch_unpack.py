"""Batch unpack remaining ZIPs with space monitoring and dedup."""
import sys, os, zipfile, hashlib, json, shutil
sys.stdout.reconfigure(encoding='utf-8')

ARCHIVE_DIR = r'C:\Users\andre\LitigationOS\12_ARCHIVES'
STAGING_DIR = r'F:\LitOS_Unpack_Staging'
SPACE_LIMIT_GB = 3.0  # Stop unpacking when F: has less than this

def get_free_gb(drive='F:'):
    import ctypes
    free = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(drive + '\\', None, None, ctypes.byref(free))
    return free.value / (1024**3)

def find_remaining_zips():
    """Find ZIPs in archive that haven't been unpacked to staging."""
    already_done = set()
    if os.path.exists(STAGING_DIR):
        already_done = set(d for d in os.listdir(STAGING_DIR) if os.path.isdir(os.path.join(STAGING_DIR, d)))
    
    remaining = []
    for root, dirs, files in os.walk(ARCHIVE_DIR):
        for f in files:
            if f.lower().endswith('.zip'):
                base = os.path.splitext(f)[0]
                if base not in already_done:
                    remaining.append(os.path.join(root, f))
    return remaining

def unpack_zip(zip_path, dest_dir):
    """Unpack a single ZIP, return file count."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_dir)
            return len(zf.namelist())
    except (zipfile.BadZipFile, Exception) as e:
        print(f'  BAD ZIP: {os.path.basename(zip_path)}: {e}')
        return -1

def dedup_directory(dirpath):
    """Remove duplicate files within a directory by SHA-256."""
    seen = {}
    removed = 0
    freed = 0
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            fp = os.path.join(root, f)
            try:
                h = hashlib.sha256()
                with open(fp, 'rb') as fh:
                    while True:
                        chunk = fh.read(8192)
                        if not chunk:
                            break
                        h.update(chunk)
                digest = h.hexdigest()
                if digest in seen:
                    sz = os.path.getsize(fp)
                    os.remove(fp)
                    removed += 1
                    freed += sz
                else:
                    seen[digest] = fp
            except Exception:
                pass
    return removed, freed

def main():
    zips = find_remaining_zips()
    print(f'Found {len(zips)} remaining ZIPs to unpack')
    print(f'F: drive free: {get_free_gb("F:"):.1f}GB')
    
    total_unpacked = 0
    total_files = 0
    total_deduped = 0
    total_freed = 0
    failed = []
    
    for i, zp in enumerate(zips):
        free_gb = get_free_gb('F:')
        if free_gb < SPACE_LIMIT_GB:
            print(f'\nSTOPPING: F: drive only has {free_gb:.1f}GB free (limit: {SPACE_LIMIT_GB}GB)')
            print(f'Unpacked {total_unpacked}/{len(zips)} this batch')
            break
        
        base = os.path.splitext(os.path.basename(zp))[0]
        dest = os.path.join(STAGING_DIR, base)
        os.makedirs(dest, exist_ok=True)
        
        count = unpack_zip(zp, dest)
        if count < 0:
            failed.append(zp)
            shutil.rmtree(dest, ignore_errors=True)
            continue
        
        # Dedup within the unpacked dir
        dupes, freed = dedup_directory(dest)
        
        total_unpacked += 1
        total_files += count
        total_deduped += dupes
        total_freed += freed
        
        # Delete the source ZIP after successful unpack
        try:
            os.remove(zp)
        except Exception:
            pass
        
        if (i + 1) % 25 == 0:
            print(f'  Progress: {i+1}/{len(zips)} | Files: {total_files} | Deduped: {total_deduped} | F: free: {get_free_gb("F:"):.1f}GB')
    
    summary = {
        'total_zips_found': len(zips),
        'unpacked': total_unpacked,
        'files_extracted': total_files,
        'duplicates_removed': total_deduped,
        'space_freed_bytes': total_freed,
        'failed': [os.path.basename(f) for f in failed],
        'f_drive_free_gb': round(get_free_gb('F:'), 2)
    }
    
    report_path = os.path.join(STAGING_DIR, '_BATCH_UNPACK_REPORT.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f'\n=== BATCH UNPACK COMPLETE ===')
    print(f'Unpacked: {total_unpacked}/{len(zips)}')
    print(f'Files extracted: {total_files}')
    print(f'Duplicates removed: {total_deduped}')
    print(f'Failed: {len(failed)}')
    print(f'F: drive free: {get_free_gb("F:"):.1f}GB')

if __name__ == '__main__':
    main()
