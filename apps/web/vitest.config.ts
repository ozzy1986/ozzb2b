import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// `__dirname` isn't defined in ESM; derive it from `import.meta.url`.
// This works in both CJS (Windows local) and ESM (Linux CI) resolution modes.
const here = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  esbuild: {
    // React 19 automatic JSX runtime: no `import React` in every test file.
    jsx: 'automatic',
  },
  resolve: {
    // Mirrors tsconfig's paths: `@/*` resolves to `./src/*` first (the only
    // location where this repo keeps reusable code). App routes are tested
    // through Playwright / integration flows rather than vitest.
    alias: {
      '@': path.resolve(here, 'src'),
    },
  },
  test: {
    environment: 'jsdom',
    globals: false,
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx', 'app/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{ts,tsx}', 'app/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.*',
        'src/**/*.d.ts',
        'app/**/page.tsx',
        'app/**/layout.tsx',
        'app/**/route.ts',
        'app/**/sitemap.ts',
        'app/**/robots.ts',
      ],
      // Coverage is collected but not gated yet. Raise thresholds as new
      // component tests are added. Fail-fast floors are enforced for API,
      // scraper and Go services where coverage is already high.
      thresholds: {
        lines: 0,
        statements: 0,
        branches: 0,
        functions: 0,
      },
    },
  },
});
