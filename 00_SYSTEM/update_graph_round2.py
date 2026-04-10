"""Add new adversary nodes to THEMANBEARPIG graph data.
Adds: Brian Cross, Kostrzewa + updates threat levels.
"""
import json, os
from datetime import datetime, date

GRAPH_PATH = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\graph_data_v7.json"

with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    graph = json.load(f)

nodes = graph.get("nodes", [])
links = graph.get("links", [])

# Check existing node IDs
existing_ids = {n["id"] for n in nodes}
print(f"Existing nodes: {len(nodes)}")
print(f"Existing links: {len(links)}")

new_nodes = []
new_links = []

# === NEW NODE: Brian Cross ===
if "CROSS_BRIAN" not in existing_ids:
    new_nodes.append({
        "id": "CROSS_BRIAN",
        "label": "Brian Cross",
        "layer": "ADVERSARY_NET",
        "tier": 4,
        "threat": 6,
        "description": "Shady Oaks Park Manager — directed fraud, illegal eviction, harassment",
        "lane": "B",
        "evidence_count": 20,
        "file_mentions": 8660,
        "category": "housing_adversary"
    })
    # Links for Brian Cross
    new_links.extend([
        {"source": "CROSS_BRIAN", "target": "VANDAM_CASSANDRA", "type": "COORDINATION", "weight": 7, "label": "management coordination"},
        {"source": "CROSS_BRIAN", "target": "SHADY_OAKS", "type": "EMPLOYMENT", "weight": 8, "label": "park manager"},
        {"source": "CROSS_BRIAN", "target": "PIGORS_ANDREW", "type": "ATTACK", "weight": 6, "label": "harassment + fraud"},
    ])
    print("  Added: CROSS_BRIAN (Brian Cross)")

# === NEW NODE: Kostrzewa ===
if "KOSTRZEWA" not in existing_ids:
    new_nodes.append({
        "id": "KOSTRZEWA",
        "label": "Judge Kostrzewa",
        "layer": "JUDICIAL_CARTEL",
        "tier": 3,
        "threat": 5,
        "description": "60th District Court — criminal case 2025-25245676SM",
        "lane": "CRIMINAL",
        "evidence_count": 49,
        "file_mentions": 895,
        "category": "judicial"
    })
    new_links.extend([
        {"source": "KOSTRZEWA", "target": "LADAS_HOOPES", "type": "COURT_CONNECTION", "weight": 6, "label": "60th District colleague"},
        {"source": "KOSTRZEWA", "target": "PIGORS_ANDREW", "type": "JUDICIAL_ACTION", "weight": 5, "label": "criminal proceedings"},
    ])
    print("  Added: KOSTRZEWA (Judge Kostrzewa)")

# === Update separation days on relevant nodes ===
sep_days = (date.today() - date(2025, 7, 29)).days
for node in nodes:
    if node.get("id") == "SEP_COUNTER" or node.get("label", "").startswith("Separation"):
        node["label"] = f"Separation: {sep_days} Days"
        node["description"] = f"{sep_days} days since last contact with L.D.W. (Jul 29, 2025)"
        print(f"  Updated: SEP_COUNTER → {sep_days} days")

# === Check for KIM_DAVIS, ensure exists ===
if "KIM_DAVIS" not in existing_ids:
    new_nodes.append({
        "id": "KIM_DAVIS",
        "label": "Kim Davis",
        "layer": "ADVERSARY_NET",
        "tier": 4,
        "threat": 5,
        "description": "Shady Oaks — directed fraud and illegal eviction operations",
        "lane": "B",
        "evidence_count": 499,
        "file_mentions": 252,
        "category": "housing_adversary"
    })
    new_links.extend([
        {"source": "KIM_DAVIS", "target": "CROSS_BRIAN", "type": "MANAGEMENT_CHAIN", "weight": 7, "label": "directed operations"},
        {"source": "KIM_DAVIS", "target": "SHADY_OAKS", "type": "EMPLOYMENT", "weight": 8, "label": "park management"},
    ])
    print("  Added: KIM_DAVIS")

