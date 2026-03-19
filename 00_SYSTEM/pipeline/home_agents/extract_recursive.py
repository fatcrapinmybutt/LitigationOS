#!/usr/bin/env python3
"""
Optimized recursive extraction script with buffering and efficient processing.
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime
import sys

# === Configuration ===
SOURCE_DIRS = [
    'C:\\Users\\andre\\Music',
    'C:\\Users\\andre\\Scans'
]
OUTPUT_DIR = 'D:\\LITIGATIONOS_DATA'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MIN_FILE_SIZE = 50  # bytes
SKIP_PATTERNS = ['fredprime-legal-system', 'czkawka-master', 'node_modules', '.git', '__pycache__']
PROGRESS_INTERVAL = 500
FLUSH_INTERVAL = 500

# === Regex patterns (pre-compiled for speed) ===
CITATION_REGEX = re.compile(r'\b(?:U\.S\.|U\.S\.C\.|Fed\.|App\.|D\.?C\.|Cir\.|No\.?|v\.)\b|\b\d+\s+U\.S\.\s+\d+\b|\b\d+\s+F\.\d*d\s+\d+\b|\b\d+\s+F\.\s+Supp\.\s+\d+\b', re.IGNORECASE)
VIOLATION_REGEX = re.compile(r'(?:violation|breach|infringement|violation of|failed to|failure to|unauthorized|illegal|unlawful|prohibited|non-?complian(?:ce|t))', re.IGNORECASE)
DATE_REGEX = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b', re.IGNORECASE)
PERSON_REGEX = re.compile(r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b(?=\s+(?:said|stated|argued|testified|claimed|denied|admitted))')

def is_top_level_file(file_path):
    """Check if file's parent directory is exactly 'Music' or 'Scans'"""
    parent_name = Path(file_path).parent.name.lower()
    return parent_name in ['music', 'scans']

def should_skip(file_path):
    """Check if file should be skipped"""
    path_str = str(file_path).lower()
    
    # Check skip patterns
    for pattern in SKIP_PATTERNS:
        if pattern.lower() in path_str:
            return True
    
    # Check file size
    try:
        size = os.path.getsize(file_path)
        if size > MAX_FILE_SIZE or size < MIN_FILE_SIZE:
            return True
    except:
        return True
    
    return False

def find_recursive_files():
    """Find all .md and .txt files recursively"""
    files = []
    for source_dir in SOURCE_DIRS:
        if not os.path.exists(source_dir):
            print(f"Directory not found: {source_dir}", file=sys.stderr)
            continue
        
        for root, dirs, filenames in os.walk(source_dir):
            # Skip unwanted directories in-place
            dirs[:] = [d for d in dirs if not any(skip.lower() in d.lower() for skip in SKIP_PATTERNS)]
            
            for filename in filenames:
                if not filename.lower().endswith(('.md', '.txt')):
                    continue
                
                file_path = os.path.join(root, filename)
                
                # Skip top-level files
                if is_top_level_file(file_path):
                    continue
                
                # Skip based on filtering rules
                if should_skip(file_path):
                    continue
                
                files.append(file_path)
    
    return files

def get_context(text, match_start, match_end, max_len=200):
    """Extract context around match"""
    start = max(0, match_start - 50)
    end = min(len(text), match_end + 50)
    context = text[start:end].replace('\n', ' ').strip()
    return context[:max_len] if context else ''

