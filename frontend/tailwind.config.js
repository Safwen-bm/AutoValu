/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Base — warm, paper-toned instead of stark white/grey.
        paper: '#EFEBE2',
        surface: '#FBF9F4',
        'surface-alt': '#E4DFD1',
        border: '#DBD3C2',

        // Text
        ink: {
          950: '#1C1913',
          500: '#6E655A',
          400: '#A79E8F',
        },

        // Brand — gunmetal steel (structure) + headlight amber (action).
        steel: {
          DEFAULT: '#2B383D',
          hover: '#374750',
          light: '#4B6068',
        },
        amber: {
          DEFAULT: '#C97A1A',
          hover: '#AD6712',
          light: '#E7A24F',
        },

        // Verdict semaphore — green / teal / burnt orange / brick red,
        // reused everywhere a price gets judged (hero card + checker tool).
        verdict: {
          great: '#3F7A4F',
          'great-bg': '#E4EEE2',
          fair: '#35707D',
          'fair-bg': '#DFEAEC',
          steep: '#C15A22',
          'steep-bg': '#F5E3D3',
          bad: '#A13328',
          'bad-bg': '#F3DEDA',
        },
      },
      fontFamily: {
        sans: ['var(--font-body)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
    },
  },
  plugins: [],
};