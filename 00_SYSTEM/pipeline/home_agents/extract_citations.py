#!/usr/bin/env python3
"""
Extract legal citations, violations, dates, and person mentions from documents.
Writes results to D:\LITIGATIONOS_DATA\
"""

import os
import re
import csv
from pathlib import Path
from datetime import datetime
import glob

# Configuration
TEMP_DIR = r"D:\TEMP"
OUTPUT_DIR = r"D:\LITIGATIONOS_DATA"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
MAX_CAPTURES_PER_FILE = 300

# Source directories (non-recursive, top-level only)
SOURCE_DIRS = [
    r"C:\Users\andre\Music",
    r"C:\Users\andre\Scans"
]

# Regex patterns
PATTERNS = {
    'MCR': re.compile(r'MCR\s*(\d{1,2}\.\d{3})'),
    'MCL': re.compile(r'MCL\s*(\d{3,4}\.\d{1,5})'),
    'CASE_LAW': re.compile(r'(\d{1,3})\s+Mich\s+(?:App\s+)?(\d{1,4})'),
    'CANON': re.compile(r'Canon\s+([0-9.]+)'),
    'VIOLATION': re.compile(r'\b(ex parte|bias|misconduct|due process|perjury|fraud|contempt|alienation|domestic violence|retaliation|false statement|abuse of discretion)\b', re.IGNORECASE),
    'DATE': re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b', re.IGNORECASE),
    'PERSON': re.compile(r'\b(Pigors|Watson|McNeill|Rusco|HealthWest|Martini)\b', re.IGNORECASE)
}

# Violation keywords mapping
VIOLATION_KEYWORDS = {
    'ex parte', 'bias', 'misconduct', 'due process', 'perjury', 
    'fraud', 'contempt', 'alienation', 'domestic violence', 
    'retaliation', 'false statement', 'abuse of discretion'
}

def get_context(text, match_start, match_end, context_length=100):
    """Extract context around a match."""
    context_start = max(0, match_start - context_length)
    context_end = min(len(text), match_end + context_length)
    context = text[context_start:context_end].replace('\n', ' ').replace('\r', ' ')
    return context[:200]  # Limit to 200 chars

def extract_from_file(filepath):
    """Extract all citations and violations from a file."""
    citations = []
    violations = []
    dates = []
    persons = []
    
    try:
        # Check file size
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            return citations, violations, dates, persons, f"File too large"
        
        # Read file with error handling
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Extract lines for line number tracking
        lines = content.split('\n')
        
        # Track violations per file (limit to MAX_CAPTURES_PER_FILE)
        violation_count = 0
        date_count = 0
        person_count = 0
        
        # Process each line
        for line_num, line in enumerate(lines, 1):
            # MCR Citations
            for match in PATTERNS['MCR'].finditer(line):
                citations.append({
                    'cite_type': 'MCR',
                    'citation': f"MCR {match.group(1)}",
                    'line_number': line_num,
                    'context': get_context(line, match.start(), match.end())
                })
            
            # MCL Citations
            for match in PATTERNS['MCL'].finditer(line):
                citations.append({
                    'cite_type': 'MCL',
                    'citation': f"MCL {match.group(1)}",
                    'line_number': line_num,
                    'context': get_context(line, match.start(), match.end())
                })
            
            # Case Law
            for match in PATTERNS['CASE_LAW'].finditer(line):
                citations.append({
                    'cite_type': 'CASE_LAW',
                    'citation': f"{match.group(1)} Mich {match.group(2)}",
                    'line_number': line_num,
                    'context': get_context(line, match.start(), match.end())
                })
            
            # Canon References
            for match in PATTERNS['CANON'].finditer(line):
                citations.append({
                    'cite_type': 'CANON',
                    'citation': f"Canon {match.group(1)}",
                    'line_number': line_num,
                    'context': get_context(line, match.start(), match.end())
                })
            
            # Violations (limited to MAX_CAPTURES_PER_FILE)
            if violation_count < MAX_CAPTURES_PER_FILE:
                for match in PATTERNS['VIOLATION'].finditer(line):
                    violation_type = match.group(1).lower()
                    violations.append({
                        'violation_type': violation_type,
                        'line_number': line_num,
                        'context': get_context(line, match.start(), match.end())
                    })
                    violation_count += 1
                    if violation_count >= MAX_CAPTURES_PER_FILE:
                        break
            
            # Dates (limited to MAX_CAPTURES_PER_FILE)
            if date_count < MAX_CAPTURES_PER_FILE:
                for match in PATTERNS['DATE'].finditer(line):
                    dates.append({
                        'date': f"{match.group(1)} {match.group(2)}, {match.group(3)}",
                        'line_number': line_num,
                        'context': get_context(line, match.start(), match.end())
                    })
                    date_count += 1
                    if date_count >= MAX_CAPTURES_PER_FILE:
                        break
            
            # Persons (limited to MAX_CAPTURES_PER_FILE)
            if person_count < MAX_CAPTURES_PER_FILE:
                for match in PATTERNS['PERSON'].finditer(line):
                    persons.append({
                        'person': match.group(1),
                        'line_number': line_num,
                        'context': get_context(line, match.start(), match.end())
                    })
                    person_count += 1
                    if person_count >= MAX_CAPTURES_PER_FILE:
                        break
        
        return citations, violations, dates, persons, None
    
    except Exception as e:
        return citations, violations, dates, persons, str(e)

