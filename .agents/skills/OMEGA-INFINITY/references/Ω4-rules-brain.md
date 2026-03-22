# Ω4 Rules Brain — OMEGA-INFINITY Reference
> Module 4 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose
The rules brain provides the unified legal authority index — statutes, court rules, case law, canons, and local rules — with hierarchy, citation format, FTS5 search patterns, and per-lane key authorities. Every legal argument in every filing must trace back to an authority record in this brain.

---

## 1. Authority Inventory — Unified Index

Query for the current breakdown by type:
```sql
SELECT authority_type, COUNT(*) AS count
FROM authority_master_index
GROUP BY authority_type
ORDER BY count DESC;
```

### Authority Type Distribution (verify with query above)

| Type | Prefix | Description | Approximate Count |
|------|--------|-------------|-------------------|
| **MCR** | MCR | Michigan Court Rules | ~476 |
| **MCL** | MCL | Michigan Compiled Laws (statutes) | ~86 |
| **MRE** | MRE | Michigan Rules of Evidence | ~66 |
| **CaseLaw** | — | Michigan and federal case law | ~58 |
| **Canons** | Canon | Michigan Code of Judicial Conduct | ~19 |
| **Local** | LR | 14th Circuit Local Rules | ~14 |
| **FRCP** | FRCP | Federal Rules of Civil Procedure | ~5 |
| **Federal** | 42 USC / 28 USC | Federal statutes | ~4 |

### Authority Source Databases

| Database | Path | Contents |
|----------|------|----------|
| `litigation_context.db` | `C:\Users\andre\LitigationOS\litigation_context.db` | `authority_master_index`, `authority_fts`, `master_citations`, `authority_chains_v2` |
| `mcr_rules.db` | `C:\Users\andre\LitigationOS\databases\mcr_rules.db` | Full text of MCR sections (~1,297 sections) |
| `court_forms.db` | `C:\Users\andre\LitigationOS\databases\court_forms.db` | Form-to-rule cross-references |

---

## 2. Authority Hierarchy

Authorities are not equal. When authorities conflict, higher-ranked authorities prevail. When selecting authorities for a filing, lead with the strongest source.

### Binding Authority Hierarchy (Michigan State Courts)

```
LEVEL 1: Michigan Constitution
  └─ Art. 1 (Declaration of Rights), Art. 6 (Judicial Branch)
  └─ Trumps all below. Rarely cited directly unless constitutional challenge.

LEVEL 2: Michigan Compiled Laws (MCL)
  └─ MCL 722.21-722.31 (Child Custody Act) — Lane A primary
  └─ MCL 600.2950 (PPO) — Lane D primary
  └─ MCL 600.2918 (Property Recovery) — Lane B
  └─ MCL 600.1701-1721 (Superintending Control)
  └─ Enacted by legislature. Binding on all Michigan courts.

LEVEL 3: Michigan Court Rules (MCR)
  └─ Promulgated by Michigan Supreme Court
  └─ Govern procedure: how to file, serve, argue, appeal
  └─ MCR 2.003 (Disqualification) — Lane E critical
  └─ MCR 3.210 (Custody Actions) — Lane A procedural
  └─ MCR 3.708 (PPO Proceedings) — Lane D procedural
  └─ MCR 7.201-7.219 (Appeals) — Lane F critical
  └─ MCR 9.104-9.126 (JTC) — Lane E procedural

LEVEL 4: Michigan Rules of Evidence (MRE)
  └─ Govern admissibility of evidence at trial and hearings
  └─ MRE 401-403 (Relevance)
  └─ MRE 801-807 (Hearsay and exceptions)
  └─ MRE 901-902 (Authentication) — see Ω2 Evidence Brain

LEVEL 5: Michigan Supreme Court Decisions
  └─ Binding on all lower Michigan courts
  └─ Citation format: People v Smith, 500 Mich 123; 890 NW2d 456 (2023)

LEVEL 6: Michigan Court of Appeals Decisions
  └─ Published opinions are binding on trial courts
  └─ Unpublished opinions: persuasive only (MCR 7.215(C)(1))
  └─ Citation format: Smith v Jones, 340 Mich App 567; 987 NW2d 321 (2022)

LEVEL 7: Michigan Code of Judicial Conduct (Canons)
  └─ Govern judicial behavior, not litigant rights
  └─ Enforceable via JTC complaint (Lane E)
  └─ Canon 1: Integrity and independence
  └─ Canon 2: Appearance of impropriety
  └─ Canon 3: Impartiality, diligence, ex parte contacts
  └─ Canon 5: Extra-judicial activities

LEVEL 8: Local Court Rules (14th Circuit)
  └─ Supplement MCR for local practice
  └─ Scheduling, motion practice, case management
  └─ Must not conflict with MCR

LEVEL 9: Federal Authority (Lane C only)
  └─ US Constitution (14th Amendment — due process, equal protection)
  └─ 42 USC §1983, §1985, §1988
  └─ FRCP 8, 12, 56
  └─ Federal case law (6th Circuit, WDMI)
```

