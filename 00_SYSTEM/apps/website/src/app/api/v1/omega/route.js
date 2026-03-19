import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';
import { getStaticOmegaScores } from '@/lib/static-data';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const forum = searchParams.get('forum');
    const tier = searchParams.get('tier');

    if (isVercel()) {
      const data = getStaticOmegaScores();
      if (!data) return errorResponse('Static OMEGA data not found', 503);
      let scores = data.scores || [];
      if (forum) scores = scores.filter(s => s.forum === forum);
      if (tier) scores = scores.filter(s => s.tier === tier);
      return jsonResponse({
        scores,
        total: scores.length,
        filters: { forum: forum || 'all', tier: tier || 'all' },
        timestamp: new Date().toISOString(),
        source: 'static',
      });
    }

    const db = getDb();
    let query = 'SELECT * FROM omega_scores WHERE 1=1';
    const params = [];

    if (forum) {
      query += ' AND forum = ?';
      params.push(forum);
    }
    if (tier) {
      query += ' AND tier = ?';
      params.push(tier);
    }

    query += ' ORDER BY total_score DESC';

    const rows = db.prepare(query).all(...params);

    return jsonResponse({
      scores: rows,
      total: rows.length,
      filters: { forum: forum || 'all', tier: tier || 'all' },
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    return errorResponse(`Failed to fetch OMEGA scores: ${err.message}`);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
