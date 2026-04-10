"""
SELFEVOLVE APEX UPGRADE — Replaces basic SELFEVOLVE modules with bleeding-edge versions.

Upgrades:
- GraphQualityEngine: Real metrics (node overlap, sampled edge crossings, stress, convergence)
- BanditOptimizer (UCB1): Multi-armed bandit replacing simple zoom heuristic
- AnimatedTransitioner: Smooth lerp between force configs with easing
- InteractionHeatmap: Screen-space click/zoom/drag tracking with decay
- PluginManager: Kept as-is (solid)
- ConfigPresetManager: Upgraded with animated transitions
- BuildVersionTracker: Upgraded with quality score tracking
- GraphQualityEngine canvas arc gauge, sparkline, convergence LED
- Fix d3.forceCenter().strength() bug -> forceX/forceY
"""
import os, shutil, sys

SRC = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"
BAK = SRC + ".pre_apex_bak"

# Backup
shutil.copy2(SRC, BAK)
print(f"Backup: {BAK}")

content = open(SRC, "r", encoding="utf-8").read()
original_len = len(content)
print(f"Original: {len(content):,} chars")

# ────────────────────────────────────────
# 1. REPLACE CSS (lines 57-66)
# ────────────────────────────────────────
OLD_CSS = """#preset-bar{position:fixed;top:46px;left:12px;z-index:200;display:flex;gap:4px;align-items:center}
#preset-bar select{background:var(--panel);color:var(--text);border:1px solid var(--border);
border-radius:4px;padding:2px 6px;font-size:10px;font-family:Consolas,monospace}
#preset-bar button{background:var(--panel);color:var(--accent);border:1px solid var(--border);
border-radius:4px;padding:2px 8px;font-size:10px;cursor:pointer;font-family:Consolas,monospace}
#preset-bar button:hover{background:rgba(0,204,255,0.15)}
#evo-stats{position:fixed;top:46px;right:12px;z-index:200;font-size:9px;color:var(--text2);
font-family:Consolas,monospace;text-align:right}
#evo-stats .active-learn{color:var(--green)}
#evo-stats .learning{color:var(--gold)}"""

NEW_CSS = """/* ═══ SELFEVOLVE APEX — CSS ═══ */
#preset-bar{position:fixed;top:46px;left:12px;z-index:200;display:flex;gap:4px;align-items:center}
#preset-bar select{background:var(--panel);color:var(--text);border:1px solid var(--border);
border-radius:4px;padding:2px 6px;font-size:10px;font-family:Consolas,monospace}
#preset-bar button{background:var(--panel);color:var(--accent);border:1px solid var(--border);
border-radius:4px;padding:2px 8px;font-size:10px;cursor:pointer;font-family:Consolas,monospace}
#preset-bar button:hover{background:rgba(0,204,255,0.15)}
#preset-bar .transition-toggle{font-size:9px;padding:1px 5px;border-radius:8px}
#preset-bar .transition-toggle.active{background:rgba(0,255,136,0.2);border-color:var(--green);color:var(--green)}
#evo-stats{position:fixed;top:46px;right:12px;z-index:200;font-size:9px;color:var(--text2);
font-family:Consolas,monospace;text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:2px}
#evo-stats .active-learn{color:var(--green)}
#evo-stats .learning{color:var(--gold)}
#evo-stats .evo-row{display:flex;align-items:center;gap:6px}
#quality-gauge{width:48px;height:48px;cursor:pointer}
#quality-gauge:hover{filter:brightness(1.3)}
#quality-sparkline{width:90px;height:20px;background:rgba(0,0,0,0.3);border-radius:2px;border:1px solid var(--border)}
#convergence-led{width:8px;height:8px;border-radius:50%;display:inline-block;vertical-align:middle;margin-left:4px}
#convergence-led.converging{background:#0f0;box-shadow:0 0 4px #0f0;animation:ledpulse 1.5s infinite}
#convergence-led.active{background:#ff0;box-shadow:0 0 4px #ff0}
#convergence-led.idle{background:#555}
@keyframes ledpulse{0%,100%{opacity:1}50%{opacity:0.4}}
#bandit-stats{font-size:8px;color:var(--text2);max-width:160px;line-height:1.3}
#heatmap-indicator{font-size:8px;color:var(--gold)}
#quality-score-num{font-size:16px;font-weight:bold;font-family:Consolas,monospace}
#quality-score-num.excellent{color:#0f0}
#quality-score-num.good{color:#0c8}
#quality-score-num.fair{color:#ff0}
#quality-score-num.poor{color:#f80}
#quality-score-num.bad{color:#f00}"""

assert OLD_CSS in content, "CSS marker not found!"
content = content.replace(OLD_CSS, NEW_CSS, 1)
print("1/7 CSS replaced")

# ────────────────────────────────────────
# 2. REPLACE HUD HTML (lines 79-94)
# ────────────────────────────────────────
OLD_HUD = """<div id="evo-stats">
  <span id="evo-mode" class="learning">LEARNING</span> |
  <span id="evo-count">0</span> interactions
</div>

<div id="preset-bar">
  <select id="preset-select">
    <option value="">— preset —</option>
    <option value="dense_exploration">Dense</option>
    <option value="overview">Overview</option>
    <option value="presentation">Present</option>
    <option value="adversary_focus">Adversary</option>
  </select>
  <button id="btn-optimize" title="Auto-optimize layout from interactions (O)">⚡ Optimize</button>
  <button id="btn-save-preset" title="Save current config as preset">💾</button>
</div>"""

