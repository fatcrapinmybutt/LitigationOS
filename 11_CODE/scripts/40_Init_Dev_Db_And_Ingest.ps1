param(
  [Parameter(Mandatory=$true)][string]$BaseDir,
  [switch]$SkipHeavy = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Docker-Compose {
  param([string[]]$Args)
  try { & docker compose @Args; return } catch {}
  & docker-compose @Args
}

function Exec-Web($cmd) {
  Docker-Compose -Args @("exec","-T","web","bash","-lc",$cmd)
}

$repoDir = Join-Path (Join-Path $BaseDir "src") "capstone"
if (-not (Test-Path $repoDir)) { throw "Capstone repo not found at $repoDir. Run 20_Clone_And_DockerUp.ps1 first." }

Push-Location $repoDir
try {
  Write-Host "Running fab init_dev_db"
  Exec-Web "fab init_dev_db"

  Write-Host "Running fab ingest_fixtures"
  Exec-Web "fab ingest_fixtures"

  if (-not $SkipHeavy) {
    Write-Host "Running fab import_web_volumes (downloads fixtures)"
    Exec-Web "fab import_web_volumes"

    Write-Host "Running fab refresh_case_body_cache"
    Exec-Web "fab refresh_case_body_cache"

    Write-Host "Running fab rebuild_search_index (attempt 1)"
    try {
      Exec-Web "fab rebuild_search_index"
    } catch {
      Write-Host "rebuild_search_index failed (attempt 1): $($_.Exception.Message)"
      Write-Host "Retrying rebuild_search_index (attempt 2)"
      Exec-Web "fab rebuild_search_index"
    }

    Write-Host "Ensuring ngrams directory exists and running fab ngram_jurisdictions"
    Exec-Web "mkdir -p test_data/ngrams && fab ngram_jurisdictions"
  } else {
    Write-Host "SkipHeavy is set; skipping import_web_volumes / refresh_case_body_cache / rebuild_search_index / ngram_jurisdictions."
  }

} finally {
  Pop-Location
}

Write-Host "Init/ingest step complete."
