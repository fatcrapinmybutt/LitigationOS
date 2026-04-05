// Extension: litigation-arsenal
// SINGULARITY-tier litigation intelligence toolkit
// Apex lottery harvest, evidence hunting, adversary scanning, dossier management
// fd (Rust) + DB inventory + content-first analysis — ZERO os.walk()

import { joinSession } from "@github/copilot-sdk/extension";
import { execSync } from "node:child_process";
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, basename } from "node:path";

const DB_PATH = String.raw`C:\Users\andre\LitigationOS\litigation_context.db`;
const DOSSIER_DIR = String.raw`C:\Users\andre\LitigationOS\04_ANALYSIS\ADVERSARY_TRACKS`;
const TMP_DIR = String.raw`D:\LitigationOS_tmp`;
const REPO_ROOT = String.raw`C:\Users\andre\LitigationOS`;

function runPython(script, timeout = 120000) {
    try {
        return execSync(`python -I "${script}"`, {
            cwd: TMP_DIR,
            timeout,
            encoding: "utf-8",
            env: { ...process.env, PYTHONUTF8: "1" },
            maxBuffer: 10 * 1024 * 1024,
        });
    } catch (e) {
        return `ERROR: ${e.message}\n${e.stderr || ""}`.slice(0, 5000);
    }
}

