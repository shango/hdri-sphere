/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0a0b0c',
          900: '#0f1012',
          850: '#15171a',
          800: '#1c1f24',
          750: '#22262c',
          700: '#2a2e35',
          600: '#3b4049',
          500: '#525866',
          400: '#7e8693',
          300: '#a8aebb',
          200: '#d2d6dc',
          100: '#ebedf1',
        },
        lime: {
          400: '#c7df6c',
          500: '#b5d04a',
          600: '#95b13a',
          700: '#75902a',
        },
        coral: {
          400: '#ed8278',
          500: '#e25e4f',
          600: '#bf4538',
        },
        amber: {
          400: '#e3b865',
          500: '#d8a544',
          600: '#b6892f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      letterSpacing: {
        wider: '0.08em',
        widest: '0.14em',
      },
    },
  },
  plugins: [],
};
