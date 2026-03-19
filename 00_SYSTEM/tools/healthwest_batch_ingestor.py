#!/usr/bin/env python3
"""
HealthWest Evidence Batch Ingestor
Ingests all HealthWest medical evaluation files into litigation_context.db
Pro se litigant: Andrew Pigors | Custody case medical records
"""

import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3
import os
from pathlib import Path
import json
from datetime import datetime
import re
from collections import defaultdict

# ============================================================================
# Configuration
# ============================================================================
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'

SCAN_LOCATIONS = [
    # Local SSD
    (r'C:\Users\andre\LitigationOS\07_PDF', 'healthwest*.pdf', 'C:'),
    (r'C:\Users\andre\LitigationOS\01_FILINGS\EMERGENCY', 'Healthwest*', 'C:'),
    (r'C:\Users\andre\LitigationOS\00_SYSTEM\reports', 'healthwest*', 'C:'),
    
    # External D: drive
    (r'D:\LitigationOS_Extracted', 'HEALTHWEST_*.txt', 'D:'),
    
    # External F: drive (emails, manifests, events)
    (r'F:\data', '*ealthwest*', 'F:'),
    (r'F:\19_MISC', '*ealthwest*', 'F:'),
    
    # External I: drive (TEXT PDFs)
    (r'I:\!!!TEXT!!!\pdf', 'healthwest*', 'I:'),
    (r'I:\!!!TEXT!!!\pdf', 'Exhibit_M*', 'I:'),
    (r'I:\!!!TEXT!!!\pdf', 'Gmail*Healthwest*', 'I:'),
    (r'I:\CHATGPTchats', 'Healthwest*.zip', 'I:'),
]

# ============================================================================
# Utility Functions
# ============================================================================

def get_file_type(filepath):
    """Determine file type based on extension."""
    ext = Path(filepath).suffix.lower()
    ext_map = {
        '.pdf': 'pdf',
        '.txt': 'txt',
        '.md': 'txt',
        '.json': 'json',
        '.eml': 'eml',
        '.csv': 'csv',
        '.zip': 'zip',
        '.msg': 'msg',
    }
    return ext_map.get(ext, 'unknown')

def extract_text_preview(filepath, file_type):
    """Extract text preview (first 500 chars) based on file type."""
    try:
        if file_type == 'txt' or file_type == 'unknown':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(500)
        
        elif file_type == 'json':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)[:500]
        
        elif file_type == 'eml':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(500)
        
        elif file_type == 'csv':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(500)
        
        elif file_type == 'pdf':
            try:
                import fitz
                doc = fitz.open(filepath)
                if len(doc) > 0:
                    text = doc[0].get_text()[:500]
                    doc.close()
                    return text
            except Exception:
                return f"[PDF - {os.path.getsize(filepath)} bytes]"
        
        elif file_type == 'zip':
            return f"[ZIP archive - {os.path.getsize(filepath)} bytes]"
        
        elif file_type == 'msg':
            return f"[Outlook MSG - {os.path.getsize(filepath)} bytes]"
        
        return ""
    except Exception as e:
        return f"[Error reading preview: {str(e)[:100]}]"

def extract_metadata(filepath, filename):
    """Extract metadata from filename and content."""
    metadata = {
        'evaluation_number': None,
        'evaluator': None,
        'date': None,
        'finding': None,
    }
    
    # Look for patterns like "1st", "2nd", "first", "second"
    if re.search(r'\b1st\b|\bfirst\b', filename, re.I):
        metadata['evaluation_number'] = '1st'
    elif re.search(r'\b2nd\b|\bsecond\b', filename, re.I):
        metadata['evaluation_number'] = '2nd'
    
    # Look for evaluator names (common in HealthWest files)
    evaluator_patterns = [
        r'Dr\.?\s+([A-Za-z]+)',
        r'by\s+([A-Za-z\s]+?)(?:\s+\d{4}|\s*$)',
    ]
    for pattern in evaluator_patterns:
        match = re.search(pattern, filename, re.I)
        if match:
            metadata['evaluator'] = match.group(1).strip()
            break
    
    # Look for dates (YYYY-MM-DD or MM/DD/YYYY)
    date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})'
    match = re.search(date_pattern, filename)
    if match:
        metadata['date'] = match.group(1)
    
    return metadata

# ============================================================================
# Database Setup
# ============================================================================

