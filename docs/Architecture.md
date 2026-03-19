# LitigationOS — Architecture Diagrams

> Generated from verified audit data. Numbers reflect actual system state.

---

## 1. System Overview — Data Flow

```mermaid
flowchart TD
    subgraph Sources["📁 Raw File Sources"]
        C["C:\ Drive"]
        D["D:\ Drive"]
        F["F:\ Drive"]
        G["G:\ Drive"]
        H["H:\ Drive"]
        I["I:\ Drive"]
    end

    subgraph Pipeline["⚙️ 24-Phase Pipeline"]
        P0["Phase 0\nSafety Snapshot"]
        P1["Phase 1\nInventory"]
        P2["Phase 2\nDedup"]
        P3["Phase 3\nClassify"]
        P4["Phases 4a-4e\nExtract"]
        P5["Phase 5\nLEXOS Brain Feed"]
        P6["Phase 6\nGap Analysis"]
        P7["Phases 7a-7c\nGraph + Merge"]
        P8["Phase 8\nLitigation Refresh"]
        P9["Phase 9\nMCP Ingest"]
        P10["Phase 10\nJudicial Analysis"]
        P11["Phase 11\nLegal Action Discovery"]
        P12["Phase 12\nRule Audit"]
        P13_16["Phases 13-16\nRefine → Finalize → Validate → Offload"]
    end

    subgraph Intelligence["🧠 AI Stack (Local-Only)"]
        MBP["MANBEARPIG v9.0\nTF-IDF + NB + BM25"]
        LAI["LocalAI Engine\nClassify + Entities + Score"]
        BF["Bloom Filter\n3.7M citations, O(1)"]
        PC["Prefetch Cache\n9 categories, parallel"]
    end

    subgraph Outputs["📋 Court-Ready Outputs"]
        Filings["Filings & Motions"]
        Exhibits["Exhibit Binders"]
        Briefs["Appellate Briefs"]
        Packets["Court Packets"]
    end

    Sources --> P0 --> P1 --> P2 --> P3 --> P4
    P4 --> P5 --> P6 --> P7 --> P8 --> P9
    P9 --> P10 --> P11 --> P12 --> P13_16

    MBP -.->|inference| P5
    LAI -.->|classify + score| P3
    BF -.->|verify citations| P13_16
    PC -.->|prefetch hot data| P13_16

    P13_16 --> Filings
    P13_16 --> Exhibits
    P13_16 --> Briefs
    P13_16 --> Packets
```

---

## 2. Pipeline Phases — 24 Phases with Dependencies

```mermaid
flowchart LR
    subgraph Foundation["Foundation (Phases 0-3)"]
        direction TB
        Ph0["0: Safety Snapshot\nSHA-256 manifest"]
        Ph1["1: Inventory\nMulti-drive scan"]
        Ph2["2: Dedup\nContent-based"]
        Ph3["3: Classify\nMEEK lane assignment"]
        Ph0 --> Ph1 --> Ph2 --> Ph3
    end

    subgraph Extraction["Extraction (Phases 4a-4e)"]
        direction TB
        Ph4a["4a: PDF Extract"]
        Ph4b["4b: DOCX Extract"]
        Ph4c["4c: Structured Extract"]
        Ph4d["4d: Atomize"]
        Ph4e["4e: Archive Extract"]
        Ph4a --> Ph4d
        Ph4b --> Ph4d
        Ph4c --> Ph4d
        Ph4d --> Ph4e
    end

    subgraph Intelligence["Intelligence (Phases 5-6)"]
        direction TB
        Ph5["5: LEXOS Brain Feed\n50 micro-brains"]
        Ph6["6: Gap Analysis\nEGCP scoring"]
        Ph5 --> Ph6
    end

    subgraph Graph["Graph (Phases 7a-7c)"]
        direction TB
        Ph7a["7a: Graph Delta"]
        Ph7b["7b: Synthesis Merge"]
        Ph7c["7c: Knowledge Merge"]
        Ph7a --> Ph7b --> Ph7c
    end

    subgraph Integration["Integration (Phases 8-12)"]
        direction TB
        Ph8["8: Litigation Refresh"]
        Ph9["9: MCP Ingest"]
        Ph10["10: Judicial Analysis"]
        Ph11["11: Legal Action Discovery"]
        Ph12["12: Rule Audit"]
        Ph8 --> Ph9 --> Ph10 --> Ph11 --> Ph12
    end

    subgraph Finalization["Finalization (Phases 13-16)"]
        direction TB
        Ph13["13: Refinement"]
        Ph14["14: Finalization"]
        Ph15["15: Validation"]
        Ph16["16: Desktop Offload"]
        Ph13 --> Ph14 --> Ph15 --> Ph16
    end

    Foundation --> Extraction --> Intelligence --> Graph --> Integration --> Finalization
```

---

## 3. Agent Fleet — 48 Agents in 7 Tiers

