@echo off
set OUTDIR=out\neo4j_export
set COE=out\COE.csv
set ASL=out\ASL.csv
set NSC=out\NSC_timeline.csv
set FCC=out\FCC_flags.json
set VM=out\VM.json
set REB=out\REBUTTAL_PACK.csv
python tools\neo4j\litigos_to_neo4j.py emit-csv --out_dir %OUTDIR% --coe %COE% --asl %ASL% --nsc %NSC% --fcc %FCC% --vm %VM% --rebuttal %REB%
echo Done. See docs\NEO4J_RUNBOOK.md
