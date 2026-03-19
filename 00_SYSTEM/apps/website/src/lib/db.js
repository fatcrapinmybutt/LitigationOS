import path from 'path';

const IS_VERCEL = !!process.env.VERCEL;
const DB_PATH = process.env.DB_PATH || path.resolve('C:/Users/andre/LitigationOS/litigation_context.db');

let _db = null;

/**
 * Returns a better-sqlite3 database instance (local dev only).
 * On Vercel, throws — API routes should use getStaticFallback() instead.
 */
export function getDb() {
  if (IS_VERCEL) {
    throw new Error('better-sqlite3 is not available on Vercel. Use static data fallback.');
  }
  if (!_db) {
    const Database = require('better-sqlite3');
    _db = new Database(DB_PATH, { readonly: true, fileMustExist: true });
    _db.pragma('journal_mode = WAL');
    _db.pragma('cache_size = -64000');
  }
  return _db;
}

/** Returns true when running on Vercel (static fallback mode). */
export function isVercel() {
  return IS_VERCEL;
}

export function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'X-RateLimit-Limit': '100',
    'X-RateLimit-Remaining': '99',
    'X-RateLimit-Reset': String(Math.floor(Date.now() / 1000) + 60),
  };
}

export function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders() },
  });
}

export function errorResponse(message, status = 500) {
  return jsonResponse({ error: message, status }, status);
}
