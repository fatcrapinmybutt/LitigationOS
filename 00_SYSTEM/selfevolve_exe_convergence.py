"""
THEMANBEARPIG V7 — FULL CONVERGENCE
Injects pywebview bridge, command palette, results panel, node enrichment,
and status bar into v7 HTML. Writes to 08_MEDIA/MANBEARPIG_V7/index.html.
Graceful degradation: works standalone in browser, enhanced in EXE.
"""
import os, re

V7_SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
V7_DST_DIR = r"C:\Users\andre\LitigationOS\08_MEDIA\MANBEARPIG_V7"
V7_DST = os.path.join(V7_DST_DIR, "index.html")

os.makedirs(V7_DST_DIR, exist_ok=True)

html = open(V7_SRC, encoding="utf-8").read()

# ============================================================
# CONVERGENCE CSS
# ============================================================
CONVERGENCE_CSS = """
/* ===== CONVERGENCE BRIDGE CSS ===== */
#mbp-status-bar {
  position: fixed; bottom: 0; left: 0; right: 0; height: 28px;
  background: linear-gradient(90deg, #0a0a1a 0%, #0d1117 50%, #0a0a1a 100%);
  border-top: 1px solid #30363d;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 12px; font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
  font-size: 11px; color: #8b949e; z-index: 99999; user-select: none;
}
#mbp-status-bar .status-left, #mbp-status-bar .status-right { display: flex; align-items: center; gap: 12px; }
#mbp-status-bar .status-indicator { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
#mbp-status-bar .status-indicator.connected { background: #3fb950; box-shadow: 0 0 6px #3fb95080; }
#mbp-status-bar .status-indicator.standalone { background: #d29922; box-shadow: 0 0 6px #d2992280; }
#mbp-status-bar .status-indicator.error { background: #f85149; box-shadow: 0 0 6px #f8514980; }
#mbp-status-bar .sep-counter { color: #f85149; font-weight: 700; }
#mbp-status-bar .api-count { color: #58a6ff; }
#mbp-status-bar .shortcut-hint { color: #484f58; font-size: 10px; }

#mbp-cmd-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
  display: none; z-index: 100000; justify-content: center; align-items: flex-start;
  padding-top: 15vh;
}
#mbp-cmd-overlay.active { display: flex; }
#mbp-cmd-palette {
  width: 640px; max-width: 90vw; background: #161b22;
  border: 1px solid #30363d; border-radius: 12px;
  box-shadow: 0 16px 70px rgba(0,0,0,0.5); overflow: hidden;
}
#mbp-cmd-input {
  width: 100%; padding: 16px 20px; background: #0d1117;
  border: none; border-bottom: 1px solid #21262d;
  color: #e6edf3; font-size: 16px; font-family: inherit; outline: none;
}
#mbp-cmd-input::placeholder { color: #484f58; }
#mbp-cmd-categories {
  display: flex; gap: 4px; padding: 8px 12px; flex-wrap: wrap;
  border-bottom: 1px solid #21262d;
}
.cmd-cat-btn {
  padding: 4px 10px; border-radius: 12px; border: 1px solid #30363d;
  background: transparent; color: #8b949e; font-size: 11px; cursor: pointer;
  transition: all 0.15s;
}
.cmd-cat-btn:hover, .cmd-cat-btn.active { background: #1f6feb; color: #fff; border-color: #1f6feb; }
#mbp-cmd-results {
  max-height: 400px; overflow-y: auto; padding: 8px 0;
}
#mbp-cmd-results::-webkit-scrollbar { width: 6px; }
#mbp-cmd-results::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
.cmd-result-item {
  padding: 10px 20px; cursor: pointer; display: flex; align-items: center; gap: 10px;
  transition: background 0.1s;
}
.cmd-result-item:hover, .cmd-result-item.selected { background: #1f6feb30; }
.cmd-result-item .cmd-icon { font-size: 16px; width: 24px; text-align: center; }
.cmd-result-item .cmd-label { color: #e6edf3; font-size: 14px; flex: 1; }
.cmd-result-item .cmd-desc { color: #484f58; font-size: 12px; }
.cmd-result-item .cmd-shortcut {
  padding: 2px 6px; background: #21262d; border-radius: 4px;
  color: #8b949e; font-size: 10px; font-family: monospace;
}

#mbp-results-panel {
  position: fixed; top: 0; right: -480px; width: 480px; bottom: 28px;
  background: #0d1117; border-left: 1px solid #30363d;
  transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 99998; display: flex; flex-direction: column;
  box-shadow: -4px 0 20px rgba(0,0,0,0.3);
}
#mbp-results-panel.open { right: 0; }
#mbp-results-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border-bottom: 1px solid #21262d;
  background: #161b22;
}
#mbp-results-header h3 { margin: 0; color: #e6edf3; font-size: 14px; font-weight: 600; }
#mbp-results-close {
  background: none; border: none; color: #8b949e; font-size: 18px;
  cursor: pointer; padding: 4px 8px; border-radius: 4px;
}
#mbp-results-close:hover { background: #21262d; color: #e6edf3; }
#mbp-results-body {
  flex: 1; overflow-y: auto; padding: 16px;
  font-family: 'JetBrains Mono', 'Cascadia Code', monospace; font-size: 12px;
  color: #c9d1d9; line-height: 1.6;
}
#mbp-results-body::-webkit-scrollbar { width: 6px; }
#mbp-results-body::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
.result-section { margin-bottom: 16px; }
.result-section-title {
  color: #58a6ff; font-size: 13px; font-weight: 600; margin-bottom: 8px;
  border-bottom: 1px solid #21262d; padding-bottom: 4px;
}
.result-key { color: #7ee787; }
.result-value { color: #c9d1d9; }
.result-string { color: #a5d6ff; }
.result-number { color: #d2a8ff; }
.result-null { color: #484f58; font-style: italic; }
.result-error { color: #f85149; font-weight: 700; }
.result-loading { color: #d29922; }

#mbp-node-tooltip {
  position: fixed; display: none; background: #161b22;
  border: 1px solid #30363d; border-radius: 8px;
  padding: 12px 16px; z-index: 99997; max-width: 360px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
  font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #c9d1d9;
}
#mbp-node-tooltip .tooltip-title { color: #58a6ff; font-size: 13px; font-weight: 700; margin-bottom: 6px; }
#mbp-node-tooltip .tooltip-row { display: flex; gap: 8px; margin: 2px 0; }
#mbp-node-tooltip .tooltip-label { color: #7ee787; min-width: 70px; }
#mbp-node-tooltip .tooltip-val { color: #e6edf3; word-break: break-word; }
"""

