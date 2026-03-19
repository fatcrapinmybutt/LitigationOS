from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def _read_json(name: str, default):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))

def build_evidence_coverage() -> dict:
    matrix = _read_json("exhibit_matrix.json", {"rows": []})
    atoms_payload = _read_json("evidence_atoms.json", {"atoms": []})
    atoms = {a.get("atom_id"): a for a in atoms_payload.get("atoms", [])}

    rows_out = []
    lane_rollup = defaultdict(lambda: {"required": 0.0, "found": 0.0, "rows": 0, "missing_atoms": []})
    vehicle_scores = defaultdict(list)

    for row in matrix.get("rows", []):
        required_ids = row.get("required_atoms", [])
        required_weight = 0.0
        found_weight = 0.0
        missing = []
        supporting = []
        for aid in required_ids:
            atom = atoms.get(aid)
            weight = float((atom or {}).get("coverage_weight", 1.0))
            required_weight += weight
            if atom:
                found_weight += weight
                supporting.append({
                    "atom_id": aid,
                    "label": atom.get("label"),
                    "truth_tag": atom.get("truth_tag"),
                    "pinpoint": atom.get("pinpoint"),
                    "linked_exhibit_count": len(atom.get("linked_exhibits", []))
                })
            else:
                missing.append(aid)
        score = round(found_weight / required_weight, 4) if required_weight else 0.0
        status_band = "GREEN" if score >= 0.85 else ("AMBER" if score >= 0.55 else "RED")
        row_out = {
            "matrix_id": row.get("matrix_id"),
            "lane": row.get("lane"),
            "title": row.get("title"),
            "vehicle_ids": row.get("vehicle_ids", []),
            "required_atom_count": len(required_ids),
            "found_atom_count": len(supporting),
            "required_weight": round(required_weight, 2),
            "found_weight": round(found_weight, 2),
            "coverage_score": score,
            "status_band": status_band,
            "missing_atom_ids": missing,
            "supporting_atoms": supporting,
            "target_findings": row.get("target_findings", []),
            "resolution_target": row.get("resolution_target")
        }
        rows_out.append(row_out)
        lr = lane_rollup[row.get("lane") or "UNLANED"]
        lr["required"] += required_weight
        lr["found"] += found_weight
        lr["rows"] += 1
        lr["missing_atoms"].extend(missing)
        for vid in row.get("vehicle_ids", []):
            vehicle_scores[vid].append(score)

    lane_summary = []
    for lane, vals in sorted(lane_rollup.items()):
        score = round(vals["found"] / vals["required"], 4) if vals["required"] else 0.0
        lane_summary.append({
            "lane": lane,
            "rows": vals["rows"],
            "coverage_score": score,
            "required_weight": round(vals["required"], 2),
            "found_weight": round(vals["found"], 2),
            "status_band": "GREEN" if score >= 0.85 else ("AMBER" if score >= 0.55 else "RED"),
            "missing_atom_ids": sorted(set(vals["missing_atoms"]))
        })

    vehicle_summary = [{"vehicle_id": vid, "coverage_score": round(sum(scores)/len(scores),4), "sample_count": len(scores)}
                      for vid, scores in sorted(vehicle_scores.items())]

    overall_req = sum(x["required_weight"] for x in rows_out)
    overall_found = sum(x["found_weight"] for x in rows_out)
    overall = {
        "matrix_row_count": len(rows_out),
        "atom_count_available": len(atoms),
        "coverage_score": round(overall_found / overall_req, 4) if overall_req else 0.0,
        "required_weight": round(overall_req, 2),
        "found_weight": round(overall_found, 2)
    }

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "overall": overall,
        "lane_summary": lane_summary,
        "vehicle_summary": vehicle_summary,
        "rows": rows_out
    }
    (DATA / "evidence_coverage.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps(build_evidence_coverage(), indent=2))
