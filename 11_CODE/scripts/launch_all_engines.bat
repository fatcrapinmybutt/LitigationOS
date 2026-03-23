@echo off
echo LitigationOS ENGINE PACK Launcher
python RUNNERS\run_temporal_memory_engine.py
python RUNNERS\run_lexnlp_enrichment_engine.py
python RUNNERS\run_rag_contrast_validator.py
pause
