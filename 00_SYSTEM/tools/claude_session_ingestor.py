#!/usr/bin/env python3
r"""
Claude/Copilot Session Evidence Ingestor
Catalogs all conversation session data for litigation context.
Database: C:\Users\andre\LitigationOS\litigation_context.db
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import glob
import json
import re

# CRITICAL: Proper stdout encoding
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# Database connection with robust settings
DB_PATH = r'C:\Users\andre\LitigationOS\litigation_context.db'
db = sqlite3.connect(DB_PATH)
db.execute('PRAGMA busy_timeout=60000')
db.execute('PRAGMA journal_mode=WAL')
db.execute('PRAGMA cache_size=-32000')
db.row_factory = sqlite3.Row

def init_database():
    """Create schema if not exists."""
    db.execute('''
    CREATE TABLE IF NOT EXISTS claude_session_evidence (
        id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE,
        file_name TEXT,
        file_type TEXT,
        source TEXT,
        size_bytes INTEGER,
        content_preview TEXT,
        session_date TEXT,
        topic TEXT,
        ingested_at TEXT
    )
    ''')
    db.commit()
    print("[DB] Schema initialized")

def extract_topic_from_filename(filename):
    """Extract topic from filename."""
    # Remove extensions and common prefixes
    name = Path(filename).stem
    name = re.sub(r'^(checkpoint|session|conversation|export|chat)[-_]*', '', name, flags=re.I)
    name = re.sub(r'[-_]', ' ', name)
    return name[:80] if name else "Unknown"

def extract_topic_from_content(content, filename):
    """Extract topic from first line or metadata."""
    lines = content.split('\n', 10)
    
    for line in lines:
        line = line.strip()
        # Skip markdown headers and formatting
        if line.startswith('#'):
            return line.replace('#', '').strip()[:80]
        if line and len(line) > 10 and len(line) < 200:
            return line[:80]
    
    return extract_topic_from_filename(filename)

def extract_preview(content):
    """Extract first 500 chars as preview."""
    # Remove excessive whitespace and newlines
    content = content.replace('\n', ' ').replace('\r', '')
    content = re.sub(r'\s+', ' ', content)
    return content[:500] if len(content) > 500 else content

def get_file_date(file_path):
    """Extract date from file properties or filename."""
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).isoformat()
    except:
        return None

def identify_source(file_path, content=""):
    """Identify conversation source from path and content."""
    path_lower = file_path.lower()
    content_lower = content.lower()
    
    if 'copilot' in path_lower or '.copilot' in path_lower:
        return 'copilot'
    elif 'chatgpt' in path_lower or 'chatgpt' in content_lower:
        return 'chatgpt'
    elif 'claude' in path_lower or 'anthropic' in path_lower or 'claude' in content_lower:
        return 'claude'
    elif 'gpt' in path_lower or 'openai' in path_lower:
        return 'chatgpt'
    else:
        return 'unknown'

def read_file_content(file_path):
    """Safely read file content."""
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except:
        try:
            # Fallback to latin-1
            with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
                return f.read()
        except:
            return ""

def process_file(file_path):
    """Process single file and insert into database."""
    try:
        if not os.path.isfile(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False
        
        file_name = os.path.basename(file_path)
        file_type = Path(file_path).suffix.lower() or 'unknown'
        
        # Read content
        content = read_file_content(file_path)
        if not content:
            return False
        
        # Identify source
        source = identify_source(file_path, content)
        
        # Extract metadata
        preview = extract_preview(content)
        topic = extract_topic_from_content(content, file_name)
        session_date = get_file_date(file_path)
        ingested_at = datetime.now().isoformat()
        
        # Insert with conflict handling
        try:
            db.execute('''
            INSERT OR IGNORE INTO claude_session_evidence 
            (file_path, file_name, file_type, source, size_bytes, 
             content_preview, session_date, topic, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, file_name, file_type, source, file_size, 
                  preview, session_date, topic, ingested_at))
            return True
        except sqlite3.IntegrityError:
            return False
        
    except Exception as e:
        print(f"[ERROR] Processing {file_path}: {e}")
        return False

def scan_directory(pattern):
    """Scan directory with glob pattern."""
    try:
        return glob.glob(pattern, recursive=True)
    except:
        return []

def main():
    print("=" * 80)
    print("Claude/Copilot Session Evidence Ingestor")
    print("=" * 80)
    print()
    
    # Initialize database
    init_database()
    print()
    
    # Define scan patterns
    scan_patterns = [
        # Copilot session checkpoints and plans
        (r'C:\Users\andre\.copilot\session-state\**\*.md', 'Copilot session state'),
        (r'C:\Users\andre\.copilot\session-state\*\checkpoints\*.md', 'Copilot checkpoints'),
        
        # LitigationOS reports
        (r'C:\Users\andre\LitigationOS\00_SYSTEM\reports\*', 'LitigationOS reports'),
        
        # Desktop, Downloads, Documents searches
        (r'C:\Users\andre\Desktop\*claude*', 'Desktop (claude search)'),
        (r'C:\Users\andre\Desktop\*anthropic*', 'Desktop (anthropic search)'),
        (r'C:\Users\andre\Desktop\*chatgpt*', 'Desktop (chatgpt search)'),
        (r'C:\Users\andre\Desktop\*conversation*', 'Desktop (conversation search)'),
        
        (r'C:\Users\andre\Downloads\*claude*', 'Downloads (claude search)'),
        (r'C:\Users\andre\Downloads\*anthropic*', 'Downloads (anthropic search)'),
        (r'C:\Users\andre\Downloads\*chatgpt*', 'Downloads (chatgpt search)'),
        (r'C:\Users\andre\Downloads\*conversation*', 'Downloads (conversation search)'),
        
        (r'C:\Users\andre\Documents\*claude*', 'Documents (claude search)'),
        (r'C:\Users\andre\Documents\*anthropic*', 'Documents (anthropic search)'),
        (r'C:\Users\andre\Documents\*chatgpt*', 'Documents (chatgpt search)'),
        (r'C:\Users\andre\Documents\*conversation*', 'Documents (conversation search)'),
        
        # ChatGPT exports
        (r'I:\CHATGPTchats\*', 'ChatGPT export directory'),
        (r'I:\LitigationOS_Cleanup*\temp\chatgpt_extracts\*', 'Extracted ChatGPT conversations'),
    ]
    
    stats = {
        'total': 0,
        'processed': 0,
        'by_source': {},
        'by_type': {}
    }
    
    # Process each scan pattern
    for pattern, description in scan_patterns:
        files = scan_directory(pattern)
        if not files:
            print(f"[SCAN] {description}: no files found")
            continue
        
        print(f"[SCAN] {description}: {len(files)} file(s)")
        
        for file_path in files:
            # Only process specific file types
            if not any(file_path.lower().endswith(ext) for ext in ['.md', '.txt', '.json', '.html', '.csv', '.log']):
                continue
            
            stats['total'] += 1
            if process_file(file_path):
                stats['processed'] += 1
                
                # Get source for stats
                content = read_file_content(file_path)
                source = identify_source(file_path, content)
                stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
                
                # Get type for stats
                file_type = Path(file_path).suffix.lower() or 'unknown'
                stats['by_type'][file_type] = stats['by_type'].get(file_type, 0) + 1
    
    db.commit()
    
    # Print summary
    print()
    print("=" * 80)
    print("INGESTION SUMMARY")
    print("=" * 80)
    print(f"Total files processed:  {stats['total']}")
    print(f"Successfully ingested:  {stats['processed']}")
    print()
    
    print("By Source:")
    for source, count in sorted(stats['by_source'].items()):
        print(f"  {source:15} {count:3} file(s)")
    print()
    
    print("By File Type:")
    for file_type, count in sorted(stats['by_type'].items()):
        print(f"  {file_type:15} {count:3} file(s)")
    print()
    
    # Database verification
    cursor = db.execute('SELECT COUNT(*) as count FROM claude_session_evidence')
    total_in_db = cursor.fetchone()[0]
    print(f"Total records in database: {total_in_db}")
    print()
    
    # Show sample records
    print("Sample Records (first 10):")
    print("-" * 80)
    cursor = db.execute('''
    SELECT id, file_name, source, topic, session_date 
    FROM claude_session_evidence 
    ORDER BY ingested_at DESC 
    LIMIT 10
    ''')
    
    for row in cursor.fetchall():
        print(f"  ID: {row['id']}")
        print(f"  File: {row['file_name']}")
        print(f"  Source: {row['source']}")
        print(f"  Topic: {row['topic']}")
        print(f"  Date: {row['session_date']}")
        print()
    
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print("Ingestor complete.")
    print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    finally:
        db.close()
