<# 
LitigationOS Build: Windows Signing Hook (safe)
- If you have a valid code signing cert installed OR a PFX, this script can sign an .exe.
- If not, it emits an actionable FIXLIST without changing anything.
Usage:
  powershell -ExecutionPolicy Bypass -File BUILD\sign_exe.ps1 -ExePath "dist\LitigationOS.exe" -PfxPath "C:\path\cert.pfx" -PfxPasswordEnv "PFX_PASS"
#>
param(
  [Parameter(Mandatory=$true)][string]$ExePath,
  [string]$PfxPath="",
  [string]$PfxPasswordEnv="PFX_PASS",
  [string]$TimeStampUrl="http://timestamp.digicert.com"
)
function Fail($msg){Write-Host "[FAIL] $msg"; exit 2}
if(!(Test-Path $ExePath)){Fail "ExePath not found: $ExePath"}
$Signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue)?.Source
if(-not $Signtool){Fail "signtool.exe not found. Install Windows SDK or Visual Studio Build Tools."}
if($PfxPath -and !(Test-Path $PfxPath)){Fail "PfxPath not found: $PfxPath"}
if($PfxPath){
  $pass = [Environment]::GetEnvironmentVariable($PfxPasswordEnv)
  if(-not $pass){Fail "Missing env var $PfxPasswordEnv for PFX password."}
  & $Signtool sign /f $PfxPath /p $pass /tr $TimeStampUrl /td sha256 /fd sha256 $ExePath
} else {
  # Attempt to sign using a cert in the store (best-effort)
  & $Signtool sign /a /tr $TimeStampUrl /td sha256 /fd sha256 $ExePath
}
if($LASTEXITCODE -ne 0){Fail "signtool failed with exit code $LASTEXITCODE"}
Write-Host "[OK] Signed: $ExePath"
exit 0
