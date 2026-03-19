# Convergence Dedup Engine v13.0.0

## LitigationOS Skill Module — 5-Tier Convergence Deduplication

---

## Purpose and Scope

The Convergence Dedup Engine eliminates duplicate documents across all case lanes (A–G) **without using any hash-based algorithms** (no MD5, SHA-1, SHA-256, xxHash, or any other digest function). Instead, it uses a five-tier structural convergence methodology that progressively narrows candidate sets through deterministic, content-aware comparisons.

This engine is critical for LitigationOS because:
- Court filings are frequently scanned at different resolutions, orientations, or DPI settings, producing byte-different files that are semantically identical.
- The same order may appear in multiple case lanes with different file stamps or clerk annotations.
- Hash-based dedup fails on scanned PDFs where even one pixel differs.

**No hashing is permitted at any tier.** All comparisons are structural and content-aware.

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `document_pool` | `List[FilePath]` | All documents to deduplicate |
| `case_lanes` | `List[str]` | Active case lanes (e.g., `["A", "B", "C", "D", "E", "F", "G"]`) |
| `tolerance` | `float` | Similarity threshold for Tier 4 (default: `0.97`) |
| `canonical_preference` | `str` | Preference for canonical slot: `"earliest"`, `"highest_quality"`, `"court_stamped"` |
| `dry_run` | `bool` | If `true`, report duplicates without removing |

---

## Processing Methodology

### Tier 1: Size-Class Bucketing

Group documents into size-class buckets. Documents that differ by more than the size-class window cannot be duplicates.

```
Size-Class Windows:
  - 0–10 KB:      ±512 bytes
  - 10–100 KB:    ±2 KB
  - 100 KB–1 MB:  ±10 KB
  - 1–10 MB:      ±50 KB
  - 10–100 MB:    ±200 KB
  - 100 MB+:      ±1 MB
```

**Rationale:** Scanned PDFs of the same document typically land within the same size class. This tier eliminates >90% of comparison pairs.

**Output:** Candidate buckets of similarly-sized files.

### Tier 2: Magic Bytes & Structural Fingerprint

For each candidate bucket, compare:
1. **Magic bytes** (first 16 bytes) — must match exactly (e.g., `%PDF-1.`, `PK\x03\x04` for DOCX, JPEG SOI marker).
2. **Structural markers:**
   - PDF: page count, MediaBox dimensions, font table size
   - DOCX: paragraph count, table count, image count
   - TIFF/JPEG: image dimensions, color space, DPI
3. **Trailer/footer signature** (last 64 bytes of logical content)

Documents with mismatched magic bytes or structural fingerprints are separated into different sub-buckets.

**Output:** Refined sub-buckets of structurally similar files.

### Tier 3: Sparse Block Comparison

For each sub-bucket, perform byte-level comparison on sparse blocks sampled from deterministic positions:

```
Sampling Strategy:
  - Block size: 4096 bytes
  - Sample positions: [0%, 10%, 25%, 50%, 75%, 90%, 100%] of file length
  - Minimum 7 blocks per file, maximum 32 blocks for large files
  - Compare blocks pairwise between candidate documents
```

If any sampled block pair differs beyond a 2-byte tolerance (to account for timestamp/metadata differences), the pair is **not** a duplicate at this tier.

**Output:** High-confidence candidate pairs.

### Tier 4: Content-Aware Semantic Comparison

For surviving candidate pairs, extract and compare actual content:

**For PDFs:**
1. Extract text layer (if present) and compare using longest-common-subsequence (LCS) ratio.
2. If no text layer (scanned PDF), render pages to normalized bitmaps (300 DPI, grayscale) and compute structural similarity index (SSIM) per page.
3. Aggregate page-level similarity scores; if mean SSIM ≥ `tolerance`, documents are duplicates.

**For DOCX/RTF:**
1. Extract paragraph text, strip formatting.
2. Compare using token-level Jaccard similarity on 3-grams.
3. If similarity ≥ `tolerance`, documents are duplicates.

