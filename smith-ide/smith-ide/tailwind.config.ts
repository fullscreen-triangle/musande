import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: { deep: "#0a0a0f", panel: "#111118", surface: "#1a1a24", hover: "#222230" },
        fg: { primary: "#e8e4dd", secondary: "#9a9690", muted: "#5a5854" },
        accent: { amber: "#d4a849", blue: "#5b8dd9", green: "#5fa85f", red: "#c94a4a", cyan: "#4db8b8" },
        border: { subtle: "#2a2a36", active: "#3a3a4a" },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
