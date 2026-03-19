import os, json, yaml
from authorities.scrape_mcl import scrape_mcl_index
from authorities.scrape_mcr import scrape_mcr_pdf
from authorities.scrape_wdmi import scrape_wdmi_local_rules
from authorities.scrape_frxx import scrape_frcp, scrape_frap
from authorities.scrape_ca6 import scrape_ca6_rules
from authorities.scrape_constitution import scrape_constitution
from authorities.util import ensure_dir

def main():
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    out_dir = ensure_dir(cfg["storage"]["out_dir"])
    nodes = []

    for j in cfg["jurisdictions"]:
        s = j["sources"]
        if j["name"] == "Michigan":
            nodes += scrape_mcl_index(s["mcl_index_url"])
            nodes += scrape_mcr_pdf(s["mcr_pdf_url"])
        elif j["name"] == "Western District of Michigan":
            nodes += scrape_wdmi_local_rules(s["wdmi_local_rules_pdf"])
        elif j["name"] == "Federal":
            nodes += scrape_frcp(s["frcp_pdf_url"])
            nodes += scrape_frap(s["frap_pdf_url"])
            nodes += scrape_constitution(s["constitution_url"])
        elif j["name"] == "Sixth Circuit":
            nodes += scrape_ca6_rules(s["ca6_rules_pdf"])

    # dedupe
    uniq = {n["id"]: n for n in nodes}
    out_path = os.path.join(out_dir, "authorities_nodes.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for n in uniq.values():
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    print(f"Wrote {len(uniq)} nodes -> {out_path}")

if __name__ == "__main__":
    main()
