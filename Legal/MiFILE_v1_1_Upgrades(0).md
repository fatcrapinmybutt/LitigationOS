# MiFILE v1.1 Upgrades

- **Visible Bates/Exhibit stamps** if `reportlab` + `PyPDF2` are installed.
- **SCAO Autofill (FDF)** for MC 01, MC 12, FOC 65, FOC 88 (place PDFs in `backend/templates/scao_forms/`; use `pdftk` to flatten).
- **Compliance Validator**: presence checks and signature hint.

To finalize SCAO fills:
```
pdftk MC01.pdf fill_form MC01_fields.fdf output MC01_filled.pdf flatten
```
