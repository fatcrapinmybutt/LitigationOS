import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticStats } from '@/lib/static-data';

export async function GET() {
  try {
    if (isVercel()) {
      const data = getStaticStats();
      if (!data) return errorResponse('Static stats data not found', 503);
      return jsonResponse({ ...data, timestamp: new Date().toISOString(), source: 'static' });
    }

    const db = getDb();

    const countTable = (name) => {
      try {
        return db.prepare(`SELECT COUNT(*) as cnt FROM ${name}`).get().cnt;
      } catch {
        return 0;
      }
    };

    const omegaScores = db.prepare(
      'SELECT name, forum, total_score, tier, separation_days FROM omega_scores ORDER BY total_score DESC'
    ).all();

    const maxSeparationDays = omegaScores.reduce(
      (max, r) => Math.max(max, r.separation_days || 0), 0
    );

    const claimsByStatus = db.prepare(
      'SELECT status, COUNT(*) as cnt FROM claims GROUP BY status'
    ).all();

    const violationsBySeverity = db.prepare(
      'SELECT severity, COUNT(*) as cnt FROM judicial_violations GROUP BY severity ORDER BY cnt DESC'
    ).all();

    const evidenceByCategory = db.prepare(
      'SELECT evidence_category, COUNT(*) as cnt FROM evidence_quotes GROUP BY evidence_category ORDER BY cnt DESC LIMIT 15'
    ).all();

    return jsonResponse({
      table_counts: {
        omega_scores: countTable('omega_scores'),
        evidence_quotes: countTable('evidence_quotes'),
        claims: countTable('claims'),
        judicial_violations: countTable('judicial_violations'),
        omega_filesystem_map: countTable('omega_filesystem_map'),
      },
      separation_days: maxSeparationDays,
      omega_summary: omegaScores,
      claims_by_status: claimsByStatus,
      violations_by_severity: violationsBySeverity,
      evidence_by_category: evidenceByCategory,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to fetch stats: ${err.message}`);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
