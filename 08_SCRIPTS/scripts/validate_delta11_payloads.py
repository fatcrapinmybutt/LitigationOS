from __future__ import annotations
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schemas.contracts.delta11_order_evidence_lineage_contracts import (
    ServiceProof,
    OrderSupersessionServiceGraph,
    EvidenceAtom,
    ExhibitMatrixRow,
    LineageProvenanceIndex,
)

def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def main():
    service = _load("data/service_proofs.json")["service_proofs"]
    [ServiceProof.model_validate(x) for x in service]

    OrderSupersessionServiceGraph.model_validate(_load("data/order_supersession_service_graph.json"))

    atoms = _load("data/evidence_atoms.json")["atoms"]
    [EvidenceAtom.model_validate(x) for x in atoms]

    rows = _load("data/exhibit_matrix.json")["rows"]
    [ExhibitMatrixRow.model_validate(x) for x in rows]

    LineageProvenanceIndex.model_validate(_load("data/lineage_provenance_index.json"))

    print({
        "service_proofs": len(service),
        "evidence_atoms": len(atoms),
        "exhibit_matrix_rows": len(rows),
        "status": "OK"
    })

if __name__ == "__main__":
    main()
