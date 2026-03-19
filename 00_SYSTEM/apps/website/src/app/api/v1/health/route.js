import { getDb, isVercel, jsonResponse, errorResponse, corsHeaders } from '@/lib/db';

export async function GET() {
  try {
    if (isVercel()) {
      return jsonResponse({
        status: 'healthy',
        database: {
          connected: false,
          mode: 'static-fallback',
          note: 'Running on Vercel with pre-exported JSON data',
        },
        timestamp: new Date().toISOString(),
        version: '1.0.0',
      });
    }

    const db = getDb();
    const integrity = db.pragma('integrity_check')[0]?.integrity_check;
    const tableCount = db.prepare(
      "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table'"
    ).get().cnt;

    return jsonResponse({
      status: 'healthy',
      database: {
        connected: true,
        integrity: integrity === 'ok' ? 'ok' : 'degraded',
        tables: tableCount,
      },
      timestamp: new Date().toISOString(),
      version: '1.0.0',
    });
  } catch (err) {
    return errorResponse(`Health check failed: ${err.message}`, 503);
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
