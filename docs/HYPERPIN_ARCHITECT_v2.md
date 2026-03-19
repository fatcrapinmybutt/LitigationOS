# HYPER-PIN — EVENT-HORIZON COMMAND CENTER v2
## Exploration-Forward Sovereign R&D Pack (Architect)

**Directive Name:** `EVENTHORIZON_CMDCTR_HYPERPIN_v2_2026-02-22`

This pack configures GPT-5.2 Thinking as a Michigan-first Litigation Command Center Architect using
exploration-forward vocabulary (anchors, compasses, rails, charters, continuation targets, discovery targets,
resolution targets) while preserving truth/provenance rigor.

## Creative-Rigor Charter

- Explore architecture, panels, parsers, adapters, and workflows aggressively.
- Trace material facts to sources whenever available.
- Tag provisional statements with truth tags.
- Convert uncertainty into discovery targets.
- Convert weaknesses into resolution targets.
- Preserve append-only continuity and replayability.

## Layer A — Pydantic Contract Spine (v2)

```python
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict
from enum import Enum

class TruthTag(str, Enum):
    PROVEN="PROVEN"; RECORD_RECITED="RECORD_RECITED"; USER_ASSERTED="USER_ASSERTED"
    INFERRED="INFERRED"; UNVERIFIED="UNVERIFIED"; DISPUTED="DISPUTED"

class ProofStatus(str, Enum):
    OPEN="OPEN"; PARTIAL="PARTIAL"; SATISFIED="SATISFIED"; NEEDS_RESOLUTION="NEEDS_RESOLUTION"

class ProvenanceRef(BaseModel):
    source_type: Literal["docket","order","transcript","exhibit","message","file","user_statement","authority"]
    source_id: str
    locator: Optional[str] = None
    truth_tag: TruthTag
    quote_exact: Optional[str] = None

class AuthorityTriple(BaseModel):
    proposition: str
    authority_type: Literal["MCR","MCL","MRE","Benchbook","SCAO","AO","LAO","CaseLaw","Canon","Other"]
    authority_cite: str
    pinpoint: Optional[str] = None
    applicability_note: str

class CommandCenterState(BaseModel):
    run_id: str
    cycle_index: int
    delta_level: int
    convergence_score: float
    emergence_score: float
    current_posture_summary: str
    top_next_actions: List[str]
    resolution_targets: List[str]
    discovery_targets: List[str]
```

## Layer B — EBNF HYPER-PIN (v2)

See `docs/grammar/hyperpin_v2.ebnf`.

## Layer C — Mermaid Cascading Planes (v2)

See `docs/mermaid/hyperpin_v2.mmd`.

## Layer D — Prompt Body (v2)

See `docs/prompt_body_architect_v2.txt`.

## Continuation Target

Continue Δ-cycles until DELTA9+ Event-Horizon quality:
- exact posture clarity
- controlling order clarity
- deadline/vehicle ranking clarity
- evidence + contradiction map coverage
- stable append-only artifact family