### Persuasive (Non-Binding) Authority
- Unpublished Michigan Court of Appeals opinions
- Other state court decisions on analogous issues
- Legal treatises and secondary sources
- Restatements
- Law review articles

---

## 3. Top-Cited Authorities

Query for the most-cited authorities in this case:
```sql
SELECT identifier, title, authority_type, citation_count
FROM authority_master_index
ORDER BY citation_count DESC
LIMIT 20;
```

### Critical Authorities by Citation Frequency

| Authority | Type | Approximate Citations | Lane | Why Critical |
|-----------|------|----------------------|------|-------------|
| **MCL 722.23** | Statute | ~709 | A | The 12 best-interest factors — foundation of every custody argument |
| **MCR 2.003** | Rule | ~382 | E, A, D | Disqualification of judge — central to misconduct lane |
| **Canon 3** | Canon | ~315 | E | Judicial impartiality and ex parte contacts |
| **MCR 3.210** | Rule | varies | A | Custody action procedures |
| **MCL 600.2950** | Statute | varies | D | PPO statutory basis |
| **MCR 7.212** | Rule | varies | F | Brief requirements on appeal |
| **MCR 2.119** | Rule | varies | All | Motion practice requirements |
| **MRE 901** | Rule | varies | All | Evidence authentication |
| **Canon 2** | Canon | varies | E | Appearance of impropriety |
| **MCR 3.708** | Rule | varies | D | PPO proceeding procedures |

### MCL 722.23 — The 12 Best-Interest Factors (Lane A Foundation)

Every custody argument must address these factors. Cite as: MCL 722.23(a)-(l).

```
(a) Love, affection, emotional ties between child and competing parties
(b) Capacity to give love, affection, guidance, continuation of education
(c) Capacity to provide food, clothing, medical care
(d) Length of time child lived in stable, satisfactory environment
(e) Permanence as a family unit of existing or proposed custodial home
(f) Moral fitness of parties
(g) Mental and physical health of parties
(h) Home, school, and community record of child
(i) Reasonable preference of child (if old enough)
(j) Willingness to facilitate close relationship with other parent
(k) Domestic violence
(l) Any other relevant factor
```

Each factor maps to evidence in `evidence_quotes` via the `claim_type` or `best_interest_factor` column. Query: `SELECT COUNT(*) FROM evidence_quotes WHERE claim_type LIKE '%factor_%'` to check coverage.

---

## 4. Authority Chain Structure

Authorities are never cited in isolation. Each citation lives within a chain that provides context, support, and distinction.

### Chain Components

```
PRIMARY AUTHORITY
  └─ The main rule or statute being applied
  └─ Example: MCL 722.23 (best-interest factors)

SUPPORTING AUTHORITY
  └─ Case law interpreting the primary authority
  └─ Example: Vodvarka v Grasmeyer, 259 Mich App 499 (2003) (established custodial environment)

DISTINGUISHING AUTHORITY
  └─ Cases or rules that might argue against the position
  └─ Must acknowledge and distinguish (not ignore)
  └─ Example: Fletcher v Fletcher, 447 Mich 871 (1994) (burden of proof standards)

APPLICATION AUTHORITY
  └─ Authority showing how the rule applies to facts like these
  └─ Analogous cases with similar fact patterns
```

