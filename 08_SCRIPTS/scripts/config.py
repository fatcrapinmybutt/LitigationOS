import os, yaml, copy
DEFAULTS = {
  "offline_only": True,
  "debug": True,
  "storage": {"base_dir":"../","cases_dir":"../cases","deliverables_dir":"../deliverables"},
  "ui": {"port": 8000}
}
def load():
    cfg = copy.deepcopy(DEFAULTS)
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml"))
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
            cfg = _deep_merge(cfg, y)
    # env overrides: LITOS__storage__cases_dir=/path
    for k,v in os.environ.items():
        if not k.startswith("LITOS__"): continue
        parts = k.split("__")[1:]
        _set(cfg, parts, v)
    return cfg

def _set(obj, path, value):
    cur = obj
    for key in path[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    # cast booleans/ints where obvious
    if isinstance(value, str) and value.lower() in ("true","false"):
        value = value.lower()=="true"
    elif isinstance(value, str) and value.isdigit():
        value = int(value)
    cur[path[-1]] = value

def _deep_merge(a, b):
    for k,v in (b or {}).items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            a[k] = _deep_merge(a[k], v)
        else:
            a[k] = v
    return a