def process_file(file_path):
    """Process a single file and extract all data"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except:
        return None
    
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    
    # Extract citations
    citations = []
    for match in CITATION_REGEX.finditer(text):
        line_num = text[:match.start()].count('\n') + 1
        context = get_context(text, match.start(), match.end())
        citations.append({
            'source_file': filename,
            'directory': directory,
            'cite_type': 'citation',
            'citation': match.group(0),
            'line_number': line_num,
            'context': context
        })
    
    # Extract violations (limit 100)
    violations = []
    for match in list(VIOLATION_REGEX.finditer(text))[:100]:
        line_num = text[:match.start()].count('\n') + 1
        context = get_context(text, match.start(), match.end())
        violations.append({
            'source_file': filename,
            'directory': directory,
            'violation_type': match.group(0),
            'line_number': line_num,
            'context': context
        })
    
    # Extract dates (limit 100)
    dates = []
    for match in list(DATE_REGEX.finditer(text))[:100]:
        line_num = text[:match.start()].count('\n') + 1
        context = get_context(text, match.start(), match.end())
        dates.append({
            'source_file': filename,
            'directory': directory,
            'date': match.group(0),
            'line_number': line_num,
            'context': context
        })
    
    # Extract persons (limit 100)
    persons = []
    for match in list(PERSON_REGEX.finditer(text))[:100]:
        line_num = text[:match.start()].count('\n') + 1
        context = get_context(text, match.start(), match.end())
        persons.append({
            'source_file': filename,
            'directory': directory,
            'person': match.group(0),
            'line_number': line_num,
            'context': context
        })
    
    # Evidence index
    score = len(citations) * 2 + len(violations) * 3 + len(dates) * 1.5 + len(persons) * 2
    evidence = {
        'source_file': filename,
        'directory': directory,
        'citations_count': len(citations),
        'violations_count': len(violations),
        'dates_count': len(dates),
        'persons_count': len(persons),
        'score': score
    }
    
    return {
        'citations': citations,
        'violations': violations,
        'dates': dates,
        'persons': persons,
        'evidence': evidence
    }

def main():
    print(f"Starting recursive extraction at {datetime.now()}")
    print(f"Output directory: {OUTPUT_DIR}")
    sys.stdout.flush()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find all files
    print("Discovering files...", flush=True)
    files = find_recursive_files()
    print(f"Found {len(files)} files to process", flush=True)
    print()
    
    if not files:
        print("No files to process.")
        return
    
    # Open CSV files in append mode
    citations_file = open(os.path.join(OUTPUT_DIR, 'MASTER_CITATIONS.csv'), 'a', newline='', encoding='utf-8', buffering=1)
    violations_file = open(os.path.join(OUTPUT_DIR, 'MASTER_VIOLATIONS.csv'), 'a', newline='', encoding='utf-8', buffering=1)
    dates_file = open(os.path.join(OUTPUT_DIR, 'MASTER_TIMELINE.csv'), 'a', newline='', encoding='utf-8', buffering=1)
    persons_file = open(os.path.join(OUTPUT_DIR, 'MASTER_PERSONS.csv'), 'a', newline='', encoding='utf-8', buffering=1)
    evidence_file = open(os.path.join(OUTPUT_DIR, 'MASTER_EVIDENCE_INDEX.csv'), 'a', newline='', encoding='utf-8', buffering=1)
    
    citations_writer = csv.DictWriter(citations_file, fieldnames=['source_file', 'directory', 'cite_type', 'citation', 'line_number', 'context'])
    violations_writer = csv.DictWriter(violations_file, fieldnames=['source_file', 'directory', 'violation_type', 'line_number', 'context'])
    dates_writer = csv.DictWriter(dates_file, fieldnames=['source_file', 'directory', 'date', 'line_number', 'context'])
    persons_writer = csv.DictWriter(persons_file, fieldnames=['source_file', 'directory', 'person', 'line_number', 'context'])
    evidence_writer = csv.DictWriter(evidence_file, fieldnames=['source_file', 'directory', 'citations_count', 'violations_count', 'dates_count', 'persons_count', 'score'])
    
    # Counters
    total_files = 0
    total_citations = 0
    total_violations = 0
    total_dates = 0
    total_persons = 0
    
    # Process files
    for idx, file_path in enumerate(files, 1):
        try:
            result = process_file(file_path)
            if not result:
                continue
            
            # Write all extracted data
            for row in result['citations']:
                citations_writer.writerow(row)
                total_citations += 1
            
            for row in result['violations']:
                violations_writer.writerow(row)
                total_violations += 1
            
            for row in result['dates']:
                dates_writer.writerow(row)
                total_dates += 1
            
            for row in result['persons']:
                persons_writer.writerow(row)
                total_persons += 1
            
            evidence_writer.writerow(result['evidence'])
            
            total_files += 1
            
            # Progress report
            if idx % PROGRESS_INTERVAL == 0:
                print(f"Progress: {idx}/{len(files)} | Files: {total_files} | C: {total_citations} | V: {total_violations} | D: {total_dates} | P: {total_persons}", flush=True)
            
            # Flush CSVs
            if idx % FLUSH_INTERVAL == 0:
                citations_file.flush()
                violations_file.flush()
                dates_file.flush()
                persons_file.flush()
                evidence_file.flush()
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr, flush=True)
            continue
    
    # Close files
    citations_file.close()
    violations_file.close()
    dates_file.close()
    persons_file.close()
    evidence_file.close()
    
    # Print final totals
    print()
    print("=" * 70)
    print(f"Extraction completed at {datetime.now()}")
    print(f"Files processed: {total_files}")
    print(f"Total citations: {total_citations}")
    print(f"Total violations: {total_violations}")
    print(f"Total dates: {total_dates}")
    print(f"Total persons: {total_persons}")
    print(f"Evidence records: {total_files}")
    print("=" * 70)
    sys.stdout.flush()

if __name__ == '__main__':
    main()
