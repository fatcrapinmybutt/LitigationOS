# THEMANBEARPIG v12.0 — DEEP DIVE INTERFACE BRAINSTORM
## Apex-Tier Interactive Intelligence Upgrades

**Current State:** Node click → small sidebar panel with label/layer/threat/3 quotes.  
**Target State:** Node click → full immersive experience with multi-tab drill-down, auto-derived legal theories from graph connections, and multi-page navigation.

---

## MODULE 1: NODE DEEP-DIVE MODAL (the "Dossier Drawer")

**Concept:** Click any node → full-screen slide-in modal with 6 tabbed sub-pages. Each tab pulls live data from all 5 engines (CORTEX, CHRONOS, ORACLE, PROMETHEUS, ATHENA). The modal IS the dossier.

### Tab A: PROFILE
- Full identity card (name, role, threat score, connection count)
- **Auto-classification**: ADVERSARY / ALLY / NEUTRAL / INSTITUTION / JUDICIAL
- Key stats: evidence count, impeachment items, contradiction count
- "Credibility Gauge" — animated ring showing credibility score (0-100)
- Top 5 most damaging quotes with source citations
- Photo/avatar placeholder (for future media integration)

### Tab B: CONNECTIONS (interactive sub-graph)
- **Mini-graph** centered on the selected node showing ALL direct connections
- Each connection link is CLICKABLE → opens THAT node's modal (recursive drill-down)
- Color-coded by relationship type: LEGAL, PERSONAL, PROFESSIONAL, FINANCIAL, CONSPIRATORIAL
- **Edge labels** show the nature of the relationship
- "Expand" button reveals 2nd-degree connections (friends-of-friends)
- **Path Finder**: Select any other node → highlights shortest path + derives legal theory

### Tab C: LEGAL (auto-derived causes of action)
- **THIS IS THE KILLER FEATURE** — the system walks the graph FROM this node and automatically derives every applicable cause of action:
  - Node type = JUDICIAL + connections to ADVERSARY → MCR 2.003 Disqualification
  - Node type = ADVERSARY + connections showing FALSE_ALLEGATION pattern → Malicious Prosecution, IIED, Abuse of Process  
  - Node type = JUDICIAL + EX_PARTE link + NO_NOTICE → Due Process (Mathews v Eldridge)
  - Node type = ADVERSARY + PPO_WEAPONIZATION + CUSTODY_INTERFERENCE → MCL 722.23(j)
  - Multiple adversaries connected through CONSPIRACY links → 42 USC 1983 conspiracy
- Each derived cause of action shows:
  - Legal theory name + elements
  - Which connections satisfy which elements (highlighted on mini-graph)
  - Citation chain (ATHENA-powered)
  - Filing readiness % for this specific theory against this node
  - "Generate Filing" button → feeds into PROMETHEUS

### Tab D: TIMELINE (node-centric chronology)
- CHRONOS-powered timeline view filtered to this entity
- Vertical scrollable timeline with event cards
- Color-coded by severity (green→yellow→orange→red)
- Each event expandable to show source document + quote
- "Escalation Trend" sparkline showing severity over time
- Zoom controls: all time / last year / last 6 months / last 30 days

### Tab E: EVIDENCE VAULT
- Scrollable evidence gallery filtered to this entity
- Each card shows: quote excerpt, source file, page, lane, category, relevance score
- Sort by: relevance / date / severity / impeachment value
- Filter by: lane / category / type
- "Export" button → generates exhibit package for this entity
- Full-text search within this entity's evidence

### Tab F: WEAPONS ARRAY
- PROMETHEUS-powered arsenal specific to this entity
- IRAC analyses available
- Cross-examination scripts (top 10 questions)
- Rebuttal arguments pre-built
- Authority chains relevant to this entity
- "Strike Plan" summary with readiness score

---

## MODULE 2: RELATIONSHIP INTELLIGENCE ENGINE ("CrossWire")

**Concept:** Every LINK in the graph is not just a visual line — it's a computed legal relationship. The system automatically derives causes of action from connection PATTERNS.

