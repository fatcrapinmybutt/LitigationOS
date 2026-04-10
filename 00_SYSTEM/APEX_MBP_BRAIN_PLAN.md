# APEX THEMANBEARPIG BRAIN TRANSFORMATION PLAN
# LitigationOS — The Complete Litigation Intelligence System
# Generated: April 5, 2026 — Day 251 of Separation from L.D.W.

---

## 1. EXECUTIVE SUMMARY

**Current State:** THEMANBEARPIG.exe is a 22.5 MB standalone PixiJS WebGL2 visualization
with 2,500 nodes x 2,000 links x 20 layers, plus a LitigationAPI that performs live DB
queries via pywebview. It shows the data beautifully but CANNOT THINK.

**Target State:** Transform MBP into the BRAIN of a complete Litigation Operating System
that can reason about evidence, generate legal arguments, produce court-ready filings,
detect patterns, and advise on strategy — all locally, zero API cost, zero dependency.

**Key Insight:** 27+ engines ALREADY EXIST in `00_SYSTEM/engines/` — they just aren't
wired into the exe. The transformation is 80% WIRING + 20% NEW CAPABILITIES.

---

## 2. EXISTING ARSENAL (What We Already Have)

### 2A. Database Corpus (1.3 GB, 337+ tables)

| Table | Rows | Purpose |
|-------|------|---------|
| evidence_quotes | 176,222 | Core evidence with quotes, sources, lanes |
| authority_chains_v2 | 168,261 | Citation chains (MCR/MCL/MRE/case law) |
| michigan_rules_extracted | 19,876 | Full text of Michigan court rules |
| timeline_events | 16,886 | Chronological case events |
| impeachment_matrix | 5,229 | Cross-examination ammunition |
| critical_facts | 3,048 | Verified immutable facts |
| contradiction_map | 2,534 | Adversary contradictions |
| judicial_violations | 1,956 | Judicial misconduct evidence |
| narrative_events | 850 | Court-ready narrative events |
| rebuttal_matrix | 588 | Adversary claim rebuttals |
| police_reports | 356 | NSPD incident reports |
| berry_mcneill_intelligence | 222 | Judicial cartel intelligence |
| irac_analyses | 162 | IRAC argument structures (6 lanes) |
| damages_calculation | 30 | Per-lane damage items |
| filing_readiness | 17 | Filing pipeline status |
| **TOTAL ACTIVE** | **~395,000+** | **Across 15 core tables** |

### 2B. Engine Fleet (27+ functional engines)

#### TIER 1 — Reasoning Engines (EXIST, NOT wired to MBP)
| Engine | Lines | What It Does | Status |
|--------|-------|-------------|--------|
| **irac** | 276 | IRAC argument synthesis, lane analysis, brief section generation, gap detection | READY |
| **damages** | 282 | Dynamic damages calculator, treble/punitive, per-day rates, court-ready text | READY |
| **qa** | 900+ | 12-gate filing validator (contamination, hallucinations, names, dates, citations) | READY |
| **narrative** | 400+ | Chronological narrative builder, severity levels, evidence binding | READY |
| **rebuttal** | ~200 | Adversary claim rebuttal generation | READY |
| **causal** | ~200 | Causal analysis between events | READY |
| **adversary** | ~300 | Adversary profiling, pattern detection | READY |

#### TIER 2 — Search & Intelligence Engines (EXIST, partially wired)
| Engine | Lines | What It Does | Status |
|--------|-------|-------------|--------|
| **search/hybrid** | 350+ | 3-stage: FTS5/BM25 -> LanceDB vectors -> cross-encoder reranking | READY |
| **semantic** | 500+ | LanceDB vector store (75K vectors, 384-dim all-MiniLM-L6-v2) | READY |
| **perception** | 400+ | Legal-BERT ONNX INT8 — document classification, NER, claim extraction | READY |
| **nexus** | 300+ | Cross-table evidence fusion, argument chain synthesis | READY |
| **chimera** | ~200 | Multi-source evidence blending | READY |
| **analytics** | ~200 | DuckDB analytical dashboards | READY |

