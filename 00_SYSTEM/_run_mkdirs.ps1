$ErrorActionPreference = 'SilentlyContinue'
$b = 'C:\Users\andre\LitigationOS\00_SYSTEM\autonomos'
$null = [System.IO.Directory]::CreateDirectory("$b\sentinel")
$null = [System.IO.Directory]::CreateDirectory("$b\inquisitor")  
$null = [System.IO.Directory]::CreateDirectory("$b\shared")
$null = [System.IO.Directory]::CreateDirectory("$b\db")
$null = [System.IO.Directory]::CreateDirectory("$b\tests")
[System.IO.File]::WriteAllText("$b\__init__.py", '"""AUTONOMOS - autonomos package."""' + "`n")
[System.IO.File]::WriteAllText("$b\sentinel\__init__.py", '"""AUTONOMOS - sentinel package."""' + "`n")
[System.IO.File]::WriteAllText("$b\inquisitor\__init__.py", '"""AUTONOMOS - inquisitor package."""' + "`n")
[System.IO.File]::WriteAllText("$b\shared\__init__.py", '"""AUTONOMOS - shared package."""' + "`n")
[System.IO.File]::WriteAllText("$b\done.txt", "ALL DONE")
Write-Output "COMPLETE"
