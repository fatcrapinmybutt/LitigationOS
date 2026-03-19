#!/usr/bin/env python3
"""
run_claim_pipeline_v39.py (v39) — Deterministic runner for candidate-only claim packet pipeline.

This runner wires together existing tools in this bundle:
1) facts template (optional) OR validate provided facts.jsonl
2) mine vehicle registry candidates (optional helper)
3) vehicle router (requires vehicle registry curated by operator)
4) authority triples candidate generator (requires propositions)
5) deadlines compute candidate (requires events spec)
6) claim packet assemble

Nothing here generates legal claims; it packages candidate retrieval outputs with validation.
"""
import argparse, os, sys, json, subprocess

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle-root", required=True, help="path to extracted bundle root (folder containing tools/, outputs/)")
    ap.add_argument("--fts-db", default="outputs/authority_anchor_fts.sqlite")
    ap.add_argument("--facts-jsonl", default="")
    ap.add_argument("--facts-manifest-json", default="manifest.json")
    ap.add_argument("--propositions-json", default="")
    ap.add_argument("--intents-json", default="")
    ap.add_argument("--vehicle-registry-json", default="docs/vehicle_registry_seed_v35.json")
    ap.add_argument("--events-json", default="")
    ap.add_argument("--out-dir", default="outputs")
    args=ap.parse_args()

    root=args.bundle_root
    def p(rel): return os.path.join(root, rel)

    os.makedirs(p(args.out_dir), exist_ok=True)

    fts_db=p(args.fts_db)
    if not os.path.exists(fts_db):
        print("missing fts db", file=sys.stderr); raise SystemExit(2)

    # facts validate if provided
    facts_validation=""
    if args.facts_jsonl:
        facts_validation=p(os.path.join(args.out_dir,"facts_validation_v39.json"))
        subprocess.run([sys.executable, p("tools/facts_pinpoint_validate.py"),
                        "--facts-jsonl", p(args.facts_jsonl),
                        "--manifest-json", p(args.facts_manifest_json),
                        "--out-json", facts_validation], check=False)

    # optional vehicle mining helper
    mined=p(os.path.join(args.out_dir,"vehicle_registry_mined_v39.json"))
    subprocess.run([sys.executable, p("tools/vehicle_registry_miner_candidate.py"),
                    "--db", fts_db,
                    "--out-json", mined,
                    "--topk", "10"], check=True)

    # vehicle routing (requires intents + curated registry)
    vehicle_out=""
    if args.intents_json and args.vehicle_registry_json:
        vehicle_out=p(os.path.join(args.out_dir,"vehicle_candidates_v39.json"))
        subprocess.run([sys.executable, p("tools/vehicle_router_registry.py"),
                        "--db", fts_db,
                        "--intents-json", p(args.intents_json),
                        "--vehicle-registry-json", p(args.vehicle_registry_json),
                        "--out-json", vehicle_out], check=True)

    triples_out=""
    if args.propositions_json:
        triples_out=p(os.path.join(args.out_dir,"authority_triples_candidates_v39.jsonl"))
        subprocess.run([sys.executable, p("tools/authority_triples_candidate.py"),
                        "--db", fts_db,
                        "--in", p(args.propositions_json),
                        "--out-jsonl", triples_out], check=True)

    deadlines_out=""
    if args.events_json:
        deadlines_out=p(os.path.join(args.out_dir,"deadlines_v39.json"))
        subprocess.run([sys.executable, p("tools/deadlines_compute_candidate.py"),
                        "--in-json", p(args.events_json),
                        "--out-json", deadlines_out], check=True)

    packet=p(os.path.join(args.out_dir,"claim_packet_candidate_v39.json"))
    packet_manifest=p(os.path.join(args.out_dir,"claim_packet_manifest_v39.json"))
    subprocess.run([sys.executable, p("tools/claim_packet_assemble_candidate.py"),
                    "--facts-jsonl", p(args.facts_jsonl) if args.facts_jsonl else "",
                    "--facts-validation-json", facts_validation if facts_validation else "",
                    "--vehicle-json", vehicle_out if vehicle_out else "",
                    "--triples-jsonl", triples_out if triples_out else "",
                    "--deadlines-json", deadlines_out if deadlines_out else "",
                    "--out-json", packet,
                    "--out-manifest-json", packet_manifest], check=True)

    print("OK packet=", os.path.relpath(packet, root))

    # v43: always emit next_best_step.json
    try:
        subprocess.run([sys.executable, p('tools/next_best_step_report.py'), '--bundle-root', root, '--out-json', p(os.path.join(args.out_dir,'next_best_step.json'))], check=False)
    except Exception:
        pass

if __name__=="__main__":
    main()
