# MSC Original Action Engine & Multi-Jurisdiction Compass
# Extracted from copilot-instructions.md for context-window efficiency

---

## MSC Available Actions — Full Inventory

| # | Action | Authority | Standard | Viability |
|---|--------|-----------|----------|-----------|
| 1 | **Superintending Control** | MCR 7.306; Const 1963 art 6 § 4 | No adequate remedy; excess of jurisdiction | ★★★★★ |
| 2 | **Mandamus** | MCR 7.306 | Clear legal duty + clear legal right | ★★★★★ |
| 3 | **Habeas Corpus** | Const 1963 art 1 § 12; MCL 600.4301 | Unlawful restraint of liberty/parental rights | ★★★★☆ |
| 4 | **Prohibition** | MCR 7.306; common law | Lower court acting in excess of jurisdiction | ★★★★☆ |
| 5 | **Emergency Application** | MCR 7.305(F); MCR 7.315(C) | Irreparable harm; immediate relief needed | ★★★★★ |
| 6 | **Declaratory Judgment** | MCL 600.605; MCR 2.605 | Actual controversy over legal relations | ★★★★☆ |
| 7 | **Leave to Appeal (bypass COA)** | MCR 7.305(B)(2) | Issue of major significance | ★★★☆☆ |
| 8 | **Quo Warranto** | MCL 600.4501 | Officer acting outside authority | ★★☆☆☆ |
| 9 | **42 USC § 1983** | 28 USC § 1343 | Deprivation of rights under color of law | ★★★★☆ |
| 10 | **JTC Complaint** | MCR 9.200-9.252 | Judicial misconduct | ALREADY FILED |

## MLLM Methods for MSC Actions

| Method | JSON-RPC Name | Description | Parameters |
|--------|--------------|-------------|------------|
| `msc_original_action_scan()` | `msc_scan` | Scan DB for evidence supporting each MSC action type | action_type (str or "all") |
| `map_evidence_to_grounds()` | `map_evidence` | 3-pass evidence mapping to 12 legal grounds | grounds (list or None=all) |
| `multi_jurisdiction_query()` | `multi_jurisdiction` | Query across 5 jurisdictions simultaneously | topic, jurisdictions |
| `mcneill_pattern_analysis()` | `mcneill_analysis` | Deep McNeill violation pattern analysis | (none) |

## Evidence-to-Ground Mapping (12 Grounds)

| Ground | Authority | Evidence Count |
|--------|-----------|---------------|
| ex_parte_violations | MCR 3.207(C)(2); MCR 2.119(B)(1); Canon 3(A)(5) | 1,720+ |
| due_process | US Const Amend XIV; Mathews v Eldridge | 274+ |
| endangerment_finding | MCL 722.27a(3); Eldred v Ziny | 707+ |
| disparate_treatment | Equal Protection; Reed v Reed | 9+ |
| disqualification | MCR 2.003(C)(1); MCR 2.003(D) | 785+ |
| ppo_weaponization | MCL 600.2950; MCR 3.707; MRE 602 | 45+ |
| bond_barrier | Boddie v Connecticut; Const art 1 § 13 | 3,941+ |
| muting_silencing | Due Process; Canon 3(A)(4) | 21+ |
| exculpatory_evidence_ignored | MRE 401-403; Brady v Maryland | 146+ |
| contempt_abuse | MCR 3.606; MCL 600.1701 | 1,612+ |
| parental_alienation | MCL 722.23(j); Lombardo v Lombardo | 194+ |
| off_record_evidence | Canon 3(A)(5); MCR 2.107 | 50+ |

## Specific McNeill/Emily Actions to Undo