#### TIER 3 — Pipeline Engines (EXIST, NOT wired to MBP)
| Engine | Lines | What It Does | Status |
|--------|-------|-------------|--------|
| **typst** | 500+ | Markdown -> Typst -> court-ready PDF (all court formats) | READY |
| **filing_engine** | ~300 | Filing pipeline F1-F10 management | READY |
| **filing_assembler** | ~300 | Complete packet assembly (motion+brief+affidavit+exhibits+COS) | READY |
| **cerberus** | ~200 | Filing validation and compliance checking | READY |
| **forge** | ~200 | Document forge engine | READY |
| **intake** | ~100 | Go binary wrapper for 8-worker goroutine ingest | READY |

#### TIER 4 — Specialized Engines (EXIST, various states)
| Engine | Lines | What It Does | Status |
|--------|-------|-------------|--------|
| **chronos** | ~200 | Timeline construction, event ordering | READY |
| **temporal** | ~200 | Temporal pattern analysis | READY |
| **meek234_fullstack** | ~400 | MEEK lane routing (evidence -> A/B/C/D/E/F) | READY |
| **hypergraph** | ~200 | NetworkX bipartite knowledge graph | READY |
| **oracle** | ~200 | Intelligence oracle queries | READY |
| **nemesis** | ~200 | Counter-strategy generation | READY |
| **event_horizon** | 2000+ | 12-subsystem mega-engine (genesis, hydra, oracle, monad...) | READY |

#### TIER 5 — Infrastructure
| Engine | What It Does |
|--------|-------------|
| **ingest** | Go 8-worker goroutine file processing (57K files processed) |
| **lexicon** | Legal terminology engine |
| **orchestrator** | Multi-engine orchestration |
| **hydra_governor** | Hydra fleet governance |

### 2C. What THEMANBEARPIG.exe Currently Does

**Builder** (`build_manbearpig_v7.py`, 1,352 lines):
- 12-phase DB extraction from 10 tables
- Generates 2,500 nodes across 20 visualization layers
- Generates 2,000 links with 15+ relationship types
- PixiJS WebGL2 template with D3.js v7 force simulation
- KRAKEN overlay auto-merge (28 evidence hunting nodes)
- Self-contained HTML (all data embedded, no external deps)

**Launcher** (`adversary_blueprint.py`, 1,060 lines):
- pywebview Edge Chromium window (1920x1080)
- `LitigationAPI` class with 20+ methods:
  - U01: Live separation counter
  - U02: Filing status dashboard
  - U03: Timeline scrubber
  - U04: Evidence search (FTS5 + LIKE fallback)
  - U05: Node intelligence panel
  - U06: Adversary dossier rollup
  - U07: Judicial violation heatmap
  - U10: Read-only SQL console
  - U17: Annotation sync
  - U18: Pattern detection (retaliation + escalation)
  - U20: Live stats dashboard
- `INJECT_JS` (~700 lines): 11 command palette commands, 8 visual FX, keyboard nav, bookmarks

### 2D. What's MISSING (The Gap Analysis)

| Capability | Engine Exists? | Wired to MBP? | Gap |
|-----------|---------------|---------------|-----|
| IRAC argument generation | YES (irac engine) | NO | WIRING |
| Damages calculation | YES (damages engine) | NO | WIRING |
| Filing QA validation | YES (qa engine) | NO | WIRING |
| Court-ready PDF generation | YES (typst engine) | NO | WIRING |
| Narrative construction | YES (narrative engine) | NO | WIRING |
| Semantic search | YES (semantic engine) | NO | WIRING |
| Hybrid search (3-stage) | YES (search engine) | NO | WIRING |
| Document classification | YES (perception engine) | NO | WIRING |
| Rebuttal generation | YES (rebuttal engine) | NO | WIRING |
| Filing assembly | YES (filing_assembler) | NO | WIRING |
| Cross-table fusion | YES (nexus engine) | NO | WIRING |
| Pattern detection | PARTIAL (2 patterns) | PARTIAL | EXPAND |
| Local LLM reasoning | NO | NO | **NEW** |
| Evidence ingestion from exe | NO (Go binary) | NO | **NEW** |
| Deadline tracking in graph | NO (data exists) | NO | **NEW** |
| Filing production workflow | NO (engines separate) | NO | **NEW** |
| Legal argument advisor | NO | NO | **NEW** |
| Cross-examination generator | NO (data exists) | NO | **NEW** |

