# ChatGPT export ingest (user messages only)

This pack includes `tools/ingest_chatgpt_export_user_messages.py`.

It extracts **only** operator/user messages from a ChatGPT data export (zip or folder),
and emits a pointer-locked ledger (`jsonl` + `txt` + `csv`).

Why it matters:
- It gives you the complete, verbatim operator narrative corpus to run against the MI WarChest.
- It becomes the authoritative source for “what Andrew said” without hallucinations.

Run (on your workstation):
```
python tools/ingest_chatgpt_export_user_messages.py --input <export.zip|folder> --outdir out/chat_export
```

Filter example:
```
python tools/ingest_chatgpt_export_user_messages.py --input export.zip --outdir out/chat_export --filter "(PPO|McNeill|Watson|custody|parenting time|contempt)"
```