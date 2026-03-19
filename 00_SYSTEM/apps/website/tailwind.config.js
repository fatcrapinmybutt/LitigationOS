/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        omega: {
          bg: '#0a0e27', surface: '#111836', card: '#1a2147',
          border: '#2a3567', text: '#e2e8f0', muted: '#94a3b8',
          accent: '#818cf8', critical: '#ef4444', success: '#22c55e',
        },
      },
    },
  },
  plugins: [],
};
