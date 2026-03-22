# LitigationOS Agent Registry
## Session 070a961b -- Generated 2026-03-22 13:11 UTC

**Total agents spawned:** 88
**By status:** completed=82, failed=1, partial=1, running=4
**By category:** extraction=22, filing=9, git=6, infrastructure=11, ml=5, monitoring=22, research=13

## Filing Agents (Court-Ready Documents)

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `berry-1983-v2` | general-purpose | DONE | 101 paragraphs, 5 counts, 5 defendants, 18 SCOTUS + 4 Sixth Cir + 3 MI authorities. Prayer $1M+. |
| `criminal-foia-v2` | general-purpose | DONE | 3 docs: FOIA, DISCOVERY_DEMAND, MOTION_SUBSTITUTE_COUNSEL. Court-ready for April 7. |
| `custody-mod` | general-purpose | DONE | 35KB package: Motion + Brief (12 factors) + Affidavit + Proposed Order + COS. 9 authorities. |
| `disqualification-motion` | general-purpose | DONE | 557 lines, 5,563 words. 4-part package. Berry-McNeill chain, Ladas-Hoopes cartel. |
| `federal-forms` | general-purpose | DONE | 4 forms: JS44, AO239 IFP, AO440 Summons x4, AO398/399 Service Waivers. ~45KB total. |
| `ifp-waivers` | general-purpose | DONE | 4 apps: MC20 (14th Circuit), COA 366810, Federal WDMI, MSC. All with sworn affidavits. |
| `jtc-complaint` | general-purpose | DONE | 35.5KB, 7 sections, 30 paragraphs, 33 exhibits. Canon violation analysis. |
| `omnibus-vacate-v2` | general-purpose | DONE | 877 lines, 73.3KB. 6 parts. All 7 police reports included. Albert admission cited 33 times. |
| `ppo-terminate` | general-purpose | DONE | 55.9KB package: Motion (CC 379) + Brief + Affidavit (29 paragraphs) + 18 exhibits. |

## Research & Evidence Agents

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `citation-verify-barretta` | explore | DONE | 348 Mich App 539; 19 NW3d 420 (2023). Confirmed. |
| `citation-verify-souden` | explore | DONE | 303 Mich App 406; 844 NW2d 151 (2013). Confirmed. |
| `conspiracy-analysis` | general-purpose | DONE | Ladas-Hoopes-McNeill 3 judges every Muskegon courthouse. McNeill 906 evidence + 467 violations. |
| `courtpack-intelligence` | general-purpose | DONE | 18 structured sections, 27.7KB. 4 cases, 26 docket entries, 7 missing orders. |
| `elite-drive-scan-v2` | general-purpose | DONE | 24,546 records. Bias ratio 1.7:1 denial, 1.9:1 grants. 394 ex parte pages. |
| `mcneill-profile` | general-purpose | DONE | Disqualification score 92% (46/50). 5059 raw -> 1238 unique violations. Ex parte rate 43.6%. |
| `msc-case-law-verify` | explore | DONE | 33+ citations verified. 90.4% verified current. |
| `msc-evidence-research` | explore | DONE | 10 queries, 83 tables. 5,059 violations, 14,756 evidence quotes. |
| `msc-existing-filings` | explore | DONE | MSC dir: 6 subdirs. 4,568-event chronology encyclopedia. |
| `ocr-crosswire` | general-purpose | DONE | 4,061 files wired, 15,250 pages, 27.4M chars. |
| `ppo-db-research` | explore | DONE | 16-section PPO evidence. All 4 allegations disproven. Albert admission. |
| `query-db-disqualification` | explore | DONE | 5,059 judicial violations. 1,940 bias incidents. 889 ex parte. |
| `strategic-assessment` | general-purpose | DONE | Threat 9.2/10. 14716 quotes, 1238 violations. Convergence 7.90/10. |

