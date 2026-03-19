LLM AUTO-PLAN — MI_SUPERPIN_ATLAS_v2026-02-14
Goal: Autonomous Michigan litigation harvesting and drafting.

1) Load all *.txt files in lexical order. Treat them as the operating spec.
2) Ask for filesystem access OR request an inventory export (manifest of files).
3) Execute the 10-cycle protocol from 01_SUPERPIN_MASTER_PROMPT_GEMINI_IDE.txt.
4) Hard gates:
   - no facts without record pinpoints
   - no quotes unless exact
   - no deadlines unless entry date pinned
   - Michigan-first authority only, unless overlay explicitly requested
5) Outputs must be written into /LitigationOS_Output/ with append-only discipline.
