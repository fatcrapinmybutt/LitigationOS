# JSON Schema validation helpers
import os, json
from jsonschema import Draft202012Validator

SCHEMA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "schemas"))

_validators = {}
def get_validator(name):
    if name in _validators:
        return _validators[name]
    path = os.path.join(SCHEMA_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    v = Draft202012Validator(schema)
    _validators[name] = v
    return v

def validate_payload(schema_name, payload):
    v = get_validator(schema_name)
    errors = sorted(v.iter_errors(payload), key=lambda e: e.path)
    if errors:
        msg = "; ".join([f"{'/'.join(map(str,e.path))}: {e.message}" for e in errors])
        raise ValueError(f"Validation failed for {schema_name}: {msg}")
    return True
