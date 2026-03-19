import os, json, yaml, pathlib
from authorities.scrape_mcl import scrape_mcl_index
from authorities.scrape_mcr import scrape_mcr_pdf
from authorities.scrape_wdmi import scrape_wdmi_local_rules
from authorities.scrape_frxx import scrape_frcp, scrape_frap
from authorities.scrape_ca6 import scrape_ca6_rules
from authorities.scrape_constitution import scrape_constitution
from authorities.scrape_common import write_nodes
from authorities.util import ensure_dir

def run(config_path: str):
    cfg = yaml.safe_load(open(config_path, 'r', encoding='utf-8'))
    out_dir = ensure_dir(cfg["storage"]["out_dir"])
    nodes_all = []

    for j in cfg["jurisdictions"]:
        name = j["name"]
        s = j["sources"]

        if name == "Michigan":
            nodes_all += scrape_mcl_index(s["mcl_index_url"])
            nodes_all += scrape_mcr_pdf(s["mcr_pdf_url"])
        elif name == "Federal":
            nodes_all += scrape_frcp(s["frcp_pdf_url"])
            nodes_all += scrape_frap(s["frap_pdf_url"])
            nodes_all += scrape_constitution(s["constitution_url"])
        elif name == "Western District of Michigan":
            nodes_all += scrape_wdmi_local_rules(s["wdmi_local_rules_pdf"])
        elif name == "Sixth Circuit":
            nodes_all += scrape_ca6_rules(s["ca6_rules_pdf"])

    # Deduplicate by id
    uniq = {}
    for n in nodes_all:
        uniq[n["id"]] = n
    nodes_all = list(uniq.values())

    write_nodes(nodes_all, os.path.join(out_dir, cfg["graph"]["export"]["json_nodes"]))
    print(f"Wrote {len(nodes_all)} authority nodes to {os.path.join(out_dir, cfg['graph']['export']['json_nodes'])}")

if __name__ == "__main__":
    run("config.yaml")
