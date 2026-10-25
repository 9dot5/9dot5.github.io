/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        accent: '#22d3a6',
        accent2: '#38bdf8',
        base: '#0b1120',
        panel: '#111a2e',
        edge: '#1f2a44'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"Fira Code"', 'ui-monospace', 'monospace']
      }
    }
  },
  plugins: []
};
