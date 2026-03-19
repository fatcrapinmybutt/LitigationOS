from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schemas.contracts.delta13_service_docket_contracts import (
    ServiceConfidencePayload, ServiceDeficiencyLedger, DocketDeltaSyncPayload,
)


def load(name: str):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


def main() -> int:
    try:
        sc = ServiceConfidencePayload.model_validate(load('service_confidence.json'))
        dl = ServiceDeficiencyLedger.model_validate(load('service_deficiency_ledger.json'))
        ds = DocketDeltaSyncPayload.model_validate(load('docket_delta_sync.json'))
        out = {
            'status': 'ok',
            'service_conf_orders': len(sc.orders),
            'service_deficiency_items': len(dl.items),
            'docket_watch_targets': len(ds.watch_targets),
        }
        print(json.dumps(out, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, indent=2))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
