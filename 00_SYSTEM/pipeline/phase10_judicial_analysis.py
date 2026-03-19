"""
OMEGA Phase 10: Judicial Analysis Engine
Cross-reference extracted evidence against Judge McNeill's documented orders.
Score violations, map to Canon/benchbook sections, build JTC exhibits.
"""
import json
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    SCANS_ROOT, MASTER_ROOT, MEEK_SIGNALS, CANON_PATTERN,
    VIOLATION_KEYWORDS, PERSON_NAMES,
    get_cyclepack_dir, report_progress, CYCLE_TS, POSTURE_TAGS,
)
from safety import write_phase_checkpoint, is_phase_done

# ── Canon Violation Mapping ─────────────────────────────────────────
CANON_VIOLATIONS = {
    "3(A)(3)": {
        "text": "Requires judges to be faithful to the law regardless of partisan interests",
        "keywords": ["bias", "ex parte", "predetermined", "impartial", "fairness"],
    },
    "3(B)(2)": {
        "text": "Judge shall hear and decide matters unless disqualified",
        "keywords": ["refuse", "hearing", "denied hearing", "no hearing", "summary"],
    },
    "3(C)(1)": {
        "text": "Judge shall disqualify in proceeding where impartiality might be questioned",
        "keywords": ["disqualif", "recuse", "bias", "prejudice", "impartial"],
    },
}

# ── Benchbook Reference Mapping ─────────────────────────────────────
BENCHBOOK_SECTIONS = {
    "DV_5_4": {
        "section": "DV §5.4",
        "title": "Domestic Violence — Evidence Standards",
        "keywords": ["domestic violence", "DV", "PPO", "protection order", "abuse",
                      "MCL 600.2950", "MCR 3.706", "MCR 3.707"],
    },
    "BI_4_2": {
        "section": "Best Interest §4.2",
        "title": "Best Interest — Factor Analysis",
        "keywords": ["best interest", "factor", "custody", "MCL 722.23",
                      "parenting time", "child welfare"],
    },
    "BI_4_6": {
        "section": "Best Interest §4.6",
        "title": "Best Interest — Domestic Violence Considerations",
        "keywords": ["best interest", "domestic violence", "factor j",
                      "safety", "MCL 722.23", "reasonable cause"],
    },
}

# ── MCR 2.003(C) Disqualification Grounds ───────────────────────────
MCR_2003C_GROUNDS = {
    "personal_bias": {
        "label": "Personal bias or prejudice",
        "subsection": "MCR 2.003(C)(1)(a)",
        "keywords": ["bias", "prejudice", "animosity", "hostility", "personal"],
    },
    "personal_knowledge": {
        "label": "Personal knowledge of disputed facts",
        "subsection": "MCR 2.003(C)(1)(b)",
        "keywords": ["personal knowledge", "ex parte", "outside information"],
    },
    "ex_parte_communication": {
        "label": "Ex parte communication about case merits",
        "subsection": "MCR 2.003(C)(1)(c)",
        "keywords": ["ex parte", "communication", "unauthorized contact"],
    },
    "expressed_opinion": {
        "label": "Publicly expressed opinion on merits",
        "subsection": "MCR 2.003(C)(1)(d)",
        "keywords": ["predetermined", "opinion", "prejudge"],
    },
    "economic_interest": {
        "label": "Financial or economic interest",
        "subsection": "MCR 2.003(C)(1)(e)",
        "keywords": ["financial", "economic", "interest", "benefit"],
    },
}

# ── Posture Weights ──────────────────────────────────────────────────
POSTURE_WEIGHT = {
    "SWORN_FACT": 3.0,
    "RECORD_FACT": 2.5,
    "EVIDENCE_FACT": 2.0,
    "ALLEGATION": 1.0,
    "INFERENCE": 0.5,
}


def _load_atom_store(cycle_dir: Path, store_name: str) -> list[dict]:
    """Load atoms from JSONL files in cycle_dir or cycle_dir/atoms/."""
    atoms: list[dict] = []
    fname = f"{store_name}.jsonl"
    for candidate in (cycle_dir / fname, cycle_dir / "atoms" / fname):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line:
                    try:
                        atoms.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            break
    return atoms


def _score_incident(severity: int, evidence_density: float, date_str: str | None) -> float:
    """Score = severity(1-10) × evidence_density × temporal_recency."""
    severity = max(1, min(10, severity))
    recency = 1.0
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            days_ago = (datetime.now() - dt.replace(tzinfo=None)).days
            recency = max(0.1, 1.0 / (1.0 + math.log1p(max(0, days_ago) / 30.0)))
        except (ValueError, TypeError):
            pass
    return round(severity * evidence_density * recency, 3)


def _match_canon_violations(text: str) -> list[str]:
    """Return list of Canon sections that match text keywords."""
    text_lower = text.lower()
    matches = []
    for canon_id, info in CANON_VIOLATIONS.items():
        if any(kw in text_lower for kw in info["keywords"]):
            matches.append(canon_id)
    return matches


