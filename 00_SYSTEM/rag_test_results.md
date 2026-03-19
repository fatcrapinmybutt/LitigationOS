# RAG Pipeline Test Results
**Run:** 2026-03-04 11:27:19

## 1. ChromaDB Connectivity

- **Store:** `C:\Users\andre\LitigationOS\00_SYSTEM\chromadb_store`
- **Collections found:** 2
  - `filing_stacks`: **265** documents
  - `evidence_master`: **1403** documents
- **Status:** ✅ ChromaDB operational

## 2. FTS5 Search Test — `evidence_quotes` for 'custody interference'

- **Query:** `custody interference`
- **Results:** 2 hits (showing top 5)

### FTS Result 1
- **Category:** general_court_doc
- **Speaker:** N/A
- **Quote:** ourt order, leading  to custody interference.  •  March 26, 2024: Emily filed a fabricated welfare check claiming...
- **Legal Significance:** Extracted DATE: March 26, 2024

### FTS Result 2
- **Category:** general_court_doc
- **Speaker:** N/A
- **Quote:** court order, leading to custody interference. 22. March 26, 2024 - Emily filed a fabricated welfare check, claimin...
- **Legal Significance:** Extracted DATE: March 26, 2024

- **Status:** ✅ FTS5 operational (2 results)

## 3. Hybrid Query Results (ChromaDB + FTS5)

### Query 1: What are the RICO allegations against Shady Oaks?

- **Search time:** 7.93s
- **Results:** 3 (hybrid)

**Result 1** [Vector] (score: 0.054)
- **Source:** `chromadb/evidence_master`
- **Metadata:** evidence_section=so_harms, item_index=6, court_action=Master Evidence Compilation, source_file=convergence_evidence.json, stack_name=EVIDENCE_MASTER, chunk_index=0
- **Text:** category: HOUSING_HARM adversary: Shady Oaks date_ref: July 17, 2024 description: HOUSING_HARM: include all of these, dont omit any   Service defects: PPO served by Emily’s parents in garage; show causes served during parenting exchanges, some under 5-day requirement.  False allegations: coca...

**Result 2** [Vector] (score: 0.054)
- **Source:** `chromadb/evidence_master`
- **Metadata:** chunk_index=0, source_file=convergence_evidence.json, evidence_section=watson_harms, stack_name=EVIDENCE_MASTER, item_index=60, court_action=Master Evidence Compilation
- **Text:** category: PARENTAL_ALIENATION adversary: Emily Watson date_ref: July 17, 2024 description: PARENTAL_ALIENATION: include all of these, dont omit any   Service defects: PPO served by Emily’s parents in garage; show causes served during parenting exchanges, some under 5-day requirement.  False alleg...

**Result 3** [Vector] (score: 0.054)
- **Source:** `chromadb/evidence_master`
- **Metadata:** stack_name=EVIDENCE_MASTER, evidence_section=watson_harms, court_action=Master Evidence Compilation, source_file=convergence_evidence.json, chunk_index=0, item_index=62
- **Text:** category: FALSE_IMPRISONMENT adversary: Emily Watson date_ref: July 17, 2024 description: FALSE_IMPRISONMENT: include all of these, dont omit any   Service defects: PPO served by Emily’s parents in garage; show causes served during parenting exchanges, some under 5-day requirement.  False allegat...

### Query 2: What evidence supports judicial bias by McNeill?

- **Search time:** 8.60s
- **Results:** 3 (hybrid)

**Result 1** [Vector] (score: 0.186)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** chunk_index=2, stack_name=JTC_MCNEILL, source_file=01_JTC_COMPLAINT.md, court_action=JTC Complaint - Judge McNeill, file_path=C:\Users\andre\LitigationOS\04_JTC_MCNEILL\FINAL_JTC_STACK\01_JTC_COMPLAINT.md
- **Text:** ng party - Made findings unsupported by evidence in the record  ### VIOLATION 3: Denial of Due Process (MCJC Canon 3(A)(3))  **Rule:** "A judge shall accord to every person who is legally interested in a proceeding, or the person's lawyer, full right to be heard according to law."  **Facts:** Plaint...

