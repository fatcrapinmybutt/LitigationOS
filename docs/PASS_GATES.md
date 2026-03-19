# PASS Gates (Event Horizon Δ∞)

A run is PASS when all gates below are satisfied.

Coverage Gate
- formsCovered == formsTotal for discovered forms
- (optional) formsCovered == formsExpected if catalogs enabled

OCR Gate
- OCR queue empty or all needs_ocr documents have OCR extraction rows

Requirements Gate
- requirements compiled per form
- requirement satisfaction satisfied==1 for all requirements in the stack

Stack Gate
- stack lint PASS for each stack folder

MiFILE/MCR Gate
- MiFILE lint returns no ERROR for each PDF intended for filing
- deadlines computed/validated when hearing date inputs exist

Export Gate
- CyclePack ZIP produced
- CyclePack manifest produced and verifies hashes
