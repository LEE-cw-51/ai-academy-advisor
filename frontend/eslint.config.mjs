import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // react-hooks 7의 새 규칙. AcademyDetailModal·AcademySearchPage의 effect를
    // 고치기 전까지 경고로 둔다.
    rules: { "react-hooks/set-state-in-effect": "warn" },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