### Chain Storage in DB

```sql
-- authority_chains_v2 structure
SELECT chain_id, primary_authority, supporting_authority, 
       distinguishing_authority, vehicle_name, chain_complete
FROM authority_chains_v2
WHERE vehicle_name = ?
ORDER BY chain_id;
```

### Building a New Chain

1. Identify the primary authority (statute or rule)
2. Search for supporting case law: `SELECT * FROM authority_master_index WHERE authority_type = 'CaseLaw' AND full_text LIKE '%MCL 722.23%'`
3. Search for distinguishing authority: cases the opposing side might cite
4. Record the chain in `authority_chains_v2`
5. Link the chain to the claim via `vehicle_name`

### Chain Completeness Check
```sql
SELECT 
  vehicle_name,
  COUNT(*) AS total_chains,
  SUM(CASE WHEN chain_complete = 1 THEN 1 ELSE 0 END) AS complete_chains,
  SUM(CASE WHEN distinguishing_authority IS NOT NULL THEN 1 ELSE 0 END) AS with_distinctions
FROM authority_chains_v2
GROUP BY vehicle_name
ORDER BY total_chains DESC;
```

---

## 5. Citation Format Standards — Michigan Courts

### Statute Citations (MCL)
```
Format: MCL [chapter].[section]
Example: MCL 722.23
         MCL 600.2950(1)
         MCL 722.23(a)-(l)

With specific subdivision:
  MCL 722.23(j) — willingness to facilitate relationship factor
```

### Court Rule Citations (MCR)
```
Format: MCR [chapter].[rule]([subrule])
Example: MCR 2.003(C)(1)
         MCR 3.210(A)
         MCR 7.212(C)(7)
         MCR 2.119(A)(1)

Full subrule path when specificity matters:
  MCR 2.003(C)(1)(b) — grounds for disqualification
```

### Evidence Rule Citations (MRE)
```
Format: MRE [rule]([subdivision])
Example: MRE 901(a)
         MRE 801(c)
         MRE 403
```

### Case Law Citations (Michigan)
```
Michigan Supreme Court:
  [Name] v [Name], [vol] Mich [page]; [vol] NW2d [page] ([year])
  Example: Vodvarka v Grasmeyer, 259 Mich App 499; 675 NW2d 847 (2003)

Michigan Court of Appeals (published):
  [Name] v [Name], [vol] Mich App [page]; [vol] NW2d [page] ([year])
  Example: Shade v Wright, 291 Mich App 17; 805 NW2d 1 (2010)

Michigan Court of Appeals (unpublished):
  [Name] v [Name], unpublished per curiam opinion of the Court of Appeals,
  issued [date] (Docket No. [number])
  Note: Cite sparingly — not binding (MCR 7.215(C)(1))
```

### Federal Citations (Lane C only)
```
Federal Statute:
  42 USC §1983
  28 USC §1343

Federal Rules:
  FRCP 8(a)
  FRCP 12(b)(6)

Federal Case Law (6th Circuit):
  [Name] v [Name], [vol] F.3d [page] (6th Cir. [year])
  Example: Harlow v Fitzgerald, 457 US 800 (1982) (qualified immunity)
```

### Canon Citations
```
Format: Michigan Code of Judicial Conduct, Canon [number]([rule])
Example: Canon 3(A)(4) — ex parte communications
         Canon 2(A) — appearance of impropriety
         Canon 3(B)(5) — impartiality
```

---

## 6. FTS5 Search Guide — Querying authority_fts

The `authority_fts` table is a Full-Text Search (FTS5) virtual table enabling fast keyword search across all authority text.

### Basic Search
```sql
SELECT identifier, title, authority_type, rank
FROM authority_fts
WHERE authority_fts MATCH 'custody AND best interest'
ORDER BY rank
LIMIT 20;
```

### Search Operators

| Operator | Example | Meaning |
|----------|---------|---------|
| `AND` | `custody AND modification` | Both terms must appear |
| `OR` | `PPO OR protection order` | Either term |
| `NOT` | `custody NOT juvenile` | Exclude term |
| `"..."` | `"best interest factors"` | Exact phrase |
| `*` | `disqualif*` | Prefix match (disqualification, disqualify, etc.) |
| `NEAR/N` | `NEAR(custody modification, 5)` | Terms within N tokens |
| `^` | `^custody` | Term must appear in first column |

