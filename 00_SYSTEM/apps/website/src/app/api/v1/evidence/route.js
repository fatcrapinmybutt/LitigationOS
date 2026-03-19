import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticEvidence } from '@/lib/static-data';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get('q');
    const limit = Math.min(parseInt(searchParams.get('limit') || '50', 10), 200);

    if (!q || q.trim().length === 0) {
      return errorResponse('Query parameter "q" is required', 400);
    }

    if (isVercel()) {
      const data = getStaticEvidence();
      if (!data) return errorResponse('Static evidence data not found', 503);
      const qLower = q.toLowerCase();
      const filtered = (data.results || [])
        .filter(r => r.quote_text && r.quote_text.toLowerCase().includes(qLower))
        .slice(0, limit);
      return jsonResponse({
        results: filtered,
        total: filtered.length,
        query: q,
        limit,
        timestamp: new Date().toISOString(),
        source: 'static',
        note: 'Limited to pre-exported snapshot. Full search requires live DB.',
      });
    }

    const db = getDb();
    const rows = db.prepare(
      `SELECT id, document_id, page_number, evidence_category, quote_text,
              speaker, date_ref, legal_significance, source_type
       FROM evidence_quotes
       WHERE quote_text LIKE ?
       LIMIT ?`
    ).all(`%${q}%`, limit);

    return jsonResponse({
      results: rows,
      total: rows.length,
      query: q,
      limit,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to search evidence: ${err.message}`);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
