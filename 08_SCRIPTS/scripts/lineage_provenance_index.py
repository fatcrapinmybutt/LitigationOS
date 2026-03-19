from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def _read(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def build_lineage_provenance_index() -> dict:
    lineage = _read(DATA / "desktop_canonical_lineage_map.json", [])
    inventory = _read(DATA / "desktop_corpus_inventory.json", [])
    replay = _read(DATA / "replay_provenance_links.json", {"links": []})

    inv_by_name = {item.get("name"): item for item in inventory if isinstance(item, dict)}
    replay_links = replay if isinstance(replay, list) else replay.get("links", [])

    link_hits_by_name = defaultdict(list)
    for link in replay_links:
        p = link.get("artifact_path", "") or ""
        tail = p.split("/")[-1]
        if tail:
            link_hits_by_name[tail].append({
                "event_id": link.get("event_id"),
                "artifact_path": p,
                "artifact_kind": link.get("artifact_kind"),
                "lane": link.get("lane"),
                "anchor": f"prov-{link.get('event_id','').replace(':','-')}-{abs(hash(p))%10000}"
            })

    groups_out = []
    classes = set()
    exts = set()
    prov_types = set()

    for g in lineage if isinstance(lineage, list) else lineage.get("lineage_groups", []):
        members_out = []
        hits = []
        for m in g.get("members", []):
            name = m.get("name")
            item = inv_by_name.get(name, {})
            ext = (name.rsplit(".", 1)[-1].lower() if "." in (name or "") else "")
            member_class = item.get("class") or m.get("class")
            classes.add(member_class or "unknown")
            if ext:
                exts.add(ext)
            member_hits = link_hits_by_name.get(name, [])
            for h in member_hits:
                prov_types.add(h.get("artifact_kind") or "unknown")
                hits.append({**h, "member_name": name})
            members_out.append({
                "name": name,
                "relation": m.get("relation"),
                "sha256": m.get("sha256"),
                "bytes": m.get("bytes"),
                "class": member_class,
                "modified": m.get("modified"),
                "extension": ext,
                "provenance_hit_count": len(member_hits)
            })
        groups_out.append({
            "lineage_id": g.get("lineage_id"),
            "normalized_stem": g.get("normalized_stem"),
            "canonical_name": g.get("canonical_name"),
            "canonical_sha256": g.get("canonical_sha256"),
            "variant_count": g.get("variant_count"),
            "members": members_out,
            "provenance_hits": hits,
            "provenance_hit_count": len(hits),
            "classes": sorted(set(x.get("class") or "unknown" for x in members_out)),
            "extensions": sorted(set(x.get("extension") for x in members_out if x.get("extension")))
        })

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "group_count": len(groups_out),
            "groups_with_provenance_hits": sum(1 for g in groups_out if g.get("provenance_hit_count")),
            "total_provenance_hits": sum(g.get("provenance_hit_count",0) for g in groups_out)
        },
        "filters": {
            "classes": sorted(c for c in classes if c),
            "extensions": sorted(exts),
            "provenance_kinds": sorted(prov_types)
        },
        "groups": groups_out
    }
    (DATA / "lineage_provenance_index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps(build_lineage_provenance_index(), indent=2))