NEW_HUD = """<div id="evo-stats">
  <div class="evo-row">
    <canvas id="quality-gauge" width="48" height="48" title="Graph Quality Score (Q for details)"></canvas>
    <div>
      <span id="quality-score-num" class="fair" title="Composite quality 0-100">\u2014</span>
      <span id="convergence-led" class="idle" title="Convergence status"></span>
    </div>
  </div>
  <div class="evo-row">
    <canvas id="quality-sparkline" width="90" height="20" title="Quality history (last 60 ticks)"></canvas>
    <span id="evo-mode" class="learning">LEARNING</span>
  </div>
  <div class="evo-row">
    <span id="evo-count">0</span> interactions |
    <span id="bandit-stats" title="UCB1 bandit arm performance"></span>
  </div>
  <div class="evo-row">
    <span id="heatmap-indicator" title="Interaction focus centroid"></span>
  </div>
</div>

<div id="preset-bar">
  <select id="preset-select">
    <option value="">\u2014 preset \u2014</option>
    <option value="dense_exploration">Dense</option>
    <option value="overview">Overview</option>
    <option value="presentation">Present</option>
    <option value="adversary_focus">Adversary</option>
  </select>
  <button id="btn-optimize" title="UCB1 bandit optimization (O)">\u26a1 Optimize</button>
  <button id="btn-save-preset" title="Save current config as preset">\U0001f4be</button>
  <button class="transition-toggle" id="btn-anim-toggle" title="Toggle animated transitions">\U0001f39e\ufe0f</button>
</div>"""

assert OLD_HUD in content, "HUD marker not found!"
content = content.replace(OLD_HUD, NEW_HUD, 1)
print("2/7 HUD HTML replaced")

# ────────────────────────────────────────
# 3. ADD Q KEY TO HELP PANEL (after P row)
# ────────────────────────────────────────
OLD_HELP = """  <div class="row"><span class="key">O</span><span>Optimize layout (auto-learn)</span></div>
  <div class="row"><span class="key">P</span><span>Cycle presets</span></div>"""

NEW_HELP = """  <div class="row"><span class="key">O</span><span>UCB1 bandit optimize</span></div>
  <div class="row"><span class="key">P</span><span>Cycle presets (animated)</span></div>
  <div class="row"><span class="key">Q</span><span>Quality report</span></div>"""

assert OLD_HELP in content, "Help marker not found!"
content = content.replace(OLD_HELP, NEW_HELP, 1)
print("3/7 Help panel updated")

# ────────────────────────────────────────
# 4. REPLACE ALL SELFEVOLVE CLASSES (lines 269-552)
# ────────────────────────────────────────
OLD_CLASSES_START = "// \u2550\u2550\u2550 SELFEVOLVE \u2014 Adaptive Self-Improvement System \u2550\u2550\u2550"
OLD_CLASSES_END = "const buildTracker = new BuildVersionTracker();"

idx_start = content.index(OLD_CLASSES_START)
idx_end = content.index(OLD_CLASSES_END) + len(OLD_CLASSES_END)

