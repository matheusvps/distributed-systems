export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
    './composables/**/*.{js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        bone: {
          50: '#fafbf6',
          100: '#f3f5ec',
          200: '#e7eadb',
          300: '#d4d9c4',
          400: '#b6bda1'
        },
        pine: {
          50: '#edf6f0',
          100: '#d2ebdb',
          200: '#a6d6b8',
          300: '#71bd90',
          400: '#479e6b',
          500: '#2c8051',
          600: '#1d6440',
          700: '#185034',
          800: '#153f2b',
          900: '#0f2d20',
          950: '#081a12'
        },
        acid: {
          50: '#f7fce8',
          100: '#ecf8c8',
          200: '#dcf197',
          300: '#c6e65c',
          400: '#aed42f',
          500: '#8fb71d',
          600: '#6f9215',
          700: '#546e16',
          800: '#445717',
          900: '#3a4a18'
        },
        ink: {
          DEFAULT: '#142019',
          900: '#142019',
          700: '#33453b',
          500: '#647368',
          400: '#8a978c'
        }
      },
      boxShadow: {
        card: '0 1px 0 rgba(20,32,25,.04), 0 1px 2px rgba(20,32,25,.06)',
        cardhover: '0 18px 40px -22px rgba(15,45,32,.45)',
        glow: '0 0 0 1px rgba(174,212,47,.4), 0 0 28px -6px rgba(174,212,47,.5)'
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'Georgia', 'serif'],
        sans: ['"Hanken Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace']
      },
      letterSpacing: {
        tightest: '-0.04em'
      },
      borderRadius: {
        '4xl': '1.75rem'
      },
      keyframes: {
        'rise-in': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        }
      },
      animation: {
        'rise-in': 'rise-in .5s cubic-bezier(.2,.7,.2,1) both',
        'fade-in': 'fade-in .4s ease both'
      }
    }
  },
  plugins: []
}
