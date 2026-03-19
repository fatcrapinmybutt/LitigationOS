# SavePoint Browser (FIX10)

## Where it looks
The SavePoint tab scans the discovered root for JSON files under:
- `sp/`
- `savepoints/`
- `checkpoints/`

It caps at 2000 JSON files for safety.

## What you can do
- Refresh list
- Click a row to preview content
- Open selected JSON in the default editor

## Recommended convention
Keep stage checkpoints under:
- `sp/<stage>/checkpoint_*.json`