### Practical Search Patterns

**Find disqualification authorities:**
```sql
SELECT identifier, title, authority_type
FROM authority_fts
WHERE authority_fts MATCH 'disqualif* OR recusal OR "MCR 2.003"'
ORDER BY rank LIMIT 15;
```

**Find parenting time authorities:**
```sql
SELECT identifier, title, authority_type
FROM authority_fts
WHERE authority_fts MATCH '"parenting time" OR "parenting-time" OR "visitation"'
ORDER BY rank LIMIT 15;
```

**Find ex parte authorities:**
```sql
SELECT identifier, title, authority_type
FROM authority_fts
WHERE authority_fts MATCH '"ex parte" OR Canon NEAR(3, 5) OR "one-sided communication"'
ORDER BY rank LIMIT 15;
```

**Find contempt authorities:**
```sql
SELECT identifier, title, authority_type
FROM authority_fts
WHERE authority_fts MATCH 'contempt AND (civil OR criminal OR "show cause")'
ORDER BY rank LIMIT 15;
```

**Find appellate standard of review:**
```sql
SELECT identifier, title, authority_type
FROM authority_fts
WHERE authority_fts MATCH '"abuse of discretion" OR "clear error" OR "de novo" OR "standard of review"'
ORDER BY rank LIMIT 15;
```

### FTS5 Performance Notes
- FTS5 searches are orders of magnitude faster than `LIKE '%term%'`
- Always prefer FTS5 MATCH over LIKE for authority searches
- The `rank` column is BM25-based relevance scoring (lower = more relevant)
- For complex queries, use the `adaptive_query_rewriter.py` which auto-converts LIKE to FTS5

---

## 7. Key MCR Rules Per Lane

### Lane A — Custody

| MCR Rule | Subject | Key Provision |
|----------|---------|---------------|
| **MCR 3.210** | Custody Actions | Governs initiation and procedure for custody disputes |
| **MCR 3.211** | Child Protective | Proceedings involving child protection — relevant if CPS involved |
| **MCR 3.214** | Parenting Time | Enforcement and modification of parenting time orders |
| **MCR 2.119** | Motion Practice | How to file and argue motions |
| **MCR 2.116** | Summary Disposition | Standards for early resolution |
| **MCR 3.206** | Initiating Actions | Domestic relations case initiation |

### Lane B — Housing

| MCR Rule | Subject | Key Provision |
|----------|---------|---------------|
| **MCR 4.201** | Summary Proceedings | Land contract forfeiture and eviction procedures |
| **MCR 2.110** | Pleadings | Complaint requirements for civil actions |
| **MCR 2.116** | Summary Disposition | Standards for dismissal/judgment |

### Lane D — PPO

| MCR Rule | Subject | Key Provision |
|----------|---------|---------------|
| **MCR 3.705** | PPO — Jurisdiction | Who may petition, what court has jurisdiction |
| **MCR 3.706** | PPO — Procedure | How to petition, modify, terminate |
| **MCR 3.707** | PPO — Contempt | Contempt for PPO violation |
| **MCR 3.708** | PPO — Post-Judgment | Modification and enforcement post-judgment |
| **MCR 2.119** | Motion Practice | Motion procedures apply in PPO context |

### Lane E — Judicial Misconduct

| MCR Rule | Subject | Key Provision |
|----------|---------|---------------|
| **MCR 2.003** | Disqualification | Grounds and procedure for disqualifying a judge |
| **MCR 2.003(C)(1)** | Grounds | Personal bias, prejudice, or conflict of interest |
| **MCR 9.104** | JTC — Purpose | Judicial Tenure Commission jurisdiction |
| **MCR 9.108** | JTC — Complaints | How to file a JTC complaint |
| **MCR 9.116** | JTC — Investigation | Investigation procedures |
| **MCR 9.120** | JTC — Proceedings | Formal proceedings before JTC |

### Lane F — Appellate

