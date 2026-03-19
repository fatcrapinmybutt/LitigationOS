from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
stats=json.loads((root/'data'/'unified_order_service_quote_graph_stats.json').read_text(encoding='utf-8'))
jumps=json.loads((root/'data'/'lineage_provenance_jump_index.json').read_text(encoding='utf-8'))
(root/'manifests'/'ops_provenance_overlay.json').write_text(json.dumps({'overlay_id':'OPS-PROVENANCE-DELTA19','cycle_id':stats.get('cycle_id'),'jump_count':len(jumps.get('provenance_jumps',[])),'discovery_target_quotes':len(stats.get('graph_health',{}).get('discovery_target_quotes',[]))},indent=2),encoding='utf-8')
print('Wrote ops provenance overlay')