def _match_benchbook_sections(text: str) -> list[dict]:
    """Return benchbook sections matching text."""
    text_lower = text.lower()
    matches = []
    for key, info in BENCHBOOK_SECTIONS.items():
        if any(kw.lower() in text_lower for kw in info["keywords"]):
            matches.append({"id": key, "section": info["section"], "title": info["title"]})
    return matches


def _match_disqualification_grounds(text: str) -> list[dict]:
    """Return MCR 2.003(C) grounds matching text."""
    text_lower = text.lower()
    matches = []
    for key, info in MCR_2003C_GROUNDS.items():
        if any(kw in text_lower for kw in info["keywords"]):
            matches.append({
                "ground": key,
                "label": info["label"],
                "subsection": info["subsection"],
            })
    return matches


def _classify_severity(text: str) -> int:
    """Heuristic severity 1-10 based on violation keyword density."""
    text_lower = text.lower()
    score = 3  # baseline
    high_severity = ["fraud", "perjury", "fabricat", "obstruction", "coercion"]
    medium_severity = ["ex parte", "bias", "contempt", "misconduct", "suppress"]
    for kw in high_severity:
        if kw in text_lower:
            score += 2
    for kw in medium_severity:
        if kw in text_lower:
            score += 1
    return min(10, score)


def _is_mcneill_related(atom: dict) -> bool:
    """Check if atom references Judge McNeill."""
    text = (atom.get("text", "") + " " + atom.get("content", "") +
            " " + atom.get("speaker", "") + " " + atom.get("person", "")).lower()
    return "mcneill" in text


