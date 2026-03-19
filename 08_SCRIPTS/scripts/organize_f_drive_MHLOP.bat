@echo off
setlocal EnableDelayedExpansion

:: === MHLOP: Mandatory High-Level Output Protocol Script ===
:: Fully recursive, hash-safe, PREVIEW-enabled, fail-safe, log-verified

:: === CONFIG ===
set "ROOT=F:\"
set "TARGET=%ROOT%Organized"
set "LOG=%TARGET%\Organize_Log.csv"
set "ERRORLOG=%TARGET%\ErrorLog.csv"
set "MAPPLAN=%TARGET%\MapPlan.csv"

:: Check for PREVIEW mode
if /I "%1"=="PREVIEW" (
    set "PREVIEW=1"
    echo 🟡 PREVIEW MODE ACTIVE – No files will be moved
)

:: Create output folders
for %%C in (WordDocs PDFs Spreadsheets Images Exhibits Scripts Audio Video Archives Evidence_Index Other Versions Quarantine) do (
    if not exist "%TARGET%\%%C" mkdir "%TARGET%\%%C"
)

:: Init logs
echo OriginalPath,Category,NewPath,SHA256,Size,LastModified,ParentFolder,VersionGroup,MatchedExhibit,BinderEligible,CloudSyncReady > "%LOG%"
echo File,Error > "%ERRORLOG%"
echo OriginalPath,PlannedCategory,PlannedNewPath > "%MAPPLAN%"

:: Start processing
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

    :: Determine category
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

    :: Keyword overrides
    echo !clean! | findstr /I "exhibit" >nul && set "category=Exhibits"
    echo !clean! | findstr /I "evidence policereport appclose lincoln emily" >nul && set "category=Evidence_Index"

    :: Flags
    set "matched=No"
    set "binder=No"
    set "cloud=No"
    set "version="

    echo !clean! | findstr /I "exhibit [a-z]" >nul && set "matched=Yes"
    if /I "!ext!"==".pdf" if "!category!"=="Exhibits" set "binder=Yes"
    if "!category!"=="PDFs"  set "cloud=Yes"
    if "!category!"=="Exhibits"  set "cloud=Yes"
    if "!category!"=="Evidence_Index"  set "cloud=Yes"

    echo !clean! | findstr /I "v1 v2 final draft copy" >nul && set "version=!clean!"

    set "dest=%TARGET%\!category!\!clean!!ext!"

    echo !full!,!category!,!dest! >> "%MAPPLAN%"

    :: If PREVIEW, skip moving
    if defined PREVIEW (
        echo [MAP] !full! → !dest!
        goto :continue
    )

    :: Error checks
    if not exist "%%~fF" (
        echo %%~fF,Not found >> "%ERRORLOG%"
        goto :continue
    )

    set "hash="
    for /f %%H in ('powershell -Command "try { Get-FileHash -Algorithm SHA256 -Path '%%~fF' | Select -ExpandProperty Hash } catch { '' }"') do (
        set "hash=%%H"
    )

    if not defined hash (
        echo %%~fF,Hash failed >> "%ERRORLOG%"
        goto :continue
    )

    if not exist "!dest!" (
        move "%%~fF" "!dest!" >nul
        if errorlevel 1 (
            echo %%~fF,Move failed >> "%ERRORLOG%"
            goto :continue
        )
        for %%S in ("!dest!") do (
            set "size=%%~zS"
            set "mod=%%~tS"
        )
        echo "%%~fF",!category!,"!dest!",!hash!,!size!,!mod!,"!parent!",!version!,!matched!,!binder!,!cloud! >> "%LOG%"
    ) else (
        echo %%~fF,Duplicate target exists >> "%ERRORLOG%"
    )

    :continue
)

echo.
echo ✅ COMPLETE. LOG: %LOG%
if defined PREVIEW (
    echo 🟡 PREVIEW MODE: No files were moved.
)
pause