| MCR Rule | Subject | Key Provision |
|----------|---------|---------------|
| **MCR 7.201** | Appeal of Right | When appeal lies as of right |
| **MCR 7.203** | Jurisdiction | COA jurisdictional requirements |
| **MCR 7.204** | Filing Claim of Appeal | Procedure and deadlines |
| **MCR 7.205** | Application for Leave | Discretionary appeals |
| **MCR 7.210** | Record on Appeal | What constitutes the record; how to supplement |
| **MCR 7.211** | Appendices | Requirements for appendices in briefs |
| **MCR 7.212** | Briefs | Brief content, format, page limits, citation rules |
| **MCR 7.215** | Opinions and Orders | Published vs. unpublished, precedential value |
| **MCR 7.216** | Miscellaneous Relief | Emergency motions, stays pending appeal |

### Lane C — Federal (supplemental)

| Rule | Subject | Key Provision |
|------|---------|---------------|
| **FRCP 8** | General Pleading | Short plain statement requirement |
| **FRCP 12** | Defenses and Objections | Motion to dismiss standards |
| **FRCP 56** | Summary Judgment | Federal summary judgment standard |
| **42 USC §1983** | Civil Rights Action | Deprivation of rights under color of law |
| **42 USC §1988** | Attorney Fees | Fee shifting in civil rights cases |

---

## 8. MCR Rules Database (mcr_rules.db) — Querying Full Rule Text

The `mcr_rules.db` database contains full text of Michigan Court Rules. Query structure:
```sql
-- Connect to mcr_rules.db (separate from litigation_context.db)
-- Check available tables first:
SELECT name FROM sqlite_master WHERE type='table';

-- Typical table: sections
-- Get the schema:
PRAGMA table_info(sections);

-- Search for a specific rule:
SELECT section_number, title, full_text
FROM sections
WHERE section_number LIKE 'MCR 2.003%';

-- Full-text search (if FTS table exists):
SELECT section_number, title
FROM sections_fts
WHERE sections_fts MATCH 'disqualification';
```

### Common MCR Queries

**Get all subrules of MCR 2.003:**
```sql
SELECT section_number, title, SUBSTR(full_text, 1, 200) AS preview
FROM sections
WHERE section_number LIKE '2.003%'
ORDER BY section_number;
```

**Find rules mentioning custody:**
```sql
SELECT section_number, title
FROM sections
WHERE full_text LIKE '%custody%'
ORDER BY section_number;
```

**Get PPO rules (MCR 3.705-3.708):**
```sql
SELECT section_number, title, full_text
FROM sections
WHERE section_number >= '3.705' AND section_number <= '3.708'
ORDER BY section_number;
```

---

## 9. Cross-Wiring — Authority to Evidence to Filing

### The Authority-Evidence-Filing Triangle

Every legal argument has three legs:
1. **Authority** — the legal rule that applies (`authority_master_index`)
2. **Evidence** — the facts that satisfy the rule (`evidence_quotes`)
3. **Filing** — the document that presents both to the court (`filing_packages`)

### Cross-Reference Columns

| Source Table | Column | Links To | Target Table |
|-------------|--------|----------|-------------|
| `authority_master_index` | `identifier` | Rule identifier (e.g., MCR 2.003) | `mcr_rules.db → sections.section_number` |
| `master_citations` | `authority_id` | Which authority is cited | `authority_master_index.authority_id` |
| `master_citations` | `vehicle_name` | Which filing cites it | `filing_readiness.vehicle_name` |
| `authority_chains_v2` | `primary_authority` | Chain root | `authority_master_index.identifier` |
| `authority_chains_v2` | `vehicle_name` | Which filing uses this chain | `filing_packages.vehicle_name` |
| `judicial_violations` | `mcr_rule` | Which rule was violated | `authority_master_index.identifier` |
| `judicial_violations` | `canon_violated` | Which Canon was violated | Canon entries in `authority_master_index` |
| `claims` | `authority_basis` | Legal basis for claim | `authority_master_index.identifier` |
| `evidence_quotes` | `vehicle_name` | Which filing context | `claims.vehicle_name` → authority chains |

### Tracing an Authority Through the System

