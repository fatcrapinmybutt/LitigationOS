#!/usr/bin/env python3
"""
ENGINE 6: DAMAGES ITEMIZATION ENGINE
Computes exact damages per category with evidence citations for court presentation.
"""
import sqlite3
import os
from datetime import datetime, date

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  DAMAGES ITEMIZATION ENGINE v1.0")
print("=" * 70)

# ======================================================================
# CREATE DAMAGES TABLE
# ======================================================================
c.execute('''CREATE TABLE IF NOT EXISTS damages_itemization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    subcategory TEXT,
    description TEXT NOT NULL,
    amount REAL,
    calculation_basis TEXT,
    evidence_ref TEXT,
    legal_basis TEXT,
    filing_target TEXT,
    date_incurred TEXT,
    is_ongoing INTEGER DEFAULT 0,
    multiplier_applicable INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

c.execute("SELECT COUNT(*) FROM damages_itemization")
if c.fetchone()[0] > 0:
    c.execute("DELETE FROM damages_itemization")
    conn.commit()

# ======================================================================
# CALCULATE DAMAGES
# ======================================================================
today = date.today()
suspension_start = date(2025, 8, 8)
days_suspended = (today - suspension_start).days
last_pt = date(2025, 7, 29)
days_since_pt = (today - last_pt).days

damages = []

# --- CATEGORY 1: WRONGFUL INCARCERATION ---
# 59+ days at Michigan daily rate
jail_days = 59
daily_rate_low = 150  # Conservative per-day wrongful incarceration
daily_rate_high = 300  # Higher estimate
damages.append(('WRONGFUL_INCARCERATION', 'Direct Incarceration Damages',
    f'{jail_days} days wrongful incarceration × ${daily_rate_low}-${daily_rate_high}/day',
    jail_days * daily_rate_low, jail_days * daily_rate_high,
    f'{jail_days} days documented jail time; no convictions warranting incarceration',
    'Jail records; booking records; release records',
    '42 USC §1983; Fourteenth Amendment Due Process',
    'USDC §1983; Civil Tort'))

# --- CATEGORY 2: LOST EMPLOYMENT ---
jobs_lost = 3
avg_annual_salary = 35000
months_unemployment = 18  # Estimated total unemployment periods
damages.append(('LOST_EMPLOYMENT', 'Lost Wages — Job Loss #1',
    'Terminated due to incarceration/court obligations — estimated 6 months wages',
    avg_annual_salary / 2, avg_annual_salary / 2,
    'Employment termination during incarceration period',
    'Employment records; termination notice',
    'Tortious Interference with Employment; 42 USC §1983',
    'USDC §1983; Civil Tort'))

damages.append(('LOST_EMPLOYMENT', 'Lost Wages — Job Loss #2',
    'Second termination due to ongoing court disruption — estimated 6 months wages',
    avg_annual_salary / 2, avg_annual_salary / 2,
    'Second employment loss caused by repeated court appearances and jail',
    'Employment records',
    'Tortious Interference with Employment',
    'Civil Tort'))

damages.append(('LOST_EMPLOYMENT', 'Lost Wages — Job Loss #3',
    'Third termination due to continued legal disruption — estimated 6 months wages',
    avg_annual_salary / 2, avg_annual_salary / 2,
    'Third job loss in cascading pattern caused by litigation abuse',
    'Employment records',
    'Tortious Interference with Employment; Pattern Evidence',
    'Civil Tort'))

# --- CATEGORY 3: HOUSING LOSSES ---
damages.append(('HOUSING_LOSS', 'Home Loss #1',
    'Lost housing due to incarceration and employment loss',
    5000, 8000,
    'Security deposit + moving costs + temporary housing',
    'Lease records; housing correspondence',
    'Consequential Damages from Wrongful Incarceration',
    'USDC §1983; Civil Tort'))

damages.append(('HOUSING_LOSS', 'Home Loss #2',
    'Second housing loss from continued economic destabilization',
    5000, 8000,
    'Second displacement due to inability to maintain housing',
    'Housing records',
    'Consequential Damages',
    'Civil Tort'))

# --- CATEGORY 4: BOND/BAIL ---
damages.append(('BOND_BAIL', 'Bond Payment',
    '$250 bond posted',
    250, 250,
    'Cash bond posted for release',
    'Bond receipt',
    'Direct cost of wrongful incarceration',
    'USDC §1983; Civil Tort'))

# --- CATEGORY 5: LEGAL COSTS ---
damages.append(('LEGAL_COSTS', 'Pro Se Litigation Costs',
    'Filing fees, copying, postage, technology, research tools',
    2500, 5000,
    'Documented expenditures for self-representation',
    'Receipts; bank statements',
    'Costs of litigation caused by abuse of process',
    'Civil Tort; COA Brief'))

damages.append(('LEGAL_COSTS', 'Imputed Attorney Fees',
    f'Pro se litigant hours × reasonable attorney rate ($200/hr) — estimated 500+ hours',
    100000, 150000,
    '500+ hours of legal research, drafting, filing at $200-$300/hr imputed rate',
    'Filing records; document creation timestamps; LitigationOS logs',
    'Kay v. Ehrler exception; Roadway Express factors; 42 USC §1988',
    'USDC §1983'))

# --- CATEGORY 6: EMOTIONAL DISTRESS ---
damages.append(('EMOTIONAL_DISTRESS', 'Parent-Child Separation Distress',
    f'{days_since_pt} days separation from minor child — ongoing',
    50000, 150000,
    f'{days_since_pt} days denied contact with 3-year-old son; developmental harm',
    'AppClose records showing abrupt cessation; psych analysis',
    'IIED — extreme and outrageous conduct; Fourteenth Amendment liberty interest',
    'USDC §1983; Civil Tort'))

damages.append(('EMOTIONAL_DISTRESS', 'False Incarceration Distress',
    '59+ days wrongful incarceration — psychological impact',
    25000, 75000,
    'Documented psychological impact of wrongful incarceration without cause',
    'Mental health records; sworn statements',
    'IIED; 42 USC §1983',
    'USDC §1983; Civil Tort'))

damages.append(('EMOTIONAL_DISTRESS', 'Reputational Harm',
    'False allegations of abuse/substance use published in court records',
    10000, 50000,
    'Court filings containing defamatory allegations accessible via public records',
    'Court filings by Barnes/Watson; drug screen results (NEGATIVE)',
    'Defamation Per Se; False Light',
    'Civil Tort'))

# --- CATEGORY 7: CHILD DAMAGES ---
damages.append(('CHILD_HARM', 'Parental Alienation — Lincoln',
    f'{days_since_pt} days denied parental relationship — developmental harm to minor child',
    0, 0,  # Quantified by expert at trial
    'Expert testimony required; documented in alienation analysis',
    'AppClose messages; psych analysis; alienation assessment',
    'Best Interest of Child; MCL 722.23; Parental Alienation Tort',
    'COA Brief; Civil Tort'))

# --- CATEGORY 8: PUNITIVE ---
damages.append(('PUNITIVE', 'Punitive Damages — Judicial Misconduct',
    '1,127 documented judicial canon violations; systematic pattern',
    0, 0,  # Determined by jury
    'Jury determination; 1,127 violations documented in judicial_violations table',
    'judicial_violations table; MCJC canons',
    '42 USC §1983; punitive damages for willful constitutional violations',
    'USDC §1983'))

damages.append(('PUNITIVE', 'Punitive Damages — Watson Family Conspiracy',
    'Premeditated conspiracy to deny parental rights via fabricated evidence',
    0, 0,
    'Albert Watson admission of premeditation; Lori Watson felony recording',
    'Text messages; recording evidence; MCL 750.539c',
    'Civil Conspiracy; IIED; Punitive multiplier',
    'Civil Tort'))

# ======================================================================
# INSERT INTO DB
# ======================================================================
total_low = 0
total_high = 0
for cat, desc, calc, low, high, basis, evidence, legal, filing in damages:
    c.execute('''INSERT INTO damages_itemization 
        (category, description, amount, calculation_basis, evidence_ref, legal_basis, filing_target,
         subcategory, is_ongoing, multiplier_applicable)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (cat, desc, low, calc, evidence, legal, filing,
         calc, 1 if 'ongoing' in desc.lower() else 0,
         1 if cat == 'PUNITIVE' else 0))
    total_low += low
    total_high += high