# === Ensure VANDAM_CASSANDRA exists ===
if "VANDAM_CASSANDRA" not in existing_ids:
    new_nodes.append({
        "id": "VANDAM_CASSANDRA",
        "label": "Cassandra VanDam",
        "layer": "ADVERSARY_NET",
        "tier": 5,
        "threat": 4,
        "description": "Shady Oaks office communications hub",
        "lane": "B",
        "evidence_count": 488,
        "file_mentions": 148,
        "category": "housing_adversary"
    })
    new_links.extend([
        {"source": "VANDAM_CASSANDRA", "target": "SHADY_OAKS", "type": "EMPLOYMENT", "weight": 6, "label": "office staff"},
    ])
    print("  Added: VANDAM_CASSANDRA")

# === Ensure DUGUID_LAUREN exists ===
if "DUGUID_LAUREN" not in existing_ids:
    new_nodes.append({
        "id": "DUGUID_LAUREN",
        "label": "Lauren Duguid",
        "layer": "ADVERSARY_NET",
        "tier": 4,
        "threat": 6,
        "description": "Prosecutor P87908 — authorized warrant, prosecutorial pipeline",
        "lane": "CRIMINAL",
        "evidence_count": 98,
        "file_mentions": 1390,
        "category": "prosecutorial"
    })
    new_links.extend([
        {"source": "DUGUID_LAUREN", "target": "HILSON_DJ", "type": "CHAIN_OF_COMMAND", "weight": 8, "label": "prosecutor's office"},
        {"source": "DUGUID_LAUREN", "target": "PIGORS_ANDREW", "type": "PROSECUTION", "weight": 7, "label": "warrant authorization"},
    ])
    print("  Added: DUGUID_LAUREN")

# === Ensure HILSON_DJ exists ===
if "HILSON_DJ" not in existing_ids:
    new_nodes.append({
        "id": "HILSON_DJ",
        "label": "DJ Hilson",
        "layer": "ADVERSARY_NET",
        "tier": 3,
        "threat": 7,
        "description": "Muskegon County Prosecutor — political machine, prosecutorial pipeline head",
        "lane": "CRIMINAL",
        "evidence_count": 67,
        "file_mentions": 475,
        "category": "prosecutorial"
    })
    new_links.extend([
        {"source": "HILSON_DJ", "target": "MCNEILL_JENNY", "type": "INSTITUTIONAL", "weight": 5, "label": "court-prosecutor nexus"},
    ])
    print("  Added: HILSON_DJ")

# === BERRY connection link ===
# Ensure Berry-Berry family link exists
berry_link_exists = any(
    (l.get("source") == "BERRY_RONALD" and l.get("target") == "BERRY_CAVAN") or
    (l.get("source") == "BERRY_CAVAN" and l.get("target") == "BERRY_RONALD")
    for l in links
)
if not berry_link_exists:
    new_links.append({
        "source": "BERRY_RONALD", 
        "target": "BERRY_CAVAN",
        "type": "FAMILY_CONNECTION",
        "weight": 9,
        "label": "CONFIRMED: extended family + social circles + local businesses"
    })
    print("  Added: BERRY_RONALD → BERRY_CAVAN family link")

# Merge
nodes.extend(new_nodes)
links.extend(new_links)

graph["nodes"] = nodes
graph["links"] = links
graph["metadata"] = graph.get("metadata", {})
graph["metadata"]["last_updated"] = datetime.now().isoformat()
graph["metadata"]["version"] = "8.1.0"
graph["metadata"]["round2_expansion"] = True
graph["metadata"]["new_nodes_added"] = len(new_nodes)
graph["metadata"]["new_links_added"] = len(new_links)

with open(GRAPH_PATH, "w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

print(f"\nGraph updated: {len(nodes)} nodes × {len(links)} links")
print(f"New nodes: {len(new_nodes)}, New links: {len(new_links)}")
print(f"Saved to: {GRAPH_PATH}")
