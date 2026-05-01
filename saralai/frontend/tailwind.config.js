/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#FAF7F2",
        paperWarm: "#F4EFE7",
        ink: "#161513",
        inkSoft: "#3D3A36",
        muted: "#7A736C",
        card: "#FFFFFF",
        slate: "#19181A",
        slateSoft: "#26242A",
        ok: "#2F7D4F",
        warn: "#C77A20",
        accent: {
          DEFAULT: "#D9542B",
          soft: "#FBE9DD",
          deep: "#A23A18",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-jakarta)",
          "Inter",
          "var(--font-kannada)",
          "var(--font-devanagari)",
          "-apple-system",
          "system-ui",
          "sans-serif",
        ],
        mono: [
          "var(--font-mono)",
          "SF Mono",
          "ui-monospace",
          "monospace",
        ],
        kan: [
          "var(--font-kannada)",
          "var(--font-jakarta)",
          "system-ui",
          "sans-serif",
        ],
      },
      fontSize: {
        hero: ["44px", { lineHeight: "1.0", letterSpacing: "-0.03em" }],
        title: ["30px", { lineHeight: "1.08", letterSpacing: "-0.02em" }],
        "card-title": ["22px", { lineHeight: "1.15", letterSpacing: "-0.015em" }],
        "body-l": ["19px", { lineHeight: "1.4", letterSpacing: "-0.01em" }],
        "body-v2": ["17px", { lineHeight: "1.5", letterSpacing: "-0.005em" }],
        label: ["13px", { lineHeight: "1.2", letterSpacing: "0.08em" }],
      },
      height: {
        btn: "68px",
        fab: "64px",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "22px",
        "4xl": "28px",
      },
      boxShadow: {
        soft: "0 2px 8px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.06)",
        card: "0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
