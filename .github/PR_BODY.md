chore(merge): import multiple repositories into LitigationOS

This PR imports the following repositories into the LitigationOS repository under the `imports/` directory:

- fatcrapinmybutt/fredprime-legal-system
- fatcrapinmybutt/FRAUD
- fatcrapinmybutt/the_manbearpig
- fatcrapinmybutt/CourtRules
- fatcrapinmybutt/MICHIGAN-HIGHER-COURTS
- fatcrapinmybutt/Michigan-MCLA

Details
- Import method: Option A (copy file contents only). Git history from the source repositories is NOT preserved.
- Placement: Each repo will be placed in `imports/<repo-name>/`.
- Branch: merge/all-repos-2026-06-28

Post-merge notes for reviewers
- Verify that filenames and directory structure under `imports/` are correct.
- If any file collisions or unexpected large binaries were present, they will appear under the respective `imports/<repo>/` folder.
- If you want full git history preserved for any repo, do not merge this PR; instead follow the instructions in IMPORT_MANIFEST.md for a subtree/history-preserving import.