**Result 2** [Vector] (score: 0.147)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** file_path=C:\Users\andre\LitigationOS\01_COA_366810\FINAL_BRIEF_STACK\01_APPELLANTS_BRIEF_ON_APPEAL.md, stack_name=COA_366810_BRIEF, chunk_index=15, court_action=Court of Appeals Case 366810, source_file=01_APPELLANTS_BRIEF_ON_APPEAL.md
- **Text:** or (ii) has failed to adhere to the appearance of impropriety standard . . .  The record establishes actual bias through multiple categories of evidence:  ### 1. Asymmetric Ex Parte Pattern  Of 55 orders entered in the custody and PPO proceedings, 24 (44%) were entered ex parte — all 24 by Judge McN...

**Result 3** [Vector] (score: 0.141)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** chunk_index=16, file_path=C:\Users\andre\LitigationOS\01_COA_366810\FINAL_BRIEF_STACK\01_APPELLANTS_BRIEF_ON_APPEAL.md, source_file=01_APPELLANTS_BRIEF_ON_APPEAL.md, court_action=Court of Appeals Case 366810, stack_name=COA_366810_BRIEF
- **Text:** redetermined Outcome  The totality of the trial court's conduct is consistent with a court that reached its conclusion about Father before hearing from both sides:  - Orders entered before evidence was fully considered; - Findings of fact unsupported by the record; - Pattern consistent across 18+ mo...

### Query 3: What damages are claimed in the Watson tort action?

- **Search time:** 10.52s
- **Results:** 3 (hybrid)

**Result 1** [Vector] (score: 0.099)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** court_action=Watson Tort Action - 14th Circuit, source_file=01_CIVIL_TORT_COMPLAINT_WATSON.md, file_path=C:\Users\andre\LitigationOS\02_TRIAL_14TH\WATSON_TORT_STACK\01_CIVIL_TORT_COMPLAINT_WATSON.md, chunk_index=35, stack_name=WATSON_TORT
- **Text:** ious disregard for Plaintiff's rights    - Punitive damages are necessary to deter Defendants and others from similar conduct    - Michigan law permits exemplary damages where the defendant's conduct is willful and wanton. *Kewin v Massachusetts Mutual Life Ins Co*, 409 Mich 401 (1980)  ## VII. PRAY...

**Result 2** [Vector] (score: 0.067)
- **Source:** `chromadb/evidence_master`
- **Metadata:** source_file=convergence_evidence.json, chunk_index=0, stack_name=EVIDENCE_MASTER, evidence_section=so_claims, court_action=Master Evidence Compilation, item_index=28
- **Text:** cl_id: CL-20260123-0029 claim_type: ALLEGATION_FROM_COMPLAINT claim_text: Award compensatory damages in an amount to be proven at trial....

**Result 3** [Vector] (score: 0.062)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** chunk_index=1, source_file=06_ADVERSARY_REBUTTAL_FRAMEWORK.md, stack_name=WATSON_TORT, court_action=Watson Tort Action - 14th Circuit, file_path=C:\Users\andre\LitigationOS\02_TRIAL_14TH\WATSON_TORT_STACK\06_ADVERSARY_REBUTTAL_FRAMEWORK.md
- **Text:** - 3-year statute for tort; conduct ongoing through present.  ## ANTICIPATED DEFENSE 7: "Family Court Jurisdiction" **Their Argument:** Claims should be in family court. **Rebuttal:** Tort claims are separate from custody proceedings. Circuit court has jurisdiction over civil torts. Claims against no...

### Query 4: What is the timeline of custody interference?

- **Search time:** 9.90s
- **Results:** 3 (hybrid)

