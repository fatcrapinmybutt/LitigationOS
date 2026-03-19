# Michigan Litigation Filing Packages for a LitigationOS Build (Clerk Stacks)
**Version:** v2026-02-28  
**Purpose:** Convert Michigan court-rule + MiFILE standards into **ranked, evidence-driven filing packages** that LitigationOS can render as **clerk stacks** (ordered bundles) with manifests, templates, and CI checks.

---

## 1) High-signal corrections & upgrades (delta notes)

### 1.1 MCR 2.119 timing (default service windows)
A lot of bad filings die on timing.

**Default service timing (unless the rules or the court set a different schedule for good cause):**
- **Motion + notice of hearing + brief/affidavits**:  
  - **9 days** before hearing if served by first-class mail  
  - **7 days** before hearing if delivered or electronically served
- **Response + brief/affidavits**:  
  - **5 days** before hearing if served by first-class mail  
  - **3 days** before hearing if delivered or electronically served

These timings are summarized in Michigan Judicial Institute benchbook material discussing MCR 2.119(C)(1)-(3).  
(See: Michigan Courts, *Civil Proceedings Benchbook* / Chapter 4 pretrial procedures summary.)

> LitigationOS implication: timing is **method-dependent** (mail vs delivery/e-service). Your CI must compute deadlines from the service method used.

### 1.2 MCR 2.119 page limits (motion + brief)
**Combined length of motion + brief** (or response + brief) is **20 double-spaced pages**, excluding attachments/exhibits, unless the court permits more.  
This is stated in Michigan Courts e-filing standards and benchbook guidance.

### 1.3 MiFILE "Index to Attachments" is real and strict
Michigan Courts e-filing standards require:
- each attachment to be **separately connected** and **referenced** to the lead document; and
- the **last page of the lead document** must contain an **“Index to Attachments”** listing each attachment title + file name.
Also: **hyperlinks must be internal** (same document) and embedded audio/video is prohibited.

### 1.4 MCR 2.003 disqualification grounds are explicitly two-track
MCR 2.003(C)(1) includes:
- **(a)** actual bias/prejudice; and
- **(b)** (i) **serious risk of actual bias** (Caperton-type due process risk) **or** (ii) **failure to adhere to the appearance of impropriety standard** (Canon 2).
Michigan Judicial Institute’s Judicial Disqualification benchbook captures the text and key Cain/Crampton lines.

---

## 2) Core authorities that define Michigan family-court filing surface

### 2.1 Motion practice “spine”
- **MCR 2.119** — form/brief requirements, page limits, service timing defaults, and court’s ability to set alternate schedules.
- **MCR 2.003** — judicial disqualification (bias, serious risk of bias, appearance of impropriety).
- **MCR 2.612** — structured relief from judgment/order; “reasonable time” generally, and **1-year** limit for certain grounds.
- **MCR 3.302** — superintending control (extraordinary; requires clear legal duty + no adequate remedy).
- **MCR 7.206** — Court of Appeals original actions package shape.
- **MCR 7.305 / 7.306** — Michigan Supreme Court leave to appeal + original proceedings (including MSC superintending control).

### 2.2 Substantive family-law anchors (statutes)
- **MCL 722.23** best-interest factors  
- **MCL 722.27** custody modification / established custodial environment constraints  
- **MCL 722.27a** parenting time (best interests; presumption of strong relationship)  
- **MCL 600.2950** PPO restraints can include **removing minor children** except as authorized by custody/PT orders (important for “PPO cloaking” fact patterns).

### 2.3 SCAO statewide forms (clerk-friendly)
- **FOC 65** Motion Regarding Parenting Time (and instructions)  
- **FOC 87** Motion Regarding Custody (and instructions)

---

## 3) Ranked filing packages → LitigationOS “planes”
Ranking is **procedural fit + evidence leverage + typical Michigan family-court usability** (not a prediction).

### Plane A — In-case family motions (highest practical ROI)
**Rank 1: FOC 65 Parenting Time (enforce/make-up/clarify/change)**
- Lead doc: FOC 65
- Required attachments: incident narrative (dates + what was ordered + what happened), exhibit set, index-to-attachments
- Service: certificate/proof consistent with MCR 2.119 + domestic-relations service concept (often referenced by the forms)

