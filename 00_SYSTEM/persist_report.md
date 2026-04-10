# Dossier Persistence Report
**Elapsed:** 20.0s

| Metric | Count |
|--------|-------|
| Raw quotes loaded | 1500 |
| Artifacts filtered | 662 |
| Internal duplicates | 412 |
| DB duplicates | 10 |
| **New quotes inserted** | **416** |
| DB total (before) | 175,223 |
| DB total (after) | 175,639 |

## Lane Breakdown

- **Lane A**: 75
- **Lane B**: 1
- **Lane D**: 49
- **Lane E**: 288
- **Lane F**: 3

## Artifact Filter Patterns

Filtered 662 entries matching:
- JSON/dict syntax, pipeline run IDs, MEEK tags
- SQL statements, Python code, file paths
- System names (LitigationOS, MANBEARPIG, SINGULARITY)
- Known noise sources (encyclopediaUNIVERSE, FileProcessingLog)
