/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans:    ["Inter", "system-ui", "sans-serif"],
        devanagari: ["'Noto Sans Devanagari'", "system-ui", "sans-serif"],
      },
      colors: {
        "aegis-alert": "#c53030",
        "aegis-safe":  "#2f855a",
        "aegis-ink":   "#0f172a",
      },
    },
  },
  plugins: [],
};