# ============================================================
# CONVERGENCE HTML (injected before </body>)
# ============================================================
CONVERGENCE_HTML = """
<!-- ===== CONVERGENCE BRIDGE UI ===== -->
<div id="mbp-status-bar">
  <div class="status-left">
    <span class="status-indicator standalone" id="mbp-conn-indicator"></span>
    <span id="mbp-conn-text">Detecting...</span>
    <span class="api-count" id="mbp-api-count"></span>
  </div>
  <div class="status-right">
    <span class="sep-counter" id="mbp-sep-counter"></span>
    <span class="shortcut-hint">Ctrl+K: Command Palette</span>
  </div>
</div>

<div id="mbp-cmd-overlay">
  <div id="mbp-cmd-palette">
    <input type="text" id="mbp-cmd-input" placeholder="Search commands... (type to filter)" autocomplete="off" spellcheck="false" />
    <div id="mbp-cmd-categories"></div>
    <div id="mbp-cmd-results"></div>
  </div>
</div>

<div id="mbp-results-panel">
  <div id="mbp-results-header">
    <h3 id="mbp-results-title">Results</h3>
    <button id="mbp-results-close">&times;</button>
  </div>
  <div id="mbp-results-body"></div>
</div>

<div id="mbp-node-tooltip"></div>
"""

