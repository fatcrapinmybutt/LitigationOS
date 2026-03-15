# LitigationOS

**LitigationOS** is a litigation intelligence system for Michigan family law (*Pigors v. Watson*).
It combines a multi-agent evidence pipeline, a local-first AI engine, an MCP server, and a desktop
application to process evidence across multiple drives into court-ready filings.

---

## Repository Layout

```
agents/               Core agent pipeline (evidence → chronology → filing)
  agent_base.py       Shared data models and utility helpers
  evidence_agent.py   Scans directories and builds EvidenceAtoms
  chronology_agent.py Derives ChronoEvents from EvidenceAtoms
  filing_agent.py     Assembles packet shells from atoms and events
  orchestrator.py     End-to-end deterministic pipeline runner
  feedback_agent.py   Records outcome signals for strategy calibration
  authority_agent.py  Michigan authority node generation helpers

core/
  script_vault.py     Persistent script catalog (SQLite-backed, versioned)

00_SYSTEM/
  mcp_server/         MCP server with FTS5 full-text search
  engines/            Production pipeline engines
  local_model/        MANBEARPIG inference engine (local-only)
  pipeline/           16-phase data pipeline

01_FILINGS/           Court-ready filing packages (Markdown → PDF)
docs/                 Legal analysis and strategy documents
08_SCRIPTS/vault/     Versioned utility scripts managed by ScriptVault
```

---

## Agent Pipeline

The core pipeline runs in four deterministic stages:

```
[Root directory]
      │
      ▼
EvidenceAgent           Scans for .pdf / .docx / .md / .txt / .jpg / .png
      │  EvidenceAtom[]
      ▼
ChronologyAgent         Infers occurrence dates from filenames; builds timeline
      │  ChronoEvent[]
      ▼
FilingAgent             Produces an Artifact packet shell (exhibit matrix + timeline)
      │  packet_shell.json
      ▼
Orchestrator            Writes outputs to out_dir/<timestamp>/, emits manifest.json
```

### Running the pipeline

```python
from pathlib import Path
from agents.orchestrator import run

run_dir = run(
    case_id="2024-001507-DC",
    root=Path("/evidence/custody"),
    out_dir=Path("/output"),
)
print("Outputs written to:", run_dir)
```

Each run produces:

| File | Contents |
|---|---|
| `evidence_atoms.jsonl` | One JSON object per scanned file |
| `chrono_events.jsonl` | Timeline events sorted by occurrence date |
| `packet_shell.json` | Exhibit matrix + timeline summary |
| `manifest.json` | Run metadata and counts |
| `run_ledger.jsonl` | Append-only audit log |

---

## Key Data Models

### `EvidenceAtom`

Represents a single source file at ingestion time.

```python
from agents.agent_base import EvidenceAtom, uuid_str, sha256_file, guess_media_type
from pathlib import Path

p = Path("/evidence/order_2024_08_08.pdf")
atom = EvidenceAtom(
    atom_id=uuid_str(),
    case_id="2024-001507-DC",
    meek_track="MEEK2",          # custody lane
    atom_type="Document",
    source_path=str(p),
    source_media_type=guess_media_type(p),   # "application/pdf"
    recorded_time="2024-08-08T12:00:00+00:00",
    sha256=sha256_file(p),
    notes="Ex parte order stripping parenting time",
)
```

### `ChronoEvent`

A timeline event derived from an `EvidenceAtom`.

```python
from agents.agent_base import ChronoEvent, uuid_str

ev = ChronoEvent(
    event_id=uuid_str(),
    case_id="2024-001507-DC",
    meek_track="MEEK3",          # PPO/contempt lane
    event_type="Hearing",
    recorded_time="2024-11-15T12:00:00+00:00",
    occurrence_time="2024-11-15T09:00:00+00:00",
    title="show_cause_hearing_2024_11_15.pdf",
    description="Derived from EvidenceAtom abc-123",
    linked_atoms=["abc-123"],
)
```

---

## Case Lanes (MEEK signals)

| Track | Subject |
|---|---|
| `MEEK1` | Housing / Shady Oaks (2025-002760-CZ) |
| `MEEK2` | Custody (2024-001507-DC) |
| `MEEK3` | PPO / Contempt (2023-5907-PP) |
| `MEEK4` | Judicial Conduct / JTC |
| `MEEK5` | Appellate / COA (366810) |

---

## ScriptVault

All utility scripts are catalogued in `script_vault.db`.  Before writing a new script, search
for an existing one:

```python
from core.script_vault import ScriptVault

vault = ScriptVault()

# Find before creating
results = vault.find("evidence mining")
if results:
    script = vault.load(results[0]["script_id"])
    # Upgrade in place
    vault.upgrade(script["script_id"], new_code, "Added Watson family patterns")
else:
    vault.register(
        "mine_evidence.py",
        code=open("mine_evidence.py").read(),
        category="mining",
        description="Mines harvest texts for actionable evidence",
        tags=["evidence", "mining", "torts"],
    )
```

---

## Requirements

- Python ≥ 3.10
- Standard library only for the agent pipeline (`pathlib`, `hashlib`, `json`, `mimetypes`)
- `sqlite3` (stdlib) for ScriptVault and the MCP server DB layer

---

## Database

The central database is `litigation_context.db` (SQLite, WAL mode).  Always connect with:

```python
import sqlite3

conn = sqlite3.connect("litigation_context.db")
conn.execute("PRAGMA busy_timeout = 60000")
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA cache_size = -32000")
conn.execute("PRAGMA synchronous = NORMAL")
```

Or use the managed context manager from the MCP server DB module:

```python
import sys, os
# Add the MCP server package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "00_SYSTEM", "mcp_server"))
from litigation_context_mcp.db import get_connection, get_stats

with get_connection() as conn:
    stats = get_stats(conn)
```
