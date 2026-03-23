#!/usr/bin/env python3
"""
Export Shady Oaks claims to CSV for easy review and analysis
"""
import sqlite3
import csv
import os

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_CSV = r"C:\Users\andre\LitigationOS\00_SYSTEM\SHADY_OAKS_CLAIMS_EXPORT.csv"

def export_claims_to_csv():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return
    
    print(f"Connecting to: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Set pragmas
        cursor.execute("PRAGMA busy_timeout=60000;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA cache_size=-32000;")
        
        # Query all claims from shadyoaks_claim_table
        print("Exporting Shady Oaks claims...")
        cursor.execute("SELECT * FROM shadyoaks_claim_table ORDER BY cl_id")
        rows = cursor.fetchall()
        
        if not rows:
            print("No claims found!")
            return
        
        # Write to CSV
        print(f"Writing {len(rows)} claims to CSV...")
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            columns = [col[0] for col in cursor.description]
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for row in rows:
                writer.writerow(dict(row))
        
        print(f"\n✓ Successfully exported {len(rows)} claims to:")
        print(f"  {OUTPUT_CSV}")
        
        # Print summary
        print("\n" + "="*80)
        print("EXPORT SUMMARY")
        print("="*80)
        print(f"Total Claims: {len(rows)}")
        print(f"Status: All UNVALIDATED")
        print(f"Source: MEEK1_COMPLAINT_MI_CIRCUIT (1).docx")
        
        # Analyze claim types and legal theories
        claim_types = {}
        for row in rows:
            ct = row['claim_type']
            claim_types[ct] = claim_types.get(ct, 0) + 1
        
        print(f"\nClaim Type Distribution:")
        for ct, count in sorted(claim_types.items()):
            print(f"  {ct}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    export_claims_to_csv()
