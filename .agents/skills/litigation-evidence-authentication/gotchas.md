# Gotchas — litigation-evidence-authentication

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The evidence speaks for itself — authentication is just a technicality." | Authentication under MRE 901(a) is a CONDITION PRECEDENT to admissibility. No matter how compelling the evidence is, if you can't authenticate it, the court will EXCLUDE it. Authentication means producing "evidence sufficient to support a finding that the matter in question is what its proponent claims." | Critical evidence excluded at trial or hearing because foundation wasn't laid. In Pigors v Watson, text messages proving custody order violations are worthless if you can't authenticate who sent them. The most damning evidence means nothing if the court won't let it in. |
| 2 | "Digital evidence is automatically authentic because it has metadata." | Digital evidence requires specific authentication beyond metadata. MRE 901(b)(4) allows authentication through "distinctive characteristics" including content and context, but metadata alone can be spoofed. The proponent must establish: (1) what the evidence is, (2) that it hasn't been altered, and (3) who created/sent it. | Opposing counsel objects on authentication grounds, court sustains, and your digital evidence is excluded. Screenshots without context, emails without header information, and texts without device verification are all vulnerable to authentication challenges. |
| 3 | "Official records are self-authenticating — no foundation needed." | While MRE 902 provides for self-authentication of certain documents (certified copies of public records, official publications), you still need to obtain the certified copies. An uncertified printout from a court website is NOT self-authenticating. MCL 600.2106 requires proper certification. | Your "official record" is excluded because it's an uncertified copy. Requesting certified copies takes time — if you wait until trial, it may be too late. Order certified copies of all official records well in advance of hearing dates. |
| 4 | "The chain of custody only matters for physical evidence in criminal cases." | Chain of custody applies in civil cases too, especially for evidence that could have been tampered with or altered. Digital evidence (photos, videos, electronic files) requires showing who had access and that no alterations occurred. MRE 901(a) applies to all evidence, civil and criminal. | Evidence excluded or given reduced weight because chain of custody gaps create doubt about integrity. In housing cases (Lane B), photographs of property defects are challenged: "How do we know this photo is from YOUR unit? When was it taken? Was it altered?" Without chain of custody, these challenges succeed. |
| 5 | "We can authenticate evidence at the hearing — no need to prepare beforehand." | Authentication preparation happens BEFORE the hearing. Witnesses must be prepared to testify about foundation. Certified copies must be obtained in advance. Technical authentication (digital forensics) may require expert testimony that must be arranged beforehand. Waiting until the hearing = scrambling and failing. | Scrambling to authenticate evidence at the hearing wastes court time, frustrates the judge, and often fails. Judge McNeill will not grant continuances because you forgot to get certified copies. Prepare authentication for EVERY exhibit before the hearing date. |

---

## Common Failure Modes

### 1. Text Message Authentication Gap
- **What happens**: Text messages offered without authenticating the sender's identity or the completeness of the conversation
- **How to prevent**: Authenticate via: subscriber information (phone records), content/context (MRE 901(b)(4)), reply doctrine, or testimony of the other participant. Include full conversation thread, not cherry-picked messages
- **Lane risk**: CRITICAL for Lane A — text messages are primary evidence for custody compliance

### 2. Photo/Video Without Metadata
- **What happens**: Photographs or videos offered without EXIF data, location data, or testimony about when/where/who took them
- **How to prevent**: Preserve original digital files with metadata intact; testify about when and where the photo was taken; use metadata extraction tools; avoid screenshots of photos (destroys metadata)
- **Lane risk**: HIGH for Lane B — property condition photos must be dated and located

### 3. Hearsay Within Authenticated Documents
- **What happens**: Document is properly authenticated but contains hearsay statements that are separately inadmissible
- **How to prevent**: Authenticate the document AND identify hearsay exceptions for statements within it. Business records (MRE 803(6)), public records (MRE 803(8)), statements against interest (MRE 804(b)(3)), or party admissions (MRE 801(d)(2))
- **Lane risk**: MEDIUM — authenticated documents with inadmissible hearsay have limited value

### 4. Best Evidence Rule Violation
- **What happens**: Offering a copy of a document without accounting for the best evidence rule (MRE 1002) which requires the original
- **How to prevent**: Produce originals when available; if original is unavailable, establish exception under MRE 1004 (lost/destroyed, in opponent's possession, collateral matter); certified copies of public records are exempt (MRE 1005)
- **Lane risk**: MEDIUM — easily prevented with advance planning

### 5. Missing Foundation Witness
- **What happens**: The witness needed to authenticate a document (author, recipient, custodian) is unavailable at the hearing
- **How to prevent**: Identify the foundation witness for every exhibit during preparation; ensure their availability; if unavailable, use alternative authentication methods (MRE 901(b) list) or stipulation
- **Lane risk**: HIGH — without a foundation witness, some evidence simply cannot be admitted

---

## Integration Gotchas

- **litigation-deposition-strategist** can use depositions to pre-authenticate exhibits (show to witness, get acknowledgment on the record)
- **litigation-analysis-engine** must tag evidence with authentication status before analysis is used in filings
- **litigation-filing-packager** should only include properly authenticated evidence in court filing packages
- **litigation-appeal-brief-engine** must verify that evidence cited in the appellate brief was properly admitted below
- Digital evidence preservation is ongoing — coordinate with evidence chain documentation
