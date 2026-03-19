# Attachment Harvest Report — LitigationOS (2026-02-08)

## Inputs processed
- nodes_merged.csv (rows=136,692, cols=13)
- nodes_neo4j_admin.csv (rows=30,028, cols=6)
- CONTRADICTION_MAP.csv (+ duplicates) (rows=141)
- tail_preview.csv (rows=50)
- 205 JSON CSV TXT .zip (detected as **.docx container**; extracted text)
- JTC_Print_Order_Master_2025-10-29_with_bookmarks_footer_toc.pdf (pages=502)
- JTC_MSC_Binder_v5_2025-10-29_19-13-34.pdf (pages=216) — **image-only/no embedded text**
- 2025-10-29_Pigors_v_Watson_MSC-JTC_Exhibits_Binder_v5.pdf (pages=216) — **image-only/no embedded text**
- 555.txt (≈324 chars; used as context reservoir, not fully re-parsed here)
- LitigationOS_CompilerCoreBundle_v1_0_0.zip (already integrated into current design)
- LitigationOS_GraphContract_v1_0_0.zip (already integrated into current design)

---

## A) Graph dataset findings

### A1) nodes_merged.csv — label distribution (top 15)
See: `nodes_merged_label_counts.csv`

Top labels (by row count):
| label                                                                                                                               |   count |
|:------------------------------------------------------------------------------------------------------------------------------------|--------:|
| Node                                                                                                                                |   76097 |
| MISC;Node                                                                                                                           |   22897 |
| Authority;MISC;Node                                                                                                                 |    8419 |
| AuthorityRef;Node                                                                                                                   |     698 |
| MISC;Node;Violation                                                                                                                 |      67 |
| MISC;Node;Remedy                                                                                                                    |      35 |
| EVENT;Node                                                                                                                          |      23 |
| Circuit Court Judge;MISC;Node;Violation                                                                                             |      19 |
| HON. JENNY L. MCNEILL,;MISC;Node;Violation                                                                                          |      19 |
| MISC;Node;PROOF OF SERVICE;Violation                                                                                                |      17 |
| Court address;MISC;Node;Violation                                                                                                   |      15 |
| Judgment  Custody,  PT, CS 2024-001507-DC;MISC;Node;Violation                                                                       |      14 |
| Court;MISC;Node;Violation                                                                                                           |      12 |
| 2023-5907-PP Hon. Judge Jenny L McNeill My court-ordered  weekend  parenting  time (November  7-10, 2024). s Halloween  …;MISC;Node |      10 |
| Judgment Custody, PT, CS2024-001507-DC;MISC;Node;Violation                                                                          |      10 |

### A2) nodes_neo4j_admin.csv — label distribution (top 15)
See: `nodes_neo4j_admin_label_counts.csv`

Top labels:
| label                                                                                                     |   count |
|:----------------------------------------------------------------------------------------------------------|--------:|
| Authority;Node;Kind_authority                                                                             |    7252 |
| AuthorityCanonical;Authority;Kind_authority_canonical                                                     |    7132 |
| Authority;Node;Kind_keyword                                                                               |    1069 |
| Authority;Node;Kind_Authority                                                                             |      28 |
| Judgment_Custody;PT;CS_2024_001507_DC;Node;Violation;Kind_violation                                       |      22 |
| Court;Node;Violation;Kind_violation                                                                       |      20 |
| Circuit_Court_Judge;Node;Violation;Kind_violation                                                         |      19 |
| HON_JENNY_L_MCNEILL;Node;Violation;Kind_violation                                                         |      19 |
| Authority;Node;Kind_authority_hub                                                                         |      18 |
| AuthoritySynthetic;Authority;Kind_authority_synthetic                                                     |      17 |
| Node;PROOF_OF_SERVICE;Violation;Kind_violation                                                            |      17 |
| Judgment_Custody;PT;CS2024_001507_DC;Node;Violation;Kind_violation                                        |      16 |
| Court_address;Node;Violation;Kind_violation                                                               |      15 |
| Node;Uniform_Child_Support_Order_7_21;Violation;Kind_violation                                            |      14 |
| Custody;Parenting_Time;and_Child_Support_Following_Facilitative_Information;Node;Violation;Kind_violation |      11 |

