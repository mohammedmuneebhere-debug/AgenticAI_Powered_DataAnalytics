/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#090a0f",
        "surface-base": "#090a0f",
        "surface-card": "#13151b",
        "surface-card-alt": "#1a1d24",
        "surface-muted": "#222630",
        "border-subtle": "rgba(255, 255, 255, 0.08)",
        surface: {
          lowest: "#06070a",
          low: "#0e1015",
          DEFAULT: "#13151b",
          high: "#1a1d24",
          highest: "#222630",
          border: "#292e3a",
          subtle: "#181b22",
        },
        primary: {
          DEFAULT: "#ffffff",
          container: "#262933",
          hover: "#2e3442",
          light: "#e2e8f0",
          text: "#f8fafc",
        },
        secondary: {
          DEFAULT: "#34D399",
          container: "rgba(6, 95, 70, 0.25)",
          dark: "#003824",
          light: "#A7F3D0",
        },
        tertiary: {
          DEFAULT: "#FBBF24",
          container: "rgba(120, 53, 15, 0.3)",
          light: "#FDE68A",
        },
        error: {
          DEFAULT: "#F87171",
          container: "rgba(127, 29, 29, 0.3)",
        },
        "on-surface": "#e2e8f0",
        "on-surface-variant": "#94a3b8",
        outline: "#64748b",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
