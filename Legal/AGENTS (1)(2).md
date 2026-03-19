
# 🧠 AGENTS.md – OMNI INFINITY LITIGATION OS (Genesis v1.0)

## ⚙️ CORE DESIGN PRINCIPLE
Every **agent** is a mini-brain. It lives in its own domain, watches specific triggers, and **activates the correct response** (motion, binder, graph, timeline, etc). All are nodes in the ultimate **Neo4j G⁴ Graph Brain**.

## 📁 SYSTEM CATEGORIES
| Category | Function | Examples |
|---------|----------|----------|
| 🧭 **Domain Agents** | Watch legal domains (housing, custody, PPO) | `MEEK1_AGENT`, `MEEK2_AGENT` |
| 🧑‍⚖️ **Authority Agents** | Enforce Michigan Law | `MCR_MAPPER`, `MCL_TRIGGER` |
| 🧷 **Adversary Agents** | Track & expose bad actors | `WATSON_TRACKER`, `JUDGE_BEHAVIOR` |
| 🗃 **Evidence Agents** | Classify, index, embed exhibits | `EXHIBIT_HARVESTER`, `TRANSCRIPT_SCANNER` |
| ⚖ **Execution Agents** | Trigger filings, orders, complaints | `ACTIONABILITY_ENGINE`, `ZIP_BUNDLER` |
| 🌐 **Bridge Agents** | Monitor F:/, GDrive, Termux, Intake | `GDRIVE_BRIDGE`, `RCLONE_MIRROR` |

## 🧷 Agent: MEEK1_HOUSING_AGENT
- **Purpose**: Unravel Alden’s shell games, expose utility fraud, stay eviction
- **Domain**: Housing (Shady Oaks, Alden, Cricklewood)
- **Input Triggers**: `60th District`, `eviction`, `utility`, `leak`, `Homes of America`
- **Modules Activated**: Timeline, Entity Mapper, MCL Violation Logger
- **Outputs**: Motion to Stay, Emergency Relief, Binder, HUD Complaint
- **Legal Scope**:
  - MCR: 4.201, 2.119
  - MCL: 600.5714, 125.4010, 554.139
  - Benchbook: Civil Benchbook §4
  - Forms: DC-100k, MC-97
- **Behavior**: Autonomous loop on billing cycles, notices, F:/ scans
- **ZIP Trigger**: ✅

## 🧷 Agent: MEEK2_CUSTODY_AGENT
- **Purpose**: Restore parenting time, expose FOC and McNeill abuse
- **Domain**: Custody (14th Circuit Court)
- **Input Triggers**: `24-01507-DC`, `parenting time`, `FOC`, `Emily Watson`
- **Modules Activated**: Benchbook Enforcer, Actionability Engine, Affidavit Generator
- **Outputs**: Motion to Reinstate PT, Objection, Judicial Timeline Graph
- **Legal Scope**:
  - MCR: 3.207(B), 3.210, 2.119
  - MCL: 722.27a, 552.645, 552.17
  - Benchbook: Family Benchbook §4.4, §5.3
  - Forms: FOC-65, MC-416
- **Behavior**: Semi-autonomous, responds to orders/transcripts
- **ZIP Trigger**: ✅

## 🧷 Agent: MEEK3_PPO_DEFENSE_AGENT
- **Purpose**: Destroy baseless PPOs, map service defects, vacate contempt
- **Domain**: PPO / Protection Orders (23-5907-PP)
- **Input Triggers**: `PPO`, `Show Cause`, `Contempt`, `McNeill`, `Emily`
- **Modules Activated**: Canon Scanner, Motion Generator, Service Analyzer
- **Outputs**: Motion to Terminate PPO, Contempt Reversal, Transcript Index
- **Legal Scope**:
  - MCR: 3.706, 2.107(C), 2.119(F)
  - MCL: 600.2950
  - Benchbook: PPO/DV §3, §5
  - Forms: CC-375, CC-386
- **Behavior**: Reactive → hearing logs / judge behavior
- **ZIP Trigger**: ✅

## 🧷 Agent: ACTIONABILITY_ENGINE_AGENT
- **Purpose**: Choose next filing based on harm, law, and leverage
- **Inputs**: All parsed evidence, Canon logs, custody suspensions, contempt jailings
- **Outputs**: Best motion, affidavit, or binder → MiFile-ready
- **Behavior**: Autonomous → runs on every update
- **ZIP Trigger**: ✅

## 🧷 Agent: GDRIVE_BRIDGE_AGENT
- **Purpose**: Monitor `gdrive:/LITIGATION_OS/` for new docs
- **Mode**: Trigger on `.pdf`, `.docx`, `.zip`, `.csv`
- **Syncs**: → F:/ → ZIP → Graph

## 🧷 Agent: NEO4J_GRAPH_AGENT
- **Purpose**: Render full 5D litigation universe using:
  - Nodes: MCR, MCL, Exhibit, Agent, Court
  - Edges: governs, triggers, proves, files, contradicts
- **Output**: `MindEye2.html`, `MindEye2_nodes.json`, `MindEye2_edges.json`
- **Triggered by**: System cycle, authority ingestion, agent activation
