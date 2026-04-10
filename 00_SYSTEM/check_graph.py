import json
p = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\graph_data_v7.json"
with open(p, 'r', encoding='utf-8') as f:
    g = json.load(f)
print("Type:", type(g).__name__)
if isinstance(g, dict):
    for k, v in g.items():
        tp = type(v).__name__
        ln = len(v) if hasattr(v, '__len__') else 'N/A'
        print(f"  {k}: {tp}, len={ln}")
        if isinstance(v, list) and v:
            first = v[0]
            if isinstance(first, dict):
                print(f"    first keys: {list(first.keys())}")
            else:
                print(f"    first type: {type(first).__name__}")
elif isinstance(g, list):
    print(f"  LIST of {len(g)} items")
    if g:
        first = g[0]
        if isinstance(first, dict):
            print(f"    first keys: {list(first.keys())}")
else:
    print("  Unexpected type!")