```mermaid
flowchart TD
    subgraph Tier1["Tier 1 — I/O Foundation"]
        A01["A01: File Scanner"]
        A02["A02: Hasher"]
        A03["A03: Dedup Engine"]
        A04["A04: Classifier"]
    end

    subgraph Tier2["Tier 2 — Extraction"]
        A05["A05: PDF Extractor"]
        A06["A06: DOCX Extractor"]
        A07["A07: Structured Parser"]
        A08["A08: Atomizer"]
    end

    subgraph Tier3["Tier 3 — Enrichment"]
        A09["A09: Entity Extractor"]
        A10["A10: Metadata Tagger"]
        A11["A11: Citation Linker"]
        A12["A12: Timeline Builder"]
    end

    subgraph TierJ["Tier J — Judicial Intelligence"]
        J01["J01: Judicial Profiler"]
        J02["J02: Bias Detector"]
        J03["J03: Violation Scanner"]
        J04["J04: Disqualification Analyst"]
    end

    subgraph TierK["Tier K — Case Intelligence"]
        K01["K01: Claim Mapper"]
        K02["K02: Evidence Scorer"]
        K03["K03: Impeachment Finder"]
        K04["K04: Contradiction Detector"]
    end

    subgraph TierL["Tier L — Legal Analysis"]
        L01["L01: Rule Auditor"]
        L02["L02: Authority Chain Builder"]
        L03["L03: Gap Analyzer"]
        L04["L04: Risk Assessor"]
    end

    subgraph TierF["Tier F — Convergence / Filing"]
        F01["F01: Filing Assembler"]
        F02["F02: Brain Feed Generator"]
        F03["F03: Graph Builder"]
        F04["F04: Certification Engine"]
        F05["F05: Export Manager"]
        F06["F06: Quality Gate"]
    end

    Tier1 -->|extracted files| Tier2
    Tier2 -->|atoms + text| Tier3
    Tier3 -->|enriched data| TierJ
    Tier3 -->|enriched data| TierK
    TierJ -->|judicial findings| TierF
    TierK -->|case intel| TierL
    TierL -->|legal analysis| TierF
```

---

## 4. Database Landscape — Central DB + Lane DBs

```mermaid
flowchart TD
    subgraph Central["🗄️ Central Database"]
        CDB["litigation_context.db\n702 tables · 10.98 GB\nWAL mode · mmap 12 GB"]
    end

    subgraph LaneDBs["📂 Case Lane Databases"]
        LA["lane_A_custody.db\n2024-001507-DC\n2023-5907-PP"]
        LB["lane_B_housing.db\n2025-002760-CZ"]
        LC["lane_C_convergence.db\nCross-lane data"]
        LD["lane_D_ppo.db\nProtection Orders"]
        LE["lane_E_misconduct.db\nJudicial / JTC"]
        LF["lane_F_appellate.db\nCOA 366810"]
    end

    subgraph Support["🔧 Support Databases"]
        MDB["master_index.db\nAgent data · WAL"]
        MEEK["MEEK_index.db\nLane classification"]
        DI["drive_inventory.db\nMulti-drive file index"]
        DF["document_fulltext.db\nFTS5 full-text search"]
        MCR["mcr_rules.db\nMichigan Court Rules"]
    end

    subgraph Cache["⚡ Performance Layer"]
        BF["Bloom Filter\n~9.6 MB in-memory\n0.01% FP rate"]
        PFC["Prefetch Cache\n9 categories · 50 MB cap\n120s TTL · 6 threads"]
    end

    CDB -->|lane routing| LA
    CDB -->|lane routing| LB
    CDB -->|lane routing| LC
    CDB -->|lane routing| LD
    CDB -->|lane routing| LE
    CDB -->|lane routing| LF

    CDB ---|agent writes| MDB
    CDB ---|classification| MEEK
    CDB ---|file index| DI
    CDB ---|search| DF
    CDB ---|rules| MCR

    CDB -->|3.7M citations| BF
    CDB -->|hot path queries| PFC
```

---

## 5. MCP Tool Categories — 47 Tools

