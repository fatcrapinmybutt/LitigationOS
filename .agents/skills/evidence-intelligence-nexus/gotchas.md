# Gotchas — evidence-intelligence-nexus

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The file hash matches, so these are definitely the same document — I can dedup by hash alone." | Andrew explicitly said: "no hashing — peek at the document to ensure they are the same." File hashes can match for different-content files (truncated copies, metadata-only changes) or differ for same-content files (different PDF generators, OCR re-runs). Content-based dedup means OPENING the file and comparing actual text. | Legitimate unique evidence gets deduped away and is permanently lost from the case. Or duplicates survive and inflate evidence counts, making aggregate statistics unreliable. |
| 2 | "I counted 305 interference incidents across the evidence tables." | Did you dedup? The same incident may appear in `evidence_quotes`, `claims`, `docket_events`, and `judicial_violations` tables. Without `SELECT COUNT(DISTINCT evidence_hash)` or content-based dedup, you're counting the same event 2-4 times. Prior sessions inflated counts this way. | Opposing counsel subpoenas the data, runs the same query with DISTINCT, gets 150 — not 305. The court sees you doubled your numbers. ALL evidence statistics become suspect. |
| 3 | "This text message screenshot is self-authenticating — no foundation needed." | MRE 901(a) requires authentication for ALL evidence. Text messages require testimony or circumstantial evidence that the message came from the purported sender. Screenshots can be fabricated. Even business records (MRE 803(6)) need a custodian or qualified witness. | Evidence excluded at hearing. Worse, if the court finds you attempted to introduce unauthenticated evidence, it may question the reliability of your other exhibits. |
| 4 | "The chain of custody for digital files doesn't matter — they're just files on a drive." | Digital evidence requires chain of custody documentation showing: original source, date obtained, storage location, access log, hash verification (SHA-256), and any copies made. MRE 901(b)(9) covers authentication of electronic evidence. Without it, opposing counsel argues the files were altered. | Motion to suppress/exclude the evidence. Even if not excluded, the trier of fact may give it less weight. For critical evidence (e.g., communications proving interference), this can be case-determinative. |
| 5 | "I'll estimate damages at $50,000 based on comparable cases." | Michigan damages must be calculated using specific methodologies. Economic damages require actual documented losses (MCL 600.2911). Treble damages (MCL 600.2919a) require proving the underlying amount first. §1983 damages (42 USC §1988) have their own framework. No estimation — only documented calculations. | Damages claim dismissed for failure to state with specificity. Or, worse, the court awards only nominal damages ($1) because you failed to prove actual damages with documentation. |
| 6 | "This FOC report is hearsay but it's in the court file, so it's admissible." | Being in the court file does NOT make a document admissible. FOC reports, while often considered by courts in custody proceedings under specific statutory authority (MCL 552.505), still have hearsay components that can be challenged. Know which portions are admissible and under what exception. | Objection sustained. Key evidence excluded. If your argument depended on that evidence, the argument fails. |
| 7 | "I moved duplicate files to the Recycle Bin — same as moving to I:\." | The rules say: "ALL DUPLICATES → I:\ drive." Recycle Bin is acceptable for general file management, but litigation duplicates must go to a dedup folder on I:\ for audit trail purposes. The I:\ drive preserves the original path metadata and allows recovery if the "duplicate" turns out to be unique. | If a file in Recycle Bin is purged, there's no recovery. If it turns out the "duplicate" was actually a different version of a document with distinct evidentiary value, that evidence is gone. |

---

## Common Failure Modes

### 1. Authentication Foundation Failure
- **What happens**: Evidence is collected and indexed but the authentication foundation is never documented. When it's time to introduce the exhibit, there's no witness identified, no business records affidavit, no chain of custody.
- **How to prevent**: For every piece of evidence, document the authentication method at intake: (1) Who can authenticate it? (2) Which MRE rule applies? (3) Is a foundation witness available? Store this in the evidence record alongside the content.
- **Lane risk**: HIGH for all lanes — unauthenticated evidence is inadmissible regardless of how probative it is.

### 2. Chain of Custody Gap
- **What happens**: Digital files are copied between drives, renamed, converted, or OCR'd without logging each step. The chain of custody has gaps that opposing counsel exploits to argue alteration.
- **How to prevent**: Every file operation must be logged: source path, destination path, operation type, timestamp, SHA-256 before and after. Use the Chain of Custody Record template from this skill's §1 section.
- **Lane risk**: HIGH for Lanes A and D — custody and PPO cases depend heavily on digital communications (texts, emails, social media).

### 3. Hearsay Trap — Unidentified Exception
- **What happens**: Agent includes evidence that is clearly hearsay (out-of-court statement offered for truth) without identifying the applicable exception under MRE 803 or 804.
- **How to prevent**: For every out-of-court statement, identify: (1) Is it hearsay? (2) If yes, which exception applies? (3) Can you lay the required foundation for that exception? Common exceptions: MRE 803(1) present sense impression, 803(2) excited utterance, 803(3) state of mind, 803(6) business records.
- **Lane risk**: MEDIUM for all lanes — hearsay is the most common evidentiary objection.

### 4. Duplicate Counting in Aggregates
- **What happens**: The same evidence event appears in multiple DB tables (`evidence_quotes`, `claims`, `judicial_violations`, `docket_events`). Agent counts each table separately and sums them, inflating the total.
- **How to prevent**: Always use `COUNT(DISTINCT ...)` on a stable identifier (evidence_hash, event_date + description). Before reporting any aggregate, verify dedup. Document the exact query.
- **Lane risk**: HIGH for Lane A (custody) — best-interest factor scoring is directly influenced by evidence counts.

### 5. Damages Calculation Without Methodology
- **What happens**: Agent estimates damages based on "analysis" or "comparable cases" rather than documenting actual losses with supporting evidence.
- **How to prevent**: Use the damages-calculation-methodology reference. Economic damages = documented out-of-pocket losses. Non-economic damages = statutory framework. Treble damages = base × 3 with statutory authority. §1983 = compensatory + punitive with qualified immunity analysis.
- **Lane risk**: HIGH for Lanes B (housing) and C (§1983) — damages are a required element of these claims.

---

## Integration Gotchas

- **evidence-intelligence-nexus feeds INTO OMEGA-LITIGATION-SUPREME M1 (Evidence Pipeline)** — this skill provides the evidence processing logic that M1 orchestrates. Don't bypass M1 and feed directly to M4 (Filing Factory).
- **Content-based dedup is NON-NEGOTIABLE** — Andrew has explicitly and repeatedly stated this. Hash-only dedup is forbidden. Open the file, read the content, compare text. This applies to ALL file operations, not just the initial dedup phase.
- **Evidence from different drives may have different metadata timestamps** — don't assume the filesystem date is the evidence date. Check for creation date in document content, email headers, or EXIF data.
- **The `evidence_quotes` table may contain quotes from the same source document split across multiple rows** — when counting "evidence items," count distinct source documents, not individual quotes.
- **SHA-256 hashing is for PROVENANCE, not for dedup** — hash every file for chain of custody proof, but use content comparison for deduplication decisions. These are two separate functions of hashing.