NEW_CLASSES = """// \u2550\u2550\u2550 SELFEVOLVE APEX \u2014 Bleeding-Edge Self-Improvement System \u2550\u2550\u2550
// GraphQualityEngine + BanditOptimizer(UCB1) + AnimatedTransitioner + InteractionHeatmap
// + PluginManager + ConfigPresetManager + BuildVersionTracker
let _linkDistMultiplier = 1.0;
let _collisionExtra = 0;
let _origLinkDistFn = null;
let _isDragging = false;

// \u2500\u2500\u2500 GraphQualityEngine: Real layout quality metrics \u2500\u2500\u2500
class GraphQualityEngine {
  constructor() {
    this.history = [];
    this.maxHistory = 60;
    this.lastScore = 0;
    this.converged = false;
    this._alphaHistory = [];
    this._velHistory = [];
    this._gridSize = 50;
  }

  measure(nodes, links, sim) {
    const t0 = performance.now();
    const overlap = this._nodeOverlap(nodes);
    const crossings = this._sampledCrossings(links, nodes, 300);
    const stress = this._sampledStress(nodes, links, 200);
    const convergence = this._convergence(sim);

    // Composite: weights tuned for litigation graph aesthetics
    const overlapPenalty = Math.min(overlap / Math.max(nodes.length * 0.02, 1), 1);
    const crossPenalty = Math.min(crossings / Math.max(links.length * 0.1, 1), 1);
    const stressPenalty = Math.min(stress, 1);
    const score = Math.round(Math.max(0, Math.min(100,
      100 * (1 - 0.35 * overlapPenalty - 0.30 * crossPenalty - 0.20 * stressPenalty + 0.15 * convergence.stability)
    )));

    const result = { score, overlap, crossings, stress: +stress.toFixed(4),
      convergence, elapsed: +(performance.now() - t0).toFixed(1) };
    this.history.push(result);
    if (this.history.length > this.maxHistory) this.history.shift();
    this.lastScore = score;
    this.converged = convergence.converged;
    return result;
  }

  _nodeOverlap(nodes) {
    const grid = new Map();
    let overlaps = 0;
    const gs = this._gridSize;
    for (const n of nodes) {
      if (n.x == null || n.y == null || n.hidden) continue;
      const gx = Math.floor(n.x / gs), gy = Math.floor(n.y / gs);
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          const key = (gx + dx) + ',' + (gy + dy);
          const cell = grid.get(key);
          if (cell) {
            for (const m of cell) {
              const dist = Math.hypot(n.x - m.x, n.y - m.y);
              if (dist < (n.r || 4) + (m.r || 4)) overlaps++;
            }
          }
        }
      }
      const key = gx + ',' + gy;
      if (!grid.has(key)) grid.set(key, []);
      grid.get(key).push(n);
    }
    return overlaps;
  }

  _sampledCrossings(links, nodes, sampleSize) {
    const vis = links.filter(l => {
      const s = (typeof l.source === 'object') ? l.source : nodes.find(n => n.id === l.source);
      const t = (typeof l.target === 'object') ? l.target : nodes.find(n => n.id === l.target);
      return s && t && !s.hidden && !t.hidden && s.x != null && t.x != null;
    });
    if (vis.length < 2) return 0;
    let crossings = 0;
    const samples = Math.min(sampleSize, vis.length * (vis.length - 1) / 2);
    for (let s = 0; s < samples; s++) {
      const i = Math.floor(Math.random() * vis.length);
      let j = Math.floor(Math.random() * (vis.length - 1));
      if (j >= i) j++;
      const a = vis[i], b = vis[j];
      const as = typeof a.source === 'object' ? a.source : nodes.find(n => n.id === a.source);
      const at = typeof a.target === 'object' ? a.target : nodes.find(n => n.id === a.target);
      const bs = typeof b.source === 'object' ? b.source : nodes.find(n => n.id === b.source);
      const bt = typeof b.target === 'object' ? b.target : nodes.find(n => n.id === b.target);
      if (as && at && bs && bt && this._segmentsIntersect(
        as.x, as.y, at.x, at.y, bs.x, bs.y, bt.x, bt.y)) crossings++;
    }
    const totalPairs = vis.length * (vis.length - 1) / 2;
    return Math.round(crossings * totalPairs / samples);
  }

  _segmentsIntersect(ax1,ay1,ax2,ay2,bx1,by1,bx2,by2) {
    const d = (bx2-bx1)*(ay1-ay2)-(by2-by1)*(ax1-ax2);
    if (Math.abs(d) < 1e-10) return false;
    const t = ((bx1-ax1)*(ay1-ay2)-(by1-ay1)*(ax1-ax2)) / d;
    const u = ((bx1-ax1)*(by1-by2)-(by1-ay1)*(bx1-bx2)) / d;
    return t > 0.01 && t < 0.99 && u > 0.01 && u < 0.99;
  }

  _sampledStress(nodes, links, sampleSize) {
    const visible = nodes.filter(n => !n.hidden && n.x != null);
    if (visible.length < 10) return 0;
    const adj = new Map();
    for (const l of links) {
      const sid = typeof l.source === 'object' ? l.source.id : l.source;
      const tid = typeof l.target === 'object' ? l.target.id : l.target;
      if (!adj.has(sid)) adj.set(sid, []);
      if (!adj.has(tid)) adj.set(tid, []);
      adj.get(sid).push(tid);
      adj.get(tid).push(sid);
    }
    let totalStress = 0, count = 0;
    const maxBFS = 6;
    for (let s = 0; s < Math.min(sampleSize, visible.length); s++) {
      const src = visible[Math.floor(Math.random() * visible.length)];
      const tgt = visible[Math.floor(Math.random() * visible.length)];
      if (src === tgt) continue;
      const dist = this._bfs(src.id, tgt.id, adj, maxBFS);
      if (dist < 0) continue;
      const layoutDist = Math.hypot(src.x - tgt.x, src.y - tgt.y);
      const idealDist = dist * 60;
      const dev = Math.abs(layoutDist - idealDist) / Math.max(idealDist, 1);
      totalStress += dev;
      count++;
    }
    return count > 0 ? totalStress / count : 0;
  }

  _bfs(srcId, tgtId, adj, maxDepth) {
    if (srcId === tgtId) return 0;
    const visited = new Set([srcId]);
    let frontier = [srcId];
    for (let depth = 1; depth <= maxDepth; depth++) {
      const next = [];
      for (const nid of frontier) {
        for (const nbr of (adj.get(nid) || [])) {
          if (nbr === tgtId) return depth;
          if (!visited.has(nbr)) { visited.add(nbr); next.push(nbr); }
        }
      }
      frontier = next;
      if (frontier.length === 0) break;
    }
    return -1;
  }

  _convergence(sim) {
    const alpha = sim.alpha();
    const nodes = sim.nodes();
    let velVar = 0, count = 0;
    for (const n of nodes) {
      if (n.vx != null && n.vy != null) { velVar += n.vx * n.vx + n.vy * n.vy; count++; }
    }
    velVar = count > 0 ? velVar / count : 0;
    this._alphaHistory.push(alpha);
    this._velHistory.push(velVar);
    if (this._alphaHistory.length > 30) this._alphaHistory.shift();
    if (this._velHistory.length > 30) this._velHistory.shift();
    const alphaSlope = this._alphaHistory.length > 5 ?
      (this._alphaHistory[this._alphaHistory.length-1] - this._alphaHistory[this._alphaHistory.length-6]) / 5 : 0;
    const converged = alpha < 0.005 && velVar < 0.1;
    const stability = Math.max(0, Math.min(1, 1 - Math.min(velVar, 10) / 10));
    return { alpha: +alpha.toFixed(4), velVar: +velVar.toFixed(4), alphaSlope: +alphaSlope.toFixed(6), converged, stability };
  }

  renderGauge(canvasId, score) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 4;
    ctx.clearRect(0, 0, w, h);
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI * 0.75, Math.PI * 2.25, false);
    ctx.lineWidth = 4;
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.stroke();
    const pct = score / 100;
    const endAngle = Math.PI * 0.75 + pct * Math.PI * 1.5;
    const color = score >= 80 ? '#0f0' : score >= 60 ? '#0c8' : score >= 40 ? '#ff0' : score >= 20 ? '#f80' : '#f00';
    ctx.beginPath();
    ctx.arc(cx, cy, r, Math.PI * 0.75, endAngle, false);
    ctx.lineWidth = 4;
    ctx.strokeStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 6;
    ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.fillStyle = color;
    ctx.font = 'bold 12px Consolas';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(score, cx, cy);
  }

  renderSparkline(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (this.history.length < 2) return;
    const scores = this.history.map(h => h.score);
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0,204,255,0.7)';
    ctx.lineWidth = 1;
    for (let i = 0; i < scores.length; i++) {
      const x = (i / (scores.length - 1)) * w;
      const y = h - (scores[i] / 100) * h;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.closePath();
    ctx.fillStyle = 'rgba(0,204,255,0.08)';
    ctx.fill();
  }
}

// \u2500\u2500\u2500 BanditOptimizer: UCB1 multi-armed bandit for layout optimization \u2500\u2500\u2500
class BanditOptimizer {
  constructor() {
    this.arms = this._initArms();
    this.totalPulls = 0;
    this.history = JSON.parse(localStorage.getItem('mbp_bandit_history') || '[]');
    this._restoreArmStats();
  }

  _initArms() {
    return [
      { id: 'tight',    charge: -15, linkMult: 0.7, collExtra: 0, decay: 0.020, pulls: 0, totalReward: 0, label: 'Tight' },
      { id: 'default',  charge: -25, linkMult: 1.0, collExtra: 0, decay: 0.018, pulls: 0, totalReward: 0, label: 'Default' },
      { id: 'spread',   charge: -40, linkMult: 1.3, collExtra: 4, decay: 0.015, pulls: 0, totalReward: 0, label: 'Spread' },
      { id: 'airy',     charge: -50, linkMult: 1.5, collExtra: 8, decay: 0.012, pulls: 0, totalReward: 0, label: 'Airy' },
      { id: 'cluster',  charge: -12, linkMult: 0.6, collExtra: 0, decay: 0.025, pulls: 0, totalReward: 0, label: 'Cluster' },
      { id: 'balanced', charge: -30, linkMult: 1.1, collExtra: 2, decay: 0.016, pulls: 0, totalReward: 0, label: 'Balanced' },
      { id: 'sparse',   charge: -60, linkMult: 1.8, collExtra: 10,decay: 0.010, pulls: 0, totalReward: 0, label: 'Sparse' },
      { id: 'compact',  charge: -18, linkMult: 0.8, collExtra: 1, decay: 0.022, pulls: 0, totalReward: 0, label: 'Compact' },
    ];
  }

  _restoreArmStats() {
    const saved = JSON.parse(localStorage.getItem('mbp_bandit_arms') || 'null');
    if (!saved) return;
    for (const arm of this.arms) {
      const s = saved.find(a => a.id === arm.id);
      if (s) { arm.pulls = s.pulls || 0; arm.totalReward = s.totalReward || 0; }
    }
    this.totalPulls = this.arms.reduce((s, a) => s + a.pulls, 0);
  }

  _saveArmStats() {
    localStorage.setItem('mbp_bandit_arms', JSON.stringify(
      this.arms.map(a => ({ id: a.id, pulls: a.pulls, totalReward: a.totalReward }))
    ));
  }

  selectArm() {
    for (const arm of this.arms) { if (arm.pulls === 0) return arm; }
    let bestArm = this.arms[0], bestUCB = -Infinity;
    const logN = Math.log(this.totalPulls);
    for (const arm of this.arms) {
      const avgReward = arm.totalReward / arm.pulls;
      const exploration = Math.sqrt(2 * logN / arm.pulls);
      const ucb = avgReward + exploration;
      if (ucb > bestUCB) { bestUCB = ucb; bestArm = arm; }
    }
    return bestArm;
  }

  applyArm(arm, sim) {
    sim.force('charge').strength(arm.charge);
    _linkDistMultiplier = arm.linkMult;
    if (_origLinkDistFn) sim.force('link').distance(d => _origLinkDistFn(d) * _linkDistMultiplier);
    _collisionExtra = arm.collExtra;
    sim.force('collision').radius(d => (d.r || 4) + 2 + _collisionExtra);
    sim.alphaDecay(arm.decay);
    const centerStr = 0.01 + (Math.abs(arm.charge) / 1500);
    if (sim.force('x')) sim.force('x').strength(centerStr);
    if (sim.force('y')) sim.force('y').strength(centerStr);
    sim.alpha(0.4).restart();
  }

  recordReward(armId, reward) {
    const arm = this.arms.find(a => a.id === armId);
    if (!arm) return;
    arm.pulls++;
    arm.totalReward += reward;
    this.totalPulls++;
    this.history.push({ armId, reward, timestamp: Date.now() });
    if (this.history.length > 200) this.history = this.history.slice(-200);
    localStorage.setItem('mbp_bandit_history', JSON.stringify(this.history));
    this._saveArmStats();
  }

  getBestArm() {
    let best = this.arms[0];
    for (const arm of this.arms) {
      if (arm.pulls > 0 && (arm.totalReward / arm.pulls) > (best.pulls > 0 ? best.totalReward / best.pulls : -Infinity))
        best = arm;
    }
    return best;
  }

  getStats() {
    return this.arms.map(a => ({
      id: a.id, label: a.label, pulls: a.pulls,
      avgReward: a.pulls > 0 ? +(a.totalReward / a.pulls).toFixed(2) : 0
    })).sort((a, b) => b.avgReward - a.avgReward);
  }
}

// \u2500\u2500\u2500 AnimatedTransitioner: Smooth force config interpolation \u2500\u2500\u2500
class AnimatedTransitioner {
  constructor() {
    this.enabled = true;
    this.duration = 600;
    this._animating = false;
    this._startTime = 0;
    this._fromConfig = null;
    this._toConfig = null;
    this._sim = null;
    this._raf = null;
  }

  transition(sim, fromConfig, toConfig) {
    if (!this.enabled) { this._applyDirect(sim, toConfig); return; }
    this._sim = sim;
    this._fromConfig = { ...fromConfig };
    this._toConfig = { ...toConfig };
    this._startTime = performance.now();
    this._animating = true;
    if (this._raf) cancelAnimationFrame(this._raf);
    this._tick();
  }

  _tick() {
    if (!this._animating) return;
    const elapsed = performance.now() - this._startTime;
    const t = Math.min(elapsed / this.duration, 1);
    const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const lerp = (a, b) => a + (b - a) * ease;
    const cfg = {
      charge: lerp(this._fromConfig.charge, this._toConfig.charge),
      linkMult: lerp(this._fromConfig.linkMult, this._toConfig.linkMult),
      collExtra: lerp(this._fromConfig.collExtra, this._toConfig.collExtra),
      decay: lerp(this._fromConfig.decay, this._toConfig.decay),
    };
    this._applyDirect(this._sim, cfg);
    if (t < 1) { this._raf = requestAnimationFrame(() => this._tick()); }
    else { this._animating = false; }
  }

  _applyDirect(sim, cfg) {
    sim.force('charge').strength(cfg.charge);
    _linkDistMultiplier = cfg.linkMult;
    if (_origLinkDistFn) sim.force('link').distance(d => _origLinkDistFn(d) * _linkDistMultiplier);
    _collisionExtra = cfg.collExtra;
    sim.force('collision').radius(d => (d.r || 4) + 2 + _collisionExtra);
    sim.alphaDecay(cfg.decay);
    sim.alpha(Math.max(sim.alpha(), 0.15)).restart();
  }

  getCurrentConfig(sim) {
    return {
      charge: sim.force('charge').strength()(),
      linkMult: _linkDistMultiplier,
      collExtra: _collisionExtra,
      decay: sim.alphaDecay(),
    };
  }

  toggle() { this.enabled = !this.enabled; return this.enabled; }
}

// \u2500\u2500\u2500 InteractionHeatmap: Track user focus areas \u2500\u2500\u2500
class InteractionHeatmap {
  constructor() {
    this.points = [];
    this.maxPoints = 200;
    this.decayRate = 0.995;
    this.totalInteractions = 0;
  }

  record(screenX, screenY, type, weight) {
    weight = weight || 1;
    this.points.push({ x: screenX, y: screenY, w: weight, type, t: Date.now() });
    if (this.points.length > this.maxPoints) this.points.shift();
    this.totalInteractions++;
    for (let i = 0; i < this.points.length - 1; i++) { this.points[i].w *= this.decayRate; }
  }

  getCentroid() {
    if (this.points.length === 0) return null;
    let wx = 0, wy = 0, tw = 0;
    for (const p of this.points) { wx += p.x * p.w; wy += p.y * p.w; tw += p.w; }
    return tw > 0.01 ? { x: Math.round(wx / tw), y: Math.round(wy / tw), weight: +tw.toFixed(1) } : null;
  }

  getDensityAt(x, y, radius) {
    radius = radius || 100;
    let density = 0;
    for (const p of this.points) {
      const dist = Math.hypot(p.x - x, p.y - y);
      if (dist < radius) density += p.w * (1 - dist / radius);
    }
    return density;
  }
}

// \u2500\u2500\u2500 PluginManager: Event hook system (upgraded with new hooks) \u2500\u2500\u2500
class PluginManager {
  constructor() {
    this.plugins = new Map();
    this.hooks = {
      'beforeRender': [], 'afterRender': [],
      'beforeForce': [], 'afterForce': [],
      'onNodeClick': [], 'onLinkClick': [],
      'onDataLoad': [], 'onLayerChange': [],
      'onClusterDetected': [], 'onConvergenceUpdate': [],
      'onQualityUpdate': [], 'onBanditPull': []
    };
  }
  register(plugin) {
    if (!plugin.id || !plugin.name) throw new Error('Plugin must have id and name');
    if (this.plugins.has(plugin.id)) return false;
    this.plugins.set(plugin.id, { ...plugin, enabled: true, registeredAt: Date.now() });
    Object.keys(this.hooks).forEach(hook => {
      if (typeof plugin[hook] === 'function')
        this.hooks[hook].push({ pluginId: plugin.id, fn: plugin[hook] });
    });
    return true;
  }
  unregister(pluginId) {
    this.plugins.delete(pluginId);
    Object.keys(this.hooks).forEach(hook => {
      this.hooks[hook] = this.hooks[hook].filter(h => h.pluginId !== pluginId);
    });
  }
  emit(hookName, ...args) {
    const handlers = this.hooks[hookName] || [];
    let result = args[0];
    for (const handler of handlers) {
      const plugin = this.plugins.get(handler.pluginId);
      if (plugin && plugin.enabled) {
        try { const r = handler.fn.call(plugin, result, ...args.slice(1)); if (r !== undefined) result = r; }
        catch (e) { console.error('Plugin ' + handler.pluginId + ' error in ' + hookName + ':', e); }
      }
    }
    return result;
  }
  toggle(pluginId, enabled) { const p = this.plugins.get(pluginId); if (p) p.enabled = enabled; }
  listPlugins() {
    return Array.from(this.plugins.values()).map(p => ({
      id: p.id, name: p.name, enabled: p.enabled, description: p.description || ''
    }));
  }
}

// \u2500\u2500\u2500 ConfigPresetManager: Smart presets with animated transitions \u2500\u2500\u2500
class ConfigPresetManager {
  constructor() {
    this.presets = JSON.parse(localStorage.getItem('mbp_presets') || '{}');
    this.defaultPresets = {
      'dense_exploration': { charge: -15, linkMult: 0.7, collExtra: 0, decay: 0.020, description: 'Tight clusters for dense regions' },
      'overview':          { charge: -40, linkMult: 1.3, collExtra: 4, decay: 0.015, description: 'Spread for full-graph overview' },
      'presentation':      { charge: -25, linkMult: 1.0, collExtra: 2, decay: 0.018, description: 'Balanced for presentations' },
      'adversary_focus':   { charge: -30, linkMult: 0.9, collExtra: 1, decay: 0.020, description: 'Adversary network focus' },
    };
    this._currentIndex = -1;
    this._presetNames = Object.keys(this.defaultPresets);
  }
  savePreset(name, config) {
    this.presets[name] = { ...config, savedAt: Date.now() };
    localStorage.setItem('mbp_presets', JSON.stringify(this.presets));
    this._presetNames = [...Object.keys(this.defaultPresets), ...Object.keys(this.presets)];
  }
  loadPreset(name) { return this.presets[name] || this.defaultPresets[name] || null; }
  listPresets() { return { ...this.defaultPresets, ...this.presets }; }
  deletePreset(name) {
    if (this.presets[name]) { delete this.presets[name]; localStorage.setItem('mbp_presets', JSON.stringify(this.presets)); }
  }
  cyclePreset() {
    this._currentIndex = (this._currentIndex + 1) % this._presetNames.length;
    const name = this._presetNames[this._currentIndex];
    return { name, config: this.loadPreset(name) };
  }
}

// \u2500\u2500\u2500 BuildVersionTracker: Semantic versioning with quality tracking \u2500\u2500\u2500
class BuildVersionTracker {
  constructor() {
    this.history = JSON.parse(localStorage.getItem('mbp_versions') || '[]');
    this.current = this.history[this.history.length - 1] || null;
  }
  recordBuild(buildInfo) {
    const version = {
      version: buildInfo.version || this.bumpVersion(),
      timestamp: new Date().toISOString(),
      nodeCount: buildInfo.nodeCount || 0,
      linkCount: buildInfo.linkCount || 0,
      layerCount: buildInfo.layerCount || 0,
      pluginCount: buildInfo.pluginCount || 0,
      qualityScore: buildInfo.qualityScore || null,
      changes: buildInfo.changes || [],
    };
    this.history.push(version);
    this.current = version;
    if (this.history.length > 200) this.history = this.history.slice(-200);
    localStorage.setItem('mbp_versions', JSON.stringify(this.history));
    return version;
  }
  bumpVersion() {
    if (!this.current) return '7.2.0';
    const parts = this.current.version.split('.').map(Number);
    parts[2]++;
    return parts.join('.');
  }
  getChangelog(lastN) {
    return this.history.slice(-(lastN || 10)).reverse().map(v => ({
      version: v.version, date: v.timestamp, nodes: v.nodeCount, links: v.linkCount,
      quality: v.qualityScore, changes: v.changes
    }));
  }
  getDelta() {
    if (this.history.length < 2) return null;
    const prev = this.history[this.history.length - 2], curr = this.current;
    return { nodes: curr.nodeCount - prev.nodeCount, links: curr.linkCount - prev.linkCount,
      version_jump: prev.version + ' \\u2192 ' + curr.version };
  }
}

// \u2500\u2500\u2500 Instantiate SELFEVOLVE APEX modules \u2500\u2500\u2500
const qualityEngine = new GraphQualityEngine();
const banditOptimizer = new BanditOptimizer();
const transitioner = new AnimatedTransitioner();
const heatmap = new InteractionHeatmap();
const pluginManager = new PluginManager();
const presetManager = new ConfigPresetManager();
const buildTracker = new BuildVersionTracker();
let _lastBanditArm = null;
let _qualityMeasureInterval = 0;"""