### A3) Authority canonical inventory (quick signal)
From `nodes_neo4j_admin.csv` rows where label includes `AuthorityCanonical` (n=7,132):
See: `authority_canonical_prefix_counts.csv`

Prefix counts:
| prefix   |   count |
|:---------|--------:|
| MCR      |    5416 |
| MCL      |    1716 |

---

## B) Contradiction Map (placeholder acquisition queue)

All three CONTRADICTION_MAP files were byte-identical; normalized copy written as:
- `contradiction_map_normalized.csv`

Current state:
- type: `MISSING_EXHIBIT_PLACEHOLDER`
- status: all `OPEN` (n=141)

Interpretation for LitigationOS:
- Treat this as an **Exhibit Acquisition Queue**, not a contradiction engine yet.
- Each row already contains:
  - exhibit label stub (description)
  - source anchor pin (pin)
  - next-step note (notes)

---

## C) JTC/MSC packet signals (text-bearing PDF)

### C1) JTC Print Order Master — key extracted content
Text extracts saved:
- `JTC_PrintOrder_keypages_p2.txt` (cover/checklist with integrity line + related matters)
- `JTC_PrintOrder_keypages_p498.txt` (start of supplemental complaint with real pin-cites)

High-signal lines (p.2 excerpt):
- Complainant: Andrew J. Pigors
- Respondent Judicial Officer: Hon. Jenny L. McNeill, 14th Judicial Circuit (Family Division)
- Related Matters: Pigors v. Watson (2024-001507-DC); Watson v. Pigors (2023-5907-PP)
- Binder Integrity: SHA-256 recorded (in the PDF text)

High-signal lines (p.498 excerpt):
- “Supplemental Complaint (Updated with Real Pin-Cites)”
- Canon framing stated (Canons 1–3) + pin-cite intent for verification

### C2) Two binder PDFs are image-only
- JTC_MSC_Binder_v5_2025-10-29_19-13-34.pdf
- 2025-10-29_Pigors_v_Watson_MSC-JTC_Exhibits_Binder_v5.pdf

If you want them atomized into Evidence/Quote atoms, the next cycle needs **page-render + OCR** (selective, not full).

---

## D) Extracted “docx-in-zip” supplement text
Source: `205 JSON CSV TXT .zip` (Word container)  
Extract saved: `supplement_docx_extracted.txt`

Key quoted passage candidates (not QUOTELOCK-verified against transcript yet):
- 2024-10-30 PPO show-cause hearing quote candidate:
  - “keep filing and filing and filing… We’re not going to do it again.”
- Administrative failures narrative: secretary emails / HealthWest results / transcript request.

These should become:
- QuoteAtom(s) + ProvenanceRecord(s) (span refs once page/line anchors are known)
- EvidenceAtom(s) for “Secretary Email Chain” + “Transcript Request / No Response”

---

## E) Immediate integration tasks (no redesign)

### E1) Bring nodes_neo4j_admin into the current contract
Action:
- Map `nodes_neo4j_admin.csv` columns into:
  - GraphNode(uid, node_type, label, props)
- Ensure labels map to contract labels (Case, Authority, EvidenceAtom, etc.)

Deliverable (next cycle):
- `neo4j_nodes.csv` and `neo4j_edges.csv` compliant with `graph_contract.yml`

### E2) Convert Contradiction Map to AcquisitionQueue nodes/edges
Action:
- Create nodes: `AcquisitionItem` (or `ExhibitPlaceholder`)
- Edge: `REFERS_TO_SOURCE` (to the source pin / doc)
- Edge: `UNBLOCKS` (to intended Exhibit/EvidenceAtom)

### E3) OCR-selective the image-only binder PDFs
Action:
- Start with: TOC, key orders, and any page that contains adverse findings/derogatory statements.
- Emit QuoteAtoms with strict provenance and spans.

---

## Files emitted in this harvest
- nodes_merged_label_counts.csv
- nodes_neo4j_admin_label_counts.csv
- authority_canonical_prefix_counts.csv
- contradiction_map_normalized.csv
- supplement_docx_extracted.txt
- JTC_PrintOrder_keypages_p2.txt
- JTC_PrintOrder_keypages_p498.txt
- tail_preview.txt
- ATTACHMENT_HARVEST_REPORT.md