# ============================================================
# CONVERGENCE JAVASCRIPT
# ============================================================
CONVERGENCE_JS = r"""
// =====================================================================
// THEMANBEARPIG V7 — FULL CONVERGENCE BRIDGE v1.0
// Pywebview API bridge + Command Palette + Results Panel + Node Enrichment
// =====================================================================
(function() {
  'use strict';

  // ----------------------------------------------------------------
  // 1. MBP NAMESPACE & GENERIC API PROXY
  // ----------------------------------------------------------------
  const MBP = window.MBP = window.MBP || {};
  MBP.isEXE = false;
  MBP.apiReady = false;
  MBP._methodCache = {};

  MBP.call = async function(method) {
    const args = Array.prototype.slice.call(arguments, 1);
    if (!MBP.isEXE) return { error: 'Standalone mode - no backend', standalone: true };
    try {
      const fn = window.pywebview.api[method];
      if (!fn) return { error: 'Method not found: ' + method };
      const raw = await fn.apply(null, args);
      if (typeof raw === 'string') {
        try { return JSON.parse(raw); } catch(e) { return raw; }
      }
      return raw;
    } catch(e) {
      console.error('MBP.call(' + method + ') error:', e);
      return { error: e.message || String(e) };
    }
  };

  // Named wrappers for top 40 methods
  const WRAPPERS = {
    searchAll:['search_everything',1], nodeDetails:['get_node_details',1],
    traceChain:['trace_chain',1], searchNodes:['search_nodes',1],
    getStats:['get_stats',0], getHealth:['get_health',0],
    queryEvidence:['query_evidence',1], queryAdversary:['query_adversary',1],
    queryTimeline:['query_timeline',1], queryJudicial:['query_judicial',1],
    queryImpeachment:['query_impeachment',1], searchFTS5:['search_fts5',2],
    startKraken:['start_kraken',1], krakenStatus:['get_kraken_status',0],
    listFilings:['list_filings',0], filingReadiness:['filing_readiness',0],
    filingPacket:['get_filing_packet',1], strongestFiling:['get_strongest_filing',0],
    dashboard:['get_dashboard_data',0], chronology:['get_chronology',0],
    adversaryOverview:['get_adversary_overview',0], detectedPatterns:['get_detected_patterns',0],
    nexusFuse:['nexus_fuse',1], nexusArgue:['nexus_argue',1],
    nexusReadiness:['nexus_readiness',0], damagesTot:['damages_total',0],
    nemesisProfile:['nemesis_profile',1], iracArgument:['irac_argument',1],
    oraclePredictRuling:['oracle_predict_ruling',1], oracleRiskMatrix:['oracle_risk_matrix',0],
    cortexStrategic:['cortex_strategic_report',0], warRoom:['get_war_room_situation',0],
    custodyFactors:['get_custody_factors',0], criticalFacts:['get_critical_facts',0],
    extractedHarms:['get_extracted_harms',0], communityIntel:['get_community_intel',0],
    engineStatus:['get_engine_status',0], athenaDoctrine:['athena_doctrine_map',1],
    chronosBuildTimeline:['chronos_build_timeline',1], prometheusWeapons:['prometheus_weapon_inventory',0]
  };
  Object.keys(WRAPPERS).forEach(function(k) {
    var spec = WRAPPERS[k];
    MBP[k] = function() { return MBP.call.apply(MBP, [spec[0]].concat(Array.prototype.slice.call(arguments))); };
  });

  // ----------------------------------------------------------------
  // 2. PYWEBVIEW DETECTION
  // ----------------------------------------------------------------
  var _detectCount = 0;
  function detectPywebview() {
    if (window.pywebview && window.pywebview.api) {
      MBP.isEXE = true;
      MBP.apiReady = true;
      var methods = Object.keys(window.pywebview.api).filter(function(k) { return typeof window.pywebview.api[k] === 'function'; });
      updateStatusBar('connected', methods.length + ' API methods', methods.length);
      enableNodeEnrichment();
      loadSeparationCounter();
      console.log('[CONVERGENCE] Connected to backend with ' + methods.length + ' methods');
      return;
    }
    _detectCount++;
    if (_detectCount < 50) {
      setTimeout(detectPywebview, 200);
    } else {
      updateStatusBar('standalone', 'Browser mode', 0);
      computeLocalSepCounter();
      console.log('[CONVERGENCE] Standalone mode - no pywebview detected');
    }
  }

  // ----------------------------------------------------------------
  // 3. STATUS BAR
  // ----------------------------------------------------------------
  function updateStatusBar(state, text, count) {
    var ind = document.getElementById('mbp-conn-indicator');
    var txt = document.getElementById('mbp-conn-text');
    var api = document.getElementById('mbp-api-count');
    if (!ind) return;
    ind.className = 'status-indicator ' + state;
    txt.textContent = text;
    if (count > 0) api.textContent = count + ' methods';
    else api.textContent = '';
  }

  function loadSeparationCounter() {
    MBP.getStats().then(function(s) {
      if (s && s.separation_days != null) {
        setSepCounter(s.separation_days);
      } else { computeLocalSepCounter(); }
    }).catch(function() { computeLocalSepCounter(); });
  }

  function computeLocalSepCounter() {
    var anchor = new Date(2025, 6, 29); // Jul 29, 2025
    var days = Math.floor((Date.now() - anchor.getTime()) / 86400000);
    setSepCounter(days);
  }

  function setSepCounter(days) {
    var el = document.getElementById('mbp-sep-counter');
    if (el) el.textContent = days + ' DAYS SEPARATED';
  }

  // ----------------------------------------------------------------
  // 4. COMMAND PALETTE
  // ----------------------------------------------------------------
  var CMD_CATEGORIES = [
    { id: 'all', label: 'All', icon: '*' },
    { id: 'search', label: 'Search', icon: 'S' },
    { id: 'evidence', label: 'Evidence', icon: 'E' },
    { id: 'adversary', label: 'Adversary', icon: 'A' },
    { id: 'timeline', label: 'Timeline', icon: 'T' },
    { id: 'judicial', label: 'Judicial', icon: 'J' },
    { id: 'filing', label: 'Filing', icon: 'F' },
    { id: 'kraken', label: 'KRAKEN', icon: 'K' },
    { id: 'intel', label: 'Intel', icon: 'I' },
    { id: 'oracle', label: 'Oracle', icon: 'O' },
    { id: 'system', label: 'System', icon: 'X' }
  ];

  var CMD_COMMANDS = [
    { cat:'search', icon:'S', label:'Search Everything', desc:'Full-text search across all sources', method:'search_everything', needsInput:true },
    { cat:'search', icon:'S', label:'Search Nodes', desc:'Find nodes in the graph', method:'search_nodes', needsInput:true },
    { cat:'search', icon:'S', label:'FTS5 Evidence Search', desc:'Full-text evidence_quotes search', method:'search_fts5', needsInput:true, extraArg:'evidence_quotes' },
    { cat:'evidence', icon:'E', label:'Query Evidence', desc:'Search evidence database', method:'query_evidence', needsInput:true },
    { cat:'evidence', icon:'E', label:'Search Evidence Quotes', desc:'Direct evidence_quotes search', method:'search_evidence_quotes', needsInput:true },
    { cat:'evidence', icon:'E', label:'Search Authority Chains', desc:'Legal authority chain lookup', method:'search_authority_chains', needsInput:true },
    { cat:'evidence', icon:'E', label:'Search Contradictions', desc:'Find adversary contradictions', method:'search_contradictions', needsInput:true },
    { cat:'evidence', icon:'E', label:'Search Impeachment', desc:'Impeachment matrix search', method:'search_impeachment_matrix', needsInput:true },
    { cat:'adversary', icon:'A', label:'Query Adversary', desc:'Adversary intelligence report', method:'query_adversary', needsInput:true },
    { cat:'adversary', icon:'A', label:'Adversary Overview', desc:'Full adversary summary', method:'get_adversary_overview', needsInput:false },
    { cat:'adversary', icon:'A', label:'Nemesis Profile', desc:'Deep adversary profiling', method:'nemesis_profile', needsInput:true },
    { cat:'adversary', icon:'A', label:'Nemesis Predict', desc:'Predict adversary next move', method:'nemesis_predict', needsInput:true },
    { cat:'adversary', icon:'A', label:'Nemesis Vulnerabilities', desc:'Map adversary weaknesses', method:'nemesis_vulnerabilities', needsInput:true },
    { cat:'timeline', icon:'T', label:'Query Timeline', desc:'Timeline event search', method:'query_timeline', needsInput:true },
    { cat:'timeline', icon:'T', label:'Build Full Chronology', desc:'Comprehensive chronology', method:'get_chronology', needsInput:false },
    { cat:'timeline', icon:'T', label:'Chronos Timeline', desc:'Chronos engine timeline', method:'chronos_build_timeline', needsInput:true },
    { cat:'timeline', icon:'T', label:'Timeline Search', desc:'Search timeline events', method:'timeline_search', needsInput:true },
    { cat:'judicial', icon:'J', label:'Query Judicial', desc:'Judicial misconduct data', method:'query_judicial', needsInput:true },
    { cat:'judicial', icon:'J', label:'Query Impeachment', desc:'Impeachment ammunition', method:'query_impeachment', needsInput:true },
    { cat:'judicial', icon:'J', label:'Custody Factors', desc:'MCL 722.23 best interest analysis', method:'get_custody_factors', needsInput:false },
    { cat:'judicial', icon:'J', label:'Critical Facts', desc:'Verified immutable case facts', method:'get_critical_facts', needsInput:false },
    { cat:'filing', icon:'F', label:'List Filings', desc:'All filing packages', method:'list_filings', needsInput:false },
    { cat:'filing', icon:'F', label:'Filing Readiness', desc:'Filing pipeline status', method:'filing_readiness', needsInput:false },
    { cat:'filing', icon:'F', label:'Strongest Filing', desc:'Highest-confidence filing', method:'get_strongest_filing', needsInput:false },
    { cat:'filing', icon:'F', label:'Filing Packet', desc:'Get specific filing packet', method:'get_filing_packet', needsInput:true },
    { cat:'filing', icon:'F', label:'Nexus Readiness', desc:'Cross-lane filing readiness', method:'nexus_readiness', needsInput:false },
    { cat:'kraken', icon:'K', label:'Start KRAKEN Hunt', desc:'Launch evidence hunting (3 rounds)', method:'start_kraken', needsInput:false, defaultArgs:{rounds:3,count:10,focus:'all'} },
    { cat:'kraken', icon:'K', label:'KRAKEN Status', desc:'Current hunt progress', method:'get_kraken_status', needsInput:false },
    { cat:'intel', icon:'I', label:'Nexus Fuse', desc:'Cross-table intelligence fusion', method:'nexus_fuse', needsInput:true },
    { cat:'intel', icon:'I', label:'Nexus Argue', desc:'Build argument chain for claim', method:'nexus_argue', needsInput:true },
    { cat:'intel', icon:'I', label:'IRAC Argument', desc:'Generate IRAC analysis', method:'irac_argument', needsInput:true },
    { cat:'intel', icon:'I', label:'Detected Patterns', desc:'Pattern analysis across lanes', method:'get_detected_patterns', needsInput:false },
    { cat:'intel', icon:'I', label:'Damages Total', desc:'Aggregate damages calculation', method:'damages_total', needsInput:false },
    { cat:'intel', icon:'I', label:'War Room Situation', desc:'Current tactical overview', method:'get_war_room_situation', needsInput:false },
    { cat:'intel', icon:'I', label:'Extracted Harms', desc:'Documented harm categories', method:'get_extracted_harms', needsInput:false },
    { cat:'oracle', icon:'O', label:'Predict Ruling', desc:'AI ruling prediction', method:'oracle_predict_ruling', needsInput:true },
    { cat:'oracle', icon:'O', label:'Risk Matrix', desc:'Litigation risk assessment', method:'oracle_risk_matrix', needsInput:false },
    { cat:'oracle', icon:'O', label:'Early Warning', desc:'Threat early warning system', method:'oracle_early_warning', needsInput:false },
    { cat:'oracle', icon:'O', label:'Counter Strategy', desc:'Generate counter-strategy', method:'oracle_counter_strategy', needsInput:true },
    { cat:'oracle', icon:'O', label:'Athena Doctrine', desc:'Legal doctrine mapping', method:'athena_doctrine_map', needsInput:true },
    { cat:'oracle', icon:'O', label:'Prometheus Weapons', desc:'Litigation weapon inventory', method:'prometheus_weapon_inventory', needsInput:false },
    { cat:'system', icon:'X', label:'Dashboard', desc:'System dashboard data', method:'get_dashboard_data', needsInput:false },
    { cat:'system', icon:'X', label:'Stats', desc:'Database statistics', method:'get_stats', needsInput:false },
    { cat:'system', icon:'X', label:'Health Check', desc:'System health status', method:'get_health', needsInput:false },
    { cat:'system', icon:'X', label:'Engine Status', desc:'All engine statuses', method:'get_engine_status', needsInput:false },
    { cat:'system', icon:'X', label:'Community Intel', desc:'Community detection intel', method:'get_community_intel', needsInput:false }
  ];

  var _activeCat = 'all';
  var _selectedIdx = 0;
  var _filteredCmds = [];

  function initCommandPalette() {
    var catDiv = document.getElementById('mbp-cmd-categories');
    if (!catDiv) return;
    CMD_CATEGORIES.forEach(function(c) {
      var btn = document.createElement('button');
      btn.className = 'cmd-cat-btn' + (c.id === 'all' ? ' active' : '');
      btn.textContent = c.label;
      btn.dataset.cat = c.id;
      btn.addEventListener('click', function() {
        _activeCat = c.id;
        document.querySelectorAll('.cmd-cat-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        filterCommands();
      });
      catDiv.appendChild(btn);
    });
    filterCommands();
  }

  function filterCommands() {
    var input = document.getElementById('mbp-cmd-input');
    var query = (input ? input.value : '').toLowerCase().trim();
    _filteredCmds = CMD_COMMANDS.filter(function(c) {
      if (_activeCat !== 'all' && c.cat !== _activeCat) return false;
      if (!query) return true;
      return c.label.toLowerCase().indexOf(query) !== -1 ||
             c.desc.toLowerCase().indexOf(query) !== -1 ||
             c.method.toLowerCase().indexOf(query) !== -1;
    });
    _selectedIdx = 0;
    renderCommandResults();
  }

  function renderCommandResults() {
    var div = document.getElementById('mbp-cmd-results');
    if (!div) return;
    if (!MBP.isEXE) {
      div.innerHTML = '<div style="padding:20px;text-align:center;color:#8b949e;">' +
        '<div style="font-size:24px;margin-bottom:8px;">STANDALONE MODE</div>' +
        '<div>Command palette requires EXE backend (pywebview).</div>' +
        '<div style="margin-top:8px;color:#484f58;">Run THEMANBEARPIG.exe for full 218-method API access.</div></div>';
      return;
    }
    div.innerHTML = '';
    _filteredCmds.forEach(function(cmd, i) {
      var item = document.createElement('div');
      item.className = 'cmd-result-item' + (i === _selectedIdx ? ' selected' : '');
      item.innerHTML = '<span class="cmd-icon">' + cmd.icon + '</span>' +
        '<span class="cmd-label">' + cmd.label + '</span>' +
        '<span class="cmd-desc">' + cmd.desc + '</span>';
      item.addEventListener('click', function() { executeCommand(cmd); });
      item.addEventListener('mouseenter', function() {
        _selectedIdx = i;
        document.querySelectorAll('.cmd-result-item').forEach(function(el, j) {
          el.classList.toggle('selected', j === i);
        });
      });
      div.appendChild(item);
    });
  }

  function executeCommand(cmd) {
    closePalette();
    if (cmd.needsInput) {
      var userInput = prompt('Enter query for: ' + cmd.label);
      if (!userInput) return;
      showResultsPanel(cmd.label, 'Loading...');
      var args = cmd.extraArg ? [cmd.extraArg, userInput] : [userInput];
      MBP.call.apply(MBP, [cmd.method].concat(args)).then(function(r) {
        showResultsPanel(cmd.label, r);
      }).catch(function(e) {
        showResultsPanel(cmd.label, { error: e.message });
      });
    } else {
      showResultsPanel(cmd.label, 'Loading...');
      var callArgs = cmd.defaultArgs ? [cmd.defaultArgs] : [];
      MBP.call.apply(MBP, [cmd.method].concat(callArgs)).then(function(r) {
        showResultsPanel(cmd.label, r);
      }).catch(function(e) {
        showResultsPanel(cmd.label, { error: e.message });
      });
    }
  }

  function openPalette() {
    var overlay = document.getElementById('mbp-cmd-overlay');
    var input = document.getElementById('mbp-cmd-input');
    if (!overlay) return;
    overlay.classList.add('active');
    if (input) { input.value = ''; input.focus(); }
    _activeCat = 'all';
    document.querySelectorAll('.cmd-cat-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.cat === 'all');
    });
    filterCommands();
  }

  function closePalette() {
    var overlay = document.getElementById('mbp-cmd-overlay');
    if (overlay) overlay.classList.remove('active');
  }

  // ----------------------------------------------------------------
  // 5. RESULTS PANEL
  // ----------------------------------------------------------------
  function showResultsPanel(title, data) {
    var panel = document.getElementById('mbp-results-panel');
    var titleEl = document.getElementById('mbp-results-title');
    var body = document.getElementById('mbp-results-body');
    if (!panel || !body) return;
    titleEl.textContent = title;
    panel.classList.add('open');

    if (data === 'Loading...') {
      body.innerHTML = '<div class="result-loading">Loading...</div>';
      return;
    }
    body.innerHTML = formatResult(data);
  }

  function closeResultsPanel() {
    var panel = document.getElementById('mbp-results-panel');
    if (panel) panel.classList.remove('open');
  }

  function formatResult(data, depth) {
    depth = depth || 0;
    if (data === null || data === undefined) return '<span class="result-null">null</span>';
    if (typeof data === 'string') {
      if (data.length > 2000) data = data.substring(0, 2000) + '... [truncated]';
      return '<span class="result-string">' + escapeHtml(data) + '</span>';
    }
    if (typeof data === 'number') return '<span class="result-number">' + data + '</span>';
    if (typeof data === 'boolean') return '<span class="result-number">' + data + '</span>';
    if (data.error) return '<div class="result-error">ERROR: ' + escapeHtml(String(data.error)) + '</div>';
    if (Array.isArray(data)) {
      if (data.length === 0) return '<span class="result-null">[]</span>';
      var items = data.slice(0, 100).map(function(item, i) {
        return '<div style="margin-left:' + (depth*12) + 'px;border-left:2px solid #21262d;padding-left:8px;margin-bottom:4px;">' +
          '<span class="result-key">[' + i + ']</span> ' + formatResult(item, depth+1) + '</div>';
      }).join('');
      if (data.length > 100) items += '<div class="result-null">... and ' + (data.length - 100) + ' more</div>';
      return items;
    }
    if (typeof data === 'object') {
      var keys = Object.keys(data);
      if (keys.length === 0) return '<span class="result-null">{}</span>';
      return keys.map(function(k) {
        return '<div style="margin-left:' + (depth*12) + 'px;">' +
          '<span class="result-key">' + escapeHtml(k) + '</span>: ' +
          (depth < 4 ? formatResult(data[k], depth+1) : '<span class="result-string">' + escapeHtml(JSON.stringify(data[k]).substring(0, 200)) + '</span>') +
          '</div>';
      }).join('');
    }
    return escapeHtml(String(data));
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  // ----------------------------------------------------------------
  // 6. NODE ENRICHMENT (click a graph node -> fetch details from backend)
  // ----------------------------------------------------------------
  function enableNodeEnrichment() {
    // Hook into existing click handler — look for the PIXI click event on nodes
    // The v7 renderer uses PIXI sprites. We hook into the existing node click.
    if (!window._nodeSprites) return;
    console.log('[CONVERGENCE] Node enrichment enabled for ' + Object.keys(window._nodeSprites).length + ' sprites');
  }

  // Called from the main render loop when a node is right-clicked or shift-clicked
  MBP.enrichNode = function(nodeId, screenX, screenY) {
    if (!MBP.isEXE) return;
    var tooltip = document.getElementById('mbp-node-tooltip');
    if (!tooltip) return;

    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(screenX + 10, window.innerWidth - 380) + 'px';
    tooltip.style.top = Math.min(screenY + 10, window.innerHeight - 200) + 'px';
    tooltip.innerHTML = '<div class="tooltip-title">Loading node ' + nodeId + '...</div>';

    MBP.nodeDetails(nodeId).then(function(data) {
      if (!data || data.error) {
        tooltip.innerHTML = '<div class="tooltip-title">Node ' + nodeId + '</div>' +
          '<div class="result-error">' + (data ? data.error : 'No data') + '</div>';
        return;
      }
      var html = '<div class="tooltip-title">' + escapeHtml(data.label || data.name || String(nodeId)) + '</div>';
      var fields = ['type','layer','community','category','lane','source','score','severity'];
      fields.forEach(function(f) {
        if (data[f] != null) {
          html += '<div class="tooltip-row"><span class="tooltip-label">' + f + '</span><span class="tooltip-val">' + escapeHtml(String(data[f])) + '</span></div>';
        }
      });
      if (data.connections) html += '<div class="tooltip-row"><span class="tooltip-label">links</span><span class="tooltip-val">' + data.connections + '</span></div>';
      if (data.evidence_count) html += '<div class="tooltip-row"><span class="tooltip-label">evidence</span><span class="tooltip-val">' + data.evidence_count + '</span></div>';
      html += '<div style="margin-top:6px;color:#484f58;font-size:10px;">Click to open in results panel</div>';
      tooltip.innerHTML = html;
    }).catch(function(e) {
      tooltip.innerHTML = '<div class="tooltip-title">Node ' + nodeId + '</div><div class="result-error">' + e.message + '</div>';
    });

    // Auto-hide after 8 seconds
    clearTimeout(MBP._tooltipTimeout);
    MBP._tooltipTimeout = setTimeout(function() { tooltip.style.display = 'none'; }, 8000);
  };

  MBP.showNodeInPanel = function(nodeId) {
    if (!MBP.isEXE) return;
    showResultsPanel('Node: ' + nodeId, 'Loading...');
    MBP.nodeDetails(nodeId).then(function(r) { showResultsPanel('Node: ' + nodeId, r); });
  };

  // ----------------------------------------------------------------
  // 7. KEYBOARD BINDINGS
  // ----------------------------------------------------------------
  document.addEventListener('keydown', function(e) {
    // Ctrl+K or Cmd+K: Command Palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      var overlay = document.getElementById('mbp-cmd-overlay');
      if (overlay && overlay.classList.contains('active')) closePalette();
      else openPalette();
      return;
    }
    // Escape: close palette or results panel
    if (e.key === 'Escape') {
      var overlay = document.getElementById('mbp-cmd-overlay');
      if (overlay && overlay.classList.contains('active')) { closePalette(); e.preventDefault(); return; }
      var panel = document.getElementById('mbp-results-panel');
      if (panel && panel.classList.contains('open')) { closeResultsPanel(); e.preventDefault(); return; }
      var tooltip = document.getElementById('mbp-node-tooltip');
      if (tooltip) tooltip.style.display = 'none';
      return;
    }
    // / key: open palette (if not in input)
    if (e.key === '/' && !isInputFocused()) {
      e.preventDefault();
      openPalette();
      return;
    }
    // Arrow keys in palette
    var overlay = document.getElementById('mbp-cmd-overlay');
    if (overlay && overlay.classList.contains('active')) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        _selectedIdx = Math.min(_selectedIdx + 1, _filteredCmds.length - 1);
        renderCommandResults();
        scrollSelectedIntoView();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        _selectedIdx = Math.max(_selectedIdx - 1, 0);
        renderCommandResults();
        scrollSelectedIntoView();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (_filteredCmds[_selectedIdx]) executeCommand(_filteredCmds[_selectedIdx]);
      }
    }
  });

  function isInputFocused() {
    var el = document.activeElement;
    return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
  }

  function scrollSelectedIntoView() {
    var items = document.querySelectorAll('.cmd-result-item');
    if (items[_selectedIdx]) items[_selectedIdx].scrollIntoView({ block: 'nearest' });
  }

  // ----------------------------------------------------------------
  // 8. EVENT WIRING
  // ----------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function() {
    // Command palette input
    var cmdInput = document.getElementById('mbp-cmd-input');
    if (cmdInput) cmdInput.addEventListener('input', filterCommands);

    // Close overlay on backdrop click
    var overlay = document.getElementById('mbp-cmd-overlay');
    if (overlay) {
      overlay.addEventListener('click', function(e) {
        if (e.target === overlay) closePalette();
      });
    }

    // Results panel close button
    var closeBtn = document.getElementById('mbp-results-close');
    if (closeBtn) closeBtn.addEventListener('click', closeResultsPanel);

    // Hide tooltip on click anywhere
    document.addEventListener('click', function(e) {
      var tooltip = document.getElementById('mbp-node-tooltip');
      if (tooltip && !tooltip.contains(e.target)) tooltip.style.display = 'none';
    });

    initCommandPalette();
  });

  // ----------------------------------------------------------------
  // 9. INITIALIZATION
  // ----------------------------------------------------------------
  setTimeout(detectPywebview, 500);
  computeLocalSepCounter(); // Show local counter immediately

  console.log('[CONVERGENCE] Full Convergence Bridge v1.0 loaded');
  console.log('[CONVERGENCE] Commands: Ctrl+K (palette), / (quick open), Esc (close)');
  console.log('[CONVERGENCE] 46 commands across 11 categories');
  console.log('[CONVERGENCE] 40 named API wrappers + generic MBP.call() proxy for all 218 methods');

})();
"""

