import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#7c3aed", // Electric Violet
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
          accent: "#c084fc",
        },
        charcoal: {
          DEFAULT: "#0d0d14",
          dark: "#050508",
          card: "#12121c",
          surface: "#171725",
          border: "rgba(139, 92, 246, 0.18)",
          hover: "#1d1d2e",
        },
        midnight: {
          DEFAULT: "#050509", // Dark Black base
          surface: "#0d0d14", // Dark Charcoal surface
          card: "#12121c", // Dark Charcoal card
          border: "rgba(139, 92, 246, 0.15)",
          hover: "rgba(124, 58, 237, 0.1)",
        },
        status: {
          valid: "#00bb7f",
          warning: "#f99c00",
          error: "#fb2c36",
          info: "#3080ff",
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Inter", "-apple-system", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      boxShadow: {
        "brand-glow": "0 0 25px -5px rgba(124, 58, 237, 0.5)",
        "violet-glow": "0 0 35px -5px rgba(139, 92, 246, 0.4)",
        "purple-glow": "0 0 30px -5px rgba(168, 85, 247, 0.45)",
        "card-glass": "0 20px 40px rgba(0, 0, 0, 0.7)",
      },
    },
  },
  plugins: [],
};

export default config;
