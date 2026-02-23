/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // <--- É ESTA LINHA QUE O TAILWIND ESTAVA PEDINDO!
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}