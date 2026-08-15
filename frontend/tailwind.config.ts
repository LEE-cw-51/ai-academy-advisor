import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // 토큰은 RGB 채널값이라 `<alpha-value>`로 합성한다. 이래야 `text-surface/80`,
      // `bg-ink/40` 같은 투명도 표기가 동작한다 (src/styles/tokens.css 주석 참고).
      colors: {
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        surface: {
          DEFAULT: "rgb(var(--color-surface) / <alpha-value>)",
          muted: "rgb(var(--color-surface-muted) / <alpha-value>)",
          subtle: "rgb(var(--color-surface-subtle) / <alpha-value>)",
        },
        brand: {
          DEFAULT: "rgb(var(--color-brand) / <alpha-value>)",
          dark: "rgb(var(--color-brand-dark) / <alpha-value>)",
        },
        ink: {
          DEFAULT: "rgb(var(--color-ink) / <alpha-value>)",
          strong: "rgb(var(--color-ink-strong) / <alpha-value>)",
          muted: "rgb(var(--color-ink-muted) / <alpha-value>)",
          subtle: "rgb(var(--color-ink-subtle) / <alpha-value>)",
        },
        border: {
          DEFAULT: "rgb(var(--color-border) / <alpha-value>)",
          soft: "rgb(var(--color-border-soft) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--color-success) / <alpha-value>)",
          bg: "rgb(var(--color-success-bg) / <alpha-value>)",
        },
        warn: {
          DEFAULT: "rgb(var(--color-warn) / <alpha-value>)",
          bg: "rgb(var(--color-warn-bg) / <alpha-value>)",
        },
        kakao: "rgb(var(--color-kakao) / <alpha-value>)",
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', "sans-serif"],
      },
      borderRadius: {
        card: "var(--radius-card)",
        btn: "var(--radius-btn)",
      },
      boxShadow: {
        card: "var(--shadow-card)",
        soft: "var(--shadow-soft)",
      },
    },
  },
  plugins: [],
} satisfies Config;
