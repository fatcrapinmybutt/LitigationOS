import json, os

# 1. Inspect graph data structure
gpath = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\graph_data_v7.json"
with open(gpath, "r", encoding="utf-8") as f:
    d = json.load(f)

print("=== GRAPH DATA STRUCTURE ===")
print(f"Top-level type: {type(d).__name__}")
print(f"Top-level keys: {list(d.keys())}")

nodes = d.get("nodes", [])
links = d.get("links", [])
print(f"\nnodes type: {type(nodes).__name__}, length: {len(nodes)}")
print(f"links type: {type(links).__name__}, length: {len(links)}")

# Show first 3 nodes
for i, n in enumerate(nodes[:3]):
    print(f"\nNode[{i}] type={type(n).__name__}: {str(n)[:200]}")

# Show first 2 links
for i, l in enumerate(links[:2]):
    print(f"\nLink[{i}] type={type(l).__name__}: {str(l)[:200]}")

# Check if nodes have IDs
if nodes and isinstance(nodes[0], dict):
    print(f"\nNode keys: {list(nodes[0].keys())}")
    # Find adversary nodes
    adv = [n for n in nodes if isinstance(n, dict) and n.get("layer") in ("ADVERSARY_CORE","ADVERSARY_NET")]
    print(f"Adversary nodes: {len(adv)}")
    for a in adv[:5]:
        print(f"  {a.get('id','?')} layer={a.get('layer','?')}")
elif nodes and isinstance(nodes[0], (int, float)):
    print(f"\nNODES ARE NUMBERS! First 10: {nodes[:10]}")
