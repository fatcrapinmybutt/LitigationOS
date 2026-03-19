#!/usr/bin/env node
/**
 * Export key tables from litigation_context.db to static JSON files
 * for Vercel serverless deployment fallback.
 *
 * Usage: node scripts/export-db-to-json.js
 */
const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.resolve(__dirname, '../../../../litigation_context.db');
const OUT_DIR = path.resolve(__dirname, '..', 'public', 'data');

if (!fs.existsSync(DB_PATH)) {
  console.error(`Database not found: ${DB_PATH}`);
  process.exit(1);
}

fs.mkdirSync(OUT_DIR, { recursive: true });

const db = new Database(DB_PATH, { readonly: true });
db.pragma('journal_mode = WAL');

function queryAll(sql) {
  try {
    return db.prepare(sql).all();
  } catch (e) {
    console.warn(`  Warning: ${e.message}`);
    return [];
  }
}

function queryOne(sql) {
  try {
    return db.prepare(sql).get();
  } catch (e) {
    console.warn(`  Warning: ${e.message}`);
    return null;
  }
}

function writeJson(filename, data) {
  const filepath = path.join(OUT_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
  const size = (fs.statSync(filepath).size / 1024).toFixed(1);
  console.log(`  ✓ ${filename} (${size} KB)`);
}

console.log('Exporting database to static JSON...');
console.log(`  DB: ${DB_PATH}`);
console.log(`  Output: ${OUT_DIR}\n`);

// --- dashboard.json ---
const SEPARATION_START = '2025-08-08';
const now = new Date();
const sepDate = new Date(SEPARATION_START);
const separationDays = Math.floor((now - sepDate) / (1000 * 60 * 60 * 24));

const totalViolations = queryOne('SELECT COUNT(*) as c FROM judicial_violations')?.c || 0;
const criticalViolations = queryOne("SELECT COUNT(*) as c FROM judicial_violations WHERE severity = 'critical'")?.c || 0;
const exParteRows = queryAll("SELECT count FROM omega_violation_analysis WHERE category LIKE '%EX_PARTE%'");
const exParteCount = exParteRows.reduce((sum, r) => sum + r.count, 0);
const totalClaims = queryOne('SELECT COUNT(*) as c FROM claims')?.c || 0;
const totalEvidence = queryOne('SELECT COUNT(*) as c FROM evidence_quotes')?.c || 0;

const readinessRows = queryAll('SELECT readiness_pct, tier FROM omega_filing_readiness');
const filingReadiness = {
  ready: readinessRows.filter(r => r.readiness_pct >= 75).length,
  nearReady: readinessRows.filter(r => r.readiness_pct >= 50 && r.readiness_pct < 75).length,
  total: readinessRows.length,
};

const topActions = queryAll(
  'SELECT id, forum, filing_name, omega_score, omega_tier, evidence_strength, readiness_score, readiness_label FROM omega_legal_actions ORDER BY omega_score DESC'
);

const recentDeadlines = queryAll(
  'SELECT action, forum, tier, deadline_date, days_remaining, priority, status FROM omega_deadlines ORDER BY days_remaining ASC LIMIT 15'
);

const violationsBySeverity = queryAll(
  'SELECT severity, COUNT(*) as count FROM judicial_violations GROUP BY severity ORDER BY count DESC'
);

const violationsByType = queryAll(
  "SELECT category, count FROM omega_violation_analysis WHERE analysis_type = 'by_type' ORDER BY count DESC LIMIT 8"
);

const omegaScores = queryAll(
  'SELECT action_id, name, forum, total_score, tier, tier_action, evidence_strength, urgency, feasibility FROM omega_scores ORDER BY total_score DESC'
);

const predictions = queryAll(
  'SELECT action_name, forum, tier, probability, impact, expected_value, confidence_interval FROM omega_predictions ORDER BY expected_value DESC LIMIT 10'
);

writeJson('dashboard.json', {
  separationDays,
  separationStart: SEPARATION_START,
  totalViolations,
  criticalViolations,
  exParteViolations: exParteCount,
  totalClaims,
  totalEvidence,
  filingReadiness,
  topActions,
  recentDeadlines,
  violationsBySeverity,
  violationsByType,
  omegaScores,
  predictions,
  exportedAt: now.toISOString(),
});

// --- filings.json ---
const filingActions = queryAll(
  'SELECT id, forum, filing_name, omega_score, omega_tier, evidence_strength, readiness_score, readiness_label FROM omega_legal_actions ORDER BY omega_score DESC'
);
const filingReadinessAll = queryAll(
  'SELECT * FROM omega_filing_readiness ORDER BY readiness_pct DESC'
);

writeJson('filings.json', {
  actions: filingActions,
  readiness: filingReadinessAll,
  exportedAt: now.toISOString(),
});

// --- timeline.json ---
const deadlines = queryAll(
  'SELECT action, forum, tier, deadline_date, days_remaining, priority, status FROM omega_deadlines ORDER BY days_remaining ASC'
);
const condensedTimeline = queryAll(
  'SELECT * FROM condensed_timeline ORDER BY rowid DESC LIMIT 100'
);

writeJson('timeline.json', {
  deadlines,
  events: condensedTimeline,
  exportedAt: now.toISOString(),
});

// --- predictions.json ---
const allPredictions = queryAll(
  'SELECT action_name, forum, tier, probability, impact, expected_value, confidence_interval FROM omega_predictions ORDER BY expected_value DESC'
);

writeJson('predictions.json', {
  predictions: allPredictions,
  exportedAt: now.toISOString(),
});

// --- stats.json (for /api/v1/stats) ---
const countTable = (name) => {
  try { return db.prepare(`SELECT COUNT(*) as cnt FROM ${name}`).get().cnt; } catch { return 0; }
};

const statsOmegaScores = queryAll(
  'SELECT name, forum, total_score, tier, separation_days FROM omega_scores ORDER BY total_score DESC'
);
const maxSeparationDays = statsOmegaScores.reduce((max, r) => Math.max(max, r.separation_days || 0), 0);

const claimsByStatus = queryAll('SELECT status, COUNT(*) as cnt FROM claims GROUP BY status');
const statsViolationsBySev = queryAll('SELECT severity, COUNT(*) as cnt FROM judicial_violations GROUP BY severity ORDER BY cnt DESC');
const evidenceByCategory = queryAll('SELECT evidence_category, COUNT(*) as cnt FROM evidence_quotes GROUP BY evidence_category ORDER BY cnt DESC LIMIT 15');

writeJson('stats.json', {
  table_counts: {
    omega_scores: countTable('omega_scores'),
    evidence_quotes: countTable('evidence_quotes'),
    claims: countTable('claims'),
    judicial_violations: countTable('judicial_violations'),
    omega_filesystem_map: countTable('omega_filesystem_map'),
  },
  separation_days: maxSeparationDays,
  omega_summary: statsOmegaScores,
  claims_by_status: claimsByStatus,
  violations_by_severity: statsViolationsBySev,
  evidence_by_category: evidenceByCategory,
  exportedAt: now.toISOString(),
});

// --- omega.json (for /api/v1/omega) ---
const allOmega = queryAll('SELECT * FROM omega_scores ORDER BY total_score DESC');

writeJson('omega.json', {
  scores: allOmega,
  total: allOmega.length,
  exportedAt: now.toISOString(),
});

// --- cases.json (for /api/v1/cases) ---
const casesClaimsCount = countTable('claims');
const casesViolationsCount = countTable('judicial_violations');
const casesEvidenceCount = countTable('evidence_quotes');
const topClaimsCases = queryAll('SELECT claim_id, classification, actor, proposition, status FROM claims LIMIT 10');
const casesSeverityCounts = queryAll('SELECT severity, COUNT(*) as cnt FROM judicial_violations GROUP BY severity ORDER BY cnt DESC');

writeJson('cases.json', {
  case_summary: {
    total_claims: casesClaimsCount,
    total_violations: casesViolationsCount,
    total_evidence_quotes: casesEvidenceCount,
    severity_breakdown: casesSeverityCounts,
  },
  recent_claims: topClaimsCases,
  exportedAt: now.toISOString(),
});

// --- evidence.json (top evidence categories for search fallback) ---
const topEvidence = queryAll(
  'SELECT id, document_id, page_number, evidence_category, quote_text, speaker, date_ref, legal_significance, source_type FROM evidence_quotes LIMIT 200'
);

writeJson('evidence.json', {
  results: topEvidence,
  total: totalEvidence,
  note: 'Static snapshot — limited to 200 records. Full search requires live DB.',
  exportedAt: now.toISOString(),
});

db.close();
console.log('\n✅ Export complete!');
