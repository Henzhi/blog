/** @type {import('tailwindcss').Config} */
const defaultTheme = require("tailwindcss/defaultTheme")
module.exports = {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue,mjs}"],
  darkMode: "class", // allows toggling dark mode manually
  theme: {
    extend: {
      fontFamily: {
        // Inter 负责拉丁/数字，中文落系统黑体（PingFang / 雅黑），等宽用 JetBrains Mono
        sans: [
          "Inter Variable",
          "Inter",
          "-apple-system",
          "Segoe UI",
          "PingFang SC",
          "Hiragino Sans GB",
          "Microsoft YaHei",
          "Noto Sans SC",
          ...defaultTheme.fontFamily.sans,
        ],
        mono: [
          "JetBrains Mono Variable",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
}
