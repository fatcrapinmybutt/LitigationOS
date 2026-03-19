CyclePack_Authority_Dockets_v1

Purpose
- Integrate your uploaded authority graph + docket artifacts into a standard, location-agnostic workspace layout.
- Produce an audit report and provide scripts to sanity-check payloads.

Key finding
- intake/DOCKETSPPO.zip failed ZipFile validation in this environment (see reports/audit_summary.json).
  This usually means: corrupt zip, non-zip file with .zip extension, or unsupported archive format.

What to do
1) Run: scripts/authority_store_sanity_check.py --root <this_folder>
2) If DOCKETSPPO.zip is truly a zip on your machine, re-export it (or upload a fresh copy) and rerun:
   scripts/extract_archive.py --root <this_folder>

No destructive operations are performed by any script.