def run_judicial_analysis(cycle_dir: Path, dry_run: bool = False):
    if is_phase_done(cycle_dir, "phase10"):
        print("[PHASE10] Already complete, skipping", file=sys.stderr)
        return

    print("[PHASE10] Judicial Analysis Engine starting...", file=sys.stderr)
    start = time.time()

    # Load all atom stores
    fact_atoms = _load_atom_store(cycle_dir, "fact_atoms")
    citation_atoms = _load_atom_store(cycle_dir, "citation_atoms")
    event_atoms = _load_atom_store(cycle_dir, "event_atoms")
    person_atoms = _load_atom_store(cycle_dir, "person_atoms")

    all_atoms = fact_atoms + citation_atoms + event_atoms + person_atoms
    print(f"[PHASE10] Loaded atoms: facts={len(fact_atoms)}, citations={len(citation_atoms)}, "
          f"events={len(event_atoms)}, persons={len(person_atoms)}", file=sys.stderr)

    # ── Analyze: find violations, score incidents ────────────────────
    violations: list[dict] = []
    benchbook_violations: list[dict] = []
    jtc_exhibits: list[dict] = []
    mcneill_timeline: list[dict] = []
    disqual_scores: dict[str, float] = {k: 0.0 for k in MCR_2003C_GROUNDS}

    for idx, atom in enumerate(all_atoms):
        text = atom.get("text", "") or atom.get("content", "")
        if not text:
            continue

        text_lower = text.lower()

        # Check for violation keywords
        has_violation = any(kw in text_lower for kw in VIOLATION_KEYWORDS)
        canon_matches = _match_canon_violations(text)
        benchbook_matches = _match_benchbook_sections(text)
        disqual_matches = _match_disqualification_grounds(text)
        is_mcneill = _is_mcneill_related(atom)

        if not (has_violation or canon_matches or disqual_matches):
            continue

        # Compute evidence density
        posture = atom.get("posture", "ALLEGATION")
        pw = POSTURE_WEIGHT.get(posture, 1.0)
        evidence_density = pw * (1.0 + 0.1 * len(canon_matches) + 0.1 * len(disqual_matches))

        severity = _classify_severity(text)
        date_str = atom.get("date") or atom.get("event_date")
        score = _score_incident(severity, evidence_density, date_str)

        source = atom.get("source_path", "") or atom.get("source", "")

        violation_entry = {
            "atom_id": atom.get("atom_id", f"ATOM-{idx}"),
            "atom_type": atom.get("atom_type", "unknown"),
            "text_excerpt": text[:500],
            "severity": severity,
            "evidence_density": round(evidence_density, 2),
            "temporal_recency": date_str,
            "score": score,
            "canon_violations": canon_matches,
            "disqualification_grounds": [d["subsection"] for d in disqual_matches],
            "source": source,
            "posture": posture,
            "mcneill_related": is_mcneill,
            "meek_lane": atom.get("meek_lane", ""),
        }
        violations.append(violation_entry)

        # Benchbook violations
        for bb in benchbook_matches:
            benchbook_violations.append({
                "atom_id": violation_entry["atom_id"],
                "violation_text": text[:300],
                "benchbook_section": bb["section"],
                "benchbook_title": bb["title"],
                "score": score,
                "source": source,
            })

        # JTC exhibits — high-severity or Canon-matching
        if severity >= 7 or canon_matches:
            jtc_exhibits.append({
                "atom_id": violation_entry["atom_id"],
                "exhibit_type": "judicial_misconduct" if is_mcneill else "procedural_violation",
                "severity": severity,
                "score": score,
                "canon_violations": canon_matches,
                "text_excerpt": text[:500],
                "source": source,
                "date": date_str,
            })

        # McNeill timeline
        if is_mcneill and date_str:
            mcneill_timeline.append({
                "date": date_str,
                "atom_id": violation_entry["atom_id"],
                "event_type": atom.get("atom_type", "unknown"),
                "severity": severity,
                "score": score,
                "text_excerpt": text[:300],
                "canon_violations": canon_matches,
                "source": source,
            })

        # Accumulate disqualification scores
        for dm in disqual_matches:
            disqual_scores[dm["ground"]] += score

        if (idx + 1) % 5000 == 0:
            report_progress("phase10", idx + 1, len(all_atoms))

    report_progress("phase10", len(all_atoms), len(all_atoms))

    # Sort results
    violations.sort(key=lambda v: v["score"], reverse=True)
    mcneill_timeline.sort(key=lambda e: e.get("date", ""))
    jtc_exhibits.sort(key=lambda e: e["score"], reverse=True)

    elapsed = round(time.time() - start, 1)

    # ── Build disqualification scorecard ─────────────────────────────
    disqual_scorecard = {
        "mcr_rule": "MCR 2.003(C)",
        "judge": "McNeill",
        "grounds": {},
        "cumulative_score": round(sum(disqual_scores.values()), 2),
        "total_violations": len(violations),
        "high_severity_count": sum(1 for v in violations if v["severity"] >= 7),
        "computed_at": datetime.now().isoformat(),
    }
    for ground_key, ground_info in MCR_2003C_GROUNDS.items():
        disqual_scorecard["grounds"][ground_key] = {
            "label": ground_info["label"],
            "subsection": ground_info["subsection"],
            "score": round(disqual_scores[ground_key], 2),
            "incident_count": sum(
                1 for v in violations
                if ground_info["subsection"] in v.get("disqualification_grounds", [])
            ),
        }

    # ── Build main report ────────────────────────────────────────────
    report = {
        "phase": "phase10_judicial_analysis",
        "judge": "McNeill",
        "cycle_dir": str(cycle_dir),
        "atom_counts": {
            "fact": len(fact_atoms),
            "citation": len(citation_atoms),
            "event": len(event_atoms),
            "person": len(person_atoms),
            "total": len(all_atoms),
        },
        "violations_found": len(violations),
        "violations": violations[:200],
        "canon_violation_summary": {
            canon_id: sum(1 for v in violations if canon_id in v["canon_violations"])
            for canon_id in CANON_VIOLATIONS
        },
        "mcneill_incidents": sum(1 for v in violations if v["mcneill_related"]),
        "jtc_exhibit_count": len(jtc_exhibits),
        "benchbook_violation_count": len(benchbook_violations),
        "disqualification_cumulative": disqual_scorecard["cumulative_score"],
        "elapsed_seconds": elapsed,
    }

    # ── Write outputs ────────────────────────────────────────────────
    if not dry_run:
        cycle_dir.mkdir(parents=True, exist_ok=True)

        (cycle_dir / "judicial_analysis_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8")

        with open(cycle_dir / "benchbook_violations.jsonl", "w", encoding="utf-8") as f:
            for bv in benchbook_violations:
                f.write(json.dumps(bv) + "\n")

        with open(cycle_dir / "jtc_new_exhibits.jsonl", "w", encoding="utf-8") as f:
            for ex in jtc_exhibits:
                f.write(json.dumps(ex) + "\n")

        (cycle_dir / "disqualification_score.json").write_text(
            json.dumps(disqual_scorecard, indent=2), encoding="utf-8")

        with open(cycle_dir / "mcneill_pattern_timeline.jsonl", "w", encoding="utf-8") as f:
            for ev in mcneill_timeline:
                f.write(json.dumps(ev) + "\n")

        print(f"[PHASE10] Outputs written to {cycle_dir}", file=sys.stderr)
        write_phase_checkpoint(cycle_dir, "phase10", {
            "status": "done",
            "violations": len(violations),
            "jtc_exhibits": len(jtc_exhibits),
            "benchbook_hits": len(benchbook_violations),
            "disqual_score": disqual_scorecard["cumulative_score"],
            "elapsed": f"{elapsed:.0f}s",
        })
    else:
        print(f"[PHASE10] DRY RUN — found {len(violations)} violations, "
              f"{len(jtc_exhibits)} JTC exhibits", file=sys.stderr)

    print(f"[PHASE10] Complete in {elapsed:.0f}s — "
          f"{len(violations)} violations, disqual score {disqual_scorecard['cumulative_score']:.1f}",
          file=sys.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 10: Judicial Analysis Engine")
    parser.add_argument("--cycle-ts", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_judicial_analysis(get_cyclepack_dir(args.cycle_ts or CYCLE_TS), args.dry_run)
