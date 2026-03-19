# .gitignore - ALFIS System (Balanced/Open Profile)
@"
# System and temporary files
*.tmp
*.bak
*.log
*.lock
*.DS_Store
Thumbs.db
ehthumbs.db
desktop.ini

# Redundant local browser and editor junk
*.crdownload
*.swp
*.~lock.*
*.pyc
*.pyo
*.db-wal
*.db-shm

# Heavy binaries not required in Git
*.exe
*.msi
*.dll
*.7z
*.rar
*.iso
*.img

# Raw video and audio
*.mp4
*.mp3
*.wav
*.avi
*.mov
*.flac
*.webm
*.mkv
*.ogg

# Auto-generated archive files (retain manually approved only)
*.zip
*.tar.gz
*.tgz
*.gz
*.xz
*.bz2

# IDE and development junk
.vscode/
.idea/
*.suo
*.user
*.sln.docstates

# ALFIS project queue folders
_GIT_IGNORE_QUEUE/
_LARGE_FILES_ZIPPED/
__pycache__/
node_modules/
"@ | Set-Content "$stagingRoot\.gitignore"

# GitHub push with dry run preview
$githubRepoURL = "https://$Env:GITHUB_PAT@github.com/fatcrapinmybutt/fredprime-legal-system.git"
if (-not (Test-Path "$stagingRoot\.git")) {
    Push-Location $stagingRoot
    git init
    git branch -m main
    git remote add origin $githubRepoURL
    Pop-Location
}

Push-Location $stagingRoot
Write-Host "📋 Staged Files (Dry Run):"
git status
Write-Host "`n🧪 Preview of next commit (simulated):"
git diff --cached --stat

git pull origin main --rebase
git add .
git commit -m "🚀 Sync full ALFIS, FRED, GODMODCOMPLEX systems"
git push -u origin main
Pop-Location

$stagingRoot = "F:\_Git_Staging"
$aiCachePath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE\label_training.json"
$refinementLogPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\reclassification_audit.json"
$priorityAuditPath = "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\dashboard_priority_flags_flat.json"

$requiredDirs = @(
    "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS",
    "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE"
)
foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

$aiCache = @{}
if (Test-Path $aiCachePath) {
    $json = Get-Content $aiCachePath -Raw | ConvertFrom-Json
    foreach ($item in $json) {
        $key = "$($item.fileName)|$($item.extension)"
        $aiCache[$key] = $item.label
    }
}

$statuteMap = @{
    'appclose_log'           = 'MCL 722.27a, FOC Handbook §2.13'
    'custody_motion'         = 'MCL 722.23, MCR 3.211(C)'
    'police_report'          = 'MCL 600.2950, MCR 3.706'
    'foc_filing'             = 'MCL 552.511b, MCR 3.224'
    'benchbook_procedure'    = 'MCR 3.200–3.230'
    'statutory_reference'    = 'MCL Index Crosslink'
    'court_rule_reference'   = 'MCR Index Crosslink'
    'alienation_video'       = 'MCL 722.23(c), Parental Alienation Benchbook'
    'opposing_party_emily'   = 'MCR 1.109(E)(5), MCL 600.2950(26)(b)'
    'ppo_case'               = 'MCL 600.2950, PPO Enforcement Manual'
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

$reclassificationAudit = @()
$priorityDashboard = @()

function Rename-AndClassifyFile($filePath) {
    $file = Get-Item $filePath
    $ext = $file.Extension.ToLower().TrimStart('.')
    $name = $file.BaseName.ToLower()
    $destinationRoot = "$stagingRoot\01_CLASSIFIED"

    $aiKey = "$($file.BaseName)|$ext"
    $aiLabel = if ($aiCache.ContainsKey($aiKey)) { $aiCache[$aiKey] } else { $null }

    $regexLabel = switch -Regex ($name) {
        'pp[o|f]' { 'ppo_case' }
        'emily|watson' { 'opposing_party_emily' }
        'custody|motion|modification' { 'custody_motion' }
        'appclose|co-parent' { 'appclose_log' }
        'benchbook|rule' { 'benchbook_procedure' }
        'foc|form|foc10' { 'foc_filing' }
        'report|officer|police|welfare|check' { 'police_report' }
        'alienation|video|mp4|vod' { 'alienation_video' }
        'statute|mcl|mcr' { 'statutory_reference' }
        default { 'unclassified' }
    }

    $label = if ($aiLabel) { $aiLabel } else { $regexLabel }

    if ($aiLabel -and ($aiLabel -ne $regexLabel)) {
        $reclassificationAudit += [PSCustomObject]@{
            File = $file.Name
            OriginalLabel = $regexLabel
            ReclassifiedAs = $aiLabel
            Timestamp = (Get-Date).ToString("s")
        }
        $priorityDashboard += [PSCustomObject]@{
            File = $file.Name
            Priority = "HIGH"
            Reason = "Label conflict detected between AI and Regex"
            Timestamp = (Get-Date).ToString("s")
        }
    }

    $aiCache[$aiKey] = $label

    $subDir = Join-Path $destinationRoot $label
    if (-not (Test-Path $subDir)) {
        New-Item -ItemType Directory -Force -Path $subDir | Out-Null
    }

    $timestamp = Get-Date -Format yyyyMMdd_HHmmss
    $newName = "${label}_$timestamp$($file.Extension)"
    $destination = Join-Path $subDir $newName
    Compress-Archive -Path $file.FullName -DestinationPath "$destination.zip" -Force
    return [PSCustomObject]@{ File = $file.Name; NewPath = "$destination.zip"; Label = $label }
}

$classifiedLog = @()
Get-ChildItem -Path $stagingRoot -Recurse -File | ForEach-Object {
    $result = Rename-AndClassifyFile $_.FullName
    $classifiedLog += $result

    git add $result.NewPath
    git commit -m "Add $($result.Label): $($result.File)" --allow-empty
}

$aiCache.GetEnumerator() | ForEach-Object {
    [PSCustomObject]@{
        fileName = ($_.Key -split '\|')[0]
        extension = ($_.Key -split '\|')[1]
        label = $_.Value
    }
} | ConvertTo-Json -Depth 5 | Set-Content $aiCachePath

$classifiedLog | ConvertTo-Json -Depth 5 | Set-Content "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\classified_log.json"
$reclassificationAudit | ConvertTo-Json -Depth 5 | Set-Content $refinementLogPath
$priorityDashboard | ConvertTo-Json -Depth 5 | Set-Content $priorityAuditPath

$stopwatch.Stop()

foreach ($label in $statuteMap.Keys) {
    $pathCheck = Join-Path $stagingRoot "*\$label*"
    if (Test-Path $pathCheck) {
        git add $pathCheck
        git commit -m "Update $label directory contents"
    }
}

$statuteOutput = @()
foreach ($entry in $statuteMap.GetEnumerator()) {
    $statuteOutput += [PSCustomObject]@{
        Label = $entry.Key
        Statutes = $entry.Value
    }
}
$statuteOutput | ConvertTo-Json -Depth 5 | Set-Content "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS\statute_routing_reference.json"
