/**
 * LitigationOS Design System — Shared Design Tokens
 * Used across Desktop, Website, and Mobile apps
 */

export const colors = {
  // Core palette
  omega: {
    bg: '#0a0e27',
    surface: '#111836',
    card: '#1a2147',
    border: '#2a3567',
    text: '#e2e8f0',
    muted: '#94a3b8',
    accent: '#818cf8',
  },

  // OMEGA score tiers
  score: {
    critical: '#ef4444', // 85-100
    high: '#f97316',     // 70-84
    medium: '#818cf8',   // 55-69
    standard: '#3b82f6', // 40-54
    hold: '#6b7280',     // <40
  },

  // Case lanes (A-F)
  lane: {
    A: '#3b82f6', // MSC
    B: '#22c55e', // COA
    C: '#a855f7', // 14th Circuit
    D: '#ef4444', // JTC
    E: '#f97316', // USDC
    F: '#eab308', // State Bar
  },

  // Semantic
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
};

export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
    mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
    display: ['Cal Sans', 'Inter', 'sans-serif'],
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
    '5xl': '3rem',
    '6xl': '3.75rem',
  },
};

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
  '3xl': '4rem',
};

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
  glow: '0 0 20px rgba(129, 140, 248, 0.3)',
  critical: '0 0 20px rgba(239, 68, 68, 0.3)',
};

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

export const omegaTiers = [
  { min: 85, max: 100, label: 'CRITICAL — FILE NOW', color: colors.score.critical },
  { min: 70, max: 84, label: 'FILE IMMEDIATELY', color: colors.score.high },
  { min: 55, max: 69, label: 'HIGH PRIORITY', color: colors.score.medium },
  { min: 40, max: 54, label: 'STANDARD', color: colors.score.standard },
  { min: 0, max: 39, label: 'HOLD', color: colors.score.hold },
];

export const laneConfig = {
  A: { label: 'Michigan Supreme Court', abbrev: 'MSC', color: colors.lane.A },
  B: { label: 'Court of Appeals', abbrev: 'COA', color: colors.lane.B },
  C: { label: '14th Circuit Court', abbrev: '14th Cir.', color: colors.lane.C },
  D: { label: 'Judicial Tenure Commission', abbrev: 'JTC', color: colors.lane.D },
  E: { label: 'US District Court', abbrev: 'USDC', color: colors.lane.E },
  F: { label: 'State Bar of Michigan', abbrev: 'State Bar', color: colors.lane.F },
};

export function getOmegaTier(score) {
  return omegaTiers.find(t => score >= t.min && score <= t.max) || omegaTiers[4];
}

export function getScoreColor(score) {
  return getOmegaTier(score).color;
}