**Result 1** [Vector] (score: 0.084)
- **Source:** `chromadb/evidence_master`
- **Metadata:** source_file=convergence_evidence.json, chunk_index=0, stack_name=EVIDENCE_MASTER, evidence_section=timeline, court_action=Master Evidence Compilation, item_index=131
- **Text:** event_date: 2024-10-25 case_type: CUSTODY event_type: order actor: Emily Watson title: Lincoln during Andrew’s scheduled parenting time. October 25, 2024: Emily avoids mediation, forcing custody disputes description: Lincoln during Andrew’s scheduled parenting time. October 25, 2024: Emily avoids me...

**Result 2** [Vector] (score: 0.084)
- **Source:** `chromadb/evidence_master`
- **Metadata:** item_index=117, source_file=convergence_evidence.json, evidence_section=timeline, court_action=Master Evidence Compilation, chunk_index=0, stack_name=EVIDENCE_MASTER
- **Text:** event_date: 2024-10-20 case_type: CUSTODY event_type: order actor: Albert Watson title: rcing custody disputes into prolonged litigation. October 20, 2024: Albert Watson accosts Andrew during a parenting description: rcing custody disputes into prolonged litigation. October 20, 2024: Albert Watson a...

**Result 3** [Vector] (score: 0.064)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** source_file=01_APPELLANTS_BRIEF_ON_APPEAL.md, file_path=C:\Users\andre\LitigationOS\01_COA_366810\FINAL_BRIEF_STACK\01_APPELLANTS_BRIEF_ON_APPEAL.md, stack_name=COA_366810_BRIEF, chunk_index=5, court_action=Court of Appeals Case 366810
- **Text:** ation of court-ordered parenting time. (LCR, Father's Motion, filed 05/13/2024.) Additional extended denials occurred from October 20 through November 12, 2024. (LCR, Father's Filings.)  Father raised these denials before the trial court, but the court took no enforcement action against Mother and i...

### Query 5: What emergency motions are pending?

- **Search time:** 8.08s
- **Results:** 3 (hybrid)

**Result 1** [Vector] (score: 0.107)
- **Source:** `chromadb/evidence_master`
- **Metadata:** stack_name=EVIDENCE_MASTER, source_file=convergence_evidence.json, item_index=208, evidence_section=mcneill_harms, court_action=Master Evidence Compilation, chunk_index=0
- **Text:** category: JUDICIAL_BIAS adversary: Judge McNeill date_ref: 08/08/2025 description: JUDICIAL_BIAS: No motions, because of filing fee, and the objection hearing is today. SO just prep this as a legal brief for the objection hearing.🧨ORAL NARRATIVE – OBJECTION HEARING  Introduction Your Honor, Andrew...

**Result 2** [Vector] (score: 0.105)
- **Source:** `chromadb/filing_stacks`
- **Metadata:** court_action=Emergency Motions Package, file_path=C:\Users\andre\LitigationOS\06_EMERGENCY\FINAL_EMERGENCY_STACK\08_PROPOSED_ORDERS.md, source_file=08_PROPOSED_ORDERS.md, stack_name=EMERGENCY_MOTIONS, chunk_index=4
- **Text:** ________________________ HON. _________________________ Chief Judge, 14th Judicial Circuit  ---  *Note: These proposed orders are submitted pursuant to local court rules requiring the moving party to submit proposed orders with motions. The Court may modify these orders as it deems appropriate.*...

**Result 3** [Vector] (score: 0.035)
- **Source:** `chromadb/evidence_master`
- **Metadata:** court_action=Master Evidence Compilation, stack_name=EVIDENCE_MASTER, source_file=convergence_evidence.json, chunk_index=0, evidence_section=timeline, item_index=34
- **Text:** event_date: 2024-04-11 case_type: PPO event_type: ex_parte actor: Judge McNeill title: PPO Amended — Ex Parte Order description: Amended personal protection order (domestic) entered ex parte. Notice to appear issued. harm_to_andrew: Due process denied — no notice/hearing; Restricted freedom via PPO...

## Summary

| Component | Status |
|-----------|--------|
| ChromaDB | ✅ 1668 docs |
| FTS5 | ✅ Operational |
| Hybrid Search | ✅ Full hybrid |
| Ollama embeddings | ✅ Available |
| Test queries | 5 executed |