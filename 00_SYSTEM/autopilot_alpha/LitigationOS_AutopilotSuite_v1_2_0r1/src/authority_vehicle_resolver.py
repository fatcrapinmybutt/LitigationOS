\
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import process, fuzz

MCR_RE = re.compile(r"\bMCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*", re.IGNORECASE)
MCL_RE = re.compile(r"\bMCL\s+\d+(?:\.\d+)*[A-Za-z]?(?:\([^)]+\))*", re.IGNORECASE)
MRE_RE = re.compile(r"\bMRE\s+\d+\b", re.IGNORECASE)

def normalize_cite(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" )", ")").replace("( ", "(")
    return s

def extract_citations(text: str) -> List[str]:
    if not text:
        return []
    hits = []
    for rx in (MCR_RE, MCL_RE, MRE_RE):
        hits.extend([normalize_cite(m.group(0)) for m in rx.finditer(text)])
    seen = set()
    out = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out

@dataclass
class AuthorityIndex:
    exact: Dict[str, str]
    space: List[str]
    space_uid: Dict[str, str]

def build_authority_index(authority_records: List[Dict[str, Any]]) -> AuthorityIndex:
    exact: Dict[str, str] = {}
    space: List[str] = []
    space_uid: Dict[str, str] = {}
    for a in authority_records:
        uid = str(a.get("uid") or "").strip()
        name = str(a.get("name") or a.get("citation") or (a.get("props") or {}).get("name") or "").strip()
        citation = str(a.get("citation") or "").strip()
        if not uid:
            continue
        if name:
            n = normalize_cite(name)
            exact.setdefault(n, uid)
            space.append(n); space_uid[n] = uid
        if citation:
            c = normalize_cite(citation)
            exact.setdefault(c, uid)
            space.append(c); space_uid[c] = uid
    space = sorted(set(space))
    return AuthorityIndex(exact=exact, space=space, space_uid=space_uid)

def resolve_citation(index: AuthorityIndex, cite: str, fuzzy_cutoff: int = 90) -> Tuple[Optional[str], Optional[str], str, Optional[int]]:
    c = normalize_cite(cite)
    if c in index.exact:
        return index.exact[c], None, "exact", 100
    if index.space:
        m = process.extractOne(c, index.space, scorer=fuzz.WRatio)
        if m and m[1] >= fuzzy_cutoff:
            uid = index.space_uid.get(m[0])
            return None, uid, "fuzzy", int(m[1])
    return None, None, "unresolved", None

def infer_vehicle_links_from_authority_props(authority_node_props: Dict[str, Any]) -> List[str]:
    keys = ["supports_vehicle", "vehicle_ids", "vehicles", "vehicle_types", "vehicle_type", "vehicle", "relief_vehicle"]
    out: List[str] = []
    for k in keys:
        v = authority_node_props.get(k)
        if not v:
            continue
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out.extend([str(x) for x in v if str(x).strip()])
        elif isinstance(v, dict):
            for vv in v.values():
                out.append(str(vv))
    seen=set(); ret=[]
    for x in out:
        s=str(x).strip()
        if not s or s in seen:
            continue
        seen.add(s); ret.append(s)
    return ret