### 2A: Link Deep-Dive
- Click any LINE between two nodes → opens a "Relationship Card"
- Shows: what connects these two entities, evidence supporting the connection, legal implications
- "This relationship supports N causes of action" with list

### 2B: Pattern Recognition (graph-walking inference)

| Pattern Detected | Derived Cause of Action | Authority |
|---|---|---|
| Judge → Adversary (PERSONAL) | Disqualification / Bias | MCR 2.003(C)(1)(b) |
| Judge → Ex Parte Orders → No Notice | Due Process Violation | 14th Amend; Mathews v Eldridge |
| Adversary → False Allegations → Police Reports → No Arrest | Malicious Prosecution | IIED elements |
| Multiple Adversaries → Coordinated Actions → Same Timeline | Civil Conspiracy | 42 USC 1983 |
| Judge → Attorney → Former Partners | Structural Conflict | Canon 2; MCR 2.003 |
| Adversary → Custody Interference → Withholding | Parental Alienation | MCL 722.23(j) |
| Judge → Contempt → Jail → No Due Process | False Imprisonment | 42 USC 1983 |
| Institution → Bias → Pattern of Favorable Treatment | Institutional Capture | Monell liability |

### 2C: Cause of Action Auto-Generator
- Walks the ENTIRE graph and outputs a ranked list of every derivable cause of action
- Each cause of action links back to the specific nodes + edges that establish it
- Strength score based on: evidence density, authority coverage, impeachment support
- "Filing Priority Matrix" derived from graph topology, not just DB queries

### 2D: Conspiracy Path Mapper
- Given any 2+ adversary nodes, find ALL paths connecting them
- Each path = potential conspiracy chain
- Auto-generates: timeline of coordinated actions, shared patterns, mutual benefit analysis
- Visualized as highlighted path on the main graph (glowing animated line)

---

## MODULE 3: MULTI-PAGE NAVIGATION ("War Room")

**Concept:** The graph is HOME, but there are 5 more "rooms" accessible via navigation bar or keyboard shortcuts.

### Page 1: GRAPH (current — enhanced with Modules 1+2)
- The existing 20-layer PixiJS visualization
- Now with deep-dive modals and relationship intelligence
- Keyboard: `1` or `Home`

### Page 2: WAR ROOM (filing command center)
- Kanban board: DRAFT → QA → READY → FILED → DOCKETED
- Each filing card shows: EGCP score, deadline, blocker count
- Click card → full filing package detail
- "Critical Path" view showing filing dependencies
- Live deadline countdown timers with color-coded urgency
- Keyboard: `2`

### Page 3: DOSSIER ROOM (adversary grid)
- Card grid of ALL adversaries with:
  - Threat score gauge
  - Evidence count badge
  - Impeachment count badge
  - Credibility score
  - Mini sparkline of activity over time
- Click card → opens Module 1 deep-dive modal
- Sort/filter by: threat / evidence / lane
- Keyboard: `3`

### Page 4: TIMELINE THEATER (full chronology)
- Horizontal scrollable mega-timeline spanning 2023-2026
- Swimlanes per actor (Emily, McNeill, Albert, FOC, etc.)
- Event density heatmap (color intensity = event frequency)
- Click any event → source document + evidence card
- Overlay: court orders, hearings, jailings, separation period
- Keyboard: `4`

### Page 5: AUTHORITY MAP (citation universe)
- Force-directed graph of just citations and legal authorities
- Cluster by: MCR / MCL / Case Law / SCOTUS / Constitutional
- Size = citation frequency, Color = authority type
- Click citation → full text + supporting chain + which filings use it
- "Coverage Heat" — which areas of law are well-covered vs gaps
- Keyboard: `5`

### Page 6: SITUATION ROOM (case health dashboard)
- Real-time dashboard with:
  - Separation day counter (prominently)
  - EGCP scores per lane (gauges)
  - Deadline tickers
  - Recent events feed
  - Threat level indicator
  - Filing pipeline progress bars
  - Evidence growth chart
  - Gap analysis summary
- Auto-refreshes from DB every 30 seconds
- Keyboard: `6`

---

## MODULE 4: SMART INFERENCE LAYER ("NEXUS")

