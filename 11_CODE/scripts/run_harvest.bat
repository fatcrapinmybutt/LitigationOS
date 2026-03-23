@echo off
set OUT=%USERPROFILE%\Downloads\LitigationOS_OUT
python tools\litigationosctl.py doctor
python tools\litigationosctl.py harvest --auto-roots --out-dir "%OUT%" --unzip --bin-probe --carve-embedded --fastsig --page-pinpoints --authority-triples --audit-signals --exact-dup --near-dup --lsh-threshold 0.85 --materialize-dupes copy
echo Done. Output: %OUT%
