/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', '"Segoe UI"', 'sans-serif'],
        mono: ['ui-monospace', '"JetBrains Mono"', 'Menlo', 'monospace'],
      },
      colors: {
        ink: '#1a1a1a',
        muted: '#666666',
        paper: '#f5f5f5',
        line: '#d9d9d9',
        forest: '#1f6f54',
        mint: '#f5f5f5',
      },
    },
  },
  plugins: [],
}
