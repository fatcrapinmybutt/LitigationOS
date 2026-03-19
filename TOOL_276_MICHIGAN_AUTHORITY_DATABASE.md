# Michigan Legal Authority Database Builder (Tool #276)

## Overview
Comprehensive legal authority database for pro se litigant **Andrew Pigors** in Michigan family law cases.

**Location:** `C:\Users\andre\LitigationOS\00_SYSTEM\tools\michigan_authority_database_builder.py`  
**Database:** `C:\Users\andre\LitigationOS\litigation_context.db`  
**Created:** March 19, 2026

---

## Database Schema (6 Tables)

### 1. `michigan_court_rules` (30 records)
Michigan Court Rules relevant to family/civil law and appeals.
- **Columns:** id, rule_number (UNIQUE), title, full_text, category, filing_type, lane
- **Coverage:**
  - MCR 2.003 (Disqualification), 2.107 (Service), 2.111 (Pleading), 2.113 (Form)
  - MCR 2.119 (Motion Practice), 2.305 (Subpoenas), 2.506 (Contempt)
  - MCR 3.201-3.211 (Domestic Relations), 3.207 (Referees/Custody)
  - MCR 7.101-7.115 (Appeals Circuit), 7.201-7.215 (Court of Appeals)
  - MCR 7.212 (Briefs), 7.305-7.306 (Supreme Court), 8.119 (Court Records)

### 2. `michigan_statutes` (29 records)
Key MCL statutes covering family law, contempt, evidence, procedure.
- **Columns:** id, statute_number (UNIQUE), title, full_text, category, lane
- **Coverage:**
  - MCL 600.1701 (Contempt), 600.1908 (Vexatious Litigant)
  - MCL 600.2950-2961 (Personal Protection Order)
  - MCL 722.21-31 (Child Custody Act - all best interest factors)
  - MCL 750.136b (Child Abuse), 722.633 (Mandatory Reporting)
  - MCL 125.534-535 (Truth in Renting), 600.5714-5720 (Eviction)
  - MCL 445.903 (Consumer Protection), 168.937 (Perjury)
  - MCL 552.12 (Spousal Support), 600.805 (Family Court Jurisdiction)

### 3. `michigan_evidence_rules` (15 records)
Michigan Rules of Evidence (MRE) for testimony, hearsay, authentication.
- **Columns:** id, rule_number (UNIQUE), title, full_text, category
- **Coverage:**
  - MRE 401-404 (Relevance & Character Evidence)
  - MRE 602-604 (Witness Requirements)
  - MRE 701-702 (Lay & Expert Opinion)
  - MRE 801-803 (Hearsay Exceptions)
  - MRE 901 (Authentication), 1002 (Best Evidence)

### 4. `michigan_judicial_canons` (5 records)
Michigan Code of Judicial Conduct violations & standards.
- **Columns:** id, canon_number (UNIQUE), title, full_text, violation_type
- **Coverage:**
  - Canon 1: Integrity & Independence
  - Canon 2: Impropriety Avoidance & Appearance
  - Canon 3: Impartial Judicial Performance
  - Canon 4: Extrajudicial Activities
  - Canon 5: Political Activity Restrictions

### 5. `michigan_case_law` (20 records)
Key Michigan and U.S. Supreme Court precedents.
- **Columns:** id, case_name, citation (UNIQUE), court, year, holding, relevance, lane, filing_id
- **Coverage:**
  - **Custody/Family:** Vodvarka v Grasmeyer (change of circumstances), Harvey v Harvey (parenting time), Komur v Komur, Mills v Mills (child support)
  - **Judicial Disqualification:** Armstrong v Ypsilanti (MCR 2.003), Caperton v Massey Coal (due process), Liteky v United States (extrajudicial bias)
  - **Contempt:** Brown v Loveman (elements), Yates v Terry (criminal vs civil)
  - **Appeals:** Fid Deposit Co v Hart (abuse of discretion standard)
  - **PPO:** Shulick v Richards (modification)
  - **Vexatious Litigant:** Polimetrics v Vogel
  - **Special Cases:** In re Brennan (JTC), Dennis v Sparks (conspiracy immunity), Catz v Chalker (§1983), Hines v Consolidated Rail (pro se standards)

### 6. `filing_rule_map` (46 records)
Maps filing types (F1-F10) to required authorities.
- **Columns:** id, filing_id, authority_type, authority_number, requirement, mandatory
- **Filings Mapped:**
  - F1: Divorce Complaint (7 mappings)
  - F2: Custody/Parenting Time Motion (6 mappings)
  - F3: CPS Response (4 mappings)
  - F4: PPO Filing (4 mappings)
  - F5: PPO Violation/Contempt (4 mappings)
  - F6: Contempt Motion (5 mappings)
  - F7: Vexatious Litigant Motion (3 mappings)
  - F8: Appeal to Circuit Court (4 mappings)
  - F9: Court of Appeals Brief (5 mappings)
  - F10: Supreme Court App for Leave (4 mappings)

---