def main():
    """Main extraction function."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting citation extraction...")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Source directories: {SOURCE_DIRS}")
    print()
    
    # Collect all files
    all_files = []
    for source_dir in SOURCE_DIRS:
        if os.path.isdir(source_dir):
            # Get all .md and .txt files (non-recursive)
            md_files = glob.glob(os.path.join(source_dir, "*.md"))
            txt_files = glob.glob(os.path.join(source_dir, "*.txt"))
            all_files.extend(md_files)
            all_files.extend(txt_files)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(all_files)} files to process")
    print()
    
    # Initialize output writers
    citations_rows = []
    violations_rows = []
    timeline_rows = []
    persons_rows = []
    evidence_rows = []
    
    # Process each file
    for idx, filepath in enumerate(all_files, 1):
        if idx % 100 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing file {idx}/{len(all_files)}: {Path(filepath).name}")
        
        source_dir = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        # Extract from file
        citations, violations, dates, persons, error = extract_from_file(filepath)
        
        if error:
            print(f"  Warning: {filename} - {error}")
            continue
        
        # Write citations
        for cite in citations:
            citations_rows.append({
                'source_file': filename,
                'directory': source_dir,
                'cite_type': cite['cite_type'],
                'citation': cite['citation'],
                'line_number': cite['line_number'],
                'context': cite['context']
            })
        
        # Write violations
        for viol in violations:
            violations_rows.append({
                'source_file': filename,
                'directory': source_dir,
                'violation_type': viol['violation_type'],
                'line_number': viol['line_number'],
                'context': viol['context']
            })
        
        # Write dates
        for date in dates:
            timeline_rows.append({
                'source_file': filename,
                'directory': source_dir,
                'date': date['date'],
                'line_number': date['line_number'],
                'context': date['context']
            })
        
        # Write persons
        for person in persons:
            persons_rows.append({
                'source_file': filename,
                'directory': source_dir,
                'person': person['person'],
                'line_number': person['line_number'],
                'context': person['context']
            })
        
        # Calculate score for evidence index
        score = (len(citations) * 10) + (len(violations) * 3) + len(dates) + (len(persons) * 2)
        evidence_rows.append({
            'source_file': filename,
            'directory': source_dir,
            'citations_count': len(citations),
            'violations_count': len(violations),
            'dates_count': len(dates),
            'persons_count': len(persons),
            'score': score
        })
    
    print()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Writing output files...")
    
    # Write MASTER_CITATIONS.csv
    citations_path = os.path.join(OUTPUT_DIR, "MASTER_CITATIONS.csv")
    with open(citations_path, 'w', newline='', encoding='utf-8') as f:
        if citations_rows:
            writer = csv.DictWriter(f, fieldnames=['source_file', 'directory', 'cite_type', 'citation', 'line_number', 'context'])
            writer.writeheader()
            writer.writerows(citations_rows)
    
    # Write MASTER_VIOLATIONS.csv
    violations_path = os.path.join(OUTPUT_DIR, "MASTER_VIOLATIONS.csv")
    with open(violations_path, 'w', newline='', encoding='utf-8') as f:
        if violations_rows:
            writer = csv.DictWriter(f, fieldnames=['source_file', 'directory', 'violation_type', 'line_number', 'context'])
            writer.writeheader()
            writer.writerows(violations_rows)
    
    # Write MASTER_TIMELINE.csv
    timeline_path = os.path.join(OUTPUT_DIR, "MASTER_TIMELINE.csv")
    with open(timeline_path, 'w', newline='', encoding='utf-8') as f:
        if timeline_rows:
            writer = csv.DictWriter(f, fieldnames=['source_file', 'directory', 'date', 'line_number', 'context'])
            writer.writeheader()
            writer.writerows(timeline_rows)
    
    # Write MASTER_PERSONS.csv
    persons_path = os.path.join(OUTPUT_DIR, "MASTER_PERSONS.csv")
    with open(persons_path, 'w', newline='', encoding='utf-8') as f:
        if persons_rows:
            writer = csv.DictWriter(f, fieldnames=['source_file', 'directory', 'person', 'line_number', 'context'])
            writer.writeheader()
            writer.writerows(persons_rows)
    
    # Write MASTER_EVIDENCE_INDEX.csv
    evidence_path = os.path.join(OUTPUT_DIR, "MASTER_EVIDENCE_INDEX.csv")
    with open(evidence_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['source_file', 'directory', 'citations_count', 'violations_count', 'dates_count', 'persons_count', 'score'])
        writer.writeheader()
        writer.writerows(evidence_rows)
    
    # Print results
    print()
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Files processed: {len(all_files)}")
    print()
    print("OUTPUT FILES:")
    print()
    
    for filepath in [citations_path, violations_path, timeline_path, persons_path, evidence_path]:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            records = lines - 1  # Exclude header
            print(f"  {os.path.basename(filepath)}")
            print(f"    Size: {size:,} bytes ({size/1024:.1f} KB)")
            print(f"    Records: {records:,}")
    
    print()
    print(f"Total citations extracted: {len(citations_rows):,}")
    print(f"Total violations extracted: {len(violations_rows):,}")
    print(f"Total dates extracted: {len(timeline_rows):,}")
    print(f"Total persons extracted: {len(persons_rows):,}")
    print()

if __name__ == "__main__":
    main()
