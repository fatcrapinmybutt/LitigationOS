/**
 * Static data provider for Vercel serverless deployment.
 * Loads pre-generated JSON files from public/data/ as a fallback
 * when better-sqlite3 is not available.
 */
import { readFileSync } from 'fs';
import path from 'path';

const dataDir = path.join(process.cwd(), 'public', 'data');

function loadJson(filename) {
  try {
    const raw = readFileSync(path.join(dataDir, filename), 'utf-8');
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

let _cache = {};

function getData(key) {
  if (!_cache[key]) {
    _cache[key] = loadJson(`${key}.json`);
  }
  return _cache[key];
}

export function getStaticDashboard() {
  return getData('dashboard');
}

export function getStaticFilings() {
  return getData('filings');
}

export function getStaticTimeline() {
  return getData('timeline');
}

export function getStaticPredictions() {
  return getData('predictions');
}

export function getStaticStats() {
  return getData('stats');
}

export function getStaticOmegaScores() {
  return getData('omega');
}

export function getStaticCases() {
  return getData('cases');
}

export function getStaticEvidence() {
  return getData('evidence');
}

/** Clear cache (useful for testing) */
export function clearStaticCache() {
  _cache = {};
}