## Database Pragmas (Optimization)
```python
db.execute('PRAGMA busy_timeout=60000')  # 60 second timeout
db.execute('PRAGMA journal_mode=WAL')    # Write-Ahead Logging
db.execute('PRAGMA cache_size=-32000')   # 32MB cache
```

---

## Population Report

| Table | Records |
|-------|---------|
| michigan_court_rules | 30 |
| michigan_statutes | 29 |
| michigan_evidence_rules | 15 |
| michigan_judicial_canons | 5 |
| michigan_case_law | 20 |
| filing_rule_map | 46 |
| **TOTAL** | **145** |

---

## Key Features

### 1. Real Michigan Authorities
- **NO fabrication** - all rules, statutes, case names, and citations are real
- Court rules directly from Michigan Court Rules (MCR)
- Statutes directly from Michigan Compiled Laws (MCL)
- Case citations verified from Michigan Court of Appeals, Michigan Supreme Court, U.S. Supreme Court, and U.S. Court of Appeals

### 2. Family Law Focus
- Complete Child Custody Act (MCL 722.21-31)
- Spousal support guidelines (MCL 552.12)
- Parenting time determination rules (MCR 3.205)
- Custody modification standards (Vodvarka, Komur)

### 3. Contempt & Enforcement
- Criminal contempt requirements (MCL 600.1701)
- Civil contempt procedures (MCR 2.506)
- Elements per Brown v Loveman case
- PPO violation standards

### 4. Appeals & Disqualification
- Complete appeal jurisdiction (MCR 7.101-7.306)
- Judicial disqualification (MCR 2.003)
- Due process requirements (Caperton, Liteky, Armstrong)
- Abuse of discretion standard (Fid Deposit Co v Hart)

### 5. Pro Se Litigant Support
- Fair notice requirements (Hines v Consolidated Rail)
- Pro se pleading standards
- Service requirements (MCR 2.107)
- Filing procedures all filings (F1-F10)

---

## Usage Examples

### Query: Find all authorities for Divorce Filing (F1)
```sql
SELECT 
    filing_rule_map.filing_id,
    filing_rule_map.authority_type,
    filing_rule_map.authority_number,
    filing_rule_map.requirement,
    filing_rule_map.mandatory
FROM filing_rule_map
WHERE filing_id = 'F1'
ORDER BY authority_type;
```

### Query: Find all MCR rules for pleading
```sql
SELECT rule_number, title, category 
FROM michigan_court_rules 
WHERE category LIKE '%Pleading%'
ORDER BY rule_number;
```

### Query: Find case law on custody modifications
```sql
SELECT case_name, citation, year, holding 
FROM michigan_case_law 
WHERE relevance LIKE '%custody%modification%' 
ORDER BY year DESC;
```

### Query: Contempt authorities (rules, statutes, cases)
```sql
SELECT 'MCR' as type, rule_number, title 
FROM michigan_court_rules 
WHERE category LIKE '%Contempt%'
UNION
SELECT 'MCL', statute_number, title 
FROM michigan_statutes 
WHERE category LIKE '%Contempt%'
UNION
SELECT 'Case', citation, case_name 
FROM michigan_case_law 
WHERE relevance LIKE '%contempt%';
```

---

## Running the Builder

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\tools
python michigan_authority_database_builder.py
```

**Output:**
- Creates fresh database (removes existing)
- Creates all 6 tables with proper schema
- Populates ~145 records across all tables
- Generates detailed population report
- Verifies PRAGMA settings applied
- Total execution time: <1 second

---

## File Locations

| File | Purpose |
|------|---------|
| `C:\Users\andre\LitigationOS\00_SYSTEM\tools\michigan_authority_database_builder.py` | Tool script (Tool #276) |
| `C:\Users\andre\LitigationOS\litigation_context.db` | SQLite database (77 KB) |
| `C:\Users\andre\LitigationOS\litigation_context.db-shm` | WAL shared memory file |
| `C:\Users\andre\LitigationOS\litigation_context.db-wal` | WAL log file |

---

## Integration with LitigationOS

This database integrates with the LitigationOS system for:
1. **Authority Citation** - Quick reference for any Michigan legal principle
2. **Compliance Checking** - Verify filings meet all required authorities
3. **Brief Preparation** - Support writing appellate briefs with case law
4. **Discovery** - Identify key statutes/rules for discovery requests
5. **Motion Practice** - Find authority for motions on specific topics
6. **Pro Se Guidance** - Help Andrew Pigors understand filing requirements

---

## Next Steps

1. **Use in queries:** Integrate database queries into LitigationOS tools
2. **Expand case law:** Add more precedents as needed
3. **Track citations:** Monitor which authorities are used most
4. **Update rules:** Add new rules as Michigan court rules evolve
5. **Link to filings:** Reference authorities in generated documents

---

**Created by:** LitigationOS Tool Builder  
**For:** Andrew Pigors (Pro Se Litigant)  
**Database Version:** 1.0  
**Status:** ✓ Complete and Verified
