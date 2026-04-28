/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          900: '#0b0d10',
          800: '#13161b',
          700: '#1c2128',
          600: '#2a313b',
          500: '#3a4350',
          400: '#5a6573',
          300: '#8b95a4',
          200: '#bcc4d0',
          100: '#e3e8ef',
        },
        accent: {
          500: '#5b9dff',
          600: '#3b7fe0',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
