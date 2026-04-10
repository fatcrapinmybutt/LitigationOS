"""Self-Improvement CI — Emit structured learning candidates and promotion proposals."""
import json
from datetime import datetime

output = {
    "self_improvement_ci": {
        "source": {
            "session_id": "67f25dc5-1351-46f4-9662-f53a773f648d",
            "commit_sha": "1d9158c77",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_name": "Research LitigationOS Databases",
            "checkpoints_analyzed": 243,
            "commits_analyzed": 30,
            "git_history_window": "2026-03-29 to 2026-04-04"
        },
        "candidates": [
            {
                "pattern_key": "harden.filing_contamination",
                "source": "qa_audit + git_history (4 filings, 8 fix events)",
                "recurrence_count": 8,
                "first_seen": "2026-03-29",
                "last_seen": "2026-04-03",
                "severity": "critical",
                "category": "filing_safety",
                "suggested_rule": "Rule 3a: AUTOMATED CONTAMINATION SWEEP — Before any filing transitions from DRAFT→QA_REVIEW, run automated grep for: engine names (*Engine, *_engine), file paths (C:\\Users\\, LitigationOS), DB refs (evidence_quotes, litigation_context.db), AI scoring (EGCP, MEEK, confidence_score), tool names (MANBEARPIG, FRED_OBJECTION). ONE HIT = QA FAIL. No exceptions.",
                "evidence_commits": ["ce39bdaef", "ceb7a353c", "76b216b39", "cf1f4fad8"],
                "affected_filings": ["F03", "F05", "F06", "F08"],
                "promotion_ready": True,
                "promotion_target": ".github/copilot-instructions.md (Rule 3 expansion)"
            },
            {
                "pattern_key": "harden.dynamic_day_counts",
                "source": "qa_audit + git_history (7 fix events across 4 filings)",
                "recurrence_count": 7,
                "first_seen": "2026-03-29",
                "last_seen": "2026-04-03",
                "severity": "critical",
                "category": "filing_safety",
                "suggested_rule": "Rule 29: DYNAMIC DAY COUNTS — In ANY court filing, separation duration MUST be computed as (filing_date - date(2025,7,29)).days at RENDER TIME. Hardcoded numbers like '230 days' or '329 days' are FORBIDDEN — they go stale the moment they're written. Typst templates must use a compute function. Markdown drafts must use [COMPUTE: separation_days] placeholder that the QA engine resolves.",
                "evidence_commits": ["8839fef58", "f56786b46", "faf8536e7", "ce39bdaef"],
                "affected_filings": ["F04", "F05", "F08", "F09"],
                "promotion_ready": True,
                "promotion_target": ".github/copilot-instructions.md (new Rule 29)"
            },
            {
                "pattern_key": "harden.stdout_contamination",
                "source": "engine_debug_findings (35 files, 2 patterns)",
                "recurrence_count": 35,
                "first_seen": "2026-04-02",
                "last_seen": "2026-04-03",
                "severity": "critical",
                "category": "engine_safety",
                "suggested_rule": "NEVER use sys.stdout = open(...) or sys.stdout.reconfigure() at module level. These corrupt stdout for ALL importers and break logging, MCP servers, and agent communication. If encoding fix is needed, wrap in try/except inside 'if __name__ == \"__main__\"' block only.",
                "evidence_commits": ["cf1f4fad8"],
                "affected_files": "35 files across chimera, chronos, oracle, nemesis, forge, lexicon, intake, rebuttal, narrative + 25 others",
                "promotion_ready": True,
                "promotion_target": ".github/instructions/ (new engine-rules or existing sqlite)"
            },
            {
                "pattern_key": "harden.schema_validation",
                "source": "engine_debug_findings (4 schema mismatches)",
                "recurrence_count": 4,
                "first_seen": "2026-04-02",
                "last_seen": "2026-04-03",
                "severity": "critical",
                "category": "database_safety",
                "suggested_rule": "Already covered by Rule 16 (Schema-verify) but needs ENFORCEMENT: Every engine constructor that touches a DB table MUST call PRAGMA table_info() on first use and cache the schema. CREATE TABLE IF NOT EXISTS does NOT validate existing schema. Use adaptive column helpers.",
                "evidence_items": ["IntakePipeline.sha256", "EventHorizon str→Path", "filing_engine.db missing", "pipeline.db missing"],
                "promotion_ready": True,
                "promotion_target": ".github/instructions/sqlite.instructions.md (strengthen Rule 16)"
            },
            {
                "pattern_key": "harden.fabricated_stats",
                "source": "user_feedback + qa_audit (3 filings)",
                "recurrence_count": 3,
                "first_seen": "2026-04-01",
                "last_seen": "2026-04-03",
                "severity": "high",
                "category": "filing_safety",
                "suggested_rule": "Rule 30: NO AGGREGATE AI STATISTICS IN FILINGS — Never include AI-generated aggregate counts in court documents (e.g., '241,160 keyword hits', '12,478 person references'). Only cite statistics that are (a) individually verifiable from a specific DB query, (b) small enough to be hand-counted or spot-checked, and (c) meaningful to a non-technical reader like a JTC commissioner.",
                "evidence_items": ["F06 JTC '241,160 keyword hits' flagged by user", "F05 MSC fabricated stats purged", "F03 keyword counts removed"],
                "promotion_ready": True,
                "promotion_target": ".github/instructions/legal-document-apex.instructions.md"
            },
            {
                "pattern_key": "harden.placeholder_prevention",
                "source": "qa_audit + git_history",
                "recurrence_count": 5,
                "first_seen": "2026-03-29",
                "last_seen": "2026-04-02",
                "severity": "high",
                "category": "filing_quality",
                "suggested_rule": "Already covered by Rule 17 (DB-first) and legal-document-apex §3, but needs AUTOMATED ENFORCEMENT: QA gate must regex-scan for \\[ANDREW_REQUIRED\\], \\[VERIFY\\], \\[COMPUTE\\], \\[INSERT\\], \\[TBD\\], \\[PLACEHOLDER\\], \\[TODO\\]. Each hit triggers mandatory 3-source search (DB + filesystem + summaries) before the placeholder can survive.",
                "promotion_ready": True,
                "promotion_target": ".github/instructions/legal-document-apex.instructions.md (strengthen §3)"
            },
            {
                "pattern_key": "harden.path_centralization",
                "source": "engine_debug_findings",
                "recurrence_count": 43,
                "first_seen": "2026-04-02",
                "last_seen": "2026-04-03",
                "severity": "high",
                "category": "code_quality",
                "suggested_rule": "All DB paths MUST use shared.get_db() or shared.get_db_path(). Hardcoded r'C:\\Users\\andre\\...' paths are FORBIDDEN in any engine, brain, or script under 00_SYSTEM/. Currently 43 files and 18/22 engines violate. Enforcement: grep -r 'C:\\\\Users\\\\andre' 00_SYSTEM/engines/ should return 0 hits.",
                "promotion_ready": True,
                "promotion_target": ".github/instructions/sqlite.instructions.md"
            },
            {
                "pattern_key": "quality.zombie_artifact_hygiene",
                "source": "prompt_audit",
                "recurrence_count": 34,
                "first_seen": "2026-04-03",
                "last_seen": "2026-04-04",
                "severity": "high",
                "category": "prompt_quality",
                "suggested_rule": "When a SINGULARITY superskill is forged by absorbing predecessor skills, the predecessors MUST be moved to an archive directory within 1 session. 34 pre-SINGULARITY zombie skills (797K chars) currently pollute the skill catalog. Also: move orphan engine dirs (7) and empty engine dirs (4) to 11_ARCHIVES/.",
                "action_items": ["Archive 34 zombie skills to .agents/skills/_archived/", "Archive 7 orphan engine dirs to 11_ARCHIVES/", "Archive 4 empty engine dirs to 11_ARCHIVES/", "Move 35 standalone engine scripts to 00_SYSTEM/engines/_scripts/"],
                "promotion_ready": True,
                "promotion_target": "Direct action (archive, not rule)"
            },
            {
                "pattern_key": "quality.prompt_budget_control",
                "source": "prompt_audit",
                "recurrence_count": 1,
                "first_seen": "2026-04-03",
                "last_seen": "2026-04-04",
                "severity": "high",
                "category": "prompt_quality",
                "suggested_rule": "Always-on prompt (copilot-instructions.md + instruction files) MUST stay under 5% of context window (~10K tokens for 200K). Currently at 9.5% (18,931 tokens). Action: deduplicate rules across layers, move reference data to DB lookups, merge stub files.",
                "promotion_ready": True,
                "promotion_target": ".github/copilot-instructions.md (restructure)"
            },
            {
                "pattern_key": "quality.stale_prompt_data",
                "source": "prompt_audit",
                "recurrence_count": 6,
                "first_seen": "2026-03-29",
                "last_seen": "2026-04-04",
                "severity": "high",
                "category": "prompt_quality",
                "suggested_rule": "DB row counts in instruction files MUST be marked as approximate with 'query live per Rule 20' caveat, OR removed entirely. Current contradictions: evidence_quotes cited as 175K/269K/116K, authority_chains as 167K/227K. These stale numbers erode trust.",
                "conflicting_values": {
                    "evidence_quotes": ["175K", "269K", "116K"],
                    "authority_chains_v2": ["167K", "227K", "118K"],
                    "michigan_rules": ["19.8K", "13.6K"]
                },
                "promotion_ready": True,
                "promotion_target": ".github/copilot-instructions.md + all instruction files"
            },
            {
                "pattern_key": "quality.rule_deduplication",
                "source": "prompt_audit",
                "recurrence_count": 15,
                "first_seen": "2026-04-03",
                "last_seen": "2026-04-04",
                "severity": "medium",
                "category": "prompt_quality",
                "suggested_rule": "Each rule should have ONE canonical location. Other files reference the rule number (e.g., 'per Rule 3'), not restate it. Exception: child safety (L.D.W.) may appear in multiple layers as defensive depth.",
                "duplication_counts": {"L.D.W./MCR_8.119": 15, "no_AI_refs": 8, "pro_se": 8, "FTS5_safety": 5, "schema_verify": 5},
                "promotion_ready": True,
                "promotion_target": ".github/copilot-instructions.md (restructure)"
            },
            {
                "pattern_key": "quality.test_coverage",
                "source": "engine_debug_findings",
                "recurrence_count": 1,
                "first_seen": "2026-04-03",
                "last_seen": "2026-04-03",
                "severity": "medium",
                "category": "code_quality",
                "suggested_rule": "Every engine dir MUST have at minimum a smoke test: import module, instantiate engine, run one basic query. Currently 34/36 engines have ZERO tests.",
                "promotion_ready": True,
                "promotion_target": ".github/instructions/testing-validation.instructions.md"
            },
            {
                "pattern_key": "quality.skills_runtime_overlap",
                "source": "prompt_audit",
                "recurrence_count": 45,
                "first_seen": "2026-04-03",
                "last_seen": "2026-04-04",
                "severity": "medium",
                "category": "prompt_quality",
                "suggested_rule": "Audit 45 .github/skills_runtime/ files against forged SINGULARITY skills. If fully absorbed, archive. If unique content exists, merge into the superskill.",
                "promotion_ready": False,
                "promotion_target": ".github/skills_runtime/ (needs manual audit first)"
            }
        ],
        "summary": {
            "candidates_total": 13,
            "promotion_ready_total": 12,
            "followup_required": True,
            "by_severity": {"critical": 4, "high": 6, "medium": 3},
            "by_category": {
                "filing_safety": 4,
                "prompt_quality": 5,
                "code_quality": 2,
                "engine_safety": 1,
                "database_safety": 1
            },
            "highest_recurrence": "harden.path_centralization (43 files)",
            "most_impactful": "harden.filing_contamination (8 occurrences across 4 filings, user-reported)"
        }
    }
}

# Write structured YAML-compatible JSON
out_path = r"D:\LitigationOS_tmp\self_improvement_ci_output.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Self-improvement CI output written to {out_path}")
print(f"   Candidates: {output['self_improvement_ci']['summary']['candidates_total']}")
print(f"   Promotion-ready: {output['self_improvement_ci']['summary']['promotion_ready_total']}")
print(f"   Critical: {output['self_improvement_ci']['summary']['by_severity']['critical']}")
print(f"   High: {output['self_improvement_ci']['summary']['by_severity']['high']}")
print(f"   Medium: {output['self_improvement_ci']['summary']['by_severity']['medium']}")

# Print promotion summary
print("\n📋 PROMOTION-READY RULES:")
for c in output["self_improvement_ci"]["candidates"]:
    if c["promotion_ready"]:
        print(f"  [{c['severity'].upper():8s}] {c['pattern_key']:40s} → {c['promotion_target']}")
