# Audit Notes (v1.0.0)

- IDs deterministic: stable sha1 short
- All nodes carry :Entity
- Core CSVs bounded size; heavy props moved to node_props.jsonl.gz
- Edge endpoints validated: no missing from/to
- Embedded PDF text extracted; OCR is optional/fail-soft (requires pillow+pytesseract+tesseract.exe)
- Authority resolution: exact match from AuthorityCiteStub citation -> Authority name/label (optional flag)