**Concept:** The system doesn't just display data — it THINKS. Auto-generated insights that surface without being asked.

### 4A: Pattern Alerts
- "New pattern detected: McNeill issued 3 ex parte orders within 48 hours of Emily filing motions — suggests coordinated timing"
- Alert badge on affected nodes
- Clicking alert → shows full pattern analysis with evidence chain

### 4B: Gap Detection
- "Emily Watson has 47 impeachment items but ZERO cross-examination scripts — generate now?"
- Highlights under-weaponized adversaries
- Suggests which engines to run for maximum impact

### 4C: Relationship Inference
- "Based on professional history + geographic proximity + communication patterns, Berry-McNeill connection confidence: 94%"
- Suggests new connections that aren't explicitly in the graph but are strongly implied by evidence

### 4D: Filing Recommendations
- "Your evidence against McNeill satisfies 4/5 elements for JTC complaint — missing element: 'pattern of persistent misconduct over 12+ months' — you have 18 months of data. RECOMMENDATION: File JTC now."
- Surfaces the highest-impact unfiled actions

---

## MODULE 5: EXPORT & PRESENTATION ENGINE

### 5A: Node-to-Filing Pipeline
- From any node's LEGAL tab → "Generate Filing" → walks through PROMETHEUS/ATHENA to produce:
  - IRAC analysis
  - Authority brief
  - Exhibit index
  - Cross-examination script
  - All packaged for download

### 5B: Relationship-to-Brief
- Select a PATTERN (conspiracy chain, retaliation sequence, etc.)
- Auto-generates a legal brief arguing that pattern, with:
  - Statement of Facts (CHRONOS timeline)
  - Legal Analysis (ATHENA citations)
  - Evidence Support (PROMETHEUS exhibit index)
  - Professional Standards (ATHENA canons/ethics)

### 5C: Presentation Mode
- "Jury View" — simplified, narrative-driven walkthrough
- "Judicial View" — authority-heavy, IRAC-structured
- "JTC View" — misconduct-focused, violation-centric
- Each view auto-selects the most relevant nodes/connections to highlight

---

## TECHNICAL APPROACH

All of this is achievable because:
1. **5 engines already built** (CORTEX, CHRONOS, ORACLE, PROMETHEUS, ATHENA) — they provide ALL the data
2. **pywebview API bridge** already works — just need more methods + JS UI
3. **PixiJS + D3 already handle** graph rendering — modals/pages are pure HTML/CSS overlay
4. **176K evidence quotes + 168K authority chains** in DB — the data is there

### Implementation Phases:
- **Phase A**: Module 1 (Deep-Dive Modal) — the foundation everything else builds on
- **Phase B**: Module 2 (CrossWire relationship intelligence) — the brain
- **Phase C**: Module 3 (Multi-Page Navigation) — the structure  
- **Phase D**: Module 4 (NEXUS inference) — the intelligence
- **Phase E**: Module 5 (Export/Presentation) — the output

### New API Methods Needed (~25):
- `node_full_profile(label)` — aggregated profile from all 5 engines
- `node_connections_graph(label, depth)` — sub-graph extraction
- `derive_causes_of_action(node_id)` — graph-walking legal inference
- `relationship_detail(node_a, node_b)` — link intelligence
- `conspiracy_paths(node_ids)` — multi-node path finding
- `pattern_alerts()` — auto-detected patterns
- `gap_recommendations()` — under-weaponized entities
- `filing_kanban()` — filing pipeline for War Room
- `adversary_cards()` — grid data for Dossier Room
- `full_timeline(actor, date_range)` — Timeline Theater data
- `citation_graph()` — Authority Map data
- `situation_dashboard()` — case health metrics
- etc.

### Estimated Complexity:
- Module 1: ~400 lines JS + ~150 lines Python API
- Module 2: ~300 lines JS + ~200 lines Python (graph-walking engine)
- Module 3: ~500 lines JS (page routing + layouts)
- Module 4: ~200 lines Python (inference engine)
- Module 5: ~300 lines JS + ~150 lines Python

**Total: ~1,500 lines JS + ~700 lines Python = ~2,200 lines net new code**
