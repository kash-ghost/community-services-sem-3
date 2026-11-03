/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dark: {
          950: "#0b0f17",
          900: "#101726",
          850: "#141d30",
          800: "#1b253b",
          700: "#273552",
        },
        accent: {
          blue: "#38bdf8",
          cyan: "#06b6d4",
          teal: "#14b8a6",
        },
        susceptibility: {
          low: "#10b981",       // emerald
          moderate: "#eab308",  // yellow
          high: "#f97316",      // orange
          very_high: "#ef4444", // red
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "monospace"],
      }
    },
  },
  plugins: [],
}
