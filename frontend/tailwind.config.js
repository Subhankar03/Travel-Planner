/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FFFCF9',
        surface: '#FFFFFF',
        surfaceAlt: '#FFF7ED',
        divider: '#E7E5E4',
        primary: {
          DEFAULT: '#F97316',
          hover: '#EA580C',
          light: '#FFEDD5',
          subtle: '#FFF7ED',
        },
        text: {
          primary: '#1C1917',
          body: '#44403C',
          secondary: '#78716C',
          muted: '#A8A29E',
        },
        semantic: {
          price: '#22C55E', // Emerald
          star: '#F59E0B',  // Amber
          flight: '#3B82F6', // Sky Blue
          hotel: '#F43F5E', // Rose
          places: '#14B8A6', // Teal
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        warm: '0 4px 14px 0 rgba(249, 115, 22, 0.05)',
        glow: '0 0 16px rgba(249, 115, 22, 0.15)',
      }
    },
  },
  plugins: [],
}
