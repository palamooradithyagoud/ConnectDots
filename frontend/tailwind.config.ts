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
          DEFAULT: "#5227ff",
          50: "#f4f1ff",
          100: "#eae5ff",
          200: "#d7cdff",
          300: "#b19eef",
          400: "#8b66ff",
          500: "#5227ff",
          600: "#441bdf",
          700: "#3814b8",
          800: "#2f1295",
          900: "#281177",
        },
        midnight: {
          DEFAULT: "#0d0d1a",
          surface: "#11111a",
          card: "#161624",
          border: "rgba(255, 255, 255, 0.08)",
          hover: "rgba(255, 255, 255, 0.04)",
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
        "brand-glow": "0 0 25px -5px rgba(82, 39, 255, 0.35)",
        "card-glass": "0 20px 40px rgba(0, 0, 0, 0.6)",
      },
    },
  },
  plugins: [],
};

export default config;
