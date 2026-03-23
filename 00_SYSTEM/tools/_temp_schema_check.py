import sqlite3
import sys
import os

# Set UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Set PRAGMAs
    cursor.execute("PRAGMA busy_timeout=60000")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-32000")
    
    print("="*80)
    print("DATABASE SCHEMA ANALYSIS")
    print("="*80)
    print(f"Database: {db_path}")
    print()
    
    # List ALL tables
    print("ALL TABLES IN DATABASE:")
    print("-"*80)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall()]
    for table_name in all_tables:
        print(f"  - {table_name}")
    print()
    
    # Specific tables to analyze
    specific_tables = [
        'evidence_quotes',
        'claims',
        'judicial_violations',
        'docket_events',
        'documents',
        'deadlines',
        'authority_chains',
        'witnesses',
        'testimony',
        'custody_factors',
        'best_interest_factors',
        'witness_statements',
        'witness_credibility',
        'contradictions',
        'hearings',
        'evidence',
        'mcr_violations',
        'canon_violations',
        'judicial_findings',
        'risk_events',
        'filing_readiness',
        'case_timeline',
        'timeline_events',
        'law_enforcement',
        'investigations',
        'alienation',
        'bias_indicators'
    ]
    
    print("="*80)
    print("DETAILED SCHEMA FOR SPECIFIC TABLES")
    print("="*80)
    print()
    
    for table_name in specific_tables:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone():
            print(f"\n{'='*80}")
            print(f"TABLE: {table_name}")
            print(f"{'='*80}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\nColumns:")
            print("-"*80)
            for col_id, col_name, col_type, not_null, default_val, pk in columns:
                pk_marker = " [PK]" if pk else ""
                nn_marker = " [NOT NULL]" if not_null else ""
                print(f"  {col_id:2d}. {col_name:30s} {col_type:15s}{pk_marker}{nn_marker}")
                if default_val:
                    print(f"      Default: {default_val}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nRow count: {count}")
        else:
            print(f"\n{'='*80}")
            print(f"TABLE: {table_name}")
            print(f"{'='*80}")
            print("  [TABLE NOT FOUND IN DATABASE]")
    
    print(f"\n{'='*80}")
    print("END OF SCHEMA ANALYSIS")
    print(f"{'='*80}")
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
