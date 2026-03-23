param(
  [Parameter(Mandatory=$true)][string]$InputZip,
  [Parameter(Mandatory=$true)][string]$Canon,
  [string]$WorkDir = "."
)

Set-Location $WorkDir

if (!(Test-Path ".\.venv")) {
  python -m venv .\.venv
}

.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt

.\.venv\Scripts\python cycle_runner.py --input-zip "$InputZip" --canon "$Canon" --state ".\state.json" --config ".\config.yaml"