content = content[:idx_start] + NEW_CLASSES + content[idx_end:]
print("4/7 Classes replaced (7 bleeding-edge classes)")

# ────────────────────────────────────────
# 5. REPLACE POST-SIM SETUP
# ────────────────────────────────────────
OLD_POSTSIM = """// SELFEVOLVE: Store original link distance function
_origLinkDistFn = (d) => {
  const t = d.type || '';
  if (t === 'FATHER_SON') return 50;
  if (t === 'MARRIED' || t === 'FORMER_PARTNER') return 40;
  if (t === 'ATTACK') return 30;
  return 60;
};
// Apply saved best config if exists
if (forceOptimizer.bestConfig) {
  forceOptimizer.applyConfig(sim, forceOptimizer.bestConfig);
}
// Record initial build
buildTracker.recordBuild({
  version: '7.1.0',
  nodeCount: NODES.length,
  linkCount: LINKS.length,
  layerCount: LAYERS.length,
  pluginCount: 0,
  changes: ['SELFEVOLVE integration']
});
forceOptimizer._updateHUD();"""

NEW_POSTSIM = """// SELFEVOLVE APEX: Store original link distance function
_origLinkDistFn = (d) => {
  const t = d.type || '';
  if (t === 'FATHER_SON') return 50;
  if (t === 'MARRIED' || t === 'FORMER_PARTNER') return 40;
  if (t === 'ATTACK') return 30;
  return 60;
};
// Apply saved best bandit arm if exists
const savedBest = banditOptimizer.getBestArm();
if (savedBest && savedBest.pulls > 0) {
  banditOptimizer.applyArm(savedBest, sim);
}
// Record initial build
buildTracker.recordBuild({
  version: '7.2.0',
  nodeCount: NODES.length,
  linkCount: LINKS.length,
  layerCount: LAYERS.length,
  pluginCount: 0,
  qualityScore: null,
  changes: ['SELFEVOLVE APEX', 'GraphQualityEngine', 'UCB1 BanditOptimizer', 'AnimatedTransitioner', 'InteractionHeatmap']
});
// Quality measurement on sim tick (every 30 ticks)
_qualityMeasureInterval = 0;
function _selfevolveTickHook() {
  _qualityMeasureInterval++;
  if (_qualityMeasureInterval % 30 === 0) {
    const q = qualityEngine.measure(NODES, LINKS, sim);
    pluginManager.emit('onQualityUpdate', q);
    const scoreEl = document.getElementById('quality-score-num');
    if (scoreEl) {
      scoreEl.textContent = q.score;
      scoreEl.className = q.score >= 80 ? 'excellent' : q.score >= 60 ? 'good' : q.score >= 40 ? 'fair' : q.score >= 20 ? 'poor' : 'bad';
    }
    const led = document.getElementById('convergence-led');
    if (led) led.className = q.convergence.converged ? 'converging' : q.convergence.stability > 0.5 ? 'active' : 'idle';
    qualityEngine.renderGauge('quality-gauge', q.score);
    qualityEngine.renderSparkline('quality-sparkline');
    const cntEl = document.getElementById('evo-count');
    if (cntEl) cntEl.textContent = heatmap.totalInteractions;
    const modeEl = document.getElementById('evo-mode');
    if (modeEl) {
      modeEl.textContent = banditOptimizer.totalPulls > 5 ? 'OPTIMIZING' : 'LEARNING';
      modeEl.className = banditOptimizer.totalPulls > 5 ? 'active-learn' : 'learning';
    }
    const bsEl = document.getElementById('bandit-stats');
    if (bsEl) {
      const stats = banditOptimizer.getStats().slice(0, 3);
      bsEl.textContent = stats.map(s => s.label + ':' + s.avgReward).join(' | ');
    }
    const hmEl = document.getElementById('heatmap-indicator');
    if (hmEl) {
      const c = heatmap.getCentroid();
      hmEl.textContent = c ? '\\u2295 focus (' + c.x + ',' + c.y + ')' : '';
    }
    if (_lastBanditArm && _qualityMeasureInterval > 90) {
      const reward = (q.score - 50) / 50;
      banditOptimizer.recordReward(_lastBanditArm.id, reward);
      pluginManager.emit('onBanditPull', { arm: _lastBanditArm, reward, quality: q.score });
      _lastBanditArm = null;
    }
  }
}"""

