# Gotchas — litigation-evidence-harvester

## Anti-Rationalization Table

This table prevents the most dangerous evidence handling errors — mistakes
that can result in evidence exclusion, sanctions, or destroyed credibility
when processing 427,956+ files for Michigan circuit court litigation.

| # | Excuse (Rationalization) | Reality (What Actually Happens) | Consequence |
|---|--------------------------|--------------------------------|-------------|
| 1 | "We can sort the evidence later — let's just collect everything first." | Undifferentiated collection creates an unmanageable haystack. With 427,956+ files, you'll never circle back for proper classification. The volume becomes paralyzing. Critical HIGH evidence is lost among hundreds of thousands of SKIP items. | Key evidence never found. Deadlines missed because the document that proves your point is buried in an unclassified pile. |
| 2 | "OCR is good enough — we don't need to verify the text extraction." | Modern OCR achieves 95–98% accuracy on clean documents. But legal documents with stamps, handwriting, poor copies, and multi-column layouts drop to 60–80%. A single misread date, name, or dollar amount can invalidate evidence or create false leads. | Wrong date extracted → wrong timeline event. Wrong name → wrong witness attributed. Wrong dollar amount → wrong damages claimed. Evidence challenged as unreliable. |
| 3 | "Chain of custody is for physical evidence — digital files don't need it." | MRE 901 authentication applies to electronic evidence equally. Opposing counsel will challenge that digital files are what they claim to be: "How do we know this email is authentic? When was this PDF created? Has it been modified?" Without hash verification and processing logs, you cannot answer. | Evidence excluded under MRE 901 for lack of authentication. Judge finds digital evidence unreliable without chain-of-custody documentation. |
| 4 | "We processed these files before — reprocessing is a waste of time." | Document collections change. Files are added, modified, or corrupted. Prior processing may have used different classification rules or missed files due to format issues. Incremental processing catches changes; assuming prior completeness misses them. | New evidence in modified files missed entirely. Atom database is stale. Filing references evidence that no longer matches the source document. |
| 5 | "All the important evidence is in the court filings — we don't need to scan personal documents." | Critical impeachment evidence often comes from informal sources: text messages, social media, personal notes, emails. In custody cases (Lane A), personal communications frequently contain admissions against interest that formal filings don't. | Missing the text message where Watson admits X. Missing the email where Shady Oaks acknowledges Y. Case-changing evidence never enters the record. |
| 6 | "The classification model is accurate — we can trust HIGH/MED/LOW assignments without review." | Automated classification is a first pass, not final judgment. Legal relevance requires understanding of case theory, which changes. A document classified LOW under one theory may be HIGH under another. Human review of borderline cases is essential. | HIGH evidence misclassified as LOW → never used. LOW evidence misclassified as HIGH → wasted preparation time. Case theory shifts but evidence database doesn't update. |
| 7 | "Privileged documents will be obvious — we'll catch them during processing." | Privilege screening requires active attention. Attorney-client communications may be embedded in larger document chains. Medical records may appear in unexpected contexts. HIPAA-protected information may be in communications not obviously medical. | Privileged material produced to opposing counsel. Potential waiver of attorney-client privilege. HIPAA violation. Sanctions. Court intervention. |
| 8 | "We'll use the scanned documents as-is for exhibits." | Court exhibits require specific formatting: exhibit labels, page numbering, legibility standards. Raw scans may be rotated, cropped poorly, or at insufficient resolution. The 14th Circuit has specific exhibit formatting requirements. | Exhibits rejected by clerk. Judge cannot read key evidence. Opposing counsel objects to illegible exhibits. Evidence functionally excluded. |

## Common Harvesting Failures

### 1. Deduplication Failures
**Symptom**: Same document appears multiple times in evidence database with different classifications.
**Cause**: Near-duplicate detection missed variants (scanned copy vs. native copy, different file names).
**Fix**: Use multi-layer deduplication: exact hash match → fuzzy text match → visual similarity for images.

### 2. OCR Garbage In
**Symptom**: Extracted text is nonsensical or contains systematic errors.
**Cause**: Pre-processing (deskew, denoise) not run on low-quality scans before OCR.
**Fix**: Always run pre-processing pipeline. Flag documents with OCR confidence < 80% for manual review.

### 3. Metadata Loss
**Symptom**: Document dates, authors, or source information missing after processing.
**Cause**: Metadata extraction not performed or not preserved during format conversion.
**Fix**: Extract and preserve file metadata (creation date, modification date, author, source path) at ingestion. Store separately from content.

### 4. Atom Over-Extraction
**Symptom**: Hundreds of atoms per document, most trivial.
**Cause**: Extraction parameters too broad. Every sentence treated as a discrete atom.
**Fix**: Tune extraction to focus on actionable evidence: assertions, admissions, contradictions, timeline events. Quality over quantity.

### 5. Lane Misassignment
**Symptom**: Housing evidence classified as custody, or vice versa.
**Cause**: Documents mentioning parties from multiple lanes assigned to wrong lane.
**Fix**: Support MULTI lane assignment. Documents mentioning Watson AND housing conditions span lanes A and B.

## Michigan-Specific Evidence Handling Traps

- **MRE 1001–1008 (Best Evidence)**: Michigan follows the best evidence rule. If original documents are available, copies may be challenged. Maintain originals where possible and document why copies are used.
- **MRE 901(b)(9)**: Michigan allows authentication of electronic evidence through "system or process" methodology. Document your extraction and processing pipeline to qualify under this provision.
- **HIPAA in custody cases**: Lane A custody proceedings often involve medical/mental health records. MCL 600.2157 (physician-patient privilege) applies. Ensure medical records are properly obtained under court order or waiver.
- **Business records (MRE 803(6))**: Shady Oaks corporate records (Lane B) may qualify as business records exception to hearsay. Document the custodian and record-keeping practices to establish foundation.
- **Public records (MRE 803(8))**: Lane C convergence evidence often involves public records. MRE 803(8) provides hearsay exception for public records. Authentication is simplified under MRE 902(4) for certified copies.
- **Bulk discovery**: Michigan courts can impose proportionality limits on discovery under MCR 2.302(C). Having 427,956+ files is an asset only if you can identify and produce relevant documents efficiently. Inability to manage the collection can result in adverse inferences.
