# Cascading Planes — Unified Vault Folder Structure (FormOS)

Goal: mostly flat, deduped, deterministic. All “objects” live in a content-addressed store; everything else is an index/copy/link.

Vault/
  00_OBJECTS/                      # content-addressed blobs by SHA-256
    ab/<sha256>.<ext>
  10_FORMS/                         # canonical form placement (symlink/copy to objects)
    <jurisdiction>/<court_level>/<family>/<form_code>/<revision_or_hash>/
      source/
      extracted/pages/
      extracted/fulltext.txt
      derived/requirements.json
      derived/compliance_profile.json
      derived/akn/template.xml
      derived/stack_manifest.json
  20_EVIDENCE/
  30_ORDERS_TRANSCRIPTS/
  40_FILINGS_OUTPUT/<case_id>/<package_id>/...
  90_REPORTS/coverage.json, coverage.md, missing_tasks.md

Dedup rule: bytes live only in 00_OBJECTS keyed by sha256; the rest are indices.