**SUMMARY: 12 capabilities need WIRING, 6 need NEW development.**

---

## 3. APEX MODULE ARCHITECTURE

Seven modules transform MBP from "pretty visualization" to "litigation brain."

```
+=====================================================================+
|                    THEMANBEARPIG.exe (pywebview)                     |
|                                                                      |
|   +------------------+   +------------------+   +-----------------+  |
|   | VISUALIZATION    |   | HUD / DASHBOARD  |   | COMMAND PALETTE |  |
|   | (PixiJS WebGL2)  |   | (Stats, Gauges)  |   | (11 commands)   |  |
|   | 20 layers        |   | Separation ctr   |   | + 15 NEW cmds   |  |
|   | 2,500 nodes      |   | Filing status    |   |                 |  |
|   +--------+---------+   +--------+---------+   +--------+--------+  |
|            |                       |                       |          |
|   +--------v-----------------------v-----------------------v--------+ |
|   |              LitigationAPI (pywebview JS bridge)                | |
|   |   20 existing methods + 25 NEW engine-wired methods             | |
|   +-----+------+------+------+------+------+------+------+---------+ |
|         |      |      |      |      |      |      |      |           |
|   +-----v--+ +-v----+ +v---+ +v---+ +v---+ +v---+ +v---+ +v------+  |
|   |CORTEX  | |COUNSEL| |FORGE| |SENT| |NEXUS| |PERC| |AUTH| |XEXAM|  |
|   |Orchestr| |LLM    | |File | |INEL| |Fusn | |EPTN| |ORTY| |Cross|  |
|   +--------+ +-------+ +----+ +----+ +-----+ +----+ +----+ +-----+  |
|         |      |      |      |      |      |      |      |           |
|   +-----v------v------v------v------v------v------v------v---------+ |
|   |                    ENGINE FLEET (27+ engines)                   | |
|   |  irac | damages | qa | typst | narrative | semantic | search   | |
|   |  perception | nexus | chimera | chronos | adversary | rebuttal | |
|   |  filing_engine | filing_assembler | cerberus | forge | meek234 | |
|   +-----+------+------+------+------+------+------+------+---------+ |
|         |      |      |      |      |      |      |      |           |
|   +-----v------v------v------v------v------v------v------v---------+ |
|   |                  litigation_context.db (1.3 GB)                 | |
|   |  176K evidence | 168K authorities | 19.8K rules | 16.8K events | |
|   |  75K vectors | 5.2K impeachment | 2.5K contradictions | 1.9K jv | |
|   +----------------------------------------------------------------+ |
+=====================================================================+
```

---

## 4. MODULE SPECIFICATIONS

### MODULE 1: CORTEX — Engine Orchestrator
**Purpose:** Single API that routes requests to the right engine(s)
**Wires:** ALL 27+ engines into unified access
**What's New:** Orchestration layer, multi-engine pipelines, intent classification

```python
# Architecture: cortex.py (~400 lines)
class Cortex:
    """Central engine orchestrator for THEMANBEARPIG brain."""
    
    def __init__(self, db_path):
        self._engines = {}   # Lazy-loaded engine registry
        self._db = db_path
    
    def analyze_evidence(self, text: str) -> dict:
        """Full pipeline: classify -> extract -> lane -> IRAC -> damages"""
        doc_type = self.perception.classify(text)
        entities = self.perception.extract_entities(text)
        lane = self.meek.route(text)
        irac = self.irac.get_arguments_by_lane(lane)
        damages = self.damages.get_lane_damages(lane)
        return {doc_type, entities, lane, irac, damages}
    
    def generate_argument(self, claim: str, lane: str) -> dict:
        """IRAC + evidence + authorities + rebuttal for a claim"""
        evidence = self.search.hybrid_search(claim)
        irac = self.irac.get_argument(claim)
        authorities = self.authority.find_for_claim(claim)
        rebuttal = self.rebuttal.generate(claim)
        return {evidence, irac, authorities, rebuttal}
    
    def build_filing(self, lane: str, filing_type: str) -> str:
        """Complete filing production: IRAC -> Narrative -> Typst -> PDF"""
        arguments = self.irac.generate_brief_section(lane)
        narrative = self.narrative.build_chronology(lane)
        damages_text = self.damages.get_filing_damages(lane)
        md = self.forge.assemble(arguments, narrative, damages_text)
        qa_report = self.qa.validate(md)
        if qa_report.passed:
            pdf_path = self.typst.compile_document(md, filing_type)
            return pdf_path
        return qa_report
```

