param([string]$Root)

$ErrorActionPreference="Stop"
if (!$Root) { $Root = (Get-Location).Path }

# Check if already reachable
try {
  $resp = Invoke-RestMethod -Uri "http://127.0.0.1:6333/" -Method Get -TimeoutSec 2
  return
} catch { }

# Start container (detached)
$storage = Join-Path $Root ".work\qdrant_storage"
New-Item -ItemType Directory -Force -Path $storage | Out-Null

# Windows-friendly: use named volume if bind mount fails
$containerName = "litigationos_qdrant"
$exists = docker ps -a --format "{{.Names}}" | Select-String -SimpleMatch $containerName
if ($exists) {
  docker start $containerName | Out-Null
  return
}

# Try bind mount first
try {
  docker run -d --name $containerName -p 6333:6333 -p 6334:6334 -v "${storage}:/qdrant/storage" qdrant/qdrant | Out-Null
} catch {
  # fallback to named volume
  docker volume create litigationos_qdrant_storage | Out-Null
  docker run -d --name $containerName -p 6333:6333 -p 6334:6334 -v "litigationos_qdrant_storage:/qdrant/storage" qdrant/qdrant | Out-Null
}
