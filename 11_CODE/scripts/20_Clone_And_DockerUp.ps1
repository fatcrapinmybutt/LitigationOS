param(
  [Parameter(Mandatory=$true)][string]$BaseDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Require-Cmd($name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "Required command not found in PATH: $name" }
}

function Docker-Compose {
  param([string[]]$Args)
  try {
    & docker compose @Args
    return
  } catch {
    # fallback to legacy docker-compose
  }
  & docker-compose @Args
}

Require-Cmd git
Require-Cmd docker

$srcDir = Join-Path $BaseDir "src"
$repoDir = Join-Path $srcDir "capstone"
New-Item -ItemType Directory -Force -Path $srcDir | Out-Null

if (-not (Test-Path $repoDir)) {
  Write-Host "Cloning Capstone repo to $repoDir"
  git clone https://github.com/harvard-lil/capstone $repoDir
} else {
  Write-Host "Repo already exists. Attempting to update (safe if archived)."
  Push-Location $repoDir
  try {
    git fetch --all
    git pull
  } finally {
    Pop-Location
  }
}

# Ensure docker is working
try {
  docker info | Out-Null
} catch {
  throw "Docker is not responding. Start Docker Desktop and retry."
}

Push-Location $repoDir
try {
  Write-Host "Docker compose pull (first attempt)"
  try { Docker-Compose -Args @("pull") } catch { Write-Host "Pull failed (attempt 1): $($_.Exception.Message)"; throw }
  Write-Host "Docker compose up -d"
  Docker-Compose -Args @("up","-d")
} finally {
  Pop-Location
}

Write-Host "Docker stack is up."
