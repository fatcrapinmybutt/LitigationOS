# GEMINI.md — PublicLitigationOS Harvest Workspace

You are operating inside a **trusted** workspace that contains a local harvesting + indexing runner for Michigan litigation records.

## Prime objective
1) Run the local harvester (scripts/RUN.ps1 or RUN.cmd) to generate an evidence/record index.
2) Read `./.out/<RUN_ID>/DASHBOARD.md` and `NEXT_PROMPT.md`.
3) Execute the synthesis workflow in `prompts/`:
   - issue spotting, negative connotations, due-process defects, preservation gaps
   - vehicle selection (trial/COA/MSC/JTC) based on Michigan-only authorities
   - draft court-grade packets with verified citations

## Hard rules
- Do **not** invent facts, dates, or quotes.
- Treat user statements as assertions; treat opposing statements as allegations unless supported by record artifacts.
- Only cite Michigan authorities (MCR/MCL/MRE/benchbooks/caselaw) and provide pinpoint cites.
- Prefer extracting and quoting from the harvested record before analysis.

## Where outputs live
- `.out/<RUN_ID>/` contains inventory, timeline, chunks, and the prompt spine.

