import { defineConfig } from 'vitest/config';

export default defineConfig({
  esbuild: {
    // React 19 automatic JSX runtime: no `import React` in every test file.
    jsx: 'automatic',
  },
  resolve: {
    // Mirrors tsconfig's "paths": `@/*` resolves to `./src/*`. We use
    // process.cwd() (always the package root when invoked via npm) instead
    // of __dirname / import.meta.url so the same config works in CJS and
    // ESM loader modes.
    alias: [
      {
        find: /^@\/(.*)$/,
        replacement: `${process.cwd().replace(/\\/g, '/')}/src/$1`,
      },
    ],
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
      // Thresholds intentionally disabled until we grow RTL coverage.
      // Coverage is still collected and uploaded as a CI artifact.
      thresholds: {
        lines: 0,
        statements: 0,
        branches: 0,
        functions: 0,
      },
    },
  },
});