To see how an authority flows from rule → violation → evidence → filing:

```sql
-- Step 1: Find the authority
SELECT authority_id, identifier, title FROM authority_master_index 
WHERE identifier = 'MCR 2.003';

-- Step 2: Find violations of this authority
SELECT violation_id, violation_type, description, date_occurred 
FROM judicial_violations 
WHERE mcr_rule LIKE '%2.003%';

-- Step 3: Find evidence supporting these violations
SELECT quote_text, source_file, date_referenced 
FROM evidence_quotes 
WHERE vehicle_name LIKE '%disqualification%' OR claim_type LIKE '%misconduct%';

-- Step 4: Find filings citing this authority
SELECT vehicle_name, citation_text 
FROM master_citations 
WHERE authority_id IN (SELECT authority_id FROM authority_master_index WHERE identifier = 'MCR 2.003');

-- Step 5: Find the authority chain
SELECT chain_id, primary_authority, supporting_authority, distinguishing_authority
FROM authority_chains_v2
WHERE primary_authority LIKE '%2.003%';
```

---

## Key DB Queries

### 1. Authority search with FTS5
```sql
SELECT identifier, title, authority_type, citation_count
FROM authority_fts
WHERE authority_fts MATCH ?
ORDER BY rank
LIMIT 15;
```

### 2. Top authorities by citation frequency
```sql
SELECT identifier, title, authority_type, citation_count
FROM authority_master_index
ORDER BY citation_count DESC
LIMIT 20;
```

### 3. Authority chains for a filing vehicle
```sql
SELECT chain_id, primary_authority, supporting_authority,
       distinguishing_authority, chain_complete
FROM authority_chains_v2
WHERE vehicle_name = ?
ORDER BY chain_id;
```

### 4. Judicial violations by rule
```sql
SELECT mcr_rule, canon_violated, violation_type, 
       COUNT(*) AS violation_count
FROM judicial_violations
WHERE mcr_rule IS NOT NULL OR canon_violated IS NOT NULL
GROUP BY mcr_rule, canon_violated, violation_type
ORDER BY violation_count DESC
LIMIT 20;
```

### 5. Citation coverage per filing vehicle
```sql
SELECT 
  fr.vehicle_name,
  (SELECT COUNT(*) FROM master_citations mc WHERE mc.vehicle_name = fr.vehicle_name) AS citations,
  (SELECT COUNT(*) FROM authority_chains_v2 ac WHERE ac.vehicle_name = fr.vehicle_name) AS chains,
  (SELECT COUNT(*) FROM authority_chains_v2 ac WHERE ac.vehicle_name = fr.vehicle_name AND ac.chain_complete = 1) AS complete_chains
FROM filing_readiness fr
ORDER BY citations DESC;
```

---

## 10. Overruled and Superseded Authority Detection

Before citing any authority, verify it has not been overruled, superseded, or otherwise weakened. Filing a brief that cites bad law undermines credibility and may violate professional obligations.

### Detection Protocol
1. **Check `authority_master_index` status field:**
   ```sql
   SELECT identifier, title, status, superseded_by, overruled_date
   FROM authority_master_index
   WHERE identifier = ?;
   ```
2. **Check authority chain for negative treatment:**
   ```sql
   SELECT chain_id, distinguishing_authority
   FROM authority_chains_v2
   WHERE primary_authority = ? AND distinguishing_authority IS NOT NULL;
   ```
3. **Cross-reference with current MCR/MCL text:**
   If the rule was amended, the `mcr_rules.db` has the current version. Compare the version cited with the current text.

### Common Pitfalls
- **Amended statutes:** MCL sections get amended by the legislature — verify the version you are citing is current
- **Revised court rules:** MCR rules are revised by the Michigan Supreme Court — check effective dates
- **Overruled case law:** A Michigan Supreme Court decision can overrule a Court of Appeals decision
- **Superseded by statute:** A statutory change can supersede court-made rules
- **Limited holdings:** A case may be good law on one issue but overruled on another — cite the specific holding