| # | Action | Date | Authority Violated | Remedy |
|---|--------|------|--------------------|--------|
| 1 | Ex parte order suspending ALL parenting time | Aug 9, 2025 | MCR 3.207(C)(2), MCL 722.27a(3) | VACATE via superintending control |
| 2 | $250 bond requirement for new filings | ~Apr 2025 | Boddie v Connecticut, MCR 2.003 | VACATE — unconstitutional |
| 3 | Denial of motion to restore parenting time | Sep 9, 2025 | MCL 722.27a, Due Process | REVERSE via mandamus |
| 4 | PPO extensions based on false allegations | Multiple | MCL 600.2950, MRE 801 | VACATE — no competent evidence |
| 5 | Contempt findings | Multiple | MCR 3.606, Due Process | VACATE — procedural violations |
| 6 | Denial of disqualification motion (self-ruling) | Sep 2024 | MCR 2.003(D) — Chief Judge must decide | REVERSE + reassign |
| 7 | 156+ defective ex parte orders | 2024-2025 | MCR 3.207, MCR 2.119(B)(1) | MASS VACATUR |
| 8 | Accepting Emily's unverified allegations | Ongoing | MRE 602, MRE 801, MRE 901 | STRIKE from record |
| 9 | Refusing to view exculpatory evidence (photos) | Aug 28, 2025 | MRE 401-403, Due Process | Mandate evidentiary hearing |
| 10 | Ex parte handling of USB/HealthWest evidence | Multiple | Canon 3(A)(5), Due Process | Declare void |
| 11 | Muting/silencing Plaintiff at hearings | Multiple | Due Process, Canon 3(A)(4) | Mandate right to be heard |
| 12 | Disparate treatment (zero sanctions on Emily) | Ongoing | Equal Protection, Canon 2A | Equal enforcement order |

## 5 Jurisdictions — Coordinated Escalation

| Jurisdiction | Court | Filing Vehicle | Deadline |
|-------------|-------|---------------|----------|
| **Circuit** | 14th Circuit, Muskegon County | Emergency Motion to Restore PT; Motion to Disqualify | ASAP |
| **COA** | Michigan Court of Appeals | Appellant Brief (COA 366810) | 2026-04-15 |
| **MSC** | Michigan Supreme Court | Superintending Control + Mandamus + Emergency App | 2026-04-01 |
| **Federal** | USDC Western District of Michigan | 42 USC § 1983 Complaint | 2026-04-30 |
| **JTC** | Judicial Tenure Commission | Formal Complaint | FILED |

## Authority Hierarchy (per jurisdiction)

**Michigan Circuit:** MCR → MCL → MRE → Michigan Case Law → SCAO Forms
**Michigan COA:** MCR Ch 7 → MCL → MRE → Published MI COA → MI Supreme Court
**Michigan MSC:** Const 1963 → MCR Ch 7.3xx → MCL → MSC precedent
**Federal USDC:** US Constitution → 42 USC → 28 USC → FRCP → 6th Circuit precedent
**JTC:** Const 1963 art 6 § 30 → MCR 9.200-9.252 → Code of Judicial Conduct

## MLLM Architecture Summary

| Component | Details |
|-----------|---------|
| **Algorithm** | TF-IDF + Naive Bayes + Cosine Similarity |
| **Corpus** | 200,000 documents |
| **Vocabulary** | 50,000 terms |
| **Features** | 50,000 TF-IDF features |
| **Intent Classes** | 8 (case_law, court_rules, deadlines, evidence, filings, judicial, statutes, strategy) |
| **Document Types** | 34 classes |
| **Legal Concepts** | 29 (20 base + 9 MSC/federal additions) |
| **Inference Engine** | 2,889 lines Python at `00_SYSTEM/local_model/inference_engine.py` |

## Brain & Learning Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `brain_stats` | Knowledge cluster health metrics | (none) |
| `knowledge_gaps` | Get identified knowledge gaps | limit |
| `resolve_gap` | Mark a knowledge gap resolved | gap_id, note |
| `feedback` | Rate a query result for learning | query_id, rating, comment |
| `get_weak_areas` | Identify weak knowledge areas | (none) |
| `auto_diagnose` | Self-diagnosis of model health | (none) |
