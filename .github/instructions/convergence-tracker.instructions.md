---
description: "Total Legal Convergence tracker — auto-loaded every session. Contains convergence tables schema, status queries, and next-action protocol. Drives autonomous legal authority expansion across sessions."
applyTo: "**/*"
---

# Total Legal Convergence — Autonomous Session Protocol

## PURPOSE
Make the entire Michigan judiciary machine-readable. Track progress across sessions automatically using 5 persistent tables in `litigation_context.db`.

## ON EVERY SESSION START — Query Convergence Status

Run this FIRST when the user asks about convergence, legal authority status, or "what's next":

```sql
-- 1. Overall progress
SELECT status, COUNT(*) as domains,
       ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM convergence_domains),1) as pct
FROM convergence_domains GROUP BY status ORDER BY domains DESC;

-- 2. Next wave to execute (first non-COMPLETE wave)
SELECT wave_id, wave_name, agent_count, status, depends_on
FROM convergence_waves WHERE status != 'COMPLETE'
ORDER BY wave_number LIMIT 3;

-- 3. Ready todos (PENDING with no unfinished dependencies)
SELECT t.todo_id, t.title, t.wave_id, t.target_table, t.target_rows
FROM convergence_todos t
WHERE t.status = 'PENDING'
  AND (t.depends_on IS NULL
       OR t.depends_on IN (SELECT todo_id FROM convergence_todos WHERE status = 'COMPLETE'))
ORDER BY t.wave_id LIMIT 10;

-- 4. Drive assets not yet ingested
SELECT drive_letter, directory, file_count, content_description, priority
FROM drive_inventory WHERE is_ingested = 0 ORDER BY priority DESC;
```

## TABLE SCHEMAS (in litigation_context.db)

### convergence_domains (105 rows)
Tracks 53 legal domains across 11 categories (A-K). Each domain has RED/YELLOW/GREEN status.
```
domain_id TEXT PK    -- e.g. 'A1', 'B8', 'G5'
category TEXT        -- A through K
category_name TEXT   -- 'Michigan Court Rules', 'Torts & Civil Theories', etc.
domain_name TEXT     -- 'Landlord-Tenant', 'IIED', 'MCR Criminal Procedure'
authority_range TEXT -- 'MCR 6.001-6.933', 'MCL 554.601+', etc.
status TEXT          -- RED (not started), YELLOW (partial), GREEN (complete)
status_detail TEXT   -- Human-readable status
wave_id TEXT         -- Which wave handles this domain
target_rows INTEGER  -- Expected rows to add
actual_rows INTEGER  -- Rows actually added (update after completion)
last_updated TEXT    -- Timestamp of last status change
```

### convergence_waves (10 rows)
10 execution waves with dependencies.
```
wave_id TEXT PK      -- W1 through W10
wave_number INTEGER  -- 1-10
wave_name TEXT       -- 'Local File Ingestion', 'MCR Complete Expansion', etc.
agent_count INTEGER  -- Number of agents in this wave
status TEXT          -- PENDING, IN_PROGRESS, COMPLETE, BLOCKED
depends_on TEXT      -- Wave ID this depends on (NULL = no dependency)
started_at TEXT      -- When execution began
completed_at TEXT    -- When execution finished
results TEXT         -- Summary of what was accomplished
```

### convergence_todos (37 rows)
Actionable tasks per wave.
```
todo_id TEXT PK      -- e.g. 'w1-mcl-html', 'w5-intentional-torts'
wave_id TEXT         -- Parent wave
title TEXT           -- Short description
description TEXT     -- Full task description
status TEXT          -- PENDING, IN_PROGRESS, COMPLETE, BLOCKED
depends_on TEXT      -- Todo ID this depends on
source_path TEXT     -- File/directory to process
target_table TEXT    -- DB table to populate
target_rows INTEGER  -- Expected rows
actual_rows INTEGER  -- Actual rows added (update after completion)
started_at TEXT      -- Execution start
completed_at TEXT    -- Execution end
agent_name TEXT      -- Which agent executed this
```

### drive_inventory (13 rows)
All discovered legal file locations across 7 drives.
```
drive_letter TEXT    -- C, D, F, G, I, J
directory TEXT       -- Full path
file_count INTEGER   -- Number of legal files
content_description TEXT -- What's there
is_ingested INTEGER  -- 0=not yet, 1=processed
priority TEXT        -- CRITICAL, HIGH, MEDIUM, LOW
```

### legal_theories (populated by Wave 5-6)
Causes of action, defenses, and doctrines with elements.
```
theory_name TEXT     -- 'IIED', 'Malicious Prosecution', 'Res Judicata'
theory_type TEXT     -- 'tort', 'defense', 'doctrine', 'statutory_claim'
category TEXT        -- 'intentional_tort', 'equitable_defense', 'immunity'
elements TEXT        -- Required elements (pipe-separated)
primary_authority TEXT
michigan_statute TEXT
federal_statute TEXT
key_cases TEXT
lane_applicability TEXT -- Which case lanes this applies to
```

## AFTER COMPLETING WORK — Update Status

