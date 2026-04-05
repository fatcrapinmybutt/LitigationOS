"""THEMANBEARPIG v8.0 — SINGULARITY CONVERGENCE
20-layer PixiJS WebGL2 + D3.js v7 litigation intelligence mega-visualization.
Packaged as standalone Windows .exe via PyInstaller + pywebview (edgechromium).

v8.0: LitigationAPI js_api bridge — 15 methods providing live DB access.
All queries read-only. Graceful degradation if DB not found.
"""
import webview, sys, os, re, sqlite3, json, traceback
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

VERSION = "8.0.0"
TITLE = f"THEMANBEARPIG v{VERSION} — SINGULARITY CONVERGENCE"

# ═══════════════ CONFIG ═══════════════
SEP_DATE = date(2025, 7, 29)
DB_SEARCH_PATHS = [
    Path(r"C:\Users\andre\LitigationOS\litigation_context.db"),
    Path(os.path.expanduser("~/LitigationOS/litigation_context.db")),
]
READONLY_BLOCK = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|REPLACE|ATTACH|DETACH|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


def _find_db():
    for p in DB_SEARCH_PATHS:
        if p.exists():
            return p
    return None


class LitigationAPI:
    """pywebview js_api — silent background intelligence layer.
    All methods return JSON-serializable dicts/lists.
    Lazy DB connection. Graceful degradation if DB missing.
    """

    def __init__(self):
        self._conn = None
        self._db_path = _find_db()
        self._db_available = self._db_path is not None

    def _get_conn(self):
        if self._conn is not None:
            return self._conn
        if not self._db_available:
            return None
        try:
            self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._conn.execute("PRAGMA busy_timeout=60000")
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA cache_size=-32000")
            self._conn.execute("PRAGMA temp_store=MEMORY")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.row_factory = sqlite3.Row
        except Exception:
            self._conn = None
            self._db_available = False
        return self._conn

    @staticmethod
    def _sanitize_fts5(q):
        return re.sub(r'[^\w\s*"]', ' ', q).strip()

    def _safe_query(self, sql, params=(), limit=100):
        conn = self._get_conn()
        if conn is None:
            return []
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows[:limit]]
        except Exception:
            return []

    # ── U01: Live separation counter ──
    def get_live_data(self):
        sep = (date.today() - SEP_DATE).days
        conn = self._get_conn()
        stats = {}
        if conn:
            try:
                row = conn.execute("""
                    SELECT
                        (SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0) AS ev,
                        (SELECT COUNT(*) FROM judicial_violations) AS jv,
                        (SELECT COUNT(*) FROM impeachment_matrix) AS im,
                        (SELECT COUNT(*) FROM timeline_events) AS tl,
                        (SELECT COUNT(*) FROM contradiction_map) AS ct
                """).fetchone()
                stats = dict(row) if row else {}
            except Exception:
                pass
        return {
            "sep_days": sep,
            "sep_date": "2025-07-29",
            "today": date.today().isoformat(),
            "db_available": self._db_available,
            "db_path": str(self._db_path) if self._db_path else None,
            "stats": stats,
        }

    # ── U02: Live filing dashboard ──
    def get_filing_status(self):
        return self._safe_query("""
            SELECT vehicle_name, status, confidence, filed_date, deadline,
                   notes, last_updated
            FROM filing_readiness
            ORDER BY confidence DESC
        """)

    # ── U03: Timeline months for scrubber ──
    def get_timeline_months(self):
        rows = self._safe_query("""
            SELECT DISTINCT substr(event_date, 1, 7) AS month
            FROM timeline_events
            WHERE event_date IS NOT NULL AND length(event_date) >= 7
            ORDER BY month
        """, limit=500)
        return [r["month"] for r in rows]

    def get_timeline(self, from_date=None, to_date=None, actor=None, limit=50):
        sql = "SELECT event_date, event_description, actors, source_document FROM timeline_events WHERE 1=1"
        params = []
        if from_date:
            sql += " AND event_date >= ?"
            params.append(from_date)
        if to_date:
            sql += " AND event_date <= ?"
            params.append(to_date)
        if actor:
            sql += " AND actors LIKE ?"
            params.append(f"%{actor}%")
        sql += " ORDER BY event_date DESC LIMIT ?"
        params.append(limit)
        return self._safe_query(sql, tuple(params), limit=limit)

    # ── U04: Deep evidence search (FTS5 + LIKE fallback) ──
    def search_evidence(self, query, limit=20):
        if not query or not query.strip():
            return []
        conn = self._get_conn()
        if conn is None:
            return []
        clean = self._sanitize_fts5(query)
        results = []
        if clean:
            try:
                results = self._safe_query("""
                    SELECT e.id, e.quote_text, e.source_file, e.page_number,
                           e.category, e.lane, e.relevance_score
                    FROM evidence_quotes e
                    JOIN evidence_fts f ON e.rowid = f.rowid
                    WHERE evidence_fts MATCH ? AND e.is_duplicate = 0
                    ORDER BY e.relevance_score DESC
                    LIMIT ?
                """, (clean, limit), limit=limit)
            except Exception:
                pass
        if not results:
            results = self._safe_query("""
                SELECT id, quote_text, source_file, page_number,
                       category, lane, relevance_score
                FROM evidence_quotes
                WHERE is_duplicate = 0
                  AND quote_text LIKE ?
                ORDER BY relevance_score DESC
                LIMIT ?
            """, (f"%{query.strip()[:100]}%", limit), limit=limit)
        return results

    # ── U05: Node intel (evidence + impeachment + contradictions) ──
    def get_node_intel(self, node_label):
        if not node_label:
            return {}
        like = f"%{node_label[:100]}%"
        evidence = self._safe_query("""
            SELECT quote_text, source_file, page_number, category, relevance_score
            FROM evidence_quotes
            WHERE is_duplicate = 0 AND quote_text LIKE ?
            ORDER BY relevance_score DESC LIMIT 5
        """, (like,), limit=5)
        impeachment = self._safe_query("""
            SELECT target, category, evidence_summary, impeachment_value,
                   cross_exam_question
            FROM impeachment_matrix
            WHERE target LIKE ? OR evidence_summary LIKE ?
            ORDER BY impeachment_value DESC LIMIT 5
        """, (like, like), limit=5)
        contradictions = self._safe_query("""
            SELECT actor, statement_1, statement_2, severity, source_1, source_2
            FROM contradiction_map
            WHERE actor LIKE ?
            ORDER BY severity DESC LIMIT 5
        """, (like,), limit=5)
        timeline = self._safe_query("""
            SELECT event_date, event_description, actors
            FROM timeline_events
            WHERE event_description LIKE ? OR actors LIKE ?
            ORDER BY event_date DESC LIMIT 5
        """, (like, like), limit=5)
        ev_count = 0
        conn = self._get_conn()
        if conn:
            try:
                r = conn.execute(
                    "SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0 AND quote_text LIKE ?",
                    (like,),
                ).fetchone()
                ev_count = r[0] if r else 0
            except Exception:
                pass
        return {
            "label": node_label,
            "evidence_count": ev_count,
            "evidence": evidence,
            "impeachment": impeachment,
            "contradictions": contradictions,
            "timeline": timeline,
        }

    # ── U06: Adversary dossier ──
    def get_dossier(self, name):
        if not name:
            return {}
        like = f"%{name[:100]}%"
        violations = self._safe_query("""
            SELECT violation_type, COUNT(*) as cnt
            FROM judicial_violations
            WHERE description LIKE ? OR actor LIKE ?
            GROUP BY violation_type ORDER BY cnt DESC LIMIT 10
        """, (like, like), limit=10)
        impeach = self._safe_query("""
            SELECT category, COUNT(*) as cnt,
                   ROUND(AVG(impeachment_value), 1) as avg_sev
            FROM impeachment_matrix
            WHERE target LIKE ?
            GROUP BY category ORDER BY cnt DESC LIMIT 10
        """, (like,), limit=10)
        contradicts = self._safe_query("""
            SELECT statement_1, statement_2, severity, source_1, source_2
            FROM contradiction_map WHERE actor LIKE ?
            ORDER BY severity DESC LIMIT 10
        """, (like,), limit=10)
        ev_count = 0
        conn = self._get_conn()
        if conn:
            try:
                r = conn.execute(
                    "SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0 AND quote_text LIKE ?",
                    (like,),
                ).fetchone()
                ev_count = r[0] if r else 0
            except Exception:
                pass
        return {
            "name": name,
            "evidence_count": ev_count,
            "violations": violations,
            "impeachment": impeach,
            "contradictions": contradicts,
        }

    # ── U07: Judicial intel ──
    def get_judicial_intel(self, judge=None):
        like = f"%{judge[:100]}%" if judge else "%McNeill%"
        violations = self._safe_query("""
            SELECT violation_type, COUNT(*) as cnt
            FROM judicial_violations
            WHERE description LIKE ? OR actor LIKE ?
            GROUP BY violation_type ORDER BY cnt DESC
        """, (like, like), limit=20)
        cartel = self._safe_query("""
            SELECT person, connection_type, description, evidence_source
            FROM berry_mcneill_intelligence
            ORDER BY id LIMIT 20
        """, limit=20)
        return {"judge": judge, "violations": violations, "cartel": cartel}

    # ── U10: Read-only SQL console ──
    def run_query(self, sql):
        if not sql or not sql.strip():
            return {"error": "Empty query"}
        if READONLY_BLOCK.search(sql):
            return {"error": "Write operations blocked — read-only access"}
        return {"rows": self._safe_query(sql, limit=200)}

    # ── U17: Annotation sync ──
    def sync_annotations(self, annotations_json):
        """Receive annotations from JS localStorage, persist to DB."""
        conn = self._get_conn()
        if conn is None:
            return {"synced": False, "reason": "no_db"}
        try:
            annots = json.loads(annotations_json) if isinstance(annotations_json, str) else annotations_json
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mbp_annotations (
                    node_id TEXT PRIMARY KEY,
                    text TEXT,
                    type TEXT,
                    label TEXT,
                    ts INTEGER,
                    synced_at TEXT
                )
            """)
            for nid, data in annots.items():
                conn.execute("""
                    INSERT OR REPLACE INTO mbp_annotations (node_id, text, type, label, ts, synced_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (nid, data.get("text", ""), data.get("type", "note"),
                      data.get("label", ""), data.get("ts", 0)))
            conn.commit()
            return {"synced": True, "count": len(annots)}
        except Exception as e:
            return {"synced": False, "reason": str(e)}

    def load_annotations(self):
        return self._safe_query("""
            SELECT node_id, text, type, label, ts FROM mbp_annotations ORDER BY ts DESC
        """, limit=500)

    # ── U20: Live stats dashboard ──
    def get_stats(self):
        conn = self._get_conn()
        if conn is None:
            return {}
        try:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0) AS evidence,
                    (SELECT COUNT(*) FROM judicial_violations) AS violations,
                    (SELECT COUNT(*) FROM impeachment_matrix) AS impeachment,
                    (SELECT COUNT(*) FROM timeline_events) AS timeline,
                    (SELECT COUNT(*) FROM contradiction_map) AS contradictions,
                    (SELECT COUNT(*) FROM authority_chains_v2) AS authority_chains,
                    (SELECT COUNT(*) FROM master_citations) AS citations,
                    (SELECT COUNT(*) FROM police_reports) AS police,
                    (SELECT COUNT(*) FROM berry_mcneill_intelligence) AS cartel_intel
            """).fetchone()
            return dict(row) if row else {}
        except Exception:
            return {}

    # ── U18: Pattern detection ──
    def get_patterns(self):
        retaliation = self._safe_query("""
            SELECT t1.event_date AS trigger_date, t1.event_description AS trigger_event,
                   t2.event_date AS response_date, t2.event_description AS response_event
            FROM timeline_events t1
            JOIN timeline_events t2 ON t2.event_date > t1.event_date
                AND julianday(t2.event_date) - julianday(t1.event_date) BETWEEN 0 AND 7
            WHERE t1.actors LIKE '%Pigors%' AND t2.actors LIKE '%Watson%'
                AND (t2.event_description LIKE '%ex parte%'
                     OR t2.event_description LIKE '%PPO%'
                     OR t2.event_description LIKE '%contempt%'
                     OR t2.event_description LIKE '%order%')
            ORDER BY t1.event_date DESC LIMIT 20
        """, limit=20)
        escalation = self._safe_query("""
            SELECT event_date, event_description, actors
            FROM timeline_events
            WHERE event_description LIKE '%jail%'
               OR event_description LIKE '%incarcerat%'
               OR event_description LIKE '%suspend%'
               OR event_description LIKE '%ex parte%'
               OR event_description LIKE '%contempt%'
            ORDER BY event_date LIMIT 30
        """, limit=30)
        return {"retaliation": retaliation, "escalation": escalation}

    # ── Search impeachment (for cmd palette) ──
    def search_impeachment(self, target, min_severity=0):
        return self._safe_query("""
            SELECT target, category, evidence_summary, impeachment_value,
                   cross_exam_question, source_file
            FROM impeachment_matrix
            WHERE target LIKE ? AND impeachment_value >= ?
            ORDER BY impeachment_value DESC LIMIT 20
        """, (f"%{target[:100]}%", min_severity), limit=20)

    # ── Search contradictions ──
    def search_contradictions(self, entity):
        return self._safe_query("""
            SELECT actor, statement_1, statement_2, severity, source_1, source_2
            FROM contradiction_map
            WHERE actor LIKE ?
            ORDER BY severity DESC LIMIT 20
        """, (f"%{entity[:100]}%",), limit=20)


# ═══════════════ JS INJECTION ═══════════════

INJECT_JS = r"""
(function() {
    // Guard: only run if pywebview API is available
    if (!window.pywebview || !window.pywebview.api) return;
    const API = window.pywebview.api;
    const $ = id => document.getElementById(id);

    // ── U01: Live Separation Counter ──
    API.get_live_data().then(d => {
        if (!d || !d.sep_days) return;
        const el = $('sep-days');
        if (el) {
            el.textContent = d.sep_days;
            if (d.sep_days > 300) {
                el.style.animation = 'pulse-red 1.5s ease-in-out infinite';
                const style = document.createElement('style');
                style.textContent = '@keyframes pulse-red{0%,100%{opacity:1}50%{opacity:0.5;text-shadow:0 0 20px #ff2244}}';
                document.head.appendChild(style);
            }
            el.title = 'Last contact: ' + d.sep_date + ' | Today: ' + d.today;
        }
        // Store for export/MD
        if (typeof SEP_DAYS !== 'undefined') window.SEP_DAYS = d.sep_days;

        // ── U20: Live stats in HUD ──
        if (d.stats) {
            const hud = $('hud');
            if (hud) {
                const s = d.stats;
                let html = hud.innerHTML;
                if (!html.includes('db-stats')) {
                    const div = document.createElement('div');
                    div.id = 'db-stats';
                    div.style.cssText = 'margin-top:4px;border-top:1px solid rgba(0,229,255,0.2);padding-top:4px;font-size:9px;color:var(--text2)';
                    div.innerHTML = '📊 EV:' + (s.ev||0).toLocaleString() +
                        ' JV:' + (s.jv||0).toLocaleString() +
                        ' IM:' + (s.im||0).toLocaleString() +
                        ' TL:' + (s.tl||0).toLocaleString() +
                        ' CT:' + (s.ct||0).toLocaleString();
                    hud.appendChild(div);
                }
            }
        }
    });

    // ── U02: Live Filing Dashboard ──
    const origRenderFilings = window.renderFilings;
    window.renderFilings = function() {
        API.get_filing_status().then(filings => {
            const ls = $('filing-list');
            if (!ls || !filings || filings.length === 0) {
                if (origRenderFilings) origRenderFilings();
                return;
            }
            ls.innerHTML = filings.map(f => {
                const color = f.status === 'FILED' ? '#00ff88' :
                              f.status === 'DRAFT' ? '#ffcc44' :
                              f.status === 'QA_REVIEW' ? '#00ccff' : '#ff4466';
                const conf = f.confidence ? Math.round(f.confidence * 100) + '%' : '?';
                return '<div style="margin:4px 0;padding:4px;border-left:3px solid ' + color + ';padding-left:6px">' +
                    '<div style="color:' + color + ';font-weight:bold">' + (f.vehicle_name||'?') + '</div>' +
                    '<div>Status: ' + (f.status||'?') + ' | Conf: ' + conf + '</div>' +
                    (f.deadline ? '<div style="color:#ff8800">⏰ ' + f.deadline + '</div>' : '') +
                    '</div>';
            }).join('');
        });
    };

    // ── U03: Populate Timeline ──
    API.get_timeline_months().then(months => {
        if (!months || months.length === 0) return;
        if (typeof TL_MONTHS !== 'undefined' && TL_MONTHS.length === 0) {
            months.forEach(m => TL_MONTHS.push(m));
            const slider = $('tl-slider');
            if (slider) {
                slider.max = TL_MONTHS.length - 1;
                slider.value = TL_MONTHS.length - 1;
            }
            const cur = $('tl-current');
            if (cur) cur.textContent = TL_MONTHS[TL_MONTHS.length - 1] || '';
        }
    });

    // ── U04: Deep Evidence Search ──
    const origSearch = $('search');
    if (origSearch) {
        const input = origSearch.querySelector('input');
        if (input) {
            let searchTimer = null;
            const dropdown = document.createElement('div');
            dropdown.id = 'ev-search-results';
            dropdown.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:rgba(4,8,20,0.96);border:1px solid rgba(0,229,255,0.2);border-radius:0 0 6px 6px;max-height:300px;overflow-y:auto;display:none;z-index:200;font-size:10px;backdrop-filter:blur(8px)';
            origSearch.style.position = 'relative';
            origSearch.appendChild(dropdown);

            input.addEventListener('input', function() {
                clearTimeout(searchTimer);
                const q = this.value.trim();
                if (q.length < 3) { dropdown.style.display = 'none'; return; }
                searchTimer = setTimeout(() => {
                    API.search_evidence(q, 5).then(results => {
                        if (!results || results.length === 0) {
                            dropdown.style.display = 'none';
                            return;
                        }
                        dropdown.innerHTML = '<div style="padding:4px 8px;color:var(--accent);font-weight:bold;border-bottom:1px solid rgba(0,229,255,0.1)">📄 Evidence (' + results.length + ')</div>' +
                            results.map(r => '<div style="padding:4px 8px;border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer" onmouseover="this.style.background=\'rgba(0,204,255,0.1)\'" onmouseout="this.style.background=\'none\'">' +
                                '<div style="color:var(--text1)">' + (r.quote_text||'').substring(0, 120) + '...</div>' +
                                '<div style="color:var(--text2);font-size:8px">' + (r.source_file||'?') + (r.page_number ? ' p.' + r.page_number : '') + ' | ' + (r.lane||'?') + ' | ' + (r.category||'') + '</div>' +
                            '</div>').join('');
                        dropdown.style.display = 'block';
                    });
                }, 400);
            });

            input.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 300));
        }
    }

    // ── U05: Enhanced Node Info Panel ──
    const origShowInfo = window.showInfo;
    window.showInfo = function(n) {
        if (origShowInfo) origShowInfo(n);
        if (!n || !n.label) return;
        API.get_node_intel(n.label).then(intel => {
            const body = $('info-body');
            if (!body || !intel) return;
            let extra = '';
            if (intel.evidence_count > 0) {
                extra += '<div style="margin-top:8px;border-top:1px solid rgba(0,229,255,0.15);padding-top:6px">';
                extra += '<div style="color:var(--accent);font-weight:bold">📊 DB Intelligence</div>';
                extra += '<div style="color:var(--text2)">Evidence: ' + intel.evidence_count.toLocaleString() + ' items</div>';
                if (intel.evidence && intel.evidence.length > 0) {
                    extra += '<div style="margin-top:4px;font-size:9px">';
                    intel.evidence.slice(0, 3).forEach(e => {
                        extra += '<div style="margin:2px 0;padding:2px 4px;background:rgba(0,204,255,0.05);border-radius:3px">"' +
                            (e.quote_text||'').substring(0, 100) + '..."<br><span style="color:var(--text2)">' +
                            (e.source_file||'') + '</span></div>';
                    });
                    extra += '</div>';
                }
                if (intel.impeachment && intel.impeachment.length > 0) {
                    extra += '<div style="color:#ff3366;margin-top:4px">🎯 Impeachment: ' + intel.impeachment.length + '</div>';
                    intel.impeachment.slice(0, 2).forEach(im => {
                        extra += '<div style="font-size:9px;margin:2px 0;padding:2px 4px;background:rgba(255,51,102,0.05);border-radius:3px">' +
                            (im.evidence_summary||'').substring(0, 80) + ' (sev:' + (im.impeachment_value||'?') + ')</div>';
                    });
                }
                if (intel.contradictions && intel.contradictions.length > 0) {
                    extra += '<div style="color:#ff4466;margin-top:4px">⚡ Contradictions: ' + intel.contradictions.length + '</div>';
                }
                extra += '</div>';
            }
            if (extra) body.innerHTML += extra;
        });
    };

    // ── U10: DB Commands in Command Palette ──
    if (typeof CMDS !== 'undefined') {
        const dbCmds = [
            {n:'🔍 Search evidence...', a:() => {
                const q = prompt('Search evidence:');
                if (q) API.search_evidence(q, 10).then(r => {
                    if (r && r.length > 0) alert('Found ' + r.length + ' results:\n\n' + r.map(e => '• ' + (e.quote_text||'').substring(0,80)).join('\n'));
                    else alert('No evidence found for: ' + q);
                });
            }},
            {n:'🎯 Impeachment lookup...', a:() => {
                const t = prompt('Target name:');
                if (t) API.search_impeachment(t, 0).then(r => {
                    alert('Impeachment items: ' + (r?r.length:0) + '\n\n' + (r||[]).slice(0,5).map(i => '• [' + (i.impeachment_value||'?') + '] ' + (i.evidence_summary||'').substring(0,60)).join('\n'));
                });
            }},
            {n:'⚡ Contradictions...', a:() => {
                const e = prompt('Entity name:');
                if (e) API.search_contradictions(e).then(r => {
                    alert('Contradictions: ' + (r?r.length:0) + '\n\n' + (r||[]).slice(0,5).map(c => '• "' + (c.statement_1||'').substring(0,40) + '" vs "' + (c.statement_2||'').substring(0,40) + '"').join('\n'));
                });
            }},
            {n:'⚖️ Judicial intel', a:() => {
                API.get_judicial_intel('McNeill').then(r => {
                    const v = (r.violations||[]).map(v => v.cnt + ' ' + v.violation_type).join('\n');
                    alert('Judicial Violations:\n' + v);
                });
            }},
            {n:'📅 Recent timeline events', a:() => {
                API.get_timeline(null, null, null, 15).then(r => {
                    alert('Recent Events:\n\n' + (r||[]).map(e => e.event_date + ' — ' + (e.event_description||'').substring(0,60)).join('\n'));
                });
            }},
            {n:'📁 Filing readiness', a:() => {
                API.get_filing_status().then(r => {
                    alert('Filings:\n\n' + (r||[]).map(f => (f.status||'?') + ' | ' + (f.vehicle_name||'?') + ' (' + Math.round((f.confidence||0)*100) + '%)').join('\n'));
                });
            }},
            {n:'📊 Case statistics', a:() => {
                API.get_stats().then(s => {
                    if (!s) { alert('No stats available'); return; }
                    alert('Case Statistics:\n\n' + Object.entries(s).map(([k,v]) => k + ': ' + (v||0).toLocaleString()).join('\n'));
                });
            }},
            {n:'🕵️ Adversary dossier...', a:() => {
                const nm = prompt('Adversary name:');
                if (nm) API.get_dossier(nm).then(d => {
                    let msg = 'Dossier: ' + (d.name||'?') + '\nEvidence: ' + (d.evidence_count||0).toLocaleString();
                    if (d.violations && d.violations.length) msg += '\n\nViolations:\n' + d.violations.map(v => v.cnt + ' ' + v.violation_type).join('\n');
                    if (d.impeachment && d.impeachment.length) msg += '\n\nImpeachment:\n' + d.impeachment.map(i => i.cnt + ' ' + i.category + ' (avg:' + i.avg_sev + ')').join('\n');
                    alert(msg);
                });
            }},
            {n:'🔎 SQL console...', a:() => {
                const sql = prompt('Read-only SQL:');
                if (sql) API.run_query(sql).then(r => {
                    if (r.error) { alert('Error: ' + r.error); return; }
                    const rows = r.rows || [];
                    if (rows.length === 0) { alert('No results'); return; }
                    const keys = Object.keys(rows[0]);
                    alert('Results (' + rows.length + '):\n\n' + rows.slice(0,10).map(r => keys.map(k => k + '=' + r[k]).join(' | ')).join('\n'));
                });
            }},
            {n:'🔄 Sync annotations to DB', a:() => {
                const data = localStorage.getItem('mbp_annotations');
                if (!data) { alert('No annotations to sync'); return; }
                API.sync_annotations(data).then(r => {
                    alert(r.synced ? 'Synced ' + r.count + ' annotations to DB' : 'Sync failed: ' + (r.reason||'unknown'));
                });
            }},
        ];
        dbCmds.forEach(c => CMDS.push(c));
    }

    // ── U09: Evidence Density Rings (disabled by default, toggle via cmd palette) ──
    window._evDensityOn = false;
    if (typeof CMDS !== 'undefined') {
        CMDS.push({n:'Toggle evidence density rings', a:() => {
            window._evDensityOn = !window._evDensityOn;
            if (!window._evDensityOn) return;
            // Batch query for all visible node labels
            const labels = (typeof NODES !== 'undefined') ? NODES.filter(n => n._sprite && n._sprite.visible).map(n => n.label) : [];
            if (labels.length === 0) return;
            // Apply rings via node data enhancement
            labels.forEach(label => {
                API.get_node_intel(label).then(intel => {
                    if (!intel || !intel.evidence_count) return;
                    const n = (typeof nodeMap !== 'undefined') ? nodeMap.get(label) : null;
                    if (n) n._evCount = intel.evidence_count;
                });
            });
        }});
    }

    // ── U11: Keyboard Node Navigation ──
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        // Escape closes all panels
        if (e.key === 'Escape') {
            ['cmd-palette','filing-dash','annot-panel','annot-input','help','export-menu','ctx-menu','ev-search-results'].forEach(id => {
                const el = $(id);
                if (el) el.style.display = 'none';
            });
            return;
        }

        // Ctrl+B: bookmark selected node
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            if (typeof selectedNode !== 'undefined' && selectedNode) {
                let bookmarks = JSON.parse(localStorage.getItem('mbp_bookmarks') || '{}');
                if (bookmarks[selectedNode.id]) {
                    delete bookmarks[selectedNode.id];
                } else {
                    bookmarks[selectedNode.id] = {label: selectedNode.label, layer: selectedNode.layer, ts: Date.now()};
                }
                localStorage.setItem('mbp_bookmarks', JSON.stringify(bookmarks));
            }
            return;
        }

        // Tab: cycle through visible nodes
        if (e.key === 'Tab' && !e.ctrlKey && !e.shiftKey) {
            e.preventDefault();
            if (typeof NODES === 'undefined') return;
            const visible = NODES.filter(n => n._sprite && n._sprite.visible);
            if (visible.length === 0) return;
            const curIdx = selectedNode ? visible.indexOf(selectedNode) : -1;
            const next = visible[(curIdx + 1) % visible.length];
            if (next && typeof showInfo === 'function') {
                window.selectedNode = next;
                showInfo(next);
                if (next.x !== undefined && typeof transform !== 'undefined' && typeof app !== 'undefined') {
                    const tx = -next.x * transform.k + app.screen.width / 2;
                    const ty = -next.y * transform.k + app.screen.height / 2;
                }
            }
            return;
        }

        // Enter: open info for selected
        if (e.key === 'Enter' && typeof selectedNode !== 'undefined' && selectedNode) {
            if (typeof showInfo === 'function') showInfo(selectedNode);
            return;
        }
    });

    // ── U12: Bookmark commands ──
    if (typeof CMDS !== 'undefined') {
        CMDS.push({n:'⭐ Show bookmarks', a:() => {
            const bm = JSON.parse(localStorage.getItem('mbp_bookmarks') || '{}');
            const entries = Object.entries(bm);
            if (entries.length === 0) { alert('No bookmarks. Select a node and press Ctrl+B.'); return; }
            alert('Bookmarks:\n\n' + entries.map(([id, b]) => '⭐ ' + b.label + ' [' + b.layer + ']').join('\n'));
        }});
    }

    // ── U15: Session Restore ──
    try {
        const saved = JSON.parse(localStorage.getItem('mbp_session') || 'null');
        if (saved && typeof visibleLayers !== 'undefined') {
            if (saved.theme && typeof setTheme === 'function') setTheme(saved.theme);
        }
    } catch(e) {}

    // Save session state periodically
    setInterval(() => {
        try {
            const state = {
                theme: document.documentElement.getAttribute('data-theme') || 'dark',
                timestamp: Date.now(),
            };
            localStorage.setItem('mbp_session', JSON.stringify(state));
        } catch(e) {}
    }, 30000);

    // ── U07: Violation heatmap command ──
    if (typeof CMDS !== 'undefined') {
        let heatmapOn = false;
        CMDS.push({n:'🔥 Toggle violation heatmap', a:() => {
            heatmapOn = !heatmapOn;
            if (typeof NODES === 'undefined') return;
            NODES.forEach(n => {
                if (!n._sprite || n.layer !== 'JUDICIAL_CARTEL') return;
                if (heatmapOn) {
                    const attacks = (n.data && n.data.attacks) || 0;
                    const intensity = Math.min(attacks / 1000, 1);
                    n._sprite.alpha = 0.4 + intensity * 0.6;
                    n._sprite.tint = 0xff2244;
                } else {
                    n._sprite.alpha = 1;
                    n._sprite.tint = 0xffffff;
                }
            });
        }});
    }

    // ── U16: Threat Radar in HUD ──
    API.get_live_data().then(d => {
        if (!d || !d.db_available) return;
        const hud = $('hud');
        if (!hud) return;
        // Already added db-stats above, now add threat radar
        const radar = document.createElement('div');
        radar.id = 'threat-radar';
        radar.style.cssText = 'margin-top:4px;border-top:1px solid rgba(255,34,68,0.3);padding-top:4px;font-size:9px';
        const threats = (typeof NODES !== 'undefined') ?
            NODES.filter(n => n.threat >= 8).sort((a,b) => b.threat - a.threat).slice(0, 5) : [];
        if (threats.length > 0) {
            radar.innerHTML = '<span style="color:#ff2244;font-weight:bold">⚠ THREATS</span><br>' +
                threats.map(t => '<span style="color:' + t.color + '">' + t.label + ' (' + t.threat + ')</span>').join('<br>');
            hud.appendChild(radar);
        }
    });

    // ═══════════════════════════════════════════════
    // ═══ V01-V08: VISUAL UPGRADES ═══
    // ═══════════════════════════════════════════════

    // ── V04: Animated Nebula Background (CSS only, zero JS cost) ──
    const nebulaCSS = document.createElement('style');
    nebulaCSS.textContent = `
      @keyframes nebula-rotate {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      @keyframes scanline-sweep {
        0%   { top: -2px; }
        100% { top: 100%; }
      }
      body::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: -1;
        background: radial-gradient(ellipse at 20% 50%, rgba(15,5,40,0.4) 0%, transparent 50%),
                    radial-gradient(ellipse at 80% 20%, rgba(5,15,50,0.3) 0%, transparent 50%),
                    radial-gradient(ellipse at 50% 80%, rgba(30,5,30,0.2) 0%, transparent 50%);
        background-size: 200% 200%;
        animation: nebula-rotate 120s ease-in-out infinite;
        pointer-events: none;
      }
      .scan-line-fx {
        position: absolute;
        left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, rgba(0,255,136,0.12) 30%, rgba(0,255,136,0.12) 70%, transparent 100%);
        pointer-events: none;
        animation: scanline-sweep 8s linear infinite;
        z-index: 999;
      }
    `;
    document.head.appendChild(nebulaCSS);

    // ── V08: HUD Scan Line Effect ──
    ['hud', 'stats-table'].forEach(id => {
        const el = $(id);
        if (el) {
            el.style.position = el.style.position || 'relative';
            el.style.overflow = 'hidden';
            const line = document.createElement('div');
            line.className = 'scan-line-fx';
            el.appendChild(line);
        }
    });

    // ── V01: Adversary Pulse Animation ──
    // ── V03: Threat Aura Breathing ──
    // ── V05: Connection Flash on Select ──
    // ── V06: Layer Fade Transitions ──
    // ── V07: Hover Proximity Glow ──
    // All integrated into a single efficient animation frame
    (function initVisualFX() {
        if (typeof NODES === 'undefined' || typeof app === 'undefined') return;
        let vfxTime = 0;
        let flashLinks = null;  // V05: {startTime, node} when selection changes
        let fadingLayers = {};  // V06: {layerId: {target, current}}

        // V05: Track selection changes for connection flash
        let prevSelected = null;

        // V06: Override toggleLayer for fade transitions
        const origToggle = window.toggleLayer;
        if (origToggle) {
            window.toggleLayer = function(id, btn) {
                const container = (typeof layerContainers !== 'undefined') ? layerContainers[id] : null;
                if (container) {
                    const isVisible = (typeof visibleLayers !== 'undefined') && visibleLayers.has(id);
                    fadingLayers[id] = {
                        target: isVisible ? 0 : 1,
                        current: container.alpha
                    };
                }
                origToggle(id, btn);
            };
        }

        // V02: Link Flow Particles (weapon chain)
        const particlePool = [];
        const MAX_PARTICLES = 150;
        const particleContainer = new PIXI.Container();
        particleContainer.zIndex = 5;
        if (typeof world !== 'undefined') world.addChild(particleContainer);
        const pTex = (function() {
            const g = new PIXI.Graphics();
            g.beginFill(0xffffff);
            g.drawCircle(0, 0, 1.5);
            g.endFill();
            return app.renderer.generateTexture(g);
        })();
        for (let i = 0; i < MAX_PARTICLES; i++) {
            const s = new PIXI.Sprite(pTex);
            s.anchor.set(0.5);
            s.visible = false;
            s.alpha = 0;
            s._progress = 0;
            s._link = null;
            s._speed = 0;
            particlePool.push(s);
            particleContainer.addChild(s);
        }

        // Assign particles to weapon chain links
        function assignParticles() {
            if (typeof LINKS === 'undefined') return;
            const weaponLinks = LINKS.filter(l => {
                const t = l.type || '';
                return (t === 'ATTACK' || t === 'CONSPIRACY_CHAIN' || t === 'WEAPON') &&
                       typeof l.source !== 'string' && typeof l.target !== 'string';
            });
            let pi = 0;
            weaponLinks.forEach(link => {
                if (pi >= MAX_PARTICLES) return;
                const count = (link.type === 'CONSPIRACY_CHAIN') ? 3 : 2;
                for (let c = 0; c < count && pi < MAX_PARTICLES; c++) {
                    const p = particlePool[pi++];
                    p._link = link;
                    p._progress = Math.random();
                    p._speed = 0.003 + Math.random() * 0.004;
                    // Color by weapon type
                    const wt = (link.weapon_type || link.type || '').toLowerCase();
                    if (wt.includes('alleg')) p.tint = 0xff2244;
                    else if (wt.includes('parte')) p.tint = 0xcc44ff;
                    else if (wt.includes('ppo') || wt.includes('protect')) p.tint = 0xff8800;
                    else if (wt.includes('contempt')) p.tint = 0xffcc44;
                    else if (wt.includes('conspir')) p.tint = 0x00ccff;
                    else p.tint = 0x4488cc;
                }
            });
        }
        setTimeout(assignParticles, 3000);  // Wait for simulation settle

        // ── Main VFX ticker (runs every frame) ──
        app.ticker.add(() => {
            vfxTime += app.ticker.deltaMS / 1000;

            // V01: Adversary pulse + V03: Threat aura
            NODES.forEach(n => {
                if (!n._sprite || !n._sprite.visible) return;
                const layer = n.layer || '';

                // V01: Pulse adversary nodes
                if (layer === 'ADVERSARY_CORE' || layer === 'ADVERSARY_NET') {
                    const speed = 1.5 + (n.threat || 0) * 0.3;
                    n._sprite.alpha = 0.75 + 0.25 * Math.sin(vfxTime * speed);
                }

                // V03: Breathing glow for high-threat
                if (n._glow && (n.threat || 0) >= 7) {
                    const baseScale = n.r * 2.5 / 16;
                    const breathe = 1.0 + 0.12 * Math.sin(vfxTime * 0.8 + (n.id ? n.id.length : 0));
                    n._glow.scale.set(baseScale * breathe);
                    n._glow.alpha = 0.18 + 0.08 * Math.sin(vfxTime * 0.6);
                }
            });

            // V02: Update particle positions along links
            const zk = (typeof transform !== 'undefined') ? transform.k : 1;
            const showParticles = zk > 0.25;
            particlePool.forEach(p => {
                if (!p._link) { p.visible = false; return; }
                const s = p._link.source, t = p._link.target;
                if (!showParticles || s.x == null || t.x == null) { p.visible = false; return; }
                const sVis = (typeof isVis !== 'undefined') ? (isVis(s) && isVis(t)) : true;
                if (!sVis) { p.visible = false; return; }
                p._progress += p._speed;
                if (p._progress > 1) p._progress -= 1;
                const prog = p._progress;
                p.position.set(
                    s.x + (t.x - s.x) * prog,
                    s.y + (t.y - s.y) * prog
                );
                p.alpha = 0.5 + 0.3 * Math.sin(prog * Math.PI);
                p.visible = true;
            });

            // V05: Connection flash on select
            if (typeof selectedNode !== 'undefined' && selectedNode !== prevSelected) {
                prevSelected = selectedNode;
                if (selectedNode) {
                    flashLinks = { startTime: vfxTime, node: selectedNode };
                }
            }

            // V06: Layer fade transitions
            if (typeof layerContainers !== 'undefined') {
                Object.keys(fadingLayers).forEach(id => {
                    const f = fadingLayers[id];
                    const c = layerContainers[id];
                    if (!c) { delete fadingLayers[id]; return; }
                    const speed = 0.015;
                    if (Math.abs(f.current - f.target) < 0.01) {
                        c.alpha = f.target;
                        delete fadingLayers[id];
                    } else {
                        f.current += (f.target - f.current) * speed * app.ticker.deltaMS;
                        c.alpha = Math.max(0, Math.min(1, f.current));
                    }
                });
            }
        });

        // V05: Extend link drawing to include flash effect
        const origUpdateLinks = window.updateLinks;
        if (origUpdateLinks) {
            window.updateLinks = function() {
                origUpdateLinks();
                if (!flashLinks || typeof linkGfx === 'undefined') return;
                const elapsed = vfxTime - flashLinks.startTime;
                if (elapsed > 0.5) { flashLinks = null; return; }
                const flashAlpha = 0.8 * (1 - elapsed / 0.5);
                const fn = flashLinks.node;
                if (typeof LINKS === 'undefined') return;
                LINKS.forEach(l => {
                    const s = l.source, t = l.target;
                    if (typeof s === 'string' || typeof t === 'string') return;
                    if (s !== fn && t !== fn) return;
                    if (s.x == null || t.x == null) return;
                    linkGfx.lineStyle(2, 0xffffff, flashAlpha);
                    linkGfx.moveTo(s.x, s.y);
                    linkGfx.lineTo(t.x, t.y);
                });
            };
        }

        // V07: Hover proximity glow intensify
        const origMove = app.view._vfxMoveHandler;
        app.view.addEventListener('pointermove', function(e) {
            if (typeof NODES === 'undefined' || typeof transform === 'undefined') return;
            const inv = transform.invert ? transform.invert([e.offsetX, e.offsetY]) : [e.offsetX, e.offsetY];
            const wx = inv[0], wy = inv[1];
            const radius = 80;
            NODES.forEach(n => {
                if (!n._glow || !n._sprite || !n._sprite.visible) return;
                const dx = (n.x || 0) - wx, dy = (n.y || 0) - wy;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < radius) {
                    const boost = 0.18 * (1 - dist / radius);
                    n._glow.alpha = Math.min(0.5, (n._glow.alpha || 0.15) + boost);
                }
            });
        });
    })();

    console.log('[LitigationAPI] v8.0 — SINGULARITY CONVERGENCE active. 28 upgrades. DB: ' + (window.pywebview && window.pywebview.api ? 'connected' : 'offline'));
})();
"""


def get_html_path():
    if getattr(sys, '_MEIPASS', None):
        return os.path.join(sys._MEIPASS, 'THEMANBEARPIG_v7.html')
    return os.path.join(os.path.dirname(__file__), 'THEMANBEARPIG_v7.html')


def on_loaded(window):
    """Inject JS enhancements after HTML is fully loaded."""
    try:
        window.evaluate_js(INJECT_JS)
    except Exception as e:
        print(f"[LitigationAPI] JS injection error: {e}")


if __name__ == '__main__':
    html_path = get_html_path()
    if not os.path.exists(html_path):
        print(f"ERROR: {html_path} not found")
        print(f"Expected at: {html_path}")
        print("Run build_manbearpig_v7.py first to generate the HTML.")
        sys.exit(1)

    api = LitigationAPI()

    window = webview.create_window(
        TITLE,
        html_path,
        js_api=api,
        width=1920,
        height=1080,
        resizable=True,
        min_size=(1024, 768),
        background_color='#0a0a1a',
        text_select=True,
    )
    window.events.loaded += lambda: on_loaded(window)
    webview.start(gui='edgechromium', debug=False)
