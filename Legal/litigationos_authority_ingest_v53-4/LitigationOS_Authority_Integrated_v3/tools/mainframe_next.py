#!/usr/bin/env python3
"""
mainframe_next.py (v45) — One-command "next step" orchestrator.

Runs, in order:
1) next_best_step_report.py -> outputs/next_best_step.json
2) generate_runbook_v44.py -> docs/RUNBOOK_NEXT.md
3) (optional) templates_seed_intents_props_v43.py if outputs/intents.json or outputs/propositions.json missing

Non-interpretive; no facts/law generation.
"""
import argparse, os, subprocess, sys, json

def exists_nonzero(p):
    return os.path.exists(p) and os.path.getsize(p) > 0

def run(cmd):
    return subprocess.run(cmd, check=False)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle-root", default=".")
    ap.add_argument("--out-json", default="outputs/next_best_step.json")
    ap.add_argument("--out-runbook", default="docs/RUNBOOK_NEXT.md")
    ap.add_argument("--seed-templates-if-missing", action="store_true")
    args=ap.parse_args()

    root=os.path.abspath(args.bundle_root)
    tools=os.path.join(root,"tools")
    out_json=os.path.join(root,args.out_json)
    out_runbook=os.path.join(root,args.out_runbook)

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    os.makedirs(os.path.dirname(out_runbook), exist_ok=True)

    # Optional template seeding
    if args.seed_templates_if_missing:
        intents=os.path.join(root,"outputs","intents.json")
        props=os.path.join(root,"outputs","propositions.json")
        if not exists_nonzero(intents) or not exists_nonzero(props):
            seed=os.path.join(tools,"templates_seed_intents_props_v43.py")
            if os.path.exists(seed):
                run([sys.executable, seed, "--out-dir", os.path.join(root,"outputs")])

    # Next best step JSON
    run([sys.executable, os.path.join(tools,"next_best_step_report.py"),
         "--bundle-root", root, "--out-json", out_json])

    # Runbook MD
    run([sys.executable, os.path.join(tools,"generate_runbook_v44.py"),
         "--bundle-root", root, "--out-md", os.path.join("docs","RUNBOOK_NEXT.md")])

    # v49: if docket_events exists and deadlines missing, generate candidate deadlines
    dock=os.path.join(root,'outputs','docket_events.json')
    deads=os.path.join(root,'outputs','deadlines.json')
    if os.path.exists(dock) and os.path.getsize(dock)>0 and (not os.path.exists(deads) or os.path.getsize(deads)==0):
        v49=os.path.join(tools,'deadlines_from_docket_v49.py')
        if os.path.exists(v49):
            run([sys.executable, v49, '--docket-json', dock, '--out-deadlines', deads])

    # Print concise summary
    if exists_nonzero(out_json):
        data=json.load(open(out_json,"r",encoding="utf-8"))
        print("STATUS:", data.get("status"))
        print("NEXT:", data.get("single_best_action"))
        print("WHY:", data.get("why"))
        if data.get("inputs_needed"):
            print("INPUTS_NEEDED:", "; ".join(data["inputs_needed"]))
        if data.get("commands"):
            print("COMMANDS:")
            for c in data["commands"]:
                print(" ", c)
    else:
        print("ERROR: next_best_step.json not created", file=sys.stderr)
        raise SystemExit(2)

if __name__=="__main__":
    main()
