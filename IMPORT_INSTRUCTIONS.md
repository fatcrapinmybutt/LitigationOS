# Merge repositories into LitigationOS (branch: merge/all-repos-2026-06-28)

This branch was prepared by the repository owner and assistant to consolidate several related repositories into LitigationOS. It contains helper files and a script to perform the import locally:

- scripts/import_repos.sh — clones and copies each source repo into imports/<repo>/
- IMPORT_MANIFEST.md — lists repos and metadata
- .github/PR_BODY.md — proposed PR description

Next steps (automated workflow):
1. Run the import script locally or in a CI runner with write access to the repository:
   - bash scripts/import_repos.sh
2. Review the new files in `imports/`.
3. Commit and push the imports to this branch (merge/all-repos-2026-06-28):
   - git add imports/ && git commit -m "chore(merge): import repositories into imports/" && git push origin merge/all-repos-2026-06-28
4. Open or update a Pull Request targeting the default branch and review/merge.

If you would like me to attempt the import now using the GitHub API from this environment (subject to API limits), reply and I will proceed. Otherwise, run the script in your environment and I will continue with PR preparation once the files are present.