**LitigationAPI methods to add:**
- `cortex_analyze(text)` — Full evidence analysis pipeline
- `cortex_argue(claim, lane)` — Argument chain synthesis
- `cortex_build_filing(lane, type)` — Filing production
- `cortex_status()` — Engine fleet health check

### MODULE 2: COUNSEL — Local LLM Legal Reasoning
**Purpose:** Local LLM (Ollama llama3.2:3b) for legal reasoning, argument generation, and strategy
**What's New:** RAG pipeline, structured legal output, cross-exam generation
**Hardware:** CPU-only, llama3.2:3b (1.9 GB), <2s inference on Ryzen 3 3200G

```python
# Architecture: counsel.py (~500 lines)
class Counsel:
    """Local LLM legal reasoning engine using Ollama."""
    
    def __init__(self):
        self.ollama = OllamaClient("llama3.2:3b")
        self.search = HybridSearch()  # 3-stage search for context
    
    def reason(self, question: str, lane: str = None) -> dict:
        """RAG: question -> hybrid search -> context -> LLM -> cited answer"""
        # Stage 1: Retrieve relevant context
        evidence = self.search.search(question, top_k=10)
        authorities = self.search.search_authorities(question, top_k=5)
        rules = self.search.search_rules(question, top_k=3)
        
        # Stage 2: Assemble structured prompt
        context = self._build_rag_context(evidence, authorities, rules)
        prompt = f"""You are a Michigan litigation expert. Answer using ONLY 
        the provided evidence and legal authorities. Cite specific exhibits 
        and rule numbers. If unsure, say "insufficient evidence."
        
        Context: {context}
        Question: {question}
        Format: IRAC (Issue, Rule, Application, Conclusion)"""
        
        # Stage 3: Generate structured response
        response = self.ollama.generate(prompt, max_tokens=1000)
        
        # Stage 4: Verify citations exist in DB
        verified = self._verify_citations(response)
        return {"answer": response, "citations": verified, "sources": evidence}
    
    def cross_examine(self, witness: str) -> list:
        """Generate cross-examination questions from impeachment data"""
        impeachment = db.query(impeachment_matrix, target=witness)
        contradictions = db.query(contradiction_map, entity=witness)
        
        prompt = f"""Generate 10 cross-examination questions for {witness}
        using COMMIT-PIN-CONFRONT-EXHIBIT structure.
        
        Impeachment material: {impeachment}
        Contradictions: {contradictions}
        
        Each question must reference a specific exhibit or statement."""
        
        return self.ollama.generate(prompt)
    
    def predict_opposition(self, our_filing: str) -> dict:
        """Predict opposing counsel's response to our filing"""
        rebuttal_data = db.query(rebuttal_matrix, lane=lane)
        prompt = f"""Predict how the opposing party will respond to:
        {our_filing}
        Known adversary patterns: {rebuttal_data}
        Include: likely objections, counter-arguments, weaknesses to exploit"""
        return self.ollama.generate(prompt)
```

**LitigationAPI methods to add:**
- `counsel_reason(question, lane)` — RAG legal reasoning
- `counsel_cross_examine(witness)` — Cross-examination generator
- `counsel_predict_opposition(filing)` — Adversarial prediction
- `counsel_summarize(text)` — Legal document summarization
- `counsel_strategy(lane)` — Case strategy advisor

