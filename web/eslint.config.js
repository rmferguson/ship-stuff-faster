import { dirname } from 'path';
import { fileURLToPath } from 'url';
import { FlatCompat } from '@eslint/eslintrc';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * ESLint v9 flat config.
 *
 * Uses FlatCompat to bridge next/core-web-vitals (which still uses the legacy
 * config format) into the v9 flat config API. This is the recommended approach
 * until eslint-config-next ships a native flat config.
 *
 * Do NOT add a .eslintrc.json — having both configs causes silent conflicts.
 * This file is the single source of truth for linting rules.
 */
const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
];

export default eslintConfig;