## Extraction Agents (Brain DB Population)

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `apex-extractor` | general-purpose | DONE | 530 lines, ijson streaming, MEEK lanes, tree walker. |
| `brain-reroute-wave2` | general-purpose | DONE | 10,953 routed. narrative_context 9,104. session_intelligence 13,976. |
| `chatgpt-extract` | general-purpose | RUNNING | Streaming 3.2GB ChatGPT JSON (4 unique files, ~5100 convos) |
| `find-chatgpt-json` | explore | DONE | 28 JSON + 8 ZIP. Total ~6.5GB raw. |
| `harvest-all-instruction-files` | explore | DONE | Instruction file collection |
| `harvest-brains-apex` | general-purpose | DONE | 6,737 records routed to permanent tables. |
| `harvest-checkpoints` | explore | DONE | Checkpoint data extraction |
| `harvest-copilot-apex` | general-purpose | DONE | 826 new from 102 sessions. Brain DB 38,266 / 448MB. |
| `harvest-db-intelligence` | explore | DONE | Database intelligence extraction |
| `harvest-dedup` | task | DONE | Content-based file deduplication |
| `harvest-desktop-context` | explore | DONE | Desktop file intelligence |
| `harvest-lanes-apex` | general-purpose | DONE | 10,552 lane-enriched, 14,051 relevance-scored. |
| `harvest-pdf-apex` | general-purpose | DONE | 4,918 PDFs (4.4GB), 10,231 records. 958 image-only need OCR. |
| `harvest-schema` | task | DONE | Brain DB schema creation |
| `harvest-session-files` | explore | DONE | Session file collection |
| `harvest-session-store-deep` | explore | DONE | Session store deep mining |
| `harvest-synthesize-apex` | general-purpose | DONE | 323 lines, 23.6KB. 92,246 quotes, 5,059 violations. |
| `harvest-text-apex` | general-purpose | DONE | 448 files, 17,209 messages in 54s. 5 platforms. |
| `mass-pdf-ingest` | general-purpose | DONE | 425 files -> 579 pages. 40 atoms -> evidence_quotes. |
| `new-pdf-ingest` | task | DONE | 2 PDFs extracted. Low relevance. |
| `scan-c-drive-sessions` | explore | DONE | C: drive chat file scan |
| `scan-ij-drives-sessions` | explore | DONE | I:/J: drive chat file scan |

## ML/Intelligence Agents (Wave 2)

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `check-tesseract` | explore | DONE | Tesseract binary YES. pytesseract/Pillow NOT installed. |
| `contradiction-engine` | general-purpose | RUNNING | Two-stage bi-encoder + cross-encoder contradiction detection |
| `run-meek-enricher` | task | RUNNING | MEEK lane detection on newly extracted records |
| `verify-ml-env` | explore | DONE | ML venv package verification |
| `verify-ml-venv` | explore | DONE | All packages OK. all-MiniLM-L6-v2 model cached. |

## Infrastructure Agents

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `build-db-module` | general-purpose | DONE | Database module construction |
| `create-command-runner` | general-purpose | DONE | MCP command runner server built |
| `create-engine-stubs` | general-purpose | DONE | Engine module stubs created |
| `create-mcp-db` | explore | DONE | MCP database module created |
| `fix-mcp-deps` | task | DONE | MCP dependency installation |
| `fix-python-env` | task | DONE | Python env diagnostics and repair |
| `fix-python312` | task | DONE | Python 3.12.10 + .ml_venv 1045MB. |
| `install-apex-nlp` | task | PARTIAL | dateparser OK, sentence-transformers FAILED on Python 3.14. |
| `ml-venv-setup` | task | FAILED | Used 3.14 instead of 3.12. Retried via fix-python312. |
| `msgspec-install` | task | DONE | msgspec 0.20.0 on Python 3.14 |
| `space-reclaim` | task | RUNNING | Moving 12_ARCHIVES from C: to J: |

## Monitoring & Diagnostic Agents

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `brain-db-schema` | explore | DONE | Schema column verification |
| `check-brain-db` | task | DONE | Brain DB progress audit |
| `check-brain-db-schema` | task | DONE | Brain DB schema verification |
| `check-commit-pattern` | explore | DONE | Git commit pattern verification |
| `check-existing-data` | explore | DONE | Pre-existing data audit |
| `check-extractor` | explore | DONE | Extractor progress check |
| `check-manifest` | task | DONE | Manifest status verification |
| `check-paths-and-schema` | explore | DONE | Path/schema verification |
| `config-audit` | explore | DONE | Config file audit |
| `diagnose-db-py` | explore | DONE | db.py GOAWAY diagnosis |
| `diagnose-goaway` | explore | DONE | GOAWAY 503 error analysis |
| `exact-schemas` | explore | DONE | Exact column names for routing |
| `explore-chat-dirs` | explore | DONE | Chat directory structure mapping |
| `explore-pdf-setup` | explore | DONE | PDF extraction setup verification |
| `explore-session-files` | explore | DONE | Session file structure mapping |
| `find-broken-things` | explore | DONE | Codebase health audit |
| `find-pydantic-models` | explore | DONE | Pydantic model inventory |
| `find-text-files` | task | DONE | Text file inventory scan |
| `full-asset-inventory` | explore | DONE | Drive and file inventory scan |
| `mcp-server-status` | explore | DONE | Initial MCP server diagnostics |
| `prior-sessions-work` | explore | DONE | Session store intelligence harvest |
| `verify-dbs-exist` | explore | DONE | Brain DB 431MB. Lit DB 437MB. |

## Git/Save Agents

| Agent ID | Type | Status | Result |
|----------|------|--------|--------|
| `git-commit-apex` | task | DONE | commits b2722e98 + 5f149060 |
| `git-commit-condensation` | task | DONE | Session condensation commit |
| `git-commit-extractor` | task | DONE | commit 6d0d6c5d |
| `git-save-wave2` | task | DONE | Commit 7020d67c |
| `run-brain-router` | task | DONE | Brain router execution |
| `save-progress` | task | DONE | Checkpoint commit 124b7510 |
