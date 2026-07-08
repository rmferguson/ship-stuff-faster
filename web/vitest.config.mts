import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

/**
 * Vitest configuration.
 *
 * Coverage exclusions:
 * - shadcn/ui primitive wrappers (src/components/ui/) — tested by the library
 * - Config files — not application logic
 * - Test utilities — not production code
 *
 * This keeps coverage metrics meaningful: only app-specific code counts.
 * Add your own exclusions here (e.g., generated files, stubs).
 */
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: [
        'node_modules/**',
        'src/test/**',
        '**/*.config.*',
        // shadcn/ui primitive wrappers — covered by the library, not by our tests
        'src/components/ui/**',
        '.next/**',
        'coverage/**',
        'src/app/layout.tsx', // root layout — no business logic
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        branches: 70,
        statements: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
});
