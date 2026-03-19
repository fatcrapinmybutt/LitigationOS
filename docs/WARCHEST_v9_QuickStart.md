# WarChest v9 QuickStart (Michigan-First)

This guide assumes you have a local corpus (exports, filings, PDFs, transcripts, narratives) and you want:
- an authority “WarChest” built from official sources
- a crosswire map that shows which parts of your corpus cite which authorities

## 0) Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 1) Put your corpus in `inputs/`

Recommended layout:

- `inputs/ChatExports/` (ChatGPT exports, logs)
- `inputs/Orders/` (signed orders, notices)
- `inputs/Transcripts/`
- `inputs/Filings/`
- `inputs/PoliceReports/`
- `inputs/Notes/` (MD/TXT)

The pipeline scans `inputs/` recursively.

## 2) Run the pipeline (one command)

### Windows
Double-click `RUN_ALL.cmd`  
or:

```bat
RUN_ALL.cmd
```

### macOS/Linux
```bash
bash RUN_ALL.sh
```

## 3) What gets produced

`out/authority_index.sqlite`  
SQLite DB for lookup (by type + cite string + title + source file).

`out/authority_atoms.jsonl`  
Line-delimited AuthorityAtom objects (portable for GraphRAG / Neo4j import).

`out/crosswire_hits.csv`  
Rows: file_path, line_no (if known), matched_citation, matched_authority_id, confidence, snippet.

## 4) Power modes (optional)

### A) Limit harvesting to one topic (faster)
Example: custody/PT + contempt:

```bash
python tools/harvest_official_sources.py --include "(?i)foc87|foc89|foc65|mc416|mcr|mre|contempt|dvbb" --extract-zips
```

### B) Add more official sources
Edit:
- `sources/official_sources.yaml`

Then re-run.

### C) Crosswire more roots
By default the crosswire step scans `inputs/` and `out/`. You can add more roots:

```bash
python tools/crosswire_evidence_against_authority.py --db out/authority_index.sqlite --roots inputs out "F:/LitigationOS"
```

## 5) Feeding an LLM agent (recommended prompt pattern)

Use `out/crosswire_hits.csv` + `out/authority_atoms.jsonl` as the “ground truth spine”.
Then instruct the agent:
- **No invented facts**
- **No invented authority text**
- **Only cite authority atoms that exist in the index**
- **Anything missing becomes an acquisition task**

## 6) Troubleshooting

- If a download returns 403/404: keep the source in the registry but mark it for manual fetch.
- If a PDF cannot be parsed: it will still be indexed as a file-level atom; you can add a better extractor later.
- If nothing crosswires: confirm your corpus has citations like `MCL 722.27`, `MCR 3.207`, `MRE 803`, `Const 1963 art 1 § 17`, etc.
