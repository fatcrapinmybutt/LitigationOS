from pathlib import Path
import json

def build_graph(data_dir: Path):
    orders=json.loads((data_dir/'orders.json').read_text(encoding='utf-8'))['orders']
    services=json.loads((data_dir/'service_proofs.json').read_text(encoding='utf-8'))['service_proofs']
    quotes=json.loads((data_dir/'transcript_quotes.json').read_text(encoding='utf-8'))['transcript_quotes']
    nodes=[]; edges=[]
    def n(i,k,l,**x): nodes.append({'id':i,'kind':k,'label':l,**x})
    def e(i,s,t,r,**x): edges.append({'edge_id':i,'source':s,'target':t,'relationship':r,**x})
    seen=set()
    for o in orders:
        n(o['order_id'],'order',o['title'],case_id=o['case_id'],entered_date=o['entered_date'],status=o.get('status'))
        for sid in o.get('supersedes',[]): e(f"E-SUP-{o['order_id']}-{sid}",o['order_id'],sid,'SUPERSEDES')
        for sp in o.get('service_proof_ids',[]): e(f"E-SVC-{o['order_id']}-{sp}",o['order_id'],sp,'SERVED_BY')
        for qid in o.get('quote_anchor_ids',[]): e(f"E-Q-{qid}-{o['order_id']}",qid,o['order_id'],'QUOTE_ANCHOR_FOR')
    for s in services:
        n(s['service_id'],'service_proof',f"{s['method']} to {s['served_to']}",served_date=s['served_date'],confidence_band=s.get('confidence_band'),artifact_id=s.get('artifact_id'))
        if s.get('artifact_id'):
            n(s['artifact_id'],'service_artifact',s['artifact_id'],source_class='affidavit_or_notice')
            e(f"E-ART-{s['artifact_id']}-{s['service_id']}",s['artifact_id'],s['service_id'],'EVIDENCES_SERVICE')
    for q in quotes:
        n(q['quote_id'],'quote_anchor',q.get('quote_preview','')[:60],source_id=q.get('source_id'),page=q.get('page'),line_start=q.get('line_start'),line_end=q.get('line_end'),quote_status=q.get('quote_status'))
        src='SRC-'+q['source_id']
        if src not in seen:
            n(src,'record_source',q['source_id'],source_id=q['source_id'])
            seen.add(src)
        e(f"E-QSRC-{q['quote_id']}",src,q['quote_id'],'CONTAINS_QUOTE')
    return {'graph_id':'UNIFIED-OSQ-GRAPH','nodes':nodes,'edges':edges}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    out=root/'data'/'unified_order_service_quote_graph.runtime.json'
    out.write_text(json.dumps(build_graph(root/'data'), indent=2), encoding='utf-8')
    print(f'Wrote {out}')