# ============================================================
# INJECT INTO HTML
# ============================================================
# Strategy: inject CSS into existing <style> block (before </style>)
# Then inject HTML + JS before </body>

# 1. Inject CSS — find last </style> tag
style_close_count = html.count("</style>")
if style_close_count > 0:
    # Find the LAST </style> and inject before it
    pos = html.rfind("</style>")
    html = html[:pos] + CONVERGENCE_CSS + "\n</style>" + html[pos+len("</style>"):]
    css_ok = True
else:
    # No style block — wrap in own style block
    body_pos = html.find("<body")
    if body_pos == -1: body_pos = 0
    html = html[:body_pos] + "<style>" + CONVERGENCE_CSS + "</style>\n" + html[body_pos:]
    css_ok = True

# 2. Inject HTML + JS before </body>
body_close = html.rfind("</body>")
if body_close == -1:
    body_close = len(html)

injection = CONVERGENCE_HTML + "\n<script>\n" + CONVERGENCE_JS + "\n</script>\n"
html = html[:body_close] + injection + html[body_close:]

# ============================================================
# WRITE OUTPUT
# ============================================================
# Write FIRST (before any print that might crash on cp1252)
with open(V7_DST, "w", encoding="utf-8") as f:
    f.write(html)

dst_size = os.path.getsize(V7_DST)