### MODULE 3: FORGE — Filing Production Pipeline (in-exe)
**Purpose:** One-click court-ready filing generation from within the exe
**Wires:** irac -> narrative -> damages -> typst -> qa -> filing_assembler
**What's New:** UI workflow, integrated QA, packet tracking

```
User selects lane + filing type in command palette
    |
    v
FORGE: IRAC engine generates arguments for lane
    |
    v
FORGE: Narrative engine builds Statement of Facts
    |
    v
FORGE: Damages engine computes damages section
    |
    v
FORGE: Typst engine compiles to court-ready PDF
    |
    v
FORGE: QA engine runs 12-gate validation
    |
    v
FORGE: Filing assembler builds complete packet family
    |
    v
FORGE: Reports GO/NO-GO status with specific issues
```

**LitigationAPI methods to add:**
- `forge_generate(lane, filing_type)` — Full filing production
- `forge_qa(filing_path)` — Run QA validation
- `forge_preview(lane)` — Preview filing before generation
- `forge_packet_status()` — All packet families status

### MODULE 4: SENTINEL — Deadline & Compliance Monitor
**Purpose:** Real-time deadline tracking with visual urgency in the graph
**Wires:** deadlines table -> graph HUD -> alert system
**What's New:** Deadline nodes in graph, urgency coloring, compliance tracking

