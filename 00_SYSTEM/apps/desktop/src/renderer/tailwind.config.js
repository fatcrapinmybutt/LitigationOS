/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/renderer/pages/**/*.{js,jsx,ts,tsx}',
    './src/renderer/components/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        omega: {
          bg: '#0a0e27',
          surface: '#111836',
          card: '#1a2147',
          border: '#2a3567',
          text: '#e2e8f0',
          muted: '#94a3b8',
          critical: '#ef4444',
          high: '#f97316',
          standard: '#3b82f6',
          hold: '#6b7280',
          success: '#22c55e',
          accent: '#818cf8',
        },
        lane: {
          A: '#3b82f6', // MSC
          B: '#22c55e', // COA
          C: '#a855f7', // 14th Circuit
          D: '#ef4444', // JTC
          E: '#f97316', // USDC
          F: '#eab308', // State Bar
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(129, 140, 248, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(129, 140, 248, 0.4)' },
        },
      },
    },
  },
  plugins: [],
};
