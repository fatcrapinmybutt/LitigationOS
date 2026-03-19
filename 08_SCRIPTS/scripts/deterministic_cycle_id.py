from __future__ import annotations
from pathlib import Path
import zlib
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

def build_cycle_id(delta_level: int = 10) -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    seed = f"{ROOT.name}|{stamp}|{delta_level}"
    crc = zlib.crc32(seed.encode("utf-8")) & 0xFFFFFFFF
    return f"CYCLE-{delta_level:02d}-{stamp}-{crc:08X}"

if __name__ == "__main__":
    print(build_cycle_id())
