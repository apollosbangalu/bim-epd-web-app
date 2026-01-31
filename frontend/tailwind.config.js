/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Gray Theme
        'gray-theme': {
          'bg-primary': '#1a1a1a',
          'bg-secondary': '#2d2d2d',
          'bg-tertiary': '#3a3a3a',
          'text-primary': '#ffffff',
          'text-secondary': '#b0b0b0',
          'accent-primary': '#4a9eff',
          'accent-secondary': '#00d4ff',
          'border': '#404040',
        },
        // Dark Navy Theme
        'navy-theme': {
          'bg-primary': '#0a1628',
          'bg-secondary': '#162447',
          'bg-tertiary': '#1f2f4a',
          'text-primary': '#e8f1f5',
          'text-secondary': '#8fa3b8',
          'accent-primary': '#00d9ff',
          'accent-secondary': '#7b2cbf',
          'border': '#2a3f5f',
        },
      },
    },
  },
  plugins: [],
}