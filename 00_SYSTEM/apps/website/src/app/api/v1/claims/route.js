import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticCases } from '@/lib/static-data';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = Math.max(parseInt(searchParams.get('page') || '1', 10), 1);
    const limit = Math.min(Math.max(parseInt(searchParams.get('limit') || '20', 10), 1), 100);
    const offset = (page - 1) * limit;

    if (isVercel()) {
      const data = getStaticCases();
      if (!data) return errorResponse('Static claims data not found', 503);
      const allClaims = data.recent_claims || [];
      const total = data.case_summary?.total_claims || allClaims.length;
      return jsonResponse({
        claims: allClaims.slice(offset, offset + limit),
        pagination: { page, limit, total, total_pages: Math.ceil(total / limit) },
        timestamp: new Date().toISOString(),
        source: 'static',
      });
    }

    const db = getDb();
    const total = db.prepare('SELECT COUNT(*) as cnt FROM claims').get().cnt;

    const rows = db.prepare(
      `SELECT claim_id, issue_id, doc, classification, actor, proposition,
              affirmative_counter_proposition, status, generated_at
       FROM claims
       ORDER BY generated_at DESC
       LIMIT ? OFFSET ?`
    ).all(limit, offset);

    return jsonResponse({
      claims: rows,
      pagination: {
        page,
        limit,
        total,
        total_pages: Math.ceil(total / limit),
      },
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to fetch claims: ${err.message}`);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
