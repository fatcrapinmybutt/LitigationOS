# Download Link Reliability Rules
- Create artifacts under /mnt/data with ASCII-safe filenames.
- Verify file exists and nonzero size.
- ZIPs must pass zipfile.testzip()==OK.
- Compute SHA-256.
- Include DOWNLOAD_AUDIT.md, manifest.json, manifest.csv, and this document.
- Enforce size gate <=90MB via sharding or externalizing >=10MB artifacts with pointers.