**Rank 2: FOC 87 Custody (when threshold met)**
- Lead doc: FOC 87
- Must carry “proper cause/change of circumstances” + ECE + best interests structure
- Requires record-building aligned with custody appellate standards (Fletcher) and ECE analysis (Pierron)

### Plane B — Record repair & relief
**Rank 3: MCR 2.612 Relief from Order**
- Use when you can credibly fit: mistake/neglect, newly discovered evidence, fraud/misrep, voidness, etc.
- Time limits: “reasonable time,” and **1-year** for some grounds

**Rank 4: Record integrity / closure defects**
- Not a single rule, but a controlled “record spine” package (ROA, file stamps, hearing notices, service proofs, and orders).
- LitigationOS should treat this as a *data acquisition bundle* that powers Plane C/D.

### Plane C — Decisionmaker integrity (high risk/high reward)
**Rank 5: MCR 2.003 Disqualification**
- Only deploy with **objective record** (transcript quotations, orders, extrajudicial facts if any)
- Explicitly plead under the correct prong: (a) actual bias; (b)(i) serious risk of bias; or (b)(ii) appearance of impropriety

### Plane D — Extraordinary review / escalation
**Rank 6: COA Original Action (MCR 7.206)**
- Complaint + brief + supporting record evidence/affidavits + proof of service

**Rank 7: MSC escalation**
- **MCR 7.305** application for leave to appeal (with strict content requirements)
- **MCR 7.306** original proceedings, including MSC superintending control in certain circumstances

> LitigationOS caution: “no adequate remedy” is the gating predicate for superintending control; the system should require a checklist-based justification.

---

## 4) MiFILE hard checks → deterministic lints (minimum)
These items are rejectable (or risky) when wrong:
- **Signature**: /s/ name is acceptable; unsigned filings may be rejected.
- **Page size**: 8.5x11 view; must print without manipulation.
- **Font**: 12–13 point body; footnotes ≥10.
- **Margins**: 1" top/bottom; 0.5" sides; no text in margins (court stamps only).
- **OCR/searchable PDF**: documents you control must be converted directly to PDF; scanning is prohibited unless you didn’t create it electronically or wet signature required.
- **25 MB file size**; split into parts with “Part 1 of N”.
- **Index to Attachments** on the last page of the lead doc; attachments connected separately and named per standards.
- **Self-contained**: hyperlinks only to content within same document; no embedded audio/video.

---

## 5) LitigationOS machine-readable primitives
- **Clerk stack** = ordered file list + validation rules + “what evidence must exist” checklist.
- **Manifest** = JSON record describing the case, the package, its documents, and evidence pointers.
- **Lint** = deterministic rules that either PASS/FAIL or emit FIX steps.

This bundle includes JSON Schemas + example manifests + YAML lint rules + starter Akoma Ntoso templates.

---

## 6) Curated source list
(Primary sources you should pin as “Authority Snapshots” in LitigationOS)

- Michigan Courts: *Preparing Electronic Documents for Filing* (MiFILE standards)
- Michigan Courts: MiFILE Quick Reference Guide (attachments + 25MB + naming)
- Michigan Courts: FOC 65 + instructions
- Michigan Courts: FOC 87 + instructions
- Michigan Courts: MJI *Judicial Disqualification in Michigan* (MCR 2.003 text + Cain lines)
- Michigan Courts: COA Guide to Original Actions (MCR 7.206 practical packaging)
- Michigan Legislature: MCL 722.23, 722.27, 722.27a, 600.2950
- Michigan Supreme Court: Pierron v Pierron (2010) opinion PDF
- Michigan Supreme Court: Fletcher v Fletcher (1994) (standard-of-review anchor; official opinion is harder to locate online; use multiple confirming sources)

---

## 7) Single Best Next Step (Δ99)
Implement the **deterministic “Rule+MiFILE Lint” first**, then ingest your **ROA + service proofs + key orders** so LitigationOS can auto-select between:
- Plane A (FOC 65/87) vs
- Plane C (2.003) vs
- Plane D (COA/MSC extraordinary)

In other words: build the *submission-physics* engine, then feed it record spine.
