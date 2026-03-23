$ErrorActionPreference="Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$py = "python"
& $py (Join-Path $root "tools\rebuild_masterpack_zip.py")
