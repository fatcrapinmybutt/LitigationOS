# LitigationOS Database Schema Analysis
# File: C:\Users\andre\LitigationOS\litigation_context.db
# Database Size: ~12.2 GB
# Total Tables: 804

## SUMMARY

The litigation_context.db is a comprehensive litigation intelligence system with:
- **Core tables**: evidence, claims, docket events, judicial violations
- **Strategic tables**: rebuttal matrices, impeachment indexes, witness databases
- **Evidence analysis**: contradiction maps, actor violations, adversary assertions
- **Full-text search (FTS)**: Multiple tables with FTS4 indexes for rapid searching

---

## PRIMARY TABLES (4 Core Tables)

### 1. evidence_quotes
**Purpose**: Stores extracted quotes from court documents as key evidence pieces
**Row count**: 36,891 records
**Columns**:
- id (INTEGER, PK)
- document_id (INTEGER) - Links to source document
- page_number (INTEGER) - Location in document
- evidence_category (TEXT) - TRANSCRIPT, ORDER, DECLARATION, etc.
- quote_text (TEXT, NOT NULL) - The actual quoted text
- quote_hash (TEXT) - Hash for deduplication
- quote_type (TEXT) - HEARING_REF, JUDICIAL_ORDER, etc.
- speaker (TEXT) - Who made the statement
- date_ref (TEXT) - When it occurred
- legal_significance (TEXT) - Why it matters
- created_at (TIMESTAMP)
- source_type (TEXT) - PDF_COURT_DOC, etc.

**Sample rows**:
- Row 1: Ex parte hearing transcript (11/26/2025) from Judge McNeill
- Row 2: Transcript about parenting time suspension
- Row 3: Hearing references and custodial environment discussion

---

### 2. claims
**Purpose**: Tracks legal claims, counterclaims, and propositions with supporting evidence
**Row count**: 653 records
**Columns**:
- claim_id (TEXT, PK)
- issue_id (TEXT) - ISSUE_EX_PARTE_PROCEDURE, ISSUE_PARENTING_TIME_RESTRICTION, etc.
- doc (TEXT) - Document reference
- line_no (INTEGER) - Line number in document
- classification (TEXT) - ex_parte_reference, parenting_time_restriction, etc.
- actor (TEXT) - court_text, witness_name, attorney_name
- proposition (TEXT) - The actual claim statement
- affirmative_counter_proposition (TEXT) - Rebuttal or counter-argument
- evidence_targets (JSON array) - Supporting evidence references
- status (TEXT) - supported, rebuttable, disputed
- generated_at (TEXT) - When classified
- classifier_version (TEXT) - Algorithm version

**Sample rows**:
- Row 1: Ex parte procedure claim with MCR violations
- Row 2: Parenting time restriction claim
- Row 3: Mental health assessment claim

---

### 3. docket_events
**Purpose**: Case timeline events and procedural milestones from court records
**Row count**: 221 records
**Columns**:
- event_id (TEXT, PK) - DE-001, DE-002, etc.
- case_id (TEXT, NOT NULL) - Case number (2024-001507-DC)
- event_date_iso (TEXT, NOT NULL) - ISO date when event occurred
- record_date_iso (TEXT) - When recorded
- title (TEXT, NOT NULL) - Event description
- event_type (TEXT) - filing, order, hearing, appeal, etc.
- summary (TEXT) - Detailed event summary
- truth_tag (TEXT) - RECORD_RECITED, DISPUTED, etc.
- created_at (TEXT)

**Sample rows**:
- Row 1: Custody Complaint Filed (2024-06-15)
- Row 2: Ex Parte Custody Order Entered (2024-07-01)
- Row 3: PPO Issued Against Andrew Pigors (2024-09-15)

---

### 4. judicial_violations
**Purpose**: Documents violations of judicial conduct rules and ethical standards
**Row count**: 1,127 records
**Columns**:
- violation_id (TEXT, PK) - JV-c22d274f6e3b format
- judge_name (TEXT, NOT NULL) - Hon. Jenny L. McNeill, etc.
- canon_number (TEXT) - MCR 2.003 (Disqualification), etc.
- canon_text (TEXT) - Full text of the rule violated
- violation_description (TEXT, NOT NULL) - What happened and evidence
- evidence_refs (TEXT) - Citation to supporting evidence
- severity (TEXT) - critical, high, medium, low
- jtc_exhibit_id (TEXT) - Judicial Tenure Commission exhibit ID
- created_at (TEXT)

**Sample rows**:
- Row 1-3: Judge McNeill's disqualification violations under MCR 2.003(C)(1)

---

## STRATEGIC PATTERN TABLES (Found via pattern search)

### Rebuttal Tables (7 tables)
- **rebuttal_matrix** (553 rows) - Strategic rebuttals to adversary assertions
  - Columns: id, source_type, adversary, assertion_text, rebuttal_evidence, tort_cause, priority_score
- **rebuttal_matrix_fts** - Full-text search index
- **hypervisor_c11_rebuttal_microbriefs** - Condensed rebuttal briefs

### Impeachment Tables (8 tables)
- **impeachment_index** (11 rows) - Witness contradictions and credibility attacks
  - Columns: id, target_witness, statement_a/b, contradiction_type, impeachment_value, legal_use
- **impeachment_index_fts** - FTS index
- **impeachment_packages** - Grouped impeachment materials

