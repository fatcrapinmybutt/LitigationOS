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
if (-not (Test-Path $repoDir)) { throw "Capstone repo not found at $repoDir." }

Push-Location $repoDir
try {
  Docker-Compose -Args @("exec","web","bash","-lc","fab run")
} finally {
  Pop-Location
}
