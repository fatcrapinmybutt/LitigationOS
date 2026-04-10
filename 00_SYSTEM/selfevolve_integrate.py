"""
SELFEVOLVE Integration Script for THEMANBEARPIG v7 HTML
Integrates 4 self-evolution modules: AdaptiveForceOptimizer, ConfigPresetManager,
PluginManager, BuildVersionTracker into the v7 visualization.
"""
import sys

FILE = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7\THEMANBEARPIG_v7.html"

with open(FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Read {len(lines)} lines, {sum(len(l) for l in lines)} bytes")

# All edits are described as (line_number_1based, action, content)
# We'll build the new file by processing insertions

# === EDIT 1: CSS additions ===
# Insert before line 57 (</style>) — after the tooltip CSS on line 56
CSS_BLOCK = """\
#preset-bar{position:fixed;top:46px;left:12px;z-index:200;display:flex;gap:4px;align-items:center}
#preset-bar select{background:var(--panel);color:var(--text);border:1px solid var(--border);
border-radius:4px;padding:2px 6px;font-size:10px;font-family:Consolas,monospace}
#preset-bar button{background:var(--panel);color:var(--accent);border:1px solid var(--border);
border-radius:4px;padding:2px 8px;font-size:10px;cursor:pointer;font-family:Consolas,monospace}
#preset-bar button:hover{background:rgba(0,204,255,0.15)}
#evo-stats{position:fixed;top:46px;right:12px;z-index:200;font-size:9px;color:var(--text2);
font-family:Consolas,monospace;text-align:right}
#evo-stats .active-learn{color:var(--green)}
#evo-stats .learning{color:var(--gold)}
"""

# === EDIT 2: HTML additions ===
# Insert after line 67 (end of HUD panel) — add evolution stats display
HUD_HTML = """\

<div id="evo-stats">
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
</div>
"""

# Insert after line 108 (last help row before </div>) — add new keyboard shortcuts
HELP_ROWS = """\
  <div class="row"><span class="key">O</span><span>Optimize layout (auto-learn)</span></div>
  <div class="row"><span class="key">P</span><span>Cycle presets</span></div>
"""

# === EDIT 3: JavaScript classes — insert after line 238 (let tickCount = 0;) ===
JS_CLASSES = r"""
// ═══ SELFEVOLVE — Adaptive Self-Improvement System ═══
let _linkDistMultiplier = 1.0;
let _collisionExtra = 0;
let _origLinkDistFn = null; // stored after sim creation
let _isDragging = false;

class AdaptiveForceOptimizer {
  constructor() {
    this.interactions = JSON.parse(localStorage.getItem('mbp_interactions') || '[]');
    this.bestConfig = JSON.parse(localStorage.getItem('mbp_best_config') || 'null');
    this.configHistory = JSON.parse(localStorage.getItem('mbp_config_history') || '[]');
  }

  recordInteraction(type, params) {
    if (_isDragging && type !== 'drag_end') return;
    this.interactions.push({
      type, params,
      timestamp: Date.now(),
      config: this.getCurrentConfig()
    });
    if (this.interactions.length > 500) this.interactions = this.interactions.slice(-500);
    localStorage.setItem('mbp_interactions', JSON.stringify(this.interactions));
    this._updateHUD();
  }

  getCurrentConfig() {
    return {
      chargeStrength: sim ? sim.force('charge').strength() : -25,
      linkDistMultiplier: _linkDistMultiplier,
      centerStrength: sim && sim.force('center') ? sim.force('center').strength() : 0.03,
      collisionExtra: _collisionExtra,
      alphaDecay: sim ? sim.alphaDecay() : 0.018
    };
  }

  optimize() {
    if (this.interactions.length < 20) return null;
    if (_isDragging) return null;

    const recent = this.interactions.slice(-50);
    const zoomOuts = recent.filter(i => i.type === 'zoom_out').length;
    const zoomIns = recent.filter(i => i.type === 'zoom_in').length;
    const drags = recent.filter(i => i.type === 'drag_end').length;
    const clicks = recent.filter(i => i.type === 'click').length;

    const config = { ...this.getCurrentConfig() };

    // Too much zoom-out → nodes too spread → weaken charge (less repulsion)
    if (zoomOuts > zoomIns * 2) {
      config.chargeStrength = Math.min(config.chargeStrength + 5, -5);
      config.linkDistMultiplier = Math.max(config.linkDistMultiplier - 0.1, 0.4);
    }
    // Too much zoom-in → nodes too clustered → strengthen charge (more repulsion)
    if (zoomIns > zoomOuts * 2) {
      config.chargeStrength = Math.max(config.chargeStrength - 5, -100);
      config.linkDistMultiplier = Math.min(config.linkDistMultiplier + 0.1, 2.5);
    }
    // Lots of dragging → layout unsatisfying → settle faster
    if (drags > clicks * 3) {
      config.alphaDecay = Math.min(config.alphaDecay + 0.003, 0.06);
    }

    this.bestConfig = config;
    this.configHistory.push({ ...config, timestamp: Date.now() });
    if (this.configHistory.length > 100) this.configHistory = this.configHistory.slice(-100);

    localStorage.setItem('mbp_best_config', JSON.stringify(config));
    localStorage.setItem('mbp_config_history', JSON.stringify(this.configHistory));

    return config;
  }

  applyConfig(simulation, config) {
    if (!config || _isDragging) return;
    simulation.force('charge').strength(config.chargeStrength);
    _linkDistMultiplier = config.linkDistMultiplier;
    if (_origLinkDistFn) {
      simulation.force('link').distance(d => _origLinkDistFn(d) * _linkDistMultiplier);
    }
    if (simulation.force('center')) {
      simulation.force('center').strength(config.centerStrength);
    }
    _collisionExtra = config.collisionExtra;
    simulation.force('collision').radius(d => d.r + 2 + _collisionExtra);
    simulation.alphaDecay(config.alphaDecay);
    simulation.alpha(0.3).restart();
  }

  getEvolutionStats() {
    return {
      totalInteractions: this.interactions.length,
      configChanges: this.configHistory.length,
      currentConfig: this.getCurrentConfig(),
      bestConfig: this.bestConfig,
      learningRate: this.interactions.length >= 20 ? 'ACTIVE' : 'LEARNING'
    };
  }

  _updateHUD() {
    const modeEl = document.getElementById('evo-mode');
    const countEl = document.getElementById('evo-count');
    if (modeEl) {
      const active = this.interactions.length >= 20;
      modeEl.textContent = active ? 'ACTIVE' : 'LEARNING';
      modeEl.className = active ? 'active-learn' : 'learning';
    }
    if (countEl) countEl.textContent = this.interactions.length;
  }
}

class ConfigPresetManager {
  constructor() {
    this.presets = JSON.parse(localStorage.getItem('mbp_presets') || '{}');
    this.defaultPresets = {
      'dense_exploration': {
        chargeStrength: -50, linkDistMultiplier: 0.7, centerStrength: 0.06,
        collisionExtra: 0, alphaDecay: 0.012,
        description: 'Tight clusters for exploring dense regions'
      },
      'overview': {
        chargeStrength: -12, linkDistMultiplier: 1.5, centerStrength: 0.02,
        collisionExtra: 8, alphaDecay: 0.025,
        description: 'Spread out for full-graph overview'
      },
      'presentation': {
        chargeStrength: -25, linkDistMultiplier: 1.0, centerStrength: 0.03,
        collisionExtra: 3, alphaDecay: 0.018,
        description: 'Balanced layout for presentations'
      },
      'adversary_focus': {
        chargeStrength: -40, linkDistMultiplier: 0.8, centerStrength: 0.05,
        collisionExtra: 2, alphaDecay: 0.015,
        description: 'Adversary network analysis mode'
      }
    };
    this._presetNames = ['dense_exploration', 'overview', 'presentation', 'adversary_focus'];
    this._currentIdx = -1;
  }

  savePreset(name, config) {
    this.presets[name] = { ...config, savedAt: Date.now() };
    localStorage.setItem('mbp_presets', JSON.stringify(this.presets));
  }

  loadPreset(name) {
    return this.presets[name] || this.defaultPresets[name] || null;
  }

  cyclePreset() {
    this._currentIdx = (this._currentIdx + 1) % this._presetNames.length;
    const name = this._presetNames[this._currentIdx];
    const sel = document.getElementById('preset-select');
    if (sel) sel.value = name;
    return { name, config: this.loadPreset(name) };
  }

  listPresets() {
    return { ...this.defaultPresets, ...this.presets };
  }

  deletePreset(name) {
    if (this.presets[name]) {
      delete this.presets[name];
      localStorage.setItem('mbp_presets', JSON.stringify(this.presets));
    }
  }
}

class PluginManager {
  constructor() {
    this.plugins = new Map();
    this.hooks = {
      'beforeRender': [], 'afterRender': [],
      'beforeForce': [], 'afterForce': [],
      'onNodeClick': [], 'onLinkClick': [],
      'onDataLoad': [], 'onLayerChange': [],
      'onClusterDetected': [], 'onConvergenceUpdate': []
    };
  }

  register(plugin) {
    if (!plugin.id || !plugin.name) throw new Error('Plugin must have id and name');
    if (this.plugins.has(plugin.id)) return false;
    this.plugins.set(plugin.id, { ...plugin, enabled: true, registeredAt: Date.now() });
    Object.keys(this.hooks).forEach(hook => {
      if (typeof plugin[hook] === 'function') {
        this.hooks[hook].push({ pluginId: plugin.id, fn: plugin[hook] });
      }
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
        try {
          const r = handler.fn.call(plugin, result, ...args.slice(1));
          if (r !== undefined) result = r;
        } catch (e) {
          console.error('Plugin ' + handler.pluginId + ' error in ' + hookName + ':', e);
        }
      }
    }
    return result;
  }

  toggle(pluginId, enabled) {
    const plugin = this.plugins.get(pluginId);
    if (plugin) plugin.enabled = enabled;
  }

  listPlugins() {
    return Array.from(this.plugins.values()).map(p => ({
      id: p.id, name: p.name, enabled: p.enabled,
      description: p.description || ''
    }));
  }
}

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
      changes: buildInfo.changes || []
    };
    this.history.push(version);
    this.current = version;
    if (this.history.length > 200) this.history = this.history.slice(-200);
    localStorage.setItem('mbp_versions', JSON.stringify(this.history));
    return version;
  }

  bumpVersion() {
    if (!this.current) return '7.1.0';
    const parts = this.current.version.split('.').map(Number);
    parts[2]++;
    return parts.join('.');
  }

  getChangelog(lastN = 10) {
    return this.history.slice(-lastN).reverse().map(v => ({
      version: v.version, date: v.timestamp,
      nodes: v.nodeCount, links: v.linkCount, changes: v.changes
    }));
  }

  getDelta() {
    if (this.history.length < 2) return null;
    const prev = this.history[this.history.length - 2];
    const curr = this.current;
    return {
      nodes: curr.nodeCount - prev.nodeCount,
      links: curr.linkCount - prev.linkCount,
      layers: curr.layerCount - prev.layerCount,
      version_jump: prev.version + ' -> ' + curr.version
    };
  }
}

// Instantiate SELFEVOLVE modules
const forceOptimizer = new AdaptiveForceOptimizer();
const presetManager = new ConfigPresetManager();
const pluginManager = new PluginManager();
const buildTracker = new BuildVersionTracker();
"""

# Now build the new file
new_lines = []
i = 0
total = len(lines)

while i < total:
    line_num = i + 1  # 1-based

    # EDIT 1: Insert CSS before </style> (line 57)
    if line_num == 57:
        new_lines.append(CSS_BLOCK)
        new_lines.append(lines[i])  # </style>
        i += 1
        continue

    # EDIT 2a: Insert HUD HTML after line 67 (end of HUD panel </div>)
    if line_num == 67:
        new_lines.append(lines[i])  # </div> of HUD
        new_lines.append(HUD_HTML)
        i += 1
        continue

    # EDIT 2b: Insert help rows after line 108 (last help row before </div>)
    if line_num == 108:
        new_lines.append(lines[i])  # <div class="row">...Scroll...</div>
        new_lines.append(HELP_ROWS)
        i += 1
        continue

    # EDIT 3: Insert JS classes after line 238 (let tickCount = 0;)
    if line_num == 238:
        new_lines.append(lines[i])  # let tickCount = 0;
        new_lines.append(JS_CLASSES)
        i += 1
        continue

    # Default: copy line as-is
    new_lines.append(lines[i])
    i += 1

# Now we need to do inline modifications for hook wiring
# Convert to a single string, then do targeted replacements
content = ''.join(new_lines)

# === HOOK 1: Store original link distance function after sim creation ===
# After the sim definition ends at ".on('tick', () => { linksDirty = true; });"
# Insert code to store original function and apply saved config
SIM_HOOK = """
// SELFEVOLVE: Store original link distance function
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
forceOptimizer._updateHUD();
"""
content = content.replace(
    "  .on('tick', () => { linksDirty = true; });\n\n// ═══ UPDATE FUNCTIONS",
    "  .on('tick', () => { linksDirty = true; pluginManager.emit('afterForce'); });\n" + SIM_HOOK + "\n// ═══ UPDATE FUNCTIONS"
)

# === HOOK 2: Ticker — wrap with beforeRender/afterRender ===
content = content.replace(
    "app.ticker.add(() => {\n  tickCount++;",
    "app.ticker.add(() => {\n  pluginManager.emit('beforeRender');\n  tickCount++;"
)
content = content.replace(
    "  if (tickCount % 20 === 0) updateMinimap();\n});",
    "  if (tickCount % 20 === 0) updateMinimap();\n  pluginManager.emit('afterRender');\n});"
)

# === HOOK 3: Zoom — record interactions ===
content = content.replace(
    "  .on('zoom', (e) => {\n    transform = e.transform;\n    world.position.set(transform.x, transform.y);\n    world.scale.set(transform.k);\n  });",
    """  .on('zoom', (e) => {
    const prevK = transform.k;
    transform = e.transform;
    world.position.set(transform.x, transform.y);
    world.scale.set(transform.k);
    if (transform.k > prevK) forceOptimizer.recordInteraction('zoom_in', {scale: transform.k});
    else if (transform.k < prevK) forceOptimizer.recordInteraction('zoom_out', {scale: transform.k});
  });"""
)

# === HOOK 4: Pointerdown — record click + plugin hook ===
content = content.replace(
    "    if (found && found !== selectedNode) {\n      selectedNode = found;\n      showInfo(found);",
    "    if (found && found !== selectedNode) {\n      selectedNode = found;\n      showInfo(found);\n      forceOptimizer.recordInteraction('click', {nodeId: found.id});\n      pluginManager.emit('onNodeClick', found);"
)

# === HOOK 5: toggleLayer — plugin hook ===
content = content.replace(
    "  linksDirty = true;\n  updateNodeVisibility();\n}",
    "  linksDirty = true;\n  updateNodeVisibility();\n  pluginManager.emit('onLayerChange', id, visibleLayers);\n}",
    1  # only first occurrence
)

# === HOOK 6: Keyboard — add O and P shortcuts ===
# Insert before the final "else if ((e.ctrlKey || e.metaKey) && e.key === 'f')"
KEYBOARD_ADDITIONS = """  } else if (e.key === 'o' || e.key === 'O') {
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
"""
content = content.replace(
    "  } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {",
    KEYBOARD_ADDITIONS + "  } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {"
)

# === HOOK 7: Drag start — set _isDragging flag ===
content = content.replace(
    "  .on('start', (e) => {\n    if (!e.subject) return;\n    dragNode = e.subject;",
    "  .on('start', (e) => {\n    if (!e.subject) return;\n    dragNode = e.subject;\n    _isDragging = true;"
)

# === HOOK 8: Drag end — clear flag, record interaction ===
content = content.replace(
    "    dragNode = null;\n    app.view.style.cursor = 'grab';\n  });",
    "    _isDragging = false;\n    forceOptimizer.recordInteraction('drag_end', {nodeId: dragNode ? dragNode.id : null});\n    dragNode = null;\n    app.view.style.cursor = 'grab';\n  });"
)

# === HOOK 9: Preset selector and optimize button wiring ===
# Insert before the console.log at the end (before "console.log('THEMANBEARPIG v7.0")
INIT_BLOCK = """
// ═══ SELFEVOLVE UI WIRING ═══
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
});

"""
content = content.replace(
    "console.log('THEMANBEARPIG v7.0 loaded:',",
    INIT_BLOCK + "console.log('THEMANBEARPIG v7.0 + SELFEVOLVE loaded:',"
)

# Write the result
with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
with open(FILE, 'r', encoding='utf-8') as f:
    result = f.readlines()

print(f"Written {len(result)} lines, {sum(len(l) for l in result)} bytes")
print("SUCCESS")
