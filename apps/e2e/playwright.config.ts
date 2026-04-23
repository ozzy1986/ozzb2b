import { defineConfig, devices } from '@playwright/test';

/**
 * E2E smoke suite for the Next.js web app.
 *
 * We run three viewports (mobile, tablet, desktop) so every shipped release
 * is exercised at the breakpoints real users hit. The web server is started
 * via `next start`; the API URL is intentionally unreachable so tests only
 * verify the page shell, routing, and client-side validation — the very
 * things that must not break regardless of backend availability.
 */

const port = Number(process.env.E2E_PORT ?? 3030);
const baseURL = process.env.E2E_BASE_URL ?? `http://127.0.0.1:${port}`;
const skipWebServer = process.env.E2E_SKIP_WEBSERVER === '1';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]]
    : [['list']],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [
    {
      name: 'desktop-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'tablet-webkit',
      use: { ...devices['iPad (gen 7)'] },
    },
    {
      name: 'mobile-webkit',
      use: { ...devices['iPhone 13'] },
    },
  ],
  webServer: skipWebServer
    ? undefined
    : {
        // Run the already-built Next.js app. The CI job builds ../web first.
        // `cwd` keeps node_modules resolution inside apps/web so we don't have
        // to hoist anything at the workspace root.
        command: `npm run start -- -p ${port}`,
        cwd: '../web',
        url: `${baseURL}/login`,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        stdout: 'pipe',
        stderr: 'pipe',
        env: {
          OZZB2B_API_URL: 'http://127.0.0.1:9',
          NEXT_PUBLIC_OZZB2B_API_URL: 'http://127.0.0.1:9',
          NODE_ENV: 'production',
        },
      },
});
