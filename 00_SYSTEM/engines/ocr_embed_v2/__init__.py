"""
OCR Embed v2 — OCR extraction and embedding pipeline (DEPRECATED).

Superseded by the semantic engine (LanceDB + sentence-transformers) and
pypdfium2-based intake pipeline.
DO NOT USE — use intake engine (Go) + semantic engine instead.

Key resources:
    src/        — Core OCR and embedding logic (reference only)
    scripts/    — CLI utilities for batch processing
    config/     — Engine configuration (OCR backend, model selection)
    prompts/    — Prompt templates for LLM-assisted OCR correction
    docs/       — Usage documentation and architecture notes
"""
__deprecated__ = True
__superseded_by__ = "intake (Go) + semantic engine"
