# Michigan composition requirements RuleBank (MI)

This file summarizes engineering-grade composition requirements you must enforce when generating or filling Michigan court forms and filings.

## Global baseline (MCR 1.109)
- Filing standards: legible, English, 8½×11, caption structure; 12–13 point body font except SCAO forms.
- Signatures: documents must be signed; electronic signatures accepted.
- Protected PII: redaction + SCAO PII forms when PII must be provided.

## MiFILE “Electronic Document Standards” (Policies & Standards No. 2, rev. 7/17/2020)
Enforce as reject/accept criteria:
- OCR/searchable PDF; direct-to-PDF when filer controls creation.
- Page size 8½×11 view; printable without manipulation.
- Margins: 1" top/bottom; ½" sides; no margin text/images.
- Font: 12–13 pt body (except SCAO forms); ≥10 pt footnotes.
- Spacing: 1.5 or double (except forms/quotes/footnotes); paragraphs numbered where applicable.
- Metadata removed; correct orientation; no blank pages.
- File size ≤25MB; multi-part segments allowed.
- Attachments: Index to Attachments on last page of lead doc; separate attachments; **LT/SP exception**: combine lead+attachments.

## Motions (MCR 2.119)
Validate motion structure: grounds + authority + relief; briefs where required; title specificity.

## Appellate (MiFILE + Subchapters 7.200 / 7.300)
Create appellate doc-types as “forms” and bind their composition requirements (brief content/format, certificates, service).

## Clerk rejection reasons (records management standards)
Encode common reject reasons: formatting, signature missing, outdated SCAO form, wrong confidentiality/seal labels, wrong bundling, missing fee/waiver, etc.

## Per-form binding rule
For each SCAO form version, derive a `ComplianceProfile` from:
1) authority citations on the form
2) instruction PDF requirements (attachments/copies/service)
3) global MiFILE + MCR rules (with SCAO-form exceptions)
