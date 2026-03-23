<#
rclone_export.ps1 (template)
Copies a folder (or zip) to your own storage using rclone.
Edit REMOTE and DEST as needed.
#>
param(
  [Parameter(Mandatory=$true)][string]$Source,
  [string]$Remote="gdrive",
  [string]$Dest="gdrive:/LITIGATION_INTAKE/EXPORTS/"
)
Write-Host "Exporting $Source to $Dest via $Remote"
rclone copy "$Source" "$Dest" --progress --transfers 4 --checkers 8 --create-empty-src-dirs
