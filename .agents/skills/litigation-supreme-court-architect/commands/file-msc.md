# COMMAND: FILE-MSC — MSC FILING WORKFLOW

## SYNOPSIS

```
file-msc <action-type> --lane <A|B|C> [--mode DRAFT|FILE_READY|PCG]
```

## DESCRIPTION

Step-by-step workflow for preparing and filing any Michigan Supreme Court action.
Each step is a gate — do not advance until the current gate passes.

---

## QUICK START — BY FILING TYPE

### Application for Leave to Appeal
```
file-msc leave --lane A --mode DRAFT
```
1. Confirm COA final decision exists → record date
2. Calculate 56-day deadline from COA decision date
3. Identify MCR 7.305(B) grounds (see references/strategy/grounds-matrix.md)
4. Draft questions presented (2-3 maximum)
5. Build brief per MCR 7.212(C) (see references/forms/brief-architecture.md)
6. Compile appendix (COA opinion, trial court orders, key transcripts)
7. Prepare cover page, TOC, TOA
8. Prepare CC 298 application form
9. Prepare proof of service (MC 12)
10. Prepare fee ($375) or fee waiver (MC 20)
11. Switch to FILE_READY → run compliance checklist
12. File → switch to PCG

### Bypass Application
```
file-msc bypass --lane A --mode DRAFT
```
1. Document why COA delay causes irreparable harm
2. Document why issue has major significance to state jurisprudence
3. Prepare bypass-specific brief: extraordinary circumstances section FIRST
4. Include all standard application components (as above)
5. Add separate section: "Why Bypass Is Necessary"
6. File → switch to PCG

### Extraordinary Writ (Mandamus / Superintending Control)
```
file-msc writ --type mandamus --lane C --mode DRAFT
```
1. Confirm no adequate remedy at law exists
2. Identify clear legal right to relief
3. Identify clear legal duty of respondent
4. Draft complaint for writ per MCR 7.306
5. Draft brief in support — cite Const 1963 Art 6 §4
6. Prepare proof of service on respondent
7. File → switch to PCG

### Habeas Corpus
```
file-msc writ --type habeas --lane A --mode DRAFT
```
1. Confirm physical custody/restraint exists
2. Confirm exhaustion of lower court remedies
3. Draft petition per MCR 7.306(B)(3)
4. Attach prior court orders, custody determinations
5. File → switch to PCG

### Motion (Extension / Stay / Amicus)
```
file-msc motion --type stay --lane A --mode DRAFT
```
1. Identify motion type and governing rule (MCR 7.311)
2. Draft motion with specific relief requested
3. Draft brief in support
4. Prepare proposed order
5. Prepare proof of service
6. File → switch to PCG

### Certified Question (Party Response)
```
file-msc certified --lane B --mode DRAFT
```
1. Review MSC order accepting certified question
2. Review federal court certification order
3. Draft brief addressing certified question
4. Comply with MSC scheduling order
5. File → switch to PCG

---

## DETAILED WORKFLOW — GATE-BY-GATE

### GATE 1: ACTION SELECTION

```
Input: Current procedural posture of the case
Process:
  1. Is there a COA final decision?
     YES → Leave to appeal (PATH 1)
     NO  → Continue
  2. Is case pending in COA with emergency?
     YES → Bypass (PATH 2)
     NO  → Continue
  3. Is this a matter within MSC original jurisdiction?
     YES → Original proceeding (PATH 3) or Writ (PATH 4)
     NO  → Continue
  4. Is there a federal certification?
     YES → Certified question response (PATH 5)
     NO  → Continue
  5. Is this a procedural motion in existing MSC case?
     YES → Motion (PATH 6)
     NO  → STOP — re-evaluate posture
Output: Selected filing path
```

### GATE 2: GROUNDS ANALYSIS

```
Input: Selected filing path + case facts
Process:
  1. Map case facts to MCR 7.305(B) grounds
  2. For each potential ground:
     a. Identify supporting authority
     b. Identify counterargument
     c. Rate strength: STRONG / MODERATE / WEAK
  3. Select 2-3 strongest grounds
  4. Draft preliminary questions presented
Output: [VM] VehicleMap with selected grounds
```

### GATE 3: FORM PREPARATION

```
Input: Filing path + grounds
Process:
  1. Pull required forms from references/forms/README.md
  2. Complete CC 298 (if application)
  3. Prepare cover page with proper caption
  4. Draft TOC outline
  5. Prepare MC 12 (proof of service) — leave date blank
  6. Prepare MC 20 (fee waiver) if applicable
Output: Completed form packet
```

### GATE 4: BRIEF DRAFTING

```
Input: Grounds + forms + record
Process:
  1. Follow references/forms/brief-architecture.md structure
  2. Draft each required section:
     a. Statement of jurisdiction
     b. Questions presented
     c. Statement of proceedings and facts
     d. Argument (one section per question presented)
     e. Relief requested
  3. Generate TOC and TOA
  4. Verify page limits
  5. Run [AT] AuthorityTriples for every cited authority
Output: Draft brief
```

### GATE 5: RECORD COMPILATION

```
Input: Brief + lower court record
Process:
  1. List every document referenced in brief
  2. Verify each document exists in the record
  3. Compile appendix:
     a. COA decision/opinion
     b. Trial court order(s) being challenged
     c. Key transcript excerpts
     d. Critical exhibits
  4. Create appendix index
  5. Cross-reference brief citations to appendix tabs
Output: Compiled appendix
```

### GATE 6: SERVICE

```
Input: Complete filing packet
Process:
  1. Identify all parties requiring service
  2. Determine service method (mail, email if stipulated, personal)
  3. Serve all parties
  4. Complete MC 12 proof of service with dates and method
  5. Retain proof of mailing (USPS receipt, email confirmation)
Output: Completed MC 12 + service proof
```

### GATE 7: FILING

```
Input: Complete packet + proof of service
Process:
  1. Verify copy count (original + copies for all parties + 1)
  2. Include fee ($375) or fee waiver (MC 20)
  3. Verify all signatures
  4. File with MSC Clerk:
     Michigan Supreme Court Clerk
     925 W. Ottawa Street
     P.O. Box 30052
     Lansing, MI 48909
     (517) 373-0120
  5. Obtain filing receipt / confirmation
  6. Switch to PCG mode
Output: Filed action + receipt
```

---

## POST-FILING CHECKLIST (PCG MODE)

```
[ ] Filing receipt saved
[ ] MC 12 proof of service filed with court
[ ] Calendar: Response deadline (28 days from service)
[ ] Calendar: If response filed → Reply deadline (14 days)
[ ] Calendar: Oral argument date (if ordered)
[ ] All filed documents copied and retained
[ ] Docket checked within 7 days for case number assignment
[ ] TrueFiling account checked for electronic notifications
```

---

## ERROR RECOVERY

| Error | Recovery |
|-------|----------|
| Missed 56-day deadline | File motion for late application — must show good cause + meritorious claim. Extremely difficult. |
| Wrong number of copies | Call clerk immediately — request leave to supplement copies |
| Missing fee | File MC 20 fee waiver immediately OR pay fee — clerk may hold rather than reject |
| Service defect | Re-serve immediately + file amended proof of service |
| Brief exceeds page limit | File motion for leave to exceed page limit with justification |
| Appendix incomplete | File supplemental appendix with motion for leave to file |
| Wrong form used | Contact clerk — may allow substitution if substance correct |
