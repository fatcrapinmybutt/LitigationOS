# Michigan Court Document Standards — document-forge-supreme

## MCR Formatting Requirements

All filings in Michigan courts must comply with the Michigan Court Rules (MCR). Key rules for document formatting:

### MCR 2.113 — Form of Pleadings (Circuit Court)

```
Caption format (mandatory):
┌─────────────────────────────────────────────────────┐
│ STATE OF MICHIGAN                                    │
│ IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON      │
│ 14th JUDICIAL CIRCUIT                                │
│                                                      │
│ ANDREW JAMES PIGORS,                                │
│        Plaintiff,                    Case No. XXXX   │
│                                      Hon. Jenny L.   │
│ v.                                   McNeill         │
│                                                      │
│ EMILY A. WATSON,                                    │
│        Defendant.                                    │
│ ─────────────────/                                   │
└─────────────────────────────────────────────────────┘

Requirements:
- Names in ALL CAPS in caption
- Case number on right side
- Judge name below case number
- Horizontal rule after defendant name
- "Plaintiff" and "Defendant" labels right-aligned under names
```

### MCR 7.212 — Brief Formatting (Court of Appeals)

```
Page requirements:
- Paper size: 8.5" × 11"
- Margins: minimum 1 inch on all sides
- Line spacing: double-spaced (except quotes and footnotes)
- Font: proportional 12-point (Times New Roman preferred) or monospace 10-point
- Page numbering: bottom center, starting from first page of text

Page limits (MCR 7.212(B)):
- Appellant's brief: 50 pages
- Appellee's brief: 50 pages
- Reply brief: 25 pages
- Application for leave to appeal: 50 pages
- Cross-application: 25 pages

Excluded from page count: table of contents, index of authorities, signature block,
certificate of service, appendix
```

### MCR 2.119 — Motion Practice

```
Required components for any motion:
1. Caption (per MCR 2.113)
2. Title of motion (e.g., "MOTION FOR DISQUALIFICATION")
3. Statement of issues (numbered)
4. Brief in support (can be combined or separate)
5. Proposed order (separate document)
6. Certificate/proof of service

Timing:
- Motion: filed and served at least 9 days before hearing
- Response: at least 5 days before hearing
- Reply: at least 3 days before hearing

Service:
- Per MCR 2.107 — on all parties or their attorneys
- Proof of service must state: method, date, person served, address
```

### MCR 2.107 — Service of Process

```
Acceptable methods:
- Personal delivery
- First-class mail (add 3 days to response time)
- Electronic service (if consented to by receiving party)
- Fax (if consented to)

Proof of service must include:
- Name of person served
- Method of service
- Date of service
- Address served to
- Signature of person making service
```

## Certificate of Service Template

```
CERTIFICATE OF SERVICE

I hereby certify that on [DATE], I served a copy of the foregoing
[DOCUMENT TITLE] upon the following by [METHOD]:

[NAME]
[ADDRESS LINE 1]
[ADDRESS LINE 2]
[CITY, STATE ZIP]

                                    _________________________
                                    Andrew James Pigors
                                    1977 Whitehall Road, Lot 17
                                    North Muskegon, MI 49445
                                    (231) 903-5690
                                    andrewjpigors@gmail.com
                                    In Propria Persona

Dated: [DATE]
```

## Pro Se Signature Block

```
Respectfully submitted,

_________________________
Andrew James Pigors
In Propria Persona
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
Telephone: (231) 903-5690
Email: andrewjpigors@gmail.com

Dated: [DATE]
```

## Muskegon County 14th Circuit Local Rules

Key local requirements beyond MCR:
- E-filing required via TrueFiling (see TrueFiling_User_Guide.pdf)
- Electronic document standards per `electronicdocument_stds.pdf`
- Document rejection standards per `rejection_stds.pdf`
- Specific scheduling order formats for family division

## Child Protection (MCR 8.119(H))

**CRITICAL**: The child's name must NEVER appear in filings. Use initials only: **L.D.W.**
MCR 8.119(H) requires redaction of minor children's names in all court documents accessible to the public.

## SCAO Form Reference

Michigan SCAO publishes mandatory forms for specific filings. Query `court_forms.db`:
```sql
SELECT form_number, form_name, form_type FROM forms WHERE category = 'family';
```

Common forms for Pigors v Watson:
- MC 280 — Motion (general)
- MC 281 — Response to Motion
- MC 282 — Proposed Order
- CC 381 — Proof of Service
- FOC forms — Friend of Court specific filings
