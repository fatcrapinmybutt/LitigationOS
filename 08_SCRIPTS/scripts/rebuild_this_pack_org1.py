from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
out=root.parent/'LITIGATION_COMMAND_CENTER_DELTA19_UNIFIED_GRAPH_APPEND_PACK_20260222.rebuilt.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    [z.write(p,p.relative_to(root)) for p in sorted(root.rglob('*')) if p.is_file()]
with zipfile.ZipFile(out) as z:
    bad=z.testzip(); assert bad is None, bad
print(out)
