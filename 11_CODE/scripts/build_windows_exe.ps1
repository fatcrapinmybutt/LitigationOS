\
    # Build MBP_TRUEMASTER.exe on Windows using PyInstaller.
    # Usage (PowerShell):
    #   .\build_windows_exe.ps1
    Set-StrictMode -Version Latest
    $ErrorActionPreference = "Stop"

    if (!(Test-Path ".\.venv")) {
        py -m venv .venv
    }
    .\.venv\Scripts\Activate.ps1
    python -m pip install -U pip
    python -m pip install -r requirements-core.txt
    python -m pip install pyinstaller

    # Windowed, single-file build
    pyinstaller --noconsole --onefile -n MBP_TRUEMASTER mbp_truemaster_gui_entry.py
    Write-Host "Built: .\dist\MBP_TRUEMASTER.exe"
