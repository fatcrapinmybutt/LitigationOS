import { joinSession } from "@github/copilot-sdk/extension";
import { execFile, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const HELPER_PATH = join(__dirname, "query_helper.py");
const BRIDGE_PATH = join(__dirname, "lexos_bridge.py");
const DB_PATH = "C:\\Users\\andre\\LitigationOS\\litigation_context.db";
const BRIDGE_TIMEOUT = 60000; // 60s for bridge tools (multi-query orchestration)

// Safety guards (RangeError prevention)
const MAX_STDOUT_BYTES = 2 * 1024 * 1024;   // 2 MB cap for subprocess stdout
const MAX_STDERR_BYTES = 64 * 1024;          // 64 KB cap for stderr
const MAX_FORMAT_ROWS = 200;                 // Max rows to render in markdown tables
const MAX_OUTPUT_CHARS = 500_000;            // 500 KB max for any single tool output
const MAX_BRIDGE_ITEMS = 500;                // Max items from bridge arrays

function safeTruncate(str, maxLen, label = "output") {
    if (typeof str !== "string") {
        try { str = String(str ?? ""); } catch { return "[unstringifiable value]"; }
    }
    if (str.length <= maxLen) return str;
    return str.substring(0, maxLen) +
        `\n\n⚠️ [${label} truncated: ${str.length.toLocaleString()} → ${maxLen.toLocaleString()} chars]`;
}

function safeStringify(obj, maxLen = MAX_OUTPUT_CHARS) {
    try {
        const s = JSON.stringify(obj, null, 2);
        return safeTruncate(s, maxLen, "JSON");
    } catch {
        return "[object too large to serialize]";
    }
}

// Secure query transport — all queries via query_helper.py (JSON stdin/stdout, ? placeholders only)

function queryDB(request) {
    return new Promise((resolve) => {
        const child = execFile(
            "python",
            [HELPER_PATH],
            { maxBuffer: 10 * 1024 * 1024, timeout: 30000 },
            (err, stdout) => {
                if (err) {
                    if (err.killed)
                        resolve("⏰ Query timed out after 30 seconds. Try a more specific query.");
                    else
                        resolve(`Error: ${String(err.message || err).substring(0, 200)}`);
                    return;
                }
                try {
                    const trimmed = (stdout || "").trimEnd();
                    if (trimmed.length > MAX_STDOUT_BYTES) {
                        resolve(`⚠️ Query result too large (${(trimmed.length / 1024 / 1024).toFixed(1)} MB). Add LIMIT or narrow your query.`);
                        return;
                    }
                    const data = JSON.parse(trimmed);
                    if (data.error) {
                        resolve(`❌ Query error: ${String(data.error).substring(0, 200)}`);
                        return;
                    }
                    resolve(data);
                } catch (parseErr) {
                    resolve(`❌ Parse error: ${String(parseErr.message || parseErr).substring(0, 200)}`);
                }
            },
        );
        child.stdin.write(JSON.stringify(request));
        child.stdin.end();
    });
}

// Bridge transport (lexos_bridge.py) — multi-query orchestration via JSON stdin/stdout

function callBridge(payload, timeoutMs = BRIDGE_TIMEOUT) {
    return new Promise((resolve) => {
        const proc = spawn("python", [BRIDGE_PATH], {
            env: { ...process.env, OLLAMA_MODELS: "J:\\OLLAMA_MODELS" },
            stdio: ["pipe", "pipe", "pipe"],
        });

        let stdout = "";
        let stderr = "";
        let settled = false;

        const timer = setTimeout(() => {
            if (!settled) {
                settled = true;
                proc.kill();
                resolve({ error: "⏰ Bridge timed out. Try a simpler query." });
            }
        }, timeoutMs);

        proc.stdout.on("data", (d) => {
            if (stdout.length < MAX_STDOUT_BYTES) {
                stdout += d;
                if (stdout.length > MAX_STDOUT_BYTES) {
                    stdout = stdout.substring(0, MAX_STDOUT_BYTES);
                }
            }
        });
        proc.stderr.on("data", (d) => {
            if (stderr.length < MAX_STDERR_BYTES) {
                stderr += d;
                if (stderr.length > MAX_STDERR_BYTES) {
                    stderr = stderr.substring(0, MAX_STDERR_BYTES);
                }
            }
        });

        proc.on("error", (err) => {
            if (!settled) {
                settled = true;
                clearTimeout(timer);
                resolve({ error: `Bridge spawn error: ${err.message}` });
            }
        });

        proc.on("close", (code) => {
            if (!settled) {
                settled = true;
                clearTimeout(timer);
                if (stdout.trim()) {
                    try {
                        const parsed = JSON.parse(stdout.trim());
                        resolve(parsed);
                    } catch {
                        resolve({ error: `JSON parse failed (code ${code})`, raw: stdout.slice(0, 500) });
                    }
                } else {
                    resolve({ error: stderr.slice(0, 500) || `Bridge exited with code ${code}` });
                }
            }
        });

        proc.stdin.write(JSON.stringify(payload));
        proc.stdin.end();
    });
}

// Markdown formatter (queryDB results)

function formatResult(data) {
    if (typeof data === "string") return safeTruncate(data, MAX_OUTPUT_CHARS, "text result");

    if (data.stats) {
        let out =
            "## 📊 Database Statistics\n\n| Table | Rows |\n| --- | --- |\n";
        for (const [k, v] of Object.entries(data.stats)) {
            out += `| ${k} | ${typeof v === "number" ? v.toLocaleString() : v} |\n`;
        }
        return out;
    }

    if (!data.rows || data.rows.length === 0) return "No results found.";

    const displayRows = data.rows.length > MAX_FORMAT_ROWS
        ? data.rows.slice(0, MAX_FORMAT_ROWS)
        : data.rows;
    const rowsCapped = data.rows.length > MAX_FORMAT_ROWS;

    let out = `**${data.count} rows**`;
    if (data.truncated) out += ` (${data.truncated} more available)`;
    if (rowsCapped) out += ` (showing first ${MAX_FORMAT_ROWS} of ${data.rows.length})`;
    out += "\n\n";
    out += "| " + data.columns.join(" | ") + " |\n";
    out += "| " + data.columns.map(() => "---").join(" | ") + " |\n";
    for (const row of displayRows) {
        const vals = data.columns.map((c) => {
            let v = String(row[c] ?? "");
            if (v.length > 150) v = v.substring(0, 147) + "...";
            return v.replace(/\|/g, "\\|").replace(/\n/g, " ");
        });
        out += "| " + vals.join(" | ") + " |\n";
        if (out.length > MAX_OUTPUT_CHARS) {
            out += "\n⚠️ [Table truncated — output size limit reached]\n";
            break;
        }
    }
    return out;
}

// Bridge formatters (rich markdown from lexos_bridge.py responses)

function formatNarrative(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const lane = data.lane ? ` — Lane ${data.lane}` : "";
    const lines = [`## 📖 Chronological Narrative${lane}`, `> ⚡ DB-only (instant)`, ``];
    let events = data.events || data.narrative || [];
    if (Array.isArray(events) && events.length) {
        const capped = events.length > MAX_BRIDGE_ITEMS;
        if (capped) events = events.slice(0, MAX_BRIDGE_ITEMS);
        for (const ev of events) {
            const date = ev.event_date || ev.date || "????-??-??";
            const desc = String(ev.event_description || ev.description || ev.text || "").substring(0, 500);
            const actors = ev.actors ? ` _(${String(ev.actors).substring(0, 100)})_` : "";
            const tag = ev.lane ? ` \`[${ev.lane}]\`` : "";
            lines.push(`- **${date}**${tag} ${desc}${actors}`);
        }
        if (capped) lines.push(`\n⚠️ _Showing first ${MAX_BRIDGE_ITEMS} of ${(data.events || data.narrative).length} events_`);
    } else if (typeof events === "string") {
        lines.push(safeTruncate(events, MAX_OUTPUT_CHARS, "narrative"));
    } else {
        lines.push("_No narrative events found._");
    }
    if (data.total != null) lines.push(`\n**Total events:** ${data.total}`);
    const result = lines.join("\n");
    return result.length > MAX_OUTPUT_CHARS ? safeTruncate(result, MAX_OUTPUT_CHARS, "narrative") : result;
}

function formatFilingPlan(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const lane = data.lane ? ` — Lane ${data.lane}` : "";
    const lines = [`## 📋 Filing Strategy${lane}`, `> ⚡ DB-only (instant)`, ``];
    let filings = data.filings || data.plan || [];
    if (Array.isArray(filings) && filings.length) {
        if (filings.length > MAX_BRIDGE_ITEMS) filings = filings.slice(0, MAX_BRIDGE_ITEMS);
        lines.push(`| # | Filing | Deadline | Fee | Court | Status |`);
        lines.push(`| --- | --- | --- | --- | --- | --- |`);
        filings.forEach((f, i) => {
            const urg = f.urgency === "critical" || f.urgency === "high" ? "🔴"
                : f.urgency === "medium" ? "🟡" : "🟢";
            lines.push(
                `| ${i + 1} | ${String(f.filing || f.name || f.title || "—").substring(0, 200)} ` +
                `| ${f.deadline || "TBD"} | ${f.fee || "$0"} ` +
                `| ${String(f.court || "—").substring(0, 100)} | ${urg} ${f.status || f.urgency || "—"} |`
            );
        });
    } else if (typeof filings === "string") {
        lines.push(safeTruncate(filings, MAX_OUTPUT_CHARS, "filing plan"));
    } else {
        lines.push("_No filing plan data found._");
    }
    if (data.total_fees) lines.push(`\n**Estimated total fees:** ${data.total_fees}`);
    return safeTruncate(lines.join("\n"), MAX_OUTPUT_CHARS, "filing plan");
}

function formatRulesCheck(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const lines = [`## 📏 Procedural Compliance Check`, `> ⚡ DB-only (instant)`, ``];
    let rules = data.rules || data.results || [];
    if (Array.isArray(rules) && rules.length) {
        if (rules.length > MAX_BRIDGE_ITEMS) rules = rules.slice(0, MAX_BRIDGE_ITEMS);
        for (const r of rules) {
            const status = r.compliant === true ? "🟢 Compliant"
                : r.compliant === false ? "🔴 Non-compliant" : "🟡 Review needed";
            lines.push(`### ${r.rule_number || r.rule || "Rule"}: ${String(r.title || "").substring(0, 200)}`);
            lines.push(`**Status:** ${status}`);
            if (r.full_text || r.text) {
                lines.push("```");
                lines.push(String(r.full_text || r.text).slice(0, 600));
                lines.push("```");
            }
            if (r.notes) lines.push(`> ${String(r.notes).substring(0, 300)}`);
            lines.push("");
        }
    } else if (typeof rules === "string") {
        lines.push(safeTruncate(rules, MAX_OUTPUT_CHARS, "rules"));
    } else if (data.rule_text || data.text) {
        lines.push("```");
        lines.push(String(data.rule_text || data.text).slice(0, 2000));
        lines.push("```");
    } else {
        lines.push("_No matching rules found._");
    }
    return safeTruncate(lines.join("\n"), MAX_OUTPUT_CHARS, "rules check");
}

function formatAdversary(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const name = data.person || data.name || "Unknown";
    const lines = [`## 🕵️ Adversary Profile — ${name}`, `> ⚡ DB-only (instant)`, ``];
    const fields = [
        ["Role", data.role],
        ["Credibility Score", data.credibility_score ?? data.credibility],
        ["Contradiction Count", data.contradiction_count ?? data.contradictions],
        ["Impeachment Items", data.impeachment_count ?? data.impeachment_items],
        ["Key Weakness", data.weakness || data.key_weakness],
        ["Lanes Involved", data.lanes ? (Array.isArray(data.lanes) ? data.lanes.join(", ") : data.lanes) : undefined],
    ].filter(([, v]) => v !== undefined && v !== null);
    if (fields.length) {
        lines.push(`| Attribute | Value |`);
        lines.push(`| --- | --- |`);
        for (const [k, v] of fields) lines.push(`| ${k} | ${String(v).substring(0, 300)} |`);
        lines.push("");
    }
    if (Array.isArray(data.key_facts) && data.key_facts.length) {
        lines.push(`### Key Facts`);
        const facts = data.key_facts.length > MAX_BRIDGE_ITEMS ? data.key_facts.slice(0, MAX_BRIDGE_ITEMS) : data.key_facts;
        for (const f of facts) lines.push(`- ${String(f).substring(0, 500)}`);
        lines.push("");
    }
    if (Array.isArray(data.top_contradictions) && data.top_contradictions.length) {
        lines.push(`### Top Contradictions`);
        const contras = data.top_contradictions.length > MAX_BRIDGE_ITEMS ? data.top_contradictions.slice(0, MAX_BRIDGE_ITEMS) : data.top_contradictions;
        for (const c of contras) {
            const text = typeof c === "string" ? c : c.text || c.contradiction_text || safeStringify(c, 500);
            lines.push(`- 🔴 ${String(text).substring(0, 500)}`);
        }
        lines.push("");
    }
    if (fields.length === 0 && !data.key_facts && data.profile) {
        lines.push(typeof data.profile === "string"
            ? safeTruncate(data.profile, MAX_OUTPUT_CHARS, "profile")
            : safeStringify(data.profile, MAX_OUTPUT_CHARS));
    }
    return safeTruncate(lines.join("\n"), MAX_OUTPUT_CHARS, "adversary profile");
}

function formatGapAnalysis(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const lane = data.lane ? ` — Lane ${data.lane}` : "";
    const lines = [`## 🔍 Gap Analysis${lane}`, `> ⚡ DB-only (instant)`, ``];
    const categories = [
        ["Missing Evidence", data.missing_evidence],
        ["Missing Claims", data.missing_claims],
        ["Missing Filings", data.missing_filings],
        ["Weak Points", data.weak_points],
    ];
    let hasContent = false;
    for (const [label, items] of categories) {
        if (!items || (Array.isArray(items) && items.length === 0)) continue;
        hasContent = true;
        lines.push(`### ${label}`);
        if (Array.isArray(items)) {
            const capped = items.length > MAX_BRIDGE_ITEMS ? items.slice(0, MAX_BRIDGE_ITEMS) : items;
            for (const item of capped) {
                const sev = typeof item === "object" ? item.severity : undefined;
                const icon = sev === "critical" || sev === "high" ? "🔴" : sev === "medium" ? "🟡" : "🟢";
                const text = typeof item === "string" ? item : item.description || item.text || safeStringify(item, 500);
                lines.push(`- ${icon} ${String(text).substring(0, 500)}`);
            }
        } else {
            lines.push(String(items).substring(0, 2000));
        }
        lines.push("");
    }
    if (!hasContent && data.gaps) {
        if (Array.isArray(data.gaps)) {
            const capped = data.gaps.length > MAX_BRIDGE_ITEMS ? data.gaps.slice(0, MAX_BRIDGE_ITEMS) : data.gaps;
            for (const g of capped) lines.push(`- ${typeof g === "string" ? g : g.text || safeStringify(g, 500)}`);
        } else {
            lines.push(String(data.gaps).substring(0, 2000));
        }
        hasContent = true;
    }
    if (!hasContent) lines.push("_No gaps identified._");
    return safeTruncate(lines.join("\n"), MAX_OUTPUT_CHARS, "gap analysis");
}

function formatCrossConnect(data) {
    if (data.error) return `❌ **Error:** ${String(data.error).substring(0, 500)}`;
    const lines = [`## 🔗 Cross-Lane Intelligence — "${data.topic || "N/A"}"`, `> ⚡ DB-only (instant)`, ``];
    let connections = data.connections || data.results || [];
    if (Array.isArray(connections) && connections.length) {
        if (connections.length > MAX_BRIDGE_ITEMS) connections = connections.slice(0, MAX_BRIDGE_ITEMS);
        const byLane = {};
        for (const c of connections) {
            const lane = c.lane || "Unassigned";
            if (!byLane[lane]) byLane[lane] = [];
            byLane[lane].push(c);
        }
        for (const [lane, items] of Object.entries(byLane)) {
            lines.push(`### Lane ${lane}`);
            for (const item of items) {
                const text = String(item.text || item.description || item.event_description || item.quote_text || safeStringify(item, 300)).slice(0, 300);
                const src = item.source || item.source_file || "";
                lines.push(`- ${text}${src ? ` _(${String(src).substring(0, 100)})_` : ""}`);
            }
            lines.push("");
        }
    } else if (typeof connections === "string") {
        lines.push(safeTruncate(connections, MAX_OUTPUT_CHARS, "connections"));
    } else {
        lines.push("_No cross-lane connections found._");
    }
    if (data.lanes_touched) {
        const lt = Array.isArray(data.lanes_touched) ? data.lanes_touched.join(", ") : data.lanes_touched;
        lines.push(`**Lanes touched:** ${lt}`);
    }
    return safeTruncate(lines.join("\n"), MAX_OUTPUT_CHARS, "cross-connect");
}

// Extension session

const session = await joinSession({
    hooks: {
        onSessionStart: async () => {
            await session.log(
                "⚖️ SINGULARITY v7.1 — 22 tools + 8 slash commands + governance hooks",
                { level: "info" },
            );
        },
        beforeInvoke: async (toolCall) => {
            // Log all tool invocations for governance audit trail
            const ts = new Date().toISOString();
            await session.log(`[${ts}] Tool: ${toolCall.name}`, { level: "debug" });
            return toolCall; // pass through unchanged
        },
        afterInvoke: async (toolCall, result) => {
            // Track tool performance
            if (result.error) {
                await session.log(`⚠️ Tool ${toolCall.name} failed: ${result.error}`, { level: "warn" });
            }
            return result;
        },
    },
    slashCommands: [
        {
            name: "filing",
            description: "Filing workflow: check readiness, generate documents, assemble packages",
            handler: async (args, session) => {
                const lane = args.trim() || "all";
                return `Check filing readiness and generate documents for lane: ${lane}. Use nexus_readiness, filing_status, and lexos_filing_plan tools to assess current state. If a specific lane is specified, focus there. Show readiness scores, gaps, and next steps.`;
            },
        },
        {
            name: "evidence",
            description: "Search evidence across all sources with hybrid FTS5+semantic+reranking",
            handler: async (args, session) => {
                const query = args.trim();
                if (!query) return "Usage: /evidence <search terms>. Example: /evidence parental alienation";
                return `Deep evidence search for: "${query}". Use nexus_fuse to search across evidence_quotes, timeline_events, police_reports, impeachment_matrix, and authority_chains simultaneously. Then use search_evidence for FTS5 results and lexos_cross_connect to trace across lanes.`;
            },
        },
        {
            name: "argue",
            description: "Build complete argument chain: evidence + authorities + impeachment",
            handler: async (args, session) => {
                const claim = args.trim();
                if (!claim) return "Usage: /argue <claim>. Example: /argue judicial bias";
                return `Build a complete argument chain for the claim: "${claim}". Use nexus_argue to find supporting evidence, legal authorities, and impeachment ammunition. Show chain strength score. Then use search_authority_chains to verify all citations exist in the database.`;
            },
        },
        {
            name: "timeline",
            description: "Build chronological narrative for a topic or date range",
            handler: async (args, session) => {
                const query = args.trim();
                if (!query) return "Usage: /timeline <topic or date>. Example: /timeline custody withholding";
                return `Build a chronological narrative for: "${query}". Use lexos_narrative and timeline_search to construct a time-ordered story. Focus on key events, actors, and evidence citations.`;
            },
        },
        {
            name: "damages",
            description: "Calculate damages across all lanes with conservative and aggressive estimates",
            handler: async (args, session) => {
                const lane = args.trim() || "";
                return `Calculate comprehensive damages${lane ? ` for lane ${lane}` : " across all lanes"}. Use nexus_damages to get conservative and aggressive amounts by category. Include constitutional violations, emotional distress, economic harm, and punitive multipliers.`;
            },
        },
        {
            name: "impeach",
            description: "Build impeachment package for a target witness/party",
            handler: async (args, session) => {
                const target = args.trim();
                if (!target) return "Usage: /impeach <person>. Example: /impeach Emily Watson";
                return `Build a comprehensive impeachment package for: "${target}". Use search_impeachment with high severity, search_contradictions, and lexos_adversary to compile prior inconsistent statements, contradictions, and credibility attacks. Score overall credibility.`;
            },
        },
        {
            name: "status",
            description: "Full system status: case health, deadlines, filing readiness, separation counter",
            handler: async (args, session) => {
                const today = new Date();
                const sep = new Date("2025-07-29");
                const days = Math.floor((today - sep) / 86400000);
                return `System status check. Separation day count: ${days} days since July 29, 2025. Use check_deadlines for upcoming deadlines, nexus_readiness for filing readiness across all lanes, and nexus_priorities for daily action priorities. Show everything in a dashboard format.`;
            },
        },
        {
            name: "judge",
            description: "Judicial intelligence profile for a specific judge",
            handler: async (args, session) => {
                const judge = args.trim() || "McNeill";
                return `Build judicial intelligence profile for Judge ${judge}. Use judicial_intel to get patterns, bias indicators, and misconduct evidence. Cross-reference with search_impeachment targeting the judge. Show ruling patterns, ex parte rate, and JTC exhibits.`;
            },
        },
    ],
    tools: [
        {
            name: "query_litigation_db",
            description:
                "Run a parameterized SQL query against litigation_context.db (186 tables, 1.3 M+ rows). " +
                "Pass SQL with ? placeholders and a params array — values are NEVER interpolated. " +
                "Key tables: evidence_quotes, timeline_events, michigan_rules_extracted, police_reports, " +
                "impeachment_matrix, authority_chains_v2, contradiction_map, deadlines, filing_packages.",
            parameters: {
                type: "object",
                properties: {
                    sql: {
                        type: "string",
                        description: "SQL with ? placeholders. Example: SELECT * FROM evidence_quotes WHERE category = ? AND lane = ? LIMIT 20",
                    },
                    params: {
                        type: "array",
                        description: "Parameter values matching ? placeholders. Example: ['custody', 'F7']",
                    },
                    max_rows: {
                        type: "number",
                        description: "Maximum rows to return (default 50, max 500)",
                    },
                },
                required: ["sql"],
            },
            handler: async (args) => {
                const result = await queryDB({
                    action: "query",
                    sql: args.sql,
                    params: args.params || [],
                    max_rows: Math.min(args.max_rows || 50, 500),
                });
                return formatResult(result);
            },
        },

        {
            name: "search_evidence",
            description:
                "Full-text search across evidence. Uses FTS5 with snippet() for evidence_quotes " +
                "and timeline_events (ranked results with highlighted excerpts). Falls back to " +
                "LIKE for police_reports and michigan_rules_extracted.",
            parameters: {
                type: "object",
                properties: {
                    query: {
                        type: "string",
                        description: 'FTS5 search terms (AND, OR, NOT, "quoted phrases", prefix*). ' +
                            "Examples: 'custody alienation', '\"parental alienation\" OR \"best interest\"'",
                    },
                    table: {
                        type: "string",
                        description: "Table to search (default: evidence_quotes)",
                        enum: ["evidence_quotes", "timeline_events", "police_reports", "michigan_rules_extracted"],
                    },
                    limit: {
                        type: "number",
                        description: "Max results (default 25, max 100)",
                    },
                },
                required: ["query"],
            },
            handler: async (args) => {
                const table = args.table || "evidence_quotes";
                const limit = Math.min(args.limit || 25, 100);
                const q = args.query.trim();

                if (q.length < 2)
                    return "❌ Search query must be at least 2 characters.";

                let result;

                if (table === "evidence_quotes") {
                    result = await queryDB({
                        action: "query",
                        sql: "SELECT eq.source_file, " +
                            "snippet(evidence_fts, 0, '>>>', '<<<', '...', 64) AS excerpt, " +
                            "eq.category, eq.lane, eq.relevance_score, evidence_fts.rank " +
                            "FROM evidence_fts " +
                            "JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid " +
                            "WHERE evidence_fts MATCH ? " +
                            "ORDER BY evidence_fts.rank LIMIT ?",
                        params: [q, limit],
                        max_rows: limit,
                    });
                } else if (table === "timeline_events") {
                    result = await queryDB({
                        action: "query",
                        sql: "SELECT snippet(timeline_fts, 0, '>>>', '<<<', '...', 64) AS excerpt, " +
                            "timeline_fts.actors, timeline_fts.rank " +
                            "FROM timeline_fts " +
                            "WHERE timeline_fts MATCH ? " +
                            "ORDER BY timeline_fts.rank LIMIT ?",
                        params: [q, limit],
                        max_rows: limit,
                    });
                } else if (table === "police_reports") {
                    const terms = q.split(/\s+/).filter((t) => t.length >= 2);
                    if (terms.length === 0)
                        return "❌ No valid search terms (minimum 2 characters each).";
                    const conds = terms.map(() => "full_text LIKE ?").join(" AND ");
                    const params = terms.map((t) => `%${t}%`);
                    params.push(limit);
                    result = await queryDB({
                        action: "query",
                        sql: `SELECT filename, allegations, exculpatory, false_reports, ` +
                            `substr(full_text, 1, 300) AS excerpt ` +
                            `FROM police_reports WHERE ${conds} LIMIT ?`,
                        params,
                        max_rows: limit,
                    });
                } else if (table === "michigan_rules_extracted") {
                    const terms = q.split(/\s+/).filter((t) => t.length >= 2);
                    if (terms.length === 0)
                        return "❌ No valid search terms (minimum 2 characters each).";
                    const conds = terms.map(() => "full_text LIKE ?").join(" AND ");
                    const params = terms.map((t) => `%${t}%`);
                    params.push(limit);
                    result = await queryDB({
                        action: "query",
                        sql: `SELECT rule_number, rule_type, title, ` +
                            `substr(full_text, 1, 300) AS excerpt ` +
                            `FROM michigan_rules_extracted WHERE ${conds} LIMIT ?`,
                        params,
                        max_rows: limit,
                    });
                } else {
                    return "❌ Unknown table. Use: evidence_quotes, timeline_events, police_reports, michigan_rules_extracted";
                }

                return formatResult(result);
            },
        },

        {
            name: "check_deadlines",
            description:
                "Check litigation deadlines and filing due dates with urgency color coding. " +
                "Shows overdue items 🔴, critical 🟠 (≤3 days), urgent 🟡 (≤7 days), and OK 🟢. Also lists filing packages.",
            parameters: {
                type: "object",
                properties: {
                    days_ahead: {
                        type: "number",
                        description: "Show deadlines within N days from now (default 30)",
                    },
                },
            },
            handler: async (args) => {
                const days = args?.days_ahead || 30;
                const modifier = `+${days} days`;

                const dlData = await queryDB({
                    action: "query",
                    sql: "SELECT title, due_date, court, case_number, status, urgency, " +
                        "CAST(julianday(due_date) - julianday('now') AS INTEGER) AS days_remaining " +
                        "FROM deadlines " +
                        "WHERE due_date <= date('now', ?) " +
                        "ORDER BY due_date ASC",
                    params: [modifier],
                    max_rows: 50,
                });

                // Inject urgency flags
                if (typeof dlData === "object" && dlData.rows) {
                    for (const row of dlData.rows) {
                        const d = row.days_remaining;
                        if (d < 0) row.urgency_flag = "🔴 OVERDUE";
                        else if (d <= 3) row.urgency_flag = "🟠 CRITICAL";
                        else if (d <= 7) row.urgency_flag = "🟡 URGENT";
                        else row.urgency_flag = "🟢 OK";
                    }
                    if (!dlData.columns.includes("urgency_flag"))
                        dlData.columns.push("urgency_flag");
                }

                const pkgData = await queryDB({
                    action: "query",
                    sql: "SELECT filing_id, title, lane, case_number, doc_count, status " +
                        "FROM filing_packages ORDER BY lane",
                    params: [],
                    max_rows: 20,
                });

                return (
                    `## ⏰ Deadlines (next ${days} days)\n\n` +
                    formatResult(dlData) +
                    "\n\n## 📦 Filing Packages\n\n" +
                    formatResult(pkgData)
                );
            },
        },

        {
            name: "case_context",
            description:
                "Comprehensive context for active litigation cases. Returns database statistics, " +
                "filing packages, and recent timeline. Optionally filter by case number.",
            parameters: {
                type: "object",
                properties: {
                    case_id: {
                        type: "string",
                        description: "Optional case number to focus on (e.g. '2024-001507-DC', '366810')",
                    },
                },
            },
            handler: async (args) => {
                const statsData = await queryDB({ action: "stats" });

                let pkgSql =
                    "SELECT filing_id, title, lane, case_number, doc_count, status FROM filing_packages";
                let pkgParams = [];
                if (args?.case_id) {
                    pkgSql += " WHERE case_number LIKE ?";
                    pkgParams = [`%${args.case_id}%`];
                }
                pkgSql += " ORDER BY lane";
                const pkgData = await queryDB({
                    action: "query",
                    sql: pkgSql,
                    params: pkgParams,
                    max_rows: 20,
                });

                const tlData = await queryDB({
                    action: "query",
                    sql: "SELECT event_date, category, event_description, actors " +
                        "FROM timeline_events ORDER BY event_date DESC LIMIT 10",
                    params: [],
                    max_rows: 10,
                });

                return (
                    "## 📊 LitigationOS Intelligence Summary\n\n" +
                    formatResult(statsData) +
                    "\n\n## 📦 Filing Packages\n\n" +
                    formatResult(pkgData) +
                    "\n\n## 📅 Recent Timeline\n\n" +
                    formatResult(tlData)
                );
            },
        },

        {
            name: "filing_status",
            description:
                "Detailed status of a specific filing package by lane. Shows package info, related evidence count, and deadlines.",
            parameters: {
                type: "object",
                properties: {
                    lane: {
                        type: "string",
                        description: "Filing lane: F1-F10, CRIMINAL, F-VAC, F-MSC2",
                        enum: ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "CRIMINAL", "F-VAC", "F-MSC2"],
                    },
                },
                required: ["lane"],
            },
            handler: async (args) => {
                const lane = args.lane;

                const pkgData = await queryDB({
                    action: "query",
                    sql: "SELECT * FROM filing_packages " +
                        "WHERE lane = ? OR filing_id LIKE ? OR title LIKE ?",
                    params: [lane, `%${lane}%`, `%${lane}%`],
                    max_rows: 5,
                });

                const evData = await queryDB({
                    action: "query",
                    sql: "SELECT COUNT(*) AS evidence_count FROM evidence_quotes " +
                        "WHERE lane LIKE ? OR tags LIKE ?",
                    params: [`%${lane}%`, `%${lane}%`],
                    max_rows: 1,
                });

                const dlData = await queryDB({
                    action: "query",
                    sql: "SELECT title, due_date, status, " +
                        "CAST(julianday(due_date) - julianday('now') AS INTEGER) AS days_remaining " +
                        "FROM deadlines WHERE filing_id LIKE ? ORDER BY due_date",
                    params: [`%${lane}%`],
                    max_rows: 10,
                });

                return (
                    `## 📄 Filing Package: ${lane}\n\n` +
                    formatResult(pkgData) +
                    "\n\n## 📎 Related Evidence\n\n" +
                    formatResult(evData) +
                    "\n\n## ⏰ Deadlines\n\n" +
                    formatResult(dlData)
                );
            },
        },

        {
            name: "search_impeachment",
            description:
                "Search impeachment_matrix for cross-examination ammunition. " +
                "Columns: category, evidence_summary, source_file, quote_text, impeachment_value (1-10), " +
                "cross_exam_question, filing_relevance, event_date.",
            parameters: {
                type: "object",
                properties: {
                    target: {
                        type: "string",
                        description: "Person / entity to impeach (e.g. 'Emily', 'Watson', 'Judge McNeill')",
                    },
                    category: {
                        type: "string",
                        description: "Category filter (e.g. 'custody', 'PPO', 'financial')",
                    },
                    min_severity: {
                        type: "number",
                        description: "Minimum impeachment_value (1-10, default 1)",
                    },
                    limit: {
                        type: "number",
                        description: "Max results (default 25, max 100)",
                    },
                },
            },
            handler: async (args) => {
                const limit = Math.min(args.limit || 25, 100);
                const minSev = args.min_severity || 1;
                const conditions = ["impeachment_value >= ?"];
                const params = [minSev];

                if (args.target) {
                    conditions.push(
                        "(category LIKE ? OR evidence_summary LIKE ? OR cross_exam_question LIKE ?)",
                    );
                    params.push(
                        `%${args.target}%`,
                        `%${args.target}%`,
                        `%${args.target}%`,
                    );
                }
                if (args.category) {
                    conditions.push("category LIKE ?");
                    params.push(`%${args.category}%`);
                }
                params.push(limit);

                const result = await queryDB({
                    action: "query",
                    sql: "SELECT category, evidence_summary, source_file, " +
                        "substr(quote_text, 1, 200) AS quote_text, " +
                        "impeachment_value, cross_exam_question, " +
                        "filing_relevance, event_date " +
                        "FROM impeachment_matrix " +
                        `WHERE ${conditions.join(" AND ")} ` +
                        "ORDER BY impeachment_value DESC LIMIT ?",
                    params,
                    max_rows: limit,
                });

                return "## 🎯 Impeachment Results\n\n" + formatResult(result);
            },
        },

        {
            name: "search_contradictions",
            description:
                "Search contradiction_map for inconsistencies. Columns: claim_id, source_a, source_b, " +
                "contradiction_text, severity, lane. Find where parties contradict themselves or others.",
            parameters: {
                type: "object",
                properties: {
                    entity: {
                        type: "string",
                        description: "Person or topic (searches source_a, source_b, contradiction_text)",
                    },
                    severity: {
                        type: "string",
                        description: "Severity filter (e.g. 'high', 'critical')",
                    },
                    lane: {
                        type: "string",
                        description: "Filing lane filter (e.g. 'F7', 'CRIMINAL')",
                    },
                    limit: {
                        type: "number",
                        description: "Max results (default 25, max 100)",
                    },
                },
            },
            handler: async (args) => {
                const limit = Math.min(args.limit || 25, 100);
                const conditions = [];
                const params = [];

                if (args.entity) {
                    conditions.push(
                        "(source_a LIKE ? OR source_b LIKE ? OR contradiction_text LIKE ?)",
                    );
                    params.push(
                        `%${args.entity}%`,
                        `%${args.entity}%`,
                        `%${args.entity}%`,
                    );
                }
                if (args.severity) {
                    conditions.push("severity LIKE ?");
                    params.push(`%${args.severity}%`);
                }
                if (args.lane) {
                    conditions.push("lane LIKE ?");
                    params.push(`%${args.lane}%`);
                }

                const where =
                    conditions.length > 0
                        ? "WHERE " + conditions.join(" AND ")
                        : "";
                params.push(limit);

                const result = await queryDB({
                    action: "query",
                    sql: "SELECT claim_id, source_a, source_b, " +
                        "substr(contradiction_text, 1, 250) AS contradiction_text, " +
                        `severity, lane FROM contradiction_map ${where} ` +
                        "ORDER BY id DESC LIMIT ?",
                    params,
                    max_rows: limit,
                });

                return "## ⚡ Contradictions Found\n\n" + formatResult(result);
            },
        },

        {
            name: "search_authority_chains",
            description:
                "Search authority_chains_v2 (31K citation chains). Columns: primary_citation, " +
                "supporting_citation, relationship, source_document, source_type, lane, paragraph_context. " +
                "Find which citations support which arguments.",
            parameters: {
                type: "object",
                properties: {
                    citation: {
                        type: "string",
                        description: "Citation to search (e.g. 'MCL 722.23', 'MCR 2.003', 'Vodvarka')",
                    },
                    lane: {
                        type: "string",
                        description: "Filing lane filter",
                    },
                    source_type: {
                        type: "string",
                        description: "Source type filter (e.g. 'motion', 'brief', 'order')",
                    },
                    limit: {
                        type: "number",
                        description: "Max results (default 25, max 100)",
                    },
                },
            },
            handler: async (args) => {
                const limit = Math.min(args.limit || 25, 100);
                const conditions = [];
                const params = [];

                if (args.citation) {
                    conditions.push(
                        "(primary_citation LIKE ? OR supporting_citation LIKE ?)",
                    );
                    params.push(`%${args.citation}%`, `%${args.citation}%`);
                }
                if (args.lane) {
                    conditions.push("lane LIKE ?");
                    params.push(`%${args.lane}%`);
                }
                if (args.source_type) {
                    conditions.push("source_type LIKE ?");
                    params.push(`%${args.source_type}%`);
                }

                const where =
                    conditions.length > 0
                        ? "WHERE " + conditions.join(" AND ")
                        : "";
                params.push(limit);

                const result = await queryDB({
                    action: "query",
                    sql: "SELECT primary_citation, supporting_citation, relationship, " +
                        "source_document, source_type, lane, " +
                        "substr(paragraph_context, 1, 200) AS context " +
                        `FROM authority_chains_v2 ${where} ` +
                        "ORDER BY id DESC LIMIT ?",
                    params,
                    max_rows: limit,
                });

                return "## 📚 Authority Chains\n\n" + formatResult(result);
            },
        },

        {
            name: "nexus_fuse",
            description:
                "Cross-table evidence fusion. Searches evidence_quotes (FTS5), timeline_events (FTS5), " +
                "police_reports, impeachment_matrix, and authority_chains simultaneously. Returns fused results from all 5 sources.",
            parameters: {
                type: "object",
                properties: {
                    topic: {
                        type: "string",
                        description: "FTS5 search terms (AND, OR, NOT, quoted phrases). E.g.: 'alienation', 'PPO OR protection order'",
                    },
                    lanes: {
                        type: "array",
                        items: { type: "string" },
                        description: "Optional lane filter: A, B, D, E, F, CRIMINAL",
                    },
                    limit: {
                        type: "number",
                        description: "Max results per source (default 50)",
                    },
                },
                required: ["topic"],
            },
            handler: async (args) => {
                const q = args.topic.trim();
                const limit = Math.min(args.limit || 50, 100);
                const likeTerms = q.split(/\s+/).filter((t) => t.length >= 2);

                // Evidence quotes (FTS5)
                const evRes = await queryDB({
                    action: "query",
                    sql: "SELECT eq.source_file, " +
                        "snippet(evidence_fts, 0, '>>>', '<<<', '...', 48) AS excerpt, " +
                        "eq.category, eq.lane, eq.relevance_score " +
                        "FROM evidence_fts " +
                        "JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid " +
                        "WHERE evidence_fts MATCH ? ORDER BY evidence_fts.rank LIMIT ?",
                    params: [q, limit],
                    max_rows: limit,
                });

                // Timeline events (FTS5)
                const tlRes = await queryDB({
                    action: "query",
                    sql: "SELECT snippet(timeline_fts, 0, '>>>', '<<<', '...', 48) AS excerpt, " +
                        "timeline_fts.actors " +
                        "FROM timeline_fts WHERE timeline_fts MATCH ? " +
                        "ORDER BY timeline_fts.rank LIMIT ?",
                    params: [q, limit],
                    max_rows: limit,
                });

                // Police reports (LIKE)
                let prRes = "No matches.";
                if (likeTerms.length > 0) {
                    const prConds = likeTerms.map(() => "full_text LIKE ?").join(" AND ");
                    const prParams = likeTerms.map((t) => `%${t}%`);
                    prParams.push(limit);
                    prRes = await queryDB({
                        action: "query",
                        sql: `SELECT filename, allegations, exculpatory, false_reports FROM police_reports WHERE ${prConds} LIMIT ?`,
                        params: prParams,
                        max_rows: limit,
                    });
                }

                // Impeachment matrix
                const impRes = await queryDB({
                    action: "query",
                    sql: "SELECT category, evidence_summary, impeachment_value, cross_exam_question " +
                        "FROM impeachment_matrix WHERE evidence_summary LIKE ? OR category LIKE ? " +
                        "ORDER BY impeachment_value DESC LIMIT ?",
                    params: [`%${likeTerms[0] || q}%`, `%${likeTerms[0] || q}%`, limit],
                    max_rows: limit,
                });

                // Authority chains
                const authRes = await queryDB({
                    action: "query",
                    sql: "SELECT primary_citation, supporting_citation, relationship, lane " +
                        "FROM authority_chains_v2 WHERE primary_citation LIKE ? OR supporting_citation LIKE ? LIMIT ?",
                    params: [`%${likeTerms[0] || q}%`, `%${likeTerms[0] || q}%`, limit],
                    max_rows: limit,
                });

                return safeTruncate(
                    `## 🔥 NEXUS Fusion: "${q}"\n\n` +
                    "### Evidence Quotes\n" + formatResult(evRes) + "\n\n" +
                    "### Timeline Events\n" + formatResult(tlRes) + "\n\n" +
                    "### Police Reports\n" + formatResult(prRes) + "\n\n" +
                    "### Impeachment\n" + formatResult(impRes) + "\n\n" +
                    "### Authority Chains\n" + formatResult(authRes),
                    MAX_OUTPUT_CHARS, "nexus fusion"
                );
            },
        },

        {
            name: "nexus_case_map",
            description:
                "Multi-standard case analysis. For custody: all 12 MCL 722.23 best interest factors with scores and evidence. " +
                "For judicial: violations and bias events. Also housing, criminal, federal, ppo, appellate.",
            parameters: {
                type: "object",
                properties: {
                    case_type: {
                        type: "string",
                        description: "Case type: custody, housing, judicial, criminal, federal, ppo, appellate",
                    },
                },
                required: ["case_type"],
            },
            handler: async (args) => {
                const ct = (args.case_type || "").toLowerCase();
                let result;

                if (ct === "custody") {
                    result = await queryDB({
                        action: "query",
                        sql: "SELECT factor, description, andrew_score, emily_score, " +
                            "evidence_count, assessment FROM custody_factors ORDER BY factor",
                        params: [],
                        max_rows: 15,
                    });
                } else if (ct === "judicial") {
                    result = await queryDB({
                        action: "query",
                        sql: "SELECT violation_type, COUNT(*) AS cnt, " +
                            "GROUP_CONCAT(DISTINCT source_file) AS sources " +
                            "FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC",
                        params: [],
                        max_rows: 30,
                    });
                } else {
                    result = await queryDB({
                        action: "query",
                        sql: "SELECT category, COUNT(*) AS evidence_count, " +
                            "GROUP_CONCAT(DISTINCT lane) AS lanes " +
                            "FROM evidence_quotes WHERE category LIKE ? GROUP BY category ORDER BY evidence_count DESC LIMIT 20",
                        params: [`%${ct}%`],
                        max_rows: 20,
                    });
                }

                return `## 🗺️ Case Map: ${args.case_type}\n\n` + formatResult(result);
            },
        },

        {
            name: "nexus_readiness",
            description:
                "Filing readiness dashboard across all lanes. Shows evidence count, authority count, " +
                "impeachment count, readiness score, deadline, and gap analysis per filing package.",
            parameters: {
                type: "object",
                properties: {
                    lane: {
                        type: "string",
                        description: "Optional lane filter: A, B, D, E, F, CRIMINAL. Omit for all lanes.",
                    },
                },
            },
            handler: async (args) => {
                let pkgSql =
                    "SELECT fp.filing_id, fp.title, fp.lane, fp.status, fp.doc_count, " +
                    "(SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.lane LIKE '%' || fp.lane || '%') AS evidence_count, " +
                    "(SELECT COUNT(*) FROM authority_chains_v2 ac WHERE ac.lane LIKE '%' || fp.lane || '%') AS authority_count " +
                    "FROM filing_packages fp";
                const params = [];
                if (args?.lane) {
                    pkgSql += " WHERE fp.lane LIKE ?";
                    params.push(`%${args.lane}%`);
                }
                pkgSql += " ORDER BY fp.lane";

                const result = await queryDB({
                    action: "query",
                    sql: pkgSql,
                    params,
                    max_rows: 20,
                });

                return "## 🚦 Filing Readiness Dashboard\n\n" + formatResult(result);
            },
        },

        {
            name: "nexus_priorities",
            description:
                "Daily action priorities across ALL cases. Combines deadline urgency with filing readiness gaps. " +
                "Shows overdue items, days until each deadline, priority scores, and parent-child separation counter.",
            parameters: { type: "object", properties: {} },
            handler: async () => {
                const dlData = await queryDB({
                    action: "query",
                    sql: "SELECT title, due_date, court, case_number, " +
                        "CAST(julianday(due_date) - julianday('now') AS INTEGER) AS days_remaining " +
                        "FROM deadlines ORDER BY due_date ASC LIMIT 20",
                    params: [],
                    max_rows: 20,
                });

                const sepDays = await queryDB({
                    action: "query",
                    sql: "SELECT CAST(julianday('now') - julianday('2025-07-29') AS INTEGER) AS separation_days",
                    params: [],
                    max_rows: 1,
                });

                return (
                    "## 🎯 Daily Priorities\n\n" +
                    formatResult(dlData) + "\n\n" +
                    "### ⏱️ Parent-Child Separation\n" +
                    formatResult(sepDays)
                );
            },
        },

        {
            name: "nexus_argue",
            description:
                "Argument chain synthesis. For a given claim, finds supporting evidence (FTS5), " +
                "legal authorities, and impeachment ammunition. Returns chain strength score and rating.",
            parameters: {
                type: "object",
                properties: {
                    claim: {
                        type: "string",
                        description: "The claim or argument. E.g.: 'parental alienation', 'wrongful eviction', 'judicial bias'",
                    },
                    lane: {
                        type: "string",
                        description: "Optional lane filter",
                    },
                    limit: {
                        type: "number",
                        description: "Max results per source (default 10)",
                    },
                },
                required: ["claim"],
            },
            handler: async (args) => {
                const claim = args.claim.trim();
                const limit = Math.min(args.limit || 10, 50);
                const likeTerms = claim.split(/\s+/).filter((t) => t.length >= 2);
                const likeTerm = likeTerms[0] || claim;

                const evRes = await queryDB({
                    action: "query",
                    sql: "SELECT eq.source_file, " +
                        "snippet(evidence_fts, 0, '>>>', '<<<', '...', 48) AS excerpt, " +
                        "eq.relevance_score " +
                        "FROM evidence_fts " +
                        "JOIN evidence_quotes eq ON eq.id = evidence_fts.rowid " +
                        "WHERE evidence_fts MATCH ? ORDER BY evidence_fts.rank LIMIT ?",
                    params: [claim, limit],
                    max_rows: limit,
                });

                const authRes = await queryDB({
                    action: "query",
                    sql: "SELECT primary_citation, supporting_citation, relationship " +
                        "FROM authority_chains_v2 WHERE primary_citation LIKE ? OR supporting_citation LIKE ? LIMIT ?",
                    params: [`%${likeTerm}%`, `%${likeTerm}%`, limit],
                    max_rows: limit,
                });

                const impRes = await queryDB({
                    action: "query",
                    sql: "SELECT evidence_summary, impeachment_value, cross_exam_question " +
                        "FROM impeachment_matrix WHERE evidence_summary LIKE ? " +
                        "ORDER BY impeachment_value DESC LIMIT ?",
                    params: [`%${likeTerm}%`, limit],
                    max_rows: limit,
                });

                return safeTruncate(
                    `## ⚔️ Argument Chain: "${claim}"\n\n` +
                    "### Supporting Evidence\n" + formatResult(evRes) + "\n\n" +
                    "### Legal Authority\n" + formatResult(authRes) + "\n\n" +
                    "### Impeachment Support\n" + formatResult(impRes),
                    MAX_OUTPUT_CHARS, "argument chain"
                );
            },
        },

        {
            name: "nexus_damages",
            description:
                "Aggregate damages across all claims and lanes. Shows conservative and aggressive amounts by lane and category.",
            parameters: {
                type: "object",
                properties: {
                    lane: {
                        type: "string",
                        description: "Optional lane filter. Omit for all lanes.",
                    },
                },
            },
            handler: async (args) => {
                let sql =
                    "SELECT lane, category, SUM(amount_conservative) AS conservative, " +
                    "SUM(amount_aggressive) AS aggressive, COUNT(*) AS claim_count " +
                    "FROM damages";
                const params = [];
                if (args?.lane) {
                    sql += " WHERE lane LIKE ?";
                    params.push(`%${args.lane}%`);
                }
                sql += " GROUP BY lane, category ORDER BY aggressive DESC";

                const result = await queryDB({
                    action: "query",
                    sql,
                    params,
                    max_rows: 50,
                });

                return "## 💰 Damages Summary\n\n" + formatResult(result);
            },
        },

        {
            name: "judicial_intel",
            description:
                "Judicial intelligence findings for judges. Shows patterns, bias indicators, violation types, and misconduct evidence.",
            parameters: {
                type: "object",
                properties: {
                    judge: {
                        type: "string",
                        description: "Judge name (e.g. 'McNeill', 'Hoopes'). Omit for all judges.",
                    },
                },
            },
            handler: async (args) => {
                const conditions = [];
                const params = [];
                if (args?.judge) {
                    conditions.push("(description LIKE ? OR source_file LIKE ?)");
                    params.push(`%${args.judge}%`, `%${args.judge}%`);
                }
                const where = conditions.length ? "WHERE " + conditions.join(" AND ") : "";

                const result = await queryDB({
                    action: "query",
                    sql: `SELECT violation_type, COUNT(*) AS cnt, ` +
                        `GROUP_CONCAT(DISTINCT severity) AS severities, ` +
                        `GROUP_CONCAT(DISTINCT source_file) AS sources ` +
                        `FROM judicial_violations ${where} ` +
                        `GROUP BY violation_type ORDER BY cnt DESC`,
                    params,
                    max_rows: 30,
                });

                return `## 🔍 Judicial Intelligence${args?.judge ? ": " + args.judge : ""}\n\n` + formatResult(result);
            },
        },

        {
            name: "lexos_narrative",
            description:
                "⚡ Chronological narrative builder (instant, no LLM). Builds time-ordered story from 16K+ timeline events. " +
                "Filter by lane: A=custody, D=PPO, E=judicial, F=appellate, CRIMINAL.",
            parameters: {
                type: "object",
                properties: {
                    query: { type: "string", description: "Topic/keywords for narrative focus" },
                    lane: { type: "string", description: "Filter by litigation lane", enum: ["A", "B", "C", "D", "E", "F", "CRIMINAL"] },
                },
                required: ["query"],
            },
            handler: async (args) => {
                const payload = { action: "narrative", query: args.query };
                if (args.lane) payload.lane = args.lane;
                return formatNarrative(await callBridge(payload, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "lexos_filing_plan",
            description:
                "⚡ Filing strategy with deadlines, fees, and sequence (instant, no LLM). Returns prioritized filing plan.",
            parameters: {
                type: "object",
                properties: {
                    lane: { type: "string", description: "Specific lane to plan for, or omit for all" },
                },
            },
            handler: async (args) => {
                const payload = { action: "filing_plan" };
                if (args.lane) payload.lane = args.lane;
                return formatFilingPlan(await callBridge(payload, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "lexos_rules_check",
            description:
                "⚡ Procedural compliance validator (instant, no LLM). Checks MCR/MCL for requirements, deadlines, service rules.",
            parameters: {
                type: "object",
                properties: {
                    query: { type: "string", description: "Filing type or rule. E.g., 'MCR 2.003', 'motion for reconsideration'" },
                },
                required: ["query"],
            },
            handler: async (args) => {
                return formatRulesCheck(await callBridge({ action: "rules_check", query: args.query }, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "lexos_adversary",
            description:
                "⚡ Deep adversary profile builder (instant, no LLM). Builds comprehensive profile from " +
                "impeachment, contradictions, evidence, and timeline. Shows credibility score, weaknesses.",
            parameters: {
                type: "object",
                properties: {
                    person: { type: "string", description: "Person name. E.g., 'Emily Watson', 'McNeill', 'Pamela Rusco'" },
                },
                required: ["person"],
            },
            handler: async (args) => {
                return formatAdversary(await callBridge({ action: "adversary", person: args.person }, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "lexos_gap_analysis",
            description:
                "⚡ Missing evidence, claims, and filings detector (instant, no LLM). " +
                "Identifies gaps: missing evidence, unclaimed damages, unfiled motions, weak authority chains.",
            parameters: {
                type: "object",
                properties: {
                    lane: { type: "string", description: "Specific lane to analyze, or omit for all" },
                },
            },
            handler: async (args) => {
                const payload = { action: "gap_analysis" };
                if (args.lane) payload.lane = args.lane;
                return formatGapAnalysis(await callBridge(payload, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "lexos_cross_connect",
            description:
                "⚡ Cross-lane intelligence fusion (instant, no LLM). Traces a topic across all litigation " +
                "lanes to find connections, patterns, and shared evidence.",
            parameters: {
                type: "object",
                properties: {
                    topic: { type: "string", description: "Topic to trace. E.g., 'false allegations', 'parental alienation'" },
                },
                required: ["topic"],
            },
            handler: async (args) => {
                return formatCrossConnect(await callBridge({ action: "cross_connect", topic: args.topic }, BRIDGE_TIMEOUT));
            },
        },

        {
            name: "timeline_search",
            description:
                "Search the litigation timeline for events by date range, category, or actor. 16K+ events chronologically indexed.",
            parameters: {
                type: "object",
                properties: {
                    query: {
                        type: "string",
                        description: "FTS5 search terms for event text",
                    },
                    date_from: {
                        type: "string",
                        description: "Start date (YYYY-MM-DD)",
                    },
                    date_to: {
                        type: "string",
                        description: "End date (YYYY-MM-DD)",
                    },
                    actor: {
                        type: "string",
                        description: "Filter by actor name",
                    },
                    limit: {
                        type: "number",
                        description: "Max results (default 30)",
                    },
                },
            },
            handler: async (args) => {
                const limit = Math.min(args.limit || 30, 100);

                if (args.query) {
                    const result = await queryDB({
                        action: "query",
                        sql: "SELECT snippet(timeline_fts, 0, '>>>', '<<<', '...', 48) AS event, " +
                            "timeline_fts.actors FROM timeline_fts WHERE timeline_fts MATCH ? " +
                            "ORDER BY timeline_fts.rank LIMIT ?",
                        params: [args.query, limit],
                        max_rows: limit,
                    });
                    return "## 📅 Timeline Results\n\n" + formatResult(result);
                }

                const conditions = [];
                const params = [];
                if (args.date_from) { conditions.push("event_date >= ?"); params.push(args.date_from); }
                if (args.date_to) { conditions.push("event_date <= ?"); params.push(args.date_to); }
                if (args.actor) { conditions.push("actors LIKE ?"); params.push(`%${args.actor}%`); }
                const where = conditions.length ? "WHERE " + conditions.join(" AND ") : "";
                params.push(limit);

                const result = await queryDB({
                    action: "query",
                    sql: `SELECT event_date, category, event_description, actors FROM timeline_events ${where} ORDER BY event_date DESC LIMIT ?`,
                    params,
                    max_rows: limit,
                });
                return "## 📅 Timeline Results\n\n" + formatResult(result);
            },
        },
    ],
});
