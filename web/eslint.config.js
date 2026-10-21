import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

/**
 * ESLint v9 flat config.
 *
 * eslint-config-next ships native flat configs as of v16, so no FlatCompat
 * bridge is needed.
 *
 * Do NOT add a .eslintrc.json — having both configs causes silent conflicts.
 * This file is the single source of truth for linting rules.
 */
const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // `next lint` ignored build output implicitly; plain `eslint .` does not.
  globalIgnores(['.next/**', 'out/**', 'build/**', 'coverage/**', 'next-env.d.ts']),
]);

export default eslintConfig;