```sql
-- Mark a todo complete
UPDATE convergence_todos
SET status = 'COMPLETE', actual_rows = ?, completed_at = datetime('now')
WHERE todo_id = ?;

-- Update domain status
UPDATE convergence_domains
SET status = 'GREEN', actual_rows = ?, last_updated = datetime('now')
WHERE domain_id = ?;

-- Mark wave complete (after all its todos are done)
UPDATE convergence_waves
SET status = 'COMPLETE', completed_at = datetime('now'), results = ?
WHERE wave_id = ?
  AND NOT EXISTS (
    SELECT 1 FROM convergence_todos
    WHERE wave_id = ? AND status != 'COMPLETE'
  );
```

## WAVE SUMMARY

| Wave | Name | Agents | Key Target | Depends On |
|------|------|--------|------------|------------|
| W1 | Local File Ingestion | 5 | Parse 17.5GB on-disk → rules: 2,443→5,000+ | None |
| W2 | MCR Complete Expansion | 3 | All 9 MCR chapters fully covered | W1 |
| W3 | MCL Systematic Expansion | 4 | MCL: 68→500+ statutes | W1 |
| W4 | Case Law Deep Dive | 4 | 200+ verified cases with pin cites | None |
| W5 | Torts & Causes of Action | 4 | 17 tort theories with elements | W3 |
| W6 | Defenses & Immunity | 3 | 15 defensive doctrines | W4 |
| W7 | Specialized Areas | 4 | L/T, mobile home, CPS, local rules | W3 |
| W8 | Federal Law Overlay | 3 | §1983, RICO, Fair Housing, FRCP | W4 |
| W9 | Forms & Constitutional | 3 | 500+ forms + constitutional text | None |
| W10 | Convergence & Cross-Linking | 4 | Dedup, cross-link, IRAC, quality audit | All |

## CRITICAL ASSETS NOT YET INGESTED

| Path | Files | Priority | Content |
|------|-------|----------|---------|
| 09_REFERENCE/ | 5,613 HTML | CRITICAL | MCL statutes from legislature.mi.gov |
| 02_AUTHORITY/ | 2,253 | CRITICAL | MCR full text, authority CSVs, benchbooks |
| I:\ | 4,010 PDF | HIGH | Active case files, motions, briefs |
| D:\SCAO_FORMS | 130+ PDF | HIGH | SCAO court form PDFs |

## CATEGORY COVERAGE (11 categories, A-K)

- **A** Michigan Court Rules (MCR 1-9)
- **B** Michigan Compiled Laws (20 acts)
- **C** Michigan Rules of Evidence (MRE)
- **D** Case Law (MSC, COA, 6th Cir, SCOTUS)
- **E** Court Forms (SCAO, MC, FOC, MDHHS, AO)
- **F** Constitutional Law (MI + US)
- **G** Torts & Civil Theories (17 causes of action)
- **H** Criminal Law & Procedure
- **I** Defenses & Doctrines (15 mechanisms)
- **J** Specialized Areas (L/T, mobile home, probate, CPS, local rules)
- **K** Federal Law (§1983, RICO, Fair Housing, FRCP, ADA)

## CASE INTELLIGENCE — Pigors v. Watson (condensed from 41 sessions)

### Judicial Misconduct (5,059 documented violations)
- Ex parte: 3,697 (73%) | Benchbook: 504 | MCR 2.003 refusals: 167 | Procedural: 161 | PPO weaponization: 126 | Due process denial: 105 | Evidence exclusion: ~200
- **Aug 8, 2025 "Five Orders Day"**: Aug 5 USB recording → Aug 7 NS2505044 Albert premeditation admission → Aug 8 FIVE ex parte orders, zero notice
- **Contempt abuse**: SC#5 (14 days) + SC#6+7 (45 days) = 59 days jail. Lost 2 homes + 2 jobs. Birthday messages via AppClose = 1st Amendment violation

### Emily A. Watson — Escalating False Allegations
1. "Suicidal" → welfare checks cleared Andrew | 2. "Arsenic poisoning" → ER toxicology NEGATIVE | 3. "Physical assault" → police: no evidence | 4. "Drug use" → projection (Officer Randall: Emily admitted METH USE) | 5. "Threats" → AppClose shows normal communication

### Key Evidence (critical paths)
- Albert+Emily kitchen audio: `I:\08_AUDIO\albert and Emily audio nov 30 2023.mp3` (14.86 MB)
- Albert+Emily kitchen video: `I:\Appclose\EVERYTHIING\videos\Albertemily.mp4` (1.35 GB)
- NS2505044: Albert premeditation admission | HealthWest eval: Father deemed fit (LOCUS 12, excluded by McNeill)
- Desktop: MASTER_LITIGATION_ENCYCLOPEDIA.md, AUTHORITY_INVENTORY_COMPLETE.txt, COMPREHENSIVE_JUDICIAL_ANALYSIS.md

### Damages Model (§1983 + State)
| Category | Low | High |
|----------|-----|------|
| Lost parenting time | $100K | $500K |
| False imprisonment | $50K | $200K |
| Lost employment | $80K | $160K |
| Lost housing | $40K | $120K |
| Emotional distress | $100K | $500K |
| Punitive (§1983) | $250K | $1M |
| **TOTAL** | **$620K** | **$2.48M** |
