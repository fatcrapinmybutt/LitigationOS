# Cascading Planes v2 - Unified Vault Folder Structure (FormOS)

Vault/
  00_OBJECTS/                          # CAS blobs by sha256
    ab/<sha256>.<ext>
  05_ZIP_STAGING/                      # exploded zips (optional; can be deleted after ingest)
  10_FORMS/<jur>/<level>/<family>/<code>/<rev_or_hash>/
    source/
      form.pdf
      inst.pdf (optional)
    extracted/
      pages/p0001.txt ...
      fulltext.txt
      ocr/fulltext.txt (optional)
    derived/
      instructions_fulltext.txt
      instructions_spans.json
      requirements.json
      compliance_profile.json
      fields.json
      akn/template.xml
      stack_manifest.json
  20_EVIDENCE/
  30_ORDERS_TRANSCRIPTS/
  40_FILINGS_OUTPUT/<case_id>/<form_code_or_id>/
    lead/
    attachments/
    service/
    exhibits/
    manifest.json
  90_REPORTS/
    coverage_v2.json
    coverage_v2.md
    missing_tasks.md

Design invariant: bytes live only in 00_OBJECTS; all other files are indexes or derived artifacts.
