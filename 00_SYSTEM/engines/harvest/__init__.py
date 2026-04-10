"""Harvest Engine — Permanent, zero-API evidence ingestion pipeline.

Scans drives for PDF/DOCX/TXT/CSV/JSON/ZIP/DB files, extracts text,
classifies by litigation lane (MEEK), analyzes for actors/dates/authorities,
and persists to litigation_context.db multi-table.

CLI: python harvest.py --drive G: --mode deep
"""
__version__ = "1.0.0"
__engine__ = "harvest"
