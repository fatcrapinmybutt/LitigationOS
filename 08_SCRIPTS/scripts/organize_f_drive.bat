@echo off
setlocal EnableDelayedExpansion

:: === CONFIGURATION ===
set "ROOT=F:\"
set "TARGET=%ROOT%Organized"
set "LOG=%TARGET%\Organize_Log.csv"

:: === PREPARE TARGET FOLDERS ===
for %%C in (WordDocs PDFs Spreadsheets Images Exhibits Scripts Audio Video Archives Evidence_Index Other Versions Quarantine) do (
    if not exist "%TARGET%\%%C" mkdir "%TARGET%\%%C"
)

:: === INIT LOG ===
echo OriginalPath,Category,NewPath,SHA256,Size,LastModified,ParentFolder,VersionGroup,MatchedExhibit,BinderEligible,CloudSyncReady > "%LOG%"

:: === PROCESS ALL FILES RECURSIVELY ===
for /R "%ROOT%" %%F in (*) do (
    set "full=%%~fF"
    set "ext=%%~xF"
    set "name=%%~nF"
    set "category=Other"
    set "parent=%%~dpF"
    set "renamed=!name:~lock.=!"
    set "renamed=!renamed:#=!"
    set "renamed=!renamed:_= !"
    set "clean=!renamed!"

    :: === CATEGORY BY EXTENSION ===
    if /I "!ext!"==".docx"  set "category=WordDocs"
    if /I "!ext!"==".doc"   set "category=WordDocs"
    if /I "!ext!"==".rtf"   set "category=WordDocs"
    if /I "!ext!"==".pdf"   set "category=PDFs"
    if /I "!ext!"==".xlsx"  set "category=Spreadsheets"
    if /I "!ext!"==".csv"   set "category=Spreadsheets"
    if /I "!ext!"==".jpg"   set "category=Images"
    if /I "!ext!"==".jpeg"  set "category=Images"
    if /I "!ext!"==".png"   set "category=Images"
    if /I "!ext!"==".gif"   set "category=Images"
    if /I "!ext!"==".bmp"   set "category=Images"
    if /I "!ext!"==".bat"   set "category=Scripts"
    if /I "!ext!"==".ps1"   set "category=Scripts"
    if /I "!ext!"==".py"    set "category=Scripts"
    if /I "!ext!"==".mp3"   set "category=Audio"
    if /I "!ext!"==".wav"   set "category=Audio"
    if /I "!ext!"==".m4a"   set "category=Audio"
    if /I "!ext!"==".mp4"   set "category=Video"
    if /I "!ext!"==".mov"   set "category=Video"
    if /I "!ext!"==".avi"   set "category=Video"
    if /I "!ext!"==".zip"   set "category=Archives"
    if /I "!ext!"==".rar"   set "category=Archives"
    if /I "!ext!"==".7z"    set "category=Archives"

    :: === KEYWORD OVERRIDES ===
    echo !clean! | findstr /I "exhibit" >nul && set "category=Exhibits"
    echo !clean! | findstr /I "evidence policereport appclose lincoln emily" >nul && set "category=Evidence_Index"

    :: === FLAGS & PROPERTIES ===
    set "matched=No"
    set "binder=No"
    set "cloud=No"
    set "version="

    echo !clean! | findstr /I "exhibit [a-z]" >nul && set "matched=Yes"
    if /I "!ext!"==".pdf" if "!category!"=="Exhibits" set "binder=Yes"
    if "!category!"=="PDFs"  set "cloud=Yes"
    if "!category!"=="Exhibits"  set "cloud=Yes"
    if "!category!"=="Evidence_Index"  set "cloud=Yes"

    :: === VERSION DETECTION ===
    echo !clean! | findstr /I "v1 v2 final draft copy" >nul && set "version=!clean!"

    :: === HASHING ===
    for /f %%H in ('powershell -Command "Get-FileHash -Algorithm SHA256 -Path '%%~fF' | Select -ExpandProperty Hash"') do (
        set "hash=%%H"
    )

    :: === TARGET PATH ===
    set "dest=%TARGET%\!category!\!clean!!ext!"

    if not exist "!dest!" (
        move "%%~fF" "!dest!" >nul 2>&1
        for %%S in ("!dest!") do (
            set "size=%%~zS"
            set "mod=%%~tS"
        )
        echo "%%~fF",!category!,"!dest!",!hash!,!size!,!mod!,"!parent!",!version!,!matched!,!binder!,!cloud! >> "%LOG%"
    ) else (
        echo Skipped duplicate: %%~fF
    )
)

echo.
echo ✅ ORGANIZATION COMPLETE. CHAIN OF CUSTODY LOG:
echo    %LOG%
pause