assert OLD_POSTSIM in content, "Post-sim marker not found!"
content = content.replace(OLD_POSTSIM, NEW_POSTSIM, 1)
print("5/7 Post-sim setup replaced")

# ────────────────────────────────────────
# 6. REPLACE KEYBOARD HANDLERS
# ────────────────────────────────────────
OLD_KEYBOARD = """  } else if (e.key === 'o' || e.key === 'O') {
    const cfg = forceOptimizer.optimize();
    if (cfg) {
      forceOptimizer.applyConfig(sim, cfg);
      console.log('SELFEVOLVE: Layout optimized', cfg);
    } else {
      console.log('SELFEVOLVE: Need 20+ interactions to optimize (' + forceOptimizer.interactions.length + ' so far)');
    }
  } else if (e.key === 'p' || e.key === 'P') {
    const { name, config } = presetManager.cyclePreset();
    if (config) {
      forceOptimizer.applyConfig(sim, config);
      console.log('SELFEVOLVE: Preset applied:', name);
    }
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {"""

NEW_KEYBOARD = """  } else if (e.key === 'o' || e.key === 'O') {
    // UCB1 bandit optimization
    const arm = banditOptimizer.selectArm();
    const fromCfg = transitioner.getCurrentConfig(sim);
    const toCfg = { charge: arm.charge, linkMult: arm.linkMult, collExtra: arm.collExtra, decay: arm.decay };
    transitioner.transition(sim, fromCfg, toCfg);
    _lastBanditArm = arm;
    _qualityMeasureInterval = 0;
    console.log('SELFEVOLVE APEX: UCB1 arm "' + arm.label + '" (pulls:' + arm.pulls + ', avg:' + (arm.pulls > 0 ? (arm.totalReward/arm.pulls).toFixed(2) : '?') + ')');
  } else if (e.key === 'p' || e.key === 'P') {
    const { name, config } = presetManager.cyclePreset();
    if (config) {
      const fromCfg = transitioner.getCurrentConfig(sim);
      transitioner.transition(sim, fromCfg, config);
      console.log('SELFEVOLVE APEX: Preset:', name);
    }
  } else if (e.key === 'q' || e.key === 'Q') {
    const q = qualityEngine.measure(NODES, LINKS, sim);
    const best = banditOptimizer.getBestArm();
    const stats = banditOptimizer.getStats();
    console.log('%c\\u2550\\u2550\\u2550 SELFEVOLVE APEX Quality Report \\u2550\\u2550\\u2550', 'color:#0cf;font-weight:bold');
    console.log('Quality:', q.score + '/100 | Overlaps:', q.overlap, '| Crossings:', q.crossings, '| Stress:', q.stress);
    console.log('Convergence:', q.convergence.converged ? 'CONVERGED' : 'active', '(\\u03b1=' + q.convergence.alpha + ' vel=' + q.convergence.velVar + ')');
    console.log('Best arm:', best.label, '(avg ' + (best.pulls > 0 ? (best.totalReward/best.pulls).toFixed(3) : 'n/a') + ', ' + best.pulls + ' pulls)');
    console.log('All arms:', stats.map(s => s.label + '=' + s.avgReward).join(', '));
    console.log('Heatmap:', heatmap.totalInteractions, 'interactions');
    alert('Quality: ' + q.score + '/100\\nOverlaps: ' + q.overlap + '  Crossings: ' + q.crossings + '\\nStress: ' + q.stress + '  Converged: ' + q.convergence.converged + '\\nBest arm: ' + best.label + ' (' + best.pulls + ' pulls)');
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {"""

