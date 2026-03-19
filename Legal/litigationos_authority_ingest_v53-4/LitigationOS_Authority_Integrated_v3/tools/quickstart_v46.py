#!/usr/bin/env python3
"""
quickstart_v46.py — Creates minimal working scaffold and prints next commands.

Non-interpretive: does not create facts/law; only files + runbook.
"""
import os, json, subprocess, sys, shutil

def exists_nonzero(p):
    return os.path.exists(p) and os.path.getsize(p)>0

def main():
    os.makedirs("outputs", exist_ok=True)
    # seed templates if missing
    seed=os.path.join("tools","templates_seed_intents_props_v43.py")
    if os.path.exists(seed):
        if not exists_nonzero(os.path.join("outputs","intents.json")) or not exists_nonzero(os.path.join("outputs","propositions.json")):
            subprocess.run([sys.executable, seed, "--out-dir", "outputs"], check=False)

    # run mainframe next
    mf=os.path.join("tools","mainframe_next.py")
    if os.path.exists(mf):
        subprocess.run([sys.executable, mf, "--seed-templates-if-missing"], check=False)

    print("\nNEXT: Add evidence intake list, then generate facts skeleton:")
    print("  1) copy docs/examples/evidence_intake_in.example.json -> outputs/evidence_intake_in.json (edit paths)")
    print("  2) python tools/evidence_intake_to_facts_skeleton_v44.py --in-json outputs/evidence_intake_in.json --out-facts-jsonl outputs/facts.jsonl")
    print("  3) python tools/fact_capture_cli_v46.py --facts-jsonl outputs/facts.jsonl --run-validate --manifest-json manifest.json")
    print("  4) python tools/mainframe_next.py")
    print("\nSee docs/RUNBOOK_NEXT.md for gate status.\n")

if __name__=="__main__":
    main()
