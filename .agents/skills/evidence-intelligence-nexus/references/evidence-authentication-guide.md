# Evidence Authentication Guide — evidence-intelligence-nexus

## Michigan Rules of Evidence — Authentication Requirements

### MRE 901: Requirement of Authentication or Identification

**General principle (MRE 901(a))**: The requirement of authentication or identification
as a condition precedent to admissibility is satisfied by evidence sufficient to support
a finding that the matter in question is what its proponent claims.

---

## Authentication Methods by Evidence Type

### 1. Text Messages / SMS
**Rule**: MRE 901(b)(1) (testimony of witness with knowledge) or MRE 901(b)(4) (distinctive characteristics)
**Foundation requirements**:
- Witness who sent or received the messages
- OR distinctive characteristics (content, context, phone number identification)
- Screenshot alone is INSUFFICIENT — must establish who sent/received
- Phone records from carrier can corroborate

**Best practice**: Preserve original device data. Screenshots supplemented by
carrier records showing message timestamps and phone numbers.

### 2. Emails
**Rule**: MRE 901(b)(1), MRE 901(b)(4), MRE 901(b)(9)
**Foundation requirements**:
- Testimony of sender or recipient
- OR email headers showing routing information
- OR distinctive characteristics (email address, writing style, referenced events)
- Consider: was the account compromised? Can the email be spoofed?

**Best practice**: Preserve full email with headers. Obtain from email provider
if possible. Screenshots of email bodies are weakest form of authentication.

### 3. Social Media Posts
**Rule**: MRE 901(b)(1), MRE 901(b)(4)
**Foundation requirements**:
- Account holder testimony
- OR circumstantial evidence connecting the post to the purported author
- Screenshot of post with URL, timestamp, and account name visible
- Evidence that the account belongs to the purported author

**Best practice**: Use web archiving tools (Wayback Machine, archive.today).
Screenshots supplemented by metadata from the platform API if available.

### 4. Photographs / Videos
**Rule**: MRE 901(b)(1) — testimony that the photo/video is a fair and accurate representation
**Foundation requirements**:
- Witness who was present and can testify the image accurately depicts the scene
- For surveillance video: testimony of person who installed/maintained the system
- EXIF data can corroborate date, time, location

**Best practice**: Preserve original file with metadata. Do not crop, filter,
or edit — any alteration must be disclosed and the original preserved.

### 5. Business Records (including FOC Reports)
**Rule**: MRE 803(6) — records of regularly conducted activity
**Foundation requirements**:
- Made at or near the time of the event
- By or from information transmitted by a person with knowledge
- Kept in the course of a regularly conducted business activity
- It was the regular practice to make such records
- Testimony of the custodian or other qualified witness (or certification under MRE 902(11))

**For FOC reports**: Admissible under MCL 552.505 in custody proceedings, but
hearsay within the report (third-party statements) may be separately challenged.

### 6. Court Records / Official Documents
**Rule**: MRE 902(1), 902(4) — self-authenticating
**Foundation requirements**:
- Certified copies from the court clerk are self-authenticating
- Must bear the court's seal or clerk's certification
- No extrinsic evidence of authenticity required

**Best practice**: Always obtain certified copies for court filings.
Uncertified copies require authentication by someone with knowledge.

### 7. Audio Recordings
**Rule**: MRE 901(b)(1), MRE 901(b)(5) (voice identification)
**Foundation requirements**:
- Testimony of a participant in the conversation
- OR voice identification by someone familiar with the speaker's voice
- Michigan is a one-party consent state (MCL 750.539c) — only one party
  to the conversation must consent to recording

**Best practice**: Preserve original recording. Provide transcript. Note who
is speaking at each point. Document recording device and settings.

### 8. Digital Files (PDFs, Documents, Spreadsheets)
**Rule**: MRE 901(b)(9) — process or system
**Foundation requirements**:
- Evidence describing the process or system used to produce the result
- Showing that the process or system produces an accurate result
- For files from litigation_context.db: document the ingest pipeline, hashing,
  and chain of custody from original source to current storage

**Best practice**: SHA-256 hash at every stage. Document the pipeline that
processed the file. Maintain access logs showing who touched the file.

---

## MRE 902: Self-Authentication (No Extrinsic Evidence Required)

| Category | Rule | Example |
|----------|------|---------|
| Domestic public documents under seal | 902(1) | Certified court orders |
| Domestic public documents not under seal | 902(2) | With certification |
| Official publications | 902(5) | Published statutes, court rules |
| Newspapers and periodicals | 902(6) | Published articles |
| Trade inscriptions | 902(7) | Labels, signs, tags |
| Certified business records | 902(11) | With declaration of custodian |
| Certified foreign records | 902(12) | With declaration |

---

## MRE 903: Subscribing Witness Testimony Not Required

Subscribing witness testimony is generally not required to authenticate a writing,
except where required by the laws of the jurisdiction whose laws govern the validity
of the writing.

---

## Authentication Checklist (For Every Exhibit)

```
For each exhibit in the case:
□ Evidence type identified (text, email, photo, document, recording, etc.)
□ Applicable MRE rule identified (901(b)(1), 901(b)(4), 901(b)(9), 902, etc.)
□ Foundation witness identified (who can authenticate this?)
□ Foundation questions drafted
□ Chain of custody documented (source → storage → court)
□ SHA-256 hash recorded (for digital evidence)
□ Hearsay analysis completed (is content hearsay? which exception?)
□ Original preserved (or explanation of why original is unavailable per MRE 1004)
□ Bates number assigned
□ Lane tag assigned (A-F)
```
