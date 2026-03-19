from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import blake2b
from datetime import datetime
from typing import Iterable

@dataclass(frozen=True)
class CycleSeed:
    directive_name: str
    cycle_index: int
    delta_level: int
    lane_scope: tuple[str, ...] = ()

def make_cycle_id(seed: CycleSeed) -> str:
    lane_part = ",".join(sorted(seed.lane_scope))
    raw = f"{seed.directive_name}|{seed.cycle_index}|{seed.delta_level}|{lane_part}"
    digest = blake2b(raw.encode("utf-8"), digest_size=10).hexdigest().upper()
    return f"CYCLE-{seed.delta_level:02d}-{seed.cycle_index:04d}-{digest}"

def make_cycle_record(seed: CycleSeed) -> dict:
    cycle_id = make_cycle_id(seed)
    return {
        "directive_name": seed.directive_name,
        "cycle_index": seed.cycle_index,
        "delta_level": seed.delta_level,
        "lane_scope": list(seed.lane_scope),
        "cycle_id": cycle_id,
        "generated_at_iso": datetime.now().isoformat(timespec="seconds")
    }

if __name__ == "__main__":
    demo = CycleSeed(
        directive_name="EVENTHORIZON_CMDCTR_EXECUTOR_v2_2026-02-22",
        cycle_index=7,
        delta_level=7,
        lane_scope=("MEEK1","MEEK2","MEEK3","MEEK4")
    )
    print(make_cycle_record(demo))
