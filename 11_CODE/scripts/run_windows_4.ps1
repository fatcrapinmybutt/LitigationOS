# Run harvester in Windows PowerShell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python forms_harvest.py
