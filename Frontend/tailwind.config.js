/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './index.html',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        mainText: '#1f2937',
        'primary-blue': '#3b82f6',
        'secondary-blue': '#1e40af',
        'primary-gray': '#6b7280',
        'error-red': '#ef4444',
        'primary-dark': '#111827',
      },
      fontFamily: {
        sans: ['Open Sans', 'sans-serif'],
        urbanist: ['Urbanist', 'sans-serif'],
      },
      animation: {
        fadeIn: 'fadeIn 0.5s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};