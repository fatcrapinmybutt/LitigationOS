# Evidence & Chronology Lane — 12 Agents

## Evidence Intake (7 agents)

### AGENT:EVID_INTAKE
- **Role**: Detect new files, classify by type, assign EvidenceAtom IDs
- **Outputs**: EvidenceAtom records with classification + IDs

### AGENT:OCR_FALLBACK
- **Role**: Apply OCR pipeline to worst-case scans
- **Outputs**: Quote-safe excerpts with confidence scores

### AGENT:QUOTE_DB
- **Role**: Build QuoteDB: (doc, page, para/line, quote, checksum)
- **Outputs**: QuoteDB entries with provenance chain

### AGENT:EXHIBIT_BUILDER
- **Role**: Create cover pages (Plaintiff yellow / Defendant blue), exhibit lists, binders
- **Outputs**: Formatted exhibit packages

### AGENT:CHAIN_OF_CUSTODY
- **Role**: Track provenance + hashing + change log
- **Outputs**: Chain-of-custody records with SHA-256 hashes

### AGENT:HEARSAY_MAPPER
- **Role**: Flag hearsay risks + exceptions + MRE hooks
- **Outputs**: Hearsay analysis: `{statement, rule, exception, admissible}`

### AGENT:TRANSCRIPT_ATTACK
- **Role**: Discrepancy locator: transcript vs order vs docket
- **Outputs**: Discrepancy reports with page/line references

## Chronology & Contradictions (5 agents)

### AGENT:TIMELINE_BUILDER
- **Role**: Event ingestion + bi-temporal modeling
- **Outputs**: Timeline entries: `{event, date_actual, date_recorded, source}`

### AGENT:DEADLINE_ENGINE
- **Role**: Compute deadlines from orders/rules + alerts
- **Outputs**: Deadline records with MCR basis + alert thresholds

### AGENT:CONTRADICTION_SCANNER
- **Role**: Statement vs record conflict grids
- **Outputs**: ContradictionMap: `{claim_A, source_A, claim_B, source_B, conflict_type}`

### AGENT:PATTERN_ENGINE
- **Role**: Recurring conduct narratives, grouped by actor & timeframe
- **Outputs**: Pattern reports: `{actor, pattern, instances, timeframe}`

### AGENT:HARM_MAP
- **Role**: Harm to causation to relief mapping
- **Outputs**: Harm chain: `{harm, causation, evidence, relief, damages}`