assert OLD_KEYBOARD in content, "Keyboard marker not found!"
content = content.replace(OLD_KEYBOARD, NEW_KEYBOARD, 1)
print("6/7 Keyboard handlers upgraded (O=UCB1, P=animated, Q=quality)")

# ────────────────────────────────────────
# 7. REPLACE UI WIRING
# ────────────────────────────────────────
OLD_WIRING = """// \u2550\u2550\u2550 SELFEVOLVE UI WIRING \u2550\u2550\u2550
document.getElementById('preset-select').addEventListener('change', (e) => {
  const name = e.target.value;
  if (!name) return;
  const config = presetManager.loadPreset(name);
  if (config) {
    forceOptimizer.applyConfig(sim, config);
    console.log('SELFEVOLVE: Preset loaded:', name);
  }
});
document.getElementById('btn-optimize').addEventListener('click', () => {
  const cfg = forceOptimizer.optimize();
  if (cfg) {
    forceOptimizer.applyConfig(sim, cfg);
    console.log('SELFEVOLVE: Optimized from button');
  } else {
    alert('Need 20+ interactions to optimize (' + forceOptimizer.interactions.length + ' so far)');
  }
});
document.getElementById('btn-save-preset').addEventListener('click', () => {
  const name = prompt('Preset name:');
  if (name) {
    presetManager.savePreset(name, forceOptimizer.getCurrentConfig());
    console.log('SELFEVOLVE: Preset saved:', name);
  }
});"""