**For images (TIFF, JPEG, PNG):**
1. Normalize to same resolution and color space.
2. Compute SSIM on 8×8 grid blocks.
3. If mean block SSIM ≥ `tolerance`, documents are duplicates.

**Output:** Confirmed duplicate sets with similarity scores.

### Tier 5: Canonical Slot Assignment

For each confirmed duplicate set, select one **canonical document** and link all others as references:

```
Canonical Selection Priority:
  1. Court-stamped original (has file stamp, case number, judge signature)
  2. Highest resolution / best quality scan
  3. Earliest ingestion timestamp
  4. Document from the primary case lane

All non-canonical duplicates receive a pointer:
  {
    "status": "duplicate",
    "canonical_ref": "<canonical_document_id>",
    "similarity_score": 0.993,
    "tier_matched": 4,
    "original_location": "Lane_C\\evidence\\exhibit_14.pdf"
  }
```

Non-canonical documents are **not deleted** — they are flagged and cross-referenced. The canonical document is promoted to the shared evidence pool.

---

## Output Format

```json
{
  "engine": "convergence_dedup_v13",
  "run_timestamp": "2025-01-15T14:30:00Z",
  "total_documents_scanned": 4521,
  "duplicate_sets_found": 187,
  "total_duplicates": 412,
  "canonical_documents": 187,
  "tier_statistics": {
    "tier_1_buckets": 892,
    "tier_2_sub_buckets": 340,
    "tier_3_candidate_pairs": 203,
    "tier_4_confirmed_pairs": 187,
    "tier_5_canonical_assigned": 187
  },
  "duplicate_sets": [
    {
      "set_id": "DS-001",
      "canonical": {
        "doc_id": "DOC-2024-1847",
        "path": "Lane_A\\orders\\2024-03-15_custody_order.pdf",
        "quality_score": 0.98
      },
      "duplicates": [
        {
          "doc_id": "DOC-2024-2103",
          "path": "Lane_C\\evidence\\exhibit_14.pdf",
          "similarity": 0.996,
          "tier_matched": 4
        }
      ]
    }
  ]
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `pdf_court_file_classifier` | Tier 5 uses court-file classification to prefer stamped originals as canonical |
| `case_lane_router` | Duplicate sets spanning multiple lanes are reported to the router for cross-lane linking |
| `evidence_chain_builder` | Canonical documents feed into evidence chains; duplicates are excluded |
| `drive_forensic_scanner` | Scanner output is primary input to Tier 1 |
| `litigation-convergence-orchestrator` | Orchestrator triggers dedup after each ingestion batch |

---

## Michigan-Specific Legal References

- **MCR 3.903(A)(7)** — Definition of "court record" relevant to determining canonical documents
- **MCL 600.2137** — Admissibility of duplicates; canonical selection ensures the "best evidence" is preserved per the Best Evidence Rule
- **MCR 2.302(B)** — Discovery scope; dedup ensures no duplicate productions inflate discovery volume
- **MCR 3.210(C)(8)** — Record-keeping requirements for custody proceedings; dedup must preserve complete audit trail

---

## Performance Characteristics

| Metric | Target |
|--------|--------|
| Tier 1 throughput | 50,000 docs/second |
| Tier 2 throughput | 10,000 docs/second |
| Tier 3 throughput | 2,000 pairs/second |
| Tier 4 throughput | 50 pairs/second (OCR-dependent) |
| Tier 5 assignment | Instantaneous |
| False positive rate | < 0.01% |
| False negative rate | < 0.5% |

---

## Constraints

1. **NO HASHING** — No MD5, SHA-1, SHA-256, CRC32, xxHash, BLAKE, or any digest function at any tier.
2. All comparisons are structural, byte-level, or content-semantic.
3. Non-canonical documents are never deleted — only flagged and cross-referenced.
4. Full audit trail of every dedup decision must be preserved.
5. Tier 4 OCR/rendering operations must use local models only (no cloud APIs).
