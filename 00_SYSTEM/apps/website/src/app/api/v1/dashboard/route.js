import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticDashboard } from '@/lib/static-data';

export async function GET() {
  try {
    if (isVercel()) {
      const data = getStaticDashboard();
      if (!data) return errorResponse('Static dashboard data not found', 503);
      return jsonResponse({ ...data, timestamp: new Date().toISOString(), source: 'static' });
    }

    const db = getDb();

    const SEPARATION_START = '2025-08-08';
    const now = new Date();
    const sepDate = new Date(SEPARATION_START);
    const separationDays = Math.floor((now - sepDate) / (1000 * 60 * 60 * 24));

    // Violation counts
    const totalViolations = db.prepare('SELECT COUNT(*) as c FROM judicial_violations').get().c;
    const criticalViolations = db.prepare(
      "SELECT COUNT(*) as c FROM judicial_violations WHERE severity = 'critical'"
    ).get().c;
    const exParteCount = db.prepare(
      "SELECT count FROM omega_violation_analysis WHERE category LIKE '%EX_PARTE%'"
    ).all().reduce((sum, r) => sum + r.count, 0);

    // Claims & evidence
    const totalClaims = db.prepare('SELECT COUNT(*) as c FROM claims').get().c;
    const totalEvidence = db.prepare('SELECT COUNT(*) as c FROM evidence_quotes').get().c;

    // Filing readiness
    const readinessRows = db.prepare('SELECT readiness_pct, tier FROM omega_filing_readiness').all();
    const filingReadiness = {
      ready: readinessRows.filter(r => r.readiness_pct >= 75).length,
      nearReady: readinessRows.filter(r => r.readiness_pct >= 50 && r.readiness_pct < 75).length,
      total: readinessRows.length,
    };

    // Top actions from omega_legal_actions
    const topActions = db.prepare(
      'SELECT id, forum, filing_name, omega_score, omega_tier, evidence_strength, readiness_score, readiness_label FROM omega_legal_actions ORDER BY omega_score DESC'
    ).all();

    // Recent deadlines
    const recentDeadlines = db.prepare(
      'SELECT action, forum, tier, deadline_date, days_remaining, priority, status FROM omega_deadlines ORDER BY days_remaining ASC LIMIT 15'
    ).all();

    // Violations by severity for chart
    const violationsBySeverity = db.prepare(
      'SELECT severity, COUNT(*) as count FROM judicial_violations GROUP BY severity ORDER BY count DESC'
    ).all();

    // Violations by type from analysis table
    const violationsByType = db.prepare(
      "SELECT category, count FROM omega_violation_analysis WHERE analysis_type = 'by_type' ORDER BY count DESC LIMIT 8"
    ).all();

    // OMEGA scores
    const omegaScores = db.prepare(
      'SELECT action_id, name, forum, total_score, tier, tier_action, evidence_strength, urgency, feasibility FROM omega_scores ORDER BY total_score DESC'
    ).all();

    // Predictions
    const predictions = db.prepare(
      'SELECT action_name, forum, tier, probability, impact, expected_value, confidence_interval FROM omega_predictions ORDER BY expected_value DESC LIMIT 10'
    ).all();

    return jsonResponse({
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
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to fetch dashboard data: ${err.message}`);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
