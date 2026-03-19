import sqlite3

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

print("=" * 100)
print("DETAILED ANALYSIS OF KEY FOCUS AREA TABLES")
print("=" * 100)

# Get comprehensive stats on violation-related tables
violation_tables = [
    'judicial_violations',
    'constitutional_violations', 
    'actor_violations',
    'appclose_violations',
    'auth_benchbook_violations',
    'berry_ethics_violations',
    'ppo_violations',
    'housing_violations',
    'global_harms_violations',
    'master_violations_parsed'
]

print("\n" + "=" * 50)
print("VIOLATION TABLES ANALYSIS")
print("=" * 50)

for table in violation_tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n{table} ({count} records)")
            print("  Columns:")
            for row in schema[:8]:  # First 8 columns
                print(f"    - {row[1]} ({row[2]})")
    except Exception as e:
        pass

# Analyze accusation and rebuttal tables
print("\n\n" + "=" * 50)
print("ACCUSATION & REBUTTAL ANALYSIS")
print("=" * 50)

accusation_tables = [
    'hypervisor_c11_accusation_index',
    'hypervisor_c11_rebuttal_microbriefs',
    'rebuttal_matrix',
    'watson_perjury_compilation',
    'police_report_analysis',
    'police_report_chronology'
]

for table in accusation_tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n{table} ({count} records)")
            print("  Columns:")
            for row in schema[:6]:
                print(f"    - {row[1]} ({row[2]})")
    except Exception as e:
        pass

# Case law tables
print("\n\n" + "=" * 50)
print("CASE LAW & CONSTITUTIONAL AUTHORITY")
print("=" * 50)

caselaw_tables = [
    'caselaw_due_process_custody',
    'caselaw_federal_civil_rights',
    'caselaw_parental_alienation',
    'caselaw_ppo_abuse'
]

for table in caselaw_tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n{table} ({count} records)")
            print("  Columns:")
            for row in schema[:6]:
                print(f"    - {row[1]} ({row[2]})")
    except Exception as e:
        pass

# Harm analysis tables
print("\n\n" + "=" * 50)
print("HARM ANALYSIS TABLES")
print("=" * 50)

harm_tables = [
    'adversary_harm_summary',
    'extracted_harms',
    'psychological_harm_docs',
    'harm_severity_heatmap'
]

for table in harm_tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n{table} ({count} records)")
            print("  Columns:")
            for row in schema[:6]:
                print(f"    - {row[1]} ({row[2]})")
    except Exception as e:
        pass

# Pattern tables
print("\n\n" + "=" * 50)
print("PATTERN ANALYSIS")
print("=" * 50)

pattern_tables = [
    'alienation_tactics',
    'alienation_scoring',
    'chronological_misconduct',
    'violation_patterns',
    'system_error_patterns',
    'parental_alienation_evidence',
    'omega_violation_analysis',
    'omega_evidence_patterns'
]

for table in pattern_tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        schema = cur.fetchall()
        if schema:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"\n{table} ({count} records)")
            print("  Columns:")
            for row in schema[:6]:
                print(f"    - {row[1]} ({row[2]})")
    except Exception as e:
        pass

conn.close()