### Shepardizing Equivalent
Without access to Westlaw/LexisNexis, use these DB-based verification methods:
```sql
-- Find all negative citations for an authority
SELECT mc.citation_text, mc.treatment, mc.vehicle_name
FROM master_citations mc
WHERE mc.authority_id IN (
  SELECT authority_id FROM authority_master_index WHERE identifier = ?
)
AND mc.treatment IN ('distinguished', 'overruled', 'questioned', 'limited');
```

---

## 11. Local Rules — 14th Judicial Circuit

The 14th Circuit has local rules that supplement the MCR. These are critical for filing in Muskegon County.

### Key Local Rules

| Local Rule | Subject | Impact |
|------------|---------|--------|
| **Scheduling** | Motion hearing scheduling | Must follow local scheduling procedures — contact clerk |
| **Brief page limits** | Page or word limits for briefs | May differ from MCR defaults — check local rule |
| **E-filing** | MiFILE requirements | 14th Circuit participates in MiFILE — electronic filing required |
| **Discovery** | Discovery procedures | May have local discovery conferences or cut-off dates |
| **Case management** | Status conferences, scheduling orders | Comply with any outstanding scheduling order |

### Querying Local Rules
```sql
SELECT identifier, title, full_text
FROM authority_master_index
WHERE authority_type = 'Local'
ORDER BY identifier;
```

### Local Practice Tips (14th Circuit, Muskegon County)
- File electronically via MiFILE unless specific exception applies
- Proposed orders must be submitted in editable format (Word) in addition to PDF
- Contact the court clerk at (231) 724-6241 for hearing dates
- Family Division motions are heard on the judge's regular motion day — confirm schedule
- Pro se litigants are held to the same procedural standards as attorneys (but courts are encouraged to construe filings liberally)

---

## 12. Strategic Authority Selection

### Selecting the Strongest Authority for Each Argument

When multiple authorities support a point, select based on this priority:

1. **Most recent binding authority** — newer cases better reflect current law
2. **Highest court level** — Supreme Court > Court of Appeals > Trial Court
3. **Most factually analogous** — cases with similar facts are most persuasive
4. **Published over unpublished** — published COA opinions bind; unpublished do not
5. **Plurality/majority over concurrence/dissent** — majority holdings are binding; concurrences are persuasive only

### Authority Density Standards

| Filing Type | Minimum Authorities | Recommended |
|-------------|-------------------|-------------|
| Simple motion | 1-2 per argument | 3-5 total |
| Complex motion with brief | 3-5 per argument | 10-15 total |
| Appellate brief | 5-10 per issue | 20-40 total |
| §1983 complaint | 2-3 per element | 10-20 total |
| JTC complaint | 1-2 per allegation | 5-10 total |

### Building Persuasive Authority Sections

The ideal authority section in a brief follows this structure:
1. **State the rule** — cite the primary authority (statute or court rule)
2. **Explain the rule** — cite case law interpreting the rule (what does it mean?)
3. **Apply the rule** — cite analogous cases (cases with similar facts that reached favorable outcomes)
4. **Distinguish adverse authority** — cite and address cases the opposing side will rely on
5. **Conclude** — restate why the rule compels the requested result

Each step requires different authorities from `authority_master_index` and `authority_chains_v2`. Build the chain before drafting the section.

---

## Cross-Wiring Points

| This Brain | Links To | Via Column(s) |
|------------|----------|---------------|
| Ω4 Rules → Ω1 Litigation | `master_citations.vehicle_name` → filing vehicle strategy decisions |
| Ω4 Rules → Ω1 Litigation | `authority_chains_v2.vehicle_name` → filing strength assessment |
| Ω4 Rules → Ω2 Evidence | `judicial_violations.mcr_rule` → evidence of rule violations |
| Ω4 Rules → Ω2 Evidence | `judicial_violations.evidence_source` → source file for violation evidence |
| Ω4 Rules → Ω3 Forms | `court_forms_complete.court_level` → which rules govern which forms |
| Ω1 Litigation → Ω4 Rules | `claims.authority_basis` → primary authority for each claim |
| Ω2 Evidence → Ω4 Rules | Authentication scoring uses MRE 901/902 from this brain |
| Ω3 Forms → Ω4 Rules | MCR 2.113, 2.107, 2.119 govern form requirements and service |
