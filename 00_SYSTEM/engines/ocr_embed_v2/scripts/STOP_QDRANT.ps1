$ErrorActionPreference="Stop"
$containerName = "litigationos_qdrant"
try {
  $exists = docker ps -a --format "{{.Names}}" | Select-String -SimpleMatch $containerName
  if ($exists) {
    docker stop $containerName | Out-Null
    Write-Host "Stopped $containerName" -ForegroundColor Green
  } else {
    Write-Host "Container not found." -ForegroundColor Yellow
  }
} catch {
  Write-Host "Docker not found." -ForegroundColor Yellow
}