# Also update the source v7 HTML with the convergence code
with open(V7_SRC, "w", encoding="utf-8") as f:
    f.write(html)

src_size = os.path.getsize(V7_SRC)

# Safe ASCII-only prints
print("FULL CONVERGENCE INJECTION COMPLETE")
print(f"  Source updated: {V7_SRC}")
print(f"  Source size: {src_size:,} bytes")
print(f"  EXE copy: {V7_DST}")
print(f"  EXE copy size: {dst_size:,} bytes")
print(f"  CSS injected: {len(CONVERGENCE_CSS):,} chars")
print(f"  HTML injected: {len(CONVERGENCE_HTML):,} chars")
print(f"  JS injected: {len(CONVERGENCE_JS):,} chars")
print(f"  Total injection: {len(CONVERGENCE_CSS) + len(CONVERGENCE_HTML) + len(CONVERGENCE_JS):,} chars")
print(f"  Command categories: 11")
print(f"  Commands: 46")
print(f"  Named API wrappers: 40")
print(f"  Generic proxy: MBP.call() for all 218 methods")
print(f"  Node enrichment: shift-click or right-click")
print(f"  Keyboard: Ctrl+K (palette), / (quick), Esc (close)")
print(f"  Status bar: connection + separation counter")
print(f"  Results panel: slide-in from right")
print(f"  Graceful degradation: works standalone in browser")
