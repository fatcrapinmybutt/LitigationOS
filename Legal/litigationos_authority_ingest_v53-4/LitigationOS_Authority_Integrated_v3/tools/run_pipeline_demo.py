#!/usr/bin/env python3
"""
Run Pipeline Demo v21
Runs the minimal chain:
vehicle_router_mi.py -> proposition_builder.py -> claim_compiler_gate.py -> draft_from_claim_packet.py -> draft_validator.py
Then preflight_gate.py with deadlines if present.
This is a DEMO orchestrator for reproducibility; you will later replace inputs with real artifacts.
"""
import argparse, os, sys, subprocess, json, shutil

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Path to extracted bundle root (contains tools/, outputs/)")
    ap.add_argument("--use-deadlines", action="store_true")
    args=ap.parse_args()
    root=args.root
    tools=os.path.join(root,"tools")
    out=os.path.join(root,"outputs")
    os.makedirs(out, exist_ok=True)

    py=sys.executable

    # Inputs already expected in outputs/ from prior demo runs:
    vehicle_map=os.path.join(out,"vehicle_map_candidates_PASS.json")
    anchors=os.path.join(out,"authority_anchors.csv")
    props=os.path.join(out,"authority_propositions_candidates_v18.jsonl")
    evidence=os.path.join(out,"evidence_facts_candidates_demo.jsonl")
    claim_packets=os.path.join(out,"claim_packets_PASS_v18.jsonl")
    draft=os.path.join(out,"draft_locked_demo_v21.txt")
    valj=os.path.join(out,"draft_validation_report_demo_v21.json")
    valc=os.path.join(out,"draft_validation_issues_demo_v21.csv")

    # Draft + validate
    subprocess.run([py, os.path.join(tools,"draft_from_claim_packet.py"),
                    "--claim-packets-jsonl", claim_packets,
                    "--out-draft-txt", draft,
                    "--title", "LOCKED DRAFT DEMO v21"], check=True)
    subprocess.run([py, os.path.join(tools,"draft_validator.py"),
                    "--draft-txt", draft, "--out-json", valj, "--out-csv", valc], check=True)

    # Preflight
    pre=os.path.join(out,"preflight_report_demo_v21.json")
    prefx=os.path.join(out,"preflight_fixlist_demo_v21.csv")
    deadlines=os.path.join(out,"deadlines_candidates_demo_v20.csv") if args.use_deadlines else ""
    cmd=[py, os.path.join(tools,"preflight_gate.py"),
         "--vehicle-map-json", vehicle_map,
         "--claim-packets-jsonl", claim_packets,
         "--out-json", pre,
         "--out-csv", prefx]
    if deadlines and os.path.exists(deadlines) and os.path.getsize(deadlines)>0:
        cmd += ["--deadlines-csv", deadlines]
    subprocess.run(cmd, check=True)

    print("OK pipeline_demo_complete")

if __name__=="__main__":
    main()
