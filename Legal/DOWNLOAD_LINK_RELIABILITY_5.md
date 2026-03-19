# DOWNLOAD_LINK_RELIABILITY.md
Rule: Before emitting any sandbox download link, the assistant must:
1) Create the file under /mnt/data with an ASCII-safe filename.
2) Verify existence and nonzero size.
3) If ZIP: run zipfile.testzip()==None (OK).
4) Compute SHA-256 and record in DOWNLOAD_AUDIT.md and manifest.
5) Include DOWNLOAD_AUDIT.md, manifest.json, manifest.csv, and this document inside the bundle.
6) Enforce Size Gate: <=90MB (prefer <=45MB); if exceeded, shard or externalize >=10MB artifacts with inventories.
7) Print the sandbox link as the final line of the response with no text after it.
