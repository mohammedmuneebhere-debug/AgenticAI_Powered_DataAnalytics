/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-app)",
        "surface-base": "var(--bg-app)",
        "surface-card": "var(--bg-surface)",
        "surface-card-alt": "var(--bg-elevated)",
        "surface-muted": "var(--bg-elevated)",
        "border-subtle": "var(--border-subtle)",
        surface: {
          lowest: "var(--bg-app)",
          low: "var(--bg-sidebar)",
          DEFAULT: "var(--bg-surface)",
          high: "var(--bg-elevated)",
          highest: "var(--bg-elevated)",
          border: "var(--border)",
          subtle: "var(--bg-elevated)",
        },
        primary: {
          DEFAULT: "var(--primary)",
          container: "var(--bg-elevated)",
          hover: "var(--primary-hover)",
          light: "var(--text-primary)",
          text: "var(--text-primary)",
          foreground: "var(--on-primary)",
        },
        secondary: {
          DEFAULT: "var(--secondary)",
          container: "rgba(6, 95, 70, 0.25)",
          dark: "#003824",
          light: "#A7F3D0",
        },
        tertiary: {
          DEFAULT: "var(--tertiary)",
          container: "rgba(120, 53, 15, 0.3)",
          light: "#FDE68A",
        },
        error: {
          DEFAULT: "var(--error)",
          container: "rgba(127, 29, 29, 0.3)",
        },
        "on-surface": "var(--text-primary)",
        "on-surface-variant": "var(--text-secondary)",
        outline: "var(--text-muted)",
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
