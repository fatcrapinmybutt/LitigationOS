# LOCAL lane Organizer Stack

This lane is a safe-by-default organizer for local drives (Windows paths supported).
It is built around a plan-first workflow so you can audit changes before anything moves.

## Workflow
1) 00_SETUP.cmd
   - Creates a local venv under LOCAL\.venv
   - Installs requirements

2) 10_PLAN.cmd
   - Scans the configured root paths
   - Produces a plan JSON under F:\LitigationOS\_OrganizeAI\LOCAL\RUN_YYYYMMDD_HHMMSS\plan.json

3) 15_VALIDATE.cmd
   - Validates a plan JSON and writes validate.json

4) 20_APPLY.cmd
   - Applies the plan (moves and renames) after a typed safety gate
   - Writes an undo JSON in the same RUN folder

5) 30_SELF_TEST.cmd
   - Runs the local self-test twice if needed

6) 40_UNDO_LAST.cmd
   - Uses the most recent undo JSON to roll back the last apply

## Notes
- Rename behavior is conservative and can be disabled or tuned in config.yaml.
- Nothing happens outside the paths you explicitly set as roots.
- If you mirror to Google Drive with rclone, keep rename settings aligned between LOCAL and GDRIVE lanes.
