---
name: ai-doc-assembly — Smart Document Assembly Pipeline
description: >
  AI-driven assembly of complete filing packages. Auto-selects correct forms,
  pulls relevant exhibits, generates certificates of service, and validates
  completeness. Lane-aware routing with Michigan court form integration.
  Keywords: document assembly, filing package, forms, exhibits, court filing
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Validate assembled package
    agent: ai-filing-guardian
    prompt: Filing package assembled. Run compliance validation before filing.
    send: false
---

# Smart Document Assembly Pipeline

## Overview
Automatically assemble complete filing packages: select the right Michigan court forms, pull relevant exhibits from evidence stores, generate required certificates, and validate completeness — all lane-aware.

## Module Structure
```
00_SYSTEM/ai_modules/doc_assembly/
├── __init__.py
├── form_selector.py        # Select correct Michigan court forms
├── exhibit_selector.py     # AI-driven exhibit selection for the filing
├── certificate_gen.py      # Generate cert of service, verification, etc.
├── package_assembler.py    # Assemble complete filing package
├── completeness_checker.py # Verify all required components present
├── template_filler.py      # Fill form templates with case data
├── lane_router.py          # Route to correct court/division
├── config.py
└── tests/
```

## Package Components
1. **Cover Page** — Court caption, case number, document title
2. **Main Document** — Motion, brief, complaint, etc.
3. **Exhibits** — Selected, Bates-stamped, indexed
4. **Certificate of Service** — Method, parties, dates
5. **Proposed Order** — If required by rule
6. **Filing Fee Info** — Amount, waiver status

## Rules
1. Form selection uses Michigan court form database (MC, DC, CC, COA prefixes)
2. Exhibit selection based on evidence scorer relevance + admissibility scores
3. Certificate of service auto-populated from case party database
4. All packages validated by filing guardian before output
5. Lane routing determines court, division, and form variants
