param(
  [Parameter(Mandatory=$true)][string]$BaseDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Docker-Compose {
  param([string[]]$Args)
  try { & docker compose @Args; return } catch {}
  & docker-compose @Args
}

$repoDir = Join-Path (Join-Path $BaseDir "src") "capstone"
if (-not (Test-Path $repoDir)) { throw "Capstone repo not found at $repoDir. Run 20_Clone_And_DockerUp.ps1 first." }

Push-Location $repoDir
try {
  $dbs = @("capdb","capapi","cap_user_data")
  foreach ($db in $dbs) {
    Write-Host "Ensuring database exists: $db"
    $sql = "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$db') THEN CREATE DATABASE $db; END IF; END $$;"
    Docker-Compose -Args @("exec","-T","db","psql","--user=postgres","-c",$sql)
  }
} finally {
  Pop-Location
}

Write-Host "Database creation step complete."