const session = await joinSession({
    tools: [
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 1: LOTTERY HARVEST — Random content-first file analysis
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "lottery_harvest",
            description: `Apex lottery harvest: picks N random files from ALL drives (using fd Rust + DB inventory — zero os.walk), reads actual content (PDF/DOCX/TXT/CSV/HTML/JSON/MD), analyzes for 22 adversary patterns, legal authorities (MCR/MCL/MRE/USC/FRCP/case law), 8 evidence categories, extracts key quotes. Returns scored results (HIGH/MEDIUM/LOW). Use when: hunting for new evidence, expanding dossiers, discovering unknown intelligence across 206K+ indexed files.`,
            parameters: {
                type: "object",
                properties: {
                    count: {
                        type: "number",
                        description: "Number of random files to draw (default 10, max 50)",
                    },
                    drives: {
                        type: "string",
                        description: "Comma-separated drive letters to include (default: all). Example: 'C,D,I'",
                    },
                    focus: {
                        type: "string",
                        description: "Optional focus topic — boosts scoring for files mentioning this. Example: 'shady oaks', 'McNeill', 'PPO'",
                    },
                },
            },
            skipPermission: true,
            handler: async (args) => {
                const count = Math.min(args.count || 10, 50);
                const drives = args.drives || "all";
                const focus = args.focus || "";
                const output = runPython(join(TMP_DIR, "lottery_v2.py"));
                const resultsPath = join(TMP_DIR, "lottery_results_v2.json");
                let results = "";
                if (existsSync(resultsPath)) {
                    results = readFileSync(resultsPath, "utf-8").slice(0, 50000);
                }
                return `LOTTERY HARVEST (${count} files)\n${output}\n\nJSON Results:\n${results}`;
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 2: DOSSIER STATUS — All adversary dossier files + stats
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "dossier_status",
            description: `List all adversary dossier files in 04_ANALYSIS/ADVERSARY_TRACKS/ with file sizes, last modified dates, and line counts. Shows the full intelligence arsenal at a glance. Use when: checking what dossiers exist, verifying coverage, planning expansion.`,
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => {
                try {
                    const files = readdirSync(DOSSIER_DIR)
                        .filter(f => f.endsWith(".md"))
                        .sort();
                    const rows = files.map(f => {
                        const fp = join(DOSSIER_DIR, f);
                        const stat = statSync(fp);
                        const content = readFileSync(fp, "utf-8");
                        const lines = content.split("\n").length;
                        const kb = (stat.size / 1024).toFixed(1);
                        const mod = stat.mtime.toISOString().slice(0, 10);
                        return `${f.padEnd(45)} ${kb.padStart(8)} KB  ${String(lines).padStart(5)} lines  ${mod}`;
                    });
                    return `ADVERSARY DOSSIER ARSENAL (${files.length} files)\n${"─".repeat(80)}\n${rows.join("\n")}\n${"─".repeat(80)}\nTotal: ${files.length} dossiers in ${DOSSIER_DIR}`;
                } catch (e) {
                    return `Error reading dossiers: ${e.message}`;
                }
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 3: INTEL DASHBOARD — Quick DB intelligence stats
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "intel_dashboard",
            description: `Quick intelligence dashboard from litigation_context.db: evidence_quotes count, timeline_events, impeachment_matrix, contradictions, judicial_violations, berry_mcneill_intelligence, authority_chains, police_reports, file_inventory totals. Plus separation day counter. Use when: session startup, checking DB health, verifying persistence.`,
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => {
                const script = `
import sqlite3, json
from datetime import date
conn = sqlite3.connect(r"${DB_PATH.replace(/\\/g, "\\\\")}")
conn.execute("PRAGMA busy_timeout=30000")
tables = [
    ("evidence_quotes", "SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0"),
    ("timeline_events", "SELECT COUNT(*) FROM timeline_events"),
    ("impeachment_matrix", "SELECT COUNT(*) FROM impeachment_matrix"),
    ("contradiction_map", "SELECT COUNT(*) FROM contradiction_map"),
    ("judicial_violations", "SELECT COUNT(*) FROM judicial_violations"),
    ("berry_mcneill_intel", "SELECT COUNT(*) FROM berry_mcneill_intelligence"),
    ("authority_chains_v2", "SELECT COUNT(*) FROM authority_chains_v2"),
    ("police_reports", "SELECT COUNT(*) FROM police_reports"),
    ("michigan_rules", "SELECT COUNT(*) FROM michigan_rules_extracted"),
    ("file_inventory", "SELECT COUNT(*) FROM file_inventory"),
]
results = {}
for name, sql in tables:
    try:
        results[name] = conn.execute(sql).fetchone()[0]
    except:
        results[name] = "N/A"
sep_days = (date.today() - date(2025, 7, 29)).days
results["separation_days"] = sep_days
conn.close()
print(json.dumps(results))
`;
                const tmpScript = join(TMP_DIR, "_intel_dash.py");
                const { writeFileSync } = await import("node:fs");
                writeFileSync(tmpScript, script, "utf-8");
                const raw = runPython(tmpScript, 15000);
                try {
                    const data = JSON.parse(raw.trim().split("\n").pop());
                    const lines = Object.entries(data).map(
                        ([k, v]) => `  ${k.padEnd(25)} ${String(v).padStart(10)}`
                    );
                    return `📊 LITIGATION INTELLIGENCE DASHBOARD\n${"═".repeat(50)}\n${lines.join("\n")}\n${"═".repeat(50)}\n⏱ Father-son separation: ${data.separation_days} days`;
                } catch {
                    return `Raw output:\n${raw}`;
                }
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 4: ADVERSARY SCAN — Deep scan for specific adversary
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "adversary_scan",
            description: `Deep adversary intelligence scan: queries evidence_quotes, impeachment_matrix, contradiction_map, timeline_events, judicial_violations, and berry_mcneill_intelligence for a specific person. Returns aggregated intelligence with top quotes, contradictions, and impeachment ammo. Use when: building or expanding a specific adversary dossier.`,
            parameters: {
                type: "object",
                properties: {
                    target: {
                        type: "string",
                        description: "Adversary name to scan for. Example: 'Emily Watson', 'McNeill', 'Rusco', 'Shady Oaks'",
                    },
                },
                required: ["target"],
            },
            skipPermission: true,
            handler: async (args) => {
                const target = args.target.replace(/'/g, "''");
                const script = `
import sqlite3, json
conn = sqlite3.connect(r"${DB_PATH.replace(/\\/g, "\\\\")}")
conn.execute("PRAGMA busy_timeout=30000")
t = '${target}'
results = {"target": t}

# Evidence quotes
try:
    rows = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE ? AND is_duplicate=0", (f'%{t}%',)).fetchone()
    results["evidence_quotes"] = rows[0]
    top = conn.execute("SELECT quote_text, source_file, category FROM evidence_quotes WHERE quote_text LIKE ? AND is_duplicate=0 ORDER BY relevance_score DESC LIMIT 5", (f'%{t}%',)).fetchall()
    results["top_quotes"] = [{"text": r[0][:200], "source": r[1], "cat": r[2]} for r in top]
except Exception as e:
    results["evidence_error"] = str(e)

# Impeachment
try:
    rows = conn.execute("SELECT COUNT(*) FROM impeachment_matrix WHERE target LIKE ?", (f'%{t}%',)).fetchone()
    results["impeachment_entries"] = rows[0]
    top = conn.execute("SELECT category, evidence_summary, impeachment_value FROM impeachment_matrix WHERE target LIKE ? ORDER BY impeachment_value DESC LIMIT 5", (f'%{t}%',)).fetchall()
    results["top_impeachment"] = [{"cat": r[0], "summary": r[1][:150], "value": r[2]} for r in top]
except:
    pass

# Contradictions
try:
    rows = conn.execute("SELECT COUNT(*) FROM contradiction_map WHERE contradiction_text LIKE ?", (f'%{t}%',)).fetchone()
    results["contradictions"] = rows[0]
except:
    pass

# Timeline
try:
    rows = conn.execute("SELECT COUNT(*) FROM timeline_events WHERE event_description LIKE ? OR actors LIKE ?", (f'%{t}%', f'%{t}%')).fetchone()
    results["timeline_events"] = rows[0]
except:
    pass

# Judicial violations
try:
    rows = conn.execute("SELECT COUNT(*) FROM judicial_violations WHERE description LIKE ? OR judge_name LIKE ?", (f'%{t}%', f'%{t}%')).fetchone()
    results["judicial_violations"] = rows[0]
except:
    pass

conn.close()
print(json.dumps(results, indent=2, default=str))
`;
                const tmpScript = join(TMP_DIR, "_adv_scan.py");
                const { writeFileSync } = await import("node:fs");
                writeFileSync(tmpScript, script, "utf-8");
                const raw = runPython(tmpScript, 30000);
                return `🎯 ADVERSARY SCAN: ${args.target}\n${raw}`;
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 5: FILE UNIVERSE — Show file counts by ext/drive
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "file_universe",
            description: `Show total file counts across all drives by extension and drive letter, using fd (Rust) for fast drives and DB file_inventory for slow USB/SD drives. Reveals the full scope of discoverable intelligence. Use when: planning evidence hunts, understanding corpus coverage.`,
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => {
                const script = `
import sqlite3, json, subprocess
results = {}

# DB inventory by drive/ext
conn = sqlite3.connect(r"${DB_PATH.replace(/\\/g, "\\\\")}")
conn.execute("PRAGMA busy_timeout=30000")
try:
    rows = conn.execute("""
        SELECT drive_letter, extension, COUNT(*) as cnt 
        FROM file_inventory 
        WHERE extension IN ('.pdf','.txt','.csv','.html','.json','.docx','.md')
        GROUP BY drive_letter, extension 
        ORDER BY cnt DESC
    """).fetchall()
    results["db_inventory"] = [{"drive": r[0], "ext": r[1], "count": r[2]} for r in rows]
    total = conn.execute("SELECT COUNT(*) FROM file_inventory").fetchone()[0]
    results["db_total"] = total
except Exception as e:
    results["db_error"] = str(e)
conn.close()

# fd count for C drive
try:
    r = subprocess.run(['fd', '--type', 'f', '-e', 'pdf', '-e', 'txt', '-e', 'csv', '-e', 'html',
        '-e', 'json', '-e', 'docx', '-e', 'md', '--no-ignore',
        '--exclude', 'node_modules', '--exclude', '.git', '--exclude', 'AppData',
        '--exclude', '__pycache__', '--exclude', '.cache',
        '.', r'C:\\Users\\andre'], capture_output=True, text=True, timeout=20, encoding='utf-8', errors='replace')
    results["fd_c_drive"] = len([l for l in r.stdout.strip().split('\\n') if l.strip()])
except Exception as e:
    results["fd_error"] = str(e)

print(json.dumps(results, indent=2))
`;
                const tmpScript = join(TMP_DIR, "_file_universe.py");
                const { writeFileSync } = await import("node:fs");
                writeFileSync(tmpScript, script, "utf-8");
                return runPython(tmpScript, 30000);
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 6: SEPARATION COUNTER — Dynamic father-son separation
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "separation_counter",
            description: `Compute father-son separation days since July 29, 2025. Dynamic, never hardcoded. Shows days, weeks, months breakdown and urgency classification.`,
            parameters: { type: "object", properties: {} },
            skipPermission: true,
            handler: async () => {
                const anchor = new Date(2025, 6, 29); // July 29, 2025
                const now = new Date();
                const days = Math.floor((now - anchor) / 86400000);
                const weeks = Math.floor(days / 7);
                const months = Math.floor(days / 30.44);
                const urgency = days > 300 ? "CRITICAL" : days > 200 ? "SEVERE" : "URGENT";
                return `FATHER-SON SEPARATION COUNTER\n${"=".repeat(40)}\n  Days:   ${days}\n  Weeks:  ${weeks}\n  Months: ${months}\n  Status: ${urgency}\n  Anchor: July 29, 2025 (last contact with L.D.W.)\n  Today:  ${now.toISOString().slice(0, 10)}\n${"=".repeat(40)}\nEvery day matters. File everything. Fight for L.D.W.`;
            },
        },

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // TOOL 7: KRACK-A-LACK (KAL) — Run KRAKEN evidence hunting rounds
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        {
            name: "krack_a_lack",
            description: `KRACK-A-LACK (KAL) — Run PROJECT KRAKEN autonomous evidence hunting rounds. Picks random files from ALL drives (fd Rust + DB inventory for 206K+ files), reads actual content (PDF/DOCX/TXT/CSV/HTML/JSON/MD), scores against 22 adversary patterns + 6 legal authority types + 8 evidence categories. HIGH findings auto-persist to evidence_quotes DB and auto-expand matching adversary dossier files. Use when: user says KAL, KRACK-A-LACK, run rounds, hunt evidence, expand dossiers, or wants autonomous multi-round evidence discovery.`,
            parameters: {
                type: "object",
                properties: {
                    rounds: {
                        type: "number",
                        description: "Number of hunting rounds to run (default 3, max 20). Each round picks 'count' random files.",
                    },
                    count: {
                        type: "number",
                        description: "Files per round (default 10, max 50).",
                    },
                    focus: {
                        type: "string",
                        description: "Focus mode: 'all' (default), 'adversary', 'judicial', 'housing', 'custody', 'ppo', 'legal'. Boosts scoring for the chosen domain.",
                    },
                    drives: {
                        type: "string",
                        description: "Comma-separated drive letters (default: all). Example: 'C,D,I'",
                    },
                },
            },
            skipPermission: true,
            handler: async (args) => {
                const rounds = Math.min(args.rounds || 3, 20);
                const count = Math.min(args.count || 10, 50);
                const focus = args.focus || "all";
                const drives = args.drives || "";
                const krakenPath = join(TMP_DIR, "kraken.py");
                if (!existsSync(krakenPath)) {
                    return "ERROR: kraken.py not found at " + krakenPath;
                }
                let cmd = `python -I "${krakenPath}" --rounds ${rounds} --count ${count} --focus ${focus}`;
                if (drives) cmd += ` --drives ${drives}`;
                try {
                    const timeout = Math.max(rounds * count * 8000, 60000); // ~8s per file, min 60s
                    const result = execSync(cmd, {
                        cwd: TMP_DIR,
                        timeout,
                        encoding: "utf-8",
                        env: { ...process.env, PYTHONUTF8: "1" },
                        maxBuffer: 10 * 1024 * 1024,
                    });
                    return `KRACK-A-LACK COMPLETE\n${"=".repeat(50)}\n${result}`;
                } catch (e) {
                    const out = (e.stdout || "") + "\n" + (e.stderr || "");
                    return `KAL run error (may have partial results):\n${out.slice(0, 8000)}`;
                }
            },
        },
    ],

    hooks: {
        onSessionStart: async (input) => {
            const anchor = new Date(2025, 6, 29);
            const days = Math.floor((new Date() - anchor) / 86400000);
            return {
                additionalContext: `[LitigationOS Arsenal Active] Separation: ${days} days. Tools: lottery_harvest, dossier_status, intel_dashboard, adversary_scan, file_universe, separation_counter.`,
            };
        },
    },
});
