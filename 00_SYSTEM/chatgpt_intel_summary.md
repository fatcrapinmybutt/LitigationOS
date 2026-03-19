# ChatGPT Litigation Intelligence Summary
Generated: 2026-03-04T11:47:17.924196

## Overview
Processed all ChatGPT conversation data with litigation-relevance classification 
and FTS5 full-text search indexing.

## Source
- Table: `chatgpt_conversations` (168,949 rows, 2,332 conversations)
- Processing time: 121.0s

## Statistics
- **Total messages**: 168,949
- **Total words**: 62,371,965
- **Unique conversations**: 2,332
- **Litigation-relevant messages**: 125,017 (74.0%)
- **Litigation-relevant conversations**: 2,302 (98.7%)
- **Litigation-relevant words**: 60,454,906

## Messages by Role
| Role | Count |
|------|-------|
| assistant | 80,765 |
| user | 60,473 |
| tool | 27,711 |

## Top Litigation-Relevant Conversations
| Title | Messages | Words |
|-------|----------|-------|
| Litigation OS overview | 4064 | 555,405 |
| Env Variables and Secrets | 4041 | 732,105 |
| Mega systems graphs THIs ONE | 1199 | 408,969 |
| No content provided | 1086 | 598,538 |
| Legal IQ system blueprint | 926 | 460,984 |
| MindEye2 completed, download latest files | 891 | 179,027 |
| Eviction fact chain | 866 | 184,316 |
| Litigation OS overview update | 780 | 184,677 |
| Litigation Strategy and Tactics | 699 | 127,389 |
| Next LitigationOS harvest cycle instructions | 688 | 795,520 |
| Activate top systems | 674 | 221,931 |
| PPO Contempt Strategy Email | 621 | 121,338 |
| Branch · Michigan Legal Framework .md | 617 | 11,199 |
| Litigation Strategy Plan | 571 | 108,716 |
| Lawsuit Draft against Watsons | 551 | 278,167 |
| Federal Filing Requirements Summary | 532 | 99,588 |
| Eviction Relief and Custody | 523 | 119,350 |
| Activate litigation OS | 507 | 132,680 |
| Automated Legal Orchestration | 486 | 2,690,036 |
| Mainframe activation complete | 474 | 210,278 |
| Real-time Michigan legal mapping launched | 472 | 314,044 |
| Chat synthesis prompt | 467 | 419,516 |
| Files expired, please re-upload | 457 | 82,442 |
| WDMI PARSING | 437 | 164,085 |
| Omnicore Litigation Status | 413 | 83,626 |
| Branch · Michigan COA Filing Blueprint | 403 | 31,224 |
| Court Bypass Strategy | 379 | 59,802 |
| Branch · Parenting time suspension prompt | 366 | 114,894 |
| Google Drive connection setup | 358 | 111,582 |
| Parenting time suspension prompt | 357 | 238,391 |

## Note on ChatGPT Export Files
The split part files in `G:\AI\` (`conversations.json (1).part01` through `.part20`) 
are in a **binary/encrypted format** (magic bytes: `04 E4 40 E7`) that is not standard 
gzip, zip, or 7z. They cannot be reassembled without the original splitting tool or 
decryption key. The existing `chatgpt_conversations` table (168,949 rows) was used as 
the primary data source.

## Database
- Table: `chatgpt_litigation_intel`
- FTS5: `chatgpt_litigation_intel_fts`
- DB: `C:\Users\andre\LitigationOS\litigation_context.db`

## Keyword List Used for Classification
litigation, court, custody, evidence, filing, motion, judge, mcneill, watson, shady oaks, ppo, appeal, coa, court of appeals, hearing, order, petition, respondent, petitioner, plaintiff, defendant, attorney, lawyer, legal, statute, mcl, michigan, family court, circuit court, probate... (85 total keywords)
