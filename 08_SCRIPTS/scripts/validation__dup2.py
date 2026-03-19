import os, json
from jsonschema import Draft202012Validator

SCHEMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schemas"))
_cache = {}

def validate_payload(schema_name, payload):
    path = os.path.join(SCHEMA_DIR, schema_name)
    if schema_name not in _cache:
        with open(path, "r", encoding="utf-8") as f:
            _cache[schema_name] = Draft202012Validator(json.load(f))
    v = _cache[schema_name]
    errs = list(v.iter_errors(payload))
    if errs:
        msgs = [f"{'/'.join(map(str,e.path))}: {e.message}" for e in errs]
        raise ValueError(f"{schema_name} validation failed: " + "; ".join(msgs))
    return True
