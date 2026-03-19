#!/usr/bin/env python3
import argparse, json, os, subprocess, sys, datetime

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle-root", default=".")
    ap.add_argument("--out-md", default="docs/RUNBOOK_NEXT.md")
    args=ap.parse_args()

    root=os.path.abspath(args.bundle_root)
    out_json=os.path.join(root,"outputs","next_best_step.json")

    if not (os.path.exists(out_json) and os.path.getsize(out_json)>0):
        subprocess.run([sys.executable, os.path.join(root,"tools","next_best_step_report.py"),
                        "--bundle-root", root, "--out-json", out_json], check=False)

    if not (os.path.exists(out_json) and os.path.getsize(out_json)>0):
        raise SystemExit(2)

    data=json.load(open(out_json,"r",encoding="utf-8"))
    gates=data.get("gates") or []
    cmds=data.get("commands") or []
    inputs=data.get("inputs_needed") or []

    md=[]
    md.append("# LitigationOS Authority Ingest — RUNBOOK (v44)\n\n")
    md.append(f"Generated: {datetime.datetime.utcnow().isoformat()}Z\n\n")
    md.append("## Next best step\n\n")
    md.append(f"**Status:** {data.get('status')}\n\n")
    md.append(f"**Single best action:** {data.get('single_best_action')}\n\n")
    md.append(f"**Why:** {data.get('why')}\n\n")

    md.append("## Gates\n\n")
    md.append("| Gate | Status | Detail |\n|---|---|---|\n")
    for g in gates:
        md.append(f"| {g.get('gate')} | {g.get('status')} | {g.get('detail','')} |\n")

    md.append("\n## Inputs needed\n\n")
    if inputs:
        for i in inputs:
            md.append(f"- {i}\n")
    else:
        md.append("- (none)\n")

    md.append("\n## Commands (copy/paste)\n\n")
    if cmds:
        md.append("```bash\n")
        for c in cmds:
            md.append(c+"\n")
        md.append("```\n")
    else:
        md.append("_No commands suggested._\n")

    out_path=os.path.join(root,args.out_md)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path,"w",encoding="utf-8").write("".join(md))
    print("OK wrote", args.out_md)

if __name__=="__main__":
    main()