```mermaid
flowchart LR
    subgraph MCP["litigation-context-mcp v2\n47 Tools"]
        direction TB

        subgraph Core["Core (10)"]
            C1["scan_drives"]
            C2["ingest_pdf"]
            C3["bulk_ingest"]
            C4["search (FTS5)"]
            C5["list_documents"]
            C6["get_document"]
            C7["get_stats"]
            C8["upcoming_deadlines"]
            C9["filing_search"]
            C10["evidence_lookup"]
        end

        subgraph Filing["Filing (8)"]
            F1["filing_readiness"]
            F2["filing_validate"]
            F3["filing_assemble"]
            F4["efiling_prep"]
            F5["brief_compliance"]
            F6["placeholder_scan"]
            F7["placeholder_resolve"]
            F8["filing_export"]
        end

        subgraph Evidence["Evidence (7)"]
            E1["evidence_chain"]
            E2["evidence_gaps"]
            E3["evidence_link"]
            E4["evidence_authenticate"]
            E5["bates_assign"]
            E6["exhibit_index"]
            E7["evidence_timeline"]
        end

        subgraph Deadline["Deadline (5)"]
            D1["deadline_dashboard"]
            D2["deadline_ics"]
            D3["deadline_urgency"]
            D4["deadline_add"]
            D5["deadline_update"]
        end

        subgraph Analysis["Analysis (5)"]
            An1["authority_index"]
            An2["citation_graph"]
            An3["impeachment_search"]
            An4["contradiction_find"]
            An5["judicial_bias_scan"]
        end

        subgraph QA["QA (4)"]
            Q1["prefiling_qa"]
            Q2["qa_sweep"]
            Q3["signature_check"]
            Q4["service_check"]
        end

        subgraph Backup["Backup (3)"]
            B1["backup_create"]
            B2["backup_version"]
            B3["backup_report"]
        end

        subgraph Calendar["Calendar (2)"]
            Ca1["calendar_generate"]
            Ca2["calendar_sync"]
        end

        subgraph System["System (1)"]
            S1["system_health"]
        end
    end

    subgraph Consumers["Consumers"]
        CP["Copilot CLI"]
        GUI["Desktop GUI"]
        AG["Agent Fleet"]
    end

    Core --> Consumers
    Filing --> Consumers
    Evidence --> Consumers
    Deadline --> Consumers
    Analysis --> Consumers
    QA --> Consumers
    Backup --> Consumers
    Calendar --> Consumers
    System --> Consumers
```

---

## 6. Six Case Lanes — Routing Architecture

```mermaid
flowchart TD
    Input["Incoming Evidence / Document"]

    subgraph MEEK["MEEK Signal Detection\nPriority: E → D → F → C → A → B"]
        M4["MEEK4: Judicial keywords"]
        M3["MEEK3: PPO keywords"]
        M5["MEEK5: Appellate keywords"]
        MC["Cross-lane signals"]
        M2["MEEK2: Custody keywords"]
        M1["MEEK1: Housing keywords"]
    end

    Input --> MEEK

    M4 -->|"match"| LaneE["Lane E — Judicial Misconduct\nJudge McNeill · JTC"]
    M3 -->|"match"| LaneD["Lane D — PPO\nProtection Orders"]
    M5 -->|"match"| LaneF["Lane F — Appellate\nCOA 366810"]
    MC -->|"match"| LaneC["Lane C — Convergence\nCross-lane synthesis"]
    M2 -->|"match"| LaneA["Lane A — Custody\nWatson · 2024-001507-DC"]
    M1 -->|"match"| LaneB["Lane B — Housing\nShady Oaks · 2025-002760-CZ"]

    LaneE -->|"⛔ cross-contamination guard"| LaneE
    LaneA -->|"⛔ cross-contamination guard"| LaneA

    style LaneE fill:#ff6b6b,color:#000
    style LaneD fill:#ffa07a,color:#000
    style LaneF fill:#87ceeb,color:#000
    style LaneC fill:#dda0dd,color:#000
    style LaneA fill:#90ee90,color:#000
    style LaneB fill:#f0e68c,color:#000
```

---

## Appendix: Performance Module Audit Summary

### Bloom Citation Filter (`bloom_citation_filter.py`)

| Metric | Value |
|--------|-------|
| Target FP rate | 0.01% (1 in 10,000) |
| Memory | ~9.6 MB (bytearray-backed bitfield) |
| Hash function | MurmurHash3 128-bit (Kirsch-Mitzenmacker double-hashing) |
| Data sources | `master_citations` (3.7M rows) + `auth_rules` (1.2K rows) |
| Thread safety | Yes — `threading.Lock` on add, lock-free reads |
| Lazy loading | Yes — double-checked locking via `_ensure_loaded()` |
| Production use | **Yes** — imported by `filing_production_pipeline.py` (line 354), validated by `phase3_validate.py` |
| API | `contains()` O(1), `verify_batch()`, `verify_with_fallback()` (Bloom + DB confirm) |
| Extension potential | High — same `BloomFilter` class works for evidence hashes, filing IDs, or any membership test |

### Prefetch Cache (`prefetch_cache.py`)

| Metric | Value |
|--------|-------|
| Categories cached | 9: claims, evidence, claim_evidence_links, authority, auth_rules, deadlines, filing_readiness, impeachment, judicial_violations |
| Max memory | 50 MB soft cap (size-based eviction) |
| TTL | 120 seconds per entry |
| Parallelism | 6 worker threads via `ThreadPoolExecutor` |
| Invalidation | TTL-based expiry + explicit `invalidate()` + size-based LRU eviction |
| Thread safety | Yes — `threading.Event` per entry for blocking get, `threading.Lock` for store |
| Production use | **Not yet imported** — singleton `cache` is ready but no consumer imports it |
| Schema safety | Validates table/column existence before every query via `PRAGMA table_info()` |
| DB tuning | WAL + mmap 12 GB + 128 MB cache + `query_only=ON` |