import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3efe4",
        ink: "#1c1712",
        muted: "#5e564c",
        line: "#e4d8c4",
        card: "#fffaf2",
        rust: "#9a3412",
        moss: "#3f6212",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(28,23,18,0.04), 0 16px 40px rgba(80, 52, 20, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
