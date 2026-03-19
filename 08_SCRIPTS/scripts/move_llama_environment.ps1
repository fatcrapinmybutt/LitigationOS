# === CONFIG ===
$destRoot = "F:\LLAMA"
$cacheDest = "$destRoot\huggingface_cache"
$modelsDest = "$destRoot\models"
$scriptsDest = "$destRoot\scripts"

# === CREATE FOLDERS ===
New-Item -ItemType Directory -Path $cacheDest -Force | Out-Null
New-Item -ItemType Directory -Path $modelsDest -Force | Out-Null
New-Item -ItemType Directory -Path $scriptsDest -Force | Out-Null

Write-Host "`n🔍 Scanning for known Hugging Face + LLaMA folders..."

# === MOVE HUGGINGFACE CACHE ===
$hfSource = "$env:USERPROFILE\.cache\huggingface"
if (Test-Path $hfSource) {
    Write-Host "✅ Moving Hugging Face cache: $hfSource"
    Copy-Item -Path $hfSource -Destination $cacheDest -Recurse -Force
} else {
    Write-Host "❌ Hugging Face cache not found at $hfSource"
}

# === MOVE .gguf or .safetensors MODEL FILES ===
Write-Host "`n🔍 Scanning C:\ for .gguf and .safetensors files..."
Get-ChildItem -Path C:\ -Recurse -Include *.gguf, *.safetensors -ErrorAction SilentlyContinue -File |
    ForEach-Object {
        $dest = Join-Path $modelsDest $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Force
        Write-Host "📦 Copied model file: $($_.FullName)"
    }

# === MOVE PYTHON SCRIPTS (.py, .ipynb) ===
Write-Host "`n🔍 Scanning C:\ for Python scripts..."
Get-ChildItem -Path C:\ -Recurse -Include *.py, *.ipynb -ErrorAction SilentlyContinue -File |
    ForEach-Object {
        $dest = Join-Path $scriptsDest $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Force
        Write-Host "📜 Copied script: $($_.FullName)"
    }

Write-Host "`n✅ Done. Everything is now in: $destRoot"