NEW_WIRING = """// \u2550\u2550\u2550 SELFEVOLVE APEX UI WIRING \u2550\u2550\u2550
document.getElementById('preset-select').addEventListener('change', (e) => {
  const name = e.target.value;
  if (!name) return;
  const config = presetManager.loadPreset(name);
  if (config) {
    const fromCfg = transitioner.getCurrentConfig(sim);
    transitioner.transition(sim, fromCfg, config);
    console.log('SELFEVOLVE APEX: Preset:', name);
  }
});
document.getElementById('btn-optimize').addEventListener('click', () => {
  const arm = banditOptimizer.selectArm();
  const fromCfg = transitioner.getCurrentConfig(sim);
  const toCfg = { charge: arm.charge, linkMult: arm.linkMult, collExtra: arm.collExtra, decay: arm.decay };
  transitioner.transition(sim, fromCfg, toCfg);
  _lastBanditArm = arm;
  _qualityMeasureInterval = 0;
  console.log('SELFEVOLVE APEX: UCB1 arm "' + arm.label + '"');
});
document.getElementById('btn-save-preset').addEventListener('click', () => {
  const name = prompt('Preset name:');
  if (name) {
    presetManager.savePreset(name, transitioner.getCurrentConfig(sim));
    console.log('SELFEVOLVE APEX: Preset saved:', name);
  }
});
document.getElementById('btn-anim-toggle').addEventListener('click', () => {
  const on = transitioner.toggle();
  const btn = document.getElementById('btn-anim-toggle');
  btn.classList.toggle('active', on);
  btn.title = on ? 'Animated transitions ON' : 'Animated transitions OFF';
  console.log('SELFEVOLVE APEX: Transitions', on ? 'ON' : 'OFF');
});
document.getElementById('quality-gauge').addEventListener('click', () => {
  const q = qualityEngine.measure(NODES, LINKS, sim);
  alert('Quality: ' + q.score + '/100\\nOverlaps: ' + q.overlap + '  Crossings: ' + q.crossings + '\\nStress: ' + q.stress + '  Elapsed: ' + q.elapsed + 'ms');
});"""

