# Authority Acquisition Plan (WarChest Coverage Program)

Goal
Build a Michigan “Authority WarChest” that is *auditably comprehensive* for litigation: every proposition traceable to a pinpointable span.

Core corpora (Michigan primary)
1) Michigan Court Rules (MCR) — full text, versioned
2) Michigan Rules of Evidence (MRE) — full text, versioned
3) Michigan Compiled Laws (MCL) — at minimum Titles/Chapters relevant to:
   - domestic relations (custody/parenting time/child support)
   - PPO / criminal procedure interactions
   - contempt enforcement mechanisms
   - mental health code + confidentiality/records
4) Michigan Constitution (1963) + relevant historical references if needed
5) Benchbooks + SCAO guides
6) SCAO/FOC/MC forms + instructions (where mandated)
7) Caselaw layer governance:
   - Published Michigan Supreme Court (binding)
   - Published Michigan Court of Appeals (binding)
   - Unpublished COA (persuasive only; clearly tagged)

Coverage metrics (what “100%” means operationally)
- MCR coverage = rules ingested / total rules (by numeric sections)
- MRE coverage = rules ingested / total
- MCL coverage = targeted chapters ingested / targeted list
- Caselaw coverage = published holdings ingested / published list for chosen date range
- Benchbook coverage = volumes ingested / chosen volumes

Crosswiring requirements
Every authority span must have:
- AuthorityID (source hash)
- CitationKey (e.g., MCR 2.003, MRE 803, MCL 552.###)
- Pinpoint pointer (section/subsection/paragraph/line-range if available)
- Extract method: embedded text vs OCR

Pipeline (recommended)
A) Acquire official corpora locally (PDF/HTML/TXT exports)
B) Normalize → “line-addressable shards”:
   - one file per rule/section (or per chapter subsection)
   - stable IDs
C) Build WarChest DB (mi_warchest_builder_v2.py)
D) Run Record Matcher to generate:
   - IssueGrid (issue ↔ authority ↔ record pointers)
   - AuthorityTriples (proposition ↔ authority ↔ pinpoint)
E) Draft compiler consumes IssueGrid → vehicle packets → court-ready drafts

