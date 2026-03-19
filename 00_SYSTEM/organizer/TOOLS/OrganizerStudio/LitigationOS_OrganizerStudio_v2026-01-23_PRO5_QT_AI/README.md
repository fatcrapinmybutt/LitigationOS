# OrganizerStudio PRO (Qt Edition)

OrganizerStudio is a plan-first organizer with a professional desktop GUI and a Windows executable build pipeline.

## What it does
- LOCAL lane: scans one or more local roots, proposes a plan to denest, bucketize, and rename safely
- GDRIVE lane: does the same inside a single scoped Google Drive folder subtree
- PLAN then VALIDATE then APPLY is enforced in the GUI

## Safety model
- You always review the plan before apply
- APPLY is disabled until VALIDATE succeeds
- Undo artifacts are produced for best-effort rollback

## Run the GUI
1) Unzip to: F:\LitigationOS\_TOOLS\OrganizerStudio\
2) Double click: LAUNCH_STUDIO_QT.cmd
3) In the GUI:
   - Set LOCAL roots and config path
   - Set GDRIVE scoped folder ID and config path
   - Use PLAN PREVIEW to select a plan file and load rows
   - Click VALIDATE, then APPLY

## Build an executable
1) Double click: BUILD_EXE_QT.cmd
2) Run: dist\OrganizerStudio\OrganizerStudio.exe

## Google Drive setup
You need two files inside the GDRIVE folder:
- credentials.json (OAuth client secrets)
- token.json (auto-created after the first login)

## Drive rename test
Use this to verify rename permissions before a full apply:
python GDRIVE\rename_test.py --file-id <ID> --new-name "TestName.txt" --rollback

## Output locations
- LOCAL: F:\LitigationOS\_OrganizeAI\LOCAL\RUN_*
- GDRIVE: F:\LitigationOS\_OrganizeAI\GDRIVE\RUN_*
- State: F:\LitigationOS\_OrganizeAI\STUDIO\state.json

## AI MODELS stage
The AI stage uses embeddings models to provide semantic suggestions.
Recommended embedding model: nomic-ai/nomic-embed-text-v1.5 (Apache-2.0 license).
Alternative: BAAI/bge-small-en-v1.5 (MIT license).

Steps:
1) Run LAUNCH_STUDIO_QT.cmd
2) Open AI MODELS tab
3) Click Install AI deps
4) Click Download model
5) Click Smoke test embeddings