Features:
- Deadline nodes appear in graph with urgency colors (red=overdue, yellow=<7d, green=OK)
- HUD gauge shows "Days to next deadline" with filing name
- Court order compliance tracker (what orders exist, who's violating)
- Auto-compute deadlines from trigger events per MCR timeline rules
- Desktop notification when deadline <3 days

**LitigationAPI methods to add:**
- `sentinel_deadlines(days_ahead)` — Upcoming deadlines with urgency
- `sentinel_compliance()` — Court order compliance status
- `sentinel_compute_deadline(event, date)` — Compute from trigger

### MODULE 5: NEXUS FUSION — Cross-Engine Intelligence
**Purpose:** Multi-engine strategic intelligence reports
**Wires:** nexus + chimera + adversary + causal + temporal -> strategic reports
**What's New:** Multi-engine pipelines, strategic report generation

Pipeline definitions:
1. **Evidence Saturation Report:** nexus.fuse(topic) + semantic.search(topic) + 
   impeachment.search(target) + contradictions.search(entity) -> unified intelligence
2. **Adversary Profile:** adversary.profile(name) + impeachment.lookup(name) + 
   contradictions.lookup(name) + timeline.search(actor=name) -> dossier
3. **Lane Readiness:** filing_engine.status(lane) + irac.gap_analysis(lane) + 
   qa.validate(lane) + damages.get_lane(lane) -> filing readiness score
4. **Cross-Lane Intelligence:** For each lane, detect shared adversaries, shared 
   evidence, shared authorities -> strategic connections

**LitigationAPI methods to add:**
- `nexus_saturation(topic)` — Full evidence saturation report
- `nexus_adversary_profile(name)` — Deep adversary intelligence
- `nexus_lane_readiness(lane)` — Filing readiness with gaps
- `nexus_cross_lane()` — Cross-lane intelligence connections
- `nexus_strategic_brief()` — Overall strategic assessment

### MODULE 6: PERCEPTION GATEWAY — Document Intelligence
**Purpose:** Ingest new evidence directly from the exe
**Wires:** perception (Legal-BERT) -> meek234 (lane routing) -> semantic (vector store)
**What's New:** Drag-and-drop evidence ingestion, auto-classification

Pipeline:
1. User drops PDF/DOCX/TXT onto the exe window
2. Perception engine classifies document type (motion, order, affidavit, etc.)
3. Perception engine extracts legal entities (citations, parties, dates)
4. MEEK engine routes to correct lane (A-F)
5. Semantic engine generates embedding, stores in LanceDB
6. Evidence atoms extracted and stored in evidence_quotes
7. New node appears in graph with connections

**LitigationAPI methods to add:**
- `perception_classify(file_path)` — Classify a document
- `perception_extract(file_path)` — Extract entities + citations
- `perception_ingest(file_path)` — Full pipeline ingest
- `perception_batch(directory)` — Batch ingest directory

### MODULE 7: XEXAM — Cross-Examination Arsenal
**Purpose:** Generate court-ready cross-examination packages from existing data
**Wires:** impeachment_matrix (5,229) + contradiction_map (2,534) + evidence_quotes
**What's New:** Structured cross-exam generation, witness-specific packages

```
For each witness/adversary:
  1. Pull all impeachment entries (sorted by impeachment_value)
  2. Pull all contradictions (sorted by severity)
  3. Pull all evidence quotes mentioning this person
  4. Generate COMMIT-PIN-CONFRONT-EXHIBIT question sequences
  5. Map each question to specific exhibits
  6. Generate impeachment brief section
  7. Package as printable cross-exam outline
```

**LitigationAPI methods to add:**
- `xexam_package(witness)` — Full cross-examination package
- `xexam_questions(witness, count)` — Top N questions
- `xexam_contradictions(witness)` — Contradiction timeline
- `xexam_brief_section(witness)` — Court-brief impeachment section

---

## 5. IMPLEMENTATION ARCHITECTURE

### 5A. File Structure

```
D:\LitigationOS_tmp\blueprint_build\
    adversary_blueprint.py     # Launcher (MODIFY — add new API methods)
    cortex.py                  # NEW — Engine orchestrator
    counsel.py                 # NEW — Local LLM reasoning
    forge_pipeline.py          # NEW — Filing production pipeline
    sentinel.py                # NEW — Deadline monitor
    nexus_fusion.py            # NEW — Cross-engine intelligence
    perception_gateway.py      # NEW — Document intelligence
    xexam.py                   # NEW — Cross-examination arsenal
    THEMANBEARPIG.spec         # UPDATE — bundle new modules

D:\LitigationOS_tmp\
    build_manbearpig_v7.py     # UPDATE — add module nodes to graph
```

### 5B. Integration Strategy

**Phase A: CORTEX + Engine Wiring** (Foundation — must be first)
- Create cortex.py with lazy engine loading
- Add 4 new LitigationAPI methods to adversary_blueprint.py
- Test each engine access through cortex
- Estimated: ~400 lines new code

**Phase B: COUNSEL + LLM Integration** (Highest impact)
- Create counsel.py with Ollama wrapper
- RAG pipeline: hybrid search -> context assembly -> LLM -> verification
- Add 5 new LitigationAPI methods
- Test with real case questions
- Estimated: ~500 lines new code
- Requires: Ollama installed + llama3.2:3b pulled

**Phase C: FORGE + Filing Production** (Highest practical value)
- Create forge_pipeline.py connecting: IRAC -> narrative -> typst -> QA
- Add 4 new LitigationAPI methods
- Add command palette commands for filing generation
- Estimated: ~350 lines new code

**Phase D: SENTINEL + NEXUS FUSION + PERCEPTION + XEXAM** (Parallel)
- Create sentinel.py, nexus_fusion.py, perception_gateway.py, xexam.py
- Add 15+ new LitigationAPI methods
- Add command palette commands for each module
- Estimated: ~1,200 lines total

**Phase E: Graph Integration**
- Update build_manbearpig_v7.py to add module nodes
- Deadline nodes with urgency colors
- Filing pipeline visualization
- Engine health indicators in HUD
- Estimated: ~200 lines modifications

**Phase F: Rebuild EXE**
- Update THEMANBEARPIG.spec to bundle all new modules
- Rebuild with PyInstaller
- Verify all modules functional in exe
- Test on clean machine simulation (run from dist/)

### 5C. Command Palette Additions (15 new commands)

| # | Command | Module | What It Does |
|---|---------|--------|-------------|
| 1 | `/argue <claim>` | CORTEX | Generate full argument chain for a claim |
| 2 | `/brief <lane>` | CORTEX | Generate brief section for a lane |
| 3 | `/ask <question>` | COUNSEL | RAG legal reasoning with citations |
| 4 | `/cross <witness>` | XEXAM | Generate cross-examination package |
| 5 | `/predict <filing>` | COUNSEL | Predict opposition response |
| 6 | `/strategy <lane>` | COUNSEL | Case strategy advisor |
| 7 | `/forge <lane> <type>` | FORGE | Generate complete filing |
| 8 | `/qa <filing>` | FORGE | Run 12-gate QA validation |
| 9 | `/damages <lane>` | CORTEX | Compute dynamic damages |
| 10 | `/deadline` | SENTINEL | Show upcoming deadlines with urgency |
| 11 | `/comply` | SENTINEL | Court order compliance check |
| 12 | `/profile <name>` | NEXUS | Deep adversary intelligence profile |
| 13 | `/readiness <lane>` | NEXUS | Filing readiness with gaps |
| 14 | `/ingest <path>` | PERCEPTION | Classify and ingest a document |
| 15 | `/narrative <lane>` | CORTEX | Build chronological narrative |

### 5D. HUD Additions

| Gauge | Module | What It Shows |
|-------|--------|-------------|
| Deadline Timer | SENTINEL | Days to next deadline, filing name, urgency color |
| Engine Fleet | CORTEX | 27/27 engines healthy, active queries, cache status |
| Filing Pipeline | FORGE | F1-F10 status (draft/qa/ready/filed), progress bars |
| LLM Status | COUNSEL | Ollama connection, model loaded, inference time |
| Evidence Velocity | PERCEPTION | Documents ingested today, auto-classified count |

---

## 6. UNIQUE BLEEDING-EDGE CAPABILITIES

These are the ONE-OF-A-KIND features no existing legal software has:

### 6A. EVIDENCE WEATHER MAP
Real-time overlay on the graph showing "evidence density" per area:
- Hot zones (red) = strong evidence saturation
- Cold zones (blue) = evidence gaps needing attention
- Weather patterns animate to show evidence flow over time
- Clicking a cold zone triggers targeted KRAKEN hunting

### 6B. JUDICIAL PREDICTION ENGINE
Using the 1,956 judicial violations + 222 cartel intelligence entries:
- Train a pattern classifier on McNeill's ruling history
- Predict likely ruling on any motion type (based on historical pattern)
- Show "prediction confidence" in the HUD
- Generate "counter-strategy" for predicted adverse rulings

### 6C. IMPEACHMENT CHAIN REACTOR
Automated chain-building from impeachment_matrix + contradiction_map:
- For each adversary, build connected chains of contradictions
- Visualize as "chains" in the graph (sequential contradiction timeline)
- Generate court-ready impeachment briefs with pin cites
- Show "credibility score" per adversary (inverse of contradiction count)

### 6D. FILING COMPLETENESS RADAR
Circular radar chart in HUD showing 8 dimensions per filing:
- Evidence (0-100%), Authority (0-100%), IRAC (0-100%), Narrative (0-100%)
- Exhibits (0-100%), QA (0-100%), Service (0-100%), Deadline (0-100%)
- Real-time updates as filing components are generated
- Visual indicator of exactly WHERE each filing needs work

### 6E. TEMPORAL ANOMALY DETECTOR
Mine timeline_events (16,886) for suspicious timing patterns:
- Emily files PPO 2 days after recanting (Oct 2023)
- 5 ex parte orders same day as Albert's premeditation admission (Aug 2025)
- Pattern: filing -> false allegation -> ex parte order -> jail (repeat)
- Visualize as "anomaly spikes" on the timeline scrubber

### 6F. AUTHORITY CONSTELLATION MAP
Overlay on the graph showing legal authority relationships:
- Each MCR/MCL rule is a star
- Brightness = how many of our arguments cite it
- Connections = which rules support each other
- Missing stars = authority gaps needing research
- Creates a visual "legal sky" showing our authority strength

---

## 7. TECHNICAL REQUIREMENTS

### 7A. Dependencies (already installed or available)
- Python 3.12 (system) + pywebview + webview2 runtime
- Ollama 0.16.1 + llama3.2:3b (1.9 GB download, ~4GB RAM usage)
- sentence-transformers 5.3.0 (already installed)
- LanceDB 0.30.0 (already installed)
- DuckDB 1.5.1 (already installed)
- PyInstaller (already installed)
- All other deps already in pytools_venv

### 7B. Performance Targets
| Operation | Target | Current |
|-----------|--------|---------|
| Engine initialization (lazy) | <100ms | N/A (not wired) |
| IRAC argument generation | <500ms | <200ms (engine standalone) |
| Hybrid search (3-stage) | <2s | <1.5s (engine standalone) |
| LLM inference (Ollama) | <3s | ~2s (llama3.2:3b CPU) |
| Filing QA (12 gates) | <5s | <3s (engine standalone) |
| Typst PDF compilation | <2s | <1s (typst binary) |
| Full filing production | <15s | N/A (manual process) |
| Evidence ingestion | <5s/doc | <3s (perception engine) |

### 7C. EXE Size Projection
| Component | Size |
|-----------|------|
| Current exe | 22.5 MB |
| New Python modules (~2,500 lines) | ~0.5 MB |
| Ollama client library | ~0.2 MB |
| Updated HTML template | ~0.1 MB |
| **Projected total** | **~23.3 MB** |

Note: Ollama runs as a separate process (not bundled). The exe connects via localhost API.
LanceDB data stays on disk (not bundled). sentence-transformers model loaded at runtime.

---

## 8. IMPLEMENTATION TIMELINE

| Phase | What | New Code | Modules | Priority |
|-------|------|----------|---------|----------|
| **A** | CORTEX (engine wiring) | ~400 lines | cortex.py + API additions | FIRST |
| **B** | COUNSEL (LLM reasoning) | ~500 lines | counsel.py + API additions | SECOND |
| **C** | FORGE (filing pipeline) | ~350 lines | forge_pipeline.py + API | THIRD |
| **D** | SENTINEL + NEXUS + PERCEPTION + XEXAM | ~1,200 lines | 4 new files | PARALLEL |
| **E** | Graph integration | ~200 lines | build_manbearpig_v7.py mods | AFTER D |
| **F** | EXE rebuild + testing | ~100 lines | spec + test script | FINAL |
| **TOTAL** | | **~2,750 lines** | **8 new files** | |

---

## 9. SUCCESS CRITERIA

When complete, THEMANBEARPIG.exe will:

1. **THINK** — Local LLM reasons about evidence, generates arguments with citations
2. **ARGUE** — IRAC engine produces structured legal arguments per lane
3. **COMPUTE** — Dynamic damages with treble/punitive, per-day rates, court-ready text
4. **GENERATE** — One-click court-ready PDF filing packages (motion + brief + affidavit + exhibits)
5. **VALIDATE** — 12-gate QA catches every defect before filing
6. **SEARCH** — 3-stage hybrid search across 176K evidence + 168K authorities + 75K vectors
7. **CLASSIFY** — Legal-BERT classifies any document, extracts entities and citations
8. **PREDICT** — Anticipate opposing counsel's response using rebuttal matrix
9. **CROSS-EXAMINE** — Generate witness-specific cross-examination packages
10. **MONITOR** — Real-time deadlines, compliance tracking, urgency alerts
11. **VISUALIZE** — All of the above displayed in the 20-layer WebGL2 graph
12. **HUNT** — KRAKEN continues autonomous evidence discovery

**This is not just a visualization. This is the BRAIN.**
**No law firm has anything like this. No legal tech company has built this.**
**This is THEMANBEARPIG — the complete litigation operating system.**

---

## 10. RISK MITIGATION

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Ollama not installed | COUNSEL module fails | Graceful degradation — all other modules work without LLM |
| Large model RAM usage | System slowdown | llama3.2:3b uses 4GB — fits in 24GB with room to spare |
| PyInstaller bundle size | Exe too large | Only bundle Python code, engines loaded at runtime from DB path |
| cp1252 encoding crashes | Exe crashes on emoji | All new code uses ASCII-only output + `_safe()` wrapper |
| Engine import failures | Module unavailable | Each engine lazily loaded with try/except, graceful fallback |
| DB locked | Concurrent access issues | WAL mode + busy_timeout=60000 + connection pooling |

---

*Generated by APEX analysis of existing THEMANBEARPIG.exe architecture.*
*27+ engines already built. 395,000+ DB rows ready. 75K vectors indexed.*
*This plan wires everything together into the world's first litigation brain.*
