# CLEAN LEGAL CLASSIFIER (.ps1)

$benchbookScanRoot = "F:\"
$benchbookTargetDir = "F:\Benchbook_Project"
$stagingRoot = "F:\_Git_Staging"
$pdftotextExe = '"C:\Program Files\Glyph & Cog\XpdfReader-win64\pdftotext.exe"'

$matrixOutput = "$benchbookTargetDir\benchbook_matrix.json"
$statuteMapOutput = "$benchbookTargetDir\statute_map.json"

$requiredDirs = @(
  $benchbookTargetDir,
  "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\AI_CACHE",
  "$stagingRoot\00_SYSTEM_CORE\CENTRAL_DASHBOARD\METRICS",
  "$stagingRoot\01_CLASSIFIED"
)
foreach ($dir in $requiredDirs) {
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}

Write-Host "`n🔍 OCRing first page of all PDFs on F:\..."
Get-ChildItem -Path $benchbookScanRoot -Recurse -Filter *.pdf | ForEach-Object {
  $pdfPath = $_.FullName
  $ocrTxtPath = "$benchbookTargetDir\$($_.BaseName).txt"
  $cmd = "$pdftotextExe -f 1 -l 1 `"$pdfPath`" `"$ocrTxtPath`""
  try { Invoke-Expression $cmd } catch { Write-Warning "OCR failed for $($_.Name)" }
}

$benchbookMatrix = @{}
Get-ChildItem -Path $benchbookTargetDir -Filter *.txt | ForEach-Object {
  $content = Get-Content $_.FullName -Raw
  $matches = Select-String -InputObject $content -Pattern 'MCL\s\d+\.\d+[a-z]*|\bMCR\s\d+\.\d+[a-z]*' -AllMatches
  if ($matches.Matches.Count -gt 0) {
    $label = ($_.BaseName).ToLower() -replace '[^a-z0-9]', '_'
    if (-not $benchbookMatrix.ContainsKey($label)) { $benchbookMatrix[$label] = @() }
    foreach ($match in $matches.Matches) {
      $ref = $match.Value.Trim()
      if ($benchbookMatrix[$label] -notcontains $ref) { $benchbookMatrix[$label] += $ref }
    }
  }
}
$benchbookMatrix | ConvertTo-Json -Depth 5 | Set-Content $matrixOutput

$labelStatuteMap = @{}
foreach ($entry in $benchbookMatrix.GetEnumerator()) {
  $label = $entry.Key
  $statutes = $entry.Value
  foreach ($statute in $statutes) {
    $shortLabel = switch -Regex ($label) {
      'custody' { 'custody_motion' }
      'alienation' { 'alienation_video' }
      'police|report' { 'police_report' }
      'benchbook' { 'benchbook_procedure' }
      'foc|form' { 'foc_filing' }
      'appclose|parent' { 'appclose_log' }
      'pp[o|f]' { 'ppo_case' }
      default { 'misc_procedure' }
    }
    if (-not $labelStatuteMap.ContainsKey($shortLabel)) { $labelStatuteMap[$shortLabel] = @() }
    if ($labelStatuteMap[$shortLabel] -notcontains $statute) { $labelStatuteMap[$shortLabel] += $statute }
  }
}
$labelStatuteMap | ConvertTo-Json -Depth 5 | Set-Content $statuteMapOutput

Write-Host "`n✅ Finished OCR, classification routing built successfully."