assert OLD_WIRING in content, "UI wiring marker not found!"
content = content.replace(OLD_WIRING, NEW_WIRING, 1)
print("7/7 UI wiring replaced")

# ────────────────────────────────────────
# BONUS: Wire tick hook + heatmap + console log
# ────────────────────────────────────────
OLD_TICK = ".on('tick', () => { linksDirty = true; pluginManager.emit('afterForce'); });"
NEW_TICK = ".on('tick', () => { linksDirty = true; pluginManager.emit('afterForce'); _selfevolveTickHook(); });"
if OLD_TICK in content:
    content = content.replace(OLD_TICK, NEW_TICK, 1)
    print("B1 Sim tick hook wired")

# Replace forceOptimizer interaction recording with heatmap
replacements = [
    ("forceOptimizer.recordInteraction('zoom_in', { k: transform.k });",
     "heatmap.record(W/2, H/2, 'zoom_in', 1);"),
    ("forceOptimizer.recordInteraction('zoom_out', { k: transform.k });",
     "heatmap.record(W/2, H/2, 'zoom_out', 1);"),
    ("forceOptimizer.recordInteraction('click', { nodeId: hit.id, layer: hit.layer });",
     "heatmap.record(e.data.global.x, e.data.global.y, 'click', 2);"),
    ("forceOptimizer.recordInteraction('drag_start', { nodeId: d.id });",
     "heatmap.record(event.x, event.y, 'drag_start', 1.5);"),
    ("forceOptimizer.recordInteraction('drag_end', { nodeId: d.id });",
     "heatmap.record(event.x, event.y, 'drag_end', 1.5);"),
    ("forceOptimizer.recordInteraction('layer_toggle', { layer: L.name, visible: !btn.classList.contains('active') });",
     "heatmap.record(W/2, H/2, 'layer_toggle', 1);"),
]
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        print(f"  B2 Replaced: {old[:50]}...")

OLD_CONSOLE = "console.log('THEMANBEARPIG v7.0 + SELFEVOLVE loaded:', NODES.length, 'nodes,', LINKS.length, 'links');"
NEW_CONSOLE = "console.log('THEMANBEARPIG v7.2 APEX loaded:', NODES.length, 'nodes,', LINKS.length, 'links, [GraphQuality + UCB1 Bandit + AnimTransitions + Heatmap]');"
if OLD_CONSOLE in content:
    content = content.replace(OLD_CONSOLE, NEW_CONSOLE, 1)
    print("B3 Console log updated to v7.2 APEX")

# ────────────────────────────────────────
# WRITE OUTPUT
# ────────────────────────────────────────
with open(SRC, "w", encoding="utf-8") as f:
    f.write(content)

new_lines = content.count('\n') + 1
print(f"\nDone! {original_len:,} -> {len(content):,} chars ({len(content)-original_len:+,})")
print(f"Lines: ~{new_lines}")
print(f"File: {SRC}")

# Final check for remaining old references
remaining = []
for i, line in enumerate(content.split('\n'), 1):
    if "forceOptimizer" in line:
        remaining.append(f"  line {i}: {line.strip()[:80]}")
if remaining:
    print(f"\nWARN: {len(remaining)} remaining forceOptimizer refs:")
    for r in remaining:
        print(r)
else:
    print("\nClean: Zero remaining forceOptimizer references")
