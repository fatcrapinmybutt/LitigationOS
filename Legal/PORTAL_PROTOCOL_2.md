# Portal protocol (v4)

## Signals (local mode)
Directory: `~/.mbp_portal/signal/`
- `open`  => allow tick to enqueue work
- `close` => tick will not enqueue new work (existing queue remains)

## Queue
- `~/.mbp_portal/queue/*.json` (pending)
- `queue/inprogress/*.json` (claimed)
- `queue/done/*.json` (finished)
- `queue/failed/*.json` (failed, with error field)

## Provenance per run
`~/.mbp_portal/runs/<profile>/<run_id>/`
- run_meta.json
- run_result.json
- rclone/combined.txt (if enabled)
- rclone/dest_after.lsf (if enabled)
- rclone/rclone.log
- mirror_index.csv
- hook_results.json
- cyclepack.json
