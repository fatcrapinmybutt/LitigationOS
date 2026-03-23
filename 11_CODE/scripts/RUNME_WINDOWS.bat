@echo off
setlocal
set "HERE=%~dp0"
cd /d "%HERE%"
set "LITIGATIONOS_HOME=%HERE%"
echo [OK] LITIGATIONOS_HOME=%LITIGATIONOS_HOME%
echo.

echo [1/3] Available macros:
python operator\operator_run.py --list-macros
echo.

echo [2/3] Fast smoke test (tiny sample dataset):
echo   python tests\smoke_test_macro_full_pipeline.py
echo.

echo [3/3] ZIP Frankenstein + Pipeline examples:
echo   ZIP-only (scan drives for *.zip and build a script kit):
echo     python operator\operator_run.py --profile PROFILE_PC_DEFAULT --run-macro MACRO_ZIP_FRANKENSTEIN_ONLY --workspace run --zip-roots F:\ D:\
echo.
echo   ZIP -> Harvest -> Merge -> Query:
echo     python operator\operator_run.py --profile PROFILE_PC_DEFAULT --run-macro MACRO_ZIP_FRANKENSTEIN_FULL_PIPELINE --workspace run --zip-roots F:\ D:\ --query "MCR 2.003"
echo.
echo Done.
endlocal
