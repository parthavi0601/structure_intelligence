/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        neon: {
          cyan:   '#00D1FF',
          green:  '#00EA77',
          yellow: '#FFDF00',
          red:    '#FF355E',
          purple: '#A855F7',
        },
        dark: {
          DEFAULT: '#070C18',
          card:    '#0D1428',
          panel:   '#10192E',
          border:  'rgba(255,255,255,0.06)',
        },
      },
      animation: {
        'pulse-slow': 'pulse-slow 3s ease-in-out infinite',
        'float': 'float 4s ease-in-out infinite',
        'blink': 'blink 1s step-end infinite',
      },
    },
  },
  plugins: [],
};