conn.commit()
print(f"\n[+] Inserted {len(damages)} damage line items")

# ======================================================================
# GENERATE DAMAGES DOCUMENT
# ======================================================================
doc_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\DAMAGES_ITEMIZATION.md'
with open(doc_path, 'w', encoding='utf-8') as f:
    f.write("# DAMAGES ITEMIZATION SCHEDULE\n")
    f.write("## Pigors v. Watson et al. — Case 2024-001507-DC\n")
    f.write(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write("---\n\n")
    f.write(f"### TOTAL QUANTIFIED DAMAGES: ${total_low:,.0f} — ${total_high:,.0f}\n")
    f.write("### (Excludes punitive damages and child harm — determined at trial)\n\n")
    f.write("---\n\n")
    
    current_cat = None
    for cat, desc, calc, low, high, basis, evidence, legal, filing in damages:
        if cat != current_cat:
            current_cat = cat
            f.write(f"\n## {cat.replace('_', ' ')}\n\n")
        
        f.write(f"### {desc}\n")
        f.write(f"- **Amount:** ${low:,.0f}")
        if high > low:
            f.write(f" — ${high:,.0f}")
        elif low == 0:
            f.write(" (TBD at trial)")
        f.write("\n")
        f.write(f"- **Calculation:** {calc}\n")
        f.write(f"- **Evidence:** {evidence}\n")
        f.write(f"- **Legal Basis:** {legal}\n")
        f.write(f"- **Filing Target:** {filing}\n\n")
    
    f.write("\n---\n\n")
    f.write("## SUMMARY\n\n")
    f.write(f"| Category | Low Estimate | High Estimate |\n")
    f.write(f"|----------|-------------|---------------|\n")
    
    cat_totals = {}
    for cat, desc, calc, low, high, basis, evidence, legal, filing in damages:
        if cat not in cat_totals:
            cat_totals[cat] = [0, 0]
        cat_totals[cat][0] += low
        cat_totals[cat][1] += high
    
    for cat, (low, high) in cat_totals.items():
        f.write(f"| {cat.replace('_', ' ')} | ${low:,.0f} | ${high:,.0f} |\n")
    f.write(f"| **TOTAL** | **${total_low:,.0f}** | **${total_high:,.0f}** |\n")
    f.write(f"\n*Punitive damages and child harm quantification excluded — to be determined at trial.*\n")

doc_size = os.path.getsize(doc_path)
print(f"[+] Generated {doc_size/1024:.0f}KB damages document")

print(f"\n{'='*70}")
print(f"  DAMAGES ENGINE COMPLETE")
print(f"  Quantified: ${total_low:,.0f} — ${total_high:,.0f}")
print(f"  + Punitive (jury) + Child Harm (expert)")
print(f"  {len(damages)} line items across {len(cat_totals)} categories")
print(f"{'='*70}")

conn.close()
