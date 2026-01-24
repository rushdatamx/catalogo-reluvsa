/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],
  theme: {
    extend: {
      colors: {
        // Colores RELUVSA
        reluvsa: {
          yellow: '#FFED00',
          black: '#1a1a1a',
          red: '#E31E24',
        },
        // Colores estilo Notion
        notion: {
          bg: '#ffffff',
          'bg-subtle': '#f7f7f5',
          border: '#e5e5e3',
          'text-primary': '#37352f',
          'text-secondary': '#787774',
        },
        // Estados
        success: '#0f7b0f',
        warning: '#cf9700',
        danger: '#e03e3e',
        // Rushdata
        rushdata: {
          gray: '#9CA3AF',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