def init_database():
    """Initialize database with CRITICAL settings."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA cache_size=-32000')
    
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS healthwest_evidence (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            source_drive TEXT NOT NULL,
            size_bytes INTEGER,
            content_preview TEXT,
            evaluation_number TEXT,
            evaluator TEXT,
            date TEXT,
            finding TEXT,
            lane TEXT DEFAULT 'A',
            ingested_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    return conn

# ============================================================================
# Scan and Ingest
# ============================================================================

def scan_and_ingest(conn):
    """Scan all locations and ingest files."""
    
    stats = {
        'total_found': 0,
        'total_ingested': 0,
        'by_drive': defaultdict(int),
        'by_type': defaultdict(int),
        'by_location': defaultdict(int),
        'errors': [],
    }
    
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    for location, pattern, drive in SCAN_LOCATIONS:
        location_path = Path(location)
        
        if not location_path.exists():
            stats['errors'].append(f"Location does not exist: {location}")
            continue
        
        try:
            # Find matching files
            files = list(location_path.glob(pattern))
            
            for filepath in files:
                if not filepath.is_file():
                    continue
                
                stats['total_found'] += 1
                file_path_str = str(filepath)
                filename = filepath.name
                file_type = get_file_type(file_path_str)
                size_bytes = filepath.stat().st_size
                
                # Extract content preview
                content_preview = extract_text_preview(file_path_str, file_type)
                
                # Extract metadata
                metadata = extract_metadata(file_path_str, filename)
                
                # Insert into database
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO healthwest_evidence
                        (file_path, file_name, file_type, source_drive, size_bytes, 
                         content_preview, evaluation_number, evaluator, date, finding, ingested_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_path_str,
                        filename,
                        file_type,
                        drive,
                        size_bytes,
                        content_preview,
                        metadata['evaluation_number'],
                        metadata['evaluator'],
                        metadata['date'],
                        metadata['finding'],
                        now,
                    ))
                    
                    if cursor.rowcount > 0:
                        stats['total_ingested'] += 1
                        stats['by_drive'][drive] += 1
                        stats['by_type'][file_type] += 1
                        stats['by_location'][location] += 1
                
                except sqlite3.Error as e:
                    stats['errors'].append(f"DB insert error for {filename}: {str(e)[:100]}")
        
        except Exception as e:
            stats['errors'].append(f"Scan error for {location}: {str(e)[:100]}")
    
    conn.commit()
    return stats

# ============================================================================
# Reporting
# ============================================================================

def print_summary(stats):
    """Print ingestion summary."""
    print("\n" + "="*70)
    print("HEALTHWEST EVIDENCE BATCH INGESTOR - SUMMARY")
    print("="*70)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total files found:     {stats['total_found']}")
    print(f"   Total files ingested:  {stats['total_ingested']}")
    
    if stats['by_drive']:
        print(f"\n💾 BY DRIVE:")
        for drive, count in sorted(stats['by_drive'].items()):
            print(f"   {drive}  {count} files")
    
    if stats['by_type']:
        print(f"\n📁 BY FILE TYPE:")
        for ftype, count in sorted(stats['by_type'].items()):
            print(f"   {ftype:10s}  {count} files")
    
    if stats['by_location']:
        print(f"\n📍 BY LOCATION:")
        for location, count in sorted(stats['by_location'].items()):
            print(f"   {location:50s}  {count} files")
    
    if stats['errors']:
        print(f"\n⚠️  ERRORS ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:  # Show first 10
            print(f"   • {error}")
        if len(stats['errors']) > 10:
            print(f"   ... and {len(stats['errors']) - 10} more errors")
    
    print("\n" + "="*70)
    print(f"✅ Ingest complete. Database: {DB_PATH}")
    print("="*70 + "\n")

# ============================================================================
# Main
# ============================================================================

def main():
    print("\n🔄 INITIALIZING HEALTHWEST BATCH INGESTOR...")
    print(f"   Database: {DB_PATH}")
    
    # Initialize database
    conn = init_database()
    print("✅ Database initialized")
    
    # Scan and ingest
    print("\n🔍 SCANNING ALL HEALTHWEST LOCATIONS...")
    stats = scan_and_ingest(conn)
    conn.close()
    
    # Print summary
    print_summary(stats)

if __name__ == '__main__':
    main()
