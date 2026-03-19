import os, csv, json
from collections import defaultdict

class GraphAnalytics:
    """
    CSV-based graph analytics to detect shell patterns without requiring a live Neo4j instance.
    Patterns detected:
    - Common Registered Agent (Person -> multiple LLC via REGISTERED_AGENT or REL.type)
    - Round-Robin Ownership (LLC OWNS LLC and reverse)
    - Rent Extraction Chain (Person -LEASES-> Property <-OWNS- LLC -MANAGES-> LLC)
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.runs_dir = os.path.join(self.root, "..", "..", "data", "graph_runs")
        os.makedirs(self.runs_dir, exist_ok=True)

    def _latest_run(self):
        runs = [d for d in os.listdir(self.runs_dir) if os.path.isdir(os.path.join(self.runs_dir, d))]
        return sorted(runs)[-1] if runs else None

    def _headers(self, path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return next(csv.reader(f), [])

    def _colmap_nodes(self, headers):
        H = [h.lower() for h in headers]
        def pick(*names, default=None):
            for n in names:
                if n in H:
                    return headers[H.index(n)]
            return default
        return {
            "id": pick("id","node","node_id", default=headers[0] if headers else "id"),
            "label": pick("label","labels","type", default=None),
            "name": pick("name","display","title","full_name", default=None)
        }

    def _colmap_edges(self, headers):
        H = [h.lower() for h in headers]
        def pick(*names, default=None):
            for n in names:
                if n in H:
                    return headers[H.index(n)]
            return default
        src = pick("from","source","src","start","start_id", default=headers[0] if headers else "from")
        dst = pick("to","target","dst","end","end_id", default=headers[1] if len(headers)>1 else "to")
        et  = pick("type","rel","relationship", default=None)
        return {"src": src, "dst": dst, "type": et}

    def analyze(self, run_id: str | None = None) -> dict:
        rid = run_id or self._latest_run()
        if not rid:
            return {"ok": False, "error": "no_graph_runs"}
        run_dir = os.path.join(self.runs_dir, rid)
        nodes_csv = os.path.join(run_dir, "nodes.csv")
        edges_csv = os.path.join(run_dir, "edges.csv")
        if not (os.path.exists(nodes_csv) and os.path.exists(edges_csv)):
            return {"ok": False, "error": "missing_nodes_or_edges"}

        # Load nodes
        nh = self._headers(nodes_csv)
        nm = self._colmap_nodes(nh)
        nodes = {}
        labels = {}
        names = {}
        with open(nodes_csv, "r", encoding="utf-8", errors="ignore") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                nid = (row.get(nm["id"]) or "").strip()
                if not nid: 
                    continue
                nodes[nid] = row
                L = (row.get(nm["label"]) or "").strip()
                labels[nid] = L.lower() if L else ""
                names[nid] = (row.get(nm["name"]) or row.get(nm["id"]) or "").strip()

        # Load edges
        eh = self._headers(edges_csv)
        em = self._colmap_edges(eh)
        edges = []
        with open(edges_csv, "r", encoding="utf-8", errors="ignore") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                src = (row.get(em["src"]) or "").strip()
                dst = (row.get(em["dst"]) or "").strip()
                typ = (row.get(em["type"]) or "").strip().lower() if em["type"] else ""
                edges.append({"src": src, "dst": dst, "type": typ, "row": row})

        # Index by type
        by_type = defaultdict(list)
        for e in edges:
            t = e["type"]
            by_type[t].append(e)

        # Helper: type aliases
        def is_registered_agent(t): 
            return t in {"registered_agent","agent_for","ra"} or t.startswith("registered")
        def is_owns(t): 
            return t in {"owns","owned_by"} or "own" in t
        def is_manages(t): 
            return t in {"manages","managed_by"} or "manage" in t
        def is_leases(t): 
            return t in {"leases","leased_by","rents","rented_by"} or "lease" in t or "rent" in t

        # Pattern 1: Common Registered Agent (Person -> multiple LLC)
        agent_to_llcs = defaultdict(set)
        for e in edges:
            if is_registered_agent(e["type"]):
                srcL = labels.get(e["src"], "")
                dstL = labels.get(e["dst"], "")
                # Direction agnostic: link Person <-> LLC
                if "person" in srcL and ("llc" in dstL or "company" in dstL or "corp" in dstL or "entity" in dstL):
                    agent_to_llcs[e["src"]].add(e["dst"])
                if "person" in dstL and ("llc" in srcL or "company" in srcL or "corp" in srcL or "entity" in srcL):
                    agent_to_llcs[e["dst"]].add(e["src"])
        common_agents = [{"agent_id": a, "agent_name": names.get(a, a), "llc_count": len(v), "llc_ids": sorted(list(v))} 
                         for a, v in agent_to_llcs.items() if len(v) >= 2]

        # Pattern 2: Round-robin ownership
        owns_map = defaultdict(set)
        for e in edges:
            if is_owns(e["type"]):
                owns_map[e["src"]].add(e["dst"])
        loops = []
        seen_pairs = set()
        for a, outs in owns_map.items():
            for b in outs:
                if a != b and a in owns_map.get(b, set()):
                    key = tuple(sorted([a,b]))
                    if key not in seen_pairs:
                        seen_pairs.add(key)
                        loops.append({"a": a, "a_name": names.get(a, a), "b": b, "b_name": names.get(b, b)})

        # Pattern 3: Rent extraction chain: Person -LEASES-> Property <-OWNS- LLC -MANAGES-> LLC
        # Build quick adjacency by type
        leases = [e for e in edges if is_leases(e["type"])]
        owns = [e for e in edges if is_owns(e["type"])]
        manages = [e for e in edges if is_manages(e["type"])]
        property_nodes = {nid for nid, L in labels.items() if "property" in L or "home" in L or "unit" in L or "lot" in L}
        rent_chains = []
        # Person -> Property via LEASES
        for e1 in leases:
            if "person" not in labels.get(e1["src"], ""): 
                continue
            if e1["dst"] not in property_nodes:
                continue
            prop = e1["dst"]
            # find LLC OWNS prop (both directions considered)
            llc_owners = [e for e in owns if (e["dst"] == prop and ("llc" in labels.get(e["src"], "") or "company" in labels.get(e["src"], "") or "corp" in labels.get(e["src"], "")))]
            for own in llc_owners:
                llc = own["src"]
                # find llc -> manages -> mgmt
                mgmts = [e for e in manages if e["src"] == llc and ("llc" in labels.get(e["dst"], "") or "company" in labels.get(e["dst"], ""))]
                for mg in mgmts:
                    rent_chains.append({
                        "tenant_id": e1["src"], "tenant_name": names.get(e1["src"], e1["src"]),
                        "property_id": prop, "property_name": names.get(prop, prop),
                        "owner_llc_id": llc, "owner_llc_name": names.get(llc, llc),
                        "manager_llc_id": mg["dst"], "manager_llc_name": names.get(mg["dst"], mg["dst"])
                    })

        # Pressure tags
        pressure = {}
        if common_agents:
            pressure["registered_agent_network"] = min(0.4, 0.1 * max(c["llc_count"] for c in common_agents))
        if loops:
            pressure["ownership_loop"] = min(0.4, 0.1 * len(loops))
        if rent_chains:
            pressure["rent_extraction_chain"] = min(0.4, 0.05 * len(rent_chains))

        return {
            "ok": True,
            "run_id": rid,
            "summary": {
                "common_registered_agents": len(common_agents),
                "ownership_loops": len(loops),
                "rent_extraction_chains": len(rent_chains)
            },
            "details": {
                "common_registered_agents": common_agents[:50],
                "ownership_loops": loops[:100],
                "rent_extraction_chains": rent_chains[:100]
            },
            "pressure": pressure
        }
