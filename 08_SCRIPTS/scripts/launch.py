from pathlib import Path
import http.server,socketserver,os,webbrowser,json,datetime
root=Path(__file__).resolve().parents[1]
(root/'manifests'/'cycle_state.json').write_text(json.dumps({'directive_name':'EVENTHORIZON_CMDCTR_DELTA19_UNIFIED_GRAPH','cycle_id':'CYCLE-19-UNIFIEDGRAPH-DEMO','delta_level':19,'convergence_score':0.97,'emergence_score':0.94,'last_launch_utc':datetime.datetime.utcnow().isoformat()+'Z','top_next_actions':['Authority-edge graft for unified graph','Transcript exact quote promotion','Service affidavit field parser']},indent=2),encoding='utf-8')
os.chdir(root/'ui')
with socketserver.TCPServer(('127.0.0.1',8765), http.server.SimpleHTTPRequestHandler) as httpd:
    url='http://127.0.0.1:8765/index.html'; print(url)
    try:webbrowser.open(url)
    except Exception: pass
    httpd.serve_forever()
