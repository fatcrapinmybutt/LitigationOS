import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticCases } from '@/lib/static-data';

export async function GET() {
  try {
    if (isVercel()) {
      const data = getStaticCases();
      if (!data) return errorResponse('Static cases data not found', 503);
      return jsonResponse({ ...data, timestamp: new Date().toISOString(), source: 'static' });
    }

    const db = getDb();

    const claimsCount = db.prepare('SELECT COUNT(*) as cnt FROM claims').get().cnt;
    const violationsCount = db.prepare('SELECT COUNT(*) as cnt FROM judicial_violations').get().cnt;
    const evidenceCount = db.prepare('SELECT COUNT(*) as cnt FROM evidence_quotes').get().cnt;

    const topClaims = db.prepare(
      'SELECT claim_id, classification, actor, proposition, status FROM claims LIMIT 10'
    ).all();

    const severityCounts = db.prepare(
      'SELECT severity, COUNT(*) as cnt FROM judicial_violations GROUP BY severity ORDER BY cnt DESC'
    ).all();

    return jsonResponse({
      case_summary: {
        total_claims: claimsCount,
        total_violations: violationsCount,
        total_evidence_quotes: evidenceCount,
        severity_breakdown: severityCounts,
      },
      recent_claims: topClaims,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to fetch case summary: ${err.message}`);
  }
}

export async function POST(request) {
  // Database is read-only; return 405 with guidance
  return errorResponse('Database is read-only. Case creation not supported via API.', 405);
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
