---
name: local-python-executor
description: "Safe local Python execution for LitigationOS. Wraps safe_shell.py with shadow module protection. Replaces inference.sh python-executor. Triggers: python, execute, run script, safe python, sandbox"
---

# Local Python Executor

Safe Python execution with shadow module protection (22 modules in repo root).

## Safe Execution

```powershell
# Load agent profile
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1

sspy file.py          # Syntax check
srun script.py        # Safe run (avoids shadows)
spy "print(1+1)"      # Safe inline Python
senv                  # Environment check
sshadow               # Shadow module audit
```

## Shadow Modules (NEVER set CWD to repo root)

json.py, typing.py, numpy.py, pandas.py, collections.py, datetime.py, os.py,
pathlib.py, re.py, sqlite3.py, sys.py, time.py, uuid.py, hashlib.py,
logging.py, pickle.py, subprocess.py, threading.py, abc.py, io.py, functools.py

## SDK Integration

```python
import sys
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM")
from sdk import inference, RAGPipeline
from sdk.tool_builder import litigation_tools
```