### Witness Tables (4 tables)
- **witness_database** (9 rows) - Witness master list
  - Columns: id, name, role, harm_count, impeachment_count, credibility_score, priority
- **witness_profiles** - Detailed witness profiles
- **witness_package_links** - Links to supporting materials
- **cycle6_witnesses** - Latest cycle witness data

### Contradiction Tables (7 tables)
- **contradiction_map** (10,672 rows) - All identified contradictions in evidence
  - Columns: id, source_a_type, source_a_text, source_b_type, source_b_text, contradiction_type, severity, legal_impact
- **contradiction_timeline** - Chronological contradiction view
- **timeline_contradictions** - Temporal analysis
- **cycle6_contradictions** - Latest cycle data

### Violation Tables (21+ tables)
- **judicial_violations** - Core judicial conduct violations
- **actor_violations** (8,348 rows) - Violations by judges, attorneys, parties
  - Columns: id, actor, role, violation_type, description, severity, linked_actors
- **constitutional_violations** - Constitutional claim tracking
- **global_harms_violations** - Multi-level harm analysis
- **berry_ethics_violations** - Ethics-specific violations
- **housing_violations**, **ppo_violations** - Domain-specific violations
- Multiple FTS indexes for each

### Ex Parte Tables (1 table found)
- **caselaw_ex_parte_reversal** - Case law on reversing ex parte orders

### No Bias-Specific Tables
- Pattern search for 'bias' returned no results
- Bias analysis likely integrated into other tables (contradictions, violations, assertions)

---

## RELATIONSHIP & QUERY PATTERNS

### Primary Key Relationships
- evidence_quotes → document_id (links to document storage)
- claims → issue_id (links to legal issues), evidence_targets (JSON references)
- docket_events → case_id (links to case data)
- judicial_violations → judge_name (links actors to violations)
- actor_violations → actor field (can link to judge, attorney, or party)

### Evidence Chain
1. Evidence extracted → evidence_quotes (36,891 records)
2. Claims identified from evidence → claims (653 records)
3. Claims linked to docket timeline → docket_events (221 records)
4. Violations identified → judicial_violations (1,127 records)
5. Actor violations tracked → actor_violations (8,348 records)
6. Contradictions documented → contradiction_map (10,672 records)
7. Rebuttal strategies → rebuttal_matrix (553 records)
8. Witness credibility → witness_database (9 witnesses) + impeachment_index (11 contradictions)

---

## RECOMMENDED QUERIES FOR LITIGATION TOOLS

### 1. Find All Evidence Against Judge McNeill
\\\sql
SELECT jv.violation_id, jv.canon_number, jv.violation_description, 
       av.actor, av.violation_type, av.severity
FROM judicial_violations jv
LEFT JOIN actor_violations av ON av.actor LIKE '%McNeill%'
WHERE jv.judge_name = 'Hon. Jenny L. McNeill'
ORDER BY jv.severity DESC
\\\

### 2. Build Rebuttal to Adversary Assertion
\\\sql
SELECT rm.adversary, rm.assertion_text, rm.rebuttal_evidence, rm.rebuttal_citation
FROM rebuttal_matrix rm
WHERE rm.source_type = 'adversary_assertion'
AND rm.priority_score > 7
ORDER BY rm.priority_score DESC
\\\

### 3. Identify Witness Contradictions
\\\sql
SELECT ii.target_witness, ii.statement_a, ii.statement_b, 
       ii.contradiction_type, ii.impeachment_value
FROM impeachment_index ii
WHERE ii.legal_use IN ('disqualification', 'credibility_attack')
\\\

### 4. Timeline of Violations
\\\sql
SELECT de.event_date_iso, de.title, av.violation_type, av.description, av.severity
FROM docket_events de
LEFT JOIN actor_violations av ON av.date = de.event_date_iso
ORDER BY de.event_date_iso ASC
\\\

### 5. Evidence Quote with Full Context
\\\sql
SELECT eq.id, eq.evidence_category, eq.speaker, eq.quote_text, 
       eq.legal_significance, eq.date_ref
FROM evidence_quotes eq
WHERE eq.legal_significance IS NOT NULL
AND eq.evidence_category IN ('HEARING_REF', 'JUDICIAL_ORDER')
LIMIT 20
\\\

---

## DATABASE STRUCTURE NOTES

- **Full-Text Search**: 100+ FTS4 tables for rapid searching across evidence, assertions, violations
- **Indexing**: Comprehensive indexing on id, actor, judge_name, violation_type, contradiction_type
- **Size**: ~12.2 GB - highly data-dense with 804 tables total
- **Integrity**: Evidence chain maintains referential integrity through FK-like patterns
- **Timestamps**: Most records include created_at for audit trail
- **JSON Fields**: evidence_targets in claims, linked_actors in actor_violations

---

## NEXT STEPS FOR YOUR TOOL

1. **Query the evidence_quotes** for case-specific evidence
2. **Cross-reference with judicial_violations** to build judicial misconduct arguments
3. **Use rebuttal_matrix** to generate counter-arguments
4. **Leverage contradiction_map** to impeach witness testimony
5. **Track actor_violations** to show patterns of misconduct
6. **Use FTS indexes** for rapid full-text search across all evidence

This database appears to be an advanced litigation support system specifically designed for family law/parental rights cases with comprehensive judicial misconduct tracking.
