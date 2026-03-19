# Gotchas — Timeline Forensics

## Anti-Rationalization Matrix

| Trap | What It Looks Like | Why It's Wrong | Correct Approach |
|------|-------------------|----------------|------------------|
| Relying on memory instead of documents | Constructing timeline based on party recollections without corroborating records | Memory is unreliable; courts require documentary evidence; opposing party will exploit inconsistencies | Build timeline exclusively from dated documents (texts, emails, records, photos with EXIF data), then fill gaps with testimony |
| Ignoring metadata | Using document content but not examining file metadata (creation dates, modification dates, EXIF data) | Metadata can prove or disprove the claimed timeline of events; may reveal document fabrication or alteration | Extract and preserve metadata from all digital evidence; use metadata to corroborate or impeach claimed dates |
| Cherry-picking favorable dates | Including only events that support your narrative and omitting unfavorable ones | Opposing counsel will identify gaps and present the omitted events; selective timelines destroy credibility | Include ALL significant events, even unfavorable ones; address unfavorable events with context and explanation |
| Single-source timelines | Building entire timeline from one type of evidence (e.g., only text messages) | Single-source timelines miss events documented elsewhere; multi-source corroboration is far more persuasive | Cross-reference multiple sources: court records, phone records, financial records, social media, witness accounts |
| Not authenticating timeline evidence | Presenting timeline exhibits without establishing the foundation for each underlying document | MRE 901 requires authentication; undocumented or unauthenticated timeline entries may be excluded at trial | Prepare authentication for each timeline entry: who created it, when, chain of custody, reliability of the source |

## Failure Modes
1. **Timeline Contradiction Exposed**: Opposing party identifies internal contradictions in your timeline. Recovery: Audit the entire timeline for consistency before filing; cross-reference every entry against independent records; correct errors proactively.
2. **Metadata Tampering Allegation**: Opposing party claims your digital evidence has been altered. Recovery: Preserve original files with hash values (SHA-256); maintain chain of custody documentation; consider forensic examiner testimony if challenged.
3. **Hearsay Objection to Timeline Entries**: Court sustains hearsay objection to entries based on third-party statements. Recovery: Identify the evidentiary basis for each entry (business record, party admission, present sense impression); prepare alternative foundations.
4. **Spoliation Allegation**: Gap in timeline raises suspicion that evidence was destroyed. Recovery: Document preservation efforts from the beginning of litigation; explain any gaps with evidence of non-existence rather than destruction.

## Integration Gotchas
- When combining with **litigation-parental-alienation-detector**, the timeline IS the core evidence — build a parallel timeline showing: (1) alienating behaviors, (2) parenting time denials, (3) child behavioral changes, correlated by date.
- Data flow TO **litigation-motion-practice**: Timeline exhibits must be formatted for court submission — use clear date columns, source citations, and exhibit references for every entry.
- Michigan-specific pitfall: In the 14th Circuit Family Division, judges expect timelines to be concise and focused. A 50-page timeline covering every minor event will not be read. Create both a detailed working timeline (for preparation) and a court-ready summary timeline (key events only, 2-5 pages).
